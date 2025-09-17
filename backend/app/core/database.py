"""Database connection and session management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable
import logging
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)


DEFAULT_LOCAL_DB_URL = "sqlite+aiosqlite:///./tmp/dev.sqlite3"


def _load_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        logger.warning("DATABASE_URL not set; falling back to local SQLite database.")
        return DEFAULT_LOCAL_DB_URL
    return url


DATABASE_URL = _load_database_url()
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

_engine_kwargs = {
    "echo": DATABASE_ECHO,
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith(("postgresql://", "postgresql+asyncpg://")):
    _engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_recycle": 3600,
        "pool_timeout": 30,
    })

engine = create_async_engine(
    DATABASE_URL,
    **_engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base class for SQLAlchemy models
Base = declarative_base()


async def init_db() -> None:
    """Initialise database schema (development convenience)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")


async def close_db() -> None:
    """Dispose the engine (used on application shutdown)."""
    await engine.dispose()
    logger.info("Database engine disposed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:  # pragma: no cover - exercised via FastAPI
        try:
            yield session
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager helper for manual session handling."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()
            raise


class DatabaseManager:
    """Simple health-check manager for database connectivity."""

    def __init__(self) -> None:
        self._healthy = False

    async def health_check(self) -> bool:
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            self._healthy = True
        except Exception as exc:  # noqa: BLE001
            logger.error("Database health check failed", exc_info=exc)
            self._healthy = False
        return self._healthy

    @property
    def is_healthy(self) -> bool:
        return self._healthy

    @property
    def session_factory(self) -> Callable[[], AsyncSession]:
        return AsyncSessionLocal


db_manager = DatabaseManager()


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Compatibility helper for legacy code/tests that expect a generator."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()
            raise
