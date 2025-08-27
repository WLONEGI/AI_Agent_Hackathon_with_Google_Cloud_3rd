"""Generated Content domain entity."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from uuid import uuid4
from dataclasses import dataclass, field

from app.domain.manga.value_objects.quality_metrics import QualityScore
from app.domain.common.events import DomainEvent


class ContentType(str, Enum):
    """Content type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    DIALOGUE = "dialogue"
    PANEL_LAYOUT = "panel_layout"
    CHARACTER_DESIGN = "character_design"
    BACKGROUND = "background"
    SOUND_EFFECT = "sound_effect"
    NARRATION = "narration"
    COMPOSITE = "composite"


class ContentStatus(str, Enum):
    """Content generation status."""
    DRAFT = "draft"
    GENERATED = "generated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"
    FINALIZED = "finalized"
    ARCHIVED = "archived"


class ContentFormat(str, Enum):
    """Content format specification."""
    # Text formats
    PLAIN_TEXT = "text/plain"
    MARKDOWN = "text/markdown"
    HTML = "text/html"
    JSON = "application/json"
    
    # Image formats
    PNG = "image/png"
    JPEG = "image/jpeg"
    WEBP = "image/webp"
    SVG = "image/svg+xml"
    
    # Layout formats
    PANEL_JSON = "layout/panel"
    COMPOSITE_JSON = "layout/composite"


class ContentId:
    """Content identifier value object."""
    
    def __init__(self, value: Optional[str] = None):
        self._value = value or str(uuid4())
    
    @property
    def value(self) -> str:
        return self._value
    
    def __str__(self) -> str:
        return self._value
    
    def __eq__(self, other) -> bool:
        return isinstance(other, ContentId) and self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value)


