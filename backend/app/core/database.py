"""Database connection and session management."""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
import logging
import os

logger = logging.getLogger(__name__)

# Get database URL from environment variable to avoid circular imports
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/manga_service")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# Create async engine with database-specific settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration (no connection pooling)
    engine = create_async_engine(
        DATABASE_URL,
        echo=DATABASE_ECHO,
        poolclass=NullPool,  # SQLite doesn't support connection pooling
    )
else:
    # PostgreSQL configuration with pooling
    engine = create_async_engine(
        DATABASE_URL,
        echo=DATABASE_ECHO,
        pool_size=20,  # Increased from default for production load
        max_overflow=10,  # Allow temporary spike connections
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_timeout=30,  # Connection timeout in seconds
        connect_args={
            "server_settings": {"jit": "off"},  # Disable JIT for consistent performance
            "command_timeout": 60,
            "timeout": 60,
        },
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def init_db() -> None:
    """Initialize database (create tables)."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


async def close_db() -> None:
    """Close database connections."""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Get database session as context manager."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """Database connection manager with health checks."""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
        self._healthy = False
    
    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                self._healthy = True
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self._healthy = False
            return False
    
    async def get_session(self) -> AsyncSession:
        """Get a new database session."""
        if not self._healthy:
            await self.health_check()
        return self.session_factory()
    
    @property
    def is_healthy(self) -> bool:
        """Check if database connection is healthy."""
        return self._healthy


# Global database manager instance
db_manager = DatabaseManager()