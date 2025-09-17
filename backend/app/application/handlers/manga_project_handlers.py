"""Manga project-related command and query handlers."""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from app.application.commands.base_command import CommandResult
from app.application.queries.base_query import QueryResult, PaginatedResult
from app.application.handlers.base_handler import (
    AbstractCommandHandler, 
    AbstractQueryHandler, 
    BaseHandler
)

# Commands and Queries
from app.application.commands.manga_project_commands import (
    CreateMangaProjectCommand,
    UpdateMangaProjectCommand,
    DeleteMangaProjectCommand,
    AddMangaFileCommand,
    AddProjectTagCommand,
    ArchiveMangaProjectCommand
)
from app.application.queries.manga_project_queries import (
    GetMangaProjectQuery,
    ListMangaProjectsQuery,
    SearchMangaProjectsQuery,
    GetMangaProjectStatsQuery
)

# DTOs
from app.application.dto.manga_project_dto import (
    MangaProjectDTO,
    MangaProjectCreateDTO,
    MangaProjectUpdateDTO,
    MangaProjectStatsDTO
)

# Domain services and repositories
from app.domain.manga.repositories.manga_projects_repository import (
    MangaProjectsRepository,
    ProjectNotFoundError,
    ProjectTitleExistsError,
    ProjectAccessDeniedError
)
from app.domain.common.entities import MangaProjectEntity


logger = logging.getLogger(__name__)


class CreateMangaProjectCommandHandler(AbstractCommandHandler[CreateMangaProjectCommand, str], BaseHandler):
    """Handler for creating manga projects."""
    
    def __init__(self, project_repository: MangaProjectsRepository):
        super().__init__()
        self.project_repository = project_repository
    
    async def handle(self, command: CreateMangaProjectCommand) -> CommandResult[str]:
        """Handle project creation command."""
        try:
            await self.validate_command(command)
            
            # Create project entity
            project_entity = MangaProjectEntity(
                project_id=uuid4(),
                user_id=UUID(command.user_id),
                title=command.title,
                status="draft",
                metadata=command.metadata or {},
                settings=command.settings or {},
                total_pages=command.total_pages,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                expires_at=command.expires_at
            )
            
            # Create project through repository
            created_project = await self.project_repository.create(project_entity)
            project_id = str(created_project.project_id)
            
            self.log_command_execution(command, CommandResult.success_result(project_id))
            return CommandResult.success_result(project_id)
            
        except ProjectTitleExistsError as e:
            error_result = CommandResult.conflict_error("Project title")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to create project: {str(e)}", 
                "PROJECT_CREATION_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class UpdateMangaProjectCommandHandler(AbstractCommandHandler[UpdateMangaProjectCommand, bool], BaseHandler):
    """Handler for updating manga projects."""
    
    def __init__(self, project_repository: MangaProjectsRepository):
        super().__init__()
        self.project_repository = project_repository
    
    async def handle(self, command: UpdateMangaProjectCommand) -> CommandResult[bool]:
        """Handle project update command."""
        try:
            await self.validate_command(command)
            
            # Get existing project
            project = await self.project_repository.find_by_id(UUID(command.project_id))
            if not project:
                return CommandResult.not_found_error("Project")
            
            # Update project entity
            if command.title is not None:
                project.title = command.title
            if command.status is not None:
                project.status = command.status
            if command.metadata is not None:
                project.metadata = command.metadata
            if command.settings is not None:
                project.settings = command.settings
            if command.total_pages is not None:
                project.total_pages = command.total_pages
            if command.expires_at is not None:
                project.expires_at = command.expires_at
            
            project.updated_at = datetime.utcnow()
            
            # Update through repository
            updated_project = await self.project_repository.update(project)
            success = updated_project is not None
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except ProjectNotFoundError:
            error_result = CommandResult.not_found_error("Project")
            self.log_command_execution(command, error_result)
            return error_result
        except ProjectTitleExistsError:
            error_result = CommandResult.conflict_error("Project title")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to update project: {str(e)}", 
                "PROJECT_UPDATE_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class DeleteMangaProjectCommandHandler(AbstractCommandHandler[DeleteMangaProjectCommand, bool], BaseHandler):
    """Handler for deleting manga projects."""
    
    def __init__(self, project_repository: MangaProjectsRepository):
        super().__init__()
        self.project_repository = project_repository
    
    async def handle(self, command: DeleteMangaProjectCommand) -> CommandResult[bool]:
        """Handle project deletion command."""
        try:
            await self.validate_command(command)
            
            # Check if project exists
            project = await self.project_repository.find_by_id(UUID(command.project_id))
            if not project:
                return CommandResult.not_found_error("Project")
            
            # Delete through repository
            success = await self.project_repository.delete(UUID(command.project_id))
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to delete project: {str(e)}",
                "PROJECT_DELETION_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class AddMangaFileCommandHandler(AbstractCommandHandler[AddMangaFileCommand, bool], BaseHandler):
    """Handler for adding files to projects."""
    
    def __init__(self, project_repository: MangaProjectsRepository):
        super().__init__()
        self.project_repository = project_repository
    
    async def handle(self, command: AddMangaFileCommand) -> CommandResult[bool]:
        """Handle add file command."""
        try:
            await self.validate_command(command)
            
            # Add file through repository
            success = await self.project_repository.add_file(
                project_id=UUID(command.project_id),
                file_path=command.file_path,
                file_type=command.file_type,
                metadata=command.metadata
            )
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except ProjectNotFoundError:
            error_result = CommandResult.not_found_error("Project")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to add file: {str(e)}",
                "FILE_ADD_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class AddProjectTagCommandHandler(AbstractCommandHandler[AddProjectTagCommand, bool], BaseHandler):
    """Handler for adding tags to projects."""
    
    def __init__(self, project_repository: MangaProjectsRepository):
        super().__init__()
        self.project_repository = project_repository
    
    async def handle(self, command: AddProjectTagCommand) -> CommandResult[bool]:
        """Handle add tag command."""
        try:
            await self.validate_command(command)
            
            # Add tag through repository
            success = await self.project_repository.add_tag(
                project_id=UUID(command.project_id),
                tag=command.tag_name
            )
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except ProjectNotFoundError:
            error_result = CommandResult.not_found_error("Project")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to add tag: {str(e)}",
                "TAG_ADD_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class GetMangaProjectQueryHandler(AbstractQueryHandler[GetMangaProjectQuery, MangaProjectDTO], BaseHandler):
    """Handler for getting manga project by ID."""
    
    def __init__(self, project_repository: MangaProjectsRepository):
        super().__init__()
        self.project_repository = project_repository
    
    async def handle(self, query: GetMangaProjectQuery) -> QueryResult[MangaProjectDTO]:
        """Handle get project query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get project from repository
                project = await self.project_repository.find_by_id(UUID(query.project_id))
                
                if not project:
                    return None
                
                # Convert entity to DTO
                project_dto = MangaProjectDTO(
                    project_id=str(project.project_id),
                    user_id=str(project.user_id),
                    title=project.title,
                    status=project.status,
                    metadata=project.metadata,
                    settings=project.settings,
                    total_pages=project.total_pages,
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                    expires_at=project.expires_at
                )
                
                # Optionally include stats
                if query.include_stats:
                    try:
                        stats_data = await self.project_repository.get_project_stats(UUID(query.project_id))
                        if stats_data:
                            project_dto.stats = MangaProjectStatsDTO(**stats_data)
                    except Exception as e:
                        logger.warning(f"Failed to load project stats: {str(e)}")
                
                return project_dto
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            if not result:
                error_result = QueryResult.not_found_error("Project")
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
                f"Failed to get project: {str(e)}",
                "PROJECT_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result


class ListMangaProjectsQueryHandler(AbstractQueryHandler[ListMangaProjectsQuery, PaginatedResult[MangaProjectDTO]], BaseHandler):
    """Handler for listing manga projects."""
    
    def __init__(self, project_repository: MangaProjectsRepository):
        super().__init__()
        self.project_repository = project_repository
    
    async def handle(self, query: ListMangaProjectsQuery) -> QueryResult[PaginatedResult[MangaProjectDTO]]:
        """Handle list projects query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get projects from repository
                projects = await self.project_repository.find_by_user(
                    user_id=UUID(query.user_id),
                    status=query.status,
                    limit=query.pagination.page_size,
                    offset=query.pagination.offset,
                    order_by=query.pagination.sort_by or "created_at",
                    order_direction=query.pagination.sort_direction.value
                )
                
                # Get total count (simplified - in production would optimize this)
                all_projects = await self.project_repository.find_by_user(
                    user_id=UUID(query.user_id),
                    status=query.status,
                    limit=1000,  # Max reasonable limit
                    offset=0
                )
                total_count = len(all_projects)
                
                # Convert entities to DTOs
                project_dtos = [
                    MangaProjectDTO(
                        project_id=str(project.project_id),
                        user_id=str(project.user_id),
                        title=project.title,
                        status=project.status,
                        metadata=project.metadata,
                        settings=project.settings,
                        total_pages=project.total_pages,
                        created_at=project.created_at,
                        updated_at=project.updated_at,
                        expires_at=project.expires_at
                    ) for project in projects
                ]
                
                return PaginatedResult.create(
                    items=project_dtos,
                    total_count=total_count,
                    pagination=query.pagination
                )
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to list projects: {str(e)}",
                "PROJECT_LIST_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result


