"""SQLAlchemy model for Phase Result."""

from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, JSON,
    Index, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class PhaseResultModel(Base):
    """SQLAlchemy model for phase execution results."""
    
    __tablename__ = "phase_results"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Session association
    session_id = Column(String(36), ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Phase information
    phase_number = Column(Integer, nullable=False)
    phase_name = Column(String(100), nullable=False)
    
    # Execution status
    status = Column(String(50), nullable=False, default="pending", index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time = Column(Float, nullable=True)
    
    # Input and output data (stored as JSON)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    intermediate_results = Column(JSON, nullable=True)  # Array of intermediate results
    
    # Quality metrics (stored as JSON)
    quality_score = Column(JSON, nullable=True)
    validation_results = Column(JSON, nullable=True)
    
    # AI model information
    model_used = Column(String(100), nullable=True)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_cost_usd = Column(Float, default=0.0, nullable=False)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Performance metrics
    cpu_usage_percent = Column(Float, default=0.0, nullable=False)
    memory_usage_mb = Column(Float, default=0.0, nullable=False)
    api_call_count = Column(Integer, default=0, nullable=False)
    cache_hit_count = Column(Integer, default=0, nullable=False)
    
    # Metadata (stored as JSON)
    phase_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_phase_results_session_phase', 'session_id', 'phase_number'),
        Index('idx_phase_results_session_status', 'session_id', 'status'),
        Index('idx_phase_results_phase_number', 'phase_number'),
        Index('idx_phase_results_status', 'status'),
        Index('idx_phase_results_processing_time', 'processing_time'),
        Index('idx_phase_results_cost', 'total_cost_usd'),
        Index('idx_phase_results_model', 'model_used'),
        Index('idx_phase_results_created_at', 'created_at'),
        Index('idx_phase_results_completed_at', 'completed_at'),
    )
    
    def __repr__(self) -> str:
        return f"<PhaseResult(id='{self.id}', session_id='{self.session_id}', phase={self.phase_number}, status='{self.status}')>"