"""
MFA Service for GRC Application
Handles OTP generation, email sending, and verification
"""
import hashlib
import secrets
import string
import logging
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Users, MfaEmailChallenge, MfaAuditLog

logger = logging.getLogger(__name__)


class MfaService:
    """Service class for handling MFA operations"""
    
    OTP_EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 3
    
    @classmethod
    def create_mfa_challenge(cls, user, request=None):
        """Create a new MFA challenge for the user"""
        # Expire any existing pending challenges
        cls.expire_pending_challenges(user)
        
        # Generate OTP
        otp = MfaEmailChallenge.generate_otp()
        otp_hash = MfaEmailChallenge.hash_otp(otp)
        
        # Create challenge
        expires_at = timezone.now() + timedelta(minutes=cls.OTP_EXPIRY_MINUTES)
        
        challenge = MfaEmailChallenge.objects.create(
            UserId=user,
            OtpHash=otp_hash,
            ExpiresAt=expires_at,
            IpAddress=MfaAuditLog.get_client_ip(request) if request else None,
            UserAgent=request.META.get('HTTP_USER_AGENT', '')[:400] if request else None
        )
        
        # Send OTP email
        cls.send_otp_email(user, otp)
        
        # Log the event
        MfaAuditLog.log_event(
            user=user,
            event_type=MfaAuditLog.EVT_ISSUED,
            detail_json={'challenge_id': challenge.ChallengeId},
            request=request
        )
        
        logger.info(f"MFA challenge created for user {user.UserName} (ID: {user.UserId})")
        return challenge
    
    @classmethod
    def verify_otp(cls, user, otp, request=None):
        """Verify OTP for the user"""
        try:
            # Get the latest pending challenge
            challenge = MfaEmailChallenge.objects.filter(
                UserId=user,
                Status=MfaEmailChallenge.STATUS_PENDING
            ).order_by('-CreatedAt').first()
            
            if not challenge:
                return {'success': False, 'error': 'No pending challenge found. Please request a new OTP.'}
            
            # Check if expired
            if challenge.is_expired():
                challenge.Status = MfaEmailChallenge.STATUS_EXPIRED
                challenge.save()
                return {'success': False, 'error': 'OTP has expired. Please request a new OTP.'}
            
            # Increment attempts
            challenge.increment_attempts()
            
            # Check max attempts
            if challenge.Attempts > cls.MAX_ATTEMPTS:
                challenge.mark_failed()
                MfaAuditLog.log_event(
                    user=user,
                    event_type=MfaAuditLog.EVT_FAIL,
                    detail_json={'reason': 'max_attempts_exceeded', 'attempts': challenge.Attempts},
                    request=request
                )
                return {'success': False, 'error': 'Maximum attempts exceeded. Please request a new OTP.'}
            
            # Verify OTP
            if challenge.verify_otp(otp):
                # Mark as satisfied
                challenge.mark_satisfied()
                
                # Log success
                MfaAuditLog.log_event(
                    user=user,
                    event_type=MfaAuditLog.EVT_OK,
                    detail_json={'challenge_id': challenge.ChallengeId},
                    request=request
                )
                
                logger.info(f"MFA OTP verified successfully for user {user.UserName} (ID: {user.UserId})")
                return {
                    'success': True,
                    'challenge_id': challenge.ChallengeId
                }
            else:
                # Log failed attempt
                MfaAuditLog.log_event(
                    user=user,
                    event_type=MfaAuditLog.EVT_FAIL,
                    detail_json={'reason': 'invalid_otp', 'attempts': challenge.Attempts},
                    request=request
                )
                
                remaining_attempts = cls.MAX_ATTEMPTS - challenge.Attempts
                if remaining_attempts > 0:
                    error_msg = f'Invalid OTP. {remaining_attempts} attempt(s) remaining.'
                else:
                    error_msg = 'Invalid OTP. Maximum attempts exceeded. Please request a new OTP.'
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Error verifying OTP for user {user.UserName}: {str(e)}")
            return {'success': False, 'error': f'Verification failed: {str(e)}'}
    
    @classmethod
    def expire_pending_challenges(cls, user):
        """Expire all pending challenges for a user"""
        MfaEmailChallenge.objects.filter(
            UserId=user,
            Status=MfaEmailChallenge.STATUS_PENDING
        ).update(Status=MfaEmailChallenge.STATUS_EXPIRED)
    
    @classmethod
    def send_otp_email(cls, user, otp):
        """Send OTP via email"""
        try:
            if not user.Email:
                logger.error(f"Cannot send OTP email: User {user.UserName} has no email address")
                return False
            
            subject = 'Your Login Verification Code'
            
            # Plain text message
            message = f"""
Hello {user.FirstName or user.UserName},

Your login verification code is: {otp}

This code will expire in {cls.OTP_EXPIRY_MINUTES} minutes.

If you didn't request this code, please ignore this email.

Best regards,
GRC Security Team
            """.strip()
            
            # Try to use notification service if available
            try:
                from .routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                
                expiry_time = f"{cls.OTP_EXPIRY_MINUTES} minutes"
                notification_data = {
                    'notification_type': 'mfaOTP',
                    'email': user.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        user.FirstName or user.UserName,
                        otp,
                        expiry_time,
                        'GRC System'
                    ],
                }
                
                email_result = notification_service.send_multi_channel_notification(notification_data)
                
                if email_result.get('success'):
                    method_used = email_result.get('details', {}).get('email', {}).get('method', 'unknown')
                    logger.info(f"MFA OTP email sent successfully to {user.Email} via {method_used}")
                    return True
                else:
                    logger.warning(f"Notification service failed, falling back to SMTP: {email_result.get('error', 'Unknown error')}")
            except Exception as notification_error:
                logger.warning(f"Notification service unavailable, using SMTP fallback: {str(notification_error)}")
            
            # SMTP Fallback
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@grc.com'),
                recipient_list=[user.Email],
                fail_silently=False
            )
            
            logger.info(f"MFA OTP email sent via SMTP to {user.Email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send OTP email to {user.Email}: {str(e)}")
            return False
    
    @classmethod
    def has_pending_challenge(cls, user):
        """Check if user has a valid pending challenge"""
        challenge = MfaEmailChallenge.objects.filter(
            UserId=user,
            Status=MfaEmailChallenge.STATUS_PENDING
        ).order_by('-CreatedAt').first()
        
        if challenge and not challenge.is_expired():
            return True
        return False

