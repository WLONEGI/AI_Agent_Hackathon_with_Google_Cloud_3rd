"""Manga generation domain service."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from app.domain.manga.entities.session import MangaSession, SessionId, SessionStatus
from app.domain.manga.entities.phase_result import PhaseResult, PhaseStatus
from app.domain.manga.entities.generated_content import GeneratedContent, ContentStatus
from app.domain.manga.value_objects.generation_params import GenerationParameters
from app.domain.manga.value_objects.quality_metrics import QualityScore
from app.domain.manga.repositories.session_repository import SessionRepository
from app.domain.manga.repositories.phase_result_repository import PhaseResultRepository
from app.domain.manga.repositories.generated_content_repository import GeneratedContentRepository


class MangaGenerationService:
    """Domain service for manga generation orchestration."""
    
    def __init__(
        self,
        session_repository: SessionRepository,
        phase_result_repository: PhaseResultRepository,
        content_repository: GeneratedContentRepository
    ):
        self.session_repository = session_repository
        self.phase_result_repository = phase_result_repository
        self.content_repository = content_repository
    
    async def start_manga_generation(
        self,
        user_id: str,
        input_text: str,
        generation_params: GenerationParameters,
        title: Optional[str] = None
    ) -> MangaSession:
        """Start a new manga generation session."""
        # Create new session
        session = MangaSession(
            user_id=user_id,
            title=title or self._generate_title_from_input(input_text),
            input_text=input_text,
            generation_params=generation_params,
            hitl_enabled=generation_params.enable_hitl
        )
        
        # Start the generation process
        session.start_generation()
        
        # Save session
        await self.session_repository.save(session)
        
        return session
    
    async def advance_to_next_phase(
        self,
        session_id: SessionId,
        current_phase_result: Dict[str, Any],
        quality_score: Optional[QualityScore] = None
    ) -> MangaSession:
        """Complete current phase and advance to next."""
        session = await self.session_repository.find_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        current_phase = session.current_phase
        
        # Complete current phase
        session.complete_phase(current_phase, current_phase_result, quality_score)
        
        # Check if we need HITL feedback
        if self._requires_human_feedback(session, quality_score):
            session.request_feedback(current_phase)
        elif current_phase < session.total_phases:
            # Advance to next phase
            session.advance_to_phase(current_phase + 1)
        
        # Save updated session
        await self.session_repository.save(session)
        
        return session
    
    async def handle_hitl_feedback(
        self,
        session_id: SessionId,
        phase_number: int,
        feedback: Dict[str, Any],
        approved: bool
    ) -> MangaSession:
        """Handle human-in-the-loop feedback."""
        session = await self.session_repository.find_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        if not session.can_receive_feedback():
            raise ValueError("Session is not waiting for feedback")
        
        # Process feedback
        session.receive_feedback(phase_number, feedback)
        
        if approved:
            # Continue to next phase if approved
            if phase_number < session.total_phases:
                session.advance_to_phase(phase_number + 1)
        else:
            # Handle rejection - might need to retry phase
            await self._handle_phase_rejection(session, phase_number, feedback)
        
        # Save updated session
        await self.session_repository.save(session)
        
        return session
    
    async def retry_failed_session(self, session_id: SessionId) -> MangaSession:
        """Retry a failed manga generation session."""
        session = await self.session_repository.find_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        if session.status != SessionStatus.FAILED:
            raise ValueError("Can only retry failed sessions")
        
        # Retry the session
        session.retry_generation()
        
        # Reset to beginning or failed phase
        failed_phase = await self._find_failed_phase(session_id)
        if failed_phase:
            session.current_phase = failed_phase.phase_number
        else:
            session.current_phase = 1
        
        # Save updated session
        await self.session_repository.save(session)
        
        return session
    
    async def pause_generation(
        self,
        session_id: SessionId,
        reason: Optional[str] = None
    ) -> MangaSession:
        """Pause an active generation session."""
        session = await self.session_repository.find_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.pause_generation(reason)
        
        # Save updated session
        await self.session_repository.save(session)
        
        return session
    
    async def resume_generation(self, session_id: SessionId) -> MangaSession:
        """Resume a paused generation session."""
        session = await self.session_repository.find_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.resume_generation()
        
        # Save updated session
        await self.session_repository.save(session)
        
        return session
    
    async def cancel_generation(
        self,
        session_id: SessionId,
        reason: Optional[str] = None
    ) -> MangaSession:
        """Cancel a generation session."""
        session = await self.session_repository.find_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.cancel_generation(reason)
        
        # Save updated session
        await self.session_repository.save(session)
        
        return session
    
    async def get_session_progress(self, session_id: SessionId) -> Dict[str, Any]:
        """Get detailed progress information for a session."""
        session = await self.session_repository.find_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Get phase results
        phase_results = await self.phase_result_repository.find_by_session_id(str(session_id))
        
        # Get generated content
        content_items = await self.content_repository.find_by_session_id(str(session_id))
        
        return {
            "session": {
                "id": str(session.id),
                "status": session.status.value,
                "current_phase": session.current_phase,
                "total_phases": session.total_phases,
                "progress_percentage": session.get_progress_percentage(),
                "estimated_remaining_time": session.get_estimated_remaining_time(),
                "is_active": session.is_active(),
                "is_completed": session.is_completed(),
                "is_failed": session.is_failed()
            },
            "phases": [
                {
                    "phase_number": result.phase_number,
                    "status": result.status.value,
                    "processing_time": result.processing_time,
                    "quality_score": result.quality_score.overall_score if result.quality_score else None,
                    "error_message": result.error_message,
                    "retry_count": result.retry_count
                }
                for result in sorted(phase_results, key=lambda x: x.phase_number)
            ],
            "content": [
                {
                    "id": str(content.id),
                    "type": content.content_type.value,
                    "status": content.status.value,
                    "phase_number": content.phase_number,
                    "quality_score": content.quality_score.overall_score if content.quality_score else None,
                    "preview": content.get_content_preview(200)
                }
                for content in sorted(content_items, key=lambda x: (x.phase_number, x.created_at))
            ]
        }
    
    async def cleanup_stale_sessions(self, timeout_minutes: int = 60) -> int:
        """Clean up stale sessions that have been inactive."""
        stale_sessions = await self.session_repository.find_stale_sessions(timeout_minutes)
        
        cleanup_count = 0
        for session in stale_sessions:
            try:
                session.pause_generation("Session timed out due to inactivity")
                await self.session_repository.save(session)
                cleanup_count += 1
            except Exception as e:
                # Log error but continue with other sessions
                continue
        
        return cleanup_count
    
    async def get_generation_statistics(
        self,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get generation statistics."""
        end_date = datetime.utcnow()
        start_date = end_date.replace(day=end_date.day - days)
        
        # Get session statistics
        session_stats = await self.session_repository.get_session_statistics(user_id)
        
        # Get phase statistics
        phase_stats = await self.phase_result_repository.get_phase_statistics()
        
        # Get content statistics
        content_stats = await self.content_repository.get_content_statistics()
        
        return {
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "sessions": session_stats,
            "phases": phase_stats,
            "content": content_stats,
            "summary": {
                "total_sessions": session_stats.get("total", 0),
                "completed_sessions": session_stats.get("completed", 0),
                "success_rate": session_stats.get("success_rate", 0.0),
                "average_completion_time": session_stats.get("avg_completion_time", 0.0),
                "total_content_generated": content_stats.get("total", 0)
            }
        }
    
    def _generate_title_from_input(self, input_text: str) -> str:
        """Generate a title from input text."""
        # Simple title generation - in practice, this might use AI
        words = input_text.split()[:5]
        title = " ".join(words)
        if len(title) > 50:
            title = title[:47] + "..."
        return title or "マンガ作品"
    
    def _requires_human_feedback(
        self,
        session: MangaSession,
        quality_score: Optional[QualityScore]
    ) -> bool:
        """Determine if human feedback is required."""
        if not session.hitl_enabled:
            return False
        
        # Critical phases always require feedback
        critical_phases = {4, 5}  # Name and Image generation
        if session.current_phase in critical_phases:
            return True
        
        # Low quality scores require feedback
        if quality_score and quality_score.overall_score < session.generation_params.quality_threshold:
            return True
        
        return False
    
    async def _handle_phase_rejection(
        self,
        session: MangaSession,
        phase_number: int,
        feedback: Dict[str, Any]
    ) -> None:
        """Handle rejection of a phase result."""
        # Find the phase result
        phase_result = await self.phase_result_repository.find_by_session_and_phase(
            str(session.id), phase_number
        )
        
        if phase_result and phase_result.can_retry():
            # Retry the phase
            phase_result.retry_processing()
            await self.phase_result_repository.save(phase_result)
            
            # Reset session to retry phase
            session.current_phase = phase_number
        else:
            # Max retries exceeded - fail the session
            session.fail_generation("Phase rejected and max retries exceeded")
    
    async def _find_failed_phase(self, session_id: SessionId) -> Optional[PhaseResult]:
        """Find the first failed phase in a session."""
        phase_results = await self.phase_result_repository.find_by_session_id(str(session_id))
        
        for result in sorted(phase_results, key=lambda x: x.phase_number):
            if result.status == PhaseStatus.FAILED:
                return result
        
        return None