"""
Example usage of the CacheService for research query caching
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.cache_service import CacheService
from models.research import ResearchResult, SourceResult, SourceType

async def main():
    """Example usage of the cache service"""
    
    # Initialize cache service with 24-hour TTL
    cache_service = CacheService(default_ttl_hours=24)
    
    # Example query
    query = "Machine Learning Algorithms"
    
    print(f"Original query: '{query}'")
    print(f"Normalized query: '{cache_service.normalize_query(query)}'")
    print(f"Cache key: '{cache_service.generate_cache_key(query)}'")
    
    # Test query normalization with different variations
    variations = [
        "Machine Learning Algorithms",
        "machine learning algorithms",
        "Algorithms Machine Learning",
        "The Machine Learning and Algorithms",
        "Machine    Learning,   Algorithms!"
    ]
    
    print("\nQuery normalization examples:")
    for variation in variations:
        normalized = cache_service.normalize_query(variation)
        cache_key = cache_service.generate_cache_key(variation)
        print(f"  '{variation}' -> '{normalized}' -> {cache_key}")
    
    # Create sample research result
    source_results = [
        SourceResult(
            title="Deep Learning with Python",
            authors=["François Chollet"],
            abstract="A comprehensive guide to deep learning with Python",
            source_type=SourceType.GOOGLE_BOOKS,
            isbn="9781617294433"
        ),
        SourceResult(
            title="Attention Is All You Need",
            authors=["Ashish Vaswani", "Noam Shazeer"],
            abstract="The Transformer model architecture",
            source_type=SourceType.GOOGLE_SCHOLAR,
            citation_count=15000
        )
    ]
    
    research_result = ResearchResult(
        query_id="example-query-123",
        results={
            "google_books": [source_results[0]],
            "google_scholar": [source_results[1]]
        },
        ai_summary="This research covers machine learning algorithms with focus on deep learning and transformer architectures.",
        confidence_score=0.92,
        cached=False
    )
    
    print(f"\nCreated sample research result with {len(research_result.results)} source types")
    print(f"AI Summary: {research_result.ai_summary}")
    print(f"Confidence Score: {research_result.confidence_score}")
    
    # Note: In a real application, you would:
    # 1. Check cache first: cached_result = await cache_service.get_cached_result(query)
    # 2. If not cached, perform research and then store: await cache_service.store_result(query, result)
    # 3. Periodically clean up: await cache_service.cleanup_expired_cache()
    # 4. Monitor cache stats: stats = await cache_service.get_cache_stats()
    
    print("\nCache service methods available:")
    methods = [
        "get_cached_result(query) - Retrieve cached result",
        "store_result(query, result, ttl_hours) - Store result in cache",
        "invalidate_cache(query) - Remove specific cached result",
        "cleanup_expired_cache() - Remove expired entries",
        "get_cache_stats() - Get cache statistics",
        "clear_all_cache() - Clear all cached entries"
    ]
    
    for method in methods:
        print(f"  - {method}")

if __name__ == "__main__":
    asyncio.run(main())