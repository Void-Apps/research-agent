"""
Unit tests for Google Scholar integration service
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from typing import List, Dict, Any

from services.google_scholar_service import GoogleScholarService
from models.research import SourceResult, SourceType

class TestGoogleScholarService:
    """Test cases for GoogleScholarService"""
    
    @pytest.fixture
    def service(self):
        """Create a GoogleScholarService instance for testing"""
        return GoogleScholarService(
            max_results=5,
            rate_limit_delay=0.1,  # Faster for testing
            max_retries=2,
            use_proxy=False
        )
    
    @pytest.fixture
    def mock_paper_data(self):
        """Mock paper data from Google Scholar"""
        return {
            'title': 'Machine Learning in Healthcare: A Comprehensive Review',
            'author': [
                {'name': 'John Smith'},
                {'name': 'Jane Doe'}
            ],
            'abstract': 'This paper reviews the applications of machine learning in healthcare...',
            'url': 'https://scholar.google.com/citations?view_op=view_citation&hl=en&user=abc123',
            'pub_year': '2023',
            'num_citations': 42,
            'snippet': 'Machine learning has revolutionized healthcare...'
        }
    
    @pytest.fixture
    def mock_paper_minimal(self):
        """Mock minimal paper data"""
        return {
            'title': 'Minimal Paper Title',
            'author': 'Single Author',
            'pub_year': '2022'
        }
    
    @pytest.fixture
    def mock_paper_invalid(self):
        """Mock invalid paper data"""
        return {
            'title': '',  # Empty title should be filtered out
            'author': [],
            'abstract': None
        }
    
    def test_init_default_params(self):
        """Test service initialization with default parameters"""
        service = GoogleScholarService()
        
        assert service.max_results == 20
        assert service.rate_limit_delay == 2.0
        assert service.max_retries == 3
        assert service.use_proxy == False
        assert service._last_request_time == 0.0
    
    def test_init_custom_params(self):
        """Test service initialization with custom parameters"""
        service = GoogleScholarService(
            max_results=10,
            rate_limit_delay=1.5,
            max_retries=5,
            use_proxy=True
        )
        
        assert service.max_results == 10
        assert service.rate_limit_delay == 1.5
        assert service.max_retries == 5
        assert service.use_proxy == True
    
    @pytest.mark.asyncio
    async def test_rate_limit_no_delay_needed(self, service):
        """Test rate limiting when no delay is needed"""
        # First request should not delay
        start_time = asyncio.get_event_loop().time()
        await service._rate_limit()
        end_time = asyncio.get_event_loop().time()
        
        # Should be very fast (less than 0.01 seconds)
        assert end_time - start_time < 0.01
    
    @pytest.mark.asyncio
    async def test_rate_limit_with_delay(self, service):
        """Test rate limiting when delay is needed"""
        # Mock time.time to control timing
        with patch('time.time') as mock_time:
            # Set up mock time sequence
            mock_time.side_effect = [
                1000.0,  # _last_request_time set to this
                1000.05,  # current time when _rate_limit is called (50ms later)
                1000.05,  # time_since_last calculation
                1000.15   # after sleep
            ]
            
            service._last_request_time = 1000.0
            
            start_time = asyncio.get_event_loop().time()
            await service._rate_limit()
            end_time = asyncio.get_event_loop().time()
            
            # Should have called time.time multiple times
            assert mock_time.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self, service):
        """Test exponential backoff calculation"""
        delay_0 = await service._exponential_backoff(0)
        delay_1 = await service._exponential_backoff(1)
        delay_2 = await service._exponential_backoff(2)
        
        # Each delay should be roughly double the previous (with jitter)
        assert 0.8 <= delay_0 <= 1.5  # Base delay ~1.0 with jitter
        assert 1.8 <= delay_1 <= 2.5  # ~2.0 with jitter
        assert 3.8 <= delay_2 <= 4.5  # ~4.0 with jitter
    
    def test_parse_publication_date_valid_year(self, service):
        """Test parsing valid publication year"""
        result = service._parse_publication_date("2023")
        assert result == datetime(2023, 1, 1)
        
        result = service._parse_publication_date("2000")
        assert result == datetime(2000, 1, 1)
    
    def test_parse_publication_date_invalid_inputs(self, service):
        """Test parsing invalid publication dates"""
        assert service._parse_publication_date(None) is None
        assert service._parse_publication_date("") is None
        assert service._parse_publication_date("invalid") is None
        assert service._parse_publication_date("1800") is None  # Too old
        assert service._parse_publication_date("2050") is None  # Too future
        assert service._parse_publication_date("23") is None    # Too short
    
    def test_extract_paper_data_complete(self, service, mock_paper_data):
        """Test extracting complete paper data"""
        result = service._extract_paper_data(mock_paper_data)
        
        assert result is not None
        assert result.title == 'Machine Learning in Healthcare: A Comprehensive Review'
        assert result.authors == ['John Smith', 'Jane Doe']
        assert result.abstract == 'This paper reviews the applications of machine learning in healthcare...'
        assert result.url == 'https://scholar.google.com/citations?view_op=view_citation&hl=en&user=abc123'
        assert result.publication_date == datetime(2023, 1, 1)
        assert result.source_type == SourceType.GOOGLE_SCHOLAR
        assert result.citation_count == 42
    
    def test_extract_paper_data_minimal(self, service, mock_paper_minimal):
        """Test extracting minimal paper data"""
        result = service._extract_paper_data(mock_paper_minimal)
        
        assert result is not None
        assert result.title == 'Minimal Paper Title'
        assert result.authors == ['Single Author']
        assert result.abstract is None
        assert result.url is None
        assert result.publication_date == datetime(2022, 1, 1)
        assert result.source_type == SourceType.GOOGLE_SCHOLAR
        assert result.citation_count is None
    
    def test_extract_paper_data_invalid(self, service, mock_paper_invalid):
        """Test extracting invalid paper data returns None"""
        result = service._extract_paper_data(mock_paper_invalid)
        assert result is None
    
    def test_extract_paper_data_exception(self, service):
        """Test extracting paper data handles exceptions"""
        # Malformed data that would cause an exception
        malformed_data = {'title': ['not_a_string']}  # Title should be string, not list
        
        result = service._extract_paper_data(malformed_data)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_search_papers_empty_query(self, service):
        """Test search with empty query"""
        results = await service.search_papers("")
        assert results == []
        
        results = await service.search_papers("   ")
        assert results == []
        
        results = await service.search_papers(None)
        assert results == []
    
    @pytest.mark.asyncio
    @patch('services.google_scholar_service.scholarly')
    async def test_search_papers_success(self, mock_scholarly, service, mock_paper_data):
        """Test successful paper search"""
        # Mock the scholarly search
        mock_search_query = Mock()
        mock_scholarly.search_pubs.return_value = mock_search_query
        
        # Mock the async generator
        async def mock_async_generator():
            yield mock_paper_data
        
        service._async_search_generator = Mock(return_value=mock_async_generator())
        
        results = await service.search_papers("machine learning")
        
        assert len(results) == 1
        assert results[0].title == 'Machine Learning in Healthcare: A Comprehensive Review'
        assert results[0].source_type == SourceType.GOOGLE_SCHOLAR
        mock_scholarly.search_pubs.assert_called_once_with("machine learning")
    
    @pytest.mark.asyncio
    @patch('services.google_scholar_service.scholarly')
    async def test_search_papers_with_retries(self, mock_scholarly, service):
        """Test search with retries on failure"""
        # Mock scholarly to raise exception on first call, succeed on second
        # Note: service.max_retries is 2, so we have 2 attempts total
        call_count = 0
        def side_effect_func(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception(f"Error attempt {call_count}")
            return Mock()  # Success on second attempt
        
        mock_scholarly.search_pubs.side_effect = side_effect_func
        
        # Mock the async generator method to return a successful result
        async def mock_async_generator(search_query):
            yield {'title': 'Test Paper', 'author': [{'name': 'Test Author'}], 'pub_year': '2023'}
        
        # Patch the method directly
        service._async_search_generator = mock_async_generator
        
        results = await service.search_papers("test query")
        
        # Should succeed after retries
        assert len(results) == 1
        assert results[0].title == 'Test Paper'
        assert mock_scholarly.search_pubs.call_count == 2
    
    @pytest.mark.asyncio
    @patch('services.google_scholar_service.scholarly')
    async def test_search_papers_all_retries_fail(self, mock_scholarly, service):
        """Test search when all retries fail"""
        # Mock scholarly to always raise exception
        mock_scholarly.search_pubs.side_effect = Exception("Persistent error")
        
        results = await service.search_papers("test query")
        
        # Should return empty list after all retries fail
        assert results == []
        assert mock_scholarly.search_pubs.call_count == service.max_retries
    
    @pytest.mark.asyncio
    @patch('services.google_scholar_service.scholarly')
    async def test_search_papers_max_results_limit(self, mock_scholarly, service, mock_paper_data):
        """Test that search respects max_results limit"""
        mock_search_query = Mock()
        mock_scholarly.search_pubs.return_value = mock_search_query
        
        # Mock async generator that yields more papers than max_results
        async def mock_async_generator():
            for i in range(10):  # More than service.max_results (5)
                paper_data = mock_paper_data.copy()
                paper_data['title'] = f"Paper {i}"
                yield paper_data
        
        service._async_search_generator = Mock(return_value=mock_async_generator())
        
        results = await service.search_papers("test query")
        
        # Should only return max_results number of papers
        assert len(results) == service.max_results
    
    @pytest.mark.asyncio
    @patch('services.google_scholar_service.scholarly')
    async def test_get_paper_details_success(self, mock_scholarly, service, mock_paper_data):
        """Test successful paper details retrieval"""
        # Mock scholarly search_pubs_query
        mock_query_result = Mock()
        mock_query_result.__next__ = Mock(return_value=mock_paper_data)
        mock_scholarly.search_pubs_query.return_value = mock_query_result
        
        result = await service.get_paper_details("test_paper_id")
        
        assert result is not None
        assert result.title == 'Machine Learning in Healthcare: A Comprehensive Review'
        mock_scholarly.search_pubs_query.assert_called_once_with('cluster:test_paper_id')
    
    @pytest.mark.asyncio
    @patch('services.google_scholar_service.scholarly')
    async def test_get_paper_details_not_found(self, mock_scholarly, service):
        """Test paper details when paper not found"""
        # Mock empty result
        mock_query_result = Mock()
        mock_query_result.__next__ = Mock(side_effect=StopIteration)
        mock_scholarly.search_pubs_query.return_value = mock_query_result
        
        result = await service.get_paper_details("nonexistent_id")
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('services.google_scholar_service.scholarly')
    async def test_get_paper_details_with_retries(self, mock_scholarly, service, mock_paper_data):
        """Test paper details with retries"""
        # Mock to fail first, succeed second
        mock_query_result = Mock()
        mock_query_result.__next__ = Mock(return_value=mock_paper_data)
        
        mock_scholarly.search_pubs_query.side_effect = [
            Exception("Network error"),
            mock_query_result
        ]
        
        result = await service.get_paper_details("test_paper_id")
        
        assert result is not None
        assert result.title == 'Machine Learning in Healthcare: A Comprehensive Review'
        assert mock_scholarly.search_pubs_query.call_count == 2
    
    @pytest.mark.asyncio
    async def test_search_by_author_empty_name(self, service):
        """Test search by author with empty name"""
        results = await service.search_by_author("")
        assert results == []
        
        results = await service.search_by_author("   ")
        assert results == []
        
        results = await service.search_by_author(None)
        assert results == []
    
    @pytest.mark.asyncio
    @patch.object(GoogleScholarService, 'search_papers')
    async def test_search_by_author_success(self, mock_search, service):
        """Test successful search by author"""
        # Mock search_papers to return test results
        mock_results = [
            SourceResult(
                title="Paper by Author",
                authors=["Test Author"],
                source_type=SourceType.GOOGLE_SCHOLAR
            )
        ]
        mock_search.return_value = mock_results
        
        results = await service.search_by_author("Test Author")
        
        assert results == mock_results
        mock_search.assert_called_once_with('author:"Test Author"')
    
    @pytest.mark.asyncio
    @patch.object(GoogleScholarService, 'search_papers')
    async def test_search_by_author_max_papers_limit(self, mock_search, service):
        """Test search by author respects max_papers limit"""
        mock_search.return_value = []
        
        original_max = service.max_results
        await service.search_by_author("Test Author", max_papers=3)
        
        # Should temporarily change max_results
        mock_search.assert_called_once()
        # Should restore original max_results
        assert service.max_results == original_max
    
    def test_get_service_status(self, service):
        """Test service status retrieval"""
        status = service.get_service_status()
        
        expected_keys = {
            "service", "max_results", "rate_limit_delay", 
            "max_retries", "use_proxy", "last_request_time", "status"
        }
        
        assert set(status.keys()) == expected_keys
        assert status["service"] == "Google Scholar"
        assert status["max_results"] == service.max_results
        assert status["rate_limit_delay"] == service.rate_limit_delay
        assert status["max_retries"] == service.max_retries
        assert status["use_proxy"] == service.use_proxy
        assert status["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_async_search_generator_stop_iteration(self, service):
        """Test async search generator handles StopIteration"""
        mock_search_query = Mock()
        mock_search_query.__next__ = Mock(side_effect=StopIteration)
        
        results = []
        async for paper in service._async_search_generator(mock_search_query):
            results.append(paper)
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_async_search_generator_exception(self, service):
        """Test async search generator handles exceptions"""
        mock_search_query = Mock()
        mock_search_query.__next__ = Mock(side_effect=Exception("Test error"))
        
        results = []
        async for paper in service._async_search_generator(mock_search_query):
            results.append(paper)
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_async_search_generator_yields_papers(self, service, mock_paper_data):
        """Test async search generator yields papers correctly"""
        mock_search_query = Mock()
        # First call returns paper, second raises StopIteration
        mock_search_query.__next__ = Mock(side_effect=[mock_paper_data, StopIteration])
        
        results = []
        async for paper in service._async_search_generator(mock_search_query):
            results.append(paper)
        
        assert len(results) == 1
        assert results[0] == mock_paper_data

# Integration test fixtures and helpers
@pytest.fixture
def mock_scholarly_integration():
    """Mock scholarly module for integration tests"""
    with patch('services.google_scholar_service.scholarly') as mock:
        yield mock

class TestGoogleScholarServiceIntegration:
    """Integration tests for GoogleScholarService"""
    
    @pytest.mark.asyncio
    async def test_full_search_workflow(self, mock_scholarly_integration):
        """Test complete search workflow with mocked scholarly"""
        service = GoogleScholarService(max_results=2, rate_limit_delay=0.01)
        
        # Mock paper data
        paper1 = {
            'title': 'First Paper',
            'author': [{'name': 'Author One'}],
            'abstract': 'First abstract',
            'pub_year': '2023',
            'num_citations': 10
        }
        paper2 = {
            'title': 'Second Paper', 
            'author': [{'name': 'Author Two'}],
            'abstract': 'Second abstract',
            'pub_year': '2022',
            'num_citations': 5
        }
        
        # Mock the search query generator
        mock_search_query = Mock()
        mock_search_query.__next__ = Mock(side_effect=[paper1, paper2, StopIteration])
        mock_scholarly_integration.search_pubs.return_value = mock_search_query
        
        results = await service.search_papers("test query")
        
        assert len(results) == 2
        assert results[0].title == 'First Paper'
        assert results[0].authors == ['Author One']
        assert results[0].citation_count == 10
        assert results[1].title == 'Second Paper'
        assert results[1].authors == ['Author Two']
        assert results[1].citation_count == 5
        
        mock_scholarly_integration.search_pubs.assert_called_once_with("test query")