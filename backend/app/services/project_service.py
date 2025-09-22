from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import MangaAsset, MangaAssetType, MangaProject, UserAccount


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_projects(
        self,
        user: UserAccount,
        *,
        page: int,
        limit: int,
        sort: str,
        order: str,
        status_filter: Optional[str],
    ) -> Tuple[List[MangaProject], Dict[str, int]]:
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20

        query = select(MangaProject).options(selectinload(MangaProject.assets)).where(MangaProject.user_id == user.id)
        count_query = select(func.count()).select_from(MangaProject).where(MangaProject.user_id == user.id)

        if status_filter and status_filter != "all":
            query = query.where(MangaProject.status == status_filter)
            count_query = count_query.where(MangaProject.status == status_filter)

        sort_column = self._resolve_sort_column(sort)
        ordering = desc(sort_column) if order == "desc" else asc(sort_column)
        query = query.order_by(ordering).offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(query)
        projects = result.scalars().all()

        total_result = await self.db.execute(count_query)
        total_items = total_result.scalar_one()
        total_pages = max(1, (total_items + limit - 1) // limit)

        return projects, {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": total_pages,
        }

    async def get_project(self, user: UserAccount, project_id: UUID) -> MangaProject:
        project = await self._get_user_project(user, project_id)
        return project

    async def update_project(
        self,
        user: UserAccount,
        project_id: UUID,
        updates: Dict[str, object],
    ) -> MangaProject:
        project = await self._get_user_project(user, project_id)
        allowed_fields = {"title", "description", "visibility"}
        modified_fields = []
        for field, value in updates.items():
            if field in allowed_fields and value is not None:
                setattr(project, field, value)
                modified_fields.append(field)
        if not modified_fields:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no_fields_updated")
        return project

    async def delete_project(self, user: UserAccount, project_id: UUID) -> None:
        project = await self._get_user_project(user, project_id)
        await self.db.delete(project)

    async def _get_user_project(self, user: UserAccount, project_id: UUID) -> MangaProject:
        result = await self.db.execute(
            select(MangaProject).options(selectinload(MangaProject.assets)).where(MangaProject.id == project_id, MangaProject.user_id == user.id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project_not_found")
        return project

    @staticmethod
    def _resolve_sort_column(sort: str):
        if sort == "updated_at":
            return MangaProject.updated_at
        if sort == "title":
            return MangaProject.title
        return MangaProject.created_at

    @staticmethod
    def extract_thumbnail(project: MangaProject) -> Optional[str]:
        for asset in project.assets:
            if asset.asset_type == MangaAssetType.THUMBNAIL:
                return asset.signed_url
        return None

    @staticmethod
    def aggregate_files(project: MangaProject) -> Dict[str, object]:
        files: Dict[str, object] = {"pdf_url": None, "webp_urls": [], "thumbnail_url": None}
        for asset in project.assets:
            if asset.asset_type == MangaAssetType.PDF:
                files["pdf_url"] = asset.signed_url
            elif asset.asset_type == MangaAssetType.WEBP:
                files.setdefault("webp_urls", []).append(asset.signed_url)
            elif asset.asset_type == MangaAssetType.THUMBNAIL:
                files["thumbnail_url"] = asset.signed_url
        return files
