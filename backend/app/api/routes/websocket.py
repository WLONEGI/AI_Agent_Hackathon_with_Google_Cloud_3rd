from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.websocket import (
    InboundMessage,
    UserFeedbackMessage,
    KeepAliveMessage,
    build_error_message,
)
from app.core.settings import get_settings
from app.dependencies import get_db_session
from app.services.hitl_service import HITLService
from app.services.realtime_hub import realtime_hub

logger = logging.getLogger(__name__)
router = APIRouter()


async def handle_user_feedback(
    message: UserFeedbackMessage,
    request_id: UUID,
    websocket: WebSocket,
    db: AsyncSession
) -> None:
    """Handle user feedback message"""
    try:
        hitl_service = HITLService(db)

        # Submit feedback through HITL service
        result = await hitl_service.submit_feedback(
            session_id=request_id,
            phase=message.phase,
            feedback_type=message.feedback_type,
            selected_options=message.selected_options,
            natural_language_input=message.natural_language_input,
            user_satisfaction_score=message.user_satisfaction_score,
            processing_time_ms=message.processing_time_ms,
        )

        # Send success confirmation compatible with frontend format
        response = {
            "type": "feedbackReceived",
            "data": {
                "feedbackId": result.feedback_id,
                "processingSuccess": result.processing_success,
                "message": "Feedback received successfully",
                "timestamp": message.timestamp.isoformat()
            }
        }
        await websocket.send_json(response)

        logger.info(f"Processed user feedback: session={request_id}, phase={message.phase}")

    except Exception as e:
        logger.exception(f"Error handling user feedback: {e}")

        # Send error response
        error_msg = build_error_message(
            session_id=str(request_id),
            error_code="FEEDBACK_ERROR",
            error_message=f"Failed to process feedback: {str(e)}",
            severity="high"
        )
        await websocket.send_json(error_msg.dict())


async def handle_keep_alive(
    message: KeepAliveMessage,
    request_id: UUID,
    websocket: WebSocket
) -> None:
    """Handle keep-alive ping"""
    response = {
        "type": "pong",
        "data": {
            "timestamp": message.timestamp.isoformat(),
            "sessionId": str(request_id)
        }
    }
    await websocket.send_json(response)


async def process_inbound_message(
    raw_message: Dict[str, Any],
    request_id: UUID,
    websocket: WebSocket,
    db: AsyncSession
) -> None:
    """Process incoming message from client"""
    try:
        message_type = raw_message.get("type")

        if message_type == "user_feedback":
            message = UserFeedbackMessage(**raw_message)
            await handle_user_feedback(message, request_id, websocket, db)

        elif message_type == "ping":
            message = KeepAliveMessage(**raw_message)
            await handle_keep_alive(message, request_id, websocket)

        else:
            logger.warning(f"Unknown message type: {message_type}")
            error_msg = build_error_message(
                session_id=str(request_id),
                error_code="UNKNOWN_MESSAGE_TYPE",
                error_message=f"Unknown message type: {message_type}",
                severity="low"
            )
            await websocket.send_json(error_msg.dict())

    except ValidationError as e:
        logger.error(f"Message validation error: {e}")
        error_msg = build_error_message(
            session_id=str(request_id),
            error_code="VALIDATION_ERROR",
            error_message=f"Invalid message format: {str(e)}",
            severity="medium"
        )
        await websocket.send_json(error_msg.dict())

    except Exception as e:
        logger.exception(f"Error processing inbound message: {e}")
        error_msg = build_error_message(
            session_id=str(request_id),
            error_code="PROCESSING_ERROR",
            error_message=f"Failed to process message: {str(e)}",
            severity="high"
        )
        await websocket.send_json(error_msg.dict())


@router.websocket("/ws/session/{request_id}")
async def websocket_session_endpoint(
    websocket: WebSocket,
    request_id: UUID,
    token: str | None = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Enhanced WebSocket endpoint with bidirectional HITL support"""
    settings = get_settings()

    # Basic token gate: allow empty tokens in development environments
    if settings.app_env != "development" and not token:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    queue = await realtime_hub.subscribe(request_id)

    async def send_outbound_messages():
        """Task for sending server messages to client"""
        try:
            while True:
                event = await queue.get()
                await websocket.send_json(event)
        except Exception as e:
            logger.error(f"Error in outbound message handler: {e}")

    async def receive_inbound_messages():
        """Task for receiving client messages"""
        try:
            while True:
                raw_data = await websocket.receive_text()
                try:
                    message_data = json.loads(raw_data)
                    await process_inbound_message(message_data, request_id, websocket, db)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    error_msg = build_error_message(
                        session_id=str(request_id),
                        error_code="INVALID_JSON",
                        error_message="Invalid JSON format",
                        severity="medium"
                    )
                    await websocket.send_json(error_msg.dict())
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session: {request_id}")
        except Exception as e:
            logger.exception(f"Error in inbound message handler: {e}")

    # Run both message handlers concurrently
    try:
        await asyncio.gather(
            send_outbound_messages(),
            receive_inbound_messages(),
            return_exceptions=True
        )
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for session: {request_id}")
    except Exception as e:
        logger.exception(f"WebSocket error for session {request_id}: {e}")
    finally:
        await realtime_hub.unsubscribe(request_id, queue)
