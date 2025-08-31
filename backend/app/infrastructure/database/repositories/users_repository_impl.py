"""Users repository implementation using SQLAlchemy."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.domain.common.entities import UserEntity
from app.domain.manga.repositories.users_repository import (
    UsersRepository, RepositoryError, UserNotFoundError, DuplicateEmailError
)
from app.infrastructure.database.models.users_model import UsersModel
from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)


class UsersRepositoryImpl(UsersRepository):
    """SQLAlchemy implementation of UsersRepository."""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """Initialize with optional database session."""
        self.db_session = db_session
    
    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db_session:
            return self.db_session
        return next(get_db())
    
    def _model_to_entity(self, model: UsersModel) -> UserEntity:
        """Convert database model to domain entity."""
        return UserEntity(
            user_id=model.user_id,
            email=model.email,
            display_name=model.display_name,
            account_type=model.account_type,
            firebase_claims=model.firebase_claims or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
            # Optional fields would be set separately if needed
            is_active=True,
            is_verified=True
        )
    
    def _entity_to_model_data(self, entity: UserEntity) -> Dict[str, Any]:
        """Convert domain entity to model data dict."""
        return {
            'user_id': entity.user_id,
            'email': entity.email,
            'display_name': entity.display_name,
            'account_type': entity.account_type,
            'firebase_claims': entity.firebase_claims,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at
        }
    
    async def create(self, user: UserEntity) -> UserEntity:
        """Create a new user."""
        try:
            session = await self._get_session()
            
            # Validate entity before creation
            user.validate()
            
            # Check for duplicate email
            existing = await session.execute(
                select(UsersModel).where(UsersModel.email == user.email)
            )
            if existing.scalars().first():
                raise DuplicateEmailError(f"User with email {user.email} already exists")
            
            # Create model instance
            model_data = self._entity_to_model_data(user)
            model = UsersModel(**model_data)
            
            session.add(model)
            await session.commit()
            await session.refresh(model)
            
            logger.info(f"Created user: {user.user_id}")
            return self._model_to_entity(model)
            
        except IntegrityError as e:
            await session.rollback()
            if "email" in str(e):
                raise DuplicateEmailError(f"Email {user.email} already exists")
            raise RepositoryError(f"Failed to create user: {str(e)}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise RepositoryError(f"Failed to create user: {str(e)}")
    
    async def find_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        """Find user by ID."""
        try:
            session = await self._get_session()
            
            result = await session.execute(
                select(UsersModel).where(UsersModel.user_id == user_id)
            )
            model = result.scalars().first()
            
            if model:
                return self._model_to_entity(model)
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by ID {user_id}: {str(e)}")
            raise RepositoryError(f"Failed to find user: {str(e)}")
    
    async def find_by_email(self, email: str) -> Optional[UserEntity]:
        """Find user by email address."""
        try:
            session = await self._get_session()
            
            result = await session.execute(
                select(UsersModel).where(UsersModel.email == email)
            )
            model = result.scalars().first()
            
            if model:
                return self._model_to_entity(model)
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {str(e)}")
            raise RepositoryError(f"Failed to find user: {str(e)}")
    
    async def update(self, user: UserEntity) -> UserEntity:
        """Update existing user."""
        try:
            session = await self._get_session()
            
            # Validate entity before update
            user.validate()
            
            # Check if user exists
            existing_result = await session.execute(
                select(UsersModel).where(UsersModel.user_id == user.user_id)
            )
            existing_model = existing_result.scalars().first()
            
            if not existing_model:
                raise UserNotFoundError(f"User {user.user_id} not found")
            
            # Check for email conflicts with other users
            if existing_model.email != user.email:
                email_check = await session.execute(
                    select(UsersModel).where(
                        and_(
                            UsersModel.email == user.email,
                            UsersModel.user_id != user.user_id
                        )
                    )
                )
                if email_check.scalars().first():
                    raise DuplicateEmailError(f"Email {user.email} already in use")
            
            # Update fields
            existing_model.email = user.email
            existing_model.display_name = user.display_name
            existing_model.account_type = user.account_type
            existing_model.firebase_claims = user.firebase_claims
            existing_model.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(existing_model)
            
            logger.info(f"Updated user: {user.user_id}")
            return self._model_to_entity(existing_model)
            
        except (UserNotFoundError, DuplicateEmailError):
            await session.rollback()
            raise
        except IntegrityError as e:
            await session.rollback()
            if "email" in str(e):
                raise DuplicateEmailError(f"Email {user.email} already exists")
            raise RepositoryError(f"Failed to update user: {str(e)}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating user {user.user_id}: {str(e)}")
            raise RepositoryError(f"Failed to update user: {str(e)}")
    
    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID."""
        try:
            session = await self._get_session()
            
            result = await session.execute(
                delete(UsersModel).where(UsersModel.user_id == user_id)
            )
            
            await session.commit()
            deleted_count = result.rowcount
            
            if deleted_count > 0:
                logger.info(f"Deleted user: {user_id}")
                return True
            return False
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            raise RepositoryError(f"Failed to delete user: {str(e)}")
    
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
        """List users with filtering and pagination."""
        try:
            session = await self._get_session()
            
            query = select(UsersModel)
            
            # Apply filters
            conditions = []
            if account_type:
                conditions.append(UsersModel.account_type == account_type)
            if created_after:
                conditions.append(UsersModel.created_at >= created_after)
            if created_before:
                conditions.append(UsersModel.created_at <= created_before)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Apply ordering
            order_field = getattr(UsersModel, order_by, UsersModel.created_at)
            if order_direction.lower() == "desc":
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field.asc())
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            raise RepositoryError(f"Failed to list users: {str(e)}")
    
    async def count_users(
        self,
        account_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> int:
        """Count users matching criteria."""
        try:
            session = await self._get_session()
            
            query = select(func.count(UsersModel.user_id))
            
            # Apply filters
            conditions = []
            if account_type:
                conditions.append(UsersModel.account_type == account_type)
            if created_after:
                conditions.append(UsersModel.created_at >= created_after)
            if created_before:
                conditions.append(UsersModel.created_at <= created_before)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await session.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error counting users: {str(e)}")
            raise RepositoryError(f"Failed to count users: {str(e)}")
    
    async def search_users(
        self,
        search_term: str,
        search_fields: List[str] = None,
        account_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[UserEntity]:
        """Search users by term across specified fields."""
        try:
            session = await self._get_session()
            
            if search_fields is None:
                search_fields = ["display_name", "email"]
            
            # Build search conditions
            search_conditions = []
            search_pattern = f"%{search_term}%"
            
            if "display_name" in search_fields:
                search_conditions.append(UsersModel.display_name.ilike(search_pattern))
            if "email" in search_fields:
                search_conditions.append(UsersModel.email.ilike(search_pattern))
            
            query = select(UsersModel).where(or_(*search_conditions))
            
            # Apply account type filter
            if account_type:
                query = query.where(UsersModel.account_type == account_type)
            
            # Apply pagination and ordering
            query = query.order_by(UsersModel.display_name.asc()).offset(offset).limit(limit)
            
            result = await session.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            raise RepositoryError(f"Failed to search users: {str(e)}")
    
    async def get_user_stats(
        self,
        user_id: UUID,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get user statistics for specified period."""
        try:
            session = await self._get_session()
            
            # Check if user exists
            user_check = await session.execute(
                select(UsersModel).where(UsersModel.user_id == user_id)
            )
            if not user_check.scalars().first():
                raise UserNotFoundError(f"User {user_id} not found")
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # This would typically involve joins with other tables like projects and generations
            # For now, return basic stats structure
            stats = {
                "user_id": str(user_id),
                "period_days": period_days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_projects": 0,
                "completed_projects": 0,
                "total_generations": 0,
                "successful_generations": 0,
                "success_rate": 0.0,
                "average_processing_time": 0.0
            }
            
            return stats
            
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {str(e)}")
            raise RepositoryError(f"Failed to get user stats: {str(e)}")
    
    async def update_last_login(self, user_id: UUID) -> bool:
        """Update user's last login timestamp."""
        try:
            session = await self._get_session()
            
            result = await session.execute(
                update(UsersModel)
                .where(UsersModel.user_id == user_id)
                .values(updated_at=datetime.utcnow())
            )
            
            await session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating last login for {user_id}: {str(e)}")
            raise RepositoryError(f"Failed to update last login: {str(e)}")
    
    async def get_user_preferences(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user preferences."""
        try:
            # For now, return default preferences structure
            # In a full implementation, this might query a separate preferences table
            default_preferences = {
                "user_id": str(user_id),
                "device_capability": 0.5,
                "network_speed": 5000,
                "preferred_quality": 3,
                "auto_adapt": True,
                "theme": "auto",
                "language": "ja",
                "notifications_enabled": True,
                "email_notifications": True,
                "auto_start_generation": False,
                "feedback_timeout_minutes": 30,
                "save_intermediate_results": True
            }
            
            return default_preferences
            
        except Exception as e:
            logger.error(f"Error getting preferences for {user_id}: {str(e)}")
            raise RepositoryError(f"Failed to get user preferences: {str(e)}")
    
    async def update_user_preferences(
        self,
        user_id: UUID,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences."""
        try:
            # For now, just validate that user exists
            session = await self._get_session()
            
            user_check = await session.execute(
                select(UsersModel).where(UsersModel.user_id == user_id)
            )
            if not user_check.scalars().first():
                raise UserNotFoundError(f"User {user_id} not found")
            
            # In a full implementation, this would update a preferences table
            logger.info(f"Updated preferences for user: {user_id}")
            return True
            
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating preferences for {user_id}: {str(e)}")
            raise RepositoryError(f"Failed to update preferences: {str(e)}")
    
    async def validate_user_permission(
        self,
        user_id: UUID,
        action: str,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> bool:
        """Validate if user has permission for action."""
        try:
            session = await self._get_session()
            
            # Get user to check account type
            result = await session.execute(
                select(UsersModel).where(UsersModel.user_id == user_id)
            )
            user = result.scalars().first()
            
            if not user:
                return False
            
            # Basic permission logic based on account type
            if user.account_type == "admin":
                return True
            
            # Define permission rules
            permission_rules = {
                "create_project": ["free", "premium", "admin"],
                "update_project": ["free", "premium", "admin"],
                "delete_project": ["free", "premium", "admin"],
                "create_generation": ["free", "premium", "admin"],
                "view_generation": ["free", "premium", "admin"],
                "cancel_generation": ["free", "premium", "admin"],
                "admin_access": ["admin"],
                "moderate_content": ["admin"]
            }
            
            allowed_types = permission_rules.get(action, [])
            return user.account_type in allowed_types
            
        except Exception as e:
            logger.error(f"Error validating permission for {user_id}: {str(e)}")
            raise RepositoryError(f"Failed to validate permission: {str(e)}")
    
    async def get_users_by_quota_status(
        self,
        quota_type: str = "daily",
        is_exceeded: bool = True
    ) -> List[UserEntity]:
        """Get users by quota status."""
        try:
            session = await self._get_session()
            
            # For now, return empty list as quota logic would require additional tables
            # In a full implementation, this would join with quota tables
            return []
            
        except Exception as e:
            logger.error(f"Error getting users by quota status: {str(e)}")
            raise RepositoryError(f"Failed to get users by quota: {str(e)}")