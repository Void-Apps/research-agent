from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import logging

from models.research import (
    ResearchQuery, ResearchResult, QueryStatus, 
    ResearchQueryRequest, ResearchQueryResponse, ResearchResultResponse
)
from services.research_orchestrator import ResearchOrchestrator
from services.cache_service import CacheService
from database.connection import get_collection
from exceptions import (
    ValidationError, QueryNotFoundError, QueryProcessingError,
    DatabaseError, CacheError
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])

# Global service instances
research_orchestrator = ResearchOrchestrator()
cache_service = CacheService()


class ResearchStatusResponse(BaseModel):
    query_id: str
    status: QueryStatus
    progress: Optional[float] = None
    message: Optional[str] = None
    created_at: Optional[datetime] = None


class ResearchHistoryResponse(BaseModel):
    queries: List[ResearchQuery]
    total: int
    page: int
    limit: int


async def get_queries_collection():
    """Dependency to get research queries collection"""
    return await get_collection("research_queries")


async def get_results_collection():
    """Dependency to get research results collection"""
    return await get_collection("research_results")


@router.post("/query", response_model=ResearchQueryResponse, status_code=status.HTTP_201_CREATED)
async def submit_research_query(
    request: ResearchQueryRequest,
    background_tasks: BackgroundTasks,
    queries_collection=Depends(get_queries_collection)
):
    """Submit a new research query for processing."""
    try:
        # Validate input
        if not request.query or not request.query.strip():
            raise ValidationError("Research query cannot be empty", field="query")
        
        if len(request.query.strip()) > 1000:
            raise ValidationError(
                "Research query too long (maximum 1000 characters)", 
                field="query",
                details={"max_length": 1000, "current_length": len(request.query.strip())}
            )
        
        # Submit query to orchestrator
        research_query = await research_orchestrator.submit_research_query(
            query_text=request.query.strip(),
            user_id=request.user_id
        )
        
        # Store query in database
        query_doc = research_query.model_dump(by_alias=True)
        query_doc.pop("_id", None)  # Let MongoDB generate the ID
        await queries_collection.insert_one(query_doc)
        
        # Start background processing
        background_tasks.add_task(
            process_research_query_background,
            research_query.query_id
        )
        
        logger.info(f"Research query submitted: {research_query.query_id}")
        
        return ResearchQueryResponse(
            query_id=research_query.query_id,
            status=research_query.status,
            message="Research query submitted successfully and processing started"
        )
        
    except (ValidationError, DatabaseError, CacheError):
        raise
    except ValueError as e:
        logger.error(f"Validation error in submit_research_query: {e}")
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(f"Error submitting research query: {e}")
        raise QueryProcessingError("unknown", "Failed to submit research query", {"error": str(e)})


@router.get("/results/{query_id}", response_model=ResearchResultResponse)
async def get_research_results(
    query_id: str,
    queries_collection=Depends(get_queries_collection),
    results_collection=Depends(get_results_collection)
):
    """Get research results for a specific query ID."""
    try:
        # Validate query ID format
        if not query_id or not query_id.strip():
            raise ValidationError("Query ID is required", field="query_id")
        
        # Check if query exists
        query_doc = await queries_collection.find_one({"query_id": query_id})
        if not query_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query {query_id} not found"
            )
        
        query = ResearchQuery(**query_doc)
        
        # If query is still processing, return status without results
        if query.status in [QueryStatus.PENDING, QueryStatus.PROCESSING]:
            return ResearchResultResponse(
                query_id=query_id,
                query_text=query.query_text,
                status=query.status,
                results=None,
                ai_summary=None,
                confidence_score=None,
                cached=False,
                created_at=query.timestamp
            )
        
        # If query failed, return error status
        if query.status == QueryStatus.FAILED:
            return ResearchResultResponse(
                query_id=query_id,
                query_text=query.query_text,
                status=query.status,
                results=None,
                ai_summary="Research query failed to process",
                confidence_score=None,
                cached=False,
                created_at=query.timestamp
            )
        
        # Query completed, get results
        result_doc = await results_collection.find_one({"query_id": query_id})
        if not result_doc:
            # Query marked as completed but no results found
            logger.error(f"Query {query_id} marked as completed but no results found")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Results not found for completed query"
            )
        
        result = ResearchResult(**result_doc)
        
        return ResearchResultResponse(
            query_id=query_id,
            query_text=query.query_text,
            status=query.status,
            results=result.results,
            ai_summary=result.ai_summary,
            confidence_score=result.confidence_score,
            cached=result.cached,
            created_at=result.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving research results for {query_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving results"
        )


@router.get("/status/{query_id}", response_model=ResearchStatusResponse)
async def get_research_status(
    query_id: str,
    queries_collection=Depends(get_queries_collection)
):
    """Check the status of a research query."""
    try:
        # Validate query ID
        if not query_id or not query_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query ID is required"
            )
        
        # Get query from database
        query_doc = await queries_collection.find_one({"query_id": query_id})
        if not query_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query {query_id} not found"
            )
        
        query = ResearchQuery(**query_doc)
        
        # Calculate progress based on status
        progress_map = {
            QueryStatus.PENDING: 0.0,
            QueryStatus.PROCESSING: 0.5,
            QueryStatus.COMPLETED: 1.0,
            QueryStatus.FAILED: 0.0
        }
        
        # Generate status message
        message_map = {
            QueryStatus.PENDING: "Query is in queue for processing",
            QueryStatus.PROCESSING: "Research in progress across multiple sources",
            QueryStatus.COMPLETED: "Research completed successfully",
            QueryStatus.FAILED: "Research query failed to process"
        }
        
        return ResearchStatusResponse(
            query_id=query_id,
            status=query.status,
            progress=progress_map.get(query.status, 0.0),
            message=message_map.get(query.status, "Unknown status"),
            created_at=query.timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for query {query_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while checking query status"
        )


@router.get("/history", response_model=ResearchHistoryResponse)
async def get_research_history(
    user_id: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    queries_collection=Depends(get_queries_collection)
):
    """Get user's research history."""
    try:
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be greater than 0"
            )
        
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        # Build query filter
        query_filter = {}
        if user_id:
            query_filter["user_id"] = user_id
        
        # Calculate skip for pagination
        skip = (page - 1) * limit
        
        # Get total count
        total = await queries_collection.count_documents(query_filter)
        
        # Get queries with pagination, sorted by timestamp (newest first)
        cursor = queries_collection.find(query_filter).sort("timestamp", -1).skip(skip).limit(limit)
        query_docs = await cursor.to_list(length=limit)
        
        # Convert to ResearchQuery objects
        queries = [ResearchQuery(**doc) for doc in query_docs]
        
        logger.info(f"Retrieved {len(queries)} queries for history (page {page}, limit {limit})")
        
        return ResearchHistoryResponse(
            queries=queries,
            total=total,
            page=page,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving research history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving research history"
        )


