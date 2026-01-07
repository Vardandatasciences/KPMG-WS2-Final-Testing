"""
Vendor Lifecycle Tracker Views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    VendorApprovals, 
    VendorStatusHistory, 
    VendorLifecycleStages,
    VendorContracts,
    VendorSlas
)
from tprm_backend.apps.vendor_core.models import Vendors, Users, TempVendor, LifecycleTracker
from tprm_backend.apps.vendor_risk.models import VendorRiskAssessments
from tprm_backend.apps.vendor_approval.models import ApprovalRequests, ApprovalStages

# RBAC imports
from tprm_backend.rbac.tprm_decorators import rbac_vendor_required
from tprm_backend.apps.vendor_core.vendor_authentication import JWTAuthentication, SimpleAuthenticatedPermission

# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    filter_queryset_by_tenant,
    get_tenant_aware_queryset,
    require_tenant,
    tenant_filter
)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('ViewLifecycleHistory')
@require_tenant
@tenant_filter
def lifecycle_tracker_data(request):
    """
    Get comprehensive lifecycle tracker data including:
    - Timeline events for a specific vendor
    - Stage analytics
    - Recent status changes
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

        vendor_id = request.GET.get('vendor_id')
        search_term = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        stage_filter = request.GET.get('stage', '')
        
        # Get timeline events - pass tenant_id for filtering
        timeline_events = get_timeline_events(vendor_id, search_term, status_filter, stage_filter, tenant_id)
        
        # Get stage analytics - pass tenant_id for filtering
        stage_analytics = get_stage_analytics(tenant_id)
        
        # Get recent status changes - pass tenant_id for filtering
        recent_changes = get_recent_status_changes(tenant_id)
        
        # Get vendor stages from temp_vendor table - pass tenant_id for filtering
        vendor_stages = get_vendor_stages_from_temp_table(tenant_id)
        
        return Response({
            'timeline_events': timeline_events,
            'stage_analytics': stage_analytics,
            'recent_changes': recent_changes,
            'vendor_stages': vendor_stages
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch lifecycle data: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_timeline_events(vendor_id=None, search_term='', status_filter='', stage_filter='', tenant_id=None):
    """Get timeline events for vendors from temp_vendor table
    MULTI-TENANCY: Filters by tenant_id
    """
    events = []
    
    try:
        # Get temp vendors with their lifecycle stage information
        # MULTI-TENANCY: Filter by tenant
        if tenant_id:
            temp_vendors_query = TempVendor.objects.filter(tenant_id=tenant_id).order_by('-created_at')
        else:
            temp_vendors_query = TempVendor.objects.all().order_by('-created_at')
        
        if vendor_id:
            temp_vendors_query = temp_vendors_query.filter(id=vendor_id)
        
        if search_term:
            temp_vendors_query = temp_vendors_query.filter(
                Q(company_name__icontains=search_term) |
                Q(vendor_code__icontains=search_term)
            )
        
        if status_filter:
            temp_vendors_query = temp_vendors_query.filter(status__icontains=status_filter)
        
        # Get lifecycle stages for reference
        lifecycle_stages = VendorLifecycleStages.objects.filter(is_active=True)
        stage_lookup = {stage.stage_id: stage for stage in lifecycle_stages}
        
        for vendor in temp_vendors_query[:20]:  # Limit to 20 events
            # Get stage information
            stage_info = None
            if vendor.lifecycle_stage and vendor.lifecycle_stage in stage_lookup:
                stage_info = stage_lookup[vendor.lifecycle_stage]
            
            # Determine status based on vendor status
            status_mapping = {
                'active': 'completed',
                'pending': 'pending',
                'approved': 'completed',
                'rejected': 'failed',
                'in_progress': 'pending'
            }
            
            events.append({
                'id': f"temp_vendor_{vendor.id}",
                'date': vendor.created_at.strftime('%Y-%m-%d') if vendor.created_at else 'N/A',
                'title': stage_info.stage_name if stage_info else 'Unknown Stage',
                'description': f"{vendor.company_name} - {stage_info.stage_name if stage_info else 'Unknown Stage'}",
                'status': status_mapping.get(vendor.status, 'pending'),
                'user': 'System'  # Temp vendors are typically system-created
            })
            
    except Exception as e:
        print(f"Error fetching timeline events: {e}")
        # Return empty list if there's an error
        return []
    
    # Sort events by date (newest first)
    events.sort(key=lambda x: x['date'], reverse=True)
    
    return events


def get_stage_analytics(tenant_id=None):
    """Get analytics for each lifecycle stage from temp_vendor table
    MULTI-TENANCY: Filters by tenant_id
    """
    analytics = []
    
    try:
        # Get all lifecycle stages
        stages = VendorLifecycleStages.objects.filter(is_active=True).order_by('stage_order')
        
        # Get total vendor count from temp_vendor table
        # MULTI-TENANCY: Filter by tenant
        if tenant_id:
            total_vendors = TempVendor.objects.filter(tenant_id=tenant_id).count()
        else:
            total_vendors = TempVendor.objects.count()
        
        for stage in stages:
            # Count vendors in this stage from temp_vendor table
            # MULTI-TENANCY: Filter by tenant
            if tenant_id:
                vendors_in_stage = TempVendor.objects.filter(lifecycle_stage=stage.stage_id, tenant_id=tenant_id).count()
            else:
                vendors_in_stage = TempVendor.objects.filter(lifecycle_stage=stage.stage_id).count()
            
            # Calculate percentage
            percentage = (vendors_in_stage / total_vendors * 100) if total_vendors > 0 else 0
            
            analytics.append({
                'stage': stage.stage_name,
                'vendors': vendors_in_stage,
                'percentage': round(percentage, 1)
            })
            
    except Exception as e:
        print(f"Error fetching stage analytics: {e}")
        # Return empty list if there's an error
        return []
    
    return analytics


def get_recent_status_changes(tenant_id=None):
    """Get recent status changes from temp_vendor table
    MULTI-TENANCY: Filters by tenant_id
    """
    recent_changes = []
    
    try:
        # Get recent temp vendors ordered by updated_at
        # MULTI-TENANCY: Filter by tenant
        if tenant_id:
            temp_vendors = TempVendor.objects.filter(
                updated_at__isnull=False,
                tenant_id=tenant_id
            ).order_by('-updated_at')[:10]
        else:
            temp_vendors = TempVendor.objects.filter(
                updated_at__isnull=False
            ).order_by('-updated_at')[:10]
        
        # Get lifecycle stages for reference
        lifecycle_stages = VendorLifecycleStages.objects.filter(is_active=True)
        stage_lookup = {stage.stage_id: stage for stage in lifecycle_stages}
        
        for vendor in temp_vendors:
            # Calculate time ago
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
            
            # Get current stage name
            current_stage = "Unknown Stage"
            if vendor.lifecycle_stage and vendor.lifecycle_stage in stage_lookup:
                current_stage = stage_lookup[vendor.lifecycle_stage].stage_name
            
            recent_changes.append({
                'vendor': vendor.company_name,
                'from': 'Previous Stage',  # We don't have historical data in temp_vendor
                'to': current_stage,
                'date': time_ago
            })
            
    except Exception as e:
        print(f"Error fetching recent status changes: {e}")
        # Return empty list if there's an error
        return []
    
    return recent_changes


def get_vendor_stages_from_temp_table(tenant_id=None):
    """Get vendor stages from temp_vendor table with stage information
    MULTI-TENANCY: Filters by tenant_id
    """
    vendor_stages = []
    
    try:
        # Get all temp vendors with their lifecycle stage information
        # MULTI-TENANCY: Filter by tenant
        if tenant_id:
            temp_vendors = TempVendor.objects.filter(tenant_id=tenant_id).order_by('-created_at')
        else:
            temp_vendors = TempVendor.objects.all().order_by('-created_at')
        
        # Get lifecycle stages for reference
        lifecycle_stages = VendorLifecycleStages.objects.filter(is_active=True).order_by('stage_order')
        stage_lookup = {stage.stage_id: stage for stage in lifecycle_stages}
        
        for vendor in temp_vendors:
            # Get stage information
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
            
    except Exception as e:
        print(f"Error fetching vendor stages from temp table: {e}")
        # Return empty list if there's an error
        return []
    
    return vendor_stages


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('ViewLifecycleHistory')
@require_tenant
@tenant_filter
def vendor_lifecycle_stages(request):
    """Get all lifecycle stages
    MULTI-TENANCY: Lifecycle stages may be shared across tenants
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

        stages = VendorLifecycleStages.objects.filter(is_active=True).order_by('stage_order')
        
        stage_data = []
        for stage in stages:
            stage_data.append({
                'stage_id': stage.stage_id,
                'stage_name': stage.stage_name,
                'stage_code': stage.stage_code,
                'stage_order': stage.stage_order,
                'description': stage.description,
                'approval_required': stage.approval_required,
                'max_duration_days': stage.max_duration_days
            })
        
        return Response({'stages': stage_data})
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch lifecycle stages: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('ViewLifecycleHistory')
@require_tenant
@tenant_filter
def vendor_timeline(request, vendor_id):
    """Get timeline for a specific vendor
    MULTI-TENANCY: Ensures vendor belongs to tenant
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

        # MULTI-TENANCY: Filter by tenant
        vendor = Vendors.objects.get(vendor_id=vendor_id, tenant_id=tenant_id)
        
        # Get all timeline events for this vendor
        timeline_events = get_timeline_events(vendor_id=vendor_id)
        
        # Get vendor details
        vendor_data = {
            'vendor_id': vendor.vendor_id,
            'company_name': vendor.company_name,
            'status': vendor.status,
            'lifecycle_stage': vendor.lifecycle_stage,
            'onboarding_date': vendor.onboarding_date,
            'last_assessment_date': vendor.last_assessment_date
        }
        
        return Response({
            'vendor': vendor_data,
            'timeline_events': timeline_events
        })
        
    except Vendors.DoesNotExist:
        return Response(
            {'error': 'Vendor not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch vendor timeline: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('ViewLifecycleHistory')
@require_tenant
@tenant_filter
def temp_vendor_stages(request):
    """Get vendor stages from temp_vendor table
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

        vendor_stages = get_vendor_stages_from_temp_table(tenant_id)
        
        return Response({
            'vendor_stages': vendor_stages,
            'total_count': len(vendor_stages)
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch vendor stages: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('update_vendor')
@require_tenant
@tenant_filter
def update_vendor_stage(request):
    """Update vendor lifecycle stage
    MULTI-TENANCY: Ensures vendor belongs to tenant
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

        vendor_id = request.data.get('vendor_id')
        new_stage = request.data.get('new_stage')
        change_reason = request.data.get('change_reason', '')
        comments = request.data.get('comments', '')
        
        if not vendor_id or not new_stage:
            return Response(
                {'error': 'vendor_id and new_stage are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # MULTI-TENANCY: Filter by tenant
        vendor = Vendors.objects.get(vendor_id=vendor_id, tenant_id=tenant_id)
        old_stage = vendor.lifecycle_stage
        
        # Update vendor stage
        vendor.lifecycle_stage = new_stage
        vendor.save()
        
        # Create status history entry
        VendorStatusHistory.objects.create(
            vendor=vendor,
            old_stage=old_stage,
            new_stage=new_stage,
            changed_by=request.user,
            change_reason=change_reason,
            comments=comments,
            change_date=timezone.now()
        )
        
        return Response({
            'message': 'Vendor stage updated successfully',
            'vendor_id': vendor_id,
            'old_stage': old_stage,
            'new_stage': new_stage
        })
        
    except Vendors.DoesNotExist:
        return Response(
            {'error': 'Vendor not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to update vendor stage: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('ViewLifecycleHistory')
@require_tenant
@tenant_filter
def get_vendors_list(request):
    """Get list of all vendors for dropdown filtering
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

        # Get all temp vendors for dropdown
        # MULTI-TENANCY: Filter by tenant
        temp_vendors = TempVendor.objects.filter(tenant_id=tenant_id).order_by('company_name')
        
        vendors_list = []
        for vendor in temp_vendors:
            vendors_list.append({
                'vendor_id': vendor.id,
                'vendor_code': vendor.vendor_code,
                'company_name': vendor.company_name,
                'legal_name': vendor.legal_name,
                'status': vendor.status,
                'lifecycle_stage_id': vendor.lifecycle_stage
            })
        
        return Response({
            'vendors': vendors_list,
            'total_count': len(vendors_list)
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch vendors list: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('ViewLifecycleHistory')
@require_tenant
@tenant_filter
def get_vendor_lifecycle_timeline(request, vendor_id):
    """Get detailed lifecycle timeline for a specific vendor from lifecycle_tracker
    MULTI-TENANCY: Ensures vendor belongs to tenant
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

        # Get vendor details
        # MULTI-TENANCY: Filter by tenant
        vendor = TempVendor.objects.get(id=vendor_id, tenant_id=tenant_id)
        
        # Get lifecycle tracker entries for this vendor
        lifecycle_entries = LifecycleTracker.objects.filter(
            vendor_id=vendor_id
        ).order_by('started_at')
        
        # Get all lifecycle stages for reference
        lifecycle_stages = VendorLifecycleStages.objects.filter(is_active=True)
        stage_lookup = {stage.stage_id: stage for stage in lifecycle_stages}
        
        timeline_data = []
        for entry in lifecycle_entries:
            stage_info = stage_lookup.get(entry.lifecycle_stage)
            
            # Calculate duration if ended
            duration = None
            if entry.ended_at and entry.started_at:
                duration_delta = entry.ended_at - entry.started_at
                duration = {
                    'days': duration_delta.days,
                    'total_hours': duration_delta.total_seconds() / 3600,
                    'display': f"{duration_delta.days} days, {duration_delta.seconds // 3600} hours"
                }
            
            # Determine status
            status = 'completed' if entry.ended_at else 'in_progress'
            
            timeline_data.append({
                'tracker_id': entry.id,
                'stage_id': entry.lifecycle_stage,
                'stage_name': stage_info.stage_name if stage_info else 'Unknown Stage',
                'stage_code': stage_info.stage_code if stage_info else 'UNKNOWN',
                'stage_description': stage_info.description if stage_info else None,
                'stage_order': stage_info.stage_order if stage_info else 0,
                'started_at': entry.started_at.isoformat() if entry.started_at else None,
                'ended_at': entry.ended_at.isoformat() if entry.ended_at else None,
                'duration': duration,
                'status': status,
                'approval_required': stage_info.approval_required if stage_info else False,
                'max_duration_days': stage_info.max_duration_days if stage_info else None
            })
        
        # Calculate overall progress
        total_stages = VendorLifecycleStages.objects.filter(is_active=True).count()
        completed_stages = len([entry for entry in timeline_data if entry['status'] == 'completed'])
        progress_percentage = (completed_stages / total_stages * 100) if total_stages > 0 else 0
        
        vendor_data = {
            'vendor_id': vendor.id,
            'vendor_code': vendor.vendor_code,
            'company_name': vendor.company_name,
            'legal_name': vendor.legal_name,
            'business_type': vendor.business_type,
            'industry_sector': vendor.industry_sector,
            'risk_level': vendor.risk_level,
            'status': vendor.status,
            'current_lifecycle_stage': vendor.lifecycle_stage,
            'is_critical_vendor': vendor.is_critical_vendor,
            'has_data_access': vendor.has_data_access,
            'has_system_access': vendor.has_system_access,
            'created_at': vendor.created_at.isoformat() if vendor.created_at else None,
            'updated_at': vendor.updated_at.isoformat() if vendor.updated_at else None,
            'progress_percentage': round(progress_percentage, 1),
            'completed_stages': completed_stages,
            'total_stages': total_stages
        }
        
        return Response({
            'vendor': vendor_data,
            'timeline': timeline_data,
            'summary': {
                'total_stages': total_stages,
                'completed_stages': completed_stages,
                'current_stage': timeline_data[-1] if timeline_data else None,
                'progress_percentage': round(progress_percentage, 1)
            }
        })
        
    except TempVendor.DoesNotExist:
        return Response(
            {'error': 'Vendor not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch vendor lifecycle timeline: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('ViewLifecycleHistory')
@require_tenant
@tenant_filter
def get_lifecycle_analytics(request):
    """Get comprehensive lifecycle analytics
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

        # Get stage analytics from lifecycle_tracker
        stage_analytics = []
        stages = VendorLifecycleStages.objects.filter(is_active=True).order_by('stage_order')
        
        for stage in stages:
            # Count vendors currently in this stage
            # MULTI-TENANCY: Filter by tenant
            current_in_stage = TempVendor.objects.filter(lifecycle_stage=stage.stage_id, tenant_id=tenant_id).count()
            
            # Count vendors who have completed this stage
            # MULTI-TENANCY: Filter by tenant through vendor
            vendor_ids = TempVendor.objects.filter(tenant_id=tenant_id).values_list('id', flat=True)
            completed_stage = LifecycleTracker.objects.filter(
                lifecycle_stage=stage.stage_id,
                ended_at__isnull=False,
                vendor_id__in=vendor_ids
            ).count()
            
            # Count vendors currently active in this stage
            active_in_stage = LifecycleTracker.objects.filter(
                lifecycle_stage=stage.stage_id,
                ended_at__isnull=True,
                vendor_id__in=vendor_ids
            ).count()
            
            # Calculate average duration for completed stages
            completed_entries = LifecycleTracker.objects.filter(
                lifecycle_stage=stage.stage_id,
                ended_at__isnull=False,
                started_at__isnull=False,
                vendor_id__in=vendor_ids
            )
            
            avg_duration_hours = 0
            if completed_entries.exists():
                total_duration = sum([
                    (entry.ended_at - entry.started_at).total_seconds() / 3600 
                    for entry in completed_entries
                ])
                avg_duration_hours = total_duration / completed_entries.count()
            
            stage_analytics.append({
                'stage_id': stage.stage_id,
                'stage_name': stage.stage_name,
                'stage_code': stage.stage_code,
                'stage_order': stage.stage_order,
                'current_vendors': current_in_stage,
                'completed_vendors': completed_stage,
                'active_vendors': active_in_stage,
                'avg_duration_hours': round(avg_duration_hours, 2),
                'avg_duration_days': round(avg_duration_hours / 24, 2),
                'max_duration_days': stage.max_duration_days,
                'approval_required': stage.approval_required
            })
        
        # Get overall statistics
        # MULTI-TENANCY: Filter by tenant
        total_vendors = TempVendor.objects.filter(tenant_id=tenant_id).count()
        vendors_with_tracking = LifecycleTracker.objects.filter(vendor_id__in=vendor_ids).values('vendor_id').distinct().count()
        
        return Response({
            'stage_analytics': stage_analytics,
            'overall_stats': {
                'total_vendors': total_vendors,
                'vendors_with_tracking': vendors_with_tracking,
                'tracking_coverage_percentage': round((vendors_with_tracking / total_vendors * 100), 2) if total_vendors > 0 else 0
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch lifecycle analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def update_lifecycle_stage_completion(vendor_id, stage_code, completion_status='completed'):
    """
    Utility function to update lifecycle stage completion in lifecycle_tracker table
    
    Args:
        vendor_id (int): ID of the vendor
        stage_code (str): Stage code (e.g., 'QUES_APP', 'RES_APP', 'VEN_APP')
        completion_status (str): 'completed' or 'started'
    
    Returns:
        dict: Result of the operation
    """
    try:
        from apps.vendor_core.models import LifecycleTracker, TempVendor
        from apps.vendor_core.views import get_lifecycle_stage_id_by_code
        from django.utils import timezone
        
        current_time = timezone.now()
        
        # Get stage ID by code
        stage_id = get_lifecycle_stage_id_by_code(stage_code)
        
        if not stage_id:
            return {
                'success': False, 
                'error': f'Could not find stage ID for code: {stage_code}'
            }
        
        if completion_status == 'completed':
            # End the current stage
            stage_entry = LifecycleTracker.objects.filter(
                vendor_id=vendor_id,
                lifecycle_stage=stage_id,
                ended_at__isnull=True
            ).first()
            
            if stage_entry:
                stage_entry.ended_at = current_time
                stage_entry.save()
                return {
                    'success': True,
                    'message': f'Ended {stage_code} stage for vendor {vendor_id}',
                    'stage_code': stage_code,
                    'vendor_id': vendor_id,
                    'ended_at': current_time.isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'No active {stage_code} stage found for vendor {vendor_id}'
                }
        
        elif completion_status == 'started':
            # Start a new stage
            LifecycleTracker.objects.create(
                vendor_id=vendor_id,
                lifecycle_stage=stage_id,
                started_at=current_time
            )
            
            # Update temp vendor current stage
            try:
                temp_vendor = TempVendor.objects.get(id=vendor_id)
                temp_vendor.lifecycle_stage = stage_id
                temp_vendor.save()
            except TempVendor.DoesNotExist:
                pass  # Continue even if temp vendor update fails
            
            return {
                'success': True,
                'message': f'Started {stage_code} stage for vendor {vendor_id}',
                'stage_code': stage_code,
                'vendor_id': vendor_id,
                'started_at': current_time.isoformat()
            }
        
        else:
            return {
                'success': False,
                'error': f'Invalid completion_status: {completion_status}. Must be "completed" or "started"'
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error updating lifecycle stage: {str(e)}'
        }
