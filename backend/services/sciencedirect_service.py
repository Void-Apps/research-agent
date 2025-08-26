"""
ScienceDirect integration service for scientific paper research
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

class ScienceDirectService:
    """
    Service for integrating with ScienceDirect (Elsevier) API to search scientific papers
    
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
        Initialize ScienceDirect service
        
        Args:
            api_key: Elsevier API key (required for API access)
            max_results: Maximum number of results to return per search
            rate_limit_delay: Base delay between requests in seconds
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.max_results = min(max_results, 100)  # Elsevier API limit
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self._last_request_time = 0.0
        
        # Elsevier API base URLs
        self.search_url = "https://api.elsevier.com/content/search/sciencedirect"
        self.article_url = "https://api.elsevier.com/content/article"
        
        # Default headers
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'AI-Research-Agent/1.0'
        }
        
        if self.api_key:
            self.headers['X-ELS-APIKey'] = self.api_key
        
        logger.info(f"Initialized ScienceDirect service with max_results={self.max_results}")
    
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
    
    def _parse_publication_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse publication date from various formats
        
        Args:
            date_str: Publication date string from ScienceDirect
            
        Returns:
            Datetime object or None if parsing fails
        """
        if not date_str:
            return None
        
        try:
            date_str = str(date_str).strip()
            
            # Try different date formats used by Elsevier
            date_formats = [
                "%Y-%m-%d",          # 2023-01-15
                "%Y-%m",             # 2023-01
                "%Y",                # 2023
                "%d %B %Y",          # 15 January 2023
                "%B %Y",             # January 2023
                "%Y/%m/%d",          # 2023/01/15
                "%d/%m/%Y",          # 15/01/2023
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    # Validate year range
                    if 1900 <= parsed_date.year <= datetime.now().year + 1:
                        return parsed_date
                except ValueError:
                    continue
            
            # If all formats fail, try to extract just the year
            if date_str.isdigit() and len(date_str) == 4:
                year = int(date_str)
                if 1900 <= year <= datetime.now().year + 1:
                    return datetime(year, 1, 1)
                    
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _extract_access_status(self, entry: Dict[str, Any]) -> str:
        """
        Extract access status from ScienceDirect entry
        
        Args:
            entry: Raw entry data from ScienceDirect API
            
        Returns:
            Access status string
        """
        # Check for open access indicators
        open_access = entry.get('openaccess', False)
        if open_access:
            return "open_access"
        
        # Check for subscription access
        if entry.get('link'):
            links = entry['link'] if isinstance(entry['link'], list) else [entry['link']]
            for link in links:
                if isinstance(link, dict) and link.get('@rel') == 'scidir':
                    return "subscription_required"
        
        # Check for free access
        if entry.get('prism:url'):
            return "available"
        
        return "restricted"
    
    def _extract_paper_data(self, entry: Dict[str, Any]) -> Optional[SourceResult]:
        """
        Extract and normalize paper data from ScienceDirect API result
        
        Args:
            entry: Raw entry data from ScienceDirect API
            
        Returns:
            SourceResult object or None if extraction fails
        """
        try:
            # Extract basic information
            title = entry.get('dc:title', '').strip()
            if not title:
                return None
            
            # Extract authors
            authors = []
            author_data = entry.get('authors', {}).get('author', [])
            if not isinstance(author_data, list):
                author_data = [author_data] if author_data else []
            
            for author in author_data:
                if isinstance(author, dict):
                    given_name = author.get('given-name', '')
                    surname = author.get('surname', '')
                    if given_name and surname:
                        authors.append(f"{given_name} {surname}")
                    elif surname:
                        authors.append(surname)
                elif isinstance(author, str):
                    authors.append(author)
            
            # Extract abstract/description
            abstract = entry.get('dc:description') or entry.get('prism:teaser')
            if abstract:
                abstract = abstract.strip()
                # Truncate very long abstracts
                if len(abstract) > 2000:
                    abstract = abstract[:1997] + "..."
                if not abstract:  # If empty after stripping
                    abstract = None
            else:
                abstract = None
            
            # Extract DOI
            doi = entry.get('prism:doi')
            if doi is not None:
                doi = doi.strip()
                if not doi:  # Empty after stripping
                    doi = None
                elif not doi.startswith('10.'):
                    # Sometimes DOI comes without the prefix
                    if '/' in doi:
                        doi = f"10.{doi}"
                    else:
                        doi = None
            else:
                doi = None
            
            # Extract journal information
            journal = entry.get('prism:publicationName') or entry.get('dc:source')
            
            # Extract URL
            url = None
            if entry.get('link'):
                links = entry['link'] if isinstance(entry['link'], list) else [entry['link']]
                for link in links:
                    if isinstance(link, dict):
                        if link.get('@rel') == 'scidir':
                            url = link.get('@href')
                            break
            
            # Fallback to prism:url
            if not url:
                url = entry.get('prism:url')
            
            # Extract publication date
            pub_date = (entry.get('prism:coverDate') or 
                       entry.get('prism:publicationDate') or 
                       entry.get('dc:date'))
            publication_date = self._parse_publication_date(pub_date)
            
            # Extract access status
            access_status = self._extract_access_status(entry)
            
            return SourceResult(
                title=title,
                authors=authors,
                abstract=abstract,
                url=url,
                publication_date=publication_date,
                source_type=SourceType.SCIENCEDIRECT,
                doi=doi,
                journal=journal,
                access_status=access_status
            )
            
        except Exception as e:
            logger.error(f"Error extracting ScienceDirect paper data: {e}")
            return None
    
    def _build_search_url(self, query: str, start: int = 0) -> str:
        """
        Build ScienceDirect API search URL
        
        Args:
            query: Search query string
            start: Starting index for pagination
            
        Returns:
            Complete API URL
        """
        encoded_query = quote_plus(query)
        url = f"{self.search_url}?query={encoded_query}&count={self.max_results}&start={start}"
        
        # Add additional parameters
        url += "&view=COMPLETE&field=title,authors,abstract,doi,publicationName,coverDate,openaccess,link"
        
        return url
    
    async def _make_api_request(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to ScienceDirect API
        
        Args:
            url: API URL to request
            
        Returns:
            JSON response data or None if request fails
        """
        if not self.api_key:
            logger.error("ScienceDirect API key is required but not provided")
            raise ValueError("API key is required for ScienceDirect access")
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout, headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        logger.error("ScienceDirect API authentication failed - check API key")
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=401,
                            message="Authentication failed"
                        )
                    elif response.status == 429:
                        # Rate limited
                        logger.warning("ScienceDirect API rate limit exceeded")
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=429,
                            message="Rate limit exceeded"
                        )
                    elif response.status == 403:
                        logger.error("ScienceDirect API access forbidden - check API key permissions")
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=403,
                            message="Access forbidden"
                        )
                    else:
                        logger.error(f"ScienceDirect API error: {response.status}")
                        response.raise_for_status()
                        
        except asyncio.TimeoutError:
            logger.error("ScienceDirect API request timeout")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"ScienceDirect API client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in ScienceDirect API request: {e}")
            raise
        
        return None
    
    async def search_papers(self, query: str) -> List[SourceResult]:
        """
        Search for scientific papers on ScienceDirect
        
        Args:
            query: Search query string
            
        Returns:
            List of SourceResult objects
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to ScienceDirect search")
            return []
        
        if not self.api_key:
            logger.error("ScienceDirect API key is required but not provided")
            return []
        
        results = []
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Searching ScienceDirect for: '{query}' (attempt {attempt + 1})")
                
                # Apply rate limiting
                await self._rate_limit()
                
                # Build search URL
                search_url = self._build_search_url(query.strip())
                
                # Make API request
                response_data = await self._make_api_request(search_url)
                
                if not response_data:
                    logger.warning("No response data from ScienceDirect API")
                    continue
                
                # Extract search results
                search_results = response_data.get('search-results', {})
                entries = search_results.get('entry', [])
                total_results = int(search_results.get('opensearch:totalResults', 0))
                
                logger.info(f"ScienceDirect API returned {len(entries)} entries (total: {total_results})")
                
                # Process each entry
                for entry in entries:
                    paper_result = self._extract_paper_data(entry)
                    if paper_result:
                        results.append(paper_result)
                        logger.debug(f"Extracted paper: {paper_result.title}")
                
                logger.info(f"Successfully retrieved {len(results)} papers from ScienceDirect")
                return results
                
            except aiohttp.ClientResponseError as e:
                if e.status == 429:  # Rate limit
                    last_exception = e
                    logger.warning(f"ScienceDirect rate limit hit on attempt {attempt + 1}")
                    
                    if attempt < self.max_retries - 1:
                        delay = await self._exponential_backoff(attempt)
                        logger.info(f"Retrying ScienceDirect search in {delay:.2f} seconds")
                        await asyncio.sleep(delay)
                    else:
                        logger.error("ScienceDirect rate limit exceeded all retry attempts")
                elif e.status in [401, 403]:  # Auth errors
                    last_exception = e
                    logger.error(f"ScienceDirect authentication error {e.status}: {e}")
                    break  # Don't retry on auth errors
                else:
                    last_exception = e
                    logger.error(f"ScienceDirect API error {e.status} on attempt {attempt + 1}: {e}")
                    if attempt < self.max_retries - 1:
                        delay = await self._exponential_backoff(attempt)
                        logger.info(f"Retrying ScienceDirect search in {delay:.2f} seconds")
                        await asyncio.sleep(delay)
                    else:
                        logger.error("ScienceDirect API error exceeded all retry attempts")
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"ScienceDirect search attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = await self._exponential_backoff(attempt)
                    logger.info(f"Retrying ScienceDirect search in {delay:.2f} seconds")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All ScienceDirect search attempts failed. Last error: {e}")
        
        # If we get here, all attempts failed
        if last_exception:
            logger.error(f"ScienceDirect search failed after {self.max_retries} attempts: {last_exception}")
        
        return results
    
    async def get_article_details(self, doi: str) -> Optional[SourceResult]:
        """
        Get detailed information for a specific article by DOI
        
        Args:
            doi: DOI of the article
            
        Returns:
            Detailed SourceResult or None if not found
        """
        if not doi or not doi.strip():
            logger.warning("Empty DOI provided")
            return None
        
        if not self.api_key:
            logger.error("ScienceDirect API key is required but not provided")
            return None
        
        # Clean DOI
        clean_doi = doi.strip()
        if not clean_doi.startswith('10.'):
            logger.warning(f"Invalid DOI format: {clean_doi}")
            return None
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Getting article details for DOI: {clean_doi} (attempt {attempt + 1})")
                
                # Apply rate limiting
                await self._rate_limit()
                
                # Build article URL
                article_url = f"{self.article_url}/doi/{clean_doi}"
                article_url += "?view=FULL&field=title,authors,abstract,doi,publicationName,coverDate,openaccess"
                
                # Make API request
                response_data = await self._make_api_request(article_url)
                
                if response_data:
                    # Extract article data
                    full_text_retrieval = response_data.get('full-text-retrieval-response', {})
                    core_data = full_text_retrieval.get('coredata', {})
                    
                    if core_data:
                        # Convert to entry format for extraction
                        entry = {
                            'dc:title': core_data.get('dc:title'),
                            'authors': full_text_retrieval.get('authors', {}),
                            'dc:description': core_data.get('dc:description'),
                            'prism:doi': core_data.get('prism:doi'),
                            'prism:publicationName': core_data.get('prism:publicationName'),
                            'prism:coverDate': core_data.get('prism:coverDate'),
                            'openaccess': core_data.get('openaccess'),
                            'prism:url': core_data.get('prism:url')
                        }
                        
                        result = self._extract_paper_data(entry)
                        if result:
                            logger.info(f"Successfully retrieved article details: {result.title}")
                            return result
                
                logger.warning(f"No article found with DOI: {clean_doi}")
                return None
                
            except aiohttp.ClientResponseError as e:
                if e.status == 404:
                    logger.warning(f"Article not found with DOI: {clean_doi}")
                    return None
                elif e.status == 429:
                    last_exception = e
                    logger.warning(f"ScienceDirect rate limit hit on attempt {attempt + 1}")
                    
                    if attempt < self.max_retries - 1:
                        delay = await self._exponential_backoff(attempt)
                        await asyncio.sleep(delay)
                    else:
                        logger.error("ScienceDirect rate limit exceeded all retry attempts")
                elif e.status in [401, 403]:
                    last_exception = e
                    logger.error(f"ScienceDirect authentication error {e.status}: {e}")
                    break
                else:
                    last_exception = e
                    logger.error(f"ScienceDirect API error {e.status}: {e}")
                    break
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Article details attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = await self._exponential_backoff(attempt)
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed to get article details after {self.max_retries} attempts: {e}")
        
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
        query = f'AUTH("{author_name.strip()}")'
        
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
    
    async def search_by_journal(self, journal_name: str, max_papers: int = 10) -> List[SourceResult]:
        """
        Search for papers in a specific journal
        
        Args:
            journal_name: Name of the journal to search in
            max_papers: Maximum number of papers to return
            
        Returns:
            List of SourceResult objects
        """
        if not journal_name or not journal_name.strip():
            logger.warning("Empty journal name provided")
            return []
        
        # Use journal-specific search query
        query = f'SRCTITLE("{journal_name.strip()}")'
        
        # Temporarily adjust max_results for this search
        original_max = self.max_results
        self.max_results = min(max_papers, self.max_results)
        
        try:
            results = await self.search_papers(query)
            logger.info(f"Found {len(results)} papers in journal: {journal_name}")
            return results
        finally:
            # Restore original max_results
            self.max_results = original_max
    
    async def search_by_subject(self, subject: str, max_papers: int = 10) -> List[SourceResult]:
        """
        Search for papers by subject area
        
        Args:
            subject: Subject area to search for
            max_papers: Maximum number of papers to return
            
        Returns:
            List of SourceResult objects
        """
        if not subject or not subject.strip():
            logger.warning("Empty subject provided")
            return []
        
        # Use subject-specific search query
        query = f'SUBJAREA("{subject.strip()}")'
        
        # Temporarily adjust max_results for this search
        original_max = self.max_results
        self.max_results = min(max_papers, self.max_results)
        
        try:
            results = await self.search_papers(query)
            logger.info(f"Found {len(results)} papers on subject: {subject}")
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
            "service": "ScienceDirect",
            "max_results": self.max_results,
            "rate_limit_delay": self.rate_limit_delay,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "has_api_key": bool(self.api_key),
            "last_request_time": self._last_request_time,
            "status": "active" if self.api_key else "inactive (no API key)"
        }