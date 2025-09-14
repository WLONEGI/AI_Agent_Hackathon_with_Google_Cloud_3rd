"""Phase 7: Final Integration and Quality Adjustment.

This module provides comprehensive final integration and quality adjustment
capabilities for the manga generation pipeline.
"""

from .agent import Phase7IntegrationAgent
from .validator import Phase7Validator
from .schemas import (
    # Input/Output schemas
    FinalIntegrationInput,
    FinalIntegrationOutput,

    # Quality Assessment models
    QualityMetric,
    QualityAssessment,

    # Page Compilation models
    CompiledPage,
    ReadingValidation,
    CompilationMetadata,

    # Output Formatting models
    FormattedOutput,
    FileSuggestion,

    # Planning and Analysis models
    ImprovementPlan,
    FinalScores,
    MangaMetadata,
    ProcessingSummary,

    # Configuration models
    IntegrationConfig,

    # Enums
    QualityGrade,
    OutputFormat,
    IntegrationStatus
)

# Import processors for direct access
from .quality_assessment import QualityAssessmentModule
from .page_compiler import PageCompilerModule
from .output_formatter import OutputFormatterModule
from .prompts import FinalIntegrationPrompts

__all__ = [
    # Main components
    "Phase7IntegrationAgent",
    "Phase7Validator",

    # Input/Output schemas
    "FinalIntegrationInput",
    "FinalIntegrationOutput",

    # Quality models
    "QualityMetric",
    "QualityAssessment",

    # Page models
    "CompiledPage",
    "ReadingValidation",
    "CompilationMetadata",

    # Output models
    "FormattedOutput",
    "FileSuggestion",

    # Planning models
    "ImprovementPlan",
    "FinalScores",
    "MangaMetadata",
    "ProcessingSummary",

    # Configuration
    "IntegrationConfig",

    # Enums
    "QualityGrade",
    "OutputFormat",
    "IntegrationStatus",

    # Processors
    "QualityAssessmentModule",
    "PageCompilerModule",
    "OutputFormatterModule",
    "FinalIntegrationPrompts"
]