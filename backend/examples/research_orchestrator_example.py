"""
Example usage of the Research Orchestrator service
"""
import asyncio
import logging
from datetime import datetime

from services.research_orchestrator import ResearchOrchestrator
from services.google_scholar_service import GoogleScholarService
from services.google_books_service import GoogleBooksService
from services.sciencedirect_service import ScienceDirectService
from services.agno_ai_service import AgnoAIService
from services.cache_service import CacheService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def basic_research_example():
    """
    Basic example of using the research orchestrator
    """
    print("=== Basic Research Orchestrator Example ===")
    
    # Initialize orchestrator with default services
    orchestrator = ResearchOrchestrator()
    
    # Submit a research query
    query_text = "machine learning in healthcare applications"
    print(f"Submitting research query: '{query_text}'")
    
    query = await orchestrator.submit_research_query(
        query_text=query_text,
        user_id="example_user"
    )
    
    print(f"Query submitted with ID: {query.query_id}")
    print(f"Query status: {query.status}")
    
    # Process the research query
    print("Processing research query...")
    result = await orchestrator.process_research_query(query.query_id)
    
    print(f"Research completed!")
    print(f"Query ID: {result.query_id}")
    print(f"Cached result: {result.cached}")
    print(f"AI Summary: {result.ai_summary}")
    print(f"Confidence Score: {result.confidence_score}")
    
    # Display results by source
    for source_type, source_results in result.results.items():
        print(f"\n{source_type.upper()} Results: {len(source_results)} items")
        for i, source_result in enumerate(source_results[:3], 1):  # Show first 3
            print(f"  {i}. {source_result.title}")
            print(f"     Authors: {', '.join(source_result.authors)}")
            if source_result.abstract:
                print(f"     Abstract: {source_result.abstract[:100]}...")

async def custom_services_example():
    """
    Example using custom configured services
    """
    print("\n=== Custom Services Configuration Example ===")
    
    # Initialize services with custom configurations
    scholar_service = GoogleScholarService(
        max_results=10,
        rate_limit_delay=1.5,
        use_proxy=False
    )
    
    books_service = GoogleBooksService(
        api_key=None,  # Use without API key for demo
        max_results=15,
        rate_limit_delay=1.0
    )
    
    sciencedirect_service = ScienceDirectService(
        api_key=None,  # Would need real API key for actual use
        max_results=10,
        rate_limit_delay=2.0
    )
    
    agno_service = AgnoAIService(model_name="gpt-4")
    cache_service = CacheService(default_ttl_hours=48)
    
    # Initialize orchestrator with custom services
    orchestrator = ResearchOrchestrator(
        google_scholar_service=scholar_service,
        google_books_service=books_service,
        sciencedirect_service=sciencedirect_service,
        agno_ai_service=agno_service,
        cache_service=cache_service,
        max_concurrent_requests=5,
        timeout_seconds=60
    )
    
    # Get service health status
    health = await orchestrator.get_service_health()
    print("Service Health Status:")
    for service_name, status in health.items():
        print(f"  {service_name}: {status.get('status', 'unknown')}")
    
    # Submit and process a query
    query = await orchestrator.submit_research_query(
        "artificial intelligence ethics frameworks"
    )
    
    print(f"\nProcessing query: {query.query_id}")
    result = await orchestrator.process_research_query(query.query_id)
    
    print(f"Results summary:")
    total_results = sum(len(results) for results in result.results.values())
    print(f"  Total results: {total_results}")
    print(f"  AI confidence: {result.confidence_score}")

async def author_search_example():
    """
    Example of searching by author across all sources
    """
    print("\n=== Author Search Example ===")
    
    orchestrator = ResearchOrchestrator()
    
    author_name = "Geoffrey Hinton"
    print(f"Searching for works by: {author_name}")
    
    results = await orchestrator.search_by_author(
        author_name=author_name,
        max_results_per_source=5
    )
    
    print(f"Author search results:")
    for source_type, source_results in results.items():
        print(f"\n{source_type.upper()}: {len(source_results)} results")
        for i, result in enumerate(source_results, 1):
            print(f"  {i}. {result.title}")
            if result.publication_date:
                print(f"     Year: {result.publication_date.year}")

