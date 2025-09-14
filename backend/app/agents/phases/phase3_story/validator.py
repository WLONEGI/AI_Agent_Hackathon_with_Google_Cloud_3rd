"""Validator for Phase 3: Story Structure and Scene Analysis."""

from typing import Dict, Any, List
from app.agents.base.validator import BaseValidator, ValidationResult
from .schemas import (
    StoryAnalysisOutput,
    StoryStructure,
    SceneDetails,
    NarrativeFlow,
    StoryStructureType,
    PacingType,
    ScenePurposeType,
    EmotionalBeatType,
    STORY_STRUCTURE_TEMPLATES
)


class Phase3Validator(BaseValidator):
    """Validator for Phase 3 story analysis output."""

    def __init__(self):
        super().__init__("Story Structure Analysis")

        # Phase 3 specific required fields
        self.required_fields.extend([
            "story_structure",
            "plot_progression",
            "scenes",
            "narrative_flow",
            "total_scenes",
            "story_complexity_score",
            "scene_summaries",
            "character_usage"
        ])

        # Scene validation rules
        self.min_scenes = 3
        self.max_scenes = 50
        self.required_scene_fields = [
            "scene_number", "pages", "page_count", "title",
            "purpose", "pacing", "emotional_beat", "visual_style"
        ]

        # Story structure requirements
        self.valid_structures = [s.value for s in StoryStructureType]
        self.min_acts = 2
        self.max_acts = 7

    async def validate(self, output_data: Dict[str, Any]) -> ValidationResult:
        """Validate Phase 3 output with comprehensive checks."""

        result = ValidationResult()
        result.phase_name = "Phase 3: Story Structure Analysis"
        result.is_valid = True

        # Basic field validation
        basic_validation = self._validate_required_fields(output_data)
        if not basic_validation.is_valid:
            result.merge(basic_validation)
            return result

        # Story structure validation
        structure_validation = self._validate_story_structure(output_data.get("story_structure", {}))
        result.merge(structure_validation)

        # Scene validation
        scene_validation = await self._validate_scenes(output_data.get("scenes", []))
        result.merge(scene_validation)

        # Plot progression validation
        plot_validation = self._validate_plot_progression(output_data.get("plot_progression", {}))
        result.merge(plot_validation)

        # Narrative flow validation
        narrative_validation = self._validate_narrative_flow(
            output_data.get("narrative_flow", {}),
            output_data.get("scenes", [])
        )
        result.merge(narrative_validation)

        # Scene consistency validation
        consistency_validation = self._validate_scene_consistency(
            output_data.get("scenes", []),
            output_data.get("total_scenes", 0)
        )
        result.merge(consistency_validation)

        # Character integration validation
        character_validation = self._validate_character_integration(
            output_data.get("character_usage", {}),
            output_data.get("scenes", [])
        )
        result.merge(character_validation)

        # Quality metrics validation
        metrics_validation = self._validate_quality_metrics(output_data)
        result.merge(metrics_validation)

        return result

    def _validate_story_structure(self, story_structure: Dict[str, Any]) -> ValidationResult:
        """Validate story structure data."""

        result = ValidationResult()
        result.is_valid = True

        if not story_structure:
            result.add_error("Story structure is required")
            return result

        # Validate structure type
        structure_type = story_structure.get("type")
        if not structure_type:
            result.add_error("Story structure type is required")
        elif structure_type not in self.valid_structures:
            result.add_error(f"Invalid structure type: {structure_type}")

        # Validate acts
        acts = story_structure.get("acts", [])
        if not acts:
            result.add_error("Story structure must have acts")
        else:
            if len(acts) < self.min_acts:
                result.add_error(f"Too few acts: {len(acts)} (minimum: {self.min_acts})")
            elif len(acts) > self.max_acts:
                result.add_warning(f"Many acts: {len(acts)} (typical maximum: {self.max_acts})")

            # Validate individual acts
            total_percentage = 0.0
            for i, act in enumerate(acts):
                act_result = self._validate_single_act(act, i + 1)
                result.merge(act_result)

                duration = act.get("duration_percentage", 0.0)
                total_percentage += duration

            # Check total percentage
            if abs(total_percentage - 1.0) > 0.1:
                result.add_warning(f"Act duration percentages don't sum to 1.0: {total_percentage}")

        # Validate total acts consistency
        total_acts = story_structure.get("total_acts", 0)
        if total_acts != len(acts):
            result.add_warning(f"Total acts mismatch: reported={total_acts}, actual={len(acts)}")

        return result

    def _validate_single_act(self, act: Dict[str, Any], act_number: int) -> ValidationResult:
        """Validate a single act's data."""

        result = ValidationResult()
        result.is_valid = True

        # Required act fields
        required_fields = ["act_number", "title", "purpose", "duration_percentage"]
        missing_fields = [field for field in required_fields if field not in act]
        if missing_fields:
            result.add_error(f"Act {act_number} missing fields: {missing_fields}")

        # Validate act number
        reported_number = act.get("act_number")
        if reported_number != act_number:
            result.add_error(f"Act number mismatch: expected {act_number}, got {reported_number}")

        # Validate duration percentage
        duration = act.get("duration_percentage", 0.0)
        if not isinstance(duration, (int, float)) or not 0.0 <= duration <= 1.0:
            result.add_error(f"Act {act_number} invalid duration: {duration} (must be 0.0-1.0)")

        # Check scene and page ranges
        scene_range = act.get("scene_range", [])
        page_range = act.get("page_range", [])

        if scene_range and not isinstance(scene_range, list):
            result.add_error(f"Act {act_number} scene_range must be a list")

        if page_range and not isinstance(page_range, list):
            result.add_error(f"Act {act_number} page_range must be a list")

        return result

    async def _validate_scenes(self, scenes: List[Dict[str, Any]]) -> ValidationResult:
        """Validate scene data."""

        result = ValidationResult()
        result.is_valid = True

        if not scenes:
            result.add_error("No scenes provided")
            return result

        if len(scenes) < self.min_scenes:
            result.add_error(f"Too few scenes: {len(scenes)} (minimum: {self.min_scenes})")

        if len(scenes) > self.max_scenes:
            result.add_warning(f"Many scenes: {len(scenes)} (recommended max: {self.max_scenes})")

        # Validate each scene
        scene_numbers = set()
        total_pages = set()

        for i, scene in enumerate(scenes):
            scene_result = self._validate_single_scene(scene, i)
            result.merge(scene_result)

            # Check for duplicate scene numbers
            scene_number = scene.get("scene_number")
            if scene_number in scene_numbers:
                result.add_error(f"Duplicate scene number: {scene_number}")
            else:
                scene_numbers.add(scene_number)

            # Check page overlap
            pages = scene.get("pages", [])
            if isinstance(pages, list):
                scene_pages = set(pages)
                overlap = total_pages.intersection(scene_pages)
                if overlap:
                    result.add_error(f"Scene {scene_number} has page overlap: {sorted(overlap)}")
                total_pages.update(scene_pages)

        # Check scene number sequence
        if scene_numbers:
            expected_numbers = set(range(1, len(scenes) + 1))
            if scene_numbers != expected_numbers:
                missing = expected_numbers - scene_numbers
                extra = scene_numbers - expected_numbers
                if missing:
                    result.add_error(f"Missing scene numbers: {sorted(missing)}")
                if extra:
                    result.add_error(f"Extra scene numbers: {sorted(extra)}")

        return result

    def _validate_single_scene(self, scene: Dict[str, Any], index: int) -> ValidationResult:
        """Validate a single scene's data."""

        result = ValidationResult()
        result.is_valid = True

        scene_number = scene.get("scene_number", index + 1)

        # Required fields check
        missing_fields = [field for field in self.required_scene_fields if field not in scene]
        if missing_fields:
            result.add_error(f"Scene {scene_number} missing fields: {missing_fields}")

        # Validate scene number
        if not isinstance(scene_number, int) or scene_number < 1:
            result.add_error(f"Scene {scene_number} invalid scene number")

        # Validate pages
        pages = scene.get("pages", [])
        page_count = scene.get("page_count", 0)

        if not isinstance(pages, list):
            result.add_error(f"Scene {scene_number} pages must be a list")
        elif len(pages) != page_count:
            result.add_warning(f"Scene {scene_number} page count mismatch: list={len(pages)}, reported={page_count}")

        # Validate enums
        purpose = scene.get("purpose")
        if purpose and purpose not in [p.value for p in ScenePurposeType]:
            result.add_error(f"Scene {scene_number} invalid purpose: {purpose}")

        pacing = scene.get("pacing")
        if pacing and pacing not in [p.value for p in PacingType]:
            result.add_error(f"Scene {scene_number} invalid pacing: {pacing}")

        emotional_beat = scene.get("emotional_beat")
        if emotional_beat and emotional_beat not in [e.value for e in EmotionalBeatType]:
            result.add_error(f"Scene {scene_number} invalid emotional_beat: {emotional_beat}")

        # Validate optional fields
        characters_present = scene.get("characters_present", [])
        if characters_present and not isinstance(characters_present, list):
            result.add_warning(f"Scene {scene_number} characters_present should be a list")

        return result

    def _validate_plot_progression(self, plot_progression: Dict[str, Any]) -> ValidationResult:
        """Validate plot progression data."""

        result = ValidationResult()
        result.is_valid = True

        if not plot_progression:
            result.add_error("Plot progression is required")
            return result

        # Required plot elements
        required_elements = ["opening", "inciting_incident", "climax", "resolution"]
        missing_elements = [elem for elem in required_elements if not plot_progression.get(elem)]
        if missing_elements:
            result.add_error(f"Plot progression missing elements: {missing_elements}")

        # Validate list fields
        list_fields = ["rising_action", "falling_action"]
        for field in list_fields:
            value = plot_progression.get(field, [])
            if value and not isinstance(value, list):
                result.add_error(f"Plot progression {field} must be a list")
            elif isinstance(value, list) and len(value) == 0:
                result.add_warning(f"Plot progression {field} is empty")

        return result

    def _validate_narrative_flow(
        self,
        narrative_flow: Dict[str, Any],
        scenes: List[Dict[str, Any]]
    ) -> ValidationResult:
        """Validate narrative flow data."""

        result = ValidationResult()
        result.is_valid = True

        if not narrative_flow:
            result.add_error("Narrative flow is required")
            return result

        # Required narrative components
        required_components = ["character_arcs", "theme_development", "tension_curve", "pacing_analysis"]
        missing_components = [comp for comp in required_components if comp not in narrative_flow]
        if missing_components:
            result.add_error(f"Narrative flow missing components: {missing_components}")

        # Validate character arcs
        character_arcs = narrative_flow.get("character_arcs", [])
        if isinstance(character_arcs, list):
            for i, arc in enumerate(character_arcs):
                if not isinstance(arc, dict):
                    result.add_error(f"Character arc {i} must be a dictionary")
                    continue

                required_arc_fields = ["character_name", "starting_state", "ending_state"]
                missing_arc_fields = [field for field in required_arc_fields if not arc.get(field)]
                if missing_arc_fields:
                    result.add_error(f"Character arc {i} missing fields: {missing_arc_fields}")

        # Validate tension curve
        tension_curve = narrative_flow.get("tension_curve", {})
        if tension_curve:
            points = tension_curve.get("points", [])
            if isinstance(points, list):
                scene_count = len(scenes)
                for point in points:
                    scene_num = point.get("scene_number", 0)
                    if scene_num < 1 or scene_num > scene_count:
                        result.add_error(f"Tension point references invalid scene: {scene_num}")

                    tension_level = point.get("tension_level")
                    if tension_level is not None and not (0.0 <= tension_level <= 1.0):
                        result.add_error(f"Invalid tension level: {tension_level} (must be 0.0-1.0)")

        return result

    def _validate_scene_consistency(
        self,
        scenes: List[Dict[str, Any]],
        total_scenes: int
    ) -> ValidationResult:
        """Validate scene consistency."""

        result = ValidationResult()
        result.is_valid = True

        actual_scene_count = len(scenes)
        if actual_scene_count != total_scenes:
            result.add_warning(f"Scene count mismatch: actual={actual_scene_count}, reported={total_scenes}")

        # Check scene flow
        if scenes:
            # Validate pacing distribution
            pacing_counts = {}
            for scene in scenes:
                pacing = scene.get("pacing", "medium")
                pacing_counts[pacing] = pacing_counts.get(pacing, 0) + 1

            # Check for pacing variety
            if len(pacing_counts) == 1:
                result.add_warning("All scenes have the same pacing - consider varying pacing for better flow")

            # Check emotional beat variety
            emotional_beats = [scene.get("emotional_beat", "tension") for scene in scenes]
            unique_beats = set(emotional_beats)
            if len(unique_beats) < 3 and len(scenes) > 5:
                result.add_warning("Limited emotional beat variety - consider more emotional range")

        return result

    def _validate_character_integration(
        self,
        character_usage: Dict[str, Any],
        scenes: List[Dict[str, Any]]
    ) -> ValidationResult:
        """Validate character integration across scenes."""

        result = ValidationResult()
        result.is_valid = True

        if not character_usage:
            result.add_warning("Character usage information is missing")
            return result

        scene_count = len(scenes)
        if scene_count == 0:
            return result

        # Validate character usage data
        for character_name, scene_list in character_usage.items():
            if not isinstance(scene_list, list):
                result.add_error(f"Character usage for '{character_name}' must be a list")
                continue

            # Check for invalid scene references
            for scene_num in scene_list:
                if not isinstance(scene_num, int) or scene_num < 1 or scene_num > scene_count:
                    result.add_error(f"Character '{character_name}' references invalid scene: {scene_num}")

            # Check character presence
            usage_percentage = len(scene_list) / scene_count
            if usage_percentage < 0.1:
                result.add_warning(f"Character '{character_name}' appears in very few scenes: {len(scene_list)}/{scene_count}")

        return result

    def _validate_quality_metrics(self, output_data: Dict[str, Any]) -> ValidationResult:
        """Validate quality metrics."""

        result = ValidationResult()
        result.is_valid = True

        # Score fields that should be 0.0-1.0
        score_fields = [
            "story_complexity_score",
            "pacing_consistency_score",
            "character_integration_score"
        ]

        for field in score_fields:
            score = output_data.get(field)
            if score is not None:
                if not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0:
                    result.add_error(f"Invalid {field}: {score} (must be 0.0-1.0)")

        # Check metadata
        timestamp = output_data.get("generation_timestamp")
        if not timestamp:
            result.add_info("Missing generation timestamp")

        ai_model = output_data.get("ai_model_used")
        if not ai_model:
            result.add_info("Missing AI model information")

        processing_time = output_data.get("processing_time")
        if processing_time is not None and (not isinstance(processing_time, (int, float)) or processing_time < 0):
            result.add_warning(f"Invalid processing time: {processing_time}")

        return result

    def get_validation_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of validation results."""

        scenes = output_data.get("scenes", [])
        story_structure = output_data.get("story_structure", {})

        return {
            "total_scenes": len(scenes),
            "story_structure_type": story_structure.get("type", "unknown"),
            "total_acts": len(story_structure.get("acts", [])),
            "scene_pacing_distribution": self._get_pacing_distribution(scenes),
            "emotional_beat_distribution": self._get_emotional_distribution(scenes),
            "completeness_score": self._calculate_completeness_score(output_data),
            "consistency_score": self._calculate_consistency_score(output_data),
            "validation_passed": True  # This would be set by the actual validation
        }

    def _get_pacing_distribution(self, scenes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of scene pacing."""

        distribution = {}
        for scene in scenes:
            pacing = scene.get("pacing", "medium")
            distribution[pacing] = distribution.get(pacing, 0) + 1

        return distribution

    def _get_emotional_distribution(self, scenes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of emotional beats."""

        distribution = {}
        for scene in scenes:
            beat = scene.get("emotional_beat", "tension")
            distribution[beat] = distribution.get(beat, 0) + 1

        return distribution

    def _calculate_completeness_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate overall data completeness score."""

        total_score = 0.0
        components = 0

        # Story structure completeness (20%)
        story_structure = output_data.get("story_structure", {})
        if story_structure:
            structure_score = 0.0
            structure_score += 0.3 if story_structure.get("type") else 0.0
            structure_score += 0.4 if story_structure.get("acts") else 0.0
            structure_score += 0.3 if story_structure.get("structure_rationale") else 0.0
            total_score += 0.2 * structure_score
        components += 0.2

        # Scenes completeness (30%)
        scenes = output_data.get("scenes", [])
        if scenes:
            scene_score = 0.0
            complete_scenes = 0
            for scene in scenes:
                scene_completeness = sum(1 for field in self.required_scene_fields if scene.get(field))
                scene_completeness /= len(self.required_scene_fields)
                complete_scenes += scene_completeness
            scene_score = complete_scenes / len(scenes) if scenes else 0.0
            total_score += 0.3 * scene_score
        components += 0.3

        # Plot progression completeness (20%)
        plot_progression = output_data.get("plot_progression", {})
        if plot_progression:
            plot_fields = ["opening", "inciting_incident", "rising_action", "climax", "falling_action", "resolution"]
            plot_score = sum(1 for field in plot_fields if plot_progression.get(field)) / len(plot_fields)
            total_score += 0.2 * plot_score
        components += 0.2

        # Narrative flow completeness (20%)
        narrative_flow = output_data.get("narrative_flow", {})
        if narrative_flow:
            narrative_fields = ["character_arcs", "theme_development", "tension_curve", "pacing_analysis"]
            narrative_score = sum(1 for field in narrative_fields if narrative_flow.get(field)) / len(narrative_fields)
            total_score += 0.2 * narrative_score
        components += 0.2

        # Metadata completeness (10%)
        metadata_fields = ["generation_timestamp", "ai_model_used", "processing_time"]
        metadata_score = sum(1 for field in metadata_fields if output_data.get(field)) / len(metadata_fields)
        total_score += 0.1 * metadata_score
        components += 0.1

        return total_score / components if components > 0 else 0.0

    def _calculate_consistency_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate data consistency score."""

        score = 1.0

        # Check scene count consistency
        scenes = output_data.get("scenes", [])
        total_scenes = output_data.get("total_scenes", 0)
        if len(scenes) != total_scenes:
            score -= 0.1

        # Check character usage consistency
        character_usage = output_data.get("character_usage", {})
        scene_count = len(scenes)
        for character_name, scene_list in character_usage.items():
            if isinstance(scene_list, list):
                for scene_num in scene_list:
                    if scene_num < 1 or scene_num > scene_count:
                        score -= 0.05
                        break

        # Check story structure consistency
        story_structure = output_data.get("story_structure", {})
        acts = story_structure.get("acts", [])
        total_acts = story_structure.get("total_acts", 0)
        if len(acts) != total_acts:
            score -= 0.1

        # Check scene summaries consistency
        scene_summaries = output_data.get("scene_summaries", [])
        if len(scene_summaries) != len(scenes):
            score -= 0.1

        return max(0.0, score)

    async def _validate_phase_specific(
        self,
        output: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate Phase 3 specific requirements."""

        # Validate story structure
        structure_validation = await self._validate_story_structure(output.get("story_structure", {}))
        result.merge(structure_validation)

        # Validate scenes
        scene_validation = await self._validate_scenes(output.get("scenes", []))
        result.merge(scene_validation)

        # Validate plot progression
        plot_validation = self._validate_plot_progression(output.get("plot_progression", {}))
        result.merge(plot_validation)

        # Validate narrative flow
        flow_validation = self._validate_narrative_flow(output.get("narrative_flow", {}))
        result.merge(flow_validation)

        # Validate character consistency
        character_validation = self._validate_character_consistency(output)
        result.merge(character_validation)