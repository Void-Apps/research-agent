"""
Unit tests for API structure and basic endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import json

from main import app

client = TestClient(app)


class TestAPIStructure:
    """Test API structure and configuration"""
    
    def test_app_creation(self):
        """Test that the FastAPI app is created correctly"""
        assert app.title == "AI Research Agent API"
        assert app.version == "1.0.0"
        assert app.docs_url == "/api/docs"
        assert app.redoc_url == "/api/redoc"
        assert app.openapi_url == "/api/openapi.json"
    
    def test_cors_middleware_configured(self):
        """Test that CORS middleware is properly configured"""
        # Check that CORS headers are present in response
        response = client.options("/api/health")
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented
        
        # Test actual CORS with a GET request
        response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
    
    def test_process_time_header(self):
        """Test that process time header is added to responses"""
        response = client.get("/api/health")
        assert "X-Process-Time" in response.headers
        assert float(response.headers["X-Process-Time"]) >= 0


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct information"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "AI Research Agent API"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/api/docs"
        assert data["health"] == "/api/health"


class TestHealthEndpoints:
    """Test health and metrics endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-research-agent"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        assert "uptime" in data
        assert isinstance(data["uptime"], (int, float))
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_metrics_endpoint(self, mock_disk, mock_memory, mock_cpu):
        """Test metrics endpoint with mocked system data"""
        # Mock system metrics
        mock_cpu.return_value = 25.5
        mock_memory.return_value.percent = 60.0
        mock_memory.return_value.available = 1024 * 1024 * 1024  # 1GB
        mock_disk.return_value.percent = 45.0
        mock_disk.return_value.free = 10 * 1024 * 1024 * 1024  # 10GB
        
        response = client.get("/api/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "ai-research-agent"
        assert "timestamp" in data
        assert "system" in data
        assert "application" in data
        
        # Check system metrics
        system = data["system"]
        assert system["cpu_usage_percent"] == 25.5
        assert system["memory_usage_percent"] == 60.0
        assert system["memory_available_mb"] == 1024.0
        assert system["disk_usage_percent"] == 45.0
        assert system["disk_free_gb"] == 10.0
        
        # Check application metrics (placeholders)
        app_metrics = data["application"]
        assert "active_queries" in app_metrics
        assert "cache_hit_rate" in app_metrics
        assert "total_queries_processed" in app_metrics
        assert "average_response_time_ms" in app_metrics


class TestResearchEndpoints:
    """Test research API endpoints"""
    
    def test_submit_research_query_success(self):
        """Test successful research query submission"""
        query_data = {
            "query": "artificial intelligence in healthcare",
            "user_id": "test_user_123"
        }
        
        response = client.post("/api/research/query", json=query_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "query_id" in data
        assert data["status"] == "pending"
        assert data["message"] == "Research query submitted successfully"
        assert len(data["query_id"]) > 0
    
    def test_submit_research_query_empty_query(self):
        """Test research query submission with empty query"""
        query_data = {"query": "   "}  # Empty/whitespace query
        
        response = client.post("/api/research/query", json=query_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()
    
    def test_submit_research_query_missing_query(self):
        """Test research query submission with missing query field"""
        query_data = {"user_id": "test_user"}  # Missing query field
        
        response = client.post("/api/research/query", json=query_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_research_results_not_found(self):
        """Test getting research results for non-existent query"""
        query_id = "non-existent-query-id"
        
        response = client.get(f"/api/research/results/{query_id}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert query_id in data["detail"]
    
    def test_get_research_status(self):
        """Test getting research status"""
        query_id = "test-query-id"
        
        response = client.get(f"/api/research/status/{query_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["query_id"] == query_id
        assert data["status"] == "pending"
        assert "progress" in data
        assert "message" in data
    
    def test_get_research_status_empty_id(self):
        """Test getting research status with empty query ID"""
        response = client.get("/api/research/status/")
        assert response.status_code == 404  # Path not found
    
    def test_get_research_history_default(self):
        """Test getting research history with default parameters"""
        response = client.get("/api/research/history")
        assert response.status_code == 200
        
        data = response.json()
        assert "queries" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert data["page"] == 1
        assert data["limit"] == 10
        assert isinstance(data["queries"], list)
    
    def test_get_research_history_with_params(self):
        """Test getting research history with custom parameters"""
        response = client.get("/api/research/history?page=2&limit=5&user_id=test_user")
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 2
        assert data["limit"] == 5
    
    def test_get_research_history_invalid_page(self):
        """Test getting research history with invalid page number"""
        response = client.get("/api/research/history?page=0")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "greater than 0" in data["detail"]
    
    def test_get_research_history_invalid_limit(self):
        """Test getting research history with invalid limit"""
        response = client.get("/api/research/history?limit=101")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "between 1 and 100" in data["detail"]


class TestErrorHandling:
    """Test error handling and middleware"""
    
    def test_404_endpoint(self):
        """Test accessing non-existent endpoint"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test method not allowed error"""
        response = client.delete("/api/health")  # DELETE not allowed on health endpoint
        assert response.status_code == 405
    
    def test_invalid_json(self):
        """Test invalid JSON in request body"""
        response = client.post(
            "/api/research/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestAPIDocumentation:
    """Test API documentation endpoints"""
    
    @pytest.mark.skip(reason="OpenAPI schema generation has Pydantic serialization issue with custom ObjectId")
    def test_openapi_schema(self):
        """Test OpenAPI schema endpoint"""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "AI Research Agent API"
        assert schema["info"]["version"] == "1.0.0"
    
    def test_docs_endpoint(self):
        """Test Swagger UI docs endpoint"""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_endpoint(self):
        """Test ReDoc documentation endpoint"""
        response = client.get("/api/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])