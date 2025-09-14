"""Name Generator Processor for Phase 4 - Panel Layout and Composition Generation."""

from typing import Dict, Any, List, Optional, Tuple
import math
import random
from ..schemas import (
    PageLayout, Panel, PanelSize, PanelPosition, CameraSettings,
    CompositionGuide, ReadingFlow, LayoutPatternType, CameraAngleType,
    CompositionRuleType, PanelShapeType, BorderStyleType, ImportanceLevel,
    TransitionType, PanelTransition, DramaticMoment, ShotListItem,
    LayoutAnalysis, CameraStatistics, LayoutTemplate
)

class NameGenerator:
    """Core processor for generating manga panel layouts and compositions."""

    def __init__(self):
        """Initialize the name generator with configuration data."""
        self.layout_patterns = self._initialize_layout_patterns()
        self.camera_angles = self._initialize_camera_angles()
        self.composition_rules = self._initialize_composition_rules()
        self.panel_shapes = self._initialize_panel_shapes()
        self.layout_templates = self._initialize_layout_templates()

    def _initialize_layout_patterns(self) -> Dict[LayoutPatternType, Dict[str, Any]]:
        """Initialize layout patterns for different manga styles."""
        return {
            LayoutPatternType.STANDARD: {
                "panels_per_page": 5,
                "variation": 2,
                "complexity": "medium",
                "preferred_shapes": [PanelShapeType.RECTANGLE, PanelShapeType.SQUARE]
            },
            LayoutPatternType.ACTION: {
                "panels_per_page": 4,
                "variation": 3,
                "complexity": "high",
                "preferred_shapes": [PanelShapeType.HORIZONTAL, PanelShapeType.IRREGULAR]
            },
            LayoutPatternType.DIALOGUE: {
                "panels_per_page": 6,
                "variation": 1,
                "complexity": "low",
                "preferred_shapes": [PanelShapeType.RECTANGLE, PanelShapeType.VERTICAL]
            },
            LayoutPatternType.DRAMATIC: {
                "panels_per_page": 3,
                "variation": 2,
                "complexity": "high",
                "preferred_shapes": [PanelShapeType.SQUARE, PanelShapeType.IRREGULAR]
            }
        }

    def _initialize_camera_angles(self) -> Dict[CameraAngleType, Dict[str, Any]]:
        """Initialize camera angle configurations."""
        return {
            CameraAngleType.EXTREME_LONG: {"distance": 5, "impact": "establishing", "frequency": 0.05},
            CameraAngleType.LONG: {"distance": 4, "impact": "context", "frequency": 0.15},
            CameraAngleType.MEDIUM: {"distance": 3, "impact": "standard", "frequency": 0.40},
            CameraAngleType.CLOSE: {"distance": 2, "impact": "emotion", "frequency": 0.25},
            CameraAngleType.EXTREME_CLOSE: {"distance": 1, "impact": "detail", "frequency": 0.10},
            CameraAngleType.BIRD_EYE: {"distance": 4, "impact": "overview", "frequency": 0.03},
            CameraAngleType.WORM_EYE: {"distance": 3, "impact": "dramatic", "frequency": 0.02}
        }

    def _initialize_composition_rules(self) -> Dict[CompositionRuleType, float]:
        """Initialize composition rule weights."""
        return {
            CompositionRuleType.RULE_OF_THIRDS: 0.4,
            CompositionRuleType.GOLDEN_RATIO: 0.2,
            CompositionRuleType.SYMMETRICAL: 0.15,
            CompositionRuleType.DIAGONAL: 0.15,
            CompositionRuleType.CENTERED: 0.1
        }

    def _initialize_panel_shapes(self) -> Dict[PanelShapeType, Dict[str, Any]]:
        """Initialize panel shape configurations."""
        return {
            PanelShapeType.RECTANGLE: {
                "frequency": 0.7,
                "aspect_ratios": [(4, 3), (16, 9), (3, 2)]
            },
            PanelShapeType.SQUARE: {
                "frequency": 0.15,
                "aspect_ratios": [(1, 1)]
            },
            PanelShapeType.VERTICAL: {
                "frequency": 0.08,
                "aspect_ratios": [(2, 3), (9, 16)]
            },
            PanelShapeType.HORIZONTAL: {
                "frequency": 0.05,
                "aspect_ratios": [(3, 1), (4, 1)]
            },
            PanelShapeType.IRREGULAR: {
                "frequency": 0.02,
                "aspect_ratios": [(3, 2), (5, 3)]
            }
        }

    def _initialize_layout_templates(self) -> List[LayoutTemplate]:
        """Initialize layout templates for different panel counts."""
        templates = []

        # 4-panel template
        templates.append(LayoutTemplate(
            template_id="four_panel_grid",
            name="Four Panel Grid",
            panel_count=4,
            grid_layout=(2, 2),
            panel_positions=[
                PanelPosition(x=0.0, y=0.0, z_index=0),
                PanelPosition(x=0.5, y=0.0, z_index=0),
                PanelPosition(x=0.0, y=0.5, z_index=0),
                PanelPosition(x=0.5, y=0.5, z_index=0)
            ],
            panel_sizes=[
                PanelSize(width=0.48, height=0.48, aspect_ratio=(1, 1)),
                PanelSize(width=0.48, height=0.48, aspect_ratio=(1, 1)),
                PanelSize(width=0.48, height=0.48, aspect_ratio=(1, 1)),
                PanelSize(width=0.48, height=0.48, aspect_ratio=(1, 1))
            ],
            suitable_genres=["action", "drama"],
            complexity_rating=2
        ))

        # 6-panel template
        templates.append(LayoutTemplate(
            template_id="six_panel_standard",
            name="Six Panel Standard",
            panel_count=6,
            grid_layout=(3, 2),
            panel_positions=[
                PanelPosition(x=0.0, y=0.0, z_index=0),
                PanelPosition(x=0.33, y=0.0, z_index=0),
                PanelPosition(x=0.66, y=0.0, z_index=0),
                PanelPosition(x=0.0, y=0.5, z_index=0),
                PanelPosition(x=0.33, y=0.5, z_index=0),
                PanelPosition(x=0.66, y=0.5, z_index=0)
            ],
            panel_sizes=[
                PanelSize(width=0.32, height=0.48, aspect_ratio=(2, 3)),
                PanelSize(width=0.32, height=0.48, aspect_ratio=(2, 3)),
                PanelSize(width=0.32, height=0.48, aspect_ratio=(2, 3)),
                PanelSize(width=0.32, height=0.48, aspect_ratio=(2, 3)),
                PanelSize(width=0.32, height=0.48, aspect_ratio=(2, 3)),
                PanelSize(width=0.32, height=0.48, aspect_ratio=(2, 3))
            ],
            suitable_genres=["dialogue", "slice_of_life"],
            complexity_rating=1
        ))

        return templates

    def generate_panel_layouts(
        self,
        scenes: List[Dict[str, Any]],
        page_allocation: List[Dict[str, Any]],
        genre: str,
        pacing: Dict[str, Any]
    ) -> List[PageLayout]:
        """
        Generate panel layouts for all pages based on scenes and pacing.

        Args:
            scenes: List of scene data from Phase 3
            page_allocation: Page allocation data from Phase 3
            genre: Genre from Phase 1
            pacing: Pacing data from Phase 3

        Returns:
            List of complete page layouts
        """
        pages = []

        # Determine base layout pattern
        layout_pattern = self._select_layout_pattern(genre, pacing)

        for page_info in page_allocation:
            page_num = page_info.get("page", 1)
            page_scenes = page_info.get("scenes", [])

            # Get scenes for this page
            scenes_on_page = [s for s in scenes if s.get("scene_number") in page_scenes]

            # Generate page layout
            page_layout = self._generate_single_page_layout(
                page_num, scenes_on_page, layout_pattern, genre
            )

            pages.append(page_layout)

        return pages

    def _select_layout_pattern(self, genre: str, pacing: Dict[str, Any]) -> Dict[str, Any]:
        """Select appropriate layout pattern based on genre and pacing."""
        pattern_type = LayoutPatternType.STANDARD

        if genre == "action":
            pattern_type = LayoutPatternType.ACTION
        elif pacing.get("rhythm") == "steady":
            pattern_type = LayoutPatternType.DIALOGUE
        elif any(p > 0.5 for p in pacing.get("tension_curve", [])):
            pattern_type = LayoutPatternType.DRAMATIC

        return self.layout_patterns[pattern_type]

    def _generate_single_page_layout(
        self,
        page_num: int,
        scenes: List[Dict[str, Any]],
        layout_pattern: Dict[str, Any],
        genre: str
    ) -> PageLayout:
        """Generate layout for a single page."""
        # Calculate panel count
        panel_count = self._calculate_panel_count(scenes, layout_pattern)

        # Create panel layout
        panels = self._create_panel_layout(panel_count, scenes, page_num, genre)

        # Assign camera work
        panels_with_camera = self._assign_camera_work(panels, scenes, genre)

        # Establish reading order and flow
        reading_flow = self._establish_reading_flow(panels_with_camera)

        # Determine page importance
        page_importance = self._determine_page_importance(scenes)

        return PageLayout(
            page_number=page_num,
            panels=panels_with_camera,
            scene_numbers=[s.get("scene_number", 0) for s in scenes],
            layout_type=LayoutPatternType.STANDARD,  # Would be determined by pattern
            reading_flow=reading_flow,
            page_impact=page_importance,
            page_emotion=self._determine_page_emotion(scenes)
        )

    def _calculate_panel_count(
        self,
        scenes: List[Dict[str, Any]],
        layout_pattern: Dict[str, Any]
    ) -> int:
        """Calculate optimal panel count for page."""
        base_count = layout_pattern["panels_per_page"]
        variation = layout_pattern["variation"]

        # Adjust for scene importance
        importance_modifier = 0
        for scene in scenes:
            if scene.get("importance") == "high":
                importance_modifier -= 1  # Fewer panels for important scenes
            elif scene.get("importance") == "low":
                importance_modifier += 1  # More panels for less important scenes

        # Apply variation
        variation_amount = random.randint(-variation, variation)

        final_count = base_count + importance_modifier + variation_amount

        # Clamp between reasonable limits
        return max(2, min(8, final_count))

    def _create_panel_layout(
        self,
        panel_count: int,
        scenes: List[Dict[str, Any]],
        page_num: int,
        genre: str
    ) -> List[Panel]:
        """Create specific panel layout for a page."""
        panels = []

        # Find appropriate template or create custom layout
        template = self._find_suitable_template(panel_count, genre)

        if template:
            panels = self._apply_template(template, scenes, page_num)
        else:
            panels = self._create_custom_layout(panel_count, scenes, page_num, genre)

        return panels

    def _find_suitable_template(self, panel_count: int, genre: str) -> Optional[LayoutTemplate]:
        """Find a suitable layout template."""
        for template in self.layout_templates:
            if (template.panel_count == panel_count and
                (not template.suitable_genres or genre in template.suitable_genres)):
                return template
        return None

    def _apply_template(
        self,
        template: LayoutTemplate,
        scenes: List[Dict[str, Any]],
        page_num: int
    ) -> List[Panel]:
        """Apply a layout template to create panels."""
        panels = []

        for i in range(template.panel_count):
            panel_id = f"p{page_num}_panel{i+1}"

            # Get template data
            position = template.panel_positions[i] if i < len(template.panel_positions) else PanelPosition(x=0, y=0)
            size = template.panel_sizes[i] if i < len(template.panel_sizes) else PanelSize(width=0.2, height=0.2, aspect_ratio=(1, 1))

            # Determine scene reference
            scene_index = min(i * len(scenes) // template.panel_count, len(scenes) - 1) if scenes else 0
            scene = scenes[scene_index] if scenes else {}

            panel = Panel(
                panel_id=panel_id,
                size=size,
                position=position,
                shape=self._select_panel_shape(size),
                border_style=self._select_border_style(scene.get("emotion", "neutral")),
                camera_settings=self._create_default_camera_settings(),
                composition=self._create_default_composition(),
                content_description=scene.get("description", f"Panel {i+1}"),
                scene_reference=scene.get("scene_number", 0),
                importance=ImportanceLevel(scene.get("importance", "medium"))
            )

            panels.append(panel)

        return panels

    def _create_custom_layout(
        self,
        panel_count: int,
        scenes: List[Dict[str, Any]],
        page_num: int,
        genre: str
    ) -> List[Panel]:
        """Create custom panel layout."""
        panels = []

        # Calculate grid layout
        grid_rows, grid_cols = self._calculate_grid_layout(panel_count)

        for i in range(panel_count):
            panel_id = f"p{page_num}_panel{i+1}"

            # Calculate position in grid
            row = i // grid_cols
            col = i % grid_cols

            # Calculate normalized position and size
            x = col / grid_cols
            y = row / grid_rows
            width = 1.0 / grid_cols * 0.95  # 5% margin
            height = 1.0 / grid_rows * 0.95

            position = PanelPosition(x=x, y=y, z_index=0)
            size = PanelSize(width=width, height=height, aspect_ratio=(4, 3))

            # Determine scene reference
            scene_index = min(i * len(scenes) // panel_count, len(scenes) - 1) if scenes else 0
            scene = scenes[scene_index] if scenes else {}

            panel = Panel(
                panel_id=panel_id,
                size=size,
                position=position,
                shape=self._select_panel_shape(size),
                border_style=self._select_border_style(scene.get("emotion", "neutral")),
                camera_settings=self._create_default_camera_settings(),
                composition=self._create_default_composition(),
                content_description=scene.get("description", f"Panel {i+1}"),
                scene_reference=scene.get("scene_number", 0),
                importance=ImportanceLevel(scene.get("importance", "medium"))
            )

            panels.append(panel)

        return panels

    def _calculate_grid_layout(self, panel_count: int) -> Tuple[int, int]:
        """Calculate optimal grid layout for panel count."""
        if panel_count <= 2:
            return (1, panel_count)
        elif panel_count <= 4:
            return (2, 2)
        elif panel_count <= 6:
            return (2, 3)
        elif panel_count <= 8:
            return (2, 4)
        else:
            return (3, 3)

    def _select_panel_shape(self, size: PanelSize) -> PanelShapeType:
        """Select appropriate panel shape based on size."""
        aspect_ratio = size.width / size.height if size.height > 0 else 1

        if 0.9 <= aspect_ratio <= 1.1:
            return PanelShapeType.SQUARE
        elif aspect_ratio > 1.5:
            return PanelShapeType.HORIZONTAL
        elif aspect_ratio < 0.7:
            return PanelShapeType.VERTICAL
        else:
            return PanelShapeType.RECTANGLE

    def _select_border_style(self, emotion: str) -> BorderStyleType:
        """Select border style based on emotion."""
        emotion_borders = {
            "angry": BorderStyleType.JAGGED,
            "shocked": BorderStyleType.WAVY,
            "dreamy": BorderStyleType.DOTTED,
            "intense": BorderStyleType.THICK,
            "flashback": BorderStyleType.DASHED
        }

        return emotion_borders.get(emotion, BorderStyleType.SOLID)

    def _create_default_camera_settings(self) -> CameraSettings:
        """Create default camera settings."""
        return CameraSettings(
            angle=CameraAngleType.MEDIUM,
            distance=3,
            tilt=0.0,
            focus_point=(0.5, 0.5),
            depth_of_field=0.5
        )

    def _create_default_composition(self) -> CompositionGuide:
        """Create default composition guide."""
        return CompositionGuide(
            rule=CompositionRuleType.RULE_OF_THIRDS,
            focal_points=[(0.33, 0.33)],
            leading_lines=[],
            balance_weight=0.5,
            rhythm_factor=0.5
        )

    def _assign_camera_work(
        self,
        panels: List[Panel],
        scenes: List[Dict[str, Any]],
        genre: str
    ) -> List[Panel]:
        """Assign camera angles and composition to panels."""
        updated_panels = []

        for i, panel in enumerate(panels):
            # Determine appropriate camera angle
            camera_angle = self._select_camera_angle(panel, scenes, i, genre)

            # Create camera settings
            camera_settings = CameraSettings(
                angle=camera_angle,
                distance=self.camera_angles[camera_angle]["distance"],
                tilt=random.uniform(-15, 15),
                focus_point=self._calculate_focus_point(panel),
                depth_of_field=random.uniform(0.3, 0.8)
            )

            # Create composition guide
            composition = self._create_composition_guide(panel, camera_angle)

            # Update panel
            updated_panel = Panel(
                panel_id=panel.panel_id,
                size=panel.size,
                position=panel.position,
                shape=panel.shape,
                border_style=panel.border_style,
                camera_settings=camera_settings,
                composition=composition,
                content_description=panel.content_description,
                scene_reference=panel.scene_reference,
                importance=panel.importance
            )

            updated_panels.append(updated_panel)

        return updated_panels

    def _select_camera_angle(
        self,
        panel: Panel,
        scenes: List[Dict[str, Any]],
        panel_index: int,
        genre: str
    ) -> CameraAngleType:
        """Select appropriate camera angle for panel."""
        # Weighted random selection based on frequency
        angles = list(self.camera_angles.keys())
        weights = [self.camera_angles[angle]["frequency"] for angle in angles]

        # Adjust weights based on context
        if panel.importance == ImportanceLevel.HIGH:
            # Prefer close-up shots for important panels
            close_index = angles.index(CameraAngleType.CLOSE)
            weights[close_index] *= 2

        if genre == "action":
            # Prefer dynamic angles for action
            bird_index = angles.index(CameraAngleType.BIRD_EYE)
            worm_index = angles.index(CameraAngleType.WORM_EYE)
            weights[bird_index] *= 1.5
            weights[worm_index] *= 1.5

        return random.choices(angles, weights=weights)[0]

    def _calculate_focus_point(self, panel: Panel) -> Tuple[float, float]:
        """Calculate focus point for panel."""
        # Use rule of thirds intersection points
        thirds_points = [
            (0.33, 0.33), (0.66, 0.33),
            (0.33, 0.66), (0.66, 0.66)
        ]

        return random.choice(thirds_points)

    def _create_composition_guide(
        self,
        panel: Panel,
        camera_angle: CameraAngleType
    ) -> CompositionGuide:
        """Create composition guide for panel."""
        # Select composition rule based on camera angle and importance
        if panel.importance == ImportanceLevel.HIGH:
            rule = CompositionRuleType.GOLDEN_RATIO
        elif camera_angle in [CameraAngleType.EXTREME_CLOSE, CameraAngleType.CLOSE]:
            rule = CompositionRuleType.CENTERED
        else:
            rule = CompositionRuleType.RULE_OF_THIRDS

        # Generate focal points based on rule
        focal_points = self._generate_focal_points(rule)

        return CompositionGuide(
            rule=rule,
            focal_points=focal_points,
            leading_lines=[],
            balance_weight=random.uniform(0.3, 0.7),
            rhythm_factor=random.uniform(0.4, 0.8)
        )

    def _generate_focal_points(self, rule: CompositionRuleType) -> List[Tuple[float, float]]:
        """Generate focal points based on composition rule."""
        if rule == CompositionRuleType.RULE_OF_THIRDS:
            return [(0.33, 0.33), (0.66, 0.66)]
        elif rule == CompositionRuleType.GOLDEN_RATIO:
            return [(0.38, 0.38), (0.62, 0.62)]
        elif rule == CompositionRuleType.CENTERED:
            return [(0.5, 0.5)]
        elif rule == CompositionRuleType.DIAGONAL:
            return [(0.25, 0.25), (0.75, 0.75)]
        else:
            return [(0.4, 0.4), (0.6, 0.6)]

    def _establish_reading_flow(self, panels: List[Panel]) -> ReadingFlow:
        """Establish reading order and flow for panels."""
        # Sort panels by position (left-to-right, top-to-bottom)
        sorted_panels = sorted(panels, key=lambda p: (p.position.y, p.position.x))
        reading_order = [panel.panel_id for panel in sorted_panels]

        # Calculate flow quality based on spatial progression
        flow_quality = self._calculate_flow_quality(panels, reading_order)

        # Identify attention points
        attention_points = [(0.33, 0.33), (0.66, 0.66)]  # Default rule of thirds

        return ReadingFlow(
            reading_order=reading_order,
            flow_quality=flow_quality,
            attention_points=attention_points,
            flow_disruptions=[],
            estimated_reading_time=len(panels) * 3.0  # 3 seconds per panel
        )

    def _calculate_flow_quality(
        self,
        panels: List[Panel],
        reading_order: List[str]
    ) -> float:
        """Calculate reading flow quality score."""
        if len(panels) < 2:
            return 1.0

        panel_positions = {panel.panel_id: panel.position for panel in panels}
        flow_scores = []

        for i in range(len(reading_order) - 1):
            current_id = reading_order[i]
            next_id = reading_order[i + 1]

            current_pos = panel_positions[current_id]
            next_pos = panel_positions[next_id]

            # Assess flow naturalness
            dx = next_pos.x - current_pos.x
            dy = next_pos.y - current_pos.y

            # Prefer left-to-right, then top-to-bottom
            if dx > 0:  # Moving right
                flow_scores.append(1.0)
            elif dx == 0 and dy > 0:  # Moving down
                flow_scores.append(0.8)
            elif dx < 0 and dy > 0:  # New line
                flow_scores.append(0.6)
            else:
                flow_scores.append(0.3)

        return sum(flow_scores) / len(flow_scores)

    def _determine_page_importance(self, scenes: List[Dict[str, Any]]) -> ImportanceLevel:
        """Determine overall page importance based on scenes."""
        if not scenes:
            return ImportanceLevel.MEDIUM

        importance_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        total_score = sum(importance_scores.get(scene.get("importance", "medium"), 2) for scene in scenes)
        avg_score = total_score / len(scenes)

        if avg_score >= 3.5:
            return ImportanceLevel.CRITICAL
        elif avg_score >= 2.5:
            return ImportanceLevel.HIGH
        elif avg_score >= 1.5:
            return ImportanceLevel.MEDIUM
        else:
            return ImportanceLevel.LOW

    def _determine_page_emotion(self, scenes: List[Dict[str, Any]]) -> str:
        """Determine overall page emotion based on scenes."""
        if not scenes:
            return "neutral"

        emotions = [scene.get("emotion", "neutral") for scene in scenes]

        # Return most common emotion
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        return max(emotion_counts, key=emotion_counts.get)