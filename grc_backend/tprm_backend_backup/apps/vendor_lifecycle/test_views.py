"""
Test views for vendor lifecycle without authentication
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from .models import VendorLifecycleStages
from tprm_backend.apps.vendor_core.models import TempVendor


@api_view(['GET'])
def test_lifecycle_data(request):
    """Test endpoint to get lifecycle data without authentication"""
    try:
        # Get temp vendors with their lifecycle stage information
        temp_vendors = TempVendor.objects.all().order_by('-created_at')
        
        # Get lifecycle stages for reference
        lifecycle_stages = VendorLifecycleStages.objects.filter(is_active=True)
        stage_lookup = {stage.stage_id: stage for stage in lifecycle_stages}
        
        # Get timeline events
        timeline_events = []
        for vendor in temp_vendors[:20]:  # Limit to 20 events
            stage_info = None
            if vendor.lifecycle_stage and vendor.lifecycle_stage in stage_lookup:
                stage_info = stage_lookup[vendor.lifecycle_stage]
            
            status_mapping = {
                'active': 'completed',
                'pending': 'pending',
                'approved': 'completed',
                'rejected': 'failed',
                'in_progress': 'pending'
            }
            
            timeline_events.append({
                'id': f"vendor_{vendor.id}",
                'date': vendor.created_at.strftime('%Y-%m-%d') if vendor.created_at else 'N/A',
                'title': stage_info.stage_name if stage_info else 'Unknown Stage',
                'description': f"{vendor.company_name} - {stage_info.stage_name if stage_info else 'Unknown Stage'}",
                'status': status_mapping.get(vendor.status, 'pending'),
                'user': 'System'
            })
        
        # Get stage analytics
        stage_analytics = []
        total_vendors = temp_vendors.count()
        
        for stage in lifecycle_stages:
            vendors_in_stage = temp_vendors.filter(lifecycle_stage=stage.stage_id).count()
            percentage = (vendors_in_stage / total_vendors * 100) if total_vendors > 0 else 0
            
            stage_analytics.append({
                'stage': stage.stage_name,
                'vendors': vendors_in_stage,
                'percentage': round(percentage, 1)
            })
        
        # Get recent changes
        recent_changes = []
        recent_vendors = temp_vendors.filter(updated_at__isnull=False).order_by('-updated_at')[:10]
        
        for vendor in recent_vendors:
            if vendor.updated_at:
                time_diff = timezone.now() - vendor.updated_at
                if time_diff.days > 0:
                    time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
                else:
                    minutes = time_diff.seconds // 60
                    time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                time_ago = "Unknown"
            
            current_stage = "Unknown Stage"
            if vendor.lifecycle_stage and vendor.lifecycle_stage in stage_lookup:
                current_stage = stage_lookup[vendor.lifecycle_stage].stage_name
            
            recent_changes.append({
                'vendor': vendor.company_name,
                'from': 'Previous Stage',
                'to': current_stage,
                'date': time_ago
            })
        
        # Get vendor stages
        vendor_stages = []
        for vendor in temp_vendors:
            stage_info = None
            if vendor.lifecycle_stage and vendor.lifecycle_stage in stage_lookup:
                stage_info = stage_lookup[vendor.lifecycle_stage]
            
            vendor_stages.append({
                'vendor_id': vendor.id,
                'vendor_code': vendor.vendor_code,
                'company_name': vendor.company_name,
                'legal_name': vendor.legal_name,
                'lifecycle_stage_id': vendor.lifecycle_stage,
                'stage_name': stage_info.stage_name if stage_info else 'Unknown Stage',
                'stage_code': stage_info.stage_code if stage_info else 'UNKNOWN',
                'business_type': vendor.business_type,
                'industry_sector': vendor.industry_sector,
                'risk_level': vendor.risk_level,
                'status': vendor.status,
                'is_critical_vendor': vendor.is_critical_vendor,
                'has_data_access': vendor.has_data_access,
                'has_system_access': vendor.has_system_access,
                'created_at': vendor.created_at.strftime('%Y-%m-%d %H:%M:%S') if vendor.created_at else None,
                'updated_at': vendor.updated_at.strftime('%Y-%m-%d %H:%M:%S') if vendor.updated_at else None,
                'stage_description': stage_info.description if stage_info else None,
                'approval_required': stage_info.approval_required if stage_info else False,
                'max_duration_days': stage_info.max_duration_days if stage_info else None
            })
        
        return Response({
            'timeline_events': timeline_events,
            'stage_analytics': stage_analytics,
            'recent_changes': recent_changes,
            'vendor_stages': vendor_stages,
            'total_vendors': total_vendors
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch lifecycle data: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
