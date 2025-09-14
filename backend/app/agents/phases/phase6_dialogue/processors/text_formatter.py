"""Phase 6: Text Formatter and Placement Processor.

This module handles text placement, typography, bubble design, and readability
optimization for manga dialogue and narration elements.
"""

from typing import Dict, Any, List, Optional, Tuple
import math
import logging

from ..schemas import (
    TextPlacement, BubbleDesign, TypographySpecifications, TypographyFont,
    TypographySpecification, ReadabilityOptimization, FlowAnalysis,
    DensityAnalysis, InterferenceAnalysis, ReadabilityIssue,
    Position, TextArea, BorderProperties, FillProperties, TailProperties,
    PanelDialogue, DialogueElement, TextPlacementTask,
    BubbleStyle, BubbleShape, BorderStyle, TailDirection, ElementType,
    PlacementPosition, DialogueType, ImportanceLevel, SpeechPattern,
    TypographyStyle, FontWeight, TextAlignment, TailStyle,
    JapaneseTextRules, SpecialCharacters
)


logger = logging.getLogger(__name__)


class TextFormatter:
    """Text formatting and placement processor for Phase 6."""

    def __init__(self):
        """Initialize text formatter with placement rules and settings."""

        # Text placement rules based on panel composition
        self.placement_rules = {
            "close_up": {
                "preferred_positions": ["top", "bottom"],
                "avoid_positions": ["center"],
                "max_text_coverage": 0.3
            },
            "medium_shot": {
                "preferred_positions": ["top", "sides", "bottom"],
                "avoid_positions": [],
                "max_text_coverage": 0.4
            },
            "wide_shot": {
                "preferred_positions": ["anywhere"],
                "avoid_positions": [],
                "max_text_coverage": 0.5
            },
            "action_scene": {
                "preferred_positions": ["edges"],
                "avoid_positions": ["center", "movement_path"],
                "max_text_coverage": 0.25
            }
        }

        # Japanese text formatting rules
        self.japanese_text_rules = JapaneseTextRules(
            reading_direction="right_to_left",
            vertical_text=True,
            character_spacing="normal",
            line_spacing=1.2,
            punctuation_handling="japanese_rules"
        )

        # Typography styles by genre
        self.genre_typography = {
            "action": {
                "primary_font": "bold_manga_font",
                "emphasis_style": "heavy_bold",
                "line_weight": "thick"
            },
            "romance": {
                "primary_font": "elegant_manga_font",
                "emphasis_style": "italic",
                "line_weight": "medium"
            },
            "mystery": {
                "primary_font": "atmospheric_manga_font",
                "emphasis_style": "subtle_bold",
                "line_weight": "varied"
            },
            "slice_of_life": {
                "primary_font": "friendly_manga_font",
                "emphasis_style": "gentle_bold",
                "line_weight": "light"
            }
        }

        # Quality thresholds
        self.max_text_density = 80
        self.min_distance_between_elements = 0.15
        self.max_reading_time_per_panel = 15.0

    async def create_text_placements(
        self,
        dialogue_content: List[PanelDialogue],
        panel_specifications: List[Dict[str, Any]],
        generated_images: Optional[List[Any]] = None
    ) -> List[TextPlacement]:
        """Create text placement specifications for dialogue content.

        Args:
            dialogue_content: Generated dialogue for all panels
            panel_specifications: Panel layout specifications from Phase 4
            generated_images: Generated images from Phase 5

        Returns:
            List of text placement specifications
        """

        text_placements = []

        try:
            for panel_dialogue in dialogue_content:
                panel_id = panel_dialogue.panel_id

                # Find panel specification
                panel_spec = next(
                    (spec for spec in panel_specifications if spec.get("panel_id") == panel_id),
                    {}
                )

                # Find generated image
                panel_image = None
                if generated_images:
                    panel_image = next(
                        (img for img in generated_images if img.panel_id == panel_id),
                        None
                    )

                # Create placements for dialogue elements
                for i, dialogue_elem in enumerate(panel_dialogue.dialogue_elements):
                    placement = await self._create_dialogue_placement(
                        dialogue_elem, panel_spec, panel_image, i, len(panel_dialogue.dialogue_elements)
                    )
                    text_placements.append(placement)

                # Create placement for narration if exists
                if panel_dialogue.narration:
                    narration_placement = await self._create_narration_placement(
                        panel_dialogue.narration, panel_spec, panel_image, len(panel_dialogue.dialogue_elements)
                    )
                    text_placements.append(narration_placement)

        except Exception as e:
            logger.error(f"Error creating text placements: {e}")

        return text_placements

    async def _create_dialogue_placement(
        self,
        dialogue_element: DialogueElement,
        panel_spec: Dict[str, Any],
        panel_image: Any,
        dialogue_index: int,
        total_dialogues: int
    ) -> TextPlacement:
        """Create placement specification for dialogue element."""

        panel_id = panel_spec.get("panel_id", "")
        camera_angle = panel_spec.get("camera_angle", "medium_shot")
        panel_size = panel_spec.get("size", "medium")

        # Determine optimal position
        position = await self._determine_dialogue_position(
            camera_angle, panel_size, dialogue_index, total_dialogues
        )

        # Determine bubble style
        dialogue_type = dialogue_element.dialogue_type.value
        bubble_style = self._get_bubble_style_for_type(dialogue_type)

        # Calculate text area dimensions
        text_area = await self._calculate_text_area(
            dialogue_element.text,
            bubble_style,
            panel_spec
        )

        # Determine tail direction
        tail_direction = await self._determine_tail_direction(
            position, panel_spec.get("characters", []), dialogue_element.speaker
        )

        placement = TextPlacement(
            panel_id=panel_id,
            element_type=ElementType.DIALOGUE,
            speaker=dialogue_element.speaker,
            text_content=dialogue_element.text,
            dialogue_type=dialogue_element.dialogue_type,
            position=position,
            bubble_style=BubbleStyle(bubble_style),
            text_area=text_area,
            reading_order=dialogue_index + 1,
            importance=dialogue_element.importance,
            speech_pattern=dialogue_element.speech_pattern,
            emotion=dialogue_element.emotion,
            tail_direction=TailDirection(tail_direction) if tail_direction else None
        )

        return placement

    async def _create_narration_placement(
        self,
        narration: Any,  # NarrationElement from schemas
        panel_spec: Dict[str, Any],
        panel_image: Any,
        existing_dialogues: int
    ) -> TextPlacement:
        """Create placement specification for narration."""

        panel_id = panel_spec.get("panel_id", "")

        # Narration typically goes at top or bottom
        position = Position(
            x=0.5,
            y=0.1 if narration.position.value == "top" else 0.9,
            anchor="top" if narration.position.value == "top" else "bottom"
        )

        # Calculate text area for narration box
        text_area = await self._calculate_text_area(
            narration.text,
            "rectangular_box",
            panel_spec
        )

        placement = TextPlacement(
            panel_id=panel_id,
            element_type=ElementType.NARRATION,
            speaker=None,
            text_content=narration.text,
            dialogue_type=DialogueType.NARRATION,
            position=position,
            bubble_style=BubbleStyle.RECTANGULAR_BOX,
            text_area=text_area,
            reading_order=existing_dialogues + 1,
            importance=narration.importance,
            narration_style=narration.style
        )

        return placement

    async def _determine_dialogue_position(
        self,
        camera_angle: str,
        panel_size: str,
        dialogue_index: int,
        total_dialogues: int
    ) -> Position:
        """Determine optimal position for dialogue bubble."""

        # Get placement rules for camera angle
        rules = self.placement_rules.get(camera_angle, self.placement_rules["medium_shot"])
        preferred_positions = rules["preferred_positions"]

        if total_dialogues == 1:
            # Single dialogue - use best position
            if "top" in preferred_positions:
                return Position(x=0.7, y=0.2, anchor="top_right")
            elif "sides" in preferred_positions:
                return Position(x=0.1, y=0.3, anchor="left")
            else:
                return Position(x=0.5, y=0.8, anchor="bottom")
        else:
            # Multiple dialogues - distribute across preferred positions
            if dialogue_index == 0:
                # First dialogue gets priority position
                return Position(x=0.7, y=0.2, anchor="top_right")
            elif dialogue_index == 1:
                # Second dialogue on opposite side/position
                return Position(x=0.3, y=0.7, anchor="bottom_left")
            else:
                # Additional dialogues fill remaining space
                return Position(x=0.5, y=0.5, anchor="center")

    async def _calculate_text_area(
        self,
        text: str,
        bubble_style: str,
        panel_spec: Dict[str, Any]
    ) -> TextArea:
        """Calculate text area dimensions and properties."""

        # Estimate text dimensions based on length and style
        text_length = len(text)
        estimated_lines = max(1, text_length // 12)  # ~12 chars per line

        # Base dimensions (relative to panel)
        if bubble_style == "rectangular_box":
            # Narration boxes are typically wider and shorter
            width_ratio = min(0.8, text_length * 0.03)
            height_ratio = max(0.1, estimated_lines * 0.05)
        else:
            # Speech bubbles are more circular/oval
            width_ratio = min(0.4, text_length * 0.025)
            height_ratio = max(0.15, estimated_lines * 0.08)

        # Adjust for panel size
        panel_size = panel_spec.get("size", "medium")
        size_multiplier = {"small": 0.8, "medium": 1.0, "large": 1.2, "splash": 1.5}.get(panel_size, 1.0)

        text_area = TextArea(
            width_ratio=width_ratio * size_multiplier,
            height_ratio=height_ratio * size_multiplier,
            estimated_lines=estimated_lines,
            font_size=self._calculate_font_size(text_length, panel_size),
            padding={"top": 8, "bottom": 8, "left": 12, "right": 12},
            text_alignment=TextAlignment.CENTER
        )

        return text_area

    def _calculate_font_size(self, text_length: int, panel_size: str) -> int:
        """Calculate appropriate font size."""

        base_sizes = {"small": 10, "medium": 12, "large": 14, "splash": 16}
        base_size = base_sizes.get(panel_size, 12)

        # Adjust for text length
        if text_length > 20:
            base_size -= 1
        elif text_length < 10:
            base_size += 1

        return max(8, min(18, base_size))

    async def _determine_tail_direction(
        self,
        bubble_position: Position,
        panel_characters: List[Dict[str, Any]],
        speaker: Optional[str]
    ) -> str:
        """Determine direction for speech bubble tail."""

        if not speaker or not panel_characters:
            return "down"

        # Simple tail direction based on bubble position
        bubble_x = bubble_position.x
        bubble_y = bubble_position.y

        if bubble_y < 0.3:  # Bubble at top
            return "down"
        elif bubble_y > 0.7:  # Bubble at bottom
            return "up"
        elif bubble_x < 0.3:  # Bubble at left
            return "right"
        elif bubble_x > 0.7:  # Bubble at right
            return "left"
        else:
            return "down"  # Default

    def _get_bubble_style_for_type(self, dialogue_type: str) -> str:
        """Get bubble style for dialogue type."""

        style_mapping = {
            "speech": "standard_speech",
            "thought": "cloud_thought",
            "shout": "jagged_excitement",
            "whisper": "dotted_soft",
            "narration": "rectangular_box"
        }

        return style_mapping.get(dialogue_type, "standard_speech")

    async def generate_bubble_designs(
        self, text_placements: List[TextPlacement]
    ) -> List[BubbleDesign]:
        """Generate bubble design specifications."""

        bubble_designs = []

        for placement in text_placements:
            if placement.element_type == ElementType.DIALOGUE:
                design = await self._create_bubble_design(placement)
                bubble_designs.append(design)
            elif placement.element_type == ElementType.NARRATION:
                design = await self._create_narration_box_design(placement)
                bubble_designs.append(design)

        return bubble_designs

    async def _create_bubble_design(self, placement: TextPlacement) -> BubbleDesign:
        """Create bubble design specification."""

        bubble_style = placement.bubble_style.value
        dialogue_type = placement.dialogue_type.value
        emotion = placement.emotion

        # Base bubble design
        design = BubbleDesign(
            panel_id=placement.panel_id,
            element_id=f"{placement.panel_id}_{placement.speaker or 'unknown'}",
            bubble_type=placement.bubble_style,
            shape=self._determine_bubble_shape(bubble_style),
            border=self._determine_bubble_border(dialogue_type, emotion),
            fill=self._determine_bubble_fill(dialogue_type),
            tail=TailProperties(
                style=self._get_tail_style_for_type(dialogue_type),
                direction=placement.tail_direction or TailDirection.DOWN,
                length="medium"
            ),
            effects=self._determine_bubble_effects(emotion, dialogue_type)
        )

        return design

    def _determine_bubble_shape(self, bubble_style: str) -> BubbleShape:
        """Determine bubble shape based on style."""

        shape_mapping = {
            "standard_speech": BubbleShape.OVAL,
            "cloud_thought": BubbleShape.CLOUD,
            "jagged_excitement": BubbleShape.JAGGED,
            "dotted_soft": BubbleShape.OVAL,
            "rectangular_box": BubbleShape.RECTANGLE
        }

        return shape_mapping.get(bubble_style, BubbleShape.OVAL)

    def _determine_bubble_border(self, dialogue_type: str, emotion: str) -> BorderProperties:
        """Determine bubble border properties."""

        if dialogue_type == "shout":
            return BorderProperties(width=3, style=BorderStyle.SOLID, color="black")
        elif dialogue_type == "whisper":
            return BorderProperties(width=1, style=BorderStyle.DOTTED, color="gray")
        elif dialogue_type == "thought":
            return BorderProperties(width=1, style=BorderStyle.DASHED, color="gray")
        else:
            return BorderProperties(width=2, style=BorderStyle.SOLID, color="black")

    def _determine_bubble_fill(self, dialogue_type: str) -> FillProperties:
        """Determine bubble fill properties."""

        if dialogue_type == "thought":
            return FillProperties(color="white", opacity=0.9)
        elif dialogue_type == "narration":
            return FillProperties(color="lightgray", opacity=1.0)
        else:
            return FillProperties(color="white", opacity=1.0)

    def _get_tail_style_for_type(self, dialogue_type: str) -> TailStyle:
        """Get tail style for dialogue type."""

        style_mapping = {
            "speech": TailStyle.POINTED,
            "thought": TailStyle.BUBBLES,
            "shout": TailStyle.LIGHTNING,
            "whisper": TailStyle.SMALL_CURVED,
            "narration": TailStyle.NONE
        }

        return style_mapping.get(dialogue_type, TailStyle.POINTED)

    def _determine_bubble_effects(self, emotion: str, dialogue_type: str) -> List[str]:
        """Determine special effects for bubble."""

        effects = []

        if emotion in ["tension", "climax"] and dialogue_type == "shout":
            effects.append("vibration_effect")

        if emotion == "anxiety":
            effects.append("slight_tremor")

        if dialogue_type == "thought":
            effects.append("soft_shadow")

        return effects

    async def _create_narration_box_design(self, placement: TextPlacement) -> BubbleDesign:
        """Create narration box design specification."""

        design = BubbleDesign(
            panel_id=placement.panel_id,
            element_id=f"{placement.panel_id}_narration",
            bubble_type=BubbleStyle.RECTANGULAR_BOX,
            shape=BubbleShape.RECTANGLE,
            border=BorderProperties(width=1, style=BorderStyle.SOLID, color="black"),
            fill=FillProperties(color="white", opacity=1.0),
            tail=TailProperties(
                style=TailStyle.NONE,
                direction=TailDirection.DOWN,
                length="medium"
            ),
            effects=["clean_edges"],
            corner_radius=0
        )

        return design

    async def generate_typography_specifications(
        self,
        text_placements: List[TextPlacement],
        genre: str = "slice_of_life"
    ) -> TypographySpecifications:
        """Generate typography specifications for the manga."""

        # Get base typography for genre
        base_typography_dict = self.genre_typography.get(genre, self.genre_typography["slice_of_life"])

        base_typography = TypographyFont(
            primary_font=TypographyStyle.FRIENDLY_MANGA,
            emphasis_style=base_typography_dict["emphasis_style"],
            line_weight=base_typography_dict["line_weight"],
            font_weight=FontWeight.NORMAL
        )

        # Generate specifications for dialogue and narration
        dialogue_specs = []
        narration_specs = []

        for placement in text_placements:
            if placement.element_type == ElementType.DIALOGUE:
                spec = self._create_dialogue_typography_spec(placement, base_typography)
                dialogue_specs.append(spec)
            else:
                spec = self._create_narration_typography_spec(placement, base_typography)
                narration_specs.append(spec)

        typography_specs = TypographySpecifications(
            base_typography=base_typography,
            dialogue_specifications=dialogue_specs,
            narration_specifications=narration_specs,
            japanese_text_rules=self.japanese_text_rules,
            font_fallbacks=["Noto Sans CJK JP", "Hiragino Kaku Gothic Pro", "MS Gothic"],
            special_characters=SpecialCharacters()
        )

        return typography_specs

    def _create_dialogue_typography_spec(
        self, placement: TextPlacement, base_typography: TypographyFont
    ) -> TypographySpecification:
        """Create typography specification for dialogue."""

        dialogue_type = placement.dialogue_type.value
        importance = placement.importance.value
        emotion = placement.emotion

        # Create modified typography based on dialogue characteristics
        font_spec_dict = {
            "primary_font": base_typography.primary_font,
            "emphasis_style": base_typography.emphasis_style,
            "line_weight": base_typography.line_weight,
            "font_weight": base_typography.font_weight,
            "font_size_modifier": 1.0
        }

        # Adjust based on dialogue type
        if dialogue_type == "shout":
            font_spec_dict.update({
                "font_weight": FontWeight.BOLD,
                "font_size_modifier": 1.2,
                "letter_spacing": "wide"
            })
        elif dialogue_type == "whisper":
            font_spec_dict.update({
                "font_weight": FontWeight.LIGHT,
                "font_size_modifier": 0.8,
                "letter_spacing": "tight"
            })
        elif dialogue_type == "thought":
            font_spec_dict.update({
                "font_style": "italic",
                "font_size_modifier": 0.9,
                "opacity": 0.8
            })

        # Adjust based on importance
        if importance == "high":
            font_spec_dict["font_size_modifier"] *= 1.1
        elif importance == "low":
            font_spec_dict["font_size_modifier"] *= 0.9

        font_spec = TypographyFont(**font_spec_dict)

        return TypographySpecification(
            panel_id=placement.panel_id,
            element_id=f"{placement.panel_id}_{placement.speaker or 'unknown'}",
            typography=font_spec,
            text_effects=self._determine_text_effects(emotion, dialogue_type)
        )

    def _create_narration_typography_spec(
        self, placement: TextPlacement, base_typography: TypographyFont
    ) -> TypographySpecification:
        """Create typography specification for narration."""

        font_spec = TypographyFont(
            primary_font=base_typography.primary_font,
            emphasis_style=base_typography.emphasis_style,
            line_weight=base_typography.line_weight,
            font_weight=FontWeight.NORMAL,
            font_size_modifier=0.85,
            line_height=1.3,
            text_alignment=TextAlignment.LEFT
        )

        return TypographySpecification(
            panel_id=placement.panel_id,
            element_id=f"{placement.panel_id}_narration",
            typography=font_spec,
            text_effects=[],
            box_style="clean_rectangle"
        )

    def _determine_text_effects(self, emotion: str, dialogue_type: str) -> List[str]:
        """Determine text effects based on emotion and type."""

        effects = []

        if emotion in ["tension", "climax"] and dialogue_type == "shout":
            effects.append("bold_outline")

        if emotion in ["anxiety", "fear"]:
            effects.append("slight_tremor")

        if dialogue_type == "thought":
            effects.append("soft_glow")

        if emotion == "satisfaction":
            effects.append("warm_tone")

        return effects

    async def analyze_readability(
        self,
        text_placements: List[TextPlacement],
        panel_specifications: List[Dict[str, Any]]
    ) -> ReadabilityOptimization:
        """Analyze and optimize text readability."""

        # Analyze potential readability issues
        readability_issues = []
        optimization_suggestions = []

        # Group placements by panel
        panel_groups = {}
        for placement in text_placements:
            panel_id = placement.panel_id
            if panel_id not in panel_groups:
                panel_groups[panel_id] = []
            panel_groups[panel_id].append(placement)

        # Analyze each panel
        for panel_id, placements in panel_groups.items():
            panel_analysis = await self._analyze_panel_readability(panel_id, placements)
            readability_issues.extend(panel_analysis["issues"])
            optimization_suggestions.extend(panel_analysis["suggestions"])

        # Calculate overall readability score
        readability_score = self._calculate_readability_score(readability_issues, text_placements)

        # Analyze reading flow
        flow_analysis = await self._analyze_reading_flow(text_placements)

        # Analyze text density
        density_analysis = self._analyze_text_density(text_placements)

        # Analyze visual interference
        interference_analysis = self._analyze_visual_interference(
            text_placements, panel_specifications
        )

        readability_optimization = ReadabilityOptimization(
            overall_readability_score=readability_score,
            identified_issues=[
                ReadabilityIssue(
                    panel_id=issue.split(":")[0].replace("Panel ", ""),
                    issue_type="readability",
                    severity="medium",
                    description=issue
                ) for issue in readability_issues[:10]  # Limit to 10 issues
            ],
            optimization_suggestions=optimization_suggestions,
            reading_flow_analysis=flow_analysis,
            text_density_analysis=density_analysis,
            visual_interference_analysis=interference_analysis
        )

        return readability_optimization

    async def _analyze_panel_readability(
        self, panel_id: str, placements: List[TextPlacement]
    ) -> Dict[str, Any]:
        """Analyze readability for a single panel."""

        issues = []
        suggestions = []

        # Check text density
        total_text_length = sum(len(p.text_content) for p in placements)
        if total_text_length > self.max_text_density:
            issues.append(f"Panel {panel_id}: 文字密度が高すぎます")
            suggestions.append(f"Panel {panel_id}: テキスト量の削減を検討")

        # Check reading order clarity
        reading_orders = [p.reading_order for p in placements]
        if len(set(reading_orders)) != len(reading_orders):
            issues.append(f"Panel {panel_id}: 読み順が不明確です")
            suggestions.append(f"Panel {panel_id}: 読み順の明確化")

        # Check position conflicts
        positions = [(p.position.x, p.position.y) for p in placements]
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], i+1):
                if abs(pos1[0] - pos2[0]) < self.min_distance_between_elements and \
                   abs(pos1[1] - pos2[1]) < self.min_distance_between_elements:
                    issues.append(f"Panel {panel_id}: テキスト要素が重複する可能性")
                    suggestions.append(f"Panel {panel_id}: テキスト配置の調整")
                    break

        return {"issues": issues, "suggestions": suggestions}

    def _calculate_readability_score(
        self, issues: List[str], text_placements: List[TextPlacement]
    ) -> float:
        """Calculate overall readability score."""

        if not text_placements:
            return 1.0

        # Start with perfect score
        score = 1.0

        # Deduct for each issue type
        issue_penalties = {
            "文字密度": 0.15,
            "読み順": 0.2,
            "重複": 0.1,
            "視覚的干渉": 0.1
        }

        for issue in issues:
            for issue_type, penalty in issue_penalties.items():
                if issue_type in issue:
                    score -= penalty
                    break

        return max(0.0, round(score, 2))

    async def _analyze_reading_flow(self, text_placements: List[TextPlacement]) -> FlowAnalysis:
        """Analyze reading flow across panels."""

        # Group by panel and sort by reading order
        panel_flows = {}
        for placement in text_placements:
            panel_id = placement.panel_id
            if panel_id not in panel_flows:
                panel_flows[panel_id] = []
            panel_flows[panel_id].append(placement)

        # Sort each panel by reading order
        for panel_id in panel_flows:
            panel_flows[panel_id].sort(key=lambda x: x.reading_order)

        flow_analysis = FlowAnalysis(
            panels_with_clear_flow=0,
            panels_with_issues=0,
            average_elements_per_panel=0.0,
            flow_recommendations=[]
        )

        total_elements = 0
        for panel_id, placements in panel_flows.items():
            total_elements += len(placements)

            # Check if reading order is clear
            orders = [p.reading_order for p in placements]
            if orders == sorted(orders) and len(set(orders)) == len(orders):
                flow_analysis.panels_with_clear_flow += 1
            else:
                flow_analysis.panels_with_issues += 1
                flow_analysis.flow_recommendations.append(
                    f"Panel {panel_id}: 読み順の明確化が必要"
                )

        if panel_flows:
            flow_analysis.average_elements_per_panel = round(
                total_elements / len(panel_flows), 1
            )

        return flow_analysis

    def _analyze_text_density(self, text_placements: List[TextPlacement]) -> DensityAnalysis:
        """Analyze text density distribution."""

        panel_densities = {}

        for placement in text_placements:
            panel_id = placement.panel_id
            text_length = len(placement.text_content)

            if panel_id not in panel_densities:
                panel_densities[panel_id] = 0
            panel_densities[panel_id] += text_length

        densities = list(panel_densities.values())

        if not densities:
            return DensityAnalysis(
                average_text_per_panel=0.0,
                max_text_panel=0,
                min_text_panel=0,
                density_variance=0.0,
                high_density_panels=0,
                recommended_max_density=60
            )

        density_analysis = DensityAnalysis(
            average_text_per_panel=sum(densities) / len(densities),
            max_text_panel=max(densities),
            min_text_panel=min(densities),
            density_variance=self._calculate_variance(densities),
            high_density_panels=len([d for d in densities if d > 80]),
            recommended_max_density=60
        )

        return density_analysis

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        if not values:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return round(variance, 2)

    def _analyze_visual_interference(
        self, text_placements: List[TextPlacement], panel_specifications: List[Dict[str, Any]]
    ) -> InterferenceAnalysis:
        """Analyze potential visual interference between text and images."""

        interference_analysis = InterferenceAnalysis(
            potential_conflicts=[],
            safe_placements=0,
            risky_placements=0,
            recommendations=[]
        )

        for placement in text_placements:
            panel_id = placement.panel_id
            position = placement.position

            # Find corresponding panel spec
            panel_spec = next(
                (spec for spec in panel_specifications if spec.get("panel_id") == panel_id),
                {}
            )

            # Check for potential conflicts
            camera_angle = panel_spec.get("camera_angle", "medium_shot")
            focus_element = panel_spec.get("focus_element", "")

            # Analyze interference risk
            risk_level = self._assess_interference_risk(position, camera_angle, focus_element)

            if risk_level == "high":
                interference_analysis.risky_placements += 1
                interference_analysis.potential_conflicts.append(
                    f"Panel {panel_id}: テキストが主要な視覚要素と干渉する可能性"
                )
                interference_analysis.recommendations.append(
                    f"Panel {panel_id}: テキスト位置の調整を推奨"
                )
            else:
                interference_analysis.safe_placements += 1

        return interference_analysis

    def _assess_interference_risk(
        self, position: Position, camera_angle: str, focus_element: str
    ) -> str:
        """Assess interference risk between text and image elements."""

        pos_x = position.x
        pos_y = position.y

        # High risk areas based on camera angle
        if camera_angle in ["close_up", "extreme_close_up"]:
            # Face area is typically center
            if 0.3 <= pos_x <= 0.7 and 0.2 <= pos_y <= 0.8:
                return "high"
        elif "character" in focus_element and 0.2 <= pos_x <= 0.8 and 0.3 <= pos_y <= 0.7:
            return "medium"

        return "low"