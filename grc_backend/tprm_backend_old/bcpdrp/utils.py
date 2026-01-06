"""
Utility functions for BCP/DRP API
"""
from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    """Create a standardized success response"""
    return Response({
        'success': True,
        'message': message,
        'data': data
    }, status=status_code)


def error_response(message="Error occurred", status_code=status.HTTP_400_BAD_REQUEST, errors=None):
    """Create a standardized error response"""
    response_data = {
        'success': False,
        'message': message
    }
    if errors:
        response_data['errors'] = errors
    
    return Response(response_data, status=status_code)


def not_found_response(message="Resource not found"):
    """Create a 404 not found response"""
    return error_response(message, status.HTTP_404_NOT_FOUND)


def validation_error_response(errors, message="Validation failed"):
    """Create a validation error response"""
    return error_response(message, status.HTTP_400_BAD_REQUEST, errors)


def convert_dict_keys_to_snake(data):
    """Convert dictionary keys from camelCase to snake_case"""
    if not isinstance(data, dict):
        return data
    
    converted = {}
    for key, value in data.items():
        # Convert camelCase to snake_case
        snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
        converted[snake_key] = value
    
    return converted


def convert_dict_keys_to_camel(data):
    """Convert dictionary keys from snake_case to camelCase"""
    if not isinstance(data, dict):
        return data
    
    converted = {}
    for key, value in data.items():
        # Convert snake_case to camelCase
        camel_key = ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(key.split('_')))
        converted[camel_key] = value
    
    return converted
