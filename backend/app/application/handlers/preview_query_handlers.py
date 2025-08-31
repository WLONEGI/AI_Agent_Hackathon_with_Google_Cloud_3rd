"""
Preview System Query Handlers - Phase 2 Preview System Implementation.

This module contains query handlers for preview system data retrieval
including version queries, interaction analysis, and quality recommendations.

Implements Query Handler pattern with read-optimized operations.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from app.application.handlers.base_handler import BaseQueryHandler
from app.application.queries.preview_queries import (
    GetPreviewVersionByIdQuery,
    GetPreviewVersionsByRequestQuery,
    GetVersionTreeQuery,
    GetFinalVersionsQuery,
    GetActiveVersionsQuery,
    GetPreviewInteractionByIdQuery,
    GetInteractionsByVersionQuery,
    GetInteractionsByUserQuery,
    GetPendingInteractionsQuery,
    GetInteractionStatisticsQuery,
    GetQualitySettingsByUserQuery,
    GetQualityRecommendationsQuery,
    GetStorageUsageQuery,
    GetVersionPerformanceStatsQuery,
    GetUserEngagementStatsQuery,
    GetQualityTrendsQuery,
    GetVersionComparisonQuery,
    GetFeedbackHeatmapQuery,
    GetRecommendedVersionsQuery
)
from app.application.messaging.query_result import QueryResult
from app.domain.manga.repositories.preview_repository import (
    PreviewRepository,
    PreviewVersionNotFoundException,
    PreviewInteractionNotFoundException,
    PreviewQualitySettingsNotFoundException
)

logger = logging.getLogger(__name__)


# ===== Preview Version Query Handlers =====

class GetPreviewVersionByIdHandler(BaseQueryHandler[GetPreviewVersionByIdQuery, Dict[str, Any]]):
    """Handler for retrieving preview version by ID."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetPreviewVersionByIdQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get preview version by ID."""
        try:
            logger.debug(
                f"Retrieving preview version: {query.version_id}",
                extra={
                    "query": "GetPreviewVersionById",
                    "version_id": str(query.version_id)
                }
            )
            
            version = await self.preview_repository.find_preview_version_by_id(query.version_id)
            
            if not version:
                return QueryResult.failure(
                    error_code="version_not_found",
                    error=f"Preview version not found: {query.version_id}"
                )
            
            result = {
                "version_id": str(version.version_id),
                "request_id": str(version.request_id),
                "parent_version_id": str(version.parent_version_id) if version.parent_version_id else None,
                "phase": version.phase,
                "version_data": version.version_data,
                "change_description": version.change_description,
                "quality_level": version.quality_level,
                "quality_score": version.quality_score,
                "is_active": version.is_active,
                "is_final": version.is_final,
                "branch_name": version.branch_name,
                "merge_status": version.merge_status,
                "asset_urls": version.asset_urls,
                "thumbnail_url": version.thumbnail_url,
                "view_count": version.view_count,
                "feedback_count": version.feedback_count,
                "created_at": version.created_at.isoformat() if version.created_at else None,
                "updated_at": version.updated_at.isoformat() if version.updated_at else None,
                "generation_time_ms": version.generation_time_ms,
                "file_size_bytes": version.file_size_bytes,
                "complexity_score": version.calculate_complexity_score()
            }
            
            logger.debug(
                f"Successfully retrieved preview version: {query.version_id}",
                extra={
                    "query": "GetPreviewVersionById",
                    "version_id": str(query.version_id)
                }
            )
            
            return QueryResult.success(result)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve preview version: {str(e)}",
                extra={
                    "query": "GetPreviewVersionById",
                    "version_id": str(query.version_id),
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_preview_version_failed",
                error=f"Failed to retrieve preview version: {str(e)}"
            )


