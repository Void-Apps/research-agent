"""
Unit tests for database initialization
"""
import pytest
from unittest.mock import AsyncMock, patch
from database.init_db import (
    create_indexes, create_ttl_indexes, initialize_collections, 
    initialize_database, drop_database
)

class TestDatabaseInitialization:
    """Test database initialization functionality"""
    
    @pytest.mark.asyncio
    async def test_create_indexes(self, mock_database):
        """Test index creation for all collections"""
        mock_database.research_queries.create_indexes = AsyncMock()
        mock_database.research_results.create_indexes = AsyncMock()
        mock_database.cache_metadata.create_indexes = AsyncMock()
        
        await create_indexes(mock_database)
        
        # Verify that create_indexes was called for each collection
        mock_database.research_queries.create_indexes.assert_called_once()
        mock_database.research_results.create_indexes.assert_called_once()
        mock_database.cache_metadata.create_indexes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_ttl_indexes(self, mock_database):
        """Test TTL index creation"""
        mock_database.research_results.create_index = AsyncMock()
        
        await create_ttl_indexes(mock_database)
        
        # Verify TTL index was created
        mock_database.research_results.create_index.assert_called_once()
        call_args = mock_database.research_results.create_index.call_args
        assert call_args[0][0] == [("expires_at", 1)]  # ASCENDING = 1
        assert call_args[1]["expireAfterSeconds"] == 0
    
    @pytest.mark.asyncio
    async def test_initialize_collections_success(self, mock_database):
        """Test successful collection initialization"""
        mock_database.create_collection = AsyncMock()
        
        await initialize_collections(mock_database)
        
        # Verify create_collection was called for each collection
        assert mock_database.create_collection.call_count == 3
        
        # Check that collections were created with proper names
        call_args_list = mock_database.create_collection.call_args_list
        collection_names = [call[0][0] for call in call_args_list]
        
        assert "research_queries" in collection_names
        assert "research_results" in collection_names
        assert "cache_metadata" in collection_names
    
    @pytest.mark.asyncio
    async def test_initialize_collections_already_exists(self, mock_database):
        """Test collection initialization when collections already exist"""
        mock_database.create_collection = AsyncMock(
            side_effect=Exception("already exists")
        )
        
        # Should not raise exception when collections already exist
        await initialize_collections(mock_database)
        
        assert mock_database.create_collection.call_count == 3
    
    @pytest.mark.asyncio
    async def test_initialize_database(self):
        """Test complete database initialization"""
        with patch('database.init_db.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # Mock all the initialization functions
            with patch('database.init_db.initialize_collections') as mock_init_collections, \
                 patch('database.init_db.create_indexes') as mock_create_indexes, \
                 patch('database.init_db.create_ttl_indexes') as mock_create_ttl:
                
                await initialize_database()
                
                # Verify all initialization steps were called
                mock_init_collections.assert_called_once_with(mock_db)
                mock_create_indexes.assert_called_once_with(mock_db)
                mock_create_ttl.assert_called_once_with(mock_db)
    
    @pytest.mark.asyncio
    async def test_drop_database(self):
        """Test database dropping functionality"""
        with patch('database.init_db.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.name = "test_database"
            mock_db.client.drop_database = AsyncMock()
            mock_get_db.return_value = mock_db
            
            await drop_database()
            
            mock_db.client.drop_database.assert_called_once_with("test_database")