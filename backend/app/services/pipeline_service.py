from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.core.clients import get_storage_client
from app.services.realtime_hub import build_event, realtime_hub
from app.services.vertex_ai_service import get_vertex_service

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
            build_event("session_start", sessionId=str(session.request_id)),
        )

        project = session.project
        phase_context: Dict[int, Dict[str, object]] = {}
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

            try:
                phase_payload = await self._process_phase(session, phase_config, phase_context)
            except Exception as exc:  # pragma: no cover - error path
                logger.exception("Phase %s failed", phase_number)
                await self._handle_failure(session, project, phase_number, str(exc))
                return

            phase_result = PhaseResult(
                session_id=session.id,
                phase=phase_number,
                status="completed",
                content=phase_payload,
                quality_score=0.85,
            )
            self.db.add(phase_result)
            await self.db.flush()

            preview = PreviewVersion(
                session_id=session.id,
                phase=phase_number,
                version_data=phase_payload.get("preview"),
                quality_level=4,
                quality_score=0.85,
            )
            self.db.add(preview)
            await self.db.flush()

            cache_entry = PreviewCacheMetadata(
                cache_key=f"preview/{session.request_id}/phase-{phase_number}/v{preview.created_at.timestamp():.0f}",
                version_id=preview.id,
                phase=phase_number,
                quality_level=4,
                signed_url=self._build_signed_url(session, phase_config, preview),
                content_type="application/json",
                expires_at=datetime.utcnow() + timedelta(seconds=self.settings.signed_url_ttl_seconds),
            )
            self.db.add(cache_entry)

            if phase_number == 5:
                image_record = GeneratedImage(
                    session_id=session.id,
                    phase=phase_number,
                    storage_path=f"projects/{session.project_id}/sessions/{session.request_id}/phase-{phase_number}.png",
                    signed_url=self._build_signed_url(session, phase_config, preview, file_extension="png"),
                    image_metadata={"style": (project.style if project else None), "quality_score": 0.82},
                )
                self.db.add(image_record)

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
            project.total_pages = self._estimate_pages(session)
            project.updated_at = datetime.utcnow()
            self._upsert_project_assets(project, session)
        await self.db.flush()

        await realtime_hub.publish(
            session.request_id,
            build_event(
                "session_complete",
                results={"project_id": str(session.project_id) if session.project_id else None},
                sessionId=str(session.request_id),
            ),
        )

    async def _get_session(self, request_id: UUID) -> Optional[MangaSession]:
        result = await self.db.execute(
            select(MangaSession).where(MangaSession.request_id == request_id)
        )
        return result.scalar_one_or_none()

    def _generate_phase_payload(self, session: MangaSession, phase_config: Dict[str, object]) -> Dict[str, object]:
        phase = phase_config["phase"]
        label = phase_config["label"]
        session_meta = session.session_metadata or {}
        title = session_meta.get("title", "Untitled")
        narrative_snippet = (session_meta.get("text", "") or "")[:280]
        return {
            "phase": phase,
            "name": phase_config["name"],
            "summary": f"{label} 完了: {title}",
            "preview": {
                "title": title,
                "phase": phase,
                "generated_at": datetime.utcnow().isoformat(),
                "key": phase_config["preview_key"],
                "details": {
                    "highlight": narrative_snippet,
                    "quality_score": 0.82,
                },
            },
        }

    def _build_signed_url(
        self,
        session: MangaSession,
        phase_config: Dict[str, object],
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

    def _estimate_pages(self, session: MangaSession) -> int:
        previews = len(session.preview_versions)
        session_meta = session.session_metadata or {}
        base_pages = session_meta.get("options", {}).get("expected_pages") if session_meta.get("options") else None
        if isinstance(base_pages, int) and base_pages > 0:
            return base_pages
        return max(8, previews)

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

    async def _process_phase(
        self,
        session: MangaSession,
        phase_config: Dict[str, object],
        context: Dict[int, Dict[str, object]],
    ) -> Dict[str, object]:
        phase_number = phase_config["phase"]
        session_meta = session.session_metadata or {}
        base_prompt = session_meta.get("text", "")

        if phase_number == 1:
            prompt = f"Analyze the following manga story concept and summarize key themes, setting, and tone:\n{base_prompt}"
            concept_text = await self.vertex_service.generate_text(prompt)
            payload = {
                "phase": phase_number,
                "summary": concept_text,
                "preview": {
                    "type": "text",
                    "content": concept_text,
                    "concepts": concept_text.split("\n"),
                },
            }
        elif phase_number == 2:
            previous = context.get(1, {})
            prompt = (
                "Based on the following concept summary, draft concise character bios (name, role, appearance, personality) "
                "for up to 3 main characters.\n\nConcept Summary:\n"
                f"{previous.get('summary', base_prompt)}"
            )
            characters_text = await self.vertex_service.generate_text(prompt)
            payload = {
                "phase": phase_number,
                "characters": characters_text,
                "preview": {
                    "type": "text",
                    "content": characters_text,
                },
            }
        elif phase_number == 3:
            prompt = (
                "Design a manga story outline with act structure (act, scenes, emotional beats) based on the concept below."
                f"\n\nConcept:\n{context.get(1, {}).get('summary', base_prompt)}\n\nCharacters:\n{context.get(2, {}).get('characters', '')}"
            )
            outline_text = await self.vertex_service.generate_text(prompt)
            payload = {
                "phase": phase_number,
                "outline": outline_text,
                "preview": {
                    "type": "text",
                    "content": outline_text,
                },
            }
        elif phase_number == 4:
            prompt = (
                "Create panel layout guidance (panel count, viewpoint, key action) for the manga outline below."
                f"\n\nOutline:\n{context.get(3, {}).get('outline', base_prompt)}"
            )
            layout_text = await self.vertex_service.generate_text(prompt)
            payload = {
                "phase": phase_number,
                "layout": layout_text,
                "preview": {
                    "type": "text",
                    "content": layout_text,
                },
            }
        elif phase_number == 5:
            prompt = (
                "Generate a detailed visual description for a key scene from the outline."
                f"\n\nOutline:\n{context.get(3, {}).get('outline', base_prompt)}"
            )
            images = await self.vertex_service.generate_image(prompt)
            payload = {
                "phase": phase_number,
                "images": images,
                "preview": {
                    "type": "image",
                    "content": images,
                },
            }
        elif phase_number == 6:
            prompt = (
                "Draft dialogue lines for the key characters in the outline below. Include speaker and dialogue text."
                f"\n\nOutline:\n{context.get(3, {}).get('outline', base_prompt)}"
            )
            dialogue_text = await self.vertex_service.generate_text(prompt)
            payload = {
                "phase": phase_number,
                "dialogue": dialogue_text,
                "preview": {
                    "type": "text",
                    "content": dialogue_text,
                },
            }
        else:
            prompt = (
                "Summarize the final manga deliverable, highlighting themes, character arcs, and visual direction."
                f"\n\nOutline:\n{context.get(3, {}).get('outline', base_prompt)}"
            )
            final_text = await self.vertex_service.generate_text(prompt)
            payload = {
                "phase": phase_number,
                "summary": final_text,
                "preview": {
                    "type": "text",
                    "content": final_text,
                },
            }

        return payload

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
