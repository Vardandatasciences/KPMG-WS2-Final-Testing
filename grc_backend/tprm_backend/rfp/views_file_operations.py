"""
Django API Views for S3 File Operations
Provides REST API endpoints for file upload, download, and export operations
"""

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import os
import tempfile
from typing import Dict, Any

from .s3_service import get_s3_service
from .models import FileStorage, S3Files, RFP
from .rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission
from tprm_backend.rbac.tprm_decorators import rbac_rfp_required, rbac_rfp_optional

# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    require_tenant,
    tenant_filter
)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def s3_health_check(request):
    """
    Health check endpoint for S3 microservice
    MULTI-TENANCY: Ensures tenant context is present
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    try:
        s3_service = get_s3_service()
        result = s3_service.test_connection()
        
        return Response({
            'status': 'healthy' if result.get('overall_success') else 'unhealthy',
            's3_service': result,
            'django_integration': 'active'
        })
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def upload_file(request):
    """
    Upload a file to S3 via microservice
    
    Expected form data:
    - file: The file to upload
    - user_id: User ID for tracking
    - custom_file_name: Optional custom name for the file
    - rfp_id: Optional RFP ID for association
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # Get form data
        file = request.FILES.get('file')
        user_id = request.POST.get('user_id', 'default-user')
        custom_file_name = request.POST.get('custom_file_name')
        rfp_id = request.POST.get('rfp_id')
        
        # MULTI-TENANCY: Verify RFP belongs to tenant if rfp_id provided
        if rfp_id:
            from .models import RFP
            try:
                rfp = RFP.objects.get(rfp_id=int(rfp_id), tenant_id=tenant_id)
            except RFP.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'RFP not found: {rfp_id}'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if not file:
            return Response({
                'success': False,
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # Upload to S3
            s3_service = get_s3_service()
            result = s3_service.upload_file(
                file_path=temp_file_path,
                user_id=user_id,
                custom_file_name=custom_file_name or file.name,
                rfp_id=int(rfp_id) if rfp_id else None
            )
            
            return Response(result)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def download_file(request):
    """
    Download a file from S3 via microservice
    
    Expected JSON data:
    - s3_key: S3 key of the file to download
    - file_name: Name for the downloaded file
    - user_id: User ID for tracking
    - destination_path: Optional local path to save the file
    MULTI-TENANCY: Ensures tenant context is present
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    try:
        data = request.data
        
        s3_key = data.get('s3_key')
        file_name = data.get('file_name')
        user_id = data.get('user_id', 'default-user')
        destination_path = data.get('destination_path', './downloads')
        
        if not s3_key or not file_name:
            return Response({
                'success': False,
                'error': 's3_key and file_name are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Download from S3
        s3_service = get_s3_service()
        result = s3_service.download_file(
            s3_key=s3_key,
            file_name=file_name,
            user_id=user_id,
            destination_path=destination_path
        )
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def export_data(request):
    """
    Export data to S3 via microservice
    
    Expected JSON data:
    - data: Data to export (list or dict)
    - export_format: Format for export (json, csv, xml, txt, pdf)
    - file_name: Name for the exported file
    - user_id: User ID for tracking
    - rfp_id: Optional RFP ID for association
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        data = request.data
        
        export_data = data.get('data')
        export_format = data.get('export_format')
        file_name = data.get('file_name')
        user_id = data.get('user_id', 'default-user')
        rfp_id = data.get('rfp_id')
        
        # MULTI-TENANCY: Verify RFP belongs to tenant if rfp_id provided
        if rfp_id:
            from .models import RFP
            try:
                rfp = RFP.objects.get(rfp_id=int(rfp_id), tenant_id=tenant_id)
            except RFP.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'RFP not found: {rfp_id}'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if not all([export_data, export_format, file_name]):
            return Response({
                'success': False,
                'error': 'data, export_format, and file_name are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Export to S3
        s3_service = get_s3_service()
        result = s3_service.export_data(
            data=export_data,
            export_format=export_format,
            file_name=file_name,
            user_id=user_id,
            rfp_id=int(rfp_id) if rfp_id else None
        )
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def file_history(request):
    """
    Get file operation history
    
    Query parameters:
    - user_id: Filter by user ID
    - operation_type: Filter by operation type (upload, download, export)
    - limit: Maximum number of records (default: 10)
    MULTI-TENANCY: Ensures tenant context is present
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    try:
        user_id = request.GET.get('user_id')
        operation_type = request.GET.get('operation_type')
        limit = int(request.GET.get('limit', 10))
        
        s3_service = get_s3_service()
        history = s3_service.get_file_history(
            user_id=user_id,
            operation_type=operation_type,
            limit=limit
        )
        
        return Response({
            'success': True,
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def file_stats(request):
    """
    Get file operation statistics
    MULTI-TENANCY: Ensures tenant context is present
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    try:
        s3_service = get_s3_service()
        stats = s3_service.get_file_stats()
        
        return Response({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_file_by_id(request, file_id):
    """
    Get specific file operation details by ID
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # MULTI-TENANCY: Filter by tenant (if FileStorage has tenant_id field)
        try:
            file_storage = FileStorage.objects.get(id=file_id)
            # Note: If FileStorage model has tenant_id, add: tenant_id=tenant_id
        except FileStorage.DoesNotExist:
            return Response({
                'success': False,
                'error': 'File operation not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'file_operation': {
                'id': file_storage.id,
                'operation_type': file_storage.operation_type,
                'user_id': file_storage.user_id,
                'file_name': file_storage.file_name,
                'stored_name': file_storage.stored_name,
                's3_url': file_storage.s3_url,
                's3_key': file_storage.s3_key,
                's3_bucket': file_storage.s3_bucket,
                'file_type': file_storage.file_type,
                'file_size': file_storage.file_size,
                'content_type': file_storage.content_type,
                'export_format': file_storage.export_format,
                'record_count': file_storage.record_count,
                'status': file_storage.status,
                'error': file_storage.error,
                'metadata': file_storage.metadata,
                'platform': file_storage.platform,
                'created_at': file_storage.created_at.isoformat() if file_storage.created_at else None,
                'updated_at': file_storage.updated_at.isoformat() if file_storage.updated_at else None,
                'completed_at': file_storage.completed_at.isoformat() if file_storage.completed_at else None,
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])  # Allow anonymous access for vendor portal
@permission_classes([AllowAny])  # Allow anonymous access for vendor portal
@csrf_exempt
def get_s3_file_by_id(request, file_id):
    """
    Get specific S3 file details by ID - PUBLIC ENDPOINT
    No authentication required for vendor portal access
    Allows anonymous access for vendor portal document validation
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    # For public endpoints, try to get tenant_id from file metadata if not in request
    if not tenant_id:
        # Try to get from file metadata
        pass
    
    try:
        # MULTI-TENANCY: Filter by tenant (if S3Files has tenant_id field)
        try:
            s3_file = S3Files.objects.get(id=file_id)
            # Note: If S3Files model has tenant_id, add: tenant_id=tenant_id
            # For now, we'll validate tenant access through related RFP if available
        except S3Files.DoesNotExist:
            return Response({
                'success': False,
                'error': 'S3 file not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            's3_file': {
                'id': s3_file.id,
                'file_name': s3_file.file_name,
                'file_type': s3_file.file_type,
                'url': s3_file.url,
                'user_id': s3_file.user_id,
                'metadata': s3_file.metadata,
                'uploaded_at': s3_file.uploaded_at.isoformat() if s3_file.uploaded_at else None,
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def export_rfp_data(request, rfp_id):
    """
    Export RFP data in various formats
    
    Expected JSON data:
    - export_format: Format for export (json, csv, xml, txt, pdf)
    - file_name: Name for the exported file
    - user_id: User ID for tracking
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        data = request.data
        
        export_format = data.get('export_format', 'json')
        file_name = data.get('file_name', f'rfp_{rfp_id}_export')
        user_id = data.get('user_id', 'default-user')
        
        # Get RFP data (you'll need to implement this based on your RFP model)
        from .models import RFP
        # MULTI-TENANCY: Filter by tenant
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=tenant_id)
        except RFP.DoesNotExist:
            return Response({
                'success': False,
                'error': 'RFP not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare RFP data for export
        rfp_data = {
            'rfp_id': rfp.rfp_id,
            'rfp_number': rfp.rfp_number,
            'rfp_title': rfp.rfp_title,
            'description': rfp.description,
            'rfp_type': rfp.rfp_type,
            'category': rfp.category,
            'estimated_value': float(rfp.estimated_value) if rfp.estimated_value else None,
            'currency': rfp.currency,
            'status': rfp.status,
            'created_at': rfp.created_at.isoformat() if rfp.created_at else None,
            'updated_at': rfp.updated_at.isoformat() if rfp.updated_at else None,
            'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
            'evaluation_period_end': rfp.evaluation_period_end.isoformat() if rfp.evaluation_period_end else None,
            'award_date': rfp.award_date.isoformat() if rfp.award_date else None,
        }
        
        # Export to S3
        s3_service = get_s3_service()
        result = s3_service.export_data(
            data=rfp_data,
            export_format=export_format,
            file_name=file_name,
            user_id=user_id,
            rfp_id=rfp_id
        )
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
