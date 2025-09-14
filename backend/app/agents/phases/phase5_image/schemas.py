"""Phase 5: Image Generation - Pydantic Schema Definitions."""

from typing import Dict, Any, Optional, List, Tuple, Literal, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from uuid import UUID

# =====================================
# Enum Definitions
# =====================================

class CameraAngleType(str, Enum):
    """Camera angle types for image generation."""
    EXTREME_CLOSE_UP = "extreme_close_up"
    CLOSE_UP = "close_up"
    MEDIUM_SHOT = "medium_shot"
    FULL_SHOT = "full_shot"
    WIDE_SHOT = "wide_shot"
    BIRD_EYE = "bird_eye"
    WORM_EYE = "worm_eye"

class CompositionType(str, Enum):
    """Composition style types."""
    RULE_OF_THIRDS = "rule_of_thirds"
    CENTERED_COMPOSITION = "centered_composition"
    DIAGONAL_COMPOSITION = "diagonal_composition"
    ENVIRONMENTAL_COMPOSITION = "environmental_composition"

class EmphasisType(str, Enum):
    """Style emphasis types."""
    CHARACTER_FOCUS = "character_focus"
    ENVIRONMENT_FOCUS = "environment_focus"
    ACTION_SCENE = "action_scene"
    EMOTIONAL_SCENE = "emotional_scene"
    BALANCED = "balanced"

class QualityLevel(str, Enum):
    """Quality level options."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"

class ColorMode(str, Enum):
    """Color mode options."""
    BLACK_AND_WHITE = "black_and_white"
    GRAYSCALE = "grayscale"
    COLOR = "color"
    SEPIA = "sepia"

class EnergyLevel(str, Enum):
    """Energy level for dynamic scenes."""
    GENTLE = "gentle"
    MODERATE = "moderate"
    HIGH = "high"
    INTENSE = "intense"
    ATMOSPHERIC = "atmospheric"

class LineWeight(str, Enum):
    """Line weight styles."""
    SOFT = "soft"
    STANDARD = "standard"
    BOLD = "bold"
    VARIED = "varied"

class BackgroundDetailLevel(str, Enum):
    """Background detail levels."""
    MINIMAL = "minimal"
    SIMPLE = "simple"
    MODERATE = "moderate"
    DETAILED = "detailed"
    ULTRA_DETAILED = "ultra_detailed"

class EmotionalTone(str, Enum):
    """Emotional tone options."""
    NEUTRAL = "neutral"
    TENSION = "tension"
    ANXIETY = "anxiety"
    CLIMAX = "climax"
    RELIEF = "relief"
    SATISFACTION = "satisfaction"
    CURIOSITY = "curiosity"

class LightingSetup(str, Enum):
    """Lighting setup options."""
    NATURAL_BALANCED = "natural_balanced"
    SOFT_NATURAL = "soft_natural"
    WARM_EVEN = "warm_even"
    DRAMATIC_HIGH_CONTRAST = "dramatic_high_contrast"
    HARSH_SHADOWS = "harsh_shadows"
    INTENSE_DIRECTIONAL = "intense_directional"

class PriorityLevel(int, Enum):
    """Task priority levels."""
    LOWEST = 1
    LOW = 2
    MEDIUM = 5
    HIGH = 7
    HIGHEST = 10

class ConsistencyLevel(str, Enum):
    """Consistency level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXCELLENT = "excellent"

# =====================================
# Core Models
# =====================================

class StyleParameters(BaseModel):
    """Style parameters for image generation."""
    art_style: str = Field(default="manga", description="Base art style")
    quality_level: QualityLevel = Field(..., description="Quality level setting")
    aspect_ratio: str = Field(default="4:3", description="Image aspect ratio")
    color_mode: ColorMode = Field(..., description="Color mode setting")
    emphasis: EmphasisType = Field(..., description="Visual emphasis type")
    detail_level: str = Field(..., description="Detail level specification")
    energy_level: Optional[EnergyLevel] = Field(None, description="Energy level for dynamic scenes")
    line_weight: Optional[LineWeight] = Field(None, description="Line weight style")
    dynamic_elements: bool = Field(default=False, description="Include dynamic elements")

class CharacterPromptInfo(BaseModel):
    """Character information for prompt generation."""
    name: str = Field(..., description="Character name")
    expression: str = Field(default="neutral", description="Character expression")
    prominence: float = Field(default=0.5, ge=0, le=1, description="Character prominence (0-1)")
    appearance_description: Optional[str] = Field(None, description="Appearance description")
    base_prompt: Optional[str] = Field(None, description="Base visual prompt")

