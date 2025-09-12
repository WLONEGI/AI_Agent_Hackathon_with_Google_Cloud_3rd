"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis_client import redis_manager
from app.core.logging import setup_logging
from app.core.firebase import initialize_firebase
from app.api import manga, health
from app.api.v1 import api_router as api_v1_router, websocket_router_v1
from app.api.v1.error_handlers import (
    api_error_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler,
    APIError,
    ErrorContextMiddleware
)
from app.services.integrated_ai_service import IntegratedAIService
from app.services.cache_service import CacheService
from app.services.websocket_service import WebSocketService
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Manga Generation Service...")
    
    # Skip complex initialization for Cloud Run startup
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
    
    try:
        # Initialize Firebase (optional for basic service)
        # Fix: Use correct nested settings path
        firebase_initialized = initialize_firebase(
            settings.firebase_project_id,
            settings.firebase_credentials_path
        )
        if firebase_initialized:
            logger.info("Firebase initialized successfully")
        else:
            logger.warning("Firebase initialization failed - authentication may not work properly")
    except Exception as e:
        logger.warning(f"Firebase initialization failed: {e}")
    
    try:
        # Connect to Redis
        await redis_manager.connect()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
    
    # Initialize services
    try:
        app.state.integrated_ai_service = IntegratedAIService()
        app.state.cache_service = CacheService()
        app.state.websocket_service = WebSocketService()
        logger.info("Services initialized")
    except Exception as e:
        logger.warning(f"Service initialization failed: {e}")
    
    # Start background tasks
    try:
        await app.state.cache_service.start_background_tasks()
        logger.info("Background tasks started")
    except Exception as e:
        logger.warning(f"Background task startup failed: {e}")
    
    logger.info("Application started successfully")
    logger.info(f"7-Phase pipeline ready: Total processing time ~{sum(settings.phase_timeouts.values())}s")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Manga Generation Service...")
    
    # Stop background tasks
    await app.state.cache_service.stop_background_tasks()
    
    # Close connections
    await redis_manager.disconnect()
    await close_db()
    
    logger.info("Application shut down successfully")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered manga generation service with Human-in-the-Loop functionality",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None
)

# Add middleware
app.add_middleware(ErrorContextMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Register error handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Include routers
app.include_router(health.router, tags=["health"])

# Legacy v0 routes (for backward compatibility)
app.include_router(manga.router, prefix=f"{settings.api_prefix}/manga", tags=["manga-legacy"])

# New v1 API routes
app.include_router(api_v1_router, prefix=settings.api_prefix, tags=["api-v1"])

# Development API routes (temporarily enabled for testing)
# Enable mock routes for development testing
if True:  # Always enable for development testing
    from app.api.v1.manga_mock import router as manga_mock_router
    app.include_router(manga_mock_router, prefix=f"{settings.api_prefix}", tags=["manga-mock"])

# WebSocket routes
app.include_router(websocket_router_v1, tags=["websocket-v1"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API discovery."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "processing",
        "api_versions": {
            "v1": {
                "status": "stable",
                "base_url": f"{settings.api_prefix}",
                "docs": f"{settings.api_prefix}/info",
                "websocket": "/ws/v1"
            },
            "v0": {
                "status": "deprecated",
                "base_url": f"{settings.api_prefix}/manga",
                "deprecation_date": "2024-06-01"
            }
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs" if settings.debug else None,
            "api_info": f"{settings.api_prefix}/info",
            "websocket_health": "/ws/v1/health"
        },
        "pipeline": {
            "phases": 7,
            "total_time_seconds": sum(settings.phase_timeouts.values()),
            "critical_phases": settings.critical_phases,
            "parallel_phases": settings.parallel_phases,
            "phase_details": {
                phase_num: settings.get_phase_config(phase_num)
                for phase_num in range(1, 8)
            }
        },
        "features": {
            "hitl_feedback": True,
            "real_time_updates": True,
            "websocket_support": True,
            "rate_limiting": True,
            "authentication": True,
            "quality_assessment": True,
            "quality_gates": True,
            "preview_interactive": True,
            "version_control": True,
            "sse_streaming": True
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )