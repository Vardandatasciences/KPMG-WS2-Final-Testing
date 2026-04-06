"""
RBAC Views for GRC System

This module provides views for RBAC functionality including user permissions.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect as csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..jwt_auth import UnifiedJWTAuthentication
from .utils import RBACUtils

logger = logging.getLogger(__name__)


def _authenticated_grc_user_id(request):
    """Resolve GRC user id from DRF-authenticated request.user."""
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    uid = getattr(user, 'pk', None)
    if uid is not None:
        return uid
    uid = getattr(user, 'id', None)
    if uid is not None:
        return uid
    return getattr(user, 'userid', None)


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_permissions(request):
    """
    Get user permissions for frontend RBAC service
    
    Returns:
        JSON response with user permissions organized by module
    """
    try:
        user_id = _authenticated_grc_user_id(request)
        if not user_id:
            return Response(
                {
                    'error': 'Authentication required',
                    'message': 'Valid JWT authentication required',
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        permissions_summary = RBACUtils.get_user_permissions_summary(user_id)

        if not permissions_summary:
            return Response(
                {
                    'error': 'User not found',
                    'message': 'User not found in RBAC system',
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Organize permissions by module
        organized_permissions = {
            'policy': {},
            'compliance': {},
            'audit': {},
            'risk': {},
            'incident': {}
        }
        
        # Map permissions to modules
        permission_mapping = {
            # Policy permissions
            'view_all_policy': 'policy',
            'create_policy': 'policy',
            'edit_policy': 'policy',
            'approve_policy': 'policy',
            'delete_policy': 'policy',
            'assign_policy': 'policy',
            'policy_performance_analytics': 'policy',
            
            # Compliance permissions
            'view_all_compliance': 'compliance',
            'create_compliance': 'compliance',
            'edit_compliance': 'compliance',
            'approve_compliance': 'compliance',
            'delete_compliance': 'compliance',
            'compliance_performance_analytics': 'compliance',
            
            # Audit permissions
            'view_audit_reports': 'audit',
            'conduct_audit': 'audit',
            'review_audit': 'audit',
            'assign_audit': 'audit',
            'audit_performance_analytics': 'audit',
            
            # Risk permissions
            'view_all_risk': 'risk',
            'create_risk': 'risk',
            'edit_risk': 'risk',
            'approve_risk': 'risk',
            'delete_risk': 'risk',
            'risk_performance_analytics': 'risk',
            
            # Incident permissions
            'view_all_incident': 'incident',
            'create_incident': 'incident',
            'edit_incident': 'incident',
            'approve_incident': 'incident',
            'delete_incident': 'incident',
            'incident_performance_analytics': 'incident'
        }
        
        # Process permissions from the summary
        permissions_data = permissions_summary.get('permissions', {})
        
        # Process each module's permissions directly
        for module_name, module_permissions in permissions_data.items():
            if module_name in organized_permissions:
                for field_name, has_permission in module_permissions.items():
                    # Map field names to frontend permission names based on module
                    if module_name == 'policy':
                        if field_name == 'create':
                            permission_name = 'create_policy'
                        elif field_name == 'view_all':
                            permission_name = 'view_all_policy'
                        elif field_name == 'edit':
                            permission_name = 'edit_policy'
                        elif field_name == 'approve':
                            permission_name = 'approve_policy'
                        elif field_name == 'analytics':
                            permission_name = 'policy_performance_analytics'
                        elif field_name == 'create_framework':
                            permission_name = 'create_framework'
                        elif field_name == 'approve_framework':
                            permission_name = 'approve_framework'
                        else:
                            continue
                    elif module_name == 'compliance':
                        if field_name == 'create':
                            permission_name = 'create_compliance'
                        elif field_name == 'view_all':
                            permission_name = 'view_all_compliance'
                        elif field_name == 'edit':
                            permission_name = 'edit_compliance'
                        elif field_name == 'approve':
                            permission_name = 'approve_compliance'
                        elif field_name == 'analytics':
                            permission_name = 'compliance_performance_analytics'
                        else:
                            continue
                    elif module_name == 'audit':
                        if field_name == 'assign':
                            permission_name = 'assign_audit'
                        elif field_name == 'conduct':
                            permission_name = 'conduct_audit'
                        elif field_name == 'review':
                            permission_name = 'review_audit'
                        elif field_name == 'view_reports':
                            permission_name = 'view_audit_reports'
                        elif field_name == 'analytics':
                            permission_name = 'audit_performance_analytics'
                        else:
                            continue
                    elif module_name == 'risk':
                        if field_name == 'create':
                            permission_name = 'create_risk'
                        elif field_name == 'view_all':
                            permission_name = 'view_all_risk'
                        elif field_name == 'edit':
                            permission_name = 'edit_risk'
                        elif field_name == 'approve':
                            permission_name = 'approve_risk'
                        elif field_name == 'assign':
                            permission_name = 'assign_risk'
                        elif field_name == 'evaluate':
                            permission_name = 'evaluate_assigned_risk'
                        elif field_name == 'analytics':
                            permission_name = 'risk_performance_analytics'
                        else:
                            continue
                    elif module_name == 'incident':
                        if field_name == 'create':
                            permission_name = 'create_incident'
                        elif field_name == 'view_all':
                            permission_name = 'view_all_incident'
                        elif field_name == 'edit':
                            permission_name = 'edit_incident'
                        elif field_name == 'assign':
                            permission_name = 'assign_incident'
                        elif field_name == 'evaluate':
                            permission_name = 'evaluate_assigned_incident'
                        elif field_name == 'escalate':
                            permission_name = 'escalate_to_risk'
                        elif field_name == 'analytics':
                            permission_name = 'incident_performance_analytics'
                        else:
                            continue
                    else:
                        continue
                    
                    organized_permissions[module_name][permission_name] = has_permission
        

        
        # Add user info
        response_data = {
            'user_id': user_id,
            'username': permissions_summary.get('username'),
            'role': permissions_summary.get('role'),
            'permissions': organized_permissions,
            'is_admin': permissions_summary.get('is_admin', False)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception:
        logger.exception('[RBAC VIEWS] Error getting user permissions')
        return Response(
            {
                'error': 'Internal server error',
                'message': 'Error retrieving user permissions',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET', 'POST'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([IsAuthenticated])
def check_permission(request):
    """
    Check if user has a specific permission
    
    Supports both GET (query parameters) and POST (JSON body):
        module: Module name (e.g., 'policy', 'compliance')
        permission: Permission name (e.g., 'create_policy', 'view_all_policy')
    """
    try:
        user_id = _authenticated_grc_user_id(request)
        if not user_id:
            return Response(
                {
                    'error': 'Authentication required',
                    'message': 'Valid JWT authentication required',
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        module = None
        permission = None

        logger.debug('[RBAC CHECK] method=%s path=%s', request.method, request.path)

        if request.method == 'GET':
            module = request.GET.get('module')
            permission = request.GET.get('permission')
        elif request.method == 'POST':
            try:
                body_data = json.loads(request.body)
                module = body_data.get('module')
                permission = body_data.get('permission')
            except (json.JSONDecodeError, AttributeError):
                module = request.POST.get('module')
                permission = request.POST.get('permission')

        if not module or not permission:
            return Response(
                {
                    'error': 'Missing parameters',
                    'message': 'Both module and permission parameters are required',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        has_permission = RBACUtils.has_permission(user_id, module, permission)

        return Response(
            {
                'user_id': user_id,
                'module': module,
                'permission': permission,
                'has_permission': has_permission,
            },
            status=status.HTTP_200_OK,
        )

    except Exception:
        logger.exception('[RBAC VIEWS] Error checking permission')
        return Response(
            {
                'error': 'Internal server error',
                'message': 'Error checking permission',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
