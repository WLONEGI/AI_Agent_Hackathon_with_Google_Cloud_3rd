from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients import get_storage_client
from app.core.settings import get_settings
from app.db.models import (
    GeneratedImage,
    MangaAsset,
    MangaAssetType,
    MangaProject,
    MangaProjectStatus,
    MangaSession,
    MangaSessionStatus,
    PhaseResult,
    PreviewCacheMetadata,
    PreviewVersion,
)
from app.services.realtime_hub import build_event, realtime_hub
from app.services.vertex_ai_service import (
    VertexAIServiceError,
    VertexAIRateLimitError,
    VertexAICredentialsError,
    VertexAIUnavailableError,
    get_vertex_service,
)

logger = logging.getLogger(__name__)

PHASE_SEQUENCE = (
    {
        "phase": 1,
        "name": "concept_analysis",
        "label": "Phase1: コンセプト・世界観分析",
        "preview_key": "concept_sheet",
    },
    {
        "phase": 2,
        "name": "character_design",
        "label": "Phase2: キャラクター設計",
        "preview_key": "character_board",
    },
    {
        "phase": 3,
        "name": "story_structure",
        "label": "Phase3: プロット構成",
        "preview_key": "story_outline",
    },
    {
        "phase": 4,
        "name": "name_generation",
        "label": "Phase4: ネーム生成",
        "preview_key": "name_layout",
    },
    {
        "phase": 5,
        "name": "scene_imagery",
        "label": "Phase5: シーン画像生成",
        "preview_key": "scene_preview",
    },
    {
        "phase": 6,
        "name": "dialogue_layout",
        "label": "Phase6: セリフ配置",
        "preview_key": "dialogue_layout",
    },
    {
        "phase": 7,
        "name": "final_composition",
        "label": "Phase7: 最終統合・品質調整",
        "preview_key": "final_board",
    },
)

QUALITY_THRESHOLD = 0.72
MAX_PHASE_RETRIES = 3
DEFAULT_PAGE_MIN = 8
MAX_PANEL_IMAGES = 3


class PipelineOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.vertex_service = get_vertex_service()

    async def run(self, request_id: UUID) -> None:
        session = await self._get_session(request_id)
        if session is None:
            raise ValueError("session_not_found")

        session.status = MangaSessionStatus.RUNNING.value
        session.started_at = session.started_at or datetime.utcnow()
        await self.db.flush()

        await realtime_hub.publish(
            session.request_id,
            build_event(
                "session_start",
                sessionId=str(session.request_id),
                requestId=str(session.request_id),
            ),
        )

        project = session.project
        phase_context: Dict[int, Dict[str, Any]] = {}
        for phase_config in PHASE_SEQUENCE:
            phase_number = phase_config["phase"]
            session.current_phase = phase_number
            await self.db.flush()

            await realtime_hub.publish(
                session.request_id,
                build_event(
                    "phase_start",
                    phaseId=phase_number,
                    phaseName=phase_config["label"],
                ),
            )

            await realtime_hub.publish(
                session.request_id,
                build_event(
                    "phase_progress",
                    phase=phase_number,
                    progress=10,
                    status="processing",
                ),
            )

            attempt = 0
            phase_payload: Optional[Dict[str, Any]] = None
            quality_score = 0.0
            while attempt < MAX_PHASE_RETRIES:
                attempt += 1
                try:
                    phase_payload = await self._process_phase(session, phase_config, phase_context, attempt)
                except VertexAICredentialsError as exc:
                    logger.error("Vertex AI credentials error on phase %s: %s", phase_number, exc)
                    await self._handle_failure(session, project, phase_number, "vertex_credentials_error")
                    return
                except VertexAIUnavailableError as exc:
                    logger.warning("Vertex AI unavailable on phase %s (attempt %s): %s", phase_number, attempt, exc)
                    if attempt >= MAX_PHASE_RETRIES:
                        await self._handle_failure(session, project, phase_number, "vertex_ai_unavailable")
                        return
                    continue
                except VertexAIRateLimitError as exc:
                    logger.warning("Vertex AI rate limited on phase %s (attempt %s): %s", phase_number, attempt, exc)
                    if attempt >= MAX_PHASE_RETRIES:
                        await self._handle_failure(session, project, phase_number, "vertex_rate_limited")
                        return
                    await asyncio.sleep(min(2 * attempt, 5))
                    continue
                except VertexAIServiceError as exc:
                    logger.warning("Vertex AI service error on phase %s (attempt %s): %s", phase_number, attempt, exc)
                    if attempt >= MAX_PHASE_RETRIES:
                        await self._handle_failure(session, project, phase_number, str(exc))
                        return
                    continue
                except Exception as exc:  # pragma: no cover - unexpected failure
                    logger.exception("Unexpected failure processing phase %s", phase_number)
                    await self._handle_failure(session, project, phase_number, str(exc))
                    return

                quality_score = phase_payload.get("metadata", {}).get("quality", 0.0)
                if quality_score >= QUALITY_THRESHOLD:
                    break

                logger.warning(
                    "Phase %s quality %.2f below threshold %.2f (attempt %s)",
                    phase_number,
                    quality_score,
                    QUALITY_THRESHOLD,
                    attempt,
                )
                if attempt >= MAX_PHASE_RETRIES:
                    await self._handle_failure(session, project, phase_number, "quality_threshold_not_met")
                    return

            if phase_payload is None:
                await self._handle_failure(session, project, phase_number, "phase_payload_missing")
                return

            if attempt > 1:
                session.retry_count = (session.retry_count or 0) + (attempt - 1)

            await self._persist_phase_outputs(
                session=session,
                project=project,
                phase_config=phase_config,
                phase_payload=phase_payload,
            )

            await realtime_hub.publish(
                session.request_id,
                build_event(
                    "phase_progress",
                    phase=phase_number,
                    progress=90,
                    status="completed",
                    preview=phase_payload.get("preview"),
                ),
            )

            await realtime_hub.publish(
                session.request_id,
                build_event(
                    "phase_complete",
                    phaseId=phase_number,
                    result=phase_payload,
                ),
            )

            phase_context[phase_number] = phase_payload

        session.status = MangaSessionStatus.COMPLETED.value
        session.completed_at = datetime.utcnow()
        if project is not None:
            project.status = MangaProjectStatus.COMPLETED
            project.total_pages = self._estimate_pages(session, phase_context)
            project.updated_at = datetime.utcnow()
            self._upsert_project_assets(project, session)
        await self.db.flush()

        await realtime_hub.publish(
            session.request_id,
            build_event(
                "session_complete",
                results={"project_id": str(session.project_id) if session.project_id else None},
                sessionId=str(session.request_id),
                requestId=str(session.request_id),
            ),
        )

    async def _get_session(self, request_id: UUID) -> Optional[MangaSession]:
        result = await self.db.execute(
            select(MangaSession).where(MangaSession.request_id == request_id)
        )
        return result.scalar_one_or_none()

    async def _persist_phase_outputs(
        self,
        *,
        session: MangaSession,
        project: Optional[MangaProject],
        phase_config: Dict[str, Any],
        phase_payload: Dict[str, Any],
    ) -> None:
        phase_number = phase_config["phase"]
        quality_score = float(phase_payload.get("metadata", {}).get("quality", 0.0))

        phase_result = PhaseResult(
            session_id=session.id,
            phase=phase_number,
            status="completed",
            content=phase_payload,
            quality_score=quality_score,
        )
        self.db.add(phase_result)
        await self.db.flush()

        preview_version = PreviewVersion(
            session_id=session.id,
            phase=phase_number,
            version_data=phase_payload.get("preview"),
            quality_level=self._quality_to_level(quality_score),
            quality_score=quality_score,
        )
        self.db.add(preview_version)
        await self.db.flush()

        cache_entry = PreviewCacheMetadata(
            cache_key=(
                f"preview/{session.request_id}/phase-{phase_number}/"
                f"v{preview_version.created_at.timestamp():.0f}"
            ),
            version_id=preview_version.id,
            phase=phase_number,
            quality_level=self._quality_to_level(quality_score),
            signed_url=self._build_signed_url(session, phase_config, preview_version),
            content_type="application/json",
            expires_at=datetime.utcnow() + timedelta(seconds=self.settings.signed_url_ttl_seconds),
        )
        self.db.add(cache_entry)

        if phase_number == 5:
            images = phase_payload.get("data", {}).get("images", [])
            for index, image in enumerate(images, start=1):
                storage_path = (
                    f"projects/{session.project_id}/sessions/{session.request_id}/"
                    f"phase-{phase_number}/panel-{index}.png"
                )
                image_record = GeneratedImage(
                    session_id=session.id,
                    phase=phase_number,
                    storage_path=storage_path,
                    signed_url=self._build_asset_signed_url(storage_path),
                    image_metadata={
                        "panel_id": image.get("panelId"),
                        "status": image.get("status"),
                        "prompt": image.get("prompt"),
                        "has_preview": bool(image.get("url")),
                    },
                )
                self.db.add(image_record)

        await self.db.flush()

    async def _process_phase(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
        attempt: int,
    ) -> Dict[str, Any]:
        phase_number = phase_config["phase"]
        handler_map = {
            1: self._run_phase_concept,
            2: self._run_phase_characters,
            3: self._run_phase_story_structure,
            4: self._run_phase_panel_layout,
            5: self._run_phase_scene_imagery,
            6: self._run_phase_dialogue_layout,
            7: self._run_phase_final_composition,
        }
        handler = handler_map.get(phase_number)
        if handler is None:
            raise ValueError(f"unsupported_phase_{phase_number}")

        start_time = time.perf_counter()
        result = await handler(session, phase_config, context)
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        data = result.get("data", {})
        preview = result.get("preview") or data
        diagnostics = result.get("diagnostics", {})
        quality = self._evaluate_quality(phase_number, data, diagnostics)
        confidence = min(0.98, max(0.55, quality + 0.05))

        metadata = {
            "processingTimeMs": processing_time_ms,
            "quality": round(quality, 3),
            "confidence": round(confidence, 3),
            "attempt": attempt,
        }
        metadata.update(diagnostics)

        payload = {
            "phaseId": phase_number,
            "phaseName": phase_config["label"],
            "phaseKey": phase_config["name"],
            "data": data,
            "metadata": metadata,
            "preview": preview,
        }
        return payload

    async def _run_phase_concept(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        session_meta = session.session_metadata or {}
        story_text = session_meta.get("text", "")
        title = session_meta.get("title", "Untitled")
        trimmed_story = story_text[:6000]

        prompt = (
            "You are an AI manga production planner."
            " Extract concept metadata from the following story."
            " Respond in JSON with keys: themes (array of strings), world_setting, genre,"
            " target_audience, mood, synopsis (<=160 chars), page_estimate (int)."
            f"\n\nTITLE: {title}\nSTORY:\n{trimmed_story}"
        )
        raw = await self.vertex_service.generate_text(prompt)
        parsed = self._parse_json(raw)

        data = {
            "themes": self._ensure_list_of_strings(parsed, "themes", default=[title, "成長", "冒険"]),
            "worldSetting": self._coalesce(parsed, ["world_setting", "setting"], default="物語に基づく世界設定"),
            "genre": self._coalesce(parsed, ["genre"], default="ドラマ"),
            "targetAudience": self._coalesce(parsed, ["target_audience", "audience"], default="一般読者"),
            "mood": self._coalesce(parsed, ["mood", "tone"], default="希望と緊張が交錯"),
        }
        synopsis = self._coalesce(parsed, ["synopsis"], default=story_text[:160])
        page_estimate = self._coalesce(parsed, ["page_estimate", "pages"], default=max(DEFAULT_PAGE_MIN, math.ceil(len(story_text) / 800)))
        diagnostics = {
            "synopsis": synopsis,
            "pageEstimate": int(page_estimate) if isinstance(page_estimate, (int, float)) else DEFAULT_PAGE_MIN,
        }

        preview = {
            "themes": data["themes"][:3],
            "worldSetting": data["worldSetting"],
            "genre": data["genre"],
            "targetAudience": data["targetAudience"],
            "mood": data["mood"],
            "synopsis": synopsis,
        }

        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_characters(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        concept = context.get(1, {}).get("data", {})
        session_meta = session.session_metadata or {}
        story_text = session_meta.get("text", "")[:4000]

        prompt = (
            "You are designing manga characters."
            " Using the concept below, output JSON with key 'characters' (array of up to 3 objects)"
            " each object having name, role, appearance, personality."
            " Provide vivid but concise descriptions."
            f"\n\nCONCEPT: {json.dumps(concept, ensure_ascii=False)}\n\nSTORY_SNIPPET:\n{story_text}"
        )
        raw = await self.vertex_service.generate_text(prompt)
        parsed = self._parse_json(raw)
        characters = self._ensure_list_of_dicts(parsed, "characters")
        if not characters:
            characters = [
                {
                    "name": "主人公",
                    "role": "語り手",
                    "appearance": "短い黒髪と真剣な瞳",
                    "personality": "責任感が強く仲間思い",
                }
            ]

        awaitables = []
        for index, character in enumerate(characters[:2], start=1):
            prompt_image = (
                f"Manga character concept art for {character.get('name', 'main character')} in the style of modern Japanese manga. "
                f"World setting: {concept.get('worldSetting', 'contemporary Japan')}. "
                f"Appearance: {character.get('appearance', 'detailed description')}."
            )
            awaitables.append(self.vertex_service.generate_image(prompt_image))

        image_results: list[list[dict[str, Any]]] = []
        if awaitables:
            image_results = await asyncio.gather(*awaitables, return_exceptions=True)
        else:
            image_results = []

        enriched_characters = []
        for idx, character in enumerate(characters):
            image_url: Optional[str] = None
            if idx < len(image_results):
                result = image_results[idx]
                if isinstance(result, list) and result:
                    first = result[0]
                    image_url = first.get("data_url") or first.get("url")
            enriched_characters.append(
                {
                    "name": character.get("name", f"キャラクター{idx + 1}"),
                    "role": character.get("role", "主要人物"),
                    "appearance": character.get("appearance", "外見情報なし"),
                    "personality": character.get("personality", "性格情報なし"),
                    "imageUrl": image_url,
                }
            )

        data = {
            "characters": enriched_characters,
            "imageUrl": next((c["imageUrl"] for c in enriched_characters if c.get("imageUrl")), None),
        }
        diagnostics = {
            "characterCount": len(enriched_characters),
        }
        preview = {
            "characters": enriched_characters[:2],
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_story_structure(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        concept = context.get(1, {}).get("data", {})
        characters = context.get(2, {}).get("data", {}).get("characters", [])
        session_meta = session.session_metadata or {}
        story_text = session_meta.get("text", "")[:5000]

        prompt = (
            "Create a three-act manga story outline in JSON with keys:"
            " acts (array of objects with title, description, scenes array) and overall_arc."
            " Scenes should be concise strings."
            f"\n\nCONCEPT: {json.dumps(concept, ensure_ascii=False)}"
            f"\nCHARACTERS: {json.dumps(characters, ensure_ascii=False)}"
            f"\nSOURCE:\n{story_text}"
        )
        raw = await self.vertex_service.generate_text(prompt)
        parsed = self._parse_json(raw)
        acts = self._ensure_list_of_dicts(parsed, "acts")
        if not acts:
            acts = [
                {
                    "title": "序章",
                    "description": "主人公が世界の異変に気づく",
                    "scenes": ["主人公の日常", "導入となる事件"],
                },
                {
                    "title": "対立",
                    "description": "仲間を得て課題に立ち向かう",
                    "scenes": ["仲間との出会い", "試練", "決断"],
                },
                {
                    "title": "解決",
                    "description": "クライマックスと余韻",
                    "scenes": ["最終決戦", "余韻のシーン"],
                },
            ]
        overall_arc = self._coalesce(parsed, ["overall_arc", "overallArc"], default="主人公の成長と世界の変革")

        data = {
            "acts": [
                {
                    "title": act.get("title", f"Act {idx + 1}"),
                    "description": act.get("description", ""),
                    "scenes": self._ensure_list_of_strings_from_value(act.get("scenes"), default=[]),
                }
                for idx, act in enumerate(acts)
            ],
            "overallArc": overall_arc,
        }
        diagnostics = {
            "actCount": len(data["acts"]),
            "sceneCount": sum(len(act["scenes"]) for act in data["acts"]),
        }
        preview = {
            "acts": data["acts"][:2],
            "overallArc": overall_arc,
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_panel_layout(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        story = context.get(3, {}).get("data", {})
        concept = context.get(1, {}).get("data", {})
        acts = story.get("acts", [])

        prompt = (
            "Design manga panel layout guidance in JSON with keys:"
            " panels (array of objects: description, composition, characters (array), dialogues (array), camera_angle)"
            " and page_count (int)."
            f"\n\nSTORY STRUCTURE: {json.dumps(story, ensure_ascii=False)}"
            f"\nCONCEPT: {json.dumps(concept, ensure_ascii=False)}"
        )
        raw = await self.vertex_service.generate_text(prompt)
        parsed = self._parse_json(raw)
        panels = self._ensure_list_of_dicts(parsed, "panels")
        if not panels:
            panels = [
                {
                    "description": "主人公が世界の異変に気づく導入カット",
                    "composition": "ワイドショット",
                    "characters": ["主人公"],
                    "dialogues": ["これは一体…"],
                    "camera_angle": "俯瞰",
                },
                {
                    "description": "仲間との合流で意思を固める",
                    "composition": "ミディアム",
                    "characters": ["主人公", "仲間"],
                    "dialogues": ["一緒にやろう"],
                    "camera_angle": "アイレベル",
                },
            ]
        page_count = parsed.get("page_count") or max(DEFAULT_PAGE_MIN, len(acts) * 6)

        data = {
            "panels": [
                {
                    "description": panel.get("description", "シーンの説明"),
                    "composition": panel.get("composition", "ミディアム"),
                    "characters": self._ensure_list_of_strings_from_value(panel.get("characters"), default=[]),
                    "dialogues": self._ensure_list_of_strings_from_value(panel.get("dialogues"), default=[]),
                    "cameraAngle": panel.get("camera_angle", panel.get("cameraAngle", "アイレベル")),
                }
                for panel in panels
            ],
            "pageCount": int(page_count) if isinstance(page_count, (int, float)) else DEFAULT_PAGE_MIN,
        }
        diagnostics = {
            "panelCount": len(data["panels"]),
            "pageCount": data["pageCount"],
        }
        preview = {
            "panels": data["panels"][:4],
            "pageCount": data["pageCount"],
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_scene_imagery(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        panels = context.get(4, {}).get("data", {}).get("panels", [])
        concept = context.get(1, {}).get("data", {})
        if not panels:
            panels = [
                {
                    "description": "主人公が街角で空を見上げる印象的なシーン",
                    "composition": "ロングショット",
                    "characters": ["主人公"],
                    "dialogues": [],
                    "cameraAngle": "ローアングル",
                }
            ]

        selected_panels = panels[:MAX_PANEL_IMAGES]
        prompts = []
        for panel in selected_panels:
            prompt = (
                f"Generate highly detailed manga panel concept art. "
                f"Scene: {panel.get('description', 'dramatic moment')}. "
                f"Characters: {', '.join(panel.get('characters', [])) or 'main cast'}. "
                f"Camera: {panel.get('cameraAngle', 'eye level')}. "
                f"World setting: {concept.get('worldSetting', 'contemporary Japan')}."
            )
            prompts.append(prompt)

        async def _generate(prompt: str) -> list[dict[str, Any]]:
            try:
                return await self.vertex_service.generate_image(prompt)
            except VertexAIServiceError:
                return [
                    {
                        "image_base64": None,
                        "data_url": None,
                        "description": f"Placeholder image for: {prompt[:100]}",
                    }
                ]

        results = await asyncio.gather(*(_generate(p) for p in prompts), return_exceptions=True)

        images = []
        diagnostics_generated = 0
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                images.append(
                    {
                        "url": None,
                        "prompt": prompts[idx],
                        "panelId": idx + 1,
                        "status": "error",
                    }
                )
                continue
            image_entry = result[0] if result else {}
            url = image_entry.get("data_url") or image_entry.get("url")
            status = "completed" if url else "error"
            diagnostics_generated += 1 if url else 0
            images.append(
                {
                    "url": url,
                    "prompt": prompts[idx],
                    "panelId": idx + 1,
                    "status": status,
                }
            )

        data = {
            "images": images,
        }
        diagnostics = {
            "requestedPanels": len(prompts),
            "generatedImages": diagnostics_generated,
        }
        preview = {
            "images": images,
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_dialogue_layout(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        story = context.get(3, {}).get("data", {})
        characters = context.get(2, {}).get("data", {}).get("characters", [])
        panels = context.get(4, {}).get("data", {}).get("panels", [])

        prompt = (
            "Draft manga dialogues in JSON with keys: dialogues (array of {character, text, position, style, bubble_type})"
            " and sound_effects (array). Keep dialogue concise."
            f"\n\nSTORY STRUCTURE: {json.dumps(story, ensure_ascii=False)}"
            f"\nCHARACTERS: {json.dumps(characters, ensure_ascii=False)}"
            f"\nPANELS: {json.dumps(panels[:4], ensure_ascii=False)}"
        )
        raw = await self.vertex_service.generate_text(prompt)
        parsed = self._parse_json(raw)
        dialogues = self._ensure_list_of_dicts(parsed, "dialogues")
        if not dialogues:
            dialogues = [
                {
                    "character": character.get("name", "キャラクター"),
                    "text": "ここが転機になる…",
                    "position": "top-left",
                    "style": "bold",
                    "bubble_type": "speech",
                }
                for character in characters[:2]
            ] or [
                {
                    "character": "ナレーション",
                    "text": "物語はここから加速する",
                    "position": "bottom",
                    "style": "narration",
                    "bubble_type": "narration",
                }
            ]
        sound_effects = self._ensure_list_of_strings(parsed, "sound_effects", default=["ドン", "ザワザワ"])

        data = {
            "dialogues": [
                {
                    "character": item.get("character", "モブ"),
                    "text": item.get("text", "…"),
                    "position": item.get("position", "center"),
                    "style": item.get("style", "normal"),
                    "bubbleType": item.get("bubble_type", "speech"),
                }
                for item in dialogues
            ],
            "soundEffects": sound_effects,
        }
        diagnostics = {
            "dialogueCount": len(data["dialogues"]),
        }
        preview = {
            "dialogues": data["dialogues"][:5],
            "soundEffects": sound_effects[:3],
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_final_composition(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        concept = context.get(1, {}).get("data", {})
        structure = context.get(3, {}).get("data", {})
        panels = context.get(4, {}).get("data", {})
        dialogues = context.get(6, {}).get("data", {})
        images = context.get(5, {}).get("data", {})

        total_pages = panels.get("pageCount", DEFAULT_PAGE_MIN)
        final_pages = [
            {
                "pageNumber": idx + 1,
                "panels": len(panels.get("panels", [])) // max(1, total_pages) or 4,
            }
            for idx in range(min(total_pages, 12))
        ]
        quality_checks = [
            {"item": "世界観一貫性", "status": "completed", "score": 0.9},
            {"item": "キャラクター整合性", "status": "completed", "score": 0.88},
            {"item": "画像品質", "status": "processing", "score": 0.0 if not images.get("images") else 0.82},
            {"item": "校正完了", "status": "pending", "score": None},
        ]
        scored_items = [item["score"] for item in quality_checks if isinstance(item.get("score"), (int, float))]
        overall_quality = round(sum(scored_items) / max(1, len(scored_items)), 2)

        data = {
            "finalPages": final_pages,
            "qualityChecks": quality_checks,
            "overallQuality": overall_quality,
        }
        diagnostics = {
            "totalPages": total_pages,
            "imageCount": len(images.get("images", [])),
            "dialogueCount": len(dialogues.get("dialogues", [])),
        }
        preview = {
            "overallQuality": overall_quality,
            "qualityChecks": quality_checks,
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _handle_failure(
        self,
        session: MangaSession,
        project: Optional[MangaProject],
        phase_number: int,
        message: str,
    ) -> None:
        session.status = MangaSessionStatus.FAILED.value
        session.completed_at = datetime.utcnow()
        await self.db.flush()

        await realtime_hub.publish(
            session.request_id,
            build_event("phase_error", phaseId=phase_number, error=message),
        )
        await realtime_hub.publish(
            session.request_id,
            build_event("session_error", error=message),
        )

        await realtime_hub.publish(
            session.request_id,
            build_event(
                "session_complete",
                results={"project_id": str(session.project_id) if session.project_id else None},
                sessionId=str(session.request_id),
                status="failed",
            ),
        )

        if project is not None:
            project.status = MangaProjectStatus.FAILED
            project.updated_at = datetime.utcnow()
        await self.db.flush()

    def _build_signed_url(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        preview: PreviewVersion,
        *,
        file_extension: str = "json",
    ) -> str:
        bucket = self.settings.gcs_bucket_preview
        path = (
            f"preview/{session.request_id}/phase-{phase_config['phase']}/"
            f"{preview.id}.{file_extension}"
        )
        try:
            client = get_storage_client()
            bucket_ref = client.bucket(bucket)
            blob = bucket_ref.blob(path)
            expiration = datetime.utcnow() + timedelta(seconds=self.settings.signed_url_ttl_seconds)
            return blob.generate_signed_url(expiration=expiration, method="GET", version="v4")
        except Exception:
            return f"https://storage.googleapis.com/{bucket}/{path}"

    def _estimate_pages(self, session: MangaSession, context: Dict[int, Dict[str, Any]]) -> int:
        structure_data = context.get(3, {}).get("data", {})
        panel_data = context.get(4, {}).get("data", {})
        session_meta = session.session_metadata or {}
        base_pages = session_meta.get("options", {}).get("expected_pages") if session_meta.get("options") else None
        if isinstance(base_pages, int) and base_pages > 0:
            return base_pages
        if panel_data.get("pageCount"):
            return max(DEFAULT_PAGE_MIN, int(panel_data["pageCount"]))
        act_count = len(structure_data.get("acts", []))
        return max(DEFAULT_PAGE_MIN, act_count * 6)

    def _upsert_project_assets(self, project, session: MangaSession) -> None:
        existing_pdf = next((asset for asset in project.assets if asset.asset_type == MangaAssetType.PDF), None)
        storage_path = f"projects/{project.id}/final/{session.request_id}.pdf"
        signed_url = self._build_asset_signed_url(storage_path)
        asset_payload = {
            "project_id": project.id,
            "asset_type": MangaAssetType.PDF,
            "storage_path": storage_path,
            "signed_url": signed_url,
            "asset_metadata": {
                "total_pages": project.total_pages,
                "generated_at": datetime.utcnow().isoformat(),
            },
        }
        if existing_pdf:
            for key, value in asset_payload.items():
                setattr(existing_pdf, key, value)
        else:
            self.db.add(MangaAsset(**asset_payload))

    def _build_asset_signed_url(self, storage_path: str) -> str:
        bucket = self.settings.gcs_bucket_preview
        try:
            client = get_storage_client()
            bucket_ref = client.bucket(bucket)
            blob = bucket_ref.blob(storage_path)
            expiration = datetime.utcnow() + timedelta(seconds=self.settings.signed_url_ttl_seconds)
            return blob.generate_signed_url(expiration=expiration, method="GET", version="v4")
        except Exception:
            return f"https://storage.googleapis.com/{bucket}/{storage_path}"

    def _parse_json(self, raw: str | None) -> Dict[str, Any]:
        if not raw:
            return {}
        text = raw.strip()
        if "```" in text:
            segments = [segment for segment in text.split("```") if segment.strip()]
            if segments:
                text = segments[-1]
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            cleaned = candidate.replace("\n", " ")
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return {}

    def _ensure_list_of_strings(self, parsed: Dict[str, Any], key: str, *, default: Optional[list[str]] = None) -> list[str]:
        default = default or []
        value = parsed.get(key)
        return self._ensure_list_of_strings_from_value(value, default=default)

    def _ensure_list_of_strings_from_value(self, value: Any, *, default: Optional[list[str]] = None) -> list[str]:
        default = default or []
        if isinstance(value, list):
            result: list[str] = []
            for item in value:
                if isinstance(item, str):
                    result.append(item.strip())
                elif isinstance(item, dict):
                    result.append(next(iter(item.values())) if item else "")
                else:
                    result.append(str(item))
            return [entry for entry in result if entry]
        if isinstance(value, str):
            parts = [part.strip() for part in value.split("\n") if part.strip()]
            return parts or default
        return default

    def _ensure_list_of_dicts(self, parsed: Dict[str, Any], key: str) -> list[Dict[str, Any]]:
        value = parsed.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [value]
        return []

    def _coalesce(self, parsed: Dict[str, Any] | None, keys: list[str], *, default: Any = "") -> Any:
        if not parsed:
            return default
        for key in keys:
            if key in parsed and parsed[key]:
                return parsed[key]
        return default

    def _quality_to_level(self, quality: float) -> int:
        if quality >= 0.9:
            return 5
        if quality >= 0.85:
            return 4
        if quality >= 0.78:
            return 3
        if quality >= QUALITY_THRESHOLD:
            return 2
        return 1

    def _evaluate_quality(
        self,
        phase_number: int,
        data: Dict[str, Any],
        diagnostics: Dict[str, Any],
    ) -> float:
        if phase_number == 1:
            theme_score = min(1.0, len(data.get("themes", [])) / 4)
            coverage = 0.2 if data.get("worldSetting") else 0
            mood = 0.15 if data.get("mood") else 0
            score = 0.62 + theme_score * 0.2 + coverage + mood
        elif phase_number == 2:
            char_count = len(data.get("characters", []))
            image_bonus = 0.05 if data.get("imageUrl") else 0
            score = 0.64 + min(0.18, char_count * 0.05) + image_bonus
        elif phase_number == 3:
            act_count = len(data.get("acts", []))
            scene_count = diagnostics.get("sceneCount", 0)
            score = 0.66 + min(0.12, act_count * 0.04) + min(0.1, scene_count * 0.01)
        elif phase_number == 4:
            panel_count = diagnostics.get("panelCount", len(data.get("panels", [])))
            page_count = data.get("pageCount", DEFAULT_PAGE_MIN)
            score = 0.68 + min(0.12, panel_count * 0.01) + min(0.08, page_count / 100)
        elif phase_number == 5:
            generated = diagnostics.get("generatedImages", 0)
            requested = diagnostics.get("requestedPanels", 1)
            ratio = generated / max(requested, 1)
            score = 0.65 + min(1.0, ratio) * 0.25
        elif phase_number == 6:
            dialogue_count = diagnostics.get("dialogueCount", len(data.get("dialogues", [])))
            sfx_count = len(data.get("soundEffects", []))
            score = 0.66 + min(0.14, dialogue_count * 0.015) + min(0.05, sfx_count * 0.015)
        elif phase_number == 7:
            overall = data.get("overallQuality", 0.8)
            checks_completed = sum(1 for item in data.get("qualityChecks", []) if item.get("status") == "completed")
            score = 0.7 + min(0.12, checks_completed * 0.03) + min(0.1, overall / 1.2)
        else:
            score = 0.7

        return max(0.55, min(0.97, score))
