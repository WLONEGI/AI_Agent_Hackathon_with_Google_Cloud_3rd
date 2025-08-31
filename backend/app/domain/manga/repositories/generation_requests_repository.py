"""Generation request repository interface for domain layer."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from ...common.entities import GenerationRequestEntity


class GenerationRequestsRepository(ABC):
    """Abstract repository interface for generation request operations.
    
    This interface defines the contract for generation request data persistence
    operations including queue management and progress tracking.
    """
    
    @abstractmethod
    async def create(self, request: GenerationRequestEntity) -> GenerationRequestEntity:
        """Create a new generation request.
        
        Args:
            request: Request entity to create
            
        Returns:
            Created request entity with populated fields
            
        Raises:
            RepositoryError: If creation fails
            QuotaExceededError: If user quota exceeded
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, request_id: UUID) -> Optional[GenerationRequestEntity]:
        """Find request by ID.
        
        Args:
            request_id: Request ID to search for
            
        Returns:
            Request entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
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
        """Find requests by user ID.
        
        Args:
            user_id: User ID to search for
            status: Filter by request status
            project_id: Filter by project ID
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by
            order_direction: Order direction (asc, desc)
            
        Returns:
            List of request entities
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def update(self, request: GenerationRequestEntity) -> GenerationRequestEntity:
        """Update existing request.
        
        Args:
            request: Request entity with updated data
            
        Returns:
            Updated request entity
            
        Raises:
            RepositoryError: If update fails
            RequestNotFoundError: If request doesn't exist
        """
        pass
    
    @abstractmethod
    async def delete(self, request_id: UUID) -> bool:
        """Delete request by ID.
        
        Args:
            request_id: ID of request to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def find_by_status(
        self,
        status: str,
        user_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[GenerationRequestEntity]:
        """Find requests by status.
        
        Args:
            status: Request status to filter by
            user_id: Optional user ID filter
            project_id: Optional project ID filter
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching request entities
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get current queue statistics.
        
        Returns:
            Dictionary containing queue metrics:
            - queued_count: Number of queued requests
            - processing_count: Number of processing requests
            - average_wait_time: Average wait time in seconds
            - estimated_wait_time: Estimated wait time for new requests
            - total_processed_today: Total processed today
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def update_progress(
        self,
        request_id: UUID,
        current_module: int,
        progress_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update request progress.
        
        Args:
            request_id: Request ID to update
            current_module: Current processing module (0-7)
            progress_data: Optional progress metadata
            
        Returns:
            True if updated successfully
            
        Raises:
            RepositoryError: If update fails
            RequestNotFoundError: If request doesn't exist
        """
        pass
    
    @abstractmethod
    async def retry_request(self, request_id: UUID) -> bool:
        """Retry failed request.
        
        Args:
            request_id: Request ID to retry
            
        Returns:
            True if retry initiated successfully
            
        Raises:
            RepositoryError: If operation fails
            RequestNotFoundError: If request doesn't exist
            RetryLimitExceededError: If max retries exceeded
        """
        pass
    
    @abstractmethod
    async def cancel_request(self, request_id: UUID) -> bool:
        """Cancel pending or processing request.
        
        Args:
            request_id: Request ID to cancel
            
        Returns:
            True if cancelled successfully
            
        Raises:
            RepositoryError: If operation fails
            RequestNotFoundError: If request doesn't exist
            RequestNotCancellableError: If request cannot be cancelled
        """
        pass
    
    @abstractmethod
    async def get_next_queued_request(
        self,
        exclude_user_ids: Optional[List[UUID]] = None
    ) -> Optional[GenerationRequestEntity]:
        """Get next request from queue for processing.
        
        Args:
            exclude_user_ids: User IDs to exclude (for concurrent processing limits)
            
        Returns:
            Next request entity to process, None if queue empty
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def mark_processing_started(
        self,
        request_id: UUID,
        processing_node: Optional[str] = None
    ) -> bool:
        """Mark request as processing started.
        
        Args:
            request_id: Request ID to mark as processing
            processing_node: Optional processing node identifier
            
        Returns:
            True if marked successfully
            
        Raises:
            RepositoryError: If operation fails
            RequestNotFoundError: If request doesn't exist
        """
        pass
    
    @abstractmethod
    async def mark_processing_completed(
        self,
        request_id: UUID,
        output_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark request as processing completed.
        
        Args:
            request_id: Request ID to mark as completed
            output_data: Optional output metadata
            
        Returns:
            True if marked successfully
            
        Raises:
            RepositoryError: If operation fails
            RequestNotFoundError: If request doesn't exist
        """
        pass
    
    @abstractmethod
    async def mark_processing_failed(
        self,
        request_id: UUID,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark request as processing failed.
        
        Args:
            request_id: Request ID to mark as failed
            error_message: Error message
            error_details: Optional error details
            
        Returns:
            True if marked successfully
            
        Raises:
            RepositoryError: If operation fails
            RequestNotFoundError: If request doesn't exist
        """
        pass
    
    @abstractmethod
    async def get_user_daily_quota_usage(
        self,
        user_id: UUID,
        date: Optional[datetime] = None
    ) -> int:
        """Get user's daily quota usage.
        
        Args:
            user_id: User ID to check quota for
            date: Date to check (defaults to today)
            
        Returns:
            Number of requests submitted today
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def get_user_concurrent_requests(
        self,
        user_id: UUID
    ) -> int:
        """Get user's current concurrent processing requests.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Number of currently processing requests
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def cleanup_stale_requests(
        self,
        stale_threshold_minutes: int = 60
    ) -> int:
        """Cleanup stale processing requests.
        
        Args:
            stale_threshold_minutes: Minutes after which processing is considered stale
            
        Returns:
            Number of requests cleaned up
            
        Raises:
            RepositoryError: If operation fails
        """
        pass


# Repository-specific exceptions
class GenerationRequestRepositoryError(Exception):
    """Base generation request repository error."""
    pass


class RequestNotFoundError(GenerationRequestRepositoryError):
    """Request not found error."""
    pass


class QuotaExceededError(GenerationRequestRepositoryError):
    """User quota exceeded error."""
    pass


class RetryLimitExceededError(GenerationRequestRepositoryError):
    """Retry limit exceeded error."""
    pass


class RequestNotCancellableError(GenerationRequestRepositoryError):
    """Request cannot be cancelled error."""
    pass


class ConcurrencyLimitExceededError(GenerationRequestRepositoryError):
    """Concurrency limit exceeded error."""
    pass