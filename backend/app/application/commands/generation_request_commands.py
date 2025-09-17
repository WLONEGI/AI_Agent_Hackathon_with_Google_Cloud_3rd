"""Generation request related commands for CQRS pattern."""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .base_command import Command, RequireUserMixin, RequireIdMixin, CommandValidationError


@dataclass(kw_only=True)
class CreateGenerationRequestCommand(Command[str], RequireUserMixin):
    """Command to create a new generation request."""
    
    project_id: str
    input_text: str
    request_settings: Dict[str, Any]
    priority: str = "normal"  # normal, high
    webhook_url: Optional[str] = None
    
    def validate(self) -> None:
        """Validate create generation request command."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if not self.input_text or not self.input_text.strip():
            raise CommandValidationError("Input text is required")
        
        if len(self.input_text) > 100000:  # 100K character limit
            raise CommandValidationError("Input text must be 100,000 characters or less")
        
        if not self.request_settings:
            raise CommandValidationError("Request settings are required")
        
        if self.priority not in ["normal", "high"]:
            raise CommandValidationError("Priority must be 'normal' or 'high'")
        
        if self.webhook_url is not None:
            if len(self.webhook_url) > 500:
                raise CommandValidationError("Webhook URL must be 500 characters or less")
            if not self.webhook_url.startswith(('http://', 'https://')):
                raise CommandValidationError("Webhook URL must be a valid HTTP/HTTPS URL")


@dataclass(kw_only=True)
class UpdateGenerationRequestStatusCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to update generation request status."""
    
    request_id: str
    status: str  # queued, processing, completed, failed
    current_module: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate update status command."""
        self.validate_user_required()
        self.validate_id_required("request_id")
        
        valid_statuses = ["queued", "processing", "completed", "error"]
        if self.status not in valid_statuses:
            raise CommandValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if self.status == "error" and not self.error_message:
            raise CommandValidationError("Error message is required when status is 'failed'")
        
        if self.current_module is not None:
            if not (0 <= self.current_module <= 7):
                raise CommandValidationError("Current module must be between 0 and 7")
        
        if self.started_at and self.completed_at:
            if self.completed_at <= self.started_at:
                raise CommandValidationError("Completed time must be after started time")


@dataclass(kw_only=True)
class RetryGenerationRequestCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to retry a failed generation request."""
    
    request_id: str
    reason: Optional[str] = None
    reset_module: Optional[int] = None
    
    def validate(self) -> None:
        """Validate retry generation request command."""
        self.validate_user_required()
        self.validate_id_required("request_id")
        
        if self.reset_module is not None:
            if not (0 <= self.reset_module <= 7):
                raise CommandValidationError("Reset module must be between 0 and 7")


@dataclass(kw_only=True)
class CancelGenerationRequestCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to cancel a generation request."""
    
    request_id: str
    reason: Optional[str] = None
    
    def validate(self) -> None:
        """Validate cancel generation request command."""
        self.validate_user_required()
        self.validate_id_required("request_id")


@dataclass(kw_only=True)
class ProcessFeedbackCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to process user feedback for a generation request."""
    
    request_id: str
    phase_number: int
    feedback_type: str  # natural_language, quick_option, skip
    natural_language_input: Optional[str] = None
    quick_option: Optional[str] = None
    intensity: Optional[float] = None
    target_elements: Optional[Dict[str, Any]] = None
    timeout_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate process feedback command."""
        self.validate_user_required()
        self.validate_id_required("request_id")
        
        if not (1 <= self.phase_number <= 7):
            raise CommandValidationError("Phase number must be between 1 and 7")
        
        valid_types = ["natural_language", "quick_option", "skip"]
        if self.feedback_type not in valid_types:
            raise CommandValidationError(f"Feedback type must be one of: {', '.join(valid_types)}")
        
        if self.feedback_type == "natural_language":
            if not self.natural_language_input or not self.natural_language_input.strip():
                raise CommandValidationError("Natural language input is required for natural_language feedback")
            if len(self.natural_language_input) > 5000:
                raise CommandValidationError("Natural language input must be 5000 characters or less")
        
        if self.feedback_type == "quick_option":
            if not self.quick_option or not self.quick_option.strip():
                raise CommandValidationError("Quick option is required for quick_option feedback")
            if len(self.quick_option) > 50:
                raise CommandValidationError("Quick option must be 50 characters or less")
        
        if self.intensity is not None:
            if not (0.0 <= self.intensity <= 1.0):
                raise CommandValidationError("Intensity must be between 0.0 and 1.0")
        
        if self.timeout_at is not None:
            if self.timeout_at <= datetime.utcnow():
                raise CommandValidationError("Timeout must be in the future")


@dataclass(kw_only=True)
class UpdateGenerationProgressCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to update generation progress."""
    
    request_id: str
    current_phase: int
    phase_status: str  # pending, processing, feedback_waiting, completed, failed
    progress_percentage: float
    estimated_completion: Optional[datetime] = None
    phase_data: Optional[Dict[str, Any]] = None
    
    def validate(self) -> None:
        """Validate update progress command."""
        self.validate_user_required()
        self.validate_id_required("request_id")
        
        if not (1 <= self.current_phase <= 7):
            raise CommandValidationError("Current phase must be between 1 and 7")
        
        valid_statuses = ["pending", "processing", "feedback_waiting", "completed", "error"]
        if self.phase_status not in valid_statuses:
            raise CommandValidationError(f"Phase status must be one of: {', '.join(valid_statuses)}")
        
        if not (0.0 <= self.progress_percentage <= 100.0):
            raise CommandValidationError("Progress percentage must be between 0.0 and 100.0")
        
        if self.estimated_completion is not None:
            if self.estimated_completion <= datetime.utcnow():
                raise CommandValidationError("Estimated completion must be in the future")


@dataclass(kw_only=True)
class CreateFeedbackRequestCommand(Command[str], RequireUserMixin, RequireIdMixin):
    """Command to create a feedback request."""
    
    request_id: str
    phase_number: int
    feedback_type: str
    natural_language_input: Optional[str] = None
    quick_option: Optional[str] = None
    intensity: Optional[float] = None
    target_elements: Optional[Dict[str, Any]] = None
    estimated_modification_time: Optional[int] = None
    timeout_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate create feedback request command."""
        self.validate_user_required()
        self.validate_id_required("request_id")
        
        if not (1 <= self.phase_number <= 7):
            raise CommandValidationError("Phase number must be between 1 and 7")
        
        valid_types = ["natural_language", "quick_option", "skip"]
        if self.feedback_type not in valid_types:
            raise CommandValidationError(f"Feedback type must be one of: {', '.join(valid_types)}")
        
        if self.intensity is not None:
            if not (0.0 <= self.intensity <= 1.0):
                raise CommandValidationError("Intensity must be between 0.0 and 1.0")
        
        if self.estimated_modification_time is not None:
            if self.estimated_modification_time < 0:
                raise CommandValidationError("Estimated modification time cannot be negative")


@dataclass(kw_only=True)
class CompleteFeedbackRequestCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to complete a feedback request."""
    
    feedback_id: str
    status: str  # completed, failed
    processing_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate complete feedback request command."""
        self.validate_user_required()
        self.validate_id_required("feedback_id")
        
        if self.status not in ["completed", "error"]:
            raise CommandValidationError("Status must be 'completed' or 'failed'")
        
        if self.status == "error" and not self.error_message:
            raise CommandValidationError("Error message is required when status is 'failed'")
        
        if self.status == "completed" and not self.processing_result:
            raise CommandValidationError("Processing result is required when status is 'completed'")