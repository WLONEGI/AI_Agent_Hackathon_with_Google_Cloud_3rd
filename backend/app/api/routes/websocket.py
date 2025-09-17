from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.settings import get_settings
from app.services.realtime_hub import realtime_hub


router = APIRouter()


@router.websocket("/ws/session/{request_id}")
async def websocket_session_endpoint(websocket: WebSocket, request_id: UUID, token: str | None = None):
    settings = get_settings()
    # Basic token gate: allow empty tokens in development environments
    if settings.app_env != "development" and not token:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    queue = await realtime_hub.subscribe(request_id)
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        await realtime_hub.unsubscribe(request_id, queue)
