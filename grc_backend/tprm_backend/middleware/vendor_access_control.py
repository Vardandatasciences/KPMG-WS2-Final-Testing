"""
Vendor Access Control Middleware - Centralized authorization with default-deny
"""

import logging
import os
from typing import Dict, List, Optional
from django.conf import settings as django_settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction

vendor_auth_logger = logging.getLogger('vendor_security')

def _get_or_create_dev_vendor_admin_user():
    """
    Development-only fallback user bootstrap made race-safe for concurrent requests.
    """
    existing_user = User.objects.filter(id=60).first()
    if existing_user:
        return existing_user

    try:
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username='GRC Administrator',
                defaults={
                    'id': 60,
                    'email': 'admin@vendor.com',
                    'first_name': 'GRC',
                    'last_name': 'Administrator',
                    'is_active': True,
                    'is_staff': True,
                },
            )
            if created:
                bootstrap_pw = os.environ.get('VENDOR_DEV_BOOTSTRAP_PASSWORD', '').strip()
                if not bootstrap_pw:
                    vendor_auth_logger.error(
                        "VENDOR_DEV_BOOTSTRAP_PASSWORD must be set to create the dev vendor admin user."
                    )
                    raise RuntimeError(
                        "VENDOR_DEV_BOOTSTRAP_PASSWORD is required when bootstrapping vendor dev admin."
                    )
                user.set_password(bootstrap_pw)
                user.save(update_fields=['password'])
            return user
    except Exception:
        return User.objects.filter(id=60).first() or User.objects.filter(username='GRC Administrator').first()


