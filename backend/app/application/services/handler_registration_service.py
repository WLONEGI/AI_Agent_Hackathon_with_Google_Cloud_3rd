"""
Handler Registration Service - Phase 2 CQRS Handler Registration.

This module provides centralized handler registration for Command and Query buses,
enabling complete CQRS implementation with dependency injection support.

Registers all command handlers, query handlers, and their dependencies.
"""

import logging
from typing import Dict, Any

from app.application.messaging.command_bus import CommandBus
from app.application.messaging.query_bus import QueryBus

# Import all command handlers
from app.application.handlers.preview_command_handlers import (
    CreatePreviewVersionHandler,
    UpdatePreviewVersionHandler,
    SetFinalVersionHandler,
    IncrementViewCountHandler,
    DeletePreviewVersionHandler,
    CreatePreviewInteractionHandler,
    UpdateInteractionStatusHandler,
    ApplyInteractionsToVersionHandler,
    CreateQualitySettingsHandler,
    UpdateQualitySettingsHandler,
    UpdatePerformanceMetricsHandler,
    CleanupOldVersionsHandler
)

# Import all query handlers
from app.application.handlers.preview_query_handlers import (
    GetPreviewVersionByIdHandler,
    GetPreviewVersionsByRequestHandler,
    GetVersionTreeHandler,
    GetFinalVersionsHandler,
    GetPreviewInteractionByIdHandler,
    GetInteractionsByVersionHandler,
    GetPendingInteractionsHandler,
    GetInteractionStatisticsHandler,
    GetQualitySettingsByUserHandler,
    GetQualityRecommendationsHandler,
    GetStorageUsageHandler,
    GetVersionPerformanceStatsHandler,
    GetFeedbackHeatmapHandler
)

# Import all commands
from app.application.commands.preview_commands import (
    CreatePreviewVersionCommand,
    UpdatePreviewVersionCommand,
    SetFinalVersionCommand,
    IncrementViewCountCommand,
    DeletePreviewVersionCommand,
    CreatePreviewInteractionCommand,
    UpdateInteractionStatusCommand,
    ApplyInteractionsToVersionCommand,
    CreateQualitySettingsCommand,
    UpdateQualitySettingsCommand,
    UpdatePerformanceMetricsCommand,
    CleanupOldVersionsCommand
)

# Import all queries
from app.application.queries.preview_queries import (
    GetPreviewVersionByIdQuery,
    GetPreviewVersionsByRequestQuery,
    GetVersionTreeQuery,
    GetFinalVersionsQuery,
    GetPreviewInteractionByIdQuery,
    GetInteractionsByVersionQuery,
    GetPendingInteractionsQuery,
    GetInteractionStatisticsQuery,
    GetQualitySettingsByUserQuery,
    GetQualityRecommendationsQuery,
    GetStorageUsageQuery,
    GetVersionPerformanceStatsQuery,
    GetFeedbackHeatmapQuery
)

# Import repository interface
from app.domain.manga.repositories.preview_repository import PreviewRepository

logger = logging.getLogger(__name__)


