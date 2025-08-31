"""Manga project repository implementation using SQLAlchemy."""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.manga_models import MangaProject, ProjectFile, ProjectTag
from app.domain.manga.repositories.manga_projects_repository import (
    MangaProjectsRepository,
    MangaProjectRepositoryError,
    ProjectNotFoundError,
    ProjectTitleExistsError,
    ProjectAccessDeniedError
)
from app.domain.common.entities import MangaProjectEntity
from app.infrastructure.database.repositories.base_repository import BaseRepository


logger = logging.getLogger(__name__)


class MangaProjectsRepositoryImpl(MangaProjectsRepository, BaseRepository):
    """SQLAlchemy implementation of manga projects repository."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.session = session
    
    async def create(self, project: MangaProjectEntity) -> MangaProjectEntity:
        """Create a new manga project."""
        try:
            # Check if project title exists for user
            existing_check = select(MangaProject).where(
                and_(
                    MangaProject.user_id == project.user_id,
                    MangaProject.title == project.title,
                    MangaProject.status != "archived"
                )
            )
            result = await self.session.execute(existing_check)
            existing_project = result.scalar_one_or_none()
            
            if existing_project:
                raise ProjectTitleExistsError(f"Project with title '{project.title}' already exists")
            
            # Create database model
            db_project = MangaProject(
                project_id=project.project_id,
                user_id=project.user_id,
                title=project.title,
                status=project.status,
                metadata=project.metadata or {},
                settings=project.settings or {},
                total_pages=project.total_pages,
                created_at=project.created_at,
                updated_at=project.updated_at,
                expires_at=project.expires_at
            )
            
            self.session.add(db_project)
            await self.session.commit()
            await self.session.refresh(db_project)
            
            logger.info(f"Created manga project {project.project_id} for user {project.user_id}")
            return self._to_entity(db_project)
            
        except ProjectTitleExistsError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create manga project: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to create project: {str(e)}")
    
    async def find_by_id(self, project_id: UUID) -> Optional[MangaProjectEntity]:
        """Find project by ID."""
        try:
            query = select(MangaProject).where(MangaProject.project_id == project_id)
            result = await self.session.execute(query)
            db_project = result.scalar_one_or_none()
            
            if db_project:
                return self._to_entity(db_project)
            return None
            
        except Exception as e:
            logger.error(f"Failed to find project {project_id}: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to find project: {str(e)}")
    
    async def find_by_user(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> List[MangaProjectEntity]:
        """Find projects by user ID."""
        try:
            query = select(MangaProject).where(MangaProject.user_id == user_id)
            
            # Add status filter
            if status:
                query = query.where(MangaProject.status == status)
            
            # Add ordering
            order_column = getattr(MangaProject, order_by, MangaProject.created_at)
            if order_direction.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
            
            # Add pagination
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            db_projects = result.scalars().all()
            
            return [self._to_entity(p) for p in db_projects]
            
        except Exception as e:
            logger.error(f"Failed to find projects for user {user_id}: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to find user projects: {str(e)}")
    
    async def update(self, project: MangaProjectEntity) -> MangaProjectEntity:
        """Update existing project."""
        try:
            # Check if project exists
            query = select(MangaProject).where(MangaProject.project_id == project.project_id)
            result = await self.session.execute(query)
            db_project = result.scalar_one_or_none()
            
            if not db_project:
                raise ProjectNotFoundError(f"Project {project.project_id} not found")
            
            # Update fields
            db_project.title = project.title
            db_project.status = project.status
            db_project.metadata = project.metadata or {}
            db_project.settings = project.settings or {}
            db_project.total_pages = project.total_pages
            db_project.updated_at = project.updated_at
            db_project.expires_at = project.expires_at
            
            await self.session.commit()
            await self.session.refresh(db_project)
            
            logger.info(f"Updated manga project {project.project_id}")
            return self._to_entity(db_project)
            
        except ProjectNotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update project {project.project_id}: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to update project: {str(e)}")
    
    async def delete(self, project_id: UUID) -> bool:
        """Delete project by ID."""
        try:
            # Check if project exists
            query = select(MangaProject).where(MangaProject.project_id == project_id)
            result = await self.session.execute(query)
            db_project = result.scalar_one_or_none()
            
            if not db_project:
                return False
            
            # Delete associated files and tags first
            await self.session.execute(
                delete(ProjectFile).where(ProjectFile.project_id == project_id)
            )
            await self.session.execute(
                delete(ProjectTag).where(ProjectTag.project_id == project_id)
            )
            
            # Delete project
            await self.session.execute(
                delete(MangaProject).where(MangaProject.project_id == project_id)
            )
            
            await self.session.commit()
            logger.info(f"Deleted manga project {project_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete project {project_id}: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to delete project: {str(e)}")
    
    async def find_by_status(
        self,
        status: str,
        user_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[MangaProjectEntity]:
        """Find projects by status."""
        try:
            query = select(MangaProject).where(MangaProject.status == status)
            
            if user_id:
                query = query.where(MangaProject.user_id == user_id)
            
            query = query.order_by(desc(MangaProject.created_at)).limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            db_projects = result.scalars().all()
            
            return [self._to_entity(p) for p in db_projects]
            
        except Exception as e:
            logger.error(f"Failed to find projects by status {status}: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to find projects by status: {str(e)}")
    
    async def search_projects(
        self,
        search_term: str,
        user_id: Optional[UUID] = None,
        search_fields: List[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[MangaProjectEntity]:
        """Search projects by term."""
        try:
            if search_fields is None:
                search_fields = ["title"]
            
            conditions = []
            search_term_lower = search_term.lower()
            
            # Build search conditions
            if "title" in search_fields:
                conditions.append(func.lower(MangaProject.title).contains(search_term_lower))
            
            if not conditions:
                conditions.append(func.lower(MangaProject.title).contains(search_term_lower))
            
            query = select(MangaProject).where(or_(*conditions))
            
            # Add filters
            if user_id:
                query = query.where(MangaProject.user_id == user_id)
            if status:
                query = query.where(MangaProject.status == status)
            
            # Add pagination and ordering
            query = query.order_by(desc(MangaProject.updated_at)).limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            db_projects = result.scalars().all()
            
            return [self._to_entity(p) for p in db_projects]
            
        except Exception as e:
            logger.error(f"Failed to search projects with term '{search_term}': {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to search projects: {str(e)}")
    
    async def get_project_stats(self, project_id: UUID) -> Dict[str, Any]:
        """Get project statistics."""
        try:
            # Check if project exists
            project_query = select(MangaProject).where(MangaProject.project_id == project_id)
            result = await self.session.execute(project_query)
            db_project = result.scalar_one_or_none()
            
            if not db_project:
                raise ProjectNotFoundError(f"Project {project_id} not found")
            
            # Get file count
            file_count_query = select(func.count(ProjectFile.id)).where(
                ProjectFile.project_id == project_id
            )
            file_result = await self.session.execute(file_count_query)
            file_count = file_result.scalar() or 0
            
            # Get tag count
            tag_count_query = select(func.count(ProjectTag.id)).where(
                ProjectTag.project_id == project_id
            )
            tag_result = await self.session.execute(tag_count_query)
            tag_count = tag_result.scalar() or 0
            
            stats = {
                "project_id": str(project_id),
                "title": db_project.title,
                "status": db_project.status,
                "total_pages": db_project.total_pages or 0,
                "file_count": file_count,
                "tag_count": tag_count,
                "created_at": db_project.created_at.isoformat(),
                "updated_at": db_project.updated_at.isoformat(),
                "is_expired": db_project.expires_at and datetime.utcnow() > db_project.expires_at
            }
            
            return stats
            
        except ProjectNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get project stats {project_id}: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to get project stats: {str(e)}")
    
    async def add_file(
        self,
        project_id: UUID,
        file_path: str,
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add file to project."""
        try:
            # Check if project exists
            project_query = select(MangaProject).where(MangaProject.project_id == project_id)
            result = await self.session.execute(project_query)
            db_project = result.scalar_one_or_none()
            
            if not db_project:
                raise ProjectNotFoundError(f"Project {project_id} not found")
            
            # Check if file already exists
            existing_file_query = select(ProjectFile).where(
                and_(
                    ProjectFile.project_id == project_id,
                    ProjectFile.file_path == file_path
                )
            )
            result = await self.session.execute(existing_file_query)
            existing_file = result.scalar_one_or_none()
            
            if existing_file:
                return True  # File already exists
            
            # Add file
            project_file = ProjectFile(
                project_id=project_id,
                file_path=file_path,
                file_type=file_type,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            
            self.session.add(project_file)
            await self.session.commit()
            
            logger.info(f"Added file {file_path} to project {project_id}")
            return True
            
        except ProjectNotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to add file to project {project_id}: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to add file: {str(e)}")
    
    async def remove_file(self, project_id: UUID, file_path: str) -> bool:
        """Remove file from project."""
        try:
            result = await self.session.execute(
                delete(ProjectFile).where(
                    and_(
                        ProjectFile.project_id == project_id,
                        ProjectFile.file_path == file_path
                    )
                )
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Removed file {file_path} from project {project_id}")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to remove file from project {project_id}: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to remove file: {str(e)}")
    
    async def add_tag(self, project_id: UUID, tag: str) -> bool:
        """Add tag to project."""
        try:
            # Check if project exists
            project_query = select(MangaProject).where(MangaProject.project_id == project_id)
            result = await self.session.execute(project_query)
            db_project = result.scalar_one_or_none()
            
            if not db_project:
                raise ProjectNotFoundError(f"Project {project_id} not found")
            
            # Check if tag already exists
            existing_tag_query = select(ProjectTag).where(
                and_(
                    ProjectTag.project_id == project_id,
                    ProjectTag.tag == tag
                )
            )
            result = await self.session.execute(existing_tag_query)
            existing_tag = result.scalar_one_or_none()
            
            if existing_tag:
                return True  # Tag already exists
            
            # Add tag
            project_tag = ProjectTag(
                project_id=project_id,
                tag=tag,
                created_at=datetime.utcnow()
            )
            
            self.session.add(project_tag)
            await self.session.commit()
            
            logger.info(f"Added tag '{tag}' to project {project_id}")
            return True
            
        except ProjectNotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to add tag to project {project_id}: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to add tag: {str(e)}")
    
    async def remove_tag(self, project_id: UUID, tag: str) -> bool:
        """Remove tag from project."""
        try:
            result = await self.session.execute(
                delete(ProjectTag).where(
                    and_(
                        ProjectTag.project_id == project_id,
                        ProjectTag.tag == tag
                    )
                )
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Removed tag '{tag}' from project {project_id}")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to remove tag from project {project_id}: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to remove tag: {str(e)}")
    
    async def get_expired_projects(
        self,
        before_date: Optional[datetime] = None
    ) -> List[MangaProjectEntity]:
        """Get expired projects."""
        try:
            cutoff_date = before_date or datetime.utcnow()
            
            query = select(MangaProject).where(
                and_(
                    MangaProject.expires_at.is_not(None),
                    MangaProject.expires_at <= cutoff_date,
                    MangaProject.status != "archived"
                )
            ).order_by(MangaProject.expires_at)
            
            result = await self.session.execute(query)
            db_projects = result.scalars().all()
            
            return [self._to_entity(p) for p in db_projects]
            
        except Exception as e:
            logger.error(f"Failed to get expired projects: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to get expired projects: {str(e)}")
    
    async def archive_project(self, project_id: UUID) -> bool:
        """Archive project."""
        try:
            result = await self.session.execute(
                update(MangaProject)
                .where(MangaProject.project_id == project_id)
                .values(status="archived", updated_at=datetime.utcnow())
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Archived project {project_id}")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to archive project {project_id}: {str(e)}")
            raise MangaProjectRepositoryError(f"Failed to archive project: {str(e)}")
    
    def _to_entity(self, db_project: MangaProject) -> MangaProjectEntity:
        """Convert database model to domain entity."""
        return MangaProjectEntity(
            project_id=db_project.project_id,
            user_id=db_project.user_id,
            title=db_project.title,
            status=db_project.status,
            metadata=db_project.metadata,
            settings=db_project.settings,
            total_pages=db_project.total_pages,
            created_at=db_project.created_at,
            updated_at=db_project.updated_at,
            expires_at=db_project.expires_at
        )