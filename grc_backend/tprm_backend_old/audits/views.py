"""
Views for the Audits app.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes as permission_classes_decorator, authentication_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

# Use Unified JWT Authentication from GRC
from grc.jwt_auth import UnifiedJWTAuthentication
from django.utils import timezone
from datetime import datetime, timedelta
import jwt
import logging

from .models import Audit, StaticQuestionnaire, AuditVersion, AuditFinding, AuditReport
from .serializers import (
    AuditSerializer, AuditCreateSerializer, AuditListSerializer,
    StaticQuestionnaireSerializer, AuditVersionSerializer, 
    AuditFindingSerializer, AuditReportSerializer
)
from tprm_backend.slas.models import VendorSLA, SLAMetric

logger = logging.getLogger(__name__)


class SimpleAuthenticatedPermission(BasePermission):
    """Custom permission class that checks for authenticated users"""
    def has_permission(self, request, view):
        # Just check if user object exists and is authenticated
        # UnifiedJWTAuthentication handles GRC/TPRM user verification
        if request.user and hasattr(request.user, 'is_authenticated'):
            return request.user.is_authenticated
        return False



class AuditListView(generics.ListCreateAPIView):
    """List and create audits."""
    queryset = Audit.objects.all()
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'audit_type', 'frequency', 'auditor_id', 'reviewer_id']
    search_fields = ['title', 'scope']
    ordering_fields = ['due_date', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AuditCreateSerializer
        return AuditListSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to return full audit payload including audit_id and sla_id."""
        try:
            print(f"Received audit creation request: {request.data}")
            create_serializer = AuditCreateSerializer(data=request.data)
            create_serializer.is_valid(raise_exception=True)
            audit_instance = create_serializer.save()
            # Re-serialize with full serializer to include audit_id, sla_id, sla_name, etc.
            output_serializer = AuditSerializer(audit_instance)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error creating audit: {e}")
            return Response(
                {'error': str(e), 'details': 'Failed to create audit'},
                status=status.HTTP_400_BAD_REQUEST
            )


class AuditDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete audit."""
    queryset = Audit.objects.all()
    serializer_class = AuditSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]


class QuestionnairesPagination(PageNumberPagination):
    """Custom pagination for questionnaires that allows fetching all records."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000  # Allow up to 1000 records per page


class StaticQuestionnaireListView(generics.ListCreateAPIView):
    """List and create static questionnaires."""
    queryset = StaticQuestionnaire.objects.all()
    serializer_class = StaticQuestionnaireSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    pagination_class = QuestionnairesPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['metric_name', 'question_type', 'is_required']


class StaticQuestionnaireDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete static questionnaire."""
    queryset = StaticQuestionnaire.objects.all()
    serializer_class = StaticQuestionnaireSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]


class AuditVersionListView(generics.ListCreateAPIView):
    """List and create audit versions."""
    queryset = AuditVersion.objects.all()
    serializer_class = AuditVersionSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'version_type', 'approval_status', 'user_id']
    ordering_fields = ['date_created', 'created_at']
    ordering = ['-created_at']


class AuditVersionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete audit version."""
    queryset = AuditVersion.objects.all()
    serializer_class = AuditVersionSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]


class AuditFindingListView(generics.ListCreateAPIView):
    """List and create audit findings."""
    queryset = AuditFinding.objects.all()
    serializer_class = AuditFindingSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'metrics_id', 'user_id']
    ordering_fields = ['check_date', 'created_at']
    ordering = ['-created_at']


class AuditFindingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete audit finding."""
    queryset = AuditFinding.objects.all()
    serializer_class = AuditFindingSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]


class AuditReportListView(generics.ListCreateAPIView):
    """List and create audit reports."""
    queryset = AuditReport.objects.all()
    serializer_class = AuditReportSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'sla_id', 'metrics_id']
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']


class AuditReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete audit report."""
    queryset = AuditReport.objects.all()
    serializer_class = AuditReportSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
