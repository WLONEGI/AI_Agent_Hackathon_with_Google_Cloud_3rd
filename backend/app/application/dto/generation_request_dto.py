"""Generation request related DTOs for data transfer."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from .base_dto import BaseDTO, StatsDTO, validate_required_fields, validate_field_length


@dataclass
class GenerationRequestDTO(BaseDTO):
    """DTO for generation request data transfer."""
    
    request_id: str
    project_id: str
    user_id: str
    input_text: str
    request_settings: Dict[str, Any]
    status: str  # queued, processing, completed, failed
    created_at: datetime
    current_module: int = 0
    priority: str = "normal"
    webhook_url: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    
    # Related data (populated when requested)
    phases: Optional[List['PhaseExecutionDTO']] = None
    feedback_requests: Optional[List['FeedbackRequestDTO']] = None
    progress: Optional['GenerationRequestProgressDTO'] = None
    
    def validate(self) -> None:
        """Validate generation request DTO."""
        validate_required_fields(self, [
            'request_id', 'project_id', 'user_id', 
            'input_text', 'request_settings', 'status'
        ])
        
        valid_statuses = ["queued", "processing", "completed", "error"]
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if self.priority not in ["normal", "high"]:
            raise ValueError("Priority must be 'normal' or 'high'")
        
        if not (0 <= self.current_module <= 7):
            raise ValueError("Current module must be between 0 and 7")
        
        if len(self.input_text) > 100000:  # 100K character limit
            raise ValueError("Input text must be 100,000 characters or less")


@dataclass
class GenerationRequestCreateDTO(BaseDTO):
    """DTO for creating a new generation request."""
    
    project_id: str
    input_text: str
    request_settings: Dict[str, Any]
    priority: str = "normal"
    webhook_url: Optional[str] = None
    
    def validate(self) -> None:
        """Validate generation request create DTO."""
        validate_required_fields(self, ['project_id', 'input_text', 'request_settings'])
        
        if not self.input_text.strip():
            raise ValueError("Input text cannot be empty")
        
        if len(self.input_text) > 100000:
            raise ValueError("Input text must be 100,000 characters or less")
        
        if self.priority not in ["normal", "high"]:
            raise ValueError("Priority must be 'normal' or 'high'")
        
        if self.webhook_url is not None:
            validate_field_length(self, {'webhook_url': (10, 500)})
            if not self.webhook_url.startswith(('http://', 'https://')):
                raise ValueError("Webhook URL must be a valid HTTP/HTTPS URL")


@dataclass
class GenerationRequestUpdateDTO(BaseDTO):
    """DTO for updating generation request information."""
    
    status: Optional[str] = None
    current_module: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    priority: Optional[str] = None
    
    def validate(self) -> None:
        """Validate generation request update DTO."""
        if self.status is not None:
            valid_statuses = ["queued", "processing", "completed", "error"]
            if self.status not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if self.current_module is not None:
            if not (0 <= self.current_module <= 7):
                raise ValueError("Current module must be between 0 and 7")
        
        if self.priority is not None:
            if self.priority not in ["normal", "high"]:
                raise ValueError("Priority must be 'normal' or 'high'")
        
        if self.started_at and self.completed_at:
            if self.completed_at <= self.started_at:
                raise ValueError("Completed time must be after started time")


@dataclass
class GenerationRequestStatsDTO(StatsDTO):
    """DTO for generation request statistics."""
    
    total_requests: int = 0
    queued_requests: int = 0
    processing_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    
    # Performance metrics
    average_processing_time_seconds: float = 0.0
    average_queue_time_seconds: float = 0.0
    success_rate: float = 0.0
    retry_rate: float = 0.0
    
    # Phase-specific metrics
    phase_stats: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    bottleneck_phases: List[int] = field(default_factory=list)
    
    # Quality metrics
    average_quality_score: float = 0.0
    feedback_rate: float = 0.0
    average_feedback_per_request: float = 0.0
    
    # Resource utilization
    total_api_calls: int = 0
    total_processing_cost: float = 0.0
    
    # Trends (compared to previous period)
    requests_trend_percentage: float = 0.0
    success_rate_trend: float = 0.0
    
    def calculate_derived_stats(self) -> None:
        """Calculate derived statistics."""
        # Success rate
        if self.total_requests > 0:
            self.success_rate = self.completed_requests / self.total_requests * 100
        
        # Retry rate
        if self.total_requests > 0:
            retried_requests = sum(
                stats.get('retry_count', 0) for stats in self.phase_stats.values()
            )
            self.retry_rate = retried_requests / self.total_requests * 100


@dataclass
class GenerationRequestProgressDTO(BaseDTO):
    """DTO for generation request progress information."""
    
    request_id: str
    current_phase: int
    status: str
    total_phases: int = 7
    progress_percentage: float = 0.0
    
    # Phase details
    phase_statuses: Dict[int, str] = field(default_factory=dict)
    phase_progress: Dict[int, float] = field(default_factory=dict)
    
    # Time estimates
    estimated_completion_at: Optional[datetime] = None
    estimated_remaining_seconds: Optional[float] = None
    
    # Current phase info
    current_phase_name: Optional[str] = None
    current_phase_status: Optional[str] = None
    current_phase_started_at: Optional[datetime] = None
    
    # Feedback status
    is_waiting_feedback: bool = False
    feedback_timeout_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate generation progress DTO."""
        validate_required_fields(self, ['request_id', 'current_phase', 'status'])
        
        if not (0 <= self.current_phase <= self.total_phases):
            raise ValueError(f"Current phase must be between 0 and {self.total_phases}")
        
        if not (0.0 <= self.progress_percentage <= 100.0):
            raise ValueError("Progress percentage must be between 0.0 and 100.0")
        
        valid_statuses = ["queued", "processing", "completed", "error"]
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")


