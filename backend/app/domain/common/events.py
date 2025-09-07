"""Domain events base classes."""

from abc import ABC
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class DomainEvent(ABC):
    """Base class for all domain events."""
    
    # Event metadata
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_version: int = field(default=1)
    
    # Event source
    aggregate_id: Optional[str] = field(default=None)
    aggregate_type: Optional[str] = field(default=None)
    
    # Event context
    correlation_id: Optional[str] = field(default=None)
    causation_id: Optional[str] = field(default=None)
    user_id: Optional[str] = field(default=None)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_event_type(self) -> str:
        """Get event type name."""
        return self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.get_event_type(),
            "occurred_at": self.occurred_at.isoformat(),
            "event_version": self.event_version,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "payload": self._get_payload()
        }
    
    def _get_payload(self) -> Dict[str, Any]:
        """Get event-specific payload data."""
        # Get all fields except the base DomainEvent fields
        payload = {}
        for key, value in self.__dict__.items():
            if key not in ["event_id", "occurred_at", "event_version", 
                          "aggregate_id", "aggregate_type", "correlation_id", 
                          "causation_id", "user_id", "metadata"]:
                if hasattr(value, 'value'):  # Handle value objects
                    payload[key] = value.value
                elif hasattr(value, 'isoformat'):  # Handle datetime
                    payload[key] = value.isoformat()
                else:
                    payload[key] = value
        return payload
    
    def with_correlation(self, correlation_id: str) -> "DomainEvent":
        """Create new event with correlation ID."""
        return dataclass.replace(self, correlation_id=correlation_id)
    
    def with_causation(self, causation_id: str) -> "DomainEvent":
        """Create new event with causation ID."""
        return dataclass.replace(self, causation_id=causation_id)
    
    def with_user(self, user_id: str) -> "DomainEvent":
        """Create new event with user ID."""
        return dataclass.replace(self, user_id=user_id)
    
    def with_metadata(self, **metadata: Any) -> "DomainEvent":
        """Create new event with additional metadata."""
        new_metadata = {**self.metadata, **metadata}
        return dataclass.replace(self, metadata=new_metadata)


@dataclass
class IntegrationEvent(DomainEvent):
    """Base class for integration events that cross bounded contexts."""
    
    # Integration specific fields
    published_at: Optional[datetime] = field(default=None)
    retry_count: int = field(default=0)
    max_retries: int = field(default=3)
    
    def mark_published(self) -> "IntegrationEvent":
        """Mark event as published."""
        return dataclass.replace(self, published_at=datetime.utcnow())
    
    def increment_retry(self) -> "IntegrationEvent":
        """Increment retry count."""
        return dataclass.replace(self, retry_count=self.retry_count + 1)
    
    def can_retry(self) -> bool:
        """Check if event can be retried."""
        return self.retry_count < self.max_retries


# Common domain event types
@dataclass
class EntityCreatedEvent(DomainEvent):
    """Event raised when an entity is created."""
    entity_type: str = field(default="")
    entity_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityUpdatedEvent(DomainEvent):
    """Event raised when an entity is updated."""
    entity_type: str = field(default="")
    changed_fields: Dict[str, Any] = field(default_factory=dict)
    previous_values: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityDeletedEvent(DomainEvent):
    """Event raised when an entity is deleted."""
    entity_type: str = field(default="")
    entity_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessStartedEvent(DomainEvent):
    """Event raised when a business process starts."""
    process_name: str = field(default="")
    process_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessCompletedEvent(DomainEvent):
    """Event raised when a business process completes."""
    process_name: str = field(default="")
    process_result: Dict[str, Any] = field(default_factory=dict)
    processing_time_seconds: Optional[float] = field(default=None)


@dataclass
class ProcessFailedEvent(DomainEvent):
    """Event raised when a business process fails."""
    process_name: str = field(default="")
    error_message: str = field(default="")
    error_code: Optional[str] = field(default=None)
    retry_count: int = field(default=0)


@dataclass 
class ValidationFailedEvent(DomainEvent):
    """Event raised when validation fails."""
    validation_type: str = field(default="")
    validation_errors: Dict[str, List[str]] = field(default_factory=dict)
    validated_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityCheckEvent(DomainEvent):
    """Event raised for quality check results."""
    quality_score: float = field(default=0.0)
    quality_details: Dict[str, float] = field(default_factory=dict)
    passed_threshold: bool = field(default=False)
    threshold_value: float = field(default=0.6)