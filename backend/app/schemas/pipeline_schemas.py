"""Pydantic schemas for manga generation pipeline data flow."""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from uuid import UUID
from enum import Enum


# Base schemas
class QualityLevel(str, Enum):
    """Quality level enumeration."""
    ULTRA_HIGH = "ultra_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    PREVIEW = "preview"


class PhaseStatus(str, Enum):
    """Phase execution status."""
    PENDING = "pending"
    PROCESSING = "processing"
    WAITING_FEEDBACK = "waiting_feedback"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


# Phase 1 Schemas
class WorldSettingSchema(BaseModel):
    """World setting information."""
    time_period: str
    location: str
    atmosphere: str


class Phase1OutputSchema(BaseModel):
    """Phase 1 (Concept Analysis) output schema."""
    original_text: str
    text_length: int
    themes: List[str]
    genre: str
    world_setting: WorldSettingSchema
    tone: str
    key_elements: List[str]
    target_audience: str
    narrative_style: str
    estimated_pages: int

    @validator("genre")
    def validate_genre(cls, v):
        valid_genres = ["fantasy", "romance", "action", "mystery", "slice_of_life", "sci_fi", "horror", "general"]
        if v not in valid_genres:
            raise ValueError(f"Genre must be one of {valid_genres}")
        return v

    @validator("estimated_pages")
    def validate_pages(cls, v):
        if v < 1 or v > 100:
            raise ValueError("Estimated pages must be between 1 and 100")
        return v


