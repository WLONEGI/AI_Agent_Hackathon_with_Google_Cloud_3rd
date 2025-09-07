"""Generated content repository implementation using SQLAlchemy."""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.domain.manga.entities.generated_content import (
    GeneratedContent, ContentId, ContentType, ContentStatus, ContentFormat
)
from app.domain.manga.repositories.generated_content_repository import GeneratedContentRepository
from app.infrastructure.database.models.generated_content_model import GeneratedContentModel
from app.core.database import get_db


class GeneratedContentRepositoryImpl(GeneratedContentRepository):
    """SQLAlchemy implementation of GeneratedContentRepository."""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """Initialize with optional database session."""
        self.db_session = db_session
    
    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db_session:
            return self.db_session
        return next(get_db())
    
    def _model_to_entity(self, model: GeneratedContentModel) -> GeneratedContent:
        """Convert database model to domain entity."""
        # Determine content data based on what's stored
        content_data = model.content_data
        if content_data is None and model.content_text:
            content_data = model.content_text
        elif content_data is None and model.content_binary:
            content_data = model.content_binary
        
        return GeneratedContent(
            id=ContentId(model.id),
            session_id=model.session_id,
            phase_number=model.phase_number,
            phase_result_id=model.phase_result_id,
            content_type=ContentType(model.content_type),
            content_format=ContentFormat(model.content_format),
            title=model.title,
            description=model.description,
            content_data=content_data or "",
            content_url=model.content_url,
            content_size_bytes=model.content_size_bytes,
            content_hash=model.content_hash,
            generated_by=model.generated_by,
            generation_prompt=model.generation_prompt,
            generation_params=model.generation_params or {},
            status=ContentStatus(model.status),
            version=model.version,
            parent_content_id=ContentId(model.parent_content_id) if model.parent_content_id else None,
            quality_score=None,  # TODO: Convert from JSON to QualityScore object
            validation_results=model.validation_results or {},
            auto_approved=model.auto_approved,
            hitl_feedback=model.hitl_feedback or {},
            feedback_count=model.feedback_count,
            approval_score=model.approval_score,
            related_content_ids=[ContentId(cid) for cid in (model.related_content_ids or [])],
            dependencies=[ContentId(did) for did in (model.dependencies or [])],
            tags=model.tags or [],
            generation_time_seconds=model.generation_time_seconds,
            processing_cost_usd=model.processing_cost_usd,
            storage_cost_usd=model.storage_cost_usd,
            created_at=model.created_at,
            updated_at=model.updated_at,
            approved_at=model.approved_at,
            finalized_at=model.finalized_at,
            archived_at=model.archived_at,
            metadata=model.metadata or {}
        )
    
    def _entity_to_model_data(self, entity: GeneratedContent) -> Dict[str, Any]:
        """Convert domain entity to model data."""
        # Determine how to store content data
        content_data = None
        content_text = None
        content_binary = None
        
        if isinstance(entity.content_data, str):
            content_text = entity.content_data
        elif isinstance(entity.content_data, bytes):
            content_binary = entity.content_data
        else:
            content_data = entity.content_data
        
        return {
            "id": str(entity.id),
            "session_id": entity.session_id,
            "phase_number": entity.phase_number,
            "phase_result_id": entity.phase_result_id,
            "content_type": entity.content_type.value,
            "content_format": entity.content_format.value,
            "title": entity.title,
            "description": entity.description,
            "content_data": content_data,
            "content_text": content_text,
            "content_binary": content_binary,
            "content_url": entity.content_url,
            "content_size_bytes": entity.content_size_bytes,
            "content_hash": entity.content_hash,
            "generated_by": entity.generated_by,
            "generation_prompt": entity.generation_prompt,
            "generation_params": entity.generation_params,
            "status": entity.status.value,
            "version": entity.version,
            "parent_content_id": str(entity.parent_content_id) if entity.parent_content_id else None,
            "quality_score": entity.quality_score.to_dict() if entity.quality_score else None,
            "validation_results": entity.validation_results,
            "auto_approved": entity.auto_approved,
            "hitl_feedback": entity.hitl_feedback,
            "feedback_count": entity.feedback_count,
            "approval_score": entity.approval_score,
            "related_content_ids": [str(cid) for cid in entity.related_content_ids],
            "dependencies": [str(did) for did in entity.dependencies],
            "tags": entity.tags,
            "generation_time_seconds": entity.generation_time_seconds,
            "processing_cost_usd": entity.processing_cost_usd,
            "storage_cost_usd": entity.storage_cost_usd,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "approved_at": entity.approved_at,
            "finalized_at": entity.finalized_at,
            "archived_at": entity.archived_at,
            "metadata": entity.metadata
        }
    
    async def save(self, content: GeneratedContent) -> None:
        """Save or update generated content."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(GeneratedContentModel.id == str(content.id))
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        model_data = self._entity_to_model_data(content)
        
        if existing:
            stmt = update(GeneratedContentModel).where(
                GeneratedContentModel.id == str(content.id)
            ).values(**model_data)
            await db.execute(stmt)
        else:
            model = GeneratedContentModel(**model_data)
            db.add(model)
        
        await db.commit()
    
    async def find_by_id(self, content_id: ContentId) -> Optional[GeneratedContent]:
        """Find content by ID."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(GeneratedContentModel.id == str(content_id))
        result = await db.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._model_to_entity(model) if model else None
    
    async def find_by_session_id(self, session_id: str) -> List[GeneratedContent]:
        """Find all content for a session."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(
            GeneratedContentModel.session_id == session_id
        ).order_by(GeneratedContentModel.phase_number, GeneratedContentModel.created_at)
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_session_and_phase(
        self, 
        session_id: str, 
        phase_number: int
    ) -> List[GeneratedContent]:
        """Find content for a specific session and phase."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(
            and_(
                GeneratedContentModel.session_id == session_id,
                GeneratedContentModel.phase_number == phase_number
            )
        ).order_by(GeneratedContentModel.created_at)
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_content_type(self, content_type: ContentType) -> List[GeneratedContent]:
        """Find content by type."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(
            GeneratedContentModel.content_type == content_type.value
        ).order_by(GeneratedContentModel.created_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_status(self, status: ContentStatus) -> List[GeneratedContent]:
        """Find content by status."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(
            GeneratedContentModel.status == status.value
        ).order_by(GeneratedContentModel.updated_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_pending_review(self) -> List[GeneratedContent]:
        """Find content pending human review."""
        db = await self._get_session()
        
        review_statuses = [
            ContentStatus.REVIEWED.value,
            ContentStatus.GENERATED.value
        ]
        
        stmt = select(GeneratedContentModel).where(
            GeneratedContentModel.status.in_(review_statuses)
        ).order_by(GeneratedContentModel.created_at)
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_approved_content(
        self, 
        session_id: Optional[str] = None
    ) -> List[GeneratedContent]:
        """Find approved content."""
        db = await self._get_session()
        
        conditions = [GeneratedContentModel.status == ContentStatus.APPROVED.value]
        if session_id:
            conditions.append(GeneratedContentModel.session_id == session_id)
        
        stmt = select(GeneratedContentModel).where(
            and_(*conditions)
        ).order_by(GeneratedContentModel.approved_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_rejected_content(
        self, 
        session_id: Optional[str] = None
    ) -> List[GeneratedContent]:
        """Find rejected content."""
        db = await self._get_session()
        
        conditions = [GeneratedContentModel.status == ContentStatus.REJECTED.value]
        if session_id:
            conditions.append(GeneratedContentModel.session_id == session_id)
        
        stmt = select(GeneratedContentModel).where(
            and_(*conditions)
        ).order_by(GeneratedContentModel.updated_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_final_content(self, session_id: str) -> List[GeneratedContent]:
        """Find finalized content for a session."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(
            and_(
                GeneratedContentModel.session_id == session_id,
                GeneratedContentModel.status == ContentStatus.FINALIZED.value
            )
        ).order_by(GeneratedContentModel.phase_number)
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_hash(self, content_hash: str) -> List[GeneratedContent]:
        """Find content by hash."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(
            GeneratedContentModel.content_hash == content_hash
        ).order_by(GeneratedContentModel.created_at)
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_generator(self, generated_by: str) -> List[GeneratedContent]:
        """Find content by generator."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(
            GeneratedContentModel.generated_by == generated_by
        ).order_by(GeneratedContentModel.created_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_tags(self, tags: List[str]) -> List[GeneratedContent]:
        """Find content containing any of the specified tags."""
        db = await self._get_session()
        
        # For PostgreSQL, we could use JSON operations, but for simplicity we'll use text search
        tag_conditions = []
        for tag in tags:
            tag_conditions.append(
                GeneratedContentModel.tags.cast(text).contains(f'"{tag}"')
            )
        
        stmt = select(GeneratedContentModel).where(
            or_(*tag_conditions)
        ).order_by(GeneratedContentModel.created_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_with_dependencies(
        self, 
        dependency_id: ContentId
    ) -> List[GeneratedContent]:
        """Find content that depends on specified content."""
        db = await self._get_session()
        
        # Use JSON contains operator for dependencies array
        stmt = select(GeneratedContentModel).where(
            GeneratedContentModel.dependencies.cast(text).contains(f'"{str(dependency_id)}"')
        )
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_related_content(
        self, 
        content_id: ContentId
    ) -> List[GeneratedContent]:
        """Find content related to specified content."""
        db = await self._get_session()
        
        # Use JSON contains operator for related_content_ids array
        stmt = select(GeneratedContentModel).where(
            GeneratedContentModel.related_content_ids.cast(text).contains(f'"{str(content_id)}"')
        )
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_content_versions(
        self, 
        parent_content_id: ContentId
    ) -> List[GeneratedContent]:
        """Find all versions of content."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(
            GeneratedContentModel.parent_content_id == str(parent_content_id)
        ).order_by(GeneratedContentModel.version)
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        content_type: Optional[ContentType] = None
    ) -> List[GeneratedContent]:
        """Find content within date range."""
        db = await self._get_session()
        
        conditions = [
            GeneratedContentModel.created_at >= start_date,
            GeneratedContentModel.created_at <= end_date
        ]
        
        if content_type:
            conditions.append(GeneratedContentModel.content_type == content_type.value)
        
        stmt = select(GeneratedContentModel).where(
            and_(*conditions)
        ).order_by(GeneratedContentModel.created_at.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_high_quality_content(self, quality_threshold: float = 0.8) -> List[GeneratedContent]:
        """Find high quality content."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(
            and_(
                GeneratedContentModel.approval_score.is_not(None),
                GeneratedContentModel.approval_score >= quality_threshold
            )
        ).order_by(GeneratedContentModel.approval_score.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_low_quality_content(self, quality_threshold: float = 0.6) -> List[GeneratedContent]:
        """Find low quality content."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(
            and_(
                GeneratedContentModel.approval_score.is_not(None),
                GeneratedContentModel.approval_score < quality_threshold
            )
        ).order_by(GeneratedContentModel.approval_score.asc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_large_content(self, size_threshold_mb: float = 1.0) -> List[GeneratedContent]:
        """Find large content."""
        db = await self._get_session()
        
        size_threshold_bytes = int(size_threshold_mb * 1024 * 1024)
        
        stmt = select(GeneratedContentModel).where(
            GeneratedContentModel.content_size_bytes > size_threshold_bytes
        ).order_by(GeneratedContentModel.content_size_bytes.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_expensive_content(self, cost_threshold: float = 0.05) -> List[GeneratedContent]:
        """Find expensive content."""
        db = await self._get_session()
        
        stmt = select(GeneratedContentModel).where(
            GeneratedContentModel.processing_cost_usd > cost_threshold
        ).order_by(GeneratedContentModel.processing_cost_usd.desc())
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def count_by_type_and_status(
        self, 
        content_type: ContentType, 
        status: ContentStatus
    ) -> int:
        """Count content by type and status."""
        db = await self._get_session()
        
        stmt = select(func.count(GeneratedContentModel.id)).where(
            and_(
                GeneratedContentModel.content_type == content_type.value,
                GeneratedContentModel.status == status.value
            )
        )
        
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    async def count_by_session(self, session_id: str) -> int:
        """Count content for a session."""
        db = await self._get_session()
        
        stmt = select(func.count(GeneratedContentModel.id)).where(
            GeneratedContentModel.session_id == session_id
        )
        
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    async def delete(self, content_id: ContentId) -> bool:
        """Delete content."""
        db = await self._get_session()
        
        stmt = delete(GeneratedContentModel).where(
            GeneratedContentModel.id == str(content_id)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0
    
    async def delete_by_session(self, session_id: str) -> int:
        """Delete all content for a session."""
        db = await self._get_session()
        
        stmt = delete(GeneratedContentModel).where(
            GeneratedContentModel.session_id == session_id
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount
    
    async def archive_old_content(self, days_old: int = 90) -> int:
        """Archive old content."""
        db = await self._get_session()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        stmt = update(GeneratedContentModel).where(
            and_(
                GeneratedContentModel.created_at < cutoff_date,
                GeneratedContentModel.status != ContentStatus.ARCHIVED.value
            )
        ).values(
            status=ContentStatus.ARCHIVED.value,
            archived_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount
    
    async def exists(self, content_id: ContentId) -> bool:
        """Check if content exists."""
        db = await self._get_session()
        
        stmt = select(func.count(GeneratedContentModel.id)).where(
            GeneratedContentModel.id == str(content_id)
        )
        
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        return count > 0
    
    async def get_content_statistics(
        self, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get content statistics."""
        db = await self._get_session()
        
        base_conditions = []
        if session_id:
            base_conditions.append(GeneratedContentModel.session_id == session_id)
        
        # Total content
        total_stmt = select(func.count(GeneratedContentModel.id))
        if base_conditions:
            total_stmt = total_stmt.where(and_(*base_conditions))
        
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        # By type
        type_stats = {}
        for content_type in ContentType:
            type_conditions = base_conditions + [GeneratedContentModel.content_type == content_type.value]
            type_stmt = select(func.count(GeneratedContentModel.id)).where(and_(*type_conditions))
            
            result = await db.execute(type_stmt)
            type_stats[content_type.value] = result.scalar() or 0
        
        # By status
        status_stats = {}
        for status in ContentStatus:
            status_conditions = base_conditions + [GeneratedContentModel.status == status.value]
            status_stmt = select(func.count(GeneratedContentModel.id)).where(and_(*status_conditions))
            
            result = await db.execute(status_stmt)
            status_stats[status.value] = result.scalar() or 0
        
        return {
            "total": total,
            "by_type": type_stats,
            "by_status": status_stats,
            "session_id": session_id
        }
    
    async def get_storage_usage(self, session_id: Optional[str] = None) -> Dict[str, float]:
        """Get storage usage statistics."""
        db = await self._get_session()
        
        conditions = []
        if session_id:
            conditions.append(GeneratedContentModel.session_id == session_id)
        
        # Total size
        size_stmt = select(func.sum(GeneratedContentModel.content_size_bytes))
        if conditions:
            size_stmt = size_stmt.where(and_(*conditions))
        
        size_result = await db.execute(size_stmt)
        total_bytes = size_result.scalar() or 0
        
        return {
            "total_bytes": float(total_bytes),
            "total_mb": float(total_bytes) / (1024 * 1024),
            "total_gb": float(total_bytes) / (1024 * 1024 * 1024)
        }
    
    async def get_generation_costs(
        self, 
        session_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get generation cost statistics."""
        db = await self._get_session()
        
        conditions = []
        if session_id:
            conditions.append(GeneratedContentModel.session_id == session_id)
        if start_date:
            conditions.append(GeneratedContentModel.created_at >= start_date)
        if end_date:
            conditions.append(GeneratedContentModel.created_at <= end_date)
        
        # Total processing cost
        proc_cost_stmt = select(func.sum(GeneratedContentModel.processing_cost_usd))
        if conditions:
            proc_cost_stmt = proc_cost_stmt.where(and_(*conditions))
        
        proc_result = await db.execute(proc_cost_stmt)
        processing_cost = proc_result.scalar() or 0.0
        
        # Total storage cost
        storage_cost_stmt = select(func.sum(GeneratedContentModel.storage_cost_usd))
        if conditions:
            storage_cost_stmt = storage_cost_stmt.where(and_(*conditions))
        
        storage_result = await db.execute(storage_cost_stmt)
        storage_cost = storage_result.scalar() or 0.0
        
        return {
            "processing_cost_usd": float(processing_cost),
            "storage_cost_usd": float(storage_cost),
            "total_cost_usd": float(processing_cost + storage_cost)
        }
    
    async def search_content(
        self,
        query: str,
        content_types: Optional[List[ContentType]] = None,
        limit: int = 50
    ) -> List[GeneratedContent]:
        """Search content by text query."""
        db = await self._get_session()
        
        # Simple text search - in production would use full-text search
        # Use parameterized queries to prevent SQL injection
        search_pattern = f"%{query}%"
        conditions = [
            or_(
                GeneratedContentModel.title.ilike(search_pattern),
                GeneratedContentModel.description.ilike(search_pattern),
                GeneratedContentModel.content_text.ilike(search_pattern)
            )
        ]
        
        if content_types:
            type_values = [ct.value for ct in content_types]
            conditions.append(GeneratedContentModel.content_type.in_(type_values))
        
        stmt = select(GeneratedContentModel).where(
            and_(*conditions)
        ).order_by(GeneratedContentModel.created_at.desc()).limit(limit)
        
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def find_duplicate_content(
        self, 
        similarity_threshold: float = 0.9
    ) -> List[List[GeneratedContent]]:
        """Find groups of duplicate content."""
        db = await self._get_session()
        
        # Find content with same hash (exact duplicates)
        stmt = select(
            GeneratedContentModel.content_hash,
            func.count(GeneratedContentModel.id).label('count')
        ).where(
            GeneratedContentModel.content_hash.is_not(None)
        ).group_by(
            GeneratedContentModel.content_hash
        ).having(
            func.count(GeneratedContentModel.id) > 1
        )
        
        hash_result = await db.execute(stmt)
        duplicate_hashes = [row.content_hash for row in hash_result.all()]
        
        # Get content for each duplicate hash
        duplicate_groups = []
        for hash_value in duplicate_hashes:
            hash_stmt = select(GeneratedContentModel).where(
                GeneratedContentModel.content_hash == hash_value
            )
            content_result = await db.execute(hash_stmt)
            models = content_result.scalars().all()
            
            group = [self._model_to_entity(model) for model in models]
            duplicate_groups.append(group)
        
        return duplicate_groups
    
    async def update_content_status(
        self, 
        content_id: ContentId, 
        status: ContentStatus
    ) -> bool:
        """Update content status only."""
        db = await self._get_session()
        
        stmt = update(GeneratedContentModel).where(
            GeneratedContentModel.id == str(content_id)
        ).values(
            status=status.value,
            updated_at=datetime.utcnow()
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0
    
    async def bulk_approve_content(
        self,
        content_ids: List[ContentId],
        approval_score: float
    ) -> int:
        """Bulk approve content."""
        db = await self._get_session()
        
        id_strings = [str(cid) for cid in content_ids]
        
        stmt = update(GeneratedContentModel).where(
            GeneratedContentModel.id.in_(id_strings)
        ).values(
            status=ContentStatus.APPROVED.value,
            approval_score=approval_score,
            approved_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount
    
    async def bulk_reject_content(
        self,
        content_ids: List[ContentId],
        reason: str
    ) -> int:
        """Bulk reject content."""
        db = await self._get_session()
        
        id_strings = [str(cid) for cid in content_ids]
        
        stmt = update(GeneratedContentModel).where(
            GeneratedContentModel.id.in_(id_strings)
        ).values(
            status=ContentStatus.REJECTED.value,
            hitl_feedback={"reason": reason, "rejected_at": datetime.utcnow().isoformat()},
            updated_at=datetime.utcnow()
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount
    
    async def find_content_needing_cleanup(
        self, 
        days_old: int = 30
    ) -> List[ContentId]:
        """Find content IDs for cleanup."""
        db = await self._get_session()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        cleanup_statuses = [
            ContentStatus.DRAFT.value,
            ContentStatus.REJECTED.value,
            ContentStatus.ARCHIVED.value
        ]
        
        stmt = select(GeneratedContentModel.id).where(
            and_(
                GeneratedContentModel.status.in_(cleanup_statuses),
                GeneratedContentModel.created_at < cutoff_date
            )
        )
        
        result = await db.execute(stmt)
        content_ids = result.scalars().all()
        
        return [ContentId(cid) for cid in content_ids]