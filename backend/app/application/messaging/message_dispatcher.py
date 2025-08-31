"""Unified message dispatcher for commands and queries."""

from typing import Any, Union, Dict, List, Optional
import logging
from datetime import datetime

from app.application.commands.base_command import AbstractCommand, CommandResult
from app.application.queries.base_query import AbstractQuery, QueryResult
from .command_bus import CommandBus
from .query_bus import QueryBus

logger = logging.getLogger(__name__)

Message = Union[AbstractCommand, AbstractQuery]
MessageResult = Union[CommandResult[Any], QueryResult[Any]]


class MessageDispatcher:
    """Unified dispatcher for commands and queries.
    
    Provides a single entry point for all CQRS operations
    with unified logging, metrics, and error handling.
    """
    
    def __init__(self, command_bus: CommandBus, query_bus: QueryBus):
        self.command_bus = command_bus
        self.query_bus = query_bus
        self._global_metrics: Dict[str, Any] = {
            'total_messages': 0,
            'total_commands': 0,
            'total_queries': 0,
            'failed_messages': 0,
            'start_time': datetime.utcnow().isoformat()
        }
    
    async def dispatch(self, message: Message) -> MessageResult:
        """Dispatch message to appropriate bus.
        
        Args:
            message: Command or Query to dispatch
            
        Returns:
            Result from command or query execution
        """
        self._global_metrics['total_messages'] += 1
        
        try:
            if isinstance(message, AbstractCommand):
                self._global_metrics['total_commands'] += 1
                result = await self.command_bus.dispatch(message)
                
                # Log command execution
                logger.info(
                    f"Command dispatched: {message.get_command_type()} "
                    f"[{message.command_id}] - Success: {result.success}"
                )
                
                return result
                
            elif isinstance(message, AbstractQuery):
                self._global_metrics['total_queries'] += 1
                result = await self.query_bus.dispatch(message)
                
                # Log query execution
                logger.info(
                    f"Query dispatched: {message.get_query_type()} "
                    f"[{message.query_id}] - Success: {result.success}"
                )
                
                return result
                
            else:
                error_msg = f"Unknown message type: {type(message)}"
                logger.error(error_msg)
                self._global_metrics['failed_messages'] += 1
                
                # Return appropriate error result
                if hasattr(message, 'command_id'):
                    return CommandResult.error_result(error_msg, "UNKNOWN_MESSAGE_TYPE")
                else:
                    return QueryResult.error_result(error_msg, "UNKNOWN_MESSAGE_TYPE")
                    
        except Exception as e:
            logger.exception(f"Message dispatch failed: {str(e)}")
            self._global_metrics['failed_messages'] += 1
            
            # Return appropriate error result
            if isinstance(message, AbstractCommand):
                return CommandResult.error_result(
                    f"Dispatch failed: {str(e)}",
                    "DISPATCH_ERROR"
                )
            else:
                return QueryResult.error_result(
                    f"Dispatch failed: {str(e)}",
                    "DISPATCH_ERROR"
                )
    
    async def dispatch_batch(self, messages: List[Message]) -> List[MessageResult]:
        """Dispatch multiple messages in optimized batches.
        
        Args:
            messages: List of commands and queries to dispatch
            
        Returns:
            List of results in same order as input
        """
        if not messages:
            return []
        
        # Separate commands and queries for parallel processing
        commands = [msg for msg in messages if isinstance(msg, AbstractCommand)]
        queries = [msg for msg in messages if isinstance(msg, AbstractQuery)]
        
        # Create mapping to restore original order
        message_order = {}
        for i, message in enumerate(messages):
            message_order[id(message)] = i
        
        results = [None] * len(messages)
        
        # Dispatch commands and queries in parallel
        command_task = self.command_bus.dispatch_many(commands) if commands else []
        query_task = self.query_bus.dispatch_many(queries) if queries else []
        
        # Wait for both batches to complete
        if commands and queries:
            command_results, query_results = await asyncio.gather(command_task, query_task)
        elif commands:
            command_results = await command_task
            query_results = []
        elif queries:
            query_results = await query_task
            command_results = []
        else:
            return []
        
        # Restore original order
        cmd_idx = 0
        query_idx = 0
        
        for message in messages:
            original_idx = message_order[id(message)]
            
            if isinstance(message, AbstractCommand):
                results[original_idx] = command_results[cmd_idx]
                cmd_idx += 1
            else:
                results[original_idx] = query_results[query_idx]
                query_idx += 1
        
        # Update global metrics
        self._global_metrics['total_messages'] += len(messages)
        self._global_metrics['total_commands'] += len(commands)
        self._global_metrics['total_queries'] += len(queries)
        
        failed_count = sum(1 for result in results if not result.success)
        self._global_metrics['failed_messages'] += failed_count
        
        logger.info(
            f"Batch dispatch completed: {len(messages)} messages "
            f"({len(commands)} commands, {len(queries)} queries) - "
            f"{failed_count} failures"
        )
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on messaging system.
        
        Returns:
            Health status and metrics
        """
        try:
            # Basic connectivity test
            test_query = type('TestQuery', (AbstractQuery,), {
                'validate': lambda self: None,
                'get_query_type': lambda self: 'HealthCheckQuery'
            })()
            
            # Don't actually dispatch, just check handler registration
            command_handlers = len(self.command_bus._handlers)
            query_handlers = len(self.query_bus._handlers)
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'handlers': {
                    'command_handlers': command_handlers,
                    'query_handlers': query_handlers,
                    'total_handlers': command_handlers + query_handlers
                },
                'metrics': self._global_metrics.copy(),
                'bus_metrics': {
                    'command_metrics': self.command_bus.get_metrics(),
                    'query_metrics': self.query_bus.get_metrics()
                }
            }
            
        except Exception as e:
            logger.exception(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'metrics': self._global_metrics.copy()
            }
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics from all buses.
        
        Returns:
            Complete metrics report
        """
        command_metrics = self.command_bus.get_metrics()
        query_metrics = self.query_bus.get_metrics()
        
        # Calculate aggregate statistics
        total_command_executions = sum(
            metrics['total_executions'] for metrics in command_metrics.values()
        )
        total_query_executions = sum(
            metrics['total_executions'] for metrics in query_metrics.values()
        )
        
        successful_commands = sum(
            metrics['successful_executions'] for metrics in command_metrics.values()
        )
        successful_queries = sum(
            metrics['successful_executions'] for metrics in query_metrics.values()
        )
        
        return {
            'global_metrics': self._global_metrics.copy(),
            'aggregate_stats': {
                'total_command_executions': total_command_executions,
                'total_query_executions': total_query_executions,
                'command_success_rate': successful_commands / max(total_command_executions, 1),
                'query_success_rate': successful_queries / max(total_query_executions, 1),
                'overall_success_rate': (successful_commands + successful_queries) / 
                                       max(total_command_executions + total_query_executions, 1)
            },
            'command_metrics': command_metrics,
            'query_metrics': query_metrics,
            'handler_info': {
                'command_handlers': self.command_bus.get_handler_info(),
                'query_handlers': self.query_bus.get_handler_info()
            }
        }
    
    def clear_all_metrics(self) -> None:
        """Clear all metrics from dispatcher and buses."""
        self._global_metrics = {
            'total_messages': 0,
            'total_commands': 0,
            'total_queries': 0,
            'failed_messages': 0,
            'start_time': datetime.utcnow().isoformat()
        }
        
        self.command_bus.clear_metrics()
        self.query_bus.clear_metrics()
        
        logger.info("All messaging metrics cleared")


# Default dispatcher instance
def create_message_dispatcher(
    command_bus: Optional[CommandBus] = None,
    query_bus: Optional[QueryBus] = None
) -> MessageDispatcher:
    """Create message dispatcher with optional custom buses.
    
    Args:
        command_bus: Custom command bus or None for default
        query_bus: Custom query bus or None for default
        
    Returns:
        Configured MessageDispatcher instance
    """
    from .command_bus import command_bus as default_command_bus
    from .query_bus import query_bus as default_query_bus
    
    return MessageDispatcher(
        command_bus or default_command_bus,
        query_bus or default_query_bus
    )