from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
import psutil
import os

from error_handlers import get_error_metrics
from monitoring import get_monitoring_summary

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