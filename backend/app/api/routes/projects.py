from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.project import (
    MangaProjectDetailResponse,
    MangaProjectItem,
    MangaProjectListResponse,
    MangaProjectUpdateRequest,
    MangaProjectUpdateResponse,
    Pagination,
)
from app.dependencies import get_db_session
from app.dependencies.auth import get_current_user
from app.db.models import MangaProject, UserAccount
from app.services.project_service import ProjectService


router = APIRouter(prefix="/api/v1/manga", tags=["manga-projects"])


@router.get("", response_model=MangaProjectListResponse)
async def list_projects(
    page: int = 1,
    limit: int = 20,
    sort: str = "created_at",
    order: str = "desc",
    status_filter: str = "all",
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MangaProjectListResponse:
    service = ProjectService(db)
    projects, meta = await service.list_projects(
        current_user,
        page=page,
        limit=limit,
        sort=sort,
        order=order,
        status_filter=status_filter,
    )

    items: List[MangaProjectItem] = []
    for project in projects:
        thumbnail_url = ProjectService.extract_thumbnail(project)
        size_bytes = sum(int(asset.size_bytes) for asset in project.assets if asset.size_bytes)
        items.append(
            MangaProjectItem(
                manga_id=project.id,
                title=project.title,
                status=project.status,
                pages=project.total_pages,
                style=project.style,
                created_at=project.created_at,
                updated_at=project.updated_at,
                thumbnail_url=thumbnail_url,
                size_bytes=size_bytes or None,
            )
        )

    pagination = Pagination(
        page=meta["page"],
        limit=meta["limit"],
        total_items=meta["total_items"],
        total_pages=meta["total_pages"],
        has_next=meta["page"] < meta["total_pages"],
        has_previous=meta["page"] > 1,
    )

    return MangaProjectListResponse(items=items, pagination=pagination)


@router.get("/{manga_id}", response_model=MangaProjectDetailResponse)
async def get_project_detail(
    manga_id: UUID,
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MangaProjectDetailResponse:
    service = ProjectService(db)
    project = await service.get_project(current_user, manga_id)
    files = service.aggregate_files(project)
    metadata = project.project_metadata or {}
    if project.settings:
        metadata = {"settings": project.settings, **metadata}
    return MangaProjectDetailResponse(
        manga_id=project.id,
        title=project.title,
        status=project.status,
        metadata=metadata,
        files=files,
        created_at=project.created_at,
        updated_at=project.updated_at,
        expires_at=project.expires_at,
    )


@router.put("/{manga_id}", response_model=MangaProjectUpdateResponse)
async def update_project(
    manga_id: UUID,
    payload: MangaProjectUpdateRequest,
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MangaProjectUpdateResponse:
    service = ProjectService(db)
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no_fields_provided")
    project = await service.update_project(current_user, manga_id, updates)
    return MangaProjectUpdateResponse(
        manga_id=project.id,
        updated_fields=list(updates.keys()),
        updated_at=project.updated_at,
    )


@router.delete("/{manga_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    manga_id: UUID,
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    service = ProjectService(db)
    await service.delete_project(current_user, manga_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
