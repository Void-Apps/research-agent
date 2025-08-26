"""
Pytest configuration and fixtures for testing
"""
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import json

# Set test environment variables
os.environ["MONGODB_DATABASE"] = "test_ai_research_agent"
os.environ["MONGODB_HOST"] = "localhost"
os.environ["MONGODB_PORT"] = "27017"
os.environ["ENVIRONMENT"] = "test"
os.environ["GOOGLE_SCHOLAR_API_KEY"] = "test_key"
os.environ["GOOGLE_BOOKS_API_KEY"] = "test_key"
os.environ["SCIENCEDIRECT_API_KEY"] = "test_key"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_database():
    """Mock database for testing"""
    mock_db = AsyncMock()
    mock_db.research_queries = AsyncMock()
    mock_db.research_results = AsyncMock()
    mock_db.cache_metadata = AsyncMock()
    return mock_db

@pytest.fixture
def mock_collection():
    """Mock collection for testing"""
    mock_collection = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    mock_collection.create_index = AsyncMock()
    mock_collection.create_indexes = AsyncMock()
    return mock_collection

@pytest.fixture
def test_client():
    """Create a test client for FastAPI"""
    from main import app
    return TestClient(app)

@pytest.fixture
def mock_research_query():
    """Mock research query data"""
    return {
        "id": "test-query-123",
        "query": "artificial intelligence machine learning",
        "user_id": "test-user",
        "timestamp": datetime.now(timezone.utc),
        "status": "completed"
    }

@pytest.fixture
def mock_scholar_result():
    """Mock Google Scholar result"""
    return {
        "title": "Deep Learning for Natural Language Processing",
        "authors": ["John Smith", "Jane Doe"],
        "abstract": "This paper presents a comprehensive study of deep learning techniques.",
        "citation_count": 150,
        "url": "https://scholar.google.com/test",
        "publication_year": 2023
    }

@pytest.fixture
def mock_books_result():
    """Mock Google Books result"""
    return {
        "title": "Machine Learning: A Comprehensive Guide",
        "authors": ["Alice Johnson"],
        "description": "A complete guide to machine learning algorithms.",
        "isbn": "978-0123456789",
        "preview_link": "https://books.google.com/test",
        "published_date": "2023-01-01"
    }

@pytest.fixture
def mock_sciencedirect_result():
    """Mock ScienceDirect result"""
    return {
        "title": "Advanced Neural Networks in Computer Vision",
        "authors": ["Bob Wilson", "Carol Brown"],
        "abstract": "This study explores neural networks in computer vision.",
        "doi": "10.1016/j.test.2023.01.001",
        "journal": "Journal of Artificial Intelligence",
        "publication_date": datetime.now(timezone.utc)
    }

@pytest.fixture
def mock_research_result(mock_scholar_result, mock_books_result, mock_sciencedirect_result):
    """Mock complete research result"""
    return {
        "query_id": "test-query-123",
        "sources": {
            "google_scholar": [mock_scholar_result],
            "google_books": [mock_books_result],
            "sciencedirect": [mock_sciencedirect_result]
        },
        "ai_summary": "The research shows significant advances in AI and ML.",
        "confidence_score": 0.85,
        "cached": False
    }

@pytest.fixture
def mock_http_response():
    """Mock HTTP response for external API calls"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_response.text = json.dumps({"results": []})
    return mock_response

@pytest.fixture
def mock_agno_agent():
    """Mock Agno AI agent"""
    mock_agent = AsyncMock()
    mock_agent.run.return_value = {
        "synthesis": "AI-generated research synthesis",
        "insights": ["Key insight 1", "Key insight 2"],
        "confidence": 0.85
    }
    return mock_agent

@pytest.fixture(autouse=True)
def mock_external_apis():
    """Mock all external API calls"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.get.return_value.status_code = 200
        mock_instance.get.return_value.json.return_value = {"results": []}
        mock_instance.post.return_value.status_code = 200
        mock_instance.post.return_value.json.return_value = {"results": []}
        yield mock_instance

@pytest.fixture
def mock_cache_service():
    """Mock cache service"""
    mock_service = AsyncMock()
    mock_service.get_cached_result.return_value = None
    mock_service.cache_result.return_value = True
    mock_service.normalize_query.return_value = "normalized_query"
    return mock_service

# Test data generators
def generate_test_id():
    """Generate a test ID"""
    import uuid
    return str(uuid.uuid4())

def generate_test_timestamp():
    """Generate a test timestamp"""
    return datetime.now(timezone.utc)

# Async test helpers
async def async_test_helper(coro):
    """Helper for running async tests"""
    return await coro