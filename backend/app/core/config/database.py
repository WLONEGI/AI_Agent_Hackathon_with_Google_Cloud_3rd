"""Database configuration settings."""

from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field, field_validator


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # Primary database configuration
    url: str = Field(..., env="DATABASE_URL")
    pool_size: int = Field(20, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(10, env="DATABASE_MAX_OVERFLOW")
    pool_timeout: int = Field(30, env="DATABASE_POOL_TIMEOUT")
    pool_recycle: int = Field(3600, env="DATABASE_POOL_RECYCLE")
    echo: bool = Field(False, env="DATABASE_ECHO")
    echo_pool: bool = Field(False, env="DATABASE_ECHO_POOL")
    
    # Connection configuration
    connect_timeout: int = Field(10, env="DATABASE_CONNECT_TIMEOUT")
    command_timeout: int = Field(60, env="DATABASE_COMMAND_TIMEOUT")
    server_side_cursors: bool = Field(False, env="DATABASE_SERVER_SIDE_CURSORS")
    
    # SSL Configuration
    ssl_mode: Optional[str] = Field("prefer", env="DATABASE_SSL_MODE")
    ssl_cert: Optional[str] = Field(None, env="DATABASE_SSL_CERT")
    ssl_key: Optional[str] = Field(None, env="DATABASE_SSL_KEY")
    ssl_ca: Optional[str] = Field(None, env="DATABASE_SSL_CA")
    
    # Migration configuration
    migration_timeout: int = Field(300, env="DATABASE_MIGRATION_TIMEOUT")
    migration_lock_timeout: int = Field(60, env="DATABASE_MIGRATION_LOCK_TIMEOUT")
    
    # Health check configuration
    health_check_interval: int = Field(30, env="DATABASE_HEALTH_CHECK_INTERVAL")
    health_check_timeout: int = Field(5, env="DATABASE_HEALTH_CHECK_TIMEOUT")
    
    # Performance configuration
    statement_timeout: int = Field(30000, env="DATABASE_STATEMENT_TIMEOUT")  # milliseconds
    idle_in_transaction_session_timeout: int = Field(60000, env="DATABASE_IDLE_TIMEOUT")  # milliseconds
    
    @field_validator("url")
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v:
            raise ValueError("Database URL is required")
        
        if not (v.startswith(("postgresql://", "postgresql+asyncpg://")) or v.startswith(("sqlite://", "sqlite+aiosqlite://"))):
            raise ValueError("Database URL must be a PostgreSQL or SQLite URL")
        
        return v
    
    @field_validator("pool_size")
    def validate_pool_size(cls, v):
        """Validate pool size."""
        if v < 1:
            raise ValueError("Pool size must be at least 1")
        if v > 100:
            raise ValueError("Pool size cannot exceed 100")
        return v
    
    @field_validator("max_overflow")
    def validate_max_overflow(cls, v):
        """Validate max overflow."""
        if v < 0:
            raise ValueError("Max overflow cannot be negative")
        if v > 50:
            raise ValueError("Max overflow cannot exceed 50")
        return v
    
    @field_validator("ssl_mode")
    def validate_ssl_mode(cls, v):
        """Validate SSL mode."""
        if v is None:
            return v
        
        valid_modes = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
        if v not in valid_modes:
            raise ValueError(f"SSL mode must be one of {valid_modes}")
        return v
    
    class Config:
        env_file = ".env"
        env_prefix = "DATABASE_"
        case_sensitive = False
        extra = "ignore"
    
    @property
    def async_url(self) -> str:
        """Get async database URL."""
        if self.url.startswith("postgresql://"):
            return self.url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if self.url.startswith("sqlite://"):
            return self.url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return self.url
    
    @property
    def sync_url(self) -> str:
        """Get sync database URL for migrations."""
        if self.url.startswith("postgresql+asyncpg://"):
            return self.url.replace("postgresql+asyncpg://", "postgresql://", 1)
        if self.url.startswith("sqlite+aiosqlite://"):
            return self.url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return self.url
    
    def get_engine_config(self) -> dict:
        """Get SQLAlchemy engine configuration."""
        config = {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.echo,
            "echo_pool": self.echo_pool,
        }
        
        # Add connect args
        connect_args = {}
        
        if self.connect_timeout:
            connect_args["connect_timeout"] = self.connect_timeout
        
        if self.command_timeout:
            connect_args["command_timeout"] = self.command_timeout
        
        if self.server_side_cursors:
            connect_args["server_side_cursors"] = self.server_side_cursors
        
        if self.statement_timeout:
            connect_args["options"] = f"-c statement_timeout={self.statement_timeout}"
        
        # SSL configuration
        if self.ssl_mode and self.ssl_mode != "disable":
            connect_args["sslmode"] = self.ssl_mode
            
            if self.ssl_cert:
                connect_args["sslcert"] = self.ssl_cert
            if self.ssl_key:
                connect_args["sslkey"] = self.ssl_key
            if self.ssl_ca:
                connect_args["sslrootcert"] = self.ssl_ca
        
        if connect_args:
            config["connect_args"] = connect_args
        
        return config
    
    def get_alembic_config(self) -> dict:
        """Get Alembic migration configuration."""
        return {
            "sqlalchemy.url": self.sync_url,
            "migration_timeout": self.migration_timeout,
            "lock_timeout": self.migration_lock_timeout
        }
    
    def get_health_check_config(self) -> dict:
        """Get database health check configuration."""
        return {
            "interval": self.health_check_interval,
            "timeout": self.health_check_timeout,
            "query": "SELECT 1"
        }