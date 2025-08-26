"""
Unit tests for Google Books integration service
"""
import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import List, Dict, Any

from services.google_books_service import GoogleBooksService
from models.research import SourceResult, SourceType

class TestGoogleBooksService:
    """Test cases for GoogleBooksService"""
    
    @pytest.fixture
    def service(self):
        """Create a GoogleBooksService instance for testing"""
        return GoogleBooksService(
            api_key="test_api_key",
            max_results=5,
            rate_limit_delay=0.1,  # Faster for testing
            max_retries=2,
            timeout=10
        )
    
    @pytest.fixture
    def service_no_key(self):
        """Create a GoogleBooksService instance without API key"""
        return GoogleBooksService(
            api_key=None,
            max_results=5,
            rate_limit_delay=0.1,
            max_retries=2
        )
    
    @pytest.fixture
    def mock_book_data(self):
        """Mock book data from Google Books API"""
        return {
            "volumeInfo": {
                "title": "Machine Learning: A Comprehensive Guide",
                "authors": ["John Smith", "Jane Doe"],
                "description": "This comprehensive guide covers all aspects of machine learning from basic concepts to advanced techniques. It includes practical examples and real-world applications.",
                "publishedDate": "2023-01-15",
                "infoLink": "https://books.google.com/books?id=abc123",
                "previewLink": "https://books.google.com/books?id=abc123&printsec=frontcover",
                "canonicalVolumeLink": "https://books.google.com/books/about/Machine_Learning.html?id=abc123",
                "industryIdentifiers": [
                    {"type": "ISBN_13", "identifier": "9781234567890"},
                    {"type": "ISBN_10", "identifier": "1234567890"}
                ]
            }
        }
    
    @pytest.fixture
    def mock_book_minimal(self):
        """Mock minimal book data"""
        return {
            "volumeInfo": {
                "title": "Minimal Book Title",
                "authors": ["Single Author"],
                "publishedDate": "2022"
            }
        }
    
    @pytest.fixture
    def mock_book_invalid(self):
        """Mock invalid book data"""
        return {
            "volumeInfo": {
                "title": "",  # Empty title should be filtered out
                "authors": [],
                "description": None
            }
        }
    
    @pytest.fixture
    def mock_api_response(self, mock_book_data):
        """Mock Google Books API response"""
        return {
            "kind": "books#volumes",
            "totalItems": 1,
            "items": [mock_book_data]
        }
    
    def test_init_default_params(self):
        """Test service initialization with default parameters"""
        service = GoogleBooksService()
        
        assert service.api_key is None
        assert service.max_results == 20
        assert service.rate_limit_delay == 1.0
        assert service.max_retries == 3
        assert service.timeout == 30
        assert service._last_request_time == 0.0
        assert service.base_url == "https://www.googleapis.com/books/v1/volumes"
    
    def test_init_custom_params(self):
        """Test service initialization with custom parameters"""
        service = GoogleBooksService(
            api_key="test_key",
            max_results=10,
            rate_limit_delay=1.5,
            max_retries=5,
            timeout=60
        )
        
        assert service.api_key == "test_key"
        assert service.max_results == 10
        assert service.rate_limit_delay == 1.5
        assert service.max_retries == 5
        assert service.timeout == 60
    
    def test_init_max_results_limit(self):
        """Test that max_results is capped at API limit"""
        service = GoogleBooksService(max_results=100)
        assert service.max_results == 40  # Google Books API limit
    
    @pytest.mark.asyncio
    async def test_rate_limit_no_delay_needed(self, service):
        """Test rate limiting when no delay is needed"""
        start_time = asyncio.get_event_loop().time()
        await service._rate_limit()
        end_time = asyncio.get_event_loop().time()
        
        # Should be very fast (less than 0.01 seconds)
        assert end_time - start_time < 0.01
    
    @pytest.mark.asyncio
    async def test_rate_limit_with_delay(self, service):
        """Test rate limiting when delay is needed"""
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
    
    def test_parse_publication_date_various_formats(self, service):
        """Test parsing various publication date formats"""
        # Test different valid formats
        assert service._parse_publication_date("2023-01-15") == datetime(2023, 1, 15)
        assert service._parse_publication_date("2023-01") == datetime(2023, 1, 1)
        assert service._parse_publication_date("2023") == datetime(2023, 1, 1)
        assert service._parse_publication_date("01/15/2023") == datetime(2023, 1, 15)
        assert service._parse_publication_date("January 15, 2023") == datetime(2023, 1, 15)
        assert service._parse_publication_date("January 2023") == datetime(2023, 1, 1)
    
    def test_parse_publication_date_invalid_inputs(self, service):
        """Test parsing invalid publication dates"""
        assert service._parse_publication_date(None) is None
        assert service._parse_publication_date("") is None
        assert service._parse_publication_date("invalid") is None
        assert service._parse_publication_date("800") is None   # Too old
        current_year = datetime.now().year
        future_year = str(current_year + 10)
        assert service._parse_publication_date(future_year) is None  # Too future
        assert service._parse_publication_date("23") is None    # Too short
    
    def test_extract_book_data_complete(self, service, mock_book_data):
        """Test extracting complete book data"""
        result = service._extract_book_data(mock_book_data)
        
        assert result is not None
        assert result.title == "Machine Learning: A Comprehensive Guide"
        assert result.authors == ["John Smith", "Jane Doe"]
        assert "comprehensive guide covers all aspects" in result.abstract
        assert result.url == "https://books.google.com/books/about/Machine_Learning.html?id=abc123"
        assert result.publication_date == datetime(2023, 1, 15)
        assert result.source_type == SourceType.GOOGLE_BOOKS
        assert result.isbn == "9781234567890"
        assert result.preview_link == "https://books.google.com/books?id=abc123&printsec=frontcover"
    
    def test_extract_book_data_minimal(self, service, mock_book_minimal):
        """Test extracting minimal book data"""
        result = service._extract_book_data(mock_book_minimal)
        
        assert result is not None
        assert result.title == "Minimal Book Title"
        assert result.authors == ["Single Author"]
        assert result.abstract is None
        assert result.url is None
        assert result.publication_date == datetime(2022, 1, 1)
        assert result.source_type == SourceType.GOOGLE_BOOKS
        assert result.isbn is None
        assert result.preview_link is None
    
    def test_extract_book_data_invalid(self, service, mock_book_invalid):
        """Test extracting invalid book data returns None"""
        result = service._extract_book_data(mock_book_invalid)
        assert result is None
    
    def test_extract_book_data_long_description(self, service):
        """Test extracting book data with very long description"""
        long_description = "A" * 1500  # Very long description
        book_data = {
            "volumeInfo": {
                "title": "Test Book",
                "authors": ["Test Author"],
                "description": long_description
            }
        }
        
        result = service._extract_book_data(book_data)
        
        assert result is not None
        assert len(result.abstract) == 1000  # Should be truncated to 1000 chars (997 + "...")
        assert result.abstract.endswith("...")
    
    def test_extract_book_data_exception(self, service):
        """Test extracting book data handles exceptions"""
        # Malformed data that would cause an exception
        malformed_data = {"volumeInfo": {"title": ["not_a_string"]}}  # Title should be string
        
        result = service._extract_book_data(malformed_data)
        assert result is None
    
    def test_build_search_url_with_api_key(self, service):
        """Test building search URL with API key"""
        url = service._build_search_url("machine learning")
        
        assert "q=machine+learning" in url
        assert "maxResults=5" in url
        assert "startIndex=0" in url
        assert "key=test_api_key" in url
        assert url.startswith("https://www.googleapis.com/books/v1/volumes")
    
    def test_build_search_url_without_api_key(self, service_no_key):
        """Test building search URL without API key"""
        url = service_no_key._build_search_url("test query")
        
        assert "q=test+query" in url
        assert "maxResults=5" in url
        assert "startIndex=0" in url
        assert "key=" not in url
    
    def test_build_search_url_with_start_index(self, service):
        """Test building search URL with start index"""
        url = service._build_search_url("test", start_index=10)
        
        assert "startIndex=10" in url
    
    @pytest.mark.asyncio
    async def test_make_api_request_success(self, service):
        """Test successful API request"""
        mock_response_data = {"test": "data"}
        
        # Mock the entire _make_api_request method instead of aiohttp internals
        with patch.object(service, '_make_api_request', return_value=mock_response_data):
            result = await service._make_api_request("http://test.com")
            assert result == mock_response_data
    
    @pytest.mark.asyncio
    async def test_make_api_request_rate_limit(self, service):
        """Test API request with rate limit error"""
        rate_limit_error = aiohttp.ClientResponseError(
            request_info=Mock(),
            history=[],
            status=429,
            message="Rate limit exceeded"
        )
        
        with patch.object(service, '_make_api_request', side_effect=rate_limit_error):
            with pytest.raises(aiohttp.ClientResponseError) as exc_info:
                await service._make_api_request("http://test.com")
            
            assert exc_info.value.status == 429
    
    @pytest.mark.asyncio
    async def test_make_api_request_timeout(self, service):
        """Test API request timeout"""
        with patch.object(service, '_make_api_request', side_effect=asyncio.TimeoutError()):
            with pytest.raises(asyncio.TimeoutError):
                await service._make_api_request("http://test.com")
    
    @pytest.mark.asyncio
    async def test_search_books_empty_query(self, service):
        """Test search with empty query"""
        results = await service.search_books("")
        assert results == []
        
        results = await service.search_books("   ")
        assert results == []
        
        results = await service.search_books(None)
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_books_success(self, service, mock_api_response):
        """Test successful book search"""
        with patch.object(service, '_make_api_request', return_value=mock_api_response):
            results = await service.search_books("machine learning")
            
            assert len(results) == 1
            assert results[0].title == "Machine Learning: A Comprehensive Guide"
            assert results[0].source_type == SourceType.GOOGLE_BOOKS
    
    @pytest.mark.asyncio
    async def test_search_books_no_items(self, service):
        """Test search with no results"""
        empty_response = {
            "kind": "books#volumes",
            "totalItems": 0,
            "items": []
        }
        
        with patch.object(service, '_make_api_request', return_value=empty_response):
            results = await service.search_books("nonexistent book")
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_search_books_with_retries(self, service, mock_api_response):
        """Test search with retries on failure"""
        call_count = 0
        
        async def mock_request(url):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise aiohttp.ClientError("Network error")
            return mock_api_response
        
        with patch.object(service, '_make_api_request', side_effect=mock_request):
            results = await service.search_books("test query")
            
            assert len(results) == 1
            assert call_count == 2  # First failed, second succeeded
    
    @pytest.mark.asyncio
    async def test_search_books_rate_limit_retry(self, service, mock_api_response):
        """Test search with rate limit retry"""
        call_count = 0
        
        async def mock_request(url):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                error = aiohttp.ClientResponseError(
                    request_info=Mock(),
                    history=[],
                    status=429,
                    message="Rate limit exceeded"
                )
                raise error
            return mock_api_response
        
        with patch.object(service, '_make_api_request', side_effect=mock_request):
            results = await service.search_books("test query")
            
            assert len(results) == 1
            assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_search_books_all_retries_fail(self, service):
        """Test search when all retries fail"""
        async def mock_request(url):
            raise aiohttp.ClientError("Persistent error")
        
        with patch.object(service, '_make_api_request', side_effect=mock_request):
            results = await service.search_books("test query")
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_get_book_details_success(self, service, mock_book_data):
        """Test successful book details retrieval"""
        with patch.object(service, '_make_api_request', return_value=mock_book_data):
            result = await service.get_book_details("test_volume_id")
            
            assert result is not None
            assert result.title == "Machine Learning: A Comprehensive Guide"
    
    @pytest.mark.asyncio
    async def test_get_book_details_empty_id(self, service):
        """Test book details with empty volume ID"""
        result = await service.get_book_details("")
        assert result is None
        
        result = await service.get_book_details("   ")
        assert result is None
        
        result = await service.get_book_details(None)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_book_details_not_found(self, service):
        """Test book details when book not found"""
        async def mock_request(url):
            error = aiohttp.ClientResponseError(
                request_info=Mock(),
                history=[],
                status=404,
                message="Not found"
            )
            raise error
        
        with patch.object(service, '_make_api_request', side_effect=mock_request):
            result = await service.get_book_details("nonexistent_id")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_book_details_with_retries(self, service, mock_book_data):
        """Test book details with retries"""
        call_count = 0
        
        async def mock_request(url):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise aiohttp.ClientError("Network error")
            return mock_book_data
        
        with patch.object(service, '_make_api_request', side_effect=mock_request):
            result = await service.get_book_details("test_volume_id")
            
            assert result is not None
            assert result.title == "Machine Learning: A Comprehensive Guide"
            assert call_count == 2
    
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
    async def test_search_by_author_success(self, service):
        """Test successful search by author"""
        mock_results = [
            SourceResult(
                title="Book by Author",
                authors=["Test Author"],
                source_type=SourceType.GOOGLE_BOOKS
            )
        ]
        
        with patch.object(service, 'search_books', return_value=mock_results) as mock_search:
            results = await service.search_by_author("Test Author")
            
            assert results == mock_results
            mock_search.assert_called_once_with('inauthor:"Test Author"')
    
    @pytest.mark.asyncio
    async def test_search_by_author_max_books_limit(self, service):
        """Test search by author respects max_books limit"""
        with patch.object(service, 'search_books', return_value=[]) as mock_search:
            original_max = service.max_results
            await service.search_by_author("Test Author", max_books=3)
            
            # Should restore original max_results
            assert service.max_results == original_max
    
    @pytest.mark.asyncio
    async def test_search_by_subject_empty_subject(self, service):
        """Test search by subject with empty subject"""
        results = await service.search_by_subject("")
        assert results == []
        
        results = await service.search_by_subject("   ")
        assert results == []
        
        results = await service.search_by_subject(None)
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_by_subject_success(self, service):
        """Test successful search by subject"""
        mock_results = [
            SourceResult(
                title="Book on Subject",
                authors=["Test Author"],
                source_type=SourceType.GOOGLE_BOOKS
            )
        ]
        
        with patch.object(service, 'search_books', return_value=mock_results) as mock_search:
            results = await service.search_by_subject("Machine Learning")
            
            assert results == mock_results
            mock_search.assert_called_once_with('subject:"Machine Learning"')
    
    @pytest.mark.asyncio
    async def test_search_by_subject_max_books_limit(self, service):
        """Test search by subject respects max_books limit"""
        with patch.object(service, 'search_books', return_value=[]) as mock_search:
            original_max = service.max_results
            await service.search_by_subject("Test Subject", max_books=3)
            
            # Should restore original max_results
            assert service.max_results == original_max
    
    def test_get_service_status(self, service):
        """Test service status retrieval"""
        status = service.get_service_status()
        
        expected_keys = {
            "service", "max_results", "rate_limit_delay", 
            "max_retries", "timeout", "has_api_key", 
            "last_request_time", "status"
        }
        
        assert set(status.keys()) == expected_keys
        assert status["service"] == "Google Books"
        assert status["max_results"] == service.max_results
        assert status["rate_limit_delay"] == service.rate_limit_delay
        assert status["max_retries"] == service.max_retries
        assert status["timeout"] == service.timeout
        assert status["has_api_key"] == True  # service fixture has API key
        assert status["status"] == "active"
    
    def test_get_service_status_no_api_key(self, service_no_key):
        """Test service status without API key"""
        status = service_no_key.get_service_status()
        assert status["has_api_key"] == False


