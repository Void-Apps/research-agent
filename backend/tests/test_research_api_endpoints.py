"""
Integration tests for research API endpoints
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from models.research import (
    ResearchQuery, ResearchResult, QueryStatus, SourceResult, SourceType
)


# Mock the main app for testing
@pytest.fixture
def mock_app():
    """Create a mock FastAPI app for testing"""
    from fastapi import FastAPI
    from routers.research import router
    
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(mock_app):
    """Create test client"""
    return TestClient(mock_app)


@pytest.fixture
async def async_client(mock_app):
    """Create async test client"""
    async with AsyncClient(app=mock_app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_collections():
    """Mock MongoDB collections"""
    queries_collection = AsyncMock()
    results_collection = AsyncMock()
    
    async def mock_get_queries_collection():
        return queries_collection
    
    async def mock_get_results_collection():
        return results_collection
    
    with patch('routers.research.get_queries_collection', side_effect=mock_get_queries_collection), \
         patch('routers.research.get_results_collection', side_effect=mock_get_results_collection):
        yield queries_collection, results_collection


class TestResearchAPIEndpoints:
    """Test suite for research API endpoints"""
    

@pytest.fixture
def sample_research_query():
    """Sample research query for testing"""
    return ResearchQuery(
        query_id="test-query-123",
        query_text="artificial intelligence machine learning",
        user_id="test-user",
        timestamp=datetime.utcnow(),
        status=QueryStatus.PENDING
    )


@pytest.fixture
def sample_research_result():
    """Sample research result for testing"""
    return ResearchResult(
        query_id="test-query-123",
        results={
            "google_scholar": [
                SourceResult(
                    title="AI Research Paper",
                    authors=["John Doe", "Jane Smith"],
                    abstract="This paper discusses AI advancements",
                    source_type=SourceType.GOOGLE_SCHOLAR,
                    citation_count=150
                )
            ],
            "google_books": [
                SourceResult(
                    title="Machine Learning Handbook",
                    authors=["Alice Johnson"],
                    abstract="Comprehensive guide to ML",
                    source_type=SourceType.GOOGLE_BOOKS,
                    isbn="978-1234567890"
                )
            ],
            "sciencedirect": [
                SourceResult(
                    title="Deep Learning Applications",
                    authors=["Bob Wilson"],
                    abstract="Applications of deep learning",
                    source_type=SourceType.SCIENCEDIRECT,
                    doi="10.1016/j.example.2023.01.001"
                )
            ]
        },
        ai_summary="This research covers various aspects of AI and ML",
        confidence_score=0.85,
        cached=False,
        created_at=datetime.utcnow()
    )


class TestSubmitResearchQuery:
    """Test POST /api/research/query endpoint"""
    
    def test_submit_valid_query(self, client, mock_collections):
        """Test submitting a valid research query"""
        queries_collection, _ = mock_collections
        
        # Mock orchestrator response
        with patch('routers.research.research_orchestrator') as mock_orchestrator:
            mock_query = ResearchQuery(
                query_id="test-123",
                query_text="test query",
                status=QueryStatus.PENDING,
                timestamp=datetime.utcnow()
            )
            mock_orchestrator.submit_research_query.return_value = mock_query
            queries_collection.insert_one.return_value = AsyncMock()
            
            response = client.post(
                "/api/research/query",
                json={"query": "artificial intelligence", "user_id": "test-user"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "query_id" in data
            assert data["status"] == "pending"
            assert "message" in data
    
    def test_submit_empty_query(self, client, mock_collections):
        """Test submitting empty query returns 400"""
        response = client.post(
            "/api/research/query",
            json={"query": "", "user_id": "test-user"}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_submit_query_too_long(self, client, mock_collections):
        """Test submitting query that's too long returns 400"""
        long_query = "a" * 1001  # Exceeds 1000 character limit
        
        response = client.post(
            "/api/research/query",
            json={"query": long_query, "user_id": "test-user"}
        )
        
        assert response.status_code == 400
        assert "too long" in response.json()["detail"].lower()
    
    def test_submit_query_without_user_id(self, client, mock_collections):
        """Test submitting query without user_id is allowed"""
        queries_collection, _ = mock_collections
        
        with patch('routers.research.research_orchestrator') as mock_orchestrator:
            mock_query = ResearchQuery(
                query_id="test-123",
                query_text="test query",
                status=QueryStatus.PENDING,
                timestamp=datetime.utcnow()
            )
            mock_orchestrator.submit_research_query.return_value = mock_query
            queries_collection.insert_one.return_value = AsyncMock()
            
            response = client.post(
                "/api/research/query",
                json={"query": "artificial intelligence"}
            )
            
            assert response.status_code == 201
    
    def test_submit_query_orchestrator_error(self, client, mock_collections):
        """Test handling orchestrator errors"""
        with patch('routers.research.research_orchestrator') as mock_orchestrator:
            mock_orchestrator.submit_research_query.side_effect = ValueError("Invalid query")
            
            response = client.post(
                "/api/research/query",
                json={"query": "test query"}
            )
            
            assert response.status_code == 400
            assert "Invalid query" in response.json()["detail"]


