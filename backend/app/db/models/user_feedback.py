from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False)
    phase = Column(Integer, nullable=False)
    feedback_type = Column(String(32), nullable=False, default="natural_language")
    payload = Column(JSON, nullable=False)
    sentiment_score = Column(Numeric(4, 2), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    session = relationship("MangaSession", back_populates="feedback_entries")
