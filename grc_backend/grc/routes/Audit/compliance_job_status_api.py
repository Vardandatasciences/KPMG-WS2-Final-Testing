"""
API Endpoints for Compliance Job Status
Allows frontend to poll for background job progress
"""
import logging
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt

from .compliance_job_tracker import ComplianceJobTracker
from ...authentication import verify_jwt_token
from ...rbac.utils import RBACUtils

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Skip CSRF check

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def get_compliance_job_status(request, job_id):
    """
    Get status of a background compliance check job
    
    Returns:
        {
            'success': True,
            'job_id': '...',
            'status': 'pending' | 'processing' | 'completed' | 'failed',
            'progress_percent': 0-100,
            'total_requirements': 100,
            'processed_requirements': 45,
            'completed_requirements': 45,
            'failed_requirements': 0,
            'results': {...} (only if completed),
            'error': '...' (only if failed)
        }
    """
    try:
        job = ComplianceJobTracker.get_job(job_id)
        
        if not job:
            return Response({
                'success': False,
                'error': f'Job {job_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        response_data = {
            'success': True,
            'job_id': job['job_id'],
            'status': job['status'],
            'progress_percent': job['progress_percent'],
            'total_requirements': job['total_requirements'],
            'processed_requirements': job['processed_requirements'],
            'completed_requirements': job['completed_requirements'],
            'failed_requirements': job['failed_requirements'],
            'started_at': job['started_at'],
            'completed_at': job.get('completed_at')
        }
        
        if job['status'] == 'completed' and job.get('results'):
            response_data['results'] = job['results']
        
        if job['status'] == 'failed' and job.get('error'):
            response_data['error'] = job['error']
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Error getting job status for {job_id}: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
