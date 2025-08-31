"""
Preview System Command Handlers - Phase 2 Preview System Implementation.

This module contains command handlers for preview system operations
including version management, interactions, and quality settings.

Implements Command Handler pattern with business logic orchestration.
"""

import logging
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime

from app.application.handlers.base_handler import BaseCommandHandler
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
from app.application.messaging.command_result import CommandResult
from app.domain.manga.repositories.preview_repository import (
    PreviewRepository,
    PreviewVersionNotFoundException,
    PreviewInteractionNotFoundException,
    PreviewQualitySettingsNotFoundException
)
from app.domain.common.preview_entities import (
    PreviewVersionEntity,
    PreviewInteractionEntity,
    PreviewQualitySettingsEntity
)

logger = logging.getLogger(__name__)


# ===== Preview Version Command Handlers =====

class CreatePreviewVersionHandler(BaseCommandHandler[CreatePreviewVersionCommand, Dict[str, Any]]):
    """Handler for creating new preview versions."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: CreatePreviewVersionCommand) -> CommandResult[Dict[str, Any]]:
        """Handle preview version creation."""
        try:
            logger.info(
                f"Creating preview version for request {command.request_id}, phase {command.phase}",
                extra={
                    "command": "CreatePreviewVersion",
                    "request_id": str(command.request_id),
                    "phase": command.phase,
                    "parent_version_id": str(command.parent_version_id) if command.parent_version_id else None
                }
            )
            
            # Create preview version entity
            version_entity = PreviewVersionEntity(
                version_id=uuid4(),
                request_id=command.request_id,
                parent_version_id=command.parent_version_id,
                phase=command.phase,
                version_data=command.version_data,
                change_description=command.change_description,
                quality_level=command.quality_level,
                branch_name=command.branch_name,
                asset_urls=command.asset_urls,
                thumbnail_url=command.thumbnail_url,
                generation_time_ms=command.generation_time_ms,
                file_size_bytes=command.file_size_bytes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to repository
            created_version = await self.preview_repository.create_preview_version(version_entity)
            
            logger.info(
                f"Successfully created preview version: {created_version.version_id}",
                extra={
                    "command": "CreatePreviewVersion",
                    "version_id": str(created_version.version_id),
                    "request_id": str(created_version.request_id),
                    "phase": created_version.phase
                }
            )
            
            return CommandResult.success({
                "version_id": str(created_version.version_id),
                "request_id": str(created_version.request_id),
                "phase": created_version.phase,
                "quality_level": created_version.quality_level,
                "is_active": created_version.is_active,
                "created_at": created_version.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error(
                f"Failed to create preview version: {str(e)}",
                extra={
                    "command": "CreatePreviewVersion",
                    "request_id": str(command.request_id),
                    "phase": command.phase,
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="preview_version_creation_failed",
                error=f"Failed to create preview version: {str(e)}"
            )


class UpdatePreviewVersionHandler(BaseCommandHandler[UpdatePreviewVersionCommand, Dict[str, Any]]):
    """Handler for updating preview versions."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: UpdatePreviewVersionCommand) -> CommandResult[Dict[str, Any]]:
        """Handle preview version update."""
        try:
            logger.info(
                f"Updating preview version: {command.version_id}",
                extra={
                    "command": "UpdatePreviewVersion",
                    "version_id": str(command.version_id)
                }
            )
            
            # Get existing version
            existing_version = await self.preview_repository.find_preview_version_by_id(command.version_id)
            if not existing_version:
                return CommandResult.failure(
                    error_code="version_not_found",
                    error=f"Preview version not found: {command.version_id}"
                )
            
            # Update fields that are provided
            if command.version_data is not None:
                existing_version.version_data = command.version_data
            
            if command.change_description is not None:
                existing_version.change_description = command.change_description
            
            if command.quality_level is not None:
                existing_version.quality_level = command.quality_level
            
            if command.quality_score is not None:
                existing_version.quality_score = command.quality_score
            
            if command.is_active is not None:
                existing_version.is_active = command.is_active
            
            if command.is_final is not None:
                existing_version.is_final = command.is_final
            
            if command.branch_name is not None:
                existing_version.branch_name = command.branch_name
            
            if command.merge_status is not None:
                existing_version.merge_status = command.merge_status
            
            if command.asset_urls is not None:
                existing_version.asset_urls = command.asset_urls
            
            if command.thumbnail_url is not None:
                existing_version.thumbnail_url = command.thumbnail_url
            
            if command.generation_time_ms is not None:
                existing_version.generation_time_ms = command.generation_time_ms
            
            if command.file_size_bytes is not None:
                existing_version.file_size_bytes = command.file_size_bytes
            
            existing_version.updated_at = datetime.utcnow()
            
            # Save updated version
            updated_version = await self.preview_repository.update_preview_version(existing_version)
            
            logger.info(
                f"Successfully updated preview version: {updated_version.version_id}",
                extra={
                    "command": "UpdatePreviewVersion",
                    "version_id": str(updated_version.version_id)
                }
            )
            
            return CommandResult.success({
                "version_id": str(updated_version.version_id),
                "request_id": str(updated_version.request_id),
                "phase": updated_version.phase,
                "quality_level": updated_version.quality_level,
                "is_active": updated_version.is_active,
                "is_final": updated_version.is_final,
                "updated_at": updated_version.updated_at.isoformat()
            })
            
        except PreviewVersionNotFoundException as e:
            return CommandResult.failure(
                error_code="version_not_found",
                error=str(e)
            )
        except Exception as e:
            logger.error(
                f"Failed to update preview version: {str(e)}",
                extra={
                    "command": "UpdatePreviewVersion",
                    "version_id": str(command.version_id),
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="preview_version_update_failed",
                error=f"Failed to update preview version: {str(e)}"
            )


class SetFinalVersionHandler(BaseCommandHandler[SetFinalVersionCommand, Dict[str, Any]]):
    """Handler for setting a version as final."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: SetFinalVersionCommand) -> CommandResult[Dict[str, Any]]:
        """Handle setting version as final."""
        try:
            logger.info(
                f"Setting final version: {command.version_id}",
                extra={
                    "command": "SetFinalVersion",
                    "version_id": str(command.version_id)
                }
            )
            
            # Set as final version (repository handles unsetting others)
            final_version = await self.preview_repository.set_final_version(command.version_id)
            
            logger.info(
                f"Successfully set final version: {final_version.version_id}",
                extra={
                    "command": "SetFinalVersion",
                    "version_id": str(final_version.version_id),
                    "request_id": str(final_version.request_id),
                    "phase": final_version.phase
                }
            )
            
            return CommandResult.success({
                "version_id": str(final_version.version_id),
                "request_id": str(final_version.request_id),
                "phase": final_version.phase,
                "is_final": final_version.is_final,
                "is_active": final_version.is_active,
                "updated_at": final_version.updated_at.isoformat()
            })
            
        except PreviewVersionNotFoundException as e:
            return CommandResult.failure(
                error_code="version_not_found",
                error=str(e)
            )
        except Exception as e:
            logger.error(
                f"Failed to set final version: {str(e)}",
                extra={
                    "command": "SetFinalVersion",
                    "version_id": str(command.version_id),
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="set_final_version_failed",
                error=f"Failed to set final version: {str(e)}"
            )


class IncrementViewCountHandler(BaseCommandHandler[IncrementViewCountCommand, Dict[str, Any]]):
    """Handler for incrementing view count."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: IncrementViewCountCommand) -> CommandResult[Dict[str, Any]]:
        """Handle view count increment."""
        try:
            logger.debug(
                f"Incrementing view count for version: {command.version_id}",
                extra={
                    "command": "IncrementViewCount",
                    "version_id": str(command.version_id)
                }
            )
            
            # Increment view count
            new_count = await self.preview_repository.increment_view_count(command.version_id)
            
            logger.debug(
                f"Successfully incremented view count: {command.version_id} -> {new_count}",
                extra={
                    "command": "IncrementViewCount",
                    "version_id": str(command.version_id),
                    "new_count": new_count
                }
            )
            
            return CommandResult.success({
                "version_id": str(command.version_id),
                "new_view_count": new_count
            })
            
        except PreviewVersionNotFoundException as e:
            return CommandResult.failure(
                error_code="version_not_found",
                error=str(e)
            )
        except Exception as e:
            logger.error(
                f"Failed to increment view count: {str(e)}",
                extra={
                    "command": "IncrementViewCount",
                    "version_id": str(command.version_id),
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="increment_view_count_failed",
                error=f"Failed to increment view count: {str(e)}"
            )


class DeletePreviewVersionHandler(BaseCommandHandler[DeletePreviewVersionCommand, Dict[str, Any]]):
    """Handler for deleting preview versions."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: DeletePreviewVersionCommand) -> CommandResult[Dict[str, Any]]:
        """Handle preview version deletion."""
        try:
            logger.info(
                f"Deleting preview version: {command.version_id}",
                extra={
                    "command": "DeletePreviewVersion",
                    "version_id": str(command.version_id)
                }
            )
            
            # Delete version and all its interactions
            deleted = await self.preview_repository.delete_preview_version(command.version_id)
            
            if deleted:
                logger.info(
                    f"Successfully deleted preview version: {command.version_id}",
                    extra={
                        "command": "DeletePreviewVersion",
                        "version_id": str(command.version_id)
                    }
                )
                
                return CommandResult.success({
                    "version_id": str(command.version_id),
                    "deleted": True
                })
            else:
                return CommandResult.failure(
                    error_code="version_not_found",
                    error=f"Preview version not found: {command.version_id}"
                )
            
        except Exception as e:
            logger.error(
                f"Failed to delete preview version: {str(e)}",
                extra={
                    "command": "DeletePreviewVersion",
                    "version_id": str(command.version_id),
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="delete_preview_version_failed",
                error=f"Failed to delete preview version: {str(e)}"
            )


# ===== Preview Interaction Command Handlers =====

class CreatePreviewInteractionHandler(BaseCommandHandler[CreatePreviewInteractionCommand, Dict[str, Any]]):
    """Handler for creating preview interactions."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: CreatePreviewInteractionCommand) -> CommandResult[Dict[str, Any]]:
        """Handle preview interaction creation."""
        try:
            logger.info(
                f"Creating preview interaction for version {command.version_id}",
                extra={
                    "command": "CreatePreviewInteraction",
                    "version_id": str(command.version_id),
                    "user_id": str(command.user_id),
                    "element_id": command.element_id,
                    "change_type": command.change_type
                }
            )
            
            # Create interaction entity
            interaction_entity = PreviewInteractionEntity(
                interaction_id=uuid4(),
                version_id=command.version_id,
                user_id=command.user_id,
                element_id=command.element_id,
                element_type=command.element_type,
                change_type=command.change_type,
                change_data=command.change_data,
                change_description=command.change_description,
                confidence_score=command.confidence_score,
                interaction_type=command.interaction_type,
                session_id=command.session_id,
                position_x=command.position_x,
                position_y=command.position_y,
                position_data=command.position_data,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to repository
            created_interaction = await self.preview_repository.create_preview_interaction(interaction_entity)
            
            logger.info(
                f"Successfully created preview interaction: {created_interaction.interaction_id}",
                extra={
                    "command": "CreatePreviewInteraction",
                    "interaction_id": str(created_interaction.interaction_id),
                    "version_id": str(created_interaction.version_id),
                    "change_type": created_interaction.change_type
                }
            )
            
            return CommandResult.success({
                "interaction_id": str(created_interaction.interaction_id),
                "version_id": str(created_interaction.version_id),
                "user_id": str(created_interaction.user_id),
                "element_id": created_interaction.element_id,
                "change_type": created_interaction.change_type,
                "interaction_type": created_interaction.interaction_type,
                "status": created_interaction.status,
                "created_at": created_interaction.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error(
                f"Failed to create preview interaction: {str(e)}",
                extra={
                    "command": "CreatePreviewInteraction",
                    "version_id": str(command.version_id),
                    "user_id": str(command.user_id),
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="preview_interaction_creation_failed",
                error=f"Failed to create preview interaction: {str(e)}"
            )


class UpdateInteractionStatusHandler(BaseCommandHandler[UpdateInteractionStatusCommand, Dict[str, Any]]):
    """Handler for updating interaction status."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: UpdateInteractionStatusCommand) -> CommandResult[Dict[str, Any]]:
        """Handle interaction status update."""
        try:
            logger.info(
                f"Updating interaction status: {command.interaction_id} -> {command.status}",
                extra={
                    "command": "UpdateInteractionStatus",
                    "interaction_id": str(command.interaction_id),
                    "status": command.status,
                    "reviewed_by": str(command.reviewed_by) if command.reviewed_by else None
                }
            )
            
            # Update interaction status
            updated_interaction = await self.preview_repository.update_interaction_status(
                command.interaction_id,
                command.status,
                command.reviewed_by
            )
            
            logger.info(
                f"Successfully updated interaction status: {updated_interaction.interaction_id}",
                extra={
                    "command": "UpdateInteractionStatus",
                    "interaction_id": str(updated_interaction.interaction_id),
                    "status": updated_interaction.status,
                    "reviewed_by": str(updated_interaction.reviewed_by) if updated_interaction.reviewed_by else None
                }
            )
            
            return CommandResult.success({
                "interaction_id": str(updated_interaction.interaction_id),
                "version_id": str(updated_interaction.version_id),
                "status": updated_interaction.status,
                "reviewed_by": str(updated_interaction.reviewed_by) if updated_interaction.reviewed_by else None,
                "reviewed_at": updated_interaction.reviewed_at.isoformat() if updated_interaction.reviewed_at else None,
                "applied_at": updated_interaction.applied_at.isoformat() if updated_interaction.applied_at else None,
                "updated_at": updated_interaction.updated_at.isoformat()
            })
            
        except PreviewInteractionNotFoundException as e:
            return CommandResult.failure(
                error_code="interaction_not_found",
                error=str(e)
            )
        except Exception as e:
            logger.error(
                f"Failed to update interaction status: {str(e)}",
                extra={
                    "command": "UpdateInteractionStatus",
                    "interaction_id": str(command.interaction_id),
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="update_interaction_status_failed",
                error=f"Failed to update interaction status: {str(e)}"
            )


class ApplyInteractionsToVersionHandler(BaseCommandHandler[ApplyInteractionsToVersionCommand, Dict[str, Any]]):
    """Handler for applying interactions to create new version."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: ApplyInteractionsToVersionCommand) -> CommandResult[Dict[str, Any]]:
        """Handle applying interactions to version."""
        try:
            logger.info(
                f"Applying {len(command.interaction_ids)} interactions to version {command.version_id}",
                extra={
                    "command": "ApplyInteractionsToVersion",
                    "version_id": str(command.version_id),
                    "interaction_count": len(command.interaction_ids)
                }
            )
            
            # Apply interactions to create new version
            # Note: This is a complex operation that involves business logic
            # to merge interaction changes into version data
            new_version = await self.preview_repository.apply_interactions_to_version(
                command.version_id,
                command.interaction_ids
            )
            
            logger.info(
                f"Successfully applied interactions to create new version",
                extra={
                    "command": "ApplyInteractionsToVersion",
                    "original_version_id": str(command.version_id),
                    "new_version_id": str(new_version.version_id),
                    "applied_interactions": len(command.interaction_ids)
                }
            )
            
            return CommandResult.success({
                "original_version_id": str(command.version_id),
                "new_version_id": str(new_version.version_id),
                "applied_interactions": len(command.interaction_ids),
                "new_version_data": new_version.version_data,
                "created_at": new_version.created_at.isoformat() if new_version.created_at else None
            })
            
        except PreviewVersionNotFoundException as e:
            return CommandResult.failure(
                error_code="version_not_found",
                error=str(e)
            )
        except PreviewInteractionNotFoundException as e:
            return CommandResult.failure(
                error_code="interaction_not_found",
                error=str(e)
            )
        except Exception as e:
            logger.error(
                f"Failed to apply interactions to version: {str(e)}",
                extra={
                    "command": "ApplyInteractionsToVersion",
                    "version_id": str(command.version_id),
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="apply_interactions_failed",
                error=f"Failed to apply interactions: {str(e)}"
            )


# ===== Preview Quality Settings Command Handlers =====

class CreateQualitySettingsHandler(BaseCommandHandler[CreateQualitySettingsCommand, Dict[str, Any]]):
    """Handler for creating quality settings."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: CreateQualitySettingsCommand) -> CommandResult[Dict[str, Any]]:
        """Handle quality settings creation."""
        try:
            logger.info(
                f"Creating quality settings for user: {command.user_id}",
                extra={
                    "command": "CreateQualitySettings",
                    "user_id": str(command.user_id),
                    "preferred_quality": command.preferred_quality,
                    "device_capability": command.device_capability
                }
            )
            
            # Create quality settings entity
            settings_entity = PreviewQualitySettingsEntity(
                setting_id=uuid4(),
                user_id=command.user_id,
                device_capability=command.device_capability,
                bandwidth_estimate=command.bandwidth_estimate,
                preferred_quality=command.preferred_quality,
                max_quality=command.max_quality,
                auto_adjust_quality=command.auto_adjust_quality,
                max_generation_time_seconds=command.max_generation_time_seconds,
                preferred_resolution=command.preferred_resolution,
                enable_caching=command.enable_caching,
                preview_format_preference=command.preview_format_preference,
                enable_progressive_loading=command.enable_progressive_loading,
                enable_thumbnails=command.enable_thumbnails,
                ai_enhancement_level=command.ai_enhancement_level,
                enable_smart_cropping=command.enable_smart_cropping,
                enable_color_optimization=command.enable_color_optimization,
                enable_realtime_preview=command.enable_realtime_preview,
                feedback_sensitivity=command.feedback_sensitivity,
                auto_apply_suggestions=command.auto_apply_suggestions,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to repository
            created_settings = await self.preview_repository.create_quality_settings(settings_entity)
            
            logger.info(
                f"Successfully created quality settings: {created_settings.setting_id}",
                extra={
                    "command": "CreateQualitySettings",
                    "setting_id": str(created_settings.setting_id),
                    "user_id": str(created_settings.user_id)
                }
            )
            
            return CommandResult.success({
                "setting_id": str(created_settings.setting_id),
                "user_id": str(created_settings.user_id),
                "preferred_quality": created_settings.preferred_quality,
                "device_capability": created_settings.device_capability,
                "auto_adjust_quality": created_settings.auto_adjust_quality,
                "created_at": created_settings.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error(
                f"Failed to create quality settings: {str(e)}",
                extra={
                    "command": "CreateQualitySettings",
                    "user_id": str(command.user_id),
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="quality_settings_creation_failed",
                error=f"Failed to create quality settings: {str(e)}"
            )


class UpdateQualitySettingsHandler(BaseCommandHandler[UpdateQualitySettingsCommand, Dict[str, Any]]):
    """Handler for updating quality settings."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: UpdateQualitySettingsCommand) -> CommandResult[Dict[str, Any]]:
        """Handle quality settings update."""
        try:
            logger.info(
                f"Updating quality settings for user: {command.user_id}",
                extra={
                    "command": "UpdateQualitySettings",
                    "user_id": str(command.user_id)
                }
            )
            
            # Get existing settings
            existing_settings = await self.preview_repository.find_quality_settings_by_user(command.user_id)
            if not existing_settings:
                return CommandResult.failure(
                    error_code="settings_not_found",
                    error=f"Quality settings not found for user: {command.user_id}"
                )
            
            # Update fields that are provided
            if command.device_capability is not None:
                existing_settings.device_capability = command.device_capability
            
            if command.bandwidth_estimate is not None:
                existing_settings.bandwidth_estimate = command.bandwidth_estimate
            
            if command.preferred_quality is not None:
                existing_settings.preferred_quality = command.preferred_quality
            
            if command.max_quality is not None:
                existing_settings.max_quality = command.max_quality
            
            if command.auto_adjust_quality is not None:
                existing_settings.auto_adjust_quality = command.auto_adjust_quality
            
            if command.max_generation_time_seconds is not None:
                existing_settings.max_generation_time_seconds = command.max_generation_time_seconds
            
            if command.preferred_resolution is not None:
                existing_settings.preferred_resolution = command.preferred_resolution
            
            if command.enable_caching is not None:
                existing_settings.enable_caching = command.enable_caching
            
            if command.preview_format_preference is not None:
                existing_settings.preview_format_preference = command.preview_format_preference
            
            if command.enable_progressive_loading is not None:
                existing_settings.enable_progressive_loading = command.enable_progressive_loading
            
            if command.enable_thumbnails is not None:
                existing_settings.enable_thumbnails = command.enable_thumbnails
            
            if command.ai_enhancement_level is not None:
                existing_settings.ai_enhancement_level = command.ai_enhancement_level
            
            if command.enable_smart_cropping is not None:
                existing_settings.enable_smart_cropping = command.enable_smart_cropping
            
            if command.enable_color_optimization is not None:
                existing_settings.enable_color_optimization = command.enable_color_optimization
            
            if command.enable_realtime_preview is not None:
                existing_settings.enable_realtime_preview = command.enable_realtime_preview
            
            if command.feedback_sensitivity is not None:
                existing_settings.feedback_sensitivity = command.feedback_sensitivity
            
            if command.auto_apply_suggestions is not None:
                existing_settings.auto_apply_suggestions = command.auto_apply_suggestions
            
            existing_settings.updated_at = datetime.utcnow()
            
            # Save updated settings
            updated_settings = await self.preview_repository.update_quality_settings(existing_settings)
            
            logger.info(
                f"Successfully updated quality settings for user: {command.user_id}",
                extra={
                    "command": "UpdateQualitySettings",
                    "user_id": str(command.user_id),
                    "setting_id": str(updated_settings.setting_id)
                }
            )
            
            return CommandResult.success({
                "setting_id": str(updated_settings.setting_id),
                "user_id": str(updated_settings.user_id),
                "preferred_quality": updated_settings.preferred_quality,
                "device_capability": updated_settings.device_capability,
                "auto_adjust_quality": updated_settings.auto_adjust_quality,
                "updated_at": updated_settings.updated_at.isoformat()
            })
            
        except PreviewQualitySettingsNotFoundException as e:
            return CommandResult.failure(
                error_code="settings_not_found",
                error=str(e)
            )
        except Exception as e:
            logger.error(
                f"Failed to update quality settings: {str(e)}",
                extra={
                    "command": "UpdateQualitySettings",
                    "user_id": str(command.user_id),
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="quality_settings_update_failed",
                error=f"Failed to update quality settings: {str(e)}"
            )


class UpdatePerformanceMetricsHandler(BaseCommandHandler[UpdatePerformanceMetricsCommand, Dict[str, Any]]):
    """Handler for updating performance metrics."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: UpdatePerformanceMetricsCommand) -> CommandResult[Dict[str, Any]]:
        """Handle performance metrics update."""
        try:
            logger.info(
                f"Updating performance metrics for user: {command.user_id}",
                extra={
                    "command": "UpdatePerformanceMetrics",
                    "user_id": str(command.user_id),
                    "generation_time": command.generation_time
                }
            )
            
            # Update performance metrics
            updated_settings = await self.preview_repository.update_performance_metrics(
                command.user_id,
                command.generation_time,
                command.device_capability
            )
            
            logger.info(
                f"Successfully updated performance metrics for user: {command.user_id}",
                extra={
                    "command": "UpdatePerformanceMetrics",
                    "user_id": str(command.user_id),
                    "average_generation_time": updated_settings.average_generation_time
                }
            )
            
            return CommandResult.success({
                "user_id": str(updated_settings.user_id),
                "average_generation_time": updated_settings.average_generation_time,
                "device_capability": updated_settings.device_capability,
                "last_performance_update": updated_settings.last_performance_update.isoformat() if updated_settings.last_performance_update else None
            })
            
        except PreviewQualitySettingsNotFoundException as e:
            return CommandResult.failure(
                error_code="settings_not_found",
                error=str(e)
            )
        except Exception as e:
            logger.error(
                f"Failed to update performance metrics: {str(e)}",
                extra={
                    "command": "UpdatePerformanceMetrics",
                    "user_id": str(command.user_id),
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="performance_metrics_update_failed",
                error=f"Failed to update performance metrics: {str(e)}"
            )


# ===== Cleanup Command Handlers =====

class CleanupOldVersionsHandler(BaseCommandHandler[CleanupOldVersionsCommand, Dict[str, Any]]):
    """Handler for cleaning up old versions."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, command: CleanupOldVersionsCommand) -> CommandResult[Dict[str, Any]]:
        """Handle old versions cleanup."""
        try:
            logger.info(
                f"Cleaning up old versions for request: {command.request_id}",
                extra={
                    "command": "CleanupOldVersions",
                    "request_id": str(command.request_id),
                    "keep_final": command.keep_final,
                    "keep_latest_per_branch": command.keep_latest_per_branch
                }
            )
            
            # Clean up old versions
            deleted_count = await self.preview_repository.cleanup_old_versions(
                command.request_id,
                command.keep_final,
                command.keep_latest_per_branch
            )
            
            logger.info(
                f"Successfully cleaned up {deleted_count} old versions",
                extra={
                    "command": "CleanupOldVersions",
                    "request_id": str(command.request_id),
                    "deleted_count": deleted_count
                }
            )
            
            return CommandResult.success({
                "request_id": str(command.request_id),
                "deleted_versions_count": deleted_count,
                "keep_final": command.keep_final,
                "keep_latest_per_branch": command.keep_latest_per_branch
            })
            
        except Exception as e:
            logger.error(
                f"Failed to cleanup old versions: {str(e)}",
                extra={
                    "command": "CleanupOldVersions",
                    "request_id": str(command.request_id),
                    "error": str(e)
                }
            )
            return CommandResult.failure(
                error_code="cleanup_old_versions_failed",
                error=f"Failed to cleanup old versions: {str(e)}"
            )