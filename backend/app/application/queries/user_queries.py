"""User-related queries for CQRS pattern."""

from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

from .base_query import Query, RequireUserMixin, RequireIdMixin, QueryValidationError
from ..dto.user_dto import UserDTO, UserStatsDTO


@dataclass
class GetUserQuery(Query[UserDTO], RequireIdMixin):
    """Query to get a single user by ID."""
    
    user_id: str
    include_stats: bool = False
    include_preferences: bool = False
    
    def validate(self) -> None:
        """Validate get user query."""
        self.validate_id_required("user_id")


@dataclass
class GetUserByEmailQuery(Query[UserDTO]):
    """Query to get a user by email address."""
    
    email: str
    include_stats: bool = False
    include_preferences: bool = False
    
    def validate(self) -> None:
        """Validate get user by email query."""
        if not self.email or not self.email.strip():
            raise QueryValidationError("Email is required")
        
        if "@" not in self.email:
            raise QueryValidationError("Valid email address is required")


@dataclass
class ListUsersQuery(Query[List[UserDTO]], RequireUserMixin):
    """Query to list users with filtering and pagination."""
    
    account_type: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_premium: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate list users query."""
        self.validate_user_required()
        
        if self.account_type is not None:
            if self.account_type not in ["free", "premium", "admin"]:
                raise QueryValidationError("Account type must be 'free', 'premium', or 'admin'")
        
        if self.created_after and self.created_before:
            if self.created_after >= self.created_before:
                raise QueryValidationError("Created after date must be before created before date")


@dataclass
class SearchUsersQuery(Query[List[UserDTO]], RequireUserMixin):
    """Query to search users by various criteria."""
    
    search_term: str
    search_fields: List[str] = None  # email, display_name, username
    account_type: Optional[str] = None
    is_active: Optional[bool] = None
    
    def __post_init__(self):
        """Set default search fields."""
        if self.search_fields is None:
            self.search_fields = ["display_name", "email"]
    
    def validate(self) -> None:
        """Validate search users query."""
        self.validate_user_required()
        
        if not self.search_term or not self.search_term.strip():
            raise QueryValidationError("Search term is required")
        
        if len(self.search_term) < 2:
            raise QueryValidationError("Search term must be at least 2 characters")
        
        valid_fields = ["email", "display_name", "username"]
        for field in self.search_fields:
            if field not in valid_fields:
                raise QueryValidationError(f"Invalid search field: {field}")
        
        if self.account_type is not None:
            if self.account_type not in ["free", "premium", "admin"]:
                raise QueryValidationError("Account type must be 'free', 'premium', or 'admin'")


@dataclass
class GetUserStatsQuery(Query[UserStatsDTO], RequireUserMixin, RequireIdMixin):
    """Query to get user statistics."""
    
    user_id: str
    period_days: int = 30
    include_generation_stats: bool = True
    include_project_stats: bool = True
    include_usage_stats: bool = True
    
    def validate(self) -> None:
        """Validate get user stats query."""
        self.validate_user_required()
        self.validate_id_required("user_id")
        
        if self.period_days < 1:
            raise QueryValidationError("Period days must be at least 1")
        
        if self.period_days > 365:
            raise QueryValidationError("Period days cannot exceed 365")


@dataclass
class GetUserQuotaQuery(Query[dict], RequireUserMixin, RequireIdMixin):
    """Query to get user quota information."""
    
    user_id: str
    quota_type: Optional[str] = None  # daily, monthly
    
    def validate(self) -> None:
        """Validate get user quota query."""
        self.validate_user_required()
        self.validate_id_required("user_id")
        
        if self.quota_type is not None:
            if self.quota_type not in ["daily", "monthly"]:
                raise QueryValidationError("Quota type must be 'daily' or 'monthly'")


@dataclass
class GetUserPreferencesQuery(Query[dict], RequireUserMixin, RequireIdMixin):
    """Query to get user preferences."""
    
    user_id: str
    
    def validate(self) -> None:
        """Validate get user preferences query."""
        self.validate_user_required()
        self.validate_id_required("user_id")


@dataclass
class GetUserActivityQuery(Query[List[dict]], RequireUserMixin, RequireIdMixin):
    """Query to get user activity history."""
    
    user_id: str
    activity_types: Optional[List[str]] = None  # login, generation, project_create, etc.
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate get user activity query."""
        self.validate_user_required()
        self.validate_id_required("user_id")
        
        if self.from_date and self.to_date:
            if self.from_date >= self.to_date:
                raise QueryValidationError("From date must be before to date")
        
        if self.activity_types:
            valid_types = [
                "login", "logout", "generation", "project_create",
                "project_update", "project_delete", "settings_update"
            ]
            for activity_type in self.activity_types:
                if activity_type not in valid_types:
                    raise QueryValidationError(f"Invalid activity type: {activity_type}")


@dataclass
class GetUsersWithExpiredQuotaQuery(Query[List[UserDTO]], RequireUserMixin):
    """Query to get users with expired quotas (admin only)."""
    
    quota_type: str = "daily"
    expired_before: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate get expired quota query."""
        self.validate_user_required()
        
        if self.quota_type not in ["daily", "monthly"]:
            raise QueryValidationError("Quota type must be 'daily' or 'monthly'")


@dataclass
class ValidateUserPermissionQuery(Query[bool], RequireUserMixin, RequireIdMixin):
    """Query to validate user permission for an action."""
    
    user_id: str
    action: str
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    
    def validate(self) -> None:
        """Validate user permission query."""
        self.validate_user_required()
        self.validate_id_required("user_id")
        
        if not self.action or not self.action.strip():
            raise QueryValidationError("Action is required")
        
        valid_actions = [
            "create_project", "update_project", "delete_project",
            "create_generation", "view_generation", "cancel_generation",
            "admin_access", "moderate_content"
        ]
        
        if self.action not in valid_actions:
            raise QueryValidationError(f"Invalid action: {self.action}")
        
        # Some actions require resource info
        resource_required_actions = ["update_project", "delete_project", "view_generation"]
        if self.action in resource_required_actions:
            if not self.resource_id:
                raise QueryValidationError(f"Resource ID is required for action: {self.action}")


@dataclass
class GetUserGenerationLimitsQuery(Query[dict], RequireUserMixin, RequireIdMixin):
    """Query to get user generation limits and current usage."""
    
    user_id: str
    check_date: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate get generation limits query."""
        self.validate_user_required()
        self.validate_id_required("user_id")