class PanelSpecification(BaseModel):
    """Complete panel specification for image generation."""
    panel_id: str = Field(..., description="Unique panel identifier")
    panel_number: int = Field(default=1, ge=1, description="Panel number in sequence")
    page_number: int = Field(default=1, ge=1, description="Page number")
    scene_number: int = Field(default=1, ge=1, description="Scene number")

    # Visual settings
    camera_angle: CameraAngleType = Field(..., description="Camera angle type")
    composition: CompositionType = Field(..., description="Composition style")
    focus_element: str = Field(default="character_interaction", description="Focus element")
    background_detail: BackgroundDetailLevel = Field(default=BackgroundDetailLevel.MODERATE, description="Background detail level")

    # Mood and atmosphere
    emotional_tone: EmotionalTone = Field(default=EmotionalTone.NEUTRAL, description="Emotional tone")
    lighting_setup: LightingSetup = Field(default=LightingSetup.NATURAL_BALANCED, description="Lighting setup")

    # Characters in panel
    characters: List[CharacterPromptInfo] = Field(default_factory=list, description="Characters in this panel")

    # Technical settings
    size: str = Field(default="medium", description="Panel size specification")
    aspect_ratio: str = Field(default="4:3", description="Panel aspect ratio")

class ImageGenerationTask(BaseModel):
    """Individual image generation task."""
    panel_id: str = Field(..., description="Panel identifier")
    prompt: str = Field(..., min_length=10, description="Generation prompt")
    negative_prompt: str = Field(..., description="Negative prompt")
    style_parameters: StyleParameters = Field(..., description="Style parameters")
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM, description="Task priority")
    retry_count: int = Field(default=0, ge=0, description="Current retry count")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")

