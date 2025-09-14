"""Schemas for Phase 3: Story Structure and Scene Analysis."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class StoryStructureType(str, Enum):
    """Story structure types."""
    THREE_ACT = "three_act"
    KISHOOTENKETSU = "kishootenketsu"
    HERO_JOURNEY = "hero_journey"
    FIVE_ACT = "five_act"
    CUSTOM = "custom"


class PacingType(str, Enum):
    """Scene pacing types."""
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"
    VERY_FAST = "very_fast"
    VARIABLE = "variable"


class ScenePurposeType(str, Enum):
    """Scene purpose classifications."""
    EXPOSITION = "exposition"
    INCITING_INCIDENT = "inciting_incident"
    RISING_ACTION = "rising_action"
    CLIMAX = "climax"
    FALLING_ACTION = "falling_action"
    RESOLUTION = "resolution"
    CHARACTER_DEVELOPMENT = "character_development"
    WORLD_BUILDING = "world_building"
    CONFLICT_ESCALATION = "conflict_escalation"
    EMOTIONAL_BEAT = "emotional_beat"
    TRANSITION = "transition"


class EmotionalBeatType(str, Enum):
    """Emotional beat types."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    EXCITEMENT = "excitement"
    TENSION = "tension"
    RELIEF = "relief"
    HOPE = "hope"
    DESPAIR = "despair"
    TRIUMPH = "triumph"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    CONFLICT = "conflict"
    PEACE = "peace"


class VisualStyleType(str, Enum):
    """Visual style classifications for scenes."""
    ACTION = "action"
    DIALOGUE = "dialogue"
    ATMOSPHERIC = "atmospheric"
    DYNAMIC = "dynamic"
    INTIMATE = "intimate"
    PANORAMIC = "panoramic"
    CLOSE_UP = "close_up"
    MONTAGE = "montage"


class TransitionType(str, Enum):
    """Scene transition types."""
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    MATCH_CUT = "match_cut"
    JUMP_CUT = "jump_cut"
    CROSS_FADE = "cross_fade"
    TIME_JUMP = "time_jump"
    LOCATION_CHANGE = "location_change"
    PERSPECTIVE_SHIFT = "perspective_shift"


class StoryFunctionType(str, Enum):
    """Key story function types."""
    SETUP = "setup"
    CATALYST = "catalyst"
    DEBATE = "debate"
    BREAK_INTO_TWO = "break_into_two"
    B_STORY = "b_story"
    FUN_AND_GAMES = "fun_and_games"
    MIDPOINT = "midpoint"
    BAD_GUYS_CLOSE_IN = "bad_guys_close_in"
    ALL_IS_LOST = "all_is_lost"
    DARK_NIGHT = "dark_night"
    BREAK_INTO_THREE = "break_into_three"
    FINALE = "finale"
    FINAL_IMAGE = "final_image"


class ActStructure(BaseModel):
    """Act structure definition."""
    act_number: int = Field(description="Act number")
    title: str = Field(description="Act title")
    purpose: str = Field(description="Act purpose and role in story")
    scene_range: List[int] = Field(description="Scene numbers included in this act")
    page_range: List[int] = Field(description="Page numbers covered by this act")
    duration_percentage: float = Field(ge=0.0, le=1.0, description="Percentage of total story duration")
    key_events: List[str] = Field(default=[], description="Major events in this act")
    character_arcs: List[str] = Field(default=[], description="Character development in this act")
    themes_explored: List[str] = Field(default=[], description="Themes explored in this act")


class StoryStructure(BaseModel):
    """Complete story structure definition."""
    type: StoryStructureType = Field(description="Type of story structure used")
    acts: List[ActStructure] = Field(description="Act breakdown")
    total_acts: int = Field(description="Total number of acts")
    structure_rationale: str = Field(description="Why this structure was chosen")
    adaptation_notes: List[str] = Field(default=[], description="Notes on structure adaptation")


class PlotProgression(BaseModel):
    """Plot progression mapping."""
    opening: str = Field(description="Story opening description")
    inciting_incident: str = Field(description="Inciting incident that starts the plot")
    rising_action: List[str] = Field(description="Rising action events")
    climax: str = Field(description="Story climax")
    falling_action: List[str] = Field(description="Falling action events")
    resolution: str = Field(description="Story resolution")
    progression_notes: List[str] = Field(default=[], description="Notes on plot progression")


class SceneDetails(BaseModel):
    """Detailed scene information."""
    scene_number: int = Field(description="Scene number")
    pages: List[int] = Field(description="Page numbers for this scene")
    page_count: int = Field(description="Number of pages in scene")
    title: str = Field(description="Scene title")
    purpose: ScenePurposeType = Field(description="Scene purpose")
    pacing: PacingType = Field(description="Scene pacing")
    emotional_beat: EmotionalBeatType = Field(description="Emotional beat of the scene")
    visual_style: VisualStyleType = Field(description="Recommended visual style")
    transition_type: TransitionType = Field(description="Transition to next scene")
    key_story_function: StoryFunctionType = Field(description="Key story function")

    # Additional scene details
    location: Optional[str] = Field(None, description="Scene location")
    time_of_day: Optional[str] = Field(None, description="Time of day")
    characters_present: List[str] = Field(default=[], description="Characters present in scene")
    key_dialogue: List[str] = Field(default=[], description="Important dialogue points")
    visual_elements: List[str] = Field(default=[], description="Key visual elements")
    mood: str = Field(default="neutral", description="Overall mood of the scene")
    conflict_elements: List[str] = Field(default=[], description="Conflict elements in scene")


