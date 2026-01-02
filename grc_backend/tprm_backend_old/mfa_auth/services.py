import hashlib
import secrets
import string
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import User, MfaEmailChallenge, MfaAuditLog
from .jwt_service import JWTService


class MfaService:
    """Service class for handling MFA operations"""
    
    OTP_EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 3
    
    @classmethod
    def authenticate_user(cls, username, password):
        """Authenticate user with username and password"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # Fallback to the most recently updated record if duplicates exist
            user = User.objects.filter(username=username).order_by('-updated_at', '-created_at').first()
            if not user:
                return None
        # Note: In production, use proper password hashing (bcrypt, pbkdf2, etc.)
        # This is a simple comparison - replace with proper password verification
        if user.password == password and user.is_active:
            return user
        return None
    
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
            user=user,
            otp_hash=otp_hash,
            expires_at=expires_at,
            ip_address=MfaAuditLog.get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:400] if request else None
        )
        
        # Send OTP email
        cls.send_otp_email(user, otp)
        
        # Log the event
        MfaAuditLog.log_event(
            user=user,
            event_type=MfaAuditLog.EVT_ISSUED,
            detail_json={'challenge_id': challenge.challenge_id},
            request=request
        )
        
        return challenge
    
    @classmethod
    def verify_otp(cls, user, otp, request=None):
        """Verify OTP for the user"""
        try:
            # Get the latest pending challenge
            challenge = MfaEmailChallenge.objects.filter(
                user=user,
                status=MfaEmailChallenge.STATUS_PENDING
            ).order_by('-created_at').first()
            
            if not challenge:
                return {'success': False, 'error': 'No pending challenge found'}
            
            # Check if expired
            if challenge.is_expired():
                challenge.status = MfaEmailChallenge.STATUS_EXPIRED
                challenge.save()
                return {'success': False, 'error': 'OTP has expired'}
            
            # Increment attempts
            challenge.increment_attempts()
            
            # Check max attempts
            if challenge.attempts > cls.MAX_ATTEMPTS:
                challenge.mark_failed()
                MfaAuditLog.log_event(
                    user=user,
                    event_type=MfaAuditLog.EVT_FAIL,
                    detail_json={'reason': 'max_attempts_exceeded', 'attempts': challenge.attempts},
                    request=request
                )
                return {'success': False, 'error': 'Maximum attempts exceeded'}
            
            # Verify OTP
            if challenge.verify_otp(otp):
                # Mark as satisfied
                challenge.mark_satisfied()
                
                # Generate JWT tokens
                tokens = JWTService.generate_tokens(user)
                
                # Store JWT access token in session_token column
                user.session_token = tokens['access_token']
                user.save(update_fields=['session_token'])
                
                # Log success
                MfaAuditLog.log_event(
                    user=user,
                    event_type=MfaAuditLog.EVT_OK,
                    detail_json={'challenge_id': challenge.challenge_id},
                    request=request
                )
                
                return {
                    'success': True,
                    'tokens': tokens,
                    'user_id': user.userid,
                    'username': user.username
                }
            else:
                # Log failed attempt
                MfaAuditLog.log_event(
                    user=user,
                    event_type=MfaAuditLog.EVT_FAIL,
                    detail_json={'reason': 'invalid_otp', 'attempts': challenge.attempts},
                    request=request
                )
                
                remaining_attempts = cls.MAX_ATTEMPTS - challenge.attempts
                return {
                    'success': False,
                    'error': f'Invalid OTP. {remaining_attempts} attempts remaining'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Verification failed: {str(e)}'}
    
    @classmethod
    def expire_pending_challenges(cls, user):
        """Expire all pending challenges for a user"""
        MfaEmailChallenge.objects.filter(
            user=user,
            status=MfaEmailChallenge.STATUS_PENDING
        ).update(status=MfaEmailChallenge.STATUS_EXPIRED)
    
    @classmethod
    def send_otp_email(cls, user, otp):
        """Send OTP via email"""
        try:
            subject = 'Your Login Verification Code'
            
            # Try to use a template if it exists
            try:
                html_message = render_to_string('mfa_auth/otp_email.html', {
                    'user': user,
                    'otp': otp,
                    'expiry_minutes': cls.OTP_EXPIRY_MINUTES
                })
            except:
                html_message = None
            
            # Plain text message
            message = f"""
Hello {user.first_name or user.username},

Your login verification code is: {otp}

This code will expire in {cls.OTP_EXPIRY_MINUTES} minutes.

If you didn't request this code, please ignore this email.

Best regards,
Your Security Team
            """.strip()
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            return True
        except Exception as e:
            print(f"Failed to send OTP email: {e}")
            return False
    
    @classmethod
    def validate_jwt_token(cls, token):
        """Validate a JWT token and return user"""
        return JWTService.get_user_from_token(token)
    
    @classmethod
    def logout_user(cls, user):
        """Logout user by clearing session token from database"""
        user.session_token = None
        user.save(update_fields=['session_token'])
    
    @classmethod
    def get_active_sessions(cls):
        """Get all users with active sessions"""
        return User.objects.filter(
            session_token__isnull=False
        ).exclude(session_token='')
    
    @classmethod
    def force_logout_user(cls, username):
        """Force logout a specific user by username"""
        try:
            user = User.objects.get(username=username)
            user.session_token = None
            user.save(update_fields=['session_token'])
            return True
        except User.DoesNotExist:
            return False
