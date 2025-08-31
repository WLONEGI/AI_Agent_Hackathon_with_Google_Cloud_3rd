"""SQLAlchemy model for Preview Versions - Phase 2 Preview System Implementation."""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, JSON,
    Index, ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class PreviewVersionModel(Base):
    """
    SQLAlchemy model for preview versions - HITL interactive preview system.
    
    This model stores versioned preview data for each phase of manga generation,
    enabling users to view and provide feedback on intermediate results.
    
    Complies with 06.データベース設計書.md specification.
    """
    
    __tablename__ = "preview_versions"
    
    # Primary key
    version_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key relationships
    request_id = Column(String(36), nullable=False, index=True)  # FK to generation_requests
    parent_version_id = Column(String(36), nullable=True, index=True)  # Self-referencing FK for version tree
    
    # Phase information
    phase = Column(Integer, nullable=False, index=True)  # Phase number (1-7)
    
    # Version data (JSONB for flexible content storage)
    version_data = Column(JSON, nullable=False)  # Preview content data
    
    # Version metadata
    change_description = Column(Text, nullable=True)  # Description of changes from parent
    quality_level = Column(Integer, nullable=False, default=1)  # Quality level (1-5)
    quality_score = Column(Float, nullable=True)  # Calculated quality score (0.0-1.0)
    
    # Version status
    is_active = Column(Boolean, nullable=False, default=True)  # Is this version active
    is_final = Column(Boolean, nullable=False, default=False)  # Is this the final version for phase
    
    # Branching information
    branch_name = Column(String(100), nullable=True)  # Optional branch name for organization
    merge_status = Column(String(20), nullable=True, default="pending")  # pending|merged|discarded
    
    # File references (for generated assets)
    asset_urls = Column(JSON, nullable=True)  # URLs to generated images/files
    thumbnail_url = Column(String(500), nullable=True)  # Quick preview thumbnail
    
    # User interaction metadata
    view_count = Column(Integer, nullable=False, default=0)  # Number of times viewed
    feedback_count = Column(Integer, nullable=False, default=0)  # Number of feedback interactions
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Performance metadata
    generation_time_ms = Column(Integer, nullable=True)  # Time taken to generate this version
    file_size_bytes = Column(Integer, nullable=True)  # Total size of associated files
    
    # Indexes for performance
    __table_args__ = (
        # Composite index for common queries
        Index('idx_preview_versions_request_phase', 'request_id', 'phase'),
        Index('idx_preview_versions_parent_child', 'parent_version_id', 'version_id'),
        Index('idx_preview_versions_active', 'request_id', 'phase', 'is_active'),
        Index('idx_preview_versions_final', 'request_id', 'phase', 'is_final'),
        Index('idx_preview_versions_created', 'created_at'),
        
        # GIN index for JSONB data
        Index('idx_preview_versions_data_gin', 'version_data', postgresql_using='gin'),
        Index('idx_preview_versions_assets_gin', 'asset_urls', postgresql_using='gin'),
        
        # Constraints
        CheckConstraint('phase >= 1 AND phase <= 7', name='ck_preview_versions_phase_range'),
        CheckConstraint('quality_level >= 1 AND quality_level <= 5', name='ck_preview_versions_quality_level'),
        CheckConstraint('quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0)', 
                       name='ck_preview_versions_quality_score'),
        CheckConstraint('view_count >= 0', name='ck_preview_versions_view_count'),
        CheckConstraint('feedback_count >= 0', name='ck_preview_versions_feedback_count'),
        CheckConstraint('generation_time_ms IS NULL OR generation_time_ms >= 0', 
                       name='ck_preview_versions_generation_time'),
        CheckConstraint('file_size_bytes IS NULL OR file_size_bytes >= 0', 
                       name='ck_preview_versions_file_size'),
        CheckConstraint("merge_status IN ('pending', 'merged', 'discarded')", 
                       name='ck_preview_versions_merge_status'),
        
        # Unique constraint for final versions per phase
        UniqueConstraint('request_id', 'phase', 'is_final', 
                        name='uq_preview_versions_final_per_phase',
                        postgresql_where="is_final = true")
    )
    
    def __repr__(self):
        return (f"<PreviewVersionModel(version_id='{self.version_id}', "
                f"request_id='{self.request_id}', phase={self.phase}, "
                f"quality_level={self.quality_level}, "
                f"is_active={self.is_active}, is_final={self.is_final})>")


