from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.manga import PhasePreviewResponse, PhasePreviewUpdate
from app.db.models import MangaSession, PhaseResult, PreviewVersion, UserAccount


class PhasePreviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_phase_previews(
        self,
        request_id: UUID,
        current_user: UserAccount,
    ) -> List[PhasePreviewResponse]:
        """Get all phase previews for a session."""
        session = await self._get_user_session(request_id, current_user)

        from sqlalchemy import select

        # Get phase results with preview versions
        query = (
            select(PhaseResult)
            .where(PhaseResult.session_id == session.id)
            .order_by(PhaseResult.phase)
        )

        result = await self.db.execute(query)
        phase_results = result.scalars().all()

        previews = []
        for phase_result in phase_results:
            # Get latest preview version for this phase
            preview_query = (
                select(PreviewVersion)
                .where(PreviewVersion.session_id == session.id)
                .where(PreviewVersion.phase == phase_result.phase)
                .order_by(PreviewVersion.created_at.desc())
                .limit(1)
            )

            preview_result = await self.db.execute(preview_query)
            preview_version = preview_result.scalar_one_or_none()

            # Extract preview data
            preview_data = preview_version.version_data if preview_version else {}
            content = preview_data.get("content")
            image_url = preview_data.get("image_url")
            document_url = preview_data.get("document_url")

            # Calculate progress based on status
            progress = 0
            if phase_result.status == "completed":
                progress = 100
            elif phase_result.status == "running":
                progress = 50
            elif phase_result.status == "awaiting_feedback":
                progress = 90

            previews.append(
                PhasePreviewResponse(
                    id=str(phase_result.id),
                    session_id=str(session.id),
                    phase_number=phase_result.phase,
                    preview_type=self._determine_preview_type(preview_data),
                    content=content,
                    image_url=image_url,
                    document_url=document_url,
                    progress=progress,
                    status=phase_result.status,
                    metadata=preview_data,
                    created_at=phase_result.created_at,
                    updated_at=phase_result.updated_at,
                )
            )

        return previews

    async def get_phase_preview(
        self,
        request_id: UUID,
        phase_id: int,
        current_user: UserAccount,
    ) -> PhasePreviewResponse:
        """Get a specific phase preview."""
        session = await self._get_user_session(request_id, current_user)

        from sqlalchemy import select

        query = (
            select(PhaseResult)
            .where(PhaseResult.session_id == session.id)
            .where(PhaseResult.phase == phase_id)
        )

        result = await self.db.execute(query)
        phase_result = result.scalar_one_or_none()

        if not phase_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Phase {phase_id} not found",
            )

        # Get latest preview version
        preview_query = (
            select(PreviewVersion)
            .where(PreviewVersion.session_id == session.id)
            .where(PreviewVersion.phase == phase_id)
            .order_by(PreviewVersion.created_at.desc())
            .limit(1)
        )

        preview_result = await self.db.execute(preview_query)
        preview_version = preview_result.scalar_one_or_none()

        preview_data = preview_version.version_data if preview_version else {}
        content = preview_data.get("content")
        image_url = preview_data.get("image_url")
        document_url = preview_data.get("document_url")

        progress = 0
        if phase_result.status == "completed":
            progress = 100
        elif phase_result.status == "running":
            progress = 50
        elif phase_result.status == "awaiting_feedback":
            progress = 90

        return PhasePreviewResponse(
            id=str(phase_result.id),
            session_id=str(session.id),
            phase_number=phase_result.phase,
            preview_type=self._determine_preview_type(preview_data),
            content=content,
            image_url=image_url,
            document_url=document_url,
            progress=progress,
            status=phase_result.status,
            metadata=preview_data,
            created_at=phase_result.created_at,
            updated_at=phase_result.updated_at,
        )

    async def update_phase_preview(
        self,
        request_id: UUID,
        phase_id: int,
        payload: PhasePreviewUpdate,
        current_user: UserAccount,
    ) -> PhasePreviewResponse:
        """Update a phase preview."""
        session = await self._get_user_session(request_id, current_user)

        from sqlalchemy import select

        # Get or create phase result
        query = (
            select(PhaseResult)
            .where(PhaseResult.session_id == session.id)
            .where(PhaseResult.phase == phase_id)
        )

        result = await self.db.execute(query)
        phase_result = result.scalar_one_or_none()

        if not phase_result:
            # Create new phase result
            phase_result = PhaseResult(
                session_id=session.id,
                phase=phase_id,
                status=payload.status,
            )
            self.db.add(phase_result)
            await self.db.flush()

        # Update phase result status
        phase_result.status = payload.status

        # Create new preview version
        version_data = {
            "preview_type": payload.preview_type,
            "content": payload.content,
            "image_url": payload.image_url,
            "document_url": payload.document_url,
            "progress": payload.progress,
            "metadata": payload.metadata or {},
        }

        preview_version = PreviewVersion(
            session_id=session.id,
            phase=phase_id,
            version_data=version_data,
            change_description=f"Updated {payload.preview_type} preview",
        )

        self.db.add(preview_version)
        await self.db.flush()
        await self.db.commit()

        # Create event for real-time updates
        await self._create_session_event(
            session.id,
            "phase_updated",
            {
                "phase": phase_id,
                "status": payload.status,
                "progress": payload.progress,
                "preview_type": payload.preview_type,
            },
        )

        return PhasePreviewResponse(
            id=str(phase_result.id),
            session_id=str(session.id),
            phase_number=phase_id,
            preview_type=payload.preview_type,
            content=payload.content,
            image_url=payload.image_url,
            document_url=payload.document_url,
            progress=payload.progress,
            status=payload.status,
            metadata=payload.metadata,
            created_at=phase_result.created_at,
            updated_at=phase_result.updated_at,
        )

    def _determine_preview_type(self, preview_data: dict) -> str:
        """Determine preview type from data."""
        if preview_data.get("image_url"):
            return "image"
        elif preview_data.get("document_url"):
            return "document"
        else:
            return "text"

    async def _get_user_session(self, request_id: UUID, current_user: UserAccount) -> MangaSession:
        """Get session and verify ownership."""
        from sqlalchemy import select

        query = (
            select(MangaSession)
            .where(MangaSession.request_id == request_id)
            .where(MangaSession.user_id == current_user.id)
        )

        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        return session

    async def _create_session_event(self, session_id: UUID, event_type: str, event_data: dict):
        """Create a session event for real-time updates."""
        from app.db.models import SessionEvent

        event = SessionEvent(
            session_id=session_id,
            event_type=event_type,
            event_data=event_data,
        )

        self.db.add(event)
        await self.db.flush()