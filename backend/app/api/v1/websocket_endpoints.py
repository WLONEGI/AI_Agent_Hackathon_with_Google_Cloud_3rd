"""WebSocket endpoints for real-time HITL communication - API v1."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import json
import jwt
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.services.websocket_service import WebSocketService
from app.core.config import settings

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def authenticate_websocket_user(token: str, db: AsyncSession) -> Optional[User]:
    """Authenticate user via WebSocket token using shared JWT logic."""
    
    try:
        # Use shared JWT verification from security module
        from app.api.v1.security import verify_token
        payload = verify_token(token)
        
        user_id: str = payload.get("sub")
        if not user_id:
            return None
            
        # Get user from database
        user = await db.get(User, user_id)
        return user if user and user.is_active else None
        
    except Exception:
        return None


@router.websocket("/generation/{session_id}")
async def websocket_generation_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time generation communication (Design Document Compliant).
    
    Endpoint: WSS /ws/generation/{session_id}?token={jwt_token}
    
    Protocol:
    - Authentication via query parameter 'token' (JWT)
    - JSON message format with 'type' field
    - Automatic heartbeat every 30 seconds
    - Real-time generation updates and HITL feedback
    
    Message Types:
    - 'start_generation': Start generation process
    - 'feedback': Submit HITL feedback
    - 'skip_feedback': Skip current feedback phase
    - 'cancel_generation': Cancel generation
    - 'ping': Heartbeat ping
    """
    
    websocket_service = WebSocketService()
    user: Optional[User] = None
    
    await websocket.accept()
    
    try:
        # Authentication via query parameter (Design Document Compliant)
        if not token:
            await websocket.send_json({
                "type": "auth_required",
                "data": {
                    "code": "AUTH_REQUIRED",
                    "message": "JWT token required in query parameter"
                }
            })
            await websocket.close(code=1008)
            return
        
        # Authenticate user via JWT token
        user = await authenticate_websocket_user(token, db)
        if not user:
            await websocket.send_json({
                "type": "auth_required",
                "data": {
                    "code": "INVALID_TOKEN",
                    "message": "Authentication required as first message"
                }
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Already authenticated via token parameter above
        
        # Send authentication confirmation
        await websocket.send_json({
            "type": "authenticated",
            "user_id": str(user.id),
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Verify user has access to this session
        from app.models.manga import MangaSession
        session = await db.get(MangaSession, session_id)
        if not session:
            await websocket.send_json({
                "type": "error",
                "code": "SESSION_NOT_FOUND",
                "message": "Session not found"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        if session.user_id != user.id:
            await websocket.send_json({
                "type": "error", 
                "code": "ACCESS_DENIED",
                "message": "Session access denied"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Handle the connection
        await websocket_service.handle_connection(
            websocket=websocket,
            session_id=session_id,
            user_id=str(user.id)
        )
        
    except WebSocketDisconnect:
        # Clean disconnection
        pass
    except Exception as e:
        # Unexpected error
        try:
            await websocket.send_json({
                "type": "error",
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            # Log the specific error for debugging
            import logging
            logging.error(f"WebSocket error during cleanup: {e}")
        finally:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.websocket("/sessions/{session_id}/phases/{phase_number}")
async def websocket_phase_specific_endpoint(
    websocket: WebSocket,
    session_id: str,
    phase_number: int,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Phase-specific WebSocket endpoint for targeted HITL interaction.
    
    Optimized for specific phase feedback and real-time updates.
    Automatically subscribes to phase-specific events only.
    """
    
    # Validate phase number
    if phase_number < 1 or phase_number > 7:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        return
    
    websocket_service = WebSocketService()
    user: Optional[User] = None
    
    await websocket.accept()
    
    try:
        # Authentication via query parameter (Design Document Compliant)
        if not token:
            await websocket.send_json({
                "type": "auth_required",
                "data": {
                    "code": "AUTH_REQUIRED",
                    "message": "JWT token required in query parameter"
                }
            })
            await websocket.close(code=1008)
            return
        
        # Authenticate user via JWT token
        user = await authenticate_websocket_user(token, db)
        if not user:
            await websocket.send_json({
                "type": "auth_required",
                "data": {
                    "code": "INVALID_TOKEN",
                    "message": "Authentication required as first message"
                }
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Send phase-specific connection confirmation
        await websocket.send_json({
            "type": "phase_connection_established",
            "session_id": session_id,
            "phase_number": phase_number,
            "user_id": str(user.id),
            "phase_name": _get_phase_name(phase_number),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Handle phase-specific connection
        await websocket_service.handle_phase_connection(
            websocket=websocket,
            session_id=session_id,
            phase_number=phase_number,
            user_id=str(user.id)
        )
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.websocket("/global/user/{user_id}")
async def websocket_user_global_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Global user endpoint for cross-session notifications.
    
    Receives notifications about all user's sessions:
    - New session started
    - Session completed
    - Critical errors
    - System announcements
    """
    
    websocket_service = WebSocketService()
    user: Optional[User] = None
    
    await websocket.accept()
    
    try:
        # Authentication via query parameter (Design Document Compliant)
        if not token:
            await websocket.send_json({
                "type": "auth_required",
                "data": {
                    "code": "AUTH_REQUIRED",
                    "message": "JWT token required in query parameter"
                }
            })
            await websocket.close(code=1008)
            return
        
        # Authenticate user via JWT token
        user = await authenticate_websocket_user(token, db)
        if not user or str(user.id) != user_id:
            await websocket.send_json({
                "type": "auth_required",
                "data": {
                    "code": "AUTHORIZATION_FAILED",
                    "message": "User ID mismatch or invalid credentials"
                }
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Send global connection confirmation
        await websocket.send_json({
            "type": "global_connection_established",
            "user_id": user_id,
            "capabilities": [
                "cross_session_notifications",
                "system_announcements",
                "user_analytics_updates"
            ],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Handle global user connection
        await websocket_service.handle_global_user_connection(
            websocket=websocket,
            user_id=user_id
        )
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


# Health check endpoint for WebSocket monitoring
@router.websocket("/health")
async def websocket_health_check(websocket: WebSocket):
    """WebSocket health check endpoint for monitoring systems."""
    
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "type": "health_check",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "websocket_stats": websocket_service.get_stats() if 'websocket_service' in locals() else {}
        })
        
        # Wait for client response or timeout
        response = await websocket.receive_json()
        
        if response.get("type") == "ping":
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        import logging
        logging.error(f"WebSocket error in global endpoint: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


def _get_phase_name(phase_number: int) -> str:
    """Get human-readable phase name."""
    phase_names = {
        1: "Concept Analysis",
        2: "Character Design", 
        3: "Plot Structure",
        4: "Name Generation",
        5: "Image Generation",
        6: "Dialogue Placement",
        7: "Final Integration"
    }
    return phase_names.get(phase_number, f"Phase {phase_number}")


# WebSocket protocol documentation
WEBSOCKET_PROTOCOL_DOC = {
    "version": "1.0",
    "endpoints": {
        "/ws/v1/sessions/{session_id}": {
            "description": "Primary session WebSocket",
            "authentication": "JWT token required",
            "message_types": [
                "authenticate", "hitl_feedback", "progress_request", 
                "ping", "subscribe_events"
            ]
        },
        "/ws/v1/sessions/{session_id}/phases/{phase_number}": {
            "description": "Phase-specific WebSocket",
            "authentication": "JWT token required", 
            "message_types": [
                "authenticate", "phase_feedback", "phase_progress_request"
            ]
        },
        "/ws/v1/global/user/{user_id}": {
            "description": "Global user notifications",
            "authentication": "JWT token required",
            "message_types": [
                "authenticate", "subscribe_notifications"
            ]
        }
    },
    "message_format": {
        "type": "string (required)",
        "data": "object (optional)",
        "timestamp": "ISO string (auto-added)"
    }
}