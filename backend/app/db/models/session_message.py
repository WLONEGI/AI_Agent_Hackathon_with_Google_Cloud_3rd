from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base


class MessageType(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


class SessionMessage(Base):
    __tablename__ = "session_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False)
    message_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    phase = Column(Integer, nullable=True)  # Optional phase association
    message_metadata = Column(JSON, nullable=True, default=dict)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("MangaSession", back_populates="messages")