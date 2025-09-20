from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
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
