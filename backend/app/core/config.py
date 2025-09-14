"""Configuration management for the AI Manga Generation Service."""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    env: str = Field("development", env="ENV")  # Keep for backward compatibility
    debug: bool = Field(True, env="DEBUG")
    
    # Mock Settings (for local development)
    mock_enabled: bool = Field(False, env="MOCK_ENABLED")
    mock_database: bool = Field(True, env="MOCK_DATABASE")
    mock_redis: bool = Field(True, env="MOCK_REDIS")
    mock_google_auth: bool = Field(True, env="MOCK_GOOGLE_AUTH")
    mock_ai_services: bool = Field(False, env="MOCK_AI_SERVICES")
    
    # Application
    app_name: str = "AI Manga Generation Service"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(10, env="DATABASE_MAX_OVERFLOW")
    database_echo: bool = Field(False, env="DATABASE_ECHO")
    
    # Redis
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    redis_max_connections: int = Field(20, env="REDIS_MAX_CONNECTIONS")
    
    # Google Cloud & AI
    google_cloud_project: str = Field(..., env="GOOGLE_CLOUD_PROJECT")
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    vertexai_location: str = Field("asia-northeast1", env="VERTEXAI_LOCATION")
    
    # Firebase Authentication
    firebase_project_id: str = Field(..., env="FIREBASE_PROJECT_ID")
    firebase_credentials_path: Optional[str] = Field(None, env="FIREBASE_CREDENTIALS_PATH")
    firebase_credentials_json: Optional[str] = Field(None, env="FIREBASE_CREDENTIALS_JSON")
    
    # AI Models
    gemini_model: str = Field("gemini-2.5-pro", env="GEMINI_MODEL")
    imagen_model: str = Field("imagen-4.0-ultra-generate-001", env="IMAGEN_MODEL")
    max_parallel_image_generation: int = Field(5, env="MAX_PARALLEL_IMAGE_GENERATION")
    ai_api_timeout: int = Field(120, env="AI_API_TIMEOUT")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    bcrypt_rounds: int = Field(12, env="BCRYPT_ROUNDS")
    
    @field_validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        
        # Detect insecure patterns
        insecure_patterns = [
            "dev-", "test-", "default", "secret", "password", "key", 
            "CHANGE", "GENERATE", "PRODUCTION", "123", "abc"
        ]
        if any(pattern.upper() in v.upper() for pattern in insecure_patterns):
            raise ValueError(f"Secret key contains insecure patterns. Use cryptographically secure random key.")
        
        # Ensure sufficient entropy
        unique_chars = len(set(v.lower()))
        if unique_chars < 16:
            raise ValueError("Secret key has insufficient entropy. Use random generator.")
        
        return v
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env.lower() in ("development", "dev", "local")
    
    def get_phase_config(self, phase_num: int) -> dict:
        """Get phase-specific configuration."""
        return {
            "timeout_seconds": self.phase_timeouts.get(phase_num, 30),
            "quality_threshold": 0.7,
            "max_retries": 3,
            "parallel_enabled": phase_num in [2, 3, 5]  # Parallelizable phases
        }
    
    # Rate Limiting
    rate_limit_per_ip: int = Field(100, env="RATE_LIMIT_PER_IP")
    rate_limit_window_seconds: int = Field(60, env="RATE_LIMIT_WINDOW_SECONDS")
    
    # WebSocket
    ws_heartbeat_interval: int = Field(30, env="WS_HEARTBEAT_INTERVAL")
    ws_connection_timeout: int = Field(300, env="WS_CONNECTION_TIMEOUT")
    
    # Cache
    cache_l1_max_size: int = Field(1000, env="CACHE_L1_MAX_SIZE")
    cache_l1_ttl_seconds: int = Field(300, env="CACHE_L1_TTL_SECONDS")
    cache_l2_ttl_seconds: int = Field(3600, env="CACHE_L2_TTL_SECONDS")
    cache_l3_ttl_seconds: int = Field(86400, env="CACHE_L3_TTL_SECONDS")
    
    # CDN
    cdn_url: str = Field("https://cdn.manga-service.com", env="CDN_URL")
    cdn_cache_control_max_age: int = Field(86400, env="CDN_CACHE_CONTROL_MAX_AGE")
    
    # CORS
    cors_origins: List[str] = Field(
        ["http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(
        ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: List[str] = Field([
        "Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"
    ], env="CORS_ALLOW_HEADERS")
    
    # Monitoring
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    
    # Phase Processing Times (seconds)
    phase_timeouts: dict = {
        1: 12,  # コンセプト・世界観分析
        2: 18,  # キャラクター設定・簡易ビジュアル生成
        3: 15,  # プロット・ストーリー構成
        4: 20,  # ネーム生成
        5: 25,  # シーン画像生成
        6: 4,   # セリフ配置
        7: 3    # 最終統合・品質調整
    }
    
    # Quality Levels
    quality_levels: List[str] = ["ultra_high", "high", "medium", "low", "preview"]
    default_quality: str = "high"
    
    @field_validator("cors_origins", mode='before')
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("database_url")
    def validate_database_url(cls, v):
        if not v.startswith("postgresql"):
            raise ValueError("Database URL must be a PostgreSQL URL")
        return v
    
    @field_validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export commonly used settings
settings = get_settings()