from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import time
import logging
import uuid

from routers import research, health
from error_handlers import setup_error_handlers, get_error_metrics
from middleware.rate_limiting import rate_limiting_middleware, rate_limit_manager
from monitoring import performance_monitor
from logging_config import setup_enhanced_logging, add_log_aggregation, get_contextual_logger

# Load environment variables
load_dotenv()

# Set up enhanced logging
setup_enhanced_logging()
add_log_aggregation()

logger = get_contextual_logger(__name__, service="ai-research-agent", component="main")

app = FastAPI(
    title="AI Research Agent API",
    description="Backend API for AI Research Agent that provides comprehensive research capabilities",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Security middleware - only allow trusted hosts (skip in test environment)
if os.getenv("ENVIRONMENT") != "test":
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# CORS middleware configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Rate limiting middleware (applied first)
@app.middleware("http")
async def rate_limiting(request: Request, call_next):
    return await rate_limiting_middleware(request, call_next)

# Request timing and ID middleware
@app.middleware("http")
async def add_process_time_and_request_id(request: Request, call_next):
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Record request metrics
    performance_monitor.record_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=process_time * 1000
    )
    
    # Add headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    return response

# Set up comprehensive error handlers
setup_error_handlers(app)

# Include routers
app.include_router(research.router)
app.include_router(health.router)

@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "AI Research Agent API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level="info"
    )