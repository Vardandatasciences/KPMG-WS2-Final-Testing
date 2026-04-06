# Django ORM type checking suppression for this entire file
# mypy: disable-error-code="attr-defined"
# pylint: disable=no-member
# type: ignore

import logging
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from ...rbac.decorators import (
    compliance_export_required
)
from ...rbac.permissions import (
    ComplianceExportPermission
)
from ...rbac.utils import RBACUtils
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from ...serializers import UserSerializer
from ...models import (
    User, Framework, Policy, SubPolicy, Compliance, PolicyApproval, ComplianceApproval, 
    Notification, FrameworkVersion, PolicyVersion, LastChecklistItemVerified,
    AuditVersion, AuditFinding, RiskInstance, ExportTask, GRCLog
)
from ...serializers import *
from django.utils import timezone   
import datetime
import uuid
from django.db import models
from django.views.decorators.csrf import csrf_protect as csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ...routes.Global.s3_fucntions import export_data
from django.db.models import Q
import json

# MULTI-TENANCY: Import tenant utilities for data isolation
from ...tenant_utils import (
    require_tenant, tenant_filter, get_tenant_id_from_request,
    validate_tenant_access, get_tenant_aware_queryset
)


# Configure logging
logger = logging.getLogger(__name__)

def _build_compliance_export_data(tenant_id, framework_id=None, policy_id=None, subpolicy_id=None):
    """
    Build compliance export data in one go using the ORM instead of
    requiring the frontend to fetch everything record-by-record.
    """
    qs = Compliance.objects.all().select_related(
        'FrameworkId',
        'SubPolicy',
        'SubPolicy__PolicyId',
    )

    # MULTI-TENANCY: Restrict to current tenant if provided.
    # Many legacy records may have tenant set to NULL, so include those
    # in addition to tenant-specific rows to avoid empty exports.
    if tenant_id:
        qs = qs.filter(Q(tenant_id=tenant_id) | Q(tenant__isnull=True))

    # Scope filtering
    if subpolicy_id:
        qs = qs.filter(SubPolicy_id=subpolicy_id)
    elif policy_id:
        qs = qs.filter(SubPolicy__PolicyId_id=policy_id)
    elif framework_id:
        qs = qs.filter(FrameworkId_id=framework_id)

    export_rows = []
    for comp in qs.iterator():
        framework = comp.FrameworkId
        subpolicy = comp.SubPolicy
        policy = subpolicy.PolicyId

        export_rows.append({
            "FrameworkId": framework.FrameworkId,
            "FrameworkName": framework.FrameworkName,
            "PolicyId": policy.PolicyId,
            "PolicyName": policy.PolicyName,
            "SubPolicyId": subpolicy.SubPolicyId,
            "SubPolicyName": subpolicy.SubPolicyName,
            "ComplianceId": comp.ComplianceId,
            "ComplianceTitle": comp.ComplianceTitle or "",
            "ComplianceItemDescription": comp.ComplianceItemDescription or "",
            "ComplianceType": comp.ComplianceType or "",
            "Status": comp.Status or "",
            "Criticality": comp.Criticality or "",
            "MaturityLevel": comp.MaturityLevel or "",
            "MandatoryOptional": comp.MandatoryOptional or "",
            "ManualAutomatic": comp.ManualAutomatic or "",
            "CreatedByName": comp.CreatedByName or "",
            "CreatedByDate": comp.CreatedByDate.isoformat() if comp.CreatedByDate else None,
            "ComplianceVersion": comp.ComplianceVersion or "",
            "Identifier": comp.Identifier or "",
            "Scope": comp.Scope or "",
            "Objective": comp.Objective or "",
            "IsRisk": bool(comp.IsRisk),
            "PossibleDamage": comp.PossibleDamage or "",
            "Impact": comp.Impact or "",
            "Probability": comp.Probability or "",
            "ActiveInactive": comp.ActiveInactive or "",
        })

    return export_rows


