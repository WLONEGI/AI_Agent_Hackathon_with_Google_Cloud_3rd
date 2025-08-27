"""SQLAlchemy model for Manga Session."""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, JSON,
    Index, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class MangaSessionModel(Base):
    """SQLAlchemy model for manga sessions."""
    
    __tablename__ = "manga_sessions"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User association
    user_id = Column(String(36), nullable=False, index=True)
    
    # Basic information
    title = Column(String(255), nullable=True)
    input_text = Column(Text, nullable=False)
    
    # Status and timestamps
    status = Column(String(50), nullable=False, default="pending", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Phase progress
    current_phase = Column(Integer, default=0, nullable=False)
    total_phases = Column(Integer, default=7, nullable=False)
    
    # Results and data (stored as JSON)
    phase_results = Column(JSON, nullable=True)
    quality_scores = Column(JSON, nullable=True)
    output_metadata = Column(JSON, nullable=True)
    
    # Quality metrics
    final_quality_score = Column(Float, nullable=True)
    total_processing_time = Column(Float, nullable=True)
    
    # Output URLs
    preview_url = Column(String(512), nullable=True)
    download_url = Column(String(512), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # HITL configuration
    hitl_enabled = Column(Boolean, default=True, nullable=False)
    feedback_sessions = Column(JSON, nullable=True)  # List of feedback session keys
    
    # Generation parameters (stored as JSON)
    generation_params = Column(JSON, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_manga_sessions_user_status', 'user_id', 'status'),
        Index('idx_manga_sessions_user_created', 'user_id', 'created_at'),
        Index('idx_manga_sessions_status_updated', 'status', 'updated_at'),
        Index('idx_manga_sessions_current_phase', 'current_phase'),
        Index('idx_manga_sessions_quality_score', 'final_quality_score'),
        Index('idx_manga_sessions_created_at', 'created_at'),
        Index('idx_manga_sessions_completed_at', 'completed_at'),
    )
    
    def __repr__(self) -> str:
        return f"<MangaSession(id='{self.id}', user_id='{self.user_id}', status='{self.status}')>"