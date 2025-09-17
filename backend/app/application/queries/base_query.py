"""Base query classes for CQRS pattern."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar, Optional, List
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field
from enum import Enum

T = TypeVar('T')


class SortDirection(str, Enum):
    """Sort direction enumeration."""
    ASC = "asc"
    DESC = "desc"


@dataclass(kw_only=True)
class PaginationInfo:
    """Pagination information for queries."""
    
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_direction: SortDirection = SortDirection.DESC
    
    def __post_init__(self):
        """Validate pagination parameters."""
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = 20
        if self.page_size > 100:
            self.page_size = 100
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.page_size


@dataclass(kw_only=True)
class FilterInfo:
    """Filter information for queries."""
    
    filters: Dict[str, Any] = field(default_factory=dict)
    search_term: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    def has_filters(self) -> bool:
        """Check if any filters are applied."""
        return bool(
            self.filters or 
            self.search_term or 
            self.date_from or 
            self.date_to
        )
    
    def get_filter_value(self, key: str, default: Any = None) -> Any:
        """Get filter value by key."""
        return self.filters.get(key, default)
    
    def set_filter(self, key: str, value: Any) -> None:
        """Set filter value."""
        if value is not None:
            self.filters[key] = value
        elif key in self.filters:
            del self.filters[key]


@dataclass(kw_only=True)
class AbstractQuery(ABC):
    """Abstract base class for all queries in the CQRS pattern.
    
    Queries represent read operations that don't change system state.
    They should be named as questions (e.g., GetUser, ListProjects).
    """
    
    # Query metadata
    query_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    timestamp: datetime = field(default_factory=datetime.utcnow, init=False)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    pagination: PaginationInfo = field(default_factory=PaginationInfo)
    filters: FilterInfo = field(default_factory=FilterInfo)
    
    @abstractmethod
    def validate(self) -> None:
        """Validate query parameters.
        
        Raises:
            ValueError: If query parameters are invalid
        """
        pass
    
    def get_query_type(self) -> str:
        """Get query type name."""
        return self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert query to dictionary for serialization."""
        return {
            'query_id': self.query_id,
            'query_type': self.get_query_type(),
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'correlation_id': self.correlation_id,
            'pagination': {
                'page': self.pagination.page,
                'page_size': self.pagination.page_size,
                'sort_by': self.pagination.sort_by,
                'sort_direction': self.pagination.sort_direction.value
            },
            'filters': {
                'filters': self.filters.filters,
                'search_term': self.filters.search_term,
                'date_from': self.filters.date_from.isoformat() if self.filters.date_from else None,
                'date_to': self.filters.date_to.isoformat() if self.filters.date_to else None
            },
            'data': self._get_data_dict()
        }
    
    def _get_data_dict(self) -> Dict[str, Any]:
        """Get query-specific data as dictionary."""
        exclude_fields = {
            'query_id', 'timestamp', 'user_id', 'correlation_id',
            'pagination', 'filters'
        }
        return {
            key: value for key, value in self.__dict__.items()
            if key not in exclude_fields and not key.startswith('_')
        }

    def _create_validation_result(self, errors: List[str]) -> None:
        """Raise ValueError if validation errors exist."""
        if errors:
            raise ValueError('; '.join(errors))


@dataclass(kw_only=True)
class Query(AbstractQuery, Generic[T]):
    """Generic query base class with typed result.
    
    Use this for queries that expect a specific result type.
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
class PaginatedResult(Generic[T]):
    """Paginated result wrapper."""
    
    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total_count: int,
        pagination: PaginationInfo
    ) -> 'PaginatedResult[T]':
        """Create paginated result from items and pagination info."""
        total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
        has_next = pagination.page < total_pages
        has_previous = pagination.page > 1
        
        return cls(
            items=items,
            total_count=total_count,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )


@dataclass(kw_only=True)
class QueryResult(Generic[T]):
    """Result wrapper for query execution.
    
    Implements the Result pattern for consistent error handling.
    """
    
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: Optional[float] = None
    
    @classmethod
    def success_result(
        cls,
        data: T,
        execution_time_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'QueryResult[T]':
        """Create successful result."""
        return cls(
            success=True,
            data=data,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {}
        )
    
    @classmethod
    def error_result(
        cls,
        error: str,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'QueryResult[T]':
        """Create error result."""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            metadata=metadata or {}
        )
    
    @classmethod
    def validation_error(cls, error: str) -> 'QueryResult[T]':
        """Create validation error result."""
        return cls.error_result(error, "VALIDATION_ERROR")
    
    @classmethod
    def not_found_error(cls, resource: str) -> 'QueryResult[T]':
        """Create not found error result."""
        return cls.error_result(f"{resource} not found", "NOT_FOUND")
    
    @classmethod
    def permission_error(cls, action: str) -> 'QueryResult[T]':
        """Create permission error result."""
        return cls.error_result(f"Permission denied for {action}", "PERMISSION_DENIED")
    
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


class QueryValidationError(Exception):
    """Exception raised for query validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class QueryExecutionError(Exception):
    """Exception raised for query execution errors."""
    
    def __init__(self, message: str, query_type: str, cause: Optional[Exception] = None):
        self.message = message
        self.query_type = query_type
        self.cause = cause
        super().__init__(message)


# Common validation mixins
class RequireUserMixin:
    """Mixin for queries that require user authentication."""
    
    def validate_user_required(self):
        """Validate that user_id is provided."""
        if not hasattr(self, 'user_id') or not self.user_id:
            raise QueryValidationError("User ID is required for this query")


class RequireIdMixin:
    """Mixin for queries that require an ID parameter."""
    
    def validate_id_required(self, id_field_name: str = 'id'):
        """Validate that ID field is provided."""
        id_value = getattr(self, id_field_name, None)
        if not id_value:
            raise QueryValidationError(f"{id_field_name} is required")