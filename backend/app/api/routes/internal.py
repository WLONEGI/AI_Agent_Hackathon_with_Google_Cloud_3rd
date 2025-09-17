from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.tasks import TaskPayload
from app.dependencies import get_db_session
from app.services.pipeline_service import PipelineOrchestrator

router = APIRouter(prefix="/internal/tasks", tags=["internal"])


@router.post("/manga", status_code=status.HTTP_202_ACCEPTED)
async def execute_manga_task(
    payload: TaskPayload,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    orchestrator = PipelineOrchestrator(db)
    try:
        await orchestrator.run(payload.request_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "processed"}
