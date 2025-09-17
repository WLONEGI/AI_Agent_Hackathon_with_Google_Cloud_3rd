"""AI Models and Google Cloud configuration settings."""

from typing import Dict, List, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field, field_validator


class AIModelSettings(BaseSettings):
    """AI models and Google Cloud configuration."""
    
    # Google Cloud Configuration
    google_cloud_project: str = Field("local-dev-0001", env="GOOGLE_CLOUD_PROJECT")
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    vertexai_location: str = Field("asia-northeast1", env="VERTEXAI_LOCATION")
    
    # Text Generation Models (Gemini)
    gemini_model: str = Field("gemini-1.5-pro", env="GEMINI_MODEL")
    gemini_temperature: float = Field(0.7, env="GEMINI_TEMPERATURE")
    gemini_top_p: float = Field(0.8, env="GEMINI_TOP_P")
    gemini_top_k: int = Field(40, env="GEMINI_TOP_K")
    gemini_max_tokens: int = Field(8192, env="GEMINI_MAX_TOKENS")
    gemini_safety_threshold: str = Field("BLOCK_MEDIUM_AND_ABOVE", env="GEMINI_SAFETY_THRESHOLD")
    
    # Image Generation Models (Imagen)
    imagen_model: str = Field("imagen-4", env="IMAGEN_MODEL")
    imagen_quality: str = Field("high", env="IMAGEN_QUALITY")
    imagen_aspect_ratio: str = Field("1:1", env="IMAGEN_ASPECT_RATIO")
    imagen_style: str = Field("manga", env="IMAGEN_STYLE")
    imagen_negative_prompt: str = Field("blurry, low quality, distorted", env="IMAGEN_NEGATIVE_PROMPT")
    
    # Performance Configuration
    max_parallel_requests: int = Field(10, env="AI_MAX_PARALLEL_REQUESTS")
    max_parallel_image_generation: int = Field(5, env="MAX_PARALLEL_IMAGE_GENERATION")
    request_timeout: int = Field(120, env="AI_API_TIMEOUT")
    retry_attempts: int = Field(3, env="AI_RETRY_ATTEMPTS")
    retry_delay: float = Field(1.0, env="AI_RETRY_DELAY")
    
    # Rate Limiting
    requests_per_minute: int = Field(60, env="AI_REQUESTS_PER_MINUTE")
    tokens_per_minute: int = Field(100000, env="AI_TOKENS_PER_MINUTE")
    images_per_minute: int = Field(10, env="AI_IMAGES_PER_MINUTE")
    
    # Cost Management
    enable_cost_tracking: bool = Field(True, env="ENABLE_AI_COST_TRACKING")
    daily_cost_limit: float = Field(100.0, env="AI_DAILY_COST_LIMIT")  # USD
    cost_alert_threshold: float = Field(0.8, env="AI_COST_ALERT_THRESHOLD")  # 80% of limit
    
    # Model Fallback Configuration
    enable_fallback_models: bool = Field(True, env="ENABLE_AI_FALLBACK_MODELS")
    fallback_gemini_model: str = Field("gemini-1.0-pro", env="FALLBACK_GEMINI_MODEL")
    fallback_imagen_model: str = Field("imagen-3", env="FALLBACK_IMAGEN_MODEL")
    
    # Content Safety Configuration
    enable_content_filtering: bool = Field(True, env="ENABLE_CONTENT_FILTERING")
    content_safety_threshold: str = Field("medium", env="CONTENT_SAFETY_THRESHOLD")
    block_adult_content: bool = Field(True, env="BLOCK_ADULT_CONTENT")
    block_violent_content: bool = Field(False, env="BLOCK_VIOLENT_CONTENT")  # Manga may have action
    
    # Phase-specific model configuration
    phase_model_config: Dict[int, Dict[str, str]] = Field(
        default={
            1: {"model": "gemini-1.5-pro", "temperature": "0.3"},  # Concept analysis - low temp for consistency
            2: {"model": "gemini-1.5-pro", "temperature": "0.7"},  # Character design - medium temp for creativity
            3: {"model": "gemini-1.5-pro", "temperature": "0.5"},  # Plot structure - balanced temp
            4: {"model": "gemini-1.5-pro", "temperature": "0.2"},  # Name generation - low temp for precision
            5: {"model": "imagen-4", "quality": "high"},          # Image generation
            6: {"model": "gemini-1.5-pro", "temperature": "0.4"},  # Dialogue - slightly creative
            7: {"model": "gemini-1.5-pro", "temperature": "0.1"}   # Integration - very consistent
        }
    )
    
    # Prompt templates configuration
    enable_prompt_caching: bool = Field(True, env="ENABLE_PROMPT_CACHING")
    prompt_cache_ttl: int = Field(3600, env="PROMPT_CACHE_TTL")  # 1 hour
    use_system_prompts: bool = Field(True, env="USE_SYSTEM_PROMPTS")
    
    @field_validator("google_cloud_project")
    def validate_project_id(cls, v):
        """Validate Google Cloud project ID format."""
        if not v:
            raise ValueError("Google Cloud project ID is required")
        
        # Basic project ID format validation
        import re
        if not re.match(r'^[a-z][a-z0-9\-]{4,28}[a-z0-9]$', v):
            raise ValueError("Invalid Google Cloud project ID format")
        
        return v
    
    @field_validator("vertexai_location")
    def validate_location(cls, v):
        """Validate Vertex AI location."""
        valid_locations = [
            "us-central1", "us-east1", "us-west1", "us-west4",
            "europe-west1", "europe-west2", "europe-west4",
            "asia-east1", "asia-northeast1", "asia-southeast1"
        ]
        
        if v not in valid_locations:
            raise ValueError(f"Location must be one of {valid_locations}")
        
        return v
    
    @field_validator("gemini_temperature")
    def validate_temperature(cls, v):
        """Validate temperature parameter."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    @field_validator("gemini_top_p")
    def validate_top_p(cls, v):
        """Validate top_p parameter."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Top-p must be between 0.0 and 1.0")
        return v
    
    @field_validator("imagen_quality")
    def validate_imagen_quality(cls, v):
        """Validate Imagen quality setting."""
        valid_qualities = ["draft", "standard", "high", "ultra_high"]
        if v not in valid_qualities:
            raise ValueError(f"Imagen quality must be one of {valid_qualities}")
        return v
    
    @field_validator("imagen_aspect_ratio")
    def validate_aspect_ratio(cls, v):
        """Validate image aspect ratio."""
        valid_ratios = ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3"]
        if v not in valid_ratios:
            raise ValueError(f"Aspect ratio must be one of {valid_ratios}")
        return v
    
    @field_validator("content_safety_threshold")
    def validate_safety_threshold(cls, v):
        """Validate content safety threshold."""
        valid_thresholds = ["low", "medium", "high", "very_high"]
        if v not in valid_thresholds:
            raise ValueError(f"Content safety threshold must be one of {valid_thresholds}")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def get_gemini_config(self, phase_number: Optional[int] = None) -> dict:
        """Get Gemini model configuration for specific phase."""
        
        # Get base configuration (safety_threshold removed for Gemini 2.5 Pro compatibility)
        config = {
            "model": self.gemini_model,
            "temperature": self.gemini_temperature,
            "top_p": self.gemini_top_p,
            "top_k": self.gemini_top_k,
            "max_tokens": self.gemini_max_tokens
        }
        
        # Override with phase-specific configuration
        if phase_number and phase_number in self.phase_model_config:
            phase_config = self.phase_model_config[phase_number]
            config.update(phase_config)
        
        return config
    
    def get_imagen_config(self, phase_number: Optional[int] = None) -> dict:
        """Get Imagen model configuration."""
        
        config = {
            "model": self.imagen_model,
            "quality": self.imagen_quality,
            "aspect_ratio": self.imagen_aspect_ratio,
            "style": self.imagen_style,
            "negative_prompt": self.imagen_negative_prompt
        }
        
        # Override with phase-specific configuration
        if phase_number and phase_number in self.phase_model_config:
            phase_config = self.phase_model_config[phase_number]
            config.update(phase_config)
        
        return config
    
    def get_rate_limit_config(self) -> dict:
        """Get rate limiting configuration."""
        return {
            "requests_per_minute": self.requests_per_minute,
            "tokens_per_minute": self.tokens_per_minute,
            "images_per_minute": self.images_per_minute,
            "max_parallel_requests": self.max_parallel_requests,
            "max_parallel_images": self.max_parallel_image_generation
        }
    
    def get_cost_management_config(self) -> dict:
        """Get cost management configuration."""
        return {
            "tracking_enabled": self.enable_cost_tracking,
            "daily_limit": self.daily_cost_limit,
            "alert_threshold": self.cost_alert_threshold,
            "alert_at_amount": self.daily_cost_limit * self.cost_alert_threshold
        }
    
    def get_content_safety_config(self) -> dict:
        """Get content safety configuration."""
        return {
            "enabled": self.enable_content_filtering,
            "threshold": self.content_safety_threshold,
            "block_adult": self.block_adult_content,
            "block_violent": self.block_violent_content
        }
    
    def get_fallback_config(self) -> dict:
        """Get fallback model configuration."""
        return {
            "enabled": self.enable_fallback_models,
            "gemini_fallback": self.fallback_gemini_model,
            "imagen_fallback": self.fallback_imagen_model
        }
    
    def get_vertex_ai_config(self) -> dict:
        """Get Vertex AI client configuration."""
        config = {
            "project": self.google_cloud_project,
            "location": self.vertexai_location
        }
        
        if self.google_application_credentials:
            config["credentials_path"] = self.google_application_credentials
        
        return config
    
    def estimate_text_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for text generation (rough estimate)."""
        # Gemini Pro pricing (approximate)
        input_cost_per_1k = 0.00125  # USD per 1K tokens
        output_cost_per_1k = 0.00375  # USD per 1K tokens
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
    
    def estimate_image_cost(self, num_images: int) -> float:
        """Estimate cost for image generation (rough estimate)."""
        # Imagen pricing (approximate)
        cost_per_image = 0.04  # USD per image for high quality
        
        return num_images * cost_per_image