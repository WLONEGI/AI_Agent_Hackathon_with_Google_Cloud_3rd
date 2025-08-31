"""Processing module repository implementation using SQLAlchemy."""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.manga_models import (
    ProcessingModule, ModuleExecution, ProcessingCheckpoint
)
from app.domain.manga.repositories.processing_modules_repository import (
    ProcessingModulesRepository,
    ProcessingModuleRepositoryError,
    ModuleNotFoundError,
    ModuleNameExistsError,
    CheckpointNotFoundError,
    ModuleExecutionError
)
from app.domain.common.entities import ProcessingModuleEntity
from app.infrastructure.database.repositories.base_repository import BaseRepository


logger = logging.getLogger(__name__)


class ProcessingModulesRepositoryImpl(ProcessingModulesRepository, BaseRepository):
    """SQLAlchemy implementation of processing modules repository."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.session = session
    
    async def create(self, module: ProcessingModuleEntity) -> ProcessingModuleEntity:
        """Create a new processing module."""
        try:
            # Check if module name exists
            existing_check = select(ProcessingModule).where(
                ProcessingModule.module_name == module.module_name
            )
            result = await self.session.execute(existing_check)
            existing_module = result.scalar_one_or_none()
            
            if existing_module:
                raise ModuleNameExistsError(f"Module '{module.module_name}' already exists")
            
            # Create database model
            db_module = ProcessingModule(
                module_id=module.module_id,
                module_name=module.module_name,
                module_type=module.module_type,
                version=module.version,
                is_enabled=module.is_enabled,
                configuration=module.configuration,
                dependencies=module.dependencies,
                created_at=module.created_at,
                updated_at=module.updated_at
            )
            
            self.session.add(db_module)
            await self.session.commit()
            await self.session.refresh(db_module)
            
            logger.info(f"Created processing module {module.module_name}")
            return self._to_entity(db_module)
            
        except ModuleNameExistsError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create processing module: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to create module: {str(e)}")
    
    async def find_by_id(self, module_id: UUID) -> Optional[ProcessingModuleEntity]:
        """Find module by ID."""
        try:
            query = select(ProcessingModule).where(ProcessingModule.module_id == module_id)
            result = await self.session.execute(query)
            db_module = result.scalar_one_or_none()
            
            if db_module:
                return self._to_entity(db_module)
            return None
            
        except Exception as e:
            logger.error(f"Failed to find module {module_id}: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to find module: {str(e)}")
    
    async def find_by_name(self, module_name: str) -> Optional[ProcessingModuleEntity]:
        """Find module by name."""
        try:
            query = select(ProcessingModule).where(ProcessingModule.module_name == module_name)
            result = await self.session.execute(query)
            db_module = result.scalar_one_or_none()
            
            if db_module:
                return self._to_entity(db_module)
            return None
            
        except Exception as e:
            logger.error(f"Failed to find module {module_name}: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to find module: {str(e)}")
    
    async def find_by_type(
        self,
        module_type: str,
        is_enabled: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProcessingModuleEntity]:
        """Find modules by type."""
        try:
            query = select(ProcessingModule).where(ProcessingModule.module_type == module_type)
            
            if is_enabled is not None:
                query = query.where(ProcessingModule.is_enabled == is_enabled)
            
            query = query.order_by(ProcessingModule.module_name).limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            db_modules = result.scalars().all()
            
            return [self._to_entity(m) for m in db_modules]
            
        except Exception as e:
            logger.error(f"Failed to find modules by type {module_type}: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to find modules by type: {str(e)}")
    
    async def update(self, module: ProcessingModuleEntity) -> ProcessingModuleEntity:
        """Update existing module."""
        try:
            # Check if module exists
            query = select(ProcessingModule).where(ProcessingModule.module_id == module.module_id)
            result = await self.session.execute(query)
            db_module = result.scalar_one_or_none()
            
            if not db_module:
                raise ModuleNotFoundError(f"Module {module.module_id} not found")
            
            # Update fields
            db_module.module_name = module.module_name
            db_module.module_type = module.module_type
            db_module.version = module.version
            db_module.is_enabled = module.is_enabled
            db_module.configuration = module.configuration
            db_module.dependencies = module.dependencies
            db_module.updated_at = module.updated_at
            
            await self.session.commit()
            await self.session.refresh(db_module)
            
            logger.info(f"Updated processing module {module.module_name}")
            return self._to_entity(db_module)
            
        except ModuleNotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update module {module.module_id}: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to update module: {str(e)}")
    
    async def delete(self, module_id: UUID) -> bool:
        """Delete module by ID."""
        try:
            # Delete related execution records first
            await self.session.execute(
                delete(ModuleExecution).where(ModuleExecution.module_id == module_id)
            )
            
            # Delete module
            result = await self.session.execute(
                delete(ProcessingModule).where(ProcessingModule.module_id == module_id)
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Deleted processing module {module_id}")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete module {module_id}: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to delete module: {str(e)}")
    
    async def get_enabled_modules(
        self,
        module_type: Optional[str] = None,
        order_by: str = "module_name"
    ) -> List[ProcessingModuleEntity]:
        """Get enabled modules."""
        try:
            query = select(ProcessingModule).where(ProcessingModule.is_enabled == True)
            
            if module_type:
                query = query.where(ProcessingModule.module_type == module_type)
            
            order_column = getattr(ProcessingModule, order_by, ProcessingModule.module_name)
            query = query.order_by(order_column)
            
            result = await self.session.execute(query)
            db_modules = result.scalars().all()
            
            return [self._to_entity(m) for m in db_modules]
            
        except Exception as e:
            logger.error(f"Failed to get enabled modules: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to get enabled modules: {str(e)}")
    
    async def get_processing_pipeline(self) -> List[ProcessingModuleEntity]:
        """Get processing pipeline modules in order."""
        try:
            # Define pipeline order
            pipeline_types = [
                "text_analysis",
                "character_extraction",
                "panel_generation",
                "speech_bubble",
                "background_generation",
                "style_transfer",
                "quality_control",
                "output_formatting"
            ]
            
            pipeline_modules = []
            for module_type in pipeline_types:
                # Get first enabled module of each type
                query = select(ProcessingModule).where(
                    and_(
                        ProcessingModule.module_type == module_type,
                        ProcessingModule.is_enabled == True
                    )
                ).order_by(ProcessingModule.module_name).limit(1)
                
                result = await self.session.execute(query)
                db_module = result.scalar_one_or_none()
                
                if db_module:
                    pipeline_modules.append(self._to_entity(db_module))
            
            return pipeline_modules
            
        except Exception as e:
            logger.error(f"Failed to get processing pipeline: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to get processing pipeline: {str(e)}")
    
    async def record_execution_metrics(
        self,
        module_id: UUID,
        request_id: UUID,
        execution_time_seconds: float,
        memory_usage_mb: Optional[float] = None,
        cpu_usage_percent: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """Record module execution metrics."""
        try:
            execution = ModuleExecution(
                execution_id=uuid4(),
                module_id=module_id,
                request_id=request_id,
                execution_time_seconds=execution_time_seconds,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent,
                success=success,
                error_message=error_message,
                executed_at=datetime.utcnow()
            )
            
            self.session.add(execution)
            await self.session.commit()
            
            logger.info(f"Recorded execution metrics for module {module_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to record execution metrics: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to record metrics: {str(e)}")
    
    async def get_performance_stats(
        self,
        module_id: Optional[UUID] = None,
        module_type: Optional[str] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get performance statistics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            # Base query
            query = select(ModuleExecution).where(ModuleExecution.executed_at >= cutoff_date)
            
            if module_id:
                query = query.where(ModuleExecution.module_id == module_id)
            elif module_type:
                query = query.join(ProcessingModule).where(ProcessingModule.module_type == module_type)
            
            result = await self.session.execute(query)
            executions = result.scalars().all()
            
            if not executions:
                return {
                    "total_executions": 0,
                    "success_rate": 0.0,
                    "average_execution_time": 0.0,
                    "median_execution_time": 0.0,
                    "p95_execution_time": 0.0,
                    "average_memory_usage": 0.0,
                    "peak_memory_usage": 0.0,
                    "error_distribution": {}
                }
            
            # Calculate metrics
            successful_executions = [e for e in executions if e.success]
            execution_times = [e.execution_time_seconds for e in executions]
            memory_usages = [e.memory_usage_mb for e in executions if e.memory_usage_mb is not None]
            
            execution_times.sort()
            memory_usages.sort()
            
            # Error distribution
            error_distribution = {}
            for execution in executions:
                if not execution.success and execution.error_message:
                    error_type = execution.error_message.split(":")[0] if ":" in execution.error_message else "Unknown"
                    error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
            
            stats = {
                "total_executions": len(executions),
                "success_rate": len(successful_executions) / len(executions),
                "average_execution_time": sum(execution_times) / len(execution_times),
                "median_execution_time": execution_times[len(execution_times) // 2] if execution_times else 0.0,
                "p95_execution_time": execution_times[int(len(execution_times) * 0.95)] if execution_times else 0.0,
                "average_memory_usage": sum(memory_usages) / len(memory_usages) if memory_usages else 0.0,
                "peak_memory_usage": max(memory_usages) if memory_usages else 0.0,
                "error_distribution": error_distribution
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to get performance stats: {str(e)}")
    
    async def get_bottlenecks(self, period_days: int = 7) -> List[Dict[str, Any]]:
        """Identify processing bottlenecks."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            # Get average execution time by module
            query = select(
                ProcessingModule.module_id,
                ProcessingModule.module_name,
                ProcessingModule.module_type,
                func.avg(ModuleExecution.execution_time_seconds).label("avg_time"),
                func.count(ModuleExecution.execution_id).label("execution_count")
            ).select_from(
                ProcessingModule.__table__.join(ModuleExecution.__table__)
            ).where(
                ModuleExecution.executed_at >= cutoff_date
            ).group_by(
                ProcessingModule.module_id,
                ProcessingModule.module_name,
                ProcessingModule.module_type
            ).order_by(desc("avg_time"))
            
            result = await self.session.execute(query)
            rows = result.fetchall()
            
            bottlenecks = []
            for row in rows:
                # Calculate impact score (avg_time * execution_count)
                impact_score = float(row.avg_time * row.execution_count)
                
                # Generate recommendation based on avg_time
                if row.avg_time > 60:  # > 1 minute
                    recommendation = "Critical: Consider optimization or replacement"
                elif row.avg_time > 30:  # > 30 seconds
                    recommendation = "High: Review algorithm efficiency"
                elif row.avg_time > 10:  # > 10 seconds
                    recommendation = "Medium: Monitor and optimize if needed"
                else:
                    recommendation = "Low: Performance acceptable"
                
                bottlenecks.append({
                    "module_id": str(row.module_id),
                    "module_name": row.module_name,
                    "module_type": row.module_type,
                    "average_time": float(row.avg_time),
                    "execution_count": row.execution_count,
                    "impact_score": impact_score,
                    "recommendation": recommendation
                })
            
            return bottlenecks
            
        except Exception as e:
            logger.error(f"Failed to get bottlenecks: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to get bottlenecks: {str(e)}")
    
    async def get_resource_usage(
        self,
        module_id: Optional[UUID] = None,
        period_hours: int = 24
    ) -> Dict[str, Any]:
        """Get resource usage metrics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(hours=period_hours)
            
            query = select(ModuleExecution).where(ModuleExecution.executed_at >= cutoff_date)
            
            if module_id:
                query = query.where(ModuleExecution.module_id == module_id)
            
            result = await self.session.execute(query)
            executions = result.scalars().all()
            
            # Calculate metrics
            memory_usages = [e.memory_usage_mb for e in executions if e.memory_usage_mb is not None]
            cpu_usages = [e.cpu_usage_percent for e in executions if e.cpu_usage_percent is not None]
            
            # Get current concurrent executions (simplified - would need real-time data in production)
            current_time = datetime.utcnow()
            recent_executions = [e for e in executions if (current_time - e.executed_at).seconds < 300]  # Last 5 minutes
            
            usage_stats = {
                "current_memory_usage": memory_usages[-1] if memory_usages else 0.0,
                "peak_memory_usage": max(memory_usages) if memory_usages else 0.0,
                "average_cpu_usage": sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0.0,
                "peak_cpu_usage": max(cpu_usages) if cpu_usages else 0.0,
                "concurrent_executions": len(recent_executions),
                "queue_length": 0  # Would need queue implementation
            }
            
            return usage_stats
            
        except Exception as e:
            logger.error(f"Failed to get resource usage: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to get resource usage: {str(e)}")
    
    async def create_checkpoint(
        self,
        request_id: UUID,
        module_id: UUID,
        checkpoint_data: Dict[str, Any]
    ) -> str:
        """Create processing checkpoint."""
        try:
            checkpoint_id = str(uuid4())
            
            checkpoint = ProcessingCheckpoint(
                checkpoint_id=checkpoint_id,
                request_id=request_id,
                module_id=module_id,
                checkpoint_data=checkpoint_data,
                created_at=datetime.utcnow()
            )
            
            self.session.add(checkpoint)
            await self.session.commit()
            
            logger.info(f"Created checkpoint {checkpoint_id} for request {request_id}")
            return checkpoint_id
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create checkpoint: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to create checkpoint: {str(e)}")
    
    async def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get processing checkpoint."""
        try:
            query = select(ProcessingCheckpoint).where(
                ProcessingCheckpoint.checkpoint_id == checkpoint_id
            )
            result = await self.session.execute(query)
            checkpoint = result.scalar_one_or_none()
            
            if checkpoint:
                return checkpoint.checkpoint_data
            return None
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint {checkpoint_id}: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to get checkpoint: {str(e)}")
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete processing checkpoint."""
        try:
            result = await self.session.execute(
                delete(ProcessingCheckpoint).where(
                    ProcessingCheckpoint.checkpoint_id == checkpoint_id
                )
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Deleted checkpoint {checkpoint_id}")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete checkpoint {checkpoint_id}: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to delete checkpoint: {str(e)}")
    
    async def cleanup_old_metrics(self, days_to_keep: int = 90) -> int:
        """Cleanup old execution metrics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            result = await self.session.execute(
                delete(ModuleExecution).where(ModuleExecution.executed_at < cutoff_date)
            )
            
            await self.session.commit()
            cleanup_count = result.rowcount
            
            logger.info(f"Cleaned up {cleanup_count} old execution metrics")
            return cleanup_count
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to cleanup old metrics: {str(e)}")
            raise ProcessingModuleRepositoryError(f"Failed to cleanup old metrics: {str(e)}")
    
    def _to_entity(self, db_module: ProcessingModule) -> ProcessingModuleEntity:
        """Convert database model to domain entity."""
        return ProcessingModuleEntity(
            module_id=db_module.module_id,
            module_name=db_module.module_name,
            module_type=db_module.module_type,
            version=db_module.version,
            is_enabled=db_module.is_enabled,
            configuration=db_module.configuration or {},
            dependencies=db_module.dependencies or [],
            created_at=db_module.created_at,
            updated_at=db_module.updated_at
        )