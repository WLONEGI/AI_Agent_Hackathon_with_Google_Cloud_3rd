from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserAccount(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(128), unique=True, nullable=False)
    google_id = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    account_type = Column(String(32), nullable=False, default="free")
    is_active = Column(Boolean, nullable=False, default=True)
    is_premium = Column(Boolean, nullable=False, default=False)
    subscription_tier = Column(String(32), nullable=False, default="free")
    daily_generation_count = Column(Integer, nullable=False, default=0)
    daily_limit_reset_at = Column(TIMESTAMP(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    firebase_claims = Column(JSON, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    projects = relationship("MangaProject", back_populates="user")
    sessions = relationship("MangaSession", back_populates="user")
    refresh_tokens = relationship("UserRefreshToken", back_populates="user", cascade="all, delete-orphan")
    interactive_changes = relationship("InteractiveChange", foreign_keys="InteractiveChange.user_id", back_populates="user")
    approved_changes = relationship("InteractiveChange", foreign_keys="InteractiveChange.approved_by_user_id", back_populates="approved_by")
    created_branches = relationship("PreviewBranch", foreign_keys="PreviewBranch.created_by_user_id", back_populates="created_by")
    modified_branches = relationship("PreviewBranch", foreign_keys="PreviewBranch.last_modified_by", back_populates="modified_by")
