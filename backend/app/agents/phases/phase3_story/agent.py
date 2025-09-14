"""Phase 3 Agent: Story Structure and Scene Analysis."""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from app.agents.base.agent import BaseAgent
from app.agents.base.validator import BaseValidator
from app.core.logging import LoggerMixin
from app.core.config import settings

from .schemas import (
    StoryAnalysisInput,
    StoryAnalysisOutput,
    StoryStructure,
    PlotProgression,
    SceneDetails,
    NarrativeFlow,
    CharacterArc,
    ThemeDevelopment,
    TensionCurve,
    EmotionalJourney,
    ConflictAnalysis,
    ThemeIntegration,
    StoryStructureType,
    PacingType,
    STORY_STRUCTURE_TEMPLATES,
    GENRE_PACING_PATTERNS
)
from .validator import Phase3Validator
from .processors.story_analyzer import StoryAnalyzer


class Phase3StoryAgent(BaseAgent):
    """Phase 3 Agent: Story Structure Analysis and Scene Breakdown."""

    def __init__(self):
        super().__init__(
            phase_number=3,
            phase_name="ストーリー構造・場面分析",
            timeout_seconds=settings.phase_timeouts.get(3, 180)
        )

        # Initialize processors
        self.story_analyzer = StoryAnalyzer()

        # Story structure templates reference
        self.structure_templates = STORY_STRUCTURE_TEMPLATES
        self.genre_pacing = GENRE_PACING_PATTERNS

        # Default scene count ranges by genre
        self.genre_scene_ranges = {
            "action": (8, 20),
            "romance": (6, 15),
            "mystery": (10, 18),
            "fantasy": (8, 22),
            "slice_of_life": (5, 12),
            "sci_fi": (8, 20),
            "horror": (8, 16),
            "general": (6, 18)
        }

        self.logger.info("Phase 3 Story Agent initialized with structured architecture")

    def _create_validator(self) -> BaseValidator:
        """Create Phase 3 specific validator."""
        return Phase3Validator()

    async def _generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate AI prompt for story structure analysis."""

        # Extract Phase 1 and Phase 2 results
        if not previous_results or 1 not in previous_results or 2 not in previous_results:
            raise ValueError("Phase 1 and Phase 2 results required for story analysis")

        phase1_result = previous_results[1]
        phase2_result = previous_results[2]

        # Extract key information from Phase 1
        genre_analysis = phase1_result.get("genre_analysis", {})
        theme_analysis = phase1_result.get("theme_analysis", {})
        tone = phase1_result.get("tone", "neutral")
        target_audience = phase1_result.get("target_audience", "general")
        estimated_pages = phase1_result.get("estimated_pages", 20)

        primary_genre = genre_analysis.get("primary_genre", "general")
        main_themes = theme_analysis.get("main_themes", [])

        # Extract character information from Phase 2
        characters = phase2_result.get("characters", [])
        character_relationships = phase2_result.get("relationships", [])

        # Build comprehensive prompt
        prompt = f"""# ストーリー構造・場面分析指示書

## 基本情報
- 主要ジャンル: {primary_genre}
- メインテーマ: {', '.join(main_themes[:3]) if main_themes else '未指定'}
- ターゲット読者: {target_audience}
- 作品の雰囲気: {tone}
- 推定ページ数: {estimated_pages}ページ

## キャラクター情報
キャラクター数: {len(characters)}人
主要キャラクター: {', '.join([c.get('name', '無名') for c in characters[:3]])}

## 指示内容
以下のJSON形式でストーリー構造と場面分析を生成してください：

