"""
SEBI AI Auditor API Endpoints
REST API for SEBI compliance verification features
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.db import connection

from ...models import Framework, Audit
from ...tenant_utils import require_tenant, tenant_filter, get_tenant_id_from_request
from ...rbac.decorators import audit_analytics_required
from .sebi_ai_auditor import SEBIAIAuditor, enable_sebi_ai_auditor

# DRF Session auth variant that skips CSRF enforcement
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant
@tenant_filter
def enable_sebi_auditor(request, framework_id):
    """
    Enable SEBI AI Auditor for a framework
    POST /api/sebi-auditor/{framework_id}/enable/
    """
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        success = enable_sebi_ai_auditor(framework_id, tenant_id)
        if success:
            return Response({
                'success': True,
                'message': f'SEBI AI Auditor enabled for framework {framework_id}',
                'framework_id': framework_id
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Failed to enable SEBI AI Auditor. Framework not found or invalid.'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant
@tenant_filter
@audit_analytics_required
def verify_filing_accuracy(request, audit_id):
    """
    Filing Accuracy Verification
    GET /api/sebi-auditor/audit/{audit_id}/filing-accuracy/
    """
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # Get framework_id from audit
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT FrameworkId FROM audit
                WHERE AuditId = %s AND TenantId = %s
            """, [audit_id, tenant_id])
            row = cursor.fetchone()
            if not row:
                return Response({
                    'error': 'Audit not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            framework_id = row[0]
        
        auditor = SEBIAIAuditor(framework_id, tenant_id)
        document_id = request.GET.get('document_id')
        results = auditor.verify_filing_accuracy(audit_id, document_id)
        
        return Response(results, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant
@tenant_filter
@audit_analytics_required
def check_timeliness_sla(request, audit_id):
    """
    Timeliness & SLA Monitoring
    GET /api/sebi-auditor/audit/{audit_id}/timeliness-sla/?filing_type=financial_results
    """
    tenant_id = get_tenant_id_from_request(request)
    filing_type = request.GET.get('filing_type')
    
    try:
        # Get framework_id from audit
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT FrameworkId FROM audit
                WHERE AuditId = %s AND TenantId = %s
            """, [audit_id, tenant_id])
            row = cursor.fetchone()
            if not row:
                return Response({
                    'error': 'Audit not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            framework_id = row[0]
        
        auditor = SEBIAIAuditor(framework_id, tenant_id)
        results = auditor.check_timeliness_sla(audit_id, filing_type)
        
        return Response(results, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant
@tenant_filter
@audit_analytics_required
def calculate_risk_score(request, audit_id):
    """
    Risk Scoring Model
    GET /api/sebi-auditor/audit/{audit_id}/risk-score/
    """
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # Get framework_id from audit
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT FrameworkId FROM audit
                WHERE AuditId = %s AND TenantId = %s
            """, [audit_id, tenant_id])
            row = cursor.fetchone()
            if not row:
                return Response({
                    'error': 'Audit not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            framework_id = row[0]
        
        auditor = SEBIAIAuditor(framework_id, tenant_id)
        results = auditor.calculate_risk_score(audit_id)
        
        return Response(results, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant
@tenant_filter
@audit_analytics_required
def detect_patterns(request, audit_id=None):
    """
    AI-Driven Pattern & Behavioural Analysis
    GET /api/sebi-auditor/patterns/?audit_id={audit_id}
    """
    tenant_id = get_tenant_id_from_request(request)
    audit_id = audit_id or request.GET.get('audit_id')
    
    try:
        if audit_id:
            # Get framework_id from audit
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT FrameworkId FROM audit
                    WHERE AuditId = %s AND TenantId = %s
                """, [audit_id, tenant_id])
                row = cursor.fetchone()
                if not row:
                    return Response({
                        'error': 'Audit not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                framework_id = row[0]
        else:
            # Get from framework_id parameter
            framework_id = request.GET.get('framework_id')
            if not framework_id:
                return Response({
                    'error': 'audit_id or framework_id required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        auditor = SEBIAIAuditor(framework_id, tenant_id)
        results = auditor.detect_patterns(audit_id)
        
        return Response(results, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant
@tenant_filter
@audit_analytics_required
def generate_evidence_pack(request, audit_id):
    """
    Evidence Pack Generation
    GET /api/sebi-auditor/audit/{audit_id}/evidence-pack/?use_case=sebi_inspection
    """
    tenant_id = get_tenant_id_from_request(request)
    use_case = request.GET.get('use_case', 'sebi_inspection')
    
    try:
        # Get framework_id from audit
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT FrameworkId FROM audit
                WHERE AuditId = %s AND TenantId = %s
            """, [audit_id, tenant_id])
            row = cursor.fetchone()
            if not row:
                return Response({
                    'error': 'Audit not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            framework_id = row[0]
        
        auditor = SEBIAIAuditor(framework_id, tenant_id)
        results = auditor.generate_evidence_pack(audit_id, use_case)
        
        return Response(results, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant
@tenant_filter
@audit_analytics_required
def sebi_dashboard(request, framework_id=None):
    """
    SEBI Regulatory Dashboard
    GET /api/sebi-auditor/dashboard/?framework_id={framework_id}
    """
    tenant_id = get_tenant_id_from_request(request)
    framework_id = framework_id or request.GET.get('framework_id')
    
    if not framework_id:
        return Response({
            'error': 'framework_id required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        auditor = SEBIAIAuditor(framework_id, tenant_id)
        
        # Market-Level View
        with connection.cursor() as cursor:
            # % on-time filings
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN CompletionDate <= DueDate THEN 1 ELSE 0 END) as on_time,
                    ROUND(SUM(CASE WHEN CompletionDate <= DueDate THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as on_time_percent
                FROM audit
                WHERE FrameworkId = %s
                  AND TenantId = %s
                  AND DueDate IS NOT NULL
                  AND CompletionDate IS NOT NULL
            """, [framework_id, tenant_id])
            
            market_stats = cursor.fetchone()
            
            # High-risk companies (audits with high risk scores)
            cursor.execute("""
                SELECT 
                    a.AuditId,
                    a.Title,
                    COUNT(af.AuditFindingId) as finding_count
                FROM audit a
                LEFT JOIN audit_findings af ON a.AuditId = af.AuditId
                WHERE a.FrameworkId = %s
                  AND a.TenantId = %s
                GROUP BY a.AuditId, a.Title
                HAVING finding_count >= 3
                ORDER BY finding_count DESC
                LIMIT 10
            """, [framework_id, tenant_id])
            
            high_risk_audits = cursor.fetchall()
        
        dashboard_data = {
            'market_level': {
                'total_filings': market_stats[0] or 0,
                'on_time_filings': market_stats[1] or 0,
                'on_time_percentage': market_stats[2] or 0.0,
                'high_risk_audits': [
                    {
                        'audit_id': row[0],
                        'title': row[1],
                        'finding_count': row[2]
                    }
                    for row in high_risk_audits
                ]
            },
            'framework_id': framework_id,
            'sebi_enabled': auditor.is_sebi_framework
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
