"""
Preview System Commands - Phase 2 Preview System Implementation.

This module contains all commands for preview system operations
including version management, interactions, and quality settings.

Implements Command pattern for preview system operations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.application.commands.base_command import AbstractCommand
from app.application.dto.preview_dto import (
    PreviewVersionCreateDTO,
    PreviewVersionUpdateDTO,
    PreviewInteractionCreateDTO,
    PreviewQualitySettingsCreateDTO,
    PreviewQualitySettingsUpdateDTO
)


# ===== Preview Version Commands =====

@dataclass(kw_only=True)
class CreatePreviewVersionCommand(AbstractCommand):
    """
    Command to create a new preview version.
    
    Creates a new preview version for a generation request phase,
    optionally branching from a parent version.
    """
    request_id: UUID
    phase: int
    version_data: Dict[str, Any]
    parent_version_id: Optional[UUID] = None
    change_description: Optional[str] = None
    quality_level: int = 1
    branch_name: Optional[str] = None
    asset_urls: Optional[Dict[str, Any]] = None
    thumbnail_url: Optional[str] = None
    generation_time_ms: Optional[int] = None
    file_size_bytes: Optional[int] = None
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.request_id:
            errors.append("request_id is required")
        
        if not (1 <= self.phase <= 7):
            errors.append("phase must be between 1 and 7")
        
        if not self.version_data:
            errors.append("version_data is required and cannot be empty")
        
        if not (1 <= self.quality_level <= 5):
            errors.append("quality_level must be between 1 and 5")
        
        if self.generation_time_ms is not None and self.generation_time_ms < 0:
            errors.append("generation_time_ms must be non-negative")
        
        if self.file_size_bytes is not None and self.file_size_bytes < 0:
            errors.append("file_size_bytes must be non-negative")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class UpdatePreviewVersionCommand(AbstractCommand):
    """
    Command to update an existing preview version.
    
    Updates version data, metadata, and status information
    for an existing preview version.
    """
    version_id: UUID
    version_data: Optional[Dict[str, Any]] = None
    change_description: Optional[str] = None
    quality_level: Optional[int] = None
    quality_score: Optional[float] = None
    is_active: Optional[bool] = None
    is_final: Optional[bool] = None
    branch_name: Optional[str] = None
    merge_status: Optional[str] = None
    asset_urls: Optional[Dict[str, Any]] = None
    thumbnail_url: Optional[str] = None
    generation_time_ms: Optional[int] = None
    file_size_bytes: Optional[int] = None
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.version_id:
            errors.append("version_id is required")
        
        if self.quality_level is not None and not (1 <= self.quality_level <= 5):
            errors.append("quality_level must be between 1 and 5")
        
        if self.quality_score is not None and not (0.0 <= self.quality_score <= 1.0):
            errors.append("quality_score must be between 0.0 and 1.0")
        
        if self.merge_status is not None and self.merge_status not in ["pending", "merged", "discarded"]:
            errors.append("merge_status must be one of: pending, merged, discarded")
        
        if self.generation_time_ms is not None and self.generation_time_ms < 0:
            errors.append("generation_time_ms must be non-negative")
        
        if self.file_size_bytes is not None and self.file_size_bytes < 0:
            errors.append("file_size_bytes must be non-negative")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class SetFinalVersionCommand(AbstractCommand):
    """
    Command to set a version as the final version for its phase.
    
    Marks a specific version as final, unsetting any other
    final versions in the same phase of the same request.
    """
    version_id: UUID
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.version_id:
            errors.append("version_id is required")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class IncrementViewCountCommand(AbstractCommand):
    """
    Command to increment the view count for a preview version.
    
    Tracks how many times a preview version has been viewed
    for analytics and engagement metrics.
    """
    version_id: UUID
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.version_id:
            errors.append("version_id is required")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class DeletePreviewVersionCommand(AbstractCommand):
    """
    Command to delete a preview version and all its interactions.
    
    Permanently removes a preview version and all associated
    interaction data from the system.
    """
    version_id: UUID
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.version_id:
            errors.append("version_id is required")
        
        return self._create_validation_result(errors)


# ===== Preview Interaction Commands =====

@dataclass(kw_only=True)
class CreatePreviewInteractionCommand(AbstractCommand):
    """
    Command to create a new preview interaction.
    
    Records user feedback, modifications, or other interactions
    with a specific element in a preview version.
    """
    version_id: UUID
    user_id: UUID
    element_id: str
    element_type: str
    change_type: str
    change_data: Dict[str, Any]
    change_description: Optional[str] = None
    confidence_score: Optional[float] = None
    interaction_type: str = "modification"
    session_id: Optional[UUID] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_data: Optional[Dict[str, Any]] = None
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.version_id:
            errors.append("version_id is required")
        
        if not self.user_id:
            errors.append("user_id is required")
        
        if not self.element_id:
            errors.append("element_id is required")
        
        if not self.element_type:
            errors.append("element_type is required")
        
        if self.element_type not in ["text", "image", "layout", "character", "background", "effect", "dialogue"]:
            errors.append("element_type must be one of: text, image, layout, character, background, effect, dialogue")
        
        if not self.change_type:
            errors.append("change_type is required")
        
        if self.change_type not in ["edit", "move", "delete", "style", "add", "replace", "transform"]:
            errors.append("change_type must be one of: edit, move, delete, style, add, replace, transform")
        
        if not self.change_data:
            errors.append("change_data is required and cannot be empty")
        
        if self.confidence_score is not None and not (0.0 <= self.confidence_score <= 1.0):
            errors.append("confidence_score must be between 0.0 and 1.0")
        
        if self.interaction_type not in ["modification", "approval", "rejection", "comment"]:
            errors.append("interaction_type must be one of: modification, approval, rejection, comment")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class UpdateInteractionStatusCommand(AbstractCommand):
    """
    Command to update the status of a preview interaction.
    
    Updates interaction status through the approval workflow,
    tracking who reviewed and when.
    """
    interaction_id: UUID
    status: str
    reviewed_by: Optional[UUID] = None
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.interaction_id:
            errors.append("interaction_id is required")
        
        if not self.status:
            errors.append("status is required")
        
        if self.status not in ["pending", "approved", "rejected", "applied"]:
            errors.append("status must be one of: pending, approved, rejected, applied")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class ApplyInteractionsToVersionCommand(AbstractCommand):
    """
    Command to apply multiple interactions to create a new version.
    
    Processes approved interactions to generate a new preview version
    with the changes applied to the base version data.
    """
    version_id: UUID
    interaction_ids: List[UUID]
    new_version_description: Optional[str] = None
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.version_id:
            errors.append("version_id is required")
        
        if not self.interaction_ids:
            errors.append("interaction_ids is required and cannot be empty")
        
        if len(self.interaction_ids) == 0:
            errors.append("at least one interaction_id must be provided")
        
        return self._create_validation_result(errors)


# ===== Preview Quality Settings Commands =====

@dataclass(kw_only=True)
class CreateQualitySettingsCommand(AbstractCommand):
    """
    Command to create quality settings for a user.
    
    Initializes quality preferences and device capability settings
    for personalized preview generation optimization.
    """
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
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.user_id:
            errors.append("user_id is required")
        
        if not (0.1 <= self.device_capability <= 2.0):
            errors.append("device_capability must be between 0.1 and 2.0")
        
        if not (1 <= self.preferred_quality <= 5):
            errors.append("preferred_quality must be between 1 and 5")
        
        if not (1 <= self.max_quality <= 5):
            errors.append("max_quality must be between 1 and 5")
        
        if self.preferred_quality > self.max_quality:
            errors.append("preferred_quality cannot exceed max_quality")
        
        if self.max_generation_time_seconds <= 0:
            errors.append("max_generation_time_seconds must be positive")
        
        if self.preferred_resolution not in ["720p", "1080p", "1440p", "4k"]:
            errors.append("preferred_resolution must be one of: 720p, 1080p, 1440p, 4k")
        
        if self.preview_format_preference not in ["webp", "jpg", "png", "avif"]:
            errors.append("preview_format_preference must be one of: webp, jpg, png, avif")
        
        if not (0 <= self.ai_enhancement_level <= 3):
            errors.append("ai_enhancement_level must be between 0 and 3")
        
        if not (0.1 <= self.feedback_sensitivity <= 1.0):
            errors.append("feedback_sensitivity must be between 0.1 and 1.0")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class UpdateQualitySettingsCommand(AbstractCommand):
    """
    Command to update quality settings for a user.
    
    Updates user quality preferences and device capability settings
    for optimized preview generation.
    """
    user_id: UUID
    device_capability: Optional[float] = None
    bandwidth_estimate: Optional[float] = None
    preferred_quality: Optional[int] = None
    max_quality: Optional[int] = None
    auto_adjust_quality: Optional[bool] = None
    max_generation_time_seconds: Optional[int] = None
    preferred_resolution: Optional[str] = None
    enable_caching: Optional[bool] = None
    preview_format_preference: Optional[str] = None
    enable_progressive_loading: Optional[bool] = None
    enable_thumbnails: Optional[bool] = None
    ai_enhancement_level: Optional[int] = None
    enable_smart_cropping: Optional[bool] = None
    enable_color_optimization: Optional[bool] = None
    enable_realtime_preview: Optional[bool] = None
    feedback_sensitivity: Optional[float] = None
    auto_apply_suggestions: Optional[bool] = None
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.user_id:
            errors.append("user_id is required")
        
        if self.device_capability is not None and not (0.1 <= self.device_capability <= 2.0):
            errors.append("device_capability must be between 0.1 and 2.0")
        
        if self.preferred_quality is not None and not (1 <= self.preferred_quality <= 5):
            errors.append("preferred_quality must be between 1 and 5")
        
        if self.max_quality is not None and not (1 <= self.max_quality <= 5):
            errors.append("max_quality must be between 1 and 5")
        
        if (self.preferred_quality is not None and self.max_quality is not None and 
            self.preferred_quality > self.max_quality):
            errors.append("preferred_quality cannot exceed max_quality")
        
        if self.max_generation_time_seconds is not None and self.max_generation_time_seconds <= 0:
            errors.append("max_generation_time_seconds must be positive")
        
        if (self.preferred_resolution is not None and 
            self.preferred_resolution not in ["720p", "1080p", "1440p", "4k"]):
            errors.append("preferred_resolution must be one of: 720p, 1080p, 1440p, 4k")
        
        if (self.preview_format_preference is not None and 
            self.preview_format_preference not in ["webp", "jpg", "png", "avif"]):
            errors.append("preview_format_preference must be one of: webp, jpg, png, avif")
        
        if self.ai_enhancement_level is not None and not (0 <= self.ai_enhancement_level <= 3):
            errors.append("ai_enhancement_level must be between 0 and 3")
        
        if self.feedback_sensitivity is not None and not (0.1 <= self.feedback_sensitivity <= 1.0):
            errors.append("feedback_sensitivity must be between 0.1 and 1.0")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class UpdatePerformanceMetricsCommand(AbstractCommand):
    """
    Command to update performance metrics for quality settings.
    
    Records generation time and device performance data
    to optimize future preview generation settings.
    """
    user_id: UUID
    generation_time: float
    device_capability: Optional[float] = None
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.user_id:
            errors.append("user_id is required")
        
        if self.generation_time < 0:
            errors.append("generation_time must be non-negative")
        
        if self.device_capability is not None and not (0.1 <= self.device_capability <= 2.0):
            errors.append("device_capability must be between 0.1 and 2.0")
        
        return self._create_validation_result(errors)


# ===== Cleanup Commands =====

@dataclass(kw_only=True)
class CleanupOldVersionsCommand(AbstractCommand):
    """
    Command to clean up old preview versions to save storage space.
    
    Removes old preview versions while preserving final versions
    and latest versions per branch based on specified retention policies.
    """
    request_id: UUID
    keep_final: bool = True
    keep_latest_per_branch: bool = True
    
    def validate(self):
        """Validate command data."""
        errors = []
        
        if not self.request_id:
            errors.append("request_id is required")
        
        return self._create_validation_result(errors)
