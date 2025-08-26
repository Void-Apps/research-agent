"""
Research orchestrator service for coordinating multiple research sources
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor

from models.research import (
    ResearchQuery, ResearchResult, SourceResult, QueryStatus, SourceType
)
from services.google_scholar_service import GoogleScholarService
from services.google_books_service import GoogleBooksService
from services.sciencedirect_service import ScienceDirectService
from services.agno_ai_service import AgnoAIService, ResearchSynthesis
from services.cache_service import CacheService
from monitoring import monitor_async_operation, monitor_logger, performance_monitor

logger = logging.getLogger(__name__)

class ResearchOrchestrator:
    """
    Orchestrator service that coordinates research across multiple sources
    
    Manages concurrent API calls, result aggregation, caching, and AI processing
    """
    
    def __init__(
        self,
        google_scholar_service: Optional[GoogleScholarService] = None,
        google_books_service: Optional[GoogleBooksService] = None,
        sciencedirect_service: Optional[ScienceDirectService] = None,
        agno_ai_service: Optional[AgnoAIService] = None,
        cache_service: Optional[CacheService] = None,
        max_concurrent_requests: int = 3,
        timeout_seconds: int = 120
    ):
        """
        Initialize research orchestrator
        
        Args:
            google_scholar_service: Google Scholar service instance
            google_books_service: Google Books service instance
            sciencedirect_service: ScienceDirect service instance
            agno_ai_service: Agno AI service instance
            cache_service: Cache service instance
            max_concurrent_requests: Maximum concurrent API requests
            timeout_seconds: Timeout for individual service calls
        """
        # Initialize services with defaults if not provided
        self.google_scholar_service = google_scholar_service or GoogleScholarService()
        self.google_books_service = google_books_service or GoogleBooksService()
        self.sciencedirect_service = sciencedirect_service or ScienceDirectService()
        self.agno_ai_service = agno_ai_service or AgnoAIService()
        self.cache_service = cache_service or CacheService()
        
        self.max_concurrent_requests = max_concurrent_requests
        self.timeout_seconds = timeout_seconds
        
        # Track active queries
        self._active_queries: Dict[str, ResearchQuery] = {}
        
        logger.info("Research orchestrator initialized with all services")
    
    async def submit_research_query(
        self, 
        query_text: str, 
        user_id: Optional[str] = None
    ) -> ResearchQuery:
        """
        Submit a new research query for processing
        
        Args:
            query_text: The research query text
            user_id: Optional user identifier
            
        Returns:
            ResearchQuery object with unique ID
        """
        if not query_text or not query_text.strip():
            raise ValueError("Query text cannot be empty")
        
        # Generate unique query ID
        query_id = str(uuid.uuid4())
        
        # Create research query object
        research_query = ResearchQuery(
            query_id=query_id,
            query_text=query_text.strip(),
            user_id=user_id,
            timestamp=datetime.utcnow(),
            status=QueryStatus.PENDING
        )
        
        # Track active query
        self._active_queries[query_id] = research_query
        
        logger.info(f"Submitted research query: {query_id} - '{query_text[:50]}...'")
        return research_query
    
    async def process_research_query(self, query_id: str) -> ResearchResult:
        """
        Process a research query by coordinating all sources
        
        Args:
            query_id: Unique query identifier
            
        Returns:
            ResearchResult with aggregated findings
        """
        if query_id not in self._active_queries:
            raise ValueError(f"Query ID not found: {query_id}")
        
        query = self._active_queries[query_id]
        
        try:
            # Update status to processing
            query.status = QueryStatus.PROCESSING
            logger.info(f"Processing research query: {query_id}")
            
            # Check cache first
            cached_result = await self.cache_service.get_cached_result(query.query_text)
            if cached_result:
                logger.info(f"Returning cached result for query: {query_id}")
                query.status = QueryStatus.COMPLETED
                return cached_result
            
            # Perform concurrent research across all sources
            research_results = await self._coordinate_research_sources(query.query_text)
            
            # Process results with AI if available
            ai_summary, confidence_score = await self._process_with_ai(
                query.query_text, research_results
            )
            
            # Create final result
            result = ResearchResult(
                query_id=query_id,
                results=research_results,
                ai_summary=ai_summary,
                confidence_score=confidence_score,
                cached=False,
                created_at=datetime.utcnow()
            )
            
            # Cache the result
            await self.cache_service.store_result(query.query_text, result)
            
            # Update query status
            query.status = QueryStatus.COMPLETED
            
            logger.info(f"Successfully processed research query: {query_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing research query {query_id}: {e}")
            query.status = QueryStatus.FAILED
            raise
        finally:
            # Clean up active query tracking
            self._active_queries.pop(query_id, None)
    
    async def _coordinate_research_sources(self, query: str) -> Dict[str, List[SourceResult]]:
        """
        Coordinate concurrent research across all sources
        
        Args:
            query: Research query text
            
        Returns:
            Dictionary of results organized by source type
        """
        logger.info(f"Coordinating research sources for query: '{query[:50]}...'")
        
        # Create tasks for concurrent execution
        tasks = {
            SourceType.GOOGLE_SCHOLAR: self._search_google_scholar(query),
            SourceType.GOOGLE_BOOKS: self._search_google_books(query),
            SourceType.SCIENCEDIRECT: self._search_sciencedirect(query)
        }
        
        # Execute tasks concurrently with timeout
        results = {}
        completed_tasks = 0
        failed_tasks = 0
        
        try:
            # Use asyncio.gather with return_exceptions=True to handle partial failures
            task_results = await asyncio.wait_for(
                asyncio.gather(*tasks.values(), return_exceptions=True),
                timeout=self.timeout_seconds
            )
            
            # Process results from each source
            for source_type, result in zip(tasks.keys(), task_results):
                if isinstance(result, Exception):
                    logger.error(f"Error from {source_type}: {result}")
                    results[source_type.value] = []
                    failed_tasks += 1
                else:
                    results[source_type.value] = result or []
                    completed_tasks += 1
                    logger.info(f"{source_type}: {len(results[source_type.value])} results")
            
        except asyncio.TimeoutError:
            logger.error(f"Research coordination timed out after {self.timeout_seconds} seconds")
            # Return partial results if any tasks completed
            for source_type in tasks.keys():
                if source_type.value not in results:
                    results[source_type.value] = []
                    failed_tasks += 1
        
        logger.info(f"Research coordination completed: {completed_tasks} successful, {failed_tasks} failed")
        return results
    
    async def _search_google_scholar(self, query: str) -> List[SourceResult]:
        """
        Search Google Scholar with error handling
        
        Args:
            query: Search query
            
        Returns:
            List of SourceResult objects
        """
        try:
            logger.debug("Starting Google Scholar search")
            results = await self.google_scholar_service.search_papers(query)
            logger.debug(f"Google Scholar returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Google Scholar search failed: {e}")
            return []
    
    async def _search_google_books(self, query: str) -> List[SourceResult]:
        """
        Search Google Books with error handling
        
        Args:
            query: Search query
            
        Returns:
            List of SourceResult objects
        """
        try:
            logger.debug("Starting Google Books search")
            results = await self.google_books_service.search_books(query)
            logger.debug(f"Google Books returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Google Books search failed: {e}")
            return []
    
    async def _search_sciencedirect(self, query: str) -> List[SourceResult]:
        """
        Search ScienceDirect with error handling
        
        Args:
            query: Search query
            
        Returns:
            List of SourceResult objects
        """
        try:
            logger.debug("Starting ScienceDirect search")
            results = await self.sciencedirect_service.search_papers(query)
            logger.debug(f"ScienceDirect returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"ScienceDirect search failed: {e}")
            return []
    
    async def _process_with_ai(
        self, 
        query: str, 
        results: Dict[str, List[SourceResult]]
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Process research results with AI for synthesis and analysis
        
        Args:
            query: Original research query
            results: Research results from all sources
            
        Returns:
            Tuple of (AI summary, confidence score)
        """
        try:
            logger.debug("Processing results with AI synthesis")
            
            # Check if we have any results to process
            total_results = sum(len(source_results) for source_results in results.values())
            if total_results == 0:
                logger.warning("No results to process with AI")
                return None, None
            
            # Synthesize research results
            synthesis = await self.agno_ai_service.synthesize_research_results(query, results)
            
            logger.info(f"AI synthesis completed with confidence: {synthesis.confidence_score}")
            return synthesis.summary, synthesis.confidence_score
            
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            # Return fallback summary
            total_results = sum(len(source_results) for source_results in results.values())
            fallback_summary = f"Research completed for '{query}' with {total_results} results found across multiple sources."
            return fallback_summary, 0.6
    
    async def get_query_status(self, query_id: str) -> Optional[QueryStatus]:
        """
        Get the current status of a research query
        
        Args:
            query_id: Unique query identifier
            
        Returns:
            QueryStatus or None if query not found
        """
        query = self._active_queries.get(query_id)
        return query.status if query else None
    
    async def cancel_query(self, query_id: str) -> bool:
        """
        Cancel an active research query
        
        Args:
            query_id: Unique query identifier
            
        Returns:
            True if cancelled successfully, False if query not found
        """
        if query_id in self._active_queries:
            query = self._active_queries[query_id]
            query.status = QueryStatus.FAILED
            self._active_queries.pop(query_id, None)
            logger.info(f"Cancelled research query: {query_id}")
            return True
        return False
    
    def get_active_queries(self) -> List[ResearchQuery]:
        """
        Get list of currently active queries
        
        Returns:
            List of active ResearchQuery objects
        """
        return list(self._active_queries.values())
    
    async def get_service_health(self) -> Dict[str, Any]:
        """
        Get health status of all integrated services
        
        Returns:
            Dictionary with service health information
        """
        health_status = {
            "orchestrator": {
                "status": "healthy",
                "active_queries": len(self._active_queries),
                "max_concurrent_requests": self.max_concurrent_requests,
                "timeout_seconds": self.timeout_seconds
            }
        }
        
        # Get status from each service
        try:
            health_status["google_scholar"] = self.google_scholar_service.get_service_status()
        except Exception as e:
            health_status["google_scholar"] = {"status": "error", "error": str(e)}
        
        try:
            health_status["google_books"] = self.google_books_service.get_service_status()
        except Exception as e:
            health_status["google_books"] = {"status": "error", "error": str(e)}
        
        try:
            health_status["sciencedirect"] = self.sciencedirect_service.get_service_status()
        except Exception as e:
            health_status["sciencedirect"] = {"status": "error", "error": str(e)}
        
        try:
            health_status["cache"] = await self.cache_service.get_cache_stats()
        except Exception as e:
            health_status["cache"] = {"status": "error", "error": str(e)}
        
        return health_status
    
    async def search_by_author(
        self, 
        author_name: str, 
        max_results_per_source: int = 10
    ) -> Dict[str, List[SourceResult]]:
        """
        Search for research by a specific author across all sources
        
        Args:
            author_name: Name of the author to search for
            max_results_per_source: Maximum results per source
            
        Returns:
            Dictionary of results organized by source type
        """
        if not author_name or not author_name.strip():
            raise ValueError("Author name cannot be empty")
        
        logger.info(f"Searching by author: '{author_name}'")
        
        # Create tasks for concurrent author search
        tasks = {
            SourceType.GOOGLE_SCHOLAR: self._search_author_google_scholar(author_name, max_results_per_source),
            SourceType.GOOGLE_BOOKS: self._search_author_google_books(author_name, max_results_per_source),
            SourceType.SCIENCEDIRECT: self._search_author_sciencedirect(author_name, max_results_per_source)
        }
        
        # Execute tasks concurrently
        results = {}
        
        try:
            task_results = await asyncio.wait_for(
                asyncio.gather(*tasks.values(), return_exceptions=True),
                timeout=self.timeout_seconds
            )
            
            for source_type, result in zip(tasks.keys(), task_results):
                if isinstance(result, Exception):
                    logger.error(f"Error searching author in {source_type}: {result}")
                    results[source_type.value] = []
                else:
                    results[source_type.value] = result or []
                    logger.info(f"{source_type} author search: {len(results[source_type.value])} results")
        
        except asyncio.TimeoutError:
            logger.error(f"Author search timed out after {self.timeout_seconds} seconds")
            for source_type in tasks.keys():
                if source_type.value not in results:
                    results[source_type.value] = []
        
        return results
    
    async def _search_author_google_scholar(self, author_name: str, max_results: int) -> List[SourceResult]:
        """Search Google Scholar by author"""
        try:
            return await self.google_scholar_service.search_by_author(author_name, max_results)
        except Exception as e:
            logger.error(f"Google Scholar author search failed: {e}")
            return []
    
    async def _search_author_google_books(self, author_name: str, max_results: int) -> List[SourceResult]:
        """Search Google Books by author"""
        try:
            return await self.google_books_service.search_by_author(author_name, max_results)
        except Exception as e:
            logger.error(f"Google Books author search failed: {e}")
            return []
    
    async def _search_author_sciencedirect(self, author_name: str, max_results: int) -> List[SourceResult]:
        """Search ScienceDirect by author"""
        try:
            return await self.sciencedirect_service.search_by_author(author_name, max_results)
        except Exception as e:
            logger.error(f"ScienceDirect author search failed: {e}")
            return []
    
    async def get_research_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive research statistics
        
        Returns:
            Dictionary with research statistics
        """
        try:
            cache_stats = await self.cache_service.get_cache_stats()
            
            return {
                "cache_statistics": cache_stats,
                "active_queries": len(self._active_queries),
                "service_configuration": {
                    "max_concurrent_requests": self.max_concurrent_requests,
                    "timeout_seconds": self.timeout_seconds,
                    "google_scholar_max_results": self.google_scholar_service.max_results,
                    "google_books_max_results": self.google_books_service.max_results,
                    "sciencedirect_max_results": self.sciencedirect_service.max_results
                }
            }
        except Exception as e:
            logger.error(f"Error getting research statistics: {e}")
            return {
                "error": str(e),
                "active_queries": len(self._active_queries)
            }