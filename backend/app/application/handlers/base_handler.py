"""Base handler classes for CQRS pattern."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Dict, Type, Any, Optional
import logging
import time
from datetime import datetime

from app.application.commands.base_command import AbstractCommand, CommandResult
from app.application.queries.base_query import AbstractQuery, QueryResult

# Type variables for generic handlers
TCommand = TypeVar('TCommand', bound=AbstractCommand)
TQuery = TypeVar('TQuery', bound=AbstractQuery)  
TResult = TypeVar('TResult')

logger = logging.getLogger(__name__)


class AbstractCommandHandler(ABC, Generic[TCommand, TResult]):
    """Abstract base class for command handlers.
    
    Command handlers are responsible for:
    1. Validating commands
    2. Coordinating with domain services
    3. Managing transactions
    4. Publishing domain events
    """
    
    @abstractmethod
    async def handle(self, command: TCommand) -> CommandResult[TResult]:
        """Handle the command and return result.
        
        Args:
            command: The command to handle
            
        Returns:
            CommandResult with success/error information
        """
        pass
    
    async def validate_command(self, command: TCommand) -> None:
        """Validate command before handling.
        
        Args:
            command: Command to validate
            
        Raises:
            CommandValidationError: If validation fails
        """
        try:
            command.validate()
        except Exception as e:
            logger.warning(f"Command validation failed for {command.get_command_type()}: {str(e)}")
            raise
    
    def log_command_execution(self, command: TCommand, result: CommandResult[TResult]) -> None:
        """Log command execution for audit purposes."""
        logger.info(
            f"Command executed: {command.get_command_type()} "
            f"[{command.command_id}] - Success: {result.success}"
        )
        
        if result.is_error():
            logger.error(
                f"Command failed: {command.get_command_type()} "
                f"[{command.command_id}] - Error: {result.error}"
            )


class AbstractQueryHandler(ABC, Generic[TQuery, TResult]):
    """Abstract base class for query handlers.
    
    Query handlers are responsible for:
    1. Validating queries
    2. Retrieving data from read models/repositories
    3. Applying filtering and pagination
    4. Returning structured results
    """
    
    @abstractmethod
    async def handle(self, query: TQuery) -> QueryResult[TResult]:
        """Handle the query and return result.
        
        Args:
            query: The query to handle
            
        Returns:
            QueryResult with data or error information
        """
        pass
    
    async def validate_query(self, query: TQuery) -> None:
        """Validate query before handling.
        
        Args:
            query: Query to validate
            
        Raises:
            QueryValidationError: If validation fails
        """
        try:
            query.validate()
        except Exception as e:
            logger.warning(f"Query validation failed for {query.get_query_type()}: {str(e)}")
            raise
    
    def log_query_execution(self, query: TQuery, result: QueryResult[TResult]) -> None:
        """Log query execution for monitoring purposes."""
        execution_time = result.execution_time_ms or 0
        logger.info(
            f"Query executed: {query.get_query_type()} "
            f"[{query.query_id}] - Success: {result.success}, "
            f"Time: {execution_time:.2f}ms"
        )
        
        if result.is_error():
            logger.error(
                f"Query failed: {query.get_query_type()} "
                f"[{query.query_id}] - Error: {result.error}"
            )


class BaseHandler:
    """Base handler with common functionality."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute_with_timing(self, operation) -> tuple[Any, float]:
        """Execute operation with timing measurement.
        
        Returns:
            Tuple of (result, execution_time_ms)
        """
        start_time = time.perf_counter()
        try:
            result = await operation()
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            return result, execution_time_ms
        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Operation failed after {execution_time_ms:.2f}ms: {str(e)}")
            raise
    
    def create_error_metadata(self, exception: Exception) -> Dict[str, Any]:
        """Create error metadata from exception."""
        return {
            'exception_type': exception.__class__.__name__,
            'exception_message': str(exception),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def handle_domain_events(self, entity) -> None:
        """Handle domain events from entity.
        
        Args:
            entity: Domain entity with events to handle
        """
        if hasattr(entity, 'get_events'):
            events = entity.get_events()
            for event in events:
                await self._publish_domain_event(event)
            
            # Clear events after handling
            if hasattr(entity, 'clear_events'):
                entity.clear_events()
    
    async def _publish_domain_event(self, event) -> None:
        """Publish domain event to event bus.
        
        Args:
            event: Domain event to publish
        """
        # TODO: Implement event bus integration
        self.logger.info(f"Domain event published: {event.__class__.__name__}")


class HandlerRegistry:
    """Registry for command and query handlers.
    
    Provides centralized registration and lookup of handlers.
    """
    
    def __init__(self):
        self._command_handlers: Dict[Type, AbstractCommandHandler] = {}
        self._query_handlers: Dict[Type, AbstractQueryHandler] = {}
    
    def register_command_handler(
        self,
        command_type: Type[TCommand],
        handler: AbstractCommandHandler[TCommand, Any]
    ) -> None:
        """Register a command handler.
        
        Args:
            command_type: Command class type
            handler: Handler instance
        """
        self._command_handlers[command_type] = handler
        logger.info(f"Registered command handler: {command_type.__name__} -> {handler.__class__.__name__}")
    
    def register_query_handler(
        self,
        query_type: Type[TQuery],
        handler: AbstractQueryHandler[TQuery, Any]
    ) -> None:
        """Register a query handler.
        
        Args:
            query_type: Query class type
            handler: Handler instance
        """
        self._query_handlers[query_type] = handler
        logger.info(f"Registered query handler: {query_type.__name__} -> {handler.__class__.__name__}")
    
    def get_command_handler(self, command_type: Type[TCommand]) -> Optional[AbstractCommandHandler[TCommand, Any]]:
        """Get command handler by type.
        
        Args:
            command_type: Command class type
            
        Returns:
            Handler instance or None if not found
        """
        return self._command_handlers.get(command_type)
    
    def get_query_handler(self, query_type: Type[TQuery]) -> Optional[AbstractQueryHandler[TQuery, Any]]:
        """Get query handler by type.
        
        Args:
            query_type: Query class type
            
        Returns:
            Handler instance or None if not found
        """
        return self._query_handlers.get(query_type)
    
    async def execute_command(self, command: TCommand) -> CommandResult[Any]:
        """Execute command using registered handler.
        
        Args:
            command: Command to execute
            
        Returns:
            CommandResult from handler execution
            
        Raises:
            ValueError: If no handler is registered for command type
        """
        handler = self.get_command_handler(type(command))
        if not handler:
            error_msg = f"No handler registered for command type: {type(command).__name__}"
            logger.error(error_msg)
            return CommandResult.error_result(error_msg, "HANDLER_NOT_FOUND")
        
        try:
            return await handler.handle(command)
        except Exception as e:
            logger.exception(f"Command handler execution failed: {str(e)}")
            return CommandResult.error_result(
                f"Handler execution failed: {str(e)}",
                "HANDLER_EXECUTION_ERROR"
            )
    
    async def execute_query(self, query: TQuery) -> QueryResult[Any]:
        """Execute query using registered handler.
        
        Args:
            query: Query to execute
            
        Returns:
            QueryResult from handler execution
            
        Raises:
            ValueError: If no handler is registered for query type
        """
        handler = self.get_query_handler(type(query))
        if not handler:
            error_msg = f"No handler registered for query type: {type(query).__name__}"
            logger.error(error_msg)
            return QueryResult.error_result(error_msg, "HANDLER_NOT_FOUND")
        
        try:
            return await handler.handle(query)
        except Exception as e:
            logger.exception(f"Query handler execution failed: {str(e)}")
            return QueryResult.error_result(
                f"Handler execution failed: {str(e)}",
                "HANDLER_EXECUTION_ERROR"
            )
    
    def list_registered_handlers(self) -> Dict[str, Any]:
        """List all registered handlers.
        
        Returns:
            Dictionary with command and query handler information
        """
        return {
            'command_handlers': {
                cmd_type.__name__: handler.__class__.__name__
                for cmd_type, handler in self._command_handlers.items()
            },
            'query_handlers': {
                query_type.__name__: handler.__class__.__name__
                for query_type, handler in self._query_handlers.items()
            }
        }


# Global registry instance
handler_registry = HandlerRegistry()