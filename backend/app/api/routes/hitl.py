from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas.hitl import (
    ErrorResponse,
    FeedbackHistoryResponse,
    FeedbackOptionsQuery,
    FeedbackOptionsResponse,
    FeedbackResponse,
    FeedbackStateResponse,
    HITLStatusResponse,
    PhasePreviewResponse,
    UserFeedbackHistoryResponse,
    UserFeedbackRequest,
)
from app.core.settings import get_settings
from app.db.models import (
    FeedbackOptionTemplate,
    MangaSession,
    PhaseFeedbackState,
    UserFeedbackHistory,
)
from app.dependencies import get_db_session
from app.services.hitl_service import HITLService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/hitl", tags=["hitl"])


@router.post(
    "/sessions/{session_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid feedback data"},
        404: {"model": ErrorResponse, "description": "Session or feedback state not found"},
        409: {"model": ErrorResponse, "description": "Feedback already submitted or session not waiting"},
    }
)
async def submit_user_feedback(
    session_id: UUID,
    feedback: UserFeedbackRequest,
    db: AsyncSession = Depends(get_db_session),
) -> FeedbackResponse:
    """Submit user feedback for a specific session and phase"""

    try:
        # Initialize HITL service
        hitl_service = HITLService(db)

        # Submit feedback and get result
        result = await hitl_service.submit_feedback(
            session_id=session_id,
            phase=feedback.phase,
            feedback_type=feedback.feedback_type,
            selected_options=feedback.selected_options,
            natural_language_input=feedback.natural_language_input,
            user_satisfaction_score=feedback.user_satisfaction_score,
            processing_time_ms=feedback.processing_time_ms,
        )

        return FeedbackResponse(
            success=True,
            message="Feedback submitted successfully",
            processing_status="processing",
            estimated_completion_time=datetime.utcnow() + timedelta(minutes=5),
            feedback_id=str(result.feedback_id) if result else None,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Unexpected error submitting feedback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/sessions/{session_id}/feedback-state",
    response_model=FeedbackStateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Session or feedback state not found"},
    }
)
async def get_feedback_state(
    session_id: UUID,
    phase: Optional[int] = Query(None, ge=1, le=7, description="Specific phase to get state for"),
    db: AsyncSession = Depends(get_db_session),
) -> FeedbackStateResponse:
    """Get current feedback state for a session"""

    try:
        # Get the current feedback state
        query = select(PhaseFeedbackState).where(
            PhaseFeedbackState.session_id == session_id
        )

        if phase is not None:
            query = query.where(PhaseFeedbackState.phase == phase)
        else:
            # Get the most recent feedback state
            query = query.order_by(PhaseFeedbackState.phase.desc())

        result = await db.execute(query)
        feedback_state = result.scalar_one_or_none()

        if not feedback_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback state not found"
            )

        return FeedbackStateResponse(
            session_id=str(feedback_state.session_id),
            phase=feedback_state.phase,
            state=feedback_state.state,
            remaining_time_seconds=feedback_state.time_remaining_seconds(),
            feedback_started_at=feedback_state.feedback_started_at,
            feedback_timeout_at=feedback_state.feedback_timeout_at,
            feedback_received_at=feedback_state.feedback_received_at,
            preview_data=feedback_state.preview_data_dict,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting feedback state")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/sessions/{session_id}/preview/{phase}",
    response_model=PhasePreviewResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Session or preview not found"},
    }
)
async def get_phase_preview(
    session_id: UUID,
    phase: int = Path(..., ge=1, le=7, description="Phase number"),
    db: AsyncSession = Depends(get_db_session),
) -> PhasePreviewResponse:
    """Get preview data for a specific phase"""

    try:
        # Get feedback state with preview data
        query = select(PhaseFeedbackState).where(
            and_(
                PhaseFeedbackState.session_id == session_id,
                PhaseFeedbackState.phase == phase
            )
        )

        result = await db.execute(query)
        feedback_state = result.scalar_one_or_none()

        if not feedback_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preview not found for the specified session and phase"
            )

        # Get feedback options for this phase
        options_query = select(FeedbackOptionTemplate).where(
            and_(
                FeedbackOptionTemplate.phase == phase,
                FeedbackOptionTemplate.is_active == True
            )
        ).order_by(FeedbackOptionTemplate.display_order, FeedbackOptionTemplate.option_label)

        options_result = await db.execute(options_query)
        feedback_options = options_result.scalars().all()

        return PhasePreviewResponse(
            session_id=str(session_id),
            phase=phase,
            preview_data=feedback_state.preview_data_dict,
            quality_score=None,  # TODO: Get from phase results if available
            generated_at=feedback_state.feedback_started_at,
            feedback_options=[
                {
                    "id": str(option.id),
                    "phase": option.phase,
                    "option_key": option.option_key,
                    "option_label": option.option_label,
                    "option_description": option.option_description,
                    "option_category": option.option_category,
                    "display_order": option.display_order,
                    "is_active": option.is_active,
                }
                for option in feedback_options
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting phase preview")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/feedback-options/{phase}",
    response_model=FeedbackOptionsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_feedback_options(
    phase: int = Path(..., ge=1, le=7, description="Phase number"),
    category: Optional[str] = Query(None, description="Filter by option category"),
    only_active: bool = Query(True, description="Only return active options"),
    db: AsyncSession = Depends(get_db_session),
) -> FeedbackOptionsResponse:
    """Get available feedback options for a specific phase"""

    try:
        query = select(FeedbackOptionTemplate).where(
            FeedbackOptionTemplate.phase == phase
        )

        if only_active:
            query = query.where(FeedbackOptionTemplate.is_active == True)

        if category:
            query = query.where(FeedbackOptionTemplate.option_category == category)

        query = query.order_by(
            FeedbackOptionTemplate.display_order,
            FeedbackOptionTemplate.option_label
        )

        result = await db.execute(query)
        options = result.scalars().all()

        return FeedbackOptionsResponse(
            phase=phase,
            options=[
                {
                    "id": str(option.id),
                    "phase": option.phase,
                    "option_key": option.option_key,
                    "option_label": option.option_label,
                    "option_description": option.option_description,
                    "option_category": option.option_category,
                    "display_order": option.display_order,
                    "is_active": option.is_active,
                }
                for option in options
            ],
            total_count=len(options),
        )

    except Exception as e:
        logger.exception("Error getting feedback options")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/sessions/{session_id}/feedback-history",
    response_model=FeedbackHistoryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
    }
)
async def get_feedback_history(
    session_id: UUID,
    phase: Optional[int] = Query(None, ge=1, le=7, description="Filter by phase"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    db: AsyncSession = Depends(get_db_session),
) -> FeedbackHistoryResponse:
    """Get feedback history for a session"""

    try:
        # Check if session exists
        session_query = select(MangaSession).where(MangaSession.request_id == session_id)
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Get feedback history
        query = select(UserFeedbackHistory).where(
            UserFeedbackHistory.session_id == session.id
        )

        if phase is not None:
            query = query.where(UserFeedbackHistory.phase == phase)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()

        # Get paginated results
        query = query.order_by(UserFeedbackHistory.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        feedback_entries = result.scalars().all()

        return FeedbackHistoryResponse(
            session_id=str(session_id),
            feedback_entries=[
                UserFeedbackHistoryResponse(
                    id=str(entry.id),
                    session_id=str(entry.session_id),
                    phase=entry.phase,
                    feedback_type=entry.feedback_type,
                    feedback_data=entry.feedback_data_dict,
                    user_satisfaction_score=entry.user_satisfaction_score,
                    natural_language_input=entry.natural_language_input,
                    selected_options=entry.selected_options_list,
                    processing_time_ms=entry.processing_time_ms,
                    created_at=entry.created_at,
                    processing_completed_at=entry.processing_completed_at,
                    is_processed=entry.is_processed(),
                )
                for entry in feedback_entries
            ],
            total_count=total_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting feedback history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/status",
    response_model=HITLStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_hitl_status(
    db: AsyncSession = Depends(get_db_session),
) -> HITLStatusResponse:
    """Get HITL system status and configuration"""

    try:
        settings = get_settings()

        # Get active sessions count
        active_sessions_query = select(func.count()).where(
            MangaSession.status.in_(["running", "awaiting_feedback"])
        )
        active_sessions_result = await db.execute(active_sessions_query)
        active_sessions_count = active_sessions_result.scalar()

        # Get waiting feedback count
        waiting_feedback_query = select(func.count()).where(
            PhaseFeedbackState.state == "waiting"
        )
        waiting_feedback_result = await db.execute(waiting_feedback_query)
        waiting_feedback_count = waiting_feedback_result.scalar()

        return HITLStatusResponse(
            hitl_enabled=settings.hitl_enabled,
            feedback_timeout_minutes=settings.hitl_feedback_timeout_minutes,
            max_retry_attempts=settings.hitl_max_retry_attempts,
            default_quality_threshold=settings.hitl_default_quality_threshold,
            active_sessions_count=active_sessions_count,
            waiting_feedback_count=waiting_feedback_count,
        )

    except Exception as e:
        logger.exception("Error getting HITL status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )