"""Phase execution management with timeout and retry logic."""

import asyncio
import time
from typing import Any, Callable, Dict, Optional
from datetime import datetime

from app.core.logging import LoggerMixin


class ExecutionResult:
    """Result of phase execution."""
    
    def __init__(
        self,
        success: bool,
        result: Any = None,
        error: Optional[Exception] = None,
        execution_time: float = 0.0,
        retries_used: int = 0
    ):
        self.success = success
        self.result = result
        self.error = error
        self.execution_time = execution_time
        self.retries_used = retries_used


class PhaseExecutor(LoggerMixin):
    """Manages phase execution with timeout, retry, and monitoring."""
    
    def __init__(
        self,
        default_timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize executor.
        
        Args:
            default_timeout: Default timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
        """
        super().__init__()
        
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.logger.debug(
            "PhaseExecutor initialized",
            timeout=default_timeout,
            max_retries=max_retries
        )
    
    async def execute_with_timeout(
        self,
        func: Callable,
        *args,
        timeout: Optional[int] = None,
        enable_retry: bool = True,
        **kwargs
    ) -> Any:
        """Execute function with timeout and retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            timeout: Timeout in seconds (uses default if None)
            enable_retry: Whether to enable retry on failure
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            asyncio.TimeoutError: If execution times out
            Exception: If execution fails after all retries
        """
        timeout = timeout or self.default_timeout
        retries_used = 0
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                self.logger.debug(
                    "Executing phase function",
                    attempt=attempt + 1,
                    timeout=timeout
                )
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
                
                execution_time = time.time() - start_time
                
                self.logger.info(
                    "Phase execution completed",
                    execution_time=execution_time,
                    attempt=attempt + 1
                )
                
                return result
                
            except asyncio.TimeoutError as e:
                execution_time = time.time() - start_time
                retries_used = attempt
                last_error = e
                
                self.logger.warning(
                    "Phase execution timeout",
                    timeout=timeout,
                    execution_time=execution_time,
                    attempt=attempt + 1
                )
                
                if not enable_retry or attempt >= self.max_retries:
                    raise
                
                # Wait before retry
                await asyncio.sleep(self.retry_delay * (attempt + 1))
                
            except Exception as e:
                execution_time = time.time() - start_time
                retries_used = attempt
                last_error = e
                
                self.logger.error(
                    "Phase execution error",
                    error=str(e),
                    execution_time=execution_time,
                    attempt=attempt + 1
                )
                
                if not enable_retry or attempt >= self.max_retries:
                    raise
                
                # Wait before retry with exponential backoff
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        # This should not be reached due to the raise statements above
        raise last_error or Exception("Execution failed after all retries")
    
    async def execute_with_circuit_breaker(
        self,
        func: Callable,
        *args,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        **kwargs
    ) -> ExecutionResult:
        """Execute function with circuit breaker pattern.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time before attempting to close circuit
            **kwargs: Keyword arguments
            
        Returns:
            ExecutionResult with success status and result/error
        """
        # Simplified circuit breaker implementation
        # In production, this would use a proper circuit breaker library
        
        start_time = time.time()
        
        try:
            result = await self.execute_with_timeout(func, *args, **kwargs)
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=False,
                error=e,
                execution_time=execution_time
            )
    
    async def execute_parallel(
        self,
        tasks: Dict[str, Callable],
        max_concurrent: int = 5,
        timeout: Optional[int] = None
    ) -> Dict[str, ExecutionResult]:
        """Execute multiple functions in parallel with concurrency limit.
        
        Args:
            tasks: Dictionary of task_name -> function mappings
            max_concurrent: Maximum concurrent executions
            timeout: Timeout for each task
            
        Returns:
            Dictionary of task_name -> ExecutionResult mappings
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def execute_single_task(task_name: str, func: Callable):
            """Execute single task with semaphore."""
            async with semaphore:
                return await self.execute_with_circuit_breaker(func, timeout=timeout)
        
        # Create tasks
        concurrent_tasks = [
            execute_single_task(name, func)
            for name, func in tasks.items()
        ]
        
        # Execute all tasks
        task_results = await asyncio.gather(
            *concurrent_tasks,
            return_exceptions=True
        )
        
        # Map results back to task names
        for task_name, result in zip(tasks.keys(), task_results):
            if isinstance(result, Exception):
                results[task_name] = ExecutionResult(
                    success=False,
                    error=result
                )
            else:
                results[task_name] = result
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        return {
            "default_timeout": self.default_timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay
        }