from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Pagination(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class MangaProjectItem(BaseModel):
    manga_id: UUID
    title: str
    status: str
    pages: Optional[int]
    style: Optional[str]
    created_at: datetime
    updated_at: datetime
    thumbnail_url: Optional[str]
    size_bytes: Optional[int]


class MangaProjectListResponse(BaseModel):
    items: List[MangaProjectItem]
    pagination: Pagination


class MangaProjectDetailResponse(BaseModel):
    manga_id: UUID
    title: str
    status: str
    metadata: dict
    files: dict
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]


class MangaProjectUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    visibility: Optional[str] = Field(default=None, pattern="^(private|public|unlisted)$")


class MangaProjectUpdateResponse(BaseModel):
    manga_id: UUID
    updated_fields: list[str]
    updated_at: datetime
