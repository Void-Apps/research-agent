"""
Global error handlers for the AI Research Agent FastAPI application.

This module provides centralized error handling, logging, and response formatting
for all types of exceptions that can occur in the application.
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from exceptions import BaseResearchException


# Configure error logging
error_logger = logging.getLogger("error_handler")
error_logger.setLevel(logging.ERROR)


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    
    error: str
    message: str
    error_code: str
    status_code: int
    details: Optional[Dict[str, Any]] = None
    request_id: str
    timestamp: datetime
    path: Optional[str] = None


class ErrorMetrics:
    """Simple error metrics tracking."""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, datetime] = {}
    
    def record_error(self, error_code: str):
        """Record an error occurrence."""
        self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1
        self.last_errors[error_code] = datetime.utcnow()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current error metrics."""
        return {
            "error_counts": self.error_counts.copy(),
            "last_errors": {k: v.isoformat() for k, v in self.last_errors.items()},
            "total_errors": sum(self.error_counts.values())
        }


# Global error metrics instance
error_metrics = ErrorMetrics()


def generate_request_id() -> str:
    """Generate a unique request ID for error tracking."""
    return str(uuid.uuid4())


def log_error(
    error: Exception,
    request: Request,
    request_id: str,
    additional_context: Optional[Dict[str, Any]] = None
):
    """Log error with structured information."""
    context = {
        "request_id": request_id,
        "method": request.method,
        "url": str(request.url),
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if additional_context:
        context.update(additional_context)
    
    # Log the error with full traceback for debugging
    error_logger.error(
        f"Request {request_id} failed: {str(error)}",
        extra=context,
        exc_info=True
    )


async def base_research_exception_handler(request: Request, exc: BaseResearchException) -> JSONResponse:
    """Handle custom BaseResearchException and its subclasses."""
    request_id = generate_request_id()
    
    # Log the error
    log_error(exc, request, request_id, {"error_code": exc.error_code})
    
    # Record metrics
    error_metrics.record_error(exc.error_code)
    
    # Create error response
    error_response = ErrorResponse(
        error=exc.error_code,
        message=exc.message,
        error_code=exc.error_code,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id,
        timestamp=datetime.utcnow(),
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException."""
    request_id = generate_request_id()
    
    # Map HTTP status codes to error codes
    status_to_error_code = {
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
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = status_to_error_code.get(exc.status_code, "HTTP_ERROR")
    
    # Log the error
    log_error(exc, request, request_id, {"status_code": exc.status_code})
    
    # Record metrics
    error_metrics.record_error(error_code)
    
    # Create error response
    error_response = ErrorResponse(
        error=error_code,
        message=exc.detail,
        error_code=error_code,
        status_code=exc.status_code,
        details={"original_detail": exc.detail} if exc.detail else None,
        request_id=request_id,
        timestamp=datetime.utcnow(),
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    request_id = generate_request_id()
    
    # Extract validation error details
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    # Log the error
    log_error(
        exc, 
        request, 
        request_id, 
        {"validation_errors": validation_errors}
    )
    
    # Record metrics
    error_metrics.record_error("VALIDATION_ERROR")
    
    # Create error response
    error_response = ErrorResponse(
        error="VALIDATION_ERROR",
        message="Request validation failed",
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": validation_errors},
        request_id=request_id,
        timestamp=datetime.utcnow(),
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode='json')
    )


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle Starlette HTTP exceptions."""
    request_id = generate_request_id()
    
    error_code = f"HTTP_{exc.status_code}"
    
    # Log the error
    log_error(exc, request, request_id, {"status_code": exc.status_code})
    
    # Record metrics
    error_metrics.record_error(error_code)
    
    # Create error response
    error_response = ErrorResponse(
        error=error_code,
        message=exc.detail,
        error_code=error_code,
        status_code=exc.status_code,
        details=None,
        request_id=request_id,
        timestamp=datetime.utcnow(),
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions."""
    request_id = generate_request_id()
    
    # Log the error with full traceback
    log_error(
        exc, 
        request, 
        request_id, 
        {"traceback": traceback.format_exc()}
    )
    
    # Record metrics
    error_metrics.record_error("INTERNAL_SERVER_ERROR")
    
    # Create error response (don't expose internal error details in production)
    error_response = ErrorResponse(
        error="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        error_code="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=None,  # Don't expose internal details
        request_id=request_id,
        timestamp=datetime.utcnow(),
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


def setup_error_handlers(app):
    """Set up all error handlers for the FastAPI application."""
    
    # Custom exception handlers
    app.add_exception_handler(BaseResearchException, base_research_exception_handler)
    
    # FastAPI built-in exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    
    # Global exception handler (catch-all)
    app.add_exception_handler(Exception, global_exception_handler)


def get_error_metrics() -> Dict[str, Any]:
    """Get current error metrics."""
    return error_metrics.get_metrics()