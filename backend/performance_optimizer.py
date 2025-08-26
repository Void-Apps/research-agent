"""
Performance optimization utilities for the AI Research Agent application.

This module provides database query optimization, connection pooling enhancements,
and performance monitoring tools.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from pymongo.errors import OperationFailure

from database.connection import get_database
from monitoring import monitor_async_operation, monitor_logger, performance_monitor

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database query optimization and performance monitoring."""
    
    def __init__(self):
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        self.slow_query_threshold_ms = 1000  # 1 second
    
    @monitor_async_operation("database_optimization")
    async def optimize_collections(self, database: AsyncIOMotorDatabase) -> Dict[str, Any]:
        """Optimize database collections with additional indexes and settings."""
        optimization_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "optimizations_applied": [],
            "performance_improvements": {}
        }
        
        try:
            # Optimize research_queries collection
            await self._optimize_research_queries(database)
            optimization_results["optimizations_applied"].append("research_queries_indexes")
            
            # Optimize research_results collection
            await self._optimize_research_results(database)
            optimization_results["optimizations_applied"].append("research_results_indexes")
            
            # Optimize cache_metadata collection
            await self._optimize_cache_metadata(database)
            optimization_results["optimizations_applied"].append("cache_metadata_indexes")
            
            # Create compound indexes for common query patterns
            await self._create_compound_indexes(database)
            optimization_results["optimizations_applied"].append("compound_indexes")
            
            # Analyze collection statistics
            stats = await self._analyze_collection_stats(database)
            optimization_results["performance_improvements"] = stats
            
            logger.info("Database optimization completed successfully")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            raise
    
    async def _optimize_research_queries(self, database: AsyncIOMotorDatabase):
        """Optimize research_queries collection."""
        collection = database.research_queries
        
        # Additional indexes for performance
        additional_indexes = [
            IndexModel([("user_id", ASCENDING), ("timestamp", DESCENDING)]),  # User query history
            IndexModel([("status", ASCENDING), ("timestamp", DESCENDING)]),   # Status-based queries
            IndexModel([("query_text", TEXT), ("timestamp", DESCENDING)]),    # Text search with recency
        ]
        
        try:
            await collection.create_indexes(additional_indexes)
            logger.info("Created additional indexes for research_queries")
        except OperationFailure as e:
            if "already exists" not in str(e):
                logger.warning(f"Some indexes may already exist: {e}")
    
    async def _optimize_research_results(self, database: AsyncIOMotorDatabase):
        """Optimize research_results collection."""
        collection = database.research_results
        
        # Additional indexes for performance
        additional_indexes = [
            IndexModel([("query_id", ASCENDING), ("cached", ASCENDING)]),     # Cache lookup
            IndexModel([("confidence_score", DESCENDING)]),                   # Quality sorting
            IndexModel([("created_at", DESCENDING), ("cached", ASCENDING)]),  # Recent results
        ]
        
        try:
            await collection.create_indexes(additional_indexes)
            logger.info("Created additional indexes for research_results")
        except OperationFailure as e:
            if "already exists" not in str(e):
                logger.warning(f"Some indexes may already exist: {e}")
    
    async def _optimize_cache_metadata(self, database: AsyncIOMotorDatabase):
        """Optimize cache_metadata collection."""
        collection = database.cache_metadata
        
        # Additional indexes for performance
        additional_indexes = [
            IndexModel([("hit_count", DESCENDING), ("last_updated", DESCENDING)]),  # Popular queries
            IndexModel([("last_updated", ASCENDING)]),  # Cleanup old entries
        ]
        
        try:
            await collection.create_indexes(additional_indexes)
            logger.info("Created additional indexes for cache_metadata")
        except OperationFailure as e:
            if "already exists" not in str(e):
                logger.warning(f"Some indexes may already exist: {e}")
    
    async def _create_compound_indexes(self, database: AsyncIOMotorDatabase):
        """Create compound indexes for common query patterns."""
        
        # Research queries compound indexes
        research_queries_compound = [
            IndexModel([
                ("user_id", ASCENDING),
                ("status", ASCENDING),
                ("timestamp", DESCENDING)
            ]),  # User's active/completed queries
        ]
        
        try:
            await database.research_queries.create_indexes(research_queries_compound)
            logger.info("Created compound indexes for research_queries")
        except OperationFailure as e:
            if "already exists" not in str(e):
                logger.warning(f"Some compound indexes may already exist: {e}")
    
    async def _analyze_collection_stats(self, database: AsyncIOMotorDatabase) -> Dict[str, Any]:
        """Analyze collection statistics for performance insights."""
        stats = {}
        
        collections = ["research_queries", "research_results", "cache_metadata"]
        
        for collection_name in collections:
            collection = database[collection_name]
            
            try:
                # Get collection stats
                collection_stats = await database.command("collStats", collection_name)
                
                # Get index stats
                index_stats = []
                async for index in collection.list_indexes():
                    index_stats.append(index)
                
                stats[collection_name] = {
                    "document_count": collection_stats.get("count", 0),
                    "storage_size_mb": collection_stats.get("storageSize", 0) / (1024 * 1024),
                    "index_count": len(index_stats),
                    "avg_document_size_bytes": collection_stats.get("avgObjSize", 0),
                    "total_index_size_mb": collection_stats.get("totalIndexSize", 0) / (1024 * 1024)
                }
                
            except Exception as e:
                logger.warning(f"Could not get stats for {collection_name}: {e}")
                stats[collection_name] = {"error": str(e)}
        
        return stats
    
    @monitor_async_operation("slow_query_analysis")
    async def analyze_slow_queries(self, database: AsyncIOMotorDatabase) -> Dict[str, Any]:
        """Analyze slow queries and provide optimization recommendations."""
        try:
            # Enable profiling for slow operations (> 1000ms)
            await database.command("profile", 2, slowms=self.slow_query_threshold_ms)
            
            # Get profiling data
            profiler_collection = database.system.profile
            
            # Find slow queries from the last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            slow_queries = []
            
            async for query in profiler_collection.find({
                "ts": {"$gte": one_hour_ago},
                "millis": {"$gte": self.slow_query_threshold_ms}
            }).sort("millis", -1).limit(10):
                slow_queries.append({
                    "timestamp": query.get("ts"),
                    "duration_ms": query.get("millis"),
                    "operation": query.get("op"),
                    "namespace": query.get("ns"),
                    "command": query.get("command", {})
                })
            
            # Disable profiling to avoid performance impact
            await database.command("profile", 0)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "slow_query_threshold_ms": self.slow_query_threshold_ms,
                "slow_queries_found": len(slow_queries),
                "slow_queries": slow_queries,
                "recommendations": self._generate_optimization_recommendations(slow_queries)
            }
            
        except Exception as e:
            logger.error(f"Slow query analysis failed: {e}")
            return {"error": str(e)}
    
    def _generate_optimization_recommendations(self, slow_queries: List[Dict]) -> List[str]:
        """Generate optimization recommendations based on slow queries."""
        recommendations = []
        
        if not slow_queries:
            return ["No slow queries detected in the last hour"]
        
        # Analyze query patterns
        operations = {}
        for query in slow_queries:
            op = query.get("operation", "unknown")
            operations[op] = operations.get(op, 0) + 1
        
        if operations.get("find", 0) > 0:
            recommendations.append("Consider adding indexes for frequently queried fields")
        
        if operations.get("update", 0) > 0:
            recommendations.append("Review update operations for bulk update opportunities")
        
        if operations.get("aggregate", 0) > 0:
            recommendations.append("Optimize aggregation pipelines and consider using indexes")
        
        # Check for high duration queries
        max_duration = max(q.get("duration_ms", 0) for q in slow_queries)
        if max_duration > 5000:  # 5 seconds
            recommendations.append("Investigate queries taking more than 5 seconds")
        
        return recommendations


