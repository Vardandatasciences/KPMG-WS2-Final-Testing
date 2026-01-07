"""
Cookie Preferences Management Views
Handles cookie preference storage and retrieval for GDPR compliance
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from ...models import CookiePreferences, Users
import logging
import uuid

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    # Ensure IP address doesn't exceed database column length (50 chars)
    # IPv6 addresses can be up to 45 chars, so 50 is sufficient
    # Truncate to 50 to match database VARCHAR(50) constraint
    if len(ip) > 50:
        ip = ip[:50]
    return ip


def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit to 500 chars


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def save_cookie_preferences(request):
    """
    Save or update cookie preferences
    Body: {
        "user_id": 1 (optional),
        "session_id": "abc123" (optional),
        "essential_cookies": true,
        "functional_cookies": false,
        "analytics_cookies": false,
        "marketing_cookies": false,
        "preferences_saved": true
    }
    """
    try:
        logger.info(f"[Cookie] Received save request: {request.data}")
        data = request.data
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        # Log the received user_id for debugging
        logger.info(f"[Cookie] Received user_id: {user_id} (type: {type(user_id).__name__}), session_id: {session_id}")
        
        # If no session_id provided, generate one
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"[Cookie] Generated new session_id: {session_id}")
        
        # Validate user_id if provided
        user = None
        if user_id:
            try:
                user = Users.objects.get(UserId=user_id)
                logger.info(f"[Cookie] Found user: {user.UserId} - {user.UserName}")
            except Users.DoesNotExist:
                logger.warning(f"[Cookie] User {user_id} not found, saving preferences without user")
        
        # Get IP and User Agent
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        logger.info(f"[Cookie] IP: {ip_address}, UserAgent: {user_agent[:50]}...")
        
        # Try to find existing preference
        # Priority: 1) By user_id (if provided), 2) By session_id
        existing = None
        if user_id:
            # First try to find by user_id
            existing = CookiePreferences.objects.filter(UserId=user_id).order_by('-CreatedAt').first()
            if existing:
                logger.info(f"[Cookie] Found existing preference for user {user_id}: PreferenceId={existing.PreferenceId}, UserId={existing.UserId.UserId if existing.UserId else 'NULL'}")
            else:
                # If not found by user_id, try by session_id (might be session-based that needs linking)
                if session_id:
                    # First try to find session-based preference without user_id (needs linking)
                    existing = CookiePreferences.objects.filter(SessionId=session_id, UserId__isnull=True).order_by('-CreatedAt').first()
                    if existing:
                        logger.info(f"[Cookie] Found session-based preference {existing.PreferenceId} (no user_id) to link to user {user_id}")
                    else:
                        # Also try to find by session_id even if it has a user_id (might be updating)
                        existing = CookiePreferences.objects.filter(SessionId=session_id).order_by('-CreatedAt').first()
                        if existing:
                            logger.info(f"[Cookie] Found preference by session_id {session_id}: PreferenceId={existing.PreferenceId}, UserId={existing.UserId.UserId if existing.UserId else 'NULL'}")
            
            # IMPORTANT: If user_id is provided, also update ALL other session-based preferences for this session
            # This ensures that if user accepted cookies before login, all preferences get linked
            if user and session_id:
                updated_count = CookiePreferences.objects.filter(
                    SessionId=session_id,
                    UserId__isnull=True
                ).update(UserId=user)
                if updated_count > 0:
                    logger.info(f"[Cookie] Updated {updated_count} session-based preference(s) to link to user {user_id}")
        elif session_id:
            # No user_id provided, find by session_id only
            existing = CookiePreferences.objects.filter(SessionId=session_id).order_by('-CreatedAt').first()
            if existing:
                logger.info(f"[Cookie] Found existing preference for session {session_id}: PreferenceId={existing.PreferenceId}, UserId={existing.UserId.UserId if existing.UserId else 'NULL'}")
        
        # Create or update preference
        if existing:
            # Update existing preference
            logger.info(f"[Cookie] Updating existing preference {existing.PreferenceId}")
            existing.EssentialCookies = data.get('essential_cookies', existing.EssentialCookies)
            existing.FunctionalCookies = data.get('functional_cookies', existing.FunctionalCookies)
            existing.AnalyticsCookies = data.get('analytics_cookies', existing.AnalyticsCookies)
            existing.MarketingCookies = data.get('marketing_cookies', existing.MarketingCookies)
            existing.PreferencesSaved = data.get('preferences_saved', existing.PreferencesSaved)
            existing.SessionId = session_id
            existing.IpAddress = ip_address
            existing.UserAgent = user_agent
            # ALWAYS update UserId if user is provided (even if it was set before)
            if user:
                # Always update UserId when user is provided
                existing.UserId = user
                logger.info(f"[Cookie] Setting/updating preference {existing.PreferenceId} UserId to {user.UserId}")
            else:
                # Only log if no user provided, but don't clear existing UserId
                if existing.UserId:
                    logger.info(f"[Cookie] No user provided, keeping existing UserId={existing.UserId.UserId}")
                else:
                    logger.info(f"[Cookie] No user provided, UserId remains NULL")
            existing.UpdatedAt = timezone.now()
            existing.save()
            preference = existing
            logger.info(f"[Cookie] Successfully updated preference {preference.PreferenceId}, UserId={preference.UserId.UserId if preference.UserId else 'NULL'}")
        else:
            # Create new preference
            logger.info(f"[Cookie] Creating new preference for user_id={user_id}, session_id={session_id}")
            try:
                preference = CookiePreferences.objects.create(
                    UserId=user,  # Will be None if user not provided, or User object if provided
                    SessionId=session_id,
                    EssentialCookies=data.get('essential_cookies', True),
                    FunctionalCookies=data.get('functional_cookies', False),
                    AnalyticsCookies=data.get('analytics_cookies', False),
                    MarketingCookies=data.get('marketing_cookies', False),
                    PreferencesSaved=data.get('preferences_saved', True),
                    IpAddress=ip_address,
                    UserAgent=user_agent
                )
                logger.info(f"[Cookie] Successfully created preference {preference.PreferenceId}, UserId={preference.UserId.UserId if preference.UserId else 'NULL'}")
            except Exception as create_error:
                logger.error(f"[Cookie] Error creating preference: {str(create_error)}")
                import traceback
                logger.error(f"[Cookie] Traceback: {traceback.format_exc()}")
                raise
        
        return Response({
            'status': 'success',
            'message': 'Cookie preferences saved successfully',
            'data': {
                'preference_id': preference.PreferenceId,
                'user_id': preference.UserId.UserId if preference.UserId else None,
                'session_id': preference.SessionId,
                'essential_cookies': preference.EssentialCookies,
                'functional_cookies': preference.FunctionalCookies,
                'analytics_cookies': preference.AnalyticsCookies,
                'marketing_cookies': preference.MarketingCookies,
                'preferences_saved': preference.PreferencesSaved,
                'created_at': preference.CreatedAt.isoformat(),
                'updated_at': preference.UpdatedAt.isoformat()
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"[Cookie] Error saving cookie preferences: {str(e)}")
        import traceback
        logger.error(f"[Cookie] Traceback: {traceback.format_exc()}")
        return Response({
            'status': 'error',
            'message': str(e),
            'error_type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_cookie_preferences(request):
    """
    Get cookie preferences for a user or session
    Query params: user_id (optional), session_id (optional)
    """
    try:
        user_id = request.GET.get('user_id')
        session_id = request.GET.get('session_id')
        
        if not user_id and not session_id:
            return Response({
                'status': 'error',
                'message': 'Either user_id or session_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to find preference
        preference = None
        if user_id:
            preference = CookiePreferences.objects.filter(UserId=user_id).order_by('-CreatedAt').first()
        
        if not preference and session_id:
            preference = CookiePreferences.objects.filter(SessionId=session_id).order_by('-CreatedAt').first()
        
        if preference:
            return Response({
                'status': 'success',
                'data': {
                    'preference_id': preference.PreferenceId,
                    'user_id': preference.UserId.UserId if preference.UserId else None,
                    'session_id': preference.SessionId,
                    'essential_cookies': preference.EssentialCookies,
                    'functional_cookies': preference.FunctionalCookies,
                    'analytics_cookies': preference.AnalyticsCookies,
                    'marketing_cookies': preference.MarketingCookies,
                    'preferences_saved': preference.PreferencesSaved,
                    'created_at': preference.CreatedAt.isoformat(),
                    'updated_at': preference.UpdatedAt.isoformat()
                }
            }, status=status.HTTP_200_OK)
        else:
            # Return default preferences (not saved yet)
            return Response({
                'status': 'success',
                'data': {
                    'preference_id': None,
                    'user_id': int(user_id) if user_id else None,
                    'session_id': session_id,
                    'essential_cookies': True,  # Essential cookies are always enabled
                    'functional_cookies': False,
                    'analytics_cookies': False,
                    'marketing_cookies': False,
                    'preferences_saved': False,
                    'created_at': None,
                    'updated_at': None
                }
            }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error fetching cookie preferences: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

