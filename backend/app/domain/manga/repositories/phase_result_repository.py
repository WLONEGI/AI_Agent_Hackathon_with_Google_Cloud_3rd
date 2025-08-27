"""Phase result repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.domain.manga.entities.phase_result import PhaseResult, PhaseResultId, PhaseStatus


class PhaseResultRepository(ABC):
    """Abstract repository interface for phase results."""
    
    @abstractmethod
    async def save(self, phase_result: PhaseResult) -> None:
        """Save or update a phase result."""
        pass
    
    @abstractmethod
    async def find_by_id(self, result_id: PhaseResultId) -> Optional[PhaseResult]:
        """Find phase result by ID."""
        pass
    
    @abstractmethod
    async def find_by_session_id(self, session_id: str) -> List[PhaseResult]:
        """Find all phase results for a session."""
        pass
    
    @abstractmethod
    async def find_by_session_and_phase(
        self, 
        session_id: str, 
        phase_number: int
    ) -> Optional[PhaseResult]:
        """Find phase result by session ID and phase number."""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: PhaseStatus) -> List[PhaseResult]:
        """Find phase results by status."""
        pass
    
    @abstractmethod
    async def find_by_phase_number(self, phase_number: int) -> List[PhaseResult]:
        """Find all results for a specific phase number."""
        pass
    
    @abstractmethod
    async def find_failed_phases(
        self, 
        session_id: Optional[str] = None
    ) -> List[PhaseResult]:
        """Find failed phase results, optionally filtered by session."""
        pass
    
    @abstractmethod
    async def find_completed_phases(
        self, 
        session_id: str
    ) -> List[PhaseResult]:
        """Find completed phase results for a session."""
        pass
    
    @abstractmethod
    async def find_in_progress_phases(self) -> List[PhaseResult]:
        """Find all phases currently in progress."""
        pass
    
    @abstractmethod
    async def find_phases_needing_retry(self) -> List[PhaseResult]:
        """Find failed phases that can be retried."""
        pass
    
    @abstractmethod
    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        phase_number: Optional[int] = None
    ) -> List[PhaseResult]:
        """Find phase results within date range."""
        pass
    
    @abstractmethod
    async def find_slow_phases(
        self, 
        threshold_seconds: float = 30.0
    ) -> List[PhaseResult]:
        """Find phases that took longer than threshold to complete."""
        pass
    
    @abstractmethod
    async def find_high_quality_phases(
        self, 
        quality_threshold: float = 0.8
    ) -> List[PhaseResult]:
        """Find phases with quality score above threshold."""
        pass
    
    @abstractmethod
    async def find_low_quality_phases(
        self, 
        quality_threshold: float = 0.6
    ) -> List[PhaseResult]:
        """Find phases with quality score below threshold."""
        pass
    
    @abstractmethod
    async def count_by_phase_and_status(
        self, 
        phase_number: int, 
        status: PhaseStatus
    ) -> int:
        """Count phase results by phase number and status."""
        pass
    
    @abstractmethod
    async def count_by_session(self, session_id: str) -> int:
        """Count phase results for a session."""
        pass
    
    @abstractmethod
    async def delete(self, result_id: PhaseResultId) -> bool:
        """Delete a phase result. Returns True if deleted."""
        pass
    
    @abstractmethod
    async def delete_by_session(self, session_id: str) -> int:
        """Delete all phase results for a session. Returns count deleted."""
        pass
    
    @abstractmethod
    async def exists(self, result_id: PhaseResultId) -> bool:
        """Check if phase result exists."""
        pass
    
    @abstractmethod
    async def get_phase_statistics(
        self, 
        phase_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get phase processing statistics."""
        pass
    
    @abstractmethod
    async def get_session_phase_progress(self, session_id: str) -> Dict[int, PhaseStatus]:
        """Get phase progress map for a session."""
        pass
    
    @abstractmethod
    async def find_phases_with_high_cost(
        self, 
        cost_threshold: float = 0.10
    ) -> List[PhaseResult]:
        """Find phases with processing cost above threshold (USD)."""
        pass
    
    @abstractmethod
    async def find_phases_by_model(self, model_name: str) -> List[PhaseResult]:
        """Find phase results processed by specific AI model."""
        pass
    
    @abstractmethod
    async def get_average_processing_time(
        self, 
        phase_number: int
    ) -> Optional[float]:
        """Get average processing time for a phase."""
        pass
    
    @abstractmethod
    async def get_success_rate(self, phase_number: int) -> float:
        """Get success rate for a phase (0.0 to 1.0)."""
        pass
    
    @abstractmethod
    async def find_phases_with_retries(self) -> List[PhaseResult]:
        """Find phase results that required retries."""
        pass
    
    @abstractmethod
    async def update_processing_metrics(
        self,
        result_id: PhaseResultId,
        cpu_usage: float,
        memory_usage: float,
        api_calls: int = 0,
        cache_hits: int = 0
    ) -> bool:
        """Update performance metrics for a phase result."""
        pass
    
    @abstractmethod
    async def bulk_update_status(
        self,
        result_ids: List[PhaseResultId],
        new_status: PhaseStatus
    ) -> int:
        """Bulk update phase result statuses. Returns count updated."""
        pass