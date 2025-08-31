"""
Query Bus Implementation - CQRS Query Dispatch System
Provides type-safe query routing, caching, and performance optimization.
"""

import asyncio
import time
from typing import Dict, Type, TypeVar, Generic, Callable, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import uuid
import hashlib
import json

from app.application.queries.base_query import AbstractQuery, QueryResult
from app.application.handlers.base_handler import BaseQueryHandler

# Type definitions
TQuery = TypeVar('TQuery', bound=AbstractQuery)
TResult = TypeVar('TResult')

logger = logging.getLogger(__name__)


@dataclass
class QueryContext:
    """Query execution context with metadata."""
    query_id: str
    user_id: Optional[str]
    correlation_id: str
    started_at: datetime
    metadata: Dict[str, Any]
    cache_enabled: bool = True
    cache_ttl_seconds: Optional[int] = None


@dataclass
class CacheEntry:
    """Cache entry for query results."""
    data: Any
    created_at: datetime
    ttl_seconds: int
    cache_key: str
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry_time


class QueryMiddleware(ABC):
    """Base class for query middleware."""
    
    @abstractmethod
    async def handle(
        self, 
        query: AbstractQuery, 
        context: QueryContext,
        next_handler: Callable
    ) -> QueryResult:
        """Execute middleware logic."""
        pass


class CachingMiddleware(QueryMiddleware):
    """Caches query results to improve performance."""
    
    def __init__(self, default_ttl_seconds: int = 300):
        self.default_ttl_seconds = default_ttl_seconds
        self.cache: Dict[str, CacheEntry] = {}  # In production, use Redis
    
    def _generate_cache_key(self, query: AbstractQuery, user_id: Optional[str]) -> str:
        """Generate cache key for query."""
        query_data = {
            "query_type": type(query).__name__,
            "query_data": query.dict() if hasattr(query, 'dict') else str(query),
            "user_id": user_id
        }
        query_json = json.dumps(query_data, sort_keys=True)
        return hashlib.md5(query_json.encode()).hexdigest()
    
    async def handle(
        self, 
        query: AbstractQuery, 
        context: QueryContext,
        next_handler: Callable
    ) -> QueryResult:
        """Handle caching logic."""
        if not context.cache_enabled:
            return await next_handler()
        
        # Generate cache key
        cache_key = self._generate_cache_key(query, context.user_id)
        
        # Check cache
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired():
                logger.debug(
                    f"Cache hit for query: {type(query).__name__}",
                    extra={"query_id": context.query_id, "cache_key": cache_key}
                )
                return QueryResult.success(entry.data)
            else:
                # Remove expired entry
                del self.cache[cache_key]
        
        # Execute query
        result = await next_handler()
        
        # Cache successful results
        if result.is_success():
            ttl = context.cache_ttl_seconds or self.default_ttl_seconds
            entry = CacheEntry(
                data=result.data,
                created_at=datetime.utcnow(),
                ttl_seconds=ttl,
                cache_key=cache_key
            )
            self.cache[cache_key] = entry
            
            logger.debug(
                f"Cached query result: {type(query).__name__}",
                extra={"query_id": context.query_id, "cache_key": cache_key, "ttl": ttl}
            )
        
        return result
    
    def invalidate_cache(self, cache_key: Optional[str] = None):
        """Invalidate cache entries."""
        if cache_key:
            self.cache.pop(cache_key, None)
        else:
            self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_hit_ratio": getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1)
        }


