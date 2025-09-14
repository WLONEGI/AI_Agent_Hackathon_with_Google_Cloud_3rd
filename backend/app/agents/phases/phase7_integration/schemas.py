"""Phase 7: Final Integration and Quality Adjustment Schemas.

This module defines the Pydantic models and data structures for Phase 7,
which handles final integration, quality assessment, and output formatting.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# Enums
class QualityGrade(str, Enum):
    """Overall quality grade classification."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


class OutputFormat(str, Enum):
    """Available output formats."""
    COMPREHENSIVE = "comprehensive"
    SIMPLIFIED = "simplified"
    PREVIEW = "preview"
    PRODUCTION = "production"


class IntegrationStatus(str, Enum):
    """Integration process status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Input/Output Models
class FinalIntegrationInput(BaseModel):
    """Input for Phase 7 final integration."""
    session_id: str
    user_id: str
    phase_number: int = 7
    previous_results: Dict[int, Dict[str, Any]]
    output_format: OutputFormat = OutputFormat.COMPREHENSIVE
    quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    integration_preferences: Optional[Dict[str, Any]] = None


class FinalIntegrationOutput(BaseModel):
    """Output from Phase 7 final integration."""
    quality_assessment: Dict[str, Any]
    compiled_pages: List[Dict[str, Any]]
    reading_validation: Dict[str, Any]
    compilation_metadata: Dict[str, Any]
    formatted_output: Dict[str, Any]
    output_metadata: Dict[str, Any]
    file_suggestions: List[Dict[str, str]]
    manga_metadata: Dict[str, Any]
    improvement_plan: Dict[str, Any]
    final_scores: Dict[str, float]
    integration_status: IntegrationStatus
    total_pages: int
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    quality_grade: QualityGrade
    production_ready: bool
    processing_summary: Dict[str, Any]


# Quality Assessment Models
class QualityMetric(BaseModel):
    """Individual quality metric result."""
    name: str
    score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    details: Dict[str, Any]
    recommendations: List[str]


class QualityAssessment(BaseModel):
    """Comprehensive quality assessment results."""
    overall_score: float = Field(ge=0.0, le=1.0)
    metrics: List[QualityMetric]
    category_scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    critical_issues: List[str]
    recommendations: List[str]
    assessment_timestamp: datetime = Field(default_factory=datetime.utcnow)


# Page Compilation Models
class CompiledPage(BaseModel):
    """A single compiled manga page."""
    page_number: int
    panels: List[Dict[str, Any]]
    layout_type: str
    reading_flow: Dict[str, Any]
    visual_balance: Dict[str, Any]
    text_density: float
    image_elements: List[Dict[str, Any]]
    quality_scores: Dict[str, float]


class ReadingValidation(BaseModel):
    """Reading flow and navigation validation."""
    flow_score: float = Field(ge=0.0, le=1.0)
    navigation_clarity: float = Field(ge=0.0, le=1.0)
    pacing_consistency: float = Field(ge=0.0, le=1.0)
    visual_hierarchy: float = Field(ge=0.0, le=1.0)
    issues_found: List[str]
    suggestions: List[str]


class CompilationMetadata(BaseModel):
    """Metadata from the compilation process."""
    total_panels: int
    total_pages: int
    average_panels_per_page: float
    dominant_layout_types: List[str]
    text_to_image_ratio: float
    processing_time_seconds: float
    compilation_timestamp: datetime = Field(default_factory=datetime.utcnow)


# Output Formatting Models
class FormattedOutput(BaseModel):
    """Formatted output structure."""
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    file_suggestions: List[Dict[str, str]]
    format_type: OutputFormat
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)


class FileSuggestion(BaseModel):
    """File output suggestion."""
    filename: str
    format: str
    description: str
    size_estimate: Optional[str] = None
    quality_level: Optional[str] = None


# Improvement Planning Models
class ImprovementPlan(BaseModel):
    """Comprehensive improvement plan."""
    priority_issues: List[str]
    quick_fixes: List[str]
    major_improvements: List[str]
    estimated_effort: Dict[str, str]
    impact_assessment: Dict[str, float]
    implementation_order: List[str]


# Final Scores Models
class FinalScores(BaseModel):
    """Final quality and readiness scores."""
    overall_score: float = Field(ge=0.0, le=1.0)
    content_quality: float = Field(ge=0.0, le=1.0)
    visual_appeal: float = Field(ge=0.0, le=1.0)
    technical_execution: float = Field(ge=0.0, le=1.0)
    narrative_coherence: float = Field(ge=0.0, le=1.0)
    production_readiness: float = Field(ge=0.0, le=1.0)
    market_appeal: float = Field(ge=0.0, le=1.0)


# Manga Metadata Models
class MangaMetadata(BaseModel):
    """Comprehensive manga metadata."""
    title: Optional[str] = None
    genre: Optional[str] = None
    target_audience: Optional[str] = None
    page_count: int
    panel_count: int
    character_count: int
    estimated_reading_time: Optional[str] = None
    complexity_score: float = Field(ge=0.0, le=1.0)
    style_classification: Optional[str] = None
    content_tags: List[str] = Field(default_factory=list)
    creation_timestamp: datetime = Field(default_factory=datetime.utcnow)


# Processing Summary Models
class ProcessingSummary(BaseModel):
    """Summary of the entire processing pipeline."""
    phases_completed: List[int]
    total_processing_time: float
    phase_timings: Dict[str, float]
    quality_progression: Dict[str, float]
    key_achievements: List[str]
    major_challenges: List[str]
    final_assessment: str
    next_steps: List[str]


# Configuration Models
class IntegrationConfig(BaseModel):
    """Configuration for integration process."""
    quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    enable_ai_enhancement: bool = True
    output_formats: List[OutputFormat] = Field(default_factory=lambda: [OutputFormat.COMPREHENSIVE])
    detailed_reporting: bool = True
    include_recommendations: bool = True
    generate_preview: bool = True
    max_improvement_suggestions: int = Field(default=10, ge=1, le=50)