from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PreviewCacheMetadata(Base):
    __tablename__ = "preview_cache_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(255), nullable=False, unique=True)
    version_id = Column(UUID(as_uuid=True), ForeignKey("preview_versions.id", ondelete="CASCADE"), nullable=False)
    phase = Column(Integer, nullable=False)
    quality_level = Column(Integer, nullable=False)
    signed_url = Column(String(2048), nullable=False)
    content_type = Column(String(100), nullable=False, default="application/json")
    file_size = Column(Numeric(12, 0), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)

    preview_version = relationship("PreviewVersion", back_populates="cache_entry")
