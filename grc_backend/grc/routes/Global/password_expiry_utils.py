"""
Password Expiry Utility Functions
Handles password expiry checking, email notifications, forced password reset, and password history validation
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import check_password
from grc.models import Users, PasswordLog
import logging

logger = logging.getLogger(__name__)


def get_password_expiry_days():
    """Get password expiry days from settings"""
    return getattr(settings, 'PASSWORD_EXPIRY_DAYS', 90)


def get_password_warning_days():
    """Get password expiry warning days from settings"""
    return getattr(settings, 'PASSWORD_EXPIRY_WARNING_DAYS', 7)


def get_password_history_count():
    """Get password history count from settings (number of previous passwords to check)"""
    return getattr(settings, 'PASSWORD_HISTORY_COUNT', 5)


def get_last_password_change_date(user):
    """
    Get the last password change date for a user from PasswordLog table.
    Returns the timestamp of the most recent password change/reset/created action.
    If no password log exists, returns the user's CreatedAt date.
    """
    try:
        # Get the most recent password change/reset/created log entry
        last_password_log = PasswordLog.objects.filter(
            UserId=user.UserId,
            ActionType__in=['changed', 'reset', 'created']
        ).order_by('-Timestamp').first()
        
        if last_password_log:
            return last_password_log.Timestamp
        
        # If no password log exists, use user creation date
        return user.CreatedAt if user.CreatedAt else timezone.now()
    except Exception as e:
        logger.error(f"Error getting last password change date for user {user.UserId}: {str(e)}")
        # Fallback to user creation date
        return user.CreatedAt if user.CreatedAt else timezone.now()


def is_password_expired(user):
    """
    Check if user's password has expired.
    Returns (is_expired, days_until_expiry, days_since_change)
    """
    try:
        last_change_date = get_last_password_change_date(user)
        expiry_days = get_password_expiry_days()
        
        # Calculate days since password was last changed
        days_since_change = (timezone.now() - last_change_date).days
        
        # Check if expired
        is_expired = days_since_change >= expiry_days
        
        # Calculate days until expiry (negative if expired)
        days_until_expiry = expiry_days - days_since_change
        
        return is_expired, days_until_expiry, days_since_change
    except Exception as e:
        logger.error(f"Error checking password expiry for user {user.UserId}: {str(e)}")
        # On error, assume not expired to avoid blocking legitimate users
        return False, get_password_expiry_days(), 0


def is_password_expiring_soon(user):
    """
    Check if user's password is expiring soon (within warning days).
    Returns (is_expiring_soon, days_until_expiry)
    """
    try:
        is_expired, days_until_expiry, _ = is_password_expired(user)
        
        # If already expired, it's not "expiring soon", it's expired
        if is_expired:
            return False, days_until_expiry
        
        warning_days = get_password_warning_days()
        is_expiring_soon = 0 <= days_until_expiry <= warning_days
        
        return is_expiring_soon, days_until_expiry
    except Exception as e:
        logger.error(f"Error checking if password is expiring soon for user {user.UserId}: {str(e)}")
        return False, get_password_expiry_days()


def send_password_expiry_email(user, is_expired=False, days_until_expiry=0):
    """
    Send password expiry notification email to user.
    
    Args:
        user: Users model instance
        is_expired: Boolean indicating if password is expired
        days_until_expiry: Number of days until expiry (negative if expired)
    """
    try:
        from .notification_service import NotificationService
        
        notification_service = NotificationService()
        user_name = user.FirstName or user.UserName or user.Email.split('@')[0]
        platform_name = "GRC Platform"
        
        # Determine email template based on expiry status
        if is_expired:
            # Password has expired - send urgent reset email
            # Template expects: [user_name, days_since_expiry, platform_name]
            notification_data = {
                'notification_type': 'passwordExpired',
                'email': user.Email,
                'email_type': 'gmail',
                'template_data': [
                    user_name,
                    abs(days_until_expiry),  # Days since expiry
                    platform_name
                ],
            }
        else:
            # Password expiring soon - send warning email
            # Template expects: [user_name, days_until_expiry, platform_name]
            notification_data = {
                'notification_type': 'passwordExpiringSoon',
                'email': user.Email,
                'email_type': 'gmail',
                'template_data': [
                    user_name,
                    days_until_expiry,
                    platform_name
                ],
            }
        
        email_result = notification_service.send_multi_channel_notification(notification_data)
        
        if email_result.get('success'):
            logger.info(f"Password expiry email sent successfully to {user.Email} (Expired: {is_expired}, Days: {days_until_expiry})")
            return True
        else:
            logger.warning(f"Failed to send password expiry email to {user.Email}: {email_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending password expiry email to {user.Email}: {str(e)}")
        return False


def check_password_history(user, new_password):
    """
    Detect reuse of the user's current password only.

    Password hashes are not read from PasswordLog (audit: avoid credential material in log tables).
    For full N-password history, use a dedicated protected store — not general audit logs.

    Returns (is_reused, checked_count).
    """
    try:
        if user.Password and check_password(new_password, user.Password):
            logger.warning(
                "Password reuse detected for user %s: matches current password",
                user.UserName,
            )
            return True, 1
        logger.info("Password history check passed for user %s", user.UserName)
        return False, 0
    except Exception as e:
        logger.error(f"Error checking password history for user {user.UserId}: {str(e)}")
        return False, 0


def log_password_action(user, action_type, old_password_hash=None, new_password_hash=None, request=None):
    """
    Log password lifecycle metadata to PasswordLog (no password hashes — audit compliance).

    Args:
        user: Users model instance
        action_type: 'created', 'changed', or 'reset' (login is not logged here)
        old_password_hash: Ignored (kept for call-site compatibility)
        new_password_hash: Ignored (kept for call-site compatibility)
        request: Django request object (optional, for IP and User-Agent)
    """
    # Don't log login events to password_logs - they should go to grc_logs
    if action_type == 'login':
        logger.info(f"Skipping password log for login action - login events are logged to grc_logs")
        return
    
    try:
        client_ip = request.META.get('REMOTE_ADDR', '') if request else ''
        # Truncate IP address to max 45 characters (IPv6 max length) to prevent database error
        # Handle cases where proxy forwards multiple IPs or other unexpected data
        if client_ip:
            # Take first IP if multiple are comma-separated (proxy scenario)
            client_ip = client_ip.split(',')[0].strip()
            # Truncate to max 45 characters to fit database column
            client_ip = client_ip[:45]
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        PasswordLog.objects.create(
            UserId=user.UserId,
            UserName=user.UserName,
            OldPassword=None,
            NewPassword='',
            ActionType=action_type,
            IPAddress=client_ip,
            UserAgent=user_agent,
            AdditionalInfo={'action': action_type}
        )
        logger.info(f"Password log created for user {user.UserName}: {action_type}")
    except Exception as e:
        logger.error(f"Failed to create password log for user {user.UserName}: {str(e)}")
        # Don't fail the operation if logging fails