class HandlerRegistrationService:
    """
    Service for registering CQRS handlers with Command and Query buses.
    
    Provides centralized configuration and dependency injection for all
    command and query handlers in the preview system.
    """
    
    def __init__(
        self,
        command_bus: CommandBus,
        query_bus: QueryBus,
        preview_repository: PreviewRepository
    ):
        self.command_bus = command_bus
        self.query_bus = query_bus
        self.preview_repository = preview_repository
        self._registered = False
    
    def register_all_handlers(self) -> None:
        """
        Register all command and query handlers with their respective buses.
        
        This method should be called during application startup to configure
        the CQRS infrastructure with all necessary handlers.
        """
        if self._registered:
            logger.warning("Handlers have already been registered")
            return
        
        logger.info("Starting handler registration process")
        
        try:
            self._register_command_handlers()
            self._register_query_handlers()
            self._registered = True
            
            logger.info("Successfully registered all CQRS handlers")
            
            # Log registration summary
            command_handlers = self.command_bus.get_registered_handlers()
            query_handlers = self.query_bus.get_registered_handlers()
            
            logger.info(
                f"Registration summary: {len(command_handlers)} command handlers, "
                f"{len(query_handlers)} query handlers registered",
                extra={
                    "command_handlers_count": len(command_handlers),
                    "query_handlers_count": len(query_handlers),
                    "command_handlers": list(command_handlers.keys()),
                    "query_handlers": list(query_handlers.keys())
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to register handlers: {str(e)}",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def _register_command_handlers(self) -> None:
        """Register all command handlers with the command bus."""
        logger.debug("Registering command handlers")
        
        # Preview Version Command Handlers
        self.command_bus.register_handler(
            CreatePreviewVersionCommand,
            CreatePreviewVersionHandler(self.preview_repository)
        )
        
        self.command_bus.register_handler(
            UpdatePreviewVersionCommand,
            UpdatePreviewVersionHandler(self.preview_repository)
        )
        
        self.command_bus.register_handler(
            SetFinalVersionCommand,
            SetFinalVersionHandler(self.preview_repository)
        )
        
        self.command_bus.register_handler(
            IncrementViewCountCommand,
            IncrementViewCountHandler(self.preview_repository)
        )
        
        self.command_bus.register_handler(
            DeletePreviewVersionCommand,
            DeletePreviewVersionHandler(self.preview_repository)
        )
        
        # Preview Interaction Command Handlers
        self.command_bus.register_handler(
            CreatePreviewInteractionCommand,
            CreatePreviewInteractionHandler(self.preview_repository)
        )
        
        self.command_bus.register_handler(
            UpdateInteractionStatusCommand,
            UpdateInteractionStatusHandler(self.preview_repository)
        )
        
        self.command_bus.register_handler(
            ApplyInteractionsToVersionCommand,
            ApplyInteractionsToVersionHandler(self.preview_repository)
        )
        
        # Preview Quality Settings Command Handlers
        self.command_bus.register_handler(
            CreateQualitySettingsCommand,
            CreateQualitySettingsHandler(self.preview_repository)
        )
        
        self.command_bus.register_handler(
            UpdateQualitySettingsCommand,
            UpdateQualitySettingsHandler(self.preview_repository)
        )
        
        self.command_bus.register_handler(
            UpdatePerformanceMetricsCommand,
            UpdatePerformanceMetricsHandler(self.preview_repository)
        )
        
        # Cleanup Command Handlers
        self.command_bus.register_handler(
            CleanupOldVersionsCommand,
            CleanupOldVersionsHandler(self.preview_repository)
        )
        
        logger.debug("Successfully registered all command handlers")
    
    def _register_query_handlers(self) -> None:
        """Register all query handlers with the query bus."""
        logger.debug("Registering query handlers")
        
        # Preview Version Query Handlers
        self.query_bus.register_handler(
            GetPreviewVersionByIdQuery,
            GetPreviewVersionByIdHandler(self.preview_repository)
        )
        
        self.query_bus.register_handler(
            GetPreviewVersionsByRequestQuery,
            GetPreviewVersionsByRequestHandler(self.preview_repository)
        )
        
        self.query_bus.register_handler(
            GetVersionTreeQuery,
            GetVersionTreeHandler(self.preview_repository)
        )
        
        self.query_bus.register_handler(
            GetFinalVersionsQuery,
            GetFinalVersionsHandler(self.preview_repository)
        )
        
        # Preview Interaction Query Handlers
        self.query_bus.register_handler(
            GetPreviewInteractionByIdQuery,
            GetPreviewInteractionByIdHandler(self.preview_repository)
        )
        
        self.query_bus.register_handler(
            GetInteractionsByVersionQuery,
            GetInteractionsByVersionHandler(self.preview_repository)
        )
        
        self.query_bus.register_handler(
            GetPendingInteractionsQuery,
            GetPendingInteractionsHandler(self.preview_repository)
        )
        
        self.query_bus.register_handler(
            GetInteractionStatisticsQuery,
            GetInteractionStatisticsHandler(self.preview_repository)
        )
        
        # Preview Quality Settings Query Handlers
        self.query_bus.register_handler(
            GetQualitySettingsByUserQuery,
            GetQualitySettingsByUserHandler(self.preview_repository)
        )
        
        self.query_bus.register_handler(
            GetQualityRecommendationsQuery,
            GetQualityRecommendationsHandler(self.preview_repository)
        )
        
        # Analytics and Reporting Query Handlers
        self.query_bus.register_handler(
            GetStorageUsageQuery,
            GetStorageUsageHandler(self.preview_repository)
        )
        
        self.query_bus.register_handler(
            GetVersionPerformanceStatsQuery,
            GetVersionPerformanceStatsHandler(self.preview_repository)
        )
        
        self.query_bus.register_handler(
            GetFeedbackHeatmapQuery,
            GetFeedbackHeatmapHandler(self.preview_repository)
        )
        
        logger.debug("Successfully registered all query handlers")
    
    def get_registration_info(self) -> Dict[str, Any]:
        """
        Get information about registered handlers.
        
        Returns:
            Dictionary containing registration information and statistics.
        """
        command_handlers = self.command_bus.get_registered_handlers()
        query_handlers = self.query_bus.get_registered_handlers()
        
        command_middleware = self.command_bus.get_middleware_info()
        query_middleware = self.query_bus.get_middleware_info()
        
        return {
            "is_registered": self._registered,
            "command_handlers": {
                "count": len(command_handlers),
                "handlers": command_handlers
            },
            "query_handlers": {
                "count": len(query_handlers),
                "handlers": query_handlers
            },
            "command_middleware": command_middleware,
            "query_middleware": query_middleware,
            "cache_stats": {
                "command_cache": self.command_bus.get_cache_stats(),
                "query_cache": self.query_bus.get_cache_stats()
            },
            "performance_stats": {
                "command_performance": self.command_bus.get_performance_stats(),
                "query_performance": self.query_bus.get_performance_stats()
            }
        }
    
    def is_registered(self) -> bool:
        """Check if handlers have been registered."""
        return self._registered
    
    def clear_cache(self) -> None:
        """Clear all handler caches."""
        logger.info("Clearing CQRS handler caches")
        
        self.command_bus.invalidate_cache()
        self.query_bus.invalidate_cache()
        
        logger.info("Successfully cleared CQRS handler caches")


def create_handler_registration_service(
    command_bus: CommandBus,
    query_bus: QueryBus,
    preview_repository: PreviewRepository
) -> HandlerRegistrationService:
    """
    Factory function to create and configure handler registration service.
    
    Args:
        command_bus: Command bus instance
        query_bus: Query bus instance
        preview_repository: Preview repository instance
    
    Returns:
        Configured handler registration service
    """
    service = HandlerRegistrationService(
        command_bus=command_bus,
        query_bus=query_bus,
        preview_repository=preview_repository
    )
    
    logger.info("Created handler registration service")
    
    return service


def register_preview_system_handlers(
    command_bus: CommandBus,
    query_bus: QueryBus,
    preview_repository: PreviewRepository
) -> HandlerRegistrationService:
    """
    Convenience function to create service and register all handlers.
    
    This function combines service creation and handler registration
    into a single call for simplified application startup.
    
    Args:
        command_bus: Command bus instance
        query_bus: Query bus instance
        preview_repository: Preview repository instance
    
    Returns:
        Configured and registered handler registration service
    
    Raises:
        Exception: If handler registration fails
    """
    logger.info("Initializing preview system CQRS handlers")
    
    service = create_handler_registration_service(
        command_bus,
        query_bus,
        preview_repository
    )
    
    service.register_all_handlers()
    
    logger.info("Successfully initialized preview system CQRS handlers")
    
    return service