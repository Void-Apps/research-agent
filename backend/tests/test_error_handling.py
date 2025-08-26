"""
Comprehensive tests for error handling in the AI Research Agent application.

This module tests all custom exception classes, global error handlers,
error logging, and error response formatting.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from main import app
from exceptions import (
    BaseResearchException,
    ValidationError as CustomValidationError,
    QueryNotFoundError,
    QueryProcessingError,
    ExternalAPIError,
    RateLimitError,
    DatabaseError,
    CacheError,
    AIServiceError,
    ConfigurationError,
    AuthenticationError,
    AuthorizationError,
    ResourceLimitError,
    ServiceUnavailableError
)
from error_handlers import (
    ErrorResponse,
    ErrorMetrics,
    generate_request_id,
    log_error,
    base_research_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    starlette_http_exception_handler,
    global_exception_handler,
    get_error_metrics
)

client = TestClient(app)


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_base_research_exception(self):
        """Test BaseResearchException initialization."""
        exc = BaseResearchException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details={"key": "value"}
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 400
        assert exc.details == {"key": "value"}
        assert str(exc) == "Test error"
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        exc = CustomValidationError("Invalid input", field="query")
        
        assert exc.message == "Invalid input"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 400
        assert exc.details["field"] == "query"
    
    def test_query_not_found_error(self):
        """Test QueryNotFoundError exception."""
        exc = QueryNotFoundError("test-query-id")
        
        assert "test-query-id" in exc.message
        assert exc.error_code == "QUERY_NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details["query_id"] == "test-query-id"
    
    def test_query_processing_error(self):
        """Test QueryProcessingError exception."""
        exc = QueryProcessingError("test-id", "Processing failed", {"step": "analysis"})
        
        assert "test-id" in exc.message
        assert "Processing failed" in exc.message
        assert exc.error_code == "QUERY_PROCESSING_ERROR"
        assert exc.status_code == 500
        assert exc.details["query_id"] == "test-id"
        assert exc.details["reason"] == "Processing failed"
        assert exc.details["step"] == "analysis"
    
    def test_external_api_error(self):
        """Test ExternalAPIError exception."""
        exc = ExternalAPIError("Google Scholar", "search", "Rate limit exceeded")
        
        assert "Google Scholar" in exc.message
        assert "search" in exc.message
        assert exc.error_code == "EXTERNAL_API_ERROR"
        assert exc.status_code == 502
        assert exc.details["service"] == "Google Scholar"
        assert exc.details["operation"] == "search"
    
    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        exc = RateLimitError("Google Books", retry_after=60)
        
        assert "Google Books" in exc.message
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == 429
        assert exc.details["service"] == "Google Books"
        assert exc.details["retry_after_seconds"] == 60
    
    def test_database_error(self):
        """Test DatabaseError exception."""
        exc = DatabaseError("insert", "Connection timeout")
        
        assert "insert" in exc.message
        assert "Connection timeout" in exc.message
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.status_code == 500
    
    def test_cache_error(self):
        """Test CacheError exception."""
        exc = CacheError("get", "Cache miss")
        
        assert "get" in exc.message
        assert exc.error_code == "CACHE_ERROR"
        assert exc.status_code == 500
    
    def test_ai_service_error(self):
        """Test AIServiceError exception."""
        exc = AIServiceError("synthesis", "Model unavailable")
        
        assert "synthesis" in exc.message
        assert exc.error_code == "AI_SERVICE_ERROR"
        assert exc.status_code == 500
    
    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        exc = ConfigurationError("API_KEY", "Missing required configuration")
        
        assert "API_KEY" in exc.message
        assert exc.error_code == "CONFIGURATION_ERROR"
        assert exc.status_code == 500
    
    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        exc = AuthenticationError("Google Scholar", "Invalid API key")
        
        assert "Google Scholar" in exc.message
        assert exc.error_code == "AUTHENTICATION_ERROR"
        assert exc.status_code == 401
    
    def test_authorization_error(self):
        """Test AuthorizationError exception."""
        exc = AuthorizationError("research_data", "read", "Insufficient permissions")
        
        assert "research_data" in exc.message
        assert exc.error_code == "AUTHORIZATION_ERROR"
        assert exc.status_code == 403
    
    def test_resource_limit_error(self):
        """Test ResourceLimitError exception."""
        exc = ResourceLimitError("query_length", "1000", "1500")
        
        assert "query_length" in exc.message
        assert exc.error_code == "RESOURCE_LIMIT_EXCEEDED"
        assert exc.status_code == 413
    
    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError exception."""
        exc = ServiceUnavailableError("ScienceDirect", "Maintenance", retry_after=300)
        
        assert "ScienceDirect" in exc.message
        assert exc.error_code == "SERVICE_UNAVAILABLE"
        assert exc.status_code == 503
        assert exc.details["retry_after_seconds"] == 300


