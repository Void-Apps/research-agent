"""
Unit tests for research orchestrator service
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from services.research_orchestrator import ResearchOrchestrator
from services.google_scholar_service import GoogleScholarService
from services.google_books_service import GoogleBooksService
from services.sciencedirect_service import ScienceDirectService
from services.agno_ai_service import AgnoAIService, ResearchSynthesis
from services.cache_service import CacheService
from models.research import (
    ResearchQuery, ResearchResult, SourceResult, QueryStatus, SourceType
)

class TestResearchOrchestrator:
    """Test cases for ResearchOrchestrator"""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing"""
        mock_scholar = AsyncMock(spec=GoogleScholarService)
        mock_scholar.max_results = 20
        
        mock_books = AsyncMock(spec=GoogleBooksService)
        mock_books.max_results = 20
        
        mock_sciencedirect = AsyncMock(spec=ScienceDirectService)
        mock_sciencedirect.max_results = 20
        
        mock_agno = AsyncMock(spec=AgnoAIService)
        mock_cache = AsyncMock(spec=CacheService)
        
        return {
            'scholar': mock_scholar,
            'books': mock_books,
            'sciencedirect': mock_sciencedirect,
            'agno': mock_agno,
            'cache': mock_cache
        }
    
    @pytest.fixture
    def orchestrator(self, mock_services):
        """Create orchestrator with mock services"""
        return ResearchOrchestrator(
            google_scholar_service=mock_services['scholar'],
            google_books_service=mock_services['books'],
            sciencedirect_service=mock_services['sciencedirect'],
            agno_ai_service=mock_services['agno'],
            cache_service=mock_services['cache'],
            timeout_seconds=30
        )
    
    @pytest.fixture
    def sample_source_results(self):
        """Create sample source results for testing"""
        return {
            'google_scholar': [
                SourceResult(
                    title="Test Paper 1",
                    authors=["Author 1", "Author 2"],
                    abstract="Test abstract 1",
                    source_type=SourceType.GOOGLE_SCHOLAR,
                    citation_count=10
                ),
                SourceResult(
                    title="Test Paper 2",
                    authors=["Author 3"],
                    abstract="Test abstract 2",
                    source_type=SourceType.GOOGLE_SCHOLAR,
                    citation_count=5
                )
            ],
            'google_books': [
                SourceResult(
                    title="Test Book 1",
                    authors=["Book Author 1"],
                    abstract="Test book description",
                    source_type=SourceType.GOOGLE_BOOKS,
                    isbn="1234567890"
                )
            ],
            'sciencedirect': [
                SourceResult(
                    title="Test Scientific Paper",
                    authors=["Scientist 1", "Scientist 2"],
                    abstract="Scientific abstract",
                    source_type=SourceType.SCIENCEDIRECT,
                    doi="10.1000/test.doi"
                )
            ]
        }
    
    @pytest.mark.asyncio
    async def test_submit_research_query_success(self, orchestrator):
        """Test successful research query submission"""
        query_text = "machine learning algorithms"
        user_id = "test_user"
        
        query = await orchestrator.submit_research_query(query_text, user_id)
        
        assert isinstance(query, ResearchQuery)
        assert query.query_text == query_text
        assert query.user_id == user_id
        assert query.status == QueryStatus.PENDING
        assert query.query_id is not None
        assert query.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_submit_research_query_empty_text(self, orchestrator):
        """Test research query submission with empty text"""
        with pytest.raises(ValueError, match="Query text cannot be empty"):
            await orchestrator.submit_research_query("")
        
        with pytest.raises(ValueError, match="Query text cannot be empty"):
            await orchestrator.submit_research_query("   ")
    
    @pytest.mark.asyncio
    async def test_process_research_query_with_cache_hit(self, orchestrator, mock_services):
        """Test processing query with cache hit"""
        query_text = "test query"
        
        # Submit query
        query = await orchestrator.submit_research_query(query_text)
        
        # Mock cache hit
        cached_result = ResearchResult(
            query_id=query.query_id,
            results={"google_scholar": []},
            cached=True,
            created_at=datetime.utcnow()
        )
        mock_services['cache'].get_cached_result.return_value = cached_result
        
        # Process query
        result = await orchestrator.process_research_query(query.query_id)
        
        assert result == cached_result
        assert result.cached is True
        mock_services['cache'].get_cached_result.assert_called_once_with(query_text)
        
        # Verify other services were not called
        mock_services['scholar'].search_papers.assert_not_called()
        mock_services['books'].search_books.assert_not_called()
        mock_services['sciencedirect'].search_papers.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_research_query_cache_miss(self, orchestrator, mock_services, sample_source_results):
        """Test processing query with cache miss"""
        query_text = "test query"
        
        # Submit query
        query = await orchestrator.submit_research_query(query_text)
        
        # Mock cache miss
        mock_services['cache'].get_cached_result.return_value = None
        
        # Mock service responses
        mock_services['scholar'].search_papers.return_value = sample_source_results['google_scholar']
        mock_services['books'].search_books.return_value = sample_source_results['google_books']
        mock_services['sciencedirect'].search_papers.return_value = sample_source_results['sciencedirect']
        
        # Mock AI synthesis
        synthesis = ResearchSynthesis(
            summary="Test synthesis summary",
            key_insights=["Insight 1", "Insight 2"],
            confidence_score=0.8
        )
        mock_services['agno'].synthesize_research_results.return_value = synthesis
        
        # Mock cache storage
        mock_services['cache'].store_result.return_value = True
        
        # Process query
        result = await orchestrator.process_research_query(query.query_id)
        
        assert isinstance(result, ResearchResult)
        assert result.query_id == query.query_id
        assert result.cached is False
        assert result.ai_summary == synthesis.summary
        assert result.confidence_score == synthesis.confidence_score
        assert len(result.results) == 3
        
        # Verify all services were called
        mock_services['scholar'].search_papers.assert_called_once_with(query_text)
        mock_services['books'].search_books.assert_called_once_with(query_text)
        mock_services['sciencedirect'].search_papers.assert_called_once_with(query_text)
        mock_services['agno'].synthesize_research_results.assert_called_once()
        mock_services['cache'].store_result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_research_query_partial_failure(self, orchestrator, mock_services, sample_source_results):
        """Test processing query with partial service failures"""
        query_text = "test query"
        
        # Submit query
        query = await orchestrator.submit_research_query(query_text)
        
        # Mock cache miss
        mock_services['cache'].get_cached_result.return_value = None
        
        # Mock service responses - one success, one failure, one empty
        mock_services['scholar'].search_papers.return_value = sample_source_results['google_scholar']
        mock_services['books'].search_books.side_effect = Exception("Books API error")
        mock_services['sciencedirect'].search_papers.return_value = []
        
        # Mock AI synthesis
        synthesis = ResearchSynthesis(
            summary="Partial results synthesis",
            key_insights=["Insight from available sources"],
            confidence_score=0.6
        )
        mock_services['agno'].synthesize_research_results.return_value = synthesis
        
        # Mock cache storage
        mock_services['cache'].store_result.return_value = True
        
        # Process query
        result = await orchestrator.process_research_query(query.query_id)
        
        assert isinstance(result, ResearchResult)
        assert result.query_id == query.query_id
        assert len(result.results) == 3  # All sources present, even if empty
        assert len(result.results['google_scholar']) == 2
        assert len(result.results['google_books']) == 0  # Failed service
        assert len(result.results['sciencedirect']) == 0  # Empty results
    
    @pytest.mark.asyncio
    async def test_process_research_query_invalid_id(self, orchestrator):
        """Test processing query with invalid ID"""
        with pytest.raises(ValueError, match="Query ID not found"):
            await orchestrator.process_research_query("invalid_id")
    
    @pytest.mark.asyncio
    async def test_coordinate_research_sources_all_success(self, orchestrator, mock_services, sample_source_results):
        """Test coordinating research sources with all successful"""
        query = "test query"
        
        # Mock service responses
        mock_services['scholar'].search_papers.return_value = sample_source_results['google_scholar']
        mock_services['books'].search_books.return_value = sample_source_results['google_books']
        mock_services['sciencedirect'].search_papers.return_value = sample_source_results['sciencedirect']
        
        # Call coordination method
        results = await orchestrator._coordinate_research_sources(query)
        
        assert len(results) == 3
        assert 'google_scholar' in results
        assert 'google_books' in results
        assert 'sciencedirect' in results
        assert len(results['google_scholar']) == 2
        assert len(results['google_books']) == 1
        assert len(results['sciencedirect']) == 1
    
    @pytest.mark.asyncio
    async def test_coordinate_research_sources_with_failures(self, orchestrator, mock_services, sample_source_results):
        """Test coordinating research sources with some failures"""
        query = "test query"
        
        # Mock service responses with failures
        mock_services['scholar'].search_papers.return_value = sample_source_results['google_scholar']
        mock_services['books'].search_books.side_effect = Exception("API Error")
        mock_services['sciencedirect'].search_papers.side_effect = asyncio.TimeoutError()
        
        # Call coordination method
        results = await orchestrator._coordinate_research_sources(query)
        
        assert len(results) == 3
        assert len(results['google_scholar']) == 2  # Success
        assert len(results['google_books']) == 0    # Failed
        assert len(results['sciencedirect']) == 0   # Failed
    
    @pytest.mark.asyncio
    async def test_coordinate_research_sources_timeout(self, orchestrator, mock_services):
        """Test coordinating research sources with timeout"""
        query = "test query"
        
        # Mock services to take too long
        async def slow_response():
            await asyncio.sleep(100)  # Longer than timeout
            return []
        
        mock_services['scholar'].search_papers.side_effect = slow_response
        mock_services['books'].search_books.side_effect = slow_response
        mock_services['sciencedirect'].search_papers.side_effect = slow_response
        
        # Set short timeout for test
        orchestrator.timeout_seconds = 0.1
        
        # Call coordination method
        results = await orchestrator._coordinate_research_sources(query)
        
        # Should return empty results for all sources due to timeout
        assert len(results) == 3
        assert all(len(source_results) == 0 for source_results in results.values())
    
    @pytest.mark.asyncio
    async def test_process_with_ai_success(self, orchestrator, mock_services, sample_source_results):
        """Test AI processing with successful synthesis"""
        query = "test query"
        
        synthesis = ResearchSynthesis(
            summary="AI generated summary",
            key_insights=["Key insight 1", "Key insight 2"],
            confidence_score=0.9
        )
        mock_services['agno'].synthesize_research_results.return_value = synthesis
        
        summary, confidence = await orchestrator._process_with_ai(query, sample_source_results)
        
        assert summary == synthesis.summary
        assert confidence == synthesis.confidence_score
        mock_services['agno'].synthesize_research_results.assert_called_once_with(query, sample_source_results)
    
    @pytest.mark.asyncio
    async def test_process_with_ai_no_results(self, orchestrator, mock_services):
        """Test AI processing with no results"""
        query = "test query"
        empty_results = {'google_scholar': [], 'google_books': [], 'sciencedirect': []}
        
        summary, confidence = await orchestrator._process_with_ai(query, empty_results)
        
        assert summary is None
        assert confidence is None
        mock_services['agno'].synthesize_research_results.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_with_ai_failure(self, orchestrator, mock_services, sample_source_results):
        """Test AI processing with failure fallback"""
        query = "test query"
        
        mock_services['agno'].synthesize_research_results.side_effect = Exception("AI Error")
        
        summary, confidence = await orchestrator._process_with_ai(query, sample_source_results)
        
        assert "Research completed for" in summary
        assert confidence == 0.6  # Fallback confidence
    
    @pytest.mark.asyncio
    async def test_get_query_status(self, orchestrator):
        """Test getting query status"""
        query_text = "test query"
        
        # Submit query
        query = await orchestrator.submit_research_query(query_text)
        
        # Check status
        status = await orchestrator.get_query_status(query.query_id)
        assert status == QueryStatus.PENDING
        
        # Check non-existent query
        status = await orchestrator.get_query_status("invalid_id")
        assert status is None
    
    @pytest.mark.asyncio
    async def test_cancel_query(self, orchestrator):
        """Test cancelling a query"""
        query_text = "test query"
        
        # Submit query
        query = await orchestrator.submit_research_query(query_text)
        
        # Cancel query
        result = await orchestrator.cancel_query(query.query_id)
        assert result is True
        
        # Check status
        status = await orchestrator.get_query_status(query.query_id)
        assert status is None  # Query removed from active queries
        
        # Try to cancel non-existent query
        result = await orchestrator.cancel_query("invalid_id")
        assert result is False
    
    def test_get_active_queries(self, orchestrator):
        """Test getting active queries"""
        # Initially no active queries
        active = orchestrator.get_active_queries()
        assert len(active) == 0
        
        # Add some queries manually for testing
        query1 = ResearchQuery(
            query_id="test1",
            query_text="query 1",
            status=QueryStatus.PENDING
        )
        query2 = ResearchQuery(
            query_id="test2",
            query_text="query 2",
            status=QueryStatus.PROCESSING
        )
        
        orchestrator._active_queries["test1"] = query1
        orchestrator._active_queries["test2"] = query2
        
        active = orchestrator.get_active_queries()
        assert len(active) == 2
        assert query1 in active
        assert query2 in active
    
    @pytest.mark.asyncio
    async def test_get_service_health(self, orchestrator, mock_services):
        """Test getting service health status"""
        # Mock service status responses
        mock_services['scholar'].get_service_status.return_value = {"status": "active"}
        mock_services['books'].get_service_status.return_value = {"status": "active"}
        mock_services['sciencedirect'].get_service_status.return_value = {"status": "active"}
        mock_services['cache'].get_cache_stats.return_value = {"total_entries": 10}
        
        health = await orchestrator.get_service_health()
        
        assert "orchestrator" in health
        assert "google_scholar" in health
        assert "google_books" in health
        assert "sciencedirect" in health
        assert "cache" in health
        
        assert health["orchestrator"]["status"] == "healthy"
        assert health["google_scholar"]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_get_service_health_with_errors(self, orchestrator, mock_services):
        """Test getting service health with some services failing"""
        # Mock some services to fail
        mock_services['scholar'].get_service_status.side_effect = Exception("Scholar error")
        mock_services['books'].get_service_status.return_value = {"status": "active"}
        mock_services['sciencedirect'].get_service_status.return_value = {"status": "active"}
        mock_services['cache'].get_cache_stats.return_value = {"total_entries": 10}
        
        health = await orchestrator.get_service_health()
        
        assert health["orchestrator"]["status"] == "healthy"
        assert health["google_scholar"]["status"] == "error"
        assert "Scholar error" in health["google_scholar"]["error"]
        assert health["google_books"]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_search_by_author_success(self, orchestrator, mock_services, sample_source_results):
        """Test searching by author successfully"""
        author_name = "Test Author"
        max_results = 5
        
        # Mock service responses
        mock_services['scholar'].search_by_author.return_value = sample_source_results['google_scholar']
        mock_services['books'].search_by_author.return_value = sample_source_results['google_books']
        mock_services['sciencedirect'].search_by_author.return_value = sample_source_results['sciencedirect']
        
        results = await orchestrator.search_by_author(author_name, max_results)
        
        assert len(results) == 3
        assert 'google_scholar' in results
        assert 'google_books' in results
        assert 'sciencedirect' in results
        
        # Verify all services were called with correct parameters
        mock_services['scholar'].search_by_author.assert_called_once_with(author_name, max_results)
        mock_services['books'].search_by_author.assert_called_once_with(author_name, max_results)
        mock_services['sciencedirect'].search_by_author.assert_called_once_with(author_name, max_results)
    
    @pytest.mark.asyncio
    async def test_search_by_author_empty_name(self, orchestrator):
        """Test searching by author with empty name"""
        with pytest.raises(ValueError, match="Author name cannot be empty"):
            await orchestrator.search_by_author("")
        
        with pytest.raises(ValueError, match="Author name cannot be empty"):
            await orchestrator.search_by_author("   ")
    
    @pytest.mark.asyncio
    async def test_search_by_author_with_failures(self, orchestrator, mock_services, sample_source_results):
        """Test searching by author with some service failures"""
        author_name = "Test Author"
        
        # Mock service responses with failures
        mock_services['scholar'].search_by_author.return_value = sample_source_results['google_scholar']
        mock_services['books'].search_by_author.side_effect = Exception("Books error")
        mock_services['sciencedirect'].search_by_author.side_effect = Exception("ScienceDirect error")
        
        results = await orchestrator.search_by_author(author_name)
        
        assert len(results) == 3
        assert len(results['google_scholar']) == 2  # Success
        assert len(results['google_books']) == 0    # Failed
        assert len(results['sciencedirect']) == 0   # Failed
    
    @pytest.mark.asyncio
    async def test_get_research_statistics(self, orchestrator, mock_services):
        """Test getting research statistics"""
        # Mock cache stats
        cache_stats = {
            "total_entries": 100,
            "active_entries": 80,
            "cache_hit_rate_percent": 75.5
        }
        mock_services['cache'].get_cache_stats.return_value = cache_stats
        
        stats = await orchestrator.get_research_statistics()
        
        assert "cache_statistics" in stats
        assert "active_queries" in stats
        assert "service_configuration" in stats
        
        assert stats["cache_statistics"] == cache_stats
        assert stats["active_queries"] == 0
        assert "max_concurrent_requests" in stats["service_configuration"]
    
    @pytest.mark.asyncio
    async def test_get_research_statistics_error(self, orchestrator, mock_services):
        """Test getting research statistics with error"""
        # Mock cache stats to fail
        mock_services['cache'].get_cache_stats.side_effect = Exception("Cache error")
        
        stats = await orchestrator.get_research_statistics()
        
        assert "error" in stats
        assert "Cache error" in stats["error"]
        assert stats["active_queries"] == 0
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization_with_defaults(self):
        """Test orchestrator initialization with default services"""
        # This tests that the orchestrator can initialize with default services
        # In a real environment, this would create actual service instances
        with patch('services.research_orchestrator.GoogleScholarService'), \
             patch('services.research_orchestrator.GoogleBooksService'), \
             patch('services.research_orchestrator.ScienceDirectService'), \
             patch('services.research_orchestrator.AgnoAIService'), \
             patch('services.research_orchestrator.CacheService'):
            
            orchestrator = ResearchOrchestrator()
            
            assert orchestrator.google_scholar_service is not None
            assert orchestrator.google_books_service is not None
            assert orchestrator.sciencedirect_service is not None
            assert orchestrator.agno_ai_service is not None
            assert orchestrator.cache_service is not None
            assert orchestrator.max_concurrent_requests == 3
            assert orchestrator.timeout_seconds == 120
    
    @pytest.mark.asyncio
    async def test_concurrent_query_processing(self, orchestrator, mock_services, sample_source_results):
        """Test processing multiple queries concurrently"""
        # Mock cache miss for all queries
        mock_services['cache'].get_cached_result.return_value = None
        
        # Mock service responses
        mock_services['scholar'].search_papers.return_value = sample_source_results['google_scholar']
        mock_services['books'].search_books.return_value = sample_source_results['google_books']
        mock_services['sciencedirect'].search_papers.return_value = sample_source_results['sciencedirect']
        
        # Mock AI synthesis
        synthesis = ResearchSynthesis(
            summary="Test synthesis",
            key_insights=["Insight"],
            confidence_score=0.8
        )
        mock_services['agno'].synthesize_research_results.return_value = synthesis
        mock_services['cache'].store_result.return_value = True
        
        # Submit multiple queries
        query1 = await orchestrator.submit_research_query("query 1")
        query2 = await orchestrator.submit_research_query("query 2")
        query3 = await orchestrator.submit_research_query("query 3")
        
        # Process queries concurrently
        results = await asyncio.gather(
            orchestrator.process_research_query(query1.query_id),
            orchestrator.process_research_query(query2.query_id),
            orchestrator.process_research_query(query3.query_id)
        )
        
        assert len(results) == 3
        assert all(isinstance(result, ResearchResult) for result in results)
        assert all(result.cached is False for result in results)