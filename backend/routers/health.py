from fastapi import APIRouter, status, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
import psutil
import os
from pathlib import Path

from error_handlers import get_error_metrics
from monitoring import get_monitoring_summary
from middleware.rate_limiting import rate_limit_manager
from performance_optimizer import (
    database_optimizer, 
    connection_pool_optimizer, 
    performance_profiler,
    run_comprehensive_optimization
)
from logging_config import get_log_statistics

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    uptime: float


class MetricsResponse(BaseModel):
    service: str
    timestamp: datetime
    system: Dict[str, Any]
    application: Dict[str, Any]
    errors: Dict[str, Any]


@router.get("/api/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """Service health check endpoint."""
    import time
    
    # Calculate uptime (simplified - in production, track actual start time)
    uptime = time.time() % 86400  # Uptime in seconds for current day
    
    return HealthResponse(
        status="healthy",
        service="ai-research-agent",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        uptime=uptime
    )


@router.get("/api/metrics", response_model=MetricsResponse, status_code=status.HTTP_200_OK)
async def get_metrics():
    """Service metrics endpoint."""
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    system_metrics = {
        "cpu_usage_percent": cpu_percent,
        "memory_usage_percent": memory.percent,
        "memory_available_mb": memory.available / (1024 * 1024),
        "disk_usage_percent": disk.percent,
        "disk_free_gb": disk.free / (1024 * 1024 * 1024)
    }
    
    # Get enhanced monitoring summary
    monitoring_summary = get_monitoring_summary()
    
    # Extract application metrics from monitoring
    performance_metrics = monitoring_summary.get("performance", {})
    operations = performance_metrics.get("operations", {})
    
    app_metrics = {
        "total_operations": operations.get("total_operations", 0),
        "total_errors": operations.get("total_errors", 0),
        "success_rate": operations.get("success_rate", 0.0),
        "operation_breakdown": operations.get("operation_breakdown", {}),
        "recent_requests": performance_metrics.get("requests", {}).get("recent_requests", [])
    }
    
    # Get error metrics
    error_metrics = get_error_metrics()
    
    return MetricsResponse(
        service="ai-research-agent",
        timestamp=datetime.utcnow(),
        system=system_metrics,
        application=app_metrics,
        errors=error_metrics
    )


@router.get("/api/monitoring", status_code=status.HTTP_200_OK)
async def get_monitoring_data():
    """Comprehensive monitoring data endpoint."""
    return get_monitoring_summary()


@router.get("/api/rate-limit-status", status_code=status.HTTP_200_OK)
async def get_rate_limit_status(request: Request):
    """Get current rate limit status for the requesting client."""
    return await rate_limit_manager.get_rate_limit_status(request)


@router.get("/api/dashboard", status_code=status.HTTP_200_OK)
async def get_monitoring_dashboard():
    """Comprehensive monitoring dashboard with all system metrics."""
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get monitoring summary
    monitoring_data = get_monitoring_summary()
    
    # Get error metrics
    error_data = get_error_metrics()
    
    dashboard_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "service_info": {
            "name": "ai-research-agent",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "system_health": {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "disk_usage_percent": disk.percent,
            "disk_free_gb": disk.free / (1024 * 1024 * 1024),
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        },
        "application_metrics": monitoring_data.get("performance", {}),
        "error_metrics": error_data,
        "alerts": monitoring_data.get("alerts", {}),
        "rate_limiting": {
            "global_limit_per_minute": rate_limit_manager.global_limit,
            "ip_limit_per_minute": rate_limit_manager.ip_limit,
            "user_limit_per_minute": rate_limit_manager.user_limit,
            "research_limit_per_hour": rate_limit_manager.research_limit,
            "whitelist_count": len(rate_limit_manager.whitelist_ips)
        }
    }
    
    return dashboard_data


@router.get("/api/performance/optimize", status_code=status.HTTP_200_OK)
async def run_performance_optimization():
    """Run comprehensive performance optimization and return results."""
    return await run_comprehensive_optimization()


@router.get("/api/performance/profile", status_code=status.HTTP_200_OK)
async def get_performance_profile():
    """Get detailed performance profiling data."""
    return await performance_profiler.profile_application_performance()


@router.get("/api/database/analyze", status_code=status.HTTP_200_OK)
async def analyze_database_performance():
    """Analyze database performance and slow queries."""
    from database.connection import get_database
    
    database = await get_database()
    
    analysis_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "slow_queries": await database_optimizer.analyze_slow_queries(database),
        "connection_pool": await connection_pool_optimizer.analyze_connection_pool(database)
    }
    
    return analysis_results


@router.post("/api/database/optimize", status_code=status.HTTP_200_OK)
async def optimize_database():
    """Optimize database collections and indexes."""
    from database.connection import get_database
    
    database = await get_database()
    return await database_optimizer.optimize_collections(database)


@router.get("/api/logs/statistics", status_code=status.HTTP_200_OK)
async def get_logging_statistics():
    """Get comprehensive logging statistics and insights."""
    return get_log_statistics()


@router.get("/api/dashboard/ui", response_class=HTMLResponse)
async def get_monitoring_dashboard_ui():
    """Serve the monitoring dashboard HTML interface."""
    dashboard_path = Path(__file__).parent.parent / "templates" / "monitoring_dashboard.html"
    
    try:
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Monitoring Dashboard Not Found</h1><p>The dashboard template could not be loaded.</p>",
            status_code=404
        )