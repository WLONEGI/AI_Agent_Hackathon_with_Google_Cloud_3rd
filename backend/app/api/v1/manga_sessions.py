"""Optimized Manga Sessions API v1 - RESTful design with WebSocket integration."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional, AsyncIterator
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json
import asyncio

from app.core.database import get_db
from app.models.user import User
from app.domain.manga.entities.session import MangaSession, SessionStatus
from app.domain.manga.services.manga_generation_service import MangaGenerationService
from app.domain.manga.value_objects.generation_params import GenerationParameters
from app.services.integrated_ai_service import IntegratedAIService
from app.services.websocket_service import WebSocketService
from app.api.v1.security import (
    get_current_active_user, 
    check_generation_limit, 
    check_api_limit,
    Permissions,
    require_permissions
)

router = APIRouter()

# Dependency injection for services
async def get_manga_service() -> MangaGenerationService:
    """Get manga generation service instance."""
    # TODO: Implement proper DI container
    from app.infrastructure.database.repositories.session_repository_impl import SessionRepositoryImpl
    from app.infrastructure.database.repositories.phase_result_repository_impl import PhaseResultRepositoryImpl
    from app.infrastructure.database.repositories.generated_content_repository_impl import GeneratedContentRepositoryImpl
    
    return MangaGenerationService(
        SessionRepositoryImpl(),
        PhaseResultRepositoryImpl(),
        GeneratedContentRepositoryImpl()
    )

# Request/Response Models (Design Document Compliant)
class FeedbackModeSettings(BaseModel):
    """HITL feedback mode configuration."""
    enabled: bool = Field(True, description="Enable HITL feedback")
    timeout_minutes: int = Field(30, description="Feedback timeout in minutes")
    allow_skip: bool = Field(True, description="Allow skipping feedback phases")

class GenerationOptions(BaseModel):
    """Additional generation options."""
    priority: str = Field("normal", regex="^(normal|high)$", description="Processing priority")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for completion notification")
    auto_publish: bool = Field(False, description="Automatically publish after completion")

class SessionCreateRequest(BaseModel):
    """Request to create new manga session (API Design Document Compliant)."""
    title: str = Field(..., max_length=255, description="Manga title")
    text: str = Field(..., min_length=10, max_length=50000, description="Story input text")
    ai_auto_settings: bool = Field(True, description="Use AI automatic settings")
    feedback_mode: FeedbackModeSettings = Field(default_factory=FeedbackModeSettings, description="Feedback mode settings")
    options: GenerationOptions = Field(default_factory=GenerationOptions, description="Additional options")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "My Awesome Manga",
                "text": "A young hero discovers magical powers and must save the world...",
                "ai_auto_settings": True,
                "feedback_mode": {
                    "enabled": True,
                    "timeout_minutes": 30,
                    "allow_skip": True
                },
                "options": {
                    "priority": "normal",
                    "webhook_url": None,
                    "auto_publish": False
                }
            }
        }


class SessionResponse(BaseModel):
    """Standard session response model (API Design Document Compliant)."""
    request_id: UUID = Field(..., description="Request ID for tracking")
    status: str = Field(..., description="Current status (queued|processing|completed|failed)")
    estimated_completion_time: Optional[str] = Field(None, description="ISO8601 estimated completion time")
    performance_mode: str = Field("monolithic", description="Processing performance mode")
    expected_duration_minutes: int = Field(8, description="Expected duration in minutes")
    status_url: str = Field(..., description="URL for status polling")
    sse_url: str = Field(..., description="URL for Server-Sent Events")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "queued",
                "estimated_completion_time": "2025-01-20T15:30:00Z",
                "performance_mode": "monolithic",
                "expected_duration_minutes": 8,
                "status_url": "/api/v1/manga/550e8400-e29b-41d4-a716-446655440000/status",
                "sse_url": "/api/v1/manga/550e8400-e29b-41d4-a716-446655440000/stream"
            }
        }


class ModuleDetailResponse(BaseModel):
    """Current module processing details (API Design Document Compliant)."""
    module_number: int = Field(..., description="Current module number")
    module_name: str = Field(..., description="Module name (e.g., text_analysis)")
    status: str = Field(..., description="Module status (processing|completed|failed)")
    started_at: Optional[str] = Field(None, description="ISO8601 start time")
    estimated_completion: Optional[str] = Field(None, description="ISO8601 estimated completion")
    progress_percentage: float = Field(0.0, description="Module progress percentage")
    processing_mode: str = Field("in_memory", description="Processing mode")

class ModuleHistoryResponse(BaseModel):
    """Completed module history (API Design Document Compliant)."""
    module_number: int = Field(..., description="Module number")
    module_name: str = Field(..., description="Module name")
    status: str = Field(..., description="Module status")
    started_at: str = Field(..., description="ISO8601 start time")
    completed_at: str = Field(..., description="ISO8601 completion time")
    duration_seconds: float = Field(..., description="Processing duration in seconds")

class SessionStatusResponse(BaseModel):
    """Detailed session status response (API Design Document Compliant)."""
    request_id: UUID = Field(..., description="Request ID")
    status: str = Field(..., description="Overall status")
    current_module: int = Field(..., description="Current module number (1-8)")
    total_modules: int = Field(8, description="Total modules")
    module_details: ModuleDetailResponse = Field(..., description="Current module details")
    modules_history: List[ModuleHistoryResponse] = Field(default_factory=list, description="Completed modules")
    overall_progress: float = Field(0.0, description="Overall progress percentage")
    started_at: Optional[str] = Field(None, description="ISO8601 start time")
    estimated_completion: Optional[str] = Field(None, description="ISO8601 estimated completion")
    result_url: Optional[str] = Field(None, description="Result URL when completed")


# ===== DESIGN DOCUMENT COMPLIANT ENDPOINTS ONLY =====
# Only the following 3 endpoints are defined in the API design document:
# 1. POST /generate - Start manga generation
# 2. GET /{request_id}/status - Get generation status  
# 3. GET /{request_id}/stream - Server-Sent Events stream
#
# All other endpoints have been removed for design document compliance


@router.post("/generate", response_model=SessionResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_manga(
    request: SessionCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_generation_limit),
    manga_service: MangaGenerationService = Depends(get_manga_service)
) -> SessionResponse:
    """Start manga generation request (POST /api/v1/manga/generate).
    
    Fully complies with API design document specification.
    Returns 202 Accepted with request_id for tracking.
    
    Requires: manga:create permission
    Rate limit: 10 generations per hour per user
    """
    
    # Convert request to domain objects with new structure
    generation_params = {
        "ai_auto_settings": request.ai_auto_settings,
        "feedback_mode": request.feedback_mode.dict(),
        "options": request.options.dict()
    }
    
    # Start manga generation
    session = await manga_service.start_manga_generation(
        user_id=str(current_user.id),
        input_text=request.text,  # Changed from input_text to text
        generation_params=generation_params,
        title=request.title
    )
    
    # Start background processing
    background_tasks.add_task(
        _process_manga_generation,
        session.id,
        generation_params
    )
    
    # Create design document compliant response
    estimated_completion = (datetime.utcnow() + timedelta(minutes=8)).isoformat() + "Z"
    
    return SessionResponse(
        request_id=session.id,
        status="queued",
        estimated_completion_time=estimated_completion,
        performance_mode="monolithic",
        expected_duration_minutes=8,
        status_url=f"/api/v1/manga/{session.id}/status",
        sse_url=f"/api/v1/manga/{session.id}/stream"
    )


@router.get("/{request_id}/status", response_model=SessionStatusResponse)
async def get_generation_status(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit),
    manga_service: MangaGenerationService = Depends(get_manga_service)
) -> SessionStatusResponse:
    """Get generation status (GET /api/v1/manga/{request_id}/status).
    
    Fully complies with API design document specification.
    Returns detailed module-based progress information.
    
    Requires: manga:read permission + ownership
    """
    
    session = await manga_service.session_repository.find_by_id(str(request_id))
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check ownership
    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - not session owner"
        )
    
    # Get phase/module results for detailed status
    phase_results = await manga_service.phase_result_repository.find_by_session_id(str(session.id))
    
    # Convert phase-based system to module-based (design document compliance)
    current_module = min(session.current_phase, 8) if session.current_phase else 1
    module_names = [
        "text_analysis", "concept_extraction", "character_design",
        "plot_structure", "scene_generation", "dialogue_creation", 
        "image_generation", "final_integration"
    ]
    
    # Create current module details
    module_details = ModuleDetailResponse(
        module_number=current_module,
        module_name=module_names[current_module - 1] if current_module <= len(module_names) else f"module_{current_module}",
        status="processing" if session.status == "processing" else session.status,
        started_at=session.created_at.isoformat() + "Z" if session.created_at else None,
        estimated_completion=(datetime.utcnow() + timedelta(minutes=8-current_module)).isoformat() + "Z",
        progress_percentage=session.progress_percentage or 0.0,
        processing_mode="in_memory"
    )
    
    # Create modules history
    modules_history = []
    for i in range(1, current_module):
        if i <= len(phase_results):
            phase_result = phase_results[i-1]
            modules_history.append(ModuleHistoryResponse(
                module_number=i,
                module_name=module_names[i-1],
                status="completed",
                started_at=phase_result.created_at.isoformat() + "Z" if phase_result.created_at else session.created_at.isoformat() + "Z",
                completed_at=phase_result.updated_at.isoformat() + "Z" if phase_result.updated_at else session.updated_at.isoformat() + "Z",
                duration_seconds=30.0  # Approximate duration
            ))
    
    # Create design document compliant response
    return SessionStatusResponse(
        request_id=session.id,
        status=session.status,
        current_module=current_module,
        total_modules=8,
        module_details=module_details,
        modules_history=modules_history,
        overall_progress=(current_module - 1) / 8 * 100,
        started_at=session.created_at.isoformat() + "Z" if session.created_at else None,
        estimated_completion=(session.created_at + timedelta(minutes=8)).isoformat() + "Z" if session.created_at else None,
        result_url=f"/api/v1/manga/{session.id}" if session.status == "completed" else None
    )


@router.get("/{request_id}/stream")
async def stream_generation_events(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit),
    manga_service: MangaGenerationService = Depends(get_manga_service)
):
    """Server-Sent Events stream (GET /api/v1/manga/{request_id}/stream).
    
    Fully complies with API design document specification.
    Returns real-time generation progress via SSE.
    
    Requires: manga:read permission + ownership
    """
    
    # Verify session exists and ownership
    session = await manga_service.session_repository.find_by_id(str(request_id))
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    async def event_stream():
        """Generate SSE stream for manga generation progress."""
        try:
            # Get AI service
            ai_service = IntegratedAIService()
            
            # Start streaming generation events
            async for event in ai_service.generate_manga(
                user_input=session.input_text,
                user_id=session.user_id,
                db=db,
                session_id=str(request_id),
                enable_hitl=True
            ):
                # Format as SSE according to design document
                event_type = event.get("type", "progress")
                data = json.dumps(event, ensure_ascii=False)
                yield f"event: {event_type}\ndata: {data}\n\n"
                
                # Break if generation complete or failed
                if event_type in ["generation_completed", "generation_failed", "complete"]:
                    break
                    
                await asyncio.sleep(0.1)  # Small delay to prevent overwhelming
                
        except Exception as e:
            error_event = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# Background task for manga processing
async def _process_manga_generation(
    session_id: str,
    generation_params: Dict[str, Any]
) -> None:
    """Background task to process manga generation."""
    
    try:
        integrated_service = IntegratedAIService()
        await integrated_service.process_session_pipeline(session_id, generation_params)
    except Exception as e:
        # Log error and update session status
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Manga generation failed for session {session_id}: {e}")