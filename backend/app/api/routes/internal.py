from __future__ import annotations

from fastapi import APIRouter

# Internal routes router - currently no endpoints needed
# Cloud Tasks functionality has been replaced with direct processing
router = APIRouter(prefix="/internal", tags=["internal"])
