import jwt
import json
import logging
import time
import uuid
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.hashers import make_password, check_password
from .models import Users, GRCLog, RBAC, Framework
from .models import Users, GRCLog, ProductVersion
from .rbac.utils import RBACUtils
from django.views.decorators.csrf import csrf_exempt
from .mfa_service import MfaService

logger = logging.getLogger(__name__)

# JWT Settings
JWT_SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME = timedelta(days=3)  # 3 days
JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=7)  # 7 days


def _safe_parse_version(ver: str):
    """Parse semantic-ish version to a tuple for comparison."""
    if not ver:
        return (0,)
    parts = []
    for part in str(ver).split('.'):
        try:
            parts.append(int(part))
        except ValueError:
            # Fall back to string for non-numeric segments
            parts.append(part)
    return tuple(parts)


def _compare_versions(left: str, right: str) -> int:
    """Return -1 if left<right, 0 if equal, 1 if left>right."""
    l_parts = _safe_parse_version(left)
    r_parts = _safe_parse_version(right)
    # Normalize length
    max_len = max(len(l_parts), len(r_parts))
    l_parts += (0,) * (max_len - len(l_parts))
    r_parts += (0,) * (max_len - len(r_parts))
    if l_parts < r_parts:
        return -1
    if l_parts > r_parts:
        return 1
    return 0


def _get_active_versions():
    """Fetch latest and minimum supported product versions."""
    latest = ProductVersion.get_latest()
    min_supported = ProductVersion.get_min_supported()
    return {
        'latest_version': latest.version if latest else None,
        'min_supported_version': min_supported.version if min_supported else None,
    }

def _get_default_framework():
    """Get a default framework for logging purposes"""
    try:
        # Try to get the first active framework
        framework = Framework.objects.filter(ActiveInactive='Active').first()
        if framework:
            return framework
        # If no active framework, get any framework
        framework = Framework.objects.first()
        if framework:
            return framework
    except Exception as e:
        logger.warning(f"Error getting default framework for logging: {str(e)}")
    return None

def _get_user_session_token(user_id):
    """Get the active session token for a user"""
    cache_key = f"user_session_{user_id}"
    return cache.get(cache_key)

def _set_user_session_token(user_id, session_token):
    """Set the active session token for a user (expires after 7 days to match refresh token lifetime)"""
    cache_key = f"user_session_{user_id}"
    # Cache for 7 days (same as refresh token lifetime)
    cache.set(cache_key, session_token, 7 * 24 * 60 * 60)
    logger.debug(f"Session token set for user {user_id}: {session_token}")

def _invalidate_user_session(user_id):
    """Invalidate the active session for a user (used when logging in from new location)"""
    cache_key = f"user_session_{user_id}"
    cache.delete(cache_key)
    logger.info(f"Session invalidated for user {user_id}")

def _is_session_token_valid(user_id, session_token):
    """Check if a session token is valid for a user
    
    Args:
        user_id: User ID
        session_token: Session token to validate (can be None for backward compatibility)
    
    Returns:
        True if session token is valid, False otherwise
        If session_token is None (old tokens without jti), returns True for backward compatibility
    """
    # Backward compatibility: if session_token is None, allow (old tokens without jti)
    if session_token is None:
        return True
    
    active_session_token = _get_user_session_token(user_id)
    if active_session_token is None:
        # No active session exists (user logged out or never logged in with new system)
        return False
    return active_session_token == session_token

def _log_failed_login(username, login_type, client_ip, reason, failed_attempts=None, additional_info=None):
    """Log failed login attempt to grc_logs table"""
    try:
        # Get default framework
        framework = _get_default_framework()
        if not framework:
            logger.warning("Cannot log failed login attempt: No framework available")
            return
        
        # Try to resolve actual username if login_type is 'userid'
        actual_username = username
        user_id_for_log = None
        if login_type == 'userid':
            try:
                user_id = int(username)
                user_obj = Users.objects.get(UserId=user_id)
                actual_username = user_obj.UserName
                user_id_for_log = str(user_id)
            except (ValueError, Users.DoesNotExist):
                # If user doesn't exist or invalid ID, keep the original value
                actual_username = username
                user_id_for_log = username
        
        # Prepare log data
        log_data = {
            'Module': 'Authentication',
            'ActionType': 'LOGIN_FAILED',
            'Description': f'Failed login attempt for {login_type}: {username}. Reason: {reason}',
            'UserName': actual_username,  # Use actual username, not user ID
            'LogLevel': 'WARNING',
            'IPAddress': client_ip,
            'FrameworkId': framework,
            'AdditionalInfo': additional_info or {}
        }
        
        # Add user ID to additional info if we have it
        if user_id_for_log:
            log_data['AdditionalInfo']['attempted_user_id'] = user_id_for_log
        
        # Add UserId field if we have it
        if user_id_for_log:
            log_data['UserId'] = user_id_for_log
        
        # Add failed attempts count if provided
        if failed_attempts is not None:
            log_data['AdditionalInfo']['failed_attempts'] = failed_attempts
        
        # Create and save log entry
        log_entry = GRCLog(**log_data)
        log_entry.save()
        logger.debug(f"Logged failed login attempt for {actual_username} (login_type: {login_type}, identifier: {username}) to grc_logs")
    except Exception as e:
        logger.error(f"Error logging failed login attempt: {str(e)}")
        # Don't raise - logging failure shouldn't break login flow
 
def _send_account_lockout_email(user_email, username, client_ip):
    """
    Send email notification when user account is locked due to multiple failed login attempts.
    Uses SMTP configuration from .env file (SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD).
    """
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        from_name = getattr(settings, 'DEFAULT_FROM_NAME', 'GRC System')
       
        subject = 'Account Locked - Multiple Failed Login Attempts'
       
        # Create HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Account Locked</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
            <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #dc3545; margin: 0; font-size: 28px;">⚠️ Account Locked</h1>
                </div>
               
                <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                    <p style="margin: 0; color: #856404; font-weight: bold;">
                        Security Alert: Your account has been temporarily locked due to multiple failed login attempts.
                    </p>
                </div>
               
                <p style="font-size: 16px; margin-bottom: 15px;">Dear {username},</p>
               
                <p style="font-size: 16px; margin-bottom: 15px;">
                    We detected <strong>5 consecutive failed login attempts</strong> on your account.
                    As a security measure, your account has been temporarily locked for <strong>15 minutes</strong>.
                </p>
               
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px; color: #6c757d;">
                        <strong>Login Details:</strong><br>
                        Username/User ID: {username}<br>
                        IP Address: {client_ip}<br>
                        Lockout Duration: 15 minutes<br>
                        Lockout Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                </div>
               
                <h3 style="color: #333; margin-top: 30px; margin-bottom: 15px;">What should you do?</h3>
                <ul style="font-size: 16px; line-height: 1.8; margin-bottom: 20px;">
                    <li>Wait 15 minutes before attempting to login again</li>
                    <li>Make sure you are using the correct username/User ID and password</li>
                    <li>If you forgot your password, use the "Forgot Password" feature</li>
                    <li>If this was not you, please contact your administrator immediately</li>
                </ul>
               
                <div style="background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0; color: #0d47a1; font-size: 14px;">
                        <strong>Security Tip:</strong> If you continue to experience login issues,
                        please verify your credentials or contact the system administrator for assistance.
                    </p>
                </div>
               
                <p style="font-size: 14px; color: #6c757d; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                    This is an automated security notification. Please do not reply to this email.<br>
                    If you have any concerns about your account security, contact your administrator immediately.
                </p>
               
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                    <p style="margin: 0; font-size: 12px; color: #999;">
                        © {datetime.now().year} GRC System - {from_name}<br>
                        This email was sent for security purposes only.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
       
        # Plain text version
        text_content = f"""
Account Locked - Multiple Failed Login Attempts
 
Dear {username},
 
We detected 5 consecutive failed login attempts on your account.
As a security measure, your account has been temporarily locked for 15 minutes.
 
Login Details:
- Username/User ID: {username}
- IP Address: {client_ip}
- Lockout Duration: 15 minutes
- Lockout Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
 
What should you do?
- Wait 15 minutes before attempting to login again
- Make sure you are using the correct username/User ID and password
- If you forgot your password, use the "Forgot Password" feature
- If this was not you, please contact your administrator immediately
 
This is an automated security notification. Please do not reply to this email.
If you have any concerns about your account security, contact your administrator immediately.
 
© {datetime.now().year} GRC System - {from_name}
        """
       
        # Send email using Django's email backend (configured to use Azure/SMTP from .env)
        try:
            # First try using NotificationService if available (uses Azure/SMTP with fallback)
            from grc.routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
           
            # Use a simple notification or create a custom email
            # Since there's no template for account lockout, we'll use Django's send_mail directly
            # But try NotificationService's Azure sender first
            if hasattr(notification_service, 'azure_email_sender'):
                if notification_service.azure_email_sender.is_configured():
                    success = notification_service.azure_email_sender.send_email_via_graph(
                        to_email=user_email,
                        subject=subject,
                        html_body=html_content,
                        from_email=from_email,
                        from_name=from_name
                    )
                    if success:
                        logger.info(f"Account lockout email sent successfully via Azure to {user_email}")
                        return
        except Exception as notification_error:
            logger.debug(f"NotificationService unavailable, using Django send_mail: {str(notification_error)}")
       
        # Fallback to Django's send_mail (uses EMAIL_BACKEND from settings, which is configured for Azure/SMTP)
        send_mail(
            subject=subject,
            message=text_content,
            from_email=f"{from_name} <{from_email}>",
            recipient_list=[user_email],
            html_message=html_content,
            fail_silently=False,
        )
       
        logger.info(f"Account lockout email sent successfully to {user_email} for user {username}")
       
    except Exception as e:
        logger.error(f"Failed to send account lockout email to {user_email}: {str(e)}")
        # Don't raise exception - email failure shouldn't affect lockout process
 
 

