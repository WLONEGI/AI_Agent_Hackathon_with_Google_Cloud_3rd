"""Processing module related commands for CQRS pattern."""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .base_command import Command, RequireUserMixin, RequireIdMixin, CommandValidationError


@dataclass(kw_only=True)
class StartProcessingModuleCommand(Command[str], RequireUserMixin, RequireIdMixin):
    """Command to start a processing module."""
    
    request_id: str
    module_number: int
    module_name: str
    input_data: Optional[Dict[str, Any]] = None
    
    def validate(self) -> None:
        """Validate start processing module command."""
        self.validate_user_required()
        self.validate_id_required("request_id")
        
        if not (1 <= self.module_number <= 7):
            raise CommandValidationError("Module number must be between 1 and 7")
        
        if not self.module_name or not self.module_name.strip():
            raise CommandValidationError("Module name is required")
        
        # Validate module names according to the system design
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
            raise CommandValidationError(f"Module {self.module_number} must be named '{expected_name}'")


@dataclass(kw_only=True)
class CompleteProcessingModuleCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to complete a processing module."""
    
    module_id: str
    status: str  # completed, failed
    output_data: Optional[Dict[str, Any]] = None
    checkpoint_data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def validate(self) -> None:
        """Validate complete processing module command."""
        self.validate_user_required()
        self.validate_id_required("module_id")
        
        if self.status not in ["completed", "error"]:
            raise CommandValidationError("Status must be 'completed' or 'failed'")
        
        if self.status == "error" and not self.error_message:
            raise CommandValidationError("Error message is required when status is 'failed'")
        
        if self.status == "completed" and not self.output_data:
            raise CommandValidationError("Output data is required when status is 'completed'")
        
        if self.duration_ms is not None and self.duration_ms < 0:
            raise CommandValidationError("Duration cannot be negative")
        
        if self.completed_at is not None and self.completed_at > datetime.utcnow():
            raise CommandValidationError("Completion time cannot be in the future")


@dataclass(kw_only=True)
class FailProcessingModuleCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to fail a processing module."""
    
    module_id: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    failed_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate fail processing module command."""
        self.validate_user_required()
        self.validate_id_required("module_id")
        
        if not self.error_message or not self.error_message.strip():
            raise CommandValidationError("Error message is required")
        
        if self.failed_at is not None and self.failed_at > datetime.utcnow():
            raise CommandValidationError("Failed time cannot be in the future")


@dataclass(kw_only=True)
class RetryProcessingModuleCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to retry a failed processing module."""
    
    module_id: str
    reason: Optional[str] = None
    reset_checkpoint: bool = False
    new_input_data: Optional[Dict[str, Any]] = None
    
    def validate(self) -> None:
        """Validate retry processing module command."""
        self.validate_user_required()
        self.validate_id_required("module_id")


@dataclass(kw_only=True)
class UpdateProcessingModuleCheckpointCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to update processing module checkpoint."""
    
    module_id: str
    checkpoint_data: Dict[str, Any]
    checkpoint_timestamp: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate update checkpoint command."""
        self.validate_user_required()
        self.validate_id_required("module_id")
        
        if not self.checkpoint_data:
            raise CommandValidationError("Checkpoint data is required")
        
        if self.checkpoint_timestamp is not None and self.checkpoint_timestamp > datetime.utcnow():
            raise CommandValidationError("Checkpoint timestamp cannot be in the future")


@dataclass(kw_only=True)
class RecordModuleMetricsCommand(Command[str], RequireUserMixin, RequireIdMixin):
    """Command to record processing module metrics."""
    
    module_id: str
    metric_name: str
    metric_value: float
    unit: Optional[str] = None
    metric_timestamp: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate record metrics command."""
        self.validate_user_required()
        self.validate_id_required("module_id")
        
        if not self.metric_name or not self.metric_name.strip():
            raise CommandValidationError("Metric name is required")
        
        if len(self.metric_name) > 100:
            raise CommandValidationError("Metric name must be 100 characters or less")
        
        if self.unit is not None and len(self.unit) > 20:
            raise CommandValidationError("Unit must be 20 characters or less")
        
        if self.metric_timestamp is not None and self.metric_timestamp > datetime.utcnow():
            raise CommandValidationError("Metric timestamp cannot be in the future")


@dataclass(kw_only=True)
class CreatePhaseExecutionCommand(Command[str], RequireUserMixin, RequireIdMixin):
    """Command to create a phase execution record."""
    
    request_id: str
    phase_number: int
    phase_name: str
    input_data: Optional[Dict[str, Any]] = None
    feedback_timeout: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate create phase execution command."""
        self.validate_user_required()
        self.validate_id_required("request_id")
        
        if not (1 <= self.phase_number <= 7):
            raise CommandValidationError("Phase number must be between 1 and 7")
        
        if not self.phase_name or not self.phase_name.strip():
            raise CommandValidationError("Phase name is required")
        
        # Validate phase names according to the system design
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
            raise CommandValidationError(f"Phase {self.phase_number} must be named '{expected_name}'")
        
        if self.feedback_timeout is not None:
            if self.feedback_timeout <= datetime.utcnow():
                raise CommandValidationError("Feedback timeout must be in the future")


@dataclass 
class CompletePhaseExecutionCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to complete a phase execution."""
    
    execution_id: str
    status: str  # completed, failed, feedback_waiting
    output_data: Optional[Dict[str, Any]] = None
    preview_url: Optional[str] = None
    duration_ms: Optional[int] = None
    error_details: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate complete phase execution command."""
        self.validate_user_required()
        self.validate_id_required("execution_id")
        
        valid_statuses = ["completed", "error", "feedback_waiting"]
        if self.status not in valid_statuses:
            raise CommandValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if self.status == "completed" and not self.output_data:
            raise CommandValidationError("Output data is required when status is 'completed'")
        
        if self.preview_url is not None and len(self.preview_url) > 500:
            raise CommandValidationError("Preview URL must be 500 characters or less")
        
        if self.duration_ms is not None and self.duration_ms < 0:
            raise CommandValidationError("Duration cannot be negative")
        
        if self.completed_at is not None and self.completed_at > datetime.utcnow():
            raise CommandValidationError("Completion time cannot be in the future")