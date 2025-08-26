"""
Cache service for research queries with MongoDB integration
"""
import hashlib
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorCollection

from models.research import ResearchResult, CacheMetadata
from database.connection import get_collection
from exceptions import CacheError, DatabaseError

logger = logging.getLogger(__name__)

class CacheService:
    """
    Cache service for managing research query caching with MongoDB
    
    Provides query normalization, hashing, TTL management, and cache operations
    """
    
    def __init__(self, default_ttl_hours: int = 24):
        """
        Initialize cache service
        
        Args:
            default_ttl_hours: Default TTL for cached results in hours
        """
        self.default_ttl_hours = default_ttl_hours
        self._results_collection: Optional[AsyncIOMotorCollection] = None
        self._metadata_collection: Optional[AsyncIOMotorCollection] = None
    
    async def _get_collections(self):
        """Get MongoDB collections for cache operations"""
        try:
            if not self._results_collection:
                self._results_collection = await get_collection("research_results")
            if not self._metadata_collection:
                self._metadata_collection = await get_collection("cache_metadata")
            return self._results_collection, self._metadata_collection
        except Exception as e:
            raise DatabaseError("get_collections", f"Failed to get cache collections: {str(e)}")
    
    def normalize_query(self, query: str) -> str:
        """
        Normalize query text for consistent cache key generation
        
        Args:
            query: Raw query string
            
        Returns:
            Normalized query string
        """
        # Convert to lowercase
        normalized = query.lower().strip()
        
        # Remove extra whitespace and normalize spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common punctuation that doesn't affect meaning
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        
        # Remove common stop words that don't affect search meaning
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over',
            'under', 'again', 'further', 'then', 'once'
        }
        
        words = normalized.split()
        filtered_words = [word for word in words if word not in stop_words]
        
        # Sort words to handle different word orders
        filtered_words.sort()
        
        return ' '.join(filtered_words)
    
    def generate_cache_key(self, query: str) -> str:
        """
        Generate MD5 hash for normalized query
        
        Args:
            query: Query string to hash
            
        Returns:
            MD5 hash of normalized query
        """
        normalized_query = self.normalize_query(query)
        return hashlib.md5(normalized_query.encode('utf-8')).hexdigest()
    
    async def get_cached_result(self, query: str) -> Optional[ResearchResult]:
        """
        Retrieve cached research result for a query
        
        Args:
            query: Research query string
            
        Returns:
            Cached ResearchResult if found and not expired, None otherwise
        """
        try:
            results_collection, metadata_collection = await self._get_collections()
            cache_key = self.generate_cache_key(query)
            
            # Find cached result
            cached_doc = await results_collection.find_one({
                "query_hash": cache_key,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not cached_doc:
                logger.debug(f"No valid cache entry found for query hash: {cache_key}")
                return None
            
            # Update cache metadata hit count
            await metadata_collection.update_one(
                {"query_hash": cache_key},
                {
                    "$inc": {"hit_count": 1},
                    "$set": {"last_updated": datetime.utcnow()},
                    "$addToSet": {"query_variations": query}
                },
                upsert=True
            )
            
            # Convert MongoDB document to ResearchResult
            cached_doc["cached"] = True
            result = ResearchResult(**cached_doc)
            
            logger.info(f"Cache hit for query hash: {cache_key}")
            return result
            
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving cached result: {e}")
            raise CacheError("get_cached_result", f"Failed to retrieve cached result: {str(e)}")
    
    async def store_result(
        self, 
        query: str, 
        result: ResearchResult, 
        ttl_hours: Optional[int] = None
    ) -> bool:
        """
        Store research result in cache
        
        Args:
            query: Original query string
            result: ResearchResult to cache
            ttl_hours: TTL in hours, uses default if None
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            results_collection, metadata_collection = await self._get_collections()
            cache_key = self.generate_cache_key(query)
            ttl = ttl_hours or self.default_ttl_hours
            
            # Set expiration time
            expires_at = datetime.utcnow() + timedelta(hours=ttl)
            
            # Prepare document for storage
            result_doc = result.model_dump(by_alias=True)
            result_doc.update({
                "query_hash": cache_key,
                "original_query": query,
                "expires_at": expires_at,
                "cached": True
            })
            
            # Remove the _id field if it exists to let MongoDB generate it
            result_doc.pop("_id", None)
            
            # Store result with upsert
            await results_collection.replace_one(
                {"query_hash": cache_key},
                result_doc,
                upsert=True
            )
            
            # Update metadata
            await metadata_collection.update_one(
                {"query_hash": cache_key},
                {
                    "$set": {
                        "last_updated": datetime.utcnow(),
                    },
                    "$addToSet": {"query_variations": query},
                    "$setOnInsert": {"hit_count": 0}
                },
                upsert=True
            )
            
            logger.info(f"Cached result for query hash: {cache_key}, expires at: {expires_at}")
            return True
            
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error storing result in cache: {e}")
            raise CacheError("store_result", f"Failed to store result in cache: {str(e)}")
    
    async def invalidate_cache(self, query: str) -> bool:
        """
        Invalidate cached result for a specific query
        
        Args:
            query: Query string to invalidate
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        try:
            results_collection, metadata_collection = await self._get_collections()
            cache_key = self.generate_cache_key(query)
            
            # Remove cached result
            result = await results_collection.delete_one({"query_hash": cache_key})
            
            # Remove metadata
            await metadata_collection.delete_one({"query_hash": cache_key})
            
            if result.deleted_count > 0:
                logger.info(f"Invalidated cache for query hash: {cache_key}")
                return True
            else:
                logger.debug(f"No cache entry found to invalidate for query hash: {cache_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False
    
    async def cleanup_expired_cache(self) -> int:
        """
        Remove expired cache entries
        
        Returns:
            Number of entries removed
        """
        try:
            results_collection, metadata_collection = await self._get_collections()
            current_time = datetime.utcnow()
            
            # Find expired entries to get their cache keys
            expired_cursor = results_collection.find(
                {"expires_at": {"$lte": current_time}},
                {"query_hash": 1}
            )
            
            expired_keys = []
            async for doc in expired_cursor:
                expired_keys.append(doc["query_hash"])
            
            if not expired_keys:
                logger.debug("No expired cache entries found")
                return 0
            
            # Remove expired results
            result = await results_collection.delete_many({
                "expires_at": {"$lte": current_time}
            })
            
            # Remove corresponding metadata
            await metadata_collection.delete_many({
                "query_hash": {"$in": expired_keys}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} expired cache entries")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            results_collection, metadata_collection = await self._get_collections()
            current_time = datetime.utcnow()
            
            # Count total cached entries
            total_entries = await results_collection.count_documents({})
            
            # Count active (non-expired) entries
            active_entries = await results_collection.count_documents({
                "expires_at": {"$gt": current_time}
            })
            
            # Count expired entries
            expired_entries = total_entries - active_entries
            
            # Get total hit count
            hit_count_pipeline = [
                {"$group": {"_id": None, "total_hits": {"$sum": "$hit_count"}}}
            ]
            hit_count_result = await metadata_collection.aggregate(hit_count_pipeline).to_list(1)
            total_hits = hit_count_result[0]["total_hits"] if hit_count_result else 0
            
            # Calculate cache hit rate (approximate)
            cache_hit_rate = (total_hits / (total_hits + active_entries)) * 100 if (total_hits + active_entries) > 0 else 0
            
            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "total_hits": total_hits,
                "cache_hit_rate_percent": round(cache_hit_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "total_entries": 0,
                "active_entries": 0,
                "expired_entries": 0,
                "total_hits": 0,
                "cache_hit_rate_percent": 0.0
            }
    
    async def clear_all_cache(self) -> bool:
        """
        Clear all cached entries (use with caution)
        
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            results_collection, metadata_collection = await self._get_collections()
            
            # Clear all results
            await results_collection.delete_many({})
            
            # Clear all metadata
            await metadata_collection.delete_many({})
            
            logger.warning("All cache entries have been cleared")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
            return False