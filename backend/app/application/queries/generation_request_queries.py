"""Generation request related queries for CQRS pattern."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .base_query import Query, RequireUserMixin, RequireIdMixin, QueryValidationError
from ..dto.generation_request_dto import GenerationRequestDTO, GenerationRequestStatsDTO, GenerationRequestProgressDTO


@dataclass(kw_only=True)
class GetGenerationRequestQuery(Query[GenerationRequestDTO], RequireUserMixin, RequireIdMixin):
    """Query to get a single generation request by ID."""
    
    request_id: str
    include_phases: bool = False
    include_feedback: bool = False
    include_progress: bool = True
    
    def validate(self) -> None:
        """Validate get generation request query."""
        self.validate_user_required()
        self.validate_id_required("request_id")


@dataclass(kw_only=True)
class ListGenerationRequestsQuery(Query[List[GenerationRequestDTO]], RequireUserMixin):
    """Query to list generation requests with filtering."""
    
    user_id: Optional[str] = None  # If None, shows requesting user's requests
    project_id: Optional[str] = None
    status: Optional[str] = None  # queued, processing, completed, failed
    priority: Optional[str] = None  # normal, high
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    include_phases: bool = False
    include_progress: bool = True
    
    def validate(self) -> None:
        """Validate list generation requests query."""
        self.validate_user_required()
        
        if self.status is not None:
            valid_statuses = ["queued", "processing", "completed", "error"]
            if self.status not in valid_statuses:
                raise QueryValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if self.priority is not None:
            if self.priority not in ["normal", "high"]:
                raise QueryValidationError("Priority must be 'normal' or 'high'")
        
        if self.created_after and self.created_before:
            if self.created_after >= self.created_before:
                raise QueryValidationError("Created after date must be before created before date")


@dataclass(kw_only=True)
class GetGenerationRequestsByUserQuery(Query[List[GenerationRequestDTO]], RequireUserMixin, RequireIdMixin):
    """Query to get generation requests for a specific user."""
    
    user_id: str
    status: Optional[str] = None
    project_id: Optional[str] = None
    limit_days: int = 30
    include_completed: bool = True
    
    def validate(self) -> None:
        """Validate get requests by user query."""
        self.validate_user_required()
        self.validate_id_required("user_id")
        
        if self.status is not None:
            valid_statuses = ["queued", "processing", "completed", "error"]
            if self.status not in valid_statuses:
                raise QueryValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if self.limit_days < 1:
            raise QueryValidationError("Limit days must be at least 1")
        
        if self.limit_days > 365:
            raise QueryValidationError("Limit days cannot exceed 365")


@dataclass(kw_only=True)
class GetGenerationRequestsByProjectQuery(Query[List[GenerationRequestDTO]], RequireUserMixin, RequireIdMixin):
    """Query to get generation requests for a specific project."""
    
    project_id: str
    status: Optional[str] = None
    include_phases: bool = True
    include_progress: bool = True
    
    def validate(self) -> None:
        """Validate get requests by project query."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if self.status is not None:
            valid_statuses = ["queued", "processing", "completed", "error"]
            if self.status not in valid_statuses:
                raise QueryValidationError(f"Status must be one of: {', '.join(valid_statuses)}")


@dataclass(kw_only=True)
class GetGenerationRequestStatsQuery(Query[GenerationRequestStatsDTO], RequireUserMixin):
    """Query to get generation request statistics."""
    
    user_id: Optional[str] = None  # If None, gets overall stats (admin only)
    period_days: int = 30
    group_by: Optional[str] = None  # status, priority, user, project
    include_phase_stats: bool = True
    include_performance_stats: bool = True
    
    def validate(self) -> None:
        """Validate get request stats query."""
        self.validate_user_required()
        
        if self.period_days < 1:
            raise QueryValidationError("Period days must be at least 1")
        
        if self.period_days > 365:
            raise QueryValidationError("Period days cannot exceed 365")
        
        if self.group_by is not None:
            valid_groups = ["status", "priority", "user", "project"]
            if self.group_by not in valid_groups:
                raise QueryValidationError(f"Group by must be one of: {', '.join(valid_groups)}")


@dataclass(kw_only=True)
class GetGenerationQueueQuery(Query[List[GenerationRequestDTO]], RequireUserMixin):
    """Query to get generation request queue (admin only)."""
    
    priority: Optional[str] = None  # normal, high
    user_id: Optional[str] = None
    max_age_hours: int = 24
    
    def validate(self) -> None:
        """Validate get generation queue query."""
        self.validate_user_required()
        
        if self.priority is not None:
            if self.priority not in ["normal", "high"]:
                raise QueryValidationError("Priority must be 'normal' or 'high'")
        
        if self.max_age_hours < 1:
            raise QueryValidationError("Max age hours must be at least 1")
        
        if self.max_age_hours > 168:  # 7 days
            raise QueryValidationError("Max age hours cannot exceed 168 (7 days)")


