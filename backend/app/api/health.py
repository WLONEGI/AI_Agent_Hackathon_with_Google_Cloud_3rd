"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Dict, Any

from app.core.database import get_db, db_manager
from app.core.redis_client import redis_manager
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.app_name,
        "version": settings.app_version
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Detailed health check with component status."""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.app_name,
        "version": settings.app_version,
        "components": {}
    }
    
    # Check database
    try:
        await db.execute("SELECT 1")
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "PostgreSQL"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        if await redis_manager.health_check():
            health_status["components"]["cache"] = {
                "status": "healthy",
                "type": "Redis"
            }
        else:
            raise Exception("Redis health check failed")
    except Exception as e:
        health_status["components"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check AI service availability (placeholder)
    health_status["components"]["ai_service"] = {
        "status": "healthy",
        "gemini_model": settings.gemini_model,
        "imagen_model": settings.imagen_model
    }
    
    # System metrics
    health_status["metrics"] = {
        "environment": settings.env,
        "debug_mode": settings.debug,
        "max_parallel_images": settings.max_parallel_image_generation
    }
    
    return health_status


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check for Kubernetes."""
    
    # Check if all components are ready
    db_ready = await db_manager.health_check()
    redis_ready = await redis_manager.health_check()
    
    if db_ready and redis_ready:
        return {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        return {
            "ready": False,
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_ready,
            "cache": redis_ready
        }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes."""
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }