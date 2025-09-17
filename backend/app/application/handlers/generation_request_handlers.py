"""Generation request-related command and query handlers."""

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
from app.application.commands.generation_request_commands import (
    CreateGenerationRequestCommand,
    UpdateGenerationRequestStatusCommand,
    RetryGenerationRequestCommand,
    CancelGenerationRequestCommand,
    UpdateGenerationProgressCommand
)
from app.application.queries.generation_request_queries import (
    GetGenerationRequestQuery,
    ListGenerationRequestsQuery,
    GetGenerationProgressQuery,
    GetGenerationQueueStatsQuery
)

# DTOs
from app.application.dto.generation_request_dto import (
    GenerationRequestDTO,
    GenerationRequestCreateDTO,
    QueueStatsDTO,
    GenerationRequestProgressDTO
)

# Domain services and repositories
from app.domain.manga.repositories.generation_requests_repository import (
    GenerationRequestsRepository,
    RequestNotFoundError,
    QuotaExceededError,
    RetryLimitExceededError,
    RequestNotCancellableError,
    ConcurrencyLimitExceededError
)
from app.domain.common.entities import GenerationRequestEntity


logger = logging.getLogger(__name__)


class CreateGenerationRequestCommandHandler(AbstractCommandHandler[CreateGenerationRequestCommand, str], BaseHandler):
    """Handler for creating generation requests."""
    
    def __init__(self, request_repository: GenerationRequestsRepository):
        super().__init__()
        self.request_repository = request_repository
    
    async def handle(self, command: CreateGenerationRequestCommand) -> CommandResult[str]:
        """Handle request creation command."""
        try:
            await self.validate_command(command)
            
            # Check user quotas
            daily_usage = await self.request_repository.get_user_daily_quota_usage(
                UUID(command.user_id)
            )
            concurrent_requests = await self.request_repository.get_user_concurrent_requests(
                UUID(command.user_id)
            )
            
            # Simple quota validation (would use UserEntity in production)
            if daily_usage >= 10:  # Default free limit
                raise QuotaExceededError("Daily quota exceeded")
            if concurrent_requests >= 1:  # Default concurrent limit
                raise ConcurrencyLimitExceededError("Concurrent request limit exceeded")
            
            # Create request entity
            request_entity = GenerationRequestEntity(
                request_id=uuid4(),
                project_id=UUID(command.project_id),
                user_id=UUID(command.user_id),
                input_text=command.input_text,
                request_settings=command.request_settings or {},
                status="queued",
                current_module=0,
                retry_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Create request through repository
            created_request = await self.request_repository.create(request_entity)
            request_id = str(created_request.request_id)
            
            self.log_command_execution(command, CommandResult.success_result(request_id))
            return CommandResult.success_result(request_id)
            
        except QuotaExceededError as e:
            error_result = CommandResult.error_result(str(e), "QUOTA_EXCEEDED")
            self.log_command_execution(command, error_result)
            return error_result
        except ConcurrencyLimitExceededError as e:
            error_result = CommandResult.error_result(str(e), "CONCURRENCY_LIMIT_EXCEEDED")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to create request: {str(e)}", 
                "REQUEST_CREATION_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class UpdateGenerationRequestStatusCommandHandler(AbstractCommandHandler[UpdateGenerationRequestStatusCommand, bool], BaseHandler):
    """Handler for updating request status."""
    
    def __init__(self, request_repository: GenerationRequestsRepository):
        super().__init__()
        self.request_repository = request_repository
    
    async def handle(self, command: UpdateGenerationRequestStatusCommand) -> CommandResult[bool]:
        """Handle status update command."""
        try:
            await self.validate_command(command)
            
            # Route to appropriate method based on status
            if command.status == "processing":
                success = await self.request_repository.mark_processing_started(
                    UUID(command.request_id),
                    command.processing_node
                )
            elif command.status == "completed":
                success = await self.request_repository.mark_processing_completed(
                    UUID(command.request_id),
                    command.output_data
                )
            elif command.status == "error":
                success = await self.request_repository.mark_processing_failed(
                    UUID(command.request_id),
                    command.error_message or "Processing failed",
                    command.error_details
                )
            else:
                # General status update
                request = await self.request_repository.find_by_id(UUID(command.request_id))
                if not request:
                    return CommandResult.not_found_error("Request")
                
                request.status = command.status
                request.updated_at = datetime.utcnow()
                
                updated_request = await self.request_repository.update(request)
                success = updated_request is not None
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except RequestNotFoundError:
            error_result = CommandResult.not_found_error("Request")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to update status: {str(e)}", 
                "STATUS_UPDATE_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class RetryGenerationRequestCommandHandler(AbstractCommandHandler[RetryGenerationRequestCommand, bool], BaseHandler):
    """Handler for retrying failed requests."""
    
    def __init__(self, request_repository: GenerationRequestsRepository):
        super().__init__()
        self.request_repository = request_repository
    
    async def handle(self, command: RetryGenerationRequestCommand) -> CommandResult[bool]:
        """Handle retry request command."""
        try:
            await self.validate_command(command)
            
            # Retry through repository
            success = await self.request_repository.retry_request(UUID(command.request_id))
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except RequestNotFoundError:
            error_result = CommandResult.not_found_error("Request")
            self.log_command_execution(command, error_result)
            return error_result
        except RetryLimitExceededError as e:
            error_result = CommandResult.error_result(str(e), "RETRY_LIMIT_EXCEEDED")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to retry request: {str(e)}",
                "REQUEST_RETRY_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class CancelGenerationRequestCommandHandler(AbstractCommandHandler[CancelGenerationRequestCommand, bool], BaseHandler):
    """Handler for cancelling requests."""
    
    def __init__(self, request_repository: GenerationRequestsRepository):
        super().__init__()
        self.request_repository = request_repository
    
    async def handle(self, command: CancelGenerationRequestCommand) -> CommandResult[bool]:
        """Handle cancel request command."""
        try:
            await self.validate_command(command)
            
            # Cancel through repository
            success = await self.request_repository.cancel_request(UUID(command.request_id))
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except RequestNotFoundError:
            error_result = CommandResult.not_found_error("Request")
            self.log_command_execution(command, error_result)
            return error_result
        except RequestNotCancellableError as e:
            error_result = CommandResult.error_result(str(e), "REQUEST_NOT_CANCELLABLE")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to cancel request: {str(e)}",
                "REQUEST_CANCEL_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class UpdateGenerationProgressCommandHandler(AbstractCommandHandler[UpdateGenerationProgressCommand, bool], BaseHandler):
    """Handler for updating request progress."""
    
    def __init__(self, request_repository: GenerationRequestsRepository):
        super().__init__()
        self.request_repository = request_repository
    
    async def handle(self, command: UpdateGenerationProgressCommand) -> CommandResult[bool]:
        """Handle progress update command."""
        try:
            await self.validate_command(command)
            
            # Update progress through repository
            success = await self.request_repository.update_progress(
                UUID(command.request_id),
                command.current_module,
                command.progress_data
            )
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except RequestNotFoundError:
            error_result = CommandResult.not_found_error("Request")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to update progress: {str(e)}",
                "PROGRESS_UPDATE_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class GetGenerationRequestQueryHandler(AbstractQueryHandler[GetGenerationRequestQuery, GenerationRequestDTO], BaseHandler):
    """Handler for getting generation request by ID."""
    
    def __init__(self, request_repository: GenerationRequestsRepository):
        super().__init__()
        self.request_repository = request_repository
    
    async def handle(self, query: GetGenerationRequestQuery) -> QueryResult[GenerationRequestDTO]:
        """Handle get request query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get request from repository
                request = await self.request_repository.find_by_id(UUID(query.request_id))
                
                if not request:
                    return None
                
                # Convert entity to DTO
                request_dto = GenerationRequestDTO(
                    request_id=str(request.request_id),
                    project_id=str(request.project_id),
                    user_id=str(request.user_id),
                    input_text=request.input_text,
                    request_settings=request.request_settings,
                    status=request.status,
                    current_module=request.current_module,
                    started_at=request.started_at,
                    completed_at=request.completed_at,
                    retry_count=request.retry_count,
                    created_at=request.created_at,
                    updated_at=request.updated_at
                )
                
                # Add progress information
                if query.include_progress and request.status == "processing":
                    progress_data = request.request_settings.get("progress", {})
                    request_dto.progress = GenerationRequestProgressDTO(
                        current_module=request.current_module,
                        total_modules=8,
                        progress_percentage=int((request.current_module / 8) * 100),
                        module_name=self._get_module_name(request.current_module),
                        estimated_time_remaining=progress_data.get("estimated_time_remaining"),
                        details=progress_data
                    )
                
                return request_dto
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            if not result:
                error_result = QueryResult.not_found_error("Request")
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
                f"Failed to get request: {str(e)}",
                "REQUEST_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result
    
    def _get_module_name(self, module_index: int) -> str:
        """Get module name by index."""
        module_names = [
            "Text Analysis",
            "Character Extraction", 
            "Panel Generation",
            "Speech Bubble",
            "Background Generation",
            "Style Transfer",
            "Quality Control",
            "Output Formatting"
        ]
        return module_names[module_index] if 0 <= module_index < len(module_names) else "Unknown"


class ListGenerationRequestsQueryHandler(AbstractQueryHandler[ListGenerationRequestsQuery, PaginatedResult[GenerationRequestDTO]], BaseHandler):
    """Handler for listing generation requests."""
    
    def __init__(self, request_repository: GenerationRequestsRepository):
        super().__init__()
        self.request_repository = request_repository
    
    async def handle(self, query: ListGenerationRequestsQuery) -> QueryResult[PaginatedResult[GenerationRequestDTO]]:
        """Handle list requests query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get requests from repository
                requests = await self.request_repository.find_by_user(
                    user_id=UUID(query.user_id),
                    status=query.status,
                    project_id=UUID(query.project_id) if query.project_id else None,
                    limit=query.pagination.page_size,
                    offset=query.pagination.offset,
                    order_by=query.pagination.sort_by or "created_at",
                    order_direction=query.pagination.sort_direction.value
                )
                
                # Get total count (simplified)
                all_requests = await self.request_repository.find_by_user(
                    user_id=UUID(query.user_id),
                    status=query.status,
                    project_id=UUID(query.project_id) if query.project_id else None,
                    limit=1000,
                    offset=0
                )
                total_count = len(all_requests)
                
                # Convert entities to DTOs
                request_dtos = [
                    GenerationRequestDTO(
                        request_id=str(request.request_id),
                        project_id=str(request.project_id),
                        user_id=str(request.user_id),
                        input_text=request.input_text,
                        request_settings=request.request_settings,
                        status=request.status,
                        current_module=request.current_module,
                        started_at=request.started_at,
                        completed_at=request.completed_at,
                        retry_count=request.retry_count,
                        created_at=request.created_at,
                        updated_at=request.updated_at
                    ) for request in requests
                ]
                
                return PaginatedResult.create(
                    items=request_dtos,
                    total_count=total_count,
                    pagination=query.pagination
                )
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to list requests: {str(e)}",
                "REQUEST_LIST_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result


class GetGenerationProgressQueryHandler(AbstractQueryHandler[GetGenerationProgressQuery, GenerationRequestProgressDTO], BaseHandler):
    """Handler for getting request progress."""
    
    def __init__(self, request_repository: GenerationRequestsRepository):
        super().__init__()
        self.request_repository = request_repository
    
    async def handle(self, query: GetGenerationProgressQuery) -> QueryResult[GenerationRequestProgressDTO]:
        """Handle get progress query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get request from repository
                request = await self.request_repository.find_by_id(UUID(query.request_id))
                
                if not request:
                    return None
                
                # Calculate progress
                progress_data = request.request_settings.get("progress", {})
                
                progress = GenerationRequestProgressDTO(
                    current_module=request.current_module,
                    total_modules=8,
                    progress_percentage=int((request.current_module / 8) * 100),
                    module_name=self._get_module_name(request.current_module),
                    estimated_time_remaining=progress_data.get("estimated_time_remaining"),
                    details=progress_data
                )
                
                return progress
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            if not result:
                error_result = QueryResult.not_found_error("Request")
                self.log_query_execution(query, error_result)
                return error_result
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to get progress: {str(e)}",
                "PROGRESS_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result
    
    def _get_module_name(self, module_index: int) -> str:
        """Get module name by index."""
        module_names = [
            "Text Analysis",
            "Character Extraction", 
            "Panel Generation",
            "Speech Bubble",
            "Background Generation",
            "Style Transfer",
            "Quality Control",
            "Output Formatting"
        ]
        return module_names[module_index] if 0 <= module_index < len(module_names) else "Unknown"


class GetGenerationQueueStatsQueryHandler(AbstractQueryHandler[GetGenerationQueueStatsQuery, QueueStatsDTO], BaseHandler):
    """Handler for getting queue statistics."""
    
    def __init__(self, request_repository: GenerationRequestsRepository):
        super().__init__()
        self.request_repository = request_repository
    
    async def handle(self, query: GetGenerationQueueStatsQuery) -> QueryResult[QueueStatsDTO]:
        """Handle get queue stats query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get stats from repository
                stats_data = await self.request_repository.get_queue_stats()
                
                # Create stats DTO
                stats = QueueStatsDTO(
                    queued_count=stats_data["queued_count"],
                    processing_count=stats_data["processing_count"],
                    completed_count=stats_data["completed_count"],
                    failed_count=stats_data["failed_count"],
                    average_wait_time_seconds=stats_data["average_wait_time"],
                    estimated_wait_time_seconds=stats_data["estimated_wait_time"],
                    total_processed_today=stats_data["total_processed_today"]
                )
                
                return stats
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to get queue stats: {str(e)}",
                "QUEUE_STATS_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result