class PreviewInteractionModel(Base):
    """
    SQLAlchemy model for preview interactions - User feedback on preview versions.
    
    This model tracks all user interactions with preview versions,
    including feedback, modifications, and approval actions.
    
    Complies with 06.データベース設計書.md specification.
    """
    
    __tablename__ = "preview_interactions"
    
    # Primary key
    interaction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key relationships
    version_id = Column(String(36), nullable=False, index=True)  # FK to preview_versions
    user_id = Column(String(36), nullable=False, index=True)  # FK to users
    
    # Element identification
    element_id = Column(String(100), nullable=False)  # ID of the element being modified
    element_type = Column(String(50), nullable=False)  # Type of element (text, image, layout, etc.)
    
    # Change information
    change_type = Column(String(50), nullable=False)  # Type of change (edit, move, delete, style, etc.)
    change_data = Column(JSON, nullable=False)  # Detailed change data
    
    # Change metadata
    change_description = Column(Text, nullable=True)  # Human-readable description of change
    confidence_score = Column(Float, nullable=True)  # AI confidence in change (0.0-1.0)
    
    # Interaction context
    interaction_type = Column(String(30), nullable=False, default="modification")  # modification|approval|rejection
    session_id = Column(String(36), nullable=True)  # Optional session grouping
    
    # Position/coordinates (for spatial changes)
    position_x = Column(Float, nullable=True)  # X coordinate
    position_y = Column(Float, nullable=True)  # Y coordinate
    position_data = Column(JSON, nullable=True)  # Additional positioning data
    
    # Approval workflow
    status = Column(String(20), nullable=False, default="pending")  # pending|approved|rejected|applied
    reviewed_by = Column(String(36), nullable=True)  # User ID who reviewed this change
    reviewed_at = Column(DateTime(timezone=True), nullable=True)  # Review timestamp
    
    # Timestamps
    applied_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Performance tracking
    processing_time_ms = Column(Integer, nullable=True)  # Time to process this interaction
    
    # Indexes for performance
    __table_args__ = (
        # Composite indexes for common queries
        Index('idx_preview_interactions_version_user', 'version_id', 'user_id'),
        Index('idx_preview_interactions_version_element', 'version_id', 'element_id'),
        Index('idx_preview_interactions_user_applied', 'user_id', 'applied_at'),
        Index('idx_preview_interactions_status', 'status'),
        Index('idx_preview_interactions_session', 'session_id'),
        Index('idx_preview_interactions_type', 'interaction_type', 'change_type'),
        
        # GIN index for JSONB data
        Index('idx_preview_interactions_change_data_gin', 'change_data', postgresql_using='gin'),
        Index('idx_preview_interactions_position_gin', 'position_data', postgresql_using='gin'),
        
        # Partial index for pending interactions
        Index('idx_preview_interactions_pending', 'version_id', 'status', 
              postgresql_where="status = 'pending'"),
        
        # Constraints
        CheckConstraint('confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)', 
                       name='ck_preview_interactions_confidence'),
        CheckConstraint("change_type IN ('edit', 'move', 'delete', 'style', 'add', 'replace', 'transform')", 
                       name='ck_preview_interactions_change_type'),
        CheckConstraint("interaction_type IN ('modification', 'approval', 'rejection', 'comment')", 
                       name='ck_preview_interactions_interaction_type'),
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'applied')", 
                       name='ck_preview_interactions_status'),
        CheckConstraint('processing_time_ms IS NULL OR processing_time_ms >= 0', 
                       name='ck_preview_interactions_processing_time'),
        CheckConstraint("element_type IN ('text', 'image', 'layout', 'character', 'background', 'effect', 'dialogue')", 
                       name='ck_preview_interactions_element_type')
    )
    
    def __repr__(self):
        return (f"<PreviewInteractionModel(interaction_id='{self.interaction_id}', "
                f"version_id='{self.version_id}', element_id='{self.element_id}', "
                f"change_type='{self.change_type}', status='{self.status}')>")