class TestGetResearchResults:
    """Test GET /api/research/results/{query_id} endpoint"""
    
    def test_get_results_completed_query(self, client, mock_collections, sample_research_query, sample_research_result):
        """Test getting results for completed query"""
        queries_collection, results_collection = mock_collections
        
        # Mock completed query
        completed_query = sample_research_query.model_copy()
        completed_query.status = QueryStatus.COMPLETED
        queries_collection.find_one.return_value = completed_query.model_dump(by_alias=True)
        
        # Mock result
        results_collection.find_one.return_value = sample_research_result.model_dump(by_alias=True)
        
        response = client.get("/api/research/results/test-query-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == "test-query-123"
        assert data["status"] == "completed"
        assert "results" in data
        assert "ai_summary" in data
        assert data["confidence_score"] == 0.85
    
    def test_get_results_processing_query(self, client, mock_collections, sample_research_query):
        """Test getting results for processing query"""
        queries_collection, _ = mock_collections
        
        # Mock processing query
        processing_query = sample_research_query.model_copy()
        processing_query.status = QueryStatus.PROCESSING
        queries_collection.find_one.return_value = processing_query.model_dump(by_alias=True)
        
        response = client.get("/api/research/results/test-query-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == "test-query-123"
        assert data["status"] == "processing"
        assert data["results"] is None
    
    def test_get_results_failed_query(self, client, mock_collections, sample_research_query):
        """Test getting results for failed query"""
        queries_collection, _ = mock_collections
        
        # Mock failed query
        failed_query = sample_research_query.model_copy()
        failed_query.status = QueryStatus.FAILED
        queries_collection.find_one.return_value = failed_query.model_dump(by_alias=True)
        
        response = client.get("/api/research/results/test-query-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == "test-query-123"
        assert data["status"] == "failed"
        assert data["results"] is None
        assert "failed" in data["ai_summary"].lower()
    
    def test_get_results_nonexistent_query(self, client, mock_collections):
        """Test getting results for non-existent query"""
        queries_collection, _ = mock_collections
        queries_collection.find_one.return_value = None
        
        response = client.get("/api/research/results/nonexistent-query")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_results_empty_query_id(self, client, mock_collections):
        """Test getting results with empty query ID"""
        response = client.get("/api/research/results/")
        
        # This should return 404 due to path not matching
        assert response.status_code == 404
    
    def test_get_results_completed_but_no_results(self, client, mock_collections, sample_research_query):
        """Test getting results for completed query but no results in database"""
        queries_collection, results_collection = mock_collections
        
        # Mock completed query
        completed_query = sample_research_query.model_copy()
        completed_query.status = QueryStatus.COMPLETED
        queries_collection.find_one.return_value = completed_query.model_dump(by_alias=True)
        
        # Mock no results found
        results_collection.find_one.return_value = None
        
        response = client.get("/api/research/results/test-query-123")
        
        assert response.status_code == 500
        assert "not found for completed query" in response.json()["detail"]


class TestGetResearchStatus:
    """Test GET /api/research/status/{query_id} endpoint"""
    
    def test_get_status_pending_query(self, client, mock_collections, sample_research_query):
        """Test getting status for pending query"""
        queries_collection, _ = mock_collections
        queries_collection.find_one.return_value = sample_research_query.model_dump(by_alias=True)
        
        response = client.get("/api/research/status/test-query-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == "test-query-123"
        assert data["status"] == "pending"
        assert data["progress"] == 0.0
        assert "queue" in data["message"].lower()
        assert "created_at" in data
    
    def test_get_status_processing_query(self, client, mock_collections, sample_research_query):
        """Test getting status for processing query"""
        queries_collection, _ = mock_collections
        
        processing_query = sample_research_query.model_copy()
        processing_query.status = QueryStatus.PROCESSING
        queries_collection.find_one.return_value = processing_query.model_dump(by_alias=True)
        
        response = client.get("/api/research/status/test-query-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["progress"] == 0.5
        assert "progress" in data["message"].lower()
    
    def test_get_status_completed_query(self, client, mock_collections, sample_research_query):
        """Test getting status for completed query"""
        queries_collection, _ = mock_collections
        
        completed_query = sample_research_query.model_copy()
        completed_query.status = QueryStatus.COMPLETED
        queries_collection.find_one.return_value = completed_query.model_dump(by_alias=True)
        
        response = client.get("/api/research/status/test-query-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 1.0
        assert "completed" in data["message"].lower()
    
    def test_get_status_failed_query(self, client, mock_collections, sample_research_query):
        """Test getting status for failed query"""
        queries_collection, _ = mock_collections
        
        failed_query = sample_research_query.model_copy()
        failed_query.status = QueryStatus.FAILED
        queries_collection.find_one.return_value = failed_query.model_dump(by_alias=True)
        
        response = client.get("/api/research/status/test-query-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["progress"] == 0.0
        assert "failed" in data["message"].lower()
    
    def test_get_status_nonexistent_query(self, client, mock_collections):
        """Test getting status for non-existent query"""
        queries_collection, _ = mock_collections
        queries_collection.find_one.return_value = None
        
        response = client.get("/api/research/status/nonexistent-query")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_status_empty_query_id(self, client, mock_collections):
        """Test getting status with empty query ID"""
        response = client.get("/api/research/status/")
        
        # This should return 404 due to path not matching
        assert response.status_code == 404


class TestGetResearchHistory:
    """Test GET /api/research/history endpoint"""
    
    def test_get_history_default_params(self, client, mock_collections):
        """Test getting history with default parameters"""
        queries_collection, _ = mock_collections
        
        # Mock database responses
        queries_collection.count_documents.return_value = 5
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [
            {
                "query_id": "query-1",
                "query_text": "AI research",
                "user_id": "user-1",
                "timestamp": datetime.utcnow(),
                "status": "completed"
            },
            {
                "query_id": "query-2", 
                "query_text": "ML algorithms",
                "user_id": "user-1",
                "timestamp": datetime.utcnow(),
                "status": "pending"
            }
        ]
        queries_collection.find.return_value = mock_cursor
        
        response = client.get("/api/research/history")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["limit"] == 10
        assert len(data["queries"]) == 2
        assert data["queries"][0]["query_id"] == "query-1"
    
    def test_get_history_with_user_id(self, client, mock_collections):
        """Test getting history filtered by user ID"""
        queries_collection, _ = mock_collections
        
        queries_collection.count_documents.return_value = 3
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [
            {
                "query_id": "query-1",
                "query_text": "AI research",
                "user_id": "specific-user",
                "timestamp": datetime.utcnow(),
                "status": "completed"
            }
        ]
        queries_collection.find.return_value = mock_cursor
        
        response = client.get("/api/research/history?user_id=specific-user")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["queries"][0]["user_id"] == "specific-user"
    
    def test_get_history_with_pagination(self, client, mock_collections):
        """Test getting history with custom pagination"""
        queries_collection, _ = mock_collections
        
        queries_collection.count_documents.return_value = 25
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = []
        queries_collection.find.return_value = mock_cursor
        
        response = client.get("/api/research/history?page=2&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["limit"] == 5
        assert data["total"] == 25
    
    def test_get_history_invalid_page(self, client, mock_collections):
        """Test getting history with invalid page number"""
        response = client.get("/api/research/history?page=0")
        
        assert response.status_code == 400
        assert "greater than 0" in response.json()["detail"]
    
    def test_get_history_invalid_limit(self, client, mock_collections):
        """Test getting history with invalid limit"""
        response = client.get("/api/research/history?limit=101")
        
        assert response.status_code == 400
        assert "between 1 and 100" in response.json()["detail"]
    
    def test_get_history_empty_results(self, client, mock_collections):
        """Test getting history with no results"""
        queries_collection, _ = mock_collections
        
        queries_collection.count_documents.return_value = 0
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = []
        queries_collection.find.return_value = mock_cursor
        
        response = client.get("/api/research/history")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["queries"]) == 0


class TestCancelResearchQuery:
    """Test DELETE /api/research/query/{query_id} endpoint"""
    
    def test_cancel_pending_query(self, client, mock_collections, sample_research_query):
        """Test cancelling a pending query"""
        queries_collection, _ = mock_collections
        
        queries_collection.find_one.return_value = sample_research_query.model_dump(by_alias=True)
        queries_collection.update_one.return_value = AsyncMock()
        
        with patch('routers.research.research_orchestrator') as mock_orchestrator:
            mock_orchestrator.cancel_query.return_value = True
            response = client.delete("/api/research/query/test-query-123")
            
            assert response.status_code == 200
            assert "cancelled successfully" in response.json()["message"]
    
    def test_cancel_processing_query(self, client, mock_collections, sample_research_query):
        """Test cancelling a processing query"""
        queries_collection, _ = mock_collections
        
        processing_query = sample_research_query.model_copy()
        processing_query.status = QueryStatus.PROCESSING
        queries_collection.find_one.return_value = processing_query.model_dump(by_alias=True)
        queries_collection.update_one.return_value = AsyncMock()
        
        with patch('routers.research.research_orchestrator') as mock_orchestrator:
            mock_orchestrator.cancel_query.return_value = True
            response = client.delete("/api/research/query/test-query-123")
            
            assert response.status_code == 200
    
    def test_cancel_completed_query(self, client, mock_collections, sample_research_query):
        """Test cancelling a completed query (should fail)"""
        queries_collection, _ = mock_collections
        
        completed_query = sample_research_query.model_copy()
        completed_query.status = QueryStatus.COMPLETED
        queries_collection.find_one.return_value = completed_query.model_dump(by_alias=True)
        
        response = client.delete("/api/research/query/test-query-123")
        
        assert response.status_code == 400
        assert "Cannot cancel" in response.json()["detail"]
    
    def test_cancel_nonexistent_query(self, client, mock_collections):
        """Test cancelling non-existent query"""
        queries_collection, _ = mock_collections
        queries_collection.find_one.return_value = None
        
        response = client.delete("/api/research/query/nonexistent-query")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_cancel_query_orchestrator_fails(self, client, mock_collections, sample_research_query):
        """Test cancelling query when orchestrator fails"""
        queries_collection, _ = mock_collections
        
        queries_collection.find_one.return_value = sample_research_query.model_dump(by_alias=True)
        
        with patch('routers.research.research_orchestrator') as mock_orchestrator:
            mock_orchestrator.cancel_query.return_value = False
            response = client.delete("/api/research/query/test-query-123")
            
            assert response.status_code == 500
            assert "Failed to cancel" in response.json()["detail"]


class TestHealthAndStatistics:
    """Test health and statistics endpoints"""
    
    def test_get_health(self, client):
        """Test getting service health"""
        mock_health = {
            "orchestrator": {"status": "healthy"},
            "google_scholar": {"status": "healthy"},
            "google_books": {"status": "healthy"},
            "sciencedirect": {"status": "healthy"},
            "cache": {"status": "healthy"}
        }
        
        with patch('routers.research.research_orchestrator') as mock_orchestrator, \
             patch('routers.research.get_collection') as mock_get_collection:
            
            mock_orchestrator.get_service_health.return_value = mock_health
            
            mock_collection = AsyncMock()
            mock_collection.find_one.return_value = {"_id": "test"}
            mock_get_collection.return_value = mock_collection
            
            response = client.get("/api/research/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["orchestrator"]["status"] == "healthy"
            assert data["database"]["status"] == "healthy"
    
    def test_get_statistics(self, client):
        """Test getting research statistics"""
        mock_stats = {
            "cache_statistics": {"total_entries": 10},
            "active_queries": 2
        }
        
        with patch('routers.research.research_orchestrator') as mock_orchestrator, \
             patch('routers.research.get_collection') as mock_get_collection:
            
            mock_orchestrator.get_research_statistics.return_value = mock_stats
            
            mock_queries_collection = AsyncMock()
            mock_results_collection = AsyncMock()
            
            # Mock status counts
            mock_queries_collection.count_documents.side_effect = [5, 3, 2, 1]  # pending, processing, completed, failed
            mock_results_collection.count_documents.return_value = 15
            
            mock_get_collection.side_effect = [mock_queries_collection, mock_results_collection]
            
            response = client.get("/api/research/statistics")
            
            assert response.status_code == 200
            data = response.json()
            assert "cache_statistics" in data
            assert "database_statistics" in data
            assert data["database_statistics"]["total_results"] == 15


class TestBackgroundProcessing:
    """Test background processing functionality"""
    
    @pytest.mark.asyncio
    async def test_process_research_query_background_success(self, mock_collections, sample_research_result):
        """Test successful background processing"""
        from routers.research import process_research_query_background
        
        queries_collection, results_collection = mock_collections
        
        with patch('routers.research.research_orchestrator') as mock_orchestrator, \
             patch('routers.research.get_collection') as mock_get_collection:
            
            mock_orchestrator.process_research_query.return_value = sample_research_result
            
            mock_get_collection.side_effect = [results_collection, queries_collection]
            results_collection.insert_one.return_value = AsyncMock()
            queries_collection.update_one.return_value = AsyncMock()
            
            # Should not raise any exceptions
            await process_research_query_background("test-query-123")
            
            # Verify database operations were called
            results_collection.insert_one.assert_called_once()
            queries_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_research_query_background_failure(self, mock_collections):
        """Test background processing failure handling"""
        from routers.research import process_research_query_background
        
        queries_collection, _ = mock_collections
        
        with patch('routers.research.research_orchestrator') as mock_orchestrator, \
             patch('routers.research.get_collection', return_value=queries_collection):
            
            mock_orchestrator.process_research_query.side_effect = Exception("Processing failed")
            
            queries_collection.update_one.return_value = AsyncMock()
            
            # Should not raise exception (error handling)
            await process_research_query_background("test-query-123")
            
            # Verify status was updated to failed
            queries_collection.update_one.assert_called_once()
            call_args = queries_collection.update_one.call_args
            assert call_args[0][1]["$set"]["status"] == QueryStatus.FAILED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])