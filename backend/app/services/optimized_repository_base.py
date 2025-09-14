"""
Optimized Repository Base - N+1クエリ問題解決とパフォーマンス最適化
Eager loading、バッチクエリ、クエリ最適化パターンを実装
"""

from typing import Dict, Any, List, Optional, Type, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload, contains_eager
from abc import ABC, abstractmethod
import time

from app.core.logging import LoggerMixin
from app.core.async_optimization import async_performance_monitor

T = TypeVar('T')
ModelType = TypeVar('ModelType')
EntityType = TypeVar('EntityType')


class OptimizedRepositoryBase(Generic[ModelType, EntityType], LoggerMixin, ABC):
    """
    最適化されたリポジトリベースクラス
    N+1問題の解決とクエリパフォーマンスの向上
    """
    
    def __init__(self, model_class: Type[ModelType], db_session: Optional[AsyncSession] = None):
        super().__init__()
        self.model_class = model_class
        self.db_session = db_session
        
        # パフォーマンス追跡
        self.query_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "avg_query_time": 0.0,
            "total_query_time": 0.0
        }
    
    @abstractmethod
    def _model_to_entity(self, model: ModelType) -> EntityType:
        """Convert database model to domain entity."""
        pass
    
    @abstractmethod
    def _entity_to_model_data(self, entity: EntityType) -> Dict[str, Any]:
        """Convert domain entity to model data."""
        pass
    
    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db_session:
            return self.db_session
        # This would need proper dependency injection in real implementation
        raise NotImplementedError("Database session not provided")
    
    @async_performance_monitor("repository_query", slow_threshold=0.5)
    async def _execute_query_with_tracking(
        self, 
        query, 
        session: AsyncSession,
        operation_name: str = "query"
    ):
        """Execute query with performance tracking."""
        start_time = time.time()
        
        try:
            result = await session.execute(query)
            duration = time.time() - start_time
            
            # Update statistics
            self.query_stats["total_queries"] += 1
            self.query_stats["total_query_time"] += duration
            self.query_stats["avg_query_time"] = (
                self.query_stats["total_query_time"] / self.query_stats["total_queries"]
                if self.query_stats["total_queries"] > 0 else 0
            )
            
            if duration > 0.5:  # Slow query threshold
                self.query_stats["slow_queries"] += 1
                self.logger.warning(f"Slow {operation_name}: {duration:.3f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Query failed in {operation_name}: {e}")
            raise
    
    async def find_by_id_optimized(
        self, 
        id_value: Any,
        *eager_load_relations
    ) -> Optional[EntityType]:
        """Find by ID with optional eager loading to prevent N+1."""
        db = await self._get_session()
        
        stmt = select(self.model_class).where(self.model_class.id == id_value)
        
        # Add eager loading if specified
        for relation in eager_load_relations:
            if hasattr(self.model_class, relation):
                stmt = stmt.options(selectinload(getattr(self.model_class, relation)))
        
        result = await self._execute_query_with_tracking(stmt, db, "find_by_id")
        model = result.scalar_one_or_none()
        
        return self._model_to_entity(model) if model else None
    
    async def find_many_optimized(
        self,
        conditions: List,
        *eager_load_relations,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by=None
    ) -> List[EntityType]:
        """Find multiple records with optimized eager loading."""
        db = await self._get_session()
        
        stmt = select(self.model_class)
        
        # Add conditions
        if conditions:
            stmt = stmt.where(*conditions)
        
        # Add eager loading
        for relation in eager_load_relations:
            if hasattr(self.model_class, relation):
                stmt = stmt.options(selectinload(getattr(self.model_class, relation)))
        
        # Add ordering
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        
        # Add pagination
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        
        result = await self._execute_query_with_tracking(stmt, db, "find_many")
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def batch_find_by_ids(
        self,
        ids: List[Any],
        *eager_load_relations
    ) -> Dict[Any, EntityType]:
        """Batch find by IDs to reduce query count."""
        if not ids:
            return {}
        
        db = await self._get_session()
        
        stmt = select(self.model_class).where(self.model_class.id.in_(ids))
        
        # Add eager loading
        for relation in eager_load_relations:
            if hasattr(self.model_class, relation):
                stmt = stmt.options(selectinload(getattr(self.model_class, relation)))
        
        result = await self._execute_query_with_tracking(stmt, db, "batch_find")
        models = result.scalars().all()
        
        # Return as dictionary keyed by ID
        return {
            model.id: self._model_to_entity(model)
            for model in models
        }
    
    async def count_optimized(self, conditions: Optional[List] = None) -> int:
        """Optimized count query."""
        db = await self._get_session()
        
        stmt = select(func.count(self.model_class.id))
        
        if conditions:
            stmt = stmt.where(*conditions)
        
        result = await self._execute_query_with_tracking(stmt, db, "count")
        return result.scalar() or 0
    
    async def exists_optimized(self, conditions: List) -> bool:
        """Optimized existence check."""
        db = await self._get_session()
        
        stmt = select(func.count(self.model_class.id)).where(*conditions).limit(1)
        
        result = await self._execute_query_with_tracking(stmt, db, "exists")
        count = result.scalar() or 0
        
        return count > 0
    
    async def bulk_insert_optimized(
        self,
        entities: List[EntityType],
        batch_size: int = 100
    ) -> int:
        """Optimized bulk insert."""
        if not entities:
            return 0
        
        db = await self._get_session()
        inserted_count = 0
        
        # Process in batches
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            
            # Convert entities to model data
            model_data_batch = [self._entity_to_model_data(entity) for entity in batch]
            
            # Create model instances
            models = [self.model_class(**data) for data in model_data_batch]
            
            # Add to session
            db.add_all(models)
            inserted_count += len(models)
        
        await db.commit()
        
        self.logger.info(f"Bulk insert completed: {inserted_count} records")
        return inserted_count
    
    async def bulk_update_optimized(
        self,
        updates: List[Dict[str, Any]],
        conditions_field: str = "id"
    ) -> int:
        """Optimized bulk update."""
        if not updates:
            return 0
        
        db = await self._get_session()
        updated_count = 0
        
        for update_data in updates:
            condition_value = update_data.pop(conditions_field)
            
            stmt = update(self.model_class).where(
                getattr(self.model_class, conditions_field) == condition_value
            ).values(**update_data)
            
            result = await db.execute(stmt)
            updated_count += result.rowcount
        
        await db.commit()
        
        self.logger.info(f"Bulk update completed: {updated_count} records")
        return updated_count
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get repository performance statistics."""
        return {
            "repository_class": self.__class__.__name__,
            "query_stats": self.query_stats,
            "slow_query_percentage": (
                (self.query_stats["slow_queries"] / self.query_stats["total_queries"] * 100)
                if self.query_stats["total_queries"] > 0 else 0.0
            )
        }