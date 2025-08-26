"""
Example usage of ScienceDirectService for scientific paper research

This example demonstrates how to use the ScienceDirectService to search for
scientific papers, retrieve article details, and handle various search scenarios.

Note: You need a valid Elsevier API key to run this example.
Get one from: https://dev.elsevier.com/
"""
import asyncio
import logging
import os
from typing import List

from services.sciencedirect_service import ScienceDirectService
from models.research import SourceResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def basic_search_example():
    """Example of basic paper search"""
    print("\n=== Basic Search Example ===")
    
    # Initialize service with API key
    # In production, get this from environment variables or config
    api_key = os.getenv('ELSEVIER_API_KEY', 'your_api_key_here')
    
    service = ScienceDirectService(
        api_key=api_key,
        max_results=5,
        rate_limit_delay=1.0
    )
    
    # Search for papers
    query = "machine learning healthcare"
    print(f"Searching for: '{query}'")
    
    try:
        results = await service.search_papers(query)
        
        print(f"Found {len(results)} papers:")
        for i, paper in enumerate(results, 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors)}")
            print(f"   Journal: {paper.journal or 'N/A'}")
            print(f"   DOI: {paper.doi or 'N/A'}")
            print(f"   Access: {paper.access_status or 'N/A'}")
            print(f"   Date: {paper.publication_date.strftime('%Y-%m-%d') if paper.publication_date else 'N/A'}")
            if paper.abstract:
                abstract_preview = paper.abstract[:200] + "..." if len(paper.abstract) > 200 else paper.abstract
                print(f"   Abstract: {abstract_preview}")
    
    except Exception as e:
        print(f"Error during search: {e}")

async def author_search_example():
    """Example of searching by author"""
    print("\n=== Author Search Example ===")
    
    api_key = os.getenv('ELSEVIER_API_KEY', 'your_api_key_here')
    service = ScienceDirectService(api_key=api_key, max_results=3)
    
    author_name = "Smith"  # Common surname for demonstration
    print(f"Searching for papers by author: '{author_name}'")
    
    try:
        results = await service.search_by_author(author_name, max_papers=3)
        
        print(f"Found {len(results)} papers by {author_name}:")
        for i, paper in enumerate(results, 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors)}")
            print(f"   Journal: {paper.journal or 'N/A'}")
            print(f"   DOI: {paper.doi or 'N/A'}")
    
    except Exception as e:
        print(f"Error during author search: {e}")

async def journal_search_example():
    """Example of searching by journal"""
    print("\n=== Journal Search Example ===")
    
    api_key = os.getenv('ELSEVIER_API_KEY', 'your_api_key_here')
    service = ScienceDirectService(api_key=api_key, max_results=3)
    
    journal_name = "Journal of Biomedical Informatics"
    print(f"Searching for papers in journal: '{journal_name}'")
    
    try:
        results = await service.search_by_journal(journal_name, max_papers=3)
        
        print(f"Found {len(results)} papers in {journal_name}:")
        for i, paper in enumerate(results, 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors)}")
            print(f"   DOI: {paper.doi or 'N/A'}")
            print(f"   Access: {paper.access_status or 'N/A'}")
    
    except Exception as e:
        print(f"Error during journal search: {e}")

async def subject_search_example():
    """Example of searching by subject area"""
    print("\n=== Subject Search Example ===")
    
    api_key = os.getenv('ELSEVIER_API_KEY', 'your_api_key_here')
    service = ScienceDirectService(api_key=api_key, max_results=3)
    
    subject = "Computer Science"
    print(f"Searching for papers in subject area: '{subject}'")
    
    try:
        results = await service.search_by_subject(subject, max_papers=3)
        
        print(f"Found {len(results)} papers in {subject}:")
        for i, paper in enumerate(results, 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors)}")
            print(f"   Journal: {paper.journal or 'N/A'}")
            print(f"   DOI: {paper.doi or 'N/A'}")
    
    except Exception as e:
        print(f"Error during subject search: {e}")