@dataclass
class PhaseExecutionDTO(BaseDTO):
    """DTO for phase execution information."""
    
    execution_id: str
    request_id: str
    phase_number: int
    phase_name: str
    status: str  # pending, processing, feedback_waiting, completed, failed
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    preview_url: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    retry_count: int = 0
    error_details: Optional[Dict[str, Any]] = None
    feedback_timeout: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate phase execution DTO."""
        validate_required_fields(self, [
            'execution_id', 'request_id', 'phase_number', 
            'phase_name', 'status'
        ])
        
        if not (1 <= self.phase_number <= 7):
            raise ValueError("Phase number must be between 1 and 7")
        
        valid_statuses = ["pending", "processing", "feedback_waiting", "completed", "error"]
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        # Validate phase names according to system design
        valid_phases = {
            1: "concept_analysis",
            2: "character_visual",
            3: "plot_structure",
            4: "name_generation",
            5: "scene_generation",
            6: "text_placement",
            7: "final_integration"
        }
        
        expected_name = valid_phases.get(self.phase_number)
        if expected_name and self.phase_name != expected_name:
            raise ValueError(f"Phase {self.phase_number} must be named '{expected_name}'")
        
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("Duration cannot be negative")


@dataclass
class FeedbackRequestDTO(BaseDTO):
    """DTO for feedback request information."""
    
    feedback_id: str
    request_id: str
    phase_number: int
    feedback_type: str  # natural_language, quick_option, skip
    created_at: datetime
    natural_language_input: Optional[str] = None
    quick_option: Optional[str] = None
    intensity: Optional[float] = None
    target_elements: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, processing, completed, failed
    estimated_modification_time: Optional[int] = None
    timeout_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    # Results
    modifications: Optional[List['ModificationHistoryDTO']] = None
    
    def validate(self) -> None:
        """Validate feedback request DTO."""
        validate_required_fields(self, [
            'feedback_id', 'request_id', 'phase_number', 
            'feedback_type', 'status'
        ])
        
        if not (1 <= self.phase_number <= 7):
            raise ValueError("Phase number must be between 1 and 7")
        
        valid_types = ["natural_language", "quick_option", "skip"]
        if self.feedback_type not in valid_types:
            raise ValueError(f"Feedback type must be one of: {', '.join(valid_types)}")
        
        valid_statuses = ["pending", "processing", "completed", "error"]
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if self.feedback_type == "natural_language":
            if not self.natural_language_input:
                raise ValueError("Natural language input is required for natural_language feedback")
            validate_field_length(self, {'natural_language_input': (1, 5000)})
        
        if self.feedback_type == "quick_option":
            if not self.quick_option:
                raise ValueError("Quick option is required for quick_option feedback")
            validate_field_length(self, {'quick_option': (1, 50)})
        
        if self.intensity is not None:
            if not (0.0 <= self.intensity <= 1.0):
                raise ValueError("Intensity must be between 0.0 and 1.0")


@dataclass
class ModificationHistoryDTO(BaseDTO):
    """DTO for modification history information."""
    
    modification_id: str
    feedback_id: str
    modification_type: str
    target_element: str
    applied_at: datetime
    original_value: Optional[Dict[str, Any]] = None
    modified_value: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    llm_reasoning: Optional[str] = None
    
    def validate(self) -> None:
        """Validate modification history DTO."""
        validate_required_fields(self, [
            'modification_id', 'feedback_id', 'modification_type',
            'target_element'
        ])
        
        validate_field_length(self, {'target_element': (1, 100)})
        
        if self.confidence_score is not None:
            if not (0.0 <= self.confidence_score <= 1.0):
                raise ValueError("Confidence score must be between 0.0 and 1.0")


@dataclass
class GenerationQueueItemDTO(BaseDTO):
    """DTO for generation queue item (admin view)."""
    
    request_id: str
    user_id: str
    project_id: str
    priority: str
    status: str
    created_at: datetime
    estimated_processing_time_seconds: Optional[float] = None
    queue_position: Optional[int] = None
    
    # User context
    user_display_name: Optional[str] = None
    user_account_type: Optional[str] = None
    
    def validate(self) -> None:
        """Validate generation queue item DTO."""
        validate_required_fields(self, [
            'request_id', 'user_id', 'project_id', 
            'priority', 'status'
        ])


@dataclass
class GenerationPerformanceDTO(BaseDTO):
    """DTO for generation performance metrics."""
    
    period_start: datetime
    period_end: datetime
    
    # Overall metrics
    total_requests_processed: int = 0
    average_processing_time_ms: float = 0.0
    median_processing_time_ms: float = 0.0
    p95_processing_time_ms: float = 0.0
    
    # Phase breakdown
    phase_performance: Dict[int, Dict[str, float]] = field(default_factory=dict)
    
    # Error analysis
    error_rate: float = 0.0
    common_errors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Resource utilization
    peak_concurrent_requests: int = 0
    average_concurrent_requests: float = 0.0
    api_calls_per_request: float = 0.0
    
    def validate(self) -> None:
        """Validate generation performance DTO."""
        validate_required_fields(self, ['period_start', 'period_end'])
        
        if self.period_start >= self.period_end:
            raise ValueError("Period start must be before period end")

@dataclass
class QueueStatsDTO(BaseDTO):
    """DTO for generation queue statistics."""

    queued_count: int
    processing_count: int
    completed_count: int
    failed_count: int
    average_wait_time_seconds: float
    estimated_wait_time_seconds: float
    total_processed_today: int

    def validate(self) -> None:
        """Validate queue stats DTO."""
        if any(value < 0 for value in [
            self.queued_count,
            self.processing_count,
            self.completed_count,
            self.failed_count,
            self.total_processed_today
        ]):
            raise ValueError("Queue counts cannot be negative")
        if self.average_wait_time_seconds < 0 or self.estimated_wait_time_seconds < 0:
            raise ValueError("Wait times cannot be negative")