class ConnectionPoolOptimizer:
    """Optimize database connection pool settings."""
    
    def __init__(self):
        self.pool_stats = {}
    
    @monitor_async_operation("connection_pool_analysis")
    async def analyze_connection_pool(self, database: AsyncIOMotorDatabase) -> Dict[str, Any]:
        """Analyze connection pool performance and usage."""
        try:
            # Get server status for connection info
            server_status = await database.command("serverStatus")
            connections = server_status.get("connections", {})
            
            pool_analysis = {
                "timestamp": datetime.utcnow().isoformat(),
                "current_connections": connections.get("current", 0),
                "available_connections": connections.get("available", 0),
                "total_created": connections.get("totalCreated", 0),
                "active_connections": connections.get("active", 0),
                "recommendations": []
            }
            
            # Generate recommendations
            current = connections.get("current", 0)
            available = connections.get("available", 0)
            
            if current > 0 and available / current < 0.2:  # Less than 20% available
                pool_analysis["recommendations"].append(
                    "Consider increasing connection pool size - low availability"
                )
            
            if current > 50:  # High connection count
                pool_analysis["recommendations"].append(
                    "High connection count detected - review connection usage patterns"
                )
            
            return pool_analysis
            
        except Exception as e:
            logger.error(f"Connection pool analysis failed: {e}")
            return {"error": str(e)}


