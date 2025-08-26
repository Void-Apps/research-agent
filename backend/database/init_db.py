"""
Database initialization scripts and indexes
"""
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from .connection import get_database

logger = logging.getLogger(__name__)

async def create_indexes(database: AsyncIOMotorDatabase) -> None:
    """Create indexes for all collections"""
    
    # Research queries collection indexes
    research_queries_indexes = [
        IndexModel([("query_id", ASCENDING)], unique=True),
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("timestamp", DESCENDING)]),
        IndexModel([("status", ASCENDING)]),
        IndexModel([("query_text", TEXT)]),  # Text search index
    ]
    
    await database.research_queries.create_indexes(research_queries_indexes)
    logger.info("Created indexes for research_queries collection")
    
    # Research results collection indexes
    research_results_indexes = [
        IndexModel([("query_id", ASCENDING)], unique=True),
        IndexModel([("created_at", DESCENDING)]),
        IndexModel([("expires_at", ASCENDING)]),  # For TTL cleanup
        IndexModel([("cached", ASCENDING)]),
    ]
    
    await database.research_results.create_indexes(research_results_indexes)
    logger.info("Created indexes for research_results collection")
    
    # Cache metadata collection indexes
    cache_metadata_indexes = [
        IndexModel([("query_hash", ASCENDING)], unique=True),
        IndexModel([("last_updated", DESCENDING)]),
        IndexModel([("hit_count", DESCENDING)]),
    ]
    
    await database.cache_metadata.create_indexes(cache_metadata_indexes)
    logger.info("Created indexes for cache_metadata collection")

async def create_ttl_indexes(database: AsyncIOMotorDatabase) -> None:
    """Create TTL (Time To Live) indexes for automatic document expiration"""
    
    # TTL index for research_results - expire documents after expires_at
    await database.research_results.create_index(
        [("expires_at", ASCENDING)], 
        expireAfterSeconds=0  # Expire at the time specified in expires_at field
    )
    logger.info("Created TTL index for research_results collection")

async def initialize_collections(database: AsyncIOMotorDatabase) -> None:
    """Initialize collections with validation schemas"""
    
    # Research queries collection validation
    research_queries_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["query_id", "query_text", "timestamp", "status"],
            "properties": {
                "query_id": {"bsonType": "string"},
                "query_text": {"bsonType": "string", "minLength": 1},
                "user_id": {"bsonType": ["string", "null"]},
                "timestamp": {"bsonType": "date"},
                "status": {
                    "bsonType": "string",
                    "enum": ["pending", "processing", "completed", "failed"]
                },
                "metadata": {"bsonType": ["object", "null"]}
            }
        }
    }
    
    try:
        await database.create_collection(
            "research_queries",
            validator=research_queries_validator,
            validationLevel="strict"
        )
        logger.info("Created research_queries collection with validation")
    except Exception as e:
        if "already exists" in str(e):
            logger.info("research_queries collection already exists")
        else:
            logger.error(f"Error creating research_queries collection: {e}")
    
    # Research results collection validation
    research_results_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["query_id", "created_at"],
            "properties": {
                "query_id": {"bsonType": "string"},
                "results": {"bsonType": ["object", "null"]},
                "ai_summary": {"bsonType": ["string", "null"]},
                "confidence_score": {"bsonType": ["double", "null"], "minimum": 0, "maximum": 1},
                "cached": {"bsonType": "bool"},
                "created_at": {"bsonType": "date"},
                "expires_at": {"bsonType": ["date", "null"]}
            }
        }
    }    

    try:
        await database.create_collection(
            "research_results",
            validator=research_results_validator,
            validationLevel="strict"
        )
        logger.info("Created research_results collection with validation")
    except Exception as e:
        if "already exists" in str(e):
            logger.info("research_results collection already exists")
        else:
            logger.error(f"Error creating research_results collection: {e}")
    
    # Cache metadata collection validation
    cache_metadata_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["query_hash", "last_updated", "hit_count"],
            "properties": {
                "query_hash": {"bsonType": "string"},
                "last_updated": {"bsonType": "date"},
                "hit_count": {"bsonType": "int", "minimum": 0},
                "query_variations": {"bsonType": "array", "items": {"bsonType": "string"}}
            }
        }
    }
    
    try:
        await database.create_collection(
            "cache_metadata",
            validator=cache_metadata_validator,
            validationLevel="strict"
        )
        logger.info("Created cache_metadata collection with validation")
    except Exception as e:
        if "already exists" in str(e):
            logger.info("cache_metadata collection already exists")
        else:
            logger.error(f"Error creating cache_metadata collection: {e}")

async def initialize_database() -> None:
    """Initialize the entire database with collections, indexes, and validation"""
    try:
        database = await get_database()
        
        # Initialize collections with validation
        await initialize_collections(database)
        
        # Create indexes
        await create_indexes(database)
        
        # Create TTL indexes
        await create_ttl_indexes(database)
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def drop_database() -> None:
    """Drop the entire database (for testing purposes)"""
    try:
        database = await get_database()
        await database.client.drop_database(database.name)
        logger.info(f"Dropped database: {database.name}")
    except Exception as e:
        logger.error(f"Failed to drop database: {e}")
        raise

if __name__ == "__main__":
    # Run database initialization
    asyncio.run(initialize_database())