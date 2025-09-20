from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


# Base WebSocket Message Structure
class WebSocketMessage(BaseModel):
    """Base WebSocket message structure"""
    type: str = Field(..., description="Message type identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    session_id: Optional[str] = Field(default=None, description="Session identifier")


# Outbound Messages (Server -> Client)
class PhaseProgressMessage(WebSocketMessage):
    """Phase progress update message"""
    type: Literal["phase_progress"] = "phase_progress"
    data: Dict[str, Any] = Field(..., description="Phase progress data")
    phase: int = Field(..., ge=1, le=7, description="Current phase number")
    status: str = Field(..., description="Phase status")
    progress_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class FeedbackRequestMessage(WebSocketMessage):
    """Request feedback from user"""
    type: Literal["feedback_request"] = "feedback_request"
    data: Dict[str, Any] = Field(..., description="Feedback request data")
    phase: int = Field(..., ge=1, le=7, description="Phase requiring feedback")
    preview_data: Dict[str, Any] = Field(..., description="Phase preview for user review")
    timeout_seconds: int = Field(..., ge=1, description="Feedback timeout in seconds")
    feedback_options: List[Dict[str, Any]] = Field(default_factory=list, description="Available feedback options")


class SessionStatusMessage(WebSocketMessage):
    """Session status update message"""
    type: Literal["session_status"] = "session_status"
    data: Dict[str, Any] = Field(..., description="Session status data")
    status: str = Field(..., description="Session status")
    current_phase: Optional[int] = Field(default=None)
    waiting_for_feedback: bool = Field(default=False)


class ErrorMessage(WebSocketMessage):
    """Error notification message"""
    type: Literal["error"] = "error"
    data: Dict[str, Any] = Field(..., description="Error details")
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    severity: Literal["low", "medium", "high", "critical"] = Field(default="medium")


class FeedbackTimeoutMessage(WebSocketMessage):
    """Feedback timeout notification"""
    type: Literal["feedback_timeout"] = "feedback_timeout"
    data: Dict[str, Any] = Field(..., description="Timeout details")
    phase: int = Field(..., ge=1, le=7, description="Phase that timed out")
    action_taken: str = Field(..., description="Auto-action taken after timeout")


class SessionCompleteMessage(WebSocketMessage):
    """Session completion notification"""
    type: Literal["session_complete"] = "session_complete"
    data: Dict[str, Any] = Field(..., description="Completion details")
    final_status: str = Field(..., description="Final session status")
    results_url: Optional[str] = Field(default=None, description="URL to view results")


# Inbound Messages (Client -> Server)
class UserFeedbackMessage(WebSocketMessage):
    """User feedback submission"""
    type: Literal["user_feedback"] = "user_feedback"
    data: Dict[str, Any] = Field(..., description="User feedback data")
    phase: int = Field(..., ge=1, le=7, description="Phase number")
    feedback_type: Literal["approval", "modification", "skip"] = Field(..., description="Type of feedback")
    selected_options: Optional[List[str]] = Field(default=None, description="Selected feedback option keys")
    natural_language_input: Optional[str] = Field(default=None, max_length=2000, description="Free text feedback")
    user_satisfaction_score: Optional[float] = Field(default=None, ge=1.0, le=5.0, description="User satisfaction rating")
    processing_time_ms: Optional[int] = Field(default=None, ge=0, description="Time taken to provide feedback")


class KeepAliveMessage(WebSocketMessage):
    """Keep connection alive"""
    type: Literal["ping"] = "ping"
    data: Dict[str, Any] = Field(default_factory=dict)


class SubscriptionMessage(WebSocketMessage):
    """Subscription management"""
    type: Literal["subscribe", "unsubscribe"] = Field(..., description="Subscription action")
    data: Dict[str, Any] = Field(..., description="Subscription details")
    channels: List[str] = Field(..., description="Channels to subscribe/unsubscribe")


# Union types for message parsing
OutboundMessage = Union[
    PhaseProgressMessage,
    FeedbackRequestMessage,
    SessionStatusMessage,
    ErrorMessage,
    FeedbackTimeoutMessage,
    SessionCompleteMessage
]

InboundMessage = Union[
    UserFeedbackMessage,
    KeepAliveMessage,
    SubscriptionMessage
]

AnyMessage = Union[OutboundMessage, InboundMessage]


# Message builder helpers
def build_phase_progress_message(
    session_id: str,
    phase: int,
    status: str,
    progress_percentage: Optional[float] = None,
    **data: Any
) -> PhaseProgressMessage:
    """Build a phase progress message"""
    return PhaseProgressMessage(
        session_id=session_id,
        phase=phase,
        status=status,
        progress_percentage=progress_percentage,
        data=data
    )


def build_feedback_request_message(
    session_id: str,
    phase: int,
    preview_data: Dict[str, Any],
    timeout_seconds: int,
    feedback_options: List[Dict[str, Any]],
    **data: Any
) -> FeedbackRequestMessage:
    """Build a feedback request message"""
    return FeedbackRequestMessage(
        session_id=session_id,
        phase=phase,
        preview_data=preview_data,
        timeout_seconds=timeout_seconds,
        feedback_options=feedback_options,
        data=data
    )


def build_session_status_message(
    session_id: str,
    status: str,
    current_phase: Optional[int] = None,
    waiting_for_feedback: bool = False,
    **data: Any
) -> SessionStatusMessage:
    """Build a session status message"""
    return SessionStatusMessage(
        session_id=session_id,
        status=status,
        current_phase=current_phase,
        waiting_for_feedback=waiting_for_feedback,
        data=data
    )


def build_error_message(
    session_id: str,
    error_code: str,
    error_message: str,
    severity: Literal["low", "medium", "high", "critical"] = "medium",
    **data: Any
) -> ErrorMessage:
    """Build an error message"""
    return ErrorMessage(
        session_id=session_id,
        error_code=error_code,
        error_message=error_message,
        severity=severity,
        data=data
    )