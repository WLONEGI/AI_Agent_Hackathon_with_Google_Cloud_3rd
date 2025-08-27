"""Preview Interactive API v1 - Real-time preview editing and version management."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional, Union
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from app.core.database import get_db
from app.models.user import User
from app.api.v1.security import get_current_active_user, check_api_limit
from app.services.integrated_ai_service import IntegratedAIService

router = APIRouter()

# Enums
class ChangeType(str, Enum):
    TEXT_EDIT = "text_edit"
    DRAG_DROP = "drag_drop"
    RESIZE = "resize"
    COLOR_CHANGE = "color_change"
    STYLE_CHANGE = "style_change"

class ComparisonType(str, Enum):
    SIDE_BY_SIDE = "side-by-side"
    OVERLAY = "overlay"
    DIFF = "diff"

# Request/Response Models
class InteractiveElement(BaseModel):
    """Interactive element configuration."""
    element_type: str
    enabled: bool
    permissions: List[str] = Field(default_factory=list)

class PreviewData(BaseModel):
    """Phase-specific preview data."""
    phase: int
    version_id: UUID
    timestamp: datetime
    quality_level: int = Field(ge=1, le=5)
    data: Dict[str, Any]
    interactive_elements: Dict[str, InteractiveElement]
    preview_urls: Dict[str, str]

class PreviewResponse(BaseModel):
    """Complete preview response."""
    phase: int
    version_id: UUID
    timestamp: datetime
    quality_level: int
    data: Dict[str, Any]
    interactive_elements: Dict[str, InteractiveElement]
    preview_urls: Dict[str, str]
    load_time_ms: Optional[float] = None
    cache_hit: bool = False

class ChangeData(BaseModel):
    """Change data structure."""
    new_value: Any
    previous_value: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class InteractiveChange(BaseModel):
    """Interactive change request."""
    element_id: str
    change_type: ChangeType
    change_data: ChangeData
    apply_immediately: bool = True
    create_branch: bool = False
    branch_name: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "element_id": "concept.title",
                "change_type": "text_edit",
                "change_data": {
                    "new_value": "新しいタイトル",
                    "previous_value": "古いタイトル",
                    "metadata": {"user_input": True}
                },
                "apply_immediately": True,
                "create_branch": False
            }
        }

class ChangeResponse(BaseModel):
    """Change application response."""
    version_id: UUID
    branch_id: Optional[UUID] = None
    change_applied: bool
    preview_updated: bool
    preview_url: str
    estimated_regeneration_time: float
    quality_impact: Optional[float] = None

class VersionInfo(BaseModel):
    """Version information."""
    version_id: UUID
    parent_version_id: Optional[UUID] = None
    created_at: datetime
    change_description: str
    quality_score: Optional[float] = None
    is_automatic: bool = False
    branch_depth: int = 0
    author_id: Optional[str] = None

class BranchInfo(BaseModel):
    """Branch information."""
    branch_id: UUID
    branch_name: str
    versions_count: int
    latest_version_id: UUID
    created_at: datetime
    is_active: bool = True

class VersionHistoryResponse(BaseModel):
    """Version history response."""
    current_version: UUID
    timeline: List[VersionInfo]
    branches: List[BranchInfo]
    total_versions: int
    max_branch_depth: int

class VersionComparison(BaseModel):
    """Version comparison data."""
    version_id: UUID
    data: Dict[str, Any]
    quality_score: Optional[float] = None

class ComparisonDifference(BaseModel):
    """Difference between versions."""
    path: str
    type: str  # value_change, addition, deletion
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    impact_score: Optional[float] = None

class ComparisonResponse(BaseModel):
    """Version comparison response."""
    version1: VersionComparison
    version2: VersionComparison
    differences: List[ComparisonDifference]
    quality_improvement: Optional[float] = None
    visual_diff_url: Optional[str] = None
    similarity_score: float = 0.0

class RevertRequest(BaseModel):
    """Version revert request."""
    target_version_id: UUID
    create_new_branch: bool = True
    branch_name: Optional[str] = "復元されたバージョン"

class RevertResponse(BaseModel):
    """Version revert response."""
    reverted_to_version: UUID
    new_version_id: UUID
    branch_created: bool
    preview_updated: bool

# Dependency injection
async def get_ai_service() -> IntegratedAIService:
    """Get integrated AI service instance."""
    return IntegratedAIService()

# Core Preview Interactive Endpoints
@router.get("/manga/{request_id}/preview/{phase}", response_model=PreviewResponse)
async def get_phase_preview(
    request_id: UUID,
    phase: int,
    quality_level: int = Query(3, ge=1, le=5, description="Preview quality level"),
    version_id: Optional[UUID] = Query(None, description="Specific version ID"),
    adaptive: bool = Query(True, description="Enable adaptive quality"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit)
) -> PreviewResponse:
    """Get phase-specific preview data with interactive elements.
    
    Requires: manga:read permission + ownership
    """
    
    # Validate phase
    if not (1 <= phase <= 7):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phase must be between 1 and 7"
        )
    
    # Get session and verify ownership
    ai_service = await get_ai_service()
    session_status = await ai_service.get_session_status(str(request_id), db)
    
    if "error" in session_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {request_id}"
        )
    
    # Check if phase has been processed
    phase_data = None
    for phase_info in session_status.get("phases_completed", []):
        if phase_info["phase"] == phase:
            phase_data = phase_info
            break
    
    if not phase_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phase {phase} not yet processed"
        )
    
    # Generate version ID if not provided
    if not version_id:
        version_id = uuid4()
    
    # Build interactive elements based on phase
    interactive_elements = _get_phase_interactive_elements(phase)
    
    # Build preview data based on phase
    preview_data = _build_phase_preview_data(phase, phase_data)
    
    # Generate preview URLs
    preview_urls = {
        "thumbnail": f"/api/v1/previews/{request_id}/phase/{phase}/thumb.png",
        "full_preview": f"/api/v1/previews/{request_id}/phase/{phase}/full.html"
    }
    
    return PreviewResponse(
        phase=phase,
        version_id=version_id,
        timestamp=datetime.utcnow(),
        quality_level=quality_level,
        data=preview_data,
        interactive_elements=interactive_elements,
        preview_urls=preview_urls,
        load_time_ms=125.5,  # Mock value
        cache_hit=False
    )

@router.post("/manga/{request_id}/preview/{phase}/apply-change", response_model=ChangeResponse)
async def apply_interactive_change(
    request_id: UUID,
    phase: int,
    change: InteractiveChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit)
) -> ChangeResponse:
    """Apply interactive change to preview.
    
    Requires: manga:write permission + ownership
    """
    
    # Validate phase
    if not (1 <= phase <= 7):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phase must be between 1 and 7"
        )
    
    # Verify session exists and user has access
    ai_service = await get_ai_service()
    session_status = await ai_service.get_session_status(str(request_id), db)
    
    if "error" in session_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {request_id}"
        )
    
    # Validate element_id exists and is editable
    allowed_elements = _get_allowed_elements_for_phase(phase)
    if change.element_id not in allowed_elements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Element '{change.element_id}' is not editable in phase {phase}"
        )
    
    # Generate new version ID
    new_version_id = uuid4()
    branch_id = uuid4() if change.create_branch else None
    
    # TODO: Implement actual change application logic
    # This would involve:
    # 1. Validating the change data
    # 2. Applying the change to the phase result
    # 3. Regenerating preview if necessary
    # 4. Storing version information
    # 5. Updating quality scores
    
    # Calculate estimated regeneration time based on change type
    regeneration_time = _calculate_regeneration_time(change.change_type, phase)
    
    return ChangeResponse(
        version_id=new_version_id,
        branch_id=branch_id,
        change_applied=True,
        preview_updated=change.apply_immediately,
        preview_url=f"/api/v1/previews/{request_id}/phase/{phase}/preview.html",
        estimated_regeneration_time=regeneration_time,
        quality_impact=0.05  # Mock quality impact
    )

@router.get("/manga/{request_id}/preview/{phase}/versions", response_model=VersionHistoryResponse)
async def get_preview_versions(
    request_id: UUID,
    phase: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit)
) -> VersionHistoryResponse:
    """Get preview version history for a phase.
    
    Requires: manga:read permission + ownership
    """
    
    # Validate phase
    if not (1 <= phase <= 7):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phase must be between 1 and 7"
        )
    
    # TODO: Implement actual version history retrieval
    # This would query the database for version information
    
    # Mock version history
    current_version = uuid4()
    timeline = [
        VersionInfo(
            version_id=current_version,
            parent_version_id=None,
            created_at=datetime.utcnow(),
            change_description="初期バージョン",
            quality_score=0.85,
            is_automatic=True,
            branch_depth=0
        )
    ]
    
    branches = [
        BranchInfo(
            branch_id=uuid4(),
            branch_name="メインブランチ",
            versions_count=1,
            latest_version_id=current_version,
            created_at=datetime.utcnow(),
            is_active=True
        )
    ]
    
    return VersionHistoryResponse(
        current_version=current_version,
        timeline=timeline,
        branches=branches,
        total_versions=1,
        max_branch_depth=0
    )

@router.get("/manga/{request_id}/preview/compare", response_model=ComparisonResponse)
async def compare_preview_versions(
    request_id: UUID,
    version1: UUID = Query(..., description="First version ID"),
    version2: UUID = Query(..., description="Second version ID"),
    comparison_type: ComparisonType = Query(ComparisonType.SIDE_BY_SIDE, description="Comparison type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit)
) -> ComparisonResponse:
    """Compare two preview versions.
    
    Requires: manga:read permission + ownership
    """
    
    if version1 == version2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare the same version"
        )
    
    # TODO: Implement actual version comparison
    # This would:
    # 1. Retrieve both versions from storage
    # 2. Perform deep comparison of data structures
    # 3. Calculate similarity scores
    # 4. Generate visual diff if requested
    
    # Mock comparison data
    version1_data = VersionComparison(
        version_id=version1,
        data={"concept": {"genre": {"primary": "アクション"}}},
        quality_score=0.82
    )
    
    version2_data = VersionComparison(
        version_id=version2,
        data={"concept": {"genre": {"primary": "コメディ"}}},
        quality_score=0.89
    )
    
    differences = [
        ComparisonDifference(
            path="concept.genre.primary",
            type="value_change",
            old_value="アクション",
            new_value="コメディ",
            impact_score=0.15
        )
    ]
    
    return ComparisonResponse(
        version1=version1_data,
        version2=version2_data,
        differences=differences,
        quality_improvement=0.07,
        visual_diff_url=f"/api/v1/diffs/{request_id}/{version1}/{version2}.html",
        similarity_score=0.85
    )

@router.post("/manga/{request_id}/preview/{phase}/revert", response_model=RevertResponse)
async def revert_to_version(
    request_id: UUID,
    phase: int,
    revert_request: RevertRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit)
) -> RevertResponse:
    """Revert to a specific version.
    
    Requires: manga:write permission + ownership
    """
    
    # Validate phase
    if not (1 <= phase <= 7):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phase must be between 1 and 7"
        )
    
    # TODO: Implement actual version revert
    # This would:
    # 1. Validate target version exists
    # 2. Create new version based on target
    # 3. Update current state
    # 4. Create branch if requested
    # 5. Regenerate preview
    
    new_version_id = uuid4()
    
    return RevertResponse(
        reverted_to_version=revert_request.target_version_id,
        new_version_id=new_version_id,
        branch_created=revert_request.create_new_branch,
        preview_updated=True
    )

# Helper Functions
def _get_phase_interactive_elements(phase: int) -> Dict[str, InteractiveElement]:
    """Get interactive elements configuration for a phase."""
    
    phase_elements = {
        1: {  # Concept phase
            "concept_editor": InteractiveElement(element_type="text_editor", enabled=True),
            "genre_selector": InteractiveElement(element_type="dropdown", enabled=True),
            "audience_adjuster": InteractiveElement(element_type="slider", enabled=True)
        },
        2: {  # Character phase
            "character_editor": InteractiveElement(element_type="form", enabled=True),
            "visual_adjuster": InteractiveElement(element_type="color_picker", enabled=True)
        },
        3: {  # Plot phase
            "plot_editor": InteractiveElement(element_type="rich_editor", enabled=True),
            "structure_adjuster": InteractiveElement(element_type="drag_drop", enabled=True)
        },
        4: {  # Name phase
            "panel_editor": InteractiveElement(element_type="grid_editor", enabled=True),
            "flow_adjuster": InteractiveElement(element_type="drag_drop", enabled=True)
        },
        5: {  # Image phase
            "image_adjuster": InteractiveElement(element_type="image_editor", enabled=True),
            "style_selector": InteractiveElement(element_type="gallery", enabled=True)
        },
        6: {  # Dialogue phase
            "dialogue_editor": InteractiveElement(element_type="text_editor", enabled=True),
            "position_adjuster": InteractiveElement(element_type="drag_drop", enabled=True)
        },
        7: {  # Integration phase
            "final_adjuster": InteractiveElement(element_type="preview_editor", enabled=True)
        }
    }
    
    return phase_elements.get(phase, {})

def _build_phase_preview_data(phase: int, phase_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build phase-specific preview data."""
    
    # Base structure with phase-specific adaptations
    if phase == 1:  # Concept
        return {
            "concept": {
                "title": phase_data.get("title", ""),
                "summary": phase_data.get("summary", ""),
                "keywords": phase_data.get("keywords", [])
            },
            "genre": {
                "primary": phase_data.get("genre", ""),
                "secondary": phase_data.get("sub_genre", ""),
                "subgenres": []
            }
        }
    elif phase == 2:  # Character
        return {
            "characters": phase_data.get("characters", []),
            "relationships": phase_data.get("relationships", {}),
            "visual_style": phase_data.get("visual_style", {})
        }
    else:
        # Generic structure for other phases
        return {
            "phase_type": f"phase_{phase}",
            "content": phase_data,
            "metadata": {
                "processing_time": phase_data.get("processing_time", 0),
                "quality_score": phase_data.get("quality_score", 0)
            }
        }