class GetPreviewVersionsByRequestHandler(BaseQueryHandler[GetPreviewVersionsByRequestQuery, Dict[str, Any]]):
    """Handler for retrieving preview versions by request."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetPreviewVersionsByRequestQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get preview versions by request."""
        try:
            logger.debug(
                f"Retrieving preview versions for request: {query.request_id}",
                extra={
                    "query": "GetPreviewVersionsByRequest",
                    "request_id": str(query.request_id),
                    "phase": query.phase,
                    "is_active": query.is_active
                }
            )
            
            versions = await self.preview_repository.find_preview_versions_by_request(
                query.request_id,
                query.phase,
                query.is_active
            )
            
            # Apply pagination if specified
            total_count = len(versions)
            if query.offset is not None:
                versions = versions[query.offset:]
            if query.limit is not None:
                versions = versions[:query.limit]
            
            result_versions = []
            for version in versions:
                result_versions.append({
                    "version_id": str(version.version_id),
                    "request_id": str(version.request_id),
                    "parent_version_id": str(version.parent_version_id) if version.parent_version_id else None,
                    "phase": version.phase,
                    "change_description": version.change_description,
                    "quality_level": version.quality_level,
                    "quality_score": version.quality_score,
                    "is_active": version.is_active,
                    "is_final": version.is_final,
                    "branch_name": version.branch_name,
                    "merge_status": version.merge_status,
                    "thumbnail_url": version.thumbnail_url,
                    "view_count": version.view_count,
                    "feedback_count": version.feedback_count,
                    "created_at": version.created_at.isoformat() if version.created_at else None,
                    "updated_at": version.updated_at.isoformat() if version.updated_at else None,
                    "generation_time_ms": version.generation_time_ms,
                    "file_size_bytes": version.file_size_bytes
                })
            
            result = {
                "versions": result_versions,
                "total_count": total_count,
                "returned_count": len(result_versions),
                "request_id": str(query.request_id),
                "phase": query.phase,
                "is_active": query.is_active
            }
            
            logger.debug(
                f"Successfully retrieved {len(result_versions)} preview versions",
                extra={
                    "query": "GetPreviewVersionsByRequest",
                    "request_id": str(query.request_id),
                    "count": len(result_versions)
                }
            )
            
            return QueryResult.success(result)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve preview versions by request: {str(e)}",
                extra={
                    "query": "GetPreviewVersionsByRequest",
                    "request_id": str(query.request_id),
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_preview_versions_by_request_failed",
                error=f"Failed to retrieve preview versions: {str(e)}"
            )


class GetVersionTreeHandler(BaseQueryHandler[GetVersionTreeQuery, Dict[str, Any]]):
    """Handler for retrieving version tree."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetVersionTreeQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get version tree."""
        try:
            logger.debug(
                f"Retrieving version tree for request {query.request_id}, phase {query.phase}",
                extra={
                    "query": "GetVersionTree",
                    "request_id": str(query.request_id),
                    "phase": query.phase
                }
            )
            
            versions = await self.preview_repository.find_version_tree(query.request_id, query.phase)
            
            # Build tree structure with parent-child relationships
            tree_versions = []
            for version in versions:
                tree_versions.append({
                    "version_id": str(version.version_id),
                    "parent_version_id": str(version.parent_version_id) if version.parent_version_id else None,
                    "change_description": version.change_description,
                    "quality_level": version.quality_level,
                    "quality_score": version.quality_score,
                    "is_active": version.is_active,
                    "is_final": version.is_final,
                    "branch_name": version.branch_name,
                    "merge_status": version.merge_status,
                    "view_count": version.view_count,
                    "feedback_count": version.feedback_count,
                    "created_at": version.created_at.isoformat() if version.created_at else None,
                    "generation_time_ms": version.generation_time_ms,
                    "has_parent": version.has_parent(),
                    "branch_path": version.get_branch_path()
                })
            
            result = {
                "version_tree": tree_versions,
                "request_id": str(query.request_id),
                "phase": query.phase,
                "total_versions": len(tree_versions)
            }
            
            logger.debug(
                f"Successfully retrieved version tree with {len(tree_versions)} versions",
                extra={
                    "query": "GetVersionTree",
                    "request_id": str(query.request_id),
                    "phase": query.phase,
                    "count": len(tree_versions)
                }
            )
            
            return QueryResult.success(result)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve version tree: {str(e)}",
                extra={
                    "query": "GetVersionTree",
                    "request_id": str(query.request_id),
                    "phase": query.phase,
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_version_tree_failed",
                error=f"Failed to retrieve version tree: {str(e)}"
            )


