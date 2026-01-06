"""
Vendor Rate Limiting Middleware - Advanced rate limiting with multiple strategies
"""

import logging
import time
from typing import Dict, Tuple
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings

vendor_rate_logger = logging.getLogger('vendor_security')


class VendorRateLimitMiddleware(MiddlewareMixin):
    """
    Advanced rate limiting middleware with multiple strategies
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.vendor_rate_limits = self._vendor_initialize_rate_limits()
        self.vendor_burst_limits = self._vendor_initialize_burst_limits()
    
    def _vendor_initialize_rate_limits(self) -> Dict[str, Dict]:
        """Initialize rate limit configurations for different endpoints"""
        return {
            'vendor_auth_endpoints': {
                'requests_per_minute': 5,
                'requests_per_hour': 20,
                'requests_per_day': 100,
                'burst_limit': 3,
                'lockout_duration': 300,  # 5 minutes
            },
            'vendor_api_endpoints': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'requests_per_day': 10000,
                'burst_limit': 10,
                'lockout_duration': 60,  # 1 minute
            },
            'vendor_upload_endpoints': {
                'requests_per_minute': 5,
                'requests_per_hour': 50,
                'requests_per_day': 200,
                'burst_limit': 2,
                'lockout_duration': 300,  # 5 minutes
            },
            'vendor_dashboard_endpoints': {
                'requests_per_minute': 30,
                'requests_per_hour': 500,
                'requests_per_day': 2000,
                'burst_limit': 5,
                'lockout_duration': 60,  # 1 minute
            }
        }
    
    def _vendor_initialize_burst_limits(self) -> Dict[str, int]:
        """Initialize burst protection limits"""
        return {
            'vendor_global_burst': 100,  # Max requests per second globally
            'vendor_ip_burst': 10,       # Max requests per second per IP
            'vendor_user_burst': 20,     # Max requests per second per user
        }
    
    def process_request(self, request: HttpRequest) -> HttpResponse:
        """Check rate limits for incoming requests"""
        
        # Skip rate limiting for certain endpoints
        if self._vendor_should_skip_rate_limiting(request):
            return None
        
        client_ip = self._vendor_get_client_ip(request)
        user_id = getattr(request.user, 'id', 'anonymous') if hasattr(request, 'user') else 'anonymous'
        
        # Check for active lockout
        if self._vendor_is_locked_out(client_ip, user_id):
            vendor_rate_logger.warning(
                f"Request blocked - active lockout for IP: {client_ip}, User: {user_id}",
                extra={
                    'ip_address': client_ip,
                    'user_id': user_id,
                    'path': request.path,
                    'action': 'rate_limit_lockout'
                }
            )
            return JsonResponse({
                'error': 'Too many requests - temporary lockout active',
                'retry_after': self._vendor_get_lockout_remaining_time(client_ip, user_id)
            }, status=429)
        
        # Check burst protection
        if self._vendor_check_burst_limit(request, client_ip, user_id):
            vendor_rate_logger.warning(
                f"Burst limit exceeded for IP: {client_ip}, User: {user_id}",
                extra={
                    'ip_address': client_ip,
                    'user_id': user_id,
                    'path': request.path,
                    'action': 'burst_limit_exceeded'
                }
            )
            return JsonResponse({
                'error': 'Request rate too high - please slow down'
            }, status=429)
        
        # Check standard rate limits
        rate_limit_result = self._vendor_check_rate_limits(request, client_ip, user_id)
        
        if not rate_limit_result['allowed']:
            # Increment violation counter
            self._vendor_increment_violation_counter(client_ip, user_id)
            
            vendor_rate_logger.warning(
                f"Rate limit exceeded for IP: {client_ip}, User: {user_id}",
                extra={
                    'ip_address': client_ip,
                    'user_id': user_id,
                    'path': request.path,
                    'limit_type': rate_limit_result['limit_type'],
                    'retry_after': rate_limit_result['retry_after'],
                    'action': 'rate_limit_exceeded'
                }
            )
            
            response_data = {
                'error': f"Rate limit exceeded - {rate_limit_result['limit_type']}",
                'retry_after': rate_limit_result['retry_after']
            }
            
            response = JsonResponse(response_data, status=429)
            response['Retry-After'] = str(rate_limit_result['retry_after'])
            return response
        
        # Update rate limit counters
        self._vendor_update_rate_counters(request, client_ip, user_id)
        
        return None
    
    def _vendor_should_skip_rate_limiting(self, request: HttpRequest) -> bool:
        """Check if rate limiting should be skipped"""
        skip_paths = [
            '/api/v1/health/',
            '/static/',
            '/media/',
        ]
        
        # Skip for superusers in debug mode
        if settings.DEBUG and hasattr(request, 'user') and hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            return True
        
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _vendor_get_rate_limit_category(self, request: HttpRequest) -> str:
        """Determine rate limit category based on endpoint"""
        path = request.path.lower()
        
        if any(auth_path in path for auth_path in ['/vendor-auth/', '/token/']):
            return 'vendor_auth_endpoints'
        elif any(upload_path in path for upload_path in ['/upload/', '/file/']):
            return 'vendor_upload_endpoints'
        elif '/vendor-dashboard/' in path:
            return 'vendor_dashboard_endpoints'
        else:
            return 'vendor_api_endpoints'
    
    def _vendor_check_burst_limit(self, request: HttpRequest, client_ip: str, user_id: str) -> bool:
        """Check burst protection limits"""
        current_time = int(time.time())
        
        # Check global burst limit
        global_key = f"vendor_burst_global_{current_time}"
        global_count = cache.get(global_key, 0)
        if global_count >= self.vendor_burst_limits['vendor_global_burst']:
            return True
        
        # Check IP burst limit
        ip_key = f"vendor_burst_ip_{client_ip}_{current_time}"
        ip_count = cache.get(ip_key, 0)
        if ip_count >= self.vendor_burst_limits['vendor_ip_burst']:
            return True
        
        # Check user burst limit (for authenticated users)
        if user_id != 'anonymous':
            user_key = f"vendor_burst_user_{user_id}_{current_time}"
            user_count = cache.get(user_key, 0)
            if user_count >= self.vendor_burst_limits['vendor_user_burst']:
                return True
        
        # Update burst counters
        cache.set(global_key, global_count + 1, 1)  # 1 second timeout
        cache.set(ip_key, ip_count + 1, 1)
        if user_id != 'anonymous':
            cache.set(user_key, cache.get(f"vendor_burst_user_{user_id}_{current_time}", 0) + 1, 1)
        
        return False
    
    def _vendor_check_rate_limits(self, request: HttpRequest, client_ip: str, user_id: str) -> Dict:
        """Check standard rate limits"""
        category = self._vendor_get_rate_limit_category(request)
        limits = self.vendor_rate_limits[category]
        
        current_time = int(time.time())
        
        # Check different time windows
        time_windows = [
            ('minute', 60, limits['requests_per_minute']),
            ('hour', 3600, limits['requests_per_hour']),
            ('day', 86400, limits['requests_per_day']),
        ]
        
        for window_name, window_seconds, limit in time_windows:
            window_start = current_time - window_seconds
            
            # Check IP-based limit
            ip_key = f"vendor_rate_{category}_ip_{client_ip}_{window_name}"
            ip_count = self._vendor_get_request_count_in_window(ip_key, window_start, current_time)
            
            if ip_count >= limit:
                return {
                    'allowed': False,
                    'limit_type': f'{window_name} limit exceeded for IP',
                    'retry_after': window_seconds - (current_time % window_seconds)
                }
            
            # Check user-based limit (for authenticated users)
            if user_id != 'anonymous':
                user_key = f"vendor_rate_{category}_user_{user_id}_{window_name}"
                user_count = self._vendor_get_request_count_in_window(user_key, window_start, current_time)
                
                if user_count >= limit:
                    return {
                        'allowed': False,
                        'limit_type': f'{window_name} limit exceeded for user',
                        'retry_after': window_seconds - (current_time % window_seconds)
                    }
        
        return {'allowed': True}
    
    def _vendor_get_request_count_in_window(self, key: str, window_start: int, current_time: int) -> int:
        """Get request count within a time window"""
        try:
            request_times = cache.get(key, [])
            # Filter requests within the window
            recent_requests = [t for t in request_times if t >= window_start]
            return len(recent_requests)
        except Exception:
            return 0
    
    def _vendor_update_rate_counters(self, request: HttpRequest, client_ip: str, user_id: str):
        """Update rate limit counters"""
        category = self._vendor_get_rate_limit_category(request)
        current_time = int(time.time())
        
        # Update counters for different time windows
        time_windows = ['minute', 'hour', 'day']
        
        for window_name in time_windows:
            # Update IP counter
            ip_key = f"vendor_rate_{category}_ip_{client_ip}_{window_name}"
            ip_times = cache.get(ip_key, [])
            ip_times.append(current_time)
            
            # Keep only recent timestamps based on window
            if window_name == 'minute':
                ip_times = [t for t in ip_times if t >= current_time - 60]
                timeout = 60
            elif window_name == 'hour':
                ip_times = [t for t in ip_times if t >= current_time - 3600]
                timeout = 3600
            else:  # day
                ip_times = [t for t in ip_times if t >= current_time - 86400]
                timeout = 86400
            
            cache.set(ip_key, ip_times, timeout)
            
            # Update user counter (for authenticated users)
            if user_id != 'anonymous':
                user_key = f"vendor_rate_{category}_user_{user_id}_{window_name}"
                user_times = cache.get(user_key, [])
                user_times.append(current_time)
                user_times = [t for t in user_times if t >= current_time - timeout]
                cache.set(user_key, user_times, timeout)
    
    def _vendor_increment_violation_counter(self, client_ip: str, user_id: str):
        """Increment rate limit violation counter and apply lockout if necessary"""
        violation_key = f"vendor_violations_{client_ip}_{user_id}"
        violation_count = cache.get(violation_key, 0) + 1
        
        # Apply lockout after multiple violations
        if violation_count >= 3:
            lockout_key = f"vendor_lockout_{client_ip}_{user_id}"
            cache.set(lockout_key, int(time.time()), 300)  # 5 minute lockout
            cache.delete(violation_key)  # Reset violation counter
            
            vendor_rate_logger.warning(
                f"Lockout applied for IP: {client_ip}, User: {user_id}",
                extra={
                    'ip_address': client_ip,
                    'user_id': user_id,
                    'violation_count': violation_count,
                    'action': 'lockout_applied'
                }
            )
        else:
            cache.set(violation_key, violation_count, 3600)  # 1 hour timeout
    
    def _vendor_is_locked_out(self, client_ip: str, user_id: str) -> bool:
        """Check if IP/user is currently locked out"""
        lockout_key = f"vendor_lockout_{client_ip}_{user_id}"
        return cache.get(lockout_key) is not None
    
    def _vendor_get_lockout_remaining_time(self, client_ip: str, user_id: str) -> int:
        """Get remaining lockout time in seconds"""
        lockout_key = f"vendor_lockout_{client_ip}_{user_id}"
        lockout_start = cache.get(lockout_key)
        
        if lockout_start:
            elapsed = int(time.time()) - lockout_start
            remaining = max(0, 300 - elapsed)  # 5 minute lockout
            return remaining
        
        return 0
    
    def _vendor_get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address safely"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
