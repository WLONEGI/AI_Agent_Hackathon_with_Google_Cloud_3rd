"""Processing module related DTOs for data transfer."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from .base_dto import BaseDTO, StatsDTO, validate_required_fields, validate_field_length


@dataclass
class ProcessingModuleDTO(BaseDTO):
    """DTO for processing module data transfer."""
    
    module_id: str
    request_id: str
    module_number: int
    module_name: str
    status: str  # pending, processing, completed, failed
    checkpoint_data: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    
    # Related data (populated when requested)
    metrics: Optional[List['ModuleMetricDTO']] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    
    def validate(self) -> None:
        """Validate processing module DTO."""
        validate_required_fields(self, [
            'module_id', 'request_id', 'module_number',
            'module_name', 'status'
        ])
        
        if not (1 <= self.module_number <= 7):
            raise ValueError("Module number must be between 1 and 7")
        
        valid_statuses = ["pending", "processing", "completed", "failed"]
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        # Validate module names according to system design
        valid_modules = {
            1: "concept_analysis",
            2: "character_visual",
            3: "plot_structure",
            4: "name_generation", 
            5: "scene_generation",
            6: "text_placement",
            7: "final_integration"
        }
        
        expected_name = valid_modules.get(self.module_number)
        if expected_name and self.module_name != expected_name:
            raise ValueError(f"Module {self.module_number} must be named '{expected_name}'")
        
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("Duration cannot be negative")


@dataclass
class ProcessingModuleCreateDTO(BaseDTO):
    """DTO for creating a new processing module."""
    
    request_id: str
    module_number: int
    module_name: str
    input_data: Optional[Dict[str, Any]] = None
    
    def validate(self) -> None:
        """Validate processing module create DTO."""
        validate_required_fields(self, ['request_id', 'module_number', 'module_name'])
        
        if not (1 <= self.module_number <= 7):
            raise ValueError("Module number must be between 1 and 7")
        
        # Validate module names
        valid_modules = {
            1: "concept_analysis",
            2: "character_visual",
            3: "plot_structure",
            4: "name_generation",
            5: "scene_generation",
            6: "text_placement",
            7: "final_integration"
        }
        
        expected_name = valid_modules.get(self.module_number)
        if expected_name and self.module_name != expected_name:
            raise ValueError(f"Module {self.module_number} must be named '{expected_name}'")


@dataclass
class ProcessingModuleUpdateDTO(BaseDTO):
    """DTO for updating processing module information."""
    
    status: Optional[str] = None
    checkpoint_data: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    
    def validate(self) -> None:
        """Validate processing module update DTO."""
        if self.status is not None:
            valid_statuses = ["pending", "processing", "completed", "failed"]
            if self.status not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("Duration cannot be negative")
        
        if self.completed_at is not None and self.completed_at > datetime.utcnow():
            raise ValueError("Completion time cannot be in the future")


@dataclass
class ProcessingModuleStatsDTO(StatsDTO):
    """DTO for processing module statistics."""
    
    # Overall counts
    total_modules: int = 0
    pending_modules: int = 0
    processing_modules: int = 0
    completed_modules: int = 0
    failed_modules: int = 0
    
    # Performance metrics
    average_processing_time_ms: float = 0.0
    median_processing_time_ms: float = 0.0
    p95_processing_time_ms: float = 0.0
    success_rate: float = 0.0
    retry_rate: float = 0.0
    
    # Module-specific stats
    module_performance: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    bottleneck_modules: List[int] = field(default_factory=list)
    
    # Error analysis
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    most_common_errors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Resource utilization
    total_cpu_time_ms: float = 0.0
    total_memory_usage_mb: float = 0.0
    total_api_calls: int = 0
    
    # Trends
    processing_time_trend: float = 0.0  # Percentage change
    success_rate_trend: float = 0.0
    
    def calculate_derived_stats(self) -> None:
        """Calculate derived statistics."""
        # Success rate
        if self.total_modules > 0:
            self.success_rate = self.completed_modules / self.total_modules * 100
        
        # Retry rate (modules that had to be retried)
        total_retries = sum(
            stats.get('retry_count', 0) for stats in self.module_performance.values()
        )
        if self.total_modules > 0:
            self.retry_rate = total_retries / self.total_modules * 100


@dataclass
class ProcessingModuleResultDTO(BaseDTO):
    """DTO for processing module execution result."""
    
    module_id: str
    module_number: int
    module_name: str
    execution_status: str  # completed, failed
    output_data: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None
    processing_time_ms: int
    
    # Validation results
    validation_passed: bool = True
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    
    # Resource usage
    cpu_time_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    api_calls_made: int = 0
    
    # Error details (if failed)
    error_type: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    
    def validate(self) -> None:
        """Validate processing module result DTO."""
        validate_required_fields(self, [
            'module_id', 'module_number', 'module_name',
            'execution_status', 'processing_time_ms'
        ])
        
        if not (1 <= self.module_number <= 7):
            raise ValueError("Module number must be between 1 and 7")
        
        if self.execution_status not in ["completed", "failed"]:
            raise ValueError("Execution status must be 'completed' or 'failed'")
        
        if self.processing_time_ms < 0:
            raise ValueError("Processing time cannot be negative")
        
        if self.quality_score is not None:
            if not (0.0 <= self.quality_score <= 1.0):
                raise ValueError("Quality score must be between 0.0 and 1.0")
        
        if self.cpu_time_ms is not None and self.cpu_time_ms < 0:
            raise ValueError("CPU time cannot be negative")
        
        if self.memory_usage_mb is not None and self.memory_usage_mb < 0:
            raise ValueError("Memory usage cannot be negative")


@dataclass
class ModuleMetricDTO(BaseDTO):
    """DTO for module metric information."""
    
    metric_id: str
    module_id: str
    metric_name: str
    metric_value: float
    unit: Optional[str] = None
    created_at: datetime
    
    def validate(self) -> None:
        """Validate module metric DTO."""
        validate_required_fields(self, [
            'metric_id', 'module_id', 'metric_name', 'metric_value'
        ])
        
        validate_field_length(self, {'metric_name': (1, 100)})
        
        if self.unit is not None:
            validate_field_length(self, {'unit': (1, 20)})


@dataclass
class ProcessingPipelineStatusDTO(BaseDTO):
    """DTO for overall processing pipeline status."""
    
    request_id: str
    total_modules: int = 7
    completed_modules: int = 0
    failed_modules: int = 0
    current_module: Optional[int] = None
    overall_progress_percentage: float = 0.0
    
    # Module statuses
    module_statuses: Dict[int, str] = field(default_factory=dict)
    module_progress: Dict[int, float] = field(default_factory=dict)
    
    # Time estimates
    started_at: Optional[datetime] = None
    estimated_completion_at: Optional[datetime] = None
    estimated_remaining_seconds: Optional[float] = None
    
    # Current processing info
    current_module_name: Optional[str] = None
    current_module_started_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate processing pipeline status DTO."""
        validate_required_fields(self, ['request_id', 'total_modules'])
        
        if self.total_modules != 7:
            raise ValueError("Total modules must be 7")
        
        if not (0.0 <= self.overall_progress_percentage <= 100.0):
            raise ValueError("Progress percentage must be between 0.0 and 100.0")
        
        if self.current_module is not None:
            if not (1 <= self.current_module <= self.total_modules):
                raise ValueError(f"Current module must be between 1 and {self.total_modules}")


