"""Centralized error handling for API v1."""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import logging
import traceback
from typing import Dict, Any
from datetime import datetime
from uuid import uuid4

from app.core.config import settings


logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error class."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class BusinessLogicError(APIError):
    """Business logic validation error."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details
        )


class ResourceNotFoundError(APIError):
    """Resource not found error."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )


class AuthenticationError(APIError):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(APIError):
    """Authorization error."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR"
        )


class RateLimitError(APIError):
    """Rate limit exceeded error."""
    
    def __init__(self, retry_after: int = 3600):
        super().__init__(
            message="Rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )


class SessionStateError(APIError):
    """Session state error for manga generation."""
    
    def __init__(self, current_state: str, required_state: str):
        super().__init__(
            message=f"Invalid session state. Current: {current_state}, Required: {required_state}",
            status_code=status.HTTP_409_CONFLICT,
            error_code="INVALID_SESSION_STATE",
            details={"current_state": current_state, "required_state": required_state}
        )


class WebSocketError(APIError):
    """WebSocket specific error."""
    
    def __init__(self, message: str, ws_code: int = 1011):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="WEBSOCKET_ERROR",
            details={"websocket_code": ws_code}
        )


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Dict[str, Any] = None,
    request_id: str = None
) -> JSONResponse:
    """Create standardized error response."""
    
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id or str(uuid4()),
            "status_code": status_code
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if settings.debug:
        error_response["error"]["debug"] = True
    
    return JSONResponse(
        status_code=status_code,
        content=error_response,
        headers={"X-Error-Code": error_code}
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors."""
    
    request_id = getattr(request.state, "request_id", str(uuid4()))
    
    logger.warning(
        f"API Error: {exc.error_code} - {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method,
            "details": exc.details
        }
    )
    
    return create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    
    request_id = getattr(request.state, "request_id", str(uuid4()))
    
    # Map HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED", 
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method
        }
    )
    
    return create_error_response(
        error_code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code,
        request_id=request_id
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    
    request_id = getattr(request.state, "request_id", str(uuid4()))
    
    # Format validation errors
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    logger.warning(
        f"Validation Error: {len(validation_errors)} field(s)",
        extra={
            "request_id": request_id,
            "validation_errors": validation_errors,
            "path": str(request.url.path),
            "method": request.method
        }
    )
    
    return create_error_response(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": validation_errors},
        request_id=request_id
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    
    request_id = getattr(request.state, "request_id", str(uuid4()))
    
    if isinstance(exc, IntegrityError):
        error_code = "DATABASE_INTEGRITY_ERROR"
        message = "Database constraint violation"
        status_code = status.HTTP_409_CONFLICT
        
        # Extract constraint details if possible
        details = {}
        if hasattr(exc, 'orig') and exc.orig:
            details["constraint_error"] = str(exc.orig)
    
    else:
        error_code = "DATABASE_ERROR"
        message = "Database operation failed"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        details = {}
    
    # Handle WebSocket connections (they don't have method attribute)
    extra_info = {
        "request_id": request_id,
        "exception": str(exc),
    }
    
    if hasattr(request, 'url'):
        extra_info["path"] = str(request.url.path)
    if hasattr(request, 'method'):
        extra_info["method"] = request.method
    else:
        extra_info["connection_type"] = "websocket"
    
    logger.error(
        f"Database Error: {error_code} - {message}",
        extra=extra_info,
        exc_info=True
    )
    
    return create_error_response(
        error_code=error_code,
        message=message,
        status_code=status_code,
        details=details if settings.debug else None,
        request_id=request_id
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions."""
    
    request_id = getattr(request.state, "request_id", str(uuid4()))
    
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method,
            "traceback": traceback.format_exc() if settings.debug else None
        },
        exc_info=True
    )
    
    # Don't expose internal errors in production
    if settings.is_production():
        message = "An internal error occurred"
        details = None
    else:
        message = f"{type(exc).__name__}: {str(exc)}"
        details = {"traceback": traceback.format_exc()}
    
    return create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
        request_id=request_id
    )


# Error reporting utilities
class ErrorReporter:
    """Error reporting and monitoring integration."""
    
    @staticmethod
    async def report_error(
        error: Exception,
        context: Dict[str, Any],
        severity: str = "error"
    ) -> None:
        """Report error to monitoring system."""
        
        # TODO: Integrate with monitoring service (Sentry, CloudWatch, etc.)
        logger.log(
            level=getattr(logging, severity.upper(), logging.ERROR),
            msg=f"Error reported: {type(error).__name__}",
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "severity": severity
            },
            exc_info=True
        )
    
    @staticmethod
    async def report_performance_issue(
        operation: str,
        duration: float,
        threshold: float,
        context: Dict[str, Any]
    ) -> None:
        """Report performance issues."""
        
        if duration > threshold:
            logger.warning(
                f"Performance issue: {operation} took {duration:.2f}s (threshold: {threshold}s)",
                extra={
                    "operation": operation,
                    "duration": duration,
                    "threshold": threshold,
                    "context": context
                }
            )


# Error context middleware
class ErrorContextMiddleware:
    """Middleware to add error context to requests."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add request ID
            scope["state"] = getattr(scope, "state", {})
            scope["state"]["request_id"] = str(uuid4())
        
        await self.app(scope, receive, send)