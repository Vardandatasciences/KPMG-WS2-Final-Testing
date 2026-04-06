"""
Test views for debugging authentication issues.

Screening data endpoints require authentication and tenant scope (VAPT / broken access control).
"""

import logging

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from tprm_backend.utils.authentication import JWTAuthentication, SimpleAuthenticatedPermission

# MULTI-TENANCY: Import tenant utilities
from tprm_backend.core.tenant_utils import get_tenant_id_from_request

from .models import ExternalScreeningResult, TempVendor

logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def test_screening_data(request):
    """Return screening data for the authenticated user's tenant only."""
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            logger.warning(
                "[test_screening_data] Rejected: no tenant context for user=%s",
                getattr(request.user, "userid", None),
            )
            return Response(
                {
                    'error': 'Tenant context required',
                    'message': 'Screening data is only available with a resolved tenant for the authenticated user.',
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        vendor_ids = TempVendor.objects.filter(tenant_id=tenant_id).values_list('id', flat=True)
        latest_result = (
            ExternalScreeningResult.objects.filter(vendor_id__in=vendor_ids)
            .order_by('-screening_id')
            .first()
        )

        if not latest_result:
            return Response(
                {
                    'status': 'success',
                    'data': [],
                    'message': 'No screening results found',
                }
            )

        vendor = latest_result.vendor
        vendor_name = vendor.company_name if vendor else f"Vendor {latest_result.vendor_id}"

        matches = latest_result.matches.all()

        frontend_data = {
            'status': 'success',
            'data': [
                {
                    'id': latest_result.screening_id,
                    'companyName': vendor_name,
                    'source': latest_result.screening_type,
                    'date': latest_result.screening_date.strftime('%Y-%m-%d'),
                    'status': latest_result.status.lower(),
                    'matchCount': latest_result.total_matches,
                    'highRiskCount': latest_result.high_risk_matches,
                    'matches': [
                        {
                            'match_id': match.match_id,
                            'match_type': match.match_type,
                            'match_score': float(match.match_score),
                            'resolution_status': match.resolution_status,
                            'match_details': match.match_details,
                        }
                        for match in matches
                    ],
                }
            ],
        }

        return Response(frontend_data)

    except Exception as e:
        logger.exception('test_screening_data failed')
        return Response(
            {'status': 'error', 'message': 'Error fetching screening data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
