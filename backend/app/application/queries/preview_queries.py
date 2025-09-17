"""
Preview System Queries - Phase 2 Preview System Implementation.

This module contains all queries for preview system data retrieval
including version retrieval, interaction history, and quality settings.

Implements Query pattern for preview system read operations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.application.queries.base_query import AbstractQuery


# ===== Preview Version Queries =====

@dataclass(kw_only=True)
class GetPreviewVersionByIdQuery(AbstractQuery):
    """
    Query to retrieve a preview version by its ID.
    
    Returns detailed information about a specific preview version
    including metadata, content data, and status information.
    """
    version_id: UUID
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.version_id:
            errors.append("version_id is required")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetPreviewVersionsByRequestQuery(AbstractQuery):
    """
    Query to retrieve preview versions for a generation request.
    
    Returns all preview versions for a specific request,
    optionally filtered by phase and active status.
    """
    request_id: UUID
    phase: Optional[int] = None
    is_active: Optional[bool] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.request_id:
            errors.append("request_id is required")
        
        if self.phase is not None and not (1 <= self.phase <= 7):
            errors.append("phase must be between 1 and 7")
        
        if self.limit is not None and self.limit <= 0:
            errors.append("limit must be positive")
        
        if self.offset is not None and self.offset < 0:
            errors.append("offset must be non-negative")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetVersionTreeQuery(AbstractQuery):
    """
    Query to retrieve complete version tree for a request and phase.
    
    Returns all versions in hierarchical order (parent -> children)
    for a specific request and phase combination.
    """
    request_id: UUID
    phase: int
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.request_id:
            errors.append("request_id is required")
        
        if not (1 <= self.phase <= 7):
            errors.append("phase must be between 1 and 7")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetFinalVersionsQuery(AbstractQuery):
    """
    Query to retrieve all final versions for a generation request.
    
    Returns final versions for each phase of a request,
    representing the approved/selected versions.
    """
    request_id: UUID
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.request_id:
            errors.append("request_id is required")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetActiveVersionsQuery(AbstractQuery):
    """
    Query to retrieve all active preview versions.
    
    Returns active versions across all requests,
    optionally filtered by phase or time range.
    """
    phase: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if self.phase is not None and not (1 <= self.phase <= 7):
            errors.append("phase must be between 1 and 7")
        
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors.append("start_date must be before end_date")
        
        if self.limit is not None and self.limit <= 0:
            errors.append("limit must be positive")
        
        if self.offset is not None and self.offset < 0:
            errors.append("offset must be non-negative")
        
        return self._create_validation_result(errors)


# ===== Preview Interaction Queries =====

@dataclass(kw_only=True)
class GetPreviewInteractionByIdQuery(AbstractQuery):
    """
    Query to retrieve a preview interaction by its ID.
    
    Returns detailed information about a specific interaction
    including change data, status, and review information.
    """
    interaction_id: UUID
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.interaction_id:
            errors.append("interaction_id is required")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetInteractionsByVersionQuery(AbstractQuery):
    """
    Query to retrieve interactions for a specific version.
    
    Returns all interactions for a preview version,
    optionally filtered by interaction type and status.
    """
    version_id: UUID
    interaction_type: Optional[str] = None
    status: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.version_id:
            errors.append("version_id is required")
        
        if (self.interaction_type is not None and 
            self.interaction_type not in ["modification", "approval", "rejection", "comment"]):
            errors.append("interaction_type must be one of: modification, approval, rejection, comment")
        
        if (self.status is not None and 
            self.status not in ["pending", "approved", "rejected", "applied"]):
            errors.append("status must be one of: pending, approved, rejected, applied")
        
        if self.limit is not None and self.limit <= 0:
            errors.append("limit must be positive")
        
        if self.offset is not None and self.offset < 0:
            errors.append("offset must be non-negative")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetInteractionsByUserQuery(AbstractQuery):
    """
    Query to retrieve interactions by a specific user.
    
    Returns all interactions created by a user,
    optionally filtered by date range and status.
    """
    user_id: UUID
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.user_id:
            errors.append("user_id is required")
        
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors.append("start_date must be before end_date")
        
        if (self.status is not None and 
            self.status not in ["pending", "approved", "rejected", "applied"]):
            errors.append("status must be one of: pending, approved, rejected, applied")
        
        if self.limit is not None and self.limit <= 0:
            errors.append("limit must be positive")
        
        if self.offset is not None and self.offset < 0:
            errors.append("offset must be non-negative")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetPendingInteractionsQuery(AbstractQuery):
    """
    Query to retrieve pending interactions that need processing.
    
    Returns interactions with pending status,
    optionally filtered by version or priority.
    """
    version_id: Optional[UUID] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if self.limit is not None and self.limit <= 0:
            errors.append("limit must be positive")
        
        if self.offset is not None and self.offset < 0:
            errors.append("offset must be non-negative")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetInteractionStatisticsQuery(AbstractQuery):
    """
    Query to retrieve interaction statistics.
    
    Returns statistical information about interactions
    including counts, distributions, and trends.
    """
    version_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors.append("start_date must be before end_date")
        
        return self._create_validation_result(errors)


# ===== Preview Quality Settings Queries =====

@dataclass(kw_only=True)
class GetQualitySettingsByUserQuery(AbstractQuery):
    """
    Query to retrieve quality settings for a specific user.
    
    Returns quality preferences and device capability settings
    for personalized preview generation optimization.
    """
    user_id: UUID
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.user_id:
            errors.append("user_id is required")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetQualityRecommendationsQuery(AbstractQuery):
    """
    Query to get quality recommendations based on user settings and system load.
    
    Returns recommended quality settings optimized for user preferences,
    device capability, and current system performance.
    """
    user_id: UUID
    current_load: Optional[float] = None
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.user_id:
            errors.append("user_id is required")
        
        if self.current_load is not None and self.current_load < 0:
            errors.append("current_load must be non-negative")
        
        return self._create_validation_result(errors)


# ===== Analytics and Reporting Queries =====

@dataclass(kw_only=True)
class GetStorageUsageQuery(AbstractQuery):
    """
    Query to retrieve storage usage statistics.
    
    Returns storage utilization metrics including total size,
    version counts, and breakdown by phase or user.
    """
    user_id: Optional[UUID] = None
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        # No validation errors for this simple query
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetVersionPerformanceStatsQuery(AbstractQuery):
    """
    Query to retrieve version generation performance statistics.
    
    Returns performance metrics including generation times,
    quality scores, and resource utilization.
    """
    request_id: Optional[UUID] = None
    phase: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if self.phase is not None and not (1 <= self.phase <= 7):
            errors.append("phase must be between 1 and 7")
        
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors.append("start_date must be before end_date")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetUserEngagementStatsQuery(AbstractQuery):
    """
    Query to retrieve user engagement statistics.
    
    Returns metrics about user interactions, feedback patterns,
    and engagement levels with the preview system.
    """
    user_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors.append("start_date must be before end_date")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetQualityTrendsQuery(AbstractQuery):
    """
    Query to retrieve quality trend analysis.
    
    Returns quality metrics over time including score trends,
    user satisfaction, and system performance improvements.
    """
    request_id: Optional[UUID] = None
    phase: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    granularity: str = "daily"
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if self.phase is not None and not (1 <= self.phase <= 7):
            errors.append("phase must be between 1 and 7")
        
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors.append("start_date must be before end_date")
        
        if self.granularity not in ["hourly", "daily", "weekly", "monthly"]:
            errors.append("granularity must be one of: hourly, daily, weekly, monthly")
        
        return self._create_validation_result(errors)


# ===== Advanced Queries =====

@dataclass(kw_only=True)
class GetVersionComparisonQuery(AbstractQuery):
    """
    Query to compare multiple preview versions.
    
    Returns comparative analysis between versions including
    differences in content, quality scores, and user feedback.
    """
    version_ids: List[UUID]
    include_interactions: bool = False
    include_quality_metrics: bool = False
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.version_ids:
            errors.append("version_ids is required")
        
        if len(self.version_ids) < 2:
            errors.append("at least 2 version_ids are required for comparison")
        
        if len(self.version_ids) > 10:
            errors.append("maximum 10 versions can be compared at once")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetFeedbackHeatmapQuery(AbstractQuery):
    """
    Query to generate feedback heatmap for a preview version.
    
    Returns spatial distribution of user interactions and feedback
    for visual heatmap generation and hotspot analysis.
    """
    version_id: UUID
    element_type: Optional[str] = None
    interaction_type: Optional[str] = None
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.version_id:
            errors.append("version_id is required")
        
        if (self.element_type is not None and 
            self.element_type not in ["text", "image", "layout", "character", "background", "effect", "dialogue"]):
            errors.append("element_type must be one of: text, image, layout, character, background, effect, dialogue")
        
        if (self.interaction_type is not None and 
            self.interaction_type not in ["modification", "approval", "rejection", "comment"]):
            errors.append("interaction_type must be one of: modification, approval, rejection, comment")
        
        return self._create_validation_result(errors)


@dataclass(kw_only=True)
class GetRecommendedVersionsQuery(AbstractQuery):
    """
    Query to get recommended versions based on user preferences and history.
    
    Returns AI-recommended versions that match user preferences,
    quality expectations, and past interaction patterns.
    """
    user_id: UUID
    request_id: UUID
    phase: Optional[int] = None
    limit: int = 10
    
    def validate(self):
        """Validate query parameters."""
        errors = []
        
        if not self.user_id:
            errors.append("user_id is required")
        
        if not self.request_id:
            errors.append("request_id is required")
        
        if self.phase is not None and not (1 <= self.phase <= 7):
            errors.append("phase must be between 1 and 7")
        
        if not (1 <= self.limit <= 50):
            errors.append("limit must be between 1 and 50")
        
        return self._create_validation_result(errors)