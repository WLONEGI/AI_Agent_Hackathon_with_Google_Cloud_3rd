"""Phase Result domain entity."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from uuid import uuid4
from dataclasses import dataclass, field

from app.domain.manga.value_objects.quality_metrics import QualityScore
from app.domain.common.events import DomainEvent


class PhaseStatus(str, Enum):
    """Phase execution status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class PhaseResultId:
    """Phase result identifier value object."""
    
    def __init__(self, value: Optional[str] = None):
        self._value = value or str(uuid4())
    
    @property
    def value(self) -> str:
        return self._value
    
    def __str__(self) -> str:
        return self._value
    
    def __eq__(self, other) -> bool:
        return isinstance(other, PhaseResultId) and self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value)


@dataclass
class PhaseResult:
    """Phase execution result domain entity."""
    
    # Identity
    id: PhaseResultId = field(default_factory=PhaseResultId)
    session_id: str = field(default="")
    phase_number: int = field(default=0)
    phase_name: str = field(default="")
    
    # Execution status
    status: PhaseStatus = field(default=PhaseStatus.PENDING)
    started_at: Optional[datetime] = field(default=None)
    completed_at: Optional[datetime] = field(default=None)
    processing_time: Optional[float] = field(default=None)
    
    # Input and output
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    intermediate_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Quality metrics
    quality_score: Optional[QualityScore] = field(default=None)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    # AI model information
    model_used: Optional[str] = field(default=None)
    prompt_tokens: int = field(default=0)
    completion_tokens: int = field(default=0)
    total_cost_usd: float = field(default=0.0)
    
    # Error handling
    error_message: Optional[str] = field(default=None)
    error_code: Optional[str] = field(default=None)
    retry_count: int = field(default=0)
    max_retries: int = field(default=3)
    
    # Performance metrics
    cpu_usage_percent: float = field(default=0.0)
    memory_usage_mb: float = field(default=0.0)
    api_call_count: int = field(default=0)
    cache_hit_count: int = field(default=0)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Domain events
    _events: List[DomainEvent] = field(default_factory=list, init=False)
    
    def start_processing(self) -> None:
        """Start phase processing."""
        if self.status != PhaseStatus.PENDING:
            raise ValueError(f"Cannot start processing from status: {self.status}")
        
        self.status = PhaseStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        self._add_event(PhaseStartedEvent(
            phase_result_id=self.id,
            session_id=self.session_id,
            phase_number=self.phase_number,
            timestamp=self.started_at
        ))
    
    def complete_processing(
        self, 
        output_data: Dict[str, Any],
        quality_score: Optional[QualityScore] = None
    ) -> None:
        """Complete phase processing with results."""
        if self.status != PhaseStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete processing from status: {self.status}")
        
        self.status = PhaseStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.output_data = output_data
        self.quality_score = quality_score
        self.updated_at = datetime.utcnow()
        
        # Calculate processing time
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
        
        self._add_event(PhaseCompletedEvent(
            phase_result_id=self.id,
            session_id=self.session_id,
            phase_number=self.phase_number,
            quality_score=quality_score.overall_score if quality_score else None,
            processing_time=self.processing_time,
            timestamp=self.completed_at
        ))
    
    def fail_processing(self, error_message: str, error_code: Optional[str] = None) -> None:
        """Mark phase processing as failed."""
        if self.status not in [PhaseStatus.IN_PROGRESS, PhaseStatus.RETRYING]:
            raise ValueError(f"Cannot fail processing from status: {self.status}")
        
        self.status = PhaseStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_code = error_code
        self.updated_at = datetime.utcnow()
        
        # Calculate processing time even for failed phases
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
        
        self._add_event(PhaseFailedEvent(
            phase_result_id=self.id,
            session_id=self.session_id,
            phase_number=self.phase_number,
            error_message=error_message,
            error_code=error_code,
            timestamp=self.completed_at
        ))
    
    def retry_processing(self) -> None:
        """Retry failed phase processing."""
        if self.status != PhaseStatus.FAILED:
            raise ValueError("Can only retry failed phases")
        
        if self.retry_count >= self.max_retries:
            raise ValueError(f"Maximum retries ({self.max_retries}) exceeded")
        
        self.retry_count += 1
        self.status = PhaseStatus.RETRYING
        self.error_message = None
        self.error_code = None
        self.started_at = datetime.utcnow()
        self.completed_at = None
        self.updated_at = datetime.utcnow()
        
        self._add_event(PhaseRetryEvent(
            phase_result_id=self.id,
            session_id=self.session_id,
            phase_number=self.phase_number,
            retry_count=self.retry_count,
            timestamp=datetime.utcnow()
        ))
    
    def skip_processing(self, reason: str) -> None:
        """Skip phase processing with reason."""
        if self.status not in [PhaseStatus.PENDING, PhaseStatus.IN_PROGRESS]:
            raise ValueError(f"Cannot skip processing from status: {self.status}")
        
        self.status = PhaseStatus.SKIPPED
        self.completed_at = datetime.utcnow()
        self.error_message = reason
        self.updated_at = datetime.utcnow()
        
        # Calculate processing time
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
        
        self._add_event(PhaseSkippedEvent(
            phase_result_id=self.id,
            session_id=self.session_id,
            phase_number=self.phase_number,
            reason=reason,
            timestamp=self.completed_at
        ))
    
    def add_intermediate_result(self, result: Dict[str, Any]) -> None:
        """Add intermediate processing result."""
        self.intermediate_results.append({
            **result,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
    
    def update_performance_metrics(
        self,
        cpu_usage: float,
        memory_usage: float,
        api_calls: int = 0,
        cache_hits: int = 0
    ) -> None:
        """Update performance metrics."""
        self.cpu_usage_percent = cpu_usage
        self.memory_usage_mb = memory_usage
        self.api_call_count += api_calls
        self.cache_hit_count += cache_hits
        self.updated_at = datetime.utcnow()
    
    def update_cost_metrics(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float
    ) -> None:
        """Update AI model cost metrics."""
        self.model_used = model_name
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_cost_usd += cost_usd
        self.updated_at = datetime.utcnow()
    
    def is_completed(self) -> bool:
        """Check if phase processing is completed successfully."""
        return self.status == PhaseStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if phase processing has failed."""
        return self.status == PhaseStatus.FAILED
    
    def is_in_progress(self) -> bool:
        """Check if phase processing is currently active."""
        return self.status in [PhaseStatus.IN_PROGRESS, PhaseStatus.RETRYING]
    
    def can_retry(self) -> bool:
        """Check if phase can be retried."""
        return self.status == PhaseStatus.FAILED and self.retry_count < self.max_retries
    
    def get_efficiency_score(self) -> float:
        """Calculate efficiency score based on performance metrics."""
        if not self.processing_time:
            return 0.0
        
        # Base efficiency on processing time vs expected time
        expected_times = {
            1: 12.0,  # Phase 1: Concept
            2: 18.0,  # Phase 2: Character
            3: 15.0,  # Phase 3: Plot
            4: 20.0,  # Phase 4: Name
            5: 25.0,  # Phase 5: Image
            6: 4.0,   # Phase 6: Dialogue
            7: 3.0    # Phase 7: Integration
        }
        
        expected_time = expected_times.get(self.phase_number, 10.0)
        time_efficiency = expected_time / max(self.processing_time, 0.1)
        
        # Factor in cache hit rate
        if self.api_call_count > 0:
            cache_efficiency = self.cache_hit_count / self.api_call_count
        else:
            cache_efficiency = 1.0
        
        # Factor in quality score
        quality_efficiency = self.quality_score.overall_score if self.quality_score else 0.5
        
        # Weighted efficiency score
        efficiency = (
            time_efficiency * 0.4 +
            cache_efficiency * 0.3 +
            quality_efficiency * 0.3
        )
        
        return min(1.0, efficiency)  # Cap at 1.0
    
    def _add_event(self, event: DomainEvent) -> None:
        """Add domain event to the event list."""
        self._events.append(event)
    
    def get_events(self) -> List[DomainEvent]:
        """Get all domain events for this phase result."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear all domain events."""
        self._events.clear()


# Domain Events
@dataclass
class PhaseStartedEvent(DomainEvent):
    phase_result_id: PhaseResultId
    session_id: str
    phase_number: int
    timestamp: datetime


@dataclass
class PhaseCompletedEvent(DomainEvent):
    phase_result_id: PhaseResultId
    session_id: str
    phase_number: int
    quality_score: Optional[float]
    processing_time: Optional[float]
    timestamp: datetime


@dataclass
class PhaseFailedEvent(DomainEvent):
    phase_result_id: PhaseResultId
    session_id: str
    phase_number: int
    error_message: str
    error_code: Optional[str]
    timestamp: datetime


@dataclass
class PhaseRetryEvent(DomainEvent):
    phase_result_id: PhaseResultId
    session_id: str
    phase_number: int
    retry_count: int
    timestamp: datetime


@dataclass
class PhaseSkippedEvent(DomainEvent):
    phase_result_id: PhaseResultId
    session_id: str
    phase_number: int
    reason: str
    timestamp: datetime