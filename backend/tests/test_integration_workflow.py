"""
Integration tests for complete research workflow
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from main import app
from models.research import ResearchQuery, ResearchResult
from services.research_orchestrator import ResearchOrchestrator


class TestResearchWorkflowIntegration:
    """Test complete research workflow from API to database"""
    
    def setup_method(self):
        """Setup test client and mocks"""
        self.client = TestClient(app)
        self.test_query = "artificial intelligence machine learning"
        self.test_query_id = "test-query-123"
    
    @patch('services.research_orchestrator.ResearchOrchestrator.conduct_research')
    @patch('services.cache_service.CacheService.get_cached_result')
    @patch('services.cache_service.CacheService.cache_result')
    def test_complete_research_workflow(self, mock_cache_result, mock_get_cached, mock_conduct_research):
        """Test complete research workflow from query submission to results"""
        
        # Setup mocks
        mock_get_cached.return_value = None  # No cached result
        mock_cache_result.return_value = True
        
        mock_research_result = {
            "query_id": self.test_query_id,
            "sources": {
                "google_scholar": [{
                    "title": "Deep Learning for NLP",
                    "authors": ["John Smith"],
                    "abstract": "A comprehensive study of deep learning.",
                    "citation_count": 150,
                    "url": "https://scholar.google.com/test",
                    "publication_year": 2023
                }],
                "google_books": [{
                    "title": "ML Guide",
                    "authors": ["Alice Johnson"],
                    "description": "Complete guide to ML.",
                    "isbn": "978-0123456789",
                    "preview_link": "https://books.google.com/test",
                    "published_date": "2023-01-01"
                }],
                "sciencedirect": [{
                    "title": "Neural Networks in CV",
                    "authors": ["Bob Wilson"],
                    "abstract": "Neural networks in computer vision.",
                    "doi": "10.1016/j.test.2023.01.001",
                    "journal": "AI Journal",
                    "publication_date": datetime.now(timezone.utc).isoformat()
                }]
            },
            "ai_summary": "Significant advances in AI and ML applications.",
            "confidence_score": 0.85,
            "cached": False
        }
        
        mock_conduct_research.return_value = mock_research_result
        
        # Step 1: Submit research query
        response = self.client.post(
            "/api/research/query",
            json={"query": self.test_query}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "query_id" in result
        query_id = result["query_id"]
        
        # Step 2: Get research results
        response = self.client.get(f"/api/research/results/{query_id}")
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify result structure
        assert result["query_id"] == query_id
        assert "sources" in result
        assert "google_scholar" in result["sources"]
        assert "google_books" in result["sources"]
        assert "sciencedirect" in result["sources"]
        assert "ai_summary" in result
        assert "confidence_score" in result
        
        # Verify mocks were called
        mock_conduct_research.assert_called_once()
        mock_get_cached.assert_called_once()
        mock_cache_result.assert_called_once()
    
    def test_research_query_validation(self):
        """Test research query validation"""
        
        # Test empty query
        response = self.client.post(
            "/api/research/query",
            json={"query": ""}
        )
        assert response.status_code == 422
        
        # Test missing query
        response = self.client.post(
            "/api/research/query",
            json={}
        )
        assert response.status_code == 422
        
        # Test query too long
        long_query = "a" * 1001
        response = self.client.post(
            "/api/research/query",
            json={"query": long_query}
        )
        assert response.status_code == 422
    
    @patch('services.research_orchestrator.ResearchOrchestrator.conduct_research')
    def test_research_error_handling(self, mock_conduct_research):
        """Test error handling in research workflow"""
        
        # Mock research failure
        mock_conduct_research.side_effect = Exception("External API failure")
        
        response = self.client.post(
            "/api/research/query",
            json={"query": self.test_query}
        )
        
        # Should still return 200 but with error information
        assert response.status_code == 500
        result = response.json()
        assert "error" in result
    
    @patch('services.cache_service.CacheService.get_cached_result')
    def test_cached_results_workflow(self, mock_get_cached):
        """Test workflow with cached results"""
        
        # Mock cached result
        cached_result = {
            "query_id": self.test_query_id,
            "sources": {"google_scholar": [], "google_books": [], "sciencedirect": []},
            "ai_summary": "Cached summary",
            "confidence_score": 0.8,
            "cached": True
        }
        mock_get_cached.return_value = cached_result
        
        response = self.client.post(
            "/api/research/query",
            json={"query": self.test_query}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Get results
        query_id = result["query_id"]
        response = self.client.get(f"/api/research/results/{query_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["cached"] is True
        assert result["ai_summary"] == "Cached summary"
    
    def test_research_history_workflow(self):
        """Test research history retrieval"""
        
        response = self.client.get("/api/research/history")
        
        # Should return 200 even if no history
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
    
    def test_research_status_workflow(self):
        """Test research status checking"""
        
        # Test non-existent query
        response = self.client.get("/api/research/status/non-existent-id")
        assert response.status_code == 404
    
    def test_health_check_workflow(self):
        """Test health check endpoint"""
        
        response = self.client.get("/api/health")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "healthy"
    
    @patch('services.research_orchestrator.ResearchOrchestrator.conduct_research')
    def test_partial_results_workflow(self, mock_conduct_research):
        """Test workflow with partial results (some sources fail)"""
        
        # Mock partial results (only Scholar succeeds)
        partial_result = {
            "query_id": self.test_query_id,
            "sources": {
                "google_scholar": [{
                    "title": "Test Paper",
                    "authors": ["Test Author"],
                    "abstract": "Test abstract",
                    "citation_count": 10,
                    "url": "https://test.com",
                    "publication_year": 2023
                }],
                "google_books": [],  # Failed
                "sciencedirect": []  # Failed
            },
            "ai_summary": "Limited results due to API failures.",
            "confidence_score": 0.5,
            "cached": False,
            "errors": {
                "google_books": "API rate limit exceeded",
                "sciencedirect": "Authentication failed"
            }
        }
        
        mock_conduct_research.return_value = partial_result
        
        response = self.client.post(
            "/api/research/query",
            json={"query": self.test_query}
        )
        
        assert response.status_code == 200
        result = response.json()
        query_id = result["query_id"]
        
        # Get results
        response = self.client.get(f"/api/research/results/{query_id}")
        assert response.status_code == 200
        result = response.json()
        
        # Should have partial results
        assert len(result["sources"]["google_scholar"]) == 1
        assert len(result["sources"]["google_books"]) == 0
        assert len(result["sources"]["sciencedirect"]) == 0
        assert "errors" in result
        assert result["confidence_score"] == 0.5


@pytest.mark.asyncio
class TestAsyncResearchWorkflow:
    """Test async research workflow components"""
    
    async def test_concurrent_api_calls(self):
        """Test that research orchestrator makes concurrent API calls"""
        
        with patch('services.google_scholar_service.GoogleScholarService.search') as mock_scholar, \
             patch('services.google_books_service.GoogleBooksService.search') as mock_books, \
             patch('services.sciencedirect_service.ScienceDirectService.search') as mock_science, \
             patch('services.agno_ai_service.AgnoAIService.synthesize_research_results') as mock_agno:
            
            # Setup async mocks
            mock_scholar.return_value = []
            mock_books.return_value = []
            mock_science.return_value = []
            mock_agno.return_value = {
                "synthesis": "Test synthesis",
                "confidence": 0.8
            }
            
            orchestrator = ResearchOrchestrator()
            
            # Measure execution time to ensure concurrency
            import time
            start_time = time.time()
            
            result = await orchestrator.conduct_research("test query")
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete quickly due to concurrency (mocked calls)
            assert execution_time < 1.0
            
            # Verify all services were called
            mock_scholar.assert_called_once()
            mock_books.assert_called_once()
            mock_science.assert_called_once()
            mock_agno.assert_called_once()
    
    async def test_error_resilience(self):
        """Test that workflow continues when some services fail"""
        
        with patch('services.google_scholar_service.GoogleScholarService.search') as mock_scholar, \
             patch('services.google_books_service.GoogleBooksService.search') as mock_books, \
             patch('services.sciencedirect_service.ScienceDirectService.search') as mock_science, \
             patch('services.agno_ai_service.AgnoAIService.synthesize_research_results') as mock_agno:
            
            # Make some services fail
            mock_scholar.return_value = [{"title": "Test Paper"}]
            mock_books.side_effect = Exception("Books API failed")
            mock_science.side_effect = Exception("ScienceDirect API failed")
            mock_agno.return_value = {
                "synthesis": "Limited synthesis",
                "confidence": 0.4
            }
            
            orchestrator = ResearchOrchestrator()
            result = await orchestrator.conduct_research("test query")
            
            # Should still return results from successful service
            assert "sources" in result
            assert len(result["sources"]["google_scholar"]) == 1
            assert len(result["sources"]["google_books"]) == 0
            assert len(result["sources"]["sciencedirect"]) == 0
            assert result["confidence_score"] < 0.5  # Lower confidence due to failures