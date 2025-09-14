"""Phase 4: Name Generation (Panel Layout and Composition) - Pydantic Schema Definitions."""

from typing import Dict, Any, Optional, List, Tuple, Literal, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from uuid import UUID

# =====================================
# Enum Definitions
# =====================================

class LayoutPatternType(str, Enum):
    """Layout pattern types for different manga styles."""
    STANDARD = "standard"
    ACTION = "action"
    DIALOGUE = "dialogue"
    DRAMATIC = "dramatic"
    EXPERIMENTAL = "experimental"

class CameraAngleType(str, Enum):
    """Camera angle types for manga panels."""
    EXTREME_LONG = "extreme_long"
    LONG = "long"
    MEDIUM = "medium"
    CLOSE = "close"
    EXTREME_CLOSE = "extreme_close"
    BIRD_EYE = "bird_eye"
    WORM_EYE = "worm_eye"

class CompositionRuleType(str, Enum):
    """Composition rule types."""
    RULE_OF_THIRDS = "rule_of_thirds"
    GOLDEN_RATIO = "golden_ratio"
    SYMMETRICAL = "symmetrical"
    DIAGONAL = "diagonal"
    CENTERED = "centered"

class PanelShapeType(str, Enum):
    """Panel shape types."""
    RECTANGLE = "rectangle"
    SQUARE = "square"
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    IRREGULAR = "irregular"
    CIRCULAR = "circular"

class BorderStyleType(str, Enum):
    """Panel border style types."""
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    THICK = "thick"
    WAVY = "wavy"
    JAGGED = "jagged"
    NONE = "none"

