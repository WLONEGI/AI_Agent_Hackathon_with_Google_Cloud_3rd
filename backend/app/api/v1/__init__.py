"""API v1 package - Optimized RESTful API with comprehensive features."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime

from .manga_sessions import router as manga_sessions_router
from .manga_works import router as manga_works_router
from .websocket_endpoints import router as websocket_router
from .feedback import router as feedback_router
from .quality_gates import router as quality_gates_router
from .preview_interactive import router as preview_interactive_router
from .security import get_current_active_user
from app.core.config import settings

# Create main v1 router
api_router = APIRouter(prefix="/v1")

# Include all sub-routers with proper prefixes

# Manga Generation API (design document compliant paths)
# NOTE: Order matters - specific paths must come before generic paths
api_router.include_router(
    manga_sessions_router,
    prefix="/manga",
    tags=["manga-generation"],
    dependencies=[Depends(get_current_active_user)]
)

# Manga Works Management API (design document compliant paths)
# NOTE: This router handles GET /manga and GET /manga/{manga_id}
# Must be registered after manga_sessions_router to avoid path conflicts
api_router.include_router(
    manga_works_router,
    prefix="/manga", 
    tags=["manga-works"],
    dependencies=[Depends(get_current_active_user)]
)

# Quality Gate API
api_router.include_router(
    quality_gates_router,
    prefix="",
    tags=["quality-gates"],
    dependencies=[Depends(get_current_active_user)]
)

# Preview Interactive API
api_router.include_router(
    preview_interactive_router,
    prefix="",
    tags=["preview-interactive"],
    dependencies=[Depends(get_current_active_user)]
)

# HITL Feedback API
api_router.include_router(
    feedback_router,
    prefix="/manga",
    tags=["hitl-feedback"],
    dependencies=[Depends(get_current_active_user)]
)

# WebSocket router doesn't need authentication dependency (handled internally)
websocket_router_v1 = APIRouter(prefix="/ws/v1")
websocket_router_v1.include_router(websocket_router, tags=["websocket"])

# API version info endpoint
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
                "version_control": True
            },
            "authentication": {
                "methods": ["jwt"],
                "rate_limiting": True,
                "permissions_based": True
            },
            "websocket": {
                "protocol_version": "1.0",
                "endpoints": [
                    "/ws/v1/sessions/{session_id}",
                    "/ws/v1/sessions/{session_id}/phases/{phase_number}",
                    "/ws/v1/global/user/{user_id}"
                ],
                "features": [
                    "real_time_progress",
                    "hitl_feedback",
                    "quality_updates",
                    "preview_changes"
                ]
            }
        },
        "limits": {
            "generations_per_hour": 10,
            "api_calls_per_hour": 1000,
            "max_session_duration_hours": 24,
            "max_feedback_per_session": 100,
            "max_preview_versions": 50,
            "quality_override_limit": 5
        },
        "phase_configuration": {
            phase_num: settings.get_phase_config(phase_num)
            for phase_num in range(1, 8)
        },
        "timestamp": datetime.utcnow().isoformat(),
        "server_time": datetime.utcnow().isoformat()
    }

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """API v1 health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "api": "healthy",
                "database": "healthy",  # TODO: Add actual health checks
                "redis": "healthy",     # TODO: Add actual health checks
                "websocket": "healthy"  # TODO: Add actual health checks
            }
        },
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-API-Version": "1.0"
        }
    )


# Export routers for main app
__all__ = ["api_router", "websocket_router_v1"]