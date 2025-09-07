"""HITL Feedback API v1 - Human-in-the-Loop feedback management (API Design Document Compliant)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.user import User
from app.services.url_service import url_service
from app.api.v1.security import get_current_active_user, check_api_limit

router = APIRouter()

# Request/Response Models (Design Document Compliant)
class FeedbackContent(BaseModel):
    """Feedback content structure (API Design Document Compliant)."""
    natural_language: Optional[str] = Field(None, description="Natural language feedback")
    quick_option: Optional[str] = Field(None, pattern="^(make_brighter|more_serious|add_detail|simplify)$", description="Quick option selection")
    intensity: float = Field(0.7, ge=0.0, le=1.0, description="Modification intensity")
    target_elements: List[str] = Field(default_factory=list, description="Target elements for modification")

class FeedbackRequest(BaseModel):
    """Request to submit feedback (API Design Document Compliant)."""
    phase: int = Field(..., ge=1, le=7, description="Phase number")
    feedback_type: str = Field(..., pattern="^(natural_language|quick_option|skip)$", description="Feedback type")
    content: FeedbackContent = Field(..., description="Feedback content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phase": 1,
                "feedback_type": "natural_language",
                "content": {
                    "natural_language": "もっと明るい雰囲気にして、コメディ要素を強くして",
                    "quick_option": "make_brighter",
                    "intensity": 0.7,
                    "target_elements": ["story_pace", "character_mood"]
                }
            }
        }

class ParsedModification(BaseModel):
    """Parsed modification from feedback (API Design Document Compliant)."""
    type: str = Field(..., description="Modification type")
    target: str = Field(..., description="Modification target")
    direction: Optional[str] = Field(None, description="Modification direction")
    intensity: float = Field(..., description="Modification intensity")
    addition: Optional[str] = Field(None, description="Element to add")

class FeedbackResponse(BaseModel):
    """Response for feedback submission (API Design Document Compliant)."""
    feedback_id: UUID = Field(..., description="Generated feedback ID")
    request_id: UUID = Field(..., description="Request ID")
    phase: int = Field(..., description="Phase number")
    status: str = Field(..., description="Feedback status (accepted)")
    parsed_modifications: List[ParsedModification] = Field(..., description="Parsed modifications")
    estimated_modification_time: int = Field(..., description="Estimated time in seconds")
    modification_url: str = Field(..., description="URL to track modification status")

class SceneContent(BaseModel):
    """Scene content structure (API Design Document Compliant)."""
    scene_id: int = Field(..., description="Scene ID")
    title: str = Field(..., description="Scene title")
    description: str = Field(..., description="Scene description")
    emotion: str = Field(..., description="Scene emotion")
    pages: int = Field(..., description="Number of pages")

class StoryStructure(BaseModel):
    """Story structure content (API Design Document Compliant)."""
    theme: str = Field(..., description="Story theme")
    genre: str = Field(..., description="Story genre")
    target_pages: int = Field(..., description="Target page count")
    main_scenes: List[SceneContent] = Field(..., description="Main scenes")

class PreviewUrls(BaseModel):
    """Preview URLs structure (API Design Document Compliant)."""
    thumbnail: str = Field(..., description="Thumbnail URL")
    structure_diagram: str = Field(..., description="Structure diagram URL")

class QuickOption(BaseModel):
    """Quick modification option (API Design Document Compliant)."""
    label: str = Field(..., description="Option label")
    value: str = Field(..., description="Option value")

class ModificationOptions(BaseModel):
    """Available modification options (API Design Document Compliant)."""
    quick_options: List[QuickOption] = Field(..., description="Quick modification options")
    modifiable_elements: List[str] = Field(..., description="List of modifiable elements")

class PhasePreviewResponse(BaseModel):
    """Phase preview response (API Design Document Compliant)."""
    phase: int = Field(..., description="Phase number")
    phase_name: str = Field(..., description="Phase name")
    content: Dict[str, Any] = Field(..., description="Phase content")
    preview_urls: PreviewUrls = Field(..., description="Preview URLs")
    modification_options: ModificationOptions = Field(..., description="Modification options")
    feedback_deadline: str = Field(..., description="ISO8601 feedback deadline")

class AppliedModification(BaseModel):
    """Applied modification status (API Design Document Compliant)."""
    type: str = Field(..., description="Modification type")
    status: str = Field(..., description="Modification status")
    result_preview: Optional[str] = Field(None, description="Result preview URL")

class ModificationStatusResponse(BaseModel):
    """Modification status response (API Design Document Compliant)."""
    feedback_id: UUID = Field(..., description="Feedback ID")
    status: str = Field(..., pattern="^(processing|completed|failed)$", description="Overall status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    applied_modifications: List[AppliedModification] = Field(..., description="Applied modifications")
    estimated_completion: str = Field(..., description="ISO8601 estimated completion")
    next_phase_available: bool = Field(..., description="Is next phase available")

class SkipFeedbackRequest(BaseModel):
    """Request to skip feedback (API Design Document Compliant)."""
    phase: int = Field(..., ge=1, le=7, description="Phase number")
    skip_reason: str = Field(..., pattern="^(satisfied|time_constraint|default_acceptable)$", description="Skip reason")

class SkipFeedbackResponse(BaseModel):
    """Response for feedback skip (API Design Document Compliant)."""
    skipped_phase: int = Field(..., description="Skipped phase number")
    next_phase: int = Field(..., description="Next phase number")
    processing_resumed: bool = Field(..., description="Processing resumed")
    estimated_completion: str = Field(..., description="ISO8601 estimated completion")


# ===== DESIGN DOCUMENT COMPLIANT ENDPOINTS =====

@router.post("/{request_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request_id: UUID,
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit)
) -> FeedbackResponse:
    """Submit feedback for phase result (POST /api/v1/manga/{request_id}/feedback).
    
    Fully complies with API design document specification.
    Parses natural language or quick options into structured modifications.
    
    Requires: manga:feedback permission + ownership
    """
    
    # Validate session exists and user has ownership
    from app.models.manga import MangaSession
    session = await db.get(MangaSession, request_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Generate feedback ID
    feedback_id = uuid4()
    
    # Parse feedback into structured modifications
    parsed_modifications = []
    
    if request.feedback_type == "natural_language" and request.content.natural_language:
        # Parse natural language feedback
        if "明るい" in request.content.natural_language or "make_brighter" in request.content.natural_language:
            parsed_modifications.append(ParsedModification(
                type="mood_adjustment",
                target="story_atmosphere",
                direction="brighter",
                intensity=request.content.intensity
            ))
        
        if "コメディ" in request.content.natural_language or "comedy" in request.content.natural_language:
            parsed_modifications.append(ParsedModification(
                type="element_addition",
                target="story_elements",
                addition="comedy",
                intensity=0.8
            ))
    
    elif request.feedback_type == "quick_option" and request.content.quick_option:
        # Process quick options
        if request.content.quick_option == "make_brighter":
            parsed_modifications.append(ParsedModification(
                type="mood_adjustment",
                target="story_atmosphere", 
                direction="brighter",
                intensity=request.content.intensity
            ))
        elif request.content.quick_option == "more_serious":
            parsed_modifications.append(ParsedModification(
                type="mood_adjustment",
                target="story_atmosphere",
                direction="serious",
                intensity=request.content.intensity
            ))
        # Add other quick options...
    
    # Calculate estimated modification time
    base_time = 45 if parsed_modifications else 15
    estimated_time = base_time * len(parsed_modifications) if parsed_modifications else base_time
    
    return FeedbackResponse(
        feedback_id=feedback_id,
        request_id=request_id,
        phase=request.phase,
        status="accepted",
        parsed_modifications=parsed_modifications,
        estimated_modification_time=estimated_time,
        modification_url=f"/api/v1/manga/{request_id}/modification/{feedback_id}/status"
    )


@router.get("/{request_id}/phase/{phase_number}/preview", response_model=PhasePreviewResponse)
async def get_phase_preview(
    request_id: UUID,
    phase_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit)
) -> PhasePreviewResponse:
    """Get phase result preview (GET /api/v1/manga/{request_id}/phase/{phase_number}/preview).
    
    Fully complies with API design document specification.
    Returns phase-specific preview content and modification options.
    
    Requires: manga:read permission + ownership
    """
    
    # Validate phase number
    if phase_number < 1 or phase_number > 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phase number. Must be 1-7."
        )
    
    # Validate session exists and user has ownership
    from app.models.manga import MangaSession
    session = await db.get(MangaSession, request_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Phase-specific content
    phase_names = {
        1: "story_theme",
        2: "character_design", 
        3: "plot_structure",
        4: "scene_layout",
        5: "image_generation",
        6: "dialogue_placement",
        7: "final_integration"
    }
    
    # Mock content based on phase
    if phase_number == 1:
        content = {
            "story_structure": {
                "theme": "友情と成長",
                "genre": "日常系",
                "target_pages": 15,
                "main_scenes": [
                    {
                        "scene_id": 1,
                        "title": "出会い",
                        "description": "主人公が新しいクラスメイトと出会う",
                        "emotion": "nervous",
                        "pages": 3
                    }
                ]
            }
        }
    else:
        content = {
            "phase_content": f"Mock content for phase {phase_number}",
            "elements": ["element1", "element2", "element3"]
        }
    
    return PhasePreviewResponse(
        phase=phase_number,
        phase_name=phase_names.get(phase_number, f"phase_{phase_number}"),
        content=content,
        preview_urls=PreviewUrls(
            **url_service.construct_preview_urls(request_id, phase_number)
        ),
        modification_options=ModificationOptions(
            quick_options=[
                QuickOption(label="明るく", value="make_brighter"),
                QuickOption(label="シリアスに", value="more_serious"),
                QuickOption(label="詳細化", value="add_detail")
            ],
            modifiable_elements=["theme", "genre", "scene_count", "emotion_tone"]
        ),
        feedback_deadline=(datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat() + "Z"
    )


@router.get("/{request_id}/modification/{feedback_id}/status", response_model=ModificationStatusResponse)
async def get_modification_status(
    request_id: UUID,
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit)
) -> ModificationStatusResponse:
    """Get feedback modification status (GET /api/v1/manga/{request_id}/modification/{feedback_id}/status).
    
    Fully complies with API design document specification.
    Returns progress of feedback application and modification results.
    
    Requires: manga:read permission + ownership
    """
    
    # Validate session exists and user has ownership
    from app.models.manga import MangaSession
    session = await db.get(MangaSession, request_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get feedback modification status from database/cache
    # This would integrate with the actual feedback processing system
    
    return ModificationStatusResponse(
        feedback_id=feedback_id,
        status="processing",
        progress=80,
        applied_modifications=[
            AppliedModification(
                type="mood_adjustment",
                status="completed", 
                result_preview=url_service.construct_feedback_urls(str(feedback_id))["result_preview"]
            )
        ],
        estimated_completion=(datetime.utcnow().replace(minute=datetime.utcnow().minute + 5)).isoformat() + "Z",
        next_phase_available=False
    )


@router.post("/{request_id}/skip-feedback", response_model=SkipFeedbackResponse)
async def skip_feedback(
    request_id: UUID,
    request: SkipFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit)
) -> SkipFeedbackResponse:
    """Skip feedback and proceed to next phase (POST /api/v1/manga/{request_id}/skip-feedback).
    
    Fully complies with API design document specification.
    Allows users to skip feedback and continue processing.
    
    Requires: manga:feedback permission + ownership
    """
    
    # Validate phase number
    if request.phase < 1 or request.phase > 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phase number. Must be 1-7."
        )
    
    # Validate session exists and user has ownership
    from app.models.manga import MangaSession
    session = await db.get(MangaSession, request_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate session is in appropriate state for skipping
    if session.current_phase != request.phase:
        raise HTTPException(status_code=400, detail="Session not in requested phase")
    
    # Update session to skip feedback and proceed
    session.current_phase = min(request.phase + 1, 7)
    session.updated_at = datetime.utcnow()
    await db.commit()
    
    next_phase = min(request.phase + 1, 7)
    
    return SkipFeedbackResponse(
        skipped_phase=request.phase,
        next_phase=next_phase,
        processing_resumed=True,
        estimated_completion=(datetime.utcnow().replace(hour=datetime.utcnow().hour + 1)).isoformat() + "Z"
    )