"""Generation parameters value objects."""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class GenreType(str, Enum):
    """Manga genre types."""
    SHONEN = "shonen"  # 少年漫画
    SHOJO = "shojo"    # 少女漫画
    SEINEN = "seinen"  # 青年漫画
    JOSEI = "josei"    # 女性漫画
    KODOMOMUKE = "kodomomuke"  # 子供向け
    ACTION = "action"
    ROMANCE = "romance"
    COMEDY = "comedy"
    DRAMA = "drama"
    FANTASY = "fantasy"
    SCI_FI = "sci_fi"
    HORROR = "horror"
    MYSTERY = "mystery"
    SLICE_OF_LIFE = "slice_of_life"
    SPORTS = "sports"
    HISTORICAL = "historical"
    SUPERNATURAL = "supernatural"


class ArtStyle(str, Enum):
    """Art style preferences."""
    TRADITIONAL = "traditional"
    MODERN = "modern"
    REALISTIC = "realistic"
    STYLIZED = "stylized"
    CHIBI = "chibi"
    DETAILED = "detailed"
    MINIMALIST = "minimalist"
    EXPRESSIVE = "expressive"
    DYNAMIC = "dynamic"
    SOFT = "soft"
    BOLD = "bold"


class ToneType(str, Enum):
    """Story tone types."""
    LIGHT_HEARTED = "light_hearted"
    SERIOUS = "serious"
    HUMOROUS = "humorous"
    DRAMATIC = "dramatic"
    DARK = "dark"
    UPLIFTING = "uplifting"
    MELANCHOLIC = "melancholic"
    SUSPENSEFUL = "suspenseful"
    ROMANTIC = "romantic"
    ADVENTUROUS = "adventurous"
    MYSTERIOUS = "mysterious"
    INSPIRATIONAL = "inspirational"


class PanelLayout(str, Enum):
    """Panel layout preferences."""
    TRADITIONAL = "traditional"
    DYNAMIC = "dynamic"
    CINEMATIC = "cinematic"
    GRID_BASED = "grid_based"
    FLOWING = "flowing"
    EXPERIMENTAL = "experimental"
    MINIMALIST = "minimalist"
    DETAILED = "detailed"


class ContentRating(str, Enum):
    """Content rating levels."""
    ALL_AGES = "all_ages"
    TEEN = "teen"
    MATURE = "mature"
    ADULT = "adult"


