"""
MongoDB connection utilities with connection pooling
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """MongoDB connection manager with connection pooling"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self._connection_string = self._get_connection_string()
        
    def _get_connection_string(self) -> str:
        """Get MongoDB connection string from environment variables"""
        host = os.getenv("MONGODB_HOST", "localhost")
        port = os.getenv("MONGODB_PORT", "27017")
        username = os.getenv("MONGODB_USERNAME", "")
        password = os.getenv("MONGODB_PASSWORD", "")
        database_name = os.getenv("MONGODB_DATABASE", "ai_research_agent")
        
        if username and password:
            return f"mongodb://{username}:{password}@{host}:{port}/{database_name}"
        else:
            return f"mongodb://{host}:{port}/{database_name}"
    
    async def connect(self) -> None:
        """Establish connection to MongoDB with connection pooling"""
        try:
            self.client = AsyncIOMotorClient(
                self._connection_string,
                maxPoolSize=10,  # Maximum number of connections in the pool
                minPoolSize=1,   # Minimum number of connections in the pool
                maxIdleTimeMS=30000,  # Close connections after 30 seconds of inactivity
                serverSelectionTimeoutMS=5000,  # 5 second timeout for server selection
                connectTimeoutMS=10000,  # 10 second connection timeout
                socketTimeoutMS=20000,   # 20 second socket timeout
            )
            
            # Test the connection
            await self.client.admin.command('ping')
            
            database_name = os.getenv("MONGODB_DATABASE", "ai_research_agent")
            self.database = self.client[database_name]
            
            logger.info(f"Successfully connected to MongoDB database: {database_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def ping(self) -> bool:
        """Test database connection"""
        try:
            if self.client:
                await self.client.admin.command('ping')
                return True
            return False
        except Exception as e:
            logger.error(f"Database ping failed: {e}")
            return False
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database"""
        if not self.database:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.database[collection_name]

# Global database connection instance
db_connection = DatabaseConnection()

async def get_database():
    """Dependency to get database connection"""
    if not db_connection.database:
        await db_connection.connect()
    return db_connection.database

async def get_collection(collection_name: str):
    """Get a specific collection"""
    database = await get_database()
    return database[collection_name]