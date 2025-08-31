"""Base DTO classes for data transfer between layers."""

from typing import Dict, Any, List, Optional, TypeVar, Generic
from datetime import datetime
from dataclasses import dataclass, field, asdict
from abc import ABC

T = TypeVar('T')


@dataclass
class BaseDTO(ABC):
    """Base class for all Data Transfer Objects.
    
    DTOs are responsible for:
    1. Data transfer between application layers
    2. Serialization/deserialization
    3. Input validation
    4. Output formatting
    """
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary for serialization.
        
        Returns:
            Dictionary representation of the DTO
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create DTO instance from dictionary.
        
        Args:
            data: Dictionary with DTO data
            
        Returns:
            DTO instance
        """
        # Filter data to only include fields that exist in the DTO
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update DTO fields from dictionary.
        
        Args:
            data: Dictionary with updated data
        """
        field_names = {f.name for f in self.__class__.__dataclass_fields__.values()}
        for key, value in data.items():
            if key in field_names:
                setattr(self, key, value)
    
    def to_json_dict(self) -> Dict[str, Any]:
        """Convert DTO to JSON-serializable dictionary.
        
        Returns:
            JSON-serializable dictionary
        """
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, BaseDTO):
                result[key] = value.to_json_dict()
            elif isinstance(value, list) and value and isinstance(value[0], BaseDTO):
                result[key] = [item.to_json_dict() for item in value]
            else:
                result[key] = value
        return result
    
    def validate(self) -> None:
        """Validate DTO data.
        
        Override in subclasses for specific validation logic.
        
        Raises:
            ValueError: If validation fails
        """
        pass
    
    def get_non_none_fields(self) -> Dict[str, Any]:
        """Get dictionary of fields that are not None.
        
        Returns:
            Dictionary with non-None fields
        """
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def copy_with_updates(self, **updates):
        """Create a copy of DTO with updated fields.
        
        Args:
            **updates: Fields to update
            
        Returns:
            New DTO instance with updates
        """
        data = asdict(self)
        data.update(updates)
        return self.__class__.from_dict(data)


@dataclass
class PaginatedResponseDTO(Generic[T]):
    """Generic DTO for paginated responses.
    
    Used to wrap collections of DTOs with pagination metadata.
    """
    
    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total_count: int,
        page: int,
        page_size: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'PaginatedResponseDTO[T]':
        """Create paginated response from parameters.
        
        Args:
            items: List of items for current page
            total_count: Total number of items across all pages
            page: Current page number (1-based)
            page_size: Number of items per page
            metadata: Optional metadata dictionary
            
        Returns:
            PaginatedResponseDTO instance
        """
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1
        
        return cls(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            metadata=metadata or {}
        )
    
    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary with proper item handling."""
        items_json = []
        for item in self.items:
            if isinstance(item, BaseDTO):
                items_json.append(item.to_json_dict())
            elif hasattr(item, 'to_dict'):
                items_json.append(item.to_dict())
            else:
                items_json.append(item)
        
        return {
            'items': items_json,
            'total_count': self.total_count,
            'page': self.page,
            'page_size': self.page_size,
            'total_pages': self.total_pages,
            'has_next': self.has_next,
            'has_previous': self.has_previous,
            'metadata': self.metadata
        }


@dataclass
class ErrorDTO(BaseDTO):
    """DTO for error responses."""
    
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = None
    
    def validate(self) -> None:
        """Validate error DTO."""
        if not self.error:
            raise ValueError("Error message is required")
        if not self.error_code:
            raise ValueError("Error code is required")


@dataclass
class SuccessResponseDTO(BaseDTO):
    """DTO for successful responses without specific data."""
    
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatsDTO(BaseDTO):
    """Base DTO for statistics responses."""
    
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON with proper datetime handling."""
        result = super().to_json_dict()
        # Convert datetime fields to ISO format
        for field_name in ['period_start', 'period_end', 'generated_at']:
            if field_name in result and result[field_name]:
                if isinstance(result[field_name], datetime):
                    result[field_name] = result[field_name].isoformat()
        return result


@dataclass
class IdResponseDTO(BaseDTO):
    """DTO for responses that return only an ID (e.g., after creation)."""
    
    id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    message: Optional[str] = None
    
    def validate(self) -> None:
        """Validate ID response DTO."""
        if not self.id:
            raise ValueError("ID is required")


# DTO validation decorators and utilities
class DTOValidationError(Exception):
    """Exception raised for DTO validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


def validate_required_fields(dto: BaseDTO, required_fields: List[str]) -> None:
    """Validate that required fields are present in DTO.
    
    Args:
        dto: DTO to validate
        required_fields: List of required field names
        
    Raises:
        DTOValidationError: If any required field is missing
    """
    data = asdict(dto)
    for field_name in required_fields:
        value = data.get(field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise DTOValidationError(f"Field '{field_name}' is required", field_name)


def validate_field_length(dto: BaseDTO, field_constraints: Dict[str, tuple]) -> None:
    """Validate string field lengths in DTO.
    
    Args:
        dto: DTO to validate
        field_constraints: Dict mapping field names to (min_length, max_length) tuples
        
    Raises:
        DTOValidationError: If any field violates length constraints
    """
    data = asdict(dto)
    for field_name, (min_length, max_length) in field_constraints.items():
        value = data.get(field_name)
        if isinstance(value, str):
            if len(value) < min_length:
                raise DTOValidationError(
                    f"Field '{field_name}' must be at least {min_length} characters",
                    field_name
                )
            if len(value) > max_length:
                raise DTOValidationError(
                    f"Field '{field_name}' must be at most {max_length} characters",
                    field_name
                )