class VendorAccessControlMiddleware(MiddlewareMixin):
    """
    Centralized access control middleware with role-based permissions
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.vendor_permission_cache_timeout = 300  # 5 minutes
        self.vendor_role_permissions = self._vendor_initialize_permissions()
    
    def _vendor_initialize_permissions(self) -> Dict[str, List[str]]:
        """Initialize role-based permissions mapping"""
        return {
            'vendor_admin': [
                'vendor_user_management',
                'vendor_system_configuration',
                'vendor_backup_restore',
                'vendor_audit_logs',
                'vendor_all_vendor_access',
                'vendor_risk_assessment_all',
                'vendor_questionnaire_management',
                'vendor_dashboard_admin'
            ],
            'vendor_manager': [
                'vendor_vendor_management',
                'vendor_risk_assessment_manage',
                'vendor_questionnaire_create',
                'vendor_dashboard_view',
                'vendor_lifecycle_manage',
                'vendor_report_generation'
            ],
            'vendor_analyst': [
                'vendor_risk_assessment_view',
                'vendor_questionnaire_respond',
                'vendor_dashboard_view',
                'vendor_vendor_view',
                'vendor_screening_execute'
            ],
            'vendor_viewer': [
                'vendor_dashboard_view',
                'vendor_vendor_view',
                'vendor_report_view'
            ],
            'vendor_external': [
                'vendor_questionnaire_respond',
                'vendor_profile_update',
                'vendor_document_upload'
            ]
        }
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Enforce vendor permissions; optional dev bypass only when explicitly enabled."""

        if self._vendor_should_skip_access_control(request):
            return None

        required_permission = self._vendor_get_required_permission(request)
        dev_bypass = django_settings.DEBUG and os.environ.get(
            'VENDOR_ACCESS_CONTROL_DEV_BYPASS', ''
        ).strip().lower() in ('1', 'true', 'yes')

        if dev_bypass:
            if not getattr(request, 'user', None) or not request.user.is_authenticated:
                request.user = _get_or_create_dev_vendor_admin_user()
            vendor_auth_logger.info(
                f"Dev bypass: access granted for user {request.user.id} to {request.path}",
                extra={
                    'user_id': request.user.id,
                    'ip_address': self._vendor_get_client_ip(request),
                    'path': request.path,
                    'permission': required_permission,
                    'action': 'access_granted_dev_bypass',
                },
            )
            return None

        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return JsonResponse(
                {'detail': 'Authentication credentials were not provided.'},
                status=401,
            )

        if not self._vendor_user_has_permission(user, required_permission):
            vendor_auth_logger.warning(
                "Forbidden: user %s lacks %s for %s",
                getattr(user, 'id', None),
                required_permission,
                request.path,
            )
            return JsonResponse(
                {'detail': 'You do not have permission to perform this action.'},
                status=403,
            )

        return None
    
    def _vendor_should_skip_access_control(self, request: HttpRequest) -> bool:
        """Check if access control should be skipped for this request"""
        skip_paths = [
            '/api/v1/vendor-auth/login/',
            '/api/v1/vendor-auth/test/',
            '/api/v1/vendor-auth/check-auth/',
            '/api/v1/vendor-auth/register/',
            '/api/v1/token/',
            '/api/v1/health/',
            '/vendor-admin/login/',
            '/api/v1/vendor-core/api/v1/temp-vendors/',  # Allow vendor registration
            '/api/v1/vendor-questionnaire/',  # Temporarily allow questionnaire access for development
            '/api/v1/vendor-approval/',  # Allow approval endpoints for development
            '/api/v1/vendor-core/test/',  # Allow test endpoints for development
            '/api/v1/vendor-core/api/v1/screening-results/',  # Allow screening results for development
            '/api/v1/vendor-lifecycle/test-data/',  # Allow test data endpoint for development
            '/api/v1/vendor-lifecycle/vendors-list/',  # Allow vendors list for lifecycle tracker
            '/api/v1/vendor-lifecycle/vendor-timeline/',  # Allow vendor timeline for lifecycle tracker
            '/api/v1/vendor-lifecycle/analytics/',  # Allow analytics for lifecycle tracker
            '/api/v1/vendor-risk/',  # Allow vendor risk endpoints for development
            '/api/v1/risk-analysis/',  # Allow risk analysis endpoints for development
            '/api/v1/vendor-dashboard/',  # Allow vendor dashboard endpoints for development
            '/static/',
            '/media/',
        ]
        
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _vendor_get_required_permission(self, request: HttpRequest) -> Optional[str]:
        """Determine required permission based on endpoint and method"""
        path = request.path.lower()
        method = request.method.upper()
        
        # Vendor management endpoints
        if '/vendor-core/' in path:
            if method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                return 'vendor_vendor_management'
            else:
                return 'vendor_vendor_view'
        
        # Risk assessment endpoints
        elif '/vendor-risk/' in path:
            if method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                return 'vendor_risk_assessment_manage'
            else:
                return 'vendor_risk_assessment_view'
        
        # Questionnaire endpoints
        elif '/vendor-questionnaire/' in path:
            if method in ['POST'] and 'create' in path:
                return 'vendor_questionnaire_create'
            elif method in ['POST', 'PUT', 'PATCH'] and 'respond' in path:
                return 'vendor_questionnaire_respond'
            else:
                return 'vendor_questionnaire_view'
        
        # Dashboard endpoints
        elif '/vendor-dashboard/' in path:
            if 'admin' in path:
                return 'vendor_dashboard_admin'
            else:
                return 'vendor_dashboard_view'
        
        # Lifecycle management endpoints
        elif '/vendor-lifecycle/' in path:
            if method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                return 'vendor_lifecycle_manage'
            else:
                return 'vendor_lifecycle_view'
        
        # External screening endpoints
        elif '/vendor-screening/' in path:
            return 'vendor_screening_execute'
        
        # Default to requiring basic vendor access
        return 'vendor_basic_access'
    
    def _vendor_user_has_permission(self, user: User, permission: str) -> bool:
        """Check if user has the required permission"""
        try:
            # Check cache first
            cache_key = f"vendor_user_permissions_{user.id}"
            user_permissions = cache.get(cache_key)
            
            if user_permissions is None:
                # Get user permissions from database/profile
                user_permissions = self._vendor_get_user_permissions(user)
                cache.set(cache_key, user_permissions, self.vendor_permission_cache_timeout)
            
            return permission in user_permissions
            
        except Exception as e:
            vendor_auth_logger.error(f"Permission check failed for user {user.id}: {str(e)}")
            # Default deny on error
            return False
    
    def _vendor_get_user_permissions(self, user: User) -> List[str]:
        """Get all permissions for a user based on their roles"""
        permissions = set()
        
        try:
            # Check if user has vendor profile
            if hasattr(user, 'vendor_profile'):
                vendor_profile = user.vendor_profile
                
                # Get permissions based on user roles
                if hasattr(vendor_profile, 'vendor_roles'):
                    for role in vendor_profile.vendor_roles.all():
                        role_permissions = self.vendor_role_permissions.get(role.vendor_role_name, [])
                        permissions.update(role_permissions)
            
            # Super users get all permissions
            if user.is_superuser:
                all_permissions = set()
                for role_perms in self.vendor_role_permissions.values():
                    all_permissions.update(role_perms)
                permissions.update(all_permissions)
            
            # Staff users get admin permissions
            elif user.is_staff:
                permissions.update(self.vendor_role_permissions.get('vendor_admin', []))
            
            # Regular authenticated users get basic permissions
            else:
                permissions.update(['vendor_basic_access'])
                
        except Exception as e:
            vendor_auth_logger.error(f"Error getting user permissions: {str(e)}")
            # Default minimal permissions on error
            permissions = {'vendor_basic_access'}
        
        return list(permissions)
    
    def vendor_authorize(self, user: User, action: str, resource: str = None) -> bool:
        """
        Centralized authorization function for use in views
        """
        try:
            # Construct permission string
            permission = f"vendor_{action}"
            if resource:
                permission += f"_{resource}"
            
            return self._vendor_user_has_permission(user, permission)
            
        except Exception as e:
            vendor_auth_logger.error(f"Authorization check failed: {str(e)}")
            # Default deny on error
            return False
    
    def vendor_require_permission(self, permission: str):
        """
        Decorator for view functions to require specific permissions
        """
        def decorator(view_func):
            def wrapper(request, *args, **kwargs):
                if not self._vendor_user_has_permission(request.user, permission):
                    return JsonResponse({'error': 'Insufficient permissions'}, status=403)
                return view_func(request, *args, **kwargs)
            return wrapper
        return decorator
    
    def _vendor_get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address safely"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


# Global access control instance for use in views
# vendor_access_control = VendorAccessControlMiddleware(None)  # Will be initialized when needed
