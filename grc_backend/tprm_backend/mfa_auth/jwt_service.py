import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import User


class JWTService:
    """Service class for handling JWT operations"""
    
    @classmethod
    def generate_tokens(cls, user):
        """Generate access and refresh tokens for a user"""
        now = timezone.now()
        
        # MULTI-TENANCY: Get tenant_id from user
        tenant_id = None
        if hasattr(user, 'tenant_id') and user.tenant_id:
            tenant_id = user.tenant_id
        elif hasattr(user, 'TenantId') and user.TenantId:
            tenant_id = user.TenantId
        
        # Access token payload
        access_payload = {
            'user_id': user.userid,
            'username': user.username,
            'email': user.email,
            'tenant_id': tenant_id,  # MULTI-TENANCY: Include tenant_id
            'exp': int((now + timedelta(hours=settings.JWT_EXPIRY_HOURS)).timestamp()),
            'iat': int(now.timestamp()),
            'type': 'access'
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user.userid,
            'username': user.username,
            'tenant_id': tenant_id,  # MULTI-TENANCY: Include tenant_id
            'exp': int((now + timedelta(days=settings.JWT_REFRESH_EXPIRY_DAYS)).timestamp()),
            'iat': int(now.timestamp()),
            'type': 'refresh'
        }
        
        # Generate tokens
        access_token = jwt.encode(
            access_payload, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        refresh_token = jwt.encode(
            refresh_payload, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': settings.JWT_EXPIRY_HOURS * 3600,  # seconds
            'refresh_expires_in': settings.JWT_REFRESH_EXPIRY_DAYS * 24 * 3600  # seconds
        }
    
    @classmethod
    def verify_token(cls, token, token_type='access'):
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check token type
            if payload.get('type') != token_type:
                return None
            
            # Check if token is expired
            exp_timestamp = payload.get('exp')
            if exp_timestamp:
                current_timestamp = int(timezone.now().timestamp())
                if current_timestamp > exp_timestamp:
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    @classmethod
    def get_user_from_token(cls, token):
        """Get user from access token"""
        payload = cls.verify_token(token, 'access')
        if not payload:
            return None
        
        try:
            user = User.objects.get(userid=payload['user_id'])
            if user.is_active:
                # For JWT tokens, we don't need to check session_token match
                # The JWT itself is the authentication mechanism
                return user
        except User.DoesNotExist:
            pass
        
        return None
    
    @classmethod
    def refresh_access_token(cls, refresh_token):
        """Generate new access token from refresh token"""
        payload = cls.verify_token(refresh_token, 'refresh')
        if not payload:
            return None
        
        try:
            user = User.objects.get(userid=payload['user_id'])
            if not user.is_active:
                return None
            
            # Generate new access token
            now = timezone.now()
            
            # MULTI-TENANCY: Get tenant_id from user
            tenant_id = None
            if hasattr(user, 'tenant_id') and user.tenant_id:
                tenant_id = user.tenant_id
            elif hasattr(user, 'TenantId') and user.TenantId:
                tenant_id = user.TenantId
            
            access_payload = {
                'user_id': user.userid,
                'username': user.username,
                'email': user.email,
                'tenant_id': tenant_id,  # MULTI-TENANCY: Include tenant_id
                'exp': int((now + timedelta(hours=settings.JWT_EXPIRY_HOURS)).timestamp()),
                'iat': int(now.timestamp()),
                'type': 'access'
            }
            
            new_access_token = jwt.encode(
                access_payload, 
                settings.JWT_SECRET_KEY, 
                algorithm=settings.JWT_ALGORITHM
            )
            
            return {
                'access_token': new_access_token,
                'expires_in': settings.JWT_EXPIRY_HOURS * 3600
            }
            
        except User.DoesNotExist:
            return None