@dataclass(kw_only=True)
class GetGenerationProgressQuery(Query[GenerationRequestProgressDTO], RequireUserMixin, RequireIdMixin):
    """Query to get detailed progress for a generation request."""
    
    request_id: str
    include_phase_details: bool = True
    include_estimated_completion: bool = True
    include_error_details: bool = False
    
    def validate(self) -> None:
        """Validate get generation progress query."""
        self.validate_user_required()
        self.validate_id_required("request_id")


@dataclass(kw_only=True)
class GetFailedGenerationRequestsQuery(Query[List[GenerationRequestDTO]], RequireUserMixin):
    """Query to get failed generation requests."""
    
    user_id: Optional[str] = None
    error_type: Optional[str] = None
    failed_after: Optional[datetime] = None
    retry_eligible: Optional[bool] = None
    include_error_details: bool = True
    
    def validate(self) -> None:
        """Validate get failed requests query."""
        self.validate_user_required()
        
        if self.error_type is not None:
            valid_types = [
                "validation_error", "processing_error", "timeout_error",
                "quota_exceeded", "system_error", "user_cancelled"
            ]
            if self.error_type not in valid_types:
                raise QueryValidationError(f"Error type must be one of: {', '.join(valid_types)}")


@dataclass(kw_only=True)
class GetGenerationFeedbackQuery(Query[List[dict]], RequireUserMixin, RequireIdMixin):
    """Query to get feedback requests for a generation."""
    
    request_id: str
    phase_number: Optional[int] = None
    status: Optional[str] = None  # pending, processing, completed, failed
    include_modifications: bool = True
    
    def validate(self) -> None:
        """Validate get generation feedback query."""
        self.validate_user_required()
        self.validate_id_required("request_id")
        
        if self.phase_number is not None:
            if not (1 <= self.phase_number <= 7):
                raise QueryValidationError("Phase number must be between 1 and 7")
        
        if self.status is not None:
            valid_statuses = ["pending", "processing", "completed", "error"]
            if self.status not in valid_statuses:
                raise QueryValidationError(f"Status must be one of: {', '.join(valid_statuses)}")


@dataclass(kw_only=True)
class GetGenerationPhaseExecutionsQuery(Query[List[dict]], RequireUserMixin, RequireIdMixin):
    """Query to get phase executions for a generation request."""
    
    request_id: str
    phase_number: Optional[int] = None
    status: Optional[str] = None  # pending, processing, feedback_waiting, completed, failed
    include_retry_history: bool = True
    
    def validate(self) -> None:
        """Validate get phase executions query."""
        self.validate_user_required()
        self.validate_id_required("request_id")
        
        if self.phase_number is not None:
            if not (1 <= self.phase_number <= 7):
                raise QueryValidationError("Phase number must be between 1 and 7")
        
        if self.status is not None:
            valid_statuses = ["pending", "processing", "feedback_waiting", "completed", "error"]
            if self.status not in valid_statuses:
                raise QueryValidationError(f"Status must be one of: {', '.join(valid_statuses)}")


@dataclass(kw_only=True)
class GetGenerationPerformanceQuery(Query[dict], RequireUserMixin):
    """Query to get generation performance metrics."""
    
    user_id: Optional[str] = None
    period_days: int = 7
    metric_types: Optional[List[str]] = None
    group_by_phase: bool = True
    
    def validate(self) -> None:
        """Validate get generation performance query."""
        self.validate_user_required()
        
        if self.period_days < 1:
            raise QueryValidationError("Period days must be at least 1")
        
        if self.period_days > 90:
            raise QueryValidationError("Period days cannot exceed 90")
        
        if self.metric_types:
            valid_types = [
                "processing_time", "queue_time", "success_rate",
                "retry_rate", "feedback_rate", "quality_score"
            ]
            for metric_type in self.metric_types:
                if metric_type not in valid_types:
                    raise QueryValidationError(f"Invalid metric type: {metric_type}")


@dataclass(kw_only=True)
class GetPendingFeedbackQuery(Query[List[dict]], RequireUserMixin):
    """Query to get pending feedback requests for user."""
    
    timeout_approaching: bool = False  # Only show requests near timeout
    phase_number: Optional[int] = None
    
    def validate(self) -> None:
        """Validate get pending feedback query."""
        self.validate_user_required()
        
        if self.phase_number is not None:
            if not (1 <= self.phase_number <= 7):
                raise QueryValidationError("Phase number must be between 1 and 7")


@dataclass(kw_only=True)
class GetGenerationHistoryQuery(Query[List[dict]], RequireUserMixin, RequireIdMixin):
    """Query to get generation request history/audit trail."""
    
    request_id: str
    action_types: Optional[List[str]] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate get generation history query."""
        self.validate_user_required()
        self.validate_id_required("request_id")
        
        if self.from_date and self.to_date:
            if self.from_date >= self.to_date:
                raise QueryValidationError("From date must be before to date")
        
        if self.action_types:
            valid_types = [
                "created", "started", "phase_completed", "feedback_requested",
                "feedback_received", "retried", "completed", "error", "cancelled"
            ]
            for action_type in self.action_types:
                if action_type not in valid_types:
                    raise QueryValidationError(f"Invalid action type: {action_type}")