{{
    "story_structure": {{
        "type": "three_act|kishootenketsu|hero_journey|five_act|custom",
        "acts": [
            {{
                "act_number": 数値,
                "title": "幕のタイトル",
                "purpose": "この幕の役割と目的",
                "scene_range": [シーン番号のリスト],
                "page_range": [ページ番号のリスト],
                "duration_percentage": 0.0-1.0,
                "key_events": ["主要な出来事のリスト"],
                "character_arcs": ["この幕でのキャラクター展開"],
                "themes_explored": ["探求されるテーマのリスト"]
            }}
        ],
        "total_acts": 幕の総数,
        "structure_rationale": "この構造を選んだ理由",
        "adaptation_notes": ["構造適用時の注意点のリスト"]
    }},
    "plot_progression": {{
        "opening": "物語の開始部分",
        "inciting_incident": "きっかけとなる出来事",
        "rising_action": ["上昇アクションの展開リスト"],
        "climax": "物語のクライマックス",
        "falling_action": ["下降アクションの展開リスト"],
        "resolution": "物語の解決",
        "progression_notes": ["プロット展開の注意点"]
    }},
    "scenes": [
        {{
            "scene_number": シーン番号,
            "pages": [ページ番号のリスト],
            "page_count": ページ数,
            "title": "シーンタイトル",
            "purpose": "exposition|inciting_incident|rising_action|climax|falling_action|resolution|character_development|world_building",
            "pacing": "slow|medium|fast|very_fast|variable",
            "emotional_beat": "joy|sadness|anger|fear|surprise|excitement|tension|relief|hope|despair|triumph|mystery|romance|conflict|peace",
            "visual_style": "action|dialogue|atmospheric|dynamic|intimate|panoramic|close_up|montage",
            "transition_type": "cut|fade|dissolve|wipe|match_cut|jump_cut|cross_fade|time_jump|location_change|perspective_shift",
            "key_story_function": "setup|catalyst|debate|break_into_two|b_story|fun_and_games|midpoint|bad_guys_close_in|all_is_lost|dark_night|break_into_three|finale|final_image",
            "location": "シーンの場所",
            "time_of_day": "時間帯",
            "characters_present": ["登場キャラクター名のリスト"],
            "key_dialogue": ["重要な台詞のリスト"],
            "visual_elements": ["視覚的要素のリスト"],
            "mood": "シーンの雰囲気",
            "conflict_elements": ["対立要素のリスト"]
        }}
    ],
    "narrative_flow": {{
        "character_arcs": [
            {{
                "character_name": "キャラクター名",
                "arc_type": "成長アーク|対立アーク|復讐アーク等",
                "starting_state": "開始時の状態",
                "key_turning_points": ["重要な転換点のリスト"],
                "ending_state": "終了時の状態",
                "growth_trajectory": "成長の軌跡",
                "scene_involvement": [登場シーン番号のリスト]
            }}
        ],
        "theme_development": [
            {{
                "theme_name": "テーマ名",
                "introduction_scene": 導入シーン番号,
                "development_scenes": [展開シーン番号のリスト],
                "resolution_scene": 解決シーン番号,
                "thematic_elements": ["テーマ表現要素のリスト"],
                "symbol_usage": ["使用されるシンボルのリスト"]
            }}
        ],
        "tension_curve": {{
            "points": [
                {{
                    "scene_number": シーン番号,
                    "tension_level": 0.0-1.0,
                    "tension_type": "緊張の種類",
                    "description": "この時点での緊張の説明"
                }}
            ],
            "peak_tension_scene": 最高緊張シーン番号,
            "lowest_tension_scene": 最低緊張シーン番号,
            "overall_pattern": "全体的な緊張パターンの説明",
            "pacing_recommendations": ["ペーシング推奨事項のリスト"]
        }},
        "emotional_journey": [
            {{
                "scene_number": シーン番号,
                "target_emotion": "目標とする読者感情",
                "emotional_intensity": 0.0-1.0,
                "emotional_trigger": "感情のトリガー",
                "transition_to_next": "次のシーンへの感情遷移"
            }}
        ],
        "pacing_analysis": {{
            "overall_rhythm": "全体的なリズムの説明",
            "pacing_match_score": 0.0-1.0,
            "flow_issues": ["ペーシングの問題点のリスト"],
            "recommendations": ["改善推奨事項のリスト"],
            "genre_alignment": "ジャンルとの整合性"
        }}
    }},
    "total_scenes": シーンの総数,
    "story_complexity_score": 0.0-1.0,
    "pacing_consistency_score": 0.0-1.0,
    "character_integration_score": 0.0-1.0,
    "conflict_analysis": {{
        "primary_conflicts": ["主要な対立のリスト"],
        "conflict_types": ["対立の種類のリスト"],
        "escalation_pattern": "対立の段階的発展パターン",
        "resolution_pattern": "対立の解決パターン",
        "conflict_distribution": {{"シーン番号": ["そのシーンの対立のリスト"]}}
    }},
    "theme_integration": {{
        "themes_identified": ["確認されたテーマのリスト"],
        "integration_score": 0.0-1.0,
        "thematic_consistency": 0.0-1.0,
        "weak_integration_scenes": [テーマ統合の弱いシーン番号のリスト],
        "recommendations": ["テーマ統合改善推奨事項のリスト"]
    }}
}}

