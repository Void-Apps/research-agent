#!/usr/bin/env python3
"""
Demonstration script for monitoring, logging, and performance optimization features.

This script showcases the comprehensive monitoring capabilities implemented
for the AI Research Agent application.
"""

import asyncio
import logging
import time
import json
from datetime import datetime

from monitoring import (
    performance_monitor, monitor_async_operation, monitor_sync_operation,
    get_monitoring_summary, alert_manager
)
from logging_config import (
    setup_enhanced_logging, get_contextual_logger, get_log_statistics
)
from performance_optimizer import (
    performance_profiler, run_comprehensive_optimization
)


async def demo_monitoring_features():
    """Demonstrate monitoring and performance features."""
    
    print("🚀 AI Research Agent - Monitoring & Performance Demo")
    print("=" * 60)
    
    # Set up enhanced logging
    print("\n1. Setting up enhanced logging...")
    setup_enhanced_logging()
    
    # Get contextual logger
    logger = get_contextual_logger(
        "demo", 
        service="ai-research-agent",
        component="demo",
        user_id="demo_user"
    )
    
    logger.info("Demo started", extra={"demo_phase": "initialization"})
    
    # Demonstrate performance monitoring
    print("\n2. Demonstrating performance monitoring...")
    
    @monitor_async_operation("demo_async_operation")
    async def demo_async_task():
        """Demo async task with monitoring."""
        await asyncio.sleep(0.5)  # Simulate work
        logger.info("Async task completed", extra={"task_type": "async_demo"})
        return "async_result"
    
    @monitor_sync_operation("demo_sync_operation")
    def demo_sync_task():
        """Demo sync task with monitoring."""
        time.sleep(0.3)  # Simulate work
        logger.info("Sync task completed", extra={"task_type": "sync_demo"})
        return "sync_result"
    
    # Run demo operations
    print("   - Running async operation...")
    async_result = await demo_async_task()
    
    print("   - Running sync operation...")
    sync_result = demo_sync_task()
    
    # Simulate some errors for alert testing
    print("   - Simulating error conditions...")
    try:
        @monitor_async_operation("demo_error_operation")
        async def demo_error_task():
            logger.error("Simulated error occurred", extra={"error_type": "demo_error"})
            raise ValueError("Demo error for testing")
        
        await demo_error_task()
    except ValueError:
        pass  # Expected error
    
    # Record some manual metrics
    performance_monitor.record_operation("manual_operation", 150.0, success=True, source="demo")
    performance_monitor.record_operation("manual_operation", 200.0, success=False, source="demo", error="Demo error")
    performance_monitor.record_request("demo-req-1", "GET", "/api/demo", 200, 125.0)
    performance_monitor.record_request("demo-req-2", "POST", "/api/demo", 500, 250.0)
    
    # Test alert manager
    print("\n3. Testing alert management...")
    for i in range(6):  # Trigger consecutive error alert
        alert = alert_manager.record_error()
        if alert:
            print(f"   🚨 Alert triggered: {alert['type']} - {alert['count']} consecutive errors")
            break
    
    alert_manager.record_success()  # Reset
    
    # Get monitoring summary
    print("\n4. Getting monitoring summary...")
    summary = get_monitoring_summary()
    
    print(f"   - Total operations: {summary['performance']['operations']['total_operations']}")
    print(f"   - Total errors: {summary['performance']['operations']['total_errors']}")
    print(f"   - Success rate: {summary['performance']['operations']['success_rate']:.2%}")
    
    # Show operation breakdown
    operations = summary['performance']['operations']['operation_breakdown']
    print("\n   Operation breakdown:")
    for op_name, metrics in operations.items():
        print(f"     • {op_name}: {metrics['total_calls']} calls, "
              f"{metrics['avg_duration_ms']:.1f}ms avg, "
              f"{metrics['success_count']}/{metrics['total_calls']} success")
    
    # Get log statistics
    print("\n5. Getting log statistics...")
    log_stats = get_log_statistics()
    
    print(f"   - Total logs: {log_stats['statistics']['total_logs']}")
    print(f"   - By level: {log_stats['statistics']['by_level']}")
    print(f"   - Recent errors: {len(log_stats['statistics']['errors'])}")
    
    if log_stats['insights']:
        print("   - Insights:")
        for insight in log_stats['insights']:
            print(f"     • {insight}")
    
    # Performance profiling
    print("\n6. Running performance profiling...")
    profile = await performance_profiler.profile_application_performance()
    
    process_info = profile['process_info']
    print(f"   - Memory usage: {process_info['memory_usage_mb']:.1f} MB "
          f"({process_info['memory_percent']:.1f}%)")
    print(f"   - CPU usage: {process_info['cpu_percent']:.1f}%")
    print(f"   - Thread count: {process_info['thread_count']}")
    
    if profile['recommendations']:
        print("   - Recommendations:")
        for rec in profile['recommendations']:
            print(f"     • {rec}")
    
    # Demonstrate comprehensive optimization (mock database)
    print("\n7. Demonstrating optimization capabilities...")
    print("   (Note: Database optimization requires actual database connection)")
    
    # Show final summary
    print("\n8. Final monitoring summary...")
    final_summary = get_monitoring_summary()
    
    print(f"   - System health: {final_summary['system_health']}")
    
    alerts = final_summary['alerts']['alerts']
    if alerts:
        print("   - Active alerts:")
        for alert in alerts:
            print(f"     🚨 {alert['type']}: {alert}")
    else:
        print("   - No active alerts ✅")
    
    logger.info("Demo completed successfully", extra={"demo_phase": "completion"})
    
    print("\n" + "=" * 60)
    print("✅ Monitoring & Performance Demo Complete!")
    print("\nKey features demonstrated:")
    print("• Structured logging with contextual information")
    print("• Performance monitoring with decorators")
    print("• Operation metrics collection and analysis")
    print("• Alert management and threshold monitoring")
    print("• Log aggregation and statistical analysis")
    print("• Performance profiling and system metrics")
    print("• Comprehensive monitoring dashboard data")
    
    return {
        "demo_results": {
            "async_result": async_result,
            "sync_result": sync_result,
            "monitoring_summary": summary,
            "log_statistics": log_stats,
            "performance_profile": profile
        }
    }