@dataclass
class GeneratedContent:
    """Generated content domain entity."""
    
    # Identity
    id: ContentId = field(default_factory=ContentId)
    session_id: str = field(default="")
    phase_number: int = field(default=0)
    phase_result_id: Optional[str] = field(default=None)
    
    # Content properties
    content_type: ContentType = field(default=ContentType.TEXT)
    content_format: ContentFormat = field(default=ContentFormat.PLAIN_TEXT)
    title: Optional[str] = field(default=None)
    description: Optional[str] = field(default=None)
    
    # Content data
    content_data: Union[str, Dict[str, Any]] = field(default="")
    content_url: Optional[str] = field(default=None)  # For external storage
    content_size_bytes: int = field(default=0)
    content_hash: Optional[str] = field(default=None)  # For deduplication
    
    # Generation metadata
    generated_by: str = field(default="")  # AI model or agent name
    generation_prompt: Optional[str] = field(default=None)
    generation_params: Dict[str, Any] = field(default_factory=dict)
    
    # Status and versioning
    status: ContentStatus = field(default=ContentStatus.DRAFT)
    version: int = field(default=1)
    parent_content_id: Optional[ContentId] = field(default=None)
    child_content_ids: List[ContentId] = field(default_factory=list)
    
    # Quality and validation
    quality_score: Optional[QualityScore] = field(default=None)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    auto_approved: bool = field(default=False)
    
    # Human feedback
    hitl_feedback: Dict[str, Any] = field(default_factory=dict)
    feedback_count: int = field(default=0)
    approval_score: Optional[float] = field(default=None)
    
    # Content relationships
    related_content_ids: List[ContentId] = field(default_factory=list)
    dependencies: List[ContentId] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Performance metrics
    generation_time_seconds: Optional[float] = field(default=None)
    processing_cost_usd: float = field(default=0.0)
    storage_cost_usd: float = field(default=0.0)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = field(default=None)
    finalized_at: Optional[datetime] = field(default=None)
    archived_at: Optional[datetime] = field(default=None)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Domain events
    _events: List[DomainEvent] = field(default_factory=list, init=False)
    
    def generate_content(
        self,
        content_data: Union[str, Dict[str, Any]],
        generated_by: str,
        generation_time: float,
        generation_params: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark content as generated."""
        if self.status != ContentStatus.DRAFT:
            raise ValueError(f"Cannot generate content from status: {self.status}")
        
        self.content_data = content_data
        self.generated_by = generated_by
        self.generation_time_seconds = generation_time
        self.status = ContentStatus.GENERATED
        self.updated_at = datetime.utcnow()
        
        if generation_params:
            self.generation_params = generation_params
        
        # Calculate content size
        if isinstance(content_data, str):
            self.content_size_bytes = len(content_data.encode('utf-8'))
        else:
            import json
            self.content_size_bytes = len(json.dumps(content_data).encode('utf-8'))
        
        self._add_event(ContentGeneratedEvent(
            content_id=self.id,
            session_id=self.session_id,
            content_type=self.content_type,
            generated_by=generated_by,
            generation_time=generation_time,
            timestamp=datetime.utcnow()
        ))
    
    def submit_for_review(self) -> None:
        """Submit content for human review."""
        if self.status != ContentStatus.GENERATED:
            raise ValueError(f"Cannot submit for review from status: {self.status}")
        
        self.status = ContentStatus.REVIEWED
        self.updated_at = datetime.utcnow()
        
        self._add_event(ContentSubmittedForReviewEvent(
            content_id=self.id,
            session_id=self.session_id,
            timestamp=datetime.utcnow()
        ))
    
    def approve_content(self, approval_score: float, feedback: Optional[Dict[str, Any]] = None) -> None:
        """Approve content with optional feedback."""
        if self.status not in [ContentStatus.REVIEWED, ContentStatus.GENERATED]:
            raise ValueError(f"Cannot approve content from status: {self.status}")
        
        self.status = ContentStatus.APPROVED
        self.approval_score = approval_score
        self.approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if feedback:
            self.hitl_feedback = feedback
            self.feedback_count += 1
        
        self._add_event(ContentApprovedEvent(
            content_id=self.id,
            session_id=self.session_id,
            approval_score=approval_score,
            timestamp=self.approved_at
        ))
    
    def reject_content(self, reason: str, feedback: Optional[Dict[str, Any]] = None) -> None:
        """Reject content with reason and feedback."""
        if self.status not in [ContentStatus.REVIEWED, ContentStatus.GENERATED]:
            raise ValueError(f"Cannot reject content from status: {self.status}")
        
        self.status = ContentStatus.REJECTED
        self.updated_at = datetime.utcnow()
        
        rejection_feedback = {"reason": reason}
        if feedback:
            rejection_feedback.update(feedback)
        
        self.hitl_feedback = rejection_feedback
        self.feedback_count += 1
        
        self._add_event(ContentRejectedEvent(
            content_id=self.id,
            session_id=self.session_id,
            reason=reason,
            timestamp=datetime.utcnow()
        ))
    
    def revise_content(
        self,
        new_content_data: Union[str, Dict[str, Any]],
        revision_reason: str,
        generated_by: str
    ) -> None:
        """Create revised version of content."""
        if self.status != ContentStatus.REJECTED:
            raise ValueError(f"Cannot revise content from status: {self.status}")
        
        # Increment version
        self.version += 1
        self.content_data = new_content_data
        self.generated_by = generated_by
        self.status = ContentStatus.REVISED
        self.updated_at = datetime.utcnow()
        
        # Update content size
        if isinstance(new_content_data, str):
            self.content_size_bytes = len(new_content_data.encode('utf-8'))
        else:
            import json
            self.content_size_bytes = len(json.dumps(new_content_data).encode('utf-8'))
        
        self._add_event(ContentRevisedEvent(
            content_id=self.id,
            session_id=self.session_id,
            version=self.version,
            revision_reason=revision_reason,
            timestamp=datetime.utcnow()
        ))
    
    def finalize_content(self) -> None:
        """Finalize approved content."""
        if self.status not in [ContentStatus.APPROVED, ContentStatus.REVISED]:
            raise ValueError(f"Cannot finalize content from status: {self.status}")
        
        self.status = ContentStatus.FINALIZED
        self.finalized_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        self._add_event(ContentFinalizedEvent(
            content_id=self.id,
            session_id=self.session_id,
            timestamp=self.finalized_at
        ))
    
    def archive_content(self, reason: Optional[str] = None) -> None:
        """Archive content."""
        self.status = ContentStatus.ARCHIVED
        self.archived_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if reason:
            self.metadata["archive_reason"] = reason
        
        self._add_event(ContentArchivedEvent(
            content_id=self.id,
            session_id=self.session_id,
            reason=reason,
            timestamp=self.archived_at
        ))
    
    def add_relationship(self, related_content_id: ContentId, relationship_type: str) -> None:
        """Add relationship to another content."""
        if related_content_id not in self.related_content_ids:
            self.related_content_ids.append(related_content_id)
            
        if "relationships" not in self.metadata:
            self.metadata["relationships"] = {}
        
        self.metadata["relationships"][str(related_content_id)] = relationship_type
        self.updated_at = datetime.utcnow()
    
    def add_dependency(self, dependency_id: ContentId) -> None:
        """Add content dependency."""
        if dependency_id not in self.dependencies:
            self.dependencies.append(dependency_id)
            self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str) -> None:
        """Add content tag."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def update_quality_score(self, quality_score: QualityScore) -> None:
        """Update quality score."""
        self.quality_score = quality_score
        self.updated_at = datetime.utcnow()
        
        # Auto-approve if quality score is high enough
        if quality_score.overall_score >= 0.9 and self.status == ContentStatus.GENERATED:
            self.auto_approved = True
            self.approve_content(quality_score.overall_score)
    
    def is_ready_for_use(self) -> bool:
        """Check if content is ready for use."""
        return self.status in [ContentStatus.APPROVED, ContentStatus.FINALIZED]
    
    def is_pending_review(self) -> bool:
        """Check if content is pending human review."""
        return self.status in [ContentStatus.REVIEWED, ContentStatus.GENERATED]
    
    def needs_revision(self) -> bool:
        """Check if content needs revision."""
        return self.status == ContentStatus.REJECTED
    
    def has_dependencies(self) -> bool:
        """Check if content has unmet dependencies."""
        return len(self.dependencies) > 0
    
    def get_content_preview(self, max_length: int = 100) -> str:
        """Get content preview for display."""
        if isinstance(self.content_data, str):
            preview = self.content_data
        else:
            import json
            preview = json.dumps(self.content_data)
        
        if len(preview) > max_length:
            return preview[:max_length] + "..."
        return preview
    
    def calculate_total_cost(self) -> float:
        """Calculate total cost for this content."""
        return self.processing_cost_usd + self.storage_cost_usd
    
    def _add_event(self, event: DomainEvent) -> None:
        """Add domain event to the event list."""
        self._events.append(event)
    
    def get_events(self) -> List[DomainEvent]:
        """Get all domain events for this content."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear all domain events."""
        self._events.clear()


# Domain Events
@dataclass
class ContentGeneratedEvent(DomainEvent):
    content_id: ContentId
    session_id: str
    content_type: ContentType
    generated_by: str
    generation_time: float
    timestamp: datetime


@dataclass
class ContentSubmittedForReviewEvent(DomainEvent):
    content_id: ContentId
    session_id: str
    timestamp: datetime


@dataclass
class ContentApprovedEvent(DomainEvent):
    content_id: ContentId
    session_id: str
    approval_score: float
    timestamp: datetime


@dataclass
class ContentRejectedEvent(DomainEvent):
    content_id: ContentId
    session_id: str
    reason: str
    timestamp: datetime


@dataclass
class ContentRevisedEvent(DomainEvent):
    content_id: ContentId
    session_id: str
    version: int
    revision_reason: str
    timestamp: datetime


@dataclass
class ContentFinalizedEvent(DomainEvent):
    content_id: ContentId
    session_id: str
    timestamp: datetime


@dataclass
class ContentArchivedEvent(DomainEvent):
    content_id: ContentId
    session_id: str
    reason: Optional[str]
    timestamp: datetime