class PerformanceProfiler:
    """Application performance profiling and analysis."""
    
    def __init__(self):
        self.operation_profiles = {}
        self.memory_snapshots = []
    
    @monitor_async_operation("performance_profiling")
    async def profile_application_performance(self) -> Dict[str, Any]:
        """Profile overall application performance."""
        import psutil
        import gc
        
        # Get current process
        process = psutil.Process()
        
        # Memory usage
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # CPU usage
        cpu_percent = process.cpu_percent(interval=1)
        
        # Thread count
        thread_count = process.num_threads()
        
        # Garbage collection stats
        gc_stats = {
            "collections": gc.get_stats(),
            "garbage_count": len(gc.garbage),
            "threshold": gc.get_threshold()
        }
        
        # Get monitoring metrics
        monitoring_summary = performance_monitor.get_summary_metrics()
        
        profile_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "process_info": {
                "memory_usage_mb": memory_info.rss / (1024 * 1024),
                "memory_percent": memory_percent,
                "cpu_percent": cpu_percent,
                "thread_count": thread_count
            },
            "garbage_collection": gc_stats,
            "operation_metrics": monitoring_summary.get("operations", {}),
            "request_metrics": monitoring_summary.get("requests", {}),
            "recommendations": self._generate_performance_recommendations(
                memory_percent, cpu_percent, monitoring_summary
            )
        }
        
        # Store snapshot for trend analysis
        self.memory_snapshots.append({
            "timestamp": datetime.utcnow(),
            "memory_mb": memory_info.rss / (1024 * 1024),
            "cpu_percent": cpu_percent
        })
        
        # Keep only last 100 snapshots
        if len(self.memory_snapshots) > 100:
            self.memory_snapshots = self.memory_snapshots[-100:]
        
        return profile_data
    
    def _generate_performance_recommendations(
        self, 
        memory_percent: float, 
        cpu_percent: float, 
        monitoring_summary: Dict
    ) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Memory recommendations
        if memory_percent > 80:
            recommendations.append("High memory usage detected - consider memory optimization")
        
        # CPU recommendations
        if cpu_percent > 80:
            recommendations.append("High CPU usage detected - review computational efficiency")
        
        # Operation recommendations
        operations = monitoring_summary.get("operations", {})
        if operations.get("total_errors", 0) > 0:
            error_rate = operations.get("total_errors", 0) / max(operations.get("total_operations", 1), 1)
            if error_rate > 0.05:  # 5% error rate
                recommendations.append("High error rate detected - review error handling")
        
        # Request recommendations
        requests = monitoring_summary.get("requests", {})
        recent_requests = requests.get("recent_requests", [])
        if recent_requests:
            avg_duration = sum(r.get("duration_ms", 0) for r in recent_requests) / len(recent_requests)
            if avg_duration > 2000:  # 2 seconds
                recommendations.append("High average request duration - optimize request processing")
        
        return recommendations


# Global optimizer instances
database_optimizer = DatabaseOptimizer()
connection_pool_optimizer = ConnectionPoolOptimizer()
performance_profiler = PerformanceProfiler()


async def run_comprehensive_optimization() -> Dict[str, Any]:
    """Run comprehensive performance optimization and analysis."""
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "optimization_results": {}
    }
    
    try:
        database = await get_database()
        
        # Database optimization
        db_results = await database_optimizer.optimize_collections(database)
        results["optimization_results"]["database"] = db_results
        
        # Slow query analysis
        slow_query_results = await database_optimizer.analyze_slow_queries(database)
        results["optimization_results"]["slow_queries"] = slow_query_results
        
        # Connection pool analysis
        pool_results = await connection_pool_optimizer.analyze_connection_pool(database)
        results["optimization_results"]["connection_pool"] = pool_results
        
        # Performance profiling
        profile_results = await performance_profiler.profile_application_performance()
        results["optimization_results"]["performance_profile"] = profile_results
        
        logger.info("Comprehensive optimization completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Comprehensive optimization failed: {e}")
        results["error"] = str(e)
        return results


if __name__ == "__main__":
    # Run optimization
    asyncio.run(run_comprehensive_optimization())