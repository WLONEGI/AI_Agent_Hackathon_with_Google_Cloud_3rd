from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.manga import (
    FeedbackRequest,
    GenerateRequest,
    GenerateResponse,
    MessageRequest,
    MessageResponse,
    MessagesListResponse,
    PhasePreviewResponse,
    PhasePreviewUpdate,
    SessionDetailResponse,
    SessionStatusResponse,
)
from app.dependencies import get_db_session
from app.dependencies.auth import get_current_user
from app.db.models import UserAccount
from app.services.feedback_service import FeedbackService
from app.services.generation_service import GenerationService
from app.services.message_service import MessageService
from app.services.phase_preview_service import PhasePreviewService

router = APIRouter(prefix="/api/v1/manga", tags=["manga"])


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_generation(
    payload: GenerateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user),
) -> GenerateResponse:
    service = GenerationService(db)
    return await service.enqueue_generation(payload, current_user)


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