async def process_research_query_background(query_id: str):
    """
    Background task to process research query
    
    Args:
        query_id: Unique query identifier
    """
    try:
        logger.info(f"Starting background processing for query: {query_id}")
        
        # Process the research query
        result = await research_orchestrator.process_research_query(query_id)
        
        # Store result in database
        results_collection = await get_collection("research_results")
        result_doc = result.model_dump(by_alias=True)
        result_doc.pop("_id", None)  # Let MongoDB generate the ID
        await results_collection.insert_one(result_doc)
        
        # Update query status in database
        queries_collection = await get_collection("research_queries")
        await queries_collection.update_one(
            {"query_id": query_id},
            {"$set": {"status": QueryStatus.COMPLETED}}
        )
        
        logger.info(f"Successfully completed background processing for query: {query_id}")
        
    except Exception as e:
        logger.error(f"Error in background processing for query {query_id}: {e}")
        
        # Update query status to failed
        try:
            queries_collection = await get_collection("research_queries")
            await queries_collection.update_one(
                {"query_id": query_id},
                {"$set": {"status": QueryStatus.FAILED}}
            )
        except Exception as update_error:
            logger.error(f"Failed to update query status to failed: {update_error}")


@router.get("/health")
async def get_research_service_health():
    """Get health status of research service and all integrated services."""
    try:
        health_status = await research_orchestrator.get_service_health()
        
        # Add database health check
        try:
            queries_collection = await get_collection("research_queries")
            await queries_collection.find_one({}, {"_id": 1})
            health_status["database"] = {"status": "healthy"}
        except Exception as db_error:
            health_status["database"] = {"status": "error", "error": str(db_error)}
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error getting service health: {e}")
        return {
            "orchestrator": {"status": "error", "error": str(e)},
            "database": {"status": "unknown"},
            "google_scholar": {"status": "unknown"},
            "google_books": {"status": "unknown"},
            "sciencedirect": {"status": "unknown"},
            "cache": {"status": "unknown"}
        }


@router.get("/statistics")
async def get_research_statistics():
    """Get comprehensive research statistics."""
    try:
        # Get orchestrator statistics
        stats = await research_orchestrator.get_research_statistics()
        
        # Add database statistics
        queries_collection = await get_collection("research_queries")
        results_collection = await get_collection("research_results")
        
        # Count queries by status
        status_counts = {}
        for status in QueryStatus:
            count = await queries_collection.count_documents({"status": status.value})
            status_counts[status.value] = count
        
        # Count total results
        total_results = await results_collection.count_documents({})
        
        stats.update({
            "database_statistics": {
                "total_queries": sum(status_counts.values()),
                "query_status_breakdown": status_counts,
                "total_results": total_results
            }
        })
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting research statistics: {e}")
        return {
            "error": str(e),
            "database_statistics": {
                "total_queries": 0,
                "query_status_breakdown": {},
                "total_results": 0
            }
        }


@router.delete("/query/{query_id}")
async def cancel_research_query(
    query_id: str,
    queries_collection=Depends(get_queries_collection)
):
    """Cancel an active research query."""
    try:
        # Validate query ID
        if not query_id or not query_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query ID is required"
            )
        
        # Check if query exists
        query_doc = await queries_collection.find_one({"query_id": query_id})
        if not query_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query {query_id} not found"
            )
        
        query = ResearchQuery(**query_doc)
        
        # Only allow cancellation of pending or processing queries
        if query.status not in [QueryStatus.PENDING, QueryStatus.PROCESSING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel query with status: {query.status}"
            )
        
        # Cancel in orchestrator
        cancelled = await research_orchestrator.cancel_query(query_id)
        
        if cancelled:
            # Update status in database
            await queries_collection.update_one(
                {"query_id": query_id},
                {"$set": {"status": QueryStatus.FAILED}}
            )
            
            logger.info(f"Cancelled research query: {query_id}")
            return {"message": f"Query {query_id} cancelled successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel query"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling query {query_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while cancelling query"
        )