async def demo_rate_limiting():
    """Demonstrate rate limiting capabilities."""
    print("\n🔒 Rate Limiting Demo")
    print("-" * 30)
    
    from middleware.rate_limiting import rate_limit_manager
    
    print(f"Rate limiting configuration:")
    print(f"• Global limit: {rate_limit_manager.global_limit} requests/minute")
    print(f"• IP limit: {rate_limit_manager.ip_limit} requests/minute")
    print(f"• User limit: {rate_limit_manager.user_limit} requests/minute")
    print(f"• Research limit: {rate_limit_manager.research_limit} requests/hour")
    print(f"• Whitelisted IPs: {len(rate_limit_manager.whitelist_ips)}")


def demo_logging_formats():
    """Demonstrate different logging formats and features."""
    print("\n📝 Logging Features Demo")
    print("-" * 30)
    
    # Get different types of loggers
    basic_logger = logging.getLogger("basic_demo")
    contextual_logger = get_contextual_logger(
        "contextual_demo",
        user_id="demo_user_123",
        operation="demo_operation",
        request_id="req-demo-456"
    )
    
    # Demonstrate different log levels
    basic_logger.debug("Debug message - detailed information")
    basic_logger.info("Info message - general information")
    basic_logger.warning("Warning message - something unexpected")
    basic_logger.error("Error message - something went wrong")
    
    # Demonstrate contextual logging
    contextual_logger.info("Contextual info message", extra={"step": "initialization"})
    contextual_logger.warning("Contextual warning", extra={"validation_failed": True})
    
    # Demonstrate performance logging
    contextual_logger.info(
        "Operation completed",
        extra={
            "duration_ms": 150.5,
            "success": True,
            "records_processed": 42
        }
    )
    
    # Demonstrate error logging with context
    try:
        raise ValueError("Demo exception for logging")
    except ValueError as e:
        contextual_logger.error(
            "Exception occurred during demo",
            extra={"error_code": "DEMO_001"},
            exc_info=True
        )


if __name__ == "__main__":
    print("Starting AI Research Agent Monitoring Demo...")
    
    # Run the main demo
    results = asyncio.run(demo_monitoring_features())
    
    # Run additional demos
    asyncio.run(demo_rate_limiting())
    demo_logging_formats()
    
    print(f"\n📊 Demo completed at {datetime.now().isoformat()}")
    print("Check the logs and monitoring endpoints for detailed information!")