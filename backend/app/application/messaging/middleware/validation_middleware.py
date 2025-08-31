"""Validation middleware for CQRS messages."""

from typing import Any, Dict, List, Optional, Callable
import logging
from datetime import datetime

from app.application.commands.base_command import AbstractCommand, CommandResult
from app.application.queries.base_query import AbstractQuery, QueryResult
from .base_middleware import Middleware, NextHandler, Message, MessageResult

logger = logging.getLogger(__name__)


class ValidationMiddleware(Middleware):
    """Middleware for validating commands and queries.
    
    Features:
    - Built-in validation using message.validate()
    - Custom validation rules
    - Schema validation support
    - Detailed error reporting
    """
    
    def __init__(self):
        self._custom_validators: Dict[type, List[Callable]] = {}
        self._schema_validators: Dict[type, Callable] = {}
        self._validation_metrics: Dict[str, Any] = {}
    
    def register_custom_validator(
        self, 
        message_type: type, 
        validator: Callable[[Message], None]
    ) -> None:
        """Register custom validator for message type.
        
        Args:
            message_type: Type of message to validate
            validator: Validation function that raises ValueError on failure
        """
        if message_type not in self._custom_validators:
            self._custom_validators[message_type] = []
        
        self._custom_validators[message_type].append(validator)
        logger.info(f"Registered custom validator for {message_type.__name__}")
    
    def register_schema_validator(
        self, 
        message_type: type, 
        validator: Callable[[Message], None]
    ) -> None:
        """Register schema validator for message type.
        
        Args:
            message_type: Type of message to validate
            validator: Schema validation function
        """
        self._schema_validators[message_type] = validator
        logger.info(f"Registered schema validator for {message_type.__name__}")
    
    async def handle(self, message: Message, next_handler: NextHandler) -> MessageResult:
        """Validate message before proceeding to next handler.
        
        Args:
            message: Message to validate
            next_handler: Next handler in pipeline
            
        Returns:
            Validation result or next handler result
        """
        message_type = type(message)
        message_name = message_type.__name__
        
        try:
            # Update metrics
            await self._update_validation_metrics(message_name, 'attempted')
            
            # 1. Built-in validation
            await self._run_builtin_validation(message)
            
            # 2. Schema validation
            await self._run_schema_validation(message)
            
            # 3. Custom validation rules
            await self._run_custom_validation(message)
            
            # All validations passed, proceed to next handler
            await self._update_validation_metrics(message_name, 'passed')
            return await next_handler()
            
        except ValueError as ve:
            # Validation failed
            error_msg = f"Validation failed for {message_name}: {str(ve)}"
            logger.warning(error_msg)
            await self._update_validation_metrics(message_name, 'failed', str(ve))
            
            if isinstance(message, AbstractCommand):
                return CommandResult.validation_error(str(ve))
            else:
                return QueryResult.validation_error(str(ve))
                
        except Exception as e:
            # Unexpected validation error
            error_msg = f"Validation error for {message_name}: {str(e)}"
            logger.error(error_msg)
            await self._update_validation_metrics(message_name, 'error', str(e))
            
            if isinstance(message, AbstractCommand):
                return CommandResult.error_result(
                    f"Validation system error: {str(e)}",
                    "VALIDATION_SYSTEM_ERROR"
                )
            else:
                return QueryResult.error_result(
                    f"Validation system error: {str(e)}",
                    "VALIDATION_SYSTEM_ERROR"
                )
    
    async def _run_builtin_validation(self, message: Message) -> None:
        """Run built-in message validation.
        
        Args:
            message: Message to validate
            
        Raises:
            ValueError: If validation fails
        """
        try:
            message.validate()
        except Exception as e:
            raise ValueError(f"Built-in validation failed: {str(e)}")
    
    async def _run_schema_validation(self, message: Message) -> None:
        """Run schema validation if registered.
        
        Args:
            message: Message to validate
            
        Raises:
            ValueError: If schema validation fails
        """
        message_type = type(message)
        
        if message_type in self._schema_validators:
            try:
                validator = self._schema_validators[message_type]
                validator(message)
            except Exception as e:
                raise ValueError(f"Schema validation failed: {str(e)}")
    
    async def _run_custom_validation(self, message: Message) -> None:
        """Run custom validation rules if registered.
        
        Args:
            message: Message to validate
            
        Raises:
            ValueError: If any custom validation fails
        """
        message_type = type(message)
        
        if message_type in self._custom_validators:
            validators = self._custom_validators[message_type]
            
            for i, validator in enumerate(validators):
                try:
                    validator(message)
                except Exception as e:
                    raise ValueError(f"Custom validation rule {i+1} failed: {str(e)}")
    
    async def _update_validation_metrics(
        self, 
        message_name: str, 
        status: str,
        error: Optional[str] = None
    ) -> None:
        """Update validation metrics.
        
        Args:
            message_name: Name of message type
            status: Validation status (attempted, passed, failed, error)
            error: Error message if applicable
        """
        if message_name not in self._validation_metrics:
            self._validation_metrics[message_name] = {
                'attempted': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'success_rate': 0.0,
                'last_validation': None,
                'last_error': None
            }
        
        metrics = self._validation_metrics[message_name]
        
        if status == 'attempted':
            metrics['attempted'] += 1
            metrics['last_validation'] = datetime.utcnow().isoformat()
        elif status == 'passed':
            metrics['passed'] += 1
        elif status == 'failed':
            metrics['failed'] += 1
            metrics['last_error'] = error
        elif status == 'error':
            metrics['errors'] += 1
            metrics['last_error'] = error
        
        # Calculate success rate
        total_completed = metrics['passed'] + metrics['failed'] + metrics['errors']
        if total_completed > 0:
            metrics['success_rate'] = metrics['passed'] / total_completed
    
    def get_validation_metrics(self) -> Dict[str, Any]:
        """Get validation metrics for all message types.
        
        Returns:
            Dictionary of validation metrics by message type
        """
        return self._validation_metrics.copy()
    
    def clear_validation_metrics(self) -> None:
        """Clear all validation metrics."""
        self._validation_metrics.clear()
        logger.info("Validation metrics cleared")


