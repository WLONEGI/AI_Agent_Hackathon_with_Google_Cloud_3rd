"""Preview system Data Transfer Objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from .base_dto import BaseDTO, validate_required_fields, validate_field_length


@dataclass
class PreviewVersionCreateDTO(BaseDTO):
    """DTO for creating a preview version."""

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

    def validate(self) -> None:
        validate_required_fields(self, ["request_id", "phase", "version_data"])

        if not (1 <= self.phase <= 7):
            raise ValueError("phase must be between 1 and 7")

        if not (1 <= self.quality_level <= 5):
            raise ValueError("quality_level must be between 1 and 5")

        if self.generation_time_ms is not None and self.generation_time_ms < 0:
            raise ValueError("generation_time_ms must be non-negative")

        if self.file_size_bytes is not None and self.file_size_bytes < 0:
            raise ValueError("file_size_bytes must be non-negative")


@dataclass
class PreviewVersionUpdateDTO(BaseDTO):
    """DTO for updating a preview version."""

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

    def validate(self) -> None:
        validate_required_fields(self, ["version_id"])

        if self.quality_level is not None and not (1 <= self.quality_level <= 5):
            raise ValueError("quality_level must be between 1 and 5")

        if self.quality_score is not None and not (0.0 <= self.quality_score <= 1.0):
            raise ValueError("quality_score must be between 0.0 and 1.0")

        if self.merge_status is not None and self.merge_status not in {"pending", "merged", "discarded"}:
            raise ValueError("merge_status must be pending, merged, or discarded")

        if self.generation_time_ms is not None and self.generation_time_ms < 0:
            raise ValueError("generation_time_ms must be non-negative")

        if self.file_size_bytes is not None and self.file_size_bytes < 0:
            raise ValueError("file_size_bytes must be non-negative")


@dataclass
class PreviewInteractionCreateDTO(BaseDTO):
    """DTO for creating a preview interaction."""

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

    def validate(self) -> None:
        validate_required_fields(
            self,
            ["version_id", "user_id", "element_id", "element_type", "change_type", "change_data"],
        )

        if self.element_type not in {"text", "image", "layout", "character", "background", "effect", "dialogue"}:
            raise ValueError(
                "element_type must be one of: text, image, layout, character, background, effect, dialogue"
            )

        if self.change_type not in {"edit", "move", "delete", "style", "add", "replace", "transform"}:
            raise ValueError(
                "change_type must be one of: edit, move, delete, style, add, replace, transform"
            )

        if self.confidence_score is not None and not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0.0 and 1.0")

        if self.interaction_type not in {"modification", "approval", "rejection", "comment"}:
            raise ValueError("interaction_type must be modification, approval, rejection, or comment")


@dataclass
class PreviewQualitySettingsCreateDTO(BaseDTO):
    """DTO for creating preview quality settings."""

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

    def validate(self) -> None:
        validate_required_fields(self, ["user_id"])

        if not (0.1 <= self.device_capability <= 2.0):
            raise ValueError("device_capability must be between 0.1 and 2.0")

        if not (1 <= self.preferred_quality <= 5):
            raise ValueError("preferred_quality must be between 1 and 5")

        if not (1 <= self.max_quality <= 5):
            raise ValueError("max_quality must be between 1 and 5")

        if self.preferred_quality > self.max_quality:
            raise ValueError("preferred_quality cannot exceed max_quality")

        if self.max_generation_time_seconds <= 0:
            raise ValueError("max_generation_time_seconds must be positive")

        if self.preferred_resolution not in {"720p", "1080p", "1440p", "4k"}:
            raise ValueError("preferred_resolution must be one of: 720p, 1080p, 1440p, 4k")

        if self.preview_format_preference not in {"webp", "jpg", "png", "avif"}:
            raise ValueError("preview_format_preference must be one of: webp, jpg, png, avif")

        if not (0 <= self.ai_enhancement_level <= 3):
            raise ValueError("ai_enhancement_level must be between 0 and 3")

        if not (0.1 <= self.feedback_sensitivity <= 1.0):
            raise ValueError("feedback_sensitivity must be between 0.1 and 1.0")


@dataclass
class PreviewQualitySettingsUpdateDTO(BaseDTO):
    """DTO for updating preview quality settings."""

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

    def validate(self) -> None:
        validate_required_fields(self, ["user_id"])

        if self.device_capability is not None and not (0.1 <= self.device_capability <= 2.0):
            raise ValueError("device_capability must be between 0.1 and 2.0")

        if self.preferred_quality is not None and not (1 <= self.preferred_quality <= 5):
            raise ValueError("preferred_quality must be between 1 and 5")

        if self.max_quality is not None and not (1 <= self.max_quality <= 5):
            raise ValueError("max_quality must be between 1 and 5")

        if (self.preferred_quality is not None and self.max_quality is not None and
                self.preferred_quality > self.max_quality):
            raise ValueError("preferred_quality cannot exceed max_quality")

        if (self.max_generation_time_seconds is not None and
                self.max_generation_time_seconds <= 0):
            raise ValueError("max_generation_time_seconds must be positive")

        if (self.preferred_resolution is not None and
                self.preferred_resolution not in {"720p", "1080p", "1440p", "4k"}):
            raise ValueError("preferred_resolution must be one of: 720p, 1080p, 1440p, 4k")

        if (self.preview_format_preference is not None and
                self.preview_format_preference not in {"webp", "jpg", "png", "avif"}):
            raise ValueError("preview_format_preference must be one of: webp, jpg, png, avif")

        if self.ai_enhancement_level is not None and not (0 <= self.ai_enhancement_level <= 3):
            raise ValueError("ai_enhancement_level must be between 0 and 3")

        if self.feedback_sensitivity is not None and not (0.1 <= self.feedback_sensitivity <= 1.0):
            raise ValueError("feedback_sensitivity must be between 0.1 and 1.0")