@dataclass
class ModulePerformanceDTO(BaseDTO):
    """DTO for individual module performance analysis."""
    
    module_number: int
    module_name: str
    period_start: datetime
    period_end: datetime
    
    # Execution metrics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate: float = 0.0
    
    # Timing metrics
    average_processing_time_ms: float = 0.0
    median_processing_time_ms: float = 0.0
    min_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    p95_processing_time_ms: float = 0.0
    
    # Quality metrics
    average_quality_score: float = 0.0
    quality_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Resource metrics
    average_cpu_usage: float = 0.0
    average_memory_usage_mb: float = 0.0
    total_api_calls: int = 0
    
    # Error analysis
    error_types: Dict[str, int] = field(default_factory=dict)
    retry_analysis: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> None:
        """Validate module performance DTO."""
        validate_required_fields(self, [
            'module_number', 'module_name',
            'period_start', 'period_end'
        ])
        
        if not (1 <= self.module_number <= 7):
            raise ValueError("Module number must be between 1 and 7")
        
        if self.period_start >= self.period_end:
            raise ValueError("Period start must be before period end")


@dataclass
class ModuleBottleneckDTO(BaseDTO):
    """DTO for module bottleneck analysis."""
    
    module_number: int
    module_name: str
    bottleneck_type: str  # processing_time, error_rate, resource_usage
    severity_score: float  # 0.0 to 1.0
    
    # Contributing factors
    average_processing_time_ms: float = 0.0
    error_rate_percentage: float = 0.0
    retry_rate_percentage: float = 0.0
    resource_usage_score: float = 0.0
    
    # Impact analysis
    requests_affected: int = 0
    total_delay_seconds: float = 0.0
    estimated_cost_impact: float = 0.0
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate module bottleneck DTO."""
        validate_required_fields(self, [
            'module_number', 'module_name', 
            'bottleneck_type', 'severity_score'
        ])
        
        if not (1 <= self.module_number <= 7):
            raise ValueError("Module number must be between 1 and 7")
        
        valid_types = ["processing_time", "error_rate", "resource_usage"]
        if self.bottleneck_type not in valid_types:
            raise ValueError(f"Bottleneck type must be one of: {', '.join(valid_types)}")
        
        if not (0.0 <= self.severity_score <= 1.0):
            raise ValueError("Severity score must be between 0.0 and 1.0")


@dataclass
class ModuleResourceUsageDTO(BaseDTO):
    """DTO for module resource usage metrics."""
    
    module_number: int
    period_start: datetime
    period_end: datetime
    
    # CPU metrics
    total_cpu_time_ms: float = 0.0
    average_cpu_utilization: float = 0.0
    peak_cpu_utilization: float = 0.0
    
    # Memory metrics
    total_memory_usage_mb: float = 0.0
    average_memory_usage_mb: float = 0.0
    peak_memory_usage_mb: float = 0.0
    
    # API call metrics
    total_api_calls: int = 0
    api_calls_per_execution: float = 0.0
    api_error_rate: float = 0.0
    
    # Queue metrics
    average_queue_time_ms: float = 0.0
    peak_queue_length: int = 0
    
    def validate(self) -> None:
        """Validate module resource usage DTO."""
        validate_required_fields(self, ['module_number', 'period_start', 'period_end'])
        
        if not (1 <= self.module_number <= 7):
            raise ValueError("Module number must be between 1 and 7")
        
        if self.period_start >= self.period_end:
            raise ValueError("Period start must be before period end")