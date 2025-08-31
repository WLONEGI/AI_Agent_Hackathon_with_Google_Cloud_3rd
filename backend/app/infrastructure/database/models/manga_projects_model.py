"""SQLAlchemy model for Manga Projects."""

from sqlalchemy import (
    Column, String, Integer, DateTime, Index, ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class MangaProjectsModel(Base):
    """SQLAlchemy model for manga projects."""
    
    __tablename__ = "manga_projects"
    
    # Primary key
    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to users
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Project information
    title = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    
    # Project data (stored as JSONB)
    metadata = Column(JSONB, nullable=True)  # Style, character count, genre, etc.
    settings = Column(JSONB, nullable=True)  # Generation settings
    
    # Project metrics
    total_pages = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For free users (30 days)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            status.in_(['draft', 'processing', 'completed', 'failed', 'archived']),
            name='check_project_status_valid'
        ),
        CheckConstraint(
            'total_pages IS NULL OR total_pages > 0',
            name='check_total_pages_positive'
        ),
        Index('idx_projects_user_id', 'user_id'),
        Index('idx_projects_status', 'status'),
        Index('idx_projects_created_at', 'created_at', postgresql_order='DESC'),
        Index('idx_projects_expires_at', 'expires_at', postgresql_where='expires_at IS NOT NULL'),
        Index('idx_projects_user_status_created', 'user_id', 'status', 'created_at', postgresql_order=['ASC', 'ASC', 'DESC']),
        # JSONB GIN index for metadata search
        Index('idx_projects_metadata_gin', 'metadata', postgresql_using='gin'),
        # Full-text search index for titles
        Index('idx_projects_title_fts', func.to_tsvector('japanese', 'title'), postgresql_using='gin'),
    )
    
    def __repr__(self) -> str:
        return f"<MangaProject(project_id='{self.project_id}', user_id='{self.user_id}', title='{self.title}', status='{self.status}')>"