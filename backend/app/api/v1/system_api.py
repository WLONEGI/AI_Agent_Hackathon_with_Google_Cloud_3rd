"""System API v1 - System capabilities and information (API Design Document Compliant)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

# Response Models (Design Document Compliant)
class ProcessingTimeEstimate(BaseModel):
    """Processing time estimation (API Design Document Compliant)."""
    per_1000_chars: int = Field(96, description="Processing time per 1000 characters in seconds")
    base_time: int = Field(300, description="Base processing time in seconds")

class SystemCapabilitiesResponse(BaseModel):
    """System capabilities response (API Design Document Compliant)."""
    supported_styles: List[str] = Field(..., description="Supported art styles")
    max_pages: int = Field(..., description="Maximum pages per manga")
    max_text_length: int = Field(..., description="Maximum text input length")
    max_characters: int = Field(..., description="Maximum character count")
    languages: List[str] = Field(..., description="Supported languages")
    file_formats: List[str] = Field(..., description="Supported output formats")
    processing_time_estimate: ProcessingTimeEstimate = Field(..., description="Processing time estimates")


# ===== DESIGN DOCUMENT COMPLIANT ENDPOINTS =====

@router.get("/capabilities", response_model=SystemCapabilitiesResponse)
async def get_system_capabilities(
    db: AsyncSession = Depends(get_db)
) -> SystemCapabilitiesResponse:
    """Get system capabilities information (GET /api/v1/system/capabilities).
    
    Fully complies with API design document specification.
    Returns system limits, supported features, and processing estimates.
    
    Public endpoint - no authentication required.
    """
    
    return SystemCapabilitiesResponse(
        supported_styles=["realistic", "anime", "cartoon", "sketch", "watercolor"],
        max_pages=100,
        max_text_length=50000,
        max_characters=5,
        languages=["ja", "en"],
        file_formats=["pdf", "webp"],
        processing_time_estimate=ProcessingTimeEstimate(
            per_1000_chars=96,
            base_time=300
        )
    )