class GetFinalVersionsHandler(BaseQueryHandler[GetFinalVersionsQuery, Dict[str, Any]]):
    """Handler for retrieving final versions."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetFinalVersionsQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get final versions."""
        try:
            logger.debug(
                f"Retrieving final versions for request: {query.request_id}",
                extra={
                    "query": "GetFinalVersions",
                    "request_id": str(query.request_id)
                }
            )
            
            versions = await self.preview_repository.find_final_versions(query.request_id)
            
            final_versions = []
            for version in versions:
                final_versions.append({
                    "version_id": str(version.version_id),
                    "phase": version.phase,
                    "quality_level": version.quality_level,
                    "quality_score": version.quality_score,
                    "branch_name": version.branch_name,
                    "thumbnail_url": version.thumbnail_url,
                    "view_count": version.view_count,
                    "feedback_count": version.feedback_count,
                    "created_at": version.created_at.isoformat() if version.created_at else None,
                    "generation_time_ms": version.generation_time_ms,
                    "file_size_bytes": version.file_size_bytes
                })
            
            result = {
                "final_versions": final_versions,
                "request_id": str(query.request_id),
                "total_phases": len(final_versions),
                "completed_phases": [v["phase"] for v in final_versions]
            }
            
            logger.debug(
                f"Successfully retrieved {len(final_versions)} final versions",
                extra={
                    "query": "GetFinalVersions",
                    "request_id": str(query.request_id),
                    "count": len(final_versions)
                }
            )
            
            return QueryResult.success(result)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve final versions: {str(e)}",
                extra={
                    "query": "GetFinalVersions",
                    "request_id": str(query.request_id),
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_final_versions_failed",
                error=f"Failed to retrieve final versions: {str(e)}"
            )


# ===== Preview Interaction Query Handlers =====

class GetPreviewInteractionByIdHandler(BaseQueryHandler[GetPreviewInteractionByIdQuery, Dict[str, Any]]):
    """Handler for retrieving preview interaction by ID."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetPreviewInteractionByIdQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get preview interaction by ID."""
        try:
            logger.debug(
                f"Retrieving preview interaction: {query.interaction_id}",
                extra={
                    "query": "GetPreviewInteractionById",
                    "interaction_id": str(query.interaction_id)
                }
            )
            
            interaction = await self.preview_repository.find_preview_interaction_by_id(query.interaction_id)
            
            if not interaction:
                return QueryResult.failure(
                    error_code="interaction_not_found",
                    error=f"Preview interaction not found: {query.interaction_id}"
                )
            
            result = {
                "interaction_id": str(interaction.interaction_id),
                "version_id": str(interaction.version_id),
                "user_id": str(interaction.user_id),
                "element_id": interaction.element_id,
                "element_type": interaction.element_type,
                "change_type": interaction.change_type,
                "change_data": interaction.change_data,
                "change_description": interaction.change_description,
                "confidence_score": interaction.confidence_score,
                "interaction_type": interaction.interaction_type,
                "session_id": str(interaction.session_id) if interaction.session_id else None,
                "position_x": interaction.position_x,
                "position_y": interaction.position_y,
                "position_data": interaction.position_data,
                "status": interaction.status,
                "reviewed_by": str(interaction.reviewed_by) if interaction.reviewed_by else None,
                "reviewed_at": interaction.reviewed_at.isoformat() if interaction.reviewed_at else None,
                "applied_at": interaction.applied_at.isoformat() if interaction.applied_at else None,
                "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
                "updated_at": interaction.updated_at.isoformat() if interaction.updated_at else None,
                "processing_time_ms": interaction.processing_time_ms,
                "has_position": interaction.has_position(),
                "position_tuple": interaction.get_position_tuple(),
                "impact_score": interaction.calculate_impact_score()
            }
            
            logger.debug(
                f"Successfully retrieved preview interaction: {query.interaction_id}",
                extra={
                    "query": "GetPreviewInteractionById",
                    "interaction_id": str(query.interaction_id)
                }
            )
            
            return QueryResult.success(result)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve preview interaction: {str(e)}",
                extra={
                    "query": "GetPreviewInteractionById",
                    "interaction_id": str(query.interaction_id),
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_preview_interaction_failed",
                error=f"Failed to retrieve preview interaction: {str(e)}"
            )


