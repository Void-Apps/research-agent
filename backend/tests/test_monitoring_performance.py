"""
Tests for monitoring, logging, and performance optimization features.
"""

import pytest
import asyncio
import logging
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from monitoring import (
    PerformanceMonitor, AlertManager, monitor_async_operation, 
    monitor_sync_operation, get_monitoring_summary
)
from performance_optimizer import (
    DatabaseOptimizer, ConnectionPoolOptimizer, PerformanceProfiler,
    run_comprehensive_optimization
)
from logging_config import (
    LoggingConfig, ContextualLogger, LogAggregator,
    setup_enhanced_logging, get_log_statistics
)


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    def test_performance_monitor_initialization(self):
        """Test performance monitor initialization."""
        monitor = PerformanceMonitor()
        assert monitor.operation_metrics == {}
        assert monitor.request_metrics == {}
    
    def test_record_operation(self):
        """Test recording operation metrics."""
        monitor = PerformanceMonitor()
        
        # Record successful operation
        monitor.record_operation("test_operation", 150.5, success=True, user_id="test_user")
        
        assert "test_operation" in monitor.operation_metrics
        metrics = monitor.operation_metrics["test_operation"]
        assert metrics["total_calls"] == 1
        assert metrics["success_count"] == 1
        assert metrics["error_count"] == 0
        assert metrics["avg_duration_ms"] == 150.5
        assert metrics["min_duration_ms"] == 150.5
        assert metrics["max_duration_ms"] == 150.5
    
    def test_record_failed_operation(self):
        """Test recording failed operation metrics."""
        monitor = PerformanceMonitor()
        
        # Record failed operation
        monitor.record_operation("test_operation", 250.0, success=False, error="Test error")
        
        metrics = monitor.operation_metrics["test_operation"]
        assert metrics["total_calls"] == 1
        assert metrics["success_count"] == 0
        assert metrics["error_count"] == 1
    
    def test_record_request(self):
        """Test recording request metrics."""
        monitor = PerformanceMonitor()
        
        monitor.record_request("req-123", "GET", "/api/test", 200, 125.0)
        
        assert "req-123" in monitor.request_metrics
        request_data = monitor.request_metrics["req-123"]
        assert request_data["method"] == "GET"
        assert request_data["path"] == "/api/test"
        assert request_data["status_code"] == 200
        assert request_data["duration_ms"] == 125.0
    
    def test_get_summary_metrics(self):
        """Test getting summary metrics."""
        monitor = PerformanceMonitor()
        
        # Add some test data
        monitor.record_operation("op1", 100.0, success=True)
        monitor.record_operation("op2", 200.0, success=False)
        monitor.record_request("req1", "GET", "/api/test", 200, 150.0)
        
        summary = monitor.get_summary_metrics()
        
        assert "operations" in summary
        assert "requests" in summary
        assert "errors" in summary
        
        operations = summary["operations"]
        assert operations["total_operations"] == 2
        assert operations["total_errors"] == 1
        assert operations["success_rate"] == 0.5


class TestAlertManager:
    """Test alert management functionality."""
    
    def test_alert_manager_initialization(self):
        """Test alert manager initialization."""
        alert_manager = AlertManager()
        assert alert_manager.consecutive_error_count == 0
        assert "error_rate" in alert_manager.alert_thresholds
        assert "response_time_ms" in alert_manager.alert_thresholds
        assert "consecutive_errors" in alert_manager.alert_thresholds
    
    def test_record_error(self):
        """Test recording errors for consecutive error tracking."""
        alert_manager = AlertManager()
        
        # Record errors below threshold
        for i in range(4):
            result = alert_manager.record_error()
            assert result is None
        
        # Record error that exceeds threshold
        result = alert_manager.record_error()
        assert result is not None
        assert result["type"] == "consecutive_errors"
        assert result["count"] == 5
    
    def test_record_success_resets_errors(self):
        """Test that recording success resets consecutive error count."""
        alert_manager = AlertManager()
        
        # Record some errors
        alert_manager.record_error()
        alert_manager.record_error()
        assert alert_manager.consecutive_error_count == 2
        
        # Record success
        alert_manager.record_success()
        assert alert_manager.consecutive_error_count == 0


class TestMonitoringDecorators:
    """Test monitoring decorators."""
    
    @pytest.mark.asyncio
    async def test_monitor_async_operation_decorator(self):
        """Test async operation monitoring decorator."""
        
        @monitor_async_operation("test_async_op")
        async def test_async_function():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await test_async_function()
        assert result == "success"
    
    def test_monitor_sync_operation_decorator(self):
        """Test sync operation monitoring decorator."""
        
        @monitor_sync_operation("test_sync_op")
        def test_sync_function():
            time.sleep(0.1)
            return "success"
        
        result = test_sync_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_monitor_async_operation_with_exception(self):
        """Test async operation monitoring with exception."""
        
        @monitor_async_operation("test_async_error")
        async def test_async_error_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await test_async_error_function()


