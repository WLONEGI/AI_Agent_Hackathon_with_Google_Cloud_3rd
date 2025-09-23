from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.manga import (
    GenerateRequest,
    GenerateResponse,
    SessionDetailResponse,
    SessionStatusResponse,
)
from app.core import settings as core_settings
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
        self.settings = core_settings.get_settings()

    async def enqueue_generation(
        self,
        payload: GenerateRequest,
        user: UserAccount,
    ) -> GenerateResponse:
        try:
            project = MangaProject(
                user_id=user.id,
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
                user_id=user.id,
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

            # Start processing directly in background task
            await self._start_processing_task(session.request_id)

            await self.db.commit()

            expected_duration = 8 if payload.options.priority != "high" else 5
            eta = datetime.utcnow() + timedelta(minutes=expected_duration)
            return GenerateResponse(
                request_id=str(session.request_id),
                status=session.status,
                estimated_completion_time=eta,
                expected_duration_minutes=expected_duration,
                status_url=f"/api/v1/manga/sessions/{session.request_id}/status",
                websocket_channel=self._build_websocket_channel(session.request_id),
                message="Generation started",
            )
        except Exception as exc:
            # Rollback transaction on any error
            await self.db.rollback()
            import logging
            logging.getLogger(__name__).error("Failed to start generation: %s", exc)
            raise HTTPException(
                status_code=500,
                detail="Failed to start manga generation. Please try again."
            ) from exc

    async def get_status(
        self,
        request_id: UUID,
        user: Optional[UserAccount] = None,
    ) -> SessionStatusResponse:
        session = await self._get_session_by_request(request_id, user)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return SessionStatusResponse(
            session_id=str(session.id),
            request_id=str(session.request_id),
            status=session.status,
            current_phase=session.current_phase,
            updated_at=session.updated_at or datetime.utcnow(),
            project_id=str(session.project_id) if session.project_id else None,
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
            session_id=str(session.id),
            request_id=str(session.request_id),
            status=session.status,
            current_phase=session.current_phase,
            started_at=session.started_at,
            completed_at=session.completed_at,
            retry_count=session.retry_count,
            phase_results=[pr.content or {} for pr in session.phase_results],
            preview_versions=[pv.version_data or {} for pv in session.preview_versions],
            project_id=str(session.project_id) if session.project_id else None,
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

    async def _start_processing_task(self, request_id: UUID) -> None:
        """Start manga processing in a background task"""
        import asyncio
        from app.core.db import get_session_factory
        from app.services.pipeline_service import PipelineOrchestrator
        
        async def process_in_background():
            """Background task to process manga generation"""
            try:
                session_factory = get_session_factory()
                orchestrator = PipelineOrchestrator(session_factory)
                await orchestrator.run(request_id)
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"✅ Manga processing completed for request_id: {request_id}")
            except Exception as exc:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"❌ Manga processing failed for request_id: {request_id}: {exc}", exc_info=True)

        # Start background task without waiting for completion
        asyncio.create_task(process_in_background())

    def _build_websocket_channel(self, request_id: UUID) -> str:
        return f"manga-session-{request_id}"
