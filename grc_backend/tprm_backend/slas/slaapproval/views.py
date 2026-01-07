from rest_framework.decorators import api_view, authentication_classes, permission_classes as permission_classes_decorator
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils.dateparse import parse_datetime
from django.conf import settings
import logging
import jwt

# RBAC imports
from tprm_backend.rbac.tprm_decorators import rbac_sla_required, rbac_contract_required
from tprm_backend.rbac.tprm_utils import RBACTPRMUtils

# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import get_tenant_id_from_request

from .models import SLAApproval
from .serializers import (
    SLAApprovalAssignmentSerializer,
    SLAApprovalCreateAssignmentSerializer,
    SLAApprovalBulkCreateSerializer,
    SLAApprovalStatsSerializer
)

logger = logging.getLogger(__name__)


def get_authenticated_user_id(request):
    """
    Helper to extract the authenticated user's ID.
    """
    try:
        if hasattr(request, 'user') and hasattr(request.user, 'userid'):
            return int(request.user.userid)
    except Exception:
        pass

    try:
        user_id = RBACTPRMUtils.get_user_id_from_request(request)
        if user_id is not None:
            return int(user_id)
    except Exception:
        logger.debug("Unable to extract user id from RBAC utils", exc_info=True)

    return None


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


class SimpleAuthenticatedPermission(BasePermission):
    """Custom permission class that checks for authenticated users"""
    def has_permission(self, request, view):
        # Check if user is authenticated
        return bool(
            request.user and 
            hasattr(request.user, 'userid') and
            getattr(request.user, 'is_authenticated', False)
        )


