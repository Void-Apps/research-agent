"""
Example usage of Google Books integration service
"""
import asyncio
import logging
from services.google_books_service import GoogleBooksService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Example usage of Google Books service"""
    
    # Initialize the service (without API key for this example)
    # In production, you should provide an API key for higher rate limits
    service = GoogleBooksService(
        api_key=None,  # Set to your Google Books API key
        max_results=5,
        rate_limit_delay=1.0,
        max_retries=3
    )
    
    print("Google Books Service Example")
    print("=" * 40)
    
    # Example 1: Basic book search
    print("\n1. Searching for books about 'machine learning'...")
    try:
        results = await service.search_books("machine learning")
        print(f"Found {len(results)} books:")
        
        for i, book in enumerate(results[:3], 1):  # Show first 3 results
            print(f"\n{i}. {book.title}")
            print(f"   Authors: {', '.join(book.authors)}")
            if book.publication_date:
                print(f"   Published: {book.publication_date.year}")
            if book.isbn:
                print(f"   ISBN: {book.isbn}")
            if book.abstract:
                abstract = book.abstract[:200] + "..." if len(book.abstract) > 200 else book.abstract
                print(f"   Description: {abstract}")
            if book.url:
                print(f"   URL: {book.url}")
                
    except Exception as e:
        print(f"Error searching books: {e}")
    
    # Example 2: Search by author
    print("\n\n2. Searching for books by 'Andrew Ng'...")
    try:
        results = await service.search_by_author("Andrew Ng", max_books=3)
        print(f"Found {len(results)} books by Andrew Ng:")
        
        for i, book in enumerate(results, 1):
            print(f"\n{i}. {book.title}")
            print(f"   Authors: {', '.join(book.authors)}")
            if book.publication_date:
                print(f"   Published: {book.publication_date.year}")
                
    except Exception as e:
        print(f"Error searching books by author: {e}")
    
    # Example 3: Search by subject
    print("\n\n3. Searching for books on 'artificial intelligence'...")
    try:
        results = await service.search_by_subject("artificial intelligence", max_books=3)
        print(f"Found {len(results)} books on artificial intelligence:")
        
        for i, book in enumerate(results, 1):
            print(f"\n{i}. {book.title}")
            print(f"   Authors: {', '.join(book.authors)}")
            if book.publication_date:
                print(f"   Published: {book.publication_date.year}")
                
    except Exception as e:
        print(f"Error searching books by subject: {e}")
    
    # Example 4: Service status
    print("\n\n4. Service Status:")
    status = service.get_service_status()
    for key, value in status.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())