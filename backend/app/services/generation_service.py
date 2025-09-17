from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from google.cloud import tasks_v2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.manga import (
    GenerateRequest,
    GenerateResponse,
    SessionDetailResponse,
    SessionStatusResponse,
)
from app.core.clients import get_tasks_client
from app.core.settings import get_settings
from app.db.models import (
    MangaProject,
    MangaProjectStatus,
    MangaSession,
    MangaSessionStatus,
    UserAccount,
)


class GenerationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.tasks_client = get_tasks_client()

    async def enqueue_generation(
        self,
        payload: GenerateRequest,
        user: Optional[UserAccount] = None,
    ) -> GenerateResponse:
        project = MangaProject(
            user_id=user.id if user else None,
            title=payload.title,
            status=MangaProjectStatus.PROCESSING,
            project_metadata={
                "source_text_length": len(payload.text),
                "ai_auto_settings": payload.ai_auto_settings,
                "options": payload.options.model_dump(),
            },
            settings={"feedback_mode": payload.feedback_mode.model_dump()},
            total_pages=None,
        )
        self.db.add(project)
        await self.db.flush()

        generated_request_id = uuid4()
        session = MangaSession(
            request_id=generated_request_id,
            status=MangaSessionStatus.QUEUED.value,
            user_id=user.id if user else None,
            project_id=project.id,
            session_metadata={
                "title": payload.title,
                "text": payload.text,
                "feedback_mode": payload.feedback_mode.model_dump(),
                "options": payload.options.model_dump(),
            },
        )
        self.db.add(session)
        await self.db.flush()

        await self._enqueue_task(session.request_id)

        expected_duration = 8 if payload.options.priority != "high" else 5
        eta = datetime.utcnow() + timedelta(minutes=expected_duration)
        return GenerateResponse(
            request_id=session.request_id,
            status=session.status,
            estimated_completion_time=eta,
            expected_duration_minutes=expected_duration,
            status_url=f"/api/v1/manga/sessions/{session.request_id}/status",
            websocket_channel=self._build_websocket_channel(session.request_id),
            message="Generation enqueued",
        )

    async def get_status(
        self,
        request_id: UUID,
        user: Optional[UserAccount] = None,
    ) -> SessionStatusResponse:
        session = await self._get_session_by_request(request_id, user)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return SessionStatusResponse(
            session_id=session.id,
            request_id=session.request_id,
            status=session.status,
            current_phase=session.current_phase,
            updated_at=session.updated_at or datetime.utcnow(),
            project_id=session.project_id,
        )

    async def get_session(
        self,
        request_id: UUID,
        user: Optional[UserAccount] = None,
    ) -> SessionDetailResponse:
        session = await self._get_session_by_request(request_id, user)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return SessionDetailResponse(
            session_id=session.id,
            request_id=session.request_id,
            status=session.status,
            current_phase=session.current_phase,
            started_at=session.started_at,
            completed_at=session.completed_at,
            retry_count=session.retry_count,
            phase_results=[pr.content or {} for pr in session.phase_results],
            preview_versions=[pv.version_data or {} for pv in session.preview_versions],
            project_id=session.project_id,
        )

    async def _get_session_by_request(
        self,
        request_id: UUID,
        user: Optional[UserAccount] = None,
    ) -> Optional[MangaSession]:
        result = await self.db.execute(
            select(MangaSession).where(MangaSession.request_id == request_id)
        )
        session = result.scalar_one_or_none()
        if session and user and session.user_id and session.user_id != user.id:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    async def _enqueue_task(self, request_id: UUID) -> None:
        parent = self.tasks_client.queue_path(
            self.settings.cloud_tasks_project,
            self.settings.cloud_tasks_location,
            self.settings.cloud_tasks_queue,
        )

        task = tasks_v2.Task(
            http_request=tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=f"{self.settings.cloud_tasks_service_url}/internal/tasks/manga",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"request_id": str(request_id)}).encode("utf-8"),
            )
        )

        try:
            self.tasks_client.create_task(request={"parent": parent, "task": task})
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Cloud Tasks enqueue failed: %s", exc)

    def _build_websocket_channel(self, request_id: UUID) -> Optional[str]:
        if self.settings.websocket_base_url:
            return f"{self.settings.websocket_base_url}/ws/session/{request_id}"
        return f"/ws/session/{request_id}"
