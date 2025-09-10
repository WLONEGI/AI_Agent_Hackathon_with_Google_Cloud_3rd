"""Manga generation models and schemas."""

from datetime import datetime
from typing import Optional, Dict, List, Any
from uuid import uuid4
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.core.database import Base


class GenerationStatus(str, Enum):
    """Generation status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    WAITING_FEEDBACK = "waiting_feedback"
    COMPLETED = "completed"
    FAILED = "error"
    CANCELLED = "cancelled"


class QualityLevel(str, Enum):
    """Quality level enumeration."""
    ULTRA_HIGH = "ultra_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    PREVIEW = "preview"


class MangaSession(Base):
    """Main manga generation session model."""
    
    __tablename__ = "manga_sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Session metadata
    title = Column(String(255), nullable=True)
    input_text = Column(Text, nullable=False)
    genre = Column(String(100), nullable=True)
    style = Column(String(100), default="standard")
    quality_level = Column(String(20), default=QualityLevel.HIGH.value)
    
    # Processing status
    status = Column(String(50), default=GenerationStatus.PENDING.value, index=True)
    current_phase = Column(Integer, default=0)
    total_phases = Column(Integer, default=7)
    
    # HITL settings
    hitl_enabled = Column(Boolean, default=True)
    auto_proceed = Column(Boolean, default=False)
    feedback_timeout_seconds = Column(Integer, default=300)  # 5 minutes
    
    # Results storage
    final_result = Column(JSONB, nullable=True)
    preview_url = Column(Text, nullable=True)
    download_url = Column(Text, nullable=True)
    
    # Performance metrics
    total_processing_time_ms = Column(Integer, nullable=True)
    total_feedback_count = Column(Integer, default=0)
    quality_score = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # user = relationship("User", back_populates="manga_sessions")
    phase_results = relationship("PhaseResult", back_populates="session", cascade="all, delete-orphan")
    preview_versions = relationship("PreviewVersion", back_populates="session", cascade="all, delete-orphan")
    feedbacks = relationship("UserFeedback", back_populates="session", cascade="all, delete-orphan")
    quality_gates = relationship("PhaseQualityGate", back_populates="session", cascade="all, delete-orphan")
    preview_branches = relationship("PreviewBranch", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<MangaSession {self.id} - {self.status}>"
    
    @property
    def is_active(self) -> bool:
        """Check if session is still active."""
        return self.status in [GenerationStatus.PROCESSING, GenerationStatus.WAITING_FEEDBACK]
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_phases == 0:
            return 0.0
        return (self.current_phase / self.total_phases) * 100


class PhaseResult(Base):
    """Individual phase execution results."""
    
    __tablename__ = "phase_results"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Session reference
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False, index=True)
    
    # Phase information
    phase_number = Column(Integer, nullable=False)
    phase_name = Column(String(100), nullable=False)
    
    # Input/Output data
    input_data = Column(JSONB, nullable=False, default={})
    output_data = Column(JSONB, nullable=False, default={})
    
    # Preview data
    preview_data = Column(JSONB, nullable=True)
    preview_image_urls = Column(ARRAY(Text), nullable=True)
    
    # Processing metadata
    processing_time_ms = Column(Integer, nullable=False)
    ai_model_used = Column(String(100), nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Feedback tracking
    feedback_count = Column(Integer, default=0)
    feedback_applied = Column(JSONB, nullable=True)
    
    # Status
    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session = relationship("MangaSession", back_populates="phase_results")
    
    def __repr__(self) -> str:
        return f"<PhaseResult {self.phase_number} - {self.phase_name}>"


class PreviewVersion(Base):
    """Preview version management for branching."""
    
    __tablename__ = "preview_versions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Session and phase reference
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False, index=True)
    phase_number = Column(Integer, nullable=False)
    
    # Version management
    version_number = Column(Integer, nullable=False)
    branch_from_version = Column(Integer, nullable=True)
    is_main_branch = Column(Boolean, default=True)
    
    # Preview data
    preview_data = Column(JSONB, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    
    # Quality settings
    quality_level = Column(String(20), default=QualityLevel.HIGH.value)
    
    # Metadata
    created_by = Column(String(50), default="system")  # system, user, feedback
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    session = relationship("MangaSession", back_populates="preview_versions")
    
    def __repr__(self) -> str:
        return f"<PreviewVersion {self.version_number} for phase {self.phase_number}>"


class UserFeedback(Base):
    """User feedback during HITL process."""
    
    __tablename__ = "user_feedbacks"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # References
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False, index=True)
    phase_number = Column(Integer, nullable=False)
    
    # Feedback content
    feedback_type = Column(String(50), nullable=False)  # text, selection, adjustment
    feedback_text = Column(Text, nullable=True)
    feedback_data = Column(JSONB, nullable=True)
    
    # Application status
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    result_after_application = Column(JSONB, nullable=True)
    
    # User rating
    satisfaction_score = Column(Integer, nullable=True)  # 1-5
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    session = relationship("MangaSession", back_populates="feedbacks")
    
    def __repr__(self) -> str:
        return f"<UserFeedback for phase {self.phase_number}>"


class GeneratedImage(Base):
    """Generated images storage and metadata."""
    
    __tablename__ = "generated_images"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # References
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False, index=True)
    phase_number = Column(Integer, nullable=False)
    scene_number = Column(Integer, nullable=False)
    
    # Image data
    image_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    cdn_url = Column(Text, nullable=True)
    
    # Generation metadata
    prompt_used = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=True)
    
    # Image properties
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    format = Column(String(10), default="png")
    size_bytes = Column(Integer, nullable=True)
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)
    nsfw_score = Column(Float, nullable=True)
    
    # Processing metadata
    generation_time_ms = Column(Integer, nullable=False)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self) -> str:
        return f"<GeneratedImage scene_{self.scene_number}>"