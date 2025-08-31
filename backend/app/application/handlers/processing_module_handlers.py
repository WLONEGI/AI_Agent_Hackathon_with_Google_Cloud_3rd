"""Processing module-related command and query handlers."""

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
from app.application.commands.processing_module_commands import (
    StartModuleCommand,
    CompleteModuleCommand,
    FailModuleCommand,
    RetryModuleCommand,
    RecordMetricsCommand,
    CreateCheckpointCommand
)
from app.application.queries.processing_module_queries import (
    GetPerformanceQuery,
    GetBottlenecksQuery,
    GetResourceUsageQuery,
    GetProcessingPipelineQuery
)

# DTOs
from app.application.dto.processing_module_dto import (
    ProcessingModuleDTO,
    PerformanceStatsDTO,
    BottleneckDTO,
    ResourceUsageDTO,
    CheckpointDTO
)

# Domain services and repositories
from app.domain.manga.repositories.processing_modules_repository import (
    ProcessingModulesRepository,
    ModuleNotFoundError,
    ModuleNameExistsError,
    CheckpointNotFoundError,
    ModuleExecutionError
)
from app.domain.common.entities import ProcessingModuleEntity


logger = logging.getLogger(__name__)


class StartModuleCommandHandler(AbstractCommandHandler[StartModuleCommand, str], BaseHandler):
    """Handler for starting module execution."""
    
    def __init__(self, module_repository: ProcessingModulesRepository):
        super().__init__()
        self.module_repository = module_repository
    
    async def handle(self, command: StartModuleCommand) -> CommandResult[str]:
        """Handle start module command."""
        try:
            await self.validate_command(command)
            
            # Record execution start (simplified - would integrate with actual processing system)
            execution_id = str(uuid4())
            
            # In a real system, this would:
            # 1. Validate module exists and is enabled
            # 2. Check dependencies
            # 3. Start actual processing
            # 4. Return execution tracking ID
            
            module = await self.module_repository.find_by_id(UUID(command.module_id))
            if not module:
                return CommandResult.not_found_error("Module")
            
            if not module.is_enabled:
                return CommandResult.error_result("Module is not enabled", "MODULE_DISABLED")
            
            logger.info(f"Started module execution {execution_id} for module {command.module_id}")
            
            result = CommandResult.success_result(execution_id)
            self.log_command_execution(command, result)
            return result
            
        except ModuleNotFoundError:
            error_result = CommandResult.not_found_error("Module")
            self.log_command_execution(command, error_result)
            return error_result
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to start module: {str(e)}", 
                "MODULE_START_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class CompleteModuleCommandHandler(AbstractCommandHandler[CompleteModuleCommand, bool], BaseHandler):
    """Handler for completing module execution."""
    
    def __init__(self, module_repository: ProcessingModulesRepository):
        super().__init__()
        self.module_repository = module_repository
    
    async def handle(self, command: CompleteModuleCommand) -> CommandResult[bool]:
        """Handle complete module command."""
        try:
            await self.validate_command(command)
            
            # Record successful execution metrics
            success = await self.module_repository.record_execution_metrics(
                module_id=UUID(command.module_id),
                request_id=UUID(command.request_id),
                execution_time_seconds=command.execution_time_seconds,
                memory_usage_mb=command.memory_usage_mb,
                cpu_usage_percent=command.cpu_usage_percent,
                success=True
            )
            
            logger.info(f"Completed module execution for module {command.module_id}")
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to complete module: {str(e)}", 
                "MODULE_COMPLETE_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class FailModuleCommandHandler(AbstractCommandHandler[FailModuleCommand, bool], BaseHandler):
    """Handler for failing module execution."""
    
    def __init__(self, module_repository: ProcessingModulesRepository):
        super().__init__()
        self.module_repository = module_repository
    
    async def handle(self, command: FailModuleCommand) -> CommandResult[bool]:
        """Handle fail module command."""
        try:
            await self.validate_command(command)
            
            # Record failed execution metrics
            success = await self.module_repository.record_execution_metrics(
                module_id=UUID(command.module_id),
                request_id=UUID(command.request_id),
                execution_time_seconds=command.execution_time_seconds or 0.0,
                memory_usage_mb=command.memory_usage_mb,
                cpu_usage_percent=command.cpu_usage_percent,
                success=False,
                error_message=command.error_message
            )
            
            logger.warning(f"Failed module execution for module {command.module_id}: {command.error_message}")
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to record module failure: {str(e)}", 
                "MODULE_FAIL_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class RecordMetricsCommandHandler(AbstractCommandHandler[RecordMetricsCommand, bool], BaseHandler):
    """Handler for recording module metrics."""
    
    def __init__(self, module_repository: ProcessingModulesRepository):
        super().__init__()
        self.module_repository = module_repository
    
    async def handle(self, command: RecordMetricsCommand) -> CommandResult[bool]:
        """Handle record metrics command."""
        try:
            await self.validate_command(command)
            
            # Record execution metrics
            success = await self.module_repository.record_execution_metrics(
                module_id=UUID(command.module_id),
                request_id=UUID(command.request_id),
                execution_time_seconds=command.execution_time_seconds,
                memory_usage_mb=command.memory_usage_mb,
                cpu_usage_percent=command.cpu_usage_percent,
                success=command.success,
                error_message=command.error_message
            )
            
            result = CommandResult.success_result(success)
            self.log_command_execution(command, result)
            return result
            
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to record metrics: {str(e)}", 
                "METRICS_RECORD_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class CreateCheckpointCommandHandler(AbstractCommandHandler[CreateCheckpointCommand, str], BaseHandler):
    """Handler for creating processing checkpoints."""
    
    def __init__(self, module_repository: ProcessingModulesRepository):
        super().__init__()
        self.module_repository = module_repository
    
    async def handle(self, command: CreateCheckpointCommand) -> CommandResult[str]:
        """Handle create checkpoint command."""
        try:
            await self.validate_command(command)
            
            # Create checkpoint
            checkpoint_id = await self.module_repository.create_checkpoint(
                request_id=UUID(command.request_id),
                module_id=UUID(command.module_id),
                checkpoint_data=command.checkpoint_data
            )
            
            result = CommandResult.success_result(checkpoint_id)
            self.log_command_execution(command, result)
            return result
            
        except ValueError as e:
            error_result = CommandResult.validation_error(str(e))
            self.log_command_execution(command, error_result)
            return error_result
        except Exception as e:
            error_result = CommandResult.error_result(
                f"Failed to create checkpoint: {str(e)}", 
                "CHECKPOINT_CREATE_ERROR"
            )
            self.log_command_execution(command, error_result)
            return error_result