class GetInteractionsByVersionHandler(BaseQueryHandler[GetInteractionsByVersionQuery, Dict[str, Any]]):
    """Handler for retrieving interactions by version."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetInteractionsByVersionQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get interactions by version."""
        try:
            logger.debug(
                f"Retrieving interactions for version: {query.version_id}",
                extra={
                    "query": "GetInteractionsByVersion",
                    "version_id": str(query.version_id),
                    "interaction_type": query.interaction_type,
                    "status": query.status
                }
            )
            
            interactions = await self.preview_repository.find_interactions_by_version(
                query.version_id,
                query.interaction_type,
                query.status
            )
            
            # Apply pagination if specified
            total_count = len(interactions)
            if query.offset is not None:
                interactions = interactions[query.offset:]
            if query.limit is not None:
                interactions = interactions[:query.limit]
            
            result_interactions = []
            for interaction in interactions:
                result_interactions.append({
                    "interaction_id": str(interaction.interaction_id),
                    "user_id": str(interaction.user_id),
                    "element_id": interaction.element_id,
                    "element_type": interaction.element_type,
                    "change_type": interaction.change_type,
                    "change_description": interaction.change_description,
                    "confidence_score": interaction.confidence_score,
                    "interaction_type": interaction.interaction_type,
                    "status": interaction.status,
                    "position_x": interaction.position_x,
                    "position_y": interaction.position_y,
                    "reviewed_by": str(interaction.reviewed_by) if interaction.reviewed_by else None,
                    "reviewed_at": interaction.reviewed_at.isoformat() if interaction.reviewed_at else None,
                    "applied_at": interaction.applied_at.isoformat() if interaction.applied_at else None,
                    "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
                    "processing_time_ms": interaction.processing_time_ms,
                    "impact_score": interaction.calculate_impact_score()
                })
            
            result = {
                "interactions": result_interactions,
                "total_count": total_count,
                "returned_count": len(result_interactions),
                "version_id": str(query.version_id),
                "interaction_type": query.interaction_type,
                "status": query.status
            }
            
            logger.debug(
                f"Successfully retrieved {len(result_interactions)} interactions",
                extra={
                    "query": "GetInteractionsByVersion",
                    "version_id": str(query.version_id),
                    "count": len(result_interactions)
                }
            )
            
            return QueryResult.success(result)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve interactions by version: {str(e)}",
                extra={
                    "query": "GetInteractionsByVersion",
                    "version_id": str(query.version_id),
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_interactions_by_version_failed",
                error=f"Failed to retrieve interactions: {str(e)}"
            )


