"""
System Identified Risk Queue API Views
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from ...models import SystemIdentifiedRiskQueue
from ...tenant_utils import get_tenant_id_from_request, require_tenant
from .system_risk_service import (
    generate_risk_candidates_from_incidents, 
    create_risk_from_queue_entry,
    get_queue_statistics,
    update_queue_entry_review,
    reject_queue_entry
)
import json

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_tenant
def run_incident_risk_scan(request):
    """Run AI scan on incidents to generate risk candidates."""
    tenant_id = get_tenant_id_from_request(request)
    limit = request.data.get('limit', 50)
    
    print(f"[API] run_incident_risk_scan: tenant={tenant_id}, limit={limit}")
    
    try:
        results = generate_risk_candidates_from_incidents(tenant_id, limit)
        return Response({
            'status': 'success',
            'message': f"Scan completed. Created {results['created']} new risk candidates.",
            'results': results
        })
    except Exception as e:
        print(f"[API] run_incident_risk_scan error: {e}")
        return Response({
            'status': 'error',
            'message': f'Scan failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_tenant
def list_system_risk_queue(request):
    """List system identified risks with filtering."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] list_system_risk_queue: tenant={tenant_id}")
    
    # Build query
    queryset = SystemIdentifiedRiskQueue.objects.filter(tenant_id=tenant_id)
    
    # Apply filters
    source_filter = request.GET.get('source')
    if source_filter:
        queryset = queryset.filter(source_module=source_filter)
        print(f"[API] Filtering by source: {source_filter}")
    
    status_filter = request.GET.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
        print(f"[API] Filtering by status: {status_filter}")
    
    category_filter = request.GET.get('category')
    if category_filter:
        queryset = queryset.filter(category__icontains=category_filter)
        print(f"[API] Filtering by category: {category_filter}")
    
    # Order by creation date (newest first)
    queryset = queryset.order_by('-created_at')
    
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = queryset.count()
    items = queryset[start:end]
    
    print(f"[API] Found {total_count} total items, returning page {page} ({len(items)} items)")
    
    # Serialize data
    data = []
    for item in items:
        data.append({
            'id': item.id,
            'source_module': item.source_module,
            'source_ref': item.source_ref,
            'risk_title': item.risk_title,
            'risk_type': item.risk_type,
            'category': item.category,
            'criticality': item.criticality,
            'confidence_score': item.confidence_score,
            'likelihood': item.likelihood,
            'impact': item.impact,
            'exposure_rating': item.exposure_rating,
            'priority': item.priority,
            'status': item.status,
            'created_at': item.created_at.isoformat(),
            'reviewed_at': item.reviewed_at.isoformat() if item.reviewed_at else None,
        })
    
    return Response({
        'status': 'success',
        'data': data,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': (total_count + page_size - 1) // page_size
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_tenant
def get_system_risk_detail(request, risk_id):
    """Get detailed information for a specific system risk."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] get_system_risk_detail: tenant={tenant_id}, risk_id={risk_id}")
    
    risk = get_object_or_404(SystemIdentifiedRiskQueue, 
                             id=risk_id, tenant_id=tenant_id)
    
    data = {
        'id': risk.id,
        'source_module': risk.source_module,
        'source_record_id': risk.source_record_id,
        'source_ref': risk.source_ref,
        'risk_title': risk.risk_title,
        'risk_type': risk.risk_type,
        'category': risk.category,
        'criticality': risk.criticality,
        'risk_description': risk.risk_description,
        'possible_damage': risk.possible_damage,
        'business_impact': risk.business_impact,
        'likelihood': risk.likelihood,
        'impact': risk.impact,
        'exposure_rating': risk.exposure_rating,
        'priority': risk.priority,
        'mitigation_steps': risk.mitigation_steps,
        'ai_reasoning': risk.ai_reasoning,
        'confidence_score': risk.confidence_score,
        'ai_metadata': risk.ai_metadata,
        'status': risk.status,
        'review_notes': risk.review_notes,
        'rejection_reason': risk.rejection_reason,
        'created_at': risk.created_at.isoformat(),
        'updated_at': risk.updated_at.isoformat(),
        'reviewed_at': risk.reviewed_at.isoformat() if risk.reviewed_at else None,
    }
    
    return Response({'status': 'success', 'data': data})

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@require_tenant
def update_system_risk_review(request, risk_id):
    """Update system risk with review changes (save as draft)."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] update_system_risk_review: tenant={tenant_id}, risk_id={risk_id}")
    
    risk = get_object_or_404(SystemIdentifiedRiskQueue, 
                             id=risk_id, tenant_id=tenant_id)
    
    try:
        # Update using service layer
        updated_risk = update_queue_entry_review(risk, request.data, request.user.id)
        
        return Response({
            'status': 'success',
            'message': 'Risk review saved as draft.'
        })
    except Exception as e:
        print(f"[API] update_system_risk_review error: {e}")
        return Response({
            'status': 'error',
            'message': f'Failed to update risk: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_tenant
def accept_system_risk(request, risk_id):
    """Accept a system risk and create Risk Register entry."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] accept_system_risk: tenant={tenant_id}, risk_id={risk_id}")
    
    risk = get_object_or_404(SystemIdentifiedRiskQueue, 
                             id=risk_id, tenant_id=tenant_id)
    
    try:
        # Create official risk record
        created_risk = create_risk_from_queue_entry(risk, request.user.id)
        
        return Response({
            'status': 'success',
            'message': 'Risk accepted and added to Risk Register.',
            'risk_id': created_risk.RiskId
        })
    except Exception as e:
        print(f"[API] accept_system_risk error: {e}")
        return Response({
            'status': 'error',
            'message': f'Failed to create risk: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_tenant
def reject_system_risk(request, risk_id):
    """Reject a system risk with reason."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] reject_system_risk: tenant={tenant_id}, risk_id={risk_id}")
    
    risk = get_object_or_404(SystemIdentifiedRiskQueue, 
                             id=risk_id, tenant_id=tenant_id)
    
    rejection_reason = request.data.get('reason', '')
    if not rejection_reason:
        return Response({
            'status': 'error',
            'message': 'Rejection reason is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Reject using service layer
        rejected_risk = reject_queue_entry(risk, rejection_reason, request.user.id)
        
        return Response({
            'status': 'success',
            'message': 'Risk rejected successfully.'
        })
    except Exception as e:
        print(f"[API] reject_system_risk error: {e}")
        return Response({
            'status': 'error',
            'message': f'Failed to reject risk: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_tenant
def get_queue_stats(request):
    """Get statistics for the system risk queue."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] get_queue_stats: tenant={tenant_id}")
    
    try:
        stats = get_queue_statistics(tenant_id)
        
        return Response({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        print(f"[API] get_queue_stats error: {e}")
        return Response({
            'status': 'error',
            'message': f'Failed to get statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)