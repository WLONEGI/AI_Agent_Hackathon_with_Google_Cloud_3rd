"""Phase 6: Dialogue and Text Placement Schemas.

This module defines all Pydantic models and data structures for Phase 6,
which handles dialogue generation and text placement in manga panels.
"""

from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from uuid import UUID


# ==================== ENUM TYPES ====================

class DialogueType(str, Enum):
    """Types of dialogue bubbles."""
    SPEECH = "speech"
    THOUGHT = "thought"
    SHOUT = "shout"
    WHISPER = "whisper"
    NARRATION = "narration"


class BubbleStyle(str, Enum):
    """Speech bubble visual styles."""
    STANDARD_SPEECH = "standard_speech"
    CLOUD_THOUGHT = "cloud_thought"
    JAGGED_EXCITEMENT = "jagged_excitement"
    DOTTED_SOFT = "dotted_soft"
    RECTANGULAR_BOX = "rectangular_box"


class TailStyle(str, Enum):
    """Speech bubble tail styles."""
    POINTED = "pointed"
    BUBBLES = "bubbles"
    LIGHTNING = "lightning"
    SMALL_CURVED = "small_curved"
    NONE = "none"


class TextSize(str, Enum):
    """Text size options."""
    SMALL = "small"
    NORMAL = "normal"
    LARGE = "large"
    ITALIC = "italic"


class FontWeight(str, Enum):
    """Font weight options."""
    LIGHT = "light"
    NORMAL = "normal"
    BOLD = "bold"


class SpeechPattern(str, Enum):
    """Character speech patterns."""
    YOUTHFUL = "youthful"
    FORMAL = "formal"
    CASUAL = "casual"
    STANDARD = "standard"


class PlacementPosition(str, Enum):
    """Text placement positions in panels."""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
    SIDES = "sides"
    EDGES = "edges"
    ANYWHERE = "anywhere"


class ImportanceLevel(str, Enum):
    """Dialogue importance levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReadingDirection(str, Enum):
    """Reading direction for text."""
    LEFT_TO_RIGHT = "left_to_right"
    RIGHT_TO_LEFT = "right_to_left"


class TextAlignment(str, Enum):
    """Text alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class BubbleShape(str, Enum):
    """Speech bubble shapes."""
    OVAL = "oval"
    CLOUD = "cloud"
    JAGGED = "jagged"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"


class BorderStyle(str, Enum):
    """Border style options."""
    SOLID = "solid"
    DOTTED = "dotted"
    DASHED = "dashed"
    DOUBLE = "double"


