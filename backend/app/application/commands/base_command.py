"""Base command classes for CQRS pattern."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar, Optional, List
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field

T = TypeVar('T')


@dataclass(kw_only=True)
class AbstractCommand(ABC):
    """Abstract base class for all commands in the CQRS pattern.
    
    Commands represent write operations that change system state.
    They should be named in imperative mood (e.g., CreateUser, UpdateProject).
    """
    
    # Command metadata
    command_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    timestamp: datetime = field(default_factory=datetime.utcnow, init=False)
    user_id: Optional[str] = field(default=None, kw_only=True)
    correlation_id: Optional[str] = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        """Initialise optional metadata attributes for downstream use."""
        if not hasattr(self, 'user_id'):
            self.user_id: Optional[str] = None
        if not hasattr(self, 'correlation_id'):
            self.correlation_id: Optional[str] = None
    
    @abstractmethod
    def validate(self) -> None:
        """Validate command data.
        
        Raises:
            ValueError: If command data is invalid
        """
        pass
    
    def get_command_type(self) -> str:
        """Get command type name."""
        return self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary for serialization."""
        return {
            'command_id': self.command_id,
            'command_type': self.get_command_type(),
            'timestamp': self.timestamp.isoformat(),
            'data': self._get_data_dict()
        }
    
    def _get_data_dict(self) -> Dict[str, Any]:
        """Get command-specific data as dictionary."""
        exclude_fields = {'command_id', 'timestamp'}
        return {
            key: value for key, value in self.__dict__.items()
            if key not in exclude_fields and not key.startswith('_')
        }

    def _create_validation_result(self, errors: List[str]) -> None:
        """Raise ValueError if validation errors exist."""
        if errors:
            raise ValueError('; '.join(errors))


@dataclass(kw_only=True)
class Command(AbstractCommand, Generic[T]):
    """Generic command base class with typed result.
    
    Use this for commands that expect a specific result type.
    """
    
    expected_result_type: type = field(default=type(None), init=False)
    
    def __post_init__(self):
        """Set expected result type from generic parameter."""
        super().__post_init__()
        # Extract T from Generic[T] if possible
        if hasattr(self.__class__, '__orig_bases__'):
            for base in self.__class__.__orig_bases__:
                if hasattr(base, '__args__') and base.__args__:
                    self.expected_result_type = base.__args__[0]
                    break


@dataclass(kw_only=True)
class CommandResult(Generic[T]):
    """Result wrapper for command execution.
    
    Implements the Result pattern for consistent error handling.
    """
    
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success_result(cls, data: T, metadata: Optional[Dict[str, Any]] = None) -> 'CommandResult[T]':
        """Create successful result."""
        return cls(
            success=True,
            data=data,
            metadata=metadata or {}
        )
    
    @classmethod
    def error_result(
        cls, 
        error: str, 
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'CommandResult[T]':
        """Create error result."""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            metadata=metadata or {}
        )
    
    @classmethod
    def validation_error(cls, error: str) -> 'CommandResult[T]':
        """Create validation error result."""
        return cls.error_result(error, "VALIDATION_ERROR")
    
    @classmethod
    def not_found_error(cls, resource: str) -> 'CommandResult[T]':
        """Create not found error result."""
        return cls.error_result(f"{resource} not found", "NOT_FOUND")
    
    @classmethod
    def permission_error(cls, action: str) -> 'CommandResult[T]':
        """Create permission error result.""" 
        return cls.error_result(f"Permission denied for {action}", "PERMISSION_DENIED")
    
    @classmethod
    def conflict_error(cls, resource: str) -> 'CommandResult[T]':
        """Create conflict error result."""
        return cls.error_result(f"{resource} already exists", "CONFLICT")
    
    def is_success(self) -> bool:
        """Check if result is successful."""
        return self.success
    
    def is_error(self) -> bool:
        """Check if result is an error."""
        return not self.success
    
    def get_data_or_raise(self) -> T:
        """Get data or raise exception if error."""
        if self.is_error():
            raise RuntimeError(f"{self.error_code}: {self.error}")
        return self.data
    
    def get_data_or_default(self, default: T) -> T:
        """Get data or return default if error."""
        return self.data if self.is_success() else default


class CommandValidationError(Exception):
    """Exception raised for command validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class CommandExecutionError(Exception):
    """Exception raised for command execution errors."""
    
    def __init__(self, message: str, command_type: str, cause: Optional[Exception] = None):
        self.message = message
        self.command_type = command_type
        self.cause = cause
        super().__init__(message)


# Common validation mixins
class RequireUserMixin:
    """Mixin for commands that require user authentication."""
    
    def validate_user_required(self):
        """Validate that user_id is provided."""
        if not hasattr(self, 'user_id') or not self.user_id:
            raise CommandValidationError("User ID is required for this command")


class RequireIdMixin:
    """Mixin for commands that require an ID parameter."""
    
    def validate_id_required(self, id_field_name: str = 'id'):
        """Validate that ID field is provided."""
        id_value = getattr(self, id_field_name, None)
        if not id_value:
            raise CommandValidationError(f"{id_field_name} is required")