"""Base middleware classes for CQRS messaging pipeline."""

from abc import ABC, abstractmethod
from typing import Any, List, Callable, Awaitable, Union
import logging

from app.application.commands.base_command import AbstractCommand, CommandResult
from app.application.queries.base_query import AbstractQuery, QueryResult

logger = logging.getLogger(__name__)

Message = Union[AbstractCommand, AbstractQuery]
MessageResult = Union[CommandResult[Any], QueryResult[Any]]
NextHandler = Callable[[], Awaitable[MessageResult]]


class Middleware(ABC):
    """Abstract base class for middleware components.
    
    Middleware provides cross-cutting concerns like:
    - Validation
    - Logging
    - Metrics collection
    - Transaction management
    - Caching
    - Authentication/Authorization
    """
    
    @abstractmethod
    async def handle(self, message: Message, next_handler: NextHandler) -> MessageResult:
        """Handle message through middleware pipeline.
        
        Args:
            message: Command or Query being processed
            next_handler: Next handler in the pipeline
            
        Returns:
            Result from processing the message
        """
        pass
    
    @property
    def name(self) -> str:
        """Get middleware name for logging."""
        return self.__class__.__name__
    
    def should_process(self, message: Message) -> bool:
        """Determine if this middleware should process the message.
        
        Args:
            message: Message to check
            
        Returns:
            True if middleware should process, False to skip
        """
        return True
    
    async def on_before(self, message: Message) -> None:
        """Called before message processing.
        
        Args:
            message: Message about to be processed
        """
        pass
    
    async def on_after(self, message: Message, result: MessageResult) -> None:
        """Called after message processing.
        
        Args:
            message: Message that was processed
            result: Result from processing
        """
        pass
    
    async def on_error(self, message: Message, error: Exception) -> None:
        """Called when message processing fails.
        
        Args:
            message: Message that failed
            error: Exception that occurred
        """
        pass


class MiddlewareChain:
    """Manages execution of middleware pipeline.
    
    Implements the Chain of Responsibility pattern for
    processing messages through multiple middleware components.
    """
    
    def __init__(self, middleware_list: List[Middleware]):
        self.middleware_list = middleware_list.copy()
    
    async def execute(self, message: Message, final_handler: NextHandler) -> MessageResult:
        """Execute message through middleware chain.
        
        Args:
            message: Message to process
            final_handler: Final handler to execute after all middleware
            
        Returns:
            Result from processing
        """
        if not self.middleware_list:
            return await final_handler()
        
        # Create chain by wrapping handlers
        return await self._execute_middleware(0, message, final_handler)
    
    async def _execute_middleware(
        self, 
        index: int, 
        message: Message, 
        final_handler: NextHandler
    ) -> MessageResult:
        """Execute middleware at specific index.
        
        Args:
            index: Current middleware index
            message: Message being processed
            final_handler: Final handler to execute
            
        Returns:
            Result from middleware execution
        """
        if index >= len(self.middleware_list):
            return await final_handler()
        
        middleware = self.middleware_list[index]
        
        # Skip middleware that shouldn't process this message
        if not middleware.should_process(message):
            logger.debug(f"Skipping middleware: {middleware.name} for message: {type(message).__name__}")
            return await self._execute_middleware(index + 1, message, final_handler)
        
        # Create next handler for this middleware
        async def next_handler() -> MessageResult:
            return await self._execute_middleware(index + 1, message, final_handler)
        
        try:
            logger.debug(f"Executing middleware: {middleware.name} for message: {type(message).__name__}")
            
            # Execute middleware with lifecycle hooks
            await middleware.on_before(message)
            result = await middleware.handle(message, next_handler)
            await middleware.on_after(message, result)
            
            return result
            
        except Exception as e:
            logger.exception(f"Middleware {middleware.name} failed: {str(e)}")
            await middleware.on_error(message, e)
            
            # Return appropriate error result
            if isinstance(message, AbstractCommand):
                return CommandResult.error_result(
                    f"Middleware {middleware.name} failed: {str(e)}",
                    "MIDDLEWARE_ERROR"
                )
            else:
                return QueryResult.error_result(
                    f"Middleware {middleware.name} failed: {str(e)}",
                    "MIDDLEWARE_ERROR"
                )


class ConditionalMiddleware(Middleware):
    """Base class for middleware that runs conditionally.
    
    Useful for middleware that should only run for specific
    message types or under certain conditions.
    """
    
    def __init__(self, condition: Callable[[Message], bool]):
        self.condition = condition
    
    def should_process(self, message: Message) -> bool:
        """Check if middleware should process based on condition."""
        try:
            return self.condition(message)
        except Exception as e:
            logger.warning(f"Condition check failed for {self.name}: {str(e)}")
            return False


class AsyncContextMiddleware(Middleware):
    """Base class for middleware that needs async context management.
    
    Provides setup and cleanup hooks for resources that need
    proper lifecycle management.
    """
    
    async def setup(self, message: Message) -> Any:
        """Setup resources before processing.
        
        Args:
            message: Message about to be processed
            
        Returns:
            Context object to pass to cleanup
        """
        return None
    
    async def cleanup(self, message: Message, context: Any, result: MessageResult) -> None:
        """Cleanup resources after processing.
        
        Args:
            message: Message that was processed
            context: Context from setup
            result: Processing result
        """
        pass
    
    async def handle(self, message: Message, next_handler: NextHandler) -> MessageResult:
        """Handle with automatic setup/cleanup."""
        context = None
        
        try:
            context = await self.setup(message)
            result = await next_handler()
            await self.cleanup(message, context, result)
            return result
            
        except Exception as e:
            if context is not None:
                try:
                    # Try to cleanup on error
                    error_result = CommandResult.error_result(str(e), "PROCESSING_ERROR") \
                                  if isinstance(message, AbstractCommand) \
                                  else QueryResult.error_result(str(e), "PROCESSING_ERROR")
                    await self.cleanup(message, context, error_result)
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed in {self.name}: {str(cleanup_error)}")
            
            raise


class PipelineMiddleware(Middleware):
    """Middleware that applies multiple sub-middleware in sequence.
    
    Allows composing complex middleware from simpler components.
    """
    
    def __init__(self, sub_middleware: List[Middleware]):
        self.sub_middleware = sub_middleware
    
    async def handle(self, message: Message, next_handler: NextHandler) -> MessageResult:
        """Execute sub-middleware chain then next handler."""
        sub_chain = MiddlewareChain(self.sub_middleware)
        return await sub_chain.execute(message, next_handler)
    
    @property
    def name(self) -> str:
        """Get composite name including sub-middleware."""
        sub_names = [m.name for m in self.sub_middleware]
        return f"Pipeline({', '.join(sub_names)})"