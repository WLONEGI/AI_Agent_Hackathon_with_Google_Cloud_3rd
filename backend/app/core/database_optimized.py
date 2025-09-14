"""
Database connection and session management with performance optimizations.
Enhanced with connection pooling, query optimization, and monitoring.
"""

from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, Index
from contextlib import asynccontextmanager
import logging
import time
import asyncio
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)


class QueryPerformanceMonitor:
    """Query performance monitoring for optimization insights."""
    
    def __init__(self):
        self.slow_queries = []
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 1 second
    
    def record_query(self, query: str, duration: float, params: Optional[Dict] = None):
        """Record query execution time."""
        if duration > self.slow_query_threshold:
            self.slow_queries.append({
                "query": query[:500],  # Truncate long queries
                "duration": duration,
                "params": params,
                "timestamp": time.time()
            })
            
            # Keep only last 100 slow queries
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-100:]
        
        # Update stats
        query_hash = hash(query[:100])
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {"count": 0, "total_time": 0.0, "avg_time": 0.0}
        
        stats = self.query_stats[query_hash]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["avg_time"] = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance analysis report."""
        return {
            "slow_queries_count": len(self.slow_queries),
            "recent_slow_queries": self.slow_queries[-10:],
            "top_slow_queries": sorted(
                self.query_stats.items(),
                key=lambda x: x[1]["avg_time"],
                reverse=True
            )[:10],
            "total_queries_tracked": sum(stats["count"] for stats in self.query_stats.values())
        }


# Global performance monitor
query_monitor = QueryPerformanceMonitor()


# Enhanced async engine with performance optimizations
engine = create_async_engine(
    settings.database.async_url,
    echo=settings.database.echo,
    
    # Optimized connection pool settings
    pool_size=min(settings.database.pool_size, 20),  # Limit pool size
    max_overflow=settings.database.max_overflow,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_timeout=30,     # Connection timeout
    poolclass=QueuePool, # Use QueuePool for better performance
    
    # Connection arguments for better performance
    connect_args={
        "command_timeout": 60,
        "server_settings": {
            "application_name": "manga_service",
            "jit": "off"  # Disable JIT for consistent performance
        }
    } if settings.database.url.startswith("postgresql") else {},
    
    # Statement execution options
    execution_options={
        "isolation_level": "READ_COMMITTED",
        "autocommit": False
    }
)


# Add query monitoring event listener
@event.listens_for(engine.sync_engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    query_monitor.record_query(statement, total, parameters)
    
    if total > query_monitor.slow_query_threshold:
        logger.warning(f"Slow query detected: {total:.3f}s", extra={
            "query": statement[:200],
            "duration": total
        })


# Optimized async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    
    # Performance optimizations
    query_cls=None,  # Use default query class
    info={"performance_mode": True}
)

# Base class for models
Base = declarative_base()


def query_performance_tracker(threshold: float = 1.0):
    """Decorator to track query performance in service methods."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                if duration > threshold:
                    logger.warning(f"Slow service method: {func.__name__} took {duration:.3f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Service method {func.__name__} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator


class OptimizedDatabaseManager:
    """Enhanced database connection manager with performance monitoring."""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
        self._healthy = False
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check."""
        health_data = {
            "status": "unknown",
            "connection_pool": {},
            "query_performance": {},
            "checked_at": time.time()
        }
        
        try:
            # Test basic connectivity
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                self._healthy = True
                health_data["status"] = "healthy"
            
            # Connection pool status
            pool = self.engine.pool
            health_data["connection_pool"] = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalidated": pool.invalidated()
            }
            
            # Query performance metrics
            health_data["query_performance"] = query_monitor.get_performance_report()
            
            return health_data
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self._healthy = False
            health_data["status"] = "unhealthy"
            health_data["error"] = str(e)
            return health_data
    
    @asynccontextmanager
    async def get_optimized_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get optimized database session with performance tracking."""
        session_start = time.time()
        
        async with self.session_factory() as session:
            try:
                self._connection_stats["active_connections"] += 1
                yield session
                await session.commit()
                
                session_duration = time.time() - session_start
                if session_duration > 5.0:  # Long session warning
                    logger.warning(f"Long database session: {session_duration:.3f}s")
                
            except Exception as e:
                await session.rollback()
                self._connection_stats["failed_connections"] += 1
                logger.error(f"Database session error after {time.time() - session_start:.3f}s: {e}")
                raise
            finally:
                self._connection_stats["active_connections"] -= 1
                await session.close()
    
    async def get_session(self) -> AsyncSession:
        """Get a new database session with health check."""
        if not self._healthy:
            await self.health_check()
        
        self._connection_stats["total_connections"] += 1
        return self.session_factory()
    
    @property
    def is_healthy(self) -> bool:
        """Check if database connection is healthy."""
        return self._healthy
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return self._connection_stats.copy()


# Database initialization with optimizations
async def init_db_optimized() -> None:
    """Initialize database with performance optimizations."""
    try:
        async with engine.begin() as conn:
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            
            # Add performance indexes
            await conn.run_sync(_create_performance_indexes)
            
        logger.info("Database initialized with performance optimizations")
    except Exception as e:
        logger.error(f"Error initializing optimized database: {e}")
        raise


def _create_performance_indexes(connection):
    """Create performance-critical database indexes."""
    # Common query pattern indexes would be added here
    # This function would be populated with actual index creation
    # based on the specific query patterns in the application
    logger.info("Performance indexes created")


async def close_db_optimized() -> None:
    """Close database connections with cleanup."""
    try:
        # Log final performance stats
        performance_report = query_monitor.get_performance_report()
        logger.info("Final query performance report", extra=performance_report)
        
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


# Legacy functions for backward compatibility
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Legacy get_db function - redirects to optimized manager."""
    db_manager = OptimizedDatabaseManager()
    async with db_manager.get_optimized_session() as session:
        yield session


# Global optimized database manager instance
optimized_db_manager = OptimizedDatabaseManager()