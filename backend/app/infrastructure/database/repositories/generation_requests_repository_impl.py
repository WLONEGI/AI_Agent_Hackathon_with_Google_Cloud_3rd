"""Generation request repository implementation using SQLAlchemy."""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.manga_models import GenerationRequest
from app.domain.manga.repositories.generation_requests_repository import (
    GenerationRequestsRepository,
    GenerationRequestRepositoryError,
    RequestNotFoundError,
    QuotaExceededError,
    RetryLimitExceededError,
    RequestNotCancellableError,
    ConcurrencyLimitExceededError
)
from app.domain.common.entities import GenerationRequestEntity
from app.infrastructure.database.repositories.base_repository import BaseRepository


logger = logging.getLogger(__name__)


class GenerationRequestsRepositoryImpl(GenerationRequestsRepository, BaseRepository):
    """SQLAlchemy implementation of generation requests repository."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.session = session
    
    async def create(self, request: GenerationRequestEntity) -> GenerationRequestEntity:
        """Create a new generation request."""
        try:
            # Create database model
            db_request = GenerationRequest(
                request_id=request.request_id,
                project_id=request.project_id,
                user_id=request.user_id,
                input_text=request.input_text,
                request_settings=request.request_settings,
                status=request.status,
                current_module=request.current_module,
                started_at=request.started_at,
                completed_at=request.completed_at,
                retry_count=request.retry_count,
                created_at=request.created_at,
                updated_at=request.updated_at
            )
            
            self.session.add(db_request)
            await self.session.commit()
            await self.session.refresh(db_request)
            
            logger.info(f"Created generation request {request.request_id}")
            return self._to_entity(db_request)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create generation request: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to create request: {str(e)}")
    
    async def find_by_id(self, request_id: UUID) -> Optional[GenerationRequestEntity]:
        """Find request by ID."""
        try:
            query = select(GenerationRequest).where(GenerationRequest.request_id == request_id)
            result = await self.session.execute(query)
            db_request = result.scalar_one_or_none()
            
            if db_request:
                return self._to_entity(db_request)
            return None
            
        except Exception as e:
            logger.error(f"Failed to find request {request_id}: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to find request: {str(e)}")
    
    async def find_by_user(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        project_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> List[GenerationRequestEntity]:
        """Find requests by user ID."""
        try:
            query = select(GenerationRequest).where(GenerationRequest.user_id == user_id)
            
            # Add filters
            if status:
                query = query.where(GenerationRequest.status == status)
            if project_id:
                query = query.where(GenerationRequest.project_id == project_id)
            
            # Add ordering
            order_column = getattr(GenerationRequest, order_by, GenerationRequest.created_at)
            if order_direction.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
            
            # Add pagination
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            db_requests = result.scalars().all()
            
            return [self._to_entity(r) for r in db_requests]
            
        except Exception as e:
            logger.error(f"Failed to find requests for user {user_id}: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to find user requests: {str(e)}")
    
    async def update(self, request: GenerationRequestEntity) -> GenerationRequestEntity:
        """Update existing request."""
        try:
            # Check if request exists
            query = select(GenerationRequest).where(GenerationRequest.request_id == request.request_id)
            result = await self.session.execute(query)
            db_request = result.scalar_one_or_none()
            
            if not db_request:
                raise RequestNotFoundError(f"Request {request.request_id} not found")
            
            # Update fields
            db_request.input_text = request.input_text
            db_request.request_settings = request.request_settings
            db_request.status = request.status
            db_request.current_module = request.current_module
            db_request.started_at = request.started_at
            db_request.completed_at = request.completed_at
            db_request.retry_count = request.retry_count
            db_request.updated_at = request.updated_at
            
            await self.session.commit()
            await self.session.refresh(db_request)
            
            logger.info(f"Updated generation request {request.request_id}")
            return self._to_entity(db_request)
            
        except RequestNotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update request {request.request_id}: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to update request: {str(e)}")
    
    async def delete(self, request_id: UUID) -> bool:
        """Delete request by ID."""
        try:
            result = await self.session.execute(
                delete(GenerationRequest).where(GenerationRequest.request_id == request_id)
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Deleted generation request {request_id}")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete request {request_id}: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to delete request: {str(e)}")
    
    async def find_by_status(
        self,
        status: str,
        user_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[GenerationRequestEntity]:
        """Find requests by status."""
        try:
            query = select(GenerationRequest).where(GenerationRequest.status == status)
            
            if user_id:
                query = query.where(GenerationRequest.user_id == user_id)
            if project_id:
                query = query.where(GenerationRequest.project_id == project_id)
            
            query = query.order_by(GenerationRequest.created_at).limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            db_requests = result.scalars().all()
            
            return [self._to_entity(r) for r in db_requests]
            
        except Exception as e:
            logger.error(f"Failed to find requests by status {status}: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to find requests by status: {str(e)}")
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        try:
            # Count by status
            status_counts = {}
            for status in ["queued", "processing", "completed", "failed"]:
                count_query = select(func.count(GenerationRequest.request_id)).where(
                    GenerationRequest.status == status
                )
                result = await self.session.execute(count_query)
                status_counts[f"{status}_count"] = result.scalar() or 0
            
            # Calculate average wait time for completed requests in last 24h
            yesterday = datetime.utcnow() - timedelta(days=1)
            wait_time_query = select(
                func.avg(
                    func.extract('epoch', GenerationRequest.started_at) -
                    func.extract('epoch', GenerationRequest.created_at)
                )
            ).where(
                and_(
                    GenerationRequest.status == "completed",
                    GenerationRequest.completed_at >= yesterday,
                    GenerationRequest.started_at.is_not(None)
                )
            )
            result = await self.session.execute(wait_time_query)
            average_wait_time = result.scalar() or 0
            
            # Estimate wait time for new requests
            estimated_wait_time = average_wait_time * status_counts["queued_count"]
            
            # Count total processed today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count_query = select(func.count(GenerationRequest.request_id)).where(
                and_(
                    GenerationRequest.status == "completed",
                    GenerationRequest.completed_at >= today_start
                )
            )
            result = await self.session.execute(today_count_query)
            total_processed_today = result.scalar() or 0
            
            return {
                **status_counts,
                "average_wait_time": float(average_wait_time),
                "estimated_wait_time": float(estimated_wait_time),
                "total_processed_today": total_processed_today
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to get queue stats: {str(e)}")
    
    async def update_progress(
        self,
        request_id: UUID,
        current_module: int,
        progress_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update request progress."""
        try:
            update_values = {
                "current_module": current_module,
                "updated_at": datetime.utcnow()
            }
            
            if progress_data:
                # Store progress data in request_settings
                query = select(GenerationRequest).where(GenerationRequest.request_id == request_id)
                result = await self.session.execute(query)
                db_request = result.scalar_one_or_none()
                
                if not db_request:
                    raise RequestNotFoundError(f"Request {request_id} not found")
                
                settings = db_request.request_settings or {}
                settings["progress"] = progress_data
                update_values["request_settings"] = settings
            
            result = await self.session.execute(
                update(GenerationRequest)
                .where(GenerationRequest.request_id == request_id)
                .values(**update_values)
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Updated progress for request {request_id} to module {current_module}")
            
            return success
            
        except RequestNotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update progress for request {request_id}: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to update progress: {str(e)}")
    
    async def retry_request(self, request_id: UUID) -> bool:
        """Retry failed request."""
        try:
            # Get current request
            query = select(GenerationRequest).where(GenerationRequest.request_id == request_id)
            result = await self.session.execute(query)
            db_request = result.scalar_one_or_none()
            
            if not db_request:
                raise RequestNotFoundError(f"Request {request_id} not found")
            
            if db_request.status != "failed":
                raise RetryLimitExceededError("Only failed requests can be retried")
            
            if db_request.retry_count >= 3:
                raise RetryLimitExceededError("Maximum retry limit exceeded")
            
            # Reset request for retry
            result = await self.session.execute(
                update(GenerationRequest)
                .where(GenerationRequest.request_id == request_id)
                .values(
                    status="queued",
                    current_module=0,
                    retry_count=db_request.retry_count + 1,
                    started_at=None,
                    completed_at=None,
                    updated_at=datetime.utcnow()
                )
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Retrying request {request_id} (attempt {db_request.retry_count + 1})")
            
            return success
            
        except (RequestNotFoundError, RetryLimitExceededError):
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to retry request {request_id}: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to retry request: {str(e)}")
    
    async def cancel_request(self, request_id: UUID) -> bool:
        """Cancel request."""
        try:
            # Get current request
            query = select(GenerationRequest).where(GenerationRequest.request_id == request_id)
            result = await self.session.execute(query)
            db_request = result.scalar_one_or_none()
            
            if not db_request:
                raise RequestNotFoundError(f"Request {request_id} not found")
            
            if db_request.status not in ["queued", "processing"]:
                raise RequestNotCancellableError("Only queued or processing requests can be cancelled")
            
            # Cancel request
            result = await self.session.execute(
                update(GenerationRequest)
                .where(GenerationRequest.request_id == request_id)
                .values(
                    status="cancelled",
                    completed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Cancelled request {request_id}")
            
            return success
            
        except (RequestNotFoundError, RequestNotCancellableError):
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to cancel request {request_id}: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to cancel request: {str(e)}")
    
    async def get_next_queued_request(
        self,
        exclude_user_ids: Optional[List[UUID]] = None
    ) -> Optional[GenerationRequestEntity]:
        """Get next queued request."""
        try:
            query = select(GenerationRequest).where(GenerationRequest.status == "queued")
            
            if exclude_user_ids:
                query = query.where(~GenerationRequest.user_id.in_(exclude_user_ids))
            
            query = query.order_by(GenerationRequest.created_at).limit(1)
            
            result = await self.session.execute(query)
            db_request = result.scalar_one_or_none()
            
            if db_request:
                return self._to_entity(db_request)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get next queued request: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to get next request: {str(e)}")
    
    async def mark_processing_started(
        self,
        request_id: UUID,
        processing_node: Optional[str] = None
    ) -> bool:
        """Mark request as processing started."""
        try:
            update_values = {
                "status": "processing",
                "started_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            if processing_node:
                # Store processing node in request_settings
                query = select(GenerationRequest).where(GenerationRequest.request_id == request_id)
                result = await self.session.execute(query)
                db_request = result.scalar_one_or_none()
                
                if db_request:
                    settings = db_request.request_settings or {}
                    settings["processing_node"] = processing_node
                    update_values["request_settings"] = settings
            
            result = await self.session.execute(
                update(GenerationRequest)
                .where(GenerationRequest.request_id == request_id)
                .values(**update_values)
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Marked request {request_id} as processing started")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to mark request {request_id} as started: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to mark processing started: {str(e)}")
    
    async def mark_processing_completed(
        self,
        request_id: UUID,
        output_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark request as completed."""
        try:
            update_values = {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "current_module": 8  # All modules completed
            }
            
            if output_data:
                # Store output data in request_settings
                query = select(GenerationRequest).where(GenerationRequest.request_id == request_id)
                result = await self.session.execute(query)
                db_request = result.scalar_one_or_none()
                
                if db_request:
                    settings = db_request.request_settings or {}
                    settings["output"] = output_data
                    update_values["request_settings"] = settings
            
            result = await self.session.execute(
                update(GenerationRequest)
                .where(GenerationRequest.request_id == request_id)
                .values(**update_values)
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Marked request {request_id} as completed")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to mark request {request_id} as completed: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to mark processing completed: {str(e)}")
    
    async def mark_processing_failed(
        self,
        request_id: UUID,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark request as failed."""
        try:
            # Get current request to preserve retry count
            query = select(GenerationRequest).where(GenerationRequest.request_id == request_id)
            result = await self.session.execute(query)
            db_request = result.scalar_one_or_none()
            
            if not db_request:
                raise RequestNotFoundError(f"Request {request_id} not found")
            
            # Store error information
            settings = db_request.request_settings or {}
            settings["error"] = {
                "message": error_message,
                "details": error_details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self.session.execute(
                update(GenerationRequest)
                .where(GenerationRequest.request_id == request_id)
                .values(
                    status="failed",
                    completed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    request_settings=settings
                )
            )
            
            await self.session.commit()
            success = result.rowcount > 0
            
            if success:
                logger.info(f"Marked request {request_id} as failed: {error_message}")
            
            return success
            
        except RequestNotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to mark request {request_id} as failed: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to mark processing failed: {str(e)}")
    
    async def get_user_daily_quota_usage(
        self,
        user_id: UUID,
        date: Optional[datetime] = None
    ) -> int:
        """Get user's daily quota usage."""
        try:
            target_date = date or datetime.utcnow()
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            query = select(func.count(GenerationRequest.request_id)).where(
                and_(
                    GenerationRequest.user_id == user_id,
                    GenerationRequest.created_at >= start_of_day,
                    GenerationRequest.created_at < end_of_day
                )
            )
            
            result = await self.session.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Failed to get daily quota usage for user {user_id}: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to get quota usage: {str(e)}")
    
    async def get_user_concurrent_requests(self, user_id: UUID) -> int:
        """Get user's concurrent processing requests."""
        try:
            query = select(func.count(GenerationRequest.request_id)).where(
                and_(
                    GenerationRequest.user_id == user_id,
                    GenerationRequest.status == "processing"
                )
            )
            
            result = await self.session.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Failed to get concurrent requests for user {user_id}: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to get concurrent requests: {str(e)}")
    
    async def cleanup_stale_requests(self, stale_threshold_minutes: int = 60) -> int:
        """Cleanup stale processing requests."""
        try:
            stale_time = datetime.utcnow() - timedelta(minutes=stale_threshold_minutes)
            
            result = await self.session.execute(
                update(GenerationRequest)
                .where(
                    and_(
                        GenerationRequest.status == "processing",
                        GenerationRequest.updated_at <= stale_time
                    )
                )
                .values(
                    status="failed",
                    completed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            await self.session.commit()
            cleanup_count = result.rowcount
            
            logger.info(f"Cleaned up {cleanup_count} stale requests")
            return cleanup_count
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to cleanup stale requests: {str(e)}")
            raise GenerationRequestRepositoryError(f"Failed to cleanup stale requests: {str(e)}")
    
    def _to_entity(self, db_request: GenerationRequest) -> GenerationRequestEntity:
        """Convert database model to domain entity."""
        return GenerationRequestEntity(
            request_id=db_request.request_id,
            project_id=db_request.project_id,
            user_id=db_request.user_id,
            input_text=db_request.input_text,
            request_settings=db_request.request_settings or {},
            status=db_request.status,
            current_module=db_request.current_module,
            started_at=db_request.started_at,
            completed_at=db_request.completed_at,
            retry_count=db_request.retry_count,
            created_at=db_request.created_at,
            updated_at=db_request.updated_at
        )