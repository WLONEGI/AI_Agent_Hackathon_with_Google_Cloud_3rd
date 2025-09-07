"""Cache configuration settings."""

from typing import Dict, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field, field_validator


class CacheSettings(BaseSettings):
    """Multi-layer cache configuration settings."""
    
    # Redis Configuration (L2 Cache)
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    redis_max_connections: int = Field(20, env="REDIS_MAX_CONNECTIONS")
    redis_retry_on_timeout: bool = Field(True, env="REDIS_RETRY_ON_TIMEOUT")
    redis_health_check_interval: int = Field(30, env="REDIS_HEALTH_CHECK_INTERVAL")
    redis_socket_connect_timeout: int = Field(5, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    redis_socket_keepalive: bool = Field(True, env="REDIS_SOCKET_KEEPALIVE")
    redis_socket_keepalive_options: Dict = Field(default_factory=dict)
    
    # L1 Cache (In-Memory) Configuration
    l1_max_size: int = Field(1000, env="CACHE_L1_MAX_SIZE")
    l1_ttl_seconds: int = Field(300, env="CACHE_L1_TTL_SECONDS")
    l1_cleanup_interval: int = Field(60, env="CACHE_L1_CLEANUP_INTERVAL")
    
    # L2 Cache (Redis) Configuration
    l2_default_ttl: int = Field(3600, env="CACHE_L2_TTL_SECONDS")
    l2_max_connections: int = Field(10, env="CACHE_L2_MAX_CONNECTIONS")
    
    # L3 Cache (Database) Configuration  
    l3_ttl_seconds: int = Field(86400, env="CACHE_L3_TTL_SECONDS")
    l3_cleanup_batch_size: int = Field(1000, env="CACHE_L3_CLEANUP_BATCH_SIZE")
    
    # Cache Strategy Configuration
    enable_l1_cache: bool = Field(True, env="ENABLE_L1_CACHE")
    enable_l2_cache: bool = Field(True, env="ENABLE_L2_CACHE")
    enable_l3_cache: bool = Field(True, env="ENABLE_L3_CACHE")
    
    # Cache warming configuration
    enable_cache_warming: bool = Field(True, env="ENABLE_CACHE_WARMING")
    cache_warm_on_startup: bool = Field(False, env="CACHE_WARM_ON_STARTUP")
    cache_warm_batch_size: int = Field(100, env="CACHE_WARM_BATCH_SIZE")
    
    # Content-specific TTL configuration
    content_ttl_config: Dict[str, int] = Field(
        default={
            "phase_result": 3600,     # 1 hour
            "image": 7200,            # 2 hours  
            "preview": 1800,          # 30 minutes
            "session": 300,           # 5 minutes
            "ai_response": 600,       # 10 minutes
            "user_preference": 86400, # 24 hours
            "static_content": 604800, # 1 week
            "user_session": 1800      # 30 minutes
        }
    )
    
    # Cache performance settings
    compression_enabled: bool = Field(True, env="CACHE_COMPRESSION_ENABLED")
    compression_threshold: int = Field(1024, env="CACHE_COMPRESSION_THRESHOLD")  # bytes
    serialization_format: str = Field("json", env="CACHE_SERIALIZATION_FORMAT")  # json, pickle, msgpack
    
    # Cache monitoring settings
    enable_cache_metrics: bool = Field(True, env="ENABLE_CACHE_METRICS")
    metrics_collection_interval: int = Field(60, env="CACHE_METRICS_INTERVAL")
    
    @field_validator("redis_url")
    def validate_redis_url(cls, v):
        """Validate Redis URL format."""
        if not v:
            raise ValueError("Redis URL is required")
        
        if not v.startswith("redis://") and not v.startswith("rediss://"):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        
        return v
    
    @field_validator("l1_max_size")
    def validate_l1_max_size(cls, v):
        """Validate L1 cache max size."""
        if v < 10:
            raise ValueError("L1 cache max size must be at least 10")
        if v > 10000:
            raise ValueError("L1 cache max size cannot exceed 10000")
        return v
    
    @field_validator("serialization_format")
    def validate_serialization_format(cls, v):
        """Validate serialization format."""
        valid_formats = ["json", "pickle", "msgpack"]
        if v not in valid_formats:
            raise ValueError(f"Serialization format must be one of {valid_formats}")
        return v
    
    @field_validator("content_ttl_config")
    def validate_content_ttl_config(cls, v):
        """Validate content TTL configuration."""
        if not isinstance(v, dict):
            raise ValueError("Content TTL config must be a dictionary")
        
        for content_type, ttl in v.items():
            if not isinstance(ttl, int) or ttl <= 0:
                raise ValueError(f"TTL for {content_type} must be a positive integer")
        
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def get_redis_config(self) -> dict:
        """Get Redis connection configuration."""
        config = {
            "url": self.redis_url,
            "max_connections": self.redis_max_connections,
            "retry_on_timeout": self.redis_retry_on_timeout,
            "health_check_interval": self.redis_health_check_interval,
            "socket_connect_timeout": self.redis_socket_connect_timeout,
            "socket_keepalive": self.redis_socket_keepalive,
        }
        
        if self.redis_socket_keepalive_options:
            config["socket_keepalive_options"] = self.redis_socket_keepalive_options
        
        return config
    
    def get_l1_config(self) -> dict:
        """Get L1 cache configuration."""
        return {
            "max_size": self.l1_max_size,
            "ttl": self.l1_ttl_seconds,
            "cleanup_interval": self.l1_cleanup_interval,
            "enabled": self.enable_l1_cache
        }
    
    def get_l2_config(self) -> dict:
        """Get L2 cache configuration."""
        return {
            "default_ttl": self.l2_default_ttl,
            "max_connections": self.l2_max_connections,
            "enabled": self.enable_l2_cache,
            "compression_enabled": self.compression_enabled,
            "compression_threshold": self.compression_threshold
        }
    
    def get_l3_config(self) -> dict:
        """Get L3 cache configuration."""
        return {
            "ttl": self.l3_ttl_seconds,
            "cleanup_batch_size": self.l3_cleanup_batch_size,
            "enabled": self.enable_l3_cache
        }
    
    def get_ttl_for_content_type(self, content_type: str) -> int:
        """Get TTL for specific content type."""
        return self.content_ttl_config.get(content_type, self.l2_default_ttl)
    
    def get_cache_key_config(self) -> dict:
        """Get cache key configuration."""
        return {
            "prefix_separator": ":",
            "version_separator": ":",
            "hash_length": 8,
            "include_version": True
        }
    
    def get_warming_config(self) -> dict:
        """Get cache warming configuration."""
        return {
            "enabled": self.enable_cache_warming,
            "startup_warming": self.cache_warm_on_startup,
            "batch_size": self.cache_warm_batch_size
        }
    
    def get_monitoring_config(self) -> dict:
        """Get cache monitoring configuration."""
        return {
            "metrics_enabled": self.enable_cache_metrics,
            "collection_interval": self.metrics_collection_interval,
            "track_hit_rate": True,
            "track_memory_usage": True,
            "track_operation_timing": True
        }
    
    def is_multi_layer_enabled(self) -> bool:
        """Check if multi-layer caching is enabled."""
        enabled_layers = sum([
            self.enable_l1_cache,
            self.enable_l2_cache,
            self.enable_l3_cache
        ])
        return enabled_layers > 1
    
    def get_active_layers(self) -> list:
        """Get list of active cache layers."""
        layers = []
        if self.enable_l1_cache:
            layers.append("L1_MEMORY")
        if self.enable_l2_cache:
            layers.append("L2_REDIS")
        if self.enable_l3_cache:
            layers.append("L3_DATABASE")
        return layers