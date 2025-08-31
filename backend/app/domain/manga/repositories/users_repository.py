"""User repository interface for domain layer."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from ...common.entities import UserEntity


class UsersRepository(ABC):
    """Abstract repository interface for user operations.
    
    This interface defines the contract for user data persistence operations.
    Implementations should handle all database-specific logic and return
    domain entities.
    """
    
    @abstractmethod
    async def create(self, user: UserEntity) -> UserEntity:
        """Create a new user.
        
        Args:
            user: User entity to create
            
        Returns:
            Created user entity with populated fields
            
        Raises:
            RepositoryError: If creation fails
            DuplicateEmailError: If email already exists
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        """Find user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[UserEntity]:
        """Find user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def update(self, user: UserEntity) -> UserEntity:
        """Update existing user.
        
        Args:
            user: User entity with updated data
            
        Returns:
            Updated user entity
            
        Raises:
            RepositoryError: If update fails
            UserNotFoundError: If user doesn't exist
            DuplicateEmailError: If email conflicts with another user
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def list_users(
        self,
        account_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> List[UserEntity]:
        """List users with filtering and pagination.
        
        Args:
            account_type: Filter by account type (free, premium, admin)
            is_active: Filter by active status
            created_after: Filter users created after this date
            created_before: Filter users created before this date
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by
            order_direction: Order direction (asc, desc)
            
        Returns:
            List of user entities
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def count_users(
        self,
        account_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> int:
        """Count users matching criteria.
        
        Args:
            account_type: Filter by account type
            is_active: Filter by active status
            created_after: Filter users created after this date
            created_before: Filter users created before this date
            
        Returns:
            Number of matching users
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def search_users(
        self,
        search_term: str,
        search_fields: List[str] = None,
        account_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[UserEntity]:
        """Search users by term across specified fields.
        
        Args:
            search_term: Term to search for
            search_fields: Fields to search in (display_name, email)
            account_type: Filter by account type
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching user entities
            
        Raises:
            RepositoryError: If search fails
        """
        pass
    
    @abstractmethod
    async def get_user_stats(
        self,
        user_id: UUID,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get user statistics for specified period.
        
        Args:
            user_id: User ID to get stats for
            period_days: Period in days to calculate stats
            
        Returns:
            Dictionary containing user statistics
            
        Raises:
            RepositoryError: If query fails
            UserNotFoundError: If user doesn't exist
        """
        pass
    
    @abstractmethod
    async def update_last_login(self, user_id: UUID) -> bool:
        """Update user's last login timestamp.
        
        Args:
            user_id: ID of user to update
            
        Returns:
            True if updated successfully
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def get_user_preferences(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user preferences.
        
        Args:
            user_id: User ID to get preferences for
            
        Returns:
            User preferences dictionary or None if not found
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def update_user_preferences(
        self,
        user_id: UUID,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences.
        
        Args:
            user_id: User ID to update preferences for
            preferences: New preferences data
            
        Returns:
            True if updated successfully
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def validate_user_permission(
        self,
        user_id: UUID,
        action: str,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> bool:
        """Validate if user has permission for action.
        
        Args:
            user_id: User ID to check
            action: Action to validate
            resource_id: Optional resource ID
            resource_type: Optional resource type
            
        Returns:
            True if user has permission
            
        Raises:
            RepositoryError: If validation fails
        """
        pass
    
    @abstractmethod
    async def get_users_by_quota_status(
        self,
        quota_type: str = "daily",
        is_exceeded: bool = True
    ) -> List[UserEntity]:
        """Get users by quota status.
        
        Args:
            quota_type: Type of quota (daily, monthly)
            is_exceeded: Whether to get users who exceeded quota
            
        Returns:
            List of user entities matching criteria
            
        Raises:
            RepositoryError: If query fails
        """
        pass


# Repository-specific exceptions
class RepositoryError(Exception):
    """Base repository error."""
    pass


class UserNotFoundError(RepositoryError):
    """User not found error."""
    pass


class DuplicateEmailError(RepositoryError):
    """Duplicate email error."""
    pass


class PermissionDeniedError(RepositoryError):
    """Permission denied error."""
    pass