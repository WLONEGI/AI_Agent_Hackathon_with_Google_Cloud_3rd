"""Manga project repository interface for domain layer."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from ...common.entities import MangaProjectEntity


class MangaProjectsRepository(ABC):
    """Abstract repository interface for manga project operations.
    
    This interface defines the contract for manga project data persistence operations.
    Implementations should handle all database-specific logic and return
    domain entities.
    """
    
    @abstractmethod
    async def create(self, project: MangaProjectEntity) -> MangaProjectEntity:
        """Create a new manga project.
        
        Args:
            project: Project entity to create
            
        Returns:
            Created project entity with populated fields
            
        Raises:
            RepositoryError: If creation fails
            ProjectTitleExistsError: If title already exists for user
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, project_id: UUID) -> Optional[MangaProjectEntity]:
        """Find project by ID.
        
        Args:
            project_id: Project ID to search for
            
        Returns:
            Project entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_user(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> List[MangaProjectEntity]:
        """Find projects by user ID.
        
        Args:
            user_id: User ID to search for
            status: Filter by project status
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by
            order_direction: Order direction (asc, desc)
            
        Returns:
            List of project entities
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def update(self, project: MangaProjectEntity) -> MangaProjectEntity:
        """Update existing project.
        
        Args:
            project: Project entity with updated data
            
        Returns:
            Updated project entity
            
        Raises:
            RepositoryError: If update fails
            ProjectNotFoundError: If project doesn't exist
        """
        pass
    
    @abstractmethod
    async def delete(self, project_id: UUID) -> bool:
        """Delete project by ID.
        
        Args:
            project_id: ID of project to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def find_by_status(
        self,
        status: str,
        user_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[MangaProjectEntity]:
        """Find projects by status.
        
        Args:
            status: Project status to filter by
            user_id: Optional user ID filter
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching project entities
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def search_projects(
        self,
        search_term: str,
        user_id: Optional[UUID] = None,
        search_fields: List[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[MangaProjectEntity]:
        """Search projects by term across specified fields.
        
        Args:
            search_term: Term to search for
            user_id: Optional user ID filter
            search_fields: Fields to search in (title, metadata)
            status: Filter by project status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching project entities
            
        Raises:
            RepositoryError: If search fails
        """
        pass
    
    @abstractmethod
    async def get_project_stats(
        self,
        project_id: UUID
    ) -> Dict[str, Any]:
        """Get project statistics and metrics.
        
        Args:
            project_id: Project ID to get stats for
            
        Returns:
            Dictionary containing project statistics
            
        Raises:
            RepositoryError: If query fails
            ProjectNotFoundError: If project doesn't exist
        """
        pass
    
    @abstractmethod
    async def add_file(
        self,
        project_id: UUID,
        file_path: str,
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add file to project.
        
        Args:
            project_id: Project ID to add file to
            file_path: Path to the file
            file_type: Type of file (image, pdf, etc.)
            metadata: Optional file metadata
            
        Returns:
            True if file added successfully
            
        Raises:
            RepositoryError: If operation fails
            ProjectNotFoundError: If project doesn't exist
        """
        pass
    
    @abstractmethod
    async def remove_file(
        self,
        project_id: UUID,
        file_path: str
    ) -> bool:
        """Remove file from project.
        
        Args:
            project_id: Project ID to remove file from
            file_path: Path to the file to remove
            
        Returns:
            True if file removed successfully
            
        Raises:
            RepositoryError: If operation fails
        """
        pass
    
    @abstractmethod
    async def add_tag(
        self,
        project_id: UUID,
        tag: str
    ) -> bool:
        """Add tag to project.
        
        Args:
            project_id: Project ID to add tag to
            tag: Tag to add
            
        Returns:
            True if tag added successfully
            
        Raises:
            RepositoryError: If operation fails
            ProjectNotFoundError: If project doesn't exist
        """
        pass
    
    @abstractmethod
    async def remove_tag(
        self,
        project_id: UUID,
        tag: str
    ) -> bool:
        """Remove tag from project.
        
        Args:
            project_id: Project ID to remove tag from
            tag: Tag to remove
            
        Returns:
            True if tag removed successfully
            
        Raises:
            RepositoryError: If operation fails
        """
        pass
    
    @abstractmethod
    async def get_expired_projects(
        self,
        before_date: Optional[datetime] = None
    ) -> List[MangaProjectEntity]:
        """Get expired projects for cleanup.
        
        Args:
            before_date: Optional cutoff date, defaults to now
            
        Returns:
            List of expired project entities
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def archive_project(
        self,
        project_id: UUID
    ) -> bool:
        """Archive project (set status to archived).
        
        Args:
            project_id: Project ID to archive
            
        Returns:
            True if archived successfully
            
        Raises:
            RepositoryError: If operation fails
            ProjectNotFoundError: If project doesn't exist
        """
        pass


# Repository-specific exceptions
class MangaProjectRepositoryError(Exception):
    """Base manga project repository error."""
    pass


class ProjectNotFoundError(MangaProjectRepositoryError):
    """Project not found error."""
    pass


class ProjectTitleExistsError(MangaProjectRepositoryError):
    """Project title already exists for user error."""
    pass


class ProjectAccessDeniedError(MangaProjectRepositoryError):
    """Project access denied error."""
    pass