class GetPendingInteractionsHandler(BaseQueryHandler[GetPendingInteractionsQuery, Dict[str, Any]]):
    """Handler for retrieving pending interactions."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetPendingInteractionsQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get pending interactions."""
        try:
            logger.debug(
                f"Retrieving pending interactions",
                extra={
                    "query": "GetPendingInteractions",
                    "version_id": str(query.version_id) if query.version_id else None
                }
            )
            
            interactions = await self.preview_repository.find_pending_interactions(query.version_id)
            
            # Apply pagination if specified
            total_count = len(interactions)
            if query.offset is not None:
                interactions = interactions[query.offset:]
            if query.limit is not None:
                interactions = interactions[:query.limit]
            
            pending_interactions = []
            for interaction in interactions:
                pending_interactions.append({
                    "interaction_id": str(interaction.interaction_id),
                    "version_id": str(interaction.version_id),
                    "user_id": str(interaction.user_id),
                    "element_id": interaction.element_id,
                    "element_type": interaction.element_type,
                    "change_type": interaction.change_type,
                    "change_description": interaction.change_description,
                    "interaction_type": interaction.interaction_type,
                    "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
                    "processing_time_ms": interaction.processing_time_ms,
                    "impact_score": interaction.calculate_impact_score()
                })
            
            result = {
                "pending_interactions": pending_interactions,
                "total_count": total_count,
                "returned_count": len(pending_interactions),
                "version_id": str(query.version_id) if query.version_id else None
            }
            
            logger.debug(
                f"Successfully retrieved {len(pending_interactions)} pending interactions",
                extra={
                    "query": "GetPendingInteractions",
                    "count": len(pending_interactions)
                }
            )
            
            return QueryResult.success(result)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve pending interactions: {str(e)}",
                extra={
                    "query": "GetPendingInteractions",
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_pending_interactions_failed",
                error=f"Failed to retrieve pending interactions: {str(e)}"
            )


class GetInteractionStatisticsHandler(BaseQueryHandler[GetInteractionStatisticsQuery, Dict[str, Any]]):
    """Handler for retrieving interaction statistics."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetInteractionStatisticsQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get interaction statistics."""
        try:
            logger.debug(
                f"Retrieving interaction statistics",
                extra={
                    "query": "GetInteractionStatistics",
                    "version_id": str(query.version_id) if query.version_id else None,
                    "user_id": str(query.user_id) if query.user_id else None
                }
            )
            
            statistics = await self.preview_repository.get_interaction_statistics(
                query.version_id,
                query.user_id,
                query.start_date,
                query.end_date
            )
            
            # Add computed metrics
            statistics["query_parameters"] = {
                "version_id": str(query.version_id) if query.version_id else None,
                "user_id": str(query.user_id) if query.user_id else None,
                "start_date": query.start_date.isoformat() if query.start_date else None,
                "end_date": query.end_date.isoformat() if query.end_date else None
            }
            
            logger.debug(
                f"Successfully retrieved interaction statistics",
                extra={
                    "query": "GetInteractionStatistics",
                    "total_interactions": statistics.get("total_interactions", 0)
                }
            )
            
            return QueryResult.success(statistics)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve interaction statistics: {str(e)}",
                extra={
                    "query": "GetInteractionStatistics",
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_interaction_statistics_failed",
                error=f"Failed to retrieve interaction statistics: {str(e)}"
            )


# ===== Preview Quality Settings Query Handlers =====