def _get_allowed_elements_for_phase(phase: int) -> List[str]:
    """Get list of editable element IDs for a phase."""
    
    phase_elements = {
        1: ["concept.title", "concept.summary", "genre.primary", "genre.secondary"],
        2: ["character.name", "character.appearance", "character.personality"],
        3: ["plot.structure", "plot.events", "plot.climax"],
        4: ["name.panels", "name.flow", "name.composition"],
        5: ["image.style", "image.quality", "image.composition"],
        6: ["dialogue.text", "dialogue.position", "dialogue.style"],
        7: ["final.layout", "final.effects", "final.optimization"]
    }
    
    return phase_elements.get(phase, [])

def _calculate_regeneration_time(change_type: ChangeType, phase: int) -> float:
    """Calculate estimated regeneration time based on change type and phase."""
    
    base_times = {
        ChangeType.TEXT_EDIT: 2.0,
        ChangeType.DRAG_DROP: 1.5,
        ChangeType.RESIZE: 1.0,
        ChangeType.COLOR_CHANGE: 3.0,
        ChangeType.STYLE_CHANGE: 5.0
    }
    
    phase_multipliers = {
        1: 1.0,  # Concept changes are quick
        2: 1.2,  # Character changes need some processing
        3: 1.1,  # Plot changes are moderate
        4: 1.5,  # Name changes require layout recalculation
        5: 2.0,  # Image changes are expensive
        6: 1.3,  # Dialogue changes need positioning
        7: 1.8   # Final integration is complex
    }
    
    base_time = base_times.get(change_type, 3.0)
    multiplier = phase_multipliers.get(phase, 1.0)
    
    return base_time * multiplier