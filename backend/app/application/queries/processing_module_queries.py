"""Processing module related queries for CQRS pattern."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .base_query import Query, RequireUserMixin, RequireIdMixin, QueryValidationError
from ..dto.processing_module_dto import ProcessingModuleDTO, ProcessingModuleStatsDTO


@dataclass(kw_only=True)
class GetProcessingModuleQuery(Query[ProcessingModuleDTO], RequireUserMixin, RequireIdMixin):
    """Query to get a single processing module by ID."""
    
    module_id: str
    include_metrics: bool = False
    include_checkpoint_data: bool = False
    
    def validate(self) -> None:
        """Validate get processing module query."""
        self.validate_user_required()
        self.validate_id_required("module_id")


@dataclass(kw_only=True)
class ListProcessingModulesQuery(Query[List[ProcessingModuleDTO]], RequireUserMixin):
    """Query to list processing modules with filtering."""
    
    request_id: Optional[str] = None
    module_number: Optional[int] = None
    module_name: Optional[str] = None
    status: Optional[str] = None  # pending, processing, completed, failed
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None
    include_metrics: bool = False
    
    def validate(self) -> None:
        """Validate list processing modules query."""
        self.validate_user_required()
        
        if self.module_number is not None:
            if not (1 <= self.module_number <= 7):
                raise QueryValidationError("Module number must be between 1 and 7")
        
        if self.module_name is not None:
            valid_modules = [
                "concept_analysis", "character_visual", "plot_structure",
                "name_generation", "scene_generation", "text_placement", 
                "final_integration"
            ]
            if self.module_name not in valid_modules:
                raise QueryValidationError(f"Module name must be one of: {', '.join(valid_modules)}")
        
        if self.status is not None:
            valid_statuses = ["pending", "processing", "completed", "error"]
            if self.status not in valid_statuses:
                raise QueryValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if self.started_after and self.started_before:
            if self.started_after >= self.started_before:
                raise QueryValidationError("Started after date must be before started before date")


@dataclass(kw_only=True)
class GetProcessingModulesByRequestQuery(Query[List[ProcessingModuleDTO]], RequireUserMixin, RequireIdMixin):
    """Query to get processing modules for a specific generation request."""
    
    request_id: str
    module_number: Optional[int] = None
    status: Optional[str] = None
    include_metrics: bool = True
    include_checkpoint_data: bool = False
    order_by_module_number: bool = True
    
    def validate(self) -> None:
        """Validate get modules by request query."""
        self.validate_user_required()
        self.validate_id_required("request_id")
        
        if self.module_number is not None:
            if not (1 <= self.module_number <= 7):
                raise QueryValidationError("Module number must be between 1 and 7")
        
        if self.status is not None:
            valid_statuses = ["pending", "processing", "completed", "error"]
            if self.status not in valid_statuses:
                raise QueryValidationError(f"Status must be one of: {', '.join(valid_statuses)}")


@dataclass(kw_only=True)
class GetProcessingModuleStatsQuery(Query[ProcessingModuleStatsDTO], RequireUserMixin):
    """Query to get processing module statistics."""
    
    user_id: Optional[str] = None  # If None, gets overall stats (admin only)
    module_number: Optional[int] = None
    module_name: Optional[str] = None
    period_days: int = 30
    include_performance_metrics: bool = True
    include_error_analysis: bool = True
    
    def validate(self) -> None:
        """Validate get module stats query."""
        self.validate_user_required()
        
        if self.module_number is not None:
            if not (1 <= self.module_number <= 7):
                raise QueryValidationError("Module number must be between 1 and 7")
        
        if self.module_name is not None:
            valid_modules = [
                "concept_analysis", "character_visual", "plot_structure",
                "name_generation", "scene_generation", "text_placement",
                "final_integration"
            ]
            if self.module_name not in valid_modules:
                raise QueryValidationError(f"Module name must be one of: {', '.join(valid_modules)}")
        
        if self.period_days < 1:
            raise QueryValidationError("Period days must be at least 1")
        
        if self.period_days > 365:
            raise QueryValidationError("Period days cannot exceed 365")


@dataclass(kw_only=True)
class GetActiveProcessingModulesQuery(Query[List[ProcessingModuleDTO]], RequireUserMixin):
    """Query to get currently active processing modules."""
    
    user_id: Optional[str] = None
    module_number: Optional[int] = None
    max_age_minutes: int = 60  # Modules older than this are considered stale
    include_stale: bool = False
    
    def validate(self) -> None:
        """Validate get active modules query."""
        self.validate_user_required()
        
        if self.module_number is not None:
            if not (1 <= self.module_number <= 7):
                raise QueryValidationError("Module number must be between 1 and 7")
        
        if self.max_age_minutes < 1:
            raise QueryValidationError("Max age minutes must be at least 1")
        
        if self.max_age_minutes > 1440:  # 24 hours
            raise QueryValidationError("Max age minutes cannot exceed 1440 (24 hours)")


@dataclass(kw_only=True)
class GetFailedProcessingModulesQuery(Query[List[ProcessingModuleDTO]], RequireUserMixin):
    """Query to get failed processing modules."""
    
    user_id: Optional[str] = None
    module_number: Optional[int] = None
    error_type: Optional[str] = None
    failed_after: Optional[datetime] = None
    retry_eligible: Optional[bool] = None
    include_error_details: bool = True
    
    def validate(self) -> None:
        """Validate get failed modules query."""
        self.validate_user_required()
        
        if self.module_number is not None:
            if not (1 <= self.module_number <= 7):
                raise QueryValidationError("Module number must be between 1 and 7")
        
        if self.error_type is not None:
            valid_types = [
                "timeout", "validation_error", "processing_error",
                "memory_error", "api_error", "system_error"
            ]
            if self.error_type not in valid_types:
                raise QueryValidationError(f"Error type must be one of: {', '.join(valid_types)}")


@dataclass(kw_only=True)
class GetProcessingModuleMetricsQuery(Query[List[dict]], RequireUserMixin, RequireIdMixin):
    """Query to get metrics for processing modules."""
    
    module_id: Optional[str] = None  # If None, gets metrics for all modules
    metric_names: Optional[List[str]] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    group_by: Optional[str] = None  # hour, day, module, request
    
    def validate(self) -> None:
        """Validate get module metrics query."""
        self.validate_user_required()
        
        if self.from_date and self.to_date:
            if self.from_date >= self.to_date:
                raise QueryValidationError("From date must be before to date")
        
        if self.group_by is not None:
            valid_groups = ["hour", "day", "module", "request"]
            if self.group_by not in valid_groups:
                raise QueryValidationError(f"Group by must be one of: {', '.join(valid_groups)}")


@dataclass(kw_only=True)
class GetProcessingModulePerformanceQuery(Query[dict], RequireUserMixin):
    """Query to get processing module performance analysis."""
    
    module_number: Optional[int] = None
    period_days: int = 7
    comparison_period_days: Optional[int] = None  # For trend analysis
    include_percentiles: bool = True
    include_error_rates: bool = True
    
    def validate(self) -> None:
        """Validate get module performance query."""
        self.validate_user_required()
        
        if self.module_number is not None:
            if not (1 <= self.module_number <= 7):
                raise QueryValidationError("Module number must be between 1 and 7")
        
        if self.period_days < 1:
            raise QueryValidationError("Period days must be at least 1")
        
        if self.period_days > 90:
            raise QueryValidationError("Period days cannot exceed 90")
        
        if self.comparison_period_days is not None:
            if self.comparison_period_days < 1:
                raise QueryValidationError("Comparison period days must be at least 1")
            if self.comparison_period_days > 90:
                raise QueryValidationError("Comparison period days cannot exceed 90")


@dataclass(kw_only=True)
class GetProcessingBottlenecksQuery(Query[List[dict]], RequireUserMixin):
    """Query to identify processing bottlenecks."""
    
    period_days: int = 7
    min_duration_threshold_ms: int = 30000  # 30 seconds
    include_retry_analysis: bool = True
    group_by_module: bool = True
    
    def validate(self) -> None:
        """Validate get processing bottlenecks query."""
        self.validate_user_required()
        
        if self.period_days < 1:
            raise QueryValidationError("Period days must be at least 1")
        
        if self.period_days > 30:
            raise QueryValidationError("Period days cannot exceed 30")
        
        if self.min_duration_threshold_ms < 1000:  # 1 second
            raise QueryValidationError("Duration threshold must be at least 1000ms")


@dataclass(kw_only=True)
class GetModuleCheckpointQuery(Query[dict], RequireUserMixin, RequireIdMixin):
    """Query to get checkpoint data for a processing module."""
    
    module_id: str
    checkpoint_timestamp: Optional[datetime] = None  # Get checkpoint at specific time
    
    def validate(self) -> None:
        """Validate get module checkpoint query."""
        self.validate_user_required()
        self.validate_id_required("module_id")


@dataclass(kw_only=True)
class GetProcessingPipelineStatusQuery(Query[dict], RequireUserMixin, RequireIdMixin):
    """Query to get overall pipeline status for a request."""
    
    request_id: str
    include_phase_details: bool = True
    include_estimated_completion: bool = True
    
    def validate(self) -> None:
        """Validate get pipeline status query."""
        self.validate_user_required()
        self.validate_id_required("request_id")


@dataclass(kw_only=True)
class GetModuleResourceUsageQuery(Query[List[dict]], RequireUserMixin):
    """Query to get resource usage metrics for modules."""
    
    module_number: Optional[int] = None
    period_hours: int = 24
    metric_types: Optional[List[str]] = None  # cpu, memory, api_calls, processing_time
    
    def validate(self) -> None:
        """Validate get module resource usage query."""
        self.validate_user_required()
        
        if self.module_number is not None:
            if not (1 <= self.module_number <= 7):
                raise QueryValidationError("Module number must be between 1 and 7")
        
        if self.period_hours < 1:
            raise QueryValidationError("Period hours must be at least 1")
        
        if self.period_hours > 168:  # 7 days
            raise QueryValidationError("Period hours cannot exceed 168 (7 days)")
        
        if self.metric_types:
            valid_types = ["cpu", "memory", "api_calls", "processing_time", "queue_time"]
            for metric_type in self.metric_types:
                if metric_type not in valid_types:
                    raise QueryValidationError(f"Invalid metric type: {metric_type}")