# Phase 2 Schemas
class CharacterSchema(BaseModel):
    """Individual character schema."""
    name: str
    role: str
    importance: int = Field(..., ge=1, le=10)
    age: int = Field(..., ge=1, le=150)
    personality: List[str]
    background: str
    goals: str
    appearance: str
    special_traits: List[str]
    arc_potential: str

    @validator("role")
    def validate_role(cls, v):
        valid_roles = ["protagonist", "antagonist", "mentor", "ally", "support"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of {valid_roles}")
        return v


class VisualDescriptionSchema(BaseModel):
    """Visual description for character."""
    base_prompt: str
    style_tags: List[str]
    color_palette: List[str]
    pose_suggestions: List[str]
    background_elements: List[str]
    art_style: str


class Phase2OutputSchema(BaseModel):
    """Phase 2 (Character Design) output schema."""
    characters: List[CharacterSchema]
    visual_descriptions: Dict[str, VisualDescriptionSchema]
    character_relationships: Dict[str, Any]
    total_character_count: int
    main_character_count: int
    character_diversity_score: float = Field(..., ge=0.0, le=1.0)
    visual_consistency_guidelines: Dict[str, Any]


# Phase 3 Schemas
class SceneSchema(BaseModel):
    """Individual scene schema."""
    scene_number: int
    pages: List[int]
    page_count: int
    title: str
    purpose: str
    pacing: str
    emotional_beat: str
    visual_style: str
    transition_type: str
    key_story_function: str

    @validator("pacing")
    def validate_pacing(cls, v):
        if v not in ["fast", "medium", "slow"]:
            raise ValueError("Pacing must be fast, medium, or slow")
        return v


class TensionCurvePoint(BaseModel):
    """Point on tension curve."""
    scene_number: int
    tension_level: int = Field(..., ge=1, le=10)
    description: str


class Phase3OutputSchema(BaseModel):
    """Phase 3 (Story Structure) output schema."""
    story_structure: Dict[str, Any]
    plot_progression: Dict[str, Any]
    scene_breakdown: List[SceneSchema]
    narrative_flow: Dict[str, Any]
    pacing_analysis: Dict[str, Any]
    total_scenes: int
    story_complexity_score: float = Field(..., ge=0.0, le=1.0)
    theme_integration: Dict[str, Any]
    conflict_structure: Dict[str, Any]


# Phase 4 Schemas
class PanelSchema(BaseModel):
    """Individual panel schema."""
    panel_number: int
    page_number: int
    scene_number: int
    size: str
    aspect_ratio: str
    camera_angle: str
    camera_position: str
    composition: str
    focus_element: str
    background_detail: str
    dialogue_space: str
    visual_purpose: str
    emotional_tone: str
    transition_type: str
    special_effects: List[str]
    character_prominence: float = Field(..., ge=0.0, le=1.0)

    @validator("size")
    def validate_size(cls, v):
        if v not in ["splash", "large", "medium", "small"]:
            raise ValueError("Size must be splash, large, medium, or small")
        return v


class PageLayoutSchema(BaseModel):
    """Page layout schema."""
    page_number: int
    scene_numbers: List[int]
    panels: List[PanelSchema]
    page_pacing: str
    panel_count: int
    layout_type: str
    page_flow: str
    climax_panel: Optional[int]
    visual_weight_distribution: str
    reading_time_seconds: int


class Phase4OutputSchema(BaseModel):
    """Phase 4 (Panel Layout) output schema."""
    page_layouts: List[PageLayoutSchema]
    panel_specifications: List[Dict[str, Any]]
    camera_work: Dict[str, Any]
    visual_flow: Dict[str, Any]
    composition_guidelines: Dict[str, Any]
    total_pages: int
    total_panels: int
    layout_complexity_score: float = Field(..., ge=0.0, le=1.0)
    visual_storytelling_score: float = Field(..., ge=0.0, le=1.0)
    pacing_visual_alignment: Dict[str, Any]


# Phase 5 Schemas
class ImageGenerationResultSchema(BaseModel):
    """Image generation result schema."""
    panel_id: str
    success: bool
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    generation_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    retry_count: int = 0


class QualityAnalysisSchema(BaseModel):
    """Quality analysis schema."""
    success_rate: float = Field(..., ge=0.0, le=1.0)
    average_quality_score: float = Field(..., ge=0.0, le=1.0)
    average_generation_time_ms: float
    quality_distribution: Dict[str, int]
    retry_statistics: Dict[str, int]
    failure_analysis: Dict[str, int]
    total_generated: int
    successful_generations: int
    failed_generations: int
    recommendations: List[str]


class Phase5OutputSchema(BaseModel):
    """Phase 5 (Image Generation) output schema."""
    generated_images: List[ImageGenerationResultSchema]
    scene_image_mapping: Dict[str, Any]
    quality_analysis: QualityAnalysisSchema
    consistency_report: Dict[str, Any]
    generation_stats: Dict[str, Any]
    total_images_generated: int
    successful_generations: int
    failed_generations: int
    average_generation_time: float
    parallel_efficiency_score: float = Field(..., ge=0.0, le=1.0)
    cache_utilization: Dict[str, Any]


# Phase 6 Schemas
class DialogueElementSchema(BaseModel):
    """Individual dialogue element schema."""
    speaker: str
    text: str
    dialogue_type: str
    emotion: str
    importance: str
    text_length: int
    estimated_syllables: int
    speech_pattern: str

    @validator("dialogue_type")
    def validate_dialogue_type(cls, v):
        valid_types = ["speech", "thought", "shout", "whisper", "narration"]
        if v not in valid_types:
            raise ValueError(f"Dialogue type must be one of {valid_types}")
        return v

    @validator("importance")
    def validate_importance(cls, v):
        if v not in ["high", "medium", "low"]:
            raise ValueError("Importance must be high, medium, or low")
        return v


class TextPlacementSchema(BaseModel):
    """Text placement schema."""
    panel_id: str
    element_type: str
    speaker: Optional[str]
    text_content: str
    dialogue_type: str
    position: Dict[str, float]
    bubble_style: str
    text_area: Dict[str, Any]
    reading_order: int
    importance: str
    speech_pattern: Optional[str]
    emotion: str
    tail_direction: Optional[str]


class Phase6OutputSchema(BaseModel):
    """Phase 6 (Dialogue Placement) output schema."""
    dialogue_content: List[Dict[str, Any]]
    text_placements: List[TextPlacementSchema]
    typography_specifications: Dict[str, Any]
    bubble_designs: List[Dict[str, Any]]
    dialogue_flow: Dict[str, Any]
    readability_analysis: Dict[str, Any]
    total_dialogue_elements: int
    characters_speaking: int
    dialogue_density_score: float = Field(..., ge=0.0, le=1.0)
    readability_score: float = Field(..., ge=0.0, le=1.0)
    text_image_integration_score: float = Field(..., ge=0.0, le=1.0)


# Phase 7 Schemas
class QualityMetricSchema(BaseModel):
    """Quality metric result schema."""
    score: float = Field(..., ge=0.0, le=1.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    weighted_score: float = Field(..., ge=0.0, le=1.0)
    details: Dict[str, Any]
    recommendations: List[str]


class CompletionStatusSchema(BaseModel):
    """Page completion status schema."""
    total_panels: int
    panels_with_images: int
    panels_with_text: int
    complete_panels: int
    completion_percentage: float = Field(..., ge=0.0, le=1.0)


class CompiledPanelSchema(BaseModel):
    """Compiled panel with all elements."""
    panel_id: str
    panel_number: int
    layout: Dict[str, Any]
    image: Dict[str, Any]
    camera_work: Dict[str, Any]
    text_elements: List[Dict[str, Any]]
    visual_effects: List[str]
    mood: str


class CompiledPageSchema(BaseModel):
    """Compiled page with all panels."""
    page_number: int
    panels: List[CompiledPanelSchema]
    layout_type: str
    reading_time_seconds: int
    scene_numbers: List[int]
    visual_weight_distribution: str
    page_completion_status: CompletionStatusSchema


class Phase7OutputSchema(BaseModel):
    """Phase 7 (Final Integration) output schema."""
    quality_assessment: Dict[str, QualityMetricSchema]
    compiled_pages: List[CompiledPageSchema]
    layout_optimization: Dict[str, Any]
    reading_experience: Dict[str, Any]
    manga_metadata: Dict[str, Any]
    output_formats: Dict[str, Any]
    improvement_plan: Dict[str, Any]
    final_scores: Dict[str, Any]
    integration_status: str
    total_pages: int
    overall_quality_score: float = Field(..., ge=0.0, le=1.0)
    quality_grade: str
    production_ready: bool
    processing_summary: Dict[str, Any]


# Pipeline Schemas
class PhaseExecutionStatusSchema(BaseModel):
    """Phase execution status schema."""
    phase_number: int
    agent_name: str
    status: PhaseStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    execution_time_seconds: Optional[float]
    retry_count: int = 0
    error_message: Optional[str]
    dependencies: List[int]
    parallel_group: Optional[int]


class PipelineStatusSchema(BaseModel):
    """Pipeline execution status schema."""
    status: str
    current_phase: int
    total_phases: int
    progress_percentage: float = Field(..., ge=0.0, le=100.0)
    session_id: Optional[UUID]
    execution_stats: Dict[str, Any]
    phase_statuses: Dict[int, PhaseExecutionStatusSchema]


class PipelineResultSchema(BaseModel):
    """Complete pipeline result schema."""
    execution_summary: Dict[str, Any]
    quality_summary: Dict[str, Any]
    content_summary: Dict[str, Any]
    phase_summary: Dict[str, Dict[str, Any]]
    full_results: Dict[str, Any]
    session_info: Dict[str, Any]


# Input/Request Schemas
class MangaGenerationRequestSchema(BaseModel):
    """Manga generation request schema."""
    input_text: str = Field(..., min_length=10, max_length=10000)
    title: Optional[str] = Field(None, max_length=255)
    genre_preference: Optional[str] = None
    quality_level: QualityLevel = QualityLevel.HIGH
    style_preference: Optional[str] = None
    target_audience: Optional[str] = None
    hitl_enabled: bool = True
    auto_proceed: bool = False
    custom_parameters: Optional[Dict[str, Any]] = None

    @validator("input_text")
    def validate_input_text(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Input text must be at least 10 characters long")
        return v.strip()

    @validator("genre_preference")
    def validate_genre_preference(cls, v):
        if v is not None:
            valid_genres = ["fantasy", "romance", "action", "mystery", "slice_of_life", "sci_fi", "horror", "general"]
            if v not in valid_genres:
                raise ValueError(f"Genre preference must be one of {valid_genres}")
        return v


class HITLFeedback(BaseModel):
    """Human-in-the-Loop feedback schema."""
    phase_number: int = Field(..., ge=1, le=7)
    feedback_text: str
    feedback_type: str = "text"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    
    @validator("feedback_type")
    def validate_feedback_type(cls, v):
        valid_types = ["text", "selection", "adjustment", "regeneration", "approval"]
        if v not in valid_types:
            raise ValueError(f"Feedback type must be one of {valid_types}")
        return v


class FeedbackRequestSchema(BaseModel):
    """User feedback request schema."""
    session_id: UUID
    phase_number: int = Field(..., ge=1, le=7)
    feedback_type: str
    feedback_text: Optional[str] = None
    feedback_data: Optional[Dict[str, Any]] = None
    satisfaction_score: Optional[int] = Field(None, ge=1, le=5)
    apply_feedback: bool = True

    @validator("feedback_type")
    def validate_feedback_type(cls, v):
        valid_types = ["text", "selection", "adjustment", "regeneration", "approval"]
        if v not in valid_types:
            raise ValueError(f"Feedback type must be one of {valid_types}")
        return v


class RegenerationRequestSchema(BaseModel):
    """Phase regeneration request schema."""
    session_id: UUID
    phase_number: int = Field(..., ge=1, le=7)
    modifications: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    preserve_later_phases: bool = False


# Response Schemas
class BaseResponseSchema(BaseModel):
    """Base response schema."""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MangaGenerationResponseSchema(BaseResponseSchema):
    """Manga generation response schema."""
    session_id: UUID
    status: str
    progress_percentage: float
    current_phase: int
    estimated_completion_time: Optional[datetime]
    preview_available: bool = False
    feedback_required: bool = False


class PhaseResultResponseSchema(BaseResponseSchema):
    """Phase result response schema."""
    session_id: UUID
    phase_number: int
    phase_name: str
    result_data: Dict[str, Any]
    preview_data: Optional[Dict[str, Any]]
    quality_metrics: Optional[Dict[str, Any]]
    feedback_requested: bool = False


class PipelineCompleteResponseSchema(BaseResponseSchema):
    """Pipeline completion response schema."""
    session_id: UUID
    final_results: PipelineResultSchema
    download_urls: Dict[str, str]
    quality_report: Dict[str, Any]
    production_ready: bool


class ErrorResponseSchema(BaseResponseSchema):
    """Error response schema."""
    error_code: str
    error_details: Optional[Dict[str, Any]]
    retry_possible: bool = False
    suggested_action: Optional[str] = None


# Utility Schemas
class ProgressUpdateSchema(BaseModel):
    """Progress update schema for real-time updates."""
    session_id: UUID
    current_phase: int
    total_phases: int
    progress_percentage: float
    status: str
    phase_name: str
    estimated_time_remaining: Optional[int]  # seconds
    current_operation: Optional[str]


class PreviewRequestSchema(BaseModel):
    """Preview generation request schema."""
    session_id: UUID
    phase_number: int = Field(..., ge=1, le=7)
    quality_level: QualityLevel = QualityLevel.MEDIUM


class PreviewResponseSchema(BaseResponseSchema):
    """Preview response schema."""
    session_id: UUID
    phase_number: int
    preview_data: Dict[str, Any]
    preview_url: Optional[str]
    expires_at: Optional[datetime]


# Validation Schemas
class ValidationResultSchema(BaseModel):
    """Validation result schema."""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []


class QualityValidationSchema(BaseModel):
    """Quality validation schema."""
    overall_score: float = Field(..., ge=0.0, le=1.0)
    category_scores: Dict[str, float]
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    production_ready: bool
    quality_gate_passed: bool


# Base Pipeline Classes
class PhaseInput(BaseModel):
    """Base input schema for pipeline phases."""
    session_id: str
    user_id: str
    phase_number: int
    previous_results: Optional[Dict[int, Any]] = None
    accumulated_context: Dict[str, Any] = {}
    user_preferences: Dict[str, Any] = {}


class PhaseOutput(BaseModel):
    """Base output schema for pipeline phases."""
    phase_number: int
    status: PhaseStatus
    content: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    processing_time_seconds: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PipelineState(BaseModel):
    """Pipeline execution state tracking."""
    session_id: str
    user_id: str
    current_phase: int
    total_phases: int = 7
    phase_results: Dict[int, Dict[str, Any]] = {}
    accumulated_context: Dict[str, Any] = {}
    status: PhaseStatus = PhaseStatus.PENDING
    started_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Export all schemas
__all__ = [
    # Phase output schemas
    "Phase1OutputSchema",
    "Phase2OutputSchema", 
    "Phase3OutputSchema",
    "Phase4OutputSchema",
    "Phase5OutputSchema",
    "Phase6OutputSchema",
    "Phase7OutputSchema",
    
    # Pipeline schemas
    "PipelineStatusSchema",
    "PipelineResultSchema",
    "PhaseExecutionStatusSchema",
    "PhaseInput",
    "PhaseOutput", 
    "PipelineState",
    
    # Request schemas
    "MangaGenerationRequestSchema",
    "HITLFeedback",
    "FeedbackRequestSchema",
    "RegenerationRequestSchema",
    "PreviewRequestSchema",
    
    # Response schemas
    "MangaGenerationResponseSchema",
    "PhaseResultResponseSchema",
    "PipelineCompleteResponseSchema",
    "ErrorResponseSchema",
    "PreviewResponseSchema",
    
    # Utility schemas
    "ProgressUpdateSchema",
    "ValidationResultSchema",
    "QualityValidationSchema",
    
    # Component schemas
    "CharacterSchema",
    "SceneSchema",
    "PanelSchema",
    "PageLayoutSchema",
    "DialogueElementSchema",
    "TextPlacementSchema",
    "CompiledPageSchema",
    
    # Enums
    "QualityLevel",
    "PhaseStatus"
]