class GetQualitySettingsByUserHandler(BaseQueryHandler[GetQualitySettingsByUserQuery, Dict[str, Any]]):
    """Handler for retrieving quality settings by user."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetQualitySettingsByUserQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get quality settings by user."""
        try:
            logger.debug(
                f"Retrieving quality settings for user: {query.user_id}",
                extra={
                    "query": "GetQualitySettingsByUser",
                    "user_id": str(query.user_id)
                }
            )
            
            settings = await self.preview_repository.find_quality_settings_by_user(query.user_id)
            
            if not settings:
                return QueryResult.failure(
                    error_code="settings_not_found",
                    error=f"Quality settings not found for user: {query.user_id}"
                )
            
            result = {
                "setting_id": str(settings.setting_id),
                "user_id": str(settings.user_id),
                "device_capability": settings.device_capability,
                "bandwidth_estimate": settings.bandwidth_estimate,
                "preferred_quality": settings.preferred_quality,
                "max_quality": settings.max_quality,
                "auto_adjust_quality": settings.auto_adjust_quality,
                "max_generation_time_seconds": settings.max_generation_time_seconds,
                "preferred_resolution": settings.preferred_resolution,
                "enable_caching": settings.enable_caching,
                "preview_format_preference": settings.preview_format_preference,
                "enable_progressive_loading": settings.enable_progressive_loading,
                "enable_thumbnails": settings.enable_thumbnails,
                "ai_enhancement_level": settings.ai_enhancement_level,
                "enable_smart_cropping": settings.enable_smart_cropping,
                "enable_color_optimization": settings.enable_color_optimization,
                "enable_realtime_preview": settings.enable_realtime_preview,
                "feedback_sensitivity": settings.feedback_sensitivity,
                "auto_apply_suggestions": settings.auto_apply_suggestions,
                "average_generation_time": settings.average_generation_time,
                "last_performance_update": settings.last_performance_update.isoformat() if settings.last_performance_update else None,
                "created_at": settings.created_at.isoformat() if settings.created_at else None,
                "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
                "should_use_progressive_loading": settings.should_use_progressive_loading()
            }
            
            logger.debug(
                f"Successfully retrieved quality settings for user: {query.user_id}",
                extra={
                    "query": "GetQualitySettingsByUser",
                    "user_id": str(query.user_id),
                    "setting_id": str(settings.setting_id)
                }
            )
            
            return QueryResult.success(result)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve quality settings: {str(e)}",
                extra={
                    "query": "GetQualitySettingsByUser",
                    "user_id": str(query.user_id),
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_quality_settings_failed",
                error=f"Failed to retrieve quality settings: {str(e)}"
            )


class GetQualityRecommendationsHandler(BaseQueryHandler[GetQualityRecommendationsQuery, Dict[str, Any]]):
    """Handler for retrieving quality recommendations."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetQualityRecommendationsQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get quality recommendations."""
        try:
            logger.debug(
                f"Getting quality recommendations for user: {query.user_id}",
                extra={
                    "query": "GetQualityRecommendations",
                    "user_id": str(query.user_id),
                    "current_load": query.current_load
                }
            )
            
            recommendations = await self.preview_repository.get_quality_recommendations(
                query.user_id,
                query.current_load
            )
            
            logger.debug(
                f"Successfully retrieved quality recommendations",
                extra={
                    "query": "GetQualityRecommendations",
                    "user_id": str(query.user_id),
                    "recommended_quality": recommendations.get("recommended_quality")
                }
            )
            
            return QueryResult.success(recommendations)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve quality recommendations: {str(e)}",
                extra={
                    "query": "GetQualityRecommendations",
                    "user_id": str(query.user_id),
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_quality_recommendations_failed",
                error=f"Failed to retrieve quality recommendations: {str(e)}"
            )


# ===== Analytics and Reporting Query Handlers =====

class GetStorageUsageHandler(BaseQueryHandler[GetStorageUsageQuery, Dict[str, Any]]):
    """Handler for retrieving storage usage statistics."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetStorageUsageQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get storage usage."""
        try:
            logger.debug(
                f"Retrieving storage usage statistics",
                extra={
                    "query": "GetStorageUsage",
                    "user_id": str(query.user_id) if query.user_id else None
                }
            )
            
            usage_stats = await self.preview_repository.get_storage_usage(query.user_id)
            
            logger.debug(
                f"Successfully retrieved storage usage statistics",
                extra={
                    "query": "GetStorageUsage",
                    "total_versions": usage_stats.get("total_versions", 0),
                    "total_size_bytes": usage_stats.get("total_size_bytes", 0)
                }
            )
            
            return QueryResult.success(usage_stats)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve storage usage: {str(e)}",
                extra={
                    "query": "GetStorageUsage",
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_storage_usage_failed",
                error=f"Failed to retrieve storage usage: {str(e)}"
            )


