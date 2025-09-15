"""Manga Session domain entity."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from app.domain.manga.value_objects.quality_metrics import QualityScore
from app.domain.manga.value_objects.generation_params import GenerationParameters
from app.domain.common.events import DomainEvent


class SessionStatus(str, Enum):
    """Session status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_FEEDBACK = "waiting_feedback"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "error"
    CANCELLED = "cancelled"


class SessionId:
    """Session identifier value object."""
    
    def __init__(self, value: Optional[str] = None):
        self._value = value or str(uuid4())
    
    @property
    def value(self) -> str:
        return self._value
    
    def __str__(self) -> str:
        return self._value
    
    def __eq__(self, other) -> bool:
        return isinstance(other, SessionId) and self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value)


@dataclass
class MangaSession:
    """Manga generation session domain entity."""
    
    # Identity
    id: SessionId = field(default_factory=SessionId)
    user_id: str = field(default="")
    
    # Basic information
    title: Optional[str] = field(default=None)
    input_text: str = field(default="")
    
    # Status and timestamps
    status: SessionStatus = field(default=SessionStatus.PENDING)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = field(default=None)
    completed_at: Optional[datetime] = field(default=None)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Generation parameters
    generation_params: GenerationParameters = field(default_factory=GenerationParameters)
    
    # Progress tracking
    current_phase: int = field(default=0)
    total_phases: int = field(default=7)
    phase_results: Dict[int, Any] = field(default_factory=dict)
    
    # Quality and metrics
    quality_scores: Dict[int, QualityScore] = field(default_factory=dict)
    quality_score: Optional[float] = field(default=None)
    total_processing_time_ms: Optional[int] = field(default=None)
    
    # Output and preview
    preview_url: Optional[str] = field(default=None)
    download_url: Optional[str] = field(default=None)
    output_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Error handling
    error_message: Optional[str] = field(default=None)
    retry_count: int = field(default=0)
    
    # HITL and feedback
    hitl_enabled: bool = field(default=True)
    feedback_sessions: List[str] = field(default_factory=list)
    
    # Domain events
    _events: List[DomainEvent] = field(default_factory=list, init=False)
    
    def start_generation(self) -> None:
        """Start the manga generation process."""
        if self.status != SessionStatus.PENDING:
            raise ValueError(f"Cannot start generation from status: {self.status}")
        
        self.status = SessionStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.current_phase = 1
        self.updated_at = datetime.utcnow()
        
        # Add domain event
        self._add_event(SessionStartedEvent(
            session_id=self.id,
            user_id=self.user_id,
            timestamp=self.started_at
        ))
    
    def advance_to_phase(self, phase_number: int) -> None:
        """Advance to specific phase."""
        if phase_number < 1 or phase_number > self.total_phases:
            raise ValueError(f"Invalid phase number: {phase_number}")
        
        if phase_number <= self.current_phase:
            raise ValueError(f"Cannot go backward to phase {phase_number}")
        
        previous_phase = self.current_phase
        self.current_phase = phase_number
        self.updated_at = datetime.utcnow()
        
        # Add domain event
        self._add_event(PhaseAdvancedEvent(
            session_id=self.id,
            previous_phase=previous_phase,
            current_phase=phase_number,
            timestamp=datetime.utcnow()
        ))
    
    def complete_phase(
        self, 
        phase_number: int, 
        result: Any, 
        quality_score: Optional[QualityScore] = None
    ) -> None:
        """Complete a phase with results."""
        if phase_number != self.current_phase:
            raise ValueError(f"Cannot complete phase {phase_number}, current phase is {self.current_phase}")
        
        self.phase_results[phase_number] = result
        
        if quality_score:
            self.quality_scores[phase_number] = quality_score
        
        self.updated_at = datetime.utcnow()
        
        # Add domain event
        self._add_event(PhaseCompletedEvent(
            session_id=self.id,
            phase_number=phase_number,
            quality_score=quality_score.overall_score if quality_score else None,
            timestamp=datetime.utcnow()
        ))
        
        # Check if this is the final phase
        if phase_number == self.total_phases:
            self.complete_generation()
    
    def request_feedback(self, phase_number: int) -> None:
        """Request HITL feedback for a phase."""
        if not self.hitl_enabled:
            raise ValueError("HITL feedback is not enabled for this session")
        
        self.status = SessionStatus.WAITING_FEEDBACK
        self.updated_at = datetime.utcnow()
        
        # Add domain event
        self._add_event(FeedbackRequestedEvent(
            session_id=self.id,
            phase_number=phase_number,
            timestamp=datetime.utcnow()
        ))
    
    def receive_feedback(self, phase_number: int, feedback: Dict[str, Any]) -> None:
        """Receive HITL feedback and continue processing."""
        if self.status != SessionStatus.WAITING_FEEDBACK:
            raise ValueError("Session is not waiting for feedback")
        
        self.status = SessionStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
        
        # Store feedback in session
        feedback_key = f"feedback_{phase_number}_{datetime.utcnow().timestamp()}"
        self.feedback_sessions.append(feedback_key)
        
        # Add domain event
        self._add_event(FeedbackReceivedEvent(
            session_id=self.id,
            phase_number=phase_number,
            feedback_key=feedback_key,
            timestamp=datetime.utcnow()
        ))
    
    def pause_generation(self, reason: Optional[str] = None) -> None:
        """Pause the generation process."""
        if self.status not in [SessionStatus.IN_PROGRESS, SessionStatus.WAITING_FEEDBACK]:
            raise ValueError(f"Cannot pause generation from status: {self.status}")
        
        self.status = SessionStatus.PAUSED
        self.updated_at = datetime.utcnow()
        
        if reason:
            self.error_message = reason
        
        # Add domain event
        self._add_event(SessionPausedEvent(
            session_id=self.id,
            reason=reason,
            timestamp=datetime.utcnow()
        ))
    
    def resume_generation(self) -> None:
        """Resume paused generation."""
        if self.status != SessionStatus.PAUSED:
            raise ValueError(f"Cannot resume generation from status: {self.status}")
        
        self.status = SessionStatus.IN_PROGRESS
        self.error_message = None
        self.updated_at = datetime.utcnow()
        
        # Add domain event
        self._add_event(SessionResumedEvent(
            session_id=self.id,
            timestamp=datetime.utcnow()
        ))
    
    def complete_generation(self) -> None:
        """Complete the entire generation process."""
        if self.status not in [SessionStatus.IN_PROGRESS, SessionStatus.WAITING_FEEDBACK]:
            raise ValueError(f"Cannot complete generation from status: {self.status}")
        
        self.status = SessionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Calculate final quality score
        if self.quality_scores:
            self.quality_score = self._calculate_final_quality()

        # Calculate total processing time in milliseconds
        if self.started_at:
            self.total_processing_time_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        
        # Add domain event
        self._add_event(SessionCompletedEvent(
            session_id=self.id,
            quality_score=self.quality_score,
            total_processing_time_ms=self.total_processing_time_ms,
            timestamp=self.completed_at
        ))
    
    def fail_generation(self, error_message: str) -> None:
        """Mark generation as failed."""
        self.status = SessionStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Calculate processing time even for failed sessions in milliseconds
        if self.started_at:
            self.total_processing_time_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        
        # Add domain event
        self._add_event(SessionFailedEvent(
            session_id=self.id,
            error_message=error_message,
            timestamp=self.completed_at
        ))
    
    def cancel_generation(self, reason: Optional[str] = None) -> None:
        """Cancel the generation process."""
        if self.status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel generation from status: {self.status}")
        
        self.status = SessionStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if reason:
            self.error_message = reason
        
        # Calculate processing time in milliseconds
        if self.started_at:
            self.total_processing_time_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        
        # Add domain event
        self._add_event(SessionCancelledEvent(
            session_id=self.id,
            reason=reason,
            timestamp=self.completed_at
        ))
    
    def retry_generation(self) -> None:
        """Retry failed generation."""
        if self.status != SessionStatus.FAILED:
            raise ValueError("Can only retry failed generations")
        
        self.retry_count += 1
        self.status = SessionStatus.IN_PROGRESS
        self.error_message = None
        self.started_at = datetime.utcnow()
        self.completed_at = None
        self.updated_at = datetime.utcnow()
        
        # Add domain event
        self._add_event(SessionRetriedEvent(
            session_id=self.id,
            retry_count=self.retry_count,
            timestamp=datetime.utcnow()
        ))
    
    def update_preview_urls(self, preview_url: str, download_url: Optional[str] = None) -> None:
        """Update preview and download URLs."""
        self.preview_url = preview_url
        if download_url:
            self.download_url = download_url
        self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """Check if session is actively being processed."""
        return self.status in [SessionStatus.IN_PROGRESS, SessionStatus.WAITING_FEEDBACK]
    
    def is_completed(self) -> bool:
        """Check if session is completed successfully."""
        return self.status == SessionStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if session has failed."""
        return self.status in [SessionStatus.FAILED, SessionStatus.CANCELLED]
    
    def can_receive_feedback(self) -> bool:
        """Check if session can receive HITL feedback."""
        return self.hitl_enabled and self.status == SessionStatus.WAITING_FEEDBACK
    
    def get_progress_percentage(self) -> float:
        """Get progress percentage (0.0 to 1.0)."""
        if self.total_phases == 0:
            return 0.0
        return min(1.0, self.current_phase / self.total_phases)
    
    def get_estimated_remaining_time(self) -> Optional[float]:
        """Get estimated remaining processing time in seconds."""
        if not self.is_active() or not self.started_at:
            return None
        
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        progress = self.get_progress_percentage()
        
        if progress <= 0:
            return None
        
        estimated_total = elapsed / progress
        return max(0, estimated_total - elapsed)
    
    def _calculate_final_quality(self) -> float:
        """Calculate final quality score from all phase scores."""
        if not self.quality_scores:
            return 0.0
        
        # Weighted average of phase quality scores
        phase_weights = {
            1: 0.10,  # Concept
            2: 0.15,  # Character
            3: 0.15,  # Plot
            4: 0.20,  # Name (Critical)
            5: 0.20,  # Image (Critical)
            6: 0.10,  # Dialogue
            7: 0.10   # Integration
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for phase_num, quality_score in self.quality_scores.items():
            if phase_num in phase_weights:
                weight = phase_weights[phase_num]
                weighted_sum += quality_score.overall_score * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _add_event(self, event: DomainEvent) -> None:
        """Add domain event to the event list."""
        self._events.append(event)
    
    def get_events(self) -> List[DomainEvent]:
        """Get all domain events for this session."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear all domain events."""
        self._events.clear()


