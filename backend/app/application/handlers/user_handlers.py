"""User-related command and query handlers."""

from typing import List, Optional
import logging

from app.application.commands.base_command import CommandResult
from app.application.queries.base_query import QueryResult, PaginatedResult
from app.application.handlers.base_handler import (
    AbstractCommandHandler, 
    AbstractQueryHandler, 
    BaseHandler
)

# Commands and Queries
from app.application.commands.user_commands import (
    CreateUserCommand,
    UpdateUserCommand,
    DeleteUserCommand,
    VerifyUserEmailCommand,
    UpdateUserPreferencesCommand
)
from app.application.queries.user_queries import (
    GetUserQuery,
    GetUserByEmailQuery,
    ListUsersQuery,
    GetUserStatsQuery,
    SearchUsersQuery
)

# DTOs
from app.application.dto.user_dto import (
    UserDTO,
    UserCreateDTO,
    UserUpdateDTO,
    UserStatsDTO
)

# Domain services and repositories
from app.domain.manga.repositories.users_repository import UsersRepository, UserNotFoundError, DuplicateEmailError
from app.domain.common.entities import UserEntity
from uuid import UUID, uuid4
from datetime import datetime


logger = logging.getLogger(__name__)


class CreateUserCommandHandler(AbstractCommandHandler[CreateUserCommand, str], BaseHandler):
    """Handler for creating new users."""
    
    def __init__(self, user_repository: UsersRepository):
        super().__init__()
        self.user_repository = user_repository
    
    async def handle(self, command: CreateUserCommand) -> CommandResult[str]:
        """Handle user creation command."""
        try:
            # Validate command
            await self.validate_command(command)
            
            # Check if user already exists
            existing_user = await self.user_repository.find_by_email(command.email)
            if existing_user:
                return CommandResult.conflict_error("User")
            
            # Create user entity
            user_entity = UserEntity(
                user_id=uuid4(),
                email=command.email,
                display_name=command.display_name,
                account_type=command.account_type,
                firebase_claims=command.firebase_claims or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Create user through repository
            created_user = await self.user_repository.create(user_entity)
            user_id = str(created_user.user_id)
            
            self.log_command_execution(command, CommandResult.success_result(user_id))
            return CommandResult.success_result(user_id)
            
        except DuplicateEmailError as e:
            error_result = CommandResult.conflict_error("User email")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to create user: {str(e)}", 
                "USER_CREATION_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class UpdateUserCommandHandler(AbstractCommandHandler[UpdateUserCommand, bool], BaseHandler):
    """Handler for updating user information."""
    
    def __init__(self, user_repository: UsersRepository):
        super().__init__()
        self.user_repository = user_repository
    
    async def handle(self, command: UpdateUserCommand) -> CommandResult[bool]:
        """Handle user update command."""
        try:
            await self.validate_command(command)
            
            # Check if user exists
            user = await self.user_repository.find_by_id(UUID(command.user_id))
            if not user:
                return CommandResult.not_found_error("User")
            
            # Update user entity
            if command.display_name is not None:
                user.display_name = command.display_name
            if command.account_type is not None:
                user.account_type = command.account_type
            if command.firebase_claims is not None:
                user.firebase_claims = command.firebase_claims
            
            user.updated_at = datetime.utcnow()
            
            # Update through repository
            updated_user = await self.user_repository.update(user)
            success = updated_user is not None
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except UserNotFoundError as e:
            error_result = CommandResult.not_found_error("User")
            self.log_command_execution(command, error_result)
            return error_result
        except DuplicateEmailError as e:
            error_result = CommandResult.conflict_error("User email")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to update user: {str(e)}", 
                "USER_UPDATE_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class DeleteUserCommandHandler(AbstractCommandHandler[DeleteUserCommand, bool], BaseHandler):
    """Handler for deleting users."""
    
    def __init__(self, user_repository: UsersRepository):
        super().__init__()
        self.user_repository = user_repository
    
    async def handle(self, command: DeleteUserCommand) -> CommandResult[bool]:
        """Handle user deletion command."""
        try:
            await self.validate_command(command)
            
            # Check if user exists and can be deleted
            user = await self.user_repository.find_by_id(UUID(command.user_id))
            if not user:
                return CommandResult.not_found_error("User")
            
            # Delete through repository
            success = await self.user_repository.delete(UUID(command.user_id))
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except UserNotFoundError as e:
            error_result = CommandResult.not_found_error("User")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to delete user: {str(e)}",
                "USER_DELETION_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class GetUserQueryHandler(AbstractQueryHandler[GetUserQuery, UserDTO], BaseHandler):
    """Handler for getting user by ID."""
    
    def __init__(self, user_repository: UsersRepository):
        super().__init__()
        self.user_repository = user_repository
    
    async def handle(self, query: GetUserQuery) -> QueryResult[UserDTO]:
        """Handle get user query."""
        try:
            await self.validate_query(query)
            
            # Execute query with timing
            async def execute_query():
                # Get user from repository
                user = await self.user_repository.find_by_id(UUID(query.user_id))
                
                if not user:
                    return None
                
                # Convert entity to DTO
                user_dto = UserDTO(
                    user_id=str(user.user_id),
                    email=user.email,
                    display_name=user.display_name,
                    account_type=user.account_type,
                    firebase_claims=user.firebase_claims,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
                
                # Optionally include stats and preferences
                if query.include_stats:
                    stats_data = await self.user_repository.get_user_stats(UUID(query.user_id))
                    if stats_data:
                        user_dto.stats = UserStatsDTO(**stats_data)
                
                if query.include_preferences:
                    preferences_data = await self.user_repository.get_user_preferences(UUID(query.user_id))
                    if preferences_data:
                        user_dto.preferences = preferences_data
                
                return user_dto
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            if not result:
                error_result = QueryResult.not_found_error("User")
                self.log_query_execution(query, error_result)
                return error_result
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except ValueError as e:
            error_result = QueryResult.validation_error(str(e))
            self.log_query_execution(query, error_result)
            return error_result
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to get user: {str(e)}",
                "USER_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result


class GetUserByEmailQueryHandler(AbstractQueryHandler[GetUserByEmailQuery, UserDTO], BaseHandler):
    """Handler for getting user by email."""
    
    def __init__(self, user_repository: UsersRepository):
        super().__init__()
        self.user_repository = user_repository
    
    async def handle(self, query: GetUserByEmailQuery) -> QueryResult[UserDTO]:
        """Handle get user by email query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get user by email
                user = await self.user_repository.find_by_email(query.email)
                
                if not user:
                    return None
                
                # Convert entity to DTO
                user_dto = UserDTO(
                    user_id=str(user.user_id),
                    email=user.email,
                    display_name=user.display_name,
                    account_type=user.account_type,
                    firebase_claims=user.firebase_claims,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
                
                return user_dto
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            if not result:
                error_result = QueryResult.not_found_error("User")
                self.log_query_execution(query, error_result)
                return error_result
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to get user by email: {str(e)}",
                "USER_EMAIL_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result


class ListUsersQueryHandler(AbstractQueryHandler[ListUsersQuery, PaginatedResult[UserDTO]], BaseHandler):
    """Handler for listing users with filtering."""
    
    def __init__(self, user_repository: UsersRepository):
        super().__init__()
        self.user_repository = user_repository
    
    async def handle(self, query: ListUsersQuery) -> QueryResult[PaginatedResult[UserDTO]]:
        """Handle list users query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get users from repository
                users = await self.user_repository.list_users(
                    account_type=query.account_type,
                    created_after=query.created_after,
                    created_before=query.created_before,
                    limit=query.pagination.page_size,
                    offset=query.pagination.offset,
                    order_by=query.pagination.sort_by or "created_at",
                    order_direction=query.pagination.sort_direction.value
                )
                
                # Get total count
                total_count = await self.user_repository.count_users(
                    account_type=query.account_type,
                    created_after=query.created_after,
                    created_before=query.created_before
                )
                
                # Convert entities to DTOs
                user_dtos = [
                    UserDTO(
                        user_id=str(user.user_id),
                        email=user.email,
                        display_name=user.display_name,
                        account_type=user.account_type,
                        firebase_claims=user.firebase_claims,
                        created_at=user.created_at,
                        updated_at=user.updated_at
                    ) for user in users
                ]
                
                return PaginatedResult.create(
                    items=user_dtos,
                    total_count=total_count,
                    pagination=query.pagination
                )
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to list users: {str(e)}",
                "USER_LIST_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result


class GetUserStatsQueryHandler(AbstractQueryHandler[GetUserStatsQuery, UserStatsDTO], BaseHandler):
    """Handler for getting user statistics."""
    
    def __init__(self, user_repository: UsersRepository):
        super().__init__()
        self.user_repository = user_repository
    
    async def handle(self, query: GetUserStatsQuery) -> QueryResult[UserStatsDTO]:
        """Handle get user stats query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Check if user exists
                user = await self.user_repository.find_by_id(UUID(query.user_id))
                if not user:
                    return None
                
                # Get stats from repository
                stats_data = await self.user_repository.get_user_stats(
                    UUID(query.user_id), 
                    query.period_days
                )
                
                # Create stats DTO
                stats = UserStatsDTO(
                    total_projects=stats_data.get("total_projects", 0),
                    completed_projects=stats_data.get("completed_projects", 0),
                    failed_projects=stats_data.get("failed_projects", 0),
                    total_generations=stats_data.get("total_generations", 0),
                    successful_generations=stats_data.get("successful_generations", 0),
                    success_rate=stats_data.get("success_rate", 0.0),
                    daily_quota_used=stats_data.get("daily_quota_used", 0),
                    daily_quota_limit=stats_data.get("daily_quota_limit", 10),
                    average_processing_time_seconds=stats_data.get("average_processing_time", 0.0)
                )
                
                stats.calculate_derived_stats()
                return stats
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            if not result:
                error_result = QueryResult.not_found_error("User")
                self.log_query_execution(query, error_result)
                return error_result
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to get user stats: {str(e)}",
                "USER_STATS_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result


class SearchUsersQueryHandler(AbstractQueryHandler[SearchUsersQuery, List[UserDTO]], BaseHandler):
    """Handler for searching users."""
    
    def __init__(self, user_repository: UsersRepository):
        super().__init__()
        self.user_repository = user_repository
    
    async def handle(self, query: SearchUsersQuery) -> QueryResult[List[UserDTO]]:
        """Handle search users query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Search users from repository
                users = await self.user_repository.search_users(
                    search_term=query.search_term,
                    search_fields=query.search_fields,
                    account_type=query.account_type,
                    limit=query.pagination.page_size,
                    offset=query.pagination.offset
                )
                
                # Convert entities to DTOs
                user_dtos = [
                    UserDTO(
                        user_id=str(user.user_id),
                        email=user.email,
                        display_name=user.display_name,
                        account_type=user.account_type,
                        firebase_claims=user.firebase_claims,
                        created_at=user.created_at,
                        updated_at=user.updated_at
                    ) for user in users
                ]
                
                return user_dtos
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to search users: {str(e)}",
                "USER_SEARCH_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result