class ImageGenerationResult(BaseModel):
    """Result of image generation."""
    panel_id: str = Field(..., description="Panel identifier")
    success: bool = Field(..., description="Generation success status")
    image_url: Optional[str] = Field(None, description="Generated image URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    generation_time_ms: Optional[int] = Field(None, ge=0, description="Generation time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    quality_score: Optional[float] = Field(None, ge=0, le=1, description="Quality assessment score")
    retry_count: int = Field(default=0, ge=0, description="Number of retries used")

class StyleTemplate(BaseModel):
    """Style template configuration."""
    name: str = Field(..., description="Template name")
    base_style: str = Field(..., description="Base style description")
    emphasis: str = Field(..., description="Visual emphasis")
    background: str = Field(..., description="Background style")
    suitable_genres: List[str] = Field(default_factory=list, description="Suitable genres")
    energy_level: Optional[EnergyLevel] = Field(None, description="Energy level")
    line_weight: Optional[LineWeight] = Field(None, description="Line weight")

class QualityCriteria(BaseModel):
    """Quality assessment criteria."""
    character_accuracy: float = Field(default=0.25, ge=0, le=1, description="Character accuracy weight")
    style_consistency: float = Field(default=0.20, ge=0, le=1, description="Style consistency weight")
    composition_quality: float = Field(default=0.20, ge=0, le=1, description="Composition quality weight")
    technical_quality: float = Field(default=0.15, ge=0, le=1, description="Technical quality weight")
    narrative_clarity: float = Field(default=0.10, ge=0, le=1, description="Narrative clarity weight")
    artistic_appeal: float = Field(default=0.10, ge=0, le=1, description="Artistic appeal weight")

    @validator('*')
    def validate_sum_to_one(cls, v, values):
        # Check if all weights sum to approximately 1.0
        if len(values) == 5:  # All fields except the current one
            total = sum(values.values()) + v
            if not (0.99 <= total <= 1.01):
                raise ValueError(f'Quality criteria weights must sum to 1.0, got {total}')
        return v

class GenerationStatistics(BaseModel):
    """Generation statistics tracking."""
    total_generated: int = Field(default=0, ge=0, description="Total images generated")
    successful_generations: int = Field(default=0, ge=0, description="Successful generations")
    cache_hits: int = Field(default=0, ge=0, description="Cache hit count")
    average_generation_time: float = Field(default=0.0, ge=0, description="Average generation time")
    quality_distribution: Dict[str, int] = Field(default_factory=dict, description="Quality distribution")

class SceneImageMapping(BaseModel):
    """Mapping between scenes and generated images."""
    scene_number: int = Field(..., description="Scene number")
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Images for this scene")
    total_panels: int = Field(default=0, ge=0, description="Total panels in scene")

class QualityAnalysis(BaseModel):
    """Comprehensive quality analysis."""
    success_rate: float = Field(..., ge=0, le=1, description="Generation success rate")
    average_quality_score: float = Field(..., ge=0, le=1, description="Average quality score")
    average_generation_time_ms: float = Field(..., ge=0, description="Average generation time")
    quality_distribution: Dict[str, int] = Field(default_factory=dict, description="Quality score distribution")
    retry_statistics: Dict[str, int] = Field(default_factory=dict, description="Retry statistics")
    failure_analysis: Dict[str, int] = Field(default_factory=dict, description="Failure reason analysis")
    total_generated: int = Field(..., ge=0, description="Total images generated")
    successful_generations: int = Field(..., ge=0, description="Successful generations")
    failed_generations: int = Field(..., ge=0, description="Failed generations")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")

class ConsistencyAnalysis(BaseModel):
    """Character and style consistency analysis."""
    character_consistency: Dict[str, Any] = Field(default_factory=dict, description="Character consistency scores")
    style_consistency: Dict[str, Any] = Field(default_factory=dict, description="Style consistency analysis")
    quality_consistency: Dict[str, Any] = Field(default_factory=dict, description="Quality consistency analysis")
    overall_consistency_score: float = Field(..., ge=0, le=1, description="Overall consistency score")
    consistency_recommendations: List[str] = Field(default_factory=list, description="Consistency recommendations")

class CacheUtilization(BaseModel):
    """Cache utilization statistics."""
    cache_hit_rate: float = Field(..., ge=0, le=1, description="Cache hit rate")
    total_cache_entries: int = Field(..., ge=0, description="Total cache entries")
    cache_hits: int = Field(..., ge=0, description="Cache hits")
    total_requests: int = Field(..., ge=0, description="Total requests")
    cache_efficiency: ConsistencyLevel = Field(..., description="Cache efficiency level")

class ParallelEfficiency(BaseModel):
    """Parallel processing efficiency metrics."""
    efficiency_score: float = Field(..., ge=0, le=1, description="Parallel efficiency score")
    theoretical_sequential_time: float = Field(..., ge=0, description="Theoretical sequential time")
    actual_parallel_time: float = Field(..., ge=0, description="Actual parallel processing time")
    concurrency_benefit: float = Field(..., ge=0, le=1, description="Concurrency benefit factor")
    max_concurrent_generations: int = Field(..., ge=1, description="Maximum concurrent generations")

# =====================================
# Input/Output Schemas
# =====================================

class ImageGenerationInput(BaseModel):
    """Input schema for Phase 5: Image Generation."""
    original_text: str = Field(..., description="Original text content")
    phase1_results: Optional[Dict[str, Any]] = Field(None, description="Phase 1 concept analysis results")
    phase2_results: Optional[Dict[str, Any]] = Field(None, description="Phase 2 character design results")
    phase3_results: Optional[Dict[str, Any]] = Field(None, description="Phase 3 story structure results")
    phase4_results: Optional[Dict[str, Any]] = Field(None, description="Phase 4 panel layout results")
    style_preferences: Optional[Dict[str, Any]] = Field(None, description="Style preferences")
    generation_constraints: Optional[Dict[str, Any]] = Field(None, description="Generation constraints")
    max_concurrent_generations: int = Field(default=3, ge=1, le=10, description="Maximum concurrent generations")

class ImageGenerationOutput(BaseModel):
    """Output schema for Phase 5: Image Generation."""
    generated_images: List[ImageGenerationResult] = Field(..., description="Generated image results")
    scene_image_mapping: Dict[str, Any] = Field(default_factory=dict, description="Scene to image mapping")
    quality_analysis: QualityAnalysis = Field(..., description="Quality analysis results")
    consistency_report: ConsistencyAnalysis = Field(..., description="Consistency analysis")
    generation_stats: GenerationStatistics = Field(..., description="Generation statistics")
    total_images_generated: int = Field(..., ge=0, description="Total images generated")
    successful_generations: int = Field(..., ge=0, description="Successful generations")
    failed_generations: int = Field(..., ge=0, description="Failed generations")
    average_generation_time: float = Field(..., ge=0, description="Average generation time")
    parallel_efficiency_score: float = Field(..., ge=0, le=1, description="Parallel efficiency score")
    cache_utilization: CacheUtilization = Field(..., description="Cache utilization statistics")
    ai_response_metadata: Optional[Dict[str, Any]] = Field(None, description="AI response metadata")
    quality_metrics: Dict[str, float] = Field(default_factory=dict, description="Quality assessment metrics")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")

# =====================================
# Configuration Models
# =====================================

class ImageGenerationConfig(BaseModel):
    """Configuration for image generation."""
    style_templates: Dict[EmphasisType, StyleTemplate] = Field(..., description="Available style templates")
    quality_criteria: QualityCriteria = Field(..., description="Quality assessment criteria")
    default_style_parameters: StyleParameters = Field(..., description="Default style parameters")
    camera_angle_prompts: Dict[CameraAngleType, str] = Field(..., description="Camera angle prompt mappings")
    composition_prompts: Dict[CompositionType, str] = Field(..., description="Composition prompt mappings")
    emotional_tone_prompts: Dict[EmotionalTone, str] = Field(..., description="Emotional tone prompts")
    lighting_prompts: Dict[LightingSetup, str] = Field(..., description="Lighting setup prompts")
    negative_prompt_templates: List[str] = Field(..., description="Negative prompt templates")
    max_concurrent_generations: int = Field(default=3, ge=1, le=10, description="Max concurrent generations")
    cache_enabled: bool = Field(default=True, description="Enable result caching")
    retry_settings: Dict[str, int] = Field(default_factory=dict, description="Retry configuration")