"""
Preview Repository Interface - Domain layer repository for preview system.

This repository provides access to preview versions, interactions, and quality settings
for the HITL (Human-in-the-Loop) preview system.

Implements Repository pattern for preview system entities.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from app.domain.common.entities import (
    PreviewVersionEntity, 
    PreviewInteractionEntity, 
    PreviewQualitySettingsEntity
)


class PreviewRepositoryException(Exception):
    """Base exception for preview repository operations."""
    pass


class PreviewVersionNotFoundException(PreviewRepositoryException):
    """Raised when preview version is not found."""
    pass


class PreviewInteractionNotFoundException(PreviewRepositoryException):
    """Raised when preview interaction is not found."""
    pass


class PreviewQualitySettingsNotFoundException(PreviewRepositoryException):
    """Raised when preview quality settings are not found."""
    pass


class PreviewRepository(ABC):
    """
    Repository interface for preview system operations.
    
    Provides access to preview versions, user interactions, and quality settings
    for the manga generation preview system.
    """
    
    # ===== Preview Version Operations =====
    
    @abstractmethod
    async def create_preview_version(self, version: PreviewVersionEntity) -> PreviewVersionEntity:
        """
        Create a new preview version.
        
        Args:
            version: Preview version entity to create
            
        Returns:
            Created preview version entity
            
        Raises:
            PreviewRepositoryException: If creation fails
        """
        pass
    
    @abstractmethod
    async def find_preview_version_by_id(self, version_id: UUID) -> Optional[PreviewVersionEntity]:
        """
        Find preview version by ID.
        
        Args:
            version_id: Version ID to search for
            
        Returns:
            Preview version entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_preview_versions_by_request(
        self, 
        request_id: UUID, 
        phase: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[PreviewVersionEntity]:
        """
        Find preview versions by generation request.
        
        Args:
            request_id: Generation request ID
            phase: Optional phase filter
            is_active: Optional active status filter
            
        Returns:
            List of preview version entities
        """
        pass
    
    @abstractmethod
    async def find_version_tree(
        self, 
        request_id: UUID, 
        phase: int
    ) -> List[PreviewVersionEntity]:
        """
        Find complete version tree for a request and phase.
        
        Args:
            request_id: Generation request ID
            phase: Phase number
            
        Returns:
            List of preview versions in tree order (parent -> children)
        """
        pass
    
    @abstractmethod
    async def find_final_versions(self, request_id: UUID) -> List[PreviewVersionEntity]:
        """
        Find all final versions for a generation request.
        
        Args:
            request_id: Generation request ID
            
        Returns:
            List of final preview versions (one per phase)
        """
        pass
    
    @abstractmethod
    async def update_preview_version(self, version: PreviewVersionEntity) -> PreviewVersionEntity:
        """
        Update preview version.
        
        Args:
            version: Updated preview version entity
            
        Returns:
            Updated preview version entity
            
        Raises:
            PreviewVersionNotFoundException: If version not found
        """
        pass
    
    @abstractmethod
    async def set_final_version(self, version_id: UUID) -> PreviewVersionEntity:
        """
        Set a version as final for its phase (unsets other final versions in same phase).
        
        Args:
            version_id: Version ID to set as final
            
        Returns:
            Updated preview version entity
            
        Raises:
            PreviewVersionNotFoundException: If version not found
        """
        pass
    
    @abstractmethod
    async def increment_view_count(self, version_id: UUID) -> int:
        """
        Increment view count for a preview version.
        
        Args:
            version_id: Version ID to update
            
        Returns:
            New view count
            
        Raises:
            PreviewVersionNotFoundException: If version not found
        """
        pass
    
    @abstractmethod
    async def delete_preview_version(self, version_id: UUID) -> bool:
        """
        Delete preview version and all its interactions.
        
        Args:
            version_id: Version ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    # ===== Preview Interaction Operations =====
    
    @abstractmethod
    async def create_preview_interaction(
        self, 
        interaction: PreviewInteractionEntity
    ) -> PreviewInteractionEntity:
        """
        Create a new preview interaction.
        
        Args:
            interaction: Preview interaction entity to create
            
        Returns:
            Created preview interaction entity
            
        Raises:
            PreviewRepositoryException: If creation fails
        """
        pass
    
    @abstractmethod
    async def find_preview_interaction_by_id(
        self, 
        interaction_id: UUID
    ) -> Optional[PreviewInteractionEntity]:
        """
        Find preview interaction by ID.
        
        Args:
            interaction_id: Interaction ID to search for
            
        Returns:
            Preview interaction entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_interactions_by_version(
        self, 
        version_id: UUID,
        interaction_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[PreviewInteractionEntity]:
        """
        Find interactions by version.
        
        Args:
            version_id: Version ID to search for
            interaction_type: Optional interaction type filter
            status: Optional status filter
            
        Returns:
            List of preview interaction entities
        """
        pass
    
    @abstractmethod
    async def find_interactions_by_user(
        self, 
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PreviewInteractionEntity]:
        """
        Find interactions by user.
        
        Args:
            user_id: User ID to search for
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of preview interaction entities
        """
        pass
    
    @abstractmethod
    async def find_pending_interactions(
        self, 
        version_id: Optional[UUID] = None
    ) -> List[PreviewInteractionEntity]:
        """
        Find pending interactions that need processing.
        
        Args:
            version_id: Optional version filter
            
        Returns:
            List of pending preview interaction entities
        """
        pass
    
    @abstractmethod
    async def update_interaction_status(
        self, 
        interaction_id: UUID, 
        status: str,
        reviewed_by: Optional[UUID] = None
    ) -> PreviewInteractionEntity:
        """
        Update interaction status.
        
        Args:
            interaction_id: Interaction ID to update
            status: New status
            reviewed_by: Optional reviewer user ID
            
        Returns:
            Updated preview interaction entity
            
        Raises:
            PreviewInteractionNotFoundException: If interaction not found
        """
        pass
    
    @abstractmethod
    async def apply_interactions_to_version(
        self, 
        version_id: UUID, 
        interaction_ids: List[UUID]
    ) -> PreviewVersionEntity:
        """
        Apply multiple interactions to create a new version.
        
        Args:
            version_id: Parent version ID
            interaction_ids: List of interaction IDs to apply
            
        Returns:
            New preview version entity with interactions applied
            
        Raises:
            PreviewVersionNotFoundException: If version not found
            PreviewInteractionNotFoundException: If any interaction not found
        """
        pass
    
    @abstractmethod
    async def get_interaction_statistics(
        self, 
        version_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get interaction statistics.
        
        Args:
            version_id: Optional version filter
            user_id: Optional user filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with interaction statistics
        """
        pass
    
    # ===== Preview Quality Settings Operations =====
    
    @abstractmethod
    async def create_quality_settings(
        self, 
        settings: PreviewQualitySettingsEntity
    ) -> PreviewQualitySettingsEntity:
        """
        Create preview quality settings for user.
        
        Args:
            settings: Quality settings entity to create
            
        Returns:
            Created quality settings entity
            
        Raises:
            PreviewRepositoryException: If creation fails
        """
        pass
    
    @abstractmethod
    async def find_quality_settings_by_user(self, user_id: UUID) -> Optional[PreviewQualitySettingsEntity]:
        """
        Find quality settings by user ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            Quality settings entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update_quality_settings(
        self, 
        settings: PreviewQualitySettingsEntity
    ) -> PreviewQualitySettingsEntity:
        """
        Update quality settings.
        
        Args:
            settings: Updated quality settings entity
            
        Returns:
            Updated quality settings entity
            
        Raises:
            PreviewQualitySettingsNotFoundException: If settings not found
        """
        pass
    
    @abstractmethod
    async def update_performance_metrics(
        self, 
        user_id: UUID,
        generation_time: float,
        device_capability: Optional[float] = None
    ) -> PreviewQualitySettingsEntity:
        """
        Update performance metrics for quality settings.
        
        Args:
            user_id: User ID to update
            generation_time: Latest generation time
            device_capability: Optional device capability update
            
        Returns:
            Updated quality settings entity
            
        Raises:
            PreviewQualitySettingsNotFoundException: If settings not found
        """
        pass
    
    @abstractmethod
    async def get_quality_recommendations(
        self, 
        user_id: UUID,
        current_load: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get quality recommendations based on user settings and current system load.
        
        Args:
            user_id: User ID for recommendations
            current_load: Optional current system load factor
            
        Returns:
            Dictionary with quality recommendations
        """
        pass
    
    # ===== Cleanup and Maintenance Operations =====
    
    @abstractmethod
    async def cleanup_old_versions(
        self, 
        request_id: UUID,
        keep_final: bool = True,
        keep_latest_per_branch: bool = True
    ) -> int:
        """
        Clean up old preview versions to save space.
        
        Args:
            request_id: Request ID to clean up
            keep_final: Whether to keep final versions
            keep_latest_per_branch: Whether to keep latest version per branch
            
        Returns:
            Number of versions deleted
        """
        pass
    
    @abstractmethod
    async def get_storage_usage(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get storage usage statistics.
        
        Args:
            user_id: Optional user filter
            
        Returns:
            Dictionary with storage usage statistics
        """
        pass
    
    @abstractmethod
    async def get_version_performance_stats(
        self, 
        request_id: Optional[UUID] = None,
        phase: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get version generation performance statistics.
        
        Args:
            request_id: Optional request filter
            phase: Optional phase filter
            
        Returns:
            Dictionary with performance statistics
        """
        pass