class ImportanceLevel(str, Enum):
    """Importance levels for scenes and panels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TransitionType(str, Enum):
    """Panel transition types."""
    MOMENT_TO_MOMENT = "moment_to_moment"
    ACTION_TO_ACTION = "action_to_action"
    SUBJECT_TO_SUBJECT = "subject_to_subject"
    SCENE_TO_SCENE = "scene_to_scene"
    ASPECT_TO_ASPECT = "aspect_to_aspect"
    NON_SEQUITUR = "non_sequitur"

# =====================================
# Base Models
# =====================================

class PanelSize(BaseModel):
    """Panel size specification."""
    width: float = Field(..., ge=0, description="Panel width (normalized 0-1)")
    height: float = Field(..., ge=0, description="Panel height (normalized 0-1)")
    aspect_ratio: Tuple[int, int] = Field(..., description="Aspect ratio as (width, height)")

    @validator('width', 'height')
    def validate_size_range(cls, v):
        if not (0 <= v <= 1):
            raise ValueError('Size values must be between 0 and 1')
        return v

class PanelPosition(BaseModel):
    """Panel position on page."""
    x: float = Field(..., ge=0, le=1, description="X position (normalized 0-1)")
    y: float = Field(..., ge=0, le=1, description="Y position (normalized 0-1)")
    z_index: int = Field(default=0, description="Layer order for overlapping panels")

class CameraSettings(BaseModel):
    """Camera settings for panel."""
    angle: CameraAngleType = Field(..., description="Camera angle type")
    distance: int = Field(..., ge=1, le=5, description="Camera distance (1=closest, 5=farthest)")
    tilt: float = Field(default=0.0, ge=-45, le=45, description="Camera tilt in degrees")
    focus_point: Optional[Tuple[float, float]] = Field(None, description="Focus point coordinates")
    depth_of_field: float = Field(default=0.5, ge=0, le=1, description="Depth of field intensity")

class CompositionGuide(BaseModel):
    """Composition guide for panel."""
    rule: CompositionRuleType = Field(..., description="Primary composition rule")
    focal_points: List[Tuple[float, float]] = Field(default_factory=list, description="Key focal points")
    leading_lines: List[Dict[str, Any]] = Field(default_factory=list, description="Leading lines data")
    balance_weight: float = Field(default=0.5, ge=0, le=1, description="Visual balance weight")
    rhythm_factor: float = Field(default=0.5, ge=0, le=1, description="Visual rhythm factor")

class Panel(BaseModel):
    """Complete panel definition."""
    panel_id: str = Field(..., description="Unique panel identifier")
    size: PanelSize = Field(..., description="Panel size specification")
    position: PanelPosition = Field(..., description="Panel position on page")
    shape: PanelShapeType = Field(..., description="Panel shape type")
    border_style: BorderStyleType = Field(default=BorderStyleType.SOLID, description="Border style")
    camera_settings: CameraSettings = Field(..., description="Camera settings")
    composition: CompositionGuide = Field(..., description="Composition guide")
    content_description: str = Field(..., description="Panel content description")
    scene_reference: int = Field(default=0, description="Referenced scene number")
    importance: ImportanceLevel = Field(default=ImportanceLevel.MEDIUM, description="Panel importance")
    speech_bubble_count: int = Field(default=0, ge=0, description="Number of speech bubbles")
    sound_effects: List[str] = Field(default_factory=list, description="Sound effects in panel")

class LayoutPattern(BaseModel):
    """Layout pattern configuration."""
    name: LayoutPatternType = Field(..., description="Pattern type")
    panels_per_page: int = Field(..., ge=1, le=12, description="Base panels per page")
    variation: int = Field(..., ge=0, le=5, description="Variation range")
    complexity: Literal["low", "medium", "high"] = Field(..., description="Layout complexity")
    preferred_shapes: List[PanelShapeType] = Field(default_factory=list, description="Preferred panel shapes")
    rhythm_pattern: List[float] = Field(default_factory=list, description="Rhythm pattern weights")

class ReadingFlow(BaseModel):
    """Reading flow analysis."""
    reading_order: List[str] = Field(..., description="Panel IDs in reading order")
    flow_quality: float = Field(..., ge=0, le=1, description="Flow quality score")
    attention_points: List[Tuple[float, float]] = Field(default_factory=list, description="Attention focal points")
    flow_disruptions: List[str] = Field(default_factory=list, description="Panel IDs with flow issues")
    estimated_reading_time: float = Field(default=0.0, description="Estimated reading time in seconds")

class PageLayout(BaseModel):
    """Complete page layout."""
    page_number: int = Field(..., ge=1, description="Page number")
    panels: List[Panel] = Field(..., min_items=1, description="Panels on the page")
    scene_numbers: List[int] = Field(default_factory=list, description="Scene numbers on this page")
    layout_type: LayoutPatternType = Field(..., description="Layout pattern used")
    reading_flow: ReadingFlow = Field(..., description="Reading flow analysis")
    page_impact: ImportanceLevel = Field(default=ImportanceLevel.MEDIUM, description="Page importance")
    page_emotion: str = Field(default="neutral", description="Overall page emotion")

class PanelTransition(BaseModel):
    """Transition between panels."""
    from_panel: str = Field(..., description="Source panel ID")
    to_panel: str = Field(..., description="Target panel ID")
    transition_type: TransitionType = Field(..., description="Type of transition")
    time_gap: float = Field(default=0.0, ge=0, description="Time gap in seconds")
    spatial_relationship: str = Field(..., description="Spatial relationship description")
    transition_quality: float = Field(..., ge=0, le=1, description="Transition quality score")

class DramaticMoment(BaseModel):
    """Dramatic moment identification."""
    page_number: int = Field(..., description="Page where moment occurs")
    panel_id: str = Field(..., description="Panel containing the moment")
    moment_type: str = Field(..., description="Type of dramatic moment")
    intensity: float = Field(..., ge=0, le=1, description="Dramatic intensity level")
    buildup_panels: List[str] = Field(default_factory=list, description="Panels building up to this moment")
    impact_factor: float = Field(..., ge=0, le=1, description="Visual impact factor")

class CameraStatistics(BaseModel):
    """Camera usage statistics."""
    angle_distribution: Dict[CameraAngleType, int] = Field(default_factory=dict, description="Camera angle usage count")
    distance_distribution: Dict[int, int] = Field(default_factory=dict, description="Camera distance usage count")
    variety_score: float = Field(default=0.0, ge=0, le=1, description="Camera variety score")
    dominant_angle: CameraAngleType = Field(default=CameraAngleType.MEDIUM, description="Most used camera angle")
    cinematic_quality: float = Field(default=0.0, ge=0, le=1, description="Overall cinematic quality")

class LayoutAnalysis(BaseModel):
    """Comprehensive layout analysis."""
    total_panels: int = Field(..., ge=0, description="Total number of panels")
    average_panels_per_page: float = Field(..., ge=0, description="Average panels per page")
    layout_variety: float = Field(..., ge=0, le=1, description="Layout variety score")
    composition_quality: float = Field(..., ge=0, le=1, description="Overall composition quality")
    visual_balance: float = Field(..., ge=0, le=1, description="Visual balance score")
    pacing_effectiveness: float = Field(..., ge=0, le=1, description="Pacing effectiveness score")
    readability_score: float = Field(..., ge=0, le=1, description="Overall readability")
    complexity_level: Literal["simple", "moderate", "complex", "very_complex"] = Field(..., description="Layout complexity")

class ShotListItem(BaseModel):
    """Individual shot in shot list."""
    shot_number: int = Field(..., ge=1, description="Shot sequence number")
    panel_id: str = Field(..., description="Associated panel ID")
    shot_type: str = Field(..., description="Type of shot")
    camera_angle: CameraAngleType = Field(..., description="Camera angle")
    camera_movement: Optional[str] = Field(None, description="Camera movement description")
    subject: str = Field(..., description="Main subject of shot")
    background: str = Field(..., description="Background description")
    lighting: str = Field(default="natural", description="Lighting conditions")
    mood: str = Field(default="neutral", description="Mood/emotion of shot")
    duration_weight: float = Field(default=1.0, ge=0, description="Relative duration weight")

# =====================================
# Input/Output Schemas
# =====================================

class NameGenerationInput(BaseModel):
    """Input schema for Phase 4: Name Generation."""
    original_text: str = Field(..., description="Original text content")
    phase1_results: Optional[Dict[str, Any]] = Field(None, description="Phase 1 concept analysis results")
    phase2_results: Optional[Dict[str, Any]] = Field(None, description="Phase 2 character design results")
    phase3_results: Optional[Dict[str, Any]] = Field(None, description="Phase 3 story structure results")
    style_preferences: Optional[Dict[str, Any]] = Field(None, description="Style preferences")
    layout_constraints: Optional[Dict[str, Any]] = Field(None, description="Layout constraints")

class NameGenerationOutput(BaseModel):
    """Output schema for Phase 4: Name Generation."""
    pages: List[PageLayout] = Field(..., min_items=1, description="Generated page layouts")
    total_pages: int = Field(..., ge=1, description="Total number of pages")
    total_panels: int = Field(..., ge=1, description="Total number of panels")
    shot_list: List[ShotListItem] = Field(..., description="Detailed shot list")
    layout_analysis: LayoutAnalysis = Field(..., description="Layout analysis")
    camera_statistics: CameraStatistics = Field(..., description="Camera usage statistics")
    composition_guide: Dict[str, Any] = Field(default_factory=dict, description="Composition guidelines")
    reading_flow: Dict[str, ReadingFlow] = Field(default_factory=dict, description="Per-page reading flow")
    dramatic_moments: List[DramaticMoment] = Field(default_factory=list, description="Identified dramatic moments")
    panel_transitions: List[PanelTransition] = Field(default_factory=list, description="Panel transitions")
    quality_metrics: Dict[str, float] = Field(default_factory=dict, description="Quality assessment metrics")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")

# =====================================
# Template and Configuration Models
# =====================================

class LayoutTemplate(BaseModel):
    """Layout template definition."""
    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    panel_count: int = Field(..., ge=1, le=12, description="Number of panels")
    grid_layout: Tuple[int, int] = Field(..., description="Grid dimensions (rows, cols)")
    panel_positions: List[PanelPosition] = Field(..., description="Predefined panel positions")
    panel_sizes: List[PanelSize] = Field(..., description="Predefined panel sizes")
    suitable_genres: List[str] = Field(default_factory=list, description="Suitable genres")
    complexity_rating: int = Field(..., ge=1, le=5, description="Template complexity (1=simple, 5=complex)")

class CompositionTemplate(BaseModel):
    """Composition template for specific effects."""
    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    primary_rule: CompositionRuleType = Field(..., description="Primary composition rule")
    focal_point_pattern: List[Tuple[float, float]] = Field(..., description="Focal point pattern")
    suitable_emotions: List[str] = Field(default_factory=list, description="Suitable emotions")
    impact_level: ImportanceLevel = Field(..., description="Visual impact level")

class PanelGenerationConfig(BaseModel):
    """Configuration for panel generation."""
    layout_patterns: Dict[LayoutPatternType, LayoutPattern] = Field(..., description="Available layout patterns")
    camera_angles: Dict[CameraAngleType, Dict[str, Any]] = Field(..., description="Camera angle configurations")
    composition_rules: Dict[CompositionRuleType, float] = Field(..., description="Composition rule weights")
    panel_shapes: Dict[PanelShapeType, Dict[str, Any]] = Field(..., description="Panel shape configurations")
    layout_templates: List[LayoutTemplate] = Field(default_factory=list, description="Available layout templates")
    composition_templates: List[CompositionTemplate] = Field(default_factory=list, description="Composition templates")
    quality_thresholds: Dict[str, float] = Field(default_factory=dict, description="Quality thresholds")