async def article_details_example():
    """Example of getting article details by DOI"""
    print("\n=== Article Details Example ===")
    
    api_key = os.getenv('ELSEVIER_API_KEY', 'your_api_key_here')
    service = ScienceDirectService(api_key=api_key)
    
    # Example DOI - replace with a real one for testing
    doi = "10.1016/j.jbi.2023.104123"  # Example DOI
    print(f"Getting details for DOI: {doi}")
    
    try:
        result = await service.get_article_details(doi)
        
        if result:
            print(f"Article found:")
            print(f"Title: {result.title}")
            print(f"Authors: {', '.join(result.authors)}")
            print(f"Journal: {result.journal or 'N/A'}")
            print(f"DOI: {result.doi}")
            print(f"Access: {result.access_status or 'N/A'}")
            print(f"Date: {result.publication_date.strftime('%Y-%m-%d') if result.publication_date else 'N/A'}")
            print(f"URL: {result.url or 'N/A'}")
            if result.abstract:
                print(f"Abstract: {result.abstract[:300]}...")
        else:
            print("Article not found or access denied")
    
    except Exception as e:
        print(f"Error getting article details: {e}")

async def service_status_example():
    """Example of checking service status"""
    print("\n=== Service Status Example ===")
    
    api_key = os.getenv('ELSEVIER_API_KEY', 'your_api_key_here')
    service = ScienceDirectService(api_key=api_key)
    
    status = service.get_service_status()
    
    print("Service Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")

async def error_handling_example():
    """Example of error handling scenarios"""
    print("\n=== Error Handling Example ===")
    
    # Test without API key
    print("1. Testing without API key:")
    service_no_key = ScienceDirectService(api_key=None)
    results = await service_no_key.search_papers("test query")
    print(f"   Results without API key: {len(results)} (should be 0)")
    
    # Test with invalid API key
    print("\n2. Testing with invalid API key:")
    service_invalid = ScienceDirectService(api_key="invalid_key")
    try:
        results = await service_invalid.search_papers("test query")
        print(f"   Results with invalid key: {len(results)}")
    except Exception as e:
        print(f"   Expected error: {type(e).__name__}")
    
    # Test empty queries
    print("\n3. Testing empty queries:")
    api_key = os.getenv('ELSEVIER_API_KEY', 'your_api_key_here')
    service = ScienceDirectService(api_key=api_key)
    
    empty_results = await service.search_papers("")
    print(f"   Empty query results: {len(empty_results)} (should be 0)")
    
    none_results = await service.search_papers(None)
    print(f"   None query results: {len(none_results)} (should be 0)")

async def access_status_example():
    """Example showing different access status types"""
    print("\n=== Access Status Example ===")
    
    api_key = os.getenv('ELSEVIER_API_KEY', 'your_api_key_here')
    service = ScienceDirectService(api_key=api_key, max_results=10)
    
    query = "open access machine learning"
    print(f"Searching for: '{query}' to demonstrate access status")
    
    try:
        results = await service.search_papers(query)
        
        # Group results by access status
        access_groups = {}
        for paper in results:
            status = paper.access_status or "unknown"
            if status not in access_groups:
                access_groups[status] = []
            access_groups[status].append(paper)
        
        print(f"Found {len(results)} papers with access status breakdown:")
        for status, papers in access_groups.items():
            print(f"\n{status.upper()}: {len(papers)} papers")
            for paper in papers[:2]:  # Show first 2 papers in each category
                print(f"  - {paper.title[:60]}...")
    
    except Exception as e:
        print(f"Error during access status search: {e}")

async def main():
    """Run all examples"""
    print("ScienceDirect Service Examples")
    print("=" * 50)
    
    # Check if API key is available
    api_key = os.getenv('ELSEVIER_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("WARNING: No valid API key found!")
        print("Set ELSEVIER_API_KEY environment variable or update the examples.")
        print("Get an API key from: https://dev.elsevier.com/")
        print("\nRunning examples with placeholder key (will show errors)...")
    
    # Run examples
    await basic_search_example()
    await author_search_example()
    await journal_search_example()
    await subject_search_example()
    await article_details_example()
    await service_status_example()
    await error_handling_example()
    await access_status_example()
    
    print("\n" + "=" * 50)
    print("Examples completed!")

if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())