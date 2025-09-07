"""Main application settings."""

from typing import List, Optional
from pydantic import Field, field_validator
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from functools import lru_cache

from .database import DatabaseSettings
from .cache import CacheSettings
from .ai_models import AIModelSettings
from .security import SecuritySettings
from .monitoring import MonitoringSettings
from .firebase import FirebaseSettings


class Settings(BaseSettings):
    """Main application settings that combines all configuration modules."""
    
    # Environment
    env: str = Field("development", env="ENV")
    debug: bool = Field(True, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Application
    app_name: str = "AI Manga Generation Service"
    app_version: str = "1.0.0" 
    api_prefix: str = "/api/v1"
    
    # Domain-specific settings
    database: DatabaseSettings = DatabaseSettings()
    cache: CacheSettings = CacheSettings()
    ai_models: AIModelSettings = AIModelSettings()
    security: SecuritySettings = SecuritySettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    firebase: FirebaseSettings = FirebaseSettings()
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(
        ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: List[str] = Field(["*"], env="CORS_ALLOW_HEADERS")
    
    # WebSocket Configuration
    ws_heartbeat_interval: int = Field(30, env="WS_HEARTBEAT_INTERVAL")
    ws_connection_timeout: int = Field(300, env="WS_CONNECTION_TIMEOUT")
    
    # Rate Limiting
    rate_limit_per_ip: int = Field(100, env="RATE_LIMIT_PER_IP")
    rate_limit_window_seconds: int = Field(60, env="RATE_LIMIT_WINDOW_SECONDS")
    
    # CDN Configuration
    cdn_url: str = Field("https://cdn.manga-service.com", env="CDN_URL")
    cdn_cache_control_max_age: int = Field(86400, env="CDN_CACHE_CONTROL_MAX_AGE")
    
    # Phase Processing Configuration
    phase_timeouts: dict = Field(
        default={
            1: 12,  # コンセプト・世界観分析
            2: 18,  # キャラクター設定・簡易ビジュアル生成
            3: 15,  # プロット・ストーリー構成
            4: 20,  # ネーム生成（最重要）
            5: 25,  # シーン画像生成（並列処理）
            6: 4,   # セリフ配置
            7: 3    # 最終統合・品質調整
        }
    )
    
    # Quality Configuration
    quality_levels: List[str] = Field(
        default=["ultra_high", "high", "medium", "low", "preview"]
    )
    default_quality: str = Field(default="high")
    
    @field_validator("cors_origins", mode='before')
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("phase_timeouts", mode='before')
    def validate_phase_timeouts(cls, v):
        """Validate phase timeouts configuration."""
        if isinstance(v, str):
            import json
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format for phase_timeouts")
        
        if not isinstance(v, dict):
            raise ValueError("phase_timeouts must be a dictionary")
        
        # Validate all phases 1-7 are present
        required_phases = set(range(1, 8))
        provided_phases = set(int(k) for k in v.keys())
        
        if not required_phases.issubset(provided_phases):
            missing = required_phases - provided_phases
            raise ValueError(f"Missing phase timeout configuration for phases: {missing}")
        
        # Validate timeout values are positive
        for phase, timeout in v.items():
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise ValueError(f"Phase {phase} timeout must be a positive number")
        
        return v
    
    @field_validator("quality_levels")
    def validate_quality_levels(cls, v):
        """Validate quality levels configuration."""
        if not v:
            raise ValueError("At least one quality level must be defined")
        
        valid_levels = {"ultra_high", "high", "medium", "low", "preview"}
        for level in v:
            if level not in valid_levels:
                raise ValueError(f"Invalid quality level: {level}. Must be one of {valid_levels}")
        
        return v
    
    @field_validator("default_quality")
    def validate_default_quality(cls, v, values):
        """Validate default quality is in quality levels."""
        if hasattr(values, 'quality_levels') and v not in values.quality_levels:
            raise ValueError(f"Default quality '{v}' must be in quality_levels")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    @property
    def total_pipeline_time(self) -> int:
        """Calculate total pipeline processing time."""
        return sum(self.phase_timeouts.values())
    
    @property
    def critical_phases(self) -> List[int]:
        """Get list of critical phases (Phase 4 and 5)."""
        return [4, 5]  # Name generation and Image generation
    
    @property
    def parallel_phases(self) -> List[int]:
        """Get list of phases that support parallel processing."""
        return [5]  # Image generation phase
    
    def get_phase_config(self, phase_number: int) -> dict:
        """Get configuration for specific phase.
        
        Args:
            phase_number: Phase number (1-7)
            
        Returns:
            Configuration dictionary for the phase
        """
        phase_names = {
            1: "concept_analysis",
            2: "character_design", 
            3: "plot_structure",
            4: "name_generation",
            5: "image_generation",
            6: "dialogue_placement",
            7: "final_integration"
        }
        
        return {
            "phase_number": phase_number,
            "phase_name": phase_names.get(phase_number, f"phase_{phase_number}"),
            "timeout": self.phase_timeouts.get(phase_number, 60),
            "is_critical": phase_number in self.critical_phases,
            "supports_parallel": phase_number in self.parallel_phases
        }
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env.lower() in ["development", "dev", "local"]
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env.lower() in ["production", "prod"]
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.env.lower() in ["testing", "test"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()