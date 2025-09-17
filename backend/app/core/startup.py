"""Application startup and initialization logic."""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.core.database import init_db, close_db, get_db_context
from app.core.redis_client import redis_manager
from app.core.firebase import initialize_firebase
from app.core.service_health import health_monitor, ServiceStatus
from app.services.integrated_ai_service import IntegratedAIService
from app.services.cache_service import CacheService
from app.services.websocket_service import WebSocketService

logger = logging.getLogger(__name__)


class InitializationMode(Enum):
    FULL = "full"
    DEGRADED = "degraded"
    MINIMAL = "minimal"


@dataclass
class ServiceContainer:
    """Container for all application services."""
    integrated_ai_service: Optional[IntegratedAIService] = None
    cache_service: Optional[CacheService] = None
    websocket_service: Optional[WebSocketService] = None
    initialization_mode: InitializationMode = InitializationMode.MINIMAL
    health_status: Dict[str, Any] = None
    
    def is_ready(self) -> bool:
        """Check if minimum required services are ready."""
        return self.integrated_ai_service is not None


class ApplicationStartup:
    """Handle application initialization with graceful degradation."""
    
    def __init__(self):
        self.services = ServiceContainer()
        self.critical_failures = []
        self.warnings = []
    
    async def initialize_database(self) -> bool:
        """Initialize database connection."""
        try:
            await init_db()
            
            # Verify connection
            health = await health_monitor.check_database(get_db_context)
            health_monitor.register_health(
                name="database",
                status=health.status,
                message=health.message,
                metadata=health.metadata
            )
            
            if health.status == ServiceStatus.HEALTHY:
                logger.info("Database initialized successfully")
                return True
            else:
                logger.warning(f"Database initialized with status: {health.status.value}")
                self.warnings.append(f"Database {health.status.value}: {health.message}")
                return health.status != ServiceStatus.UNHEALTHY
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self.critical_failures.append(f"Database: {str(e)}")
            health_monitor.register_health(
                name="database",
                status=ServiceStatus.UNHEALTHY,
                message=str(e)
            )
            return False
    
    async def initialize_redis(self) -> bool:
        """Initialize Redis connection."""
        try:
            await redis_manager.connect()
            
            # Verify connection
            health = await health_monitor.check_redis(redis_manager.client)
            health_monitor.register_health(
                name="redis",
                status=health.status,
                message=health.message,
                metadata=health.metadata
            )
            
            if health.status == ServiceStatus.HEALTHY:
                logger.info("Redis initialized successfully")
                return True
            else:
                logger.warning(f"Redis initialized with status: {health.status.value}")
                self.warnings.append(f"Redis {health.status.value}: {health.message}")
                return health.status != ServiceStatus.UNHEALTHY
                
        except Exception as e:
            logger.warning(f"Redis initialization failed (non-critical): {e}")
            self.warnings.append(f"Redis unavailable: {str(e)}")
            health_monitor.register_health(
                name="redis",
                status=ServiceStatus.UNHEALTHY,
                message=str(e)
            )
            return False
    
    def initialize_firebase(self) -> bool:
        """Initialize Firebase authentication."""
        try:
            success = initialize_firebase(
                settings.firebase.firebase_project_id,
                settings.firebase.firebase_credentials_path
            )
            
            if success:
                logger.info("Firebase initialized successfully")
                health_monitor.register_health(
                    name="firebase",
                    status=ServiceStatus.HEALTHY,
                    message="Firebase authentication ready"
                )
                return True
            else:
                logger.warning("Firebase initialization failed - authentication may not work")
                self.warnings.append("Firebase authentication unavailable")
                health_monitor.register_health(
                    name="firebase",
                    status=ServiceStatus.DEGRADED,
                    message="Firebase not configured"
                )
                return False
                
        except Exception as e:
            logger.warning(f"Firebase initialization failed (non-critical): {e}")
            self.warnings.append(f"Firebase unavailable: {str(e)}")
            health_monitor.register_health(
                name="firebase",
                status=ServiceStatus.UNHEALTHY,
                message=str(e)
            )
            return False
    
    async def initialize_services(self, redis_available: bool) -> bool:
        """Initialize application services."""
        try:
            # Initialize AI service (critical)
            self.services.integrated_ai_service = IntegratedAIService()
            
            # Check AI service health
            health = await health_monitor.check_ai_service(self.services.integrated_ai_service)
            health_monitor.register_health(
                name="ai_service",
                status=health.status,
                message=health.message,
                metadata=health.metadata
            )
            
            if health.status == ServiceStatus.UNHEALTHY:
                logger.error("AI service initialization failed")
                self.critical_failures.append("AI service unavailable")
                return False
            
            # Initialize cache service (optional, depends on Redis)
            if redis_available:
                try:
                    self.services.cache_service = CacheService()
                    await self.services.cache_service.start_background_tasks()
                    logger.info("Cache service initialized")
                    health_monitor.register_health(
                        name="cache_service",
                        status=ServiceStatus.HEALTHY,
                        message="Cache service operational"
                    )
                except Exception as e:
                    logger.warning(f"Cache service initialization failed: {e}")
                    self.warnings.append(f"Cache service unavailable: {str(e)}")
                    health_monitor.register_health(
                        name="cache_service",
                        status=ServiceStatus.DEGRADED,
                        message=str(e)
                    )
            else:
                logger.info("Cache service skipped (Redis unavailable)")
                health_monitor.register_health(
                    name="cache_service",
                    status=ServiceStatus.DEGRADED,
                    message="Skipped due to Redis unavailability"
                )
            
            # Initialize WebSocket service (optional)
            try:
                self.services.websocket_service = WebSocketService()
                logger.info("WebSocket service initialized")
                health_monitor.register_health(
                    name="websocket_service",
                    status=ServiceStatus.HEALTHY,
                    message="WebSocket service ready"
                )
            except Exception as e:
                logger.warning(f"WebSocket service initialization failed: {e}")
                self.warnings.append(f"WebSocket service unavailable: {str(e)}")
                health_monitor.register_health(
                    name="websocket_service",
                    status=ServiceStatus.DEGRADED,
                    message=str(e)
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            self.critical_failures.append(f"Service initialization: {str(e)}")
            return False
    
    async def startup(self) -> ServiceContainer:
        """Execute startup sequence with graceful degradation."""
        logger.info("Starting AI Manga Generation Service...")
        
        # Initialize components in order of importance
        db_available = await self.initialize_database()
        redis_available = await self.initialize_redis()
        firebase_available = self.initialize_firebase()
        services_available = await self.initialize_services(redis_available)
        
        # Determine initialization mode
        if db_available and services_available and redis_available:
            self.services.initialization_mode = InitializationMode.FULL
            logger.info("Application started in FULL mode - all services available")
        elif db_available and services_available:
            self.services.initialization_mode = InitializationMode.DEGRADED
            logger.warning("Application started in DEGRADED mode - some services unavailable")
        elif services_available:
            self.services.initialization_mode = InitializationMode.MINIMAL
            logger.warning("Application started in MINIMAL mode - critical services only")
        else:
            logger.error("Application failed to start - critical services unavailable")
            raise RuntimeError(
                f"Critical failures during startup: {', '.join(self.critical_failures)}"
            )
        
        # Get overall health status
        self.services.health_status = await health_monitor.run_all_checks(
            db_session_func=get_db_context if db_available else None,
            redis_client=redis_manager.client if redis_available else None,
            ai_service=self.services.integrated_ai_service
        )
        
        # Log summary
        self._log_startup_summary()
        
        return self.services
    
    async def shutdown(self) -> None:
        """Execute shutdown sequence."""
        logger.info("Shutting down AI Manga Generation Service...")
        
        # Stop background tasks
        if self.services.cache_service:
            try:
                await self.services.cache_service.stop_background_tasks()
                logger.info("Cache service stopped")
            except Exception as e:
                logger.error(f"Error stopping cache service: {e}")
        
        # Close connections
        try:
            await redis_manager.disconnect()
            logger.info("Redis disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting Redis: {e}")
        
        try:
            await close_db()
            logger.info("Database closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
        
        logger.info("Application shut down successfully")
    
    def _log_startup_summary(self) -> None:
        """Log startup summary with warnings and status."""
        logger.info("=" * 60)
        logger.info(f"STARTUP SUMMARY - Mode: {self.services.initialization_mode.value.upper()}")
        logger.info("=" * 60)
        
        if self.critical_failures:
            logger.error(f"Critical Failures: {len(self.critical_failures)}")
            for failure in self.critical_failures:
                logger.error(f"  - {failure}")
        
        if self.warnings:
            logger.warning(f"Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        # Log feature availability
        features = {
            "7-Phase Pipeline": self.services.integrated_ai_service is not None,
            "Caching": self.services.cache_service is not None,
            "Real-time Updates": self.services.websocket_service is not None,
            "Authentication": health_monitor._health_checks.get("firebase", None) and 
                           health_monitor._health_checks["firebase"].status != ServiceStatus.UNHEALTHY,
            "Database": health_monitor._health_checks.get("database", None) and
                       health_monitor._health_checks["database"].status != ServiceStatus.UNHEALTHY,
        }
        
        logger.info("Feature Availability:")
        for feature, available in features.items():
            status = "✓" if available else "✗"
            logger.info(f"  [{status}] {feature}")
        
        # Log processing time estimate
        if self.services.integrated_ai_service:
            total_time = sum(settings.phase_timeouts.values())
            logger.info(f"Pipeline ready: ~{total_time}s total processing time")
        
        logger.info("=" * 60)


# Global startup manager
startup_manager = ApplicationStartup()
