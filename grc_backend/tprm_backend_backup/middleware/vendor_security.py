"""
Vendor Security Middleware - Implements comprehensive security controls
"""

import logging
import json
import time
from typing import Dict, Any
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import cache
import re

vendor_security_logger = logging.getLogger('vendor_security')


class VendorSecurityMiddleware(MiddlewareMixin):
    """
    Comprehensive security middleware implementing secure coding practices
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.vendor_security_headers = self._vendor_get_security_headers()
        self.vendor_blocked_patterns = self._vendor_get_blocked_patterns()
        
    def _vendor_get_security_headers(self) -> Dict[str, str]:
        """Define security headers to be added to all responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';",
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload' if not settings.DEBUG else '',
        }
    
    def _vendor_get_blocked_patterns(self) -> list:
        """Define patterns that should be blocked for security"""
        return [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # Javascript protocol
            r'vbscript:',                 # VBScript protocol
            r'onload\s*=',                # Event handlers
            r'onerror\s*=',
            r'onclick\s*=',
            r'eval\s*\(',                 # Eval functions
            r'setTimeout\s*\(',
            r'setInterval\s*\(',
            r'<iframe[^>]*>',             # Iframe tags
            r'<object[^>]*>',             # Object tags
            r'<embed[^>]*>',              # Embed tags
        ]
    
    def process_request(self, request: HttpRequest) -> HttpResponse:
        """Process incoming requests for security threats"""
        
        # Log request details for security monitoring
        self._vendor_log_request_details(request)
        
        # Check for malicious patterns in request
        if self._vendor_contains_malicious_content(request):
            vendor_security_logger.warning(
                f"Malicious content detected from IP: {self._vendor_get_client_ip(request)}"
            )
            return JsonResponse(
                {'error': 'Request contains potentially malicious content'},
                status=400
            )
        
        # Check rate limiting
        if self._vendor_is_rate_limited(request):
            vendor_security_logger.warning(
                f"Rate limit exceeded for IP: {self._vendor_get_client_ip(request)}"
            )
            return JsonResponse(
                {'error': 'Rate limit exceeded'},
                status=429
            )
        
        # Validate content length
        if self._vendor_validate_content_length(request):
            vendor_security_logger.warning(
                f"Content length exceeded from IP: {self._vendor_get_client_ip(request)}"
            )
            return JsonResponse(
                {'error': 'Request content too large'},
                status=413
            )
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Add security headers to all responses"""
        
        # Add security headers
        for header, value in self.vendor_security_headers.items():
            if value:  # Only add non-empty headers
                response[header] = value
        
        # Remove sensitive headers
        self._vendor_remove_sensitive_headers(response)
        
        # Log response for security monitoring
        self._vendor_log_response_details(request, response)
        
        return response
    
    def _vendor_log_request_details(self, request: HttpRequest):
        """Log request details for security monitoring"""
        try:
            vendor_security_logger.info(
                "Request received",
                extra={
                    'ip_address': self._vendor_get_client_ip(request),
                    'method': request.method,
                    'path': request.path,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'content_type': request.content_type,
                    'content_length': len(request.body) if hasattr(request, 'body') else 0,
                    'user_id': getattr(request.user, 'id', 'anonymous') if hasattr(request, 'user') and hasattr(request.user, 'id') else 'anonymous',
                    'action': 'request_received'
                }
            )
        except Exception as e:
            vendor_security_logger.error(f"Failed to log request details: {str(e)}")
    
    def _vendor_log_response_details(self, request: HttpRequest, response: HttpResponse):
        """Log response details for security monitoring"""
        try:
            vendor_security_logger.info(
                "Response sent",
                extra={
                    'ip_address': self._vendor_get_client_ip(request),
                    'status_code': response.status_code,
                    'path': request.path,
                    'user_id': getattr(request.user, 'id', 'anonymous') if hasattr(request, 'user') and hasattr(request.user, 'id') else 'anonymous',
                    'action': 'response_sent'
                }
            )
        except Exception as e:
            vendor_security_logger.error(f"Failed to log response details: {str(e)}")
    
    def _vendor_contains_malicious_content(self, request: HttpRequest) -> bool:
        """Check if request contains malicious patterns"""
        try:
            # Check URL parameters
            for key, value in request.GET.items():
                if self._vendor_check_patterns(str(value)):
                    return True
            
            # Check POST data
            if hasattr(request, 'POST'):
                for key, value in request.POST.items():
                    if self._vendor_check_patterns(str(value)):
                        return True
            
            # Check JSON body
            if request.content_type == 'application/json' and hasattr(request, 'body'):
                try:
                    body = json.loads(request.body.decode('utf-8'))
                    if self._vendor_check_json_patterns(body):
                        return True
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            
            # Check headers for XSS attempts
            for header, value in request.META.items():
                if header.startswith('HTTP_') and self._vendor_check_patterns(str(value)):
                    return True
            
            return False
            
        except Exception as e:
            vendor_security_logger.error(f"Error checking malicious content: {str(e)}")
            return False
    
    def _vendor_check_patterns(self, content: str) -> bool:
        """Check content against malicious patterns"""
        content_lower = content.lower()
        for pattern in self.vendor_blocked_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True
        return False
    
    def _vendor_check_json_patterns(self, data: Any) -> bool:
        """Recursively check JSON data for malicious patterns"""
        if isinstance(data, dict):
            for key, value in data.items():
                if self._vendor_check_patterns(str(key)) or self._vendor_check_json_patterns(value):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._vendor_check_json_patterns(item):
                    return True
        elif isinstance(data, str):
            return self._vendor_check_patterns(data)
        
        return False
    
    def _vendor_is_rate_limited(self, request: HttpRequest) -> bool:
        """Check if request should be rate limited"""
        try:
            client_ip = self._vendor_get_client_ip(request)
            cache_key = f"vendor_rate_limit_{client_ip}"
            
            # Get current request count
            current_count = cache.get(cache_key, 0)
            
            # Define rate limits based on endpoint
            if request.path.startswith('/api/v1/vendor-auth/'):
                max_requests = 10  # Stricter limit for auth endpoints
                window_seconds = 300  # 5 minutes
            else:
                max_requests = 100  # General API limit
                window_seconds = 3600  # 1 hour
            
            # Check if limit exceeded
            if current_count >= max_requests:
                return True
            
            # Increment counter
            cache.set(cache_key, current_count + 1, window_seconds)
            
            return False
            
        except Exception as e:
            vendor_security_logger.error(f"Rate limiting check failed: {str(e)}")
            return False
    
    def _vendor_validate_content_length(self, request: HttpRequest) -> bool:
        """Validate request content length"""
        try:
            content_length = int(request.META.get('CONTENT_LENGTH', 0))
            max_length = getattr(settings, 'VENDOR_SETTINGS', {}).get('MAX_FILE_UPLOAD_SIZE', 10 * 1024 * 1024)
            
            return content_length > max_length
            
        except (ValueError, TypeError):
            return False
    
    def _vendor_get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address safely"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _vendor_remove_sensitive_headers(self, response: HttpResponse):
        """Remove headers that might leak sensitive information"""
        sensitive_headers = [
            'Server',
            'X-Powered-By',
            'X-AspNet-Version',
            'X-AspNetMvc-Version',
        ]
        
        for header in sensitive_headers:
            if header in response:
                del response[header]
