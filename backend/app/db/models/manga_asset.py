from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class MangaAssetType:
    PDF = "pdf"
    WEBP = "webp"
    THUMBNAIL = "thumbnail"
    ARCHIVE = "archive"


class MangaAsset(Base):
    __tablename__ = "manga_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("manga_projects.id", ondelete="CASCADE"), nullable=False)
    asset_type = Column(String(32), nullable=False)
    storage_path = Column(String(512), nullable=False)
    signed_url = Column(String(2048), nullable=True)
    asset_metadata = Column(JSON, nullable=True)
    size_bytes = Column(Numeric(16, 0), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("MangaProject", back_populates="assets")
