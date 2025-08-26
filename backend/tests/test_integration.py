"""
Integration tests for the API
"""
import pytest
from fastapi.testclient import TestClient
import json

from main import app

client = TestClient(app)


class TestAPIIntegration:
    """Integration tests for the complete API"""
    
    def test_api_startup_and_basic_flow(self):
        """Test that the API starts up and basic endpoints work"""
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AI Research Agent API"
        
        # Test health endpoint
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Test metrics endpoint
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "system" in data
        assert "application" in data
    
    def test_research_api_flow(self):
        """Test the research API endpoints flow"""
        # Submit a research query
        query_data = {
            "query": "machine learning applications in healthcare",
            "user_id": "test_user"
        }
        
        response = client.post("/api/research/query", json=query_data)
        assert response.status_code == 201
        
        data = response.json()
        query_id = data["query_id"]
        assert data["status"] == "pending"
        
        # Check query status
        response = client.get(f"/api/research/status/{query_id}")
        assert response.status_code == 200
        
        status_data = response.json()
        assert status_data["query_id"] == query_id
        assert status_data["status"] == "pending"
        
        # Get research history
        response = client.get("/api/research/history")
        assert response.status_code == 200
        
        history_data = response.json()
        assert "queries" in history_data
        assert history_data["page"] == 1
        assert history_data["limit"] == 10
    
    def test_error_handling_integration(self):
        """Test error handling across the API"""
        # Test invalid research query
        response = client.post("/api/research/query", json={"query": ""})
        assert response.status_code == 400
        
        # Test non-existent query results
        response = client.get("/api/research/results/invalid-id")
        assert response.status_code == 404
        
        # Test invalid pagination
        response = client.get("/api/research/history?page=0")
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])