@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])  # Will be replaced with proper RBAC later
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def export_compliance_management(request):
    """
    Export compliance management data to various formats.

    New preferred usage (single call, server does aggregation):
    {
        "export_format": "xlsx|csv|pdf|json|xml",
        "user_id": "string",
        "file_name": "string",
        "framework_id": 4,          # optional
        "policy_id": 123,           # optional
        "subpolicy_id": 456,        # optional
        "scope": { ... }            # optional, same ids
    }

    Backwards compatible usage (legacy):
    {
        "export_format": "xlsx|csv|pdf|json|xml",
        "compliance_data": [...],
        "user_id": "string",
        "file_name": "string"
    }
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        # Log the incoming request
        logger.info(f"Compliance export request received from user: {request.user}")
        
        # Get request data
        export_format = request.data.get('export_format', 'xlsx')
        compliance_data = request.data.get('compliance_data', [])
        user_id = request.data.get('user_id', 'default_user')
        file_name = request.data.get('file_name', 'compliance_management_export')
        # Optional scope information for server-side aggregation
        scope = request.data.get('scope', {}) or {}
        framework_id = request.data.get('framework_id') or scope.get('framework_id')
        policy_id = request.data.get('policy_id') or scope.get('policy_id')
        subpolicy_id = request.data.get('subpolicy_id') or scope.get('subpolicy_id')
        
        # Handle string representation of empty list / JSON-encoded payload
        if isinstance(compliance_data, str):
            try:
                compliance_data = json.loads(compliance_data)
            except (json.JSONDecodeError, ValueError):
                compliance_data = []

        # If no compliance_data was provided, build it in one go on the server
        if not compliance_data:
            logger.info(
                f"No compliance_data provided, building export on server "
                f"(framework_id={framework_id}, policy_id={policy_id}, subpolicy_id={subpolicy_id})"
            )
            compliance_data = _build_compliance_export_data(
                tenant_id=tenant_id,
                framework_id=framework_id,
                policy_id=policy_id,
                subpolicy_id=subpolicy_id,
            )
        
        # Validate required fields - check for empty list or None AFTER server-side aggregation
        if not compliance_data or (isinstance(compliance_data, list) and len(compliance_data) == 0):
            return Response({
                'success': False,
                'error': 'No compliance data found to export for the requested scope.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not export_format:
            return Response({
                'success': False,
                'error': 'Export format is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate export format
        supported_formats = ['xlsx', 'csv', 'pdf', 'json', 'xml', 'txt']
        if export_format not in supported_formats:
            return Response({
                'success': False,
                'error': f'Unsupported export format: {export_format}. Supported formats: {supported_formats}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Log export details with data structure info
        logger.info(f"Starting compliance export: format={export_format}, records={len(compliance_data)}, user={user_id}")
        logger.info(f"Data type: {type(compliance_data)}, Is list: {isinstance(compliance_data, list)}")
        if compliance_data and len(compliance_data) > 0:
            logger.info(f"First record keys: {list(compliance_data[0].keys())[:10] if isinstance(compliance_data[0], dict) else 'N/A'}")
            logger.info(f"First record sample: {str(compliance_data[0])[:200]}...")
        else:
            logger.warning(f"⚠️  Empty or invalid compliance_data received!")
        
        # Create export task record to track export status (allows continuation if user navigates away)
        try:
            export_task = ExportTask.objects.create(
                user_id=user_id,
                file_type=export_format,
                status='processing',
                export_data={
                    'file_name': file_name,
                    'export_format': export_format,
                    'record_count': len(compliance_data),
                    'export_type': 'compliance_management',
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            export_task_id = export_task.id
            logger.info(f"Created export task {export_task_id} for tracking")
        except Exception as task_error:
            logger.warning(f"Failed to create export task: {str(task_error)}")
            export_task_id = None
        
        # Prepare export options
        export_options = {
            'file_name': f"{file_name}.{export_format}",
            'filters': {
                'export_type': 'compliance_management',
                'timestamp': datetime.datetime.now().isoformat(),
                'user_id': user_id
            },
            'columns': list(compliance_data[0].keys()) if compliance_data and len(compliance_data) > 0 and isinstance(compliance_data[0], dict) else []
        }
        
        logger.info(f"Calling export_data with {len(compliance_data)} records, format={export_format}")
        
        # Call the export service
        export_result = export_data(
            data=compliance_data,
            file_format=export_format,
            user_id=user_id,
            options=export_options
        )
        
        # Update export task with results
        if export_task_id:
            try:
                export_task = ExportTask.objects.get(id=export_task_id)
                if export_result['success']:
                    export_task.status = 'completed'
                    export_task.s3_url = export_result.get('file_url', '')
                    export_task.file_name = export_result.get('file_name', f"{file_name}.{export_format}")
                    export_task.completed_at = timezone.now()
                    export_task.export_data['file_url'] = export_result.get('file_url', '')
                    export_task.export_data['file_size'] = export_result['metadata'].get('file_size', 0)
                else:
                    export_task.status = 'failed'
                    export_task.error = export_result.get('error', 'Unknown error')
                export_task.save()
                logger.info(f"Updated export task {export_task_id} status: {export_task.status}")
            except Exception as update_error:
                logger.warning(f"Failed to update export task: {str(update_error)}")
        
        if export_result['success']:
            logger.info(f"Compliance export successful: {export_result['file_url']}")
            
            # Log the export activity
            try:
                GRCLog.objects.create(
                    user_id=user_id,
                    action='COMPLIANCE_EXPORT',
                    model_name='Compliance',
                    object_id=None,
                    details=json.dumps({
                        'export_format': export_format,
                        'record_count': len(compliance_data),
                        'file_name': export_result['file_name'],
                        'export_id': export_result.get('export_id'),
                        'method': export_result['metadata'].get('method', 'unknown')
                    }),
                    timestamp=timezone.now()
                )
            except Exception as log_error:
                logger.warning(f"Failed to log export activity: {str(log_error)}")
            
            return Response({
                'success': True,
                'message': 'Compliance data exported successfully',
                'file_url': export_result['file_url'],
                'file_name': export_result['file_name'],
                'export_id': export_task_id or export_result.get('export_id'),
                'task_id': export_task_id,  # Include task_id for status checking
                'metadata': {
                    'record_count': len(compliance_data),
                    'export_format': export_format,
                    'file_size': export_result['metadata'].get('file_size', 0),
                    'export_duration': export_result['metadata'].get('export_duration', 0),
                    'method': export_result['metadata'].get('method', 'unknown')
                }
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Compliance export failed: {export_result['error']}")
            return Response({
                'success': False,
                'error': export_result['error'],
                'message': 'Failed to export compliance data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Compliance export error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e),
            'message': 'An unexpected error occurred during export'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])  # Will be replaced with proper RBAC later
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_export_status(request, export_id):
    """
    Get the status of an export operation
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        # Query the export task from the database
        export_task = ExportTask.objects.get(id=export_id)
        
        response_data = {
            'success': True,
            'export_id': export_id,
            'status': export_task.status,  # processing, completed, failed
            'file_url': export_task.s3_url if export_task.s3_url else None,
            'file_name': export_task.file_name if export_task.file_name else None,
            'created_at': export_task.created_at.isoformat() if export_task.created_at else None,
            'completed_at': export_task.completed_at.isoformat() if export_task.completed_at else None,
            'error': export_task.error if export_task.error else None,
            'message': 'Export status retrieved successfully'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except ExportTask.DoesNotExist:
        logger.error(f"Export task {export_id} not found")
        return Response({
            'success': False,
            'error': f'Export task {export_id} not found',
            'message': 'Export task not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting export status: {str(e)}")
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Failed to get export status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])  # Will be replaced with proper RBAC later
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def list_export_history(request):
    """
    List export history for the current user
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        user_id = request.GET.get('user_id', 'default_user')
        
        # This would typically query the export history from the database
        # For now, return a simple response
        return Response({
            'success': True,
            'exports': [],
            'message': 'Export history retrieved successfully'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting export history: {str(e)}")
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Failed to get export history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
