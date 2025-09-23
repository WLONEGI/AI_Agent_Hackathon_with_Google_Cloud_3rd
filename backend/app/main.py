from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth as auth_routes
from app.api.routes import hitl as hitl_routes
from app.api.routes import internal as internal_routes
from app.api.routes import manga as manga_routes
from app.api.routes import projects as project_routes
from app.api.routes import websocket as websocket_routes
from app.api.routes import system as system_routes
from app.core.logging import configure_logging
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan with background tasks"""
    logger.info("🚀 Starting Spell backend application")

    # Start background tasks
    background_tasks = []

    try:
        # Import here to avoid circular imports and startup issues
        logger.info("🔧 Importing background services...")
        from app.services.health_monitor import start_health_monitoring
        logger.info("✅ Health monitor imported")

        from app.services.state_reconciler import start_periodic_reconciliation
        logger.info("✅ State reconciler imported")

        # Start health monitoring (every 5 minutes)
        logger.info("🏥 Starting health monitoring...")
        health_task = asyncio.create_task(start_health_monitoring(interval_minutes=5))
        background_tasks.append(health_task)
        logger.info("✅ Health monitoring started")

        # Start state reconciliation (every 10 minutes)
        logger.info("🔄 Starting state reconciliation...")
        reconcile_task = asyncio.create_task(start_periodic_reconciliation(interval_minutes=10))
        background_tasks.append(reconcile_task)
        logger.info("✅ State reconciliation started")

        logger.info("🎯 All background services started successfully")

    except Exception as e:
        logger.error(f"❌ Failed to start background services: {e}", exc_info=True)
        # Continue startup even if background services fail

    yield  # Application runs here

    # Cleanup on shutdown
    logger.info("🛑 Shutting down background services")
    for task in background_tasks:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    logger.info("✅ Shutdown complete")


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://comic-ai-agent-470309.web.app",
            "https://comic-ai-agent-470309.firebaseapp.com",
            "https://accounts.google.com",  # Google authentication
            "https://firebase.googleapis.com",  # Firebase services
            "http://localhost:3000",  # for development
            "http://localhost:3001",  # for development
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/health/live")
    async def health_live() -> dict[str, str]:
        """Basic liveness probe for Cloud Run"""
        return {"status": "ok"}

    @app.get("/health/ready")
    async def health_ready() -> dict[str, str]:
        """Readiness probe - check if app is ready to serve traffic"""
        try:
            # Basic database connectivity check
            from app.core.db import session_scope
            from sqlalchemy import text

            async with session_scope() as db_session:
                await db_session.execute(text("SELECT 1"))
                return {"status": "ready"}
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return {"status": "not_ready", "error": str(e)}

    @app.get("/health/comprehensive")
    async def health_comprehensive():
        """Comprehensive system health check"""
        try:
            from app.services.health_monitor import health_monitor
            report = await health_monitor.get_system_health()
            return {
                "status": report.overall_status.value,
                "score": report.score,
                "timestamp": report.timestamp.isoformat(),
                "metrics_count": len(report.metrics),
                "recommendations_count": len(report.recommendations)
            }
        except Exception as e:
            logger.error(f"Comprehensive health check failed: {e}")
            return {"status": "error", "error": str(e)}

    app.include_router(auth_routes.router)
    app.include_router(project_routes.router)
    app.include_router(system_routes.router)
    app.include_router(manga_routes.router)
    app.include_router(hitl_routes.router)
    app.include_router(websocket_routes.router)
    app.include_router(internal_routes.router)

    return app


app = create_app()
