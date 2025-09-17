"""API v1 package - Optimized RESTful API with comprehensive features."""

from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .manga_sessions import router as manga_sessions_router
from .manga_works import router as manga_works_router
from .websocket_endpoints import router as websocket_router
from .feedback import router as feedback_router
from .quality_gates import router as quality_gates_router
from .preview_interactive import router as preview_interactive_router
from .auth import router as auth_router
from .user_management import router as user_management_router
from .system_api import router as system_api_router
from .generation_progress import router as generation_progress_router
from .preview_system import router as preview_system_router
from .hitl_chat import router as hitl_chat_router
from .security import get_current_active_user
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis_client import redis_manager

# Create main v1 router (prefix handled in main.py)
api_router = APIRouter()


def _auth_dependencies():
    if settings.debug and settings.env.lower() in {"development", "dev", "local"}:
        return []
    return [Depends(get_current_active_user)]


# Authentication API (public endpoints - no auth required)
api_router.include_router(
    auth_router,
    prefix="",
    tags=["authentication"],
)

# Manga Generation API (design document compliant paths)
api_router.include_router(
    manga_sessions_router,
    prefix="/manga",
    tags=["manga-generation"],
    dependencies=_auth_dependencies(),
)

# Manga Works Management API (design document compliant paths)
api_router.include_router(
    manga_works_router,
    prefix="/manga",
    tags=["manga-works"],
    dependencies=_auth_dependencies(),
)

# Quality Gate API
api_router.include_router(
    quality_gates_router,
    prefix="",
    tags=["quality-gates"],
    dependencies=_auth_dependencies(),
)

# Preview Interactive API
api_router.include_router(
    preview_interactive_router,
    prefix="",
    tags=["preview-interactive"],
    dependencies=_auth_dependencies(),
)

# HITL Feedback API
api_router.include_router(
    feedback_router,
    prefix="/manga",
    tags=["hitl-feedback"],
    dependencies=_auth_dependencies(),
)

# User Management API
api_router.include_router(
    user_management_router,
    prefix="/user",
    tags=["user-management"],
    dependencies=_auth_dependencies(),
)

# System API (public endpoints)
api_router.include_router(
    system_api_router,
    prefix="/system",
    tags=["system"],
)

# Generation Progress API
api_router.include_router(
    generation_progress_router,
    prefix="",
    tags=["generation-progress"],
    dependencies=_auth_dependencies(),
)

# Preview System API
api_router.include_router(
    preview_system_router,
    prefix="",
    tags=["preview-system"],
    dependencies=_auth_dependencies(),
)

# HITL Chat API
api_router.include_router(
    hitl_chat_router,
    prefix="",
    tags=["hitl-chat"],
    dependencies=_auth_dependencies(),
)

# WebSocket router doesn't need authentication dependency (handled internally)
websocket_router_v1 = APIRouter(prefix="/ws/v1")
websocket_router_v1.include_router(websocket_router, tags=["websocket"])


@api_router.get("/info")
async def api_info():
    """Get API v1 information and capabilities."""
    return {
        "version": "1.0",
        "name": "AI Manga Generation API",
        "description": "RESTful API for AI-powered manga generation with HITL feedback",
        "capabilities": {
            "manga_generation": {
                "max_phases": 7,
                "hitl_enabled": True,
                "real_time_updates": True,
                "supported_formats": ["json", "sse"],
                "quality_gates": True,
                "preview_interactive": True,
                "version_control": True,
            },
            "authentication": {
                "methods": ["jwt"],
                "rate_limiting": True,
                "permissions_based": True,
            },
            "websocket": {
                "protocol_version": "1.0",
                "endpoints": [
                    "/ws/v1/sessions/{session_id}",
                    "/ws/v1/sessions/{session_id}/phases/{phase_number}",
                    "/ws/v1/global/user/{user_id}",
                ],
                "features": [
                    "real_time_progress",
                    "hitl_feedback",
                    "quality_updates",
                    "preview_changes",
                ],
            },
        },
        "limits": {
            "generations_per_hour": 10,
            "api_calls_per_hour": 1000,
            "max_session_duration_hours": 24,
            "max_feedback_per_session": 100,
            "max_preview_versions": 50,
            "quality_override_limit": 5,
        },
        "phase_configuration": {
            phase_num: settings.get_phase_config(phase_num)
            for phase_num in range(1, 8)
        },
        "timestamp": datetime.utcnow().isoformat(),
        "server_time": datetime.utcnow().isoformat(),
    }


@api_router.get("/health")
async def health_check():
    """API v1 health check endpoint with actual component validation."""
    components = {"api": "healthy"}
    overall_status = "healthy"

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        components["database"] = "healthy"
    except Exception:  # noqa: BLE001
        components["database"] = "unhealthy"
        overall_status = "degraded"

    try:
        await redis_manager.health_check()
        components["redis"] = "healthy" if redis_manager.is_healthy else "unhealthy"
        if not redis_manager.is_healthy:
            overall_status = "degraded"
    except Exception:  # noqa: BLE001
        components["redis"] = "unhealthy"
        overall_status = "degraded"

    try:
        from app.services.websocket_service import WebSocketService

        ws_service = WebSocketService()
        stats = ws_service.get_stats()
        components["websocket"] = "healthy" if stats.get("active_sessions", 0) >= 0 else "unhealthy"
    except Exception:  # noqa: BLE001
        components["websocket"] = "unhealthy"
        overall_status = "degraded"

    status_code = 200 if overall_status == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "components": components,
        },
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-API-Version": "1.0",
        },
    )


__all__ = ["api_router", "websocket_router_v1"]
