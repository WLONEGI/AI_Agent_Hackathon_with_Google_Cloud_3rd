"""
Domain entities for Preview System - Phase 2 Preview System Implementation.

This module contains domain entities for the HITL preview system,
including preview versions, interactions, and quality settings.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class PreviewStatus(Enum):
    """Preview version status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    FINAL = "final"
    ARCHIVED = "archived"


class InteractionType(Enum):
    """Interaction type enumeration."""
    MODIFICATION = "modification"
    APPROVAL = "approval" 
    REJECTION = "rejection"
    COMMENT = "comment"


class InteractionStatus(Enum):
    """Interaction status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


class ChangeType(Enum):
    """Change type enumeration."""
    EDIT = "edit"
    MOVE = "move"
    DELETE = "delete"
    STYLE = "style"
    ADD = "add"
    REPLACE = "replace"
    TRANSFORM = "transform"


class ElementType(Enum):
    """Element type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    LAYOUT = "layout"
    CHARACTER = "character"
    BACKGROUND = "background"
    EFFECT = "effect"
    DIALOGUE = "dialogue"


@dataclass
class PreviewVersionEntity:
    """
    Domain entity for preview versions.
    
    Represents a versioned preview of manga generation results
    that users can view and provide feedback on.
    """
    version_id: UUID
    request_id: UUID
    parent_version_id: Optional[UUID]
    phase: int
    version_data: Dict[str, Any]
    change_description: Optional[str] = None
    quality_level: int = 1
    quality_score: Optional[float] = None
    is_active: bool = True
    is_final: bool = False
    branch_name: Optional[str] = None
    merge_status: str = "pending"
    asset_urls: Optional[Dict[str, Any]] = None
    thumbnail_url: Optional[str] = None
    view_count: int = 0
    feedback_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    generation_time_ms: Optional[int] = None
    file_size_bytes: Optional[int] = None
    
    def __post_init__(self):
        """Validate entity after initialization."""
        if self.phase < 1 or self.phase > 7:
            raise ValueError("Phase must be between 1 and 7")
        
        if self.quality_level < 1 or self.quality_level > 5:
            raise ValueError("Quality level must be between 1 and 5")
        
        if self.quality_score is not None and (self.quality_score < 0.0 or self.quality_score > 1.0):
            raise ValueError("Quality score must be between 0.0 and 1.0")
        
        if self.view_count < 0:
            raise ValueError("View count cannot be negative")
        
        if self.feedback_count < 0:
            raise ValueError("Feedback count cannot be negative")
        
        if not self.version_data:
            raise ValueError("Version data cannot be empty")
    
    def increment_view_count(self) -> int:
        """Increment and return the new view count."""
        self.view_count += 1
        return self.view_count
    
    def increment_feedback_count(self) -> int:
        """Increment and return the new feedback count."""
        self.feedback_count += 1
        return self.feedback_count
    
    def set_final(self) -> None:
        """Mark this version as final."""
        self.is_final = True
        self.is_active = True
    
    def set_active(self, active: bool) -> None:
        """Set the active status of this version."""
        self.is_active = active
    
    def has_parent(self) -> bool:
        """Check if this version has a parent."""
        return self.parent_version_id is not None
    
    def get_branch_path(self) -> str:
        """Get the branch path for this version."""
        return f"{self.request_id}/{self.phase}/{self.branch_name or 'main'}"
    
    def calculate_complexity_score(self) -> float:
        """Calculate complexity score based on version data."""
        if not self.version_data:
            return 0.0
        
        # Simple complexity calculation based on data size and structure
        data_size = len(str(self.version_data))
        nested_levels = self._count_nested_levels(self.version_data)
        
        # Normalize complexity score (0.0 - 1.0)
        complexity = min(1.0, (data_size / 10000.0) + (nested_levels / 10.0))
        return complexity
    
    def _count_nested_levels(self, data: Any, current_level: int = 0) -> int:
        """Count nested levels in data structure."""
        if isinstance(data, dict):
            if not data:
                return current_level
            return max(self._count_nested_levels(v, current_level + 1) for v in data.values())
        elif isinstance(data, list):
            if not data:
                return current_level
            return max(self._count_nested_levels(item, current_level + 1) for item in data)
        else:
            return current_level