class TestGoogleBooksServiceIntegration:
    """Integration tests for GoogleBooksService"""
    
    @pytest.mark.asyncio
    async def test_full_search_workflow(self):
        """Test complete search workflow with mocked API"""
        service = GoogleBooksService(max_results=2, rate_limit_delay=0.01)
        
        # Mock API response
        mock_response = {
            "kind": "books#volumes",
            "totalItems": 2,
            "items": [
                {
                    "volumeInfo": {
                        "title": "First Book",
                        "authors": ["Author One"],
                        "description": "First book description",
                        "publishedDate": "2023",
                        "infoLink": "https://books.google.com/books?id=book1"
                    }
                },
                {
                    "volumeInfo": {
                        "title": "Second Book",
                        "authors": ["Author Two"],
                        "description": "Second book description",
                        "publishedDate": "2022",
                        "infoLink": "https://books.google.com/books?id=book2"
                    }
                }
            ]
        }
        
        with patch.object(service, '_make_api_request', return_value=mock_response):
            results = await service.search_books("test query")
            
            assert len(results) == 2
            assert results[0].title == "First Book"
            assert results[0].authors == ["Author One"]
            assert results[0].source_type == SourceType.GOOGLE_BOOKS
            assert results[1].title == "Second Book"
            assert results[1].authors == ["Author Two"]
            assert results[1].source_type == SourceType.GOOGLE_BOOKS
    
    @pytest.mark.asyncio
    async def test_isbn_extraction_priority(self):
        """Test that ISBN_13 is preferred over ISBN_10"""
        service = GoogleBooksService()
        
        book_data = {
            "volumeInfo": {
                "title": "Test Book",
                "authors": ["Test Author"],
                "industryIdentifiers": [
                    {"type": "ISBN_10", "identifier": "1234567890"},
                    {"type": "ISBN_13", "identifier": "9781234567890"},
                    {"type": "OTHER", "identifier": "other123"}
                ]
            }
        }
        
        result = service._extract_book_data(book_data)
        
        assert result is not None
        assert result.isbn == "9781234567890"  # Should prefer ISBN_13
    
    @pytest.mark.asyncio
    async def test_url_preference_order(self):
        """Test URL preference: canonical > info > preview"""
        service = GoogleBooksService()
        
        book_data = {
            "volumeInfo": {
                "title": "Test Book",
                "authors": ["Test Author"],
                "infoLink": "https://books.google.com/info",
                "previewLink": "https://books.google.com/preview",
                "canonicalVolumeLink": "https://books.google.com/canonical"
            }
        }
        
        result = service._extract_book_data(book_data)
        
        assert result is not None
        assert result.url == "https://books.google.com/canonical"
        assert result.preview_link == "https://books.google.com/preview"