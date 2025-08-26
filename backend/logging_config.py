"""
Enhanced logging configuration for the AI Research Agent application.

This module provides structured logging, log rotation, and centralized logging
configuration for all application components.
"""

import logging
import logging.handlers
import os
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from monitoring import StructuredFormatter


class EnhancedStructuredFormatter(StructuredFormatter):
    """Enhanced structured formatter with additional context."""
    
    def format(self, record):
        """Format log record with enhanced structured data."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": os.getpid(),
            "thread_name": record.thread if hasattr(record, 'thread') else None
        }
        
        # Add request context if available
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
        
        # Add service context
        log_entry["service"] = "ai-research-agent"
        log_entry["environment"] = os.getenv("ENVIRONMENT", "development")
        log_entry["version"] = "1.0.0"
        
        # Add performance metrics if available
        if hasattr(record, 'memory_usage_mb'):
            log_entry["memory_usage_mb"] = record.memory_usage_mb
        
        if hasattr(record, 'cpu_percent'):
            log_entry["cpu_percent"] = record.cpu_percent
        
        # Add business context
        if hasattr(record, 'research_query_id'):
            log_entry["research_query_id"] = record.research_query_id
        
        if hasattr(record, 'source_type'):
            log_entry["source_type"] = record.source_type
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry, default=str)


class LoggingConfig:
    """Centralized logging configuration manager."""
    
    def __init__(self):
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_format = os.getenv("LOG_FORMAT", "structured")  # structured or simple
        self.log_file_enabled = os.getenv("LOG_FILE_ENABLED", "true").lower() == "true"
        self.log_file_path = os.getenv("LOG_FILE_PATH", "logs/ai_research_agent.log")
        self.log_rotation_enabled = os.getenv("LOG_ROTATION_ENABLED", "true").lower() == "true"
        self.log_max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
        self.log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        
        # Create logs directory if it doesn't exist
        if self.log_file_enabled:
            log_dir = Path(self.log_file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
    
    def setup_logging(self) -> None:
        """Set up comprehensive logging configuration."""
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Set log level
        root_logger.setLevel(getattr(logging, self.log_level))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.log_level))
        
        if self.log_format == "structured":
            console_handler.setFormatter(EnhancedStructuredFormatter())
        else:
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        
        root_logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.log_file_enabled:
            if self.log_rotation_enabled:
                file_handler = logging.handlers.RotatingFileHandler(
                    self.log_file_path,
                    maxBytes=self.log_max_bytes,
                    backupCount=self.log_backup_count
                )
            else:
                file_handler = logging.FileHandler(self.log_file_path)
            
            file_handler.setLevel(getattr(logging, self.log_level))
            
            if self.log_format == "structured":
                file_handler.setFormatter(EnhancedStructuredFormatter())
            else:
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            
            root_logger.addHandler(file_handler)
        
        # Configure specific loggers
        self._configure_specific_loggers()
        
        logging.info("Enhanced logging configuration initialized")
    
    def _configure_specific_loggers(self) -> None:
        """Configure specific loggers for different components."""
        
        # Database logger
        db_logger = logging.getLogger("database")
        db_logger.setLevel(logging.INFO)
        
        # API logger
        api_logger = logging.getLogger("api")
        api_logger.setLevel(logging.INFO)
        
        # Services logger
        services_logger = logging.getLogger("services")
        services_logger.setLevel(logging.INFO)
        
        # Monitoring logger
        monitor_logger = logging.getLogger("monitor")
        monitor_logger.setLevel(logging.INFO)
        
        # External API logger (more verbose for debugging)
        external_api_logger = logging.getLogger("external_apis")
        external_api_logger.setLevel(logging.DEBUG if self.log_level == "DEBUG" else logging.INFO)
        
        # Reduce noise from external libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a configured logger instance."""
        return logging.getLogger(name)


class ContextualLogger:
    """Logger wrapper that adds contextual information to log records."""
    
    def __init__(self, logger: logging.Logger, context: Optional[Dict[str, Any]] = None):
        self.logger = logger
        self.context = context or {}
    
    def _add_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add context to log record extra data."""
        combined_extra = self.context.copy()
        if extra:
            combined_extra.update(extra)
        return combined_extra
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message with context."""
        self.logger.debug(message, extra=self._add_context(extra))
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message with context."""
        self.logger.info(message, extra=self._add_context(extra))
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message with context."""
        self.logger.warning(message, extra=self._add_context(extra))
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message with context."""
        self.logger.error(message, extra=self._add_context(extra), exc_info=exc_info)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log critical message with context."""
        self.logger.critical(message, extra=self._add_context(extra), exc_info=exc_info)
    
    def with_context(self, **kwargs) -> 'ContextualLogger':
        """Create a new logger with additional context."""
        new_context = self.context.copy()
        new_context.update(kwargs)
        return ContextualLogger(self.logger, new_context)


