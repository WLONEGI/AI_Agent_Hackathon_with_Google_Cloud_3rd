"""Phase result repository implementation using SQLAlchemy."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.domain.manga.entities.phase_result import PhaseResult, PhaseResultId, PhaseStatus
from app.domain.manga.repositories.phase_result_repository import PhaseResultRepository
from app.infrastructure.database.models.phase_result_model import PhaseResultModel
from app.core.database import get_db


class PhaseResultRepositoryImpl(PhaseResultRepository):
    """SQLAlchemy implementation of PhaseResultRepository."""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """Initialize with optional database session."""
        self.db_session = db_session
    
    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db_session:
            return self.db_session
        return next(get_db())
    
    def _model_to_entity(self, model: PhaseResultModel) -> PhaseResult:
        """Convert database model to domain entity."""
        # Note: In a full implementation, we would need to convert JSON quality_score back to QualityScore object
        return PhaseResult(
            id=PhaseResultId(model.id),
            session_id=model.session_id,
            phase_number=model.phase_number,
            phase_name=model.phase_name,
            status=PhaseStatus(model.status),
            started_at=model.started_at,
            completed_at=model.completed_at,
            processing_time=model.processing_time,
            input_data=model.input_data or {},
            output_data=model.output_data or {},
            intermediate_results=model.intermediate_results or [],
            quality_score=None,  # TODO: Convert from JSON to QualityScore object
            validation_results=model.validation_results or {},
            model_used=model.model_used,
            prompt_tokens=model.prompt_tokens,
            completion_tokens=model.completion_tokens,
            total_cost_usd=model.total_cost_usd,
            error_message=model.error_message,
            error_code=model.error_code,
            retry_count=model.retry_count,
            max_retries=model.max_retries,
            cpu_usage_percent=model.cpu_usage_percent,
            memory_usage_mb=model.memory_usage_mb,
            api_call_count=model.api_call_count,
            cache_hit_count=model.cache_hit_count,
            metadata=model.metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _entity_to_model_data(self, entity: PhaseResult) -> Dict[str, Any]:
        """Convert domain entity to model data."""
        return {
            "id": str(entity.id),
            "session_id": entity.session_id,
            "phase_number": entity.phase_number,
            "phase_name": entity.phase_name,
            "status": entity.status.value,
            "started_at": entity.started_at,
            "completed_at": entity.completed_at,
            "processing_time": entity.processing_time,
            "input_data": entity.input_data,
            "output_data": entity.output_data,
            "intermediate_results": entity.intermediate_results,
            "quality_score": entity.quality_score.to_dict() if entity.quality_score else None,
            "validation_results": entity.validation_results,
            "model_used": entity.model_used,
            "prompt_tokens": entity.prompt_tokens,
            "completion_tokens": entity.completion_tokens,
            "total_cost_usd": entity.total_cost_usd,
            "error_message": entity.error_message,
            "error_code": entity.error_code,
            "retry_count": entity.retry_count,
            "max_retries": entity.max_retries,
            "cpu_usage_percent": entity.cpu_usage_percent,
            "memory_usage_mb": entity.memory_usage_mb,
            "api_call_count": entity.api_call_count,
            "cache_hit_count": entity.cache_hit_count,
            "metadata": entity.metadata,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at
        }
    
    async def save(self, phase_result: PhaseResult) -> None:
        """Save or update a phase result."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(PhaseResultModel.id == str(phase_result.id))
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        model_data = self._entity_to_model_data(phase_result)
        
        if existing:
            stmt = update(PhaseResultModel).where(
                PhaseResultModel.id == str(phase_result.id)
            ).values(**model_data)
            await db.execute(stmt)
        else:
            model = PhaseResultModel(**model_data)
            db.add(model)
        
        await db.commit()
    
    async def find_by_id(self, result_id: PhaseResultId) -> Optional[PhaseResult]:
        """Find phase result by ID."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(PhaseResultModel.id == str(result_id))
        result = await db.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._model_to_entity(model) if model else None
    
    async def find_by_session_id(self, session_id: str) -> List[PhaseResult]:
        """Find all phase results for a session."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(
            PhaseResultModel.session_id == session_id
        ).order_by(PhaseResultModel.phase_number)
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_session_and_phase(
        self, 
        session_id: str, 
        phase_number: int
    ) -> Optional[PhaseResult]:
        """Find phase result by session ID and phase number."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(
            and_(
                PhaseResultModel.session_id == session_id,
                PhaseResultModel.phase_number == phase_number
            )
        )
        
        result = await db.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._model_to_entity(model) if model else None
    
    async def find_by_status(self, status: PhaseStatus) -> List[PhaseResult]:
        """Find phase results by status."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(
            PhaseResultModel.status == status.value
        ).order_by(PhaseResultModel.updated_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_phase_number(self, phase_number: int) -> List[PhaseResult]:
        """Find all results for a specific phase number."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(
            PhaseResultModel.phase_number == phase_number
        ).order_by(PhaseResultModel.updated_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_failed_phases(
        self, 
        session_id: Optional[str] = None
    ) -> List[PhaseResult]:
        """Find failed phase results."""
        db = await self._get_session()
        
        conditions = [PhaseResultModel.status == PhaseStatus.FAILED.value]
        if session_id:
            conditions.append(PhaseResultModel.session_id == session_id)
        
        stmt = select(PhaseResultModel).where(
            and_(*conditions)
        ).order_by(PhaseResultModel.updated_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_completed_phases(self, session_id: str) -> List[PhaseResult]:
        """Find completed phase results for a session."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(
            and_(
                PhaseResultModel.session_id == session_id,
                PhaseResultModel.status == PhaseStatus.COMPLETED.value
            )
        ).order_by(PhaseResultModel.phase_number)
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_in_progress_phases(self) -> List[PhaseResult]:
        """Find all phases currently in progress."""
        db = await self._get_session()
        
        in_progress_statuses = [
            PhaseStatus.IN_PROGRESS.value,
            PhaseStatus.RETRYING.value
        ]
        
        stmt = select(PhaseResultModel).where(
            PhaseResultModel.status.in_(in_progress_statuses)
        ).order_by(PhaseResultModel.updated_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_phases_needing_retry(self) -> List[PhaseResult]:
        """Find failed phases that can be retried."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(
            and_(
                PhaseResultModel.status == PhaseStatus.FAILED.value,
                PhaseResultModel.retry_count < PhaseResultModel.max_retries
            )
        )
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        phase_number: Optional[int] = None
    ) -> List[PhaseResult]:
        """Find phase results within date range."""
        db = await self._get_session()
        
        conditions = [
            PhaseResultModel.created_at >= start_date,
            PhaseResultModel.created_at <= end_date
        ]
        
        if phase_number:
            conditions.append(PhaseResultModel.phase_number == phase_number)
        
        stmt = select(PhaseResultModel).where(
            and_(*conditions)
        ).order_by(PhaseResultModel.created_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_slow_phases(self, threshold_seconds: float = 30.0) -> List[PhaseResult]:
        """Find phases that took longer than threshold."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(
            and_(
                PhaseResultModel.processing_time.is_not(None),
                PhaseResultModel.processing_time > threshold_seconds
            )
        ).order_by(PhaseResultModel.processing_time.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_high_quality_phases(self, quality_threshold: float = 0.8) -> List[PhaseResult]:
        """Find phases with high quality scores."""
        db = await self._get_session()
        
        # Note: This would require proper JSON querying for quality_score.overall_score
        # For now, we'll return an empty list as placeholder
        return []
    
    async def find_low_quality_phases(self, quality_threshold: float = 0.6) -> List[PhaseResult]:
        """Find phases with low quality scores."""
        db = await self._get_session()
        
        # Note: This would require proper JSON querying for quality_score.overall_score
        # For now, we'll return an empty list as placeholder
        return []
    
    async def count_by_phase_and_status(
        self, 
        phase_number: int, 
        status: PhaseStatus
    ) -> int:
        """Count phase results by phase number and status."""
        db = await self._get_session()
        
        stmt = select(func.count(PhaseResultModel.id)).where(
            and_(
                PhaseResultModel.phase_number == phase_number,
                PhaseResultModel.status == status.value
            )
        )
        
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    async def count_by_session(self, session_id: str) -> int:
        """Count phase results for a session."""
        db = await self._get_session()
        
        stmt = select(func.count(PhaseResultModel.id)).where(
            PhaseResultModel.session_id == session_id
        )
        
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    async def delete(self, result_id: PhaseResultId) -> bool:
        """Delete a phase result."""
        db = await self._get_session()
        
        stmt = delete(PhaseResultModel).where(
            PhaseResultModel.id == str(result_id)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0
    
    async def delete_by_session(self, session_id: str) -> int:
        """Delete all phase results for a session."""
        db = await self._get_session()
        
        stmt = delete(PhaseResultModel).where(
            PhaseResultModel.session_id == session_id
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount
    
    async def exists(self, result_id: PhaseResultId) -> bool:
        """Check if phase result exists."""
        db = await self._get_session()
        
        stmt = select(func.count(PhaseResultModel.id)).where(
            PhaseResultModel.id == str(result_id)
        )
        
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        return count > 0
    
    async def get_phase_statistics(
        self, 
        phase_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get phase processing statistics."""
        db = await self._get_session()
        
        base_query = select(PhaseResultModel)
        if phase_number:
            base_query = base_query.where(PhaseResultModel.phase_number == phase_number)
        
        # Total phases
        total_stmt = select(func.count(PhaseResultModel.id))
        if phase_number:
            total_stmt = total_stmt.where(PhaseResultModel.phase_number == phase_number)
        
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        # By status
        status_stats = {}
        for status in PhaseStatus:
            status_stmt = select(func.count(PhaseResultModel.id)).where(
                PhaseResultModel.status == status.value
            )
            if phase_number:
                status_stmt = status_stmt.where(PhaseResultModel.phase_number == phase_number)
            
            result = await db.execute(status_stmt)
            status_stats[status.value] = result.scalar() or 0
        
        # Average processing time
        avg_time_stmt = select(func.avg(PhaseResultModel.processing_time)).where(
            PhaseResultModel.processing_time.is_not(None)
        )
        if phase_number:
            avg_time_stmt = avg_time_stmt.where(PhaseResultModel.phase_number == phase_number)
        
        avg_result = await db.execute(avg_time_stmt)
        avg_processing_time = avg_result.scalar() or 0.0
        
        # Average cost
        avg_cost_stmt = select(func.avg(PhaseResultModel.total_cost_usd))
        if phase_number:
            avg_cost_stmt = avg_cost_stmt.where(PhaseResultModel.phase_number == phase_number)
        
        cost_result = await db.execute(avg_cost_stmt)
        avg_cost = cost_result.scalar() or 0.0
        
        return {
            "total": total,
            "by_status": status_stats,
            "avg_processing_time": avg_processing_time,
            "avg_cost_usd": avg_cost,
            "phase_number": phase_number
        }
    
    async def get_session_phase_progress(self, session_id: str) -> Dict[int, PhaseStatus]:
        """Get phase progress map for a session."""
        db = await self._get_session()
        
        stmt = select(
            PhaseResultModel.phase_number,
            PhaseResultModel.status
        ).where(PhaseResultModel.session_id == session_id)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        return {
            row.phase_number: PhaseStatus(row.status)
            for row in rows
        }
    
    async def find_phases_with_high_cost(self, cost_threshold: float = 0.10) -> List[PhaseResult]:
        """Find phases with high processing cost."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(
            PhaseResultModel.total_cost_usd > cost_threshold
        ).order_by(PhaseResultModel.total_cost_usd.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_phases_by_model(self, model_name: str) -> List[PhaseResult]:
        """Find phases processed by specific AI model."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(
            PhaseResultModel.model_used == model_name
        ).order_by(PhaseResultModel.created_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def get_average_processing_time(self, phase_number: int) -> Optional[float]:
        """Get average processing time for a phase."""
        db = await self._get_session()
        
        stmt = select(func.avg(PhaseResultModel.processing_time)).where(
            and_(
                PhaseResultModel.phase_number == phase_number,
                PhaseResultModel.processing_time.is_not(None)
            )
        )
        
        result = await db.execute(stmt)
        return result.scalar()
    
    async def get_success_rate(self, phase_number: int) -> float:
        """Get success rate for a phase."""
        db = await self._get_session()
        
        # Total count
        total_stmt = select(func.count(PhaseResultModel.id)).where(
            PhaseResultModel.phase_number == phase_number
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        if total == 0:
            return 0.0
        
        # Success count
        success_stmt = select(func.count(PhaseResultModel.id)).where(
            and_(
                PhaseResultModel.phase_number == phase_number,
                PhaseResultModel.status == PhaseStatus.COMPLETED.value
            )
        )
        success_result = await db.execute(success_stmt)
        success = success_result.scalar() or 0
        
        return success / total
    
    async def find_phases_with_retries(self) -> List[PhaseResult]:
        """Find phases that required retries."""
        db = await self._get_session()
        
        stmt = select(PhaseResultModel).where(
            PhaseResultModel.retry_count > 0
        ).order_by(PhaseResultModel.retry_count.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def update_processing_metrics(
        self,
        result_id: PhaseResultId,
        cpu_usage: float,
        memory_usage: float,
        api_calls: int = 0,
        cache_hits: int = 0
    ) -> bool:
        """Update performance metrics for a phase result."""
        db = await self._get_session()
        
        stmt = update(PhaseResultModel).where(
            PhaseResultModel.id == str(result_id)
        ).values(
            cpu_usage_percent=cpu_usage,
            memory_usage_mb=memory_usage,
            api_call_count=PhaseResultModel.api_call_count + api_calls,
            cache_hit_count=PhaseResultModel.cache_hit_count + cache_hits,
            updated_at=datetime.utcnow()
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0
    
    async def bulk_update_status(
        self,
        result_ids: List[PhaseResultId],
        new_status: PhaseStatus
    ) -> int:
        """Bulk update phase result statuses."""
        db = await self._get_session()
        
        id_strings = [str(rid) for rid in result_ids]
        
        stmt = update(PhaseResultModel).where(
            PhaseResultModel.id.in_(id_strings)
        ).values(
            status=new_status.value,
            updated_at=datetime.utcnow()
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount