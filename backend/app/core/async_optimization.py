"""
Async processing optimizations for manga generation pipeline.
Implements connection pooling, task batching, and concurrent processing.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable, Coroutine
from functools import wraps
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import aiohttp

from app.core.logging import LoggerMixin
from app.core.config import settings


class AsyncOptimizer(LoggerMixin):
    """Async processing optimization manager."""
    
    def __init__(self):
        super().__init__()
        
        # Connection pool for external API calls
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.http_connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=20,  # Max connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        # Thread pool for CPU-intensive tasks
        self.thread_pool = ThreadPoolExecutor(
            max_workers=min(32, (os.cpu_count() or 1) + 4),
            thread_name_prefix="manga_worker"
        )
        
        # Semaphores for rate limiting
        self.ai_api_semaphore = asyncio.Semaphore(settings.ai_models.max_parallel_image_generation)
        self.db_semaphore = asyncio.Semaphore(settings.database.pool_size)
        
        # Task batching settings
        self.batch_size = 10
        self.batch_timeout = 1.0  # seconds
        
        self.logger.info("AsyncOptimizer initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def start(self):
        """Initialize async resources."""
        if not self.http_session:
            self.http_session = aiohttp.ClientSession(
                connector=self.http_connector,
                timeout=aiohttp.ClientTimeout(total=settings.ai_api_timeout),
                headers={"User-Agent": f"{settings.app_name}/{settings.app_version}"}
            )
            self.logger.info("HTTP session initialized")
    
    async def cleanup(self):
        """Cleanup async resources."""
        if self.http_session:
            await self.http_session.close()
            self.http_session = None
        
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        
        self.logger.info("AsyncOptimizer cleanup completed")
    
    def rate_limit(self, semaphore_type: str = "api"):
        """Rate limiting decorator for async functions."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                semaphore = getattr(self, f"{semaphore_type}_semaphore", self.ai_api_semaphore)
                
                async with semaphore:
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    if duration > 10.0:  # Log slow operations
                        self.logger.warning(f"Slow {semaphore_type} operation: {func.__name__} took {duration:.2f}s")
                    
                    return result
            return wrapper
        return decorator
    
    async def batch_process(
        self,
        items: List[Any],
        processor: Callable[[Any], Coroutine],
        batch_size: Optional[int] = None,
        max_concurrency: Optional[int] = None
    ) -> List[Any]:
        """Process items in optimized batches with concurrency control."""
        if not items:
            return []
        
        batch_size = batch_size or self.batch_size
        max_concurrency = max_concurrency or settings.max_parallel_image_generation
        
        results = []
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def process_with_semaphore(item):
            async with semaphore:
                return await processor(item)
        
        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            batch_start = time.time()
            batch_results = await asyncio.gather(
                *[process_with_semaphore(item) for item in batch],
                return_exceptions=True
            )
            batch_duration = time.time() - batch_start
            
            # Log batch performance
            successful = sum(1 for r in batch_results if not isinstance(r, Exception))
            self.logger.info(
                f"Batch processed: {successful}/{len(batch)} successful in {batch_duration:.2f}s"
            )
            
            # Collect successful results
            for result in batch_results:
                if not isinstance(result, Exception):
                    results.append(result)
                else:
                    self.logger.error(f"Batch item failed: {result}")
        
        return results
    
    async def parallel_db_operations(
        self,
        operations: List[Callable[[AsyncSession], Coroutine]],
        db_session: AsyncSession
    ) -> List[Any]:
        """Execute database operations in parallel with proper session management."""
        results = []
        
        # Execute operations with database semaphore
        async def execute_with_db_limit(operation):
            async with self.db_semaphore:
                return await operation(db_session)
        
        operation_results = await asyncio.gather(
            *[execute_with_db_limit(op) for op in operations],
            return_exceptions=True
        )
        
        # Process results
        for i, result in enumerate(operation_results):
            if isinstance(result, Exception):
                self.logger.error(f"DB operation {i} failed: {result}")
            else:
                results.append(result)
        
        return results
    
    async def optimized_http_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Optimized HTTP request with connection reuse."""
        if not self.http_session:
            await self.start()
        
        try:
            async with self.http_session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(f"HTTP {response.status}: {url}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error(f"HTTP timeout: {url}")
            return None
        except Exception as e:
            self.logger.error(f"HTTP error: {url} - {e}")
            return None
    
    async def cpu_bound_task(self, func: Callable, *args, **kwargs) -> Any:
        """Execute CPU-bound task in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, func, *args, **kwargs)
    
    @asynccontextmanager
    async def performance_timer(self, operation_name: str):
        """Context manager for performance timing."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.logger.info(f"Performance: {operation_name} completed in {duration:.3f}s")
            
            if duration > 5.0:
                self.logger.warning(f"Slow operation detected: {operation_name} took {duration:.3f}s")


def async_performance_monitor(operation_name: str, slow_threshold: float = 2.0):
    """Decorator for monitoring async function performance."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                if duration > slow_threshold:
                    logger = LoggerMixin().logger
                    logger.warning(f"Slow {operation_name}: {func.__name__} took {duration:.3f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger = LoggerMixin().logger
                logger.error(f"{operation_name} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator


class TaskBatcher:
    """Intelligent task batching for optimal resource utilization."""
    
    def __init__(self, batch_size: int = 10, timeout: float = 1.0):
        self.batch_size = batch_size
        self.timeout = timeout
        self.pending_tasks = []
        self.batch_timer = None
        self.logger = LoggerMixin().logger
    
    async def add_task(self, task: Coroutine) -> Any:
        """Add task to batch processing queue."""
        self.pending_tasks.append(task)
        
        # Start batch timer if not already running
        if not self.batch_timer:
            self.batch_timer = asyncio.create_task(self._process_batch_on_timeout())
        
        # Process batch if size threshold reached
        if len(self.pending_tasks) >= self.batch_size:
            return await self._process_current_batch()
        
        return None
    
    async def _process_batch_on_timeout(self):
        """Process batch after timeout."""
        await asyncio.sleep(self.timeout)
        if self.pending_tasks:
            await self._process_current_batch()
    
    async def _process_current_batch(self) -> List[Any]:
        """Process current batch of tasks."""
        if not self.pending_tasks:
            return []
        
        batch = self.pending_tasks.copy()
        self.pending_tasks.clear()
        
        if self.batch_timer:
            self.batch_timer.cancel()
            self.batch_timer = None
        
        start_time = time.time()
        results = await asyncio.gather(*batch, return_exceptions=True)
        duration = time.time() - start_time
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        self.logger.info(f"Batch processed: {successful}/{len(batch)} in {duration:.2f}s")
        
        return [r for r in results if not isinstance(r, Exception)]


# Global async optimizer instance
async_optimizer = AsyncOptimizer()

# Import guard for optional imports
try:
    import os
except ImportError:
    import sys
    os = sys.modules.get('os', type('os', (), {'cpu_count': lambda: 4})())