"""Quality Gate API v1 - AI processing quality control and monitoring."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.user import User
from app.api.v1.security import (
    get_current_active_user,
    check_api_limit,
    require_permissions,
    Permissions
)
from app.services.integrated_ai_service import IntegratedAIService
from app.domain.manga.entities.session import MangaSession

router = APIRouter()

# Response Models
class PhaseQualityStatus(BaseModel):
    """Individual phase quality status."""
    phase: int
    agent_name: str
    quality_score: float
    status: str  # passed, failed, processing, skipped
    threshold: float
    retry_count: int
    max_retries: int
    last_updated: datetime
    error_message: Optional[str] = None
    processing_time: Optional[float] = None

class QualityGateResponse(BaseModel):
    """Complete quality gate status response."""
    request_id: UUID
    overall_status: str  # in_progress, completed, failed
    phases: List[PhaseQualityStatus]
    quality_report_url: Optional[str]
    overall_quality_score: Optional[float] = None
    total_processing_time: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class QualityOverride(BaseModel):
    """Quality gate override request."""
    override_reason: str = Field(..., min_length=10, max_length=500)
    admin_user_id: str
    force_proceed: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "override_reason": "User feedback indicates acceptable quality despite low score",
                "admin_user_id": "admin-uuid",
                "force_proceed": True
            }
        }

class QualityOverrideResponse(BaseModel):
    """Quality gate override response."""
    phase: int
    status: str  # override_approved, override_denied
    override_by: str
    override_at: datetime
    next_phase_started: bool
    reason: str

class PhaseQualityMetrics(BaseModel):
    """Quality metrics for a specific phase."""
    average_quality_score: float
    failure_rate: float
    average_retry_count: float
    average_processing_time: float

class SystemQualityMetrics(BaseModel):
    """System-wide quality metrics."""
    system_metrics: Dict[str, PhaseQualityMetrics]
    failure_rates: Dict[str, float]
    retry_statistics: Dict[str, float]
    period: Dict[str, datetime]
    total_sessions_processed: int
    total_processing_time: float

# Dependency injection for services
async def get_ai_service() -> IntegratedAIService:
    """Get integrated AI service instance."""
    return IntegratedAIService()

# Core Quality Gate Endpoints
@router.get("/manga/{request_id}/quality-gate", response_model=QualityGateResponse)
async def get_quality_gate_status(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit),
    ai_service: IntegratedAIService = Depends(get_ai_service)
) -> QualityGateResponse:
    """Get quality gate status for a manga generation session.
    
    Requires: manga:read permission + ownership
    """
    
    # Get session details
    session_status = await ai_service.get_session_status(str(request_id), db)
    
    if "error" in session_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {request_id}"
        )
    
    # Build phase quality status
    phases = []
    for phase_info in session_status.get("phases_completed", []):
        phase_status = PhaseQualityStatus(
            phase=phase_info["phase"],
            agent_name=phase_info["name"],
            quality_score=phase_info.get("quality_score", 0.0),
            status="passed" if phase_info.get("quality_score", 0) >= 0.7 else "failed",
            threshold=0.7,
            retry_count=phase_info.get("retry_count", 0),
            max_retries=3,
            last_updated=datetime.fromisoformat(session_status["created_at"]),
            processing_time=phase_info.get("processing_time", 0.0)
        )
        phases.append(phase_status)
    
    # Determine overall status
    overall_status = "in_progress"
    if session_status["status"] == "completed":
        overall_status = "completed"
    elif session_status["status"] == "failed":
        overall_status = "failed"
    
    # Calculate overall quality score
    overall_quality = session_status.get("quality_score", 0.0)
    
    return QualityGateResponse(
        request_id=request_id,
        overall_status=overall_status,
        phases=phases,
        quality_report_url=f"/api/v1/manga/{request_id}/quality-report",
        overall_quality_score=overall_quality,
        total_processing_time=session_status.get("total_processing_time", 0.0),
        created_at=datetime.fromisoformat(session_status["created_at"]),
        updated_at=datetime.utcnow()
    )

@router.post("/manga/{request_id}/phase/{phase}/quality-override", response_model=QualityOverrideResponse)
async def override_quality_gate(
    request_id: UUID,
    phase: int,
    override_request: QualityOverride,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions([Permissions.ADMIN]))
) -> QualityOverrideResponse:
    """Override quality gate for a specific phase (Admin only).
    
    Requires: admin permission
    """
    
    # Validate phase number
    if not (1 <= phase <= 7):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phase must be between 1 and 7"
        )
    
    # Verify session exists and get current status
    ai_service = IntegratedAIService()
    session_status = await ai_service.get_session_status(str(request_id), db)
    
    if "error" in session_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {request_id}"
        )
    
    # Check if phase exists and needs override
    phase_found = False
    for phase_info in session_status.get("phases_completed", []):
        if phase_info["phase"] == phase:
            phase_found = True
            if phase_info.get("quality_score", 0) >= 0.7:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Phase {phase} already passed quality gate"
                )
            break
    
    if not phase_found:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phase {phase} not found in session"
        )
    
    # TODO: Implement actual override logic
    # This would typically involve:
    # 1. Recording the override in the database
    # 2. Marking the phase as passed
    # 3. Triggering next phase if needed
    
    # For now, return success response
    return QualityOverrideResponse(
        phase=phase,
        status="override_approved",
        override_by=str(current_user.id),
        override_at=datetime.utcnow(),
        next_phase_started=override_request.force_proceed,
        reason=override_request.override_reason
    )

@router.get("/quality/metrics", response_model=SystemQualityMetrics)
async def get_system_quality_metrics(
    period_days: int = 7,
    current_user: User = Depends(require_permissions([Permissions.ADMIN]))
) -> SystemQualityMetrics:
    """Get system-wide quality metrics (Admin only).
    
    Requires: admin permission
    """
    
    # Calculate metrics for the specified period
    end_date = datetime.utcnow()
    start_date = datetime.utcnow().replace(day=end_date.day - period_days)
    
    # TODO: Implement actual metrics calculation from database
    # This would typically involve:
    # 1. Querying phase results from the specified period
    # 2. Calculating averages, failure rates, etc.
    # 3. Aggregating statistics by phase
    
    # Mock data for now
    system_metrics = {}
    for phase in range(1, 8):
        system_metrics[f"phase_{phase}"] = PhaseQualityMetrics(
            average_quality_score=0.80 + (phase * 0.02),  # Mock increasing quality by phase
            failure_rate=0.10 - (phase * 0.01),  # Mock decreasing failure rate
            average_retry_count=1.2,
            average_processing_time=10.0 + (phase * 2.0)
        )
    
    return SystemQualityMetrics(
        system_metrics=system_metrics,
        failure_rates={
            f"phase_{phase}": 0.10 - (phase * 0.01) 
            for phase in range(1, 8)
        },
        retry_statistics={
            "average_retries_per_phase": 1.2,
            "max_retries_exceeded_rate": 0.02
        },
        period={
            "start_date": start_date,
            "end_date": end_date
        },
        total_sessions_processed=150,  # Mock value
        total_processing_time=12500.0  # Mock value
    )

@router.get("/manga/{request_id}/quality-report")
async def get_quality_report(
    request_id: UUID,
    format: str = "json",  # json, pdf, html
    current_user: User = Depends(check_api_limit)
) -> Dict[str, Any]:
    """Get detailed quality report for a session.
    
    Requires: manga:read permission + ownership
    """
    
    # TODO: Implement detailed quality report generation
    # This would include:
    # 1. Detailed phase-by-phase analysis
    # 2. Quality score breakdowns
    # 3. Performance metrics
    # 4. Recommendations for improvement
    
    return {
        "request_id": str(request_id),
        "report_type": "quality_analysis",
        "generated_at": datetime.utcnow().isoformat(),
        "format": format,
        "summary": "Quality report generation not yet implemented",
        "download_url": f"/api/v1/reports/{request_id}/quality.{format}"
    }

# Health check endpoint for quality gates
@router.get("/quality/health")
async def quality_system_health() -> Dict[str, Any]:
    """Get quality system health status."""
    
    return {
        "status": "healthy",
        "quality_gates_active": True,
        "thresholds": {
            "minimum_acceptable": 0.60,
            "target_quality": 0.70,
            "excellence_threshold": 0.90
        },
        "retry_limits": {
            "max_retries": 3,
            "retry_delay_seconds": 2
        },
        "timestamp": datetime.utcnow().isoformat()
    }