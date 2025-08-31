"""SQLAlchemy model for Generation Requests."""

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, Index, ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class GenerationRequestsModel(Base):
    """SQLAlchemy model for generation requests."""
    
    __tablename__ = "generation_requests"
    
    # Primary key
    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    project_id = Column(UUID(as_uuid=True), ForeignKey("manga_projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Request data
    input_text = Column(Text, nullable=False)
    request_settings = Column(JSONB, nullable=False, default=lambda: {})
    
    # Processing status
    status = Column(String(20), nullable=False, default="queued")
    current_module = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Auto-generated timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            status.in_(['queued', 'processing', 'completed', 'failed', 'cancelled']),
            name='check_request_status_valid'
        ),
        CheckConstraint(
            'current_module >= 0 AND current_module <= 7',
            name='check_current_module_range'
        ),
        CheckConstraint(
            'retry_count >= 0',
            name='check_retry_count_non_negative'
        ),
        CheckConstraint(
            'started_at IS NULL OR completed_at IS NULL OR started_at <= completed_at',
            name='check_timestamps_logical_order'
        ),
        Index('idx_requests_project_id', 'project_id'),
        Index('idx_requests_user_id', 'user_id'),
        Index('idx_requests_status', 'status'),
        Index('idx_requests_current_module', 'current_module'),
        Index('idx_requests_created_at', 'created_at', postgresql_order='DESC'),
        Index('idx_requests_status_created', 'status', 'created_at', postgresql_order=['ASC', 'DESC']),
        # Queue processing optimization
        Index('idx_requests_queue', 'status', 'created_at', postgresql_where="status = 'queued'"),
        # Active requests monitoring
        Index('idx_requests_active', 'user_id', 'created_at', postgresql_where="status IN ('queued', 'processing')", postgresql_order=['ASC', 'DESC']),
    )
    
    def __repr__(self) -> str:
        return f"<GenerationRequest(request_id='{self.request_id}', project_id='{self.project_id}', status='{self.status}', current_module={self.current_module})>"