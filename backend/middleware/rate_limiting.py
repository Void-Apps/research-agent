"""
Rate limiting and request throttling middleware for the AI Research Agent API.

This module provides comprehensive rate limiting capabilities including:
- Per-IP rate limiting
- Per-user rate limiting
- Global rate limiting
- Sliding window rate limiting
- Request throttling with backoff
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timedelta
import os

from monitoring import monitor_logger, performance_monitor

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """Sliding window rate limiter implementation."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, key: str) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        async with self.lock:
            now = time.time()
            window_start = now - self.window_seconds
            
            # Clean old requests outside the window
            request_times = self.requests[key]
            while request_times and request_times[0] < window_start:
                request_times.popleft()
            
            # Check if under limit
            current_requests = len(request_times)
            is_allowed = current_requests < self.max_requests
            
            if is_allowed:
                request_times.append(now)
            
            # Calculate reset time
            reset_time = int(now + self.window_seconds) if request_times else int(now)
            
            rate_limit_info = {
                "limit": self.max_requests,
                "remaining": max(0, self.max_requests - current_requests - (1 if is_allowed else 0)),
                "reset": reset_time,
                "window_seconds": self.window_seconds
            }
            
            return is_allowed, rate_limit_info


class TokenBucketRateLimiter:
    """Token bucket rate limiter for smooth request throttling."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.buckets: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            "tokens": capacity,
            "last_refill": time.time()
        })
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, tokens_required: int = 1) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed and consume tokens.
        
        Returns:
            Tuple of (is_allowed, bucket_info)
        """
        async with self.lock:
            now = time.time()
            bucket = self.buckets[key]
            
            # Refill tokens based on time elapsed
            time_elapsed = now - bucket["last_refill"]
            tokens_to_add = time_elapsed * self.refill_rate
            bucket["tokens"] = min(self.capacity, bucket["tokens"] + tokens_to_add)
            bucket["last_refill"] = now
            
            # Check if enough tokens available
            is_allowed = bucket["tokens"] >= tokens_required
            
            if is_allowed:
                bucket["tokens"] -= tokens_required
            
            bucket_info = {
                "capacity": self.capacity,
                "tokens": bucket["tokens"],
                "refill_rate": self.refill_rate,
                "tokens_required": tokens_required
            }
            
            return is_allowed, bucket_info


