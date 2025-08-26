"""
Unit tests for database models and connections
"""
import pytest
import asyncio
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from bson import ObjectId

# Set test environment variables before importing modules
os.environ["MONGODB_DATABASE"] = "test_ai_research_agent"
os.environ["MONGODB_HOST"] = "localhost"
os.environ["MONGODB_PORT"] = "27017"

from database.connection import DatabaseConnection, get_database, get_collection
from models.research import (
    ResearchQuery, ResearchResult, SourceResult, CacheMetadata,
    QueryStatus, SourceType, ResearchQueryRequest, ResearchQueryResponse
)

class TestDatabaseConnection:
    """Test database connection functionality"""
    
    @pytest.fixture
    def db_connection(self):
        """Create a test database connection"""
        connection = DatabaseConnection()
        return connection
    
    @pytest.mark.asyncio
    async def test_connection_string_generation(self, db_connection):
        """Test MongoDB connection string generation"""
        # Test without credentials
        connection_string = db_connection._get_connection_string()
        assert "mongodb://localhost:27017/test_ai_research_agent" in connection_string
        
        # Test with credentials
        with patch.dict(os.environ, {
            "MONGODB_USERNAME": "testuser",
            "MONGODB_PASSWORD": "testpass"
        }):
            connection_string = db_connection._get_connection_string()
            assert "mongodb://testuser:testpass@localhost:27017/test_ai_research_agent" in connection_string
    
    @pytest.mark.asyncio
    async def test_connect_success(self, db_connection):
        """Test successful database connection"""
        with patch('database.connection.AsyncIOMotorClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.admin.command = AsyncMock(return_value={"ok": 1})
            
            await db_connection.connect()
            
            assert db_connection.client is not None
            assert db_connection.database is not None
            mock_instance.admin.command.assert_called_once_with('ping')
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, db_connection):
        """Test database connection failure"""
        with patch('database.connection.AsyncIOMotorClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.admin.command.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                await db_connection.connect()
    
    @pytest.mark.asyncio
    async def test_ping(self, db_connection):
        """Test database ping functionality"""
        with patch('database.connection.AsyncIOMotorClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.admin.command = AsyncMock(return_value={"ok": 1})
            
            await db_connection.connect()
            result = await db_connection.ping()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_collection(self, db_connection):
        """Test getting a collection from database"""
        with patch('database.connection.AsyncIOMotorClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.admin.command = AsyncMock(return_value={"ok": 1})
            
            await db_connection.connect()
            collection = db_connection.get_collection("test_collection")
            
            assert collection is not None

class TestResearchModels:
    """Test Pydantic models for research data"""
    
    def test_source_result_model(self):
        """Test SourceResult model validation"""
        # Valid source result
        source_result = SourceResult(
            title="Test Paper",
            authors=["Author 1", "Author 2"],
            abstract="Test abstract",
            url="https://example.com",
            publication_date=datetime.utcnow(),
            source_type=SourceType.GOOGLE_SCHOLAR,
            citation_count=10
        )
        
        assert source_result.title == "Test Paper"
        assert len(source_result.authors) == 2
        assert source_result.source_type == SourceType.GOOGLE_SCHOLAR
        assert source_result.citation_count == 10
    
    def test_source_result_minimal(self):
        """Test SourceResult with minimal required fields"""
        source_result = SourceResult(
            title="Minimal Paper",
            source_type=SourceType.GOOGLE_BOOKS
        )
        
        assert source_result.title == "Minimal Paper"
        assert source_result.authors == []
        assert source_result.abstract is None
        assert source_result.source_type == SourceType.GOOGLE_BOOKS
    
    def test_research_query_model(self):
        """Test ResearchQuery model validation"""
        query = ResearchQuery(
            query_id="test-query-123",
            query_text="machine learning algorithms",
            user_id="user-456",
            status=QueryStatus.PENDING
        )
        
        assert query.query_id == "test-query-123"
        assert query.query_text == "machine learning algorithms"
        assert query.user_id == "user-456"
        assert query.status == QueryStatus.PENDING
        assert isinstance(query.timestamp, datetime)
    
    def test_research_query_default_values(self):
        """Test ResearchQuery default values"""
        query = ResearchQuery(
            query_id="test-query-456",
            query_text="artificial intelligence"
        )
        
        assert query.status == QueryStatus.PENDING
        assert isinstance(query.timestamp, datetime)
        assert query.metadata == {}
        assert query.user_id is None
    
    def test_research_result_model(self):
        """Test ResearchResult model validation"""
        source_results = [
            SourceResult(
                title="Paper 1",
                source_type=SourceType.GOOGLE_SCHOLAR
            ),
            SourceResult(
                title="Book 1",
                source_type=SourceType.GOOGLE_BOOKS
            )
        ]
        
        result = ResearchResult(
            query_id="test-query-789",
            results={
                "google_scholar": [source_results[0]],
                "google_books": [source_results[1]]
            },
            ai_summary="Test summary",
            confidence_score=0.85,
            cached=False
        )
        
        assert result.query_id == "test-query-789"
        assert len(result.results) == 2
        assert result.ai_summary == "Test summary"
        assert result.confidence_score == 0.85
        assert result.cached is False
        assert isinstance(result.created_at, datetime)
    
    def test_cache_metadata_model(self):
        """Test CacheMetadata model validation"""
        cache_meta = CacheMetadata(
            query_hash="abc123def456",
            hit_count=5,
            query_variations=["query 1", "query 2"]
        )
        
        assert cache_meta.query_hash == "abc123def456"
        assert cache_meta.hit_count == 5
        assert len(cache_meta.query_variations) == 2
        assert isinstance(cache_meta.last_updated, datetime)
    
    def test_research_query_request_validation(self):
        """Test ResearchQueryRequest validation"""
        # Valid request
        request = ResearchQueryRequest(
            query="test query",
            user_id="user123"
        )
        assert request.query == "test query"
        assert request.user_id == "user123"
        
        # Test query length validation
        with pytest.raises(ValueError):
            ResearchQueryRequest(query="")  # Empty query should fail
        
        with pytest.raises(ValueError):
            ResearchQueryRequest(query="x" * 1001)  # Too long query should fail
    
    def test_research_query_response(self):
        """Test ResearchQueryResponse model"""
        response = ResearchQueryResponse(
            query_id="query-123",
            status=QueryStatus.PROCESSING,
            message="Query submitted successfully"
        )
        
        assert response.query_id == "query-123"
        assert response.status == QueryStatus.PROCESSING
        assert response.message == "Query submitted successfully"