# Domain Events
@dataclass
class SessionStartedEvent(DomainEvent):
    session_id: SessionId = field(default=None)
    user_id: str = field(default="")
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass 
class PhaseAdvancedEvent(DomainEvent):
    session_id: SessionId = field(default=None)
    previous_phase: int = field(default=0)
    current_phase: int = field(default=1)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PhaseCompletedEvent(DomainEvent):
    session_id: SessionId = field(default=None)
    phase_number: int = field(default=0)
    quality_score: Optional[float] = field(default=None)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FeedbackRequestedEvent(DomainEvent):
    session_id: SessionId = field(default=None)
    phase_number: int = field(default=0)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FeedbackReceivedEvent(DomainEvent):
    session_id: SessionId = field(default=None)
    phase_number: int = field(default=0)
    feedback_key: str = field(default="")
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionPausedEvent(DomainEvent):
    session_id: SessionId = field(default=None)
    reason: Optional[str] = field(default=None)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionResumedEvent(DomainEvent):
    session_id: SessionId = field(default=None)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionCompletedEvent(DomainEvent):
    session_id: SessionId = field(default=None)
    quality_score: Optional[float] = field(default=None)
    total_processing_time_ms: Optional[int] = field(default=None)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionFailedEvent(DomainEvent):
    session_id: SessionId = field(default=None)
    error_message: str = field(default="")
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionCancelledEvent(DomainEvent):
    session_id: SessionId = field(default=None)
    reason: Optional[str] = field(default=None)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionRetriedEvent(DomainEvent):
    session_id: SessionId = field(default=None)
    retry_count: int = field(default=0)
    timestamp: datetime = field(default_factory=datetime.utcnow)

