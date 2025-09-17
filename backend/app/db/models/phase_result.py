from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PhaseResult(Base):
    __tablename__ = "phase_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False)
    phase = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    content = Column(JSON, nullable=True)
    quality_score = Column(Numeric(4, 2), nullable=True)
    preview_version_id = Column(UUID(as_uuid=True), ForeignKey("preview_versions.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("MangaSession", back_populates="phase_results")
    preview_version = relationship("PreviewVersion", back_populates="phase_results")
