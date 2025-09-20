from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PhaseFeedbackState(Base):
    """Phase feedback state tracking for HITL system"""

    __tablename__ = "phase_feedback_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("manga_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    phase = Column(Integer, nullable=False)
    state = Column(String(50), nullable=False)  # waiting, received, processing, completed, timeout
    preview_data = Column(JSON, nullable=True)  # preview data for user
    feedback_started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    feedback_timeout_at = Column(DateTime, nullable=True)  # 30 minutes after start
    feedback_received_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    session = relationship("MangaSession", back_populates="feedback_states")

    # Constraints
    __table_args__ = (
        UniqueConstraint("session_id", "phase", name="uq_phase_feedback_states_session_phase"),
    )

    def __repr__(self) -> str:
        return f"<PhaseFeedbackState(session_id={self.session_id}, phase={self.phase}, state={self.state})>"

    @property
    def preview_data_dict(self) -> Dict[str, Any]:
        """Get preview data as dictionary"""
        return self.preview_data or {}

    def is_waiting(self) -> bool:
        """Check if state is waiting for feedback"""
        return self.state == "waiting"

    def is_completed(self) -> bool:
        """Check if feedback process is completed"""
        return self.state == "completed"

    def is_timeout(self) -> bool:
        """Check if feedback has timed out"""
        return self.state == "timeout"

    def has_received_feedback(self) -> bool:
        """Check if feedback has been received"""
        return self.feedback_received_at is not None

    def time_remaining_seconds(self) -> Optional[int]:
        """Get remaining time in seconds before timeout"""
        if not self.feedback_timeout_at:
            return None

        now = datetime.utcnow()
        if now >= self.feedback_timeout_at:
            return 0

        remaining = self.feedback_timeout_at - now
        return int(remaining.total_seconds())

    def time_elapsed_seconds(self) -> int:
        """Get elapsed time since feedback started"""
        now = datetime.utcnow()
        elapsed = now - self.feedback_started_at
        return int(elapsed.total_seconds())

    def set_timeout(self, timeout_minutes: int = 30) -> None:
        """Set timeout for feedback"""
        self.feedback_timeout_at = self.feedback_started_at + timedelta(minutes=timeout_minutes)

    def mark_received(self) -> None:
        """Mark feedback as received"""
        self.feedback_received_at = datetime.utcnow()
        self.state = "received"
        self.updated_at = datetime.utcnow()

    def mark_processing(self) -> None:
        """Mark feedback as being processed"""
        self.state = "processing"
        self.updated_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Mark feedback process as completed"""
        self.state = "completed"
        self.updated_at = datetime.utcnow()

    def mark_timeout(self) -> None:
        """Mark feedback as timed out"""
        self.state = "timeout"
        self.updated_at = datetime.utcnow()

    @classmethod
    def create_waiting_state(
        cls,
        session_id: UUID,
        phase: int,
        preview_data: Optional[Dict[str, Any]] = None,
        timeout_minutes: int = 30
    ) -> PhaseFeedbackState:
        """Create a new waiting feedback state"""
        state = cls(
            session_id=session_id,
            phase=phase,
            state="waiting",
            preview_data=preview_data,
            feedback_started_at=datetime.utcnow()  # Initialize with current time
        )
        state.set_timeout(timeout_minutes)
        return state