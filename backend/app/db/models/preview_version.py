from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PreviewVersion(Base):
    __tablename__ = "preview_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False)
    phase = Column(Integer, nullable=False)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("preview_versions.id", ondelete="SET NULL"), nullable=True)
    version_data = Column(JSON, nullable=True)
    change_description = Column(String(255), nullable=True)
    quality_level = Column(Integer, nullable=True)
    quality_score = Column(Numeric(4, 2), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    session = relationship("MangaSession", back_populates="preview_versions")
    parent_version = relationship("PreviewVersion", remote_side=[id], backref="children")
    phase_results = relationship("PhaseResult", back_populates="preview_version")
    cache_entry = relationship("PreviewCacheMetadata", back_populates="preview_version", uselist=False)
