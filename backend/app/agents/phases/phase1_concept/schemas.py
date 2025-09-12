"""Schemas for Phase 1: Concept Analysis."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class GenreType(str, Enum):
    """Manga genre types."""
    FANTASY = "fantasy"
    ROMANCE = "romance"  
    ACTION = "action"
    MYSTERY = "mystery"
    SLICE_OF_LIFE = "slice_of_life"
    SCI_FI = "sci_fi"
    HORROR = "horror"
    GENERAL = "general"


class ToneType(str, Enum):
    """Story tone types."""
    LIGHT = "light"
    DARK = "dark" 
    NEUTRAL = "neutral"
    COMEDIC = "comedic"
    SERIOUS = "serious"
    DRAMATIC = "dramatic"


class NarrativeStyle(str, Enum):
    """Narrative style types."""
    FIRST_PERSON = "first_person"
    THIRD_PERSON = "third_person"
    OMNISCIENT = "omniscient"


class TargetAudience(str, Enum):
    """Target audience types."""
    CHILDREN = "children"
    TEENS = "teens"
    YOUNG_ADULTS = "young_adults"
    ADULTS = "adults"
    GENERAL = "general"


class WorldSettings(BaseModel):
    """World setting information."""
    time_period: str = Field(
        default="modern",
        description="Time period (ancient, medieval, modern, future, etc.)"
    )
    location: str = Field(
        default="unknown",
        description="Primary location/setting"
    )
    technology_level: str = Field(
        default="modern",
        description="Technology level in the world"
    )
    magic_system: Optional[str] = Field(
        default=None,
        description="Magic system if applicable"
    )
    special_rules: List[str] = Field(
        default_factory=list,
        description="Special rules or laws in this world"
    )
    cultural_elements: List[str] = Field(
        default_factory=list,
        description="Cultural elements and social norms"
    )


class GenreAnalysis(BaseModel):
    """Genre analysis results."""
    primary_genre: GenreType = Field(
        description="Primary identified genre"
    )
    secondary_genres: List[GenreType] = Field(
        default_factory=list,
        description="Secondary genre elements"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in genre classification"
    )
    genre_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that contributed to genre classification"
    )


class ThemeAnalysis(BaseModel):
    """Theme analysis results."""
    main_themes: List[str] = Field(
        default_factory=list,
        description="Main themes identified in the story"
    )
    sub_themes: List[str] = Field(
        default_factory=list,
        description="Secondary themes"
    )
    moral_lessons: List[str] = Field(
        default_factory=list,
        description="Moral lessons or messages"
    )
    conflict_types: List[str] = Field(
        default_factory=list,
        description="Types of conflicts (internal, external, etc.)"
    )


class ConceptOutput(BaseModel):
    """Complete output for Phase 1: Concept Analysis."""
    
    # Basic analysis
    original_text: str = Field(
        description="Original input text (truncated to 1000 chars)"
    )
    text_length: int = Field(
        description="Length of original text"
    )
    
    # Genre and themes
    genre_analysis: GenreAnalysis = Field(
        description="Genre analysis results"
    )
    theme_analysis: ThemeAnalysis = Field(
        description="Theme analysis results"
    )
    
    # Story characteristics
    tone: ToneType = Field(
        description="Overall tone of the story"
    )
    narrative_style: NarrativeStyle = Field(
        description="Narrative perspective"
    )
    target_audience: TargetAudience = Field(
        description="Target audience"
    )
    
    # World building
    world_setting: WorldSettings = Field(
        description="World and setting information"
    )
    
    # Key elements
    key_characters: List[str] = Field(
        default_factory=list,
        description="Key characters mentioned or implied"
    )
    key_events: List[str] = Field(
        default_factory=list,
        description="Key events or plot points"
    )
    key_objects: List[str] = Field(
        default_factory=list,
        description="Important objects or items"
    )
    
    # Metadata
    estimated_pages: int = Field(
        ge=1,
        description="Estimated number of manga pages needed"
    )
    complexity_score: float = Field(
        ge=0.0, le=1.0,
        description="Story complexity score (0 = simple, 1 = very complex)"
    )
    visual_richness: float = Field(
        ge=0.0, le=1.0,
        description="Expected visual richness (0 = text-heavy, 1 = action-heavy)"
    )
    
    # Analysis metadata
    analysis_timestamp: str = Field(
        description="Timestamp of analysis"
    )
    ai_model_used: Optional[str] = Field(
        default=None,
        description="AI model used for analysis"
    )


class ConceptInput(BaseModel):
    """Input for Phase 1: Concept Analysis."""
    text: str = Field(
        min_length=10,
        max_length=50000,
        description="Input story text to analyze"
    )
    user_preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional user preferences for analysis"
    )