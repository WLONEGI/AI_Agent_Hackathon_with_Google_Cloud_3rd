from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.models import MangaProject, MangaSession, PhaseResult
from app.dependencies import get_db_session


router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/health")
async def system_health(db: AsyncSession = Depends(get_db_session)) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:  # pragma: no cover - defensive
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "cloud_tasks": "configured",
            "storage": "configured",
        },
    }


@router.get("/capabilities")
async def system_capabilities() -> dict:
    settings = get_settings()
    return {
        "supported_styles": ["realistic", "anime", "cartoon", "sketch"],
        "max_pages": 100,
        "max_text_length": 50000,
        "max_characters": 5,
        "languages": ["ja", "en"],
        "file_formats": ["pdf", "webp"],
        "processing_time_estimate": {
            "per_1000_chars": 96,
            "base_time": 300,
        },
        "signed_url_ttl_seconds": settings.signed_url_ttl_seconds,
    }


@router.get("/dashboard")
async def system_dashboard(db: AsyncSession = Depends(get_db_session)) -> dict:
    total_projects = await db.execute(select(func.count()).select_from(MangaProject))
    total_sessions = await db.execute(select(func.count()).select_from(MangaSession))
    recent_sessions = await db.execute(
        select(func.count())
        .select_from(MangaSession)
        .where(MangaSession.created_at >= func.now() - text("INTERVAL '1 day'"))
    )
    avg_quality = await db.execute(select(func.avg(PhaseResult.quality_score)))

    return {
        "system_overview": {
            "projects_total": total_projects.scalar_one(),
            "sessions_total": total_sessions.scalar_one(),
            "sessions_last_24h": recent_sessions.scalar_one(),
        },
        "quality_metrics": {
            "avg_quality_score": float(avg_quality.scalar_one() or 0),
        },
    }
