from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base


class PreviewVersionExtended(Base):
    __tablename__ = "preview_versions_extended"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False)
    phase_number = Column(Integer, nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("preview_branches.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("preview_versions_extended.id"), nullable=True)
    is_checkpoint = Column(Boolean, nullable=True)
    version_data = Column(JSONB, nullable=False)
    change_description = Column(Text, nullable=False)
    change_summary = Column(JSONB, nullable=True)
    interactive_elements = Column(JSONB, nullable=True)
    enabled_features = Column(ARRAY(String), nullable=True)
    quality_level = Column(Integer, nullable=True)
    quality_score = Column(Integer, nullable=True)  # double precision mapped to Integer for simplicity
    preview_urls = Column(JSONB, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    is_automatic = Column(Boolean, nullable=True)
    generation_method = Column(String(50), nullable=True)
    generation_params = Column(JSONB, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)
    cache_status = Column(String(20), nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    approved_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    session = relationship("MangaSession", back_populates="preview_versions_extended")
    branch = relationship("PreviewBranch", back_populates="versions_extended")
    parent_version = relationship("PreviewVersionExtended", remote_side=[id], back_populates="child_versions")
    child_versions = relationship("PreviewVersionExtended", back_populates="parent_version")
    created_by = relationship("UserAccount", foreign_keys=[created_by_user_id])
    approved_by = relationship("UserAccount", foreign_keys=[approved_by_user_id])
    interactive_changes = relationship("InteractiveChange", back_populates="version_extended")