from __future__ import annotations

import math
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.manga_project import MangaProject
from app.db.models.user_account import UserAccount
from app.api.schemas.manga import MangaProjectItem, MangaProjectDetailResponse, Pagination


class MangaProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_projects(
        self,
        user: UserAccount,
        page: int = 1,
        limit: int = 20,
        sort: str = "created_at",
        order: str = "desc",
        status_filter: Optional[str] = None,
    ) -> tuple[List[MangaProjectItem], Pagination]:
        """Get paginated list of user's manga projects"""

        # Validate parameters
        page = max(1, page)
        limit = min(max(1, limit), 100)

        # Build base query
        query = select(MangaProject).where(MangaProject.user_id == user.id)

        # Apply status filter
        if status_filter and status_filter != "all":
            query = query.where(MangaProject.status == status_filter)

        # Apply sorting
        sort_column = getattr(MangaProject, sort, MangaProject.created_at)
        if order.lower() == "asc":
            query = query.order_by(sort_column)
        else:
            query = query.order_by(desc(sort_column))

        # Get total count
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        projects = result.scalars().all()

        # Convert to response items
        items = [
            MangaProjectItem(
                manga_id=str(project.id),
                title=project.title,
                status=project.status,
                pages=project.total_pages,
                style=project.style,
                description=project.description,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
            for project in projects
        ]

        # Calculate pagination info
        total_pages = math.ceil(total / limit) if total > 0 else 1
        pagination = Pagination(
            page=page,
            limit=limit,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

        return items, pagination

    async def get_project_detail(
        self,
        project_id: UUID,
        user: UserAccount
    ) -> Optional[MangaProjectDetailResponse]:
        """Get detailed information about a specific manga project"""

        query = (
            select(MangaProject)
            .options(selectinload(MangaProject.session))
            .where(
                and_(
                    MangaProject.id == project_id,
                    MangaProject.user_id == user.id
                )
            )
        )

        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            return None

        # Build files information from assets (if any)
        files = {}
        if project.assets:
            files = {
                "assets": [
                    {
                        "id": str(asset.id),
                        "file_type": asset.file_type,
                        "file_url": asset.file_url,
                        "metadata": asset.metadata,
                    }
                    for asset in project.assets
                ]
            }

        return MangaProjectDetailResponse(
            manga_id=str(project.id),
            title=project.title,
            status=project.status,
            description=project.description,
            metadata=project.project_metadata,
            settings=project.settings,
            total_pages=project.total_pages,
            style=project.style,
            visibility=project.visibility,
            expires_at=project.expires_at,
            files=files,
            created_at=project.created_at,
            updated_at=project.updated_at,
            user_id=str(project.user_id) if project.user_id else None,
            session_id=str(project.session_id) if project.session_id else None,
        )

    async def project_exists(self, project_id: UUID, user: UserAccount) -> bool:
        """Check if a project exists and belongs to the user"""
        query = select(func.count()).where(
            and_(
                MangaProject.id == project_id,
                MangaProject.user_id == user.id
            )
        )
        result = await self.db.execute(query)
        return result.scalar() > 0