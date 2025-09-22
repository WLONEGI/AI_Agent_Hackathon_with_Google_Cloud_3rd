from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackMode(BaseModel):
    enabled: bool = True
    timeout_minutes: int = Field(default=30, ge=1, le=120)
    allow_skip: bool = True


class GenerateOptions(BaseModel):
    priority: str = Field(default="normal")
    webhook_url: Optional[str] = None
    auto_publish: Optional[bool] = None


class GenerateRequest(BaseModel):
    title: str
    text: str = Field(min_length=10, max_length=50000)
    ai_auto_settings: bool = True
    feedback_mode: FeedbackMode = Field(default_factory=FeedbackMode)
    options: GenerateOptions = Field(default_factory=GenerateOptions)


class GenerateResponse(BaseModel):
    request_id: str  # Changed from UUID to str for frontend compatibility
    status: str = "queued"
    estimated_completion_time: Optional[datetime] = None
    expected_duration_minutes: Optional[int] = 8
    status_url: str
    websocket_channel: Optional[str] = None
    message: Optional[str] = None


class SessionStatusResponse(BaseModel):
    session_id: str  # Changed from UUID to str for frontend compatibility
    request_id: str  # Changed from UUID to str for frontend compatibility
    status: str
    current_phase: Optional[int] = None
    updated_at: datetime
    project_id: Optional[str] = None  # Changed from UUID to str for frontend compatibility


class SessionDetailResponse(BaseModel):
    session_id: str  # Changed from UUID to str for frontend compatibility
    request_id: str  # Changed from UUID to str for frontend compatibility
    status: str
    current_phase: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    retry_count: int
    phase_results: list[dict]
    preview_versions: list[dict]
    project_id: Optional[str] = None  # Changed from UUID to str for frontend compatibility


class FeedbackPayload(BaseModel):
    feedback_type: str = Field(default="natural_language")
    content: dict


class FeedbackRequest(BaseModel):
    phase: int
    payload: FeedbackPayload


# New schemas for chat and messaging
class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    message_type: str = Field(default="user")
    phase: Optional[int] = None
    metadata: Optional[dict] = None


class MessageResponse(BaseModel):
    id: str
    session_id: str
    message_type: str
    content: str
    phase: Optional[int]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime


class MessagesListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    has_more: bool


class PhasePreviewUpdate(BaseModel):
    preview_type: str = Field(default="text")
    content: Optional[str] = None
    image_url: Optional[str] = None
    document_url: Optional[str] = None
    progress: int = Field(ge=0, le=100)
    status: str = Field(default="processing")
    metadata: Optional[dict] = None


class PhasePreviewResponse(BaseModel):
    id: str
    session_id: str
    phase_number: int
    preview_type: str
    content: Optional[str]
    image_url: Optional[str]
    document_url: Optional[str]
    progress: int
    status: str
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime


class SessionEventResponse(BaseModel):
    id: str
    session_id: str
    event_type: str
    event_data: dict
    created_at: datetime


# Manga Project schemas
class MangaProjectItem(BaseModel):
    manga_id: str
    title: str
    status: str
    pages: Optional[int] = None
    style: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Pagination(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class MangaProjectListResponse(BaseModel):
    items: List[MangaProjectItem]
    pagination: Pagination


class MangaProjectDetailResponse(BaseModel):
    manga_id: str
    title: str
    status: str
    description: Optional[str] = None
    metadata: Optional[dict] = None
    settings: Optional[dict] = None
    total_pages: Optional[int] = None
    style: Optional[str] = None
    visibility: str
    expires_at: Optional[datetime] = None
    files: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None


# Error handling schemas
class PhaseErrorDetailResponse(BaseModel):
    phase_id: int
    phase_name: str
    error_code: str
    error_message: str
    error_details: Optional[str] = None
    timestamp: datetime
    retryable: bool
    retry_count: int
    suggested_actions: List[str]


class PhaseRetryRequest(BaseModel):
    force_retry: bool = False
    reset_feedback: bool = True


class PhaseRetryResponse(BaseModel):
    phase_id: int
    status: str
    message: str
    retry_started: bool
    estimated_completion_time: Optional[datetime] = None