class CharacterArc(BaseModel):
    """Character arc progression through story."""
    character_name: str = Field(description="Character name")
    arc_type: str = Field(description="Type of character arc")
    starting_state: str = Field(description="Character's starting emotional/psychological state")
    key_turning_points: List[str] = Field(description="Major turning points in arc")
    ending_state: str = Field(description="Character's ending state")
    growth_trajectory: str = Field(description="Overall growth trajectory")
    scene_involvement: List[int] = Field(description="Scene numbers where character is involved")


class ThemeDevelopment(BaseModel):
    """Theme development throughout story."""
    theme_name: str = Field(description="Theme name")
    introduction_scene: int = Field(description="Scene where theme is introduced")
    development_scenes: List[int] = Field(description="Scenes where theme develops")
    resolution_scene: int = Field(description="Scene where theme resolves")
    thematic_elements: List[str] = Field(description="Elements that express this theme")
    symbol_usage: List[str] = Field(default=[], description="Symbols used to represent theme")


class TensionPoint(BaseModel):
    """Tension curve point."""
    scene_number: int = Field(description="Scene number")
    tension_level: float = Field(ge=0.0, le=1.0, description="Tension level (0.0-1.0)")
    tension_type: str = Field(description="Type of tension")
    description: str = Field(description="Description of tension at this point")


class TensionCurve(BaseModel):
    """Story tension curve."""
    points: List[TensionPoint] = Field(description="Tension points throughout story")
    peak_tension_scene: int = Field(description="Scene with highest tension")
    lowest_tension_scene: int = Field(description="Scene with lowest tension")
    overall_pattern: str = Field(description="Overall tension pattern description")
    pacing_recommendations: List[str] = Field(default=[], description="Pacing recommendations")


class EmotionalJourney(BaseModel):
    """Reader's emotional journey."""
    scene_number: int = Field(description="Scene number")
    target_emotion: EmotionalBeatType = Field(description="Target reader emotion")
    emotional_intensity: float = Field(ge=0.0, le=1.0, description="Emotional intensity")
    emotional_trigger: str = Field(description="What triggers this emotion")
    transition_to_next: str = Field(description="How emotion transitions to next scene")


class StoryBeat(BaseModel):
    """Story beat information."""
    beat_number: int = Field(description="Beat number")
    scene_number: int = Field(description="Associated scene number")
    beat_type: str = Field(description="Type of story beat")
    description: str = Field(description="Beat description")
    character_states: List[str] = Field(description="Character states at this beat")
    plot_significance: str = Field(description="Significance to overall plot")


class PacingAnalysis(BaseModel):
    """Pacing analysis results."""
    overall_rhythm: str = Field(description="Overall story rhythm")
    pacing_match_score: float = Field(ge=0.0, le=1.0, description="How well pacing matches genre expectations")
    flow_issues: List[str] = Field(default=[], description="Identified pacing flow issues")
    recommendations: List[str] = Field(default=[], description="Pacing improvement recommendations")
    genre_alignment: str = Field(description="How pacing aligns with genre expectations")


class NarrativeFlow(BaseModel):
    """Narrative flow analysis."""
    character_arcs: List[CharacterArc] = Field(description="Character arc progressions")
    theme_development: List[ThemeDevelopment] = Field(description="Theme development tracking")
    tension_curve: TensionCurve = Field(description="Story tension analysis")
    emotional_journey: List[EmotionalJourney] = Field(description="Reader emotional journey")
    story_beats: List[StoryBeat] = Field(description="Key story beats")
    pacing_analysis: PacingAnalysis = Field(description="Pacing analysis results")


class ConflictAnalysis(BaseModel):
    """Conflict structure analysis."""
    primary_conflicts: List[str] = Field(description="Primary conflicts identified")
    conflict_types: List[str] = Field(description="Types of conflicts present")
    escalation_pattern: str = Field(description="How conflicts escalate")
    resolution_pattern: str = Field(description="How conflicts resolve")
    conflict_distribution: Dict[int, List[str]] = Field(description="Conflicts by scene number")


class ThemeIntegration(BaseModel):
    """Theme integration analysis."""
    themes_identified: List[str] = Field(description="Themes identified in story")
    integration_score: float = Field(ge=0.0, le=1.0, description="How well themes are integrated")
    thematic_consistency: float = Field(ge=0.0, le=1.0, description="Thematic consistency score")
    weak_integration_scenes: List[int] = Field(default=[], description="Scenes with weak theme integration")
    recommendations: List[str] = Field(default=[], description="Theme integration improvements")


class StoryAnalysisInput(BaseModel):
    """Input for Phase 3 story analysis."""
    # From Phase 1
    genre_analysis: Dict[str, Any] = Field(description="Genre analysis from Phase 1")
    themes: List[str] = Field(description="Story themes from Phase 1")
    tone: str = Field(description="Story tone")
    target_audience: str = Field(description="Target audience")
    estimated_pages: int = Field(description="Estimated page count")

    # From Phase 2
    characters: List[Dict[str, Any]] = Field(description="Character profiles from Phase 2")
    character_relationships: List[Dict[str, Any]] = Field(description="Character relationships")

    # Phase 3 specific inputs
    structure_preference: Optional[StoryStructureType] = Field(None, description="Preferred story structure")
    pacing_preference: Optional[PacingType] = Field(None, description="Preferred pacing style")
    scene_count_preference: Optional[int] = Field(None, ge=3, le=50, description="Preferred scene count")


class StoryAnalysisOutput(BaseModel):
    """Output for Phase 3 story analysis."""
    story_structure: StoryStructure = Field(description="Story structure breakdown")
    plot_progression: PlotProgression = Field(description="Plot progression mapping")
    scenes: List[SceneDetails] = Field(description="Detailed scene breakdown")
    narrative_flow: NarrativeFlow = Field(description="Narrative flow analysis")

    # Analysis metrics
    total_scenes: int = Field(description="Total number of scenes")
    story_complexity_score: float = Field(ge=0.0, le=1.0, description="Story complexity score")
    pacing_consistency_score: float = Field(ge=0.0, le=1.0, description="Pacing consistency score")
    character_integration_score: float = Field(ge=0.0, le=1.0, description="Character integration score")

    # Additional analysis
    conflict_analysis: ConflictAnalysis = Field(description="Conflict structure analysis")
    theme_integration: ThemeIntegration = Field(description="Theme integration analysis")

    # Next phase interface
    scene_summaries: List[Dict[str, str]] = Field(description="Brief scene summaries for next phases")
    visual_requirements: List[Dict[str, Any]] = Field(description="Visual requirements per scene")
    character_usage: Dict[str, List[int]] = Field(description="Character usage by scene numbers")

    # Generation metadata
    generation_timestamp: str = Field(description="ISO timestamp of generation")
    ai_model_used: str = Field(description="AI model used for generation")
    processing_time: float = Field(description="Processing time in seconds")


# Story structure templates for reference
STORY_STRUCTURE_TEMPLATES = {
    StoryStructureType.THREE_ACT: {
        "acts": [
            {"number": 1, "title": "Setup", "percentage": 0.25, "purpose": "Introduce characters and world"},
            {"number": 2, "title": "Confrontation", "percentage": 0.50, "purpose": "Develop conflict and obstacles"},
            {"number": 3, "title": "Resolution", "percentage": 0.25, "purpose": "Resolve conflicts and conclude"}
        ],
        "typical_beats": ["inciting_incident", "plot_point_1", "midpoint", "plot_point_2", "climax", "resolution"]
    },
    StoryStructureType.KISHOOTENKETSU: {
        "acts": [
            {"number": 1, "title": "Ki (Introduction)", "percentage": 0.25, "purpose": "Introduce setting and characters"},
            {"number": 2, "title": "Sho (Development)", "percentage": 0.25, "purpose": "Develop situation"},
            {"number": 3, "title": "Ten (Twist)", "percentage": 0.25, "purpose": "Introduce unexpected element"},
            {"number": 4, "title": "Ketsu (Conclusion)", "percentage": 0.25, "purpose": "Resolve with new understanding"}
        ],
        "typical_beats": ["introduction", "development", "twist", "conclusion"]
    },
    StoryStructureType.HERO_JOURNEY: {
        "acts": [
            {"number": 1, "title": "Departure", "percentage": 0.30, "purpose": "Call to adventure and departure"},
            {"number": 2, "title": "Initiation", "percentage": 0.40, "purpose": "Trials and transformation"},
            {"number": 3, "title": "Return", "percentage": 0.30, "purpose": "Return with wisdom"}
        ],
        "typical_beats": ["call", "refusal", "mentor", "threshold", "tests", "ordeal", "reward", "road_back", "resurrection", "elixir"]
    }
}

# Genre-specific pacing patterns
GENRE_PACING_PATTERNS = {
    "action": {"fast": 0.4, "very_fast": 0.3, "medium": 0.2, "slow": 0.1},
    "romance": {"slow": 0.4, "medium": 0.4, "fast": 0.2, "very_fast": 0.0},
    "mystery": {"medium": 0.5, "slow": 0.3, "fast": 0.2, "very_fast": 0.0},
    "fantasy": {"medium": 0.4, "fast": 0.3, "slow": 0.2, "very_fast": 0.1},
    "slice_of_life": {"slow": 0.6, "medium": 0.3, "fast": 0.1, "very_fast": 0.0},
    "horror": {"slow": 0.3, "medium": 0.3, "fast": 0.2, "very_fast": 0.2},
    "sci_fi": {"medium": 0.4, "fast": 0.3, "slow": 0.2, "very_fast": 0.1}
}