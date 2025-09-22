from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base


class InteractiveChange(Base):
    __tablename__ = "interactive_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False)
    version_id = Column(UUID(as_uuid=True), ForeignKey("preview_versions_extended.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("preview_branches.id"), nullable=False)
    element_id = Column(String(200), nullable=False)
    change_type = Column(String(50), nullable=False)
    previous_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=False)
    change_metadata = Column(JSONB, nullable=True)
    quality_impact = Column(Float, nullable=True)
    estimated_regeneration_time = Column(Float, nullable=True)
    affected_elements = Column(ARRAY(String), nullable=True)
    applied_immediately = Column(Boolean, nullable=True)
    requires_approval = Column(Boolean, nullable=True)
    approved = Column(Boolean, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    applied_at = Column(TIMESTAMP(timezone=True), nullable=False)
    reverted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    approved_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    session = relationship("MangaSession", back_populates="interactive_changes")
    user = relationship("UserAccount", foreign_keys=[user_id], back_populates="interactive_changes")
    approved_by = relationship("UserAccount", foreign_keys=[approved_by_user_id], back_populates="approved_changes")
    branch = relationship("PreviewBranch", back_populates="interactive_changes")
    version_extended = relationship("PreviewVersionExtended", back_populates="interactive_changes")