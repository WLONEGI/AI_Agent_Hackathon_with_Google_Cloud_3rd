from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
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
    request_id = Column(UUID(as_uuid=True), unique=True, nullable=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("manga_projects.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), nullable=False, default=MangaSessionStatus.QUEUED.value)
    title = Column(String(255), nullable=True)
    text = Column(Text, nullable=True)  # Made nullable for backward compatibility
    ai_auto_settings = Column(Boolean, nullable=False, default=True)
    feedback_mode = Column(JSON, nullable=True)
    options = Column(JSON, nullable=True)
    estimated_completion_time = Column(TIMESTAMP(timezone=True), nullable=True)
    actual_completion_time = Column(TIMESTAMP(timezone=True), nullable=True)
    current_phase = Column(Integer, nullable=True, default=0)
    total_phases = Column(Integer, nullable=True, default=5)
    error_message = Column(Text, nullable=True)
    websocket_channel = Column(String(255), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    session_metadata = Column(JSON, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    phase_results = relationship("PhaseResult", back_populates="session", cascade="all, delete-orphan")
    preview_versions = relationship("PreviewVersion", back_populates="session", cascade="all, delete-orphan")
    feedback_entries = relationship("UserFeedback", back_populates="session", cascade="all, delete-orphan")
    feedback_history = relationship("UserFeedbackHistory", back_populates="session", cascade="all, delete-orphan")
    feedback_states = relationship("PhaseFeedbackState", back_populates="session", cascade="all, delete-orphan")
    messages = relationship("SessionMessage", back_populates="session", cascade="all, delete-orphan")
    events = relationship("SessionEvent", back_populates="session", cascade="all, delete-orphan")
    user = relationship("UserAccount", back_populates="sessions")
    project = relationship("MangaProject", back_populates="sessions", foreign_keys=[project_id])
    projects = relationship("MangaProject", back_populates="session", foreign_keys="MangaProject.session_id")
