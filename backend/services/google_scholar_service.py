"""
Google Scholar integration service for academic paper research
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from scholarly import scholarly, ProxyGenerator
import random
import time

from models.research import SourceResult, SourceType

logger = logging.getLogger(__name__)

class GoogleScholarService:
    """
    Service for integrating with Google Scholar to search academic papers
    
    Provides search functionality with rate limiting, error handling, and retry logic
    """
    
    def __init__(
        self, 
        max_results: int = 20,
        rate_limit_delay: float = 2.0,
        max_retries: int = 3,
        use_proxy: bool = False
    ):
        """
        Initialize Google Scholar service
        
        Args:
            max_results: Maximum number of results to return per search
            rate_limit_delay: Base delay between requests in seconds
            max_retries: Maximum number of retry attempts
            use_proxy: Whether to use proxy rotation (helps avoid rate limiting)
        """
        self.max_results = max_results
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.use_proxy = use_proxy
        self._last_request_time = 0.0
        
        # Initialize proxy if requested
        if self.use_proxy:
            try:
                pg = ProxyGenerator()
                pg.FreeProxies()
                scholarly.use_proxy(pg)
                logger.info("Initialized Google Scholar with proxy rotation")
            except Exception as e:
                logger.warning(f"Failed to initialize proxy for Google Scholar: {e}")
                self.use_proxy = False
    
    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit_delay:
            delay = self.rate_limit_delay - time_since_last
            # Add some jitter to avoid thundering herd
            jitter = random.uniform(0, 0.5)
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
    
    def _parse_publication_date(self, pub_year: Optional[str]) -> Optional[datetime]:
        """
        Parse publication year to datetime
        
        Args:
            pub_year: Publication year as string
            
        Returns:
            Datetime object or None if parsing fails
        """
        if not pub_year:
            return None
        
        try:
            # Handle various year formats
            year_str = str(pub_year).strip()
            if year_str.isdigit() and len(year_str) == 4:
                year = int(year_str)
                if 1900 <= year <= datetime.now().year + 1:
                    return datetime(year, 1, 1)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _extract_paper_data(self, paper: Dict[str, Any]) -> Optional[SourceResult]:
        """
        Extract and normalize paper data from Google Scholar result
        
        Args:
            paper: Raw paper data from scholarly
            
        Returns:
            SourceResult object or None if extraction fails
        """
        try:
            # Extract basic information
            title = paper.get('title', '').strip()
            if not title:
                return None
            
            # Extract authors
            authors = []
            author_data = paper.get('author', [])
            if isinstance(author_data, list):
                authors = [author.get('name', '') for author in author_data if author.get('name')]
            elif isinstance(author_data, str):
                authors = [author_data]
            
            # Extract abstract/snippet
            abstract = paper.get('abstract') or paper.get('snippet')
            if abstract:
                abstract = abstract.strip()
                if not abstract:  # If empty after stripping, set to None
                    abstract = None
            else:
                abstract = None
            
            # Extract URL
            url = paper.get('url') or paper.get('pub_url')
            
            # Extract publication date
            pub_year = paper.get('pub_year') or paper.get('year')
            publication_date = self._parse_publication_date(pub_year)
            
            # Extract citation count
            citation_count = None
            if 'num_citations' in paper:
                try:
                    citation_count = int(paper['num_citations'])
                except (ValueError, TypeError):
                    pass
            
            return SourceResult(
                title=title,
                authors=authors,
                abstract=abstract,
                url=url,
                publication_date=publication_date,
                source_type=SourceType.GOOGLE_SCHOLAR,
                citation_count=citation_count
            )
            
        except Exception as e:
            logger.error(f"Error extracting paper data: {e}")
            return None
    
    async def search_papers(self, query: str) -> List[SourceResult]:
        """
        Search for academic papers on Google Scholar
        
        Args:
            query: Search query string
            
        Returns:
            List of SourceResult objects
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to Google Scholar search")
            return []
        
        results = []
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Searching Google Scholar for: '{query}' (attempt {attempt + 1})")
                
                # Apply rate limiting
                await self._rate_limit()
                
                # Perform search in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                search_query = scholarly.search_pubs(query)
                
                # Collect results
                collected_count = 0
                async for paper in self._async_search_generator(search_query):
                    if collected_count >= self.max_results:
                        break
                    
                    source_result = self._extract_paper_data(paper)
                    if source_result:
                        results.append(source_result)
                        collected_count += 1
                        logger.debug(f"Extracted paper: {source_result.title}")
                
                logger.info(f"Successfully retrieved {len(results)} papers from Google Scholar")
                return results
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Google Scholar search attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = await self._exponential_backoff(attempt)
                    logger.info(f"Retrying Google Scholar search in {delay:.2f} seconds")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All Google Scholar search attempts failed. Last error: {e}")
        
        # If we get here, all attempts failed
        if last_exception:
            logger.error(f"Google Scholar search failed after {self.max_retries} attempts: {last_exception}")
        
        return results
    
    async def _async_search_generator(self, search_query):
        """
        Convert synchronous scholarly generator to async generator
        
        Args:
            search_query: Scholarly search query generator
            
        Yields:
            Paper data dictionaries
        """
        loop = asyncio.get_event_loop()
        
        try:
            # Run the synchronous generator in a thread pool
            def get_next_paper():
                try:
                    return next(search_query)
                except StopIteration:
                    return None
                except Exception as e:
                    logger.error(f"Error getting next paper from scholarly: {e}")
                    return None
            
            while True:
                paper = await loop.run_in_executor(None, get_next_paper)
                if paper is None:
                    break
                yield paper
                
                # Add small delay between papers to be respectful
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in async search generator: {e}")
    
    async def get_paper_details(self, paper_id: str) -> Optional[SourceResult]:
        """
        Get detailed information for a specific paper
        
        Args:
            paper_id: Google Scholar paper ID
            
        Returns:
            Detailed SourceResult or None if not found
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Getting paper details for ID: {paper_id} (attempt {attempt + 1})")
                
                # Apply rate limiting
                await self._rate_limit()
                
                # Get paper details in thread pool
                loop = asyncio.get_event_loop()
                paper = await loop.run_in_executor(
                    None, 
                    lambda: scholarly.search_pubs_query(f'cluster:{paper_id}')
                )
                
                if paper:
                    paper_data = next(paper, None)
                    if paper_data:
                        result = self._extract_paper_data(paper_data)
                        if result:
                            logger.info(f"Successfully retrieved paper details: {result.title}")
                            return result
                
                logger.warning(f"No paper found with ID: {paper_id}")
                return None
                
            except Exception as e:
                logger.warning(f"Paper details attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = await self._exponential_backoff(attempt)
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed to get paper details after {self.max_retries} attempts: {e}")
        
        return None
    
    async def search_by_author(self, author_name: str, max_papers: int = 10) -> List[SourceResult]:
        """
        Search for papers by a specific author
        
        Args:
            author_name: Name of the author to search for
            max_papers: Maximum number of papers to return
            
        Returns:
            List of SourceResult objects
        """
        if not author_name or not author_name.strip():
            logger.warning("Empty author name provided")
            return []
        
        # Use author-specific search query
        query = f'author:"{author_name.strip()}"'
        
        # Temporarily adjust max_results for this search
        original_max = self.max_results
        self.max_results = min(max_papers, self.max_results)
        
        try:
            results = await self.search_papers(query)
            logger.info(f"Found {len(results)} papers by author: {author_name}")
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
            "service": "Google Scholar",
            "max_results": self.max_results,
            "rate_limit_delay": self.rate_limit_delay,
            "max_retries": self.max_retries,
            "use_proxy": self.use_proxy,
            "last_request_time": self._last_request_time,
            "status": "active"
        }