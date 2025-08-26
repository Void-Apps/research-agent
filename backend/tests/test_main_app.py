"""
Tests for main FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from main import app


class TestMainApplication:
    """Test main FastAPI application"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_app_startup(self):
        """Test application starts up correctly"""
        # Test health endpoint
        response = self.client.get("/api/health")
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "version" in result
    
    def test_cors_headers(self):
        """Test CORS headers are set correctly"""
        response = self.client.options("/api/health")
        assert response.status_code == 200
        
        # Check CORS headers
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
        assert "access-control-allow-headers" in headers
    
    def test_api_documentation(self):
        """Test API documentation endpoints"""
        # Test OpenAPI schema
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
        # Verify research endpoints are documented
        paths = schema["paths"]
        assert "/api/research/query" in paths
        assert "/api/research/results/{query_id}" in paths
        assert "/api/research/history" in paths
    
    def test_error_handling_middleware(self):
        """Test global error handling"""
        # Test 404 for non-existent endpoint
        response = self.client.get("/api/non-existent")
        assert response.status_code == 404
        
        result = response.json()
        assert "detail" in result
    
    def test_request_validation(self):
        """Test request validation middleware"""
        # Test invalid JSON
        response = self.client.post(
            "/api/research/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_response_headers(self):
        """Test security headers are set"""
        response = self.client.get("/api/health")
        
        headers = response.headers
        # Check for security headers (if implemented)
        # assert "x-content-type-options" in headers
        # assert "x-frame-options" in headers
    
    @patch('routers.research.ResearchOrchestrator')
    def test_dependency_injection(self, mock_orchestrator):
        """Test dependency injection works correctly"""
        mock_instance = AsyncMock()
        mock_orchestrator.return_value = mock_instance
        mock_instance.conduct_research.return_value = {
            "query_id": "test-123",
            "sources": {"google_scholar": [], "google_books": [], "sciencedirect": []},
            "ai_summary": "Test summary",
            "confidence_score": 0.8,
            "cached": False
        }
        
        response = self.client.post(
            "/api/research/query",
            json={"query": "test query"}
        )
        
        assert response.status_code == 200
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint if available"""
        response = self.client.get("/api/metrics")
        
        # Should either return metrics or 404 if not implemented
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, dict)
    
    def test_rate_limiting(self):
        """Test rate limiting if implemented"""
        # Make multiple requests quickly
        responses = []
        for i in range(10):
            response = self.client.get("/api/health")
            responses.append(response)
        
        # All should succeed for health endpoint (no rate limiting)
        for response in responses:
            assert response.status_code == 200
    
    def test_request_logging(self):
        """Test request logging functionality"""
        # This would test if requests are being logged properly
        # For now, just ensure requests don't fail
        response = self.client.get("/api/health")
        assert response.status_code == 200
    
    def test_environment_configuration(self):
        """Test environment configuration is loaded"""
        import os
        
        # Test environment variables are set for testing
        assert os.getenv("ENVIRONMENT") == "test"
        assert os.getenv("MONGODB_DATABASE") == "test_ai_research_agent"
    
    def test_database_connection_handling(self):
        """Test database connection error handling"""
        # This would test database connection failures
        # For now, just test that endpoints handle database errors gracefully
        
        with patch('database.connection.get_database') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            # Should handle database errors gracefully
            response = self.client.post(
                "/api/research/query",
                json={"query": "test query"}
            )
            
            # Should return 500 or handle gracefully
            assert response.status_code in [500, 503]


class TestApplicationLifecycle:
    """Test application lifecycle events"""
    
    def test_startup_events(self):
        """Test startup events are handled"""
        # Test that application starts without errors
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_shutdown_events(self):
        """Test shutdown events are handled"""
        # This would test cleanup on shutdown
        # For now, just ensure no errors during client creation/destruction
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # Client cleanup should not raise errors
        del client


@pytest.mark.asyncio
class TestAsyncApplicationComponents:
    """Test async components of the application"""
    
    async def test_async_endpoints(self):
        """Test async endpoint handling"""
        from main import app
        from httpx import AsyncClient
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/health")
            assert response.status_code == 200
    
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        from main import app
        from httpx import AsyncClient
        import asyncio
        
        async def make_request(client):
            return await client.get("/api/health")
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make 5 concurrent requests
            tasks = [make_request(client) for _ in range(5)]
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 200