@dataclass(frozen=True)
class GenerationParameters:
    """Generation parameters value object."""
    
    # Genre and Style
    primary_genre: GenreType = GenreType.SHONEN
    secondary_genres: List[GenreType] = None
    art_style: ArtStyle = ArtStyle.MODERN
    tone: ToneType = ToneType.LIGHT_HEARTED
    
    # Content Specifications
    target_audience: str = "一般"
    content_rating: ContentRating = ContentRating.ALL_AGES
    language: str = "ja"
    
    # Story Structure
    chapter_count: int = 1
    page_count_per_chapter: int = 20
    panel_layout: PanelLayout = PanelLayout.TRADITIONAL
    include_color_pages: bool = False
    
    # Character Settings
    max_main_characters: int = 5
    character_development_depth: str = "medium"  # "shallow", "medium", "deep"
    include_character_backstories: bool = True
    
    # Visual Preferences
    image_resolution: str = "1024x1024"
    art_detail_level: str = "medium"  # "low", "medium", "high"
    background_complexity: str = "medium"
    
    # AI Model Settings
    text_model_temperature: float = 0.7
    image_model_guidance: float = 7.5
    creativity_boost: bool = False
    quality_threshold: float = 0.6
    
    # Processing Options
    enable_hitl: bool = True
    auto_approve_threshold: float = 0.9
    max_revision_cycles: int = 3
    enable_content_filter: bool = True
    
    # Output Format
    output_format: str = "digital"  # "digital", "print", "web"
    export_formats: List[str] = None
    include_metadata: bool = True
    
    # Advanced Options
    custom_prompts: Dict[str, str] = None
    phase_weights: Dict[int, float] = None
    style_references: List[str] = None
    
    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.secondary_genres is None:
            object.__setattr__(self, 'secondary_genres', [])
        
        if self.export_formats is None:
            object.__setattr__(self, 'export_formats', ["png", "pdf"])
        
        if self.custom_prompts is None:
            object.__setattr__(self, 'custom_prompts', {})
        
        if self.phase_weights is None:
            object.__setattr__(self, 'phase_weights', {
                1: 1.0,  # Concept
                2: 1.2,  # Character (higher weight)
                3: 1.1,  # Plot
                4: 1.5,  # Name (highest weight)
                5: 1.3,  # Image
                6: 1.0,  # Dialogue
                7: 1.0   # Integration
            })
        
        if self.style_references is None:
            object.__setattr__(self, 'style_references', [])
        
        # Validate parameters
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate generation parameters."""
        if not 0.0 <= self.text_model_temperature <= 2.0:
            raise ValueError("Text model temperature must be between 0.0 and 2.0")
        
        if not 1.0 <= self.image_model_guidance <= 20.0:
            raise ValueError("Image model guidance must be between 1.0 and 20.0")
        
        if not 0.0 <= self.quality_threshold <= 1.0:
            raise ValueError("Quality threshold must be between 0.0 and 1.0")
        
        if not 0.0 <= self.auto_approve_threshold <= 1.0:
            raise ValueError("Auto approve threshold must be between 0.0 and 1.0")
        
        if self.chapter_count < 1:
            raise ValueError("Chapter count must be at least 1")
        
        if self.page_count_per_chapter < 1:
            raise ValueError("Page count per chapter must be at least 1")
        
        if self.max_main_characters < 1:
            raise ValueError("Max main characters must be at least 1")
        
        if self.max_revision_cycles < 0:
            raise ValueError("Max revision cycles cannot be negative")
    
    @classmethod
    def create_for_genre(cls, genre: GenreType) -> "GenerationParameters":
        """Create parameters optimized for specific genre."""
        genre_configs = {
            GenreType.SHONEN: {
                "art_style": ArtStyle.DYNAMIC,
                "tone": ToneType.ADVENTUROUS,
                "max_main_characters": 6,
                "text_model_temperature": 0.8,
                "creativity_boost": True
            },
            GenreType.SHOJO: {
                "art_style": ArtStyle.SOFT,
                "tone": ToneType.ROMANTIC,
                "max_main_characters": 4,
                "text_model_temperature": 0.6,
                "include_color_pages": True
            },
            GenreType.SEINEN: {
                "art_style": ArtStyle.REALISTIC,
                "tone": ToneType.SERIOUS,
                "content_rating": ContentRating.MATURE,
                "character_development_depth": "deep",
                "text_model_temperature": 0.5
            },
            GenreType.COMEDY: {
                "art_style": ArtStyle.EXPRESSIVE,
                "tone": ToneType.HUMOROUS,
                "text_model_temperature": 0.9,
                "creativity_boost": True,
                "panel_layout": PanelLayout.DYNAMIC
            },
            GenreType.HORROR: {
                "art_style": ArtStyle.DETAILED,
                "tone": ToneType.DARK,
                "content_rating": ContentRating.MATURE,
                "text_model_temperature": 0.7,
                "background_complexity": "high"
            }
        }
        
        config = genre_configs.get(genre, {})
        return cls(primary_genre=genre, **config)
    
    @classmethod
    def create_quick_start(cls, text_input: str) -> "GenerationParameters":
        """Create quick start parameters from text input."""
        # Simple keyword analysis for genre detection
        text_lower = text_input.lower()
        
        genre = GenreType.SHONEN  # default
        tone = ToneType.LIGHT_HEARTED  # default
        
        # Genre detection
        if any(word in text_lower for word in ["恋愛", "ロマンス", "恋"]):
            genre = GenreType.ROMANCE
            tone = ToneType.ROMANTIC
        elif any(word in text_lower for word in ["アクション", "戦闘", "戦い"]):
            genre = GenreType.ACTION
            tone = ToneType.ADVENTUROUS
        elif any(word in text_lower for word in ["コメディ", "笑い", "面白い"]):
            genre = GenreType.COMEDY
            tone = ToneType.HUMOROUS
        elif any(word in text_lower for word in ["ホラー", "怖い", "恐怖"]):
            genre = GenreType.HORROR
            tone = ToneType.DARK
        elif any(word in text_lower for word in ["ミステリー", "謎", "推理"]):
            genre = GenreType.MYSTERY
            tone = ToneType.MYSTERIOUS
        
        return cls.create_for_genre(genre).with_tone(tone)
    
    def with_genre(self, genre: GenreType) -> "GenerationParameters":
        """Create new instance with different genre."""
        return dataclass.replace(self, primary_genre=genre)
    
    def with_art_style(self, style: ArtStyle) -> "GenerationParameters":
        """Create new instance with different art style."""
        return dataclass.replace(self, art_style=style)
    
    def with_tone(self, tone: ToneType) -> "GenerationParameters":
        """Create new instance with different tone."""
        return dataclass.replace(self, tone=tone)
    
    def with_quality_threshold(self, threshold: float) -> "GenerationParameters":
        """Create new instance with different quality threshold."""
        return dataclass.replace(self, quality_threshold=threshold)
    
    def with_hitl_enabled(self, enabled: bool) -> "GenerationParameters":
        """Create new instance with HITL setting."""
        return dataclass.replace(self, enable_hitl=enabled)
    
    def with_creativity_boost(self, enabled: bool) -> "GenerationParameters":
        """Create new instance with creativity boost setting."""
        return dataclass.replace(self, creativity_boost=enabled)
    
    def add_secondary_genre(self, genre: GenreType) -> "GenerationParameters":
        """Add secondary genre."""
        new_genres = list(self.secondary_genres)
        if genre not in new_genres:
            new_genres.append(genre)
        return dataclass.replace(self, secondary_genres=new_genres)
    
    def set_custom_prompt(self, phase: str, prompt: str) -> "GenerationParameters":
        """Set custom prompt for specific phase."""
        new_prompts = dict(self.custom_prompts)
        new_prompts[phase] = prompt
        return dataclass.replace(self, custom_prompts=new_prompts)
    
    def set_phase_weight(self, phase_number: int, weight: float) -> "GenerationParameters":
        """Set weight for specific phase."""
        new_weights = dict(self.phase_weights)
        new_weights[phase_number] = weight
        return dataclass.replace(self, phase_weights=new_weights)
    
    def get_phase_weight(self, phase_number: int) -> float:
        """Get weight for specific phase."""
        return self.phase_weights.get(phase_number, 1.0)
    
    def get_custom_prompt(self, phase: str) -> Optional[str]:
        """Get custom prompt for specific phase."""
        return self.custom_prompts.get(phase)
    
    def is_adult_content(self) -> bool:
        """Check if parameters indicate adult content."""
        return self.content_rating in [ContentRating.MATURE, ContentRating.ADULT]
    
    def requires_color_processing(self) -> bool:
        """Check if color processing is required."""
        return self.include_color_pages or self.output_format == "print"
    
    def get_estimated_processing_time(self) -> float:
        """Estimate total processing time in seconds."""
        base_times = {
            1: 12.0,  # Concept
            2: 18.0,  # Character
            3: 15.0,  # Plot
            4: 20.0,  # Name
            5: 25.0,  # Image
            6: 4.0,   # Dialogue
            7: 3.0    # Integration
        }
        
        total_time = 0.0
        for phase, base_time in base_times.items():
            weight = self.get_phase_weight(phase)
            quality_factor = 1.0 + (self.quality_threshold - 0.6) * 0.5
            complexity_factor = 1.0
            
            if self.creativity_boost:
                complexity_factor += 0.2
            
            if self.art_detail_level == "high":
                complexity_factor += 0.3
            elif self.art_detail_level == "low":
                complexity_factor -= 0.2
            
            phase_time = base_time * weight * quality_factor * complexity_factor
            total_time += phase_time
        
        return total_time
    
    def to_dict(self) -> Dict[str, any]:
        """Convert parameters to dictionary."""
        return {
            "primary_genre": self.primary_genre.value,
            "secondary_genres": [g.value for g in self.secondary_genres],
            "art_style": self.art_style.value,
            "tone": self.tone.value,
            "target_audience": self.target_audience,
            "content_rating": self.content_rating.value,
            "language": self.language,
            "chapter_count": self.chapter_count,
            "page_count_per_chapter": self.page_count_per_chapter,
            "panel_layout": self.panel_layout.value,
            "include_color_pages": self.include_color_pages,
            "max_main_characters": self.max_main_characters,
            "character_development_depth": self.character_development_depth,
            "include_character_backstories": self.include_character_backstories,
            "image_resolution": self.image_resolution,
            "art_detail_level": self.art_detail_level,
            "background_complexity": self.background_complexity,
            "text_model_temperature": self.text_model_temperature,
            "image_model_guidance": self.image_model_guidance,
            "creativity_boost": self.creativity_boost,
            "quality_threshold": self.quality_threshold,
            "enable_hitl": self.enable_hitl,
            "auto_approve_threshold": self.auto_approve_threshold,
            "max_revision_cycles": self.max_revision_cycles,
            "enable_content_filter": self.enable_content_filter,
            "output_format": self.output_format,
            "export_formats": self.export_formats,
            "include_metadata": self.include_metadata,
            "custom_prompts": self.custom_prompts,
            "phase_weights": self.phase_weights,
            "style_references": self.style_references,
            "estimated_processing_time": self.get_estimated_processing_time()
        }