from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base


class PreviewBranch(Base):
    __tablename__ = "preview_branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False)
    phase_number = Column(Integer, nullable=False)
    branch_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_main_branch = Column(Boolean, nullable=True)
    status = Column(String(20), nullable=True)
    parent_branch_id = Column(UUID(as_uuid=True), ForeignKey("preview_branches.id"), nullable=True)
    branch_depth = Column(Integer, nullable=True)
    child_count = Column(Integer, nullable=True)
    latest_version_id = Column(UUID(as_uuid=True), nullable=True)
    version_count = Column(Integer, nullable=True)
    quality_trend = Column(Float, nullable=True)
    user_satisfaction = Column(Float, nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    last_modified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    archived_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    session = relationship("MangaSession", back_populates="preview_branches")
    parent_branch = relationship("PreviewBranch", remote_side=[id], back_populates="child_branches")
    child_branches = relationship("PreviewBranch", back_populates="parent_branch")
    created_by = relationship("UserAccount", foreign_keys=[created_by_user_id], back_populates="created_branches")
    modified_by = relationship("UserAccount", foreign_keys=[last_modified_by], back_populates="modified_branches")
    interactive_changes = relationship("InteractiveChange", back_populates="branch")
    versions_extended = relationship("PreviewVersionExtended", back_populates="branch")