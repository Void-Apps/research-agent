"""
Custom exception classes for the AI Research Agent application.

This module defines custom exceptions for different error types that can occur
throughout the application, providing structured error handling and proper
HTTP status code mapping.
"""

from typing import Optional, Dict, Any
from fastapi import status


class BaseResearchException(Exception):
    """Base exception class for all research agent exceptions."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseResearchException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=error_details
        )


class QueryNotFoundError(BaseResearchException):
    """Raised when a research query is not found."""
    
    def __init__(self, query_id: str):
        super().__init__(
            message=f"Research query '{query_id}' not found",
            error_code="QUERY_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"query_id": query_id}
        )


class QueryProcessingError(BaseResearchException):
    """Raised when query processing fails."""
    
    def __init__(self, query_id: str, reason: str, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details.update({"query_id": query_id, "reason": reason})
        
        super().__init__(
            message=f"Failed to process query '{query_id}': {reason}",
            error_code="QUERY_PROCESSING_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=error_details
        )


class ExternalAPIError(BaseResearchException):
    """Raised when external API calls fail."""
    
    def __init__(self, service: str, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details.update({"service": service, "operation": operation, "reason": reason})
        
        super().__init__(
            message=f"External API error in {service} during {operation}: {reason}",
            error_code="EXTERNAL_API_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=error_details
        )


class RateLimitError(BaseResearchException):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, service: str, retry_after: Optional[int] = None):
        details = {"service": service}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            message=f"Rate limit exceeded for {service}",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class DatabaseError(BaseResearchException):
    """Raised when database operations fail."""
    
    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details.update({"operation": operation, "reason": reason})
        
        super().__init__(
            message=f"Database error during {operation}: {reason}",
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=error_details
        )


class CacheError(BaseResearchException):
    """Raised when cache operations fail."""
    
    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details.update({"operation": operation, "reason": reason})
        
        super().__init__(
            message=f"Cache error during {operation}: {reason}",
            error_code="CACHE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=error_details
        )


class AIServiceError(BaseResearchException):
    """Raised when AI service operations fail."""
    
    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details.update({"operation": operation, "reason": reason})
        
        super().__init__(
            message=f"AI service error during {operation}: {reason}",
            error_code="AI_SERVICE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=error_details
        )


class ConfigurationError(BaseResearchException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, config_key: str, reason: str):
        super().__init__(
            message=f"Configuration error for '{config_key}': {reason}",
            error_code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"config_key": config_key, "reason": reason}
        )


class AuthenticationError(BaseResearchException):
    """Raised when authentication fails."""
    
    def __init__(self, service: str, reason: str):
        super().__init__(
            message=f"Authentication failed for {service}: {reason}",
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"service": service, "reason": reason}
        )


class AuthorizationError(BaseResearchException):
    """Raised when authorization fails."""
    
    def __init__(self, resource: str, action: str, reason: str):
        super().__init__(
            message=f"Authorization failed for {action} on {resource}: {reason}",
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"resource": resource, "action": action, "reason": reason}
        )


class ResourceLimitError(BaseResearchException):
    """Raised when resource limits are exceeded."""
    
    def __init__(self, resource: str, limit: str, current: str):
        super().__init__(
            message=f"Resource limit exceeded for {resource}: {current} exceeds limit of {limit}",
            error_code="RESOURCE_LIMIT_EXCEEDED",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details={"resource": resource, "limit": limit, "current": current}
        )


class ServiceUnavailableError(BaseResearchException):
    """Raised when a service is temporarily unavailable."""
    
    def __init__(self, service: str, reason: str, retry_after: Optional[int] = None):
        details = {"service": service, "reason": reason}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            message=f"Service {service} is temporarily unavailable: {reason}",
            error_code="SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )