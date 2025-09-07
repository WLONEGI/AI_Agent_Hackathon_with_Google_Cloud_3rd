"""Manga generation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, WebSocket
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Optional, AsyncIterator
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field
import json

from app.core.database import get_db
from app.models.manga import MangaSession, GenerationStatus
from app.models.user import User
from app.services.integrated_ai_service import IntegratedAIService
from app.services.cache_service import CacheService
from app.services.websocket_service import WebSocketService
from app.schemas.pipeline_schemas import HITLFeedback
from app.core.config import settings
from app.api.v1.security import get_current_active_user, check_generation_limit

router = APIRouter()

# Initialize services
integrated_ai_service = IntegratedAIService()
cache_service = CacheService()
websocket_service = WebSocketService()


# Request/Response schemas
class MangaGenerationRequest(BaseModel):
    """Manga generation request schema."""
    text: str = Field(..., min_length=10, max_length=10000, description="Input story text")
    title: Optional[str] = Field(None, max_length=255, description="Optional title")
    genre: Optional[str] = Field(None, description="Preferred genre")
    style: str = Field("standard", description="Art style preference")
    quality_level: str = Field("high", description="Quality level")
    hitl_enabled: bool = Field(True, description="Enable Human-in-the-Loop")
    auto_proceed: bool = Field(False, description="Auto-proceed without feedback")


class MangaGenerationResponse(BaseModel):
    """Manga generation response schema."""
    session_id: UUID
    status: str
    message: str
    websocket_url: Optional[str] = None
    estimated_time_seconds: int


class MangaSessionResponse(BaseModel):
    """Manga session details response."""
    id: UUID
    title: Optional[str]
    status: str
    current_phase: int
    total_phases: int
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    preview_url: Optional[str]
    download_url: Optional[str]
    error_message: Optional[str]


@router.post("/generate")
async def start_generation(
    request: MangaGenerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_generation_limit)
) -> StreamingResponse:
    """Start a new manga generation session with streaming response."""
    
    # Check user generation limits
    current_user.reset_daily_limit_if_needed()
    if not current_user.can_generate:
        raise HTTPException(400, "Daily generation limit reached")
    
    user_id = str(current_user.id)
    session_id = str(uuid4())
    
    async def generate_stream() -> AsyncIterator[str]:
        """Stream generation progress"""
        async for event in integrated_ai_service.generate_manga(
            user_input=request.text,
            user_id=user_id,
            db=db,
            session_id=session_id,
            enable_hitl=request.hitl_enabled
        ):
            # Send SSE formatted event
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/sessions", response_model=List[MangaSessionResponse])
async def list_sessions(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[MangaSessionResponse]:
    """List user's manga generation sessions."""
    
    query = select(MangaSession).order_by(MangaSession.created_at.desc())
    
    # Filter by current user
    query = query.where(MangaSession.user_id == current_user.id)
    
    if status:
        query = query.where(MangaSession.status == status)
    
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return [
        MangaSessionResponse(
            id=session.id,
            title=session.title,
            status=session.status,
            current_phase=session.current_phase,
            total_phases=session.total_phases,
            progress_percentage=session.progress_percentage,
            created_at=session.created_at,
            updated_at=session.updated_at,
            preview_url=session.preview_url,
            download_url=session.download_url,
            error_message=session.error_message
        )
        for session in sessions
    ]


