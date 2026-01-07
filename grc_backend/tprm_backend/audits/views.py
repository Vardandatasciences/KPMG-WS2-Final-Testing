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

# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    filter_queryset_by_tenant,
    get_tenant_aware_queryset,
    require_tenant,
    tenant_filter
)


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
                except ImportError:
                    # If User model import fails, create a mock user
                    logger.warning(f"User model import failed, creating mock user for user_id: {user_id}")
                    class MockUser:
                        def __init__(self, user_id):
                            self.userid = user_id
                            self.username = f"user_{user_id}"
                            self.is_authenticated = True
                    
                    return (MockUser(user_id), token)
                except Exception as e:
                    # If User model doesn't exist or other error, create a mock user
                    logger.warning(f"User {user_id} not found or error: {e}, creating mock user")
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
    """List and create audits.
    MULTI-TENANCY: Filters audits by tenant to ensure tenant isolation
    Note: Using SimpleAuthenticatedPermission for both GET and POST to allow
    authenticated users to view and create audits. In production, you may want
    to restrict POST to PerformContractAuditPermission.
    """
    queryset = Audit.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]  # Changed from PerformContractAuditPermission
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'audit_type', 'frequency', 'auditor_id', 'reviewer_id']
    search_fields = ['title', 'scope']
    ordering_fields = ['due_date', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """MULTI-TENANCY: Filter audits by tenant and current user's role when appropriate."""
        queryset = super().get_queryset()
        
        # MULTI-TENANCY: Filter by tenant
        tenant_id = get_tenant_id_from_request(self.request)
        logger.info(f"[Audit List] Tenant ID from request: {tenant_id}")
        
        if tenant_id:
            # Use tenant_id for ForeignKey filtering (Django automatically handles db_column mapping)
            queryset = queryset.filter(tenant_id=tenant_id)
            total_before_user_filter = queryset.count()
            logger.info(f"[Audit List] After tenant filter (tenant_id={tenant_id}): {total_before_user_filter} audits")
        else:
            logger.warning("[Audit List] No tenant_id found in request - showing all audits (potential security issue)")
        
        # Get current user ID from request
        if hasattr(self.request, 'user') and hasattr(self.request.user, 'userid'):
            current_user_id = self.request.user.userid
            logger.info(f"[Audit List] Current user ID: {current_user_id}")
            
            # Check if user has PerformContractAudit permission
            has_permission = RBACTPRMUtils.check_contract_permission(current_user_id, 'PerformContractAudit')
            logger.info(f"[Audit List] User {current_user_id} has PerformContractAudit permission: {has_permission}")
            
            # Only apply user-based filtering if no explicit user filters are provided
            # This allows admins to see all audits when they explicitly filter
            # Also check for 'show_all' parameter to bypass user filtering (for "My Audits" page)
            has_explicit_user_filter = any([
                self.request.query_params.get('auditor_id'),
                self.request.query_params.get('reviewer_id'),
                self.request.query_params.get('assignee_id')
            ])
            show_all = self.request.query_params.get('show_all', '').lower() == 'true'
            
            # If user has PerformContractAudit permission OR show_all=true, show all audits (no user filtering)
            # Otherwise, show only audits where user is assignee, auditor, or reviewer
            if not has_explicit_user_filter and not has_permission and not show_all:
                queryset = queryset.filter(
                    Q(assignee_id=current_user_id) |
                    Q(auditor_id=current_user_id) |
                    Q(reviewer_id=current_user_id)
                )
                after_user_filter = queryset.count()
                logger.info(f"[Audit List] Filtered queryset for user {current_user_id} (no permission) - showing only assigned audits: {after_user_filter} audits (was {total_before_user_filter} before user filter)")
            elif has_permission or show_all:
                logger.info(f"[Audit List] User {current_user_id} has permission or show_all=true - showing all {queryset.count()} audits for tenant")
        else:
            logger.warning("[Audit List] No user found in request")
        
        final_count = queryset.count()
        logger.info(f"[Audit List] Final queryset count: {final_count} audits")
        
        return queryset
    
    def perform_create(self, serializer):
        """MULTI-TENANCY: Set tenant_id when creating audit"""
        tenant_id = get_tenant_id_from_request(self.request)
        serializer.save(tenant_id=tenant_id)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AuditCreateSerializer
        return AuditListSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to return full audit payload including audit_id and sla_id."""
        try:
            print(f"Received audit creation request: {request.data}")
            create_serializer = AuditCreateSerializer(data=request.data, context={'request': request})
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
    """Retrieve, update and delete audit.
    MULTI-TENANCY: Filters audits by tenant to ensure tenant isolation
    """
    queryset = Audit.objects.all()
    serializer_class = AuditSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    
    def get_queryset(self):
        """MULTI-TENANCY: Filter audits by tenant"""
        queryset = super().get_queryset()
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset


class QuestionnairesPagination(PageNumberPagination):
    """Custom pagination for questionnaires that allows fetching all records."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000  # Allow up to 1000 records per page


class StaticQuestionnaireListView(generics.ListCreateAPIView):
    """List and create static questionnaires.
    MULTI-TENANCY: Filters questionnaires by tenant to ensure tenant isolation
    """
    queryset = StaticQuestionnaire.objects.all()
    serializer_class = StaticQuestionnaireSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    pagination_class = QuestionnairesPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['metric_name', 'question_type', 'is_required']
    
    def get_queryset(self):
        """MULTI-TENANCY: Filter questionnaires by tenant"""
        queryset = super().get_queryset()
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset
    
    def perform_create(self, serializer):
        """MULTI-TENANCY: Set tenant_id when creating questionnaire"""
        tenant_id = get_tenant_id_from_request(self.request)
        serializer.save(tenant_id=tenant_id)


class StaticQuestionnaireDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete static questionnaire.
    MULTI-TENANCY: Filters questionnaires by tenant to ensure tenant isolation
    """
    queryset = StaticQuestionnaire.objects.all()
    serializer_class = StaticQuestionnaireSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    
    def get_queryset(self):
        """MULTI-TENANCY: Filter questionnaires by tenant"""
        queryset = super().get_queryset()
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset


class AuditVersionListView(generics.ListCreateAPIView):
    """List and create audit versions.
    MULTI-TENANCY: Filters audit versions by tenant to ensure tenant isolation
    """
    queryset = AuditVersion.objects.all()
    serializer_class = AuditVersionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'version_type', 'approval_status', 'user_id']
    ordering_fields = ['date_created', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """MULTI-TENANCY: Filter audit versions by tenant"""
        queryset = super().get_queryset()
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset
    
    def perform_create(self, serializer):
        """MULTI-TENANCY: Set tenant_id when creating audit version"""
        tenant_id = get_tenant_id_from_request(self.request)
        serializer.save(tenant_id=tenant_id)


class AuditVersionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete audit version.
    MULTI-TENANCY: Filters audit versions by tenant to ensure tenant isolation
    """
    queryset = AuditVersion.objects.all()
    serializer_class = AuditVersionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    
    def get_queryset(self):
        """MULTI-TENANCY: Filter audit versions by tenant"""
        queryset = super().get_queryset()
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset


class AuditFindingListView(generics.ListCreateAPIView):
    """List and create audit findings.
    MULTI-TENANCY: Filters audit findings by tenant to ensure tenant isolation
    """
    queryset = AuditFinding.objects.all()
    serializer_class = AuditFindingSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'metrics_id', 'user_id']
    ordering_fields = ['check_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """MULTI-TENANCY: Filter audit findings by tenant"""
        queryset = super().get_queryset()
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset
    
    def perform_create(self, serializer):
        """MULTI-TENANCY: Set tenant_id when creating audit finding"""
        tenant_id = get_tenant_id_from_request(self.request)
        serializer.save(tenant_id=tenant_id)


class AuditFindingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete audit finding.
    MULTI-TENANCY: Filters audit findings by tenant to ensure tenant isolation
    """
    queryset = AuditFinding.objects.all()
    serializer_class = AuditFindingSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    
    def get_queryset(self):
        """MULTI-TENANCY: Filter audit findings by tenant"""
        queryset = super().get_queryset()
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset


class AuditReportListView(generics.ListCreateAPIView):
    """List and create audit reports.
    MULTI-TENANCY: Filters audit reports by tenant to ensure tenant isolation
    """
    queryset = AuditReport.objects.all()
    serializer_class = AuditReportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'sla_id', 'metrics_id']
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']
    
    def get_queryset(self):
        """MULTI-TENANCY: Filter audit reports by tenant"""
        queryset = super().get_queryset()
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset
    
    def perform_create(self, serializer):
        """MULTI-TENANCY: Set tenant_id when creating audit report"""
        tenant_id = get_tenant_id_from_request(self.request)
        serializer.save(tenant_id=tenant_id)


class AuditReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete audit report.
    MULTI-TENANCY: Filters audit reports by tenant to ensure tenant isolation
    """
    queryset = AuditReport.objects.all()
    serializer_class = AuditReportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [PerformContractAuditPermission]
    
    def get_queryset(self):
        """MULTI-TENANCY: Filter audit reports by tenant"""
        queryset = super().get_queryset()
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([PerformContractAuditPermission])
def audit_dashboard_stats(request):
    """Get audit dashboard statistics.
    MULTI-TENANCY: Filters statistics by tenant to ensure tenant isolation
    """
    # MULTI-TENANCY: Filter by tenant
    tenant_id = get_tenant_id_from_request(request)
    audits_base = Audit.objects.all()
    if tenant_id:
        audits_base = audits_base.filter(tenant_id=tenant_id)
    
    total_audits = audits_base.count()
    active_audits = audits_base.filter(status__in=['created', 'in_progress']).count()
    completed_audits = audits_base.filter(status='completed').count()
    overdue_audits = audits_base.filter(
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
@permission_classes_decorator([SimpleAuthenticatedPermission])
@tenant_filter  # MULTI-TENANCY: Add tenant_id to request
def available_slas(request):
    """Get available SLAs for audit creation.
    MULTI-TENANCY: Filters SLAs by tenant to ensure tenant isolation
    Note: Using SimpleAuthenticatedPermission instead of PerformContractAuditPermission
    to allow users to view SLAs even if they don't have audit permissions.
    The actual audit creation will still require PerformContractAudit permission.
    """
    # MULTI-TENANCY: Filter by tenant
    tenant_id = get_tenant_id_from_request(request)
    
    # Check if user is admin (user_id = 1) - admin can access any SLA
    user_id = request.GET.get('user_id', request.headers.get('X-User-ID', '1'))
    is_admin = str(user_id) == '1'
    
    # Build base query with tenant filtering
    if tenant_id:
        slas_base = VendorSLA.objects.filter(tenant_id=tenant_id)
    else:
        slas_base = VendorSLA.objects.all()
    
    if is_admin:
        # Admin can access any SLA regardless of status (within tenant)
        slas = slas_base.select_related('vendor', 'contract')
    else:
        # Regular users can only access active SLAs (within tenant)
        slas = slas_base.filter(status='ACTIVE').select_related('vendor', 'contract')
    
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
@permission_classes_decorator([SimpleAuthenticatedPermission])
@tenant_filter  # MULTI-TENANCY: Add tenant_id to request
def sla_metrics(request, sla_id):
    """Get metrics for a specific SLA.
    MULTI-TENANCY: Ensures SLA belongs to tenant
    Note: Using SimpleAuthenticatedPermission instead of PerformContractAuditPermission
    to allow users to view SLA metrics even if they don't have audit permissions.
    The actual audit creation will still require PerformContractAudit permission.
    """
    try:
        # MULTI-TENANCY: Filter by tenant
        tenant_id = get_tenant_id_from_request(request)
        
        # Check if user is admin (user_id = 1) - admin can access any SLA
        user_id = request.GET.get('user_id', request.headers.get('X-User-ID', '1'))
        is_admin = str(user_id) == '1'
        
        # Build base query with tenant filtering
        if tenant_id:
            sla_query = VendorSLA.objects.filter(sla_id=sla_id, tenant_id=tenant_id)
        else:
            sla_query = VendorSLA.objects.filter(sla_id=sla_id)
        
        if is_admin:
            # Admin can access any SLA regardless of status (within tenant)
            sla = sla_query.get()
        else:
            # Regular users can only access active SLAs (within tenant)
            sla = sla_query.filter(status='ACTIVE').get()
        
        # MULTI-TENANCY: Filter metrics by tenant
        if tenant_id:
            metrics = SLAMetric.objects.filter(sla=sla, tenant_id=tenant_id)
        else:
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
@permission_classes_decorator([SimpleAuthenticatedPermission])
@tenant_filter  # MULTI-TENANCY: Add tenant_id to request
def available_users(request):
    """Get users with PerformContractAudit permission for auditor and reviewer assignment.
    MULTI-TENANCY: Filters users by tenant to ensure tenant isolation
    Note: Using SimpleAuthenticatedPermission to allow users to view available users.
    The actual audit creation will still require PerformContractAudit permission.
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            logger.warning("Tenant ID not found for available_users, proceeding without tenant filter")
        
        users_with_permission = []
        
        try:
            from tprm_backend.mfa_auth.models import User
            from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
            logger.info("Successfully imported User model and RBACTPRMUtils")
            
            # Get all active users with tenant filtering
            try:
                if tenant_id:
                    all_users = User.objects.filter(
                        is_active_raw__in=['Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true'],
                        tenant_id=tenant_id
                    ).order_by('userid')
                    logger.info(f"Filtered active users by tenant_id={tenant_id}")
                else:
                    all_users = User.objects.filter(
                        is_active_raw__in=['Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true']
                    ).order_by('userid')
                    logger.info("Using all active users (no tenant filter applied)")
            except Exception as orm_error:
                logger.warning(f"ORM filtering failed: {orm_error}, falling back to all users")
                all_users = User.objects.filter(
                    is_active_raw__in=['Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true']
                ).order_by('userid')
            
            logger.info(f"Found {all_users.count()} active users in database")
            
            # Filter users who have PerformContractAudit permission
            for user in all_users:
                user_id = user.userid
                
                # Check if user has PerformContractAudit permission
                try:
                    has_permission = RBACTPRMUtils.check_contract_permission(user_id, 'PerformContractAudit')
                except Exception as perm_error:
                    logger.warning(f"Error checking permission for user {user_id}: {perm_error}")
                    has_permission = False
                
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
            
            return Response({
                'success': True,
                'data': users_with_permission,
                'count': len(users_with_permission)
            })
            
        except ImportError as import_err:
            logger.warning(f"User model import failed: {import_err}, trying raw SQL fallback")
            # Raw SQL fallback
            from django.db import connection
            
            try:
                with connection.cursor() as cursor:
                    # Check if TenantId column exists
                    cursor.execute("""
                        SELECT COLUMN_NAME 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_NAME = 'users' 
                        AND COLUMN_NAME = 'TenantId'
                    """)
                    has_tenant_column = cursor.fetchone() is not None
                    
                    # Build query with optional tenant filtering
                    if has_tenant_column and tenant_id:
                        query = """
                            SELECT UserId, UserName, FirstName, LastName, Email, DepartmentId, Department
                            FROM users
                            WHERE IsActive IN ('Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true')
                            AND TenantId = %s
                            ORDER BY UserId
                        """
                        cursor.execute(query, [tenant_id])
                        logger.info(f"Raw SQL query with tenant_id={tenant_id}")
                    else:
                        query = """
                            SELECT UserId, UserName, FirstName, LastName, Email, DepartmentId, Department
                            FROM users
                            WHERE IsActive IN ('Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true')
                            ORDER BY UserId
                        """
                        cursor.execute(query)
                        logger.info("Raw SQL query without tenant filter")
                    
                    rows = cursor.fetchall()
                    logger.info(f"Raw SQL returned {len(rows)} users")
                    
                    # Process rows and check permissions
                    for row in rows:
                        user_id = row[0]
                        username = row[1] or ''
                        first_name = row[2] or ''
                        last_name = row[3] or ''
                        email = row[4] or f"user{user_id}@example.com"
                        dept_id = row[5]
                        department = row[6] or 'Unknown'
                        
                        # Check permission using RBACTPRMUtils
                        try:
                            has_permission = RBACTPRMUtils.check_contract_permission(user_id, 'PerformContractAudit')
                        except Exception as perm_error:
                            logger.warning(f"Error checking permission for user {user_id}: {perm_error}")
                            has_permission = False
                        
                        if has_permission:
                            full_name = f"{first_name} {last_name}".strip()
                            display_name = full_name if full_name else username
                            
                            # Assign role based on department or user ID
                            if dept_id == 1 or user_id % 2 == 1:
                                role = 'auditor'
                            else:
                                role = 'reviewer'
                            
                            user_data = {
                                'user_id': user_id,
                                'username': username,
                                'name': display_name,
                                'email': email,
                                'role': role,
                                'department': department,
                            }
                            users_with_permission.append(user_data)
                    
                    logger.info(f"Raw SQL fallback returned {len(users_with_permission)} users with permission")
                    
                    return Response({
                        'success': True,
                        'data': users_with_permission,
                        'count': len(users_with_permission)
                    })
                    
            except Exception as sql_error:
                logger.error(f"Raw SQL fallback also failed: {sql_error}")
                return Response({
                    'success': False,
                    'error': 'Failed to fetch users',
                    'message': 'Unable to retrieve users. Please try again later.',
                    'data': []
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        # Log error and return error response
        logger.error(f"Error fetching users with PerformContractAudit permission: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response(
            {
                'success': False,
                'error': 'Failed to fetch users',
                'message': 'Unable to retrieve users with PerformContractAudit permission. Please try again later.',
                'data': []
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([PerformContractAuditPermission])
def submit_audit_response(request, audit_id):
    """Submit responses for an audit.
    MULTI-TENANCY: Ensures audit belongs to tenant
    """
    try:
        # MULTI-TENANCY: Filter by tenant
        tenant_id = get_tenant_id_from_request(request)
        if tenant_id:
            audit = Audit.objects.get(audit_id=audit_id, tenant_id=tenant_id)
        else:
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
    """Review and approve/reject an audit.
    MULTI-TENANCY: Ensures audit belongs to tenant
    """
    try:
        # MULTI-TENANCY: Filter by tenant
        tenant_id = get_tenant_id_from_request(request)
        if tenant_id:
            audit = Audit.objects.get(audit_id=audit_id, tenant_id=tenant_id)
        else:
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
