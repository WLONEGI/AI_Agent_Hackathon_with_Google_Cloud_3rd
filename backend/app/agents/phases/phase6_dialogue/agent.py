"""Phase 6: Dialogue and Text Placement Agent.

This module provides the main agent for Phase 6, which orchestrates dialogue
generation and text placement processing for manga panels.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import asyncio
import time
import logging
import json

from app.agents.base.agent import BaseAgent
from app.core.config import settings

from .schemas import (
    DialoguePlacementInput, DialoguePlacementOutput,
    PanelDialogue, DialogueElement, TextPlacement, BubbleDesign,
    TypographySpecifications, ReadabilityOptimization, DialogueFlowAnalysis,
    TimingAnalysis, QualityMetrics, DialogueGenerationTask
)
from .validator import Phase6Validator
from .processors import DialogueGenerator, TextFormatter


logger = logging.getLogger(__name__)


class Phase6DialogueAgent(BaseAgent):
    """Phase 6 agent for dialogue generation and text placement."""

    def __init__(self):
        """Initialize Phase 6 dialogue agent."""

        super().__init__(
            phase_number=6,
            phase_name="セリフ配置",
            timeout_seconds=settings.phase_timeouts[6]
        )

        # Initialize components
        self.dialogue_generator = DialogueGenerator()
        self.text_formatter = TextFormatter()

    def _create_validator(self):
        """Create Phase 6 specific validator."""
        return Phase6Validator()

    async def _generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate AI prompt for dialogue generation."""

        # Extract previous results context
        story_context = ""
        character_context = ""
        panel_context = ""

        if previous_results:
            # Phase 2 character context
            if 2 in previous_results:
                characters = previous_results[2].get("characters", [])
                if characters:
                    character_names = [c.get("name", "") for c in characters]
                    character_context = f"登場キャラクター: {', '.join(character_names[:5])}"

            # Phase 3 story context
            if 3 in previous_results:
                story_structure = previous_results[3].get("story_structure", {})
                if story_structure:
                    story_context = f"ストーリー構造: {story_structure.get('total_acts', 0)}幕構成"

            # Phase 4 panel context
            if 4 in previous_results:
                pages = previous_results[4].get("pages", [])
                if pages:
                    total_panels = sum(len(page.get("panels", [])) for page in pages)
                    panel_context = f"総パネル数: {total_panels}"

        prompt = f"""
以下の情報をもとに、マンガパネルのセリフと配置を生成してください。

コンテキスト情報:
- {character_context}
- {story_context}
- {panel_context}

要求事項:
1. 各パネルに適切なセリフを配置
2. キャラクターの個性を反映した台詞
3. 読みやすいテキスト配置
4. 吹き出しのデザイン指定
5. 日本語の縦書き・横書き考慮

出力形式:
- JSON形式で返答
- panel_dialogues配列に各パネルの情報
- dialogue_elements配列にセリフ詳細
- text_placement情報を含む

入力データ: {input_data}
"""
        return prompt.strip()

    async def _process_ai_response(
        self,
        ai_response: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process AI response into structured output."""

        try:
            # Try to extract JSON from the response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                parsed_data = json.loads(json_str)

                # Process with actual dialogue generation based on AI suggestions
                return await self._generate_full_dialogue_output(parsed_data, input_data)

            else:
                raise ValueError("No valid JSON found in AI response")

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse AI response: {e}")
            # Generate fallback output
            return await self._generate_fallback_output(input_data)

    async def _generate_full_dialogue_output(
        self,
        ai_suggestions: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate complete dialogue output based on AI suggestions and input data."""

        # Get accumulated context with all previous phase results
        accumulated_context = input_data.get("accumulated_context", {})
        previous_results = accumulated_context.get("previous_results", {})

        # Extract data from previous phases
        phase3_result = previous_results.get(3, {}) if previous_results else {}
        phase4_result = previous_results.get(4, {}) if previous_results else {}
        phase5_result = previous_results.get(5, {}) if previous_results else {}

        # Get story structure and scenes from phase 3
        scenes = phase3_result.get("scenes", [])
        characters = phase3_result.get("characters", [])

        # Get panel layouts from phase 4
        pages = phase4_result.get("pages", [])
        panel_specifications = []
        for page in pages:
            for panel in page.get("panels", []):
                panel_specifications.append(panel)

        # Get generated images from phase 5
        generated_images = phase5_result.get("generated_images", [])

        # Validate required data
        if not scenes:
            self.logger.warning("No scenes found from Phase 3, using minimal dialogue")
            scenes = [{"scene_number": 1, "description": "Default scene"}]

        if not panel_specifications:
            self.logger.warning("No panel specifications found from Phase 4, creating default panels")
            panel_specifications = [{"panel_id": f"panel_{i}", "scene_number": 1} for i in range(4)]

        # Step 1: Generate dialogue content
        dialogue_content = await self._generate_dialogue_content(
            scenes, characters, panel_specifications, ai_suggestions
        )

        # Step 2: Create text placements
        text_placements = await self.text_formatter.create_text_placements(
            dialogue_content, panel_specifications, generated_images
        )

        # Step 3: Generate bubble designs
        speech_bubbles = await self.text_formatter.generate_bubble_designs(
            text_placements
        )

        # Step 4: Generate typography specifications
        genre = input_data.get("genre", "slice_of_life")
        typography_specs = await self.text_formatter.generate_typography_specifications(
            text_placements, genre
        )

        # Step 5: Analyze readability
        readability_optimization = await self.text_formatter.analyze_readability(
            text_placements, panel_specifications
        )

        # Step 6: Analyze timing and flow
        timing_analysis = self._analyze_dialogue_timing(dialogue_content)
        dialogue_flow_analysis = self._analyze_dialogue_flow(
            dialogue_content, scenes, characters
        )

        # Step 7: Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(
            dialogue_content, text_placements, readability_optimization,
            dialogue_flow_analysis, timing_analysis
        )

        # Step 8: Generate summary statistics
        summary_stats = self._calculate_summary_statistics(
            dialogue_content, text_placements
        )

        # Return structured output
        return {
            "dialogue_content": [d.dict() if hasattr(d, 'dict') else d for d in dialogue_content],
            "dialogue_placement": [t.dict() if hasattr(t, 'dict') else t for t in text_placements],
            "speech_bubbles": [s.dict() if hasattr(s, 'dict') else s for s in speech_bubbles],
            "timing_analysis": timing_analysis.dict() if hasattr(timing_analysis, 'dict') else timing_analysis,
            "typography_specifications": typography_specs.dict() if hasattr(typography_specs, 'dict') else typography_specs,
            "readability_optimization": readability_optimization.dict() if hasattr(readability_optimization, 'dict') else readability_optimization,
            "dialogue_flow_analysis": dialogue_flow_analysis.dict() if hasattr(dialogue_flow_analysis, 'dict') else dialogue_flow_analysis,
            "quality_metrics": quality_metrics.dict() if hasattr(quality_metrics, 'dict') else quality_metrics,
            "total_dialogue_count": summary_stats["total_dialogue_count"],
            "average_words_per_panel": summary_stats["average_words_per_panel"],
            "dialogue_distribution": summary_stats["dialogue_distribution"],
            "reading_flow": summary_stats["reading_flow"],
            "panels_processed": len(panel_specifications),
            "success_rate": summary_stats["success_rate"]
        }

    async def _generate_fallback_output(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback output when AI response parsing fails."""

        # Get accumulated context with all previous phase results
        accumulated_context = input_data.get("accumulated_context", {})
        previous_results = accumulated_context.get("previous_results", {})

        # Extract basic data
        phase4_result = previous_results.get(4, {}) if previous_results else {}
        pages = phase4_result.get("pages", [])
        total_panels = sum(len(page.get("panels", [])) for page in pages) if pages else 4

        # Create minimal dialogue content
        dialogue_content = []
        for i in range(min(total_panels, 4)):
            dialogue_content.append(PanelDialogue(
                panel_id=f"panel_{i}",
                scene_number=1,
                dialogue_elements=[
                    DialogueElement(
                        element_id=f"dialogue_{i}_1",
                        text="...",
                        speaker="Character",
                        dialogue_type="speech",
                        speech_pattern="normal",
                        emotional_tone="neutral",
                        estimated_syllables=3
                    )
                ] if i % 2 == 0 else [],
                narration=None,
                total_text_elements=1 if i % 2 == 0 else 0,
                estimated_reading_time=1.0 if i % 2 == 0 else 0.0
            ))

        # Create minimal metrics
        timing_analysis = TimingAnalysis(
            total_estimated_reading_time=float(len(dialogue_content)),
            average_reading_time_per_panel=1.0,
            reading_speed_analysis={},
            pacing_recommendations=["フォールバック生成を使用"],
            syllable_distribution={}
        )

        quality_metrics = QualityMetrics(
            dialogue_density_score=0.5,
            readability_score=0.5,
            integration_score=0.5,
            narrative_coherence_score=0.5,
            character_voice_consistency_score=0.5,
            pacing_alignment_score=0.5,
            overall_quality_score=0.5
        )

        return {
            "dialogue_content": [d.dict() for d in dialogue_content],
            "dialogue_placement": [],
            "speech_bubbles": [],
            "timing_analysis": timing_analysis.dict(),
            "typography_specifications": {},
            "readability_optimization": {
                "overall_readability_score": 0.5,
                "identified_issues": [],
                "optimization_suggestions": [],
                "reading_flow_analysis": {},
                "text_density_analysis": {},
                "visual_interference_analysis": {"safe_placements": 0, "overlapping_placements": 0}
            },
            "dialogue_flow_analysis": {
                "scene_dialogue_distribution": {},
                "character_speaking_balance": {},
                "dialogue_types_distribution": {},
                "total_dialogue_elements": len(dialogue_content),
                "average_dialogue_per_panel": 0.5,
                "narrative_progression_score": 0.5,
                "character_voice_consistency": {"overall_voice_consistency": 0.5},
                "dialogue_pacing_analysis": {"pacing_alignment_score": 0.5}
            },
            "quality_metrics": quality_metrics.dict(),
            "total_dialogue_count": len(dialogue_content),
            "average_words_per_panel": 1.0,
            "dialogue_distribution": {"1_elements": len(dialogue_content) // 2, "0_elements": len(dialogue_content) // 2},
            "reading_flow": {
                "total_panels": len(dialogue_content),
                "panels_with_dialogue": len(dialogue_content) // 2,
                "average_reading_time": 1.0
            },
            "panels_processed": len(dialogue_content),
            "success_rate": 0.5
        }

    async def _generate_dialogue_content(
        self,
        scenes: List[Dict[str, Any]],
        characters: List[Dict[str, Any]],
        panel_specifications: List[Dict[str, Any]],
        ai_suggestions: Dict[str, Any]
    ) -> List[PanelDialogue]:
        """Generate dialogue content for all panels."""

        try:
            # Create dialogue generation tasks
            dialogue_tasks = []

            for i, panel_spec in enumerate(panel_specifications):
                panel_id = panel_spec.get("panel_id", f"panel_{i}")
                scene_number = panel_spec.get("scene_number", 1)

                # Find corresponding scene
                scene = next(
                    (s for s in scenes if s.get("scene_number") == scene_number),
                    {}
                )

                # Get characters in this panel
                panel_characters = panel_spec.get("characters", [])

                # Create task
                task = DialogueGenerationTask(
                    panel_id=panel_id,
                    scene_number=scene_number,
                    characters=panel_characters,
                    scene_context=scene,
                    emotional_tone=panel_spec.get("emotional_tone", "neutral"),
                    panel_specs={
                        "camera_angle": panel_spec.get("camera_angle", "medium_shot"),
                        "size": panel_spec.get("size", "medium"),
                        "genre": "slice_of_life"
                    },
                    generation_constraints={}
                )

                dialogue_tasks.append(task)

            # Generate dialogue content in batch
            dialogue_content = await self.dialogue_generator.generate_batch_dialogues(
                dialogue_tasks
            )

            self.logger.info(f"Generated dialogue for {len(dialogue_content)} panels")
            return dialogue_content

        except Exception as e:
            self.logger.error(f"Error generating dialogue content: {e}")
            # Return empty content for all panels in case of error
            return [
                PanelDialogue(
                    panel_id=spec.get("panel_id", f"panel_{i}"),
                    scene_number=spec.get("scene_number", 1),
                    dialogue_elements=[],
                    narration=None,
                    total_text_elements=0,
                    estimated_reading_time=0.0
                )
                for i, spec in enumerate(panel_specifications)
            ]

    def _analyze_dialogue_timing(self, dialogue_content: List[PanelDialogue]) -> TimingAnalysis:
        """Analyze dialogue timing and pacing."""

        if not dialogue_content:
            return TimingAnalysis(
                total_estimated_reading_time=0.0,
                average_reading_time_per_panel=0.0,
                reading_speed_analysis={},
                pacing_recommendations=[],
                syllable_distribution={}
            )

        # Calculate timing statistics
        total_reading_time = sum(panel.estimated_reading_time for panel in dialogue_content)
        average_reading_time = total_reading_time / len(dialogue_content)

        # Analyze syllable distribution
        syllable_distribution = {}
        reading_speed_analysis = {}

        for panel in dialogue_content:
            for element in panel.dialogue_elements:
                syllable_count = element.estimated_syllables
                range_key = f"{(syllable_count // 5) * 5}-{(syllable_count // 5) * 5 + 4}"
                syllable_distribution[range_key] = syllable_distribution.get(range_key, 0) + 1

        # Generate pacing recommendations
        pacing_recommendations = []

        if average_reading_time > 10.0:
            pacing_recommendations.append("全体的に読み時間が長すぎます。テキスト量の削減を検討してください。")
        elif average_reading_time < 2.0:
            pacing_recommendations.append("読み時間が短すぎる可能性があります。内容の充実を検討してください。")
        else:
            pacing_recommendations.append("読み時間は適切な範囲内です。")

        return TimingAnalysis(
            total_estimated_reading_time=round(total_reading_time, 1),
            average_reading_time_per_panel=round(average_reading_time, 1),
            reading_speed_analysis=reading_speed_analysis,
            pacing_recommendations=pacing_recommendations,
            syllable_distribution=syllable_distribution
        )

    def _analyze_dialogue_flow(
        self,
        dialogue_content: List[PanelDialogue],
        scenes: List[Dict[str, Any]],
        characters: List[Dict[str, Any]]
    ) -> DialogueFlowAnalysis:
        """Analyze dialogue flow and narrative progression."""

        if not dialogue_content:
            return DialogueFlowAnalysis()

        # Analyze dialogue distribution across scenes
        scene_dialogue_map = {}
        for dialogue in dialogue_content:
            scene_number = dialogue.scene_number
            if scene_number not in scene_dialogue_map:
                scene_dialogue_map[scene_number] = []
            scene_dialogue_map[scene_number].extend([
                {"text": elem.text, "speaker": elem.speaker, "type": elem.dialogue_type.value}
                for elem in dialogue.dialogue_elements
            ])

        # Analyze character speaking patterns
        character_dialogue_count = {}
        for dialogue in dialogue_content:
            for element in dialogue.dialogue_elements:
                speaker = element.speaker or "Unknown"
                character_dialogue_count[speaker] = character_dialogue_count.get(speaker, 0) + 1

        # Analyze dialogue types distribution
        dialogue_types_count = {}
        for dialogue in dialogue_content:
            for element in dialogue.dialogue_elements:
                dialogue_type = element.dialogue_type.value
                dialogue_types_count[dialogue_type] = dialogue_types_count.get(dialogue_type, 0) + 1

        # Calculate narrative progression score
        narrative_progression_score = self._calculate_narrative_progression_score(
            scene_dialogue_map, scenes
        )

        # Analyze character voice consistency
        character_voice_consistency = self._analyze_character_voice_consistency(dialogue_content)

        # Analyze dialogue pacing alignment
        dialogue_pacing_analysis = self._analyze_dialogue_pacing_alignment(
            dialogue_content, scenes
        )

        # Calculate totals
        total_dialogue_elements = sum(
            len(d.dialogue_elements) for d in dialogue_content
        )
        average_dialogue_per_panel = (
            total_dialogue_elements / len(dialogue_content)
            if dialogue_content else 0.0
        )

        return DialogueFlowAnalysis(
            scene_dialogue_distribution=scene_dialogue_map,
            character_speaking_balance=character_dialogue_count,
            dialogue_types_distribution=dialogue_types_count,
            total_dialogue_elements=total_dialogue_elements,
            average_dialogue_per_panel=round(average_dialogue_per_panel, 1),
            narrative_progression_score=narrative_progression_score,
            character_voice_consistency=character_voice_consistency,
            dialogue_pacing_analysis=dialogue_pacing_analysis
        )

    def _calculate_narrative_progression_score(
        self, scene_dialogue_map: Dict[int, List], scenes: List[Dict[str, Any]]
    ) -> float:
        """Calculate how well dialogue supports narrative progression."""

        if not scene_dialogue_map or not scenes:
            return 0.5

        progression_score = 0.0
        total_scenes = len(scenes)

        for scene in scenes:
            scene_number = scene.get("scene_number", 0)
            scene_purpose = scene.get("purpose", "")
            scene_dialogues = scene_dialogue_map.get(scene_number, [])

            # Score based on dialogue presence in key scenes
            if scene_dialogues:
                if "climax" in scene_purpose or "conflict" in scene_purpose:
                    progression_score += 1.0
                elif "introduction" in scene_purpose:
                    progression_score += 0.8
                else:
                    progression_score += 0.6
            else:
                if "climax" in scene_purpose:
                    progression_score += 0.2
                else:
                    progression_score += 0.4

        return round(progression_score / total_scenes, 2) if total_scenes > 0 else 0.5

    def _analyze_character_voice_consistency(
        self, dialogue_content: List[PanelDialogue]
    ) -> Dict[str, Any]:
        """Analyze consistency of character voices."""

        character_speech_patterns = {}

        for dialogue in dialogue_content:
            for element in dialogue.dialogue_elements:
                speaker = element.speaker or "Unknown"
                speech_pattern = element.speech_pattern.value

                if speaker not in character_speech_patterns:
                    character_speech_patterns[speaker] = []
                character_speech_patterns[speaker].append(speech_pattern)

        # Calculate consistency for each character
        consistency_scores = {}
        for character, patterns in character_speech_patterns.items():
            if len(patterns) > 1:
                most_common_pattern = max(set(patterns), key=patterns.count)
                consistency_ratio = patterns.count(most_common_pattern) / len(patterns)
                consistency_scores[character] = round(consistency_ratio, 2)
            else:
                consistency_scores[character] = 1.0

        overall_consistency = (
            sum(consistency_scores.values()) / len(consistency_scores)
            if consistency_scores else 1.0
        )

        return {
            "character_consistency_scores": consistency_scores,
            "overall_voice_consistency": round(overall_consistency, 2),
            "characters_analyzed": len(character_speech_patterns),
            "consistency_issues": [
                f"{char}: 一貫性スコア {score:.2f}"
                for char, score in consistency_scores.items() if score < 0.8
            ]
        }

    def _analyze_dialogue_pacing_alignment(
        self, dialogue_content: List[PanelDialogue], scenes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze dialogue pacing alignment with scene pacing."""

        pacing_alignment = []

        for dialogue in dialogue_content:
            scene_number = dialogue.scene_number
            dialogue_elements = dialogue.dialogue_elements

            # Find corresponding scene
            scene = next(
                (s for s in scenes if s.get("scene_number") == scene_number),
                {}
            )

            scene_pacing = scene.get("pacing", "medium")

            # Calculate dialogue metrics
            total_text_length = sum(len(elem.text) for elem in dialogue_elements)
            dialogue_count = len(dialogue_elements)

            # Determine appropriateness
            if scene_pacing == "fast":
                appropriate = dialogue_count <= 2 and total_text_length <= 40
            elif scene_pacing == "slow":
                appropriate = True  # More flexible
            else:
                appropriate = dialogue_count <= 3 and total_text_length <= 80

            pacing_alignment.append({
                "scene_number": scene_number,
                "scene_pacing": scene_pacing,
                "dialogue_count": dialogue_count,
                "total_text_length": total_text_length,
                "appropriate_pacing": appropriate
            })

        # Calculate overall alignment score
        appropriate_count = sum(1 for p in pacing_alignment if p["appropriate_pacing"])
        pacing_score = appropriate_count / len(pacing_alignment) if pacing_alignment else 1.0

        return {
            "pacing_alignment_details": pacing_alignment,
            "pacing_alignment_score": round(pacing_score, 2),
            "pacing_recommendations": self._generate_pacing_recommendations(pacing_alignment)
        }

    def _generate_pacing_recommendations(self, pacing_alignment: List[Dict[str, Any]]) -> List[str]:
        """Generate pacing improvement recommendations."""

        recommendations = []

        for alignment in pacing_alignment:
            if not alignment["appropriate_pacing"]:
                scene_num = alignment["scene_number"]
                scene_pacing = alignment["scene_pacing"]
                dialogue_count = alignment["dialogue_count"]
                text_length = alignment["total_text_length"]

                if scene_pacing == "fast" and dialogue_count > 2:
                    recommendations.append(f"シーン{scene_num}: 高速ペースに合わせてセリフ数を削減")

                if text_length > 80:
                    recommendations.append(f"シーン{scene_num}: テキスト量を削減して読みやすさを向上")

        if not recommendations:
            recommendations.append("現在のセリフペーシングは適切です")

        return recommendations

    def _calculate_quality_metrics(
        self,
        dialogue_content: List[PanelDialogue],
        text_placements: List[TextPlacement],
        readability_optimization: ReadabilityOptimization,
        dialogue_flow_analysis: DialogueFlowAnalysis,
        timing_analysis: TimingAnalysis
    ) -> QualityMetrics:
        """Calculate overall quality metrics."""

        # Dialogue density score
        if dialogue_content:
            panels_with_dialogue = sum(1 for panel in dialogue_content if len(panel.dialogue_elements) > 0)
            dialogue_density_score = panels_with_dialogue / len(dialogue_content)
        else:
            dialogue_density_score = 0.0

        # Readability score
        readability_score = readability_optimization.overall_readability_score

        # Integration score (simplified)
        if text_placements:
            safe_placements = readability_optimization.visual_interference_analysis.safe_placements
            total_placements = len(text_placements)
            integration_score = safe_placements / total_placements if total_placements > 0 else 0.0
        else:
            integration_score = 0.0

        # Narrative coherence score
        narrative_coherence_score = dialogue_flow_analysis.narrative_progression_score

        # Character voice consistency score
        character_voice_consistency_score = dialogue_flow_analysis.character_voice_consistency.get(
            "overall_voice_consistency", 0.0
        )

        # Pacing alignment score
        pacing_alignment_score = dialogue_flow_analysis.dialogue_pacing_analysis.get(
            "pacing_alignment_score", 0.0
        )

        # Calculate overall quality score
        scores = [
            dialogue_density_score,
            readability_score,
            integration_score,
            narrative_coherence_score,
            character_voice_consistency_score,
            pacing_alignment_score
        ]
        overall_quality_score = sum(scores) / len(scores)

        return QualityMetrics(
            dialogue_density_score=round(dialogue_density_score, 2),
            readability_score=round(readability_score, 2),
            integration_score=round(integration_score, 2),
            narrative_coherence_score=round(narrative_coherence_score, 2),
            character_voice_consistency_score=round(character_voice_consistency_score, 2),
            pacing_alignment_score=round(pacing_alignment_score, 2),
            overall_quality_score=round(overall_quality_score, 2)
        )

    def _calculate_summary_statistics(
        self, dialogue_content: List[PanelDialogue], text_placements: List[TextPlacement]
    ) -> Dict[str, Any]:
        """Calculate summary statistics."""

        # Total dialogue count
        total_dialogue_count = sum(len(panel.dialogue_elements) for panel in dialogue_content)

        # Average words per panel
        total_words = 0
        for panel in dialogue_content:
            for elem in panel.dialogue_elements:
                total_words += len(elem.text.split())
            if panel.narration:
                total_words += len(panel.narration.text.split())

        average_words_per_panel = (
            total_words / len(dialogue_content) if dialogue_content else 0.0
        )

        # Dialogue distribution analysis
        dialogue_distribution = {}
        for panel in dialogue_content:
            element_count = len(panel.dialogue_elements)
            key = f"{element_count}_elements"
            dialogue_distribution[key] = dialogue_distribution.get(key, 0) + 1

        # Reading flow analysis
        reading_flow = {
            "total_panels": len(dialogue_content),
            "panels_with_dialogue": sum(1 for panel in dialogue_content
                                      if len(panel.dialogue_elements) > 0),
            "average_reading_time": round(
                sum(panel.estimated_reading_time for panel in dialogue_content) / len(dialogue_content)
                if dialogue_content else 0.0, 1
            )
        }

        # Success rate (simplified - based on whether panels have content)
        successful_panels = sum(1 for panel in dialogue_content
                              if panel.total_text_elements > 0 or len(panel.dialogue_elements) > 0)
        success_rate = successful_panels / len(dialogue_content) if dialogue_content else 0.0

        return {
            "total_dialogue_count": total_dialogue_count,
            "average_words_per_panel": round(average_words_per_panel, 1),
            "dialogue_distribution": dialogue_distribution,
            "reading_flow": reading_flow,
            "success_rate": round(success_rate, 2)
        }

    async def _generate_preview(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview data for Phase 6."""

        preview = {
            "phase_name": "セリフ配置",
            "summary": f"総セリフ数: {output_data.get('total_dialogue_count', 0)}",
            "key_insights": [],
            "visual_elements": []
        }

        # Add key insights
        if output_data.get("total_dialogue_count"):
            preview["key_insights"].append(f"総セリフ数: {output_data['total_dialogue_count']}")

        if output_data.get("panels_processed"):
            preview["key_insights"].append(f"処理パネル数: {output_data['panels_processed']}")

        avg_words = output_data.get("average_words_per_panel", 0.0)
        if avg_words > 0:
            preview["key_insights"].append(f"パネル平均語数: {avg_words:.1f}")

        # Add quality metrics
        quality_metrics = output_data.get("quality_metrics", {})
        overall_quality = quality_metrics.get("overall_quality_score", 0.0)
        if overall_quality > 0:
            preview["visual_elements"].append(f"品質スコア: {overall_quality:.1f}")

        readability = quality_metrics.get("readability_score", 0.0)
        if readability > 0:
            preview["visual_elements"].append(f"読みやすさ: {readability:.1f}")

        # Add dialogue distribution info
        dialogue_distribution = output_data.get("dialogue_distribution", {})
        if dialogue_distribution:
            preview["visual_elements"].append(f"セリフ分散: {len(dialogue_distribution)}種類")

        return preview