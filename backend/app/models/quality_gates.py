"""Quality Gates database models for AI processing quality control."""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class QualityGateStatus(str, Enum):
    """Quality gate status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    PASSED = "passed"
    FAILED = "error"
    OVERRIDE_APPROVED = "override_approved"
    OVERRIDE_DENIED = "override_denied"
    SKIPPED = "skipped"


class QualityOverrideStatus(str, Enum):
    """Quality override status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class PhaseQualityGate(Base):
    """Individual phase quality gate tracking."""
    
    __tablename__ = "phase_quality_gates"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Session and phase reference
    session_id = Column(UUID(as_uuid=True), ForeignKey("manga_sessions.id"), nullable=False, index=True)
    phase_number = Column(Integer, nullable=False)
    phase_name = Column(String(100), nullable=False)
    
    # Quality gate configuration
    quality_threshold = Column(Float, nullable=False, default=0.7)
    is_critical_phase = Column(Boolean, default=False)
    max_retries = Column(Integer, default=3)
    
    # Quality assessment results
    quality_score = Column(Float, nullable=True)
    status = Column(String(50), default=QualityGateStatus.PENDING.value, index=True)
    retry_count = Column(Integer, default=0)
    
    # Processing metadata
    processing_time_ms = Column(Integer, nullable=True)
    assessment_details = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Override information
    override_applied = Column(Boolean, default=False)
    override_reason = Column(Text, nullable=True)
    override_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    override_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session = relationship("MangaSession", back_populates="quality_gates")
    override_requests = relationship("QualityOverrideRequest", back_populates="quality_gate", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<PhaseQualityGate {self.phase_number} - {self.status}>"
    
    @property
    def is_passed(self) -> bool:
        """Check if quality gate has passed."""
        return self.status in [QualityGateStatus.PASSED.value, QualityGateStatus.OVERRIDE_APPROVED.value]
    
    @property
    def requires_retry(self) -> bool:
        """Check if phase requires retry."""
        return (self.status == QualityGateStatus.FAILED.value and 
                self.retry_count < self.max_retries and
                self.is_critical_phase)


class QualityOverrideRequest(Base):
    """Quality gate override requests and management."""
    
    __tablename__ = "quality_override_requests"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Quality gate reference
    quality_gate_id = Column(UUID(as_uuid=True), ForeignKey("phase_quality_gates.id"), nullable=False, index=True)
    
    # Request details
    requested_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    override_reason = Column(Text, nullable=False)
    force_proceed = Column(Boolean, default=True)
    
    # Approval workflow
    status = Column(String(50), default=QualityOverrideStatus.PENDING.value, index=True)
    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Processing results
    next_phase_started = Column(Boolean, default=False)
    pipeline_continued = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    quality_gate = relationship("PhaseQualityGate", back_populates="override_requests")
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])
    
    def __repr__(self) -> str:
        return f"<QualityOverrideRequest {self.id} - {self.status}>"
    
    @property
    def is_expired(self) -> bool:
        """Check if override request has expired."""
        return self.expires_at and datetime.utcnow() > self.expires_at


class SystemQualityMetrics(Base):
    """System-wide quality metrics aggregation."""
    
    __tablename__ = "system_quality_metrics"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    metric_type = Column(String(50), nullable=False)  # daily, weekly, monthly
    
    # Phase-specific metrics
    phase_number = Column(Integer, nullable=True)  # null for system-wide metrics
    phase_name = Column(String(100), nullable=True)
    
    # Quality metrics
    total_sessions_processed = Column(Integer, default=0)
    average_quality_score = Column(Float, nullable=True)
    quality_gate_failure_rate = Column(Float, nullable=True)
    average_retry_count = Column(Float, nullable=True)
    override_request_rate = Column(Float, nullable=True)
    
    # Performance metrics
    average_processing_time_ms = Column(Integer, nullable=True)
    total_processing_time_ms = Column(Integer, nullable=True)
    
    # Detailed statistics
    quality_distribution = Column(JSONB, nullable=True)  # score buckets
    failure_reasons = Column(JSONB, nullable=True)       # error categorization
    retry_statistics = Column(JSONB, nullable=True)      # retry patterns
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<SystemQualityMetrics {self.metric_type} - {self.period_start.date()}>"


class QualityThreshold(Base):
    """Configurable quality thresholds per phase."""
    
    __tablename__ = "quality_thresholds"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Configuration
    phase_number = Column(Integer, nullable=False)
    phase_name = Column(String(100), nullable=False)
    
    # Threshold values
    minimum_acceptable = Column(Float, nullable=False, default=0.6)
    target_quality = Column(Float, nullable=False, default=0.7)
    excellence_threshold = Column(Float, nullable=False, default=0.9)
    
    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=2)
    is_critical_phase = Column(Boolean, default=False)
    
    # Adaptive thresholds
    enable_adaptive = Column(Boolean, default=False)
    adaptation_factor = Column(Float, default=0.1)
    
    # Metadata
    description = Column(Text, nullable=True)
    configuration_notes = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<QualityThreshold phase_{self.phase_number} - target_{self.target_quality}>"
    
    @property
    def threshold_config(self) -> dict:
        """Get threshold configuration as dictionary."""
        return {
            "minimum_acceptable": self.minimum_acceptable,
            "target_quality": self.target_quality,
            "excellence_threshold": self.excellence_threshold,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "is_critical_phase": self.is_critical_phase
        }