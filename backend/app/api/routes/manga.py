from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.manga import (
    FeedbackRequest,
    GenerateRequest,
    GenerateResponse,
    MangaProjectDetailResponse,
    MangaProjectItem,
    MangaProjectListResponse,
    MessageRequest,
    MessageResponse,
    MessagesListResponse,
    Pagination,
    PhaseErrorDetailResponse,
    PhasePreviewResponse,
    PhasePreviewUpdate,
    PhaseRetryRequest,
    PhaseRetryResponse,
    SessionDetailResponse,
    SessionStatusResponse,
)
from app.dependencies import get_db_session
from app.dependencies.auth import get_current_user
from app.db.models import UserAccount
from app.services.feedback_service import FeedbackService
from app.services.generation_service import GenerationService
from app.services.manga_project_service import MangaProjectService
from app.services.message_service import MessageService
from app.services.phase_preview_service import PhasePreviewService

router = APIRouter(prefix="/api/v1/manga", tags=["manga"])


@router.get("", response_model=MangaProjectListResponse)
async def get_manga_projects(
    page: int = 1,
    limit: int = 20,
    sort: str = "created_at",
    order: str = "desc",
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> MangaProjectListResponse:
    """Get paginated list of user's manga projects"""
    service = MangaProjectService(db)
    try:
        items, pagination = await service.get_user_projects(
            user=current_user,
            page=page,
            limit=limit,
            sort=sort,
            order=order,
            status_filter=status_filter,
        )
        return MangaProjectListResponse(items=items, pagination=pagination)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{manga_id}", response_model=MangaProjectDetailResponse)
async def get_manga_project_detail(
    manga_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> MangaProjectDetailResponse:
    """Get detailed information about a specific manga project"""
    service = MangaProjectService(db)
    try:
        project = await service.get_project_detail(manga_id, current_user)
        if not project:
            raise HTTPException(status_code=404, detail="Manga project not found")
        return project
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_generation(
    payload: GenerateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> GenerateResponse:
    try:
        service = GenerationService(db)
        return await service.enqueue_generation(payload, current_user)
    except ValidationError as e:
        # Pydantic バリデーションエラーの詳細化
        error_details = []
        for error in e.errors():
            field = error.get('loc', ['unknown'])[-1]
            msg = error.get('msg', 'validation error')

            if field == 'text' and 'at least' in msg:
                error_details.append("テキストは10文字以上で入力してください")
            elif field == 'text' and 'at most' in msg:
                error_details.append("テキストは50,000文字以下で入力してください")
            elif field == 'title' and 'required' in msg:
                error_details.append("タイトルは必須です")
            else:
                error_details.append(f"{field}: {msg}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"入力内容に問題があります: {', '.join(error_details)}"
        ) from e


@router.get("/sessions/{request_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    request_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> SessionStatusResponse:
    service = GenerationService(db)
    try:
        return await service.get_status(request_id, current_user)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions/{request_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    request_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> SessionDetailResponse:
    service = GenerationService(db)
    try:
        return await service.get_session(request_id, current_user)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/sessions/{request_id}/feedback", status_code=status.HTTP_202_ACCEPTED)
async def submit_feedback(
    request_id: UUID,
    payload: FeedbackRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> dict[str, str]:
    service = FeedbackService(db)
    try:
        return await service.submit_feedback(request_id, payload, current_user)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


# Message endpoints
@router.get("/sessions/{request_id}/messages", response_model=MessagesListResponse)
async def get_session_messages(
    request_id: UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> MessagesListResponse:
    service = MessageService(db)
    try:
        return await service.get_session_messages(request_id, current_user, limit, offset)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/sessions/{request_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_session_message(
    request_id: UUID,
    payload: MessageRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> MessageResponse:
    service = MessageService(db)
    try:
        return await service.create_message(request_id, payload, current_user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# Phase preview endpoints
@router.get("/sessions/{request_id}/phases", response_model=list[PhasePreviewResponse])
async def get_phase_previews(
    request_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> list[PhasePreviewResponse]:
    service = PhasePreviewService(db)
    try:
        return await service.get_phase_previews(request_id, current_user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions/{request_id}/phases/{phase_id}", response_model=PhasePreviewResponse)
async def get_phase_preview(
    request_id: UUID,
    phase_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> PhasePreviewResponse:
    service = PhasePreviewService(db)
    try:
        return await service.get_phase_preview(request_id, phase_id, current_user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/sessions/{request_id}/phases/{phase_id}", response_model=PhasePreviewResponse)
async def update_phase_preview(
    request_id: UUID,
    phase_id: int,
    payload: PhasePreviewUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> PhasePreviewResponse:
    service = PhasePreviewService(db)
    try:
        return await service.update_phase_preview(request_id, phase_id, payload, current_user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# Phase error handling endpoints
@router.get("/sessions/{request_id}/phases/{phase_id}/error", response_model=PhaseErrorDetailResponse)
async def get_phase_error_details(
    request_id: UUID,
    phase_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> PhaseErrorDetailResponse:
    """Get detailed error information for a specific phase"""
    from app.services.pipeline_service import HITLCapablePipelineOrchestrator
    from app.core.db import get_session_factory

    try:
        # Get session and verify ownership
        generation_service = GenerationService(db)
        session = await generation_service._get_session_by_request(request_id, current_user)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get error details using pipeline service
        session_factory = get_session_factory()
        orchestrator = HITLCapablePipelineOrchestrator(session_factory)
        error_details = await orchestrator.get_phase_error_details(session, phase_id)

        if not error_details:
            raise HTTPException(status_code=404, detail="No error information found for this phase")

        return PhaseErrorDetailResponse(**error_details)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/sessions/{request_id}/phases/{phase_id}/retry", response_model=PhaseRetryResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_phase(
    request_id: UUID,
    phase_id: int,
    payload: PhaseRetryRequest = PhaseRetryRequest(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> PhaseRetryResponse:
    """Retry a specific phase of the manga generation process"""
    from app.services.pipeline_service import HITLCapablePipelineOrchestrator
    from app.core.db import get_session_factory

    try:
        # Get session and verify ownership
        generation_service = GenerationService(db)
        session = await generation_service._get_session_by_request(request_id, current_user)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check if phase exists
        from sqlalchemy import select
        from app.db.models.phase_result import PhaseResult

        result = await db.execute(
            select(PhaseResult).where(
                PhaseResult.session_id == session.id,
                PhaseResult.phase == phase_id
            )
        )
        phase_result = result.scalar_one_or_none()

        if not phase_result:
            raise HTTPException(status_code=404, detail=f"Phase {phase_id} not found")

        # Check if retry is already in progress
        if session.status == "running" and session.current_phase == phase_id:
            return PhaseRetryResponse(
                phase_id=phase_id,
                status="already_running",
                message="Phase retry is already in progress",
                retry_started=False
            )

        # Start retry using pipeline service
        session_factory = get_session_factory()
        orchestrator = HITLCapablePipelineOrchestrator(session_factory)

        retry_success = await orchestrator.retry_specific_phase(
            session=session,
            phase_id=phase_id,
            force_retry=payload.force_retry,
            reset_feedback=payload.reset_feedback
        )

        if not retry_success:
            return PhaseRetryResponse(
                phase_id=phase_id,
                status="failed",
                message="Failed to start phase retry",
                retry_started=False
            )

        # Calculate estimated completion time
        estimated_completion = datetime.utcnow() + timedelta(minutes=5)  # Estimate 5 minutes per phase

        return PhaseRetryResponse(
            phase_id=phase_id,
            status="started",
            message="Phase retry started successfully",
            retry_started=True,
            estimated_completion_time=estimated_completion
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
