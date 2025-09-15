"""Session repository implementation using SQLAlchemy."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.domain.manga.entities.session import MangaSession, SessionId, SessionStatus
from app.domain.manga.repositories.session_repository import SessionRepository
from app.infrastructure.database.models.manga_session_model import MangaSessionModel
from app.core.database import get_db


class SessionRepositoryImpl(SessionRepository):
    """SQLAlchemy implementation of SessionRepository."""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """Initialize with optional database session."""
        self.db_session = db_session
    
    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db_session:
            return self.db_session
        return next(get_db())
    
    def _model_to_entity(self, model: MangaSessionModel) -> MangaSession:
        """Convert database model to domain entity."""
        return MangaSession(
            id=SessionId(model.id),
            user_id=model.user_id,
            title=model.title,
            input_text=model.input_text,
            status=SessionStatus(model.status),
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            updated_at=model.updated_at,
            current_phase=model.current_phase,
            total_phases=model.total_phases,
            phase_results=model.phase_results or {},
            quality_scores=model.quality_scores or {},
            quality_score=model.quality_score,
            total_processing_time_ms=model.total_processing_time_ms,
            preview_url=model.preview_url,
            download_url=model.download_url,
            output_metadata=model.output_metadata or {},
            error_message=model.error_message,
            retry_count=model.retry_count,
            hitl_enabled=model.hitl_enabled,
            feedback_sessions=model.feedback_sessions or []
        )
    
    def _entity_to_model_data(self, entity: MangaSession) -> Dict[str, Any]:
        """Convert domain entity to model data for database operations."""
        return {
            "id": str(entity.id),
            "user_id": entity.user_id,
            "title": entity.title,
            "input_text": entity.input_text,
            "status": entity.status.value,
            "created_at": entity.created_at,
            "started_at": entity.started_at,
            "completed_at": entity.completed_at,
            "updated_at": entity.updated_at,
            "current_phase": entity.current_phase,
            "total_phases": entity.total_phases,
            "phase_results": entity.phase_results,
            "quality_scores": {k: v.to_dict() if hasattr(v, 'to_dict') else v
                             for k, v in entity.quality_scores.items()},
            "quality_score": entity.quality_score,
            "total_processing_time_ms": entity.total_processing_time_ms,
            "preview_url": entity.preview_url,
            "download_url": entity.download_url,
            "output_metadata": entity.output_metadata,
            "error_message": entity.error_message,
            "retry_count": entity.retry_count,
            "hitl_enabled": entity.hitl_enabled,
            "feedback_sessions": entity.feedback_sessions
        }
    
    async def save(self, session: MangaSession) -> None:
        """Save or update a manga session."""
        db = await self._get_session()
        
        # Check if exists
        stmt = select(MangaSessionModel).where(MangaSessionModel.id == str(session.id))
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        model_data = self._entity_to_model_data(session)
        
        if existing:
            # Update existing
            stmt = update(MangaSessionModel).where(
                MangaSessionModel.id == str(session.id)
            ).values(**model_data)
            await db.execute(stmt)
        else:
            # Create new
            model = MangaSessionModel(**model_data)
            db.add(model)
        
        await db.commit()
    
    async def find_by_id(self, session_id: SessionId) -> Optional[MangaSession]:
        """Find session by ID."""
        db = await self._get_session()
        
        stmt = select(MangaSessionModel).where(MangaSessionModel.id == str(session_id))
        result = await db.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._model_to_entity(model) if model else None
    
    async def find_by_user_id(self, user_id: str) -> List[MangaSession]:
        """Find all sessions for a user."""
        db = await self._get_session()
        
        stmt = select(MangaSessionModel).where(
            MangaSessionModel.user_id == user_id
        ).order_by(MangaSessionModel.created_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_status(self, status: SessionStatus) -> List[MangaSession]:
        """Find sessions by status."""
        db = await self._get_session()
        
        stmt = select(MangaSessionModel).where(
            MangaSessionModel.status == status.value
        ).order_by(MangaSessionModel.updated_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_active_sessions(self) -> List[MangaSession]:
        """Find all active sessions."""
        db = await self._get_session()
        
        active_statuses = [
            SessionStatus.IN_PROGRESS.value,
            SessionStatus.WAITING_FEEDBACK.value
        ]
        
        stmt = select(MangaSessionModel).where(
            MangaSessionModel.status.in_(active_statuses)
        ).order_by(MangaSessionModel.updated_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_user_and_status(
        self, 
        user_id: str, 
        status: SessionStatus
    ) -> List[MangaSession]:
        """Find sessions by user ID and status."""
        db = await self._get_session()
        
        stmt = select(MangaSessionModel).where(
            and_(
                MangaSessionModel.user_id == user_id,
                MangaSessionModel.status == status.value
            )
        ).order_by(MangaSessionModel.updated_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_stale_sessions(self, timeout_minutes: int = 60) -> List[MangaSession]:
        """Find sessions that have been inactive."""
        db = await self._get_session()
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        active_statuses = [
            SessionStatus.IN_PROGRESS.value,
            SessionStatus.WAITING_FEEDBACK.value
        ]
        
        stmt = select(MangaSessionModel).where(
            and_(
                MangaSessionModel.status.in_(active_statuses),
                MangaSessionModel.updated_at < cutoff_time
            )
        )
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> List[MangaSession]:
        """Find sessions created within date range."""
        db = await self._get_session()
        
        conditions = [
            MangaSessionModel.created_at >= start_date,
            MangaSessionModel.created_at <= end_date
        ]
        
        if user_id:
            conditions.append(MangaSessionModel.user_id == user_id)
        
        stmt = select(MangaSessionModel).where(
            and_(*conditions)
        ).order_by(MangaSessionModel.created_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def count_by_status(self, status: SessionStatus) -> int:
        """Count sessions by status."""
        db = await self._get_session()
        
        stmt = select(func.count(MangaSessionModel.id)).where(
            MangaSessionModel.status == status.value
        )
        
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    async def count_by_user(self, user_id: str) -> int:
        """Count sessions by user."""
        db = await self._get_session()
        
        stmt = select(func.count(MangaSessionModel.id)).where(
            MangaSessionModel.user_id == user_id
        )
        
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    async def delete(self, session_id: SessionId) -> bool:
        """Delete a session."""
        db = await self._get_session()
        
        stmt = delete(MangaSessionModel).where(
            MangaSessionModel.id == str(session_id)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0
    
    async def exists(self, session_id: SessionId) -> bool:
        """Check if session exists."""
        db = await self._get_session()
        
        stmt = select(func.count(MangaSessionModel.id)).where(
            MangaSessionModel.id == str(session_id)
        )
        
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        return count > 0
    
    async def find_sessions_needing_cleanup(self, days_old: int = 30) -> List[SessionId]:
        """Find session IDs that are candidates for cleanup."""
        db = await self._get_session()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        cleanup_statuses = [
            SessionStatus.COMPLETED.value,
            SessionStatus.FAILED.value,
            SessionStatus.CANCELLED.value
        ]
        
        stmt = select(MangaSessionModel.id).where(
            and_(
                MangaSessionModel.status.in_(cleanup_statuses),
                MangaSessionModel.completed_at < cutoff_date
            )
        )
        
        result = await db.execute(stmt)
        session_ids = result.scalars().all()
        
        return [SessionId(sid) for sid in session_ids]
    
    async def get_session_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get session statistics."""
        db = await self._get_session()
        
        base_query = select(MangaSessionModel)
        if user_id:
            base_query = base_query.where(MangaSessionModel.user_id == user_id)
        
        # Total sessions
        total_stmt = select(func.count(MangaSessionModel.id))
        if user_id:
            total_stmt = total_stmt.where(MangaSessionModel.user_id == user_id)
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        # By status
        status_stats = {}
        for status in SessionStatus:
            status_stmt = select(func.count(MangaSessionModel.id)).where(
                MangaSessionModel.status == status.value
            )
            if user_id:
                status_stmt = status_stmt.where(MangaSessionModel.user_id == user_id)
            
            result = await db.execute(status_stmt)
            status_stats[status.value] = result.scalar() or 0
        
        # Average processing time for completed sessions
        avg_time_stmt = select(func.avg(MangaSessionModel.total_processing_time_ms)).where(
            MangaSessionModel.status == SessionStatus.COMPLETED.value
        )
        if user_id:
            avg_time_stmt = avg_time_stmt.where(MangaSessionModel.user_id == user_id)
        
        avg_result = await db.execute(avg_time_stmt)
        avg_processing_time = avg_result.scalar() or 0.0
        
        # Success rate
        completed = status_stats.get(SessionStatus.COMPLETED.value, 0)
        success_rate = completed / total if total > 0 else 0.0
        
        return {
            "total": total,
            "by_status": status_stats,
            "completed": completed,
            "success_rate": success_rate,
            "avg_completion_time": avg_processing_time
        }
    
    async def find_sessions_with_quality_below(
        self, 
        threshold: float,
        limit: Optional[int] = None
    ) -> List[MangaSession]:
        """Find sessions with quality below threshold."""
        db = await self._get_session()
        
        stmt = select(MangaSessionModel).where(
            and_(
                MangaSessionModel.quality_score.is_not(None),
                MangaSessionModel.quality_score < threshold
            )
        ).order_by(MangaSessionModel.quality_score.asc())
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_user_recent_sessions(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[MangaSession]:
        """Find user's most recent sessions."""
        db = await self._get_session()
        
        stmt = select(MangaSessionModel).where(
            MangaSessionModel.user_id == user_id
        ).order_by(MangaSessionModel.created_at.desc()).limit(limit)
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def update_session_status(
        self, 
        session_id: SessionId, 
        status: SessionStatus
    ) -> bool:
        """Update session status only."""
        db = await self._get_session()
        
        stmt = update(MangaSessionModel).where(
            MangaSessionModel.id == str(session_id)
        ).values(
            status=status.value,
            updated_at=datetime.utcnow()
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0
    
    async def bulk_update_status(
        self,
        session_ids: List[SessionId],
        new_status: SessionStatus
    ) -> int:
        """Bulk update session statuses."""
        db = await self._get_session()
        
        id_strings = [str(sid) for sid in session_ids]
        
        stmt = update(MangaSessionModel).where(
            MangaSessionModel.id.in_(id_strings)
        ).values(
            status=new_status.value,
            updated_at=datetime.utcnow()
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount
    
    async def find_sessions_by_phase(self, phase_number: int) -> List[MangaSession]:
        """Find sessions currently in specified phase."""
        db = await self._get_session()
        
        stmt = select(MangaSessionModel).where(
            and_(
                MangaSessionModel.current_phase == phase_number,
                MangaSessionModel.status == SessionStatus.IN_PROGRESS.value
            )
        )
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_retry_candidate_sessions(self, max_retry_count: int = 3) -> List[MangaSession]:
        """Find failed sessions that can be retried."""
        db = await self._get_session()
        
        stmt = select(MangaSessionModel).where(
            and_(
                MangaSessionModel.status == SessionStatus.FAILED.value,
                MangaSessionModel.retry_count < max_retry_count
            )
        )
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]