from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import auth as auth_routes
from app.api.routes import internal as internal_routes
from app.api.routes import manga as manga_routes
from app.api.routes import projects as project_routes
from app.api.routes import websocket as websocket_routes
from app.api.routes import system as system_routes
from app.core.logging import configure_logging
from app.core.settings import get_settings


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.get("/health/live")
    async def health_live() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_routes.router)
    app.include_router(project_routes.router)
    app.include_router(system_routes.router)
    app.include_router(manga_routes.router)
    app.include_router(websocket_routes.router)
    app.include_router(internal_routes.router)

    return app


app = create_app()
