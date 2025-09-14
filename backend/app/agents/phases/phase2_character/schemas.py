"""Schemas for Phase 2: Character Design."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class CharacterArchetypeType(str, Enum):
    """Character archetype types."""
    PROTAGONIST = "protagonist"
    SIDEKICK = "sidekick"
    MENTOR = "mentor"
    ANTAGONIST = "antagonist"
    LOVE_INTEREST = "love_interest"
    SUPPORTING = "supporting"


class GenderType(str, Enum):
    """Gender types for characters."""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    UNKNOWN = "unknown"


class AgeGroupType(str, Enum):
    """Age group classifications."""
    CHILD = "child"          # 0-12
    TEENAGER = "teenager"    # 13-17
    YOUNG_ADULT = "young_adult"  # 18-25
    ADULT = "adult"          # 26-40
    MIDDLE_AGED = "middle_aged"  # 41-60
    ELDERLY = "elderly"      # 60+


class VisualStyleType(str, Enum):
    """Manga visual style types."""
    SHOUNEN = "shounen"
    SHOUJO = "shoujo"
    SEINEN = "seinen"
    KODOMO = "kodomo"
    JOSEI = "josei"


class HeightType(str, Enum):
    """Height classifications."""
    VERY_SHORT = "very_short"
    SHORT = "short"
    AVERAGE = "average"
    TALL = "tall"
    VERY_TALL = "very_tall"


class BuildType(str, Enum):
    """Physical build types."""
    SLIM = "slim"
    AVERAGE = "average"
    ATHLETIC = "athletic"
    MUSCULAR = "muscular"
    HEAVY = "heavy"


class HairColorType(str, Enum):
    """Hair color options."""
    BLACK = "black"
    BROWN = "brown"
    BLONDE = "blonde"
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    PINK = "pink"
    WHITE = "white"
    SILVER = "silver"


class EyeColorType(str, Enum):
    """Eye color options."""
    BLACK = "black"
    BROWN = "brown"
    BLUE = "blue"
    GREEN = "green"
    GRAY = "gray"
    HAZEL = "hazel"
    AMBER = "amber"
    VIOLET = "violet"
    RED = "red"
    GOLD = "gold"


class PersonalityTrait(BaseModel):
    """Individual personality trait."""
    trait: str = Field(description="Personality trait name")
    strength: float = Field(ge=0.0, le=1.0, description="Trait strength (0.0-1.0)")
    description: str = Field(description="Detailed trait description")


class CharacterAppearance(BaseModel):
    """Character visual appearance details."""
    hair_color: HairColorType = Field(description="Hair color")
    hair_style: str = Field(description="Hair style description")
    eye_color: EyeColorType = Field(description="Eye color")
    height: HeightType = Field(description="Height classification")
    build: BuildType = Field(description="Physical build")
    distinctive_features: List[str] = Field(default=[], description="Unique visual features")
    clothing_style: str = Field(description="Default clothing style")
    default_expression: str = Field(description="Typical facial expression")
    age_appearance: str = Field(description="Visual age appearance")


class CharacterPersonality(BaseModel):
    """Character personality profile."""
    main_traits: List[PersonalityTrait] = Field(description="Primary personality traits")
    motivation: str = Field(description="Character's main motivation")
    fears: List[str] = Field(default=[], description="Character's fears")
    strengths: List[str] = Field(default=[], description="Character strengths")
    weaknesses: List[str] = Field(default=[], description="Character weaknesses")
    speech_pattern: str = Field(description="How the character speaks")
    background_summary: str = Field(description="Brief background story")


class CharacterRelationship(BaseModel):
    """Relationship between characters."""
    character1_name: str = Field(description="First character name")
    character2_name: str = Field(description="Second character name")
    relationship_type: str = Field(description="Type of relationship")
    relationship_strength: float = Field(ge=0.0, le=1.0, description="Relationship strength")
    description: str = Field(description="Relationship description")


class CharacterProfile(BaseModel):
    """Complete character profile."""
    name: str = Field(description="Character name")
    archetype: CharacterArchetypeType = Field(description="Character archetype")
    gender: GenderType = Field(description="Character gender")
    age_group: AgeGroupType = Field(description="Age group classification")
    age_specific: Optional[int] = Field(None, ge=0, le=150, description="Specific age if known")

    appearance: CharacterAppearance = Field(description="Visual appearance")
    personality: CharacterPersonality = Field(description="Personality profile")

    role_importance: float = Field(ge=0.0, le=1.0, description="Importance in story (0.0-1.0)")
    screen_time_estimate: float = Field(ge=0.0, le=1.0, description="Estimated screen time ratio")

    # Visual generation metadata
    visual_style_preference: VisualStyleType = Field(description="Preferred visual style")
    design_complexity: float = Field(ge=0.0, le=1.0, description="Design complexity level")


class StyleGuide(BaseModel):
    """Visual style guide for character consistency."""
    overall_style: VisualStyleType = Field(description="Overall visual style")
    color_palette: Dict[str, str] = Field(description="Color palette for the character set")
    design_principles: List[str] = Field(description="Key design principles")
    consistency_notes: List[str] = Field(description="Notes for maintaining visual consistency")
    reference_notes: List[str] = Field(default=[], description="Reference materials or inspirations")


class CharacterDesignInput(BaseModel):
    """Input for Phase 2 character design."""
    # From Phase 1
    genre_analysis: Dict[str, Any] = Field(description="Genre analysis from Phase 1")
    themes: List[str] = Field(description="Story themes from Phase 1")
    target_audience: str = Field(description="Target audience")
    tone: str = Field(description="Story tone")
    world_setting: Dict[str, Any] = Field(description="World setting information")

    # Phase 2 specific inputs
    character_count_preference: Optional[int] = Field(None, ge=1, le=20, description="Preferred character count")
    visual_style_preference: Optional[VisualStyleType] = Field(None, description="Preferred visual style")
    complexity_level: Optional[float] = Field(None, ge=0.0, le=1.0, description="Design complexity preference")


class CharacterDesignOutput(BaseModel):
    """Output for Phase 2 character design."""
    characters: List[CharacterProfile] = Field(description="List of designed characters")
    relationships: List[CharacterRelationship] = Field(description="Character relationships")
    style_guide: StyleGuide = Field(description="Visual style guide")

    # Design metadata
    total_characters: int = Field(description="Total number of characters")
    main_characters_count: int = Field(description="Number of main characters")
    design_complexity_score: float = Field(ge=0.0, le=1.0, description="Overall design complexity")
    visual_consistency_score: float = Field(ge=0.0, le=1.0, description="Visual consistency score")

    # Next phase interface
    character_summaries: List[Dict[str, str]] = Field(description="Brief character summaries for next phases")
    visual_references: List[Dict[str, Any]] = Field(description="Visual reference data for image generation")

    # Generation metadata
    generation_timestamp: str = Field(description="ISO timestamp of generation")
    ai_model_used: str = Field(description="AI model used for generation")
    processing_time: float = Field(description="Processing time in seconds")


# Archetype definitions for reference
CHARACTER_ARCHETYPES = {
    CharacterArchetypeType.PROTAGONIST: {
        "keywords": ["主人公", "ヒーロー", "リーダー", "中心人物"],
        "typical_traits": ["勇敢", "決断力", "責任感", "成長意欲"],
        "role": "主人公として物語を牽引する"
    },
    CharacterArchetypeType.SIDEKICK: {
        "keywords": ["相棒", "親友", "サポーター", "助手"],
        "typical_traits": ["忠実", "サポート力", "ユーモア", "専門知識"],
        "role": "主人公を支援し、時に異なる視点を提供する"
    },
    CharacterArchetypeType.MENTOR: {
        "keywords": ["師匠", "先生", "ガイド", "賢者"],
        "typical_traits": ["知恵", "経験", "指導力", "忍耐"],
        "role": "主人公を導き、重要な知識や技能を伝える"
    },
    CharacterArchetypeType.ANTAGONIST: {
        "keywords": ["敵", "ライバル", "対立者", "障害"],
        "typical_traits": ["野心", "対立的", "強い意志", "複雑さ"],
        "role": "主人公の目標を阻害し、成長の機会を提供する"
    },
    CharacterArchetypeType.LOVE_INTEREST: {
        "keywords": ["恋人", "想い人", "パートナー", "愛する人"],
        "typical_traits": ["魅力", "感情的深さ", "独立性", "相互理解"],
        "role": "主人公の感情的成長を促進する"
    }
}

# Visual style definitions
VISUAL_STYLES = {
    VisualStyleType.SHOUNEN: {
        "eye_style": "large_dynamic",
        "proportions": "dynamic_heroic",
        "detail_level": "medium",
        "color_intensity": "high",
        "typical_features": ["アクションライン", "動的ポーズ", "明確な表情"]
    },
    VisualStyleType.SHOUJO: {
        "eye_style": "sparkly_large",
        "proportions": "elegant_graceful",
        "detail_level": "high",
        "color_intensity": "soft_high",
        "typical_features": ["花の装飾", "繊細な線", "感情的な表現"]
    },
    VisualStyleType.SEINEN: {
        "eye_style": "realistic_detailed",
        "proportions": "natural_realistic",
        "detail_level": "very_high",
        "color_intensity": "natural",
        "typical_features": ["写実的な陰影", "複雑な背景", "大人らしい表現"]
    },
    VisualStyleType.KODOMO: {
        "eye_style": "simple_round",
        "proportions": "chibi_cute",
        "detail_level": "low",
        "color_intensity": "bright",
        "typical_features": ["丸いフォルム", "シンプルな線", "可愛らしい表現"]
    },
    VisualStyleType.JOSEI: {
        "eye_style": "mature_expressive",
        "proportions": "realistic_elegant",
        "detail_level": "high",
        "color_intensity": "sophisticated",
        "typical_features": ["大人の魅力", "洗練された線", "情緒的な表現"]
    }
}