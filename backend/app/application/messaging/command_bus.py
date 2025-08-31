"""
Command Bus Implementation - CQRS Command Dispatch System
Provides type-safe command routing and middleware pipeline execution.
"""

import asyncio
import time
from typing import Dict, Type, TypeVar, Generic, Callable, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import logging
import uuid

from app.application.commands.base_command import AbstractCommand, CommandResult
from app.application.handlers.base_handler import BaseCommandHandler

# Type definitions
TCommand = TypeVar('TCommand', bound=AbstractCommand)
TResult = TypeVar('TResult')

logger = logging.getLogger(__name__)


@dataclass
class CommandContext:
    """Command execution context with metadata."""
    command_id: str
    user_id: Optional[str]
    correlation_id: str
    started_at: datetime
    metadata: Dict[str, Any]


class CommandMiddleware(ABC):
    """Base class for command middleware."""
    
    @abstractmethod
    async def handle(
        self, 
        command: AbstractCommand, 
        context: CommandContext,
        next_handler: Callable
    ) -> CommandResult:
        """Execute middleware logic."""
        pass


class ValidationMiddleware(CommandMiddleware):
    """Validates commands before execution."""
    
    async def handle(
        self, 
        command: AbstractCommand, 
        context: CommandContext,
        next_handler: Callable
    ) -> CommandResult:
        """Validate command and delegate to next handler."""
        try:
            # Validate command structure
            validation_result = command.validate()
            if not validation_result.is_valid:
                logger.warning(
                    f"Command validation failed: {validation_result.errors}",
                    extra={"command_id": context.command_id, "command_type": type(command).__name__}
                )
                return CommandResult.failure(
                    error_code="validation_failed",
                    error=f"Validation errors: {', '.join(validation_result.errors)}"
                )
            
            # Delegate to next handler
            return await next_handler()
            
        except Exception as e:
            logger.error(
                f"Validation middleware error: {str(e)}",
                extra={"command_id": context.command_id, "error": str(e)}
            )
            return CommandResult.failure(
                error_code="validation_error",
                error=f"Validation failed: {str(e)}"
            )


class LoggingMiddleware(CommandMiddleware):
    """Logs command execution with structured logging."""
    
    async def handle(
        self, 
        command: AbstractCommand, 
        context: CommandContext,
        next_handler: Callable
    ) -> CommandResult:
        """Log command execution."""
        command_type = type(command).__name__
        
        logger.info(
            f"Command execution started: {command_type}",
            extra={
                "command_id": context.command_id,
                "command_type": command_type,
                "user_id": context.user_id,
                "correlation_id": context.correlation_id
            }
        )
        
        start_time = time.time()
        try:
            result = await next_handler()
            
            execution_time = time.time() - start_time
            if result.is_success():
                logger.info(
                    f"Command execution completed: {command_type}",
                    extra={
                        "command_id": context.command_id,
                        "command_type": command_type,
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "success": True
                    }
                )
            else:
                logger.error(
                    f"Command execution failed: {command_type}",
                    extra={
                        "command_id": context.command_id,
                        "command_type": command_type,
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "error_code": result.error_code,
                        "error_message": result.error,
                        "success": False
                    }
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Command execution exception: {command_type}",
                extra={
                    "command_id": context.command_id,
                    "command_type": command_type,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "exception": str(e),
                    "success": False
                },
                exc_info=True
            )
            raise