class GetPerformanceQueryHandler(AbstractQueryHandler[GetPerformanceQuery, PerformanceStatsDTO], BaseHandler):
    """Handler for getting performance statistics."""
    
    def __init__(self, module_repository: ProcessingModulesRepository):
        super().__init__()
        self.module_repository = module_repository
    
    async def handle(self, query: GetPerformanceQuery) -> QueryResult[PerformanceStatsDTO]:
        """Handle get performance query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get performance stats from repository
                stats_data = await self.module_repository.get_performance_stats(
                    module_id=UUID(query.module_id) if query.module_id else None,
                    module_type=query.module_type,
                    period_days=query.period_days
                )
                
                # Create stats DTO
                stats = PerformanceStatsDTO(
                    module_id=query.module_id,
                    module_type=query.module_type,
                    period_days=query.period_days,
                    total_executions=stats_data["total_executions"],
                    success_rate=stats_data["success_rate"],
                    average_execution_time_seconds=stats_data["average_execution_time"],
                    median_execution_time_seconds=stats_data["median_execution_time"],
                    p95_execution_time_seconds=stats_data["p95_execution_time"],
                    average_memory_usage_mb=stats_data["average_memory_usage"],
                    peak_memory_usage_mb=stats_data["peak_memory_usage"],
                    error_distribution=stats_data["error_distribution"]
                )
                
                return stats
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to get performance stats: {str(e)}",
                "PERFORMANCE_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result


class GetBottlenecksQueryHandler(AbstractQueryHandler[GetBottlenecksQuery, List[BottleneckDTO]], BaseHandler):
    """Handler for getting processing bottlenecks."""
    
    def __init__(self, module_repository: ProcessingModulesRepository):
        super().__init__()
        self.module_repository = module_repository
    
    async def handle(self, query: GetBottlenecksQuery) -> QueryResult[List[BottleneckDTO]]:
        """Handle get bottlenecks query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get bottlenecks from repository
                bottlenecks_data = await self.module_repository.get_bottlenecks(
                    period_days=query.period_days
                )
                
                # Convert to DTOs
                bottleneck_dtos = [
                    BottleneckDTO(
                        module_id=bottleneck["module_id"],
                        module_name=bottleneck["module_name"],
                        module_type=bottleneck["module_type"],
                        average_execution_time_seconds=bottleneck["average_time"],
                        execution_count=bottleneck["execution_count"],
                        impact_score=bottleneck["impact_score"],
                        recommendation=bottleneck["recommendation"]
                    ) for bottleneck in bottlenecks_data
                ]
                
                return bottleneck_dtos
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to get bottlenecks: {str(e)}",
                "BOTTLENECKS_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result