@router.get("/sessions/{session_id}", response_model=MangaSessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MangaSessionResponse:
    """Get specific manga session details."""
    
    session = await db.get(MangaSession, session_id)
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Check ownership
    if session.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    
    return MangaSessionResponse(
        id=session.id,
        title=session.title,
        status=session.status,
        current_phase=session.current_phase,
        total_phases=session.total_phases,
        progress_percentage=session.progress_percentage,
        created_at=session.created_at,
        updated_at=session.updated_at,
        preview_url=session.preview_url,
        download_url=session.download_url,
        error_message=session.error_message
    )


@router.get("/sessions/{session_id}/phase/{phase_number}")
async def get_phase_result(
    session_id: UUID,
    phase_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get specific phase result for a session."""
    
    # Check session exists and user has access
    session = await db.get(MangaSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Check ownership
    if session.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    
    # Try cache first
    cache_key = f"phase_result:{session_id}:{phase_number}"
    cached_result = await cache_service.get(cache_key)
    
    if cached_result:
        return cached_result
    
    # Get from database
    from app.models.manga import PhaseResult
    query = select(PhaseResult).where(
        PhaseResult.session_id == session_id,
        PhaseResult.phase_number == phase_number
    )
    
    result = await db.execute(query)
    phase_result = result.scalar_one_or_none()
    
    if not phase_result:
        raise HTTPException(404, "Phase result not found")
    
    response = {
        "phase_number": phase_result.phase_number,
        "phase_name": phase_result.phase_name,
        "status": phase_result.status,
        "output_data": phase_result.output_data,
        "preview_data": phase_result.preview_data,
        "processing_time_ms": phase_result.processing_time_ms,
        "completed_at": phase_result.completed_at.isoformat() if phase_result.completed_at else None
    }
    
    # Cache the result
    await cache_service.set(cache_key, response, cache_type="phase_result", ttl=3600)
    
    return response


@router.post("/sessions/{session_id}/feedback")
async def submit_feedback(
    session_id: UUID,
    phase_number: int,
    feedback_text: str,
    feedback_data: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Submit feedback for a specific phase."""
    
    # Check session exists and ownership
    session = await db.get(MangaSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    
    if session.status != GenerationStatus.WAITING_FEEDBACK:
        raise HTTPException(400, "Session is not waiting for feedback")
    
    # Store feedback
    from app.models.manga import UserFeedback
    feedback = UserFeedback(
        session_id=session_id,
        phase_number=phase_number,
        feedback_type="text",
        feedback_text=feedback_text,
        feedback_data=feedback_data or {}
    )
    
    db.add(feedback)
    await db.commit()
    
    # Notify processing engine via Redis pub/sub
    feedback_channel = f"feedback:{session_id}"
    from app.core.redis_client import redis_manager
    await redis_manager.redis.publish(
        feedback_channel,
        json.dumps({
            "phase": phase_number,
            "feedback_text": feedback_text,
            "feedback_data": feedback_data
        })
    )
    
    return {"status": "success", "message": "Feedback submitted successfully"}


@router.post("/sessions/{session_id}/cancel")
async def cancel_generation(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Cancel an active manga generation session."""
    
    session = await db.get(MangaSession, session_id)
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Check ownership
    if session.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    
    if not session.is_active:
        raise HTTPException(400, "Session is not active")
    
    # Update status  
    session.status = GenerationStatus.CANCELLED
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    
    # Notify processing engine
    cancel_channel = f"cancel:{session_id}"
    from app.core.redis_client import redis_manager
    await redis_manager.redis.publish(cancel_channel, "cancel")
    
    return {"status": "success", "message": "Generation cancelled successfully"}


# WebSocket endpoint for HITL
@router.websocket("/ws/session/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time HITL communication."""
    
    # Extract user_id from JWT token in WebSocket connection
    try:
        token = dict(websocket.query_params).get("token")
        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            return
        
        from app.api.v1.security import verify_token
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
            
    except Exception:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    await websocket_service.handle_connection(
        websocket=websocket,
        session_id=session_id,
        user_id=user_id
    )


@router.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get current status of a manga generation session."""
    
    return await integrated_ai_service.get_session_status(session_id, db)


@router.post("/sessions/{session_id}/hitl-feedback")
async def submit_hitl_feedback(
    session_id: str,
    phase_num: int,
    feedback: HITLFeedback,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Submit HITL feedback for a specific phase."""
    
    success = await integrated_ai_service.submit_hitl_feedback(
        session_id=session_id,
        phase_num=phase_num,
        feedback=feedback,
        db=db
    )
    
    if success:
        return {"status": "success", "message": "Feedback submitted successfully"}
    else:
        raise HTTPException(400, "Failed to submit feedback")