def assign_default_rbac_permissions_for_google_sso(user):
    """
    Assign default view permissions to Google SSO users in both GRC and TPRM RBAC tables.
    This ensures users have basic view access to all modules.
    """
    try:
        # Get user's default framework - use first available if user doesn't have one
        framework = getattr(user, 'FrameworkId', None)
        if not framework:
            from .models import Framework
            framework = Framework.objects.first()
            if framework:
                logger.info(f"User {user.UserName} doesn't have FrameworkId, using default framework: {framework.FrameworkId}")
            else:
                logger.warning(f"No framework available for RBAC assignment for user {user.UserName}")
                # Continue without framework - some RBAC entries might not require it
        
        # ========================================
        # GRC RBAC Permissions
        # ========================================
        # Check if RBAC entry already exists for this user (any role)
        # Since unique_together is ['user', 'role'], we check for any existing entry first
        existing_rbac = RBAC.objects.filter(user=user).first()
        
        if existing_rbac:
            # Update existing RBAC entry with view permissions if not already set
            updated = False
            if not existing_rbac.view_all_compliance:
                existing_rbac.view_all_compliance = True
                updated = True
            if not existing_rbac.view_all_policy:
                existing_rbac.view_all_policy = True
                updated = True
            if not existing_rbac.view_audit_reports:
                existing_rbac.view_audit_reports = True
                updated = True
            if not existing_rbac.view_all_risk:
                existing_rbac.view_all_risk = True
                updated = True
            if not existing_rbac.view_all_incident:
                existing_rbac.view_all_incident = True
                updated = True
            if not existing_rbac.view_all_event:
                existing_rbac.view_all_event = True
                updated = True
            
            if updated:
                existing_rbac.save()
                logger.info(f"✅ Updated GRC RBAC permissions for Google SSO user: {user.UserName}")
            else:
                logger.info(f"✅ GRC RBAC permissions already set for Google SSO user: {user.UserName}")
        else:
            # Create new RBAC entry with view permissions
            # Only create if we have a framework
            if framework:
                rbac_entry = RBAC.objects.create(
                    user=user,
                    username=user.UserName,
                    role='End User',  # Default role for Google SSO users
                    FrameworkId=framework,
                    is_active='Y',
                # Set all view permissions to True
                view_all_compliance=True,
                view_all_policy=True,
                view_audit_reports=True,
                view_all_risk=True,
                view_all_incident=True,
                view_all_event=True,
                # All other permissions remain False (view only)
                )
                logger.info(f"✅ Created GRC RBAC entry with view permissions for Google SSO user: {user.UserName}")
            else:
                logger.warning(f"⚠️ Cannot create GRC RBAC entry for user {user.UserName}: No framework available")
        
        # ========================================
        # TPRM RBAC Permissions
        # ========================================
        try:
            from tprm_backend.rbac.models import RBACTPRM
            
            # Check if TPRM RBAC entry exists for this user
            existing_tprm_rbac = RBACTPRM.objects.filter(user_id=user.UserId).first()
            
            if existing_tprm_rbac:
                # Update existing TPRM RBAC entry with view permissions if not already set
                tprm_updated = False
                view_permissions = [
                    'view_rfp', 'view_rfp_responses', 'view_rfp_approval_status',
                    'view_rfp_versions', 'view_rfp_version', 'view_rfp_response_scores',
                    'view_rfp_analytics', 'view_rfp_audit_trail', 'view_vendors',
                    'view_contacts_documents', 'view_risk_profile', 'view_lifecycle_history',
                    'view_questionnaires', 'view_risk_assessments', 'view_screening_results',
                    'view_vendor_contracts', 'view_available_vendors', 'view_vendor_risk_scores',
                    'view_identified_risks', 'view_risk_mitigation_status',
                    'view_compliance_status_of_plans', 'view_document_access_logs',
                    'view_audit_logs', 'view_compliance_audit_results',
                    'view_incident_response_plans', 'view_sla', 'view_performance',
                    'view_alerts', 'view_dashboard_trend', 'view_plans_and_documents',
                    'view_bcp_drp_plan_status', 'view_vendor_submitted_documents',
                    'view_document_status_history', 'list_contracts', 'list_contract_terms',
                    'list_contract_renewals'
                ]
                
                for perm in view_permissions:
                    if hasattr(existing_tprm_rbac, perm) and not getattr(existing_tprm_rbac, perm):
                        setattr(existing_tprm_rbac, perm, True)
                        tprm_updated = True
                
                if tprm_updated:
                    existing_tprm_rbac.save()
                    logger.info(f"✅ Updated TPRM RBAC permissions for Google SSO user: {user.UserName}")
                else:
                    logger.info(f"✅ TPRM RBAC permissions already set for Google SSO user: {user.UserName}")
            else:
                # Create new TPRM RBAC entry with view permissions
                tprm_rbac_entry = RBACTPRM.objects.create(
                    user_id=user.UserId,
                    username=user.UserName,
                    role='End User',  # Default role for Google SSO users
                    is_active='Y',
                    # Set all view permissions to True
                    view_rfp=True,
                    view_rfp_responses=True,
                    view_rfp_approval_status=True,
                    view_rfp_versions=True,
                    view_rfp_version=True,
                    view_rfp_response_scores=True,
                    view_rfp_analytics=True,
                    view_rfp_audit_trail=True,
                    view_vendors=True,
                    view_contacts_documents=True,
                    view_risk_profile=True,
                    view_lifecycle_history=True,
                    view_questionnaires=True,
                    view_risk_assessments=True,
                    view_screening_results=True,
                    view_vendor_contracts=True,
                    view_available_vendors=True,
                    view_vendor_risk_scores=True,
                    view_identified_risks=True,
                    view_risk_mitigation_status=True,
                    view_compliance_status_of_plans=True,
                    view_document_access_logs=True,
                    view_audit_logs=True,
                    view_compliance_audit_results=True,
                    view_incident_response_plans=True,
                    view_sla=True,
                    view_performance=True,
                    view_alerts=True,
                    view_dashboard_trend=True,
                    view_plans_and_documents=True,
                    view_bcp_drp_plan_status=True,
                    view_vendor_submitted_documents=True,
                    view_document_status_history=True,
                    list_contracts=True,
                    list_contract_terms=True,
                    list_contract_renewals=True,
                    # All other permissions remain False (view only)
                )
                logger.info(f"✅ Created TPRM RBAC entry with view permissions for Google SSO user: {user.UserName}")
                
        except ImportError:
            logger.warning("TPRM RBAC model not available, skipping TPRM permissions assignment")
        except Exception as tprm_error:
            logger.error(f"Error assigning TPRM RBAC permissions for Google SSO user {user.UserName}: {str(tprm_error)}")
            import traceback
            logger.error(f"TPRM RBAC Traceback: {traceback.format_exc()}")
        
    except Exception as e:
        logger.error(f"Error assigning default RBAC permissions for Google SSO user {user.UserName}: {str(e)}")
        # Don't fail the login if RBAC assignment fails
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

# JWT Settings
JWT_SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME = timedelta(days=3)  # 3 days
JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=7)  # 7 days

def generate_jwt_tokens(user, login_time=None, session_token=None):
    """Generate JWT access and refresh tokens for a user
    
    Args:
        user: User object
        login_time: Optional original login time (for token refresh - preserves original login time)
                    If None, uses current time (for new login)
        session_token: Optional session token (for multi-session management)
                      If None, generates a new one (for new login)
    """
    try:
        import time
        versions = _get_active_versions()
        latest_version = versions.get('latest_version') or '0.0.0'
        min_supported = versions.get('min_supported_version') or latest_version
        
        # Use provided login_time or current time (for new login)
        if login_time is None:
            login_time = time.time()  # Store original login time for 5-minute timeout check
        
        # Generate or use provided session token
        if session_token is None:
            session_token = str(uuid.uuid4())
        
        # MULTI-TENANCY: Get tenant_id from user
        tenant_id = None
        tenant_name = None
        if hasattr(user, 'tenant') and user.tenant:
            tenant_id = user.tenant.tenant_id
            tenant_name = user.tenant.name
        
        # Decrypt user fields before storing in token
        username_plain = getattr(user, 'UserName_plain', None) or getattr(user, 'UserName', None)
        email_plain = getattr(user, 'email_plain', None) or getattr(user, 'Email', None)
        firstname_plain = getattr(user, 'FirstName_plain', None) or getattr(user, 'FirstName', None)
        lastname_plain = getattr(user, 'LastName_plain', None) or getattr(user, 'LastName', None)
        
        # Create refresh token
        refresh = RefreshToken()
        refresh['user_id'] = user.UserId
        refresh['username'] = username_plain
        refresh['email'] = email_plain
        refresh['first_name'] = firstname_plain
        refresh['last_name'] = lastname_plain
        # MULTI-TENANCY: Add tenant info to token
        refresh['tenant_id'] = tenant_id
        refresh['tenant_name'] = tenant_name
        refresh['ver'] = latest_version
        refresh['min_ver'] = min_supported
        refresh['login_time'] = login_time  # Store original login time (persists through token refresh)
        refresh['jti'] = session_token  # Store session token in JWT ID claim
        
        # Create access token
        access_token = refresh.access_token
        access_token['user_id'] = user.UserId
        # Use decrypted values (already computed above)
        access_token['username'] = username_plain
        access_token['email'] = email_plain
        access_token['first_name'] = firstname_plain
        access_token['last_name'] = lastname_plain
        # MULTI-TENANCY: Add tenant info to token
        access_token['tenant_id'] = tenant_id
        access_token['tenant_name'] = tenant_name
        access_token['ver'] = latest_version
        access_token['min_ver'] = min_supported
        access_token['login_time'] = login_time  # Store original login time
        access_token['jti'] = session_token  # Store session token in JWT ID claim
        
        return {
            'access': str(access_token),
            'refresh': str(refresh),
            'access_token_expires': access_token.current_time + JWT_ACCESS_TOKEN_LIFETIME,
            'refresh_token_expires': refresh.current_time + JWT_REFRESH_TOKEN_LIFETIME,
            'session_token': session_token
        }
    except Exception as e:
        logger.error(f"Error generating JWT tokens: {str(e)}")
        raise

def verify_jwt_token(token, check_session=False):
    """Verify and decode JWT token
    
    Args:
        token: JWT token string
        check_session: If True, also validates session token (multi-session management) - DISABLED
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Session token validation disabled - always allow valid JWT tokens
        # if check_session:
        #     user_id = payload.get('user_id')
        #     session_token = payload.get('jti')  # JWT ID claim contains session token
        #     if user_id:
        #         if not _is_session_token_valid(user_id, session_token):
        #             logger.warning(f"Session token invalid for user {user_id} - session may have been invalidated")
        #             return None
        
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error verifying JWT token: {str(e)}")
        return None

def get_user_from_token(token):
    """Get user from JWT token"""
    try:
        payload = verify_jwt_token(token)
        if payload and 'user_id' in payload:
            user = Users.objects.get(UserId=payload['user_id'])
            return user
        return None
    except Users.DoesNotExist:
        logger.warning(f"User not found for token payload: {payload}")
        return None
    except Exception as e:
        logger.error(f"Error getting user from token: {str(e)}")
        return None

def verify_recaptcha(captcha_token):
    """Verify reCAPTCHA token with Google's API"""
    if not getattr(settings, 'RECAPTCHA_ENABLED', True):
        logger.debug("reCAPTCHA verification disabled in settings")
        return True
    
    if not captcha_token:
        logger.warning("reCAPTCHA token is missing")
        return False
    
    secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
    if not secret_key:
        logger.warning("reCAPTCHA secret key not configured")
        return False
    
    try:
        # Verify with Google's reCAPTCHA API
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        response = requests.post(verify_url, data={
            'secret': secret_key,
            'response': captcha_token
        }, timeout=5)
        
        result = response.json()
        
        if result.get('success'):
            logger.debug("reCAPTCHA verification successful")
            return True
        else:
            error_codes = result.get('error-codes', [])
            logger.warning(f"reCAPTCHA verification failed: {error_codes}")
            return False
    except Exception as e:
        logger.error(f"Error verifying reCAPTCHA: {str(e)}")
        return False

