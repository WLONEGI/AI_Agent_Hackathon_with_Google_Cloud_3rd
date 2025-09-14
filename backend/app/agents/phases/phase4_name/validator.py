"""Phase 4: Name Generation (Panel Layout and Composition) - Validation Logic."""

from typing import Dict, Any, List, Optional, Tuple, Set
import math
from .schemas import (
    NameGenerationOutput, PageLayout, Panel, CameraAngleType,
    LayoutPatternType, ImportanceLevel, PanelShapeType,
    CompositionRuleType, PanelSize, PanelPosition
)

class Phase4Validator:
    """Comprehensive validator for Phase 4 name generation output."""

    def __init__(self):
        """Initialize validator with quality thresholds."""
        self.quality_thresholds = {
            "min_layout_quality": 0.6,
            "min_readability": 0.7,
            "min_composition_quality": 0.6,
            "min_camera_variety": 0.4,
            "min_visual_balance": 0.5,
            "max_panel_overlap": 0.1,
            "min_panel_size": 0.05,
            "max_panels_per_page": 12,
            "min_panels_per_page": 1
        }

    def validate_output(self, output: NameGenerationOutput) -> Tuple[bool, List[str], Dict[str, float]]:
        """
        Comprehensive validation of Phase 4 output.

        Args:
            output: Phase 4 output to validate

        Returns:
            Tuple of (is_valid, error_messages, quality_scores)
        """
        errors = []
        quality_scores = {}

        # Basic structure validation
        structure_valid, structure_errors = self._validate_structure(output)
        errors.extend(structure_errors)

        if not structure_valid:
            return False, errors, {}

        # Panel layout validation
        layout_valid, layout_errors, layout_scores = self._validate_layouts(output.pages)
        errors.extend(layout_errors)
        quality_scores.update(layout_scores)

        # Camera work validation
        camera_valid, camera_errors, camera_scores = self._validate_camera_work(output.pages)
        errors.extend(camera_errors)
        quality_scores.update(camera_scores)

        # Reading flow validation
        flow_valid, flow_errors, flow_scores = self._validate_reading_flow(output.pages)
        errors.extend(flow_errors)
        quality_scores.update(flow_scores)

        # Composition validation
        comp_valid, comp_errors, comp_scores = self._validate_composition(output.pages)
        errors.extend(comp_errors)
        quality_scores.update(comp_scores)

        # Layout analysis validation
        analysis_valid, analysis_errors = self._validate_layout_analysis(output.layout_analysis, output.pages)
        errors.extend(analysis_errors)

        # Shot list validation
        shot_valid, shot_errors = self._validate_shot_list(output.shot_list, output.pages)
        errors.extend(shot_errors)

        # Overall quality assessment
        overall_quality = self._calculate_overall_quality(quality_scores)
        quality_scores["overall_quality"] = overall_quality

        # Check if overall quality meets minimum standards
        is_valid = len(errors) == 0 and overall_quality >= self.quality_thresholds["min_layout_quality"]

        return is_valid, errors, quality_scores

    def _validate_structure(self, output: NameGenerationOutput) -> Tuple[bool, List[str]]:
        """Validate basic output structure."""
        errors = []

        # Check required fields
        if not output.pages:
            errors.append("No pages generated")
            return False, errors

        if output.total_pages != len(output.pages):
            errors.append(f"Page count mismatch: declared {output.total_pages}, actual {len(output.pages)}")

        total_panels = sum(len(page.panels) for page in output.pages)
        if output.total_panels != total_panels:
            errors.append(f"Panel count mismatch: declared {output.total_panels}, actual {total_panels}")

        # Validate page numbering
        page_numbers = [page.page_number for page in output.pages]
        if page_numbers != sorted(page_numbers):
            errors.append("Pages are not in sequential order")

        if min(page_numbers) != 1:
            errors.append("Page numbering should start from 1")

        if len(set(page_numbers)) != len(page_numbers):
            errors.append("Duplicate page numbers found")

        return len(errors) == 0, errors

    def _validate_layouts(self, pages: List[PageLayout]) -> Tuple[bool, List[str], Dict[str, float]]:
        """Validate panel layouts."""
        errors = []
        quality_scores = {}

        layout_qualities = []
        panel_size_violations = 0
        overlap_violations = 0

        for page in pages:
            # Validate panel count per page
            panel_count = len(page.panels)
            if panel_count < self.quality_thresholds["min_panels_per_page"]:
                errors.append(f"Page {page.page_number}: Too few panels ({panel_count})")
            elif panel_count > self.quality_thresholds["max_panels_per_page"]:
                errors.append(f"Page {page.page_number}: Too many panels ({panel_count})")

            # Validate individual panels
            page_quality, page_errors = self._validate_page_panels(page)
            errors.extend(page_errors)
            layout_qualities.append(page_quality)

            # Check for overlapping panels
            overlaps = self._check_panel_overlaps(page.panels)
            overlap_violations += overlaps

            # Check panel sizes
            for panel in page.panels:
                if panel.size.width < self.quality_thresholds["min_panel_size"] or \
                   panel.size.height < self.quality_thresholds["min_panel_size"]:
                    panel_size_violations += 1
                    errors.append(f"Panel {panel.panel_id}: Panel too small")

        # Calculate quality scores
        quality_scores["layout_quality"] = sum(layout_qualities) / len(layout_qualities) if layout_qualities else 0
        quality_scores["panel_size_compliance"] = 1.0 - (panel_size_violations / max(1, sum(len(p.panels) for p in pages)))
        quality_scores["overlap_compliance"] = 1.0 - (overlap_violations / max(1, len(pages)))

        return len(errors) == 0, errors, quality_scores

    def _validate_page_panels(self, page: PageLayout) -> Tuple[float, List[str]]:
        """Validate panels on a single page."""
        errors = []
        quality_factors = []

        # Check panel positions are within bounds
        for panel in page.panels:
            if not (0 <= panel.position.x <= 1 and 0 <= panel.position.y <= 1):
                errors.append(f"Panel {panel.panel_id}: Position out of bounds")

            # Check panel size consistency
            if panel.size.width * panel.size.height < 0.01:  # Too small
                errors.append(f"Panel {panel.panel_id}: Panel area too small")

            # Validate aspect ratio
            expected_ratio = panel.size.aspect_ratio[0] / panel.size.aspect_ratio[1]
            actual_ratio = panel.size.width / panel.size.height if panel.size.height > 0 else 0
            ratio_error = abs(expected_ratio - actual_ratio) / expected_ratio if expected_ratio > 0 else 1

            if ratio_error > 0.2:  # 20% tolerance
                errors.append(f"Panel {panel.panel_id}: Aspect ratio mismatch")

            quality_factors.append(1.0 - ratio_error)

        # Assess layout balance
        balance_score = self._assess_visual_balance(page.panels)
        quality_factors.append(balance_score)

        # Assess layout variety
        variety_score = self._assess_layout_variety(page.panels)
        quality_factors.append(variety_score)

        page_quality = sum(quality_factors) / len(quality_factors) if quality_factors else 0
        return page_quality, errors

    def _check_panel_overlaps(self, panels: List[Panel]) -> int:
        """Check for overlapping panels on a page."""
        overlap_count = 0

        for i, panel1 in enumerate(panels):
            for panel2 in panels[i+1:]:
                if self._panels_overlap(panel1, panel2):
                    overlap_count += 1

        return overlap_count

    def _panels_overlap(self, panel1: Panel, panel2: Panel) -> bool:
        """Check if two panels overlap."""
        # Calculate panel boundaries
        x1_min, y1_min = panel1.position.x, panel1.position.y
        x1_max = x1_min + panel1.size.width
        y1_max = y1_min + panel1.size.height

        x2_min, y2_min = panel2.position.x, panel2.position.y
        x2_max = x2_min + panel2.size.width
        y2_max = y2_min + panel2.size.height

        # Check for overlap
        return not (x1_max <= x2_min or x2_max <= x1_min or y1_max <= y2_min or y2_max <= y1_min)

    def _assess_visual_balance(self, panels: List[Panel]) -> float:
        """Assess visual balance of panels on a page."""
        if len(panels) < 2:
            return 1.0

        # Calculate center of mass
        total_weight = 0
        weighted_x = 0
        weighted_y = 0

        for panel in panels:
            weight = panel.size.width * panel.size.height
            center_x = panel.position.x + panel.size.width / 2
            center_y = panel.position.y + panel.size.height / 2

            total_weight += weight
            weighted_x += center_x * weight
            weighted_y += center_y * weight

        if total_weight == 0:
            return 0.0

        center_of_mass_x = weighted_x / total_weight
        center_of_mass_y = weighted_y / total_weight

        # Distance from ideal center (0.5, 0.5)
        distance = math.sqrt((center_of_mass_x - 0.5)**2 + (center_of_mass_y - 0.5)**2)

        # Convert to score (closer to center = higher score)
        balance_score = max(0, 1.0 - distance * 2)  # Max distance is ~0.7, so *2 normalizes

        return balance_score

    def _assess_layout_variety(self, panels: List[Panel]) -> float:
        """Assess variety in panel layouts."""
        if len(panels) < 2:
            return 1.0

        # Count different panel shapes
        shapes = set(panel.shape for panel in panels)
        shape_variety = len(shapes) / len(PanelShapeType)

        # Assess size variety
        sizes = [(panel.size.width, panel.size.height) for panel in panels]
        unique_sizes = len(set(sizes))
        size_variety = min(unique_sizes / len(panels), 1.0)

        # Combine variety scores
        variety_score = (shape_variety + size_variety) / 2

        return variety_score

    def _validate_camera_work(self, pages: List[PageLayout]) -> Tuple[bool, List[str], Dict[str, float]]:
        """Validate camera work and shot composition."""
        errors = []
        quality_scores = {}

        all_camera_angles = []
        all_distances = []
        composition_qualities = []

        for page in pages:
            for panel in page.panels:
                camera = panel.camera_settings

                # Validate camera distance range
                if not (1 <= camera.distance <= 5):
                    errors.append(f"Panel {panel.panel_id}: Invalid camera distance {camera.distance}")

                # Validate camera tilt range
                if not (-45 <= camera.tilt <= 45):
                    errors.append(f"Panel {panel.panel_id}: Invalid camera tilt {camera.tilt}")

                # Validate depth of field range
                if not (0 <= camera.depth_of_field <= 1):
                    errors.append(f"Panel {panel.panel_id}: Invalid depth of field {camera.depth_of_field}")

                all_camera_angles.append(camera.angle)
                all_distances.append(camera.distance)

                # Assess composition quality
                comp_quality = self._assess_composition_quality(panel)
                composition_qualities.append(comp_quality)

        # Calculate camera variety
        unique_angles = len(set(all_camera_angles))
        angle_variety = unique_angles / len(CameraAngleType)

        unique_distances = len(set(all_distances))
        distance_variety = unique_distances / 5  # Max 5 distances

        camera_variety = (angle_variety + distance_variety) / 2

        # Calculate average composition quality
        avg_composition = sum(composition_qualities) / len(composition_qualities) if composition_qualities else 0

        quality_scores["camera_variety"] = camera_variety
        quality_scores["composition_quality"] = avg_composition

        # Check if camera variety meets minimum threshold
        if camera_variety < self.quality_thresholds["min_camera_variety"]:
            errors.append(f"Insufficient camera variety: {camera_variety:.2f} < {self.quality_thresholds['min_camera_variety']}")

        return len(errors) == 0, errors, quality_scores

    def _assess_composition_quality(self, panel: Panel) -> float:
        """Assess composition quality of a panel."""
        composition = panel.composition
        quality_factors = []

        # Check focal point placement
        focal_points = composition.focal_points
        if focal_points:
            # Assess if focal points follow composition rules
            if composition.rule == CompositionRuleType.RULE_OF_THIRDS:
                # Check if focal points are near rule of thirds lines
                thirds_quality = self._assess_rule_of_thirds_compliance(focal_points)
                quality_factors.append(thirds_quality)
            elif composition.rule == CompositionRuleType.CENTERED:
                # Check if focal points are near center
                center_quality = self._assess_center_composition(focal_points)
                quality_factors.append(center_quality)

        # Assess balance weight (should be reasonable)
        balance_factor = 1.0 - abs(composition.balance_weight - 0.5) * 2
        quality_factors.append(balance_factor)

        # Assess rhythm factor
        rhythm_factor = composition.rhythm_factor
        quality_factors.append(rhythm_factor)

        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.5

    def _assess_rule_of_thirds_compliance(self, focal_points: List[Tuple[float, float]]) -> float:
        """Assess compliance with rule of thirds."""
        if not focal_points:
            return 0.5

        thirds_lines = [1/3, 2/3]
        compliance_scores = []

        for x, y in focal_points:
            # Distance to nearest thirds line
            x_dist = min(abs(x - line) for line in thirds_lines)
            y_dist = min(abs(y - line) for line in thirds_lines)

            # Score based on proximity to thirds lines
            x_score = max(0, 1.0 - x_dist * 6)  # *6 to make 1/6 distance = 0 score
            y_score = max(0, 1.0 - y_dist * 6)

            compliance_scores.append((x_score + y_score) / 2)

        return sum(compliance_scores) / len(compliance_scores)

    def _assess_center_composition(self, focal_points: List[Tuple[float, float]]) -> float:
        """Assess center composition quality."""
        if not focal_points:
            return 0.5

        center_scores = []

        for x, y in focal_points:
            # Distance from center
            dist = math.sqrt((x - 0.5)**2 + (y - 0.5)**2)

            # Score based on proximity to center
            center_score = max(0, 1.0 - dist * 2)  # Max distance ~0.7, so *2 normalizes
            center_scores.append(center_score)

        return sum(center_scores) / len(center_scores)

    def _validate_reading_flow(self, pages: List[PageLayout]) -> Tuple[bool, List[str], Dict[str, float]]:
        """Validate reading flow and panel ordering."""
        errors = []
        quality_scores = {}

        flow_qualities = []

        for page in pages:
            reading_flow = page.reading_flow

            # Check if all panels are included in reading order
            panel_ids = {panel.panel_id for panel in page.panels}
            reading_order_ids = set(reading_flow.reading_order)

            if panel_ids != reading_order_ids:
                missing = panel_ids - reading_order_ids
                extra = reading_order_ids - panel_ids
                if missing:
                    errors.append(f"Page {page.page_number}: Panels missing from reading order: {missing}")
                if extra:
                    errors.append(f"Page {page.page_number}: Extra panels in reading order: {extra}")

            # Validate flow quality
            if not (0 <= reading_flow.flow_quality <= 1):
                errors.append(f"Page {page.page_number}: Invalid flow quality {reading_flow.flow_quality}")

            flow_qualities.append(reading_flow.flow_quality)

            # Check logical flow progression
            flow_logic_score = self._assess_flow_logic(page.panels, reading_flow.reading_order)
            flow_qualities.append(flow_logic_score)

        avg_flow_quality = sum(flow_qualities) / len(flow_qualities) if flow_qualities else 0
        quality_scores["reading_flow_quality"] = avg_flow_quality

        # Check if flow quality meets minimum threshold
        if avg_flow_quality < self.quality_thresholds["min_readability"]:
            errors.append(f"Poor reading flow quality: {avg_flow_quality:.2f} < {self.quality_thresholds['min_readability']}")

        return len(errors) == 0, errors, quality_scores

    def _assess_flow_logic(self, panels: List[Panel], reading_order: List[str]) -> float:
        """Assess logical flow of panel reading order."""
        if len(panels) < 2:
            return 1.0

        panel_positions = {panel.panel_id: panel.position for panel in panels}
        flow_scores = []

        for i in range(len(reading_order) - 1):
            current_id = reading_order[i]
            next_id = reading_order[i + 1]

            if current_id in panel_positions and next_id in panel_positions:
                current_pos = panel_positions[current_id]
                next_pos = panel_positions[next_id]

                # Assess if the flow makes spatial sense (left-to-right, top-to-bottom)
                dx = next_pos.x - current_pos.x
                dy = next_pos.y - current_pos.y

                # Prefer left-to-right, then top-to-bottom flow
                if dx > 0:  # Moving right is good
                    flow_scores.append(1.0)
                elif dx == 0 and dy > 0:  # Moving down in same column is okay
                    flow_scores.append(0.8)
                elif dx < 0 and dy > 0:  # New line (move down and left) is acceptable
                    flow_scores.append(0.6)
                else:  # Other movements are less natural
                    flow_scores.append(0.3)

        return sum(flow_scores) / len(flow_scores) if flow_scores else 0.5

    def _validate_composition(self, pages: List[PageLayout]) -> Tuple[bool, List[str], Dict[str, float]]:
        """Validate overall composition and visual hierarchy."""
        errors = []
        quality_scores = {}

        composition_qualities = []
        hierarchy_scores = []

        for page in pages:
            # Assess page-level composition
            page_composition = self._assess_page_composition(page)
            composition_qualities.append(page_composition)

            # Assess visual hierarchy
            hierarchy = self._assess_visual_hierarchy(page.panels)
            hierarchy_scores.append(hierarchy)

        avg_composition = sum(composition_qualities) / len(composition_qualities) if composition_qualities else 0
        avg_hierarchy = sum(hierarchy_scores) / len(hierarchy_scores) if hierarchy_scores else 0

        quality_scores["page_composition"] = avg_composition
        quality_scores["visual_hierarchy"] = avg_hierarchy

        return len(errors) == 0, errors, quality_scores

    def _assess_page_composition(self, page: PageLayout) -> float:
        """Assess overall page composition quality."""
        factors = []

        # Visual balance assessment
        balance = self._assess_visual_balance(page.panels)
        factors.append(balance)

        # Layout variety assessment
        variety = self._assess_layout_variety(page.panels)
        factors.append(variety)

        # Panel distribution assessment
        distribution = self._assess_panel_distribution(page.panels)
        factors.append(distribution)

        return sum(factors) / len(factors) if factors else 0

    def _assess_panel_distribution(self, panels: List[Panel]) -> float:
        """Assess how well panels are distributed across the page."""
        if len(panels) < 2:
            return 1.0

        # Divide page into quadrants and check distribution
        quadrants = {(0, 0): 0, (0, 1): 0, (1, 0): 0, (1, 1): 0}

        for panel in panels:
            center_x = panel.position.x + panel.size.width / 2
            center_y = panel.position.y + panel.size.height / 2

            quad_x = 0 if center_x < 0.5 else 1
            quad_y = 0 if center_y < 0.5 else 1

            quadrants[(quad_x, quad_y)] += 1

        # Calculate distribution score (prefer even distribution)
        occupied_quadrants = sum(1 for count in quadrants.values() if count > 0)
        distribution_score = occupied_quadrants / 4.0

        return distribution_score

    def _assess_visual_hierarchy(self, panels: List[Panel]) -> float:
        """Assess visual hierarchy clarity."""
        if len(panels) < 2:
            return 1.0

        # Sort panels by importance
        importance_order = {
            ImportanceLevel.CRITICAL: 4,
            ImportanceLevel.HIGH: 3,
            ImportanceLevel.MEDIUM: 2,
            ImportanceLevel.LOW: 1
        }

        panels_by_importance = sorted(panels, key=lambda p: importance_order.get(p.importance, 1), reverse=True)

        # Check if more important panels are given more visual weight
        hierarchy_scores = []

        for i, panel in enumerate(panels_by_importance[:-1]):
            next_panel = panels_by_importance[i + 1]

            # Current panel should have more visual weight than less important ones
            current_weight = panel.size.width * panel.size.height
            next_weight = next_panel.size.width * next_panel.size.height

            if current_weight >= next_weight:
                hierarchy_scores.append(1.0)
            else:
                # Partial score based on how much smaller
                ratio = current_weight / next_weight if next_weight > 0 else 0
                hierarchy_scores.append(ratio)

        return sum(hierarchy_scores) / len(hierarchy_scores) if hierarchy_scores else 0.5

    def _validate_layout_analysis(self, analysis, pages: List[PageLayout]) -> Tuple[bool, List[str]]:
        """Validate layout analysis consistency."""
        errors = []

        # Check total panels consistency
        actual_total = sum(len(page.panels) for page in pages)
        if analysis.total_panels != actual_total:
            errors.append(f"Layout analysis panel count mismatch: {analysis.total_panels} vs {actual_total}")

        # Check average panels per page
        actual_avg = actual_total / len(pages) if pages else 0
        if abs(analysis.average_panels_per_page - actual_avg) > 0.1:
            errors.append(f"Layout analysis average mismatch: {analysis.average_panels_per_page} vs {actual_avg}")

        # Validate score ranges
        score_fields = ["layout_variety", "composition_quality", "visual_balance", "pacing_effectiveness", "readability_score"]
        for field in score_fields:
            value = getattr(analysis, field)
            if not (0 <= value <= 1):
                errors.append(f"Layout analysis {field} out of range: {value}")

        return len(errors) == 0, errors

    def _validate_shot_list(self, shot_list: List, pages: List[PageLayout]) -> Tuple[bool, List[str]]:
        """Validate shot list consistency."""
        errors = []

        # Collect all panel IDs
        all_panel_ids = set()
        for page in pages:
            for panel in page.panels:
                all_panel_ids.add(panel.panel_id)

        # Check shot list panel references
        shot_panel_ids = {shot.panel_id for shot in shot_list}

        # All panels should have corresponding shots
        missing_shots = all_panel_ids - shot_panel_ids
        if missing_shots:
            errors.append(f"Missing shots for panels: {missing_shots}")

        # No shots should reference non-existent panels
        extra_shots = shot_panel_ids - all_panel_ids
        if extra_shots:
            errors.append(f"Shots reference non-existent panels: {extra_shots}")

        # Validate shot numbering
        shot_numbers = [shot.shot_number for shot in shot_list]
        if shot_numbers != list(range(1, len(shot_numbers) + 1)):
            errors.append("Shot list numbering is not sequential")

        return len(errors) == 0, errors

    def _calculate_overall_quality(self, quality_scores: Dict[str, float]) -> float:
        """Calculate overall quality score from individual metrics."""
        if not quality_scores:
            return 0.0

        # Weight different quality aspects
        weights = {
            "layout_quality": 0.25,
            "composition_quality": 0.20,
            "reading_flow_quality": 0.20,
            "camera_variety": 0.15,
            "visual_hierarchy": 0.10,
            "page_composition": 0.10
        }

        weighted_sum = 0
        total_weight = 0

        for metric, score in quality_scores.items():
            if metric in weights:
                weighted_sum += score * weights[metric]
                total_weight += weights[metric]

        # Include any remaining metrics with equal weight
        remaining_metrics = set(quality_scores.keys()) - set(weights.keys())
        if remaining_metrics:
            remaining_weight = max(0, 1.0 - total_weight) / len(remaining_metrics)
            for metric in remaining_metrics:
                weighted_sum += quality_scores[metric] * remaining_weight
                total_weight += remaining_weight

        return weighted_sum / total_weight if total_weight > 0 else 0

    def get_quality_report(self, quality_scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate detailed quality report."""
        overall_quality = quality_scores.get("overall_quality", 0)

        # Grade assignment
        if overall_quality >= 0.9:
            grade = "A"
            description = "Excellent layout quality"
        elif overall_quality >= 0.8:
            grade = "B"
            description = "Good layout quality"
        elif overall_quality >= 0.7:
            grade = "C"
            description = "Acceptable layout quality"
        elif overall_quality >= 0.6:
            grade = "D"
            description = "Below average layout quality"
        else:
            grade = "F"
            description = "Poor layout quality"

        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []

        for metric, score in quality_scores.items():
            if metric != "overall_quality":
                if score >= 0.8:
                    strengths.append(f"{metric}: {score:.2f}")
                elif score < 0.6:
                    weaknesses.append(f"{metric}: {score:.2f}")

        # Generate recommendations
        recommendations = []
        if quality_scores.get("camera_variety", 0) < 0.5:
            recommendations.append("Increase camera angle variety for more dynamic storytelling")
        if quality_scores.get("reading_flow_quality", 0) < 0.7:
            recommendations.append("Improve panel layout for better reading flow")
        if quality_scores.get("composition_quality", 0) < 0.6:
            recommendations.append("Apply composition rules more consistently")
        if quality_scores.get("visual_hierarchy", 0) < 0.6:
            recommendations.append("Strengthen visual hierarchy to guide reader attention")

        return {
            "overall_quality": overall_quality,
            "grade": grade,
            "description": description,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "detailed_scores": quality_scores
        }