class TestDatabaseOptimizer:
    """Test database optimization functionality."""
    
    def test_database_optimizer_initialization(self):
        """Test database optimizer initialization."""
        optimizer = DatabaseOptimizer()
        assert optimizer.query_stats == {}
        assert optimizer.slow_query_threshold_ms == 1000
    
    @pytest.mark.asyncio
    async def test_analyze_collection_stats(self):
        """Test collection statistics analysis."""
        optimizer = DatabaseOptimizer()
        
        # Mock database
        mock_database = Mock()
        mock_database.command = AsyncMock(return_value={
            "count": 100,
            "storageSize": 1024 * 1024,  # 1MB
            "avgObjSize": 1024,
            "totalIndexSize": 512 * 1024  # 512KB
        })
        
        mock_collection = Mock()
        mock_collection.list_indexes = AsyncMock()
        mock_collection.list_indexes.return_value.__aiter__ = AsyncMock(return_value=iter([
            {"name": "index1"}, {"name": "index2"}
        ]))
        
        mock_database.__getitem__ = Mock(return_value=mock_collection)
        
        stats = await optimizer._analyze_collection_stats(mock_database)
        
        assert "research_queries" in stats
        assert "research_results" in stats
        assert "cache_metadata" in stats


class TestConnectionPoolOptimizer:
    """Test connection pool optimization functionality."""
    
    @pytest.mark.asyncio
    async def test_analyze_connection_pool(self):
        """Test connection pool analysis."""
        optimizer = ConnectionPoolOptimizer()
        
        # Mock database
        mock_database = Mock()
        mock_database.command = AsyncMock(return_value={
            "connections": {
                "current": 10,
                "available": 90,
                "totalCreated": 15,
                "active": 8
            }
        })
        
        analysis = await optimizer.analyze_connection_pool(mock_database)
        
        assert "timestamp" in analysis
        assert "current_connections" in analysis
        assert "available_connections" in analysis
        assert "recommendations" in analysis
        assert analysis["current_connections"] == 10
        assert analysis["available_connections"] == 90


class TestPerformanceProfiler:
    """Test performance profiling functionality."""
    
    @pytest.mark.asyncio
    async def test_profile_application_performance(self):
        """Test application performance profiling."""
        profiler = PerformanceProfiler()
        
        with patch('psutil.Process') as mock_process:
            mock_instance = Mock()
            mock_instance.memory_info.return_value = Mock(rss=100 * 1024 * 1024)  # 100MB
            mock_instance.memory_percent.return_value = 25.0
            mock_instance.cpu_percent.return_value = 15.0
            mock_instance.num_threads.return_value = 5
            mock_process.return_value = mock_instance
            
            with patch('gc.get_stats', return_value=[]), \
                 patch('gc.garbage', []), \
                 patch('gc.get_threshold', return_value=(700, 10, 10)):
                
                profile = await profiler.profile_application_performance()
                
                assert "timestamp" in profile
                assert "process_info" in profile
                assert "garbage_collection" in profile
                assert "recommendations" in profile
                
                process_info = profile["process_info"]
                assert process_info["memory_usage_mb"] == 100.0
                assert process_info["memory_percent"] == 25.0
                assert process_info["cpu_percent"] == 15.0
                assert process_info["thread_count"] == 5


class TestLoggingConfig:
    """Test logging configuration functionality."""
    
    def test_logging_config_initialization(self):
        """Test logging configuration initialization."""
        config = LoggingConfig()
        assert config.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert config.log_format in ["structured", "simple"]
        assert isinstance(config.log_file_enabled, bool)
    
    def test_setup_logging(self):
        """Test logging setup."""
        config = LoggingConfig()
        
        # This should not raise an exception
        config.setup_logging()
        
        # Check that root logger has handlers
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
    
    def test_get_logger(self):
        """Test getting a configured logger."""
        config = LoggingConfig()
        logger = config.get_logger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"


