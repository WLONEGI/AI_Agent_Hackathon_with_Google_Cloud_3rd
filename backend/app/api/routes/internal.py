from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.tasks import TaskPayload
from app.core.db import get_session_factory
from app.services.pipeline_service import PipelineOrchestrator

router = APIRouter(prefix="/internal/tasks", tags=["internal"])


@router.post("/manga", status_code=status.HTTP_202_ACCEPTED)
async def execute_manga_task(
    payload: TaskPayload,
) -> dict[str, str]:
    session_factory = get_session_factory()
    orchestrator = PipelineOrchestrator(session_factory)
    try:
        await orchestrator.run(payload.request_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "processed"}
