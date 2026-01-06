import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.utils import IntegrityError
from django.http import Http404

logger = logging.getLogger('rfp')


def custom_exception_handler(exc, context):
    """
    Custom exception handler for REST framework that adds more detailed error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If response is already handled by DRF, return it
    if response is not None:
        return response
    
    # Handle Django validation errors
    if isinstance(exc, DjangoValidationError):
        data = {
            'error': 'Validation Error',
            'detail': exc.messages if hasattr(exc, 'messages') else str(exc)
        }
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle database integrity errors
    if isinstance(exc, IntegrityError):
        data = {
            'error': 'Database Error',
            'detail': 'A database integrity error occurred. This might be due to duplicate data or constraint violations.'
        }
        logger.error(f"IntegrityError: {str(exc)}")
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle 404 errors
    if isinstance(exc, Http404):
        data = {
            'error': 'Not Found',
            'detail': 'The requested resource was not found.'
        }
        return Response(data, status=status.HTTP_404_NOT_FOUND)
    
    # Handle any other exceptions
    logger.error(f"Unhandled exception: {str(exc)}")
    data = {
        'error': 'Server Error',
        'detail': 'An unexpected error occurred. Please try again later.'
    }
    return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def sanitize_input(data):
    """
    Sanitize input data to prevent XSS and other injection attacks
    """
    if isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    elif isinstance(data, str):
        # Basic sanitization - remove script tags and other potentially dangerous content
        import re
        data = re.sub(r'<script.*?>.*?</script>', '', data, flags=re.DOTALL)
        data = re.sub(r'javascript:', '', data, flags=re.IGNORECASE)
        data = re.sub(r'on\w+\s*=', '', data, flags=re.IGNORECASE)
        return data
    else:
        return data
