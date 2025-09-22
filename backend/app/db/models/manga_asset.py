from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, BigInteger, Numeric, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class MangaAssetType:
    PDF = "pdf"
    WEBP = "webp"
    THUMBNAIL = "thumbnail"
    ARCHIVE = "archive"


class MangaAssetPhase:
    """Manga generation phase constants"""
    CONCEPT = 1
    STORY_STRUCTURE = 2
    CHARACTER_DESIGN = 3
    PANEL_LAYOUT = 4
    FINAL_RENDER = 5


class MangaAsset(Base):
    __tablename__ = "manga_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("manga_projects.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id", ondelete="SET NULL"), nullable=True)
    asset_type = Column(String(32), nullable=False)
    phase = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    content_type = Column(String(100), nullable=True)
    asset_metadata = Column(JSONB, nullable=True)
    quality_score = Column(Numeric(4, 2), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("MangaProject", back_populates="assets")
    session = relationship("MangaSession", back_populates="assets")
