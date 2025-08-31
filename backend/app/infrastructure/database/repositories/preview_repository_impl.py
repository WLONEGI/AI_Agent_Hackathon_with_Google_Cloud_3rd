"""
SQLAlchemy implementation of Preview Repository - Phase 2 Preview System Implementation.

This module implements the concrete repository for preview system operations
using SQLAlchemy ORM with PostgreSQL database.

Complies with 06.データベース設計書.md specification.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.domain.manga.repositories.preview_repository import (
    PreviewRepository,
    PreviewRepositoryException,
    PreviewVersionNotFoundException,
    PreviewInteractionNotFoundException,
    PreviewQualitySettingsNotFoundException
)
from app.domain.common.preview_entities import (
    PreviewVersionEntity,
    PreviewInteractionEntity,
    PreviewQualitySettingsEntity
)
from app.infrastructure.database.models.preview_versions_model import (
    PreviewVersionModel,
    PreviewInteractionModel,
    PreviewQualitySettingsModel
)

logger = logging.getLogger(__name__)


class PreviewRepositoryImpl(PreviewRepository):
    """
    SQLAlchemy implementation of preview repository.
    
    Provides concrete implementation for all preview system operations
    using SQLAlchemy ORM with async database operations.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== Preview Version Operations =====
    
    async def create_preview_version(self, version: PreviewVersionEntity) -> PreviewVersionEntity:
        """Create a new preview version."""
        try:
            model = PreviewVersionModel(
                version_id=str(version.version_id),
                request_id=str(version.request_id),
                parent_version_id=str(version.parent_version_id) if version.parent_version_id else None,
                phase=version.phase,
                version_data=version.version_data,
                change_description=version.change_description,
                quality_level=version.quality_level,
                quality_score=version.quality_score,
                is_active=version.is_active,
                is_final=version.is_final,
                branch_name=version.branch_name,
                merge_status=version.merge_status,
                asset_urls=version.asset_urls,
                thumbnail_url=version.thumbnail_url,
                view_count=version.view_count,
                feedback_count=version.feedback_count,
                generation_time_ms=version.generation_time_ms,
                file_size_bytes=version.file_size_bytes
            )
            
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            
            logger.info(
                f"Created preview version: {model.version_id}",
                extra={
                    "version_id": model.version_id,
                    "request_id": model.request_id,
                    "phase": model.phase
                }
            )
            
            return self._model_to_entity(model)
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Preview version creation failed - integrity error: {str(e)}")
            raise PreviewRepositoryException(f"Failed to create preview version: {str(e)}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Preview version creation failed: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def find_preview_version_by_id(self, version_id: UUID) -> Optional[PreviewVersionEntity]:
        """Find preview version by ID."""
        try:
            stmt = select(PreviewVersionModel).where(
                PreviewVersionModel.version_id == str(version_id)
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return self._model_to_entity(model)
            return None
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to find preview version by ID: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def find_preview_versions_by_request(
        self, 
        request_id: UUID, 
        phase: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[PreviewVersionEntity]:
        """Find preview versions by generation request."""
        try:
            stmt = select(PreviewVersionModel).where(
                PreviewVersionModel.request_id == str(request_id)
            )
            
            if phase is not None:
                stmt = stmt.where(PreviewVersionModel.phase == phase)
            
            if is_active is not None:
                stmt = stmt.where(PreviewVersionModel.is_active == is_active)
            
            # Order by created_at for consistent results
            stmt = stmt.order_by(desc(PreviewVersionModel.created_at))
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to find preview versions by request: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def find_version_tree(
        self, 
        request_id: UUID, 
        phase: int
    ) -> List[PreviewVersionEntity]:
        """Find complete version tree for a request and phase."""
        try:
            # Build hierarchical tree query
            stmt = select(PreviewVersionModel).where(
                and_(
                    PreviewVersionModel.request_id == str(request_id),
                    PreviewVersionModel.phase == phase
                )
            ).order_by(
                asc(PreviewVersionModel.created_at)
            )
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            # Sort by tree hierarchy (parent -> children)
            sorted_models = self._sort_version_tree(models)
            
            return [self._model_to_entity(model) for model in sorted_models]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to find version tree: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def find_final_versions(self, request_id: UUID) -> List[PreviewVersionEntity]:
        """Find all final versions for a generation request."""
        try:
            stmt = select(PreviewVersionModel).where(
                and_(
                    PreviewVersionModel.request_id == str(request_id),
                    PreviewVersionModel.is_final == True
                )
            ).order_by(asc(PreviewVersionModel.phase))
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to find final versions: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def update_preview_version(self, version: PreviewVersionEntity) -> PreviewVersionEntity:
        """Update preview version."""
        try:
            stmt = update(PreviewVersionModel).where(
                PreviewVersionModel.version_id == str(version.version_id)
            ).values(
                version_data=version.version_data,
                change_description=version.change_description,
                quality_level=version.quality_level,
                quality_score=version.quality_score,
                is_active=version.is_active,
                is_final=version.is_final,
                branch_name=version.branch_name,
                merge_status=version.merge_status,
                asset_urls=version.asset_urls,
                thumbnail_url=version.thumbnail_url,
                view_count=version.view_count,
                feedback_count=version.feedback_count,
                generation_time_ms=version.generation_time_ms,
                file_size_bytes=version.file_size_bytes,
                updated_at=func.now()
            ).returning(PreviewVersionModel)
            
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                raise PreviewVersionNotFoundException(f"Preview version not found: {version.version_id}")
            
            await self.session.commit()
            
            logger.info(
                f"Updated preview version: {model.version_id}",
                extra={"version_id": model.version_id}
            )
            
            return self._model_to_entity(model)
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to update preview version: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def set_final_version(self, version_id: UUID) -> PreviewVersionEntity:
        """Set a version as final for its phase."""
        try:
            # First get the version to find its request_id and phase
            version_model = await self.session.get(PreviewVersionModel, str(version_id))
            if not version_model:
                raise PreviewVersionNotFoundException(f"Preview version not found: {version_id}")
            
            # Unset other final versions in the same phase
            await self.session.execute(
                update(PreviewVersionModel).where(
                    and_(
                        PreviewVersionModel.request_id == version_model.request_id,
                        PreviewVersionModel.phase == version_model.phase,
                        PreviewVersionModel.version_id != str(version_id)
                    )
                ).values(is_final=False, updated_at=func.now())
            )
            
            # Set this version as final
            stmt = update(PreviewVersionModel).where(
                PreviewVersionModel.version_id == str(version_id)
            ).values(
                is_final=True,
                is_active=True,
                updated_at=func.now()
            ).returning(PreviewVersionModel)
            
            result = await self.session.execute(stmt)
            model = result.scalar_one()
            
            await self.session.commit()
            
            logger.info(
                f"Set final version: {version_id}",
                extra={
                    "version_id": str(version_id),
                    "request_id": model.request_id,
                    "phase": model.phase
                }
            )
            
            return self._model_to_entity(model)
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to set final version: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def increment_view_count(self, version_id: UUID) -> int:
        """Increment view count for a preview version."""
        try:
            stmt = update(PreviewVersionModel).where(
                PreviewVersionModel.version_id == str(version_id)
            ).values(
                view_count=PreviewVersionModel.view_count + 1,
                updated_at=func.now()
            ).returning(PreviewVersionModel.view_count)
            
            result = await self.session.execute(stmt)
            new_count = result.scalar_one_or_none()
            
            if new_count is None:
                raise PreviewVersionNotFoundException(f"Preview version not found: {version_id}")
            
            await self.session.commit()
            
            return new_count
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to increment view count: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def delete_preview_version(self, version_id: UUID) -> bool:
        """Delete preview version and all its interactions."""
        try:
            # First delete all interactions for this version
            await self.session.execute(
                delete(PreviewInteractionModel).where(
                    PreviewInteractionModel.version_id == str(version_id)
                )
            )
            
            # Then delete the version itself
            stmt = delete(PreviewVersionModel).where(
                PreviewVersionModel.version_id == str(version_id)
            )
            
            result = await self.session.execute(stmt)
            deleted_count = result.rowcount
            
            await self.session.commit()
            
            if deleted_count > 0:
                logger.info(f"Deleted preview version: {version_id}")
                return True
            else:
                return False
                
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to delete preview version: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    # ===== Preview Interaction Operations =====
    
    async def create_preview_interaction(
        self, 
        interaction: PreviewInteractionEntity
    ) -> PreviewInteractionEntity:
        """Create a new preview interaction."""
        try:
            model = PreviewInteractionModel(
                interaction_id=str(interaction.interaction_id),
                version_id=str(interaction.version_id),
                user_id=str(interaction.user_id),
                element_id=interaction.element_id,
                element_type=interaction.element_type,
                change_type=interaction.change_type,
                change_data=interaction.change_data,
                change_description=interaction.change_description,
                confidence_score=interaction.confidence_score,
                interaction_type=interaction.interaction_type,
                session_id=str(interaction.session_id) if interaction.session_id else None,
                position_x=interaction.position_x,
                position_y=interaction.position_y,
                position_data=interaction.position_data,
                status=interaction.status,
                reviewed_by=str(interaction.reviewed_by) if interaction.reviewed_by else None,
                reviewed_at=interaction.reviewed_at,
                applied_at=interaction.applied_at,
                processing_time_ms=interaction.processing_time_ms
            )
            
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            
            # Update feedback count on version
            await self.session.execute(
                update(PreviewVersionModel).where(
                    PreviewVersionModel.version_id == str(interaction.version_id)
                ).values(
                    feedback_count=PreviewVersionModel.feedback_count + 1,
                    updated_at=func.now()
                )
            )
            await self.session.commit()
            
            logger.info(
                f"Created preview interaction: {model.interaction_id}",
                extra={
                    "interaction_id": model.interaction_id,
                    "version_id": model.version_id,
                    "change_type": model.change_type
                }
            )
            
            return self._interaction_model_to_entity(model)
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Preview interaction creation failed - integrity error: {str(e)}")
            raise PreviewRepositoryException(f"Failed to create preview interaction: {str(e)}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Preview interaction creation failed: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def find_preview_interaction_by_id(
        self, 
        interaction_id: UUID
    ) -> Optional[PreviewInteractionEntity]:
        """Find preview interaction by ID."""
        try:
            stmt = select(PreviewInteractionModel).where(
                PreviewInteractionModel.interaction_id == str(interaction_id)
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return self._interaction_model_to_entity(model)
            return None
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to find preview interaction by ID: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def find_interactions_by_version(
        self, 
        version_id: UUID,
        interaction_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[PreviewInteractionEntity]:
        """Find interactions by version."""
        try:
            stmt = select(PreviewInteractionModel).where(
                PreviewInteractionModel.version_id == str(version_id)
            )
            
            if interaction_type:
                stmt = stmt.where(PreviewInteractionModel.interaction_type == interaction_type)
            
            if status:
                stmt = stmt.where(PreviewInteractionModel.status == status)
            
            stmt = stmt.order_by(desc(PreviewInteractionModel.created_at))
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._interaction_model_to_entity(model) for model in models]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to find interactions by version: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def find_interactions_by_user(
        self, 
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PreviewInteractionEntity]:
        """Find interactions by user."""
        try:
            stmt = select(PreviewInteractionModel).where(
                PreviewInteractionModel.user_id == str(user_id)
            )
            
            if start_date:
                stmt = stmt.where(PreviewInteractionModel.created_at >= start_date)
            
            if end_date:
                stmt = stmt.where(PreviewInteractionModel.created_at <= end_date)
            
            stmt = stmt.order_by(desc(PreviewInteractionModel.created_at))
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._interaction_model_to_entity(model) for model in models]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to find interactions by user: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def find_pending_interactions(
        self, 
        version_id: Optional[UUID] = None
    ) -> List[PreviewInteractionEntity]:
        """Find pending interactions that need processing."""
        try:
            stmt = select(PreviewInteractionModel).where(
                PreviewInteractionModel.status == "pending"
            )
            
            if version_id:
                stmt = stmt.where(PreviewInteractionModel.version_id == str(version_id))
            
            stmt = stmt.order_by(asc(PreviewInteractionModel.created_at))
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._interaction_model_to_entity(model) for model in models]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to find pending interactions: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def update_interaction_status(
        self, 
        interaction_id: UUID, 
        status: str,
        reviewed_by: Optional[UUID] = None
    ) -> PreviewInteractionEntity:
        """Update interaction status."""
        try:
            values = {
                "status": status,
                "updated_at": func.now()
            }
            
            if reviewed_by:
                values["reviewed_by"] = str(reviewed_by)
                values["reviewed_at"] = func.now()
            
            if status == "applied":
                values["applied_at"] = func.now()
            
            stmt = update(PreviewInteractionModel).where(
                PreviewInteractionModel.interaction_id == str(interaction_id)
            ).values(**values).returning(PreviewInteractionModel)
            
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                raise PreviewInteractionNotFoundException(f"Preview interaction not found: {interaction_id}")
            
            await self.session.commit()
            
            logger.info(
                f"Updated interaction status: {interaction_id} -> {status}",
                extra={
                    "interaction_id": str(interaction_id),
                    "status": status,
                    "reviewed_by": str(reviewed_by) if reviewed_by else None
                }
            )
            
            return self._interaction_model_to_entity(model)
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to update interaction status: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def apply_interactions_to_version(
        self, 
        version_id: UUID, 
        interaction_ids: List[UUID]
    ) -> PreviewVersionEntity:
        """Apply multiple interactions to create a new version."""
        try:
            # This is a complex operation that would involve:
            # 1. Loading the parent version
            # 2. Loading all specified interactions
            # 3. Applying the changes to create new version data
            # 4. Creating a new version entity
            # 5. Updating interaction statuses to 'applied'
            
            # For now, this is a placeholder implementation
            # In a real system, this would involve business logic
            # to merge interaction changes into version data
            
            parent_version = await self.find_preview_version_by_id(version_id)
            if not parent_version:
                raise PreviewVersionNotFoundException(f"Parent version not found: {version_id}")
            
            # TODO: Implement actual interaction application logic
            # This would involve parsing change_data from interactions
            # and applying them to the parent version's version_data
            
            # For now, just mark interactions as applied
            interaction_id_strs = [str(iid) for iid in interaction_ids]
            await self.session.execute(
                update(PreviewInteractionModel).where(
                    PreviewInteractionModel.interaction_id.in_(interaction_id_strs)
                ).values(
                    status="applied",
                    applied_at=func.now(),
                    updated_at=func.now()
                )
            )
            
            await self.session.commit()
            
            return parent_version
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to apply interactions to version: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def get_interaction_statistics(
        self, 
        version_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get interaction statistics."""
        try:
            base_query = select(PreviewInteractionModel)
            
            conditions = []
            if version_id:
                conditions.append(PreviewInteractionModel.version_id == str(version_id))
            if user_id:
                conditions.append(PreviewInteractionModel.user_id == str(user_id))
            if start_date:
                conditions.append(PreviewInteractionModel.created_at >= start_date)
            if end_date:
                conditions.append(PreviewInteractionModel.created_at <= end_date)
            
            if conditions:
                base_query = base_query.where(and_(*conditions))
            
            # Count total interactions
            total_result = await self.session.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total_interactions = total_result.scalar()
            
            # Count by status
            status_result = await self.session.execute(
                select(
                    PreviewInteractionModel.status,
                    func.count(PreviewInteractionModel.status)
                ).group_by(PreviewInteractionModel.status).select_from(
                    base_query.subquery()
                )
            )
            status_counts = dict(status_result.all())
            
            # Count by interaction type
            type_result = await self.session.execute(
                select(
                    PreviewInteractionModel.interaction_type,
                    func.count(PreviewInteractionModel.interaction_type)
                ).group_by(PreviewInteractionModel.interaction_type).select_from(
                    base_query.subquery()
                )
            )
            type_counts = dict(type_result.all())
            
            # Count by change type
            change_result = await self.session.execute(
                select(
                    PreviewInteractionModel.change_type,
                    func.count(PreviewInteractionModel.change_type)
                ).group_by(PreviewInteractionModel.change_type).select_from(
                    base_query.subquery()
                )
            )
            change_counts = dict(change_result.all())
            
            return {
                "total_interactions": total_interactions,
                "status_breakdown": status_counts,
                "interaction_type_breakdown": type_counts,
                "change_type_breakdown": change_counts,
                "pending_interactions": status_counts.get("pending", 0),
                "approved_interactions": status_counts.get("approved", 0),
                "applied_interactions": status_counts.get("applied", 0)
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get interaction statistics: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    # ===== Preview Quality Settings Operations =====
    
    async def create_quality_settings(
        self, 
        settings: PreviewQualitySettingsEntity
    ) -> PreviewQualitySettingsEntity:
        """Create preview quality settings for user."""
        try:
            model = PreviewQualitySettingsModel(
                setting_id=str(settings.setting_id),
                user_id=str(settings.user_id),
                device_capability=settings.device_capability,
                bandwidth_estimate=settings.bandwidth_estimate,
                preferred_quality=settings.preferred_quality,
                max_quality=settings.max_quality,
                auto_adjust_quality=settings.auto_adjust_quality,
                max_generation_time_seconds=settings.max_generation_time_seconds,
                preferred_resolution=settings.preferred_resolution,
                enable_caching=settings.enable_caching,
                preview_format_preference=settings.preview_format_preference,
                enable_progressive_loading=settings.enable_progressive_loading,
                enable_thumbnails=settings.enable_thumbnails,
                ai_enhancement_level=settings.ai_enhancement_level,
                enable_smart_cropping=settings.enable_smart_cropping,
                enable_color_optimization=settings.enable_color_optimization,
                enable_realtime_preview=settings.enable_realtime_preview,
                feedback_sensitivity=settings.feedback_sensitivity,
                auto_apply_suggestions=settings.auto_apply_suggestions,
                average_generation_time=settings.average_generation_time,
                last_performance_update=settings.last_performance_update
            )
            
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            
            logger.info(
                f"Created quality settings: {model.setting_id}",
                extra={
                    "setting_id": model.setting_id,
                    "user_id": model.user_id,
                    "preferred_quality": model.preferred_quality
                }
            )
            
            return self._quality_settings_model_to_entity(model)
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Quality settings creation failed - integrity error: {str(e)}")
            raise PreviewRepositoryException(f"Failed to create quality settings: {str(e)}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Quality settings creation failed: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def find_quality_settings_by_user(self, user_id: UUID) -> Optional[PreviewQualitySettingsEntity]:
        """Find quality settings by user ID."""
        try:
            stmt = select(PreviewQualitySettingsModel).where(
                PreviewQualitySettingsModel.user_id == str(user_id)
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return self._quality_settings_model_to_entity(model)
            return None
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to find quality settings by user: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def update_quality_settings(
        self, 
        settings: PreviewQualitySettingsEntity
    ) -> PreviewQualitySettingsEntity:
        """Update quality settings."""
        try:
            stmt = update(PreviewQualitySettingsModel).where(
                PreviewQualitySettingsModel.setting_id == str(settings.setting_id)
            ).values(
                device_capability=settings.device_capability,
                bandwidth_estimate=settings.bandwidth_estimate,
                preferred_quality=settings.preferred_quality,
                max_quality=settings.max_quality,
                auto_adjust_quality=settings.auto_adjust_quality,
                max_generation_time_seconds=settings.max_generation_time_seconds,
                preferred_resolution=settings.preferred_resolution,
                enable_caching=settings.enable_caching,
                preview_format_preference=settings.preview_format_preference,
                enable_progressive_loading=settings.enable_progressive_loading,
                enable_thumbnails=settings.enable_thumbnails,
                ai_enhancement_level=settings.ai_enhancement_level,
                enable_smart_cropping=settings.enable_smart_cropping,
                enable_color_optimization=settings.enable_color_optimization,
                enable_realtime_preview=settings.enable_realtime_preview,
                feedback_sensitivity=settings.feedback_sensitivity,
                auto_apply_suggestions=settings.auto_apply_suggestions,
                average_generation_time=settings.average_generation_time,
                last_performance_update=settings.last_performance_update,
                updated_at=func.now()
            ).returning(PreviewQualitySettingsModel)
            
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                raise PreviewQualitySettingsNotFoundException(f"Quality settings not found: {settings.setting_id}")
            
            await self.session.commit()
            
            logger.info(
                f"Updated quality settings: {model.setting_id}",
                extra={"setting_id": model.setting_id}
            )
            
            return self._quality_settings_model_to_entity(model)
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to update quality settings: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def update_performance_metrics(
        self, 
        user_id: UUID,
        generation_time: float,
        device_capability: Optional[float] = None
    ) -> PreviewQualitySettingsEntity:
        """Update performance metrics for quality settings."""
        try:
            # Find existing settings
            settings = await self.find_quality_settings_by_user(user_id)
            if not settings:
                raise PreviewQualitySettingsNotFoundException(f"Quality settings not found for user: {user_id}")
            
            # Update performance metrics
            settings.update_performance_metrics(generation_time)
            
            if device_capability is not None:
                settings.device_capability = device_capability
            
            # Save updated settings
            return await self.update_quality_settings(settings)
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to update performance metrics: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def get_quality_recommendations(
        self, 
        user_id: UUID,
        current_load: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get quality recommendations based on user settings and current system load."""
        try:
            settings = await self.find_quality_settings_by_user(user_id)
            if not settings:
                # Return default recommendations
                return {
                    "recommended_quality": 3,
                    "use_progressive_loading": False,
                    "estimated_generation_time": 15.0,
                    "timeout_seconds": 30,
                    "reason": "No user settings found - using defaults"
                }
            
            load = current_load or 1.0
            recommended_quality = settings.get_recommended_quality(load)
            
            return {
                "recommended_quality": recommended_quality,
                "use_progressive_loading": settings.should_use_progressive_loading(),
                "estimated_generation_time": settings.estimate_generation_time(),
                "timeout_seconds": settings.get_timeout_for_quality(recommended_quality),
                "device_capability": settings.device_capability,
                "current_load": load,
                "reason": "Based on user preferences and performance history"
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get quality recommendations: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    # ===== Cleanup and Maintenance Operations =====
    
    async def cleanup_old_versions(
        self, 
        request_id: UUID,
        keep_final: bool = True,
        keep_latest_per_branch: bool = True
    ) -> int:
        """Clean up old preview versions to save space."""
        try:
            versions_to_delete = []
            
            # Find all versions for this request
            all_versions = await self.find_preview_versions_by_request(request_id)
            
            if keep_final:
                # Keep final versions
                final_versions = await self.find_final_versions(request_id)
                final_ids = {v.version_id for v in final_versions}
            else:
                final_ids = set()
            
            if keep_latest_per_branch:
                # Find latest version per branch per phase
                latest_per_branch = {}
                for version in all_versions:
                    key = (version.phase, version.branch_name or "main")
                    if key not in latest_per_branch or version.created_at > latest_per_branch[key].created_at:
                        latest_per_branch[key] = version
                latest_ids = {v.version_id for v in latest_per_branch.values()}
            else:
                latest_ids = set()
            
            # Identify versions to delete
            for version in all_versions:
                if (version.version_id not in final_ids and 
                    version.version_id not in latest_ids):
                    versions_to_delete.append(version.version_id)
            
            # Delete identified versions
            deleted_count = 0
            for version_id in versions_to_delete:
                if await self.delete_preview_version(version_id):
                    deleted_count += 1
            
            logger.info(
                f"Cleaned up {deleted_count} old versions for request {request_id}",
                extra={
                    "request_id": str(request_id),
                    "deleted_count": deleted_count,
                    "keep_final": keep_final,
                    "keep_latest_per_branch": keep_latest_per_branch
                }
            )
            
            return deleted_count
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to cleanup old versions: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def get_storage_usage(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            base_query = select(PreviewVersionModel)
            
            if user_id:
                # Need to join with generation_requests to filter by user
                # For now, we'll return overall statistics
                pass
            
            # Count total versions
            total_result = await self.session.execute(
                select(func.count(PreviewVersionModel.version_id))
            )
            total_versions = total_result.scalar()
            
            # Sum file sizes
            size_result = await self.session.execute(
                select(func.sum(PreviewVersionModel.file_size_bytes))
            )
            total_size = size_result.scalar() or 0
            
            # Count by phase
            phase_result = await self.session.execute(
                select(
                    PreviewVersionModel.phase,
                    func.count(PreviewVersionModel.version_id),
                    func.sum(PreviewVersionModel.file_size_bytes)
                ).group_by(PreviewVersionModel.phase)
            )
            phase_stats = {
                f"phase_{phase}": {
                    "version_count": count,
                    "total_size_bytes": size or 0
                }
                for phase, count, size in phase_result.all()
            }
            
            # Count interactions
            interaction_result = await self.session.execute(
                select(func.count(PreviewInteractionModel.interaction_id))
            )
            total_interactions = interaction_result.scalar()
            
            return {
                "total_versions": total_versions,
                "total_size_bytes": total_size,
                "total_interactions": total_interactions,
                "phase_breakdown": phase_stats,
                "average_size_per_version": total_size / max(total_versions, 1)
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get storage usage: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    async def get_version_performance_stats(
        self, 
        request_id: Optional[UUID] = None,
        phase: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get version generation performance statistics."""
        try:
            stmt = select(PreviewVersionModel)
            
            conditions = []
            if request_id:
                conditions.append(PreviewVersionModel.request_id == str(request_id))
            if phase is not None:
                conditions.append(PreviewVersionModel.phase == phase)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # Get performance metrics
            result = await self.session.execute(
                select(
                    func.count(PreviewVersionModel.version_id).label("total_versions"),
                    func.avg(PreviewVersionModel.generation_time_ms).label("avg_generation_time"),
                    func.min(PreviewVersionModel.generation_time_ms).label("min_generation_time"),
                    func.max(PreviewVersionModel.generation_time_ms).label("max_generation_time"),
                    func.avg(PreviewVersionModel.quality_score).label("avg_quality_score"),
                    func.avg(PreviewVersionModel.view_count).label("avg_view_count"),
                    func.avg(PreviewVersionModel.feedback_count).label("avg_feedback_count")
                ).select_from(stmt.subquery())
            )
            
            stats = result.one()
            
            return {
                "total_versions": stats.total_versions,
                "average_generation_time_ms": float(stats.avg_generation_time or 0),
                "min_generation_time_ms": stats.min_generation_time or 0,
                "max_generation_time_ms": stats.max_generation_time or 0,
                "average_quality_score": float(stats.avg_quality_score or 0),
                "average_view_count": float(stats.avg_view_count or 0),
                "average_feedback_count": float(stats.avg_feedback_count or 0),
                "request_id": str(request_id) if request_id else None,
                "phase": phase
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get performance statistics: {str(e)}")
            raise PreviewRepositoryException(f"Database error: {str(e)}")
    
    # ===== Helper Methods =====
    
    def _model_to_entity(self, model: PreviewVersionModel) -> PreviewVersionEntity:
        """Convert SQLAlchemy model to domain entity."""
        return PreviewVersionEntity(
            version_id=UUID(model.version_id),
            request_id=UUID(model.request_id),
            parent_version_id=UUID(model.parent_version_id) if model.parent_version_id else None,
            phase=model.phase,
            version_data=model.version_data,
            change_description=model.change_description,
            quality_level=model.quality_level,
            quality_score=model.quality_score,
            is_active=model.is_active,
            is_final=model.is_final,
            branch_name=model.branch_name,
            merge_status=model.merge_status,
            asset_urls=model.asset_urls,
            thumbnail_url=model.thumbnail_url,
            view_count=model.view_count,
            feedback_count=model.feedback_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            generation_time_ms=model.generation_time_ms,
            file_size_bytes=model.file_size_bytes
        )
    
    def _interaction_model_to_entity(self, model: PreviewInteractionModel) -> PreviewInteractionEntity:
        """Convert interaction model to domain entity."""
        return PreviewInteractionEntity(
            interaction_id=UUID(model.interaction_id),
            version_id=UUID(model.version_id),
            user_id=UUID(model.user_id),
            element_id=model.element_id,
            element_type=model.element_type,
            change_type=model.change_type,
            change_data=model.change_data,
            change_description=model.change_description,
            confidence_score=model.confidence_score,
            interaction_type=model.interaction_type,
            session_id=UUID(model.session_id) if model.session_id else None,
            position_x=model.position_x,
            position_y=model.position_y,
            position_data=model.position_data,
            status=model.status,
            reviewed_by=UUID(model.reviewed_by) if model.reviewed_by else None,
            reviewed_at=model.reviewed_at,
            applied_at=model.applied_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            processing_time_ms=model.processing_time_ms
        )
    
    def _quality_settings_model_to_entity(self, model: PreviewQualitySettingsModel) -> PreviewQualitySettingsEntity:
        """Convert quality settings model to domain entity."""
        return PreviewQualitySettingsEntity(
            setting_id=UUID(model.setting_id),
            user_id=UUID(model.user_id),
            device_capability=model.device_capability,
            bandwidth_estimate=model.bandwidth_estimate,
            preferred_quality=model.preferred_quality,
            max_quality=model.max_quality,
            auto_adjust_quality=model.auto_adjust_quality,
            max_generation_time_seconds=model.max_generation_time_seconds,
            preferred_resolution=model.preferred_resolution,
            enable_caching=model.enable_caching,
            preview_format_preference=model.preview_format_preference,
            enable_progressive_loading=model.enable_progressive_loading,
            enable_thumbnails=model.enable_thumbnails,
            ai_enhancement_level=model.ai_enhancement_level,
            enable_smart_cropping=model.enable_smart_cropping,
            enable_color_optimization=model.enable_color_optimization,
            enable_realtime_preview=model.enable_realtime_preview,
            feedback_sensitivity=model.feedback_sensitivity,
            auto_apply_suggestions=model.auto_apply_suggestions,
            average_generation_time=model.average_generation_time,
            last_performance_update=model.last_performance_update,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _sort_version_tree(self, models: List[PreviewVersionModel]) -> List[PreviewVersionModel]:
        """Sort versions by tree hierarchy (parent -> children)."""
        # Create lookup for parent-child relationships
        version_map = {model.version_id: model for model in models}
        children_map = {}
        
        for model in models:
            parent_id = model.parent_version_id
            if parent_id:
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(model)
        
        # Build sorted list starting from root nodes
        sorted_models = []
        
        def add_with_children(model):
            sorted_models.append(model)
            children = children_map.get(model.version_id, [])
            children.sort(key=lambda x: x.created_at)
            for child in children:
                add_with_children(child)
        
        # Find root nodes (no parent or parent not in this set)
        root_nodes = []
        for model in models:
            if not model.parent_version_id or model.parent_version_id not in version_map:
                root_nodes.append(model)
        
        # Sort root nodes by creation date
        root_nodes.sort(key=lambda x: x.created_at)
        
        # Add each root and its children
        for root in root_nodes:
            add_with_children(root)
        
        return sorted_models