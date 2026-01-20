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
from ...authentication import get_user_from_jwt
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


def link_cookie_preferences_to_user(user, session_id=None):
    """
    Link existing cookie preferences to a user after login.
    This is called when a user logs in to link any anonymous preferences they may have created.
    
    Args:
        user: Users model instance
        session_id: Optional session_id to link by (if None, links recent preferences)
    
    Returns:
        int: Number of preferences linked
    """
    if not user or not user.UserId:
        logger.warning(f"[Cookie] Cannot link preferences: Invalid user")
        return 0
    
    logger.info(f"[Cookie] ========== Linking Cookie Preferences to User {user.UserId} ==========")
    from django.db import connection
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        updated_count = 0
        
        # Strategy 1: Link by session_id if provided (most accurate)
        # NOTE: SessionId is encrypted, so we need to use ORM to decrypt it for matching
        if session_id:
            logger.info(f"[Cookie] DEBUG: Attempting to link preferences by session_id: {session_id}")
            try:
                # Use ORM to find preferences with matching session_id (ORM handles decryption)
                # Filter for preferences with NULL UserId and matching SessionId
                preferences_to_link = CookiePreferences.objects.filter(
                    UserId__isnull=True
                )
                
                # Filter by session_id using ORM (which handles decryption)
                # We need to check each one since SessionId is encrypted
                linked_by_session = 0
                for pref in preferences_to_link:
                    # Compare decrypted SessionId (accessed via ORM)
                    if pref.SessionId == session_id:
                        # Use raw SQL to update UserId (bypasses ORM encryption issues)
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "UPDATE cookie_preferences SET UserId = %s, UpdatedAt = NOW() WHERE PreferenceId = %s",
                                [user.UserId, pref.PreferenceId]
                            )
                            if cursor.rowcount > 0:
                                linked_by_session += 1
                                logger.info(f"[Cookie] ✅ DEBUG: Linked preference {pref.PreferenceId} by session_id to user {user.UserId}")
                
                if linked_by_session > 0:
                    updated_count += linked_by_session
                    logger.info(f"[Cookie] ✅ DEBUG: Linked {linked_by_session} preference(s) by session_id to user {user.UserId}")
                else:
                    logger.info(f"[Cookie] DEBUG: No preferences found with session_id {session_id} and NULL UserId")
            except Exception as session_error:
                logger.error(f"[Cookie] ❌ ERROR: Failed to link by session_id: {str(session_error)}")
                import traceback
                logger.error(f"[Cookie] ERROR: Traceback: {traceback.format_exc()}")
        
        # Strategy 2: Link most recent preferences without UserId (within last 1 hour)
        # This catches cases where session_id might be different but user is the same
        # ALWAYS attempt to link recent preferences, even if user already has preferences
        # This handles cases where user accepted cookies before login
        logger.info(f"[Cookie] DEBUG: Attempting to link recent preferences without UserId (fallback)")
        
        # Get the most recent preferences without UserId (within last hour)
        # This catches preferences created just before login
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_prefs = CookiePreferences.objects.filter(
            UserId__isnull=True,
            CreatedAt__gte=one_hour_ago
        ).order_by('-CreatedAt')[:10]  # Increased to 10 to catch more potential matches
        
        if recent_prefs:
            logger.info(f"[Cookie] DEBUG: Found {len(recent_prefs)} recent preference(s) without UserId")
            # Update those specific preferences using raw SQL
            pref_ids = [pref.PreferenceId for pref in recent_prefs]
            with connection.cursor() as cursor:
                placeholders = ','.join(['%s'] * len(pref_ids))
                cursor.execute(
                    f"""
                    UPDATE cookie_preferences 
                    SET UserId = %s, UpdatedAt = NOW() 
                    WHERE PreferenceId IN ({placeholders})
                    """,
                    [user.UserId] + pref_ids
                )
                updated_recent = cursor.rowcount
                if updated_recent > 0:
                    updated_count += updated_recent
                    logger.info(f"[Cookie] ✅ DEBUG: Linked {updated_recent} recent preference(s) (fallback) to user {user.UserId}")
                    
                    # Verify the update using raw SQL
                    for pref_id in pref_ids:
                        cursor.execute(
                            "SELECT UserId FROM cookie_preferences WHERE PreferenceId = %s",
                            [pref_id]
                        )
                        result = cursor.fetchone()
                        if result:
                            db_user_id = result[0]
                            logger.info(f"[Cookie] ✅ VERIFIED: PreferenceId {pref_id} now has UserId: {db_user_id}")
        else:
            logger.info(f"[Cookie] DEBUG: No recent preferences found to link (fallback)")
        
        if updated_count > 0:
            logger.info(f"[Cookie] ✅ DEBUG: Total linked {updated_count} preference(s) to user {user.UserId}")
        else:
            logger.info(f"[Cookie] DEBUG: No preferences found to link (all already have UserId or none found)")
        
        logger.info(f"[Cookie] ========== End Linking Cookie Preferences ==========")
        return updated_count
            
    except Exception as bulk_error:
        logger.error(f"[Cookie] ❌ ERROR: Bulk update failed: {str(bulk_error)}")
        import traceback
        logger.error(f"[Cookie] ERROR: Traceback: {traceback.format_exc()}")
        return 0


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
        # ========== DEBUG: Initial Request Data ==========
        logger.info("=" * 80)
        logger.info("[Cookie] ========== START: Cookie Preferences Save Request ==========")
        
        # CRITICAL: Log raw request body BEFORE DRF parsing
        try:
            raw_body = request.body.decode('utf-8') if hasattr(request, 'body') and request.body else None
            logger.info(f"[Cookie] DEBUG: Raw request body (before DRF parsing): {raw_body}")
            if raw_body:
                import json
                try:
                    parsed_raw = json.loads(raw_body)
                    logger.info(f"[Cookie] DEBUG: Parsed raw body: {parsed_raw}")
                    logger.info(f"[Cookie] DEBUG: user_id in raw body: {parsed_raw.get('user_id')}")
                except:
                    logger.info(f"[Cookie] DEBUG: Could not parse raw body as JSON")
        except Exception as e:
            logger.warning(f"[Cookie] DEBUG: Could not read raw body: {str(e)}")
        
        logger.info(f"[Cookie] DEBUG: Full request data (DRF parsed): {request.data}")
        logger.info(f"[Cookie] DEBUG: Request method: {request.method}")
        logger.info(f"[Cookie] DEBUG: Request headers keys: {list(request.headers.keys())}")
        
        # CRITICAL: Log ALL headers to see what's actually received
        logger.info(f"[Cookie] DEBUG: All request headers:")
        for key, value in request.headers.items():
            if key.lower() == 'authorization':
                logger.info(f"[Cookie] DEBUG:   {key}: {value[:50]}... (length: {len(value)})")
            else:
                logger.info(f"[Cookie] DEBUG:   {key}: {value}")
        
        data = request.data
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        # Log the received user_id for debugging
        logger.info(f"[Cookie] DEBUG: Received user_id from request body: {user_id} (type: {type(user_id).__name__})")
        logger.info(f"[Cookie] DEBUG: Received session_id from request body: {session_id}")
        logger.info(f"[Cookie] DEBUG: Full request body data: {data}")
        
        # Check if Authorization header is present - try multiple ways
        auth_header = request.headers.get('Authorization', '') or request.headers.get('authorization', '') or request.META.get('HTTP_AUTHORIZATION', '')
        logger.info(f"[Cookie] DEBUG: Authorization header present: {bool(auth_header)}")
        logger.info(f"[Cookie] DEBUG: Authorization header starts with Bearer: {auth_header.startswith('Bearer ') if auth_header else False}")
        if auth_header:
            logger.info(f"[Cookie] DEBUG: Authorization header length: {len(auth_header)}")
            logger.info(f"[Cookie] DEBUG: Authorization header preview: {auth_header[:50]}...")
        else:
            logger.warning(f"[Cookie] ⚠️ WARNING: No Authorization header found in request!")
            logger.warning(f"[Cookie] ⚠️ Checked: request.headers.get('Authorization'), request.headers.get('authorization'), request.META.get('HTTP_AUTHORIZATION')")
        
        # ========== DEBUG: JWT Token Extraction ==========
        logger.info("[Cookie] DEBUG: ========== Attempting JWT Token Extraction ==========")
        user = None  # Initialize user object
        jwt_user = get_user_from_jwt(request)
        if jwt_user:
            user = jwt_user  # Use the user object directly
            user_id = jwt_user.UserId
            logger.info(f"[Cookie] ✅ DEBUG: User ID extracted from JWT token: {user_id}")
            logger.info(f"[Cookie] ✅ DEBUG: User object from JWT - UserId: {jwt_user.UserId}, UserName: {jwt_user.UserName}")
            logger.info(f"[Cookie] ✅ DEBUG: JWT user takes priority over request body user_id")
        else:
            logger.info(f"[Cookie] DEBUG: No user found in JWT token")
            logger.info(f"[Cookie] DEBUG: Will use request body user_id if provided")
        
        # ========== DEBUG: Check request.user ==========
        logger.info("[Cookie] DEBUG: ========== Checking request.user ==========")
        if not user:
            logger.info(f"[Cookie] DEBUG: request.user exists: {hasattr(request, 'user')}")
            if hasattr(request, 'user'):
                logger.info(f"[Cookie] DEBUG: request.user value: {request.user}")
                logger.info(f"[Cookie] DEBUG: request.user type: {type(request.user)}")
                if request.user:
                    logger.info(f"[Cookie] DEBUG: request.user.is_authenticated: {getattr(request.user, 'is_authenticated', 'N/A')}")
            
            if hasattr(request, 'user') and request.user and request.user.is_authenticated:
                try:
                    # request.user might be a Users object or have UserId attribute
                    if hasattr(request.user, 'UserId'):
                        user_id = request.user.UserId
                        user = request.user  # Use request.user directly if it's a Users object
                        logger.info(f"[Cookie] ✅ DEBUG: User ID extracted from request.user: {user_id}")
                        logger.info(f"[Cookie] ✅ DEBUG: User object from request.user - UserId: {user.UserId}")
                    elif hasattr(request.user, 'id'):
                        user_id = request.user.id
                        logger.info(f"[Cookie] ✅ DEBUG: User ID extracted from request.user.id: {user_id}")
                except Exception as e:
                    logger.warning(f"[Cookie] DEBUG: Could not extract user_id from request.user: {str(e)}")
                    logger.warning(f"[Cookie] DEBUG: Exception type: {type(e).__name__}")
        else:
            logger.info(f"[Cookie] DEBUG: Skipping request.user check (user already found from JWT)")
        
        # ========== DEBUG: Request Body user_id ==========
        logger.info("[Cookie] DEBUG: ========== Checking Request Body user_id ==========")
        if not user:
            # CRITICAL: Re-read user_id from request body in case it was None initially
            # This handles cases where the data might be parsed incorrectly
            user_id_from_body = data.get('user_id')
            logger.info(f"[Cookie] DEBUG: Re-reading user_id from request body: {user_id_from_body} (type: {type(user_id_from_body).__name__})")
            
            # If we got a different value, use it
            if user_id_from_body and user_id_from_body != user_id:
                logger.info(f"[Cookie] DEBUG: user_id changed from {user_id} to {user_id_from_body}")
                user_id = user_id_from_body
            
            if user_id and user_id != 'null' and user_id != 'None' and str(user_id).lower() not in ['null', 'none', '']:
                logger.info(f"[Cookie] DEBUG: Using user_id from request body: {user_id} (type: {type(user_id).__name__})")
            else:
                logger.info(f"[Cookie] DEBUG: No valid user_id provided in request body")
                logger.info(f"[Cookie] DEBUG: user_id value: {user_id}, type: {type(user_id).__name__}")
                logger.info(f"[Cookie] DEBUG: All data keys: {list(data.keys()) if data else 'No data'}")
                logger.info(f"[Cookie] DEBUG: Full data dict: {data}")
        else:
            logger.info(f"[Cookie] DEBUG: Skipping request body user_id (user already found from JWT/request.user)")
        
        # If no session_id provided, generate one
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"[Cookie] Generated new session_id: {session_id}")
        
        # ========== DEBUG: Fetch User Object from Database ==========
        logger.info("[Cookie] DEBUG: ========== Fetching User Object from Database ==========")
        logger.info(f"[Cookie] DEBUG: Current state - user_id: {user_id}, user object: {'present' if user else 'None'}")
        
        if user_id and not user:
            logger.info(f"[Cookie] DEBUG: Need to fetch user object for user_id: {user_id} (type: {type(user_id).__name__})")
            try:
                # Convert user_id to int if it's a string
                original_user_id = user_id
                if isinstance(user_id, str):
                    logger.info(f"[Cookie] DEBUG: user_id is string, attempting conversion")
                    # Handle string 'null' or 'None'
                    if user_id.lower() in ['null', 'none', '']:
                        logger.info(f"[Cookie] DEBUG: user_id is string 'null'/'none', skipping user fetch")
                        user_id = None
                    else:
                        try:
                            user_id = int(user_id)
                            logger.info(f"[Cookie] DEBUG: Successfully converted user_id from '{original_user_id}' to {user_id} (int)")
                        except ValueError as ve:
                            logger.warning(f"[Cookie] DEBUG: Cannot convert user_id '{user_id}' to int: {str(ve)}")
                            user_id = None
                else:
                    logger.info(f"[Cookie] DEBUG: user_id is already {type(user_id).__name__}, no conversion needed")
                
                # Fetch user if user_id is valid
                if user_id:
                    logger.info(f"[Cookie] DEBUG: Attempting to fetch user from database with UserId={user_id}")
                    user = Users.objects.get(UserId=user_id)
                    logger.info(f"[Cookie] ✅ DEBUG: Found user from database - UserId: {user.UserId}, UserName: {user.UserName}")
                else:
                    logger.info(f"[Cookie] DEBUG: user_id is None/invalid, cannot fetch user")
            except Users.DoesNotExist:
                logger.warning(f"[Cookie] DEBUG: User {user_id} not found in database (DoesNotExist)")
                logger.warning(f"[Cookie] DEBUG: Will save preferences without user")
                user = None
            except Exception as e:
                logger.error(f"[Cookie] DEBUG: Error fetching user {user_id}: {str(e)}")
                logger.error(f"[Cookie] DEBUG: Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"[Cookie] DEBUG: Traceback: {traceback.format_exc()}")
                user = None
        else:
            if user:
                logger.info(f"[Cookie] DEBUG: User object already present, skipping database fetch")
            elif not user_id:
                logger.info(f"[Cookie] DEBUG: No user_id available, skipping database fetch")
        
        # ========== DEBUG: Final User State ==========
        logger.info("[Cookie] DEBUG: ========== Final User State Before Save ==========")
        logger.info(f"[Cookie] DEBUG: Final user_id value: {user_id}")
        logger.info(f"[Cookie] DEBUG: Final user object: {'present' if user else 'None'}")
        if user:
            logger.info(f"[Cookie] DEBUG: Final user.UserId: {user.UserId}")
            logger.info(f"[Cookie] DEBUG: Final user.UserName: {user.UserName}")
        else:
            logger.info(f"[Cookie] DEBUG: No user object - UserId will be NULL in database")
        
        # Get IP and User Agent
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        logger.info(f"[Cookie] DEBUG: IP: {ip_address}, UserAgent: {user_agent[:50]}...")
        
        # Try to find existing preference
        # Priority: 1) By user_id (if user is available), 2) By session_id
        existing = None
        
        # CRITICAL: If we have a user (from JWT or request body), try to find preferences by user first
        if user:
            logger.info(f"[Cookie] DEBUG: User available (UserId: {user.UserId}), searching for existing preferences")
            existing = CookiePreferences.objects.filter(UserId=user).order_by('-CreatedAt').first()
            if existing:
                logger.info(f"[Cookie] DEBUG: Found existing preference for user {user.UserId}: PreferenceId={existing.PreferenceId}")
            else:
                logger.info(f"[Cookie] DEBUG: No preference found for user {user.UserId}, will search by session_id")
        
        # If not found by user, try by session_id (this handles both anonymous and logged-in cases)
        if not existing and session_id:
            logger.info(f"[Cookie] DEBUG: Searching for preferences by session_id: {session_id}")
            # First try to find session-based preference without user_id (needs linking if user is available)
            if user:
                existing = CookiePreferences.objects.filter(SessionId=session_id, UserId__isnull=True).order_by('-CreatedAt').first()
                if existing:
                    logger.info(f"[Cookie] DEBUG: Found session-based preference {existing.PreferenceId} (no user_id) - will link to user {user.UserId}")
                else:
                    # Also try to find by session_id even if it has a user_id (might be updating)
                    existing = CookiePreferences.objects.filter(SessionId=session_id).order_by('-CreatedAt').first()
                    if existing:
                        logger.info(f"[Cookie] DEBUG: Found preference by session_id: PreferenceId={existing.PreferenceId}, UserId={existing.UserId.UserId if existing.UserId else 'NULL'}")
            else:
                # No user available, just find by session_id
                existing = CookiePreferences.objects.filter(SessionId=session_id).order_by('-CreatedAt').first()
                if existing:
                    logger.info(f"[Cookie] DEBUG: Found existing preference for session {session_id}: PreferenceId={existing.PreferenceId}, UserId={existing.UserId.UserId if existing.UserId else 'NULL'}")
        
        # CRITICAL: If we have a user, aggressively link ALL preferences that don't have a UserId
        # This ensures that if user accepted cookies before login, all preferences get linked
        # We link by session_id first (most accurate), then by recent preferences (fallback)
        if user:
            logger.info(f"[Cookie] DEBUG: User available ({user.UserId}), attempting to link preferences")
            from django.db import connection
            try:
                with connection.cursor() as cursor:
                    updated_count = 0
                    
                    # Strategy 1: Link by session_id (most accurate - same browser session)
                    if session_id:
                        logger.info(f"[Cookie] DEBUG: Attempting to link preferences by session_id: {session_id}")
                        # First verify the table exists and we can query it
                        try:
                            cursor.execute(
                                "SELECT COUNT(*) FROM cookie_preferences WHERE SessionId = %s AND UserId IS NULL",
                                [session_id]
                            )
                            count_result = cursor.fetchone()
                            count_by_session = count_result[0] if count_result else 0
                            logger.info(f"[Cookie] DEBUG: Found {count_by_session} preference(s) with session_id {session_id} and NULL UserId")
                            
                            if count_by_session > 0:
                                # Use raw SQL to update - this bypasses all ORM issues
                                cursor.execute(
                                    "UPDATE cookie_preferences SET UserId = %s, UpdatedAt = NOW() WHERE SessionId = %s AND UserId IS NULL",
                                    [user.UserId, session_id]
                                )
                                updated_by_session = cursor.rowcount
                                updated_count += updated_by_session
                                logger.info(f"[Cookie] ✅ DEBUG: Linked {updated_by_session} preference(s) by session_id to user {user.UserId}")
                                
                                # Verify the update worked
                                cursor.execute(
                                    "SELECT COUNT(*) FROM cookie_preferences WHERE SessionId = %s AND UserId = %s",
                                    [session_id, user.UserId]
                                )
                                verify_count = cursor.fetchone()[0] or 0
                                logger.info(f"[Cookie] ✅ DEBUG: Verification - {verify_count} preference(s) now linked to user {user.UserId} for session {session_id}")
                            else:
                                logger.info(f"[Cookie] DEBUG: No preferences found with session_id {session_id} and NULL UserId")
                        except Exception as session_error:
                            logger.error(f"[Cookie] ❌ ERROR: Failed to link by session_id: {str(session_error)}")
                            import traceback
                            logger.error(f"[Cookie] ERROR: Traceback: {traceback.format_exc()}")
                    
                    # Strategy 2: Link most recent preferences without UserId (within last 1 hour)
                    # This catches cases where session_id might be different but user is the same
                    # Only link if user doesn't already have preferences (to avoid linking wrong ones)
                    logger.info(f"[Cookie] DEBUG: Attempting to link recent preferences without UserId (fallback)")
                    cursor.execute(
                        "SELECT COUNT(*) FROM cookie_preferences WHERE UserId = %s",
                        [user.UserId]
                    )
                    user_pref_count = cursor.fetchone()[0] or 0
                    
                    # Only link recent preferences if user doesn't have any preferences yet
                    # This prevents linking wrong preferences to a user
                    if user_pref_count == 0:
                        # Get the most recent preference IDs without UserId
                        cursor.execute(
                            """
                            SELECT PreferenceId FROM cookie_preferences 
                            WHERE UserId IS NULL 
                            AND CreatedAt >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                            ORDER BY CreatedAt DESC
                            LIMIT 5
                            """
                        )
                        pref_ids = [row[0] for row in cursor.fetchall()]
                        
                        if pref_ids:
                            # Update those specific preferences
                            placeholders = ','.join(['%s'] * len(pref_ids))
                            cursor.execute(
                                f"""
                                UPDATE cookie_preferences 
                                SET UserId = %s, UpdatedAt = NOW() 
                                WHERE PreferenceId IN ({placeholders})
                                """,
                                [user.UserId] + pref_ids
                            )
                            updated_recent = cursor.rowcount
                            if updated_recent > 0:
                                updated_count += updated_recent
                                logger.info(f"[Cookie] ✅ DEBUG: Linked {updated_recent} recent preference(s) (fallback) to user {user.UserId}")
                        else:
                            logger.info(f"[Cookie] DEBUG: No recent preferences found to link (fallback)")
                    else:
                        logger.info(f"[Cookie] DEBUG: User already has preferences, skipping fallback linking")
                    
                    if updated_count > 0:
                        logger.info(f"[Cookie] ✅ DEBUG: Total linked {updated_count} preference(s) to user {user.UserId}")
                        # Refresh existing if it was one of the updated ones
                        if existing and not existing.UserId:
                            existing.refresh_from_db()
                            logger.info(f"[Cookie] DEBUG: Refreshed existing preference after bulk update")
                    else:
                        logger.info(f"[Cookie] DEBUG: No preferences found to link (all already have UserId)")
            except Exception as bulk_error:
                logger.error(f"[Cookie] ❌ ERROR: Bulk update failed: {str(bulk_error)}")
                import traceback
                logger.error(f"[Cookie] ERROR: Traceback: {traceback.format_exc()}")
        
        # ========== DEBUG: Create or Update Preference ==========
        logger.info("[Cookie] DEBUG: ========== Creating/Updating Preference ==========")
        if existing:
            # Update existing preference
            logger.info(f"[Cookie] DEBUG: Updating existing preference {existing.PreferenceId}")
            logger.info(f"[Cookie] DEBUG: Existing preference UserId BEFORE update: {existing.UserId.UserId if existing.UserId else 'NULL'}")
            
            existing.EssentialCookies = data.get('essential_cookies', existing.EssentialCookies)
            existing.FunctionalCookies = data.get('functional_cookies', existing.FunctionalCookies)
            existing.AnalyticsCookies = data.get('analytics_cookies', existing.AnalyticsCookies)
            existing.MarketingCookies = data.get('marketing_cookies', existing.MarketingCookies)
            existing.PreferencesSaved = data.get('preferences_saved', existing.PreferencesSaved)
            existing.SessionId = session_id
            existing.IpAddress = ip_address
            existing.UserAgent = user_agent
            
            # ALWAYS update UserId if user is provided (this covers both request body and JWT-extracted user)
            # This ensures that if user logged in after saving preferences anonymously, they get linked
            if user:
                # Always update UserId when user is available (either from request body or JWT)
                logger.info(f"[Cookie] DEBUG: Setting existing.UserId to user object (UserId: {user.UserId})")
                existing.UserId = user
                # CRITICAL: Also set UserId_id directly to ensure it's saved (ForeignKey field)
                existing.UserId_id = user.UserId
                user_source = 'request body' if data.get('user_id') else 'JWT token'
                logger.info(f"[Cookie] ✅ DEBUG: Setting/updating preference {existing.PreferenceId} UserId to {user.UserId} (from {user_source})")
                logger.info(f"[Cookie] DEBUG: existing.UserId_id set to: {existing.UserId_id}")
            else:
                # Only log if no user provided, but don't clear existing UserId
                if existing.UserId:
                    logger.info(f"[Cookie] DEBUG: No user provided, keeping existing UserId={existing.UserId.UserId}")
                else:
                    logger.info(f"[Cookie] DEBUG: No user provided, UserId remains NULL")
            
            existing.UpdatedAt = timezone.now()
            logger.info(f"[Cookie] DEBUG: About to save preference to database...")
            logger.info(f"[Cookie] DEBUG: existing.UserId before save: {existing.UserId.UserId if existing.UserId else 'NULL'}")
            logger.info(f"[Cookie] DEBUG: existing.UserId_id before save: {getattr(existing, 'UserId_id', 'N/A')}")
            
            # CRITICAL: Always use raw SQL to update UserId when user is available
            # This bypasses any ORM/EncryptedFieldsMixin issues
            if user:
                # First save other fields normally
                try:
                    existing.save(update_fields=[
                        'EssentialCookies', 'FunctionalCookies', 'AnalyticsCookies', 
                        'MarketingCookies', 'PreferencesSaved', 'SessionId', 
                        'IpAddress', 'UserAgent', 'UpdatedAt'
                    ])
                    logger.info(f"[Cookie] DEBUG: Saved other fields using update_fields")
                except Exception as save_error:
                    logger.warning(f"[Cookie] DEBUG: Error saving other fields: {str(save_error)}")
                
                # ALWAYS use raw SQL to update UserId - this ensures it's saved regardless of ORM issues
                from django.db import connection
                try:
                    with connection.cursor() as cursor:
                        # Update UserId using raw SQL
                        cursor.execute(
                            "UPDATE cookie_preferences SET UserId = %s, UpdatedAt = NOW() WHERE PreferenceId = %s",
                            [user.UserId, existing.PreferenceId]
                        )
                        rows_affected = cursor.rowcount
                        logger.info(f"[Cookie] ✅ DEBUG: Used raw SQL to update UserId={user.UserId} for PreferenceId={existing.PreferenceId}, rows affected: {rows_affected}")
                        
                        if rows_affected == 0:
                            logger.error(f"[Cookie] ❌ ERROR: Raw SQL update affected 0 rows! PreferenceId={existing.PreferenceId} may not exist")
                        else:
                            # CRITICAL: Verify the update using raw SQL (not ORM) to ensure it was actually saved
                            # Use a separate query to avoid any caching issues
                            cursor.execute(
                                "SELECT UserId FROM cookie_preferences WHERE PreferenceId = %s",
                                [existing.PreferenceId]
                            )
                            result = cursor.fetchone()
                            if result:
                                db_user_id = result[0]
                                logger.info(f"[Cookie] ✅ DEBUG: Verified UserId in database via raw SQL: {db_user_id}")
                                if db_user_id != user.UserId:
                                    logger.error(f"[Cookie] ❌ ERROR: UserId mismatch after update! Expected {user.UserId}, got {db_user_id}")
                                    # Try one more time with explicit connection refresh
                                    connection.ensure_connection()
                                    cursor.execute(
                                        "UPDATE cookie_preferences SET UserId = %s, UpdatedAt = NOW() WHERE PreferenceId = %s",
                                        [user.UserId, existing.PreferenceId]
                                    )
                                    retry_rows = cursor.rowcount
                                    logger.info(f"[Cookie] ✅ DEBUG: Re-attempted UserId update, rows affected: {retry_rows}")
                                    
                                    # Verify again
                                    cursor.execute(
                                        "SELECT UserId FROM cookie_preferences WHERE PreferenceId = %s",
                                        [existing.PreferenceId]
                                    )
                                    retry_result = cursor.fetchone()
                                    if retry_result and retry_result[0] == user.UserId:
                                        logger.info(f"[Cookie] ✅ VERIFIED: UserId correctly saved after retry: {retry_result[0]}")
                                    else:
                                        logger.error(f"[Cookie] ❌ CRITICAL: Retry also failed! UserId: {retry_result[0] if retry_result else 'None'}")
                                else:
                                    logger.info(f"[Cookie] ✅ VERIFIED: UserId correctly saved to database: {db_user_id}")
                            else:
                                logger.error(f"[Cookie] ❌ ERROR: Could not verify UserId - preference not found!")
                            
                except Exception as sql_error:
                    logger.error(f"[Cookie] ❌ ERROR: Raw SQL update failed: {str(sql_error)}")
                    import traceback
                    logger.error(f"[Cookie] ERROR: Traceback: {traceback.format_exc()}")
            else:
                existing.save(update_fields=[
                    'EssentialCookies', 'FunctionalCookies', 'AnalyticsCookies', 
                    'MarketingCookies', 'PreferencesSaved', 'SessionId', 
                    'IpAddress', 'UserAgent', 'UpdatedAt'
                ])
            
            logger.info(f"[Cookie] DEBUG: Preference saved to database")
            
            preference = existing
            
            # CRITICAL: Verify UserId was actually saved by querying database directly with raw SQL
            # This bypasses ORM cache and encryption mixin issues
            if user:
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        # Use raw SQL to verify - this is the most reliable way
                        cursor.execute(
                            "SELECT UserId FROM cookie_preferences WHERE PreferenceId = %s",
                            [preference.PreferenceId]
                        )
                        result = cursor.fetchone()
                        if result:
                            db_user_id_raw = result[0]
                            logger.info(f"[Cookie] ✅ DEBUG: Successfully updated preference {preference.PreferenceId}")
                            logger.info(f"[Cookie] ✅ DEBUG: Final UserId from raw SQL query: {db_user_id_raw if db_user_id_raw else 'NULL'}")
                            
                            if db_user_id_raw != user.UserId:
                                logger.error(f"[Cookie] ❌ ERROR: UserId mismatch! Expected {user.UserId}, but database has {db_user_id_raw}")
                                # CRITICAL: Force update using raw SQL as last resort
                                logger.warning(f"[Cookie] DEBUG: Attempting force update using raw SQL...")
                                cursor.execute(
                                    "UPDATE cookie_preferences SET UserId = %s, UpdatedAt = NOW() WHERE PreferenceId = %s",
                                    [user.UserId, preference.PreferenceId]
                                )
                                rows_updated = cursor.rowcount
                                logger.info(f"[Cookie] DEBUG: Force updated UserId={user.UserId} using raw SQL, rows affected: {rows_updated}")
                                
                                # Verify again with raw SQL
                                cursor.execute(
                                    "SELECT UserId FROM cookie_preferences WHERE PreferenceId = %s",
                                    [preference.PreferenceId]
                                )
                                verify_result = cursor.fetchone()
                                if verify_result:
                                    final_user_id = verify_result[0]
                                    if final_user_id == user.UserId:
                                        logger.info(f"[Cookie] ✅ VERIFIED: UserId correctly saved after force update: {final_user_id}")
                                    else:
                                        logger.error(f"[Cookie] ❌ CRITICAL: Force update failed! UserId still {final_user_id}, expected {user.UserId}")
                                else:
                                    logger.error(f"[Cookie] ❌ CRITICAL: Could not verify after force update!")
                            else:
                                logger.info(f"[Cookie] ✅ VERIFIED: UserId correctly saved to database: {db_user_id_raw}")
                        else:
                            logger.error(f"[Cookie] ❌ ERROR: Preference {preference.PreferenceId} not found in database!")
                    
                    # Now refresh from database for ORM object (after verification)
                    preference.refresh_from_db()
                    logger.info(f"[Cookie] ✅ DEBUG: Final UserId in ORM object: {preference.UserId.UserId if preference.UserId else 'NULL'}")
                    logger.info(f"[Cookie] ✅ DEBUG: Final SessionId: {preference.SessionId}")
                except Exception as verify_error:
                    logger.error(f"[Cookie] ERROR: Could not verify UserId in database: {str(verify_error)}")
                    import traceback
                    logger.error(f"[Cookie] ERROR: Traceback: {traceback.format_exc()}")
                    # If verification fails but we have a user, try force update anyway
                    if user:
                        logger.warning(f"[Cookie] DEBUG: Verification failed, attempting force update...")
                        try:
                            from django.db import connection
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "UPDATE cookie_preferences SET UserId = %s, UpdatedAt = NOW() WHERE PreferenceId = %s",
                                    [user.UserId, preference.PreferenceId]
                                )
                                logger.info(f"[Cookie] DEBUG: Force updated UserId={user.UserId} using raw SQL (after verification error), rows affected: {cursor.rowcount}")
                        except Exception as force_error:
                            logger.error(f"[Cookie] ERROR: Force update also failed: {str(force_error)}")
            else:
                # No user, just refresh normally
                preference.refresh_from_db()
                logger.info(f"[Cookie] ✅ DEBUG: Final SessionId: {preference.SessionId}")
        else:
            # Create new preference
            effective_user_id = user.UserId if user else (user_id if user_id else None)
            logger.info(f"[Cookie] DEBUG: Creating NEW preference")
            logger.info(f"[Cookie] DEBUG: effective_user_id: {effective_user_id}")
            logger.info(f"[Cookie] DEBUG: session_id: {session_id}")
            logger.info(f"[Cookie] DEBUG: user_object: {'present' if user else 'None'}")
            if user:
                logger.info(f"[Cookie] DEBUG: user.UserId: {user.UserId}")
            
            try:
                logger.info(f"[Cookie] DEBUG: About to create CookiePreferences with UserId={user.UserId if user else 'None'}")
                
                # CRITICAL: Create preference first, then use raw SQL to set UserId if user is available
                # This ensures UserId is saved even if ORM has issues
                create_kwargs = {
                    'SessionId': session_id,
                    'EssentialCookies': data.get('essential_cookies', True),
                    'FunctionalCookies': data.get('functional_cookies', False),
                    'AnalyticsCookies': data.get('analytics_cookies', False),
                    'MarketingCookies': data.get('marketing_cookies', False),
                    'PreferencesSaved': data.get('preferences_saved', True),
                    'IpAddress': ip_address,
                    'UserAgent': user_agent
                }
                
                # Set UserId if user is available (try ORM first)
                if user:
                    create_kwargs['UserId'] = user
                    create_kwargs['UserId_id'] = user.UserId  # Also set the FK id directly
                    logger.info(f"[Cookie] DEBUG: Creating with UserId={user.UserId} and UserId_id={user.UserId}")
                else:
                    logger.info(f"[Cookie] DEBUG: Creating without UserId (anonymous)")
                
                preference = CookiePreferences.objects.create(**create_kwargs)
                logger.info(f"[Cookie] DEBUG: CookiePreferences object created in memory, PreferenceId={preference.PreferenceId}")
                
                # CRITICAL: If user is available, ALWAYS use raw SQL to ensure UserId is set
                # This is a safety measure in case ORM create didn't set it correctly
                if user:
                    from django.db import connection
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "UPDATE cookie_preferences SET UserId = %s, UpdatedAt = NOW() WHERE PreferenceId = %s",
                                [user.UserId, preference.PreferenceId]
                            )
                            rows_affected = cursor.rowcount
                            logger.info(f"[Cookie] ✅ DEBUG: Used raw SQL to set UserId={user.UserId} for new PreferenceId={preference.PreferenceId}, rows affected: {rows_affected}")
                            
                            # CRITICAL: Verify using raw SQL (not ORM) to ensure it was actually saved
                            cursor.execute(
                                "SELECT UserId FROM cookie_preferences WHERE PreferenceId = %s",
                                [preference.PreferenceId]
                            )
                            result = cursor.fetchone()
                            if result:
                                db_user_id_raw = result[0]
                                logger.info(f"[Cookie] ✅ DEBUG: Verified UserId in database via raw SQL: {db_user_id_raw}")
                                if db_user_id_raw != user.UserId:
                                    logger.error(f"[Cookie] ❌ ERROR: UserId mismatch after create! Expected {user.UserId}, got {db_user_id_raw}")
                                    # Try one more time
                                    cursor.execute(
                                        "UPDATE cookie_preferences SET UserId = %s, UpdatedAt = NOW() WHERE PreferenceId = %s",
                                        [user.UserId, preference.PreferenceId]
                                    )
                                    retry_rows = cursor.rowcount
                                    logger.info(f"[Cookie] ✅ DEBUG: Re-attempted UserId update, rows affected: {retry_rows}")
                                else:
                                    logger.info(f"[Cookie] ✅ VERIFIED: UserId correctly saved to database: {db_user_id_raw}")
                            else:
                                logger.error(f"[Cookie] ❌ ERROR: Could not verify UserId - preference not found!")
                    except Exception as sql_error:
                        logger.error(f"[Cookie] ❌ ERROR: Raw SQL update failed for new preference: {str(sql_error)}")
                        import traceback
                        logger.error(f"[Cookie] ERROR: Traceback: {traceback.format_exc()}")
                
                # Refresh to get actual database values (after raw SQL verification)
                preference.refresh_from_db()
                logger.info(f"[Cookie] ✅ DEBUG: Final UserId in ORM object: {preference.UserId.UserId if preference.UserId else 'NULL'}")
                logger.info(f"[Cookie] ✅ DEBUG: Final SessionId: {preference.SessionId}")
            except Exception as create_error:
                logger.error(f"[Cookie] DEBUG: Error creating preference: {str(create_error)}")
                logger.error(f"[Cookie] DEBUG: Exception type: {type(create_error).__name__}")
                import traceback
                logger.error(f"[Cookie] DEBUG: Traceback: {traceback.format_exc()}")
                raise
        
        # ========== DEBUG: Response Data ==========
        response_user_id = preference.UserId.UserId if preference.UserId else None
        logger.info("[Cookie] DEBUG: ========== Preparing Response ==========")
        logger.info(f"[Cookie] DEBUG: Response preference_id: {preference.PreferenceId}")
        logger.info(f"[Cookie] DEBUG: Response user_id: {response_user_id}")
        logger.info(f"[Cookie] DEBUG: Response session_id: {preference.SessionId}")
        
        response_data = {
            'status': 'success',
            'message': 'Cookie preferences saved successfully',
            'data': {
                'preference_id': preference.PreferenceId,
                'user_id': response_user_id,
                'session_id': preference.SessionId,
                'essential_cookies': preference.EssentialCookies,
                'functional_cookies': preference.FunctionalCookies,
                'analytics_cookies': preference.AnalyticsCookies,
                'marketing_cookies': preference.MarketingCookies,
                'preferences_saved': preference.PreferencesSaved,
                'created_at': preference.CreatedAt.isoformat(),
                'updated_at': preference.UpdatedAt.isoformat()
            }
        }
        
        logger.info(f"[Cookie] DEBUG: Response data: {response_data}")
        logger.info("[Cookie] ========== END: Cookie Preferences Save Request ==========")
        logger.info("=" * 80)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error("=" * 80)
        logger.error("[Cookie] ========== ERROR: Cookie Preferences Save Failed ==========")
        logger.error(f"[Cookie] ERROR: Error saving cookie preferences: {str(e)}")
        logger.error(f"[Cookie] ERROR: Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"[Cookie] ERROR: Traceback: {traceback.format_exc()}")
        logger.error("[Cookie] ========== END ERROR ==========")
        logger.error("=" * 80)
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
            # Filter by UserId field (ForeignKey), not the user_id integer
            preference = CookiePreferences.objects.filter(UserId__UserId=user_id).order_by('-CreatedAt').first()
        
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