@dataclass
class PreviewInteractionEntity:
    """
    Domain entity for preview interactions.
    
    Represents user interactions with preview versions,
    including feedback, modifications, and approval actions.
    """
    interaction_id: UUID
    version_id: UUID
    user_id: UUID
    element_id: str
    element_type: str  # ElementType enum value
    change_type: str  # ChangeType enum value
    change_data: Dict[str, Any]
    change_description: Optional[str] = None
    confidence_score: Optional[float] = None
    interaction_type: str = "modification"  # InteractionType enum value
    session_id: Optional[UUID] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_data: Optional[Dict[str, Any]] = None
    status: str = "pending"  # InteractionStatus enum value
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None
    
    def __post_init__(self):
        """Validate entity after initialization."""
        if self.confidence_score is not None and (self.confidence_score < 0.0 or self.confidence_score > 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        if not self.element_id:
            raise ValueError("Element ID cannot be empty")
        
        if not self.change_data:
            raise ValueError("Change data cannot be empty")
        
        # Validate enum values
        try:
            ElementType(self.element_type)
        except ValueError:
            raise ValueError(f"Invalid element type: {self.element_type}")
        
        try:
            ChangeType(self.change_type)
        except ValueError:
            raise ValueError(f"Invalid change type: {self.change_type}")
        
        try:
            InteractionType(self.interaction_type)
        except ValueError:
            raise ValueError(f"Invalid interaction type: {self.interaction_type}")
        
        try:
            InteractionStatus(self.status)
        except ValueError:
            raise ValueError(f"Invalid status: {self.status}")
    
    def is_pending(self) -> bool:
        """Check if interaction is pending."""
        return self.status == InteractionStatus.PENDING.value
    
    def is_approved(self) -> bool:
        """Check if interaction is approved."""
        return self.status == InteractionStatus.APPROVED.value
    
    def is_applied(self) -> bool:
        """Check if interaction is applied."""
        return self.status == InteractionStatus.APPLIED.value
    
    def approve(self, reviewed_by: UUID) -> None:
        """Approve this interaction."""
        self.status = InteractionStatus.APPROVED.value
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.utcnow()
    
    def reject(self, reviewed_by: UUID) -> None:
        """Reject this interaction."""
        self.status = InteractionStatus.REJECTED.value
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.utcnow()
    
    def apply(self) -> None:
        """Mark interaction as applied."""
        self.status = InteractionStatus.APPLIED.value
        if not self.applied_at:
            self.applied_at = datetime.utcnow()
    
    def has_position(self) -> bool:
        """Check if interaction has position data."""
        return self.position_x is not None and self.position_y is not None
    
    def get_position_tuple(self) -> Optional[tuple]:
        """Get position as tuple."""
        if self.has_position():
            return (self.position_x, self.position_y)
        return None
    
    def calculate_impact_score(self) -> float:
        """Calculate impact score of this interaction."""
        # Base score from change type
        change_weights = {
            ChangeType.DELETE.value: 0.9,
            ChangeType.REPLACE.value: 0.8,
            ChangeType.TRANSFORM.value: 0.7,
            ChangeType.ADD.value: 0.6,
            ChangeType.EDIT.value: 0.5,
            ChangeType.STYLE.value: 0.3,
            ChangeType.MOVE.value: 0.2
        }
        
        base_score = change_weights.get(self.change_type, 0.5)
        
        # Adjust based on confidence
        if self.confidence_score is not None:
            base_score *= self.confidence_score
        
        # Adjust based on element type importance
        element_weights = {
            ElementType.LAYOUT.value: 1.2,
            ElementType.CHARACTER.value: 1.1,
            ElementType.TEXT.value: 1.0,
            ElementType.DIALOGUE.value: 1.0,
            ElementType.IMAGE.value: 0.9,
            ElementType.BACKGROUND.value: 0.7,
            ElementType.EFFECT.value: 0.6
        }
        
        element_weight = element_weights.get(self.element_type, 1.0)
        
        return min(1.0, base_score * element_weight)


@dataclass
class PreviewQualitySettingsEntity:
    """
    Domain entity for preview quality settings.
    
    Represents user-specific quality preferences and device capabilities
    for preview generation optimization.
    """
    setting_id: UUID
    user_id: UUID
    device_capability: float = 1.0
    bandwidth_estimate: Optional[float] = None
    preferred_quality: int = 3
    max_quality: int = 5
    auto_adjust_quality: bool = True
    max_generation_time_seconds: int = 30
    preferred_resolution: str = "1080p"
    enable_caching: bool = True
    preview_format_preference: str = "webp"
    enable_progressive_loading: bool = True
    enable_thumbnails: bool = True
    ai_enhancement_level: int = 2
    enable_smart_cropping: bool = True
    enable_color_optimization: bool = True
    enable_realtime_preview: bool = True
    feedback_sensitivity: float = 0.5
    auto_apply_suggestions: bool = False
    average_generation_time: Optional[float] = None
    last_performance_update: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate entity after initialization."""
        if self.device_capability < 0.1 or self.device_capability > 2.0:
            raise ValueError("Device capability must be between 0.1 and 2.0")
        
        if self.preferred_quality < 1 or self.preferred_quality > 5:
            raise ValueError("Preferred quality must be between 1 and 5")
        
        if self.max_quality < 1 or self.max_quality > 5:
            raise ValueError("Max quality must be between 1 and 5")
        
        if self.preferred_quality > self.max_quality:
            raise ValueError("Preferred quality cannot exceed max quality")
        
        if self.max_generation_time_seconds <= 0:
            raise ValueError("Max generation time must be positive")
        
        if self.ai_enhancement_level < 0 or self.ai_enhancement_level > 3:
            raise ValueError("AI enhancement level must be between 0 and 3")
        
        if self.feedback_sensitivity < 0.1 or self.feedback_sensitivity > 1.0:
            raise ValueError("Feedback sensitivity must be between 0.1 and 1.0")
        
        valid_resolutions = ["720p", "1080p", "1440p", "4k"]
        if self.preferred_resolution not in valid_resolutions:
            raise ValueError(f"Resolution must be one of: {valid_resolutions}")
        
        valid_formats = ["webp", "jpg", "png", "avif"]
        if self.preview_format_preference not in valid_formats:
            raise ValueError(f"Format must be one of: {valid_formats}")
    
    def update_performance_metrics(self, generation_time: float) -> None:
        """Update performance metrics with new generation time."""
        if self.average_generation_time is None:
            self.average_generation_time = generation_time
        else:
            # Exponential moving average with alpha = 0.3
            self.average_generation_time = (0.7 * self.average_generation_time + 
                                         0.3 * generation_time)
        
        self.last_performance_update = datetime.utcnow()
    
    def get_recommended_quality(self, current_load: float = 1.0) -> int:
        """Get recommended quality level based on settings and current load."""
        if not self.auto_adjust_quality:
            return self.preferred_quality
        
        # Adjust quality based on device capability and system load
        adjusted_capability = self.device_capability / current_load
        
        if adjusted_capability >= 1.5:
            return min(self.max_quality, 5)
        elif adjusted_capability >= 1.2:
            return min(self.max_quality, 4)
        elif adjusted_capability >= 0.8:
            return min(self.max_quality, 3)
        elif adjusted_capability >= 0.5:
            return min(self.max_quality, 2)
        else:
            return 1
    
    def should_use_progressive_loading(self) -> bool:
        """Determine if progressive loading should be used."""
        return (self.enable_progressive_loading and 
                self.device_capability < 1.5 and
                self.preferred_resolution in ["1440p", "4k"])
    
    def get_timeout_for_quality(self, quality_level: int) -> int:
        """Get timeout appropriate for quality level."""
        # Scale timeout based on quality level
        quality_multiplier = quality_level / 3.0  # Normalize to 3 (medium quality)
        return int(self.max_generation_time_seconds * quality_multiplier)
    
    def estimate_generation_time(self, complexity_score: float = 0.5) -> float:
        """Estimate generation time for given complexity."""
        base_time = self.average_generation_time or 15.0  # Default 15 seconds
        
        # Adjust for quality level
        quality_factor = self.preferred_quality / 3.0
        
        # Adjust for complexity
        complexity_factor = 0.5 + complexity_score
        
        # Adjust for device capability
        device_factor = 1.5 / self.device_capability
        
        return base_time * quality_factor * complexity_factor * device_factor