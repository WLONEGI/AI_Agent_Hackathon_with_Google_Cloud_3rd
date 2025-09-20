from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserFeedbackHistory(Base):
    """User feedback history for HITL system"""

    __tablename__ = "user_feedback_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("manga_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    phase = Column(Integer, nullable=False)
    feedback_type = Column(String(50), nullable=False)  # approval, modification, skip
    feedback_data = Column(JSON, nullable=True)  # structured feedback data
    user_satisfaction_score = Column(Float, nullable=True)  # 1-5 rating
    natural_language_input = Column(Text, nullable=True)  # free text feedback
    selected_options = Column(ARRAY(String), nullable=True)  # selected feedback options
    processing_time_ms = Column(Integer, nullable=True)  # time to provide feedback
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processing_completed_at = Column(DateTime, nullable=True)  # when feedback was processed

    # Relationships
    session = relationship("MangaSession", back_populates="feedback_history")

    def __repr__(self) -> str:
        return f"<UserFeedbackHistory(session_id={self.session_id}, phase={self.phase}, type={self.feedback_type})>"

    @property
    def feedback_data_dict(self) -> Dict[str, Any]:
        """Get feedback data as dictionary"""
        return self.feedback_data or {}

    @property
    def selected_options_list(self) -> List[str]:
        """Get selected options as list"""
        return self.selected_options or []

    @property
    def processing_time_seconds(self) -> Optional[float]:
        """Get processing time in seconds"""
        if self.processing_time_ms is not None:
            return self.processing_time_ms / 1000.0
        return None

    def is_processed(self) -> bool:
        """Check if feedback has been processed"""
        return self.processing_completed_at is not None

    def is_positive_feedback(self) -> bool:
        """Check if feedback is positive (approval or high satisfaction)"""
        if self.feedback_type == "approval":
            return True
        if self.user_satisfaction_score is not None:
            return self.user_satisfaction_score >= 4.0
        return False