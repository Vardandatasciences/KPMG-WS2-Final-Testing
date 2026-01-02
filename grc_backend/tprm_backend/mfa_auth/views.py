from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json
from django.conf import settings
import logging

from .models import User, MfaEmailChallenge, MfaAuditLog
from .services import MfaService
from .jwt_service import JWTService
from .serializers import (
    LoginRequestSerializer, 
    OtpVerificationSerializer,
    LoginResponseSerializer,
    OtpResponseSerializer,
    UserSerializer
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_step1(request):
    """
    Step 1: Authenticate user credentials and send OTP
    """
    serializer = LoginRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Invalid input',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    try:
        # Authenticate user
        user = MfaService.authenticate_user(username, password)
        if not user:
            return Response({
                'success': False,
                'message': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.email:
            return Response({
                'success': False,
                'message': 'No email address found for this user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        enable_mfa = getattr(settings, 'ENABLE_VENDOR_MFA', False)
        if not enable_mfa:
            tokens = JWTService.generate_tokens(user)
            user.session_token = tokens['access_token']
            user.save(update_fields=['session_token'])
            response_data = {
                'success': True,
                'message': 'Login successful',
                'requires_otp': False,
                'user': UserSerializer(user).data,
                'session_token': tokens['access_token'],
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'expires_in': tokens['expires_in'],
                'refresh_expires_in': tokens['refresh_expires_in']
            }
            return Response(response_data, status=status.HTTP_200_OK)
        
        # Create MFA challenge and send OTP
        MfaService.create_mfa_challenge(user, request)
        
        response_data = {
            'success': True,
            'message': f'OTP sent to {user.email[:3]}***{user.email.split("@")[1]}',
            'requires_otp': True,
            'user': UserSerializer(user).data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as exc:
        logger.exception("Login step1 failed for username=%s", username)
        return Response({
            'success': False,
            'message': 'Failed to initiate login. Please contact support.',
            'error': str(exc)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    Step 2: Verify OTP and complete login
    """
    serializer = OtpVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Invalid input',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    otp = serializer.validated_data['otp']
    
    # Get user
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verify OTP
    result = MfaService.verify_otp(user, otp, request)
    
    if result['success']:
        response_data = {
            'success': True,
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'session_token': result['tokens']['access_token'],  # Frontend expects session_token
            'access_token': result['tokens']['access_token'],
            'refresh_token': result['tokens']['refresh_token'],
            'expires_in': result['tokens']['expires_in'],
            'refresh_expires_in': result['tokens']['refresh_expires_in']
        }
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': result['error']
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """
    Resend OTP for a user
    """
    username = request.data.get('username')
    if not username:
        return Response({
            'success': False,
            'message': 'Username is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if user has recent pending challenge
    recent_challenge = MfaEmailChallenge.objects.filter(
        user=user,
        status=MfaEmailChallenge.STATUS_PENDING
    ).order_by('-created_at').first()
    
    if recent_challenge and not recent_challenge.is_expired():
        return Response({
            'success': False,
            'message': 'Please wait before requesting a new OTP'
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Create new challenge
    challenge = MfaService.create_mfa_challenge(user, request)
    
    return Response({
        'success': True,
        'message': f'New OTP sent to {user.email[:3]}***{user.email.split("@")[1]}'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])  # Bypass DRF authentication
@permission_classes([AllowAny])  # Allow any user to access
def logout(request):
    """
    Logout user by clearing session token from database
    Note: We bypass DRF authentication because we use custom JWT tokens
    """
    print("=== LOGOUT REQUEST RECEIVED ===")
    auth_header = request.headers.get('Authorization', '')
    print(f"Authorization header: {auth_header[:50]}..." if len(auth_header) > 50 else f"Authorization header: {auth_header}")
    
    if not auth_header.startswith('Bearer '):
        print("ERROR: Invalid authorization header format")
        return Response({
            'success': False,
            'message': 'Invalid authorization header'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    token = auth_header.replace('Bearer ', '')
    print(f"Extracted token: {token[:20]}...")
    
    # Use our custom JWT validation (not rest_framework_simplejwt)
    user = MfaService.validate_jwt_token(token)
    print(f"User from token: {user.username if user else 'None'}")
    
    if user:
        # Log the session token before clearing
        print(f"Clearing session_token for user: {user.username}")
        print(f"Current session_token: {user.session_token[:20]}..." if user.session_token else "Current session_token: None")
        
        # Clear the session token from database
        MfaService.logout_user(user)
        
        # Verify it was cleared
        user.refresh_from_db()
        print(f"After logout - session_token: {user.session_token}")
        print("=== LOGOUT SUCCESSFUL - TOKEN CLEARED FROM DATABASE ===")
        
        return Response({
            'success': True,
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
    
    print("ERROR: Invalid or expired token")
    return Response({
        'success': False,
        'message': 'Invalid or expired token'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@authentication_classes([])  # Bypass DRF authentication
@permission_classes([AllowAny])  # Allow any user to access
def validate_session(request):
    """
    Validate JWT token and return user info
    Note: We bypass DRF authentication because we use custom JWT tokens
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({
            'success': False,
            'message': 'Invalid authorization header'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    token = auth_header.replace('Bearer ', '')
    user = MfaService.validate_jwt_token(token)
    
    if user:
        return Response({
            'success': True,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Invalid or expired token'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh access token using refresh token
    """
    refresh_token = request.data.get('refresh_token')
    if not refresh_token:
        return Response({
            'success': False,
            'message': 'Refresh token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from .jwt_service import JWTService
    result = JWTService.refresh_access_token(refresh_token)
    
    if result:
        return Response({
            'success': True,
            'access_token': result['access_token'],
            'expires_in': result['expires_in']
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Invalid or expired refresh token'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def mfa_status(request):
    """
    Get MFA status for a user
    """
    username = request.GET.get('username')
    if not username:
        return Response({
            'success': False,
            'message': 'Username is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(username=username)
        
        # Get latest challenge
        latest_challenge = MfaEmailChallenge.objects.filter(
            user=user
        ).order_by('-created_at').first()
        
        response_data = {
            'success': True,
            'user': UserSerializer(user).data,
            'has_pending_challenge': False,
            'challenge_expires_at': None
        }
        
        if latest_challenge and latest_challenge.status == MfaEmailChallenge.STATUS_PENDING:
            if not latest_challenge.is_expired():
                response_data['has_pending_challenge'] = True
                response_data['challenge_expires_at'] = latest_challenge.expires_at.isoformat()
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def active_sessions(request):
    """
    Get all active sessions (admin only)
    """
    active_users = MfaService.get_active_sessions()
    
    sessions_data = []
    for user in active_users:
        sessions_data.append({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'session_token_preview': user.session_token[:20] + '...' if user.session_token else None,
            'is_active': user.is_active
        })
    
    return Response({
        'success': True,
        'active_sessions_count': len(sessions_data),
        'sessions': sessions_data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def force_logout(request):
    """
    Force logout a specific user (admin only)
    """
    username = request.data.get('username')
    if not username:
        return Response({
            'success': False,
            'message': 'Username is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success = MfaService.force_logout_user(username)
    
    if success:
        return Response({
            'success': True,
            'message': f'User {username} has been force logged out'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': f'User {username} not found'
        }, status=status.HTTP_404_NOT_FOUND)
