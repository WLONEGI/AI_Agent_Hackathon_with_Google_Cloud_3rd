"""
Circuit Breaker Pattern Implementation
Phase 3: Fault tolerance for external service dependencies
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Optional, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit tripped, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5  # Number of failures before opening
    timeout_seconds: int = 60   # Time to wait before trying again
    success_threshold: int = 3  # Successes needed to close from half-open


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting against cascading failures

    Prevents calls to failing external services and provides graceful degradation
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_success_time: Optional[float] = None

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker

        Args:
            func: The function to call
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Result of the function call

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable for {self._time_until_retry():.1f}s"
                )

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.timeout_seconds

    def _time_until_retry(self) -> float:
        """Calculate time remaining until retry is allowed"""
        if self.last_failure_time is None:
            return 0
        elapsed = time.time() - self.last_failure_time
        return max(0, self.config.timeout_seconds - elapsed)

    def _transition_to_half_open(self) -> None:
        """Transition from OPEN to HALF_OPEN state"""
        logger.info(f"Circuit breaker '{self.name}': OPEN -> HALF_OPEN")
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0

    async def _on_success(self) -> None:
        """Handle successful function execution"""
        self.last_success_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                await self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success in closed state
            self.failure_count = 0

    async def _on_failure(self, exception: Exception) -> None:
        """Handle failed function execution"""
        self.last_failure_time = time.time()
        self.failure_count += 1

        logger.warning(
            f"Circuit breaker '{self.name}': Failure {self.failure_count} - {exception}"
        )

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                await self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately opens the circuit
            await self._transition_to_open()

    async def _transition_to_closed(self) -> None:
        """Transition to CLOSED state (normal operation)"""
        logger.info(f"Circuit breaker '{self.name}': {self.state.value} -> CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0

    async def _transition_to_open(self) -> None:
        """Transition to OPEN state (service unavailable)"""
        logger.error(
            f"Circuit breaker '{self.name}': {self.state.value} -> OPEN "
            f"(failures: {self.failure_count})"
        )
        self.state = CircuitState.OPEN
        self.success_count = 0

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "time_until_retry": self._time_until_retry() if self.state == CircuitState.OPEN else 0
        }


class CircuitBreakerManager:
    """
    Global manager for all circuit breakers in the application
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker by name"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all circuit breakers"""
        total_breakers = len(self._breakers)
        open_breakers = sum(1 for b in self._breakers.values() if b.state == CircuitState.OPEN)

        return {
            "total_breakers": total_breakers,
            "open_breakers": open_breakers,
            "healthy_percentage": ((total_breakers - open_breakers) / max(1, total_breakers)) * 100,
            "status": "healthy" if open_breakers == 0 else "degraded" if open_breakers < total_breakers else "critical"
        }


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()


# Predefined circuit breakers for external services
vertex_ai_breaker = circuit_breaker_manager.get_breaker(
    "vertex_ai",
    CircuitBreakerConfig(failure_threshold=3, timeout_seconds=120)
)

cloud_tasks_breaker = circuit_breaker_manager.get_breaker(
    "cloud_tasks",
    CircuitBreakerConfig(failure_threshold=5, timeout_seconds=60)
)

database_breaker = circuit_breaker_manager.get_breaker(
    "database",
    CircuitBreakerConfig(failure_threshold=10, timeout_seconds=30)
)