class TestContextualLogger:
    """Test contextual logger functionality."""
    
    def test_contextual_logger_initialization(self):
        """Test contextual logger initialization."""
        base_logger = logging.getLogger("test")
        context = {"user_id": "test_user", "operation": "test_op"}
        
        contextual_logger = ContextualLogger(base_logger, context)
        
        assert contextual_logger.logger == base_logger
        assert contextual_logger.context == context
    
    def test_with_context(self):
        """Test adding additional context."""
        base_logger = logging.getLogger("test")
        initial_context = {"user_id": "test_user"}
        
        contextual_logger = ContextualLogger(base_logger, initial_context)
        new_logger = contextual_logger.with_context(operation="test_op", request_id="req-123")
        
        expected_context = {
            "user_id": "test_user",
            "operation": "test_op",
            "request_id": "req-123"
        }
        assert new_logger.context == expected_context


class TestLogAggregator:
    """Test log aggregation functionality."""
    
    def test_log_aggregator_initialization(self):
        """Test log aggregator initialization."""
        aggregator = LogAggregator()
        
        assert aggregator.log_stats["total_logs"] == 0
        assert aggregator.log_stats["by_level"] == {}
        assert aggregator.log_stats["by_module"] == {}
        assert aggregator.log_stats["errors"] == []
    
    def test_process_log_record(self):
        """Test processing log records."""
        aggregator = LogAggregator()
        
        # Create mock log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.operation = "test_operation"
        
        aggregator.process_log_record(record)
        
        assert aggregator.log_stats["total_logs"] == 1
        assert aggregator.log_stats["by_level"]["INFO"] == 1
        assert aggregator.log_stats["by_module"]["test_module"] == 1
        assert aggregator.log_stats["by_operation"]["test_operation"] == 1
    
    def test_process_error_record(self):
        """Test processing error log records."""
        aggregator = LogAggregator()
        
        # Create mock error record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Test error",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        
        aggregator.process_log_record(record)
        
        assert len(aggregator.log_stats["errors"]) == 1
        error_entry = aggregator.log_stats["errors"][0]
        assert error_entry["level"] == "ERROR"
        assert error_entry["message"] == "Test error"
        assert error_entry["module"] == "test_module"
    
    def test_get_log_statistics(self):
        """Test getting log statistics."""
        aggregator = LogAggregator()
        
        # Add some test data
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        
        aggregator.process_log_record(record)
        
        stats = aggregator.get_log_statistics()
        
        assert "timestamp" in stats
        assert "statistics" in stats
        assert "insights" in stats
        
        statistics = stats["statistics"]
        assert statistics["total_logs"] == 1
        assert statistics["by_level"]["INFO"] == 1


class TestComprehensiveOptimization:
    """Test comprehensive optimization functionality."""
    
    @pytest.mark.asyncio
    async def test_run_comprehensive_optimization(self):
        """Test running comprehensive optimization."""
        
        with patch('performance_optimizer.get_database') as mock_get_db:
            mock_database = Mock()
            mock_get_db.return_value = mock_database
            
            # Mock the optimizer methods
            with patch.object(DatabaseOptimizer, 'optimize_collections', new_callable=AsyncMock) as mock_optimize, \
                 patch.object(DatabaseOptimizer, 'analyze_slow_queries', new_callable=AsyncMock) as mock_slow_queries, \
                 patch.object(ConnectionPoolOptimizer, 'analyze_connection_pool', new_callable=AsyncMock) as mock_pool, \
                 patch.object(PerformanceProfiler, 'profile_application_performance', new_callable=AsyncMock) as mock_profile:
                
                mock_optimize.return_value = {"optimizations_applied": ["test"]}
                mock_slow_queries.return_value = {"slow_queries_found": 0}
                mock_pool.return_value = {"current_connections": 5}
                mock_profile.return_value = {"process_info": {"memory_usage_mb": 100}}
                
                result = await run_comprehensive_optimization()
                
                assert "timestamp" in result
                assert "optimization_results" in result
                
                optimization_results = result["optimization_results"]
                assert "database" in optimization_results
                assert "slow_queries" in optimization_results
                assert "connection_pool" in optimization_results
                assert "performance_profile" in optimization_results


@pytest.mark.asyncio
async def test_monitoring_integration():
    """Test integration between monitoring components."""
    
    # Test that monitoring summary includes all components
    summary = get_monitoring_summary()
    
    assert "timestamp" in summary
    assert "performance" in summary
    assert "alerts" in summary
    assert "system_health" in summary


def test_log_statistics_integration():
    """Test log statistics integration."""
    
    # Set up logging and add some test logs
    setup_enhanced_logging()
    
    logger = logging.getLogger("test_integration")
    logger.info("Test info message")
    logger.error("Test error message")
    
    # Get statistics
    stats = get_log_statistics()
    
    assert "timestamp" in stats
    assert "statistics" in stats
    assert "insights" in stats


if __name__ == "__main__":
    pytest.main([__file__])