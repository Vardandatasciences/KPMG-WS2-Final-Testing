"""
Test views for authentication and API connectivity
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse


@api_view(['GET'])
@permission_classes([AllowAny])
def test_auth(request):
    """
    Simple endpoint to test authentication
    Returns information about the authenticated user
    """
    user = request.user
    
    response_data = {
        'message': 'API is working',
        'authenticated': user.is_authenticated if hasattr(user, 'is_authenticated') else False,
        'timestamp': str(request.META.get('HTTP_DATE', ''))
    }
    
    if hasattr(user, 'is_authenticated') and user.is_authenticated:
        # Try to get user details from different possible attributes
        user_id = (
            getattr(user, 'userid', None) or 
            getattr(user, 'UserId', None) or 
            getattr(user, 'id', None) or 
            getattr(user, 'pk', None)
        )
        
        username = (
            getattr(user, 'username', None) or
            getattr(user, 'UserName', None) or
            getattr(user, 'email', None) or
            'Unknown'
        )
        
        response_data.update({
            'user_id': user_id,
            'username': username,
            'user_type': type(user).__name__,
            'auth_method': 'JWT' if 'Bearer' in request.META.get('HTTP_AUTHORIZATION', '') else 'Session'
        })
    else:
        response_data['message'] = 'Not authenticated'
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_cors(request):
    """
    Simple endpoint to test CORS configuration
    """
    return JsonResponse({
        'message': 'CORS is working',
        'origin': request.META.get('HTTP_ORIGIN', 'Unknown'),
        'method': request.method
    })


@api_view(['POST', 'GET', 'PUT', 'DELETE', 'PATCH'])
@permission_classes([AllowAny])
def test_methods(request):
    """
    Test endpoint that accepts all HTTP methods
    """
    return Response({
        'message': f'{request.method} request successful',
        'method': request.method,
        'data': request.data if request.method in ['POST', 'PUT', 'PATCH'] else None
    }, status=status.HTTP_200_OK)