class MetricsMiddleware(CommandMiddleware):
    """Collects command execution metrics."""
    
    def __init__(self):
        self.metrics_store = {}  # In production, use proper metrics system
    
    async def handle(
        self, 
        command: AbstractCommand, 
        context: CommandContext,
        next_handler: Callable
    ) -> CommandResult:
        """Collect execution metrics."""
        command_type = type(command).__name__
        start_time = time.time()
        
        try:
            result = await next_handler()
            
            execution_time = time.time() - start_time
            
            # Store metrics (simplified in-memory store)
            if command_type not in self.metrics_store:
                self.metrics_store[command_type] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "total_execution_time": 0.0,
                    "average_execution_time": 0.0
                }
            
            metrics = self.metrics_store[command_type]
            metrics["total_executions"] += 1
            metrics["total_execution_time"] += execution_time
            
            if result.is_success():
                metrics["successful_executions"] += 1
            else:
                metrics["failed_executions"] += 1
                
            metrics["average_execution_time"] = metrics["total_execution_time"] / metrics["total_executions"]
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Record failed execution
            if command_type not in self.metrics_store:
                self.metrics_store[command_type] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "total_execution_time": 0.0,
                    "average_execution_time": 0.0
                }
            
            metrics = self.metrics_store[command_type]
            metrics["total_executions"] += 1
            metrics["failed_executions"] += 1
            metrics["total_execution_time"] += execution_time
            metrics["average_execution_time"] = metrics["total_execution_time"] / metrics["total_executions"]
            
            raise
    
    def get_metrics(self, command_type: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific command type."""
        return self.metrics_store.get(command_type)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all command types."""
        return self.metrics_store.copy()


class CommandBus:
    """
    Command Bus implementation with middleware pipeline support.
    Provides type-safe command dispatch and execution.
    """
    
    def __init__(self):
        self._handlers: Dict[Type[AbstractCommand], BaseCommandHandler] = {}
        self._middleware: List[CommandMiddleware] = []
        self._default_middleware_enabled = True
    
    def register_handler(self, command_type: Type[TCommand], handler: BaseCommandHandler[TCommand, Any]):
        """Register a command handler for a specific command type."""
        self._handlers[command_type] = handler
        logger.info(f"Registered handler for command: {command_type.__name__}")
    
    def add_middleware(self, middleware: CommandMiddleware):
        """Add middleware to the pipeline."""
        self._middleware.append(middleware)
        logger.info(f"Added middleware: {type(middleware).__name__}")
    
    def setup_default_middleware(self):
        """Setup default middleware pipeline."""
        if self._default_middleware_enabled:
            self.add_middleware(ValidationMiddleware())
            self.add_middleware(LoggingMiddleware())
            self.add_middleware(MetricsMiddleware())
    
    async def execute(
        self, 
        command: TCommand, 
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CommandResult[Any]:
        """
        Execute a command through the middleware pipeline.
        
        Args:
            command: Command to execute
            user_id: ID of the user executing the command
            correlation_id: Correlation ID for request tracking
            metadata: Additional metadata
            
        Returns:
            CommandResult with execution result
        """
        command_type = type(command)
        
        # Check if handler is registered
        if command_type not in self._handlers:
            logger.error(f"No handler registered for command: {command_type.__name__}")
            return CommandResult.failure(
                error_code="no_handler",
                error=f"No handler registered for command: {command_type.__name__}"
            )
        
        # Create execution context
        context = CommandContext(
            command_id=str(uuid.uuid4()),
            user_id=user_id,
            correlation_id=correlation_id or str(uuid.uuid4()),
            started_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Build middleware pipeline
        async def execute_handler() -> CommandResult:
            handler = self._handlers[command_type]
            return await handler.handle(command)
        
        # Chain middleware
        pipeline = execute_handler
        for middleware in reversed(self._middleware):
            current_middleware = middleware
            current_pipeline = pipeline
            
            async def middleware_wrapper():
                return await current_middleware.handle(command, context, current_pipeline)
            
            pipeline = middleware_wrapper
        
        # Execute through pipeline
        try:
            return await pipeline()
        except Exception as e:
            logger.error(
                f"Command execution failed with exception: {str(e)}",
                extra={
                    "command_id": context.command_id,
                    "command_type": command_type.__name__,
                    "exception": str(e)
                },
                exc_info=True
            )
            return CommandResult.failure(
                error_code="execution_exception",
                error=f"Command execution failed: {str(e)}"
            )
    
    def get_registered_handlers(self) -> Dict[str, str]:
        """Get list of registered handlers."""
        return {
            command_type.__name__: type(handler).__name__
            for command_type, handler in self._handlers.items()
        }
    
    def get_middleware_info(self) -> List[str]:
        """Get information about registered middleware."""
        return [type(middleware).__name__ for middleware in self._middleware]


# Global command bus instance
command_bus = CommandBus()

# Setup default middleware on import
command_bus.setup_default_middleware()