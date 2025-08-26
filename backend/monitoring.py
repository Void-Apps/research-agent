"""
Monitoring and logging integration for the AI Research Agent application.

This module provides enhanced monitoring capabilities including structured logging,
performance metrics, and error tracking integration.
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager
from functools import wraps

from error_handlers import error_metrics


# Configure structured logging
class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record):
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, 'operation'):
            log_entry["operation"] = record.operation
        
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = record.duration_ms
        
        if hasattr(record, 'error_code'):
            log_entry["error_code"] = record.error_code
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


def setup_monitoring_logging():
    """Set up enhanced monitoring and logging configuration."""
    
    # Create structured logger for monitoring
    monitor_logger = logging.getLogger("monitor")
    monitor_logger.setLevel(logging.INFO)
    
    # Create console handler with structured formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    
    # Add handler if not already present
    if not monitor_logger.handlers:
        monitor_logger.addHandler(console_handler)
    
    return monitor_logger


# Global monitor logger
monitor_logger = setup_monitoring_logging()


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self):
        self.operation_metrics: Dict[str, Dict[str, Any]] = {}
        self.request_metrics: Dict[str, Dict[str, Any]] = {}
    
    def record_operation(self, operation: str, duration_ms: float, success: bool = True, **kwargs):
        """Record operation performance metrics."""
        if operation not in self.operation_metrics:
            self.operation_metrics[operation] = {
                "total_calls": 0,
                "total_duration_ms": 0,
                "success_count": 0,
                "error_count": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": float('inf'),
                "max_duration_ms": 0
            }
        
        metrics = self.operation_metrics[operation]
        metrics["total_calls"] += 1
        metrics["total_duration_ms"] += duration_ms
        
        if success:
            metrics["success_count"] += 1
        else:
            metrics["error_count"] += 1
        
        metrics["avg_duration_ms"] = metrics["total_duration_ms"] / metrics["total_calls"]
        metrics["min_duration_ms"] = min(metrics["min_duration_ms"], duration_ms)
        metrics["max_duration_ms"] = max(metrics["max_duration_ms"], duration_ms)
        
        # Log the operation
        monitor_logger.info(
            f"Operation {operation} completed",
            extra={
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                **kwargs
            }
        )
    
    def record_request(self, request_id: str, method: str, path: str, status_code: int, duration_ms: float):
        """Record HTTP request metrics."""
        self.request_metrics[request_id] = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log the request
        monitor_logger.info(
            f"Request {method} {path} completed",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms
            }
        )
    
    def get_operation_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get current operation metrics."""
        return self.operation_metrics.copy()
    
    def get_request_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get recent request metrics."""
        return self.request_metrics.copy()
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        total_operations = sum(m["total_calls"] for m in self.operation_metrics.values())
        total_errors = sum(m["error_count"] for m in self.operation_metrics.values())
        
        return {
            "operations": {
                "total_operations": total_operations,
                "total_errors": total_errors,
                "success_rate": (total_operations - total_errors) / total_operations if total_operations > 0 else 0,
                "operation_breakdown": self.operation_metrics
            },
            "requests": {
                "total_requests": len(self.request_metrics),
                "recent_requests": list(self.request_metrics.values())[-10:]  # Last 10 requests
            },
            "errors": error_metrics.get_metrics()
        }


# Global performance monitor
performance_monitor = PerformanceMonitor()


@contextmanager
def monitor_operation(operation: str, **kwargs):
    """Context manager for monitoring operation performance."""
    start_time = time.time()
    success = True
    error = None
    
    try:
        yield
    except Exception as e:
        success = False
        error = str(e)
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000
        performance_monitor.record_operation(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error=error,
            **kwargs
        )


def monitor_async_operation(operation: str, **kwargs):
    """Decorator for monitoring async operation performance."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **func_kwargs):
            start_time = time.time()
            success = True
            error = None
            
            try:
                result = await func(*args, **func_kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                performance_monitor.record_operation(
                    operation=operation,
                    duration_ms=duration_ms,
                    success=success,
                    error=error,
                    **kwargs
                )
        
        return wrapper
    return decorator


def monitor_sync_operation(operation: str, **kwargs):
    """Decorator for monitoring sync operation performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **func_kwargs):
            start_time = time.time()
            success = True
            error = None
            
            try:
                result = func(*args, **func_kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                performance_monitor.record_operation(
                    operation=operation,
                    duration_ms=duration_ms,
                    success=success,
                    error=error,
                    **kwargs
                )
        
        return wrapper
    return decorator


class AlertManager:
    """Simple alert manager for critical errors and performance issues."""
    
    def __init__(self):
        self.alert_thresholds = {
            "error_rate": 0.1,  # 10% error rate
            "response_time_ms": 5000,  # 5 second response time
            "consecutive_errors": 5
        }
        self.consecutive_error_count = 0
    
    def check_error_rate_alert(self) -> Optional[Dict[str, Any]]:
        """Check if error rate exceeds threshold."""
        metrics = error_metrics.get_metrics()
        total_errors = metrics.get("total_errors", 0)
        
        if total_errors == 0:
            return None
        
        # Simple approximation - in production, you'd track total requests
        total_operations = sum(m["total_calls"] for m in performance_monitor.operation_metrics.values())
        
        if total_operations == 0:
            return None
        
        error_rate = total_errors / total_operations
        
        if error_rate > self.alert_thresholds["error_rate"]:
            return {
                "type": "high_error_rate",
                "error_rate": error_rate,
                "threshold": self.alert_thresholds["error_rate"],
                "total_errors": total_errors,
                "total_operations": total_operations
            }
        
        return None
    
    def check_performance_alert(self) -> Optional[Dict[str, Any]]:
        """Check if any operations exceed performance thresholds."""
        alerts = []
        
        for operation, metrics in performance_monitor.operation_metrics.items():
            if metrics["avg_duration_ms"] > self.alert_thresholds["response_time_ms"]:
                alerts.append({
                    "type": "slow_operation",
                    "operation": operation,
                    "avg_duration_ms": metrics["avg_duration_ms"],
                    "threshold": self.alert_thresholds["response_time_ms"]
                })
        
        return alerts if alerts else None
    
    def record_error(self):
        """Record an error for consecutive error tracking."""
        self.consecutive_error_count += 1
        
        if self.consecutive_error_count >= self.alert_thresholds["consecutive_errors"]:
            return {
                "type": "consecutive_errors",
                "count": self.consecutive_error_count,
                "threshold": self.alert_thresholds["consecutive_errors"]
            }
        
        return None
    
    def record_success(self):
        """Record a success, resetting consecutive error count."""
        self.consecutive_error_count = 0
    
    def check_all_alerts(self) -> Dict[str, Any]:
        """Check all alert conditions."""
        alerts = {
            "timestamp": datetime.utcnow().isoformat(),
            "alerts": []
        }
        
        # Check error rate
        error_rate_alert = self.check_error_rate_alert()
        if error_rate_alert:
            alerts["alerts"].append(error_rate_alert)
        
        # Check performance
        performance_alerts = self.check_performance_alert()
        if performance_alerts:
            alerts["alerts"].extend(performance_alerts)
        
        return alerts


# Global alert manager
alert_manager = AlertManager()


def get_monitoring_summary() -> Dict[str, Any]:
    """Get comprehensive monitoring summary."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "performance": performance_monitor.get_summary_metrics(),
        "alerts": alert_manager.check_all_alerts(),
        "system_health": {
            "total_operations": sum(m["total_calls"] for m in performance_monitor.operation_metrics.values()),
            "total_errors": error_metrics.get_metrics().get("total_errors", 0),
            "consecutive_errors": alert_manager.consecutive_error_count
        }
    }