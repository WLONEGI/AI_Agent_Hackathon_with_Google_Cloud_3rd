"""Preview Interactive database models for real-time preview editing and version management."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.core.database import Base


class ChangeType(str, Enum):
    """Interactive change type enumeration."""
    TEXT_EDIT = "text_edit"
    DRAG_DROP = "drag_drop"
    RESIZE = "resize"
    COLOR_CHANGE = "color_change"
    STYLE_CHANGE = "style_change"
    POSITION_CHANGE = "position_change"
    CONTENT_REPLACEMENT = "content_replacement"


class BranchStatus(str, Enum):
    """Branch status enumeration."""
    ACTIVE = "active"
    MERGED = "merged"
    ARCHIVED = "archived"
    DELETED = "deleted"


class PreviewBranch(Base):
    """Preview version branch management for branching and merging."""
    
    __tablename__ = "preview_branches"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Session reference
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False, index=True)
    phase_number = Column(Integer, nullable=False)
    
    # Branch metadata
    branch_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_main_branch = Column(Boolean, default=False)
    status = Column(String(20), default=BranchStatus.ACTIVE.value)
    
    # Branch hierarchy
    parent_branch_id = Column(UUID(as_uuid=True), ForeignKey("preview_branches.id"), nullable=True)
    branch_depth = Column(Integer, default=0)
    child_count = Column(Integer, default=0)
    
    # Version tracking
    latest_version_id = Column(UUID(as_uuid=True), nullable=True)
    version_count = Column(Integer, default=0)
    
    # Quality metrics
    quality_trend = Column(Float, nullable=True)  # Average quality improvement
    user_satisfaction = Column(Float, nullable=True)
    
    # User tracking
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    last_modified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session = relationship("MangaSession", back_populates="preview_branches")
    parent_branch = relationship("PreviewBranch", remote_side=[id])
    versions = relationship("PreviewVersionExtended", back_populates="branch", cascade="all, delete-orphan")
    interactive_changes = relationship("InteractiveChange", back_populates="branch", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    last_modified_by_user = relationship("User", foreign_keys=[last_modified_by])
    
    def __repr__(self) -> str:
        return f"<PreviewBranch {self.branch_name} - {self.status}>"
    
    @property
    def is_active(self) -> bool:
        """Check if branch is active."""
        return self.status == BranchStatus.ACTIVE.value


class PreviewVersionExtended(Base):
    """Extended preview version with enhanced branching and change tracking."""
    
    __tablename__ = "preview_versions_extended"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Session and phase reference
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False, index=True)
    phase_number = Column(Integer, nullable=False)
    
    # Branch reference
    branch_id = Column(UUID(as_uuid=True), ForeignKey("preview_branches.id"), nullable=False, index=True)
    
    # Version hierarchy
    version_number = Column(Integer, nullable=False)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("preview_versions_extended.id"), nullable=True)
    is_checkpoint = Column(Boolean, default=False)  # Major milestone versions
    
    # Preview data
    version_data = Column(JSONB, nullable=False)
    change_description = Column(Text, nullable=False)
    change_summary = Column(JSONB, nullable=True)  # Structured summary of changes
    
    # Interactive elements configuration
    interactive_elements = Column(JSONB, nullable=True, default={})
    enabled_features = Column(ARRAY(String), nullable=True)
    
    # Quality and preview settings
    quality_level = Column(Integer, default=3)  # 1-5
    quality_score = Column(Float, nullable=True)
    preview_urls = Column(JSONB, nullable=True, default={})
    thumbnail_url = Column(Text, nullable=True)
    
    # Generation metadata
    is_automatic = Column(Boolean, default=False)
    generation_method = Column(String(50), default="user_edit")  # user_edit, ai_suggestion, revert, merge
    generation_params = Column(JSONB, nullable=True)
    
    # Performance tracking
    generation_time_ms = Column(Integer, nullable=True)
    cache_status = Column(String(20), default="fresh")  # fresh, cached, expired
    
    # User tracking
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session = relationship("MangaSession")
    branch = relationship("PreviewBranch", back_populates="versions")
    parent_version = relationship("PreviewVersionExtended", remote_side=[id])
    interactive_changes = relationship("InteractiveChange", back_populates="version", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    
    def __repr__(self) -> str:
        return f"<PreviewVersionExtended {self.version_number} - {self.change_description[:50]}>"
    
    @property
    def full_version_id(self) -> str:
        """Get full version identifier with branch info."""
        return f"{self.branch.branch_name}:v{self.version_number}"


class InteractiveChange(Base):
    """Individual interactive changes made to preview elements."""
    
    __tablename__ = "interactive_changes"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # References
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False, index=True)
    version_id = Column(UUID(as_uuid=True), ForeignKey("preview_versions_extended.id"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("preview_branches.id"), nullable=False, index=True)
    
    # Change details
    element_id = Column(String(200), nullable=False, index=True)  # Element identifier (e.g., "concept.title")
    change_type = Column(String(50), nullable=False)
    
    # Change data
    previous_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=False)
    change_metadata = Column(JSONB, nullable=True, default={})
    
    # Change impact
    quality_impact = Column(Float, nullable=True)  # -1.0 to 1.0
    estimated_regeneration_time = Column(Float, nullable=True)  # seconds
    affected_elements = Column(ARRAY(String), nullable=True)
    
    # Application status
    applied_immediately = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=False)
    approved = Column(Boolean, default=True)
    
    # User tracking
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    applied_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    reverted_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session = relationship("MangaSession")
    version = relationship("PreviewVersionExtended", back_populates="interactive_changes")
    branch = relationship("PreviewBranch", back_populates="interactive_changes")
    user = relationship("User", foreign_keys=[user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    
    def __repr__(self) -> str:
        return f"<InteractiveChange {self.element_id} - {self.change_type}>"
    
    @property
    def is_reverted(self) -> bool:
        """Check if change has been reverted."""
        return self.reverted_at is not None


class PreviewCache(Base):
    """Preview data caching for performance optimization."""
    
    __tablename__ = "preview_cache"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Cache key and identification
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False, index=True)
    phase_number = Column(Integer, nullable=False)
    quality_level = Column(Integer, nullable=False)
    
    # Version reference
    version_id = Column(UUID(as_uuid=True), ForeignKey("preview_versions_extended.id"), nullable=True)
    
    # Cached data
    preview_data = Column(JSONB, nullable=False)
    preview_urls = Column(JSONB, nullable=True, default={})
    thumbnail_data = Column(JSONB, nullable=True)
    
    # Cache metadata
    content_hash = Column(String(64), nullable=False)  # SHA-256 hash for integrity
    content_type = Column(String(100), default="application/json")
    content_size = Column(Integer, nullable=True)
    
    # Performance data
    generation_time_ms = Column(Integer, nullable=True)
    compression_ratio = Column(Float, nullable=True)
    
    # Cache management
    hit_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("MangaSession")
    version = relationship("PreviewVersionExtended")
    
    def __repr__(self) -> str:
        return f"<PreviewCache {self.cache_key} - hits:{self.hit_count}>"
    
    @property
    def is_expired(self) -> bool:
        """Check if cache has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def ttl_seconds(self) -> float:
        """Get time-to-live in seconds."""
        if self.is_expired:
            return 0.0
        return (self.expires_at - datetime.utcnow()).total_seconds()


class PreviewAnalytics(Base):
    """Preview usage analytics and user behavior tracking."""
    
    __tablename__ = "preview_analytics"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Session reference
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Analytics event
    event_type = Column(String(50), nullable=False, index=True)  # view, edit, branch, revert, etc.
    event_data = Column(JSONB, nullable=True, default={})
    
    # Context
    phase_number = Column(Integer, nullable=True)
    version_id = Column(UUID(as_uuid=True), nullable=True)
    element_id = Column(String(200), nullable=True)
    
    # User behavior metrics
    interaction_duration_ms = Column(Integer, nullable=True)
    mouse_clicks = Column(Integer, default=0)
    keyboard_events = Column(Integer, default=0)
    scroll_events = Column(Integer, default=0)
    
    # Device and performance
    device_info = Column(JSONB, nullable=True)
    network_latency_ms = Column(Integer, nullable=True)
    render_time_ms = Column(Integer, nullable=True)
    
    # Satisfaction tracking
    user_satisfaction = Column(Integer, nullable=True)  # 1-5 scale
    feedback_text = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("MangaSession")
    user = relationship("User")
    
    def __repr__(self) -> str:
        return f"<PreviewAnalytics {self.event_type} - {self.created_at}>"