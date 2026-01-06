"""
Vendor Custom Exception Handler - Secure error handling with logging
"""

import logging
from typing import Dict, Any
from django.http import JsonResponse
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

vendor_error_logger = logging.getLogger('vendor_security')


def vendor_custom_exception_handler(exc, context):
    """
    Custom exception handler that ensures no sensitive information is leaked
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Get request information
    request = context.get('request')
    view = context.get('view')
    
    # Log the exception
    vendor_error_logger.error(
        f"Exception in {view.__class__.__name__ if view else 'Unknown'}: {str(exc)}",
        extra={
            'exception_type': type(exc).__name__,
            'exception_message': str(exc),
            'path': request.path if request else 'unknown',
            'method': request.method if request else 'unknown',
            'user_id': getattr(request.user, 'id', 'anonymous') if request else 'unknown',
            'ip_address': _vendor_get_client_ip(request) if request else 'unknown',
            'action': 'exception_handled'
        },
        exc_info=True
    )
    
    if response is not None:
        # Sanitize the response data
        custom_response_data = _vendor_sanitize_error_response(response.data, exc)
        
        return Response(
            custom_response_data,
            status=response.status_code,
            headers=response.get('headers', {})
        )
    
    # Handle unexpected exceptions
    return _vendor_handle_unexpected_exception(exc, context)


def _vendor_sanitize_error_response(data: Any, exc: Exception) -> Dict[str, Any]:
    """
    Sanitize error response to prevent information leakage
    """
    sanitized_data = {
        'error': True,
        'message': 'An error occurred',
        'timestamp': _vendor_get_current_timestamp()
    }
    
    # Only include detailed error information in debug mode
    if settings.DEBUG:
        sanitized_data['debug_info'] = {
            'exception_type': type(exc).__name__,
            'original_data': data
        }
    else:
        # In production, provide generic error messages
        if hasattr(exc, 'status_code'):
            status_code = exc.status_code
        elif hasattr(exc, 'default_code'):
            status_code = 400  # Default to bad request
        else:
            status_code = 500
        
        sanitized_data['message'] = _vendor_get_generic_error_message(status_code)
    
    return sanitized_data


def _vendor_get_generic_error_message(status_code: int) -> str:
    """
    Get generic error message based on status code
    """
    error_messages = {
        400: 'Invalid request. Please check your input.',
        401: 'Authentication required.',
        403: 'You do not have permission to perform this action.',
        404: 'The requested resource was not found.',
        405: 'Method not allowed.',
        429: 'Too many requests. Please try again later.',
        500: 'Internal server error. Please try again later.',
        502: 'Service temporarily unavailable.',
        503: 'Service temporarily unavailable.',
        504: 'Request timeout. Please try again.',
    }
    
    return error_messages.get(status_code, 'An unexpected error occurred.')


def _vendor_handle_unexpected_exception(exc: Exception, context: Dict) -> Response:
    """
    Handle unexpected exceptions not caught by DRF
    """
    request = context.get('request')
    
    vendor_error_logger.critical(
        f"Unhandled exception: {str(exc)}",
        extra={
            'exception_type': type(exc).__name__,
            'exception_message': str(exc),
            'path': request.path if request else 'unknown',
            'method': request.method if request else 'unknown',
            'user_id': getattr(request.user, 'id', 'anonymous') if request else 'unknown',
            'ip_address': _vendor_get_client_ip(request) if request else 'unknown',
            'action': 'unhandled_exception'
        },
        exc_info=True
    )
    
    # Return generic error response
    error_data = {
        'error': True,
        'message': _vendor_get_generic_error_message(500),
        'timestamp': _vendor_get_current_timestamp()
    }
    
    if settings.DEBUG:
        error_data['debug_info'] = {
            'exception_type': type(exc).__name__,
            'exception_message': str(exc)
        }
    
    return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _vendor_get_client_ip(request) -> str:
    """Get client IP address safely"""
    if not request:
        return 'unknown'
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def _vendor_get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    from datetime import datetime
    return datetime.utcnow().isoformat() + 'Z'
