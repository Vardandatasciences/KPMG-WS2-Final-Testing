"""
Simple authentication views for vendor management system
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.sessions.models import Session
from django.utils import timezone
from tprm_backend.apps.vendor_approval.models import Users
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def test_endpoint(request):
    """Test endpoint to check if API is working"""
    return Response({
        'success': True,
        'message': 'API is working'
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def simple_login(request):
    """
    BYPASSED login endpoint - always returns success with hardcoded user
    """
    try:
        # Always return success with hardcoded user
        hardcoded_user = {
            'id': 60,
            'username': 'GRC Administrator',
            'email': 'admin@vendor.com',
            'first_name': 'GRC',
            'last_name': 'Administrator',
            'department_id': 1
        }
        
        # Create session with hardcoded user
        try:
            request.session['user_id'] = hardcoded_user['id']
            request.session['username'] = hardcoded_user['username']
            request.session['email'] = hardcoded_user['email']
            request.session['is_authenticated'] = True
            logger.info(f"Session created successfully for hardcoded user: {hardcoded_user['username']}")
        except Exception as session_error:
            logger.error(f"Session creation error: {str(session_error)}")
            return Response({
                'success': False,
                'message': 'Session creation failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"Hardcoded user {hardcoded_user['username']} logged in successfully")
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': hardcoded_user
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred during login'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def logout(request):
    """
    Simple logout endpoint
    """
    try:
        # Clear session
        request.session.flush()
        
        logger.info("User logged out successfully")
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred during logout'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_auth(request):
    """
    BYPASSED auth check - always returns authenticated with hardcoded user
    """
    try:
        # Always return authenticated with hardcoded user
        hardcoded_user = {
            'id': 60,
            'username': 'GRC Administrator',
            'email': 'admin@vendor.com',
            'first_name': 'GRC',
            'last_name': 'Administrator',
            'department_id': 1
        }
        
        # Set session if not already set
        if not request.session.get('is_authenticated'):
            request.session['user_id'] = hardcoded_user['id']
            request.session['username'] = hardcoded_user['username']
            request.session['email'] = hardcoded_user['email']
            request.session['is_authenticated'] = True
        
        return Response({
            'authenticated': True,
            'user': hardcoded_user
        }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Auth check error: {str(e)}")
        return Response({
            'authenticated': True,  # Even on error, return authenticated
            'user': {
                'id': 60,
                'username': 'GRC Administrator',
                'email': 'admin@vendor.com',
                'first_name': 'GRC',
                'last_name': 'Administrator',
                'department_id': 1
            }
        }, status=status.HTTP_200_OK)
