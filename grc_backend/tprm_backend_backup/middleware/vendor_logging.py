"""
Vendor Logging Middleware - Comprehensive audit logging with security focus
"""

import logging
import json
import time
from typing import Dict, Any
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

# Configure structured logging
vendor_audit_logger = logging.getLogger('vendor_audit')
vendor_security_logger = logging.getLogger('vendor_security')


class VendorLoggingMiddleware(MiddlewareMixin):
    """
    Comprehensive logging middleware for security and audit purposes
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.vendor_sensitive_fields = self._vendor_get_sensitive_fields()
        self.vendor_logged_endpoints = self._vendor_get_logged_endpoints()
    
    def _vendor_get_sensitive_fields(self) -> set:
        """Define fields that should not be logged"""
        return {
            'password', 'vendor_password', 'passwd', 'pwd',
            'token', 'vendor_token', 'access_token', 'refresh_token',
            'secret', 'vendor_secret', 'api_key', 'vendor_api_key',
            'ssn', 'vendor_ssn', 'social_security', 'credit_card',
            'vendor_credit_card', 'bank_account', 'vendor_bank_account',
            'private_key', 'vendor_private_key', 'encryption_key',
            'vendor_encryption_key'
        }
    
    def _vendor_get_logged_endpoints(self) -> Dict[str, str]:
        """Define which endpoints should be logged and at what level"""
        return {
            '/api/v1/vendor-auth/': 'HIGH',
            '/api/v1/vendor-risk/': 'MEDIUM',
            '/api/v1/vendor-questionnaire/': 'MEDIUM',
            '/api/v1/vendor-dashboard/': 'LOW',
            '/api/v1/vendor-lifecycle/': 'MEDIUM',
            '/vendor-admin/': 'HIGH',
        }
    
    def process_request(self, request: HttpRequest) -> None:
        """Log incoming requests with security context"""
        request.vendor_start_time = time.time()
        
        # Determine logging level for this endpoint
        log_level = self._vendor_get_log_level(request.path)
        
        if log_level:
            request_data = self._vendor_extract_request_data(request)
            
            vendor_audit_logger.info(
                "Request started",
                extra={
                    'event_type': 'request_started',
                    'timestamp': request.vendor_start_time,
                    'ip_address': self._vendor_get_client_ip(request),
                    'user_id': getattr(request.user, 'id', 'anonymous'),
                    'session_id': request.session.session_key if hasattr(request, 'session') else None,
                    'method': request.method,
                    'path': request.path,
                    'query_params': self._vendor_sanitize_data(dict(request.GET.items())),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'referrer': request.META.get('HTTP_REFERER', ''),
                    'content_type': request.content_type,
                    'content_length': len(request.body) if hasattr(request, 'body') else 0,
                    'request_data': request_data if log_level in ['HIGH', 'MEDIUM'] else None,
                    'log_level': log_level,
                    'action': 'request_logging'
                }
            )
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log responses with performance and security metrics"""
        
        # Calculate response time
        end_time = time.time()
        start_time = getattr(request, 'vendor_start_time', end_time)
        response_time = round((end_time - start_time) * 1000, 2)  # milliseconds
        
        # Determine logging level
        log_level = self._vendor_get_log_level(request.path)
        
        if log_level:
            # Extract response data (if safe to log)
            response_data = self._vendor_extract_response_data(response, log_level)
            
            # Determine log level based on status code
            if response.status_code >= 500:
                log_function = vendor_security_logger.error
            elif response.status_code >= 400:
                log_function = vendor_security_logger.warning
            else:
                log_function = vendor_audit_logger.info
            
            log_function(
                f"Request completed - {response.status_code}",
                extra={
                    'event_type': 'request_completed',
                    'timestamp': end_time,
                    'ip_address': self._vendor_get_client_ip(request),
                    'user_id': getattr(request.user, 'id', 'anonymous'),
                    'session_id': request.session.session_key if hasattr(request, 'session') else None,
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'response_time_ms': response_time,
                    'response_size': len(response.content) if hasattr(response, 'content') else 0,
                    'response_data': response_data,
                    'log_level': log_level,
                    'action': 'response_logging'
                }
            )
            
            # Log slow requests as potential performance issues
            if response_time > 5000:  # 5 seconds
                vendor_security_logger.warning(
                    f"Slow request detected - {response_time}ms",
                    extra={
                        'event_type': 'slow_request',
                        'ip_address': self._vendor_get_client_ip(request),
                        'user_id': getattr(request.user, 'id', 'anonymous'),
                        'path': request.path,
                        'response_time_ms': response_time,
                        'action': 'performance_warning'
                    }
                )
        
        return response
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """Log exceptions with security context"""
        
        vendor_security_logger.error(
            f"Request exception: {str(exception)}",
            extra={
                'event_type': 'request_exception',
                'timestamp': time.time(),
                'ip_address': self._vendor_get_client_ip(request),
                'user_id': getattr(request.user, 'id', 'anonymous'),
                'session_id': request.session.session_key if hasattr(request, 'session') else None,
                'method': request.method,
                'path': request.path,
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'action': 'exception_logging'
            },
            exc_info=True
        )
    
    def _vendor_get_log_level(self, path: str) -> str:
        """Determine logging level based on endpoint"""
        for endpoint, level in self.vendor_logged_endpoints.items():
            if path.startswith(endpoint):
                return level
        
        # Default logging for API endpoints
        if path.startswith('/api/'):
            return 'LOW'
        
        return None
    
    def _vendor_extract_request_data(self, request: HttpRequest) -> Dict[str, Any]:
        """Extract and sanitize request data for logging"""
        try:
            data = {}
            
            # Extract POST data
            if hasattr(request, 'POST') and request.POST:
                data['post_data'] = self._vendor_sanitize_data(dict(request.POST.items()))
            
            # Extract JSON data
            if request.content_type == 'application/json' and hasattr(request, 'body'):
                try:
                    json_data = json.loads(request.body.decode('utf-8'))
                    if isinstance(json_data, dict):
                        data['json_data'] = self._vendor_sanitize_data(json_data)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    data['json_data'] = 'Invalid JSON'
            
            return data
            
        except Exception as e:
            vendor_security_logger.error(f"Error extracting request data: {str(e)}")
            return {'error': 'Failed to extract request data'}
    
    def _vendor_extract_response_data(self, response: HttpResponse, log_level: str) -> Dict[str, Any]:
        """Extract response data for logging (only for certain log levels)"""
        try:
            if log_level != 'HIGH':
                return {'logged': False, 'reason': 'Log level too low'}
            
            # Only log response data for JSON responses and small payloads
            if (hasattr(response, 'content') and 
                response.get('Content-Type', '').startswith('application/json') and
                len(response.content) < 10000):  # Limit to 10KB
                
                try:
                    json_data = json.loads(response.content.decode('utf-8'))
                    return self._vendor_sanitize_data(json_data)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return {'error': 'Invalid JSON response'}
            
            return {'logged': False, 'reason': 'Not JSON or too large'}
            
        except Exception as e:
            vendor_security_logger.error(f"Error extracting response data: {str(e)}")
            return {'error': 'Failed to extract response data'}
    
    def _vendor_sanitize_data(self, data: Any) -> Any:
        """Recursively sanitize data to remove sensitive information"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if isinstance(key, str) and key.lower() in self.vendor_sensitive_fields:
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = self._vendor_sanitize_data(value)
            return sanitized
        
        elif isinstance(data, list):
            return [self._vendor_sanitize_data(item) for item in data]
        
        elif isinstance(data, str):
            # Check if the string value looks like sensitive data
            if self._vendor_is_sensitive_value(data):
                return '[REDACTED]'
            return data
        
        else:
            return data
    
    def _vendor_is_sensitive_value(self, value: str) -> bool:
        """Check if a string value appears to be sensitive"""
        value_lower = value.lower()
        
        # Check for patterns that look like sensitive data
        sensitive_patterns = [
            r'^[a-f0-9]{32,}$',  # Hex strings (tokens, hashes)
            r'^[A-Za-z0-9+/]{20,}={0,2}$',  # Base64 encoded data
            r'^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$',  # Credit card patterns
            r'^\d{3}-\d{2}-\d{4}$',  # SSN pattern
        ]
        
        import re
        for pattern in sensitive_patterns:
            if re.match(pattern, value):
                return True
        
        return False
    
    def _vendor_get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address safely"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
