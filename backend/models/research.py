"""
Pydantic models for research data structures
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId

class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2"""
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        field_schema.update(type="string")
        return field_schema

class QueryStatus(str, Enum):
    """Status enumeration for research queries"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SourceType(str, Enum):
    """Source type enumeration"""
    GOOGLE_SCHOLAR = "google_scholar"
    GOOGLE_BOOKS = "google_books"
    SCIENCEDIRECT = "sciencedirect"

class SourceResult(BaseModel):
    """Model for individual research source results"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    title: str = Field(..., description="Title of the research item")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    abstract: Optional[str] = Field(None, description="Abstract or description")
    url: Optional[str] = Field(None, description="URL to the source")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    source_type: SourceType = Field(..., description="Type of source")
    
    # Source-specific fields
    citation_count: Optional[int] = Field(None, description="Citation count (Scholar)")
    isbn: Optional[str] = Field(None, description="ISBN (Books)")
    doi: Optional[str] = Field(None, description="DOI (ScienceDirect)")
    journal: Optional[str] = Field(None, description="Journal name (ScienceDirect)")
    preview_link: Optional[str] = Field(None, description="Preview link (Books)")
    access_status: Optional[str] = Field(None, description="Access status (ScienceDirect)")

class ResearchQuery(BaseModel):
    """Model for research queries"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    query_id: str = Field(..., description="Unique query identifier")
    query_text: str = Field(..., description="The research query text")
    user_id: Optional[str] = Field(None, description="User identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Query timestamp")
    status: QueryStatus = Field(default=QueryStatus.PENDING, description="Query status")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class ResearchResult(BaseModel):
    """Model for research results"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    query_id: str = Field(..., description="Associated query identifier")
    results: Dict[str, List[SourceResult]] = Field(
        default_factory=dict, 
        description="Results organized by source type"
    )
    ai_summary: Optional[str] = Field(None, description="AI-generated summary")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-1)")
    cached: bool = Field(default=False, description="Whether result was served from cache")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Cache expiration timestamp")

class CacheMetadata(BaseModel):
    """Model for cache metadata"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    query_hash: str = Field(..., description="MD5 hash of normalized query")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    hit_count: int = Field(default=0, description="Number of cache hits")
    query_variations: List[str] = Field(default_factory=list, description="Query variations")

# Request/Response models for API endpoints
class ResearchQueryRequest(BaseModel):
    """Request model for submitting research queries"""
    query: str = Field(..., min_length=1, max_length=1000, description="Research query text")
    user_id: Optional[str] = Field(None, description="Optional user identifier")

class ResearchQueryResponse(BaseModel):
    """Response model for research query submission"""
    query_id: str = Field(..., description="Unique query identifier")
    status: QueryStatus = Field(..., description="Query status")
    message: str = Field(..., description="Response message")

class ResearchResultResponse(BaseModel):
    """Response model for research results"""
    query_id: str = Field(..., description="Query identifier")
    query_text: str = Field(..., description="Original query text")
    status: QueryStatus = Field(..., description="Query status")
    results: Optional[Dict[str, List[SourceResult]]] = Field(None, description="Research results")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    cached: bool = Field(default=False, description="Whether served from cache")
    created_at: datetime = Field(..., description="Creation timestamp")