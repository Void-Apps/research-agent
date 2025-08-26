# Monitoring, Logging, and Performance Optimization

This document describes the comprehensive monitoring, logging, and performance optimization features implemented for the AI Research Agent application.

## Overview

The monitoring system provides:
- **Structured Logging**: JSON-formatted logs with contextual information
- **Performance Monitoring**: Operation timing and metrics collection
- **Alert Management**: Threshold-based alerting for system health
- **Database Optimization**: Query optimization and indexing
- **Rate Limiting**: Request throttling and abuse prevention
- **Performance Profiling**: System resource monitoring

## Features Implemented

### 1. Structured Logging (`logging_config.py`)

#### Enhanced Logging Configuration
- JSON-formatted structured logs
- Contextual information (user_id, request_id, operation)
- Log rotation and file management
- Multiple log levels and filtering
- Service metadata inclusion

#### Usage Examples
```python
from logging_config import get_contextual_logger

# Get a contextual logger
logger = get_contextual_logger(
    "my_service",
    user_id="user123",
    operation="data_processing"
)

# Log with additional context
logger.info("Processing started", extra={"batch_size": 100})
logger.error("Processing failed", extra={"error_code": "PROC_001"})
```

### 2. Performance Monitoring (`monitoring.py`)

#### Operation Monitoring
- Automatic timing of operations
- Success/failure tracking
- Performance metrics aggregation
- Request/response monitoring

#### Usage Examples
```python
from monitoring import monitor_async_operation, monitor_sync_operation

# Monitor async operations
@monitor_async_operation("data_fetch")
async def fetch_data():
    # Your async code here
    pass

# Monitor sync operations
@monitor_sync_operation("data_process")
def process_data():
    # Your sync code here
    pass
```

### 3. Performance Optimization (`performance_optimizer.py`)

#### Database Optimization
- Automatic index creation
- Query performance analysis
- Collection statistics
- Slow query detection

#### Connection Pool Optimization
- Connection usage analysis
- Pool size recommendations
- Performance insights

#### Application Profiling
- Memory usage monitoring
- CPU utilization tracking
- Thread count analysis
- Performance recommendations

### 4. Rate Limiting (`middleware/rate_limiting.py`)

#### Multi-Level Rate Limiting
- Global rate limits
- Per-IP rate limits
- Per-user rate limits
- Research-specific limits
- Token bucket throttling

#### Configuration
```bash
# Environment variables
RATE_LIMIT_GLOBAL_PER_MINUTE=1000
RATE_LIMIT_IP_PER_MINUTE=100
RATE_LIMIT_USER_PER_MINUTE=200
RATE_LIMIT_RESEARCH_PER_HOUR=50
RATE_LIMIT_WHITELIST_IPS=127.0.0.1,192.168.1.1
```

### 5. Alert Management

#### Alert Types
- High error rates
- Slow operations
- Consecutive errors
- Resource usage thresholds

#### Alert Configuration
```python
alert_thresholds = {
    "error_rate": 0.1,  # 10% error rate
    "response_time_ms": 5000,  # 5 second response time
    "consecutive_errors": 5
}
```

## API Endpoints

### Health and Monitoring Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Basic health check |
| `/api/metrics` | GET | System and application metrics |
| `/api/monitoring` | GET | Comprehensive monitoring data |
| `/api/dashboard` | GET | Full monitoring dashboard data |
| `/api/dashboard/ui` | GET | HTML monitoring dashboard |

### Performance Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/performance/optimize` | GET | Run comprehensive optimization |
| `/api/performance/profile` | GET | Get performance profiling data |
| `/api/database/analyze` | GET | Analyze database performance |
| `/api/database/optimize` | POST | Optimize database collections |

### Logging Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/logs/statistics` | GET | Get logging statistics and insights |
| `/api/rate-limit-status` | GET | Get current rate limit status |

## Monitoring Dashboard

Access the web-based monitoring dashboard at `/api/dashboard/ui` for:
- Real-time system metrics
- Performance charts
- Alert notifications
- Operation statistics
- Rate limiting status

## Configuration

### Environment Variables

```bash
# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=structured
LOG_FILE_ENABLED=true
LOG_FILE_PATH=logs/ai_research_agent.log
LOG_ROTATION_ENABLED=true
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# Rate Limiting
RATE_LIMIT_GLOBAL_PER_MINUTE=1000
RATE_LIMIT_IP_PER_MINUTE=100
RATE_LIMIT_USER_PER_MINUTE=200
RATE_LIMIT_RESEARCH_PER_HOUR=50

# Throttling
THROTTLE_BUCKET_CAPACITY=10
THROTTLE_REFILL_RATE=2.0

# Database
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=ai_research_agent
```

## Usage Examples

### 1. Basic Monitoring Setup

```python
from logging_config import setup_enhanced_logging
from monitoring import performance_monitor

# Set up enhanced logging
setup_enhanced_logging()

# Monitor an operation
with monitor_operation("my_operation"):
    # Your code here
    pass

# Get monitoring summary
summary = performance_monitor.get_summary_metrics()
```

### 2. Database Optimization

```python
from performance_optimizer import run_comprehensive_optimization

# Run full optimization
results = await run_comprehensive_optimization()
print(f"Optimizations applied: {results['optimization_results']}")
```

### 3. Custom Alerts

```python
from monitoring import alert_manager

# Check for alerts
alerts = alert_manager.check_all_alerts()
if alerts['alerts']:
    for alert in alerts['alerts']:
        print(f"Alert: {alert['type']} - {alert}")
```

## Best Practices

### 1. Logging
- Use contextual loggers with relevant metadata
- Include operation timing in performance-critical code
- Log errors with sufficient context for debugging
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)

### 2. Performance Monitoring
- Monitor all external API calls
- Track database operations
- Monitor resource-intensive operations
- Set up alerts for critical thresholds

### 3. Database Optimization
- Run optimization regularly (weekly/monthly)
- Monitor slow queries
- Review index usage
- Optimize based on query patterns

### 4. Rate Limiting
- Configure appropriate limits for your use case
- Monitor rate limit hits
- Use whitelisting for trusted sources
- Implement graceful degradation

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Check performance profile: `/api/performance/profile`
   - Review log aggregation settings
   - Monitor connection pool usage

2. **Slow Database Queries**
   - Run database analysis: `/api/database/analyze`
   - Check slow query logs
   - Optimize indexes: `/api/database/optimize`

3. **Rate Limiting Issues**
   - Check rate limit status: `/api/rate-limit-status`
   - Review whitelist configuration
   - Monitor rate limit metrics

4. **High Error Rates**
   - Check monitoring dashboard: `/api/dashboard`
   - Review error logs: `/api/logs/statistics`
   - Analyze alert conditions

## Testing

Run the monitoring tests:
```bash
python3 -m pytest tests/test_monitoring_performance.py -v
```

Run the monitoring demo:
```bash
python3 demo_monitoring.py
```

## Integration

The monitoring system is automatically integrated into:
- FastAPI application startup
- All API endpoints (via middleware)
- Database operations
- External service calls
- Error handling

No additional configuration is required for basic monitoring functionality.