class GetResourceUsageQueryHandler(AbstractQueryHandler[GetResourceUsageQuery, ResourceUsageDTO], BaseHandler):
    """Handler for getting resource usage metrics."""
    
    def __init__(self, module_repository: ProcessingModulesRepository):
        super().__init__()
        self.module_repository = module_repository
    
    async def handle(self, query: GetResourceUsageQuery) -> QueryResult[ResourceUsageDTO]:
        """Handle get resource usage query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get resource usage from repository
                usage_data = await self.module_repository.get_resource_usage(
                    module_id=UUID(query.module_id) if query.module_id else None,
                    period_hours=query.period_hours
                )
                
                # Create usage DTO
                usage = ResourceUsageDTO(
                    module_id=query.module_id,
                    period_hours=query.period_hours,
                    current_memory_usage_mb=usage_data["current_memory_usage"],
                    peak_memory_usage_mb=usage_data["peak_memory_usage"],
                    average_cpu_usage_percent=usage_data["average_cpu_usage"],
                    peak_cpu_usage_percent=usage_data["peak_cpu_usage"],
                    concurrent_executions=usage_data["concurrent_executions"],
                    queue_length=usage_data["queue_length"]
                )
                
                return usage
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to get resource usage: {str(e)}",
                "RESOURCE_USAGE_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result


class GetProcessingPipelineQueryHandler(AbstractQueryHandler[GetProcessingPipelineQuery, List[ProcessingModuleDTO]], BaseHandler):
    """Handler for getting processing pipeline modules."""
    
    def __init__(self, module_repository: ProcessingModulesRepository):
        super().__init__()
        self.module_repository = module_repository
    
    async def handle(self, query: GetProcessingPipelineQuery) -> QueryResult[List[ProcessingModuleDTO]]:
        """Handle get processing pipeline query."""
        try:
            await self.validate_query(query)
            
            async def execute_query():
                # Get pipeline modules from repository
                modules = await self.module_repository.get_processing_pipeline()
                
                # Convert entities to DTOs
                module_dtos = [
                    ProcessingModuleDTO(
                        module_id=str(module.module_id),
                        module_name=module.module_name,
                        module_type=module.module_type,
                        version=module.version,
                        is_enabled=module.is_enabled,
                        configuration=module.configuration,
                        dependencies=module.dependencies,
                        created_at=module.created_at,
                        updated_at=module.updated_at
                    ) for module in modules
                ]
                
                return module_dtos
            
            result, execution_time = await self.execute_with_timing(execute_query)
            
            success_result = QueryResult.success_result(result, execution_time)
            self.log_query_execution(query, success_result)
            return success_result
            
        except Exception as e:
            error_result = QueryResult.error_result(
                f"Failed to get processing pipeline: {str(e)}",
                "PIPELINE_QUERY_ERROR"
            )
            self.log_query_execution(query, error_result)
            return error_result