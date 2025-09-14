"""Phase 4: Panel Layout and Composition Generation Agent."""

from .agent import Phase4NameAgent
from .validator import Phase4Validator
from .schemas import (
    # Input/Output schemas
    NameGenerationInput,
    NameGenerationOutput,

    # Core models
    Panel,
    PageLayout,
    PanelSize,
    PanelPosition,
    CameraSettings,
    CompositionGuide,
    LayoutPattern,
    ReadingFlow,
    PanelTransition,
    DramaticMoment,
    CameraStatistics,
    LayoutAnalysis,
    ShotListItem,

    # Enum types
    LayoutPatternType,
    CameraAngleType,
    CompositionRuleType,
    PanelShapeType,
    BorderStyleType,
    ImportanceLevel,
    TransitionType,

    # Template and configuration
    LayoutTemplate,
    CompositionTemplate,
    PanelGenerationConfig
)
from .processors import NameGenerator

__all__ = [
    "Phase4NameAgent",
    "Phase4Validator",
    "NameGenerationInput",
    "NameGenerationOutput",
    "Panel",
    "PageLayout",
    "PanelSize",
    "PanelPosition",
    "CameraSettings",
    "CompositionGuide",
    "LayoutPattern",
    "ReadingFlow",
    "PanelTransition",
    "DramaticMoment",
    "CameraStatistics",
    "LayoutAnalysis",
    "ShotListItem",
    "LayoutPatternType",
    "CameraAngleType",
    "CompositionRuleType",
    "PanelShapeType",
    "BorderStyleType",
    "ImportanceLevel",
    "TransitionType",
    "LayoutTemplate",
    "CompositionTemplate",
    "PanelGenerationConfig",
    "NameGenerator"
]