def audit_dashboard_stats(request):
    """Get audit dashboard statistics."""
    total_audits = Audit.objects.count()
    active_audits = Audit.objects.filter(status__in=['created', 'in_progress']).count()
    completed_audits = Audit.objects.filter(status='completed').count()
    overdue_audits = Audit.objects.filter(
        due_date__lt=timezone.now().date(),
        status__in=['created', 'in_progress']
    ).count()
    
    return Response({
        'total_audits': total_audits,
        'active_audits': active_audits,
        'completed_audits': completed_audits,
        'overdue_audits': overdue_audits,
    })


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
def available_slas(request):
    """Get available SLAs for audit creation."""
    # Check if user is admin (user_id = 1) - admin can access any SLA
    user_id = request.GET.get('user_id', request.headers.get('X-User-ID', '1'))
    is_admin = str(user_id) == '1'
    
    if is_admin:
        # Admin can access any SLA regardless of status
        slas = VendorSLA.objects.all().select_related('vendor', 'contract')
    else:
        # Regular users can only access active SLAs
        slas = VendorSLA.objects.filter(status='ACTIVE').select_related('vendor', 'contract')
    
    sla_data = []
    for sla in slas:
        metrics_count = SLAMetric.objects.filter(sla=sla).count()
        sla_data.append({
            'sla_id': sla.sla_id,
            'sla_name': sla.sla_name,
            'sla_type': sla.sla_type,
            'status': sla.status,  # Include status for admin view
            'vendor_name': sla.vendor.company_name if sla.vendor else 'Unknown',
            'contract_name': sla.contract.contract_name if sla.contract else 'Unknown',
            'effective_date': sla.effective_date,
            'expiry_date': sla.expiry_date,
            'metrics_count': metrics_count,
            'business_service_impacted': sla.business_service_impacted,
        })
    
    return Response(sla_data)


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
def sla_metrics(request, sla_id):
    """Get metrics for a specific SLA."""
    try:
        # Check if user is admin (user_id = 1) - admin can access any SLA
        user_id = request.GET.get('user_id', request.headers.get('X-User-ID', '1'))
        is_admin = str(user_id) == '1'
        
        if is_admin:
            # Admin can access any SLA regardless of status
            sla = VendorSLA.objects.get(sla_id=sla_id)
        else:
            # Regular users can only access active SLAs
            sla = VendorSLA.objects.get(sla_id=sla_id, status='ACTIVE')
        
        metrics = SLAMetric.objects.filter(sla=sla)
        
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                'metric_id': metric.metric_id,
                'metric_name': metric.metric_name,
                'threshold': metric.threshold,
                'measurement_unit': metric.measurement_unit,
                'frequency': metric.frequency,
                'penalty': metric.penalty,
                'measurement_methodology': metric.measurement_methodology,
            })
        
        return Response({
            'sla': {
                'sla_id': sla.sla_id,
                'sla_name': sla.sla_name,
                'sla_type': sla.sla_type,
                'status': sla.status,  # Include status for admin view
            },
            'metrics': metrics_data
        })
    except VendorSLA.DoesNotExist:
        return Response(
            {'error': 'SLA not found or not active'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
def available_users(request):
    """Get available users for auditor and reviewer assignment."""
    from django.db import connections
    
    try:
        # Connect to tprm_integration database
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT UserId, UserName, Email, FirstName, LastName, DepartmentId, IsActive
                FROM users 
                WHERE IsActive = 'Y' OR IsActive = '1' OR IsActive = 'true'
                ORDER BY FirstName, LastName
            """)
            
            users_data = []
            for row in cursor.fetchall():
                user_id, username, email, first_name, last_name, dept_id, is_active = row
                
                # Combine first and last name
                full_name = f"{first_name or ''} {last_name or ''}".strip()
                if not full_name:
                    full_name = username or f"User {user_id}"
                
                # For now, we'll assign roles based on department or user ID
                # In a real system, you might have a separate roles table
                if dept_id == 1 or user_id % 2 == 1:
                    role = 'auditor'
                else:
                    role = 'reviewer'
                
                users_data.append({
                    'user_id': user_id,
                    'name': full_name,
                    'email': email or f"user{user_id}@example.com",
                    'role': role,
                    'department': f"Department {dept_id}" if dept_id else "Unknown",
                    'username': username
                })
            
            return Response(users_data)
            
    except Exception as e:
        # Fallback to mock data if database connection fails
        print(f"Error connecting to tprm_db: {e}")
        users_data = [
            {
                'user_id': 1,
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'role': 'auditor',
                'department': 'IT'
            },
            {
                'user_id': 2,
                'name': 'Jane Smith',
                'email': 'jane.smith@example.com',
                'role': 'reviewer',
                'department': 'Compliance'
            },
            {
                'user_id': 3,
                'name': 'Mike Johnson',
                'email': 'mike.johnson@example.com',
                'role': 'auditor',
                'department': 'IT'
            },
            {
                'user_id': 4,
                'name': 'Sarah Wilson',
                'email': 'sarah.wilson@example.com',
                'role': 'reviewer',
                'department': 'Compliance'
            }
        ]
        return Response(users_data)


@api_view(['POST'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
def submit_audit_response(request, audit_id):
    """Submit responses for an audit."""
    try:
        audit = Audit.objects.get(audit_id=audit_id)
        responses_data = request.data.get('responses', [])
        
        # Validate and save responses
        saved_responses = []
        for response_data in responses_data:
            question_id = response_data.get('question_id')
            try:
                question = AuditQuestion.objects.get(question_id=question_id, audit=audit)
                
                # Create or update response
                response, created = AuditResponse.objects.update_or_create(
                    audit=audit,
                    question=question,
                    submitted_by=request.data.get('submitted_by', 1),
                    defaults={
                        'response_text': response_data.get('response_text'),
                        'response_number': response_data.get('response_number'),
                        'response_boolean': response_data.get('response_boolean'),
                        'response_json': response_data.get('response_json'),
                    }
                )
                saved_responses.append(response)
            except AuditQuestion.DoesNotExist:
                continue
        
        # Update audit status if all questions answered
        total_questions = AuditQuestion.objects.filter(audit=audit).count()
        answered_questions = AuditResponse.objects.filter(audit=audit).count()
        
        if answered_questions >= total_questions:
            audit.status = 'under_review'
            audit.save()
        
        return Response({
            'message': f'Successfully saved {len(saved_responses)} responses',
            'responses_saved': len(saved_responses)
        })
        
    except Audit.DoesNotExist:
        return Response(
            {'error': 'Audit not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
def review_audit(request, audit_id):
    """Review and approve/reject an audit."""
    try:
        audit = Audit.objects.get(audit_id=audit_id)
        action = request.data.get('action', 'approve')
        comments = request.data.get('comments', '')
        
        if action == 'approve':
            audit.review_status = 'approved'
            audit.status = 'completed'
            audit.completion_date = timezone.now().date()
        else:
            audit.review_status = 'rejected'
            audit.status = 'rejected'
        
        audit.review_comments = comments
        audit.review_date = timezone.now().date()
        audit.save()
        
        return Response({
            'message': f'Audit {action}d successfully',
            'audit_status': audit.status,
            'review_status': audit.review_status
        })
        
    except Audit.DoesNotExist:
        return Response(
            {'error': 'Audit not found'},
            status=status.HTTP_404_NOT_FOUND
        )