class BusinessRuleValidationMiddleware(ValidationMiddleware):
    """Specialized validation middleware for business rules.
    
    Provides enhanced validation capabilities for complex
    business logic validation beyond simple field validation.
    """
    
    def __init__(self):
        super().__init__()
        self._business_rules: Dict[type, List[Callable]] = {}
    
    def register_business_rule(
        self, 
        message_type: type, 
        rule: Callable[[Message], bool],
        error_message: str
    ) -> None:
        """Register business rule validator.
        
        Args:
            message_type: Type of message to validate
            rule: Business rule function that returns True if valid
            error_message: Error message to show if rule fails
        """
        if message_type not in self._business_rules:
            self._business_rules[message_type] = []
        
        def rule_validator(message: Message) -> None:
            if not rule(message):
                raise ValueError(error_message)
        
        self._business_rules[message_type].append(rule_validator)
        logger.info(f"Registered business rule for {message_type.__name__}: {error_message}")
    
    async def _run_custom_validation(self, message: Message) -> None:
        """Run custom validation including business rules.
        
        Args:
            message: Message to validate
            
        Raises:
            ValueError: If any validation fails
        """
        # Run base custom validation
        await super()._run_custom_validation(message)
        
        # Run business rules
        message_type = type(message)
        
        if message_type in self._business_rules:
            business_rules = self._business_rules[message_type]
            
            for i, rule_validator in enumerate(business_rules):
                try:
                    rule_validator(message)
                except Exception as e:
                    raise ValueError(f"Business rule {i+1} failed: {str(e)}")


class ValidationResult:
    """Detailed validation result with field-level errors."""
    
    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.field_errors: Dict[str, List[str]] = {}
        self.warnings: List[str] = []
    
    def add_error(self, error: str, field: Optional[str] = None) -> None:
        """Add validation error.
        
        Args:
            error: Error message
            field: Field name if field-specific error
        """
        self.is_valid = False
        self.errors.append(error)
        
        if field:
            if field not in self.field_errors:
                self.field_errors[field] = []
            self.field_errors[field].append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add validation warning.
        
        Args:
            warning: Warning message
        """
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'field_errors': self.field_errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }