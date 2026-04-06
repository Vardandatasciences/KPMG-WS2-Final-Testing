from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from ...models import Framework, Policy
from ...rbac.permissions import PolicyViewPermission
import logging

from ...debug_utils import debug_print
from ...utils.log_sanitize import sanitize_for_log
# MULTI-TENANCY: Import tenant utilities for data isolation
from ...tenant_utils import (
    require_tenant, tenant_filter, get_tenant_id_from_request,
    validate_tenant_access, get_tenant_aware_queryset
)


logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing framework policy counts
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_framework_policy_counts(request, framework_id):
    """
    Get counts of active and inactive policies for a specific framework
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # Check if framework exists
        try:
            framework = Framework.objects.get(FrameworkId=framework_id, tenant_id=tenant_id)
        except Framework.DoesNotExist:
            return Response({
                'error': f'Framework with ID {framework_id} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get policy counts
        active_policies = Policy.objects.filter(
            tenant_id=tenant_id,
            FrameworkId=framework_id,
            ActiveInactive='Active'
        ).count()
        
        inactive_policies = Policy.objects.filter(
            tenant_id=tenant_id,
            FrameworkId=framework_id,
            ActiveInactive='Inactive'
        ).count()

        debug_print(f"DEBUG: Active policies: {active_policies}")
        debug_print(f"DEBUG: Inactive policies: {inactive_policies}")
        
        return Response({
            'framework_id': framework_id,
            'active_policies': active_policies,
            'inactive_policies': inactive_policies,
            'total_policies': active_policies + inactive_policies
        })
        
    except Exception:
        logger.exception(
            "Error getting policy counts for framework %s",
            sanitize_for_log(framework_id, 64),
        )
        return Response(
            {'error': 'Failed to get policy counts'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
