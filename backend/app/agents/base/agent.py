"""Base Agent class for all phase processing agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from uuid import UUID

from app.core.logging import LoggerMixin
from .executor import PhaseExecutor
from .validator import BaseValidator
from .metrics import AgentMetrics


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
        super().__init__()
        
        self.phase_number = phase_number
        self.phase_name = phase_name
        self.timeout_seconds = timeout_seconds
        
        # Initialize components
        self.executor = PhaseExecutor(timeout_seconds)
        self.validator = self._create_validator()
        self.metrics = AgentMetrics(phase_number, phase_name)
        
        self.logger.info(
            f"Initialized {self.phase_name} agent",
            phase_number=phase_number,
            timeout=timeout_seconds
        )
    
    @abstractmethod
    def _create_validator(self) -> BaseValidator:
        """Create phase-specific validator."""
        pass
    
    @abstractmethod
    async def _generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate AI prompt for this phase."""
        pass
    
    @abstractmethod
    async def _process_ai_response(
        self,
        ai_response: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process AI response into structured output."""
        pass
    
    @abstractmethod
    async def _generate_preview(
        self,
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate preview data for this phase."""
        pass
    
    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: str,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Process the phase with input data."""
        
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(
                f"Starting {self.phase_name} processing",
                session_id=session_id,
                phase_number=self.phase_number
            )
            
            # Generate prompt
            prompt = await self._generate_prompt(input_data, previous_results)
            
            # Execute phase processing
            result = await self.executor.execute_with_timeout(
                self._execute_phase_logic,
                input_data,
                session_id,
                prompt,
                timeout=self.timeout_seconds
            )
            
            # Validate output
            validation_result = await self.validator.validate_output(result)
            if not validation_result.is_valid:
                raise ValueError(f"Validation failed: {validation_result.errors}")
            
            # Generate preview
            preview = await self._generate_preview(result)
            result["preview"] = preview
            
            # Update metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            await self.metrics.record_success(processing_time)
            
            self.logger.info(
                f"Completed {self.phase_name} processing",
                session_id=session_id,
                processing_time=processing_time
            )
            
            return {
                "phase_number": self.phase_number,
                "phase_name": self.phase_name,
                "status": "completed",
                "processing_time": processing_time,
                "output": result,
                "preview": preview,
                "validation_passed": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            await self.metrics.record_failure(processing_time)
            
            self.logger.error(
                f"Failed {self.phase_name} processing",
                session_id=session_id,
                error=str(e),
                processing_time=processing_time
            )
            
            return {
                "phase_number": self.phase_number,
                "phase_name": self.phase_name,
                "status": "failed",
                "processing_time": processing_time,
                "error": str(e),
                "validation_passed": False,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_phase_logic(
        self,
        input_data: Dict[str, Any],
        session_id: str,
        prompt: str
    ) -> Dict[str, Any]:
        """Execute the core phase processing logic."""
        
        # This is a placeholder for AI service call
        # In real implementation, this would call Vertex AI or other AI services
        ai_response = await self._simulate_ai_call(prompt)
        
        # Process AI response into structured output
        processed_result = await self._process_ai_response(ai_response, input_data)
        
        return processed_result
    
    async def _simulate_ai_call(self, prompt: str) -> str:
        """Simulate AI service call for development."""
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        return json.dumps({
            "phase": self.phase_number,
            "result": f"Simulated AI response for {self.phase_name}",
            "prompt_length": len(prompt),
            "confidence": 0.85
        })
    
    async def apply_feedback(
        self,
        output_data: Dict[str, Any],
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply HITL feedback to phase output."""
        
        self.logger.info(
            f"Applying feedback to {self.phase_name}",
            feedback_type=feedback.get("type")
        )
        
        # Base implementation - subclasses can override
        updated_output = output_data.copy()
        updated_output["feedback_applied"] = feedback
        updated_output["revised_at"] = datetime.utcnow().isoformat()
        
        return updated_output
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        return await self.metrics.get_summary()