class TailDirection(str, Enum):
    """Speech bubble tail directions."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    UP_LEFT = "up_left"
    UP_RIGHT = "up_right"
    DOWN_LEFT = "down_left"
    DOWN_RIGHT = "down_right"


class ElementType(str, Enum):
    """Text element types."""
    DIALOGUE = "dialogue"
    NARRATION = "narration"
    SOUND_EFFECT = "sound_effect"
    CAPTION = "caption"


class NarrationStyle(str, Enum):
    """Narration box styles."""
    DESCRIPTIVE = "descriptive"
    ACTION = "action"
    ATMOSPHERIC = "atmospheric"
    TEMPORAL = "temporal"


class TypographyStyle(str, Enum):
    """Typography style categories."""
    BOLD_MANGA = "bold_manga_font"
    ELEGANT_MANGA = "elegant_manga_font"
    ATMOSPHERIC_MANGA = "atmospheric_manga_font"
    FRIENDLY_MANGA = "friendly_manga_font"


# ==================== CORE DATA MODELS ====================

class DialogueCharacteristics(BaseModel):
    """Characteristics defining dialogue appearance."""
    bubble_style: BubbleStyle
    tail_style: TailStyle
    text_size: TextSize
    font_weight: FontWeight

    class Config:
        use_enum_values = True


class PlacementRules(BaseModel):
    """Rules for text placement based on panel composition."""
    preferred_positions: List[PlacementPosition]
    avoid_positions: List[PlacementPosition]
    max_text_coverage: float = Field(ge=0.0, le=1.0)

    class Config:
        use_enum_values = True


class JapaneseTextRules(BaseModel):
    """Rules specific to Japanese text formatting."""
    reading_direction: ReadingDirection = ReadingDirection.RIGHT_TO_LEFT
    vertical_text: bool = True
    character_spacing: str = "normal"
    line_spacing: float = Field(default=1.2, ge=0.5, le=3.0)
    punctuation_handling: str = "japanese_rules"

    class Config:
        use_enum_values = True


class Position(BaseModel):
    """2D position with anchor point."""
    x: float = Field(ge=0.0, le=1.0, description="X coordinate (0-1)")
    y: float = Field(ge=0.0, le=1.0, description="Y coordinate (0-1)")
    anchor: str = Field(description="Anchor point for positioning")

    @validator('anchor')
    def validate_anchor(cls, v):
        valid_anchors = [
            "top_left", "top", "top_right",
            "left", "center", "right",
            "bottom_left", "bottom", "bottom_right"
        ]
        if v not in valid_anchors:
            raise ValueError(f"Invalid anchor: {v}")
        return v


class TextArea(BaseModel):
    """Text area dimensions and properties."""
    width_ratio: float = Field(ge=0.0, le=1.0)
    height_ratio: float = Field(ge=0.0, le=1.0)
    estimated_lines: int = Field(ge=1)
    font_size: int = Field(ge=6, le=32)
    padding: Dict[str, int] = Field(default_factory=lambda: {
        "top": 8, "bottom": 8, "left": 12, "right": 12
    })
    text_alignment: TextAlignment = TextAlignment.CENTER

    class Config:
        use_enum_values = True


class DialogueElement(BaseModel):
    """Individual dialogue element within a panel."""
    speaker: Optional[str] = Field(description="Character name who speaks")
    text: str = Field(min_length=1, description="Dialogue text content")
    dialogue_type: DialogueType = DialogueType.SPEECH
    emotion: str = Field(default="neutral", description="Emotional context")
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    text_length: int = Field(ge=0, description="Length of text")
    estimated_syllables: int = Field(ge=0, description="Estimated syllable count")
    speech_pattern: SpeechPattern = SpeechPattern.STANDARD

    class Config:
        use_enum_values = True

    @validator('text_length', pre=True, always=True)
    def set_text_length(cls, v, values):
        if 'text' in values:
            return len(values['text'])
        return v


class NarrationElement(BaseModel):
    """Narration text element."""
    text: str = Field(min_length=1, description="Narration text content")
    position: PlacementPosition = PlacementPosition.TOP
    style: NarrationStyle = NarrationStyle.DESCRIPTIVE
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    text_length: int = Field(ge=0, description="Length of text")

    class Config:
        use_enum_values = True

    @validator('text_length', pre=True, always=True)
    def set_text_length(cls, v, values):
        if 'text' in values:
            return len(values['text'])
        return v


class PanelDialogue(BaseModel):
    """Complete dialogue content for a single panel."""
    panel_id: str = Field(min_length=1, description="Panel identifier")
    scene_number: int = Field(ge=1, description="Scene number this panel belongs to")
    dialogue_elements: List[DialogueElement] = Field(default_factory=list)
    narration: Optional[NarrationElement] = None
    total_text_elements: int = Field(ge=0, description="Total text elements count")
    estimated_reading_time: float = Field(ge=0.0, description="Reading time in seconds")

    @validator('total_text_elements', pre=True, always=True)
    def set_total_elements(cls, v, values):
        dialogue_count = len(values.get('dialogue_elements', []))
        narration_count = 1 if values.get('narration') else 0
        return dialogue_count + narration_count


class BorderProperties(BaseModel):
    """Border properties for bubbles and boxes."""
    width: int = Field(ge=1, le=10, default=2)
    style: BorderStyle = BorderStyle.SOLID
    color: str = Field(default="black", pattern=r'^(black|gray|white|#[0-9A-Fa-f]{6})$')

    class Config:
        use_enum_values = True


class FillProperties(BaseModel):
    """Fill properties for bubbles and boxes."""
    color: str = Field(default="white", pattern=r'^(white|lightgray|black|#[0-9A-Fa-f]{6})$')
    opacity: float = Field(ge=0.0, le=1.0, default=1.0)


class TailProperties(BaseModel):
    """Speech bubble tail properties."""
    style: TailStyle
    direction: TailDirection
    length: str = Field(default="medium", pattern=r'^(short|medium|long)$')

    class Config:
        use_enum_values = True


class TextPlacement(BaseModel):
    """Text placement specification for dialogue or narration."""
    panel_id: str = Field(min_length=1, description="Panel identifier")
    element_type: ElementType
    speaker: Optional[str] = Field(description="Speaker name for dialogue")
    text_content: str = Field(min_length=1, description="Text content")
    dialogue_type: DialogueType = DialogueType.SPEECH
    position: Position
    bubble_style: BubbleStyle = BubbleStyle.STANDARD_SPEECH
    text_area: TextArea
    reading_order: int = Field(ge=1, description="Reading order within panel")
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    speech_pattern: Optional[SpeechPattern] = None
    emotion: str = Field(default="neutral", description="Emotional context")
    tail_direction: Optional[TailDirection] = None
    narration_style: Optional[NarrationStyle] = None

    class Config:
        use_enum_values = True


class BubbleDesign(BaseModel):
    """Speech bubble design specification."""
    panel_id: str = Field(min_length=1, description="Panel identifier")
    element_id: str = Field(min_length=1, description="Unique element identifier")
    bubble_type: BubbleStyle
    shape: BubbleShape
    border: BorderProperties
    fill: FillProperties
    tail: TailProperties
    effects: List[str] = Field(default_factory=list, description="Visual effects")
    corner_radius: int = Field(ge=0, le=20, default=0, description="Corner radius for rectangles")

    class Config:
        use_enum_values = True


class TypographyFont(BaseModel):
    """Font specification for typography."""
    primary_font: TypographyStyle
    emphasis_style: str = Field(description="Style for emphasized text")
    line_weight: str = Field(description="Overall line weight")
    font_weight: FontWeight = FontWeight.NORMAL
    font_size_modifier: float = Field(ge=0.5, le=2.0, default=1.0)
    font_style: Optional[str] = None
    letter_spacing: Optional[str] = None
    opacity: Optional[float] = Field(ge=0.0, le=1.0)
    line_height: Optional[float] = Field(ge=0.8, le=3.0)
    text_alignment: Optional[TextAlignment] = None

    class Config:
        use_enum_values = True


class TypographySpecification(BaseModel):
    """Typography specification for text elements."""
    panel_id: str = Field(min_length=1, description="Panel identifier")
    element_id: str = Field(min_length=1, description="Element identifier")
    typography: TypographyFont
    text_effects: List[str] = Field(default_factory=list)
    box_style: Optional[str] = None


class SpecialCharacters(BaseModel):
    """Special characters for text effects."""
    emphasis_marks: List[str] = Field(default_factory=lambda: ["！", "？", "…"])
    pause_indicators: List[str] = Field(default_factory=lambda: ["……", "..."])
    emotional_indicators: List[str] = Field(default_factory=lambda: ["♪", "♡", "★"])


class TypographySpecifications(BaseModel):
    """Complete typography specifications."""
    base_typography: TypographyFont
    dialogue_specifications: List[TypographySpecification] = Field(default_factory=list)
    narration_specifications: List[TypographySpecification] = Field(default_factory=list)
    japanese_text_rules: JapaneseTextRules = Field(default_factory=JapaneseTextRules)
    font_fallbacks: List[str] = Field(default_factory=lambda: [
        "Noto Sans CJK JP", "Hiragino Kaku Gothic Pro", "MS Gothic"
    ])
    special_characters: SpecialCharacters = Field(default_factory=SpecialCharacters)


class ReadabilityIssue(BaseModel):
    """Individual readability issue."""
    panel_id: str = Field(min_length=1, description="Panel with the issue")
    issue_type: str = Field(description="Type of readability issue")
    severity: str = Field(default="medium", pattern=r'^(low|medium|high)$')
    description: str = Field(description="Issue description")
    suggestion: Optional[str] = Field(description="Suggested fix")


class FlowAnalysis(BaseModel):
    """Reading flow analysis results."""
    panels_with_clear_flow: int = Field(ge=0)
    panels_with_issues: int = Field(ge=0)
    average_elements_per_panel: float = Field(ge=0.0)
    flow_recommendations: List[str] = Field(default_factory=list)


class DensityAnalysis(BaseModel):
    """Text density analysis results."""
    average_text_per_panel: float = Field(ge=0.0)
    max_text_panel: int = Field(ge=0)
    min_text_panel: int = Field(ge=0)
    density_variance: float = Field(ge=0.0)
    high_density_panels: int = Field(ge=0)
    recommended_max_density: int = Field(default=60, ge=20, le=100)


class InterferenceAnalysis(BaseModel):
    """Visual interference analysis results."""
    potential_conflicts: List[str] = Field(default_factory=list)
    safe_placements: int = Field(ge=0)
    risky_placements: int = Field(ge=0)
    recommendations: List[str] = Field(default_factory=list)


class ReadabilityOptimization(BaseModel):
    """Complete readability optimization analysis."""
    overall_readability_score: float = Field(ge=0.0, le=1.0)
    identified_issues: List[ReadabilityIssue] = Field(default_factory=list)
    optimization_suggestions: List[str] = Field(default_factory=list)
    reading_flow_analysis: FlowAnalysis
    text_density_analysis: DensityAnalysis
    visual_interference_analysis: InterferenceAnalysis


class DialogueFlowAnalysis(BaseModel):
    """Dialogue flow and narrative progression analysis."""
    scene_dialogue_distribution: Dict[int, List[Dict[str, Any]]] = Field(default_factory=dict)
    character_speaking_balance: Dict[str, int] = Field(default_factory=dict)
    dialogue_types_distribution: Dict[str, int] = Field(default_factory=dict)
    total_dialogue_elements: int = Field(ge=0)
    average_dialogue_per_panel: float = Field(ge=0.0)
    narrative_progression_score: float = Field(ge=0.0, le=1.0)
    character_voice_consistency: Dict[str, Any] = Field(default_factory=dict)
    dialogue_pacing_analysis: Dict[str, Any] = Field(default_factory=dict)


class TimingAnalysis(BaseModel):
    """Dialogue timing and pacing analysis."""
    total_estimated_reading_time: float = Field(ge=0.0, description="Total reading time in seconds")
    average_reading_time_per_panel: float = Field(ge=0.0)
    reading_speed_analysis: Dict[str, float] = Field(default_factory=dict)
    pacing_recommendations: List[str] = Field(default_factory=list)
    syllable_distribution: Dict[str, int] = Field(default_factory=dict)


class QualityMetrics(BaseModel):
    """Overall quality metrics for Phase 6 output."""
    dialogue_density_score: float = Field(ge=0.0, le=1.0)
    readability_score: float = Field(ge=0.0, le=1.0)
    integration_score: float = Field(ge=0.0, le=1.0)
    narrative_coherence_score: float = Field(ge=0.0, le=1.0)
    character_voice_consistency_score: float = Field(ge=0.0, le=1.0)
    pacing_alignment_score: float = Field(ge=0.0, le=1.0)
    overall_quality_score: float = Field(ge=0.0, le=1.0)


# ==================== INPUT/OUTPUT SCHEMAS ====================

class DialoguePlacementInput(BaseModel):
    """Input data for Phase 6 dialogue placement processing."""
    text: str = Field(min_length=1, description="Original text content")
    session_id: UUID = Field(description="Session identifier")
    genre: Optional[str] = Field(description="Story genre for dialogue styling")
    style_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    placement_constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class DialoguePlacementOutput(BaseModel):
    """Output data from Phase 6 dialogue placement processing."""
    dialogue_content: List[PanelDialogue] = Field(
        description="Generated dialogue content for all panels"
    )
    dialogue_placement: List[TextPlacement] = Field(
        description="Text placement specifications"
    )
    speech_bubbles: List[BubbleDesign] = Field(
        description="Speech bubble design specifications"
    )
    timing_analysis: TimingAnalysis = Field(
        description="Dialogue timing and pacing analysis"
    )
    typography_specifications: TypographySpecifications = Field(
        description="Typography and text formatting specifications"
    )
    readability_optimization: ReadabilityOptimization = Field(
        description="Readability analysis and optimization suggestions"
    )
    dialogue_flow_analysis: DialogueFlowAnalysis = Field(
        description="Narrative flow and character voice analysis"
    )
    quality_metrics: QualityMetrics = Field(
        description="Overall quality assessment metrics"
    )

    # Summary statistics
    total_dialogue_count: int = Field(ge=0, description="Total number of dialogue elements")
    average_words_per_panel: float = Field(ge=0.0, description="Average words per panel")
    dialogue_distribution: Dict[str, Any] = Field(
        default_factory=dict, description="Distribution of dialogue across panels"
    )
    reading_flow: Dict[str, Any] = Field(
        default_factory=dict, description="Reading flow analysis results"
    )

    # Processing metadata
    processing_time_seconds: float = Field(ge=0.0, description="Processing time")
    panels_processed: int = Field(ge=0, description="Number of panels processed")
    success_rate: float = Field(ge=0.0, le=1.0, description="Success rate")

    class Config:
        use_enum_values = True


# ==================== TASK MODELS ====================

class DialogueGenerationTask(BaseModel):
    """Task specification for dialogue generation."""
    panel_id: str = Field(min_length=1, description="Panel identifier")
    scene_number: int = Field(ge=1, description="Scene number")
    characters: List[Dict[str, Any]] = Field(default_factory=list)
    scene_context: Dict[str, Any] = Field(default_factory=dict)
    emotional_tone: str = Field(default="neutral")
    panel_specs: Dict[str, Any] = Field(default_factory=dict)
    generation_constraints: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class TextPlacementTask(BaseModel):
    """Task specification for text placement."""
    panel_dialogue: PanelDialogue
    panel_specifications: Dict[str, Any] = Field(default_factory=dict)
    image_information: Optional[Dict[str, Any]] = None
    placement_constraints: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


# ==================== CONFIGURATION ====================

class DialogueGenerationConfig(BaseModel):
    """Configuration for dialogue generation and placement."""
    # Generation settings
    max_dialogue_length: int = Field(default=25, ge=5, le=100)
    max_elements_per_panel: int = Field(default=3, ge=1, le=8)
    default_reading_speed: float = Field(default=3.5, ge=1.0, le=10.0)

    # Placement settings
    default_font_size: int = Field(default=12, ge=8, le=24)
    min_bubble_padding: int = Field(default=8, ge=4, le=20)
    max_text_coverage_ratio: float = Field(default=0.5, ge=0.1, le=0.8)

    # Quality thresholds
    min_readability_score: float = Field(default=0.7, ge=0.5, le=1.0)
    max_text_density: int = Field(default=80, ge=40, le=150)

    # Style preferences
    preferred_bubble_styles: Dict[str, BubbleStyle] = Field(default_factory=dict)
    character_speech_patterns: Dict[str, SpeechPattern] = Field(default_factory=dict)
    genre_typography_styles: Dict[str, TypographyStyle] = Field(default_factory=dict)

    # Rules and constraints
    dialogue_type_characteristics: Dict[DialogueType, DialogueCharacteristics] = Field(
        default_factory=dict
    )
    placement_rules_by_camera_angle: Dict[str, PlacementRules] = Field(
        default_factory=dict
    )
    japanese_text_formatting: JapaneseTextRules = Field(
        default_factory=JapaneseTextRules
    )

    class Config:
        use_enum_values = True