## 要求事項
1. ジャンル「{primary_genre}」に適したストーリー構造を選択してください
2. {estimated_pages}ページに適したシーン数（{self.genre_scene_ranges.get(primary_genre, (6, 18))[0]}-{self.genre_scene_ranges.get(primary_genre, (6, 18))[1]}シーン程度）で構成してください
3. テーマ「{', '.join(main_themes[:2]) if main_themes else 'なし'}」を物語全体を通じて発展させてください
4. キャラクター{len(characters)}人の成長と関係性を適切に配置してください
5. ターゲット読者「{target_audience}」に適したペーシングを維持してください
6. 視覚的なマンガ表現を考慮したシーン構成にしてください
7. 緊張と緩和のバランスを取った感情の流れを作成してください
8. 各シーンの目的と機能を明確にしてください

上記JSON形式で回答してください。"""

        return prompt

    async def _process_ai_response(
        self,
        ai_response: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process AI response into structured output."""

        # Extract previous results for fallback
        previous_results = input_data.get("previous_results", {})
        phase1_result = previous_results.get(1, {}) if previous_results else {}
        phase2_result = previous_results.get(2, {}) if previous_results else {}

        try:
            # Try to parse AI response as JSON
            ai_data = json.loads(ai_response)

            # Build structured output using processors
            story_output = await self._build_story_output(ai_data, phase1_result, phase2_result)

            return story_output

        except json.JSONDecodeError:
            # Fallback to processor-based analysis if AI response parsing fails
            self.logger.warning("AI response parsing failed, falling back to processor-based analysis")
            return await self._processor_based_analysis(phase1_result, phase2_result)

    async def _build_story_output(
        self,
        ai_data: Dict[str, Any],
        phase1_result: Dict[str, Any],
        phase2_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build structured story output from AI data."""

        # Extract basic information
        genre_analysis = phase1_result.get("genre_analysis", {})
        primary_genre = genre_analysis.get("primary_genre", "general")
        estimated_pages = phase1_result.get("estimated_pages", 20)
        characters = phase2_result.get("characters", [])

        # Process story structure
        story_structure_data = ai_data.get("story_structure", {})
        story_structure = self._process_story_structure(story_structure_data, estimated_pages)

        # Process plot progression
        plot_data = ai_data.get("plot_progression", {})
        plot_progression = self._process_plot_progression(plot_data)

        # Process scenes
        scenes_data = ai_data.get("scenes", [])
        scenes = self._process_scenes(scenes_data, estimated_pages)

        # Process narrative flow
        narrative_data = ai_data.get("narrative_flow", {})
        narrative_flow = self._process_narrative_flow(narrative_data, characters, len(scenes))

        # Process analysis data
        conflict_analysis = self._process_conflict_analysis(ai_data.get("conflict_analysis", {}))
        theme_integration = self._process_theme_integration(ai_data.get("theme_integration", {}))

        # Create scene summaries and visual requirements for next phases
        scene_summaries, visual_requirements, character_usage = self._create_next_phase_data(scenes, characters)

        # Build final output
        story_output = {
            "story_structure": story_structure,
            "plot_progression": plot_progression,
            "scenes": scenes,
            "narrative_flow": narrative_flow,
            "total_scenes": len(scenes),
            "story_complexity_score": ai_data.get("story_complexity_score", 0.6),
            "pacing_consistency_score": ai_data.get("pacing_consistency_score", 0.7),
            "character_integration_score": ai_data.get("character_integration_score", 0.8),
            "conflict_analysis": conflict_analysis,
            "theme_integration": theme_integration,
            "scene_summaries": scene_summaries,
            "visual_requirements": visual_requirements,
            "character_usage": character_usage,
            "generation_timestamp": datetime.utcnow().isoformat(),
            "ai_model_used": "gpt-4o-mini",  # In production, this would be actual model
            "processing_time": 3.2  # This would be calculated
        }

        return story_output

    def _process_story_structure(self, structure_data: Dict[str, Any], estimated_pages: int) -> Dict[str, Any]:
        """Process story structure data."""

        acts_data = structure_data.get("acts", [])
        processed_acts = []

        for act_data in acts_data:
            processed_act = {
                "act_number": act_data.get("act_number", 1),
                "title": act_data.get("title", "無題"),
                "purpose": act_data.get("purpose", "物語の展開"),
                "scene_range": act_data.get("scene_range", []),
                "page_range": act_data.get("page_range", []),
                "duration_percentage": act_data.get("duration_percentage", 0.33),
                "key_events": act_data.get("key_events", []),
                "character_arcs": act_data.get("character_arcs", []),
                "themes_explored": act_data.get("themes_explored", [])
            }
            processed_acts.append(processed_act)

        return {
            "type": structure_data.get("type", "three_act"),
            "acts": processed_acts,
            "total_acts": len(processed_acts),
            "structure_rationale": structure_data.get("structure_rationale", "選択された構造は物語に適している"),
            "adaptation_notes": structure_data.get("adaptation_notes", [])
        }

    def _process_plot_progression(self, plot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process plot progression data."""

        return {
            "opening": plot_data.get("opening", "物語の始まり"),
            "inciting_incident": plot_data.get("inciting_incident", "きっかけとなる出来事"),
            "rising_action": plot_data.get("rising_action", ["展開の積み重ね"]),
            "climax": plot_data.get("climax", "物語の頂点"),
            "falling_action": plot_data.get("falling_action", ["クライマックス後の展開"]),
            "resolution": plot_data.get("resolution", "物語の結末"),
            "progression_notes": plot_data.get("progression_notes", [])
        }

    def _process_scenes(self, scenes_data: List[Dict[str, Any]], estimated_pages: int) -> List[Dict[str, Any]]:
        """Process scenes data."""

        processed_scenes = []

        for scene_data in scenes_data:
            processed_scene = {
                "scene_number": scene_data.get("scene_number", 1),
                "pages": scene_data.get("pages", [1]),
                "page_count": scene_data.get("page_count", 1),
                "title": scene_data.get("title", "無題シーン"),
                "purpose": scene_data.get("purpose", "exposition"),
                "pacing": scene_data.get("pacing", "medium"),
                "emotional_beat": scene_data.get("emotional_beat", "tension"),
                "visual_style": scene_data.get("visual_style", "dialogue"),
                "transition_type": scene_data.get("transition_type", "cut"),
                "key_story_function": scene_data.get("key_story_function", "setup"),
                "location": scene_data.get("location", "不明"),
                "time_of_day": scene_data.get("time_of_day", "不定"),
                "characters_present": scene_data.get("characters_present", []),
                "key_dialogue": scene_data.get("key_dialogue", []),
                "visual_elements": scene_data.get("visual_elements", []),
                "mood": scene_data.get("mood", "neutral"),
                "conflict_elements": scene_data.get("conflict_elements", [])
            }
            processed_scenes.append(processed_scene)

        return processed_scenes

    def _process_narrative_flow(
        self,
        narrative_data: Dict[str, Any],
        characters: List[Dict[str, Any]],
        scene_count: int
    ) -> Dict[str, Any]:
        """Process narrative flow data."""

        # Process character arcs
        character_arcs_data = narrative_data.get("character_arcs", [])
        processed_arcs = []

        for arc_data in character_arcs_data:
            processed_arc = {
                "character_name": arc_data.get("character_name", "無名"),
                "arc_type": arc_data.get("arc_type", "サポートアーク"),
                "starting_state": arc_data.get("starting_state", "開始状態"),
                "key_turning_points": arc_data.get("key_turning_points", []),
                "ending_state": arc_data.get("ending_state", "終了状態"),
                "growth_trajectory": arc_data.get("growth_trajectory", "成長の軌跡"),
                "scene_involvement": arc_data.get("scene_involvement", [1])
            }
            processed_arcs.append(processed_arc)

        # Process theme development
        theme_dev_data = narrative_data.get("theme_development", [])
        processed_themes = []

        for theme_data in theme_dev_data:
            processed_theme = {
                "theme_name": theme_data.get("theme_name", "テーマ"),
                "introduction_scene": theme_data.get("introduction_scene", 1),
                "development_scenes": theme_data.get("development_scenes", []),
                "resolution_scene": theme_data.get("resolution_scene", scene_count),
                "thematic_elements": theme_data.get("thematic_elements", []),
                "symbol_usage": theme_data.get("symbol_usage", [])
            }
            processed_themes.append(processed_theme)

        # Process tension curve
        tension_data = narrative_data.get("tension_curve", {})
        tension_points = []

        for point_data in tension_data.get("points", []):
            point = {
                "scene_number": point_data.get("scene_number", 1),
                "tension_level": point_data.get("tension_level", 0.5),
                "tension_type": point_data.get("tension_type", "状況的緊張"),
                "description": point_data.get("description", "緊張の説明")
            }
            tension_points.append(point)

        tension_curve = {
            "points": tension_points,
            "peak_tension_scene": tension_data.get("peak_tension_scene", scene_count // 2),
            "lowest_tension_scene": tension_data.get("lowest_tension_scene", 1),
            "overall_pattern": tension_data.get("overall_pattern", "自然な起伏"),
            "pacing_recommendations": tension_data.get("pacing_recommendations", [])
        }

        # Process emotional journey
        emotional_data = narrative_data.get("emotional_journey", [])
        processed_emotional = []

        for emotion_data in emotional_data:
            emotion = {
                "scene_number": emotion_data.get("scene_number", 1),
                "target_emotion": emotion_data.get("target_emotion", "tension"),
                "emotional_intensity": emotion_data.get("emotional_intensity", 0.5),
                "emotional_trigger": emotion_data.get("emotional_trigger", "状況変化"),
                "transition_to_next": emotion_data.get("transition_to_next", "自然な流れ")
            }
            processed_emotional.append(emotion)

        # Process pacing analysis
        pacing_data = narrative_data.get("pacing_analysis", {})
        pacing_analysis = {
            "overall_rhythm": pacing_data.get("overall_rhythm", "バランスの取れたリズム"),
            "pacing_match_score": pacing_data.get("pacing_match_score", 0.7),
            "flow_issues": pacing_data.get("flow_issues", []),
            "recommendations": pacing_data.get("recommendations", []),
            "genre_alignment": pacing_data.get("genre_alignment", "ジャンルに適している")
        }

        return {
            "character_arcs": processed_arcs,
            "theme_development": processed_themes,
            "tension_curve": tension_curve,
            "emotional_journey": processed_emotional,
            "pacing_analysis": pacing_analysis
        }

    def _process_conflict_analysis(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process conflict analysis data."""

        return {
            "primary_conflicts": conflict_data.get("primary_conflicts", ["主人公vs状況"]),
            "conflict_types": conflict_data.get("conflict_types", ["内的対立", "外的対立"]),
            "escalation_pattern": conflict_data.get("escalation_pattern", "段階的な激化"),
            "resolution_pattern": conflict_data.get("resolution_pattern", "協力による解決"),
            "conflict_distribution": conflict_data.get("conflict_distribution", {})
        }

    def _process_theme_integration(self, theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process theme integration data."""

        return {
            "themes_identified": theme_data.get("themes_identified", ["成長", "友情"]),
            "integration_score": theme_data.get("integration_score", 0.8),
            "thematic_consistency": theme_data.get("thematic_consistency", 0.7),
            "weak_integration_scenes": theme_data.get("weak_integration_scenes", []),
            "recommendations": theme_data.get("recommendations", [])
        }

    def _create_next_phase_data(
        self,
        scenes: List[Dict[str, Any]],
        characters: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], Dict[str, List[int]]]:
        """Create data for next phases."""

        # Scene summaries
        scene_summaries = []
        for scene in scenes:
            summary = {
                "scene_number": str(scene["scene_number"]),
                "title": scene["title"],
                "brief_description": f"{scene['purpose']}のシーン - {scene['mood']}"
            }
            scene_summaries.append(summary)

        # Visual requirements per scene
        visual_requirements = []
        for scene in scenes:
            visual_req = {
                "scene_number": scene["scene_number"],
                "visual_style": scene["visual_style"],
                "location": scene["location"],
                "mood": scene["mood"],
                "characters_present": scene["characters_present"],
                "visual_elements": scene["visual_elements"],
                "pacing": scene["pacing"]
            }
            visual_requirements.append(visual_req)

        # Character usage by scene
        character_usage = {}
        for char in characters:
            char_name = char.get("name", "無名")
            character_usage[char_name] = []

        for scene in scenes:
            chars_present = scene.get("characters_present", [])
            for char_name in chars_present:
                if char_name in character_usage:
                    character_usage[char_name].append(scene["scene_number"])

        return scene_summaries, visual_requirements, character_usage

    async def _processor_based_analysis(
        self,
        phase1_result: Dict[str, Any],
        phase2_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback processor-based analysis when AI parsing fails."""

        # Extract necessary data
        genre_analysis = phase1_result.get("genre_analysis", {})
        theme_analysis = phase1_result.get("theme_analysis", {})
        estimated_pages = phase1_result.get("estimated_pages", 20)
        characters = phase2_result.get("characters", [])

        primary_genre = genre_analysis.get("primary_genre", "general")
        main_themes = theme_analysis.get("main_themes", [])

        # Use story analyzer
        story_structure = await self.story_analyzer.analyze_story_structure(
            genre=primary_genre,
            themes=main_themes,
            estimated_pages=estimated_pages,
            characters=characters
        )

        plot_progression = await self.story_analyzer.generate_plot_progression(
            story_structure=story_structure,
            themes=main_themes,
            characters=characters
        )

        scenes = await self.story_analyzer.create_scene_breakdown(
            story_structure=story_structure,
            plot_progression=plot_progression,
            estimated_pages=estimated_pages,
            genre=primary_genre
        )

        character_arcs = await self.story_analyzer.analyze_character_arcs(
            characters=characters,
            scenes=scenes,
            themes=main_themes
        )

        tension_curve = await self.story_analyzer.generate_tension_curve(scenes)

        # Convert to dict format
        scenes_dict = [scene.dict() if hasattr(scene, 'dict') else scene for scene in scenes]
        character_arcs_dict = [arc.dict() if hasattr(arc, 'dict') else arc for arc in character_arcs]

        # Create narrative flow
        narrative_flow = {
            "character_arcs": character_arcs_dict,
            "theme_development": [],
            "tension_curve": tension_curve.dict() if hasattr(tension_curve, 'dict') else tension_curve,
            "emotional_journey": [],
            "pacing_analysis": {
                "overall_rhythm": f"{primary_genre}ジャンルに適したリズム",
                "pacing_match_score": 0.7,
                "flow_issues": [],
                "recommendations": ["適度な緩急をつける"],
                "genre_alignment": "ジャンルに適している"
            }
        }

        # Create next phase data
        scene_summaries, visual_requirements, character_usage = self._create_next_phase_data(scenes_dict, characters)

        # Build output
        story_output = {
            "story_structure": story_structure.dict() if hasattr(story_structure, 'dict') else story_structure,
            "plot_progression": plot_progression.dict() if hasattr(plot_progression, 'dict') else plot_progression,
            "scenes": scenes_dict,
            "narrative_flow": narrative_flow,
            "total_scenes": len(scenes_dict),
            "story_complexity_score": 0.6,
            "pacing_consistency_score": 0.7,
            "character_integration_score": 0.8,
            "conflict_analysis": {
                "primary_conflicts": ["主人公vs状況"],
                "conflict_types": ["内的対立", "外的対立"],
                "escalation_pattern": "段階的な激化",
                "resolution_pattern": "協力による解決",
                "conflict_distribution": {}
            },
            "theme_integration": {
                "themes_identified": main_themes,
                "integration_score": 0.7,
                "thematic_consistency": 0.8,
                "weak_integration_scenes": [],
                "recommendations": []
            },
            "scene_summaries": scene_summaries,
            "visual_requirements": visual_requirements,
            "character_usage": character_usage,
            "generation_timestamp": datetime.utcnow().isoformat(),
            "ai_model_used": "processor_based_fallback",
            "processing_time": 2.8
        }

        return story_output

    async def _generate_preview(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview data for Phase 3."""

        story_structure = output_data.get("story_structure", {})
        scenes = output_data.get("scenes", [])
        narrative_flow = output_data.get("narrative_flow", {})

        preview = {
            "phase_name": "ストーリー構造・場面分析",
            "summary": f"シーン数: {len(scenes)}、構造: {story_structure.get('type', '不明')}",
            "key_insights": [],
            "visual_elements": []
        }

        # Add key insights
        structure_type = story_structure.get("type", "unknown")
        if structure_type:
            preview["key_insights"].append(f"物語構造: {structure_type}")

        total_acts = story_structure.get("total_acts", 0)
        if total_acts:
            preview["key_insights"].append(f"幕構成: {total_acts}幕")

        preview["key_insights"].append(f"総シーン数: {len(scenes)}")

        # Add visual elements
        if scenes:
            pacing_types = [scene.get("pacing", "medium") for scene in scenes]
            pacing_counts = {p: pacing_types.count(p) for p in set(pacing_types)}
            dominant_pacing = max(pacing_counts.keys(), key=lambda k: pacing_counts[k])
            preview["visual_elements"].append(f"主要ペーシング: {dominant_pacing}")

            visual_styles = [scene.get("visual_style", "dialogue") for scene in scenes]
            style_counts = {s: visual_styles.count(s) for s in set(visual_styles)}
            dominant_style = max(style_counts.keys(), key=lambda k: style_counts[k])
            preview["visual_elements"].append(f"主要ビジュアルスタイル: {dominant_style}")

        # Character arc information
        character_arcs = narrative_flow.get("character_arcs", [])
        if character_arcs:
            preview["visual_elements"].append(f"キャラクターアーク: {len(character_arcs)}人")

        return preview

    async def apply_story_feedback(
        self,
        output_data: Dict[str, Any],
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply feedback specifically for story adjustments."""

        feedback_type = feedback.get("type", "general")

        if feedback_type == "scene_modification":
            # Modify specific scene
            scene_number = feedback.get("scene_number")
            modifications = feedback.get("modifications", {})

            scenes = output_data.get("scenes", [])
            for scene in scenes:
                if scene.get("scene_number") == scene_number:
                    for key, value in modifications.items():
                        if key in scene:
                            scene[key] = value
                    scene["last_modified"] = datetime.utcnow().isoformat()
                    break

        elif feedback_type == "structure_adjustment":
            # Adjust story structure
            structure_adjustments = feedback.get("adjustments", {})
            story_structure = output_data.get("story_structure", {})

            for key, value in structure_adjustments.items():
                if key in story_structure:
                    story_structure[key] = value
            story_structure["last_modified"] = datetime.utcnow().isoformat()

        elif feedback_type == "pacing_adjustment":
            # Adjust scene pacing
            pacing_changes = feedback.get("pacing_changes", {})
            scenes = output_data.get("scenes", [])

            for scene_num, new_pacing in pacing_changes.items():
                for scene in scenes:
                    if scene.get("scene_number") == int(scene_num):
                        scene["pacing"] = new_pacing
                        scene["last_modified"] = datetime.utcnow().isoformat()

        # Update modification timestamp
        output_data["last_feedback_applied"] = datetime.utcnow().isoformat()
        output_data["feedback_history"] = output_data.get("feedback_history", [])
        output_data["feedback_history"].append({
            "type": feedback_type,
            "timestamp": datetime.utcnow().isoformat(),
            "feedback": feedback
        })

        return output_data