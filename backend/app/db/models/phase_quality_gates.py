from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base


class PhaseQualityGate(Base):
    __tablename__ = "phase_quality_gates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False)
    phase_number = Column(Integer, nullable=False)
    phase_name = Column(String(100), nullable=False)
    quality_threshold = Column(Float, nullable=False)
    is_critical_phase = Column(Boolean, nullable=True)
    max_retries = Column(Integer, nullable=True)
    quality_score = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)
    retry_count = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    assessment_details = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    override_applied = Column(Boolean, nullable=True)
    override_reason = Column(Text, nullable=True)
    override_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    override_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    session = relationship("MangaSession", back_populates="quality_gates")
    override_by = relationship("UserAccount", foreign_keys=[override_by_user_id])
    override_requests = relationship("QualityOverrideRequest", back_populates="quality_gate")