async def concurrent_queries_example():
    """
    Example of processing multiple queries concurrently
    """
    print("\n=== Concurrent Queries Example ===")
    
    orchestrator = ResearchOrchestrator()
    
    queries = [
        "deep learning neural networks",
        "quantum computing algorithms",
        "blockchain technology applications"
    ]
    
    print(f"Submitting {len(queries)} concurrent queries...")
    
    # Submit all queries
    submitted_queries = []
    for query_text in queries:
        query = await orchestrator.submit_research_query(query_text)
        submitted_queries.append(query)
        print(f"  Submitted: {query.query_id} - '{query_text}'")
    
    # Process all queries concurrently
    print("Processing queries concurrently...")
    start_time = datetime.now()
    
    results = await asyncio.gather(*[
        orchestrator.process_research_query(query.query_id)
        for query in submitted_queries
    ])
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    print(f"All queries processed in {processing_time:.2f} seconds")
    
    for i, result in enumerate(results):
        total_results = sum(len(source_results) for source_results in result.results.values())
        print(f"  Query {i+1}: {total_results} total results, confidence: {result.confidence_score}")

async def error_handling_example():
    """
    Example demonstrating error handling and partial results
    """
    print("\n=== Error Handling Example ===")
    
    # Create orchestrator with very short timeout to simulate failures
    orchestrator = ResearchOrchestrator(timeout_seconds=0.1)
    
    query = await orchestrator.submit_research_query(
        "complex research query that might timeout"
    )
    
    print(f"Processing query with short timeout: {query.query_id}")
    
    try:
        result = await orchestrator.process_research_query(query.query_id)
        
        # Even with timeouts/failures, we should get partial results
        print("Research completed (possibly with partial results)")
        
        for source_type, source_results in result.results.items():
            status = "success" if source_results else "failed/empty"
            print(f"  {source_type}: {len(source_results)} results ({status})")
        
        if result.ai_summary:
            print(f"  AI Summary available: {len(result.ai_summary)} characters")
        else:
            print("  No AI summary (likely due to processing issues)")
            
    except Exception as e:
        print(f"Query processing failed: {e}")

async def cache_demonstration():
    """
    Demonstrate caching functionality
    """
    print("\n=== Cache Demonstration ===")
    
    orchestrator = ResearchOrchestrator()
    
    query_text = "natural language processing transformers"
    
    # First query - should miss cache
    print("First query (cache miss expected)...")
    query1 = await orchestrator.submit_research_query(query_text)
    start_time = datetime.now()
    result1 = await orchestrator.process_research_query(query1.query_id)
    first_time = (datetime.now() - start_time).total_seconds()
    
    print(f"  First query completed in {first_time:.2f}s")
    print(f"  Cached: {result1.cached}")
    
    # Second identical query - should hit cache
    print("Second identical query (cache hit expected)...")
    query2 = await orchestrator.submit_research_query(query_text)
    start_time = datetime.now()
    result2 = await orchestrator.process_research_query(query2.query_id)
    second_time = (datetime.now() - start_time).total_seconds()
    
    print(f"  Second query completed in {second_time:.2f}s")
    print(f"  Cached: {result2.cached}")
    print(f"  Speed improvement: {(first_time / second_time):.1f}x faster")

async def statistics_example():
    """
    Example of getting research statistics
    """
    print("\n=== Research Statistics Example ===")
    
    orchestrator = ResearchOrchestrator()
    
    # Process a few queries first
    queries = ["AI research", "machine learning", "data science"]
    for query_text in queries:
        query = await orchestrator.submit_research_query(query_text)
        await orchestrator.process_research_query(query.query_id)
    
    # Get statistics
    stats = await orchestrator.get_research_statistics()
    
    print("Research Statistics:")
    if "cache_statistics" in stats:
        cache_stats = stats["cache_statistics"]
        print(f"  Cache entries: {cache_stats.get('total_entries', 0)}")
        print(f"  Active entries: {cache_stats.get('active_entries', 0)}")
        print(f"  Cache hit rate: {cache_stats.get('cache_hit_rate_percent', 0)}%")
    
    if "service_configuration" in stats:
        config = stats["service_configuration"]
        print(f"  Max concurrent requests: {config.get('max_concurrent_requests', 0)}")
        print(f"  Timeout: {config.get('timeout_seconds', 0)}s")

async def main():
    """
    Run all examples
    """
    print("Research Orchestrator Examples")
    print("=" * 50)
    
    try:
        await basic_research_example()
        await custom_services_example()
        await author_search_example()
        await concurrent_queries_example()
        await error_handling_example()
        await cache_demonstration()
        await statistics_example()
        
    except Exception as e:
        logger.error(f"Example execution failed: {e}")
        print(f"Error running examples: {e}")
    
    print("\n" + "=" * 50)
    print("Examples completed!")

if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())