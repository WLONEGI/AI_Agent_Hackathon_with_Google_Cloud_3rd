from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class MangaProjectStatus:
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MangaProject(Base):
    __tablename__ = "manga_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default=MangaProjectStatus.DRAFT)
    description = Column(Text, nullable=True)
    project_metadata = Column(JSON, nullable=True)
    settings = Column(JSON, nullable=True)
    total_pages = Column(Integer, nullable=True)
    style = Column(String(64), nullable=True)
    visibility = Column(String(32), nullable=False, default="private")
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserAccount", back_populates="projects")
    sessions = relationship("MangaSession", back_populates="project")
    assets = relationship("MangaAsset", back_populates="project", cascade="all, delete-orphan")
