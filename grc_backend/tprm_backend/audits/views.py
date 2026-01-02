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
from tprm_backend.rbac.tprm_utils import RBACTPRMUtils

logger = logging.getLogger(__name__)


class SimpleAuthenticatedPermission(BasePermission):
    """Custom permission class that checks for authenticated users"""
    def has_permission(self, request, view):
        # Check if user is authenticated
        return bool(
            request.user and 
            hasattr(request.user, 'userid') and
            getattr(request.user, 'is_authenticated', False)
        )


class PerformContractAuditPermission(BasePermission):
    """Permission class that checks for PerformContractAudit permission"""
    def has_permission(self, request, view):
        # Get user_id from request
        try:
            user_id = RBACTPRMUtils.get_user_id_from_request(request)
            
            if not user_id:
                logger.warning("[RBAC TPRM] No user_id found in request for PerformContractAudit check")
                return False
            
            # Check PerformContractAudit permission
            has_permission = RBACTPRMUtils.check_contract_permission(user_id, 'PerformContractAudit')
            
            if not has_permission:
                logger.warning(f"[RBAC TPRM] User {user_id} denied PerformContractAudit access")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error checking PerformContractAudit permission: {e}")
            return False


class JWTAuthentication(BaseAuthentication):
    """Custom JWT authentication class for DRF"""
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        try:
            token = auth_header.split(' ')[1]
            # Use JWT_SECRET_KEY from settings
            secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if user_id:
                try:
                    from mfa_auth.models import User
                    user = User.objects.get(userid=user_id)
                    # Add is_authenticated attribute for DRF compatibility
                    user.is_authenticated = True
                    return (user, token)
                except (User.DoesNotExist, ImportError):
                    # If User model doesn't exist or user not found, create a mock user
                    class MockUser:
                        def __init__(self, user_id):
                            self.userid = user_id
                            self.username = f"user_{user_id}"
                            self.is_authenticated = True
                    
                    return (MockUser(user_id), token)
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
        except Exception as e:
            logger.error(f"JWT authentication error: {str(e)}")
            return None


class AuditListView(generics.ListCreateAPIView):
    """List and create audits."""
    queryset = Audit.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]


class QuestionnairesPagination(PageNumberPagination):
    """Custom pagination for questionnaires that allows fetching all records."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000  # Allow up to 1000 records per page


class StaticQuestionnaireListView(generics.ListCreateAPIView):
    """List and create static questionnaires."""
    queryset = StaticQuestionnaire.objects.all()
    serializer_class = StaticQuestionnaireSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    pagination_class = QuestionnairesPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['metric_name', 'question_type', 'is_required']


class StaticQuestionnaireDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete static questionnaire."""
    queryset = StaticQuestionnaire.objects.all()
    serializer_class = StaticQuestionnaireSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]


class AuditVersionListView(generics.ListCreateAPIView):
    """List and create audit versions."""
    queryset = AuditVersion.objects.all()
    serializer_class = AuditVersionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'version_type', 'approval_status', 'user_id']
    ordering_fields = ['date_created', 'created_at']
    ordering = ['-created_at']


class AuditVersionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete audit version."""
    queryset = AuditVersion.objects.all()
    serializer_class = AuditVersionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]


class AuditFindingListView(generics.ListCreateAPIView):
    """List and create audit findings."""
    queryset = AuditFinding.objects.all()
    serializer_class = AuditFindingSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'metrics_id', 'user_id']
    ordering_fields = ['check_date', 'created_at']
    ordering = ['-created_at']


class AuditFindingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete audit finding."""
    queryset = AuditFinding.objects.all()
    serializer_class = AuditFindingSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]


class AuditReportListView(generics.ListCreateAPIView):
    """List and create audit reports."""
    queryset = AuditReport.objects.all()
    serializer_class = AuditReportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'sla_id', 'metrics_id']
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']


class AuditReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete audit report."""
    queryset = AuditReport.objects.all()
    serializer_class = AuditReportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([PerformContractAuditPermission])
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
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([PerformContractAuditPermission])
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
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([PerformContractAuditPermission])
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
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([PerformContractAuditPermission])
def available_users(request):
    """Get users with PerformContractAudit permission for auditor and reviewer assignment."""
    try:
        # Import required models
        from mfa_auth.models import User
        
        # Get all active users (filter by is_active_raw which can be 'Y', 'YES', '1', 'TRUE')
        all_users = User.objects.filter(
            is_active_raw__in=['Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true']
        ).order_by('userid')
        
        logger.info(f"Found {all_users.count()} active users in database")
        
        # Filter users who have PerformContractAudit permission
        users_with_permission = []
        for user in all_users:
            user_id = user.userid
            
            # Check if user has PerformContractAudit permission
            has_permission = RBACTPRMUtils.check_contract_permission(user_id, 'PerformContractAudit')
            
            # Include user if they have PerformContractAudit permission
            if has_permission:
                full_name = f"{user.first_name} {user.last_name}".strip()
                display_name = full_name if full_name else user.username
                
                # Assign role based on department or user ID (for backward compatibility)
                dept_id = getattr(user, 'department_id', None)
                if dept_id == 1 or user_id % 2 == 1:
                    role = 'auditor'
                else:
                    role = 'reviewer'
                
                user_data = {
                    'user_id': user_id,
                    'username': user.username,
                    'name': display_name,
                    'email': user.email or f"user{user_id}@example.com",
                    'role': role,  # Default role for audit users
                    'department': getattr(user, 'department', 'Unknown'),
                }
                users_with_permission.append(user_data)
                logger.info(f"User with PerformContractAudit permission: {user_data}")
        
        logger.info(f"Returning {len(users_with_permission)} users with PerformContractAudit permission to frontend")
            
        return Response(users_with_permission)
            
    except Exception as e:
        # Log error and return empty list
        logger.error(f"Error fetching users with PerformContractAudit permission: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response(
            {
                'error': 'Failed to fetch users',
                'message': 'Unable to retrieve users with PerformContractAudit permission. Please try again later.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([PerformContractAuditPermission])
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
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([PerformContractAuditPermission])
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