@api_view(['GET'])
def health_check(request):
    """Simple health check endpoint for SLA approvals"""
    return Response({
        'success': True,
        'message': 'SLA Approval API is running',
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContract')
def approval_list(request):
    """
    List all SLA approvals with filtering and pagination
    MULTI-TENANCY: Filters approvals by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        # Get query parameters
        assignee_id = request.GET.get('assignee_id')
        object_type = request.GET.get('object_type')
        status_filter = request.GET.get('status')
        is_overdue = request.GET.get('is_overdue')
        workflow_id = request.GET.get('workflow_id')
        search = request.GET.get('search', '')
        ordering = request.GET.get('ordering', '-created_at')
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        
        logger.info(f"SLA approval list request - assignee_id: {assignee_id}, tenant_id: {tenant_id}, filters: {request.GET}")
        
        current_user_id = get_authenticated_user_id(request)

        # MULTI-TENANCY: Filter by tenant_id through SLA relationship FIRST
        # Get all SLA IDs that belong to this tenant
        from tprm_backend.slas.models import VendorSLA
        if tenant_id:
            tenant_sla_ids = list(VendorSLA.objects.filter(tenant_id=tenant_id).values_list('sla_id', flat=True))
            logger.info(f"[SLA Approval List] Found {len(tenant_sla_ids)} SLAs for tenant {tenant_id}")
            logger.info(f"[SLA Approval List] Tenant SLA IDs: {tenant_sla_ids[:10]}..." if len(tenant_sla_ids) > 10 else f"[SLA Approval List] Tenant SLA IDs: {tenant_sla_ids}")
        else:
            tenant_sla_ids = None
            logger.warning("[SLA Approval List] No tenant_id found for SLA approval list request")

        # MULTI-TENANCY: Start with tenant-filtered approvals (filter by tenant FIRST)
        if tenant_id and tenant_sla_ids is not None:
            queryset = SLAApproval.objects.filter(sla_id__in=tenant_sla_ids)
            logger.info(f"[SLA Approval List] Started with {queryset.count()} approvals for tenant {tenant_id}")
        else:
            queryset = SLAApproval.objects.none()
            logger.warning(f"[SLA Approval List] Tenant {tenant_id} has no SLAs - returning empty queryset")
        
        # THEN filter by assignee_id if explicitly provided (this narrows down the tenant-filtered results)
        # Only filter by assignee_id if it's explicitly provided in the request
        # If not provided, show all approvals for the tenant (admin view)
        # But only if we have tenant-filtered results
        if queryset.exists():
            if assignee_id and assignee_id != 'null' and assignee_id != '':
                # Explicitly filter by provided assignee_id
                queryset = queryset.filter(assignee_id=assignee_id)
                logger.info(f"[SLA Approval List] Filtered by assignee_id={assignee_id}: {queryset.count()} approvals")
            else:
                # No assignee_id filter - show all approvals for tenant (admin view)
                logger.info(f"[SLA Approval List] No assignee filter - showing all {queryset.count()} approvals for tenant {tenant_id}")
        
        # Apply additional filters
        if object_type:
            queryset = queryset.filter(object_type=object_type)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if is_overdue == 'true':
            queryset = queryset.filter(
                status__in=['ASSIGNED', 'IN_PROGRESS'],
                due_date__lt=timezone.now()
            )
        
        if workflow_id:
            queryset = queryset.filter(workflow_id=workflow_id)
        
        if search:
            queryset = queryset.filter(
                Q(workflow_name__icontains=search) |
                Q(assigner_name__icontains=search) |
                Q(assignee_name__icontains=search) |
                Q(comment_text__icontains=search)
            )
        
        # Apply ordering
        queryset = queryset.order_by(ordering)
        
        logger.info(f"Query results count: {queryset.count()}")
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = SLAApprovalAssignmentSerializer(page_obj.object_list, many=True)
        
        logger.info(f"Serialized data count: {len(serializer.data)}")
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing SLA approvals: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContract')
def approval_detail(request, pk):
    """
    Get details of a specific SLA approval
    MULTI-TENANCY: Verifies approval belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        approval = SLAApproval.objects.get(approval_id=pk)
        
        # MULTI-TENANCY: Verify approval belongs to tenant through SLA relationship
        if tenant_id:
            from tprm_backend.slas.models import VendorSLA
            sla = VendorSLA.objects.filter(sla_id=approval.sla_id, tenant_id=tenant_id).first()
            if not sla:
                logger.warning(f"Approval {pk} SLA {approval.sla_id} not found for tenant {tenant_id}")
                return Response({'error': 'Approval not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SLAApprovalAssignmentSerializer(approval, context={'request': request})
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except SLAApproval.DoesNotExist:
        return Response({'error': 'Approval not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting SLA approval detail: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContract')
def approval_create(request):
    """
    Create a new SLA approval
    """
    try:
        # Set assigned_date if not provided
        data = request.data.copy()
        if not data.get('assigned_date'):
            data['assigned_date'] = timezone.now()
        
        # Auto-populate assigner_name and assignee_name from user IDs
        if data.get('assigner_id') and not data.get('assigner_name'):
            data['assigner_name'] = f"User {data['assigner_id']}"
        
        if data.get('assignee_id') and not data.get('assignee_name'):
            data['assignee_name'] = f"User {data['assignee_id']}"
        
        serializer = SLAApprovalCreateAssignmentSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            approval = serializer.save()
            
            # Update SLA status to UNDER_REVIEW if it's a SLA creation approval
            if approval.object_type == 'SLA_CREATION' and approval.sla_id:
                try:
                    from tprm_backend.slas.models import VendorSLA
                    from tprm_backend.core.tenant_utils import get_tenant_id_from_request
                    
                    # MULTI-TENANCY: Filter by tenant_id when getting SLA
                    tenant_id = get_tenant_id_from_request(request)
                    sla_query = VendorSLA.objects.filter(sla_id=approval.sla_id)
                    if tenant_id:
                        sla_query = sla_query.filter(tenant_id=tenant_id)
                    
                    sla = sla_query.first()
                    if sla:
                        if sla.status == 'PENDING':
                            sla.status = 'PENDING'  # Keep as PENDING until approved
                            sla.save()
                            logger.info(f"Updated SLA {approval.sla_id} status to PENDING")
                    else:
                        logger.warning(f"SLA {approval.sla_id} not found for status update (tenant_id: {tenant_id})")
                except Exception as e:
                    logger.warning(f"SLA {approval.sla_id} not found for status update: {str(e)}")
            
            response_serializer = SLAApprovalAssignmentSerializer(approval, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'SLA approval created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error creating SLA approval: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContract')
def approval_bulk_create(request):
    """
    Create multiple SLA approvals at once
    """
    try:
        serializer = SLAApprovalBulkCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            approvals = serializer.save()
            
            # Update SLA statuses to PENDING for SLA creation approvals
            from tprm_backend.core.tenant_utils import get_tenant_id_from_request
            tenant_id = get_tenant_id_from_request(request)
            
            for approval in approvals:
                if approval.object_type == 'SLA_CREATION' and approval.sla_id:
                    try:
                        from tprm_backend.slas.models import VendorSLA
                        
                        # MULTI-TENANCY: Filter by tenant_id when getting SLA
                        sla_query = VendorSLA.objects.filter(sla_id=approval.sla_id)
                        if tenant_id:
                            sla_query = sla_query.filter(tenant_id=tenant_id)
                        
                        sla = sla_query.first()
                        if not sla:
                            logger.warning(f"SLA {approval.sla_id} not found for status update (tenant_id: {tenant_id})")
                            continue
                        if sla.status == 'PENDING':
                            sla.status = 'PENDING'  # Keep as PENDING until approved
                            sla.save()
                            logger.info(f"Updated SLA {approval.sla_id} status to PENDING")
                    except:
                        logger.warning(f"SLA {approval.sla_id} not found for status update")
            
            response_serializer = SLAApprovalAssignmentSerializer(approvals, many=True, context={'request': request})
            
            return Response({
                'success': True,
                'message': f'{len(approvals)} SLA approvals created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error creating bulk SLA approvals: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContract')
def approval_update(request, pk):
    """
    Update a SLA approval (status, comments)
    """
    try:
        approval = SLAApproval.objects.get(approval_id=pk)
        current_user_id = get_authenticated_user_id(request)
        
        # MULTI-TENANCY: Verify the approval belongs to the current tenant
        tenant_id = get_tenant_id_from_request(request)
        if tenant_id:
            from tprm_backend.slas.models import VendorSLA
            sla_query = VendorSLA.objects.filter(sla_id=approval.sla_id)
            if tenant_id:
                sla_query = sla_query.filter(tenant_id=tenant_id)
            if not sla_query.exists():
                return Response(
                    {'error': 'Approval not found for your tenant'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Check if user has ApproveContract permission (decorator already checked, but verify)
        # Users with ApproveContract permission can update any approval
        has_permission = False
        if current_user_id:
            has_permission = RBACTPRMUtils.check_contract_permission(current_user_id, 'ApproveContract')
        
        # Allow update if:
        # 1. User is the assigned approver (assignee_id), OR
        # 2. User has ApproveContract permission
        if current_user_id is None:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        is_assignee = current_user_id == int(approval.assignee_id)
        
        if not is_assignee and not has_permission:
            return Response(
                {'error': 'Only the assigned approver or users with ApproveContract permission can update this SLA approval'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logger.info(f"[Approval Update] User {current_user_id} updating approval {pk} (is_assignee: {is_assignee}, has_permission: {has_permission})")
        
        # Only allow updating status and comment_text
        allowed_fields = ['status', 'comment_text']
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = SLAApprovalAssignmentSerializer(approval, data=update_data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'SLA approval updated successfully',
                'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except SLAApproval.DoesNotExist:
        return Response({'error': 'Approval not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error updating SLA approval: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContract')
def approval_delete(request, pk):
    """
    Delete a SLA approval
    """
    try:
        approval = SLAApproval.objects.get(approval_id=pk)
        approval.delete()
        
        return Response({
            'success': True,
            'message': 'SLA approval deleted successfully'
        })
        
    except SLAApproval.DoesNotExist:
        return Response({'error': 'Approval not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting SLA approval: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContract')
def approval_stats(request):
    """
    Get SLA approval statistics
    MULTI-TENANCY: Filters statistics by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        # MULTI-TENANCY: Filter by tenant_id through SLA relationship
        from tprm_backend.slas.models import VendorSLA
        if tenant_id:
            tenant_sla_ids = list(VendorSLA.objects.filter(tenant_id=tenant_id).values_list('sla_id', flat=True))
            queryset = SLAApproval.objects.filter(sla_id__in=tenant_sla_ids)
            logger.info(f"Filtered approval stats by tenant {tenant_id} - {len(tenant_sla_ids)} SLAs")
        else:
            queryset = SLAApproval.objects.all()
            logger.warning("No tenant_id found for approval stats request")
        
        # Apply filters if provided
        assignee_id = request.GET.get('assignee_id')
        object_type = request.GET.get('object_type')
        workflow_id = request.GET.get('workflow_id')
        
        if assignee_id:
            queryset = queryset.filter(assignee_id=assignee_id)
        if object_type:
            queryset = queryset.filter(object_type=object_type)
        if workflow_id:
            queryset = queryset.filter(workflow_id=workflow_id)
        
        # Calculate statistics
        total_approvals = queryset.count()
        pending_approvals = queryset.filter(status__in=['ASSIGNED', 'IN_PROGRESS']).count()
        overdue_approvals = queryset.filter(
            status__in=['ASSIGNED', 'IN_PROGRESS'],
            due_date__lt=timezone.now()
        ).count()
        completed_approvals = queryset.filter(status__in=['COMMENTED', 'SKIPPED', 'APPROVED', 'REJECTED']).count()
        
        # Status breakdown
        status_breakdown = dict(queryset.values('status').annotate(count=Count('status')).values_list('status', 'count'))
        
        # Type breakdown
        type_breakdown = dict(queryset.values('object_type').annotate(count=Count('object_type')).values_list('object_type', 'count'))
        
        # Assignee breakdown
        assignee_breakdown = dict(queryset.values('assignee_name').annotate(count=Count('assignee_name')).values_list('assignee_name', 'count'))
        
        # Average completion time (for completed approvals)
        completed_queryset = queryset.filter(
            status__in=['COMMENTED', 'SKIPPED', 'APPROVED', 'REJECTED'],
            assigned_date__isnull=False,
            updated_at__isnull=False
        )
        
        if completed_queryset.exists():
            avg_completion_time = completed_queryset.aggregate(
                avg_time=Avg('updated_at__date') - Avg('assigned_date__date')
            )['avg_time']
            avg_completion_time = avg_completion_time.days if avg_completion_time else 0
        else:
            avg_completion_time = 0
        
        # Overdue percentage
        overdue_percentage = (overdue_approvals / total_approvals * 100) if total_approvals > 0 else 0
        
        stats_data = {
            'total_approvals': total_approvals,
            'pending_approvals': pending_approvals,
            'overdue_approvals': overdue_approvals,
            'completed_approvals': completed_approvals,
            'approvals_by_status': status_breakdown,
            'approvals_by_type': type_breakdown,
            'approvals_by_assignee': assignee_breakdown,
            'average_completion_time': avg_completion_time,
            'overdue_percentage': round(overdue_percentage, 2)
        }
        
        serializer = SLAApprovalStatsSerializer(stats_data)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error getting SLA approval stats: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContract')
def sla_approvals_list(request, sla_id):
    """
    Get all approvals for a specific SLA
    """
    try:
        # Verify SLA exists
        try:
            from tprm_backend.slas.models import VendorSLA
            from tprm_backend.core.tenant_utils import get_tenant_id_from_request
            
            # MULTI-TENANCY: Filter by tenant_id when getting SLA
            tenant_id = get_tenant_id_from_request(request)
            sla_query = VendorSLA.objects.filter(sla_id=sla_id)
            if tenant_id:
                sla_query = sla_query.filter(tenant_id=tenant_id)
            
            sla = sla_query.first()
            if not sla:
                return Response({'error': f'SLA not found (tenant_id: {tenant_id})'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting SLA {sla_id}: {str(e)}")
            return Response({'error': 'SLA not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get approvals for this SLA
        approvals = SLAApproval.objects.filter(sla_id=sla_id)
        
        # Apply additional filters
        status_filter = request.GET.get('status')
        if status_filter:
            approvals = approvals.filter(status=status_filter)
        
        # Serialize data
        serializer = SLAApprovalAssignmentSerializer(approvals, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'sla_info': {
                'sla_id': sla.sla_id,
                'sla_name': sla.sla_name,
                'sla_type': sla.sla_type,
                'status': sla.status
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting SLA approvals: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContract')
def get_assigner_approvals(request):
    """
    Get SLA approvals where the current user is the assigner (for review)
    Admin view: if no assigner_id provided, return all approvals
    MULTI-TENANCY: Filters approvals by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        # MULTI-TENANCY: Filter by tenant_id through SLA relationship
        from tprm_backend.slas.models import VendorSLA
        if tenant_id:
            tenant_sla_ids = list(VendorSLA.objects.filter(tenant_id=tenant_id).values_list('sla_id', flat=True))
            logger.info(f"Found {len(tenant_sla_ids)} SLAs for tenant {tenant_id}")
        else:
            tenant_sla_ids = None
            logger.warning("No tenant_id found for get_assigner_approvals request")
        
        # Get query parameters
        assigner_id = request.GET.get('assigner_id')
        status_filter = request.GET.get('status')
        search = request.GET.get('search', '')
        ordering = request.GET.get('ordering', '-created_at')
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        
        current_user_id = get_authenticated_user_id(request)

        # Build query - if assigner_id is provided, filter by assigner, otherwise use current user
        if assigner_id:
            queryset = SLAApproval.objects.filter(assigner_id=assigner_id)
        elif current_user_id is not None:
            queryset = SLAApproval.objects.filter(assigner_id=current_user_id)
        else:
            queryset = SLAApproval.objects.none()
        
        # MULTI-TENANCY: Filter by tenant_id through SLA relationship
        if tenant_id and tenant_sla_ids is not None:
            queryset = queryset.filter(sla_id__in=tenant_sla_ids)
            logger.info(f"Filtered assigner approvals by tenant {tenant_id} - {queryset.count()} approvals found")
        
        # Apply additional filters
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if search:
            queryset = queryset.filter(
                Q(workflow_name__icontains=search) |
                Q(assignee_name__icontains=search) |
                Q(comment_text__icontains=search)
            )
        
        # Apply ordering
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = SLAApprovalAssignmentSerializer(page_obj.object_list, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting assigner approvals: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContract')
def available_users(request):
    """
    Get users with ApproveContract permission for SLA approval assignment
    Returns users who can be assigned as assigner or assignee for SLA approvals
    MULTI-TENANCY: Filters users by tenant when available, falls back to all users if tenant not found
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request (optional - function works without it)
        from tprm_backend.core.tenant_utils import get_tenant_id_from_request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            logger.info("Tenant ID not found for available_users, proceeding without tenant filter (fallback mode)")
        
        # Import required models with error handling
        users_with_permission = []
        try:
            from tprm_backend.mfa_auth.models import User
            logger.info("Successfully imported User model")
            
            # Get all active users (filter by is_active_raw which can be 'Y', 'YES', '1', 'TRUE')
            # MULTI-TENANCY: Try filtering by tenant_id first
            try:
                if tenant_id:
                    all_users = User.objects.filter(
                        is_active_raw__in=['Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true'],
                        tenant_id=tenant_id
                    ).order_by('userid')
                    logger.info(f"Filtered users by tenant_id={tenant_id}")
                else:
                    all_users = User.objects.filter(
                        is_active_raw__in=['Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true']
                    ).order_by('userid')
                    logger.info("Using all active users (no tenant filter)")
            except Exception as filter_error:
                logger.warning(f"Filtering by tenant_id failed: {filter_error}, trying without tenant filter")
                all_users = User.objects.filter(
                    is_active_raw__in=['Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true']
                ).order_by('userid')
                logger.info("Using all active users (fallback)")
            
            logger.info(f"Found {all_users.count()} active users in database")
            
            # Filter users who have ApproveContract permission
            for user in all_users:
                user_id = user.userid
                
                # Check if user has ApproveContract permission
                has_approve_permission = RBACTPRMUtils.check_contract_permission(user_id, 'ApproveContract')
                
                if has_approve_permission:
                    full_name = f"{user.first_name} {user.last_name}".strip()
                    display_name = full_name if full_name else user.username
                    
                    user_data = {
                        'user_id': user_id,
                        'username': user.username,
                        'name': display_name,
                        'display_name': display_name,
                        'role': 'approver'
                    }
                    users_with_permission.append(user_data)
                    logger.info(f"User with ApproveContract permission: {user_data}")
            
            logger.info(f"Returning {len(users_with_permission)} users with ApproveContract permission to frontend")
            
        except ImportError as import_err:
            logger.warning(f"User model import failed: {import_err}, trying raw SQL fallback")
            # Fallback to raw SQL if import fails
            from django.db import connection
            
            with connection.cursor() as cursor:
                try:
                    if tenant_id:
                        cursor.execute(
                            "SELECT UserId, UserName, FirstName, LastName, Email, IsActive FROM users WHERE IsActive IN ('Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true') AND TenantId = %s ORDER BY UserId",
                            [tenant_id]
                        )
                        logger.info(f"Executed raw SQL with TenantId filter for tenant_id={tenant_id}")
                    else:
                        cursor.execute(
                            "SELECT UserId, UserName, FirstName, LastName, Email, IsActive FROM users WHERE IsActive IN ('Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true') ORDER BY UserId"
                        )
                        logger.info("Executed raw SQL without TenantId filter")
                except Exception as sql_filter_error:
                    logger.warning(f"Raw SQL filtering by TenantId failed: {sql_filter_error}, trying without TenantId")
                    cursor.execute(
                        "SELECT UserId, UserName, FirstName, LastName, Email, IsActive FROM users WHERE IsActive IN ('Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true') ORDER BY UserId"
                    )
                    logger.info("Executed raw SQL without TenantId filter (fallback)")
                
                for row in cursor.fetchall():
                    user_id, username, first_name, last_name, email, is_active = row
                    if is_active and is_active.upper() in ['Y', 'YES', '1', 'TRUE']:
                        # Check if user has ApproveContract permission
                        has_approve_permission = RBACTPRMUtils.check_contract_permission(user_id, 'ApproveContract')
                        
                        if has_approve_permission:
                            full_name = f"{first_name or ''} {last_name or ''}".strip()
                            display_name = full_name if full_name else (username or f"User {user_id}")
                            
                            user_data = {
                                'user_id': user_id,
                                'username': username or f"user_{user_id}",
                                'name': display_name,
                                'display_name': display_name,
                                'role': 'approver'
                            }
                            users_with_permission.append(user_data)
            
            logger.info(f"Returning {len(users_with_permission)} users from raw SQL fallback")
        
        return Response({
            'success': True,
            'data': users_with_permission,
            'count': len(users_with_permission)
        })
        
    except Exception as e:
        # Log error and return empty list
        logger.error(f"Error fetching users with ApproveContract permission: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response(
            {
                'success': False,
                'error': 'Failed to fetch users',
                'message': 'Unable to retrieve users with ApproveContract permission. Please try again later.',
                'data': []
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContract')
@rbac_sla_required('ActivateDeactivateSLA')
def approve_sla(request, approval_id):
    """
    Approve a SLA after review
    """
    try:
        # Get the approval
        try:
            approval = SLAApproval.objects.get(approval_id=approval_id)
        except SLAApproval.DoesNotExist:
            return Response({'error': 'Approval not found'}, status=status.HTTP_404_NOT_FOUND)
        
        current_user_id = get_authenticated_user_id(request)
        
        # MULTI-TENANCY: Verify the approval belongs to the current tenant
        tenant_id = get_tenant_id_from_request(request)
        if tenant_id:
            from tprm_backend.slas.models import VendorSLA
            sla_query = VendorSLA.objects.filter(sla_id=approval.sla_id)
            if tenant_id:
                sla_query = sla_query.filter(tenant_id=tenant_id)
            if not sla_query.exists():
                return Response(
                    {'error': 'Approval not found for your tenant'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Check if user has ApproveContract permission
        # Users with ApproveContract permission can approve any approval
        has_permission = False
        if current_user_id:
            has_permission = RBACTPRMUtils.check_contract_permission(current_user_id, 'ApproveContract')
        
        # Allow approval if:
        # 1. User is the assigned approver (assignee_id), OR
        # 2. User has ApproveContract permission
        if current_user_id is None:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        is_assignee = current_user_id == int(approval.assignee_id)
        
        if not is_assignee and not has_permission:
            return Response(
                {'error': 'Only the assigned approver or users with ApproveContract permission can approve this SLA'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logger.info(f"[Approve SLA] User {current_user_id} approving approval {approval_id} (is_assignee: {is_assignee}, has_permission: {has_permission})")
        
        # Update approval status to APPROVED
        approval.status = 'APPROVED'
        approval.approval_status = 'APPROVED'
        approval.save()
        
        # Update SLA status to APPROVED
        if approval.sla_id:
            try:
                from tprm_backend.slas.models import VendorSLA
                
                # MULTI-TENANCY: Filter by tenant_id when getting SLA
                # tenant_id already retrieved above (line 892)
                sla_query = VendorSLA.objects.filter(sla_id=approval.sla_id)
                if tenant_id:
                    sla_query = sla_query.filter(tenant_id=tenant_id)
                
                sla = sla_query.first()
                if sla:
                    sla.status = 'ACTIVE'
                    sla.approval_status = 'APPROVED'
                    sla.save()
                    logger.info(f"SLA {approval.sla_id} approved (tenant_id: {tenant_id})")
                else:
                    logger.warning(f"SLA {approval.sla_id} not found for approval (tenant_id: {tenant_id})")
            except Exception as e:
                logger.warning(f"SLA {approval.sla_id} not found for approval: {str(e)}")
        
        # Serialize updated approval
        serializer = SLAApprovalAssignmentSerializer(approval, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'SLA approved successfully',
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error approving SLA: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes_decorator([SimpleAuthenticatedPermission])
@rbac_contract_required('RejectContract')
@rbac_sla_required('ActivateDeactivateSLA')
def reject_sla(request, approval_id):
    """
    Reject a SLA after review
    """
    try:
        # Get the approval
        try:
            approval = SLAApproval.objects.get(approval_id=approval_id)
        except SLAApproval.DoesNotExist:
            return Response({'error': 'Approval not found'}, status=status.HTTP_404_NOT_FOUND)
        
        current_user_id = get_authenticated_user_id(request)
        
        # MULTI-TENANCY: Verify the approval belongs to the current tenant
        tenant_id = get_tenant_id_from_request(request)
        if tenant_id:
            from tprm_backend.slas.models import VendorSLA
            sla_query = VendorSLA.objects.filter(sla_id=approval.sla_id)
            if tenant_id:
                sla_query = sla_query.filter(tenant_id=tenant_id)
            if not sla_query.exists():
                return Response(
                    {'error': 'Approval not found for your tenant'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Check if user has RejectContract or ApproveContract permission
        # Users with these permissions can reject any approval
        has_reject_permission = False
        has_approve_permission = False
        if current_user_id:
            has_reject_permission = RBACTPRMUtils.check_contract_permission(current_user_id, 'RejectContract')
            has_approve_permission = RBACTPRMUtils.check_contract_permission(current_user_id, 'ApproveContract')
        
        has_permission = has_reject_permission or has_approve_permission
        
        # Allow rejection if:
        # 1. User is the assigned approver (assignee_id), OR
        # 2. User has RejectContract or ApproveContract permission
        if current_user_id is None:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        is_assignee = current_user_id == int(approval.assignee_id)
        
        if not is_assignee and not has_permission:
            return Response(
                {'error': 'Only the assigned approver or users with RejectContract/ApproveContract permission can reject this SLA'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logger.info(f"[Reject SLA] User {current_user_id} rejecting approval {approval_id} (is_assignee: {is_assignee}, has_reject_permission: {has_reject_permission}, has_approve_permission: {has_approve_permission})")
        
        # Get rejection reason
        rejection_reason = request.data.get('rejection_reason', '')
        
        # Update approval status to REJECTED
        approval.status = 'REJECTED'
        approval.approval_status = 'REJECTED'
        approval.comment_text = f"REJECTED: {rejection_reason}" if rejection_reason else "REJECTED"
        approval.save()
        
        # Update SLA status to REJECTED
        if approval.sla_id:
            try:
                from tprm_backend.slas.models import VendorSLA
                
                # MULTI-TENANCY: Filter by tenant_id when getting SLA
                # tenant_id already retrieved above (line 989)
                sla_query = VendorSLA.objects.filter(sla_id=approval.sla_id)
                if tenant_id:
                    sla_query = sla_query.filter(tenant_id=tenant_id)
                
                sla = sla_query.first()
                if sla:
                    sla.status = 'EXPIRED'  # Mark as expired when rejected
                    sla.approval_status = 'REJECTED'
                    sla.save()
                    logger.info(f"SLA {approval.sla_id} rejected (tenant_id: {tenant_id})")
                else:
                    logger.warning(f"SLA {approval.sla_id} not found for rejection (tenant_id: {tenant_id})")
            except Exception as e:
                logger.warning(f"SLA {approval.sla_id} not found for rejection: {str(e)}")
        
        # Serialize updated approval
        serializer = SLAApprovalAssignmentSerializer(approval, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'SLA rejected successfully',
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error rejecting SLA: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)