class LogAggregator:
    """Aggregate and analyze log data for insights."""
    
    def __init__(self):
        self.log_stats = {
            "total_logs": 0,
            "by_level": {},
            "by_module": {},
            "by_operation": {},
            "errors": [],
            "performance_logs": []
        }
    
    def process_log_record(self, record: logging.LogRecord) -> None:
        """Process a log record for aggregation."""
        self.log_stats["total_logs"] += 1
        
        # Count by level
        level = record.levelname
        self.log_stats["by_level"][level] = self.log_stats["by_level"].get(level, 0) + 1
        
        # Count by module
        module = record.module
        self.log_stats["by_module"][module] = self.log_stats["by_module"].get(module, 0) + 1
        
        # Count by operation if available
        if hasattr(record, 'operation'):
            operation = record.operation
            self.log_stats["by_operation"][operation] = self.log_stats["by_operation"].get(operation, 0) + 1
        
        # Collect errors
        if record.levelno >= logging.ERROR:
            self.log_stats["errors"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName
            })
            
            # Keep only last 100 errors
            if len(self.log_stats["errors"]) > 100:
                self.log_stats["errors"] = self.log_stats["errors"][-100:]
        
        # Collect performance logs
        if hasattr(record, 'duration_ms'):
            self.log_stats["performance_logs"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "operation": getattr(record, 'operation', 'unknown'),
                "duration_ms": record.duration_ms,
                "success": getattr(record, 'success', True)
            })
            
            # Keep only last 100 performance logs
            if len(self.log_stats["performance_logs"]) > 100:
                self.log_stats["performance_logs"] = self.log_stats["performance_logs"][-100:]
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get aggregated log statistics."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": self.log_stats.copy(),
            "insights": self._generate_insights()
        }
    
    def _generate_insights(self) -> List[str]:
        """Generate insights from log data."""
        insights = []
        
        # Error rate insights
        total_logs = self.log_stats["total_logs"]
        error_count = self.log_stats["by_level"].get("ERROR", 0) + self.log_stats["by_level"].get("CRITICAL", 0)
        
        if total_logs > 0:
            error_rate = error_count / total_logs
            if error_rate > 0.05:  # 5% error rate
                insights.append(f"High error rate detected: {error_rate:.2%}")
        
        # Performance insights
        if self.log_stats["performance_logs"]:
            avg_duration = sum(log["duration_ms"] for log in self.log_stats["performance_logs"]) / len(self.log_stats["performance_logs"])
            if avg_duration > 1000:  # 1 second
                insights.append(f"High average operation duration: {avg_duration:.0f}ms")
        
        # Module insights
        if self.log_stats["by_module"]:
            most_active_module = max(self.log_stats["by_module"], key=self.log_stats["by_module"].get)
            insights.append(f"Most active module: {most_active_module}")
        
        return insights


# Global instances
logging_config = LoggingConfig()
log_aggregator = LogAggregator()


def setup_enhanced_logging() -> None:
    """Set up enhanced logging for the entire application."""
    logging_config.setup_logging()


def get_contextual_logger(name: str, **context) -> ContextualLogger:
    """Get a contextual logger with predefined context."""
    logger = logging_config.get_logger(name)
    return ContextualLogger(logger, context)


def get_log_statistics() -> Dict[str, Any]:
    """Get current log statistics and insights."""
    return log_aggregator.get_log_statistics()


# Custom log handler for aggregation
class AggregatingHandler(logging.Handler):
    """Log handler that aggregates log data for analysis."""
    
    def emit(self, record: logging.LogRecord) -> None:
        """Process log record for aggregation."""
        log_aggregator.process_log_record(record)


# Add aggregating handler to root logger
def add_log_aggregation():
    """Add log aggregation to the root logger."""
    root_logger = logging.getLogger()
    aggregating_handler = AggregatingHandler()
    aggregating_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(aggregating_handler)


if __name__ == "__main__":
    # Test logging configuration
    setup_enhanced_logging()
    add_log_aggregation()
    
    logger = get_contextual_logger("test", service="ai-research-agent")
    logger.info("Test log message", extra={"test_key": "test_value"})
    logger.error("Test error message", extra={"error_code": "TEST_001"})
    
    print(json.dumps(get_log_statistics(), indent=2))