class PreviewQualitySettingsModel(Base):
    """
    SQLAlchemy model for preview quality settings - User-specific quality preferences.
    
    This model stores quality settings and preferences for preview generation,
    allowing users to customize preview quality vs speed trade-offs.
    
    Complies with 06.データベース設計書.md specification.
    """
    
    __tablename__ = "preview_quality_settings"
    
    # Primary key
    setting_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User reference
    user_id = Column(String(36), nullable=False, unique=True, index=True)  # FK to users
    
    # Device capability assessment
    device_capability = Column(Float, nullable=False, default=1.0)  # Device capability score (0.1-2.0)
    bandwidth_estimate = Column(Float, nullable=True)  # Estimated bandwidth (Mbps)
    
    # Quality preferences
    preferred_quality = Column(Integer, nullable=False, default=3)  # Preferred quality level (1-5)
    max_quality = Column(Integer, nullable=False, default=5)  # Maximum quality level
    auto_adjust_quality = Column(Boolean, nullable=False, default=True)  # Auto-adjust based on performance
    
    # Performance preferences
    max_generation_time_seconds = Column(Integer, nullable=False, default=30)  # Maximum generation time
    preferred_resolution = Column(String(20), nullable=False, default="1080p")  # 720p|1080p|1440p|4k
    enable_caching = Column(Boolean, nullable=False, default=True)  # Enable result caching
    
    # Advanced settings
    preview_format_preference = Column(String(20), nullable=False, default="webp")  # webp|jpg|png
    enable_progressive_loading = Column(Boolean, nullable=False, default=True)  # Progressive image loading
    enable_thumbnails = Column(Boolean, nullable=False, default=True)  # Generate thumbnails
    
    # AI processing preferences
    ai_enhancement_level = Column(Integer, nullable=False, default=2)  # AI enhancement level (0-3)
    enable_smart_cropping = Column(Boolean, nullable=False, default=True)  # Smart cropping for previews
    enable_color_optimization = Column(Boolean, nullable=False, default=True)  # Color optimization
    
    # Feedback preferences
    enable_realtime_preview = Column(Boolean, nullable=False, default=True)  # Real-time preview updates
    feedback_sensitivity = Column(Float, nullable=False, default=0.5)  # Feedback sensitivity (0.1-1.0)
    auto_apply_suggestions = Column(Boolean, nullable=False, default=False)  # Auto-apply AI suggestions
    
    # Performance tracking
    average_generation_time = Column(Float, nullable=True)  # Average generation time for this user
    last_performance_update = Column(DateTime(timezone=True), nullable=True)  # Last performance assessment
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes and constraints
    __table_args__ = (
        # Constraints
        CheckConstraint('device_capability >= 0.1 AND device_capability <= 2.0', 
                       name='ck_preview_quality_device_capability'),
        CheckConstraint('bandwidth_estimate IS NULL OR bandwidth_estimate >= 0', 
                       name='ck_preview_quality_bandwidth'),
        CheckConstraint('preferred_quality >= 1 AND preferred_quality <= 5', 
                       name='ck_preview_quality_preferred'),
        CheckConstraint('max_quality >= 1 AND max_quality <= 5', 
                       name='ck_preview_quality_max'),
        CheckConstraint('max_generation_time_seconds > 0', 
                       name='ck_preview_quality_max_time'),
        CheckConstraint("preferred_resolution IN ('720p', '1080p', '1440p', '4k')", 
                       name='ck_preview_quality_resolution'),
        CheckConstraint("preview_format_preference IN ('webp', 'jpg', 'png', 'avif')", 
                       name='ck_preview_quality_format'),
        CheckConstraint('ai_enhancement_level >= 0 AND ai_enhancement_level <= 3', 
                       name='ck_preview_quality_ai_level'),
        CheckConstraint('feedback_sensitivity >= 0.1 AND feedback_sensitivity <= 1.0', 
                       name='ck_preview_quality_sensitivity'),
        CheckConstraint('average_generation_time IS NULL OR average_generation_time >= 0', 
                       name='ck_preview_quality_avg_time'),
        CheckConstraint('preferred_quality <= max_quality', 
                       name='ck_preview_quality_levels')
    )
    
    def __repr__(self):
        return (f"<PreviewQualitySettingsModel(setting_id='{self.setting_id}', "
                f"user_id='{self.user_id}', preferred_quality={self.preferred_quality}, "
                f"device_capability={self.device_capability})>")