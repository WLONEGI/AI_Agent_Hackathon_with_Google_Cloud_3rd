"""Mock Manga Generation API for local development."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import datetime
import asyncio
import structlog

from app.core.config import settings
from app.core.mock_services import get_mock_ai_service, get_mock_database
from app.models.user import User
from app.api.v1.security import get_current_active_user

logger = structlog.get_logger(__name__)
router = APIRouter()


class MangaGenerationRequest(BaseModel):
    """Request model for manga generation."""
    text: str = Field(..., min_length=10, max_length=50000, description="Story text")
    title: Optional[str] = Field(None, max_length=255, description="Optional title")


class MangaGenerationResponse(BaseModel):
    """Response model for manga generation."""
    session_id: str
    status: str
    message: str
    redirect_url: str


@router.post("/manga/generate", response_model=MangaGenerationResponse)
async def generate_manga(
    request: MangaGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict[str, Any]] = None  # Make auth optional for mock
):
    """
    Generate manga from text input (Mock implementation).
    """
    if not settings.mock_enabled:
        raise HTTPException(status_code=503, detail="Mock service not enabled")
    
    # Generate session ID
    session_id = str(uuid4())
    
    # Log the request
    logger.info("Mock manga generation started", 
                session_id=session_id,
                text_length=len(request.text),
                title=request.title)
    
    # Add background task to simulate generation
    background_tasks.add_task(
        mock_generate_manga_process,
        session_id=session_id,
        text=request.text,
        title=request.title
    )
    
    # Return immediate response
    return MangaGenerationResponse(
        session_id=session_id,
        status="processing",
        message="漫画生成を開始しました。処理画面にリダイレクトします...",
        redirect_url=f"/generation/{session_id}"
    )


async def mock_generate_manga_process(session_id: str, text: str, title: Optional[str]):
    """
    Mock manga generation process (runs in background).
    """
    try:
        mock_ai = get_mock_ai_service()
        mock_db = get_mock_database()
        
        # Store initial session
        await mock_db.create("manga_sessions", {
            "id": session_id,
            "title": title or "無題の漫画",
            "text": text,
            "status": "processing",
            "current_phase": 1,
            "total_phases": 7,
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Simulate 7-phase generation
        phases = [
            ("concept", mock_ai.generate_concept),
            ("characters", mock_ai.generate_characters),
            ("plot", mock_ai.generate_plot),
            ("panels", mock_ai.generate_panels),
            ("images", generate_mock_images),
            ("dialogue", mock_ai.generate_dialogue),
            ("finalize", mock_ai.finalize_manga)
        ]
        
        results = {}
        for i, (phase_name, phase_func) in enumerate(phases, 1):
            # Update phase progress
            await mock_db.update("manga_sessions", session_id, {
                "current_phase": i,
                "phase_name": phase_name,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Execute phase
            if phase_name == "images":
                results[phase_name] = await phase_func(mock_ai)
            elif phase_name == "characters" or phase_name == "plot":
                results[phase_name] = await phase_func(results.get("concept", {}))
            elif phase_name == "panels":
                results[phase_name] = await phase_func(results.get("plot", {}))
            elif phase_name == "dialogue":
                results[phase_name] = await phase_func(results.get("panels", {}))
            elif phase_name == "finalize":
                results[phase_name] = await phase_func(results)
            else:
                results[phase_name] = await phase_func(text)
            
            logger.info(f"Phase {i} completed", 
                       session_id=session_id, 
                       phase=phase_name)
            
            # Simulate processing time
            await asyncio.sleep(1)
        
        # Update final status
        await mock_db.update("manga_sessions", session_id, {
            "status": "completed",
            "current_phase": 7,
            "results": results,
            "completed_at": datetime.utcnow().isoformat(),
            "preview_url": results.get("finalize", {}).get("preview_url"),
            "download_url": results.get("finalize", {}).get("download_url")
        })
        
        logger.info("Mock manga generation completed", session_id=session_id)
        
    except Exception as e:
        logger.error("Mock manga generation failed", 
                    session_id=session_id, 
                    error=str(e))
        
        # Update error status
        mock_db = get_mock_database()
        await mock_db.update("manga_sessions", session_id, {
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })


async def generate_mock_images(mock_ai):
    """Generate multiple mock images."""
    images = []
    for i in range(8):  # Generate 8 pages
        image_url = await mock_ai.generate_image(f"Page {i+1}")
        images.append({
            "page": i + 1,
            "url": image_url,
            "width": 512,
            "height": 768
        })
    return {"images": images}


@router.get("/manga/session/{session_id}")
async def get_session_status(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = None  # Make auth optional for mock
):
    """
    Get manga generation session status.
    """
    if not settings.mock_enabled:
        raise HTTPException(status_code=503, detail="Mock service not enabled")
    
    mock_db = get_mock_database()
    session = await mock_db.get("manga_sessions", session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "status": session.get("status"),
        "current_phase": session.get("current_phase"),
        "total_phases": session.get("total_phases"),
        "phase_name": session.get("phase_name"),
        "title": session.get("title"),
        "preview_url": session.get("preview_url"),
        "download_url": session.get("download_url"),
        "error_message": session.get("error_message"),
        "progress_percentage": (session.get("current_phase", 0) / session.get("total_phases", 7)) * 100
    }


@router.get("/manga/session/{session_id}/result")
async def get_session_result(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = None  # Make auth optional for mock
):
    """
    Get completed manga generation result.
    """
    if not settings.mock_enabled:
        raise HTTPException(status_code=503, detail="Mock service not enabled")
    
    mock_db = get_mock_database()
    session = await mock_db.get("manga_sessions", session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Generation not completed yet")
    
    return {
        "session_id": session_id,
        "title": session.get("title"),
        "status": "completed",
        "preview_url": session.get("preview_url"),
        "download_url": session.get("download_url"),
        "results": session.get("results", {}),
        "created_at": session.get("created_at"),
        "completed_at": session.get("completed_at")
    }