"""
Google Books integration service for book research
"""
import asyncio
import logging
import aiohttp
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus
import random
import time

from models.research import SourceResult, SourceType

logger = logging.getLogger(__name__)

class GoogleBooksService:
    """
    Service for integrating with Google Books API to search books
    
    Provides search functionality with rate limiting, error handling, and retry logic
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        max_results: int = 20,
        rate_limit_delay: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize Google Books service
        
        Args:
            api_key: Google Books API key (optional, but recommended for higher limits)
            max_results: Maximum number of results to return per search
            rate_limit_delay: Base delay between requests in seconds
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.max_results = min(max_results, 40)  # Google Books API limit
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self._last_request_time = 0.0
        
        # Google Books API base URL
        self.base_url = "https://www.googleapis.com/books/v1/volumes"
        
        logger.info(f"Initialized Google Books service with max_results={self.max_results}")
    
    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit_delay:
            delay = self.rate_limit_delay - time_since_last
            # Add some jitter to avoid thundering herd
            jitter = random.uniform(0, 0.3)
            await asyncio.sleep(delay + jitter)
        
        self._last_request_time = time.time()
    
    async def _exponential_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        base_delay = 1.0
        max_delay = 60.0
        delay = min(base_delay * (2 ** attempt), max_delay)
        # Add jitter
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter
    
    def _parse_publication_date(self, published_date: Optional[str]) -> Optional[datetime]:
        """
        Parse publication date from various formats
        
        Args:
            published_date: Publication date string from Google Books
            
        Returns:
            Datetime object or None if parsing fails
        """
        if not published_date:
            return None
        
        try:
            date_str = str(published_date).strip()
            
            # Try different date formats
            date_formats = [
                "%Y-%m-%d",      # 2023-01-15
                "%Y-%m",         # 2023-01
                "%Y",            # 2023
                "%m/%d/%Y",      # 01/15/2023
                "%B %d, %Y",     # January 15, 2023
                "%B %Y",         # January 2023
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    # Validate year range
                    if 1000 <= parsed_date.year <= datetime.now().year:
                        return parsed_date
                except ValueError:
                    continue
            
            # If all formats fail, try to extract just the year
            if date_str.isdigit() and len(date_str) == 4:
                year = int(date_str)
                if 1000 <= year <= datetime.now().year:
                    return datetime(year, 1, 1)
                    
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _extract_book_data(self, book_item: Dict[str, Any]) -> Optional[SourceResult]:
        """
        Extract and normalize book data from Google Books API result
        
        Args:
            book_item: Raw book data from Google Books API
            
        Returns:
            SourceResult object or None if extraction fails
        """
        try:
            volume_info = book_item.get('volumeInfo', {})
            
            # Extract basic information
            title = volume_info.get('title', '').strip()
            if not title:
                return None
            
            # Extract authors
            authors = volume_info.get('authors', [])
            if not isinstance(authors, list):
                authors = [str(authors)] if authors else []
            
            # Extract description/abstract
            description = volume_info.get('description')
            if description:
                description = description.strip()
                # Truncate very long descriptions
                if len(description) > 1000:
                    description = description[:997] + "..."
                if not description:  # If empty after stripping
                    description = None
            else:
                description = None
            
            # Extract URLs
            info_link = volume_info.get('infoLink')
            preview_link = volume_info.get('previewLink')
            canonical_link = volume_info.get('canonicalVolumeLink')
            
            # Prefer canonical link, then info link
            url = canonical_link or info_link
            
            # Extract publication date
            published_date = volume_info.get('publishedDate')
            publication_date = self._parse_publication_date(published_date)
            
            # Extract ISBN (prefer ISBN_13 over ISBN_10)
            isbn = None
            industry_identifiers = volume_info.get('industryIdentifiers', [])
            isbn_13 = None
            isbn_10 = None
            
            for identifier in industry_identifiers:
                if identifier.get('type') == 'ISBN_13':
                    isbn_13 = identifier.get('identifier')
                elif identifier.get('type') == 'ISBN_10':
                    isbn_10 = identifier.get('identifier')
            
            # Prefer ISBN_13 over ISBN_10
            isbn = isbn_13 or isbn_10
            
            return SourceResult(
                title=title,
                authors=authors,
                abstract=description,
                url=url,
                publication_date=publication_date,
                source_type=SourceType.GOOGLE_BOOKS,
                isbn=isbn,
                preview_link=preview_link
            )
            
        except Exception as e:
            logger.error(f"Error extracting book data: {e}")
            return None
    
    def _build_search_url(self, query: str, start_index: int = 0) -> str:
        """
        Build Google Books API search URL
        
        Args:
            query: Search query string
            start_index: Starting index for pagination
            
        Returns:
            Complete API URL
        """
        encoded_query = quote_plus(query)
        url = f"{self.base_url}?q={encoded_query}&maxResults={self.max_results}&startIndex={start_index}"
        
        if self.api_key:
            url += f"&key={self.api_key}"
        
        return url
    
    async def _make_api_request(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to Google Books API
        
        Args:
            url: API URL to request
            
        Returns:
            JSON response data or None if request fails
        """
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        # Rate limited
                        logger.warning("Google Books API rate limit exceeded")
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=429,
                            message="Rate limit exceeded"
                        )
                    else:
                        logger.error(f"Google Books API error: {response.status}")
                        response.raise_for_status()
                        
        except asyncio.TimeoutError:
            logger.error("Google Books API request timeout")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Google Books API client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Google Books API request: {e}")
            raise
        
        return None
    
    async def search_books(self, query: str) -> List[SourceResult]:
        """
        Search for books on Google Books
        
        Args:
            query: Search query string
            
        Returns:
            List of SourceResult objects
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to Google Books search")
            return []
        
        results = []
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Searching Google Books for: '{query}' (attempt {attempt + 1})")
                
                # Apply rate limiting
                await self._rate_limit()
                
                # Build search URL
                search_url = self._build_search_url(query.strip())
                
                # Make API request
                response_data = await self._make_api_request(search_url)
                
                if not response_data:
                    logger.warning("No response data from Google Books API")
                    continue
                
                # Extract books from response
                items = response_data.get('items', [])
                total_items = response_data.get('totalItems', 0)
                
                logger.info(f"Google Books API returned {len(items)} items (total: {total_items})")
                
                # Process each book item
                for item in items:
                    book_result = self._extract_book_data(item)
                    if book_result:
                        results.append(book_result)
                        logger.debug(f"Extracted book: {book_result.title}")
                
                logger.info(f"Successfully retrieved {len(results)} books from Google Books")
                return results
                
            except aiohttp.ClientResponseError as e:
                if e.status == 429:  # Rate limit
                    last_exception = e
                    logger.warning(f"Google Books rate limit hit on attempt {attempt + 1}")
                    
                    if attempt < self.max_retries - 1:
                        delay = await self._exponential_backoff(attempt)
                        logger.info(f"Retrying Google Books search in {delay:.2f} seconds")
                        await asyncio.sleep(delay)
                    else:
                        logger.error("Google Books rate limit exceeded all retry attempts")
                else:
                    last_exception = e
                    logger.error(f"Google Books API error {e.status} on attempt {attempt + 1}: {e}")
                    break  # Don't retry on non-rate-limit errors
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Google Books search attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = await self._exponential_backoff(attempt)
                    logger.info(f"Retrying Google Books search in {delay:.2f} seconds")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All Google Books search attempts failed. Last error: {e}")
        
        # If we get here, all attempts failed
        if last_exception:
            logger.error(f"Google Books search failed after {self.max_retries} attempts: {last_exception}")
        
        return results
    
    async def get_book_details(self, volume_id: str) -> Optional[SourceResult]:
        """
        Get detailed information for a specific book
        
        Args:
            volume_id: Google Books volume ID
            
        Returns:
            Detailed SourceResult or None if not found
        """
        if not volume_id or not volume_id.strip():
            logger.warning("Empty volume ID provided")
            return None
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Getting book details for volume ID: {volume_id} (attempt {attempt + 1})")
                
                # Apply rate limiting
                await self._rate_limit()
                
                # Build details URL
                details_url = f"{self.base_url}/{volume_id.strip()}"
                if self.api_key:
                    details_url += f"?key={self.api_key}"
                
                # Make API request
                response_data = await self._make_api_request(details_url)
                
                if response_data:
                    book_result = self._extract_book_data(response_data)
                    if book_result:
                        logger.info(f"Successfully retrieved book details: {book_result.title}")
                        return book_result
                
                logger.warning(f"No book found with volume ID: {volume_id}")
                return None
                
            except aiohttp.ClientResponseError as e:
                if e.status == 404:
                    logger.warning(f"Book not found with volume ID: {volume_id}")
                    return None
                elif e.status == 429:
                    last_exception = e
                    logger.warning(f"Google Books rate limit hit on attempt {attempt + 1}")
                    
                    if attempt < self.max_retries - 1:
                        delay = await self._exponential_backoff(attempt)
                        await asyncio.sleep(delay)
                    else:
                        logger.error("Google Books rate limit exceeded all retry attempts")
                else:
                    last_exception = e
                    logger.error(f"Google Books API error {e.status}: {e}")
                    break
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Book details attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = await self._exponential_backoff(attempt)
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed to get book details after {self.max_retries} attempts: {e}")
        
        return None
    
    async def search_by_author(self, author_name: str, max_books: int = 10) -> List[SourceResult]:
        """
        Search for books by a specific author
        
        Args:
            author_name: Name of the author to search for
            max_books: Maximum number of books to return
            
        Returns:
            List of SourceResult objects
        """
        if not author_name or not author_name.strip():
            logger.warning("Empty author name provided")
            return []
        
        # Use author-specific search query
        query = f'inauthor:"{author_name.strip()}"'
        
        # Temporarily adjust max_results for this search
        original_max = self.max_results
        self.max_results = min(max_books, self.max_results)
        
        try:
            results = await self.search_books(query)
            logger.info(f"Found {len(results)} books by author: {author_name}")
            return results
        finally:
            # Restore original max_results
            self.max_results = original_max
    
    async def search_by_subject(self, subject: str, max_books: int = 10) -> List[SourceResult]:
        """
        Search for books by subject/category
        
        Args:
            subject: Subject or category to search for
            max_books: Maximum number of books to return
            
        Returns:
            List of SourceResult objects
        """
        if not subject or not subject.strip():
            logger.warning("Empty subject provided")
            return []
        
        # Use subject-specific search query
        query = f'subject:"{subject.strip()}"'
        
        # Temporarily adjust max_results for this search
        original_max = self.max_results
        self.max_results = min(max_books, self.max_results)
        
        try:
            results = await self.search_books(query)
            logger.info(f"Found {len(results)} books on subject: {subject}")
            return results
        finally:
            # Restore original max_results
            self.max_results = original_max
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get current service status and configuration
        
        Returns:
            Dictionary with service status information
        """
        return {
            "service": "Google Books",
            "max_results": self.max_results,
            "rate_limit_delay": self.rate_limit_delay,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "has_api_key": bool(self.api_key),
            "last_request_time": self._last_request_time,
            "status": "active"
        }