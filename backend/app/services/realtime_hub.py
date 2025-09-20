from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Dict, List, Optional
from uuid import UUID


class SessionRealtimeHub:
    def __init__(self) -> None:
        self._subscribers: Dict[UUID, List[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._history: Dict[UUID, List[dict[str, Any]]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._max_history = 50

    async def subscribe(self, request_id: UUID) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        async with self._lock:
            self._subscribers[request_id].append(queue)
            history = list(self._history.get(request_id, []))
        for event in history:
            await queue.put(event)
        return queue

    async def unsubscribe(self, request_id: UUID, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(request_id)
            if not subscribers:
                return
            try:
                subscribers.remove(queue)
            except ValueError:
                pass
            if not subscribers:
                self._subscribers.pop(request_id, None)
                self._history.pop(request_id, None)

    async def publish(self, request_id: UUID, event: dict[str, Any]) -> None:
        async with self._lock:
            subscribers = list(self._subscribers.get(request_id, []))
            history = self._history[request_id]
            history.append(event)
            if len(history) > self._max_history:
                history.pop(0)
        await asyncio.gather(*(subscriber.put(event) for subscriber in subscribers), return_exceptions=True)

    # HITL-specific helper methods
    async def publish_phase_progress(
        self,
        request_id: UUID,
        phase: int,
        status: str,
        progress_percentage: Optional[float] = None,
        **data: Any
    ) -> None:
        """Publish phase progress update"""
        event = build_phase_progress_event(
            session_id=str(request_id),
            phase=phase,
            status=status,
            progress_percentage=progress_percentage,
            **data
        )
        await self.publish(request_id, event)

    async def publish_feedback_request(
        self,
        request_id: UUID,
        phase: int,
        preview_data: Dict[str, Any],
        timeout_seconds: int,
        feedback_options: List[Dict[str, Any]],
        **data: Any
    ) -> None:
        """Publish feedback request to user"""
        event = build_feedback_request_event(
            session_id=str(request_id),
            phase=phase,
            preview_data=preview_data,
            timeout_seconds=timeout_seconds,
            feedback_options=feedback_options,
            **data
        )
        await self.publish(request_id, event)

    async def publish_session_status(
        self,
        request_id: UUID,
        status: str,
        current_phase: Optional[int] = None,
        waiting_for_feedback: bool = False,
        **data: Any
    ) -> None:
        """Publish session status using frontend-compatible phase events"""
        if waiting_for_feedback and current_phase:
            # Use phaseProgress with waiting_feedback status to signal feedback state
            await self.publish_phase_progress(
                request_id=request_id,
                phase=current_phase,
                status="waiting_feedback",
                progress_percentage=None  # No progress during feedback waiting
            )
        # Note: Other status changes are handled by regular phase events

    async def publish_feedback_timeout(
        self,
        request_id: UUID,
        phase: int,
        action_taken: str,
        **data: Any
    ) -> None:
        """Publish feedback timeout using frontend-compatible phase events"""
        # Signal timeout by updating phase status back to processing
        await self.publish_phase_progress(
            request_id=request_id,
            phase=phase,
            status="processing",
            progress_percentage=None,
            timeout_action=action_taken  # Additional context
        )

        # Also log the timeout as a system message
        from datetime import datetime
        await self.publish(
            request_id,
            {
                "type": "log",
                "data": {
                    "level": "info",
                    "message": f"フェーズ{phase}のフィードバックがタイムアウトしました。自動的に{action_taken}で続行します。",
                    "source": "system",
                    "phaseId": phase,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )

    async def publish_session_complete(
        self,
        request_id: UUID,
        final_status: str,
        results_url: Optional[str] = None,
        results: Optional[List[Dict[str, Any]]] = None,
        **data: Any
    ) -> None:
        """Publish session completion notification"""
        event = build_session_complete_event(
            session_id=str(request_id),
            final_status=final_status,
            results_url=results_url,
            results=results,
            **data
        )
        await self.publish(request_id, event)

    async def publish_error(
        self,
        request_id: UUID,
        error_code: str,
        error_message: str,
        severity: str = "medium",
        **data: Any
    ) -> None:
        """Publish error notification"""
        event = build_error_event(
            session_id=str(request_id),
            error_code=error_code,
            error_message=error_message,
            severity=severity,
            **data
        )
        await self.publish(request_id, event)


def build_event(event_type: str, **data: Any) -> dict[str, Any]:
    return {"type": event_type, "data": data}


# HITL-specific event builders
def build_phase_progress_event(
    session_id: str,
    phase: int,
    status: str,
    progress_percentage: Optional[float] = None,
    **data: Any
) -> dict[str, Any]:
    """Build phase progress event with backward compatibility"""
    event_data = {
        "phase": phase,
        "status": status,
        **data
    }

    # Maintain backward compatibility: use 'progress' field name
    if progress_percentage is not None:
        event_data["progress"] = int(progress_percentage)

    return {
        "type": "phase_progress",
        "data": event_data
    }


def build_feedback_request_event(
    session_id: str,
    phase: int,
    preview_data: Dict[str, Any],
    timeout_seconds: int,
    feedback_options: List[Dict[str, Any]],
    **data: Any
) -> dict[str, Any]:
    """Build feedback request event matching frontend WebSocketStore implementation"""
    return {
        "type": "feedbackRequest",
        "data": {
            "phaseId": phase,
            "preview": preview_data,
            "timeout": timeout_seconds
        }
    }


def build_session_status_event(
    session_id: str,
    status: str,
    current_phase: Optional[int] = None,
    waiting_for_feedback: bool = False,
    **data: Any
) -> dict[str, Any]:
    """Build session status event compatible with frontend"""
    return {
        "type": "sessionStatus",
        "data": {
            "status": status,
            "currentPhase": current_phase,
            "waitingForFeedback": waiting_for_feedback,
            "sessionId": session_id,
            **data
        }
    }


def build_feedback_timeout_event(
    session_id: str,
    phase: int,
    action_taken: str,
    **data: Any
) -> dict[str, Any]:
    """Build feedback timeout event compatible with frontend"""
    return {
        "type": "feedbackTimeout",
        "data": {
            "phaseId": phase,
            "actionTaken": action_taken,
            "sessionId": session_id,
            **data
        }
    }


def build_session_complete_event(
    session_id: str,
    final_status: str,
    results_url: Optional[str] = None,
    results: Optional[List[Dict[str, Any]]] = None,
    **data: Any
) -> dict[str, Any]:
    """Build session completion event matching frontend WebSocketStore implementation"""
    event_data = {
        "results": results or []
    }

    # sessionId is optional in frontend implementation
    if session_id:
        event_data["sessionId"] = session_id

    return {
        "type": "sessionComplete",
        "data": event_data
    }


def build_error_event(
    session_id: str,
    error_code: str,
    error_message: str,
    severity: str = "medium",
    **data: Any
) -> dict[str, Any]:
    """Build error event compatible with frontend"""
    return {
        "type": "error",
        "data": {
            "errorCode": error_code,
            "errorMessage": error_message,
            "severity": severity,
            "sessionId": session_id,
            **data
        }
    }


realtime_hub = SessionRealtimeHub()
