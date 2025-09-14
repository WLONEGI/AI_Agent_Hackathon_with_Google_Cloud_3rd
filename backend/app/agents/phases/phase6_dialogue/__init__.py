"""Phase 6: Dialogue and Text Placement Agent."""

from .agent import Phase6DialogueAgent
from .validator import Phase6Validator
from .schemas import (
    # Input/Output schemas
    DialoguePlacementInput,
    DialoguePlacementOutput,

    # Core models
    PanelDialogue,
    DialogueElement,
    NarrationElement,
    TextPlacement,
    BubbleDesign,
    TypographySpecifications,
    ReadabilityOptimization,
    DialogueFlowAnalysis,
    TimingAnalysis,
    QualityMetrics,

    # Position and layout models
    Position,
    TextArea,
    BorderProperties,
    FillProperties,
    TailProperties,

    # Typography models
    TypographyFont,
    TypographySpecification,
    SpecialCharacters,
    JapaneseTextRules,

    # Analysis models
    FlowAnalysis,
    DensityAnalysis,
    InterferenceAnalysis,
    ReadabilityIssue,

    # Task models
    DialogueGenerationTask,
    TextPlacementTask,

    # Enum types
    DialogueType,
    BubbleStyle,
    TailStyle,
    TextSize,
    FontWeight,
    SpeechPattern,
    PlacementPosition,
    ImportanceLevel,
    ReadingDirection,
    TextAlignment,
    BubbleShape,
    BorderStyle,
    TailDirection,
    ElementType,
    NarrationStyle,
    TypographyStyle,

    # Configuration
    DialogueGenerationConfig
)
from .processors import DialogueGenerator, TextFormatter

__all__ = [
    "Phase6DialogueAgent",
    "Phase6Validator",
    "DialoguePlacementInput",
    "DialoguePlacementOutput",
    "PanelDialogue",
    "DialogueElement",
    "NarrationElement",
    "TextPlacement",
    "BubbleDesign",
    "TypographySpecifications",
    "ReadabilityOptimization",
    "DialogueFlowAnalysis",
    "TimingAnalysis",
    "QualityMetrics",
    "Position",
    "TextArea",
    "BorderProperties",
    "FillProperties",
    "TailProperties",
    "TypographyFont",
    "TypographySpecification",
    "SpecialCharacters",
    "JapaneseTextRules",
    "FlowAnalysis",
    "DensityAnalysis",
    "InterferenceAnalysis",
    "ReadabilityIssue",
    "DialogueGenerationTask",
    "TextPlacementTask",
    "DialogueType",
    "BubbleStyle",
    "TailStyle",
    "TextSize",
    "FontWeight",
    "SpeechPattern",
    "PlacementPosition",
    "ImportanceLevel",
    "ReadingDirection",
    "TextAlignment",
    "BubbleShape",
    "BorderStyle",
    "TailDirection",
    "ElementType",
    "NarrationStyle",
    "TypographyStyle",
    "DialogueGenerationConfig",
    "DialogueGenerator",
    "TextFormatter"
]