"""Base Agent class for all phase processing agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from uuid import UUID
import json

from app.core.logging import LoggerMixin
from app.core.redis_client import redis_manager
from app.models.manga import PhaseResult, MangaSession
from sqlalchemy.ext.asyncio import AsyncSession


class BaseAgent(ABC, LoggerMixin):
    """Abstract base class for phase processing agents."""
    
    def __init__(
        self,
        phase_number: int,
        phase_name: str,
        timeout_seconds: int = 60
    ):
        """Initialize base agent.
        
        Args:
            phase_number: The phase number (1-7)
            phase_name: Human-readable phase name
            timeout_seconds: Maximum processing time in seconds
        """
        self.phase_number = phase_number
        self.phase_name = phase_name
        self.timeout_seconds = timeout_seconds
        self.metrics = {
            "total_processed": 0,
            "total_failures": 0,
            "average_processing_time": 0
        }
    
    @abstractmethod
    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: UUID,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Process the phase with input data.
        
        Args:
            input_data: Input data for this phase
            session_id: Current session ID
            previous_results: Results from previous phases
            
        Returns:
            Processing result dictionary
        """
        pass
    
    @abstractmethod
    async def generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate AI prompt for this phase.
        
        Args:
            input_data: Input data for prompt generation
            previous_results: Results from previous phases
            
        Returns:
            Generated prompt string
        """
        pass
    
    @abstractmethod
    async def validate_output(
        self,
        output_data: Dict[str, Any]
    ) -> bool:
        """Validate phase output before returning.
        
        Args:
            output_data: Output to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    async def process(
        self,
        session: MangaSession,
        input_data: Dict[str, Any],
        db: AsyncSession,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> PhaseResult:
        """Main processing entry point with error handling and metrics.
        
        Args:
            session: Current manga session
            input_data: Input data for processing
            db: Database session
            previous_results: Results from previous phases
            
        Returns:
            PhaseResult object with processing results
        """
        start_time = datetime.utcnow()
        phase_result = PhaseResult(
            session_id=session.id,
            phase_number=self.phase_number,
            phase_name=self.phase_name,
            input_data=input_data,
            started_at=start_time,
            status="processing"
        )
        
        try:
            # Add timeout protection
            self.log_info(
                f"Starting phase {self.phase_number}: {self.phase_name}",
                session_id=str(session.id)
            )
            
            output_data = await asyncio.wait_for(
                self.process_phase(input_data, session.id, previous_results),
                timeout=self.timeout_seconds
            )
            
            # Validate output
            if not await self.validate_output(output_data):
                raise ValueError(f"Output validation failed for phase {self.phase_number}")
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Update phase result
            phase_result.output_data = output_data
            phase_result.processing_time_ms = processing_time_ms
            phase_result.completed_at = end_time
            phase_result.status = "completed"
            
            # Update metrics
            await self._update_metrics(processing_time_ms, success=True)
            
            # Cache result
            await self._cache_result(session.id, output_data)
            
            self.log_info(
                f"Completed phase {self.phase_number} in {processing_time_ms}ms",
                session_id=str(session.id)
            )
            
            # Save to database
            db.add(phase_result)
            await db.commit()
            
            return phase_result
            
        except asyncio.TimeoutError:
            error_msg = f"Phase {self.phase_number} timeout after {self.timeout_seconds}s"
            self.log_error(error_msg, session_id=str(session.id))
            phase_result.status = "error"
            phase_result.error_message = error_msg
            await self._update_metrics(self.timeout_seconds * 1000, success=False)
            
        except Exception as e:
            error_msg = f"Phase {self.phase_number} failed: {str(e)}"
            self.log_error(error_msg, error=e, session_id=str(session.id))
            phase_result.status = "error"
            phase_result.error_message = str(e)
            await self._update_metrics(
                int((datetime.utcnow() - start_time).total_seconds() * 1000),
                success=False
            )
        
        # Save failed result to database
        db.add(phase_result)
        await db.commit()
        
        raise Exception(phase_result.error_message)
    
    async def apply_feedback(
        self,
        original_result: Dict[str, Any],
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply user feedback to adjust results.
        
        Args:
            original_result: Original processing result
            feedback: User feedback to apply
            
        Returns:
            Adjusted result after applying feedback
        """
        self.log_info(
            f"Applying feedback to phase {self.phase_number}",
            feedback_type=feedback.get("type")
        )
        
        # Default implementation - subclasses can override
        adjusted_result = original_result.copy()
        adjusted_result["feedback_applied"] = feedback
        adjusted_result["feedback_timestamp"] = datetime.utcnow().isoformat()
        
        return adjusted_result
    
    async def generate_preview(
        self,
        output_data: Dict[str, Any],
        quality_level: str = "high"
    ) -> Dict[str, Any]:
        """Generate preview data for this phase.
        
        Args:
            output_data: Phase output data
            quality_level: Preview quality level
            
        Returns:
            Preview data dictionary
        """
        # Default implementation - subclasses should override
        return {
            "phase": self.phase_number,
            "name": self.phase_name,
            "data": output_data,
            "quality": quality_level,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _cache_result(
        self,
        session_id: UUID,
        output_data: Dict[str, Any]
    ) -> None:
        """Cache phase result in Redis.
        
        Args:
            session_id: Session ID for cache key
            output_data: Data to cache
        """
        cache_key = f"phase_result:{session_id}:{self.phase_number}"
        await redis_manager.set(
            cache_key,
            json.dumps(output_data, default=str),
            ttl=3600  # 1 hour TTL
        )
    
    async def _get_cached_result(
        self,
        session_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get cached phase result from Redis.
        
        Args:
            session_id: Session ID for cache key
            
        Returns:
            Cached result if exists, None otherwise
        """
        cache_key = f"phase_result:{session_id}:{self.phase_number}"
        cached = await redis_manager.get(cache_key)
        
        if cached:
            return json.loads(cached)
        return None
    
    async def _update_metrics(
        self,
        processing_time_ms: int,
        success: bool
    ) -> None:
        """Update agent metrics.
        
        Args:
            processing_time_ms: Processing time in milliseconds
            success: Whether processing was successful
        """
        self.metrics["total_processed"] += 1
        
        if not success:
            self.metrics["total_failures"] += 1
        
        # Update average processing time
        current_avg = self.metrics["average_processing_time"]
        total = self.metrics["total_processed"]
        self.metrics["average_processing_time"] = (
            (current_avg * (total - 1) + processing_time_ms) / total
        )
        
        # Store metrics in Redis
        metrics_key = f"agent_metrics:{self.phase_number}"
        await redis_manager.set(metrics_key, self.metrics, ttl=86400)  # 24 hours
    
    def get_phase_info(self) -> Dict[str, Any]:
        """Get phase information and current metrics.
        
        Returns:
            Phase info dictionary
        """
        return {
            "phase_number": self.phase_number,
            "phase_name": self.phase_name,
            "timeout_seconds": self.timeout_seconds,
            "metrics": self.metrics
        }