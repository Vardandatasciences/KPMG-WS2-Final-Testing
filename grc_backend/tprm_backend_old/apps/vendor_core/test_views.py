"""
Test views for debugging authentication issues
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import ExternalScreeningResult

@csrf_exempt
@require_http_methods(["GET"])
def test_screening_data(request):
    """Simple test endpoint that returns screening data without authentication"""
    try:
        # Get the latest screening result
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
