"""SQLAlchemy model for Generated Content."""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, JSON, LargeBinary,
    Index, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class GeneratedContentModel(Base):
    """SQLAlchemy model for generated content."""
    
    __tablename__ = "generated_content"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Session association
    session_id = Column(String(36), ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    phase_number = Column(Integer, nullable=False)
    phase_result_id = Column(String(36), ForeignKey("phase_results.id", ondelete="SET NULL"), nullable=True)
    
    # Content properties
    content_type = Column(String(50), nullable=False, index=True)  # text, image, dialogue, etc.
    content_format = Column(String(50), nullable=False)  # json, png, jpeg, etc.
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Content data
    content_data = Column(JSON, nullable=True)  # For structured data
    content_text = Column(Text, nullable=True)  # For text content
    content_binary = Column(LargeBinary, nullable=True)  # For binary data (images, etc.)
    content_url = Column(String(512), nullable=True)  # For external storage
    content_size_bytes = Column(Integer, default=0, nullable=False)
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for deduplication
    
    # Generation metadata
    generated_by = Column(String(100), nullable=False)  # AI model or agent name
    generation_prompt = Column(Text, nullable=True)
    generation_params = Column(JSON, nullable=True)
    
    # Status and versioning
    status = Column(String(50), nullable=False, default="draft", index=True)
    version = Column(Integer, default=1, nullable=False)
    parent_content_id = Column(String(36), ForeignKey("generated_content.id", ondelete="SET NULL"), nullable=True)
    
    # Quality and validation
    quality_score = Column(JSON, nullable=True)  # QualityScore as JSON
    validation_results = Column(JSON, nullable=True)
    auto_approved = Column(Boolean, default=False, nullable=False)
    
    # Human feedback
    hitl_feedback = Column(JSON, nullable=True)
    feedback_count = Column(Integer, default=0, nullable=False)
    approval_score = Column(Float, nullable=True)
    
    # Content relationships (stored as JSON arrays)
    related_content_ids = Column(JSON, nullable=True)  # Array of related content IDs
    dependencies = Column(JSON, nullable=True)  # Array of dependency content IDs
    tags = Column(JSON, nullable=True)  # Array of tags
    
    # Performance metrics
    generation_time_seconds = Column(Float, nullable=True)
    processing_cost_usd = Column(Float, default=0.0, nullable=False)
    storage_cost_usd = Column(Float, default=0.0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata (stored as JSON)
    metadata = Column(JSON, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_generated_content_session_phase', 'session_id', 'phase_number'),
        Index('idx_generated_content_session_type', 'session_id', 'content_type'),
        Index('idx_generated_content_type_status', 'content_type', 'status'),
        Index('idx_generated_content_status', 'status'),
        Index('idx_generated_content_hash', 'content_hash'),
        Index('idx_generated_content_generated_by', 'generated_by'),
        Index('idx_generated_content_quality', 'approval_score'),
        Index('idx_generated_content_cost', 'processing_cost_usd'),
        Index('idx_generated_content_size', 'content_size_bytes'),
        Index('idx_generated_content_created_at', 'created_at'),
        Index('idx_generated_content_approved_at', 'approved_at'),
        Index('idx_generated_content_finalized_at', 'finalized_at'),
        Index('idx_generated_content_parent', 'parent_content_id'),
        Index('idx_generated_content_version', 'version'),
    )
    
    def __repr__(self) -> str:
        return f"<GeneratedContent(id='{self.id}', session_id='{self.session_id}', type='{self.content_type}', status='{self.status}')>"