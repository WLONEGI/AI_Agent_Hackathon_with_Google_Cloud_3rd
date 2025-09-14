"""Phase 6: Dialogue and Text Placement Validator.

This module provides comprehensive validation for Phase 6 dialogue generation
and text placement output, ensuring quality and consistency.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

from .schemas import (
    DialoguePlacementOutput, DialoguePlacementInput,
    PanelDialogue, DialogueElement, NarrationElement,
    TextPlacement, BubbleDesign, TypographySpecifications,
    ReadabilityOptimization, DialogueFlowAnalysis, TimingAnalysis,
    QualityMetrics, DialogueType, BubbleStyle, ImportanceLevel,
    ElementType, Position, TextArea
)


logger = logging.getLogger(__name__)


class Phase6Validator:
    """Validator for Phase 6 dialogue placement and text generation output."""

    def __init__(self):
        """Initialize validator with quality thresholds."""

        # Quality thresholds
        self.min_readability_score = 0.7
        self.min_overall_quality_score = 0.6
        self.max_text_density_per_panel = 80
        self.min_dialogue_coherence_score = 0.6
        self.max_reading_time_per_panel = 15.0  # seconds

        # Content requirements
        self.min_dialogue_elements = 0  # Allow panels without dialogue
        self.max_dialogue_elements_per_panel = 5
        self.max_dialogue_text_length = 50
        self.min_font_size = 8
        self.max_font_size = 24

        # Position validation
        self.min_position_coordinate = 0.0
        self.max_position_coordinate = 1.0
        self.min_distance_between_elements = 0.15

        # Typography validation
        self.supported_bubble_styles = {
            "standard_speech", "cloud_thought", "jagged_excitement",
            "dotted_soft", "rectangular_box"
        }
        self.supported_dialogue_types = {
            "speech", "thought", "shout", "whisper", "narration"
        }

    def validate_input(self, input_data: DialoguePlacementInput) -> Tuple[bool, List[str]]:
        """Validate Phase 6 input data.

        Args:
            input_data: Input data to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """

        errors = []

        try:
            # Validate basic input requirements
            if not input_data.text or len(input_data.text.strip()) == 0:
                errors.append("Input text is required and cannot be empty")

            if len(input_data.text) > 10000:
                errors.append("Input text exceeds maximum length of 10,000 characters")

            # Validate session ID
            if not input_data.session_id:
                errors.append("Session ID is required")

            # Validate optional fields
            if input_data.genre and len(input_data.genre) > 50:
                errors.append("Genre specification too long (max 50 characters)")

        except Exception as e:
            errors.append(f"Input validation error: {str(e)}")

        return len(errors) == 0, errors

    def validate_output(self, output_data: DialoguePlacementOutput) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate complete Phase 6 output.

        Args:
            output_data: Output data to validate

        Returns:
            Tuple of (is_valid, error_messages, validation_details)
        """

        errors = []
        warnings = []
        validation_details = {
            "content_validation": {},
            "placement_validation": {},
            "design_validation": {},
            "quality_validation": {},
            "metadata_validation": {}
        }

        try:
            # Validate core content
            content_valid, content_errors, content_details = self._validate_dialogue_content(
                output_data.dialogue_content
            )
            errors.extend(content_errors)
            validation_details["content_validation"] = content_details

            # Validate text placement
            placement_valid, placement_errors, placement_details = self._validate_text_placement(
                output_data.dialogue_placement, output_data.dialogue_content
            )
            errors.extend(placement_errors)
            validation_details["placement_validation"] = placement_details

            # Validate bubble designs
            design_valid, design_errors, design_details = self._validate_bubble_designs(
                output_data.speech_bubbles, output_data.dialogue_placement
            )
            errors.extend(design_errors)
            validation_details["design_validation"] = design_details

            # Validate typography
            typo_valid, typo_errors, typo_details = self._validate_typography(
                output_data.typography_specifications
            )
            errors.extend(typo_errors)
            validation_details["typography_validation"] = typo_details

            # Validate timing analysis
            timing_valid, timing_errors, timing_details = self._validate_timing_analysis(
                output_data.timing_analysis, output_data.dialogue_content
            )
            errors.extend(timing_errors)
            validation_details["timing_validation"] = timing_details

            # Validate readability optimization
            read_valid, read_errors, read_details = self._validate_readability_optimization(
                output_data.readability_optimization
            )
            errors.extend(read_errors)
            validation_details["readability_validation"] = read_details

            # Validate dialogue flow analysis
            flow_valid, flow_errors, flow_details = self._validate_dialogue_flow_analysis(
                output_data.dialogue_flow_analysis
            )
            errors.extend(flow_errors)
            validation_details["flow_validation"] = flow_details

            # Validate quality metrics
            quality_valid, quality_errors, quality_details = self._validate_quality_metrics(
                output_data.quality_metrics
            )
            errors.extend(quality_errors)
            validation_details["quality_validation"] = quality_details

            # Validate summary statistics
            stats_valid, stats_errors, stats_details = self._validate_summary_statistics(
                output_data
            )
            errors.extend(stats_errors)
            validation_details["statistics_validation"] = stats_details

            # Validate metadata
            meta_valid, meta_errors, meta_details = self._validate_metadata(output_data)
            errors.extend(meta_errors)
            validation_details["metadata_validation"] = meta_details

            # Cross-validation checks
            cross_valid, cross_errors, cross_details = self._cross_validate_output(output_data)
            errors.extend(cross_errors)
            validation_details["cross_validation"] = cross_details

        except Exception as e:
            errors.append(f"Validation process error: {str(e)}")
            logger.error(f"Phase 6 validation error: {e}", exc_info=True)

        is_valid = len(errors) == 0
        validation_details["overall_valid"] = is_valid
        validation_details["error_count"] = len(errors)
        validation_details["warning_count"] = len(warnings)

        return is_valid, errors, validation_details

    def _validate_dialogue_content(self, dialogue_content: List[PanelDialogue]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate dialogue content for all panels."""

        errors = []
        details = {
            "panels_validated": 0,
            "dialogue_elements_validated": 0,
            "narration_elements_validated": 0,
            "issues_found": []
        }

        if not dialogue_content:
            errors.append("No dialogue content provided")
            return False, errors, details

        panel_ids_seen = set()

        for i, panel_dialogue in enumerate(dialogue_content):
            try:
                # Validate panel dialogue structure
                if not panel_dialogue.panel_id:
                    errors.append(f"Panel {i}: Missing panel_id")
                    continue

                if panel_dialogue.panel_id in panel_ids_seen:
                    errors.append(f"Duplicate panel_id: {panel_dialogue.panel_id}")

                panel_ids_seen.add(panel_dialogue.panel_id)

                # Validate scene number
                if panel_dialogue.scene_number < 1:
                    errors.append(f"Panel {panel_dialogue.panel_id}: Invalid scene_number")

                # Validate dialogue elements
                if len(panel_dialogue.dialogue_elements) > self.max_dialogue_elements_per_panel:
                    errors.append(f"Panel {panel_dialogue.panel_id}: Too many dialogue elements "
                                f"({len(panel_dialogue.dialogue_elements)} > {self.max_dialogue_elements_per_panel})")

                for j, dialogue_elem in enumerate(panel_dialogue.dialogue_elements):
                    elem_valid, elem_errors = self._validate_dialogue_element(
                        dialogue_elem, panel_dialogue.panel_id, j
                    )
                    errors.extend(elem_errors)
                    if elem_valid:
                        details["dialogue_elements_validated"] += 1

                # Validate narration if present
                if panel_dialogue.narration:
                    narr_valid, narr_errors = self._validate_narration_element(
                        panel_dialogue.narration, panel_dialogue.panel_id
                    )
                    errors.extend(narr_errors)
                    if narr_valid:
                        details["narration_elements_validated"] += 1

                # Validate totals and timing
                expected_total = len(panel_dialogue.dialogue_elements) + (1 if panel_dialogue.narration else 0)
                if panel_dialogue.total_text_elements != expected_total:
                    errors.append(f"Panel {panel_dialogue.panel_id}: Incorrect total_text_elements count")

                if panel_dialogue.estimated_reading_time < 0:
                    errors.append(f"Panel {panel_dialogue.panel_id}: Invalid reading time")

                if panel_dialogue.estimated_reading_time > self.max_reading_time_per_panel:
                    details["issues_found"].append(f"Panel {panel_dialogue.panel_id}: Long reading time "
                                                  f"({panel_dialogue.estimated_reading_time:.1f}s)")

                details["panels_validated"] += 1

            except Exception as e:
                errors.append(f"Panel {i}: Validation error - {str(e)}")

        return len(errors) == 0, errors, details

    def _validate_dialogue_element(self, dialogue_elem: DialogueElement, panel_id: str, elem_index: int) -> Tuple[bool, List[str]]:
        """Validate individual dialogue element."""

        errors = []

        # Validate text content
        if not dialogue_elem.text or len(dialogue_elem.text.strip()) == 0:
            errors.append(f"Panel {panel_id}, element {elem_index}: Empty dialogue text")

        if len(dialogue_elem.text) > self.max_dialogue_text_length:
            errors.append(f"Panel {panel_id}, element {elem_index}: Text too long "
                         f"({len(dialogue_elem.text)} > {self.max_dialogue_text_length})")

        # Validate dialogue type
        if dialogue_elem.dialogue_type.value not in self.supported_dialogue_types:
            errors.append(f"Panel {panel_id}, element {elem_index}: Unsupported dialogue type")

        # Validate text length consistency
        if dialogue_elem.text_length != len(dialogue_elem.text):
            errors.append(f"Panel {panel_id}, element {elem_index}: Text length mismatch")

        # Validate syllable estimation
        if dialogue_elem.estimated_syllables < 0:
            errors.append(f"Panel {panel_id}, element {elem_index}: Invalid syllable count")

        # Validate speaker (optional but if present should not be empty)
        if dialogue_elem.speaker is not None and len(dialogue_elem.speaker.strip()) == 0:
            errors.append(f"Panel {panel_id}, element {elem_index}: Speaker name cannot be empty string")

        return len(errors) == 0, errors

    def _validate_narration_element(self, narration: NarrationElement, panel_id: str) -> Tuple[bool, List[str]]:
        """Validate narration element."""

        errors = []

        # Validate text content
        if not narration.text or len(narration.text.strip()) == 0:
            errors.append(f"Panel {panel_id}: Empty narration text")

        # Validate text length consistency
        if narration.text_length != len(narration.text):
            errors.append(f"Panel {panel_id}: Narration text length mismatch")

        return len(errors) == 0, errors

    def _validate_text_placement(self, placements: List[TextPlacement], dialogue_content: List[PanelDialogue]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate text placement specifications."""

        errors = []
        details = {
            "placements_validated": 0,
            "position_conflicts": [],
            "reading_order_issues": []
        }

        if not placements:
            errors.append("No text placements provided")
            return False, errors, details

        # Group placements by panel for validation
        panel_placements = {}
        for placement in placements:
            panel_id = placement.panel_id
            if panel_id not in panel_placements:
                panel_placements[panel_id] = []
            panel_placements[panel_id].append(placement)

        # Validate each panel's placements
        for panel_id, panel_places in panel_placements.items():

            # Validate reading order
            reading_orders = [p.reading_order for p in panel_places]
            if len(set(reading_orders)) != len(reading_orders):
                errors.append(f"Panel {panel_id}: Duplicate reading orders")
                details["reading_order_issues"].append(panel_id)

            if min(reading_orders) != 1 or max(reading_orders) != len(reading_orders):
                errors.append(f"Panel {panel_id}: Reading order not sequential starting from 1")
                details["reading_order_issues"].append(panel_id)

            # Check for position conflicts
            positions = [(p.position.x, p.position.y) for p in panel_places]
            for i, pos1 in enumerate(positions):
                for j, pos2 in enumerate(positions[i+1:], i+1):
                    distance = ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5
                    if distance < self.min_distance_between_elements:
                        details["position_conflicts"].append(f"Panel {panel_id}: Elements too close")

            # Validate individual placements
            for placement in panel_places:
                place_valid, place_errors = self._validate_individual_placement(placement)
                errors.extend(place_errors)
                if place_valid:
                    details["placements_validated"] += 1

        return len(errors) == 0, errors, details

    def _validate_individual_placement(self, placement: TextPlacement) -> Tuple[bool, List[str]]:
        """Validate individual text placement."""

        errors = []

        # Validate text content
        if not placement.text_content or len(placement.text_content.strip()) == 0:
            errors.append(f"Placement {placement.panel_id}: Empty text content")

        # Validate position
        if not (self.min_position_coordinate <= placement.position.x <= self.max_position_coordinate):
            errors.append(f"Placement {placement.panel_id}: Invalid x position")

        if not (self.min_position_coordinate <= placement.position.y <= self.max_position_coordinate):
            errors.append(f"Placement {placement.panel_id}: Invalid y position")

        # Validate text area
        if placement.text_area.width_ratio <= 0 or placement.text_area.width_ratio > 1:
            errors.append(f"Placement {placement.panel_id}: Invalid text area width ratio")

        if placement.text_area.height_ratio <= 0 or placement.text_area.height_ratio > 1:
            errors.append(f"Placement {placement.panel_id}: Invalid text area height ratio")

        if not (self.min_font_size <= placement.text_area.font_size <= self.max_font_size):
            errors.append(f"Placement {placement.panel_id}: Invalid font size")

        # Validate reading order
        if placement.reading_order < 1:
            errors.append(f"Placement {placement.panel_id}: Invalid reading order")

        return len(errors) == 0, errors

    def _validate_bubble_designs(self, bubble_designs: List[BubbleDesign], placements: List[TextPlacement]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate speech bubble design specifications."""

        errors = []
        details = {
            "designs_validated": 0,
            "missing_designs": [],
            "design_consistency_issues": []
        }

        # Create mapping for quick lookup
        placement_elements = {f"{p.panel_id}_{p.speaker or 'narration'}": p for p in placements}
        design_elements = {d.element_id: d for d in bubble_designs}

        # Check for missing designs
        for placement in placements:
            if placement.element_type == ElementType.DIALOGUE:
                expected_id = f"{placement.panel_id}_{placement.speaker or 'unknown'}"
                if expected_id not in design_elements:
                    details["missing_designs"].append(expected_id)

        # Validate individual designs
        for design in bubble_designs:
            design_valid, design_errors = self._validate_individual_bubble_design(design)
            errors.extend(design_errors)
            if design_valid:
                details["designs_validated"] += 1

        return len(errors) == 0, errors, details

    def _validate_individual_bubble_design(self, design: BubbleDesign) -> Tuple[bool, List[str]]:
        """Validate individual bubble design."""

        errors = []

        # Validate basic properties
        if not design.panel_id or not design.element_id:
            errors.append("Bubble design missing panel_id or element_id")

        # Validate bubble style
        if design.bubble_type.value not in self.supported_bubble_styles:
            errors.append(f"Unsupported bubble style: {design.bubble_type}")

        # Validate border properties
        if design.border.width < 1 or design.border.width > 10:
            errors.append(f"Invalid border width: {design.border.width}")

        # Validate fill properties
        if not (0.0 <= design.fill.opacity <= 1.0):
            errors.append(f"Invalid fill opacity: {design.fill.opacity}")

        # Validate corner radius
        if design.corner_radius < 0 or design.corner_radius > 20:
            errors.append(f"Invalid corner radius: {design.corner_radius}")

        return len(errors) == 0, errors

    def _validate_typography(self, typography: TypographySpecifications) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate typography specifications."""

        errors = []
        details = {
            "base_typography_valid": True,
            "dialogue_specs_validated": 0,
            "narration_specs_validated": 0
        }

        # Validate base typography
        if typography.base_typography.font_size_modifier <= 0:
            errors.append("Invalid base typography font size modifier")
            details["base_typography_valid"] = False

        # Validate dialogue specifications
        for spec in typography.dialogue_specifications:
            if spec.typography.font_size_modifier <= 0:
                errors.append(f"Invalid font size modifier in dialogue spec {spec.element_id}")
            else:
                details["dialogue_specs_validated"] += 1

        # Validate narration specifications
        for spec in typography.narration_specifications:
            if spec.typography.font_size_modifier <= 0:
                errors.append(f"Invalid font size modifier in narration spec {spec.element_id}")
            else:
                details["narration_specs_validated"] += 1

        # Validate font fallbacks
        if not typography.font_fallbacks or len(typography.font_fallbacks) == 0:
            errors.append("No font fallbacks specified")

        return len(errors) == 0, errors, details

    def _validate_timing_analysis(self, timing: TimingAnalysis, dialogue_content: List[PanelDialogue]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate timing analysis results."""

        errors = []
        details = {
            "timing_consistency": True,
            "reasonable_reading_times": True
        }

        # Validate basic timing values
        if timing.total_estimated_reading_time < 0:
            errors.append("Invalid total reading time")

        if timing.average_reading_time_per_panel < 0:
            errors.append("Invalid average reading time per panel")

        # Check consistency with dialogue content
        if dialogue_content:
            expected_total = sum(panel.estimated_reading_time for panel in dialogue_content)
            if abs(timing.total_estimated_reading_time - expected_total) > 1.0:
                errors.append("Timing analysis inconsistent with dialogue content")
                details["timing_consistency"] = False

        # Check for reasonable reading times
        if timing.average_reading_time_per_panel > self.max_reading_time_per_panel:
            details["reasonable_reading_times"] = False

        return len(errors) == 0, errors, details

    def _validate_readability_optimization(self, readability: ReadabilityOptimization) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate readability optimization analysis."""

        errors = []
        details = {
            "readability_score_valid": True,
            "analysis_components_complete": True
        }

        # Validate readability score
        if not (0.0 <= readability.overall_readability_score <= 1.0):
            errors.append("Invalid readability score")
            details["readability_score_valid"] = False

        # Check if score meets minimum threshold
        if readability.overall_readability_score < self.min_readability_score:
            errors.append(f"Readability score below threshold ({readability.overall_readability_score:.2f} < {self.min_readability_score})")

        # Validate required analysis components
        required_fields = ['reading_flow_analysis', 'text_density_analysis', 'visual_interference_analysis']
        for field in required_fields:
            if not hasattr(readability, field):
                errors.append(f"Missing readability analysis component: {field}")
                details["analysis_components_complete"] = False

        # Validate density analysis
        if hasattr(readability.text_density_analysis, 'average_text_per_panel'):
            if readability.text_density_analysis.average_text_per_panel > self.max_text_density_per_panel:
                errors.append(f"Text density too high ({readability.text_density_analysis.average_text_per_panel:.0f} > {self.max_text_density_per_panel})")

        return len(errors) == 0, errors, details

    def _validate_dialogue_flow_analysis(self, flow_analysis: DialogueFlowAnalysis) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate dialogue flow analysis."""

        errors = []
        details = {
            "flow_metrics_valid": True,
            "character_balance_reasonable": True
        }

        # Validate basic metrics
        if flow_analysis.total_dialogue_elements < 0:
            errors.append("Invalid total dialogue elements count")

        if flow_analysis.average_dialogue_per_panel < 0:
            errors.append("Invalid average dialogue per panel")

        if not (0.0 <= flow_analysis.narrative_progression_score <= 1.0):
            errors.append("Invalid narrative progression score")
            details["flow_metrics_valid"] = False

        # Check narrative progression threshold
        if flow_analysis.narrative_progression_score < self.min_dialogue_coherence_score:
            errors.append(f"Narrative progression score below threshold ({flow_analysis.narrative_progression_score:.2f} < {self.min_dialogue_coherence_score})")

        # Validate character speaking balance
        if flow_analysis.character_speaking_balance:
            speaking_counts = list(flow_analysis.character_speaking_balance.values())
            if speaking_counts:
                max_count = max(speaking_counts)
                min_count = min(speaking_counts)
                if max_count > 0 and max_count / min_count > 10:  # Very imbalanced
                    details["character_balance_reasonable"] = False

        return len(errors) == 0, errors, details

    def _validate_quality_metrics(self, quality: QualityMetrics) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate overall quality metrics."""

        errors = []
        details = {
            "all_scores_valid": True,
            "meets_quality_threshold": True
        }

        # Validate all score ranges
        score_fields = [
            'dialogue_density_score', 'readability_score', 'integration_score',
            'narrative_coherence_score', 'character_voice_consistency_score',
            'pacing_alignment_score', 'overall_quality_score'
        ]

        for field in score_fields:
            if hasattr(quality, field):
                score = getattr(quality, field)
                if not (0.0 <= score <= 1.0):
                    errors.append(f"Invalid {field}: {score}")
                    details["all_scores_valid"] = False

        # Check overall quality threshold
        if quality.overall_quality_score < self.min_overall_quality_score:
            errors.append(f"Overall quality score below threshold ({quality.overall_quality_score:.2f} < {self.min_overall_quality_score})")
            details["meets_quality_threshold"] = False

        return len(errors) == 0, errors, details

    def _validate_summary_statistics(self, output: DialoguePlacementOutput) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate summary statistics consistency."""

        errors = []
        details = {"statistics_consistent": True}

        # Validate dialogue count consistency
        actual_count = sum(len(panel.dialogue_elements) for panel in output.dialogue_content)
        if output.total_dialogue_count != actual_count:
            errors.append(f"Total dialogue count inconsistent ({output.total_dialogue_count} != {actual_count})")
            details["statistics_consistent"] = False

        # Validate average words per panel
        if output.dialogue_content:
            total_words = 0
            for panel in output.dialogue_content:
                for elem in panel.dialogue_elements:
                    total_words += len(elem.text.split())
                if panel.narration:
                    total_words += len(panel.narration.text.split())

            expected_avg = total_words / len(output.dialogue_content)
            if abs(output.average_words_per_panel - expected_avg) > 0.5:
                errors.append("Average words per panel calculation inconsistent")
                details["statistics_consistent"] = False

        return len(errors) == 0, errors, details

    def _validate_metadata(self, output: DialoguePlacementOutput) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate processing metadata."""

        errors = []
        details = {"metadata_complete": True}

        # Validate processing time
        if output.processing_time_seconds < 0:
            errors.append("Invalid processing time")

        # Validate panels processed
        if output.panels_processed < 0:
            errors.append("Invalid panels processed count")

        if output.panels_processed != len(output.dialogue_content):
            errors.append("Panels processed count inconsistent with dialogue content")

        # Validate success rate
        if not (0.0 <= output.success_rate <= 1.0):
            errors.append("Invalid success rate")

        return len(errors) == 0, errors, details

    def _cross_validate_output(self, output: DialoguePlacementOutput) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Perform cross-validation across different output components."""

        errors = []
        details = {
            "dialogue_placement_consistency": True,
            "bubble_design_consistency": True,
            "typography_consistency": True
        }

        # Check consistency between dialogue content and placements
        panel_ids_content = {panel.panel_id for panel in output.dialogue_content}
        panel_ids_placement = {place.panel_id for place in output.dialogue_placement}

        missing_in_placement = panel_ids_content - panel_ids_placement
        extra_in_placement = panel_ids_placement - panel_ids_content

        if missing_in_placement:
            errors.append(f"Panels missing in placement: {missing_in_placement}")
            details["dialogue_placement_consistency"] = False

        if extra_in_placement:
            errors.append(f"Extra panels in placement: {extra_in_placement}")
            details["dialogue_placement_consistency"] = False

        # Check consistency between placements and bubble designs
        placement_elements = {f"{p.panel_id}_{p.speaker or 'narration'}" for p in output.dialogue_placement if p.element_type == ElementType.DIALOGUE}
        design_elements = {design.element_id for design in output.speech_bubbles}

        missing_designs = placement_elements - design_elements
        if missing_designs:
            errors.append(f"Missing bubble designs for: {missing_designs}")
            details["bubble_design_consistency"] = False

        return len(errors) == 0, errors, details

    def get_quality_assessment(self, output: DialoguePlacementOutput) -> Dict[str, Any]:
        """Get comprehensive quality assessment of the output."""

        assessment = {
            "overall_quality": "unknown",
            "quality_score": 0.0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }

        try:
            quality_score = output.quality_metrics.overall_quality_score
            assessment["quality_score"] = quality_score

            if quality_score >= 0.8:
                assessment["overall_quality"] = "excellent"
            elif quality_score >= 0.7:
                assessment["overall_quality"] = "good"
            elif quality_score >= 0.6:
                assessment["overall_quality"] = "acceptable"
            else:
                assessment["overall_quality"] = "needs_improvement"

            # Analyze strengths
            if output.quality_metrics.readability_score >= 0.8:
                assessment["strengths"].append("High readability score")

            if output.quality_metrics.character_voice_consistency_score >= 0.8:
                assessment["strengths"].append("Consistent character voices")

            if output.quality_metrics.pacing_alignment_score >= 0.8:
                assessment["strengths"].append("Good pacing alignment")

            # Analyze weaknesses
            if output.quality_metrics.readability_score < 0.7:
                assessment["weaknesses"].append("Low readability score")
                assessment["recommendations"].append("Improve text placement and reduce density")

            if output.quality_metrics.integration_score < 0.7:
                assessment["weaknesses"].append("Poor text-image integration")
                assessment["recommendations"].append("Optimize text positioning to avoid visual conflicts")

            if output.readability_optimization.text_density_analysis.high_density_panels > 0:
                assessment["weaknesses"].append("High text density in some panels")
                assessment["recommendations"].append("Reduce text amount or split across more panels")

            # General recommendations
            if not assessment["recommendations"]:
                assessment["recommendations"].append("Quality meets standards - ready for production")

        except Exception as e:
            logger.error(f"Quality assessment error: {e}")
            assessment["recommendations"].append("Unable to complete quality assessment")

        return assessment