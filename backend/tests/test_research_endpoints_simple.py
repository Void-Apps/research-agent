"""
Simple integration tests for research API endpoints
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from models.research import ResearchQuery, QueryStatus


def create_test_app():
    """Create a test FastAPI app with mocked dependencies"""
    app = FastAPI()
    
    # Mock collections
    mock_queries_collection = AsyncMock()
    mock_results_collection = AsyncMock()
    
    # Mock orchestrator
    mock_orchestrator = AsyncMock()
    
    # Override dependencies
    async def mock_get_queries_collection():
        return mock_queries_collection
    
    async def mock_get_results_collection():
        return mock_results_collection
    
    # Import and patch the router
    with patch('routers.research.get_queries_collection', side_effect=mock_get_queries_collection), \
         patch('routers.research.get_results_collection', side_effect=mock_get_results_collection), \
         patch('routers.research.research_orchestrator', mock_orchestrator):
        
        from routers.research import router
        app.include_router(router)
        
        # Store mocks for test access
        app.state.mock_queries_collection = mock_queries_collection
        app.state.mock_results_collection = mock_results_collection
        app.state.mock_orchestrator = mock_orchestrator
    
    return app


class TestResearchEndpoints:
    """Test research API endpoints"""
    
    def test_submit_empty_query_returns_400(self):
        """Test that submitting an empty query returns 400"""
        app = create_test_app()
        client = TestClient(app)
        
        response = client.post(
            "/api/research/query",
            json={"query": "", "user_id": "test-user"}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_submit_valid_query_returns_201(self):
        """Test that submitting a valid query returns 201"""
        app = create_test_app()
        client = TestClient(app)
        
        # Mock the orchestrator response
        mock_query = ResearchQuery(
            query_id="test-123",
            query_text="artificial intelligence",
            status=QueryStatus.PENDING,
            timestamp=datetime.utcnow()
        )
        app.state.mock_orchestrator.submit_research_query.return_value = mock_query
        app.state.mock_queries_collection.insert_one.return_value = AsyncMock()
        
        response = client.post(
            "/api/research/query",
            json={"query": "artificial intelligence", "user_id": "test-user"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "query_id" in data
        assert data["status"] == "pending"
        assert "message" in data
    
    def test_submit_query_too_long_returns_400(self):
        """Test that submitting a query that's too long returns 400"""
        app = create_test_app()
        client = TestClient(app)
        
        long_query = "a" * 1001  # Exceeds 1000 character limit
        
        response = client.post(
            "/api/research/query",
            json={"query": long_query, "user_id": "test-user"}
        )
        
        assert response.status_code == 400
        assert "too long" in response.json()["detail"].lower()
    
    def test_get_results_nonexistent_query_returns_404(self):
        """Test getting results for non-existent query returns 404"""
        app = create_test_app()
        client = TestClient(app)
        
        app.state.mock_queries_collection.find_one.return_value = None
        
        response = client.get("/api/research/results/nonexistent-query")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_status_nonexistent_query_returns_404(self):
        """Test getting status for non-existent query returns 404"""
        app = create_test_app()
        client = TestClient(app)
        
        app.state.mock_queries_collection.find_one.return_value = None
        
        response = client.get("/api/research/status/nonexistent-query")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_history_with_invalid_page_returns_400(self):
        """Test getting history with invalid page returns 400"""
        app = create_test_app()
        client = TestClient(app)
        
        response = client.get("/api/research/history?page=0")
        
        assert response.status_code == 400
        assert "greater than 0" in response.json()["detail"]
    
    def test_get_history_with_invalid_limit_returns_400(self):
        """Test getting history with invalid limit returns 400"""
        app = create_test_app()
        client = TestClient(app)
        
        response = client.get("/api/research/history?limit=101")
        
        assert response.status_code == 400
        assert "between 1 and 100" in response.json()["detail"]
    
    def test_health_endpoint_returns_200(self):
        """Test that health endpoint returns 200"""
        app = create_test_app()
        client = TestClient(app)
        
        # Mock health response
        mock_health = {
            "orchestrator": {"status": "healthy"},
            "google_scholar": {"status": "healthy"},
            "google_books": {"status": "healthy"},
            "sciencedirect": {"status": "healthy"},
            "cache": {"status": "healthy"}
        }
        app.state.mock_orchestrator.get_service_health.return_value = mock_health
        
        # Mock database health check
        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = {"_id": "test"}
        
        with patch('routers.research.get_collection', return_value=mock_collection):
            response = client.get("/api/research/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "orchestrator" in data
        assert data["orchestrator"]["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])