class RateLimitManager:
    """Comprehensive rate limiting manager."""
    
    def __init__(self):
        # Load configuration from environment
        self.global_limit = int(os.getenv("RATE_LIMIT_GLOBAL_PER_MINUTE", "1000"))
        self.ip_limit = int(os.getenv("RATE_LIMIT_IP_PER_MINUTE", "100"))
        self.user_limit = int(os.getenv("RATE_LIMIT_USER_PER_MINUTE", "200"))
        self.research_limit = int(os.getenv("RATE_LIMIT_RESEARCH_PER_HOUR", "50"))
        
        # Initialize rate limiters
        self.global_limiter = SlidingWindowRateLimiter(self.global_limit, 60)  # per minute
        self.ip_limiter = SlidingWindowRateLimiter(self.ip_limit, 60)  # per minute
        self.user_limiter = SlidingWindowRateLimiter(self.user_limit, 60)  # per minute
        self.research_limiter = SlidingWindowRateLimiter(self.research_limit, 3600)  # per hour
        
        # Token bucket for smooth throttling
        self.throttle_limiter = TokenBucketRateLimiter(
            capacity=int(os.getenv("THROTTLE_BUCKET_CAPACITY", "10")),
            refill_rate=float(os.getenv("THROTTLE_REFILL_RATE", "2.0"))  # 2 tokens per second
        )
        
        # Whitelist for bypassing rate limits
        self.whitelist_ips = set(os.getenv("RATE_LIMIT_WHITELIST_IPS", "").split(","))
        self.whitelist_ips.discard("")  # Remove empty strings
        
        logger.info(f"Rate limiting initialized - Global: {self.global_limit}/min, IP: {self.ip_limit}/min, User: {self.user_limit}/min, Research: {self.research_limit}/hour")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers first (for proxy/load balancer setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (from headers, auth, etc.)."""
        # Check for user ID in headers
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return user_id
        
        # Could also extract from JWT token, session, etc.
        # For now, return None if not provided
        return None
    
    async def check_rate_limits(self, request: Request) -> Optional[JSONResponse]:
        """
        Check all applicable rate limits for the request.
        
        Returns:
            JSONResponse with 429 status if rate limited, None if allowed
        """
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        path = request.url.path
        
        # Skip rate limiting for whitelisted IPs
        if client_ip in self.whitelist_ips:
            monitor_logger.info(
                "Request bypassed rate limiting (whitelisted IP)",
                extra={"client_ip": client_ip, "path": path}
            )
            return None
        
        # Check global rate limit
        global_allowed, global_info = await self.global_limiter.is_allowed("global")
        if not global_allowed:
            monitor_logger.warning(
                "Request blocked by global rate limit",
                extra={"client_ip": client_ip, "path": path, "limit_info": global_info}
            )
            return self._create_rate_limit_response("Global rate limit exceeded", global_info)
        
        # Check IP-based rate limit
        ip_allowed, ip_info = await self.ip_limiter.is_allowed(client_ip)
        if not ip_allowed:
            monitor_logger.warning(
                "Request blocked by IP rate limit",
                extra={"client_ip": client_ip, "path": path, "limit_info": ip_info}
            )
            return self._create_rate_limit_response("IP rate limit exceeded", ip_info)
        
        # Check user-based rate limit (if user ID available)
        if user_id:
            user_allowed, user_info = await self.user_limiter.is_allowed(user_id)
            if not user_allowed:
                monitor_logger.warning(
                    "Request blocked by user rate limit",
                    extra={"client_ip": client_ip, "user_id": user_id, "path": path, "limit_info": user_info}
                )
                return self._create_rate_limit_response("User rate limit exceeded", user_info)
        
        # Check research-specific rate limit for research endpoints
        if "/api/research/" in path and path != "/api/research/health":
            research_key = user_id if user_id else client_ip
            research_allowed, research_info = await self.research_limiter.is_allowed(research_key)
            if not research_allowed:
                monitor_logger.warning(
                    "Request blocked by research rate limit",
                    extra={"client_ip": client_ip, "user_id": user_id, "path": path, "limit_info": research_info}
                )
                return self._create_rate_limit_response("Research rate limit exceeded", research_info)
        
        # Check throttling (token bucket)
        throttle_key = user_id if user_id else client_ip
        throttle_allowed, throttle_info = await self.throttle_limiter.is_allowed(throttle_key)
        if not throttle_allowed:
            monitor_logger.warning(
                "Request throttled",
                extra={"client_ip": client_ip, "user_id": user_id, "path": path, "throttle_info": throttle_info}
            )
            return self._create_throttle_response("Request throttled - too many requests", throttle_info)
        
        # Log successful rate limit check
        monitor_logger.debug(
            "Request passed rate limiting",
            extra={
                "client_ip": client_ip,
                "user_id": user_id,
                "path": path,
                "global_remaining": global_info["remaining"],
                "ip_remaining": ip_info["remaining"]
            }
        )
        
        return None
    
    def _create_rate_limit_response(self, message: str, limit_info: Dict[str, any]) -> JSONResponse:
        """Create a rate limit exceeded response."""
        headers = {
            "X-RateLimit-Limit": str(limit_info["limit"]),
            "X-RateLimit-Remaining": str(limit_info["remaining"]),
            "X-RateLimit-Reset": str(limit_info["reset"]),
            "Retry-After": str(limit_info.get("window_seconds", 60))
        }
        
        content = {
            "error": "rate_limit_exceeded",
            "message": message,
            "limit": limit_info["limit"],
            "remaining": limit_info["remaining"],
            "reset": limit_info["reset"],
            "retry_after": limit_info.get("window_seconds", 60)
        }
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=content,
            headers=headers
        )
    
    def _create_throttle_response(self, message: str, throttle_info: Dict[str, any]) -> JSONResponse:
        """Create a throttling response."""
        # Calculate retry after based on token refill rate
        retry_after = max(1, int(throttle_info["tokens_required"] / throttle_info["refill_rate"]))
        
        headers = {
            "X-Throttle-Capacity": str(throttle_info["capacity"]),
            "X-Throttle-Tokens": str(int(throttle_info["tokens"])),
            "X-Throttle-RefillRate": str(throttle_info["refill_rate"]),
            "Retry-After": str(retry_after)
        }
        
        content = {
            "error": "request_throttled",
            "message": message,
            "capacity": throttle_info["capacity"],
            "tokens": int(throttle_info["tokens"]),
            "refill_rate": throttle_info["refill_rate"],
            "retry_after": retry_after
        }
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=content,
            headers=headers
        )
    
    async def get_rate_limit_status(self, request: Request) -> Dict[str, any]:
        """Get current rate limit status for debugging/monitoring."""
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        
        # Get current status from all limiters
        _, global_info = await self.global_limiter.is_allowed("global")
        _, ip_info = await self.ip_limiter.is_allowed(client_ip)
        
        status_info = {
            "client_ip": client_ip,
            "user_id": user_id,
            "global_limit": global_info,
            "ip_limit": ip_info,
            "whitelisted": client_ip in self.whitelist_ips
        }
        
        if user_id:
            _, user_info = await self.user_limiter.is_allowed(user_id)
            status_info["user_limit"] = user_info
        
        return status_info


# Global rate limit manager
rate_limit_manager = RateLimitManager()


async def rate_limiting_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting."""
    start_time = time.time()
    
    # Check rate limits
    rate_limit_response = await rate_limit_manager.check_rate_limits(request)
    if rate_limit_response:
        # Record rate limit hit
        performance_monitor.record_operation(
            operation="rate_limit_hit",
            duration_ms=(time.time() - start_time) * 1000,
            success=False,
            client_ip=rate_limit_manager._get_client_ip(request),
            path=request.url.path
        )
        return rate_limit_response
    
    # Process request normally
    response = await call_next(request)
    
    # Record successful rate limit check
    performance_monitor.record_operation(
        operation="rate_limit_check",
        duration_ms=(time.time() - start_time) * 1000,
        success=True,
        client_ip=rate_limit_manager._get_client_ip(request),
        path=request.url.path
    )
    
    return response