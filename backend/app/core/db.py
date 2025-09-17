from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .settings import get_settings

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> None:
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database_url, future=True, echo=False)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        init_engine()
    assert _session_factory is not None
    return _session_factory


@asynccontextmanager
async def session_scope() -> AsyncSession:
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
