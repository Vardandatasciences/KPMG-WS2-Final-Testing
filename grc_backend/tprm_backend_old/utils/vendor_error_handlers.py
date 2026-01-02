"""
Vendor Error Handlers - Custom HTTP error handlers with security focus
"""

import logging
from django.http import JsonResponse
from django.conf import settings

vendor_error_logger = logging.getLogger('vendor_security')


def vendor_bad_request(request, exception=None):
    """
    Handle 400 Bad Request errors
    """
    vendor_error_logger.warning(
        "400 Bad Request",
        extra={
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', 'anonymous'),
            'ip_address': _vendor_get_client_ip(request),
            'action': 'bad_request_error'
        }
    )
    
    error_data = {
        'error': True,
        'status_code': 400,
        'message': 'Bad request. Please check your input.',
        'timestamp': _vendor_get_current_timestamp()
    }
    
    if settings.DEBUG and exception:
        error_data['debug_info'] = str(exception)
    
    return JsonResponse(error_data, status=400)


def vendor_permission_denied(request, exception=None):
    """
    Handle 403 Permission Denied errors
    """
    vendor_error_logger.warning(
        "403 Permission Denied",
        extra={
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', 'anonymous'),
            'ip_address': _vendor_get_client_ip(request),
            'action': 'permission_denied_error'
        }
    )
    
    error_data = {
        'error': True,
        'status_code': 403,
        'message': 'You do not have permission to access this resource.',
        'timestamp': _vendor_get_current_timestamp()
    }
    
    if settings.DEBUG and exception:
        error_data['debug_info'] = str(exception)
    
    return JsonResponse(error_data, status=403)


def vendor_not_found(request, exception=None):
    """
    Handle 404 Not Found errors
    """
    vendor_error_logger.info(
        "404 Not Found",
        extra={
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', 'anonymous'),
            'ip_address': _vendor_get_client_ip(request),
            'action': 'not_found_error'
        }
    )
    
    error_data = {
        'error': True,
        'status_code': 404,
        'message': 'The requested resource was not found.',
        'timestamp': _vendor_get_current_timestamp()
    }
    
    if settings.DEBUG and exception:
        error_data['debug_info'] = str(exception)
    
    return JsonResponse(error_data, status=404)


def vendor_server_error(request):
    """
    Handle 500 Internal Server Error
    """
    vendor_error_logger.error(
        "500 Internal Server Error",
        extra={
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', 'anonymous'),
            'ip_address': _vendor_get_client_ip(request),
            'action': 'server_error'
        }
    )
    
    error_data = {
        'error': True,
        'status_code': 500,
        'message': 'Internal server error. Please try again later.',
        'timestamp': _vendor_get_current_timestamp()
    }
    
    # Never expose internal error details in production
    if settings.DEBUG:
        error_data['debug_info'] = 'Check server logs for details'
    
    return JsonResponse(error_data, status=500)


def _vendor_get_client_ip(request) -> str:
    """Get client IP address safely"""
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
