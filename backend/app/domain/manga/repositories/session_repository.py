"""Session repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.domain.manga.entities.session import MangaSession, SessionId, SessionStatus


class SessionRepository(ABC):
    """Abstract repository interface for manga sessions."""
    
    @abstractmethod
    async def save(self, session: MangaSession) -> None:
        """Save or update a manga session."""
        pass
    
    @abstractmethod
    async def find_by_id(self, session_id: SessionId) -> Optional[MangaSession]:
        """Find session by ID."""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[MangaSession]:
        """Find all sessions for a user."""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: SessionStatus) -> List[MangaSession]:
        """Find sessions by status."""
        pass
    
    @abstractmethod
    async def find_active_sessions(self) -> List[MangaSession]:
        """Find all active (in progress or waiting feedback) sessions."""
        pass
    
    @abstractmethod
    async def find_by_user_and_status(
        self, 
        user_id: str, 
        status: SessionStatus
    ) -> List[MangaSession]:
        """Find sessions by user ID and status."""
        pass
    
    @abstractmethod
    async def find_stale_sessions(self, timeout_minutes: int = 60) -> List[MangaSession]:
        """Find sessions that have been inactive for specified minutes."""
        pass
    
    @abstractmethod
    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> List[MangaSession]:
        """Find sessions created within date range."""
        pass
    
    @abstractmethod
    async def count_by_status(self, status: SessionStatus) -> int:
        """Count sessions by status."""
        pass
    
    @abstractmethod
    async def count_by_user(self, user_id: str) -> int:
        """Count sessions by user."""
        pass
    
    @abstractmethod
    async def delete(self, session_id: SessionId) -> bool:
        """Delete a session. Returns True if deleted, False if not found."""
        pass
    
    @abstractmethod
    async def exists(self, session_id: SessionId) -> bool:
        """Check if session exists."""
        pass
    
    @abstractmethod
    async def find_sessions_needing_cleanup(self, days_old: int = 30) -> List[SessionId]:
        """Find session IDs that are candidates for cleanup."""
        pass
    
    @abstractmethod
    async def get_session_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get session statistics."""
        pass
    
    @abstractmethod
    async def find_sessions_with_quality_below(
        self, 
        threshold: float,
        limit: Optional[int] = None
    ) -> List[MangaSession]:
        """Find sessions with final quality score below threshold."""
        pass
    
    @abstractmethod
    async def find_user_recent_sessions(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[MangaSession]:
        """Find user's most recent sessions."""
        pass
    
    @abstractmethod
    async def update_session_status(
        self, 
        session_id: SessionId, 
        status: SessionStatus
    ) -> bool:
        """Update session status only. Returns True if updated."""
        pass
    
    @abstractmethod
    async def bulk_update_status(
        self,
        session_ids: List[SessionId],
        new_status: SessionStatus
    ) -> int:
        """Bulk update session statuses. Returns count of updated sessions."""
        pass
    
    @abstractmethod
    async def find_sessions_by_phase(self, phase_number: int) -> List[MangaSession]:
        """Find sessions currently in specified phase."""
        pass
    
    @abstractmethod
    async def find_retry_candidate_sessions(self, max_retry_count: int = 3) -> List[MangaSession]:
        """Find failed sessions that can be retried."""
        pass