@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_login(request):
    """JWT Login endpoint with rate limiting and account lockout"""
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')
        login_type = data.get('login_type', 'username')  # Default to username if not specified
        otp = data.get('otp')  # MFA OTP code
        captcha_token = data.get('captcha_token')  # reCAPTCHA token
        
        if not username or not password:
            return Response({
                'status': 'error',
                'message': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========================================
        # CAPTCHA VERIFICATION (only for username/userid login, not Google SSO)
        # ========================================
        if not verify_recaptcha(captcha_token):
            return Response({
                'status': 'error',
                'message': 'CAPTCHA verification failed. Please try again.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========================================
        # RATE LIMITING - PER IP
        # ========================================
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        ip_cache_key = f"login_rate_limit_ip_{client_ip}"
        ip_attempts = cache.get(ip_cache_key, 0)
        
        if ip_attempts >= 10:  # Max 10 login attempts per minute per IP
            return Response({
                'status': 'error',
                'message': 'Too many login attempts from this IP. Please wait 1 minute and try again.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Increment IP counter
        cache.set(ip_cache_key, ip_attempts + 1, 60)  # 60 seconds
        
        # ========================================
        # RATE LIMITING - PER USERNAME (LOCKOUT)
        # ========================================
        # Normalize username for cache key
        username_normalized = str(username).lower().strip()
        user_cache_key = f"login_failed_attempts_{username_normalized}"
        lockout_cache_key = f"login_locked_until_{username_normalized}"
        
        # Check if account is locked
        locked_until = cache.get(lockout_cache_key)
        if locked_until:
            remaining_seconds = int(locked_until - time.time())
            if remaining_seconds > 0:
                remaining_minutes = remaining_seconds // 60
                return Response({
                    'status': 'error',
                    'message': f'Account temporarily locked due to too many failed login attempts. Please try again in {remaining_minutes + 1} minute(s).',
                    'locked_until': remaining_seconds
                }, status=status.HTTP_403_FORBIDDEN)
            else:
                # Lock expired, clear it
                cache.delete(lockout_cache_key)
                cache.delete(user_cache_key)
        
        # Authenticate user with our custom user model based on login type
        user = None
        try:
            if login_type == 'userid':
                # Login with User ID
                user_id = int(username)  # Convert to integer
                candidate = Users.objects.get(UserId=user_id)
                logger.info(f"🔍 LOGIN DEBUG: User found by ID: {candidate.UserId} - {candidate.UserName}")
                logger.info(f"🔍 LOGIN DEBUG: User {candidate.UserId} - IsActive: {candidate.IsActive}, HasLicenseKey: {bool(candidate.license_key)}")
            else:
                # Login with Username (default) - handles encrypted usernames
                candidate = Users.find_by_username(username)
                if not candidate:
                    raise Users.DoesNotExist(f"User with username '{username}' not found")
                logger.info(f"🔍 LOGIN DEBUG: User found by username: {candidate.UserId} - {candidate.UserName}")
                logger.info(f"🔍 LOGIN DEBUG: User {candidate.UserId} - IsActive: {candidate.IsActive}, HasLicenseKey: {bool(candidate.license_key)}")

            # Check hashed password first
            password_check_result = check_password(password, candidate.Password)
            logger.info(f"🔍 LOGIN DEBUG: User {candidate.UserId} - Password check result: {password_check_result}")
            
            if password_check_result:
                user = candidate
                logger.info(f"✅ LOGIN DEBUG: Password verified successfully for User {candidate.UserId}")
            # Backward compatibility: migrate legacy plain-text passwords
            elif candidate.Password == password:
                candidate.Password = make_password(password)
                candidate.save(update_fields=['Password'])
                user = candidate
                logger.warning(f"Password for user {candidate.UserName} was stored in plain text and has been hashed.")
            else:
                logger.warning(f"❌ LOGIN DEBUG: Password check failed for User {candidate.UserId} - Password doesn't match hashed or plain text")
        except Users.DoesNotExist:
            logger.warning(f"❌ LOGIN DEBUG: User not found - login_type: {login_type}, username/userid: {username}")
            user = None
        except ValueError:
            logger.warning(f"Login failed - invalid user ID format: {username}")
            # Log failed login attempt
            _log_failed_login(
                username=username,
                login_type=login_type,
                client_ip=client_ip,
                reason='Invalid user ID format',
                additional_info={'error': 'Invalid user ID format'}
            )
            return Response({
                'status': 'error',
                'message': 'Invalid user ID format. Please enter a valid number.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user:
            # ========================================
            # FAILED LOGIN - INCREMENT COUNTER & CHECK LOCKOUT
            # ========================================
            failed_attempts = cache.get(user_cache_key, 0) + 1
            cache.set(user_cache_key, failed_attempts, 900)  # Keep counter for 15 minutes
            
            logger.error(f"❌ LOGIN FAILED: User authentication failed for {login_type}: {username} - Reason: Password mismatch or user not found (Attempt {failed_attempts}/5)")
            
            # Log failed login attempt
            _log_failed_login(
                username=username,
                login_type=login_type,
                client_ip=client_ip,
                reason='Invalid credentials',
                failed_attempts=failed_attempts,
                additional_info={'login_type': login_type, 'attempt_number': failed_attempts}
            )
            
            if failed_attempts >= 5:
                # Lock account for 15 minutes
                lockout_time = time.time() + 900  # 15 minutes from now
                cache.set(lockout_cache_key, lockout_time, 900)
                cache.delete(user_cache_key)  # Clear attempt counter
                
                # Log account lockout
                _log_failed_login(
                    username=username,
                    login_type=login_type,
                    client_ip=client_ip,
                    reason='Account locked - too many failed attempts',
                    failed_attempts=failed_attempts,
                    additional_info={'login_type': login_type, 'lockout_duration_minutes': 15, 'account_locked': True}
                )
                
                # Send email notification about account lockout
                # Try to find user by username/userid to get email address
                try:
                    user_for_email = None
                    if login_type == 'userid':
                        try:
                            user_id = int(username)
                            user_for_email = Users.objects.get(UserId=user_id)
                        except (ValueError, Users.DoesNotExist):
                            pass
                    else:
                        try:
                            # Handle encrypted usernames
                            user_for_email = Users.find_by_username(username)
                        except Users.DoesNotExist:
                            pass
                   
                    # Send email if user exists and has email
                    if user_for_email and user_for_email.Email:
                        _send_account_lockout_email(user_for_email.Email, user_for_email.UserName or username, client_ip)
                except Exception as email_error:
                    # Log error but don't fail the lockout process
                    logger.warning(f"Failed to send account lockout email: {str(email_error)}")
               
                
                return Response({
                    'status': 'error',
                    'message': f'Too many failed login attempts. Account locked for 15 minutes. (Attempt {failed_attempts}/5)'
                }, status=status.HTTP_403_FORBIDDEN)
            
            return Response({
                'status': 'error',
                'message': f'Invalid {login_type} or password. ({failed_attempts}/5 attempts)'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is active
        # NOTE: New users are created with IsActive='N' and must reset password and login to activate
        # We allow inactive users to login - they will be activated after successful password verification
        is_active = user.IsActive
        if isinstance(is_active, str):
            is_active = is_active.upper() == 'Y'
        elif isinstance(is_active, bool):
            is_active = is_active
        else:
            is_active = False
            
        # Store whether user was inactive (for activation after password verification)
        # Don't block login for inactive users - they need to login to be activated
        user_was_inactive = not is_active
        
        # ========================================
        # LICENSE KEY VALIDATION PROCESS - JWT LOGIN
        # ========================================
        logger.info(f"🔍 LOGIN DEBUG: User {user.UserId} passed password check, proceeding to license validation")
        if not getattr(settings, 'LICENSE_CHECK_ENABLED', True):
            logger.warning("🔕 LICENSE CHECK DISABLED via settings. Proceeding without external verification.")
        else:
            # Step 1: Check if user has a license key assigned
            license_verification_result = None
            logger.info(f"🔍 LOGIN DEBUG: License check enabled. User {user.UserId} license_key value: {user.license_key if user.license_key else 'None/Empty'}")
            if user.license_key:
                logger.info(f"🔐 LICENSE VALIDATION: User {user.UserName} has license key: {user.license_key[:10]}...")
                try:
                    # Step 2: Import and initialize the licensing system
                    from licensing_system import VardaanLicensingSystem
                    licensing_system = VardaanLicensingSystem()
                    logger.info(f"🔐 LICENSE VALIDATION: Licensing system initialized for user {user.UserName}")
                    # Step 3: Call external API to verify the license key
                    logger.info(f"🔐 LICENSE VALIDATION: Calling external API to verify license for user {user.UserName}")
                    license_verification_result = licensing_system.verify_license(user.license_key)
                    # Step 4: Check if license verification was successful
                    if not license_verification_result.get("success"):
                        logger.warning(f"❌ LICENSE VALIDATION FAILED: User {user.UserName} - {license_verification_result.get('error')}")
                        # Log failed login attempt due to license verification failure
                        _log_failed_login(
                            username=user.UserName,
                            login_type=login_type,
                            client_ip=client_ip,
                            reason='License verification failed',
                            additional_info={
                                'user_id': user.UserId,
                                'login_type': login_type,
                                'license_error': license_verification_result.get('error', 'Unknown license error')
                            }
                        )
                        return Response({
                            'status': 'error',
                            'message': 'License verification failed. Please contact your administrator.',
                            'license_error': license_verification_result.get('error', 'Unknown license error')
                        }, status=status.HTTP_403_FORBIDDEN)
                    else:
                        logger.info(f"✅ LICENSE VALIDATION SUCCESS: User {user.UserName} license verified successfully")
                except Exception as license_error:
                    logger.error(f"❌ LICENSE VALIDATION ERROR: User {user.UserName} - {str(license_error)}")
                    return Response({
                        'status': 'error',
                        'message': 'License verification error. Please contact your administrator.',
                        'license_error': str(license_error)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # Step 5: Handle case where user has no license key
                logger.warning(f"❌ LICENSE VALIDATION: User {user.UserName} has no license key assigned")
                # Log failed login attempt due to missing license key
                _log_failed_login(
                    username=user.UserName,
                    login_type=login_type,
                    client_ip=client_ip,
                    reason='No license key assigned',
                    additional_info={
                        'user_id': user.UserId,
                        'login_type': login_type,
                        'license_error': 'No license key assigned to user'
                    }
                )
                return Response({
                    'status': 'error',
                    'message': 'No license key assigned to this user. Please contact your administrator.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # ========================================
        # MFA VERIFICATION (only if MFA is enabled)
        # ========================================
        mfa_enabled = getattr(settings, 'MFA_ENABLED', True)
        
        if mfa_enabled:
            # If OTP is provided, verify it
            if otp:
                mfa_result = MfaService.verify_otp(user, otp, request)
                if not mfa_result.get('success'):
                    return Response({
                        'status': 'error',
                        'message': mfa_result.get('error', 'MFA verification failed'),
                        'requires_mfa': True
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                # No OTP provided - check if user has email for MFA
                if not user.Email:
                    return Response({
                        'status': 'error',
                        'message': 'Email address is required for MFA. Please contact your administrator.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create MFA challenge and send OTP
                try:
                    challenge = MfaService.create_mfa_challenge(user, request)
                    
                    # Mask email for privacy
                    email_parts = user.Email.split('@')
                    masked_email = f"{email_parts[0][:3]}***@{email_parts[1]}" if len(email_parts) == 2 else "***"
                    
                    return Response({
                        'status': 'mfa_required',
                        'message': f'Please enter the verification code sent to {masked_email}',
                        'requires_mfa': True,
                        'email_masked': masked_email
                    }, status=status.HTTP_200_OK)
                except Exception as mfa_error:
                    logger.error(f"Error creating MFA challenge for user {user.UserName}: {str(mfa_error)}")
                    return Response({
                        'status': 'error',
                        'message': 'Failed to send verification code. Please try again.'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # MFA is disabled - skip MFA verification and proceed with login
            logger.info(f"MFA is disabled - skipping MFA verification for user {user.UserName}")
        
        # ========================================
        # PASSWORD EXPIRY CHECK
        # ========================================
        from .routes.Global.password_expiry_utils import (
            is_password_expired,
            is_password_expiring_soon,
            send_password_expiry_email,
            log_password_action
        )
        from django.utils import timezone
        
        password_expired, days_until_expiry, days_since_change = is_password_expired(user)
        password_expiring_soon, _ = is_password_expiring_soon(user)
        
        # If password is expired, block login and force password reset
        if password_expired:
            # Send email notification about expired password
            send_password_expiry_email(user, is_expired=True, days_until_expiry=days_until_expiry)
            
            return Response({
                'status': 'error',
                'message': 'Your password has expired. Please reset your password using the "Forgot Password" option on the login page.',
                'password_expired': True,
                'days_since_expiry': abs(days_until_expiry)
            }, status=status.HTTP_403_FORBIDDEN)
        
        # If password is expiring soon, send warning email (but allow login)
        if password_expiring_soon:
            # Send warning email (only once per day to avoid spam)
            warning_cache_key = f"password_expiry_warning_sent_{user.UserId}_{timezone.now().date()}"
            if not cache.get(warning_cache_key):
                send_password_expiry_email(user, is_expired=False, days_until_expiry=days_until_expiry)
                cache.set(warning_cache_key, True, 86400)  # Cache for 24 hours
        
        # ========================================
        # SUCCESSFUL LOGIN - CLEAR FAILED ATTEMPT COUNTERS
        # ========================================
        cache.delete(user_cache_key)
        cache.delete(lockout_cache_key)
        
        # Update last login time and activate user on successful login
        from django.utils import timezone
        fields_to_update = ['last_login']
        user.last_login = timezone.now()
        
        if user.IsActive != 'Y':
            user.IsActive = 'Y'
            fields_to_update.append('IsActive')
            logger.info(f"✅ User {user.UserName} (ID: {user.UserId}) activated on first login")
        
        user.save(update_fields=fields_to_update)
        logger.info(f"✅ User {user.UserName} (ID: {user.UserId}) last login updated: {user.last_login}")
        
        # Note: Password logs are only saved when password is changed, not on every login
        # Login activities are logged to grc_logs instead
        
        # ========================================
        # MULTI-SESSION MANAGEMENT - DISABLED
        # ========================================
        # Session token validation disabled to prevent constant logouts
        # Users can now stay logged in across multiple locations
        
        # Generate JWT tokens without session token enforcement
        tokens = generate_jwt_tokens(user)
        
        # Store user info in session for compatibility with consistent naming
        # Decrypt username before storing in session
        username_plain = getattr(user, 'UserName_plain', None) or getattr(user, 'UserName', None)
        request.session['user_id'] = user.UserId
        request.session['username'] = username_plain
        request.session['grc_user_id'] = user.UserId  # Backup key for RBAC
        request.session['grc_username'] = username_plain
        request.session['session_created_at'] = time.time()  # Store session creation time for timeout check
        
        # Initialize framework session keys if needed
        if 'grc_framework_selected' not in request.session:
            request.session['grc_framework_selected'] = None
        if 'selected_framework_id' not in request.session:
            request.session['selected_framework_id'] = None
        
        # CRITICAL: Explicitly save the session to persist changes
        request.session.save()
        
        logger.info(f"✅ JWT LOGIN SUCCESS: User {user.UserName} (ID: {user.UserId}) logged in successfully with license verification")
        logger.info(f"JWT login successful for user {user.UserName} (ID: {user.UserId}) using {login_type}")
        logger.info(f"🔑 Session key created: {request.session.session_key}")
        
        # Log successful login to grc_logs - DIRECT DATABASE SAVE (fallback if send_log fails)
        log_saved = False
        try:
            from .routes.Global.logging_service import send_log
            logger.info(f"🔍 Attempting to log successful login for user {user.UserName} (ID: {user.UserId})")
            log_id = send_log(
                module='Authentication',
                actionType='LOGIN_SUCCESS',
                description=f'User {user.UserName} (ID: {user.UserId}) logged in successfully using JWT with {login_type}',
                userId=str(user.UserId),
                userName=user.UserName,
                logLevel='INFO',
                ipAddress=client_ip,
                additionalInfo={
                    'login_type': login_type,
                    'license_verified': True,
                    'mfa_enabled': mfa_enabled,
                    'user_activated': user_was_inactive,
                    'auth_method': 'JWT'
                },
                frameworkId=None  # Users model doesn't have FrameworkId field
            )
            if log_id:
                logger.info(f"✅ Successfully logged login to grc_logs with ID: {log_id}")
                log_saved = True
            else:
                logger.warning(f"⚠️  send_log returned None for user {user.UserName} - trying direct database save")
        except Exception as log_error:
            logger.error(f"❌ Error in send_log: {str(log_error)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # FALLBACK: Direct database save if send_log failed
        if not log_saved:
            try:
                logger.info(f"🔄 Attempting direct database save for login log")
                framework = _get_default_framework()
                if framework:
                    log_entry = GRCLog(
                        Module='Authentication',
                        ActionType='LOGIN_SUCCESS',
                        Description=f'User {user.UserName} (ID: {user.UserId}) logged in successfully using JWT with {login_type}',
                        UserId=str(user.UserId),
                        UserName=user.UserName,
                        LogLevel='INFO',
                        IPAddress=client_ip,
                        FrameworkId=framework,
                        AdditionalInfo={
                            'login_type': login_type,
                            'license_verified': True,
                            'mfa_enabled': mfa_enabled,
                            'user_activated': user_was_inactive,
                            'auth_method': 'JWT',
                            'logged_via': 'direct_database_save'
                        }
                    )
                    log_entry.save()
                    logger.info(f"✅ DIRECT SAVE SUCCESS: Logged login to grc_logs with ID: {log_entry.LogId}")
                else:
                    logger.error(f"❌ Cannot save login log: No framework available")
            except Exception as direct_save_error:
                logger.error(f"❌ CRITICAL: Direct database save also failed: {str(direct_save_error)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Don't fail login if logging fails
        
        # CRITICAL: Link cookie preferences to user after successful login
        # This ensures any anonymous preferences created before login are linked to the user
        try:
            from .routes.Cookie.cookie_views import link_cookie_preferences_to_user
            # Try to get session_id from request body (if provided) or cookies
            session_id = None
            if hasattr(request, 'data') and request.data:
                session_id = request.data.get('session_id')
            if not session_id and hasattr(request, 'COOKIES'):
                # Try to get from cookies if available
                session_id = request.COOKIES.get('cookie_session_id')
            
            # Link preferences (will use session_id if available, otherwise link recent ones)
            linked_count = link_cookie_preferences_to_user(user, session_id)
            if linked_count > 0:
                logger.info(f"✅ Linked {linked_count} cookie preference(s) to user {user.UserId} after login")
        except Exception as cookie_link_error:
            # Don't fail login if cookie linking fails
            logger.warning(f"⚠️  Failed to link cookie preferences after login: {str(cookie_link_error)}")
        
        # Check if user has accepted consent
        # Handle both string and potential null/None values
        consent_accepted_value = str(user.consent_accepted) if user.consent_accepted is not None else '0'
        consent_required = consent_accepted_value != '1'
        
        return Response({
            'status': 'success',
            'message': 'Login successful',
            'license_verified': True,  # This indicates license validation was successful
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'access_token_expires': tokens['access_token_expires'].isoformat(),
            'refresh_token_expires': tokens['refresh_token_expires'].isoformat(),
             'consent_required': consent_required,
             'product_version': {
                'version': tokens['access'].payload.get('ver') if hasattr(tokens['access'], 'payload') else None,
                'min_supported': tokens['access'].payload.get('min_ver') if hasattr(tokens['access'], 'payload') else None
            },
            'user': {
                'UserId': user.UserId,
                'UserName': getattr(user, 'UserName_plain', None) or getattr(user, 'UserName', None),
                'Email': getattr(user, 'email_plain', None) or getattr(user, 'Email', None),
                'FirstName': getattr(user, 'FirstName_plain', None) or getattr(user, 'FirstName', None),
                'LastName': getattr(user, 'LastName_plain', None) or getattr(user, 'LastName', None),
                'IsActive': user.IsActive,
                'consent_accepted': consent_accepted_value,
                'license_key': user.license_key  # Include the validated license 
            }
        })
        
    except Exception as e:
        logger.error(f"JWT login error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Login failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_refresh(request):
    """JWT Refresh endpoint with rate limiting"""
    try:
        # Rate limiting: Allow max 100 refresh attempts per minute per IP for production
        # High limit to avoid blocking legitimate clients with multiple tabs/windows
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        cache_key = f"jwt_refresh_rate_limit_{client_ip}"
        
        # Check rate limit
        attempts = cache.get(cache_key, 0)
        if attempts >= 100:  # Very high limit to avoid false positives
            # Silently return 429 without logging to avoid terminal spam
            return Response({
                'status': 'error',
                'message': 'Too many refresh attempts. Please wait before trying again.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Increment rate limit counter
        cache.set(cache_key, attempts + 1, 60)  # 60 seconds
        
        data = request.data
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'status': 'error',
                'message': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify refresh token
        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh['user_id']
            user = Users.objects.get(UserId=user_id)
            
            # Preserve original login_time from old token (for 5-minute timeout check)
            # If login_time doesn't exist in old token, use current time (backward compatibility)
            old_login_time = refresh.get('login_time')
            if old_login_time is None:
                import time
                old_login_time = time.time()  # Fallback for old tokens without login_time
            
            # Session token validation disabled - allow token refresh without session checking
            # old_session_token = refresh.get('jti')
            # if old_session_token:
            #     if not _is_session_token_valid(user_id, old_session_token):
            #         logger.warning(f"Session token invalid during refresh for user {user_id} - user logged in elsewhere")
            #         return Response({
            #             'status': 'error',
            #             'message': 'Session invalidated. Please log in again.'
            #         }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Generate new tokens with preserved login_time (before blacklisting old token)
            # This ensures we have valid tokens even if blacklisting fails
            tokens = generate_jwt_tokens(user, login_time=old_login_time)
            
            # IMPORTANT: Blacklist the old refresh token AFTER generating new tokens
            # This prevents token reuse while ensuring we have new tokens ready
            try:
                refresh.blacklist()
            except Exception:
                # Silently handle blacklist errors - don't log to avoid terminal spam
                # Continue even if blacklisting fails, as new tokens are already generated
                pass
            
            # No logging for successful refresh to keep terminal clean
            
            return Response({
                'status': 'success',
                'message': 'Token refreshed successfully',
                'access_token': tokens['access'],
                'refresh_token': tokens['refresh'],
                'access_token_expires': tokens['access_token_expires'].isoformat(),
                'refresh_token_expires': tokens['refresh_token_expires'].isoformat(),
                'product_version': {
                    'version': tokens['access'].payload.get('ver') if hasattr(tokens['access'], 'payload') else None,
                    'min_supported': tokens['access'].payload.get('min_ver') if hasattr(tokens['access'], 'payload') else None
                },
            })
            
        except (InvalidToken, TokenError):
            # Invalid or blacklisted refresh token - silently return 401 without logging
            return Response({
                'status': 'error',
                'message': 'Invalid refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Users.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'User not found'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f"JWT refresh error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Token refresh failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([])  # Disable authentication to allow logout with expired/invalid tokens
@permission_classes([AllowAny])  # Allow logout even without valid token to ensure logging
def jwt_logout(request):
    """JWT Logout endpoint"""
    print("=" * 80)
    print("🚪🚪🚪 JWT LOGOUT FUNCTION CALLED 🚪🚪🚪")
    print("=" * 80)
    logger.info("=" * 80)
    logger.info("🚪 JWT LOGOUT CALLED")
    logger.info("=" * 80)
    try:
        print("[DEBUG] JWT Logout: Starting logout process...")
        # Get user info before clearing session
        user_id = None
        username = 'Unknown'
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        framework_id = None
        
        logger.info(f"Initial state - IP: {client_ip}, Session keys: {list(request.session.keys())}")
        
        # Try to get user from token or session
        try:
            # Try to get user from JWT token
            auth_header = request.headers.get('Authorization')
            logger.info(f"Authorization header present: {auth_header is not None}")
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                user = get_user_from_token(token)
                if user:
                    user_id = user.UserId
                    username = user.UserName
                    framework_id = user.FrameworkId.FrameworkId if user.FrameworkId else None
                    logger.info(f"✅ Got user from token: {username} (ID: {user_id})")
        except Exception as token_error:
            logger.warning(f"Could not get user from token: {str(token_error)}")
        
        # Fallback to session if token doesn't work - CHECK ALL POSSIBLE SESSION KEYS
        if not user_id:
            logger.info("Token method failed, trying session...")
            # Try multiple session keys to find user_id
            user_id = (request.session.get('user_id') or 
                      request.session.get('grc_user_id') or
                      request.session.get('grc_username'))  # Sometimes username is stored as ID
            
            # Try to get username from multiple session keys
            username = (request.session.get('grc_username') or 
                       request.session.get('username') or 
                       'Unknown')
            
            logger.info(f"Session data - user_id: {user_id}, username: {username}")
            logger.info(f"All session keys: {list(request.session.keys())}")
            
            if user_id:
                try:
                    # If user_id is actually a username string, try to find user by username
                    if isinstance(user_id, str) and not user_id.isdigit():
                        user = Users.find_by_username(user_id)
                        if user:
                            user_id = user.UserId
                            username = user.UserName
                        else:
                            raise Users.DoesNotExist(f"User with username '{user_id}' not found")
                    else:
                        user = Users.objects.get(UserId=user_id)
                        username = user.UserName
                    
                    framework_id = user.FrameworkId.FrameworkId if user.FrameworkId else None
                    logger.info(f"✅ Got user from session: {username} (ID: {user_id})")
                except (Users.DoesNotExist, ValueError, TypeError) as e:
                    logger.warning(f"User ID {user_id} from session not found in database: {str(e)}")
                    # Try one more time with just the user_id as integer
                    try:
                        if user_id and str(user_id).isdigit():
                            user = Users.objects.get(UserId=int(user_id))
                            username = user.UserName
                            framework_id = user.FrameworkId.FrameworkId if user.FrameworkId else None
                            logger.info(f"✅ Got user after retry: {username} (ID: {user_id})")
                    except:
                        pass
        
        logger.info(f"Final user info - user_id: {user_id}, username: {username}, framework_id: {framework_id}")
        print(f"[DEBUG] Final user info - user_id: {user_id}, username: {username}, framework_id: {framework_id}")
        
        # Invalidate session token for multi-session management
        if user_id:
            try:
                _invalidate_user_session(user_id)
                logger.info(f"🔐 Session token invalidated for user {user_id} on logout")
            except Exception as session_error:
                logger.warning(f"Error invalidating session token: {str(session_error)}")
        
        # Log logout to grc_logs before clearing session - ALWAYS LOG, even if user_id is None
        log_saved = False
        logger.info("=" * 80)
        logger.info("🔍 STARTING LOGOUT LOGGING PROCESS")
        logger.info(f"User info - user_id: {user_id}, username: {username}, IP: {client_ip}")
        logger.info("=" * 80)
        print("=" * 80)
        print("🔍 STARTING LOGOUT LOGGING PROCESS")
        print(f"User info - user_id: {user_id}, username: {username}, IP: {client_ip}")
        print("=" * 80)
        
        # ALWAYS try to log, even if user_id is None
        print("[DEBUG] About to enter logging block...")
        if True:  # Changed from "if user_id:" to always log
            print("[DEBUG] Inside logging block - attempting send_log...")
            try:
                from .routes.Global.logging_service import send_log
                logger.info(f"🔍 Attempting to log logout for user {username} (ID: {user_id})")
                print(f"[DEBUG] 🔍 Attempting to log logout for user {username} (ID: {user_id})")
                log_id = send_log(
                    module='Authentication',
                    actionType='LOGOUT',
                    description=f'User {username} (ID: {user_id or "Unknown"}) logged out successfully (JWT)',
                    userId=str(user_id) if user_id else None,
                    userName=username if username != 'Unknown' else None,
                    logLevel='INFO',
                    ipAddress=client_ip,
                    additionalInfo={'auth_method': 'JWT', 'user_id_found': user_id is not None},
                    frameworkId=framework_id
                )
                print(f"[DEBUG] send_log returned: {log_id}")
                if log_id is not None:
                    logger.info(f"✅ Successfully logged logout to grc_logs with ID: {log_id}")
                    print(f"[DEBUG] ✅ Successfully logged logout to grc_logs with ID: {log_id}")
                    log_saved = True
                else:
                    logger.warning(f"⚠️  send_log returned None for logout - trying direct database save")
                    print(f"[DEBUG] ⚠️  send_log returned None for logout - trying direct database save")
            except Exception as log_error:
                logger.error(f"❌ Error in send_log for logout: {str(log_error)}")
                print(f"[DEBUG] ❌ Error in send_log for logout: {str(log_error)}")
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"Traceback: {error_trace}")
                print(f"[DEBUG] Traceback: {error_trace}")
            
            # FALLBACK: Direct database save if send_log failed
            print(f"[DEBUG] log_saved status: {log_saved}")
            if not log_saved:
                print("[DEBUG] Entering direct database save fallback...")
                try:
                    logger.info(f"🔄 Attempting direct database save for logout log")
                    print(f"[DEBUG] 🔄 Attempting direct database save for logout log")
                    framework = _get_default_framework()
                    print(f"[DEBUG] Framework retrieved: {framework}")
                    if framework:
                        print(f"[DEBUG] Framework found: ID={framework.FrameworkId}, Name={framework.FrameworkName}")
                        print(f"[DEBUG] Creating GRCLog entry with:")
                        print(f"  - Module: Authentication")
                        print(f"  - ActionType: LOGOUT")
                        print(f"  - UserId: {user_id} (type: {type(user_id)})")
                        print(f"  - UserName: {username}")
                        print(f"  - FrameworkId: {framework.FrameworkId}")
                        print(f"  - IPAddress: {client_ip}")
                        
                        log_entry = GRCLog(
                            Module='Authentication',
                            ActionType='LOGOUT',
                            Description=f'User {username} (ID: {user_id or "Unknown"}) logged out successfully (JWT)',
                            UserId=str(user_id) if user_id else None,
                            UserName=username if username != 'Unknown' else None,
                            LogLevel='INFO',
                            IPAddress=client_ip,
                            FrameworkId=framework,
                            AdditionalInfo={
                                'auth_method': 'JWT',
                                'logged_via': 'direct_database_save',
                                'user_id_found': user_id is not None
                            }
                        )
                        print(f"[DEBUG] GRCLog object created, about to save...")
                        log_entry.save()
                        print(f"[DEBUG] ✅ GRCLog.save() called successfully, LogId: {log_entry.LogId}")
                        
                        # Verify the log was saved with user_id
                        try:
                            saved_log = GRCLog.objects.get(LogId=log_entry.LogId)
                            logger.info(f"✅ DIRECT SAVE SUCCESS: Logged logout to grc_logs with ID: {log_entry.LogId}")
                            logger.info(f"✅ VERIFIED: Saved log has UserId={saved_log.UserId}, UserName={saved_log.UserName}")
                            print(f"[DEBUG] ✅ VERIFIED: Saved log has UserId={saved_log.UserId}, UserName={saved_log.UserName}")
                            log_saved = True
                            print(f"[LOGOUT LOG] ✅ Saved logout log with ID: {log_entry.LogId} for user {username} (ID: {user_id})")
                        except Exception as verify_error:
                            print(f"[DEBUG] ❌ Verification failed: {str(verify_error)}")
                            logger.error(f"❌ Verification failed: {str(verify_error)}")
                    else:
                        logger.error(f"❌ Cannot save logout log: No framework available")
                        print(f"[DEBUG] ❌ Cannot save logout log: No framework available")
                except Exception as direct_save_error:
                    logger.error(f"❌ CRITICAL: Direct database save for logout also failed: {str(direct_save_error)}")
                    print(f"[DEBUG] ❌ CRITICAL: Direct database save for logout also failed: {str(direct_save_error)}")
                    import traceback
                    error_trace = traceback.format_exc()
                    logger.error(f"Traceback: {error_trace}")
                    print(f"[DEBUG] Traceback: {error_trace}")
                    print(f"[LOGOUT LOG ERROR] {str(direct_save_error)}")
        
        print(f"[DEBUG] Final log_saved status: {log_saved}")
        if not log_saved:
            logger.error(f"❌❌❌ CRITICAL WARNING: Logout log was NOT saved to database!")
            print(f"[DEBUG] ❌❌❌ CRITICAL WARNING: Logout log was NOT saved to database!")
            print(f"[LOGOUT LOG ERROR] ❌ Failed to save logout log - check Django logs for details")
        else:
            logger.info("=" * 80)
            logger.info("✅ LOGOUT LOGGING COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            print("=" * 80)
            print("✅ LOGOUT LOGGING COMPLETED SUCCESSFULLY")
            print("=" * 80)
        
        print("[DEBUG] About to clear session data...")
        # Clear session data
        request.session.flush()
        
        logger.info(f"JWT logout successful for user {username}")
        
        return Response({
            'status': 'success',
            'message': 'Logout successful'
        })
        
    except Exception as e:
        logger.error(f"JWT logout error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])  # Allow any authenticated user
def accept_consent(request):
    """Accept user consent endpoint"""
    logger.info("=== ACCEPT CONSENT FUNCTION CALLED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    try:
        logger.info("Accept consent endpoint called")
        
        # Always get user from token since middleware is skipped for this endpoint
        auth_header = request.headers.get('Authorization')
        logger.info(f"Authorization header: {auth_header}")
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return Response({
                'status': 'error',
                'message': 'Authorization header with Bearer token is required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token = auth_header.split(' ')[1]
        logger.info(f"Extracted token: {token[:20]}...")
        user = get_user_from_token(token)
        logger.info(f"User from token: {user}")
        
        if not user:
            logger.error("User not found from token")
            return Response({
                'status': 'error',
                'message': 'Invalid or expired token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Update user consent status
        # Use raw SQL to update only consent_accepted without triggering encryption
        # This avoids "Data too long" errors for encrypted fields like FirstName
        # The EncryptedFieldsMixin doesn't respect update_fields, so we bypass it
        logger.info(f"Updating consent for user {user.UserName} from '{user.consent_accepted}' to '1'")
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET consent_accepted = %s, UpdatedAt = NOW() WHERE UserId = %s",
                    ['1', user.UserId]
                )
                logger.info(f"✅ Updated consent_accepted for user {user.UserId} using raw SQL")
        except Exception as sql_error:
            logger.error(f"❌ Error updating consent with raw SQL: {str(sql_error)}")
            # Fallback to ORM save (may fail if encrypted fields are too long)
            user.consent_accepted = '1'
            user.save(update_fields=['consent_accepted'])
        
        logger.info(f"User {user.UserName} (ID: {user.UserId}) accepted consent successfully")
        
        return Response({
            'status': 'success',
            'message': 'Consent accepted successfully',
            'user': {
                'UserId': user.UserId,
                'UserName': user.UserName,
                'Email': user.Email,
                'FirstName': user.FirstName,
                'LastName': user.LastName,
                'consent_accepted': user.consent_accepted
            }
        })
        
    except Exception as e:
        logger.error(f"Accept consent error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to accept consent'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_user_from_jwt(request):
    """Helper function to get user from JWT token in request headers"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        try:
            user = Users.objects.get(UserId=user_id)
            return user
        except Users.DoesNotExist:
            return None
            
    except Exception as e:
        logger.error(f"JWT verification error: {str(e)}")
        return None

@api_view(['GET'])
@permission_classes([AllowAny])
def jwt_verify(request):
    """JWT Verify endpoint"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({
                'status': 'error',
                'message': 'Authorization header with Bearer token is required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        
        if not payload:
            return Response({
                'status': 'error',
                'message': 'Invalid or expired token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user_id = payload.get('user_id')
        if not user_id:
            return Response({
                'status': 'error',
                'message': 'Invalid token payload'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = Users.objects.get(UserId=user_id)
            return Response({
                'status': 'success',
                'message': 'Token is valid',
                'user': {
                    'UserId': user.UserId,
                    'UserName': user.UserName,
                    'Email': user.Email,
                    'FirstName': user.FirstName,
                    'LastName': user.LastName
                }
            })
        except Users.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'User not found'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f"JWT verify error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Token verification failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def product_version_info(request):
    """Return latest and minimum supported product versions."""
    try:
        versions = _get_active_versions()
        latest = versions.get('latest_version')
        min_supported = versions.get('min_supported_version') or latest
        return Response({
            'status': 'success',
            'latest_version': latest,
            'min_supported_version': min_supported,
        })
    except Exception as e:
        logger.error(f"Product version info error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Unable to fetch product version info'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def test_token_version(request):
    """
    Helper endpoint for verifying token version handling:
    - Accepts Authorization: Bearer <access_token>
    - Decodes and returns token payload ver/min_ver
    - Compares against current DB min_supported/latest
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'status': 'error', 'message': 'Bearer token required'}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        if not payload:
            return Response({'status': 'error', 'message': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)

        token_ver = payload.get('ver')
        token_min_ver = payload.get('min_ver')

        versions = _get_active_versions()
        latest = versions.get('latest_version')
        min_supported = versions.get('min_supported_version') or latest

        comparison = None
        if token_ver and min_supported:
            comparison = _compare_versions(token_ver, min_supported)

        return Response({
            'status': 'success',
            'token_version': token_ver,
            'token_min_ver': token_min_ver,
            'current_latest': latest,
            'current_min_supported': min_supported,
            'is_supported': comparison is None or comparison >= 0
        })
    except Exception as e:
        logger.error(f"test_token_version error: {str(e)}")
        return Response({'status': 'error', 'message': 'Failed to verify token version'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_consent_auth(request):
    """Test endpoint to verify authentication for consent"""
    logger.info("=== TEST CONSENT AUTH FUNCTION CALLED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    # Get user from request (set by middleware)
    user = getattr(request, 'user', None)
    logger.info(f"User from request: {user}")
    
    if user:
        return Response({
            'status': 'success',
            'message': 'Authentication working correctly',
            'user': {
                'UserId': user.UserId,
                'UserName': user.UserName,
                'Email': user.Email
            }
        })
    else:
        return Response({
            'status': 'error',
            'message': 'No user found in request'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def test_consent_simple(request):
    """Simple test endpoint for consent without authentication"""
    logger.info("=== TEST CONSENT SIMPLE FUNCTION CALLED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    return Response({
        'status': 'success',
        'message': 'Test consent endpoint is working',
        'timestamp': datetime.now().isoformat()
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def mfa_verify_otp(request):
    """Verify MFA OTP and complete login"""
    # Check if MFA is enabled
    mfa_enabled = getattr(settings, 'MFA_ENABLED', True)
    if not mfa_enabled:
        return Response({
            'status': 'error',
            'message': 'MFA is currently disabled. Please use the regular login endpoint.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')
        otp = data.get('otp')
        login_type = data.get('login_type', 'username')
        
        if not username or not password or not otp:
            return Response({
                'status': 'error',
                'message': 'Username, password, and OTP are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user first
        user = None
        try:
            if login_type == 'userid':
                user_id = int(username)
                candidate = Users.objects.get(UserId=user_id)
            else:
                # Login with Username - handles encrypted usernames
                candidate = Users.find_by_username(username)
                if not candidate:
                    raise Users.DoesNotExist(f"User with username '{username}' not found")
            
            if check_password(password, candidate.Password):
                user = candidate
            elif candidate.Password == password:
                candidate.Password = make_password(password)
                candidate.save(update_fields=['Password'])
                user = candidate
        except Users.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except ValueError:
            return Response({
                'status': 'error',
                'message': 'Invalid user ID format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user:
            # Get client IP for logging
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            # Log failed login attempt in MFA verification
            _log_failed_login(
                username=username,
                login_type=login_type,
                client_ip=client_ip,
                reason='Invalid credentials during MFA verification',
                additional_info={'login_type': login_type, 'mfa_verification': True}
            )
            return Response({
                'status': 'error',
                'message': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is active
        # NOTE: New users are created with IsActive='N' and must reset password and login to activate
        # We allow inactive users to complete MFA - they will be activated after successful OTP verification
        is_active = user.IsActive
        if isinstance(is_active, str):
            is_active = is_active.upper() == 'Y'
        elif isinstance(is_active, bool):
            is_active = is_active
        else:
            is_active = False
        
        # Store whether user was inactive (for activation after successful OTP verification)
        user_was_inactive = not is_active
        
        # Get client IP for logging
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Verify OTP
        mfa_result = MfaService.verify_otp(user, otp, request)
        if not mfa_result.get('success'):
            # Log failed MFA verification
            _log_failed_login(
                username=user.UserName,
                login_type=login_type,
                client_ip=client_ip,
                reason='MFA OTP verification failed',
                additional_info={
                    'user_id': user.UserId,
                    'login_type': login_type,
                    'mfa_verification': True,
                    'mfa_error': mfa_result.get('error', 'Unknown MFA error')
                }
            )
            return Response({
                'status': 'error',
                'message': mfa_result.get('error', 'MFA verification failed'),
                'requires_mfa': True
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # License validation
        if not getattr(settings, 'LICENSE_CHECK_ENABLED', True):
            logger.warning("🔕 LICENSE CHECK DISABLED via settings.")
        else:
            if user.license_key:
                try:
                    from licensing_system import VardaanLicensingSystem
                    licensing_system = VardaanLicensingSystem()
                    license_verification_result = licensing_system.verify_license(user.license_key)
                    if not license_verification_result.get("success"):
                        # Log failed login attempt due to license verification failure in MFA
                        _log_failed_login(
                            username=user.UserName,
                            login_type=login_type,
                            client_ip=client_ip,
                            reason='License verification failed during MFA',
                            additional_info={
                                'user_id': user.UserId,
                                'login_type': login_type,
                                'mfa_verification': True,
                                'license_error': license_verification_result.get('error', 'Unknown license error')
                            }
                        )
                        return Response({
                            'status': 'error',
                            'message': 'License verification failed. Please contact your administrator.',
                            'license_error': license_verification_result.get('error', 'Unknown license error')
                        }, status=status.HTTP_403_FORBIDDEN)
                except Exception as license_error:
                    logger.error(f"License validation error: {str(license_error)}")
                    return Response({
                        'status': 'error',
                        'message': 'License verification error. Please contact your administrator.',
                        'license_error': str(license_error)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # Log failed login attempt due to missing license key in MFA
                _log_failed_login(
                    username=user.UserName,
                    login_type=login_type,
                    client_ip=client_ip,
                    reason='No license key assigned during MFA',
                    additional_info={
                        'user_id': user.UserId,
                        'login_type': login_type,
                        'mfa_verification': True,
                        'license_error': 'No license key assigned to user'
                    }
                )
                return Response({
                    'status': 'error',
                    'message': 'No license key assigned to this user. Please contact your administrator.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Activate user on successful MFA verification (set IsActive to 'Y')
        # This happens after OTP verification, so new users can login after resetting password
        if user.IsActive != 'Y':
            user.IsActive = 'Y'
            user.save(update_fields=['IsActive'])
            logger.info(f"✅ User {user.UserName} (ID: {user.UserId}) activated on successful MFA verification (was inactive)")
            print(f"[DEBUG] ✅ User {user.UserName} (ID: {user.UserId}) activated on successful MFA verification")
        
        # Log password usage on MFA login
        try:
            from ..models import PasswordLog
            PasswordLog.objects.create(
                UserId=user.UserId,
                UserName=user.UserName,
                OldPassword=None,  # No old password for login
                NewPassword=user.Password,  # Current hashed password
                ActionType='login',
                IPAddress=client_ip,
                UserAgent=request.META.get('HTTP_USER_AGENT', ''),
                AdditionalInfo={'login_type': login_type, 'mfa_verification': True, 'activated': user.IsActive == 'Y'}
            )
            logger.info(f"✅ Password log created for MFA login: {user.UserName}")
        except Exception as log_error:
            logger.error(f"❌ Failed to create password log on MFA login: {str(log_error)}")
            # Don't fail login if logging fails
        
        # Generate JWT tokens
        tokens = generate_jwt_tokens(user)
        
        # Store user info in session
        request.session['user_id'] = user.UserId
        request.session['username'] = user.UserName
        request.session['grc_user_id'] = user.UserId
        request.session['grc_username'] = user.UserName
        
        if 'grc_framework_selected' not in request.session:
            request.session['grc_framework_selected'] = None
        if 'selected_framework_id' not in request.session:
            request.session['selected_framework_id'] = None
        
        request.session.save()
        
        consent_accepted_value = str(user.consent_accepted) if user.consent_accepted is not None else '0'
        consent_required = consent_accepted_value != '1'
        
        logger.info(f"✅ MFA LOGIN SUCCESS: User {user.UserName} (ID: {user.UserId}) logged in successfully and activated")
        
        # Log successful MFA login to grc_logs
        try:
            from .routes.Global.logging_service import send_log
            send_log(
                module='Authentication',
                actionType='LOGIN_SUCCESS',
                description=f'User {user.UserName} (ID: {user.UserId}) logged in successfully using MFA with {login_type}',
                userId=str(user.UserId),
                userName=user.UserName,
                logLevel='INFO',
                ipAddress=client_ip,
                additionalInfo={
                    'login_type': login_type,
                    'license_verified': True,
                    'mfa_verification': True,
                    'user_activated': user_was_inactive,
                    'auth_method': 'JWT_MFA'
                },
                frameworkId=user.FrameworkId.FrameworkId if user.FrameworkId else None
            )
        except Exception as log_error:
            logger.error(f"Error logging successful MFA login to grc_logs: {str(log_error)}")
            # Don't fail login if logging fails
        
        return Response({
            'status': 'success',
            'message': 'Login successful',
            'license_verified': True,
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'access_token_expires': tokens['access_token_expires'].isoformat(),
            'refresh_token_expires': tokens['refresh_token_expires'].isoformat(),
            'consent_required': consent_required,
            'user': {
                'UserId': user.UserId,
                'UserName': user.UserName,
                'Email': user.Email,
                'FirstName': user.FirstName,
                'LastName': user.LastName,
                'IsActive': user.IsActive,
                'consent_accepted': consent_accepted_value,
                'license_key': user.license_key
            }
        })
        
    except Exception as e:
        logger.error(f"MFA verify OTP error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'MFA verification failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def mfa_resend_otp(request):
    """Resend MFA OTP to user's email"""
    # Check if MFA is enabled
    mfa_enabled = getattr(settings, 'MFA_ENABLED', True)
    if not mfa_enabled:
        return Response({
            'status': 'error',
            'message': 'MFA is currently disabled. Please use the regular login endpoint.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')
        login_type = data.get('login_type', 'username')
        
        if not username or not password:
            return Response({
                'status': 'error',
                'message': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        user = None
        try:
            if login_type == 'userid':
                user_id = int(username)
                candidate = Users.objects.get(UserId=user_id)
            else:
                # Login with Username - handles encrypted usernames
                candidate = Users.find_by_username(username)
                if not candidate:
                    raise Users.DoesNotExist(f"User with username '{username}' not found")
            
            if check_password(password, candidate.Password):
                user = candidate
            elif candidate.Password == password:
                candidate.Password = make_password(password)
                candidate.save(update_fields=['Password'])
                user = candidate
        except Users.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except ValueError:
            return Response({
                'status': 'error',
                'message': 'Invalid user ID format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user:
            return Response({
                'status': 'error',
                'message': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.Email:
            return Response({
                'status': 'error',
                'message': 'Email address is required for MFA. Please contact your administrator.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user has recent pending challenge
        from .models import MfaEmailChallenge
        recent_challenge = MfaEmailChallenge.objects.filter(
            UserId=user,
            Status=MfaEmailChallenge.STATUS_PENDING
        ).order_by('-CreatedAt').first()
        
        if recent_challenge and not recent_challenge.is_expired():
            # Rate limiting: Don't allow resend if challenge is still valid
            return Response({
                'status': 'error',
                'message': 'Please wait before requesting a new OTP. Check your email for the previous code.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Create new challenge
        try:
            challenge = MfaService.create_mfa_challenge(user, request)
            email_parts = user.Email.split('@')
            masked_email = f"{email_parts[0][:3]}***@{email_parts[1]}" if len(email_parts) == 2 else "***"
            
            return Response({
                'status': 'success',
                'message': f'New verification code sent to {masked_email}',
                'email_masked': masked_email
            }, status=status.HTTP_200_OK)
        except Exception as mfa_error:
            logger.error(f"Error resending MFA OTP for user {user.UserName}: {str(mfa_error)}")
            return Response({
                'status': 'error',
                'message': 'Failed to send verification code. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"MFA resend OTP error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to resend verification code'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def google_oauth_initiate(request):
    """Initiate Google OAuth SSO flow"""
    try:
        from google_auth_oauthlib.flow import Flow
        from google.oauth2.credentials import Credentials
        import secrets
        
        # Get Google OAuth configuration from settings
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
        client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')
        redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', '')
        scopes = getattr(settings, 'GOOGLE_SCOPES', 'openid email profile').split()
        
        if not client_id or not client_secret:
            return Response({
                'status': 'error',
                'message': 'Google OAuth is not configured. Please contact your administrator.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Use full scope URLs to match what Google returns
        # Convert short names to full URLs if needed
        full_scopes = []
        for scope in scopes:
            if scope == 'email':
                full_scopes.append('https://www.googleapis.com/auth/userinfo.email')
            elif scope == 'profile':
                full_scopes.append('https://www.googleapis.com/auth/userinfo.profile')
            elif scope == 'openid':
                full_scopes.append('openid')
            else:
                full_scopes.append(scope)
        
        # Create OAuth flow with full scope URLs
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=full_scopes,
            redirect_uri=redirect_uri
        )
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        request.session['google_oauth_state'] = state
        # CRITICAL: Save session explicitly to persist state across redirect
        request.session.save()
        
        logger.info(f"Google OAuth state saved to session: {state[:20]}...")
        
        # Get authorization URL
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'  # Force consent screen to get refresh token
        )
        
        logger.info(f"Google OAuth initiated - redirecting to: {authorization_url[:100]}...")
        
        return Response({
            'status': 'success',
            'authorization_url': authorization_url
        })
        
    except Exception as e:
        logger.error(f"Google OAuth initiate error: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to initiate Google OAuth: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def google_oauth_callback(request):
    """Handle Google OAuth callback and authenticate user"""
    try:
        from google_auth_oauthlib.flow import Flow
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from django.contrib.auth.hashers import make_password
        import secrets
        
        # Get parameters from callback
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        if error:
            logger.error(f"Google OAuth error: {error}")
            return Response({
                'status': 'error',
                'message': f'Google OAuth error: {error}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not code:
            return Response({
                'status': 'error',
                'message': 'Authorization code not provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify state to prevent CSRF attacks
        # Allow skipping in development if configured
        skip_state_verification = getattr(settings, 'SKIP_OAUTH_STATE_VERIFICATION', 'false').lower() == 'true'
        
        if not skip_state_verification:
            stored_state = request.session.get('google_oauth_state')
            logger.info(f"Google OAuth callback - received state: {state[:20] if state else 'None'}..., stored state: {stored_state[:20] if stored_state else 'None'}...")
            
            if not stored_state or stored_state != state:
                logger.warning(f"Google OAuth state mismatch - received: {state}, stored: {stored_state}")
                return Response({
                    'status': 'error',
                    'message': 'Invalid state parameter. Please try again.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Clear state from session after successful verification
            del request.session['google_oauth_state']
            request.session.save()
        else:
            logger.warning("⚠️ SKIPPING STATE VERIFICATION (development mode only)")
        
        # Get Google OAuth configuration
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
        client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')
        redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', '')
        scopes = getattr(settings, 'GOOGLE_SCOPES', 'openid email profile').split()
        
        # Use full scope URLs to match what Google returns
        # Convert short names to full URLs if needed
        full_scopes = []
        for scope in scopes:
            if scope == 'email':
                full_scopes.append('https://www.googleapis.com/auth/userinfo.email')
            elif scope == 'profile':
                full_scopes.append('https://www.googleapis.com/auth/userinfo.profile')
            elif scope == 'openid':
                full_scopes.append('openid')
            else:
                full_scopes.append(scope)
        
        # Create OAuth flow with full scope URLs
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=full_scopes,
            redirect_uri=redirect_uri
        )
        
        # Exchange authorization code for tokens
        # Handle scope format mismatch - Google returns full URLs, we may request short names
        import warnings
        
        try:
            # Suppress UserWarning about scope changes
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                flow.fetch_token(code=code)
        except (UserWarning, Warning) as e:
            # If it's a scope mismatch warning, try with scopes from callback URL
            error_str = str(e)
            if "Scope" in error_str or "scope" in error_str.lower():
                logger.warning(f"Scope format mismatch detected, using scopes from callback URL")
                # Get the actual scopes from the callback URL
                returned_scopes_str = request.GET.get('scope', '')
                if returned_scopes_str:
                    returned_scopes = returned_scopes_str.split()
                    logger.info(f"Using returned scopes: {returned_scopes}")
                    # Recreate flow with returned scopes
                    flow = Flow.from_client_config(
                        {
                            "web": {
                                "client_id": client_id,
                                "client_secret": client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": [redirect_uri]
                            }
                        },
                        scopes=returned_scopes,
                        redirect_uri=redirect_uri
                    )
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        flow.fetch_token(code=code)
                else:
                    logger.error("No scopes returned in callback URL")
                    raise Exception("Unable to retrieve scopes from Google OAuth callback")
            else:
                # Re-raise if it's not a scope-related warning
                raise
        except Exception as e:
            # Handle any other exceptions
            error_str = str(e)
            if "Scope" in error_str or "scope" in error_str.lower():
                # Try one more time with callback scopes
                returned_scopes_str = request.GET.get('scope', '')
                if returned_scopes_str:
                    returned_scopes = returned_scopes_str.split()
                    logger.info(f"Retrying with returned scopes: {returned_scopes}")
                    flow = Flow.from_client_config(
                        {
                            "web": {
                                "client_id": client_id,
                                "client_secret": client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": [redirect_uri]
                            }
                        },
                        scopes=returned_scopes,
                        redirect_uri=redirect_uri
                    )
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        flow.fetch_token(code=code)
                else:
                    raise
            else:
                raise
        credentials = flow.credentials
        
        # Get user info from Google
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        email = user_info.get('email')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        google_id = user_info.get('id')
        picture = user_info.get('picture', '')
        
        if not email:
            return Response({
                'status': 'error',
                'message': 'Unable to retrieve email from Google account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Google OAuth callback - email: {email}, google_id: {google_id}")
        
        # Check if user exists by email
        # Use filter().first() to handle cases where multiple users have the same email
        try:
            users_with_email = Users.objects.filter(Email=email)
            user_count = users_with_email.count()
            
            if user_count > 1:
                logger.warning(f"⚠️ Multiple users found with email {email} (count: {user_count}). Using the first active user.")
                # Try to get an active user first
                user = users_with_email.filter(IsActive='Y').first()
                if not user:
                    # If no active user, get the first one
                    user = users_with_email.first()
            elif user_count == 1:
                user = users_with_email.first()
            else:
                user = None
            
            if user:
                logger.info(f"Existing user found: {user.UserName} (ID: {user.UserId})")
            else:
                # No user found, will create new one
                logger.info(f"No existing user found with email {email}. Creating new user.")
        except Exception as e:
            logger.error(f"Error checking for existing user: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            user = None
        
        if not user:
            # User doesn't exist, create new user
            # Generate username from email
            username = email.split('@')[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while Users.objects.filter(UserName=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Get default framework (or handle if none exists)
            try:
                from .models import Framework
                default_framework = Framework.objects.first()
                if not default_framework:
                    return Response({
                        'status': 'error',
                        'message': 'No framework configured. Please contact your administrator.'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                logger.error(f"Error getting default framework: {str(e)}")
                return Response({
                    'status': 'error',
                    'message': 'Error configuring user. Please contact your administrator.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Create user with a random password (they'll use Google SSO)
            random_password = secrets.token_urlsafe(32)
            user = Users.objects.create(
                UserName=username,
                Email=email,
                FirstName=first_name,
                LastName=last_name,
                Password=make_password(random_password),
                IsActive='Y',
                DepartmentId='0',  # Default department
                FrameworkId=default_framework,
                consent_accepted='0'  # User will need to accept consent
            )
            logger.info(f"✅ New user created via Google SSO: {user.UserName} (ID: {user.UserId})")
            logger.info(f"   Email: {email}, Name: {first_name} {last_name}, Google ID: {google_id}")
        else:
            # Update existing user info if needed (in case Google profile changed)
            updated = False
            if user.FirstName != first_name:
                user.FirstName = first_name
                updated = True
            if user.LastName != last_name:
                user.LastName = last_name
                updated = True
            if updated:
                user.save()
                logger.info(f"✅ Updated user info via Google SSO: {user.UserName} (ID: {user.UserId})")
        
        # Check if user is active
        is_active = user.IsActive
        if isinstance(is_active, str):
            is_active = is_active.upper() == 'Y'
        elif isinstance(is_active, bool):
            is_active = is_active
        else:
            is_active = False
            
        if not is_active:
            return Response({
                'status': 'error',
                'message': 'User account is inactive. Please contact your administrator.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # License validation (same as regular login)
        if not getattr(settings, 'LICENSE_CHECK_ENABLED', True):
            logger.warning("🔕 LICENSE CHECK DISABLED via settings. Proceeding without external verification.")
        else:
            if user.license_key:
                try:
                    from licensing_system import VardaanLicensingSystem
                    licensing_system = VardaanLicensingSystem()
                    license_verification_result = licensing_system.verify_license(user.license_key)
                    if not license_verification_result.get("success"):
                        logger.warning(f"❌ LICENSE VALIDATION FAILED: User {user.UserName} - {license_verification_result.get('error')}")
                        return Response({
                            'status': 'error',
                            'message': 'License verification failed. Please contact your administrator.',
                            'license_error': license_verification_result.get('error', 'Unknown license error')
                        }, status=status.HTTP_403_FORBIDDEN)
                    else:
                        logger.info(f"✅ LICENSE VALIDATION SUCCESS: User {user.UserName} license verified successfully")
                except Exception as license_error:
                    logger.error(f"❌ LICENSE VALIDATION ERROR: User {user.UserName} - {str(license_error)}")
                    return Response({
                        'status': 'error',
                        'message': 'License verification error. Please contact your administrator.',
                        'license_error': str(license_error)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.warning(f"❌ LICENSE VALIDATION: User {user.UserName} has no license key assigned")
                return Response({
                    'status': 'error',
                    'message': 'No license key assigned to this user. Please contact your administrator.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # ========================================
        # MULTI-SESSION MANAGEMENT - DISABLED
        # ========================================
        # Session token validation disabled to prevent constant logouts
        # Users can now stay logged in across multiple locations
        
        # Generate JWT tokens without session token enforcement
        tokens = generate_jwt_tokens(user)
        
        # Store user info in session
        import time
        request.session['user_id'] = user.UserId
        request.session['username'] = user.UserName
        request.session['grc_user_id'] = user.UserId
        request.session['grc_username'] = user.UserName
        request.session['session_created_at'] = time.time()  # Store session creation time for timeout check
        
        if 'grc_framework_selected' not in request.session:
            request.session['grc_framework_selected'] = None
        if 'selected_framework_id' not in request.session:
            request.session['selected_framework_id'] = None
        
        request.session.save()
        
        consent_accepted_value = str(user.consent_accepted) if user.consent_accepted is not None else '0'
        consent_required = consent_accepted_value != '1'
        
        logger.info(f"✅ GOOGLE SSO LOGIN SUCCESS: User {user.UserName} (ID: {user.UserId}) logged in successfully")
        
        # Log successful Google SSO login to grc_logs
        try:
            from .routes.Global.logging_service import send_log
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            # Get google_id from user_info if available
            google_id_for_log = None
            try:
                if 'user_info' in locals() and user_info:
                    google_id_for_log = user_info.get('id')
            except:
                pass
            send_log(
                module='Authentication',
                actionType='LOGIN_SUCCESS',
                description=f'User {user.UserName} (ID: {user.UserId}) logged in successfully using Google SSO',
                userId=str(user.UserId),
                userName=user.UserName,
                logLevel='INFO',
                ipAddress=client_ip,
                additionalInfo={
                    'license_verified': True,
                    'auth_method': 'Google_SSO',
                    'google_id': google_id_for_log
                },
                frameworkId=user.FrameworkId.FrameworkId if user.FrameworkId else None
            )
        except Exception as log_error:
            logger.error(f"Error logging successful Google SSO login to grc_logs: {str(log_error)}")
            # Don't fail login if logging fails
        
        # Assign default RBAC permissions for Google SSO users (view permissions for all modules)
        try:
            assign_default_rbac_permissions_for_google_sso(user)
        except Exception as rbac_error:
            logger.error(f"Error assigning RBAC permissions for Google SSO user {user.UserName}: {str(rbac_error)}")
            # Continue with login even if RBAC assignment fails
        
        # Redirect to frontend with tokens as query parameters
        from django.shortcuts import redirect
        from urllib.parse import urlencode
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
        
        # Build redirect URL with all necessary parameters
        params = {
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'user_id': user.UserId,
            'consent_required': 'true' if consent_required else 'false',
            'access_token_expires': tokens['access_token_expires'].isoformat(),
            'refresh_token_expires': tokens['refresh_token_expires'].isoformat()
        }
        redirect_url = f"{frontend_url}/auth/google/callback?{urlencode(params)}"
        
        logger.info(f"Redirecting to frontend: {redirect_url[:100]}...")
        
        # Perform actual redirect
        return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'status': 'error',
            'message': f'Google OAuth callback failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)