class GetVersionPerformanceStatsHandler(BaseQueryHandler[GetVersionPerformanceStatsQuery, Dict[str, Any]]):
    """Handler for retrieving version performance statistics."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetVersionPerformanceStatsQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get version performance stats."""
        try:
            logger.debug(
                f"Retrieving version performance statistics",
                extra={
                    "query": "GetVersionPerformanceStats",
                    "request_id": str(query.request_id) if query.request_id else None,
                    "phase": query.phase
                }
            )
            
            performance_stats = await self.preview_repository.get_version_performance_stats(
                query.request_id,
                query.phase
            )
            
            logger.debug(
                f"Successfully retrieved version performance statistics",
                extra={
                    "query": "GetVersionPerformanceStats",
                    "total_versions": performance_stats.get("total_versions", 0),
                    "average_generation_time_ms": performance_stats.get("average_generation_time_ms", 0)
                }
            )
            
            return QueryResult.success(performance_stats)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve version performance stats: {str(e)}",
                extra={
                    "query": "GetVersionPerformanceStats",
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_version_performance_stats_failed",
                error=f"Failed to retrieve version performance stats: {str(e)}"
            )


# ===== Advanced Query Handlers =====

class GetFeedbackHeatmapHandler(BaseQueryHandler[GetFeedbackHeatmapQuery, Dict[str, Any]]):
    """Handler for generating feedback heatmap."""
    
    def __init__(self, preview_repository: PreviewRepository):
        self.preview_repository = preview_repository
    
    async def handle(self, query: GetFeedbackHeatmapQuery) -> QueryResult[Dict[str, Any]]:
        """Handle get feedback heatmap."""
        try:
            logger.debug(
                f"Generating feedback heatmap for version: {query.version_id}",
                extra={
                    "query": "GetFeedbackHeatmap",
                    "version_id": str(query.version_id),
                    "element_type": query.element_type,
                    "interaction_type": query.interaction_type
                }
            )
            
            # Get interactions for heatmap generation
            interactions = await self.preview_repository.find_interactions_by_version(
                query.version_id,
                query.interaction_type
            )
            
            # Filter by element type if specified
            if query.element_type:
                interactions = [i for i in interactions if i.element_type == query.element_type]
            
            # Build heatmap data
            heatmap_points = []
            element_interactions = {}
            
            for interaction in interactions:
                if interaction.has_position():
                    heatmap_points.append({
                        "x": interaction.position_x,
                        "y": interaction.position_y,
                        "intensity": interaction.calculate_impact_score(),
                        "interaction_type": interaction.interaction_type,
                        "element_type": interaction.element_type,
                        "change_type": interaction.change_type
                    })
                
                # Count interactions per element
                if interaction.element_id not in element_interactions:
                    element_interactions[interaction.element_id] = {
                        "count": 0,
                        "element_type": interaction.element_type,
                        "total_impact": 0.0
                    }
                
                element_interactions[interaction.element_id]["count"] += 1
                element_interactions[interaction.element_id]["total_impact"] += interaction.calculate_impact_score()
            
            result = {
                "version_id": str(query.version_id),
                "heatmap_points": heatmap_points,
                "element_interactions": element_interactions,
                "total_interactions": len(interactions),
                "total_positioned_interactions": len(heatmap_points),
                "element_type_filter": query.element_type,
                "interaction_type_filter": query.interaction_type
            }
            
            logger.debug(
                f"Successfully generated feedback heatmap",
                extra={
                    "query": "GetFeedbackHeatmap",
                    "version_id": str(query.version_id),
                    "heatmap_points": len(heatmap_points),
                    "total_interactions": len(interactions)
                }
            )
            
            return QueryResult.success(result)
            
        except Exception as e:
            logger.error(
                f"Failed to generate feedback heatmap: {str(e)}",
                extra={
                    "query": "GetFeedbackHeatmap",
                    "version_id": str(query.version_id),
                    "error": str(e)
                }
            )
            return QueryResult.failure(
                error_code="get_feedback_heatmap_failed",
                error=f"Failed to generate feedback heatmap: {str(e)}"
            )