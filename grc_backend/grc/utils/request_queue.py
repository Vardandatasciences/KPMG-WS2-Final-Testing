"""
Request Queuing and Rate Limiting for Phase 3
- Manages concurrent requests to prevent system overload
- Implements rate limiting per user/IP
- Provides queue status and wait time estimates
"""

import time
import threading
import logging
from collections import defaultdict, deque
from typing import Dict, Optional, Callable, Any
from functools import wraps
from django.http import JsonResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Global request queue
_request_queue = []
_queue_lock = threading.Lock()
_processing_count = 0
_max_concurrent = 2  # Process 2 requests at a time

# Rate limiting tracking (per IP/user)
_rate_limit_windows = defaultdict(lambda: deque())
_rate_limit_lock = threading.Lock()

# Default rate limits
DEFAULT_RATE_LIMIT = {
    "requests_per_minute": 10,
    "requests_per_hour": 100
}

def get_client_identifier(request) -> str:
    """Get unique identifier for rate limiting (IP or user ID)."""
    # Try to get user ID first
    if hasattr(request, 'user') and request.user.is_authenticated:
        return f"user_{request.user.id}"
    
    # Fall back to IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    
    return f"ip_{ip}"

def check_rate_limit(
    identifier: str,
    requests_per_minute: int = 10,
    requests_per_hour: int = 100
) -> tuple[bool, Optional[str]]:
    """
    Check if request is within rate limits.
    
    Returns:
        (allowed, error_message)
    """
    current_time = time.time()
    
    with _rate_limit_lock:
        window = _rate_limit_windows[identifier]
        
        # Remove old entries (older than 1 hour)
        while window and current_time - window[0] > 3600:
            window.popleft()
        
        # Check per-minute limit
        recent_minute = [t for t in window if current_time - t < 60]
        if len(recent_minute) >= requests_per_minute:
            return False, f"Rate limit exceeded: {requests_per_minute} requests per minute"
        
        # Check per-hour limit
        if len(window) >= requests_per_hour:
            return False, f"Rate limit exceeded: {requests_per_hour} requests per hour"
        
        # Add current request
        window.append(current_time)
        
        return True, None

def get_queue_position(request_id: str) -> Optional[int]:
    """Get position in queue for a request."""
    with _queue_lock:
        try:
            return _request_queue.index(request_id) + 1
        except ValueError:
            return None

def get_queue_status() -> Dict[str, Any]:
    """Get current queue status."""
    with _queue_lock:
        return {
            "queue_length": len(_request_queue),
            "processing": _processing_count,
            "max_concurrent": _max_concurrent,
            "estimated_wait_time": len(_request_queue) * 10  # Rough estimate: 10s per request
        }

def rate_limit_decorator(
    requests_per_minute: int = 10,
    requests_per_hour: int = 100
):
    """
    Decorator for rate limiting.
    
    Usage:
        @rate_limit_decorator(requests_per_minute=10)
        def my_view(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            identifier = get_client_identifier(request)
            allowed, error_msg = check_rate_limit(
                identifier,
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour
            )
            
            if not allowed:
                resp = JsonResponse({
                    'status': 'error',
                    'message': error_msg,
                    'rate_limit_info': {
                        'identifier': identifier,
                        'limit_per_minute': requests_per_minute,
                        'limit_per_hour': requests_per_hour
                    }
                }, status=429)
                resp['Access-Control-Allow-Origin'] = '*'
                return resp
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator

def queue_request(request_id: str) -> Dict[str, Any]:
    """
    Add request to queue.
    
    Returns:
        Dict with queue position and estimated wait time
    """
    with _queue_lock:
        if request_id not in _request_queue:
            _request_queue.append(request_id)
        
        position = _request_queue.index(request_id) + 1
        estimated_wait = (position - 1) * 10  # Rough estimate
    
    return {
        "queued": True,
        "queue_position": position,
        "estimated_wait_seconds": estimated_wait,
        "processing_count": _processing_count
    }

def start_processing(request_id: str) -> bool:
    """Mark request as processing."""
    global _processing_count
    
    with _queue_lock:
        if request_id in _request_queue:
            _request_queue.remove(request_id)
        
        if _processing_count >= _max_concurrent:
            return False
        
        _processing_count += 1
        return True

def finish_processing():
    """Mark processing as complete."""
    global _processing_count
    
    with _queue_lock:
        if _processing_count > 0:
            _processing_count -= 1

def process_with_queue(request_id: str, func: Callable, *args, **kwargs) -> Any:
    """
    Process a function with queuing.
    
    Usage:
        result = process_with_queue("req_123", my_function, arg1, arg2)
    """
    # Add to queue
    queue_info = queue_request(request_id)
    
    # Wait if not first in queue
    if queue_info["queue_position"] > 1:
        wait_time = queue_info["estimated_wait_seconds"]
        logger.info(f"⏳ Request {request_id} queued. Position: {queue_info['queue_position']}, Wait: {wait_time}s")
        time.sleep(min(wait_time, 60))  # Max wait 60s before checking again
    
    # Try to start processing
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        if start_processing(request_id):
            try:
                logger.info(f"🚀 Processing request {request_id}")
                result = func(*args, **kwargs)
                return result
            finally:
                finish_processing()
                logger.info(f"✅ Completed request {request_id}")
        else:
            # Wait a bit and retry
            time.sleep(2)
            retry_count += 1
    
    # If we couldn't start processing, return error
    raise RuntimeError("Could not start processing after queuing")

def clear_rate_limits():
    """Clear all rate limit tracking (useful for testing)."""
    global _rate_limit_windows
    with _rate_limit_lock:
        _rate_limit_windows.clear()

def get_rate_limit_stats(identifier: str) -> Dict[str, Any]:
    """Get rate limit statistics for an identifier."""
    with _rate_limit_lock:
        window = _rate_limit_windows.get(identifier, deque())
        current_time = time.time()
        
        # Count recent requests
        last_minute = [t for t in window if current_time - t < 60]
        last_hour = [t for t in window if current_time - t < 3600]
        
        return {
            "identifier": identifier,
            "requests_last_minute": len(last_minute),
            "requests_last_hour": len(last_hour),
            "total_requests": len(window)
        }












