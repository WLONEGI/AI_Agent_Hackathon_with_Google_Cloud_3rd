from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Request Schemas
class UserFeedbackRequest(BaseModel):
    """Request schema for user feedback submission"""
    phase: int = Field(..., ge=1, le=7, description="Phase number (1-7)")
    feedback_type: Literal["approval", "modification", "skip"] = Field(..., description="Type of feedback")
    selected_options: Optional[List[str]] = Field(default=None, description="Selected feedback option keys")
    natural_language_input: Optional[str] = Field(default=None, max_length=2000, description="Free text feedback")
    user_satisfaction_score: Optional[float] = Field(default=None, ge=1.0, le=5.0, description="User satisfaction rating (1-5)")
    processing_time_ms: Optional[int] = Field(default=None, ge=0, description="Time taken to provide feedback in milliseconds")


class FeedbackOptionsQuery(BaseModel):
    """Query parameters for feedback options"""
    category: Optional[str] = Field(default=None, description="Filter by option category")
    only_active: bool = Field(default=True, description="Only return active options")


# Response Schemas
class FeedbackOptionResponse(BaseModel):
    """Response schema for feedback option"""
    id: str
    phase: int
    option_key: str
    option_label: str
    option_description: Optional[str]
    option_category: Optional[str]
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


class FeedbackOptionsResponse(BaseModel):
    """Response schema for feedback options list"""
    phase: int
    options: List[FeedbackOptionResponse]
    total_count: int


class PhasePreviewResponse(BaseModel):
    """Response schema for phase preview"""
    session_id: str
    phase: int
    preview_data: Dict[str, Any]
    quality_score: Optional[float]
    generated_at: datetime
    feedback_options: List[FeedbackOptionResponse]

    class Config:
        from_attributes = True


class FeedbackStateResponse(BaseModel):
    """Response schema for feedback state"""
    session_id: str
    phase: int
    state: str  # waiting, received, processing, completed, timeout
    remaining_time_seconds: Optional[int]
    feedback_started_at: datetime
    feedback_timeout_at: Optional[datetime]
    feedback_received_at: Optional[datetime]
    preview_data: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission"""
    success: bool
    message: str
    processing_status: str
    estimated_completion_time: Optional[datetime] = None
    feedback_id: Optional[str] = None


class UserFeedbackHistoryResponse(BaseModel):
    """Response schema for user feedback history item"""
    id: str
    session_id: str
    phase: int
    feedback_type: str
    feedback_data: Optional[Dict[str, Any]]
    user_satisfaction_score: Optional[float]
    natural_language_input: Optional[str]
    selected_options: Optional[List[str]]
    processing_time_ms: Optional[int]
    created_at: datetime
    processing_completed_at: Optional[datetime]
    is_processed: bool

    class Config:
        from_attributes = True


class FeedbackHistoryResponse(BaseModel):
    """Response schema for feedback history list"""
    session_id: str
    feedback_entries: List[UserFeedbackHistoryResponse]
    total_count: int


class HITLStatusResponse(BaseModel):
    """Response schema for HITL system status"""
    hitl_enabled: bool
    feedback_timeout_minutes: int
    max_retry_attempts: int
    default_quality_threshold: float
    active_sessions_count: int
    waiting_feedback_count: int


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None


# Internal/Helper Schemas
class FeedbackProcessingResult(BaseModel):
    """Internal schema for feedback processing results"""
    feedback_id: str
    processing_success: bool
    quality_improvement: Optional[float] = None
    processing_time_ms: int
    error_message: Optional[str] = None


class HITLSessionMetrics(BaseModel):
    """Schema for HITL session metrics"""
    session_id: str
    total_feedback_count: int
    average_satisfaction_score: Optional[float]
    total_processing_time_ms: int
    completion_rate: float  # percentage of phases completed vs started


class PhaseFeedbackSummary(BaseModel):
    """Schema for phase feedback summary"""
    phase: int
    total_feedback_count: int
    approval_rate: float
    modification_rate: float
    skip_rate: float
    average_satisfaction_score: Optional[float]
    most_common_options: List[str]