from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from enum import Enum


class MangaSessionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_FEEDBACK = "awaiting_feedback"
    COMPLETED = "completed"
    FAILED = "failed"


class MangaSession(Base):
    __tablename__ = "manga_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("manga_projects.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), nullable=False, default=MangaSessionStatus.QUEUED.value)
    current_phase = Column(Integer, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    session_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    phase_results = relationship("PhaseResult", back_populates="session", cascade="all, delete-orphan")
    preview_versions = relationship("PreviewVersion", back_populates="session", cascade="all, delete-orphan")
    feedback_entries = relationship("UserFeedback", back_populates="session", cascade="all, delete-orphan")
    user = relationship("UserAccount", back_populates="sessions")
    project = relationship("MangaProject", back_populates="sessions")
