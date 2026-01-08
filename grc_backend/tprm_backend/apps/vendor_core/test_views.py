"""
Test views for debugging authentication issues
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import ExternalScreeningResult, TempVendor

# MULTI-TENANCY: Import tenant utilities
from tprm_backend.core.tenant_utils import get_tenant_id_from_request

@csrf_exempt
@require_http_methods(["GET"])
def test_screening_data(request):
    """Simple test endpoint that returns screening data without authentication
    MULTI-TENANCY: Filters by tenant when tenant context is available
    """
    try:
        # MULTI-TENANCY: Get tenant ID for filtering
        tenant_id = get_tenant_id_from_request(request)
        
        # Get the latest screening result (filtered by tenant if available)
        if tenant_id:
            # Filter by vendor's tenant
            vendor_ids = TempVendor.objects.filter(tenant_id=tenant_id).values_list('id', flat=True)
            latest_result = ExternalScreeningResult.objects.filter(vendor_id__in=vendor_ids).order_by('-screening_id').first()
        else:
            latest_result = ExternalScreeningResult.objects.order_by('-screening_id').first()
        
        if not latest_result:
            return JsonResponse({
                'status': 'success',
                'data': [],
                'message': 'No screening results found'
            })
        
        # Get the vendor information
        vendor = latest_result.vendor
        vendor_name = vendor.company_name if vendor else f"Vendor {latest_result.vendor_id}"
        
        # Get the matches
        matches = latest_result.matches.all()
        
        # Format data as the frontend expects
        frontend_data = {
            "status": "success",
            "data": [
                {
                    "id": latest_result.screening_id,
                    "companyName": vendor_name,
                    "source": latest_result.screening_type,
                    "date": latest_result.screening_date.strftime("%Y-%m-%d"),
                    "status": latest_result.status.lower(),
                    "matchCount": latest_result.total_matches,
                    "highRiskCount": latest_result.high_risk_matches,
                    "matches": [
                        {
                            "match_id": match.match_id,
                            "match_type": match.match_type,
                            "match_score": float(match.match_score),
                            "resolution_status": match.resolution_status,
                            "match_details": match.match_details
                        }
                        for match in matches
                    ]
                }
            ]
        }
        
        return JsonResponse(frontend_data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error fetching screening data: {str(e)}'
        }, status=500)