class SearchMangaProjectsQueryHandler(AbstractQueryHandler[SearchMangaProjectsQuery, List[MangaProjectDTO]], BaseHandler):
    """Handler for searching manga projects."""
    
    def __init__(self, project_repository: MangaProjectsRepository):
        super().__init__()
        self.project_repository = project_repository
    
    async def handle(self, query: SearchMangaProjectsQuery) -> QueryResult[List[MangaProjectDTO]]:
        """Handle search projects query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Search projects from repository
                projects = await self.project_repository.search_projects(
                    search_term=query.search_term,
                    user_id=UUID(query.user_id) if query.user_id else None,
                    search_fields=query.search_fields,
                    status=query.status,
                    limit=query.pagination.page_size,
                    offset=query.pagination.offset
                )
                
                # Convert entities to DTOs
                project_dtos = [
                    MangaProjectDTO(
                        project_id=str(project.project_id),
                        user_id=str(project.user_id),
                        title=project.title,
                        status=project.status,
                        metadata=project.metadata,
                        settings=project.settings,
                        total_pages=project.total_pages,
                        created_at=project.created_at,
                        updated_at=project.updated_at,
                        expires_at=project.expires_at
                    ) for project in projects
                ]
                
                return project_dtos
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to search projects: {str(e)}",
                "PROJECT_SEARCH_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result


class GetMangaProjectStatsQueryHandler(AbstractQueryHandler[GetMangaProjectStatsQuery, MangaProjectStatsDTO], BaseHandler):
    """Handler for getting project statistics."""
    
    def __init__(self, project_repository: MangaProjectsRepository):
        super().__init__()
        self.project_repository = project_repository
    
    async def handle(self, query: GetMangaProjectStatsQuery) -> QueryResult[MangaProjectStatsDTO]:
        """Handle get project stats query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get stats from repository
                stats_data = await self.project_repository.get_project_stats(
                    UUID(query.project_id)
                )
                
                # Create stats DTO
                stats = MangaProjectStatsDTO(
                    project_id=stats_data["project_id"],
                    title=stats_data["title"],
                    status=stats_data["status"],
                    total_pages=stats_data.get("total_pages", 0),
                    file_count=stats_data.get("file_count", 0),
                    tag_count=stats_data.get("tag_count", 0),
                    created_at=datetime.fromisoformat(stats_data["created_at"]),
                    updated_at=datetime.fromisoformat(stats_data["updated_at"]),
                    is_expired=stats_data.get("is_expired", False)
                )
                
                return stats
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            if not result:
                error_result = QueryResult.not_found_error("Project")
                self.log_query_execution(query, error_result)
                return error_result
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except ProjectNotFoundError:
            error_result = QueryResult.not_found_error("Project")
            self.log_query_execution(query, error_result)
            return error_result
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to get project stats: {str(e)}",
                "PROJECT_STATS_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result