"""Service health check and monitoring utilities."""

import asyncio
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Health status for a service component."""
    name: str
    status: ServiceStatus
    message: str = ""
    last_check: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "last_check": self.last_check.isoformat(),
            "metadata": self.metadata
        }


class HealthMonitor:
    """Monitor and report health status of service components."""
    
    def __init__(self):
        self._health_checks: Dict[str, ServiceHealth] = {}
        self._critical_services = {"database", "redis", "ai_service"}
        self._degraded_threshold = 0.5  # 50% of services degraded = overall degraded
    
    def register_health(
        self,
        name: str,
        status: ServiceStatus,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register or update health status for a service."""
        self._health_checks[name] = ServiceHealth(
            name=name,
            status=status,
            message=message,
            metadata=metadata or {}
        )
        
        # Log critical service issues
        if name in self._critical_services and status == ServiceStatus.UNHEALTHY:
            logger.error(f"Critical service {name} is unhealthy: {message}")
    
    async def check_database(self, db_session_func) -> ServiceHealth:
        """Check database connectivity and performance."""
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Attempt to get a session and execute a simple query
            async with db_session_func() as session:
                result = await session.execute("SELECT 1")
                _ = result.scalar()
            
            query_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if query_time < 10:  # Less than 10ms
                status = ServiceStatus.HEALTHY
                message = f"Database responding normally ({query_time:.2f}ms)"
            elif query_time < 100:  # Less than 100ms
                status = ServiceStatus.DEGRADED
                message = f"Database response slow ({query_time:.2f}ms)"
            else:
                status = ServiceStatus.UNHEALTHY
                message = f"Database response very slow ({query_time:.2f}ms)"
            
            return ServiceHealth(
                name="database",
                status=status,
                message=message,
                metadata={"response_time_ms": query_time}
            )
            
        except Exception as e:
            logger.exception("Database health check failed")
            return ServiceHealth(
                name="database",
                status=ServiceStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}"
            )
    
    async def check_redis(self, redis_client) -> ServiceHealth:
        """Check Redis connectivity and performance."""
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Ping Redis
            pong = await redis_client.ping()
            
            if not pong:
                return ServiceHealth(
                    name="redis",
                    status=ServiceStatus.UNHEALTHY,
                    message="Redis ping failed"
                )
            
            # Check memory usage
            info = await redis_client.info("memory")
            used_memory = info.get("used_memory", 0)
            max_memory = info.get("maxmemory", 0)
            
            ping_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if ping_time < 5:  # Less than 5ms
                status = ServiceStatus.HEALTHY
                message = f"Redis responding normally ({ping_time:.2f}ms)"
            elif ping_time < 50:  # Less than 50ms
                status = ServiceStatus.DEGRADED
                message = f"Redis response slow ({ping_time:.2f}ms)"
            else:
                status = ServiceStatus.UNHEALTHY
                message = f"Redis response very slow ({ping_time:.2f}ms)"
            
            # Check memory usage if max_memory is set
            if max_memory > 0:
                memory_usage = (used_memory / max_memory) * 100
                if memory_usage > 90:
                    status = ServiceStatus.DEGRADED
                    message += f" | High memory usage ({memory_usage:.1f}%)"
            
            return ServiceHealth(
                name="redis",
                status=status,
                message=message,
                metadata={
                    "response_time_ms": ping_time,
                    "used_memory_mb": used_memory / (1024 * 1024),
                    "memory_usage_percent": memory_usage if max_memory > 0 else None
                }
            )
            
        except Exception as e:
            logger.exception("Redis health check failed")
            return ServiceHealth(
                name="redis",
                status=ServiceStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}"
            )
    
    async def check_ai_service(self, ai_service) -> ServiceHealth:
        """Check AI service availability."""
        try:
            # Check if service is initialized
            if not ai_service:
                return ServiceHealth(
                    name="ai_service",
                    status=ServiceStatus.UNHEALTHY,
                    message="AI service not initialized"
                )
            
            # Check if API clients are available
            if not hasattr(ai_service, 'gemini_client') or not ai_service.gemini_client:
                return ServiceHealth(
                    name="ai_service",
                    status=ServiceStatus.DEGRADED,
                    message="Gemini client not available"
                )
            
            if not hasattr(ai_service, 'imagen_client') or not ai_service.imagen_client:
                return ServiceHealth(
                    name="ai_service",
                    status=ServiceStatus.DEGRADED,
                    message="Imagen client not available"
                )
            
            return ServiceHealth(
                name="ai_service",
                status=ServiceStatus.HEALTHY,
                message="AI service operational",
                metadata={
                    "gemini_available": True,
                    "imagen_available": True
                }
            )
            
        except Exception as e:
            logger.exception("AI service health check failed")
            return ServiceHealth(
                name="ai_service",
                status=ServiceStatus.UNHEALTHY,
                message=f"AI service check failed: {str(e)}"
            )
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        if not self._health_checks:
            return {
                "status": ServiceStatus.UNKNOWN.value,
                "message": "No health checks registered",
                "services": {},
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Count service statuses
        healthy_count = sum(
            1 for h in self._health_checks.values() 
            if h.status == ServiceStatus.HEALTHY
        )
        degraded_count = sum(
            1 for h in self._health_checks.values() 
            if h.status == ServiceStatus.DEGRADED
        )
        unhealthy_count = sum(
            1 for h in self._health_checks.values() 
            if h.status == ServiceStatus.UNHEALTHY
        )
        
        # Check critical services
        critical_unhealthy = any(
            self._health_checks.get(svc, ServiceHealth(svc, ServiceStatus.UNKNOWN)).status == ServiceStatus.UNHEALTHY
            for svc in self._critical_services
        )
        
        # Determine overall status
        if critical_unhealthy or unhealthy_count > 0:
            overall_status = ServiceStatus.UNHEALTHY
            message = f"{unhealthy_count} service(s) unhealthy"
        elif degraded_count / len(self._health_checks) >= self._degraded_threshold:
            overall_status = ServiceStatus.DEGRADED
            message = f"{degraded_count} service(s) degraded"
        elif degraded_count > 0:
            overall_status = ServiceStatus.DEGRADED
            message = f"{degraded_count} service(s) degraded, system operational"
        else:
            overall_status = ServiceStatus.HEALTHY
            message = "All services healthy"
        
        return {
            "status": overall_status.value,
            "message": message,
            "services": {
                name: health.to_dict() 
                for name, health in self._health_checks.items()
            },
            "summary": {
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "total": len(self._health_checks)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def run_all_checks(
        self,
        db_session_func=None,
        redis_client=None,
        ai_service=None
    ) -> Dict[str, Any]:
        """Run all registered health checks."""
        tasks = []
        
        if db_session_func:
            tasks.append(self.check_database(db_session_func))
        
        if redis_client:
            tasks.append(self.check_redis(redis_client))
        
        if ai_service:
            tasks.append(self.check_ai_service(ai_service))
        
        # Run all checks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, ServiceHealth):
                    self.register_health(
                        name=result.name,
                        status=result.status,
                        message=result.message,
                        metadata=result.metadata
                    )
                elif isinstance(result, Exception):
                    logger.error(f"Health check failed with exception: {result}")
        
        return self.get_overall_health()


# Global health monitor instance
health_monitor = HealthMonitor()