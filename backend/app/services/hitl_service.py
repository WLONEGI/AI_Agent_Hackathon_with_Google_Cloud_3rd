from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.models import (
    MangaSession,
    PhaseFeedbackState,
    UserFeedbackHistory,
)

# HITL Error Classes
class HITLError(Exception):
    """HITL基本エラークラス"""
    def __init__(self, message: str, error_code: str = "HITL_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class HITLSessionError(HITLError):
    """HITLセッション関連エラー"""
    def __init__(self, session_id: UUID, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "HITL_SESSION_ERROR", details)
        self.session_id = session_id

class HITLStateError(HITLError):
    """HITLステート管理エラー"""
    def __init__(self, session_id: UUID, current_state: str, expected_state: str, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid state transition: {current_state} -> {expected_state}"
        super().__init__(message, "HITL_STATE_ERROR", details)
        self.session_id = session_id
        self.current_state = current_state
        self.expected_state = expected_state

class HITLTimeoutError(HITLError):
    """HITLタイムアウトエラー"""
    def __init__(self, session_id: UUID, timeout_minutes: int, details: Optional[Dict[str, Any]] = None):
        message = f"HITL feedback timeout after {timeout_minutes} minutes"
        super().__init__(message, "HITL_TIMEOUT_ERROR", details)
        self.session_id = session_id
        self.timeout_minutes = timeout_minutes

class HITLDatabaseError(HITLError):
    """HITLデータベースエラー"""
    def __init__(self, operation: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Database error in {operation}: {message}", "HITL_DATABASE_ERROR", details)
        self.operation = operation

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

    async def _get_session_by_request_id_or_id(self, session_id: UUID) -> Optional[MangaSession]:
        """Get session by request_id if column exists, otherwise by id"""
        from sqlalchemy.exc import ProgrammingError, InvalidRequestError
        from asyncpg.exceptions import UndefinedColumnError

        try:
            # Try to query by request_id if the column exists
            session_query = select(MangaSession).where(MangaSession.request_id == session_id)
            session_result = await self.db.execute(session_query)
            return session_result.scalar_one_or_none()
        except (ProgrammingError, InvalidRequestError, UndefinedColumnError):
            # If request_id column doesn't exist, query by id instead
            logger.warning(f"request_id column not available, using id instead")
            session_query = select(MangaSession).where(MangaSession.id == session_id)
            session_result = await self.db.execute(session_query)
            return session_result.scalar_one_or_none()

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

        # Find the session - try request_id first, fallback to id if column doesn't exist
        session = await self._get_session_by_request_id_or_id(session_id)
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

        # Find the session - try request_id first, fallback to id if column doesn't exist
        session = await self._get_session_by_request_id_or_id(session_id)
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

        # Find the session - try request_id first, fallback to id if column doesn't exist
        session = await self._get_session_by_request_id_or_id(session_id)
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


class HITLSessionState(Enum):
    """HITL session states"""
    IDLE = "idle"
    WAITING_FEEDBACK = "waiting_feedback"
    PROCESSING_FEEDBACK = "processing_feedback"
    REGENERATING = "regenerating"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    ERROR = "error"


class HITLSessionContext:
    """Context for managing HITL session state"""

    def __init__(self, session_id: UUID, current_phase: int):
        self.session_id = session_id
        self.current_phase = current_phase
        self.state = HITLSessionState.IDLE
        self.iteration_count = 0
        self.max_iterations = 3
        self.feedback_data: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.started_at = datetime.utcnow()
        self.last_state_change = datetime.utcnow()

    def update_state(self, new_state: HITLSessionState, error_message: Optional[str] = None):
        """Update session state with timestamp"""
        self.state = new_state
        self.last_state_change = datetime.utcnow()
        if error_message:
            self.error_message = error_message

    def increment_iteration(self):
        """Increment iteration count and check limits"""
        self.iteration_count += 1
        return self.iteration_count <= self.max_iterations

    def can_continue(self) -> bool:
        """Check if session can continue processing"""
        return (
            self.state not in [HITLSessionState.ERROR, HITLSessionState.TIMEOUT] and
            self.iteration_count < self.max_iterations
        )


class HITLStateManager:
    """Enhanced state manager for HITL workflows"""

    def __init__(self, hitl_service: HITLService):
        self.hitl_service = hitl_service
        self.db = hitl_service.db
        self.active_sessions: Dict[UUID, HITLSessionContext] = {}

    async def start_hitl_session(self, session_id: UUID, phase: int, preview_data: Optional[Dict[str, Any]] = None) -> HITLSessionContext:
        """Start a new HITL session for a phase with error handling"""

        # Create session context
        context = HITLSessionContext(session_id, phase)
        
        try:
            # Store context early for error recovery
            self.active_sessions[session_id] = context

            # Create feedback waiting state with error handling
            try:
                await self.hitl_service.create_feedback_waiting_state(
                    session_id=session_id,
                    phase=phase,
                    preview_data=preview_data,
                    timeout_minutes=30
                )
            except Exception as db_error:
                raise HITLDatabaseError(
                    operation="create_feedback_waiting_state",
                    message=str(db_error),
                    details={"session_id": str(session_id), "phase": phase}
                )

            context.update_state(HITLSessionState.WAITING_FEEDBACK)
            logger.info(f"Started HITL session for session={session_id}, phase={phase}")

            return context

        except HITLDatabaseError:
            # Re-raise database errors
            raise
        except Exception as e:
            # Handle unexpected errors
            error_details = {
                "session_id": str(session_id),
                "phase": phase,
                "error_type": type(e).__name__
            }
            context.update_state(HITLSessionState.ERROR, str(e))
            logger.error(f"Failed to start HITL session: {e}", extra=error_details)
            
            raise HITLSessionError(
                session_id=session_id,
                message=f"Failed to start HITL session: {str(e)}",
                details=error_details
            )

    async def process_feedback_received(self, session_id: UUID, feedback_data: Dict[str, Any]) -> bool:
        """Process received feedback and determine next action with error handling"""

        context = self.active_sessions.get(session_id)
        if not context:
            raise HITLSessionError(
                session_id=session_id,
                message="No active HITL session found",
                details={"available_sessions": list(self.active_sessions.keys())}
            )

        if context.state != HITLSessionState.WAITING_FEEDBACK:
            raise HITLStateError(
                session_id=session_id,
                current_state=context.state.value,
                expected_state=HITLSessionState.WAITING_FEEDBACK.value,
                details={"feedback_data": feedback_data}
            )

        try:
            context.feedback_data = feedback_data
            context.update_state(HITLSessionState.PROCESSING_FEEDBACK)

            feedback_type = feedback_data.get("feedback_type")
            
            # Validate feedback type
            valid_types = ["approval", "modification", "skip"]
            if feedback_type not in valid_types:
                raise HITLError(
                    message=f"Invalid feedback type: {feedback_type}",
                    error_code="HITL_INVALID_FEEDBACK_TYPE",
                    details={"valid_types": valid_types, "received_type": feedback_type}
                )

            if feedback_type == "approval":
                # Feedback approved, complete the session
                context.update_state(HITLSessionState.COMPLETED)
                logger.info(f"HITL session {session_id} approved and completed")
                return True

            elif feedback_type == "modification":
                # Check iteration limits
                if not context.increment_iteration():
                    error_message = f"Maximum iterations exceeded ({context.max_iterations})"
                    context.update_state(HITLSessionState.ERROR, error_message)
                    logger.warning(f"HITL session {session_id} exceeded max iterations")
                    
                    raise HITLError(
                        message=error_message,
                        error_code="HITL_MAX_ITERATIONS_EXCEEDED",
                        details={
                            "max_iterations": context.max_iterations,
                            "current_iteration": context.iteration_count
                        }
                    )

                # Process modification feedback
                context.update_state(HITLSessionState.REGENERATING)
                logger.info(f"HITL session {session_id} processing modifications, iteration {context.iteration_count}")
                return True

            elif feedback_type == "skip":
                # Skip this phase, complete session
                context.update_state(HITLSessionState.COMPLETED)
                logger.info(f"HITL session {session_id} skipped and completed")
                return True

        except HITLError:
            # Re-raise HITL-specific errors
            raise
        except Exception as e:
            error_details = {
                "session_id": str(session_id),
                "feedback_data": feedback_data,
                "error_type": type(e).__name__
            }
            context.update_state(HITLSessionState.ERROR, str(e))
            logger.error(f"Error processing feedback for session {session_id}: {e}", extra=error_details)
            
            raise HITLSessionError(
                session_id=session_id,
                message=f"Failed to process feedback: {str(e)}",
                details=error_details
            )

    async def handle_regeneration_complete(self, session_id: UUID, regeneration_success: bool, new_preview_data: Optional[Dict[str, Any]] = None) -> bool:
        """Handle completion of regeneration process with error handling"""

        context = self.active_sessions.get(session_id)
        if not context:
            raise HITLSessionError(
                session_id=session_id,
                message="No active HITL session found for regeneration completion",
                details={"available_sessions": list(self.active_sessions.keys())}
            )

        if context.state != HITLSessionState.REGENERATING:
            raise HITLStateError(
                session_id=session_id,
                current_state=context.state.value,
                expected_state=HITLSessionState.REGENERATING.value,
                details={
                    "regeneration_success": regeneration_success,
                    "new_preview_data": new_preview_data is not None
                }
            )

        try:
            if not regeneration_success:
                error_message = "Regeneration failed"
                context.update_state(HITLSessionState.ERROR, error_message)
                logger.error(f"Regeneration failed for session {session_id}")
                
                raise HITLError(
                    message=error_message,
                    error_code="HITL_REGENERATION_FAILED",
                    details={"session_id": str(session_id), "phase": context.current_phase}
                )

            # Create new feedback waiting state for next iteration with error handling
            try:
                await self.hitl_service.create_feedback_waiting_state(
                    session_id=session_id,
                    phase=context.current_phase,
                    preview_data=new_preview_data,
                    timeout_minutes=30
                )
            except Exception as db_error:
                raise HITLDatabaseError(
                    operation="create_feedback_waiting_state_after_regeneration",
                    message=str(db_error),
                    details={
                        "session_id": str(session_id),
                        "phase": context.current_phase,
                        "iteration": context.iteration_count
                    }
                )

            context.update_state(HITLSessionState.WAITING_FEEDBACK)
            logger.info(f"HITL session {session_id} ready for next feedback iteration {context.iteration_count}")

            return True

        except (HITLError, HITLDatabaseError):
            # Re-raise HITL-specific errors
            raise
        except Exception as e:
            error_details = {
                "session_id": str(session_id),
                "regeneration_success": regeneration_success,
                "error_type": type(e).__name__
            }
            context.update_state(HITLSessionState.ERROR, str(e))
            logger.error(f"Error handling regeneration completion for session {session_id}: {e}", extra=error_details)
            
            raise HITLSessionError(
                session_id=session_id,
                message=f"Failed to handle regeneration completion: {str(e)}",
                details=error_details
            )

    async def handle_timeout(self, session_id: UUID) -> None:
        """Handle feedback timeout with error handling"""

        context = self.active_sessions.get(session_id)
        if not context:
            # セッションが見つからない場合は警告ログのみ（タイムアウトは正常な終了ケース）
            logger.warning(f"HITL session {session_id} not found for timeout handling")
            return

        try:
            # コンテキスト状態をタイムアウトに変更
            context.update_state(HITLSessionState.TIMEOUT)
            logger.warning(f"HITL session {session_id} timed out")

            # データベースでのタイムアウト処理
            try:
                await self.hitl_service.check_and_handle_timeouts()
            except Exception as db_error:
                # データベースエラーはログ出力のみ（タイムアウトセッションのクリーンアップに失敗）
                logger.error(f"Database timeout handling failed for session {session_id}: {db_error}")
                
                # HITLTimeoutErrorとして記録するが、例外は再発生させない
                raise HITLTimeoutError(
                    session_id=session_id,
                    timeout_minutes=30,  # デフォルトタイムアウト時間
                    details={
                        "database_error": str(db_error),
                        "phase": context.current_phase,
                        "iteration_count": context.iteration_count
                    }
                )

        except HITLTimeoutError:
            # HITLTimeoutErrorは再発生させずにログのみ
            logger.error(f"Timeout error details recorded for session {session_id}")
        except Exception as e:
            # 予期しないエラーは記録するが、タイムアウト処理は継続
            error_details = {
                "session_id": str(session_id),
                "phase": context.current_phase,
                "error_type": type(e).__name__
            }
            logger.error(f"Unexpected error during timeout handling for session {session_id}: {e}", extra=error_details)

    async def cleanup_session(self, session_id: UUID) -> None:
        """Clean up completed or failed session"""

        context = self.active_sessions.pop(session_id, None)
        if context:
            logger.info(f"Cleaned up HITL session {session_id}, final state: {context.state}")

    async def get_session_status(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current status of HITL session"""

        context = self.active_sessions.get(session_id)
        if not context:
            return None

        return {
            "session_id": str(session_id),
            "phase": context.current_phase,
            "state": context.state.value,
            "iteration_count": context.iteration_count,
            "max_iterations": context.max_iterations,
            "can_continue": context.can_continue(),
            "started_at": context.started_at.isoformat(),
            "last_state_change": context.last_state_change.isoformat(),
            "error_message": context.error_message,
        }

    async def get_all_active_sessions(self) -> List[Dict[str, Any]]:
        """Get status of all active sessions"""

        return [
            await self.get_session_status(session_id)
            for session_id in self.active_sessions.keys()
        ]

    async def force_cleanup_stale_sessions(self, max_age_hours: int = 24) -> int:
        """Force cleanup of stale sessions older than max_age_hours"""

        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleanup_count = 0

        stale_sessions = [
            session_id for session_id, context in self.active_sessions.items()
            if context.started_at < cutoff_time
        ]

        for session_id in stale_sessions:
            await self.cleanup_session(session_id)
            cleanup_count += 1

        logger.info(f"Cleaned up {cleanup_count} stale HITL sessions")
        return cleanup_count