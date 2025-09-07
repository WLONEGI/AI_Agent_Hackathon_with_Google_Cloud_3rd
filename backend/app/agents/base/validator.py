"""Base validation classes for phase outputs."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re
import json

from app.core.logging import LoggerMixin


@dataclass
class ValidationError:
    """Represents a validation error."""
    field: str
    message: str
    severity: str = "error"  # error, warning, info
    code: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation process."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    score: float = 0.0  # Quality score 0-1
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    def add_error(self, field: str, message: str, code: Optional[str] = None):
        """Add validation error."""
        self.errors.append(ValidationError(field, message, "error", code))
        self.is_valid = False
    
    def add_warning(self, field: str, message: str, code: Optional[str] = None):
        """Add validation warning."""
        self.warnings.append(ValidationError(field, message, "warning", code))


class BaseValidator(ABC, LoggerMixin):
    """Abstract base class for phase output validation."""
    
    def __init__(self, phase_name: str):
        """Initialize validator.
        
        Args:
            phase_name: Name of the phase being validated
        """
        super().__init__()
        self.phase_name = phase_name
        
        # Define required fields for all phases
        self.required_fields = [
            "phase_number",
            "phase_name", 
            "status",
            "output"
        ]
        
        # Define quality metrics weights
        self.quality_weights = {
            "completeness": 0.3,
            "accuracy": 0.3,
            "consistency": 0.2,
            "format_compliance": 0.2
        }
    
    async def validate_output(self, output: Dict[str, Any]) -> ValidationResult:
        """Validate phase output.
        
        Args:
            output: Phase output to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        try:
            # Base validation
            await self._validate_required_fields(output, result)
            await self._validate_data_types(output, result)
            await self._validate_common_constraints(output, result)
            
            # Phase-specific validation
            await self._validate_phase_specific(output, result)
            
            # Calculate quality score
            result.score = await self._calculate_quality_score(output, result)
            
            self.logger.debug(
                f"Validation completed for {self.phase_name}",
                is_valid=result.is_valid,
                errors=len(result.errors),
                warnings=len(result.warnings),
                quality_score=result.score
            )
            
        except Exception as e:
            self.logger.error(f"Validation error for {self.phase_name}: {e}")
            result.add_error("validation", f"Internal validation error: {str(e)}")
        
        return result
    
    async def _validate_required_fields(
        self, 
        output: Dict[str, Any], 
        result: ValidationResult
    ):
        """Validate required fields are present."""
        for field in self.required_fields:
            if field not in output:
                result.add_error(field, f"Required field '{field}' is missing")
            elif output[field] is None:
                result.add_error(field, f"Required field '{field}' cannot be None")
    
    async def _validate_data_types(
        self, 
        output: Dict[str, Any], 
        result: ValidationResult
    ):
        """Validate data types."""
        # Phase number should be integer
        if "phase_number" in output:
            if not isinstance(output["phase_number"], int):
                result.add_error("phase_number", "Phase number must be an integer")
            elif output["phase_number"] < 1 or output["phase_number"] > 7:
                result.add_error("phase_number", "Phase number must be between 1 and 7")
        
        # Status should be string
        if "status" in output:
            if not isinstance(output["status"], str):
                result.add_error("status", "Status must be a string")
            elif output["status"] not in ["pending", "processing", "completed", "error"]:
                result.add_warning("status", f"Unexpected status value: {output['status']}")
    
    async def _validate_common_constraints(
        self, 
        output: Dict[str, Any], 
        result: ValidationResult
    ):
        """Validate common constraints across all phases."""
        
        # Check if output contains actual content
        if "output" in output:
            output_content = output["output"]
            
            if isinstance(output_content, dict):
                if not output_content:
                    result.add_error("output", "Output content cannot be empty")
            elif isinstance(output_content, str):
                if not output_content.strip():
                    result.add_error("output", "Output content cannot be empty string")
        
        # Validate timestamps if present
        if "timestamp" in output:
            try:
                datetime.fromisoformat(output["timestamp"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                result.add_error("timestamp", "Invalid timestamp format")
        
        # Check processing time if present
        if "processing_time" in output:
            processing_time = output["processing_time"]
            if not isinstance(processing_time, (int, float)):
                result.add_error("processing_time", "Processing time must be a number")
            elif processing_time < 0:
                result.add_error("processing_time", "Processing time cannot be negative")
            elif processing_time > 300:  # 5 minutes
                result.add_warning("processing_time", "Processing time seems unusually high")
    
    @abstractmethod
    async def _validate_phase_specific(
        self, 
        output: Dict[str, Any], 
        result: ValidationResult
    ):
        """Validate phase-specific requirements.
        
        This method should be implemented by each phase validator
        to check phase-specific output requirements.
        """
        pass
    
    async def _calculate_quality_score(
        self, 
        output: Dict[str, Any], 
        result: ValidationResult
    ) -> float:
        """Calculate quality score for the output.
        
        Args:
            output: Phase output
            result: Current validation result
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        scores = {}
        
        # Completeness score
        scores["completeness"] = await self._score_completeness(output, result)
        
        # Accuracy score (based on validation errors)
        scores["accuracy"] = await self._score_accuracy(output, result)
        
        # Consistency score
        scores["consistency"] = await self._score_consistency(output, result)
        
        # Format compliance score
        scores["format_compliance"] = await self._score_format_compliance(output, result)
        
        # Calculate weighted average
        total_score = 0.0
        for metric, weight in self.quality_weights.items():
            if metric in scores:
                total_score += scores[metric] * weight
        
        return max(0.0, min(1.0, total_score))
    
    async def _score_completeness(
        self, 
        output: Dict[str, Any], 
        result: ValidationResult
    ) -> float:
        """Score output completeness."""
        required_present = sum(
            1 for field in self.required_fields 
            if field in output and output[field] is not None
        )
        return required_present / len(self.required_fields) if self.required_fields else 1.0
    
    async def _score_accuracy(
        self, 
        output: Dict[str, Any], 
        result: ValidationResult
    ) -> float:
        """Score accuracy based on validation errors."""
        if not result.errors:
            return 1.0
        
        # Reduce score based on number of errors
        error_penalty = min(0.9, len(result.errors) * 0.2)
        return max(0.0, 1.0 - error_penalty)
    
    async def _score_consistency(
        self, 
        output: Dict[str, Any], 
        result: ValidationResult
    ) -> float:
        """Score internal consistency of output."""
        # Base implementation - can be overridden by phase validators
        consistency_score = 1.0
        
        # Check for contradictory information
        if "status" in output and "error" in output:
            if output["status"] == "completed" and output["error"]:
                consistency_score -= 0.3
        
        # Check for warnings that might indicate inconsistency
        warning_penalty = min(0.5, len(result.warnings) * 0.1)
        consistency_score -= warning_penalty
        
        return max(0.0, consistency_score)
    
    async def _score_format_compliance(
        self, 
        output: Dict[str, Any], 
        result: ValidationResult
    ) -> float:
        """Score format compliance."""
        compliance_score = 1.0
        
        # Check JSON serializability
        try:
            json.dumps(output)
        except (TypeError, ValueError):
            compliance_score -= 0.5
        
        # Check for proper data types
        type_errors = sum(
            1 for error in result.errors 
            if "must be" in error.message.lower()
        )
        
        if type_errors > 0:
            compliance_score -= min(0.4, type_errors * 0.2)
        
        return max(0.0, compliance_score)
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules for this validator."""
        return {
            "phase_name": self.phase_name,
            "required_fields": self.required_fields,
            "quality_weights": self.quality_weights
        }