from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.models import (
    MangaSession,
    PhaseFeedbackState,
    UserFeedbackHistory,
)

logger = logging.getLogger(__name__)


class FeedbackSubmissionResult:
    """Result of feedback submission"""

    def __init__(
        self,
        feedback_id: str,
        processing_success: bool,
        quality_improvement: Optional[float] = None,
        processing_time_ms: int = 0,
        error_message: Optional[str] = None,
    ):
        self.feedback_id = feedback_id
        self.processing_success = processing_success
        self.quality_improvement = quality_improvement
        self.processing_time_ms = processing_time_ms
        self.error_message = error_message


class HITLService:
    """Service for handling Human-in-the-loop operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def submit_feedback(
        self,
        session_id: UUID,
        phase: int,
        feedback_type: str,
        selected_options: Optional[List[str]] = None,
        natural_language_input: Optional[str] = None,
        user_satisfaction_score: Optional[float] = None,
        processing_time_ms: Optional[int] = None,
    ) -> FeedbackSubmissionResult:
        """Submit user feedback for a session phase"""

        # Validate inputs
        if feedback_type not in ["approval", "modification", "skip"]:
            raise ValueError(f"Invalid feedback type: {feedback_type}")

        if phase < 1 or phase > 7:
            raise ValueError(f"Invalid phase number: {phase}")

        # Find the session
        session_query = select(MangaSession).where(MangaSession.request_id == session_id)
        session_result = await self.db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise FileNotFoundError(f"Session not found: {session_id}")

        # Find the feedback state
        feedback_state_query = select(PhaseFeedbackState).where(
            and_(
                PhaseFeedbackState.session_id == session.id,
                PhaseFeedbackState.phase == phase
            )
        )
        feedback_state_result = await self.db.execute(feedback_state_query)
        feedback_state = feedback_state_result.scalar_one_or_none()

        if not feedback_state:
            raise FileNotFoundError(f"Feedback state not found for session {session_id}, phase {phase}")

        # Check if feedback can be submitted
        if feedback_state.state != "waiting":
            raise RuntimeError(f"Cannot submit feedback. Current state: {feedback_state.state}")

        # Check if timeout has passed
        if feedback_state.feedback_timeout_at and datetime.utcnow() > feedback_state.feedback_timeout_at:
            feedback_state.mark_timeout()
            await self.db.flush()
            raise RuntimeError("Feedback timeout has expired")

        try:
            # Create feedback history entry
            feedback_history = UserFeedbackHistory(
                session_id=session.id,
                phase=phase,
                feedback_type=feedback_type,
                feedback_data={
                    "selected_options": selected_options or [],
                    "natural_language_input": natural_language_input,
                    "user_satisfaction_score": user_satisfaction_score,
                },
                user_satisfaction_score=user_satisfaction_score,
                natural_language_input=natural_language_input,
                selected_options=selected_options or [],
                processing_time_ms=processing_time_ms,
            )

            self.db.add(feedback_history)
            await self.db.flush()

            # Update feedback state
            feedback_state.mark_received()
            await self.db.flush()

            # Update session feedback count
            await self.db.execute(
                update(MangaSession)
                .where(MangaSession.id == session.id)
                .values(total_feedback_count=MangaSession.total_feedback_count + 1)
            )

            await self.db.commit()

            logger.info(
                f"Feedback submitted successfully: session={session_id}, phase={phase}, type={feedback_type}"
            )

            return FeedbackSubmissionResult(
                feedback_id=str(feedback_history.id),
                processing_success=True,
                processing_time_ms=processing_time_ms or 0,
            )

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Error submitting feedback: {e}")
            raise RuntimeError(f"Failed to submit feedback: {str(e)}")

    async def create_feedback_waiting_state(
        self,
        session_id: UUID,
        phase: int,
        preview_data: Optional[Dict[str, Any]] = None,
        timeout_minutes: Optional[int] = None,
    ) -> PhaseFeedbackState:
        """Create a new feedback waiting state"""

        timeout_minutes = timeout_minutes or self.settings.hitl_feedback_timeout_minutes

        # Find the session
        session_query = select(MangaSession).where(MangaSession.request_id == session_id)
        session_result = await self.db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise FileNotFoundError(f"Session not found: {session_id}")

        # Check if feedback state already exists for this phase
        existing_state_query = select(PhaseFeedbackState).where(
            and_(
                PhaseFeedbackState.session_id == session.id,
                PhaseFeedbackState.phase == phase
            )
        )
        existing_state_result = await self.db.execute(existing_state_query)
        existing_state = existing_state_result.scalar_one_or_none()

        if existing_state:
            # Update existing state
            existing_state.state = "waiting"
            existing_state.preview_data = preview_data
            existing_state.feedback_started_at = datetime.utcnow()
            existing_state.set_timeout(timeout_minutes)
            existing_state.feedback_received_at = None
            existing_state.updated_at = datetime.utcnow()
            feedback_state = existing_state
        else:
            # Create new feedback state
            feedback_state = PhaseFeedbackState.create_waiting_state(
                session_id=session.id,
                phase=phase,
                preview_data=preview_data,
                timeout_minutes=timeout_minutes,
            )
            self.db.add(feedback_state)

        # Update session status
        await self.db.execute(
            update(MangaSession)
            .where(MangaSession.id == session.id)
            .values(
                waiting_for_feedback=True,
                feedback_timeout_at=feedback_state.feedback_timeout_at,
            )
        )

        await self.db.flush()
        return feedback_state

    async def get_active_feedback_states(self) -> List[PhaseFeedbackState]:
        """Get all active feedback states (waiting or processing)"""

        query = select(PhaseFeedbackState).where(
            PhaseFeedbackState.state.in_(["waiting", "processing"])
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def check_and_handle_timeouts(self) -> int:
        """Check for and handle timed out feedback states"""

        now = datetime.utcnow()
        timeout_query = select(PhaseFeedbackState).where(
            and_(
                PhaseFeedbackState.state == "waiting",
                PhaseFeedbackState.feedback_timeout_at < now
            )
        )

        result = await self.db.execute(timeout_query)
        timed_out_states = result.scalars().all()

        timeout_count = 0
        for state in timed_out_states:
            state.mark_timeout()
            timeout_count += 1

            # Update session status
            await self.db.execute(
                update(MangaSession)
                .where(MangaSession.id == state.session_id)
                .values(
                    waiting_for_feedback=False,
                    feedback_timeout_at=None,
                )
            )

        if timeout_count > 0:
            await self.db.commit()
            logger.info(f"Handled {timeout_count} timed out feedback states")

        return timeout_count

    async def get_session_feedback_summary(self, session_id: UUID) -> Dict[str, Any]:
        """Get feedback summary for a session"""

        # Find the session
        session_query = select(MangaSession).where(MangaSession.request_id == session_id)
        session_result = await self.db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise FileNotFoundError(f"Session not found: {session_id}")

        # Get feedback history
        feedback_query = select(UserFeedbackHistory).where(
            UserFeedbackHistory.session_id == session.id
        )
        feedback_result = await self.db.execute(feedback_query)
        feedback_entries = feedback_result.scalars().all()

        if not feedback_entries:
            return {
                "session_id": str(session_id),
                "total_feedback_count": 0,
                "phases_with_feedback": [],
                "average_satisfaction_score": None,
                "feedback_types": {},
            }

        # Calculate statistics
        total_count = len(feedback_entries)
        phases_with_feedback = list(set(entry.phase for entry in feedback_entries))
        satisfaction_scores = [
            entry.user_satisfaction_score
            for entry in feedback_entries
            if entry.user_satisfaction_score is not None
        ]
        average_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else None

        feedback_types = {}
        for entry in feedback_entries:
            feedback_types[entry.feedback_type] = feedback_types.get(entry.feedback_type, 0) + 1

        return {
            "session_id": str(session_id),
            "total_feedback_count": total_count,
            "phases_with_feedback": sorted(phases_with_feedback),
            "average_satisfaction_score": average_satisfaction,
            "feedback_types": feedback_types,
            "completion_rate": len(phases_with_feedback) / 7.0,  # Assuming 7 phases
        }