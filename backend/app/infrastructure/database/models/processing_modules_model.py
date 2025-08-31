"""SQLAlchemy model for Processing Modules."""

from sqlalchemy import (
    Column, String, Integer, DateTime, Index, ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class ProcessingModulesModel(Base):
    """SQLAlchemy model for processing modules."""
    
    __tablename__ = "processing_modules"
    
    # Primary key
    module_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    request_id = Column(UUID(as_uuid=True), ForeignKey("generation_requests.request_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Module information
    module_number = Column(Integer, nullable=False)
    module_name = Column(String(50), nullable=False)
    
    # Processing status
    status = Column(String(20), nullable=False, default="pending")
    
    # Checkpoint data for recovery (stored as JSONB)
    checkpoint_data = Column(JSONB, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics
    duration_ms = Column(Integer, nullable=True)
    
    # Auto-generated timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            status.in_(['pending', 'processing', 'completed', 'failed', 'skipped']),
            name='check_module_status_valid'
        ),
        CheckConstraint(
            'module_number >= 1 AND module_number <= 7',
            name='check_module_number_range'
        ),
        CheckConstraint(
            module_name.in_([
                'concept_analysis',
                'character_visual', 
                'plot_structure',
                'name_generation',
                'scene_generation',
                'text_placement',
                'final_integration'
            ]),
            name='check_module_name_valid'
        ),
        CheckConstraint(
            'duration_ms IS NULL OR duration_ms >= 0',
            name='check_duration_non_negative'
        ),
        CheckConstraint(
            'started_at IS NULL OR completed_at IS NULL OR started_at <= completed_at',
            name='check_module_timestamps_logical_order'
        ),
        # Unique constraint for request-module combination
        Index('idx_modules_request_number', 'request_id', 'module_number', unique=True),
        Index('idx_modules_status', 'status'),
        Index('idx_modules_module_name', 'module_name'),
        Index('idx_modules_duration', 'duration_ms'),
        Index('idx_modules_created_at', 'created_at', postgresql_order='DESC'),
        # Performance monitoring index
        Index('idx_modules_performance', 'module_name', 'status', 'duration_ms'),
        # Processing queue optimization
        Index('idx_modules_pending', 'request_id', 'module_number', postgresql_where="status = 'pending'"),
    )
    
    def __repr__(self) -> str:
        return f"<ProcessingModule(module_id='{self.module_id}', request_id='{self.request_id}', module_number={self.module_number}, module_name='{self.module_name}', status='{self.status}')>"