class PerformanceMiddleware(QueryMiddleware):
    """Monitors query performance and implements optimizations."""
    
    def __init__(self):
        self.performance_stats = {}
    
    async def handle(
        self, 
        query: AbstractQuery, 
        context: QueryContext,
        next_handler: Callable
    ) -> QueryResult:
        """Monitor query performance."""
        query_type = type(query).__name__
        start_time = time.time()
        
        try:
            result = await next_handler()
            
            execution_time = time.time() - start_time
            
            # Update performance stats
            if query_type not in self.performance_stats:
                self.performance_stats[query_type] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "total_execution_time": 0.0,
                    "average_execution_time": 0.0,
                    "min_execution_time": float('inf'),
                    "max_execution_time": 0.0
                }
            
            stats = self.performance_stats[query_type]
            stats["total_executions"] += 1
            stats["total_execution_time"] += execution_time
            
            if result.is_success():
                stats["successful_executions"] += 1
            else:
                stats["failed_executions"] += 1
            
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_executions"]
            stats["min_execution_time"] = min(stats["min_execution_time"], execution_time)
            stats["max_execution_time"] = max(stats["max_execution_time"], execution_time)
            
            # Log slow queries
            if execution_time > 1.0:  # Log queries taking more than 1 second
                logger.warning(
                    f"Slow query detected: {query_type}",
                    extra={
                        "query_id": context.query_id,
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "query_type": query_type
                    }
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Update failure stats
            if query_type not in self.performance_stats:
                self.performance_stats[query_type] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "total_execution_time": 0.0,
                    "average_execution_time": 0.0,
                    "min_execution_time": float('inf'),
                    "max_execution_time": 0.0
                }
            
            stats = self.performance_stats[query_type]
            stats["total_executions"] += 1
            stats["failed_executions"] += 1
            stats["total_execution_time"] += execution_time
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_executions"]
            
            raise
    
    def get_performance_stats(self, query_type: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics."""
        if query_type:
            return self.performance_stats.get(query_type, {})
        return self.performance_stats.copy()


class ValidationMiddleware(QueryMiddleware):
    """Validates queries before execution."""
    
    async def handle(
        self, 
        query: AbstractQuery, 
        context: QueryContext,
        next_handler: Callable
    ) -> QueryResult:
        """Validate query and delegate to next handler."""
        try:
            # Validate query structure
            validation_result = query.validate()
            if not validation_result.is_valid:
                logger.warning(
                    f"Query validation failed: {validation_result.errors}",
                    extra={"query_id": context.query_id, "query_type": type(query).__name__}
                )
                return QueryResult.failure(
                    error_code="validation_failed",
                    error=f"Validation errors: {', '.join(validation_result.errors)}"
                )
            
            # Delegate to next handler
            return await next_handler()
            
        except Exception as e:
            logger.error(
                f"Query validation middleware error: {str(e)}",
                extra={"query_id": context.query_id, "error": str(e)}
            )
            return QueryResult.failure(
                error_code="validation_error",
                error=f"Validation failed: {str(e)}"
            )


class LoggingMiddleware(QueryMiddleware):
    """Logs query execution with structured logging."""
    
    async def handle(
        self, 
        query: AbstractQuery, 
        context: QueryContext,
        next_handler: Callable
    ) -> QueryResult:
        """Log query execution."""
        query_type = type(query).__name__
        
        logger.debug(
            f"Query execution started: {query_type}",
            extra={
                "query_id": context.query_id,
                "query_type": query_type,
                "user_id": context.user_id,
                "correlation_id": context.correlation_id,
                "cache_enabled": context.cache_enabled
            }
        )
        
        start_time = time.time()
        try:
            result = await next_handler()
            
            execution_time = time.time() - start_time
            log_level = logging.DEBUG if result.is_success() else logging.ERROR
            
            logger.log(
                log_level,
                f"Query execution completed: {query_type}",
                extra={
                    "query_id": context.query_id,
                    "query_type": query_type,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "success": result.is_success(),
                    "error_code": result.error_code if not result.is_success() else None,
                    "result_count": len(result.data) if isinstance(result.data, (list, dict)) else None
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Query execution exception: {query_type}",
                extra={
                    "query_id": context.query_id,
                    "query_type": query_type,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "exception": str(e),
                    "success": False
                },
                exc_info=True
            )
            raise


class QueryBus:
    """
    Query Bus implementation with caching and performance monitoring.
    Provides type-safe query dispatch and execution.
    """
    
    def __init__(self):
        self._handlers: Dict[Type[AbstractQuery], BaseQueryHandler] = {}
        self._middleware: List[QueryMiddleware] = []
        self._default_middleware_enabled = True
        self._caching_middleware: Optional[CachingMiddleware] = None
        self._performance_middleware: Optional[PerformanceMiddleware] = None
    
    def register_handler(self, query_type: Type[TQuery], handler: BaseQueryHandler[TQuery, Any]):
        """Register a query handler for a specific query type."""
        self._handlers[query_type] = handler
        logger.info(f"Registered handler for query: {query_type.__name__}")
    
    def add_middleware(self, middleware: QueryMiddleware):
        """Add middleware to the pipeline."""
        self._middleware.append(middleware)
        
        # Keep references to special middleware
        if isinstance(middleware, CachingMiddleware):
            self._caching_middleware = middleware
        elif isinstance(middleware, PerformanceMiddleware):
            self._performance_middleware = middleware
            
        logger.info(f"Added middleware: {type(middleware).__name__}")
    
    def setup_default_middleware(self):
        """Setup default middleware pipeline."""
        if self._default_middleware_enabled:
            self.add_middleware(ValidationMiddleware())
            self.add_middleware(LoggingMiddleware())
            self.add_middleware(CachingMiddleware(default_ttl_seconds=300))
            self.add_middleware(PerformanceMiddleware())
    
    async def execute(
        self, 
        query: TQuery, 
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cache_enabled: bool = True,
        cache_ttl_seconds: Optional[int] = None
    ) -> QueryResult[Any]:
        """
        Execute a query through the middleware pipeline.
        
        Args:
            query: Query to execute
            user_id: ID of the user executing the query
            correlation_id: Correlation ID for request tracking
            metadata: Additional metadata
            cache_enabled: Whether to enable caching for this query
            cache_ttl_seconds: Override default cache TTL
            
        Returns:
            QueryResult with execution result
        """
        query_type = type(query)
        
        # Check if handler is registered
        if query_type not in self._handlers:
            logger.error(f"No handler registered for query: {query_type.__name__}")
            return QueryResult.failure(
                error_code="no_handler",
                error=f"No handler registered for query: {query_type.__name__}"
            )
        
        # Create execution context
        context = QueryContext(
            query_id=str(uuid.uuid4()),
            user_id=user_id,
            correlation_id=correlation_id or str(uuid.uuid4()),
            started_at=datetime.utcnow(),
            metadata=metadata or {},
            cache_enabled=cache_enabled,
            cache_ttl_seconds=cache_ttl_seconds
        )
        
        # Build middleware pipeline
        async def execute_handler() -> QueryResult:
            handler = self._handlers[query_type]
            return await handler.handle(query)
        
        # Chain middleware
        pipeline = execute_handler
        for middleware in reversed(self._middleware):
            current_middleware = middleware
            current_pipeline = pipeline
            
            async def middleware_wrapper():
                return await current_middleware.handle(query, context, current_pipeline)
            
            pipeline = middleware_wrapper
        
        # Execute through pipeline
        try:
            return await pipeline()
        except Exception as e:
            logger.error(
                f"Query execution failed with exception: {str(e)}",
                extra={
                    "query_id": context.query_id,
                    "query_type": query_type.__name__,
                    "exception": str(e)
                },
                exc_info=True
            )
            return QueryResult.failure(
                error_code="execution_exception",
                error=f"Query execution failed: {str(e)}"
            )
    
    def get_registered_handlers(self) -> Dict[str, str]:
        """Get list of registered handlers."""
        return {
            query_type.__name__: type(handler).__name__
            for query_type, handler in self._handlers.items()
        }
    
    def get_middleware_info(self) -> List[str]:
        """Get information about registered middleware."""
        return [type(middleware).__name__ for middleware in self._middleware]
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics."""
        if self._caching_middleware:
            return self._caching_middleware.get_cache_stats()
        return None
    
    def get_performance_stats(self, query_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get performance statistics."""
        if self._performance_middleware:
            return self._performance_middleware.get_performance_stats(query_type)
        return None
    
    def invalidate_cache(self, cache_key: Optional[str] = None):
        """Invalidate cache entries."""
        if self._caching_middleware:
            self._caching_middleware.invalidate_cache(cache_key)


# Global query bus instance
query_bus = QueryBus()

# Setup default middleware on import
query_bus.setup_default_middleware()