"""
Cross-Framework Mapping Views
API endpoints for cross-framework compliance checking
"""
import logging
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.views.decorators.csrf import csrf_exempt
from ...rbac.utils import RBACUtils
from ...rbac.decorators import compliance_view_required, compliance_audit_required
from ...rbac.permissions import ComplianceViewPermission, ComplianceAuditPermission
from .cross_framework_mapping_service import CrossFrameworkMappingService
from ...models import AuditDocument, Framework
# MULTI-TENANCY: Import tenant utilities for data isolation
from ...tenant_utils import (
    require_tenant, tenant_filter, get_tenant_id_from_request,
    validate_tenant_access, get_tenant_aware_queryset
)

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([ComplianceAuditPermission])
@compliance_audit_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def cross_framework_check(request):
    """
    Check evidence/document against multiple frameworks
    
    Request body:
    {
        "document_id": 123,
        "primary_framework_id": 1,
        "audit_id": 456,  # optional
        "target_framework_ids": [2, 3, 4]  # optional, if not provided checks all active frameworks
    }
    """
    try:
        # Check authentication
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get request data
        document_id = request.data.get('document_id')
        primary_framework_id = request.data.get('primary_framework_id')
        audit_id = request.data.get('audit_id')
        target_framework_ids = request.data.get('target_framework_ids', None)
        
        # Validate required fields
        if not document_id:
            return Response({
                'success': False,
                'error': 'document_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not primary_framework_id:
            return Response({
                'success': False,
                'error': 'primary_framework_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify document exists
        try:
            document = AuditDocument.objects.get(DocumentId=document_id)
        except AuditDocument.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Document {document_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify primary framework exists
        try:
            primary_framework = Framework.objects.get(FrameworkId=primary_framework_id, tenant_id=tenant_id)
        except Framework.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Framework {primary_framework_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        logger.info(f"🔄 Cross-framework check requested by user {user_id}")
        logger.info(f"   Document: {document_id} ({document.DocumentName})")
        logger.info(f"   Primary Framework: {primary_framework_id} ({primary_framework.FrameworkName})")
        logger.info(f"   Target Frameworks: {target_framework_ids or 'All active frameworks'}")
        
        # Perform cross-framework check
        result = CrossFrameworkMappingService.check_document_against_multiple_frameworks(
            document_id=document_id,
            primary_framework_id=primary_framework_id,
            audit_id=audit_id,
            target_framework_ids=target_framework_ids
        )
        
        if result['success']:
            return Response({
                'success': True,
                'message': f"Document checked against {result['frameworks_checked']} frameworks",
                'data': result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Unknown error occurred'),
                'data': result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in cross_framework_check: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_cross_framework_mappings(request, document_id):
    """
    Get all cross-framework mappings for a document
    
    Returns mappings grouped by framework
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        # Check authentication
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verify document exists
        try:
            document = AuditDocument.objects.get(DocumentId=document_id)
        except AuditDocument.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Document {document_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all mappings for this document
        from ...models import AuditDocumentMapping
        mappings = AuditDocumentMapping.objects.filter(
            DocumentId=document_id
        ).select_related('FrameworkId', 'ComplianceId')
        
        # Group by framework
        framework_groups = {}
        for mapping in mappings:
            framework_id = mapping.FrameworkId.FrameworkId
            framework_name = mapping.FrameworkId.FrameworkName
            
            if framework_id not in framework_groups:
                framework_groups[framework_id] = {
                    'framework_id': framework_id,
                    'framework_name': framework_name,
                    'mappings': [],
                    'status_counts': {
                        'compliant': 0,
                        'partially_compliant': 0,
                        'non_compliant': 0,
                        'requires_review': 0
                    }
                }
            
            mapping_data = {
                'mapping_id': mapping.MappingId,
                'compliance_id': mapping.ComplianceId.ComplianceId,
                'compliance_title': mapping.ComplianceId.ComplianceTitle or mapping.ComplianceId.Identifier,
                'compliance_status': mapping.ComplianceStatus,
                'confidence_score': mapping.ConfidenceScore,
                'risk_level': mapping.RiskLevel,
                'ai_recommendations': mapping.AIRecommendations
            }
            
            framework_groups[framework_id]['mappings'].append(mapping_data)
            
            # Update status counts
            status = mapping.ComplianceStatus
            if status in framework_groups[framework_id]['status_counts']:
                framework_groups[framework_id]['status_counts'][status] += 1
        
        # Calculate overall scores for each framework
        for framework_id, group in framework_groups.items():
            total = len(group['mappings'])
            if total > 0:
                compliant = group['status_counts']['compliant']
                partially = group['status_counts']['partially_compliant']
                group['compliance_score'] = (compliant + partially * 0.5) / total
                group['overall_status'] = 'compliant' if compliant == total else \
                                         'partially_compliant' if compliant + partially > 0 else \
                                         'non_compliant'
            else:
                group['compliance_score'] = 0.0
                group['overall_status'] = 'unknown'
        
        return Response({
            'success': True,
            'document_id': document_id,
            'document_name': document.DocumentName,
            'frameworks': list(framework_groups.values())
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in get_cross_framework_mappings: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_available_frameworks(request):
    """
    Get all available frameworks for cross-framework checking
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        frameworks = CrossFrameworkMappingService.get_active_frameworks()
        
        frameworks_data = []
        for framework in frameworks:
            frameworks_data.append({
                'framework_id': framework.FrameworkId,
                'framework_name': framework.FrameworkName,
                'category': framework.Category,
                'description': framework.FrameworkDescription
            })
        
        return Response({
            'success': True,
            'frameworks': frameworks_data,
            'count': len(frameworks_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in get_available_frameworks: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

