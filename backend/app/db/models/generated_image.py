from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False)
    phase = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=False)
    signed_url = Column(String(2048), nullable=True)
    image_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