class TestErrorMetrics:
    """Test error metrics tracking."""
    
    def test_error_metrics_initialization(self):
        """Test ErrorMetrics initialization."""
        metrics = ErrorMetrics()
        
        assert metrics.error_counts == {}
        assert metrics.last_errors == {}
    
    def test_record_error(self):
        """Test recording errors."""
        metrics = ErrorMetrics()
        
        metrics.record_error("TEST_ERROR")
        metrics.record_error("TEST_ERROR")
        metrics.record_error("OTHER_ERROR")
        
        assert metrics.error_counts["TEST_ERROR"] == 2
        assert metrics.error_counts["OTHER_ERROR"] == 1
        assert "TEST_ERROR" in metrics.last_errors
        assert "OTHER_ERROR" in metrics.last_errors
    
    def test_get_metrics(self):
        """Test getting metrics."""
        metrics = ErrorMetrics()
        metrics.record_error("TEST_ERROR")
        
        result = metrics.get_metrics()
        
        assert "error_counts" in result
        assert "last_errors" in result
        assert "total_errors" in result
        assert result["error_counts"]["TEST_ERROR"] == 1
        assert result["total_errors"] == 1


class TestErrorHandlers:
    """Test error handler functions."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/test"
        request.url.__str__ = Mock(return_value="http://localhost/api/test")
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-agent"}
        return request
    
    def test_generate_request_id(self):
        """Test request ID generation."""
        request_id = generate_request_id()
        
        assert isinstance(request_id, str)
        assert len(request_id) > 0
        
        # Should generate unique IDs
        another_id = generate_request_id()
        assert request_id != another_id
    
    @patch('error_handlers.error_logger')
    def test_log_error(self, mock_logger, mock_request):
        """Test error logging."""
        error = Exception("Test error")
        request_id = "test-request-id"
        
        log_error(error, mock_request, request_id, {"extra": "context"})
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        assert "test-request-id" in call_args[0][0]
        assert call_args[1]["extra"]["request_id"] == request_id
        assert call_args[1]["extra"]["method"] == "POST"
        assert call_args[1]["extra"]["extra"] == "context"
    
    @pytest.mark.asyncio
    async def test_base_research_exception_handler(self, mock_request):
        """Test BaseResearchException handler."""
        exc = QueryNotFoundError("test-id")
        
        response = await base_research_exception_handler(mock_request, exc)
        
        assert response.status_code == 404
        
        content = json.loads(response.body)
        assert content["error"] == "QUERY_NOT_FOUND"
        assert content["error_code"] == "QUERY_NOT_FOUND"
        assert content["status_code"] == 404
        assert "test-id" in content["message"]
        assert "request_id" in content
        assert "timestamp" in content
    
    @pytest.mark.asyncio
    async def test_http_exception_handler(self, mock_request):
        """Test HTTPException handler."""
        exc = HTTPException(status_code=400, detail="Bad request")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 400
        
        content = json.loads(response.body)
        assert content["error"] == "BAD_REQUEST"
        assert content["message"] == "Bad request"
        assert content["status_code"] == 400
    
    @pytest.mark.asyncio
    async def test_validation_exception_handler(self, mock_request):
        """Test RequestValidationError handler."""
        # Create a mock validation error
        error_detail = {
            "loc": ("body", "query"),
            "msg": "field required",
            "type": "value_error.missing",
            "input": None
        }
        
        exc = RequestValidationError([error_detail])
        
        response = await validation_exception_handler(mock_request, exc)
        
        assert response.status_code == 422
        
        content = json.loads(response.body)
        assert content["error"] == "VALIDATION_ERROR"
        assert content["error_code"] == "VALIDATION_ERROR"
        assert "validation_errors" in content["details"]
    
    @pytest.mark.asyncio
    async def test_starlette_http_exception_handler(self, mock_request):
        """Test StarletteHTTPException handler."""
        exc = StarletteHTTPException(status_code=404, detail="Not found")
        
        response = await starlette_http_exception_handler(mock_request, exc)
        
        assert response.status_code == 404
        
        content = json.loads(response.body)
        assert content["error"] == "HTTP_404"
        assert content["message"] == "Not found"
    
    @pytest.mark.asyncio
    async def test_global_exception_handler(self, mock_request):
        """Test global exception handler."""
        exc = Exception("Unexpected error")
        
        response = await global_exception_handler(mock_request, exc)
        
        assert response.status_code == 500
        
        content = json.loads(response.body)
        assert content["error"] == "INTERNAL_SERVER_ERROR"
        assert content["error_code"] == "INTERNAL_SERVER_ERROR"
        assert content["message"] == "An unexpected error occurred"
        # Details should be None to avoid exposing internal errors
        assert content["details"] is None


class TestErrorHandlingIntegration:
    """Test error handling integration with FastAPI."""
    
    def test_custom_exception_integration(self):
        """Test custom exception handling through API."""
        # This would require setting up a test endpoint that raises custom exceptions
        # For now, we'll test the existing endpoints
        
        # Test 404 error
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert "request_id" in data
        assert "timestamp" in data
    
    def test_validation_error_integration(self):
        """Test validation error handling through API."""
        # Test with invalid JSON
        response = client.post("/api/research/query", json={})
        
        # Should return validation error
        assert response.status_code in [400, 422]
        
        data = response.json()
        assert "error" in data
        assert "request_id" in data
    
    def test_method_not_allowed_integration(self):
        """Test method not allowed error handling."""
        response = client.delete("/api/health")
        
        assert response.status_code == 405
        
        data = response.json()
        assert "error" in data
        assert "request_id" in data
    
    def test_error_metrics_endpoint(self):
        """Test error metrics are exposed through health endpoint."""
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "errors" in data
        assert "error_counts" in data["errors"]
        assert "total_errors" in data["errors"]


class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_error_response_creation(self):
        """Test ErrorResponse model creation."""
        response = ErrorResponse(
            error="TEST_ERROR",
            message="Test message",
            error_code="TEST_ERROR",
            status_code=400,
            details={"key": "value"},
            request_id="test-id",
            timestamp=datetime.utcnow(),
            path="/api/test"
        )
        
        assert response.error == "TEST_ERROR"
        assert response.message == "Test message"
        assert response.error_code == "TEST_ERROR"
        assert response.status_code == 400
        assert response.details == {"key": "value"}
        assert response.request_id == "test-id"
        assert response.path == "/api/test"
    
    def test_error_response_serialization(self):
        """Test ErrorResponse model serialization."""
        response = ErrorResponse(
            error="TEST_ERROR",
            message="Test message",
            error_code="TEST_ERROR",
            status_code=400,
            request_id="test-id",
            timestamp=datetime.utcnow()
        )
        
        data = response.model_dump()
        
        assert data["error"] == "TEST_ERROR"
        assert data["message"] == "Test message"
        assert data["status_code"] == 400
        assert "timestamp" in data


class TestErrorLogging:
    """Test error logging functionality."""
    
    @patch('error_handlers.error_logger')
    def test_error_logging_structure(self, mock_logger):
        """Test that errors are logged with proper structure."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.__str__ = Mock(return_value="http://test.com/api/test")
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-agent"}
        
        error = Exception("Test error")
        request_id = "test-request-id"
        
        log_error(error, request, request_id)
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        # Check log message
        assert "test-request-id" in call_args[0][0]
        
        # Check extra context
        extra = call_args[1]["extra"]
        assert extra["request_id"] == request_id
        assert extra["method"] == "GET"
        assert extra["client_ip"] == "127.0.0.1"
        assert extra["user_agent"] == "test-agent"
        assert extra["error_type"] == "Exception"
        assert extra["error_message"] == "Test error"
        
        # Check that exc_info is True for traceback
        assert call_args[1]["exc_info"] is True


if __name__ == "__main__":
    pytest.main([__file__])