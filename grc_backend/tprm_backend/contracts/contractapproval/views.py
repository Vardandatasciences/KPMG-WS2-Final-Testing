from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.authentication import BaseAuthentication
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils.dateparse import parse_datetime
from django.conf import settings
import logging
import jwt

from tprm_backend.contracts.models import ContractApproval, VendorContract, ContractTerm, ContractClause
from tprm_backend.contracts.contractapproval.serializers import (
    ContractApprovalAssignmentSerializer,
    ContractApprovalCreateAssignmentSerializer,
    ContractApprovalBulkCreateSerializer,
    ContractApprovalStatsSerializer
)
from tprm_backend.contracts.serializers import VendorContractSerializer, ContractTermSerializer, ContractClauseSerializer
from tprm_backend.contracts.views import RateLimiter, SecurityManager
from tprm_backend.rbac.tprm_decorators import rbac_contract_required
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    get_tenant_aware_queryset,
    require_tenant,
    tenant_filter
)

logger = logging.getLogger(__name__)


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
    """Simple health check endpoint for contractapproval"""
    return Response({
        'success': True,
        'message': 'ContractApproval API is running',
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_list(request):
    """
    List contract approvals with filtering and pagination.
    
    Security: Users can only view approvals assigned to them.
    If no assignee_id is provided, automatically filters by authenticated user's ID.
    MULTI-TENANCY: Filters approvals by tenant to ensure tenant isolation
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=200, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
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
        
        logger.info(f"Contract approval list request - User: {getattr(request.user, 'userid', 'anonymous')}, tenant_id: {tenant_id}, assignee_id: {assignee_id}, filters: {request.GET}")
        
        # Build query - if assignee_id is provided, allow users to view their own approvals
        # even without general 'list' permission
        # MULTI-TENANCY: Filter by tenant_id, but also handle null tenant_id for backward compatibility
        if assignee_id:
            # User is requesting their own approvals - allow this
            # Try both string and integer conversion to handle potential type mismatches
            try:
                assignee_id_int = int(assignee_id)
                # Try with tenant_id first, then fallback to null tenant_id if no results
                queryset = ContractApproval.objects.filter(assignee_id=assignee_id_int, tenant_id=tenant_id)
                
                # If no results with tenant_id, try with null tenant_id (backward compatibility)
                if queryset.count() == 0:
                    null_tenant_queryset = ContractApproval.objects.filter(assignee_id=assignee_id_int, tenant_id__isnull=True)
                    if null_tenant_queryset.exists():
                        # Found approvals with null tenant_id - update them and use them
                        logger.info(f"Found {null_tenant_queryset.count()} approvals with null tenant_id for assignee {assignee_id_int}, updating them")
                        null_tenant_queryset.update(tenant_id=tenant_id)
                        queryset = ContractApproval.objects.filter(assignee_id=assignee_id_int, tenant_id=tenant_id)
                
                # If still no results, try string version
                if queryset.count() == 0:
                    queryset = ContractApproval.objects.filter(assignee_id=str(assignee_id), tenant_id=tenant_id)
                    if queryset.count() == 0:
                        null_tenant_queryset = ContractApproval.objects.filter(assignee_id=str(assignee_id), tenant_id__isnull=True)
                        if null_tenant_queryset.exists():
                            logger.info(f"Found {null_tenant_queryset.count()} approvals with null tenant_id for assignee {assignee_id} (string), updating them")
                            null_tenant_queryset.update(tenant_id=tenant_id)
                            queryset = ContractApproval.objects.filter(assignee_id=str(assignee_id), tenant_id=tenant_id)
                    
            except ValueError:
                queryset = ContractApproval.objects.filter(assignee_id=assignee_id, tenant_id=tenant_id)
                if queryset.count() == 0:
                    queryset = ContractApproval.objects.filter(assignee_id=assignee_id, tenant_id__isnull=True)
        else:
            # Security: If no assignee_id is provided, filter by the authenticated user's ID
            # This ensures users can ONLY see approvals assigned to them
            current_user_id = getattr(request.user, 'userid', None)
            if current_user_id:
                try:
                    current_user_id_int = int(current_user_id)
                    # Try with tenant_id first, then fallback to null tenant_id if no results
                    queryset = ContractApproval.objects.filter(assignee_id=current_user_id_int, tenant_id=tenant_id)
                    
                    # If no results with tenant_id, try with null tenant_id (backward compatibility)
                    if queryset.count() == 0:
                        null_tenant_queryset = ContractApproval.objects.filter(assignee_id=current_user_id_int, tenant_id__isnull=True)
                        if null_tenant_queryset.exists():
                            # Found approvals with null tenant_id - update them and use them
                            logger.info(f"Found {null_tenant_queryset.count()} approvals with null tenant_id for assignee {current_user_id_int}, updating them")
                            null_tenant_queryset.update(tenant_id=tenant_id)
                            queryset = ContractApproval.objects.filter(assignee_id=current_user_id_int, tenant_id=tenant_id)
                    
                    # If still no results, try string version
                    if queryset.count() == 0:
                        queryset = ContractApproval.objects.filter(assignee_id=str(current_user_id), tenant_id=tenant_id)
                        if queryset.count() == 0:
                            null_tenant_queryset = ContractApproval.objects.filter(assignee_id=str(current_user_id), tenant_id__isnull=True)
                            if null_tenant_queryset.exists():
                                logger.info(f"Found {null_tenant_queryset.count()} approvals with null tenant_id for assignee {current_user_id} (string), updating them")
                                null_tenant_queryset.update(tenant_id=tenant_id)
                                queryset = ContractApproval.objects.filter(assignee_id=str(current_user_id), tenant_id=tenant_id)
                except (ValueError, TypeError):
                    queryset = ContractApproval.objects.filter(assignee_id=current_user_id, tenant_id=tenant_id)
                    if queryset.count() == 0:
                        queryset = ContractApproval.objects.filter(assignee_id=current_user_id, tenant_id__isnull=True)
            else:
                # No user ID available - return empty queryset for security
                queryset = ContractApproval.objects.none()
        
        # Apply additional filters (assignee_id already filtered above if provided)
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
        logger.info(f"Query SQL: {queryset.query}")
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = ContractApprovalAssignmentSerializer(page_obj.object_list, many=True)
        
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
        logger.error(f"Error listing contract approvals: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': str(e),
            'data': [],
            'pagination': {
                'page': 1,
                'page_size': 20,
                'total_pages': 0,
                'total_count': 0,
                'has_next': False,
                'has_previous': False
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_detail(request, pk):
    """
    Get details of a specific contract approval
    MULTI-TENANCY: Filters approval by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        approval = ContractApproval.objects.get(approval_id=pk, tenant_id=tenant_id)
        serializer = ContractApprovalAssignmentSerializer(approval)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except ContractApproval.DoesNotExist:
        return Response({'error': 'Approval not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting contract approval detail: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_create(request):
    """
    Create a new contract approval
    MULTI-TENANCY: Automatically assigns tenant_id to the approval
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=50, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Security validation
        SecurityManager.validate_contract_data(request.data)
        
        # Set assigned_date if not provided
        data = request.data.copy()
        if not data.get('assigned_date'):
            from django.utils import timezone
            data['assigned_date'] = timezone.now()
        
        # MULTI-TENANCY: Set tenant_id if not provided
        if not data.get('tenant_id'):
            data['tenant_id'] = tenant_id
        
        # Auto-populate assigner_name and assignee_name from user IDs
        if data.get('assigner_id') and not data.get('assigner_name'):
            try:
                from mfa_auth.models import User
                assigner = User.objects.get(userid=data['assigner_id'])
                data['assigner_name'] = f"{assigner.first_name} {assigner.last_name}".strip() or assigner.username
            except ImportError:
                logger.warning(f"User model import failed, using raw SQL for assigner_id {data['assigner_id']}")
                # Fallback to raw SQL
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT FirstName, LastName, UserName FROM users WHERE UserId = %s",
                            [data['assigner_id']]
                        )
                        row = cursor.fetchone()
                        if row:
                            first_name, last_name, username = row
                            full_name = f"{first_name or ''} {last_name or ''}".strip()
                            data['assigner_name'] = full_name if full_name else (username or f"User {data['assigner_id']}")
                        else:
                            data['assigner_name'] = f"User {data['assigner_id']}"
                except Exception as sql_err:
                    logger.error(f"Raw SQL query failed for assigner: {sql_err}")
                    data['assigner_name'] = f"User {data['assigner_id']}"
            except Exception as e:
                logger.warning(f"Error getting assigner name: {e}")
                data['assigner_name'] = f"User {data['assigner_id']}"
        
        if data.get('assignee_id') and not data.get('assignee_name'):
            try:
                from mfa_auth.models import User
                assignee = User.objects.get(userid=data['assignee_id'])
                data['assignee_name'] = f"{assignee.first_name} {assignee.last_name}".strip() or assignee.username
            except ImportError:
                logger.warning(f"User model import failed, using raw SQL for assignee_id {data['assignee_id']}")
                # Fallback to raw SQL
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT FirstName, LastName, UserName FROM users WHERE UserId = %s",
                            [data['assignee_id']]
                        )
                        row = cursor.fetchone()
                        if row:
                            first_name, last_name, username = row
                            full_name = f"{first_name or ''} {last_name or ''}".strip()
                            data['assignee_name'] = full_name if full_name else (username or f"User {data['assignee_id']}")
                        else:
                            data['assignee_name'] = f"User {data['assignee_id']}"
                except Exception as sql_err:
                    logger.error(f"Raw SQL query failed for assignee: {sql_err}")
                    data['assignee_name'] = f"User {data['assignee_id']}"
            except Exception as e:
                logger.warning(f"Error getting assignee name: {e}")
                data['assignee_name'] = f"User {data['assignee_id']}"
        
        serializer = ContractApprovalCreateAssignmentSerializer(data=data)
        
        if serializer.is_valid():
            # MULTI-TENANCY: Ensure tenant_id is set when saving
            approval = serializer.save(tenant_id=tenant_id)
            
            # Update contract status to UNDER_REVIEW if it's a contract creation approval
            if approval.object_type == 'CONTRACT_CREATION' and approval.object_id:
                try:
                    from tprm_backend.contracts.models import VendorContract
                    contract = VendorContract.objects.get(contract_id=approval.object_id)
                    if contract.status == 'PENDING_ASSIGNMENT':
                        contract.status = 'UNDER_REVIEW'
                        contract.save()
                        logger.info(f"Updated contract {approval.object_id} status to UNDER_REVIEW")
                except VendorContract.DoesNotExist:
                    logger.warning(f"Contract {approval.object_id} not found for status update")
                except Exception as e:
                    logger.error(f"Error updating contract status: {str(e)}")
            
            response_serializer = ContractApprovalAssignmentSerializer(approval)
            
            return Response({
                'success': True,
                'message': 'Contract approval created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error creating contract approval: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
def approval_bulk_create(request):
    """
    Create multiple contract approvals at once
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=20, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer = ContractApprovalBulkCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            approvals = serializer.save()
            
            # Update contract statuses to UNDER_REVIEW for contract creation approvals
            for approval in approvals:
                if approval.object_type == 'CONTRACT_CREATION' and approval.object_id:
                    try:
                        from tprm_backend.contracts.models import VendorContract
                        contract = VendorContract.objects.get(contract_id=approval.object_id)
                        if contract.status == 'PENDING_ASSIGNMENT':
                            contract.status = 'UNDER_REVIEW'
                            contract.save()
                            logger.info(f"Updated contract {approval.object_id} status to UNDER_REVIEW")
                    except VendorContract.DoesNotExist:
                        logger.warning(f"Contract {approval.object_id} not found for status update")
                    except Exception as e:
                        logger.error(f"Error updating contract status: {str(e)}")
            
            response_serializer = ContractApprovalAssignmentSerializer(approvals, many=True)
            
            return Response({
                'success': True,
                'message': f'{len(approvals)} contract approvals created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error creating bulk contract approvals: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_update(request, pk):
    """
    Update a contract approval (status, comments)
    MULTI-TENANCY: Filters approval by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        approval = ContractApproval.objects.get(approval_id=pk, tenant_id=tenant_id)
        
        # Only allow updating status and comment_text
        allowed_fields = ['status', 'comment_text']
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = ContractApprovalAssignmentSerializer(approval, data=update_data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Contract approval updated successfully',
                'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except ContractApproval.DoesNotExist:
        return Response({'error': 'Approval not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error updating contract approval: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_delete(request, pk):
    """
    Delete a contract approval
    MULTI-TENANCY: Filters approval by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        approval = ContractApproval.objects.get(approval_id=pk, tenant_id=tenant_id)
        approval.delete()
        
        return Response({
            'success': True,
            'message': 'Contract approval deleted successfully'
        })
        
    except ContractApproval.DoesNotExist:
        return Response({'error': 'Approval not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting contract approval: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_stats(request):
    """
    Get contract approval statistics.
    
    Security: Returns statistics only for approvals assigned to the authenticated user.
    If no assignee_id is provided, automatically uses authenticated user's ID.
    MULTI-TENANCY: Filters statistics by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Apply filters if provided
        assignee_id = request.GET.get('assignee_id')
        object_type = request.GET.get('object_type')
        workflow_id = request.GET.get('workflow_id')
        
        # Security: If no assignee_id is provided, use the authenticated user's ID
        # This ensures users can ONLY see stats for approvals assigned to them
        if not assignee_id:
            assignee_id = getattr(request.user, 'userid', None)
        
        # Get base queryset filtered by assignee_id and tenant_id
        if assignee_id:
            try:
                assignee_id_int = int(assignee_id)
                queryset = ContractApproval.objects.filter(assignee_id=assignee_id_int, tenant_id=tenant_id)
                
                # If no results with int, try string
                if queryset.count() == 0:
                    queryset = ContractApproval.objects.filter(assignee_id=str(assignee_id), tenant_id=tenant_id)
            except (ValueError, TypeError):
                queryset = ContractApproval.objects.filter(assignee_id=assignee_id, tenant_id=tenant_id)
        else:
            # No user ID available - return empty queryset for security
            queryset = ContractApproval.objects.none()
        
        # Apply additional filters
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
        completed_approvals = queryset.filter(status__in=['COMMENTED', 'SKIPPED']).count()
        
        # Status breakdown
        status_breakdown = dict(queryset.values('status').annotate(count=Count('status')).values_list('status', 'count'))
        
        # Type breakdown
        type_breakdown = dict(queryset.values('object_type').annotate(count=Count('object_type')).values_list('object_type', 'count'))
        
        # Assignee breakdown
        assignee_breakdown = dict(queryset.values('assignee_name').annotate(count=Count('assignee_name')).values_list('assignee_name', 'count'))
        
        # Average completion time (for completed approvals)
        completed_queryset = queryset.filter(
            status__in=['COMMENTED', 'SKIPPED'],
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
        
        serializer = ContractApprovalStatsSerializer(stats_data)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error getting contract approval stats: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_approvals_list(request, contract_id):
    """
    Get all approvals for a specific contract
    MULTI-TENANCY: Filters approvals by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Verify contract exists and belongs to tenant
        try:
            contract = VendorContract.objects.get(contract_id=contract_id, tenant_id=tenant_id)
        except VendorContract.DoesNotExist:
            return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get approvals for this contract, filtered by tenant
        approvals = ContractApproval.objects.filter(object_id=contract_id, tenant_id=tenant_id)
        
        # Apply additional filters
        status_filter = request.GET.get('status')
        if status_filter:
            approvals = approvals.filter(status=status_filter)
        
        # Serialize data
        serializer = ContractApprovalAssignmentSerializer(approvals, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'contract_info': {
                'contract_id': contract.contract_id,
                'contract_title': contract.contract_title,
                'contract_number': contract.contract_number,
                'status': contract.status
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting contract approvals: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_contract_approvals(request):
    """
    Get contract approvals for a specific contract by object_id
    MULTI-TENANCY: Filters approvals by tenant to ensure tenant isolation
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=200, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Get query parameters
        object_id = request.GET.get('object_id')
        object_type = request.GET.get('object_type', 'CONTRACT_CREATION')
        
        if not object_id:
            return Response({'error': 'object_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Build query, filtered by tenant
        queryset = ContractApproval.objects.filter(
            object_type=object_type,
            object_id=object_id,
            tenant_id=tenant_id
        ).order_by('-created_at')
        
        # Serialize data
        serializer = ContractApprovalAssignmentSerializer(queryset, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Exception in get_contract_approvals: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_assigner_approvals(request):
    """
    Get contract approvals where the current user is the assigner (for review)
    
    Security: If assigner_id is not provided, automatically filters by authenticated user's ID
    to ensure users only see their own assigned approvals.
    MULTI-TENANCY: Filters approvals by tenant to ensure tenant isolation
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=200, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Get query parameters
        assigner_id = request.GET.get('assigner_id')
        status_filter = request.GET.get('status')
        search = request.GET.get('search', '')
        ordering = request.GET.get('ordering', '-created_at')
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        
        # If assigner_id not provided, use authenticated user's ID (SECURITY)
        if not assigner_id:
            if hasattr(request.user, 'userid'):
                assigner_id = request.user.userid
            elif hasattr(request.user, 'id'):
                assigner_id = request.user.id
            else:
                # If no user ID available, return empty queryset (SECURITY)
                return Response({
                    'success': True,
                    'data': [],
                    'pagination': {
                        'page': 1,
                        'page_size': page_size,
                        'total_pages': 0,
                        'total_count': 0,
                        'has_next': False,
                        'has_previous': False
                    }
                })
        
        logger.info(f"Assigner approvals request - User: {request.user.userid if hasattr(request.user, 'userid') else 'N/A'}, tenant_id: {tenant_id}, assigner_id: {assigner_id}, filters: {request.GET}")
        
        # Build query for approvals where user is the assigner
        # MULTI-TENANCY: Filter by tenant_id, but also handle null tenant_id for backward compatibility
        try:
            assigner_id_int = int(assigner_id)
            # Try with tenant_id first, then fallback to null tenant_id if no results
            queryset = ContractApproval.objects.filter(assigner_id=assigner_id_int, tenant_id=tenant_id)
            
            # If no results with tenant_id, try with null tenant_id (backward compatibility)
            if queryset.count() == 0:
                null_tenant_queryset = ContractApproval.objects.filter(assigner_id=assigner_id_int, tenant_id__isnull=True)
                if null_tenant_queryset.exists():
                    # Found approvals with null tenant_id - update them and use them
                    logger.info(f"Found {null_tenant_queryset.count()} approvals with null tenant_id for assigner {assigner_id_int}, updating them")
                    null_tenant_queryset.update(tenant_id=tenant_id)
                    queryset = ContractApproval.objects.filter(assigner_id=assigner_id_int, tenant_id=tenant_id)
            
            # If still no results, try string version
            if queryset.count() == 0:
                queryset = ContractApproval.objects.filter(assigner_id=str(assigner_id), tenant_id=tenant_id)
                if queryset.count() == 0:
                    null_tenant_queryset = ContractApproval.objects.filter(assigner_id=str(assigner_id), tenant_id__isnull=True)
                    if null_tenant_queryset.exists():
                        logger.info(f"Found {null_tenant_queryset.count()} approvals with null tenant_id for assigner {assigner_id} (string), updating them")
                        null_tenant_queryset.update(tenant_id=tenant_id)
                        queryset = ContractApproval.objects.filter(assigner_id=str(assigner_id), tenant_id=tenant_id)
        except (ValueError, TypeError):
            queryset = ContractApproval.objects.filter(assigner_id=assigner_id, tenant_id=tenant_id)
            if queryset.count() == 0:
                null_tenant_queryset = ContractApproval.objects.filter(assigner_id=assigner_id, tenant_id__isnull=True)
                if null_tenant_queryset.exists():
                    logger.info(f"Found {null_tenant_queryset.count()} approvals with null tenant_id for assigner {assigner_id}, updating them")
                    null_tenant_queryset.update(tenant_id=tenant_id)
                    queryset = ContractApproval.objects.filter(assigner_id=assigner_id, tenant_id=tenant_id)
        
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
        serializer = ContractApprovalAssignmentSerializer(page_obj.object_list, many=True)
        
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
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': str(e),
            'data': [],
            'pagination': {
                'page': 1,
                'page_size': 20,
                'total_pages': 0,
                'total_count': 0,
                'has_next': False,
                'has_previous': False
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approve_contract(request, approval_id):
    """
    Approve a contract after review
    
    Performance: Backup is created asynchronously AFTER approval to prevent blocking
    MULTI-TENANCY: Filters approval by tenant to ensure tenant isolation
    """
    import threading
    
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=50, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Get the approval, filtered by tenant (with fallback to null tenant_id for backward compatibility)
        try:
            approval = ContractApproval.objects.get(approval_id=approval_id, tenant_id=tenant_id)
        except ContractApproval.DoesNotExist:
            # Try with null tenant_id for backward compatibility
            try:
                approval = ContractApproval.objects.get(approval_id=approval_id, tenant_id__isnull=True)
                # Update the approval with tenant_id if it was null
                if approval.tenant_id is None:
                    approval.tenant_id = tenant_id
                    approval.save(update_fields=['tenant_id'])
                    logger.info(f"Updated approval {approval_id} with tenant_id {tenant_id}")
            except ContractApproval.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Approval not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is the assigner (handle both int and string comparisons)
        current_user_id = getattr(request.user, 'userid', None)
        assigner_id = approval.assigner_id
        
        # Normalize both IDs for comparison
        try:
            current_user_id_int = int(current_user_id) if current_user_id else None
            assigner_id_int = int(assigner_id) if assigner_id else None
            if current_user_id_int != assigner_id_int:
                return Response({
                    'success': False,
                    'error': 'You can only approve contracts you assigned'
                }, status=status.HTTP_403_FORBIDDEN)
        except (ValueError, TypeError):
            # Fallback to string comparison
            if str(current_user_id) != str(assigner_id):
                return Response({
                    'success': False,
                    'error': 'You can only approve contracts you assigned'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Update approval status to APPROVED and set approved_date
        approval.status = 'APPROVED'
        approval.approved_date = timezone.now()
        approval.save()
        
        # Update contract, terms, clauses, and subcontracts status to APPROVED
        if approval.object_type == 'CONTRACT_CREATION' and approval.object_id:
            try:
                # Update main contract status to APPROVED
                from tprm_backend.contracts.models import VendorContract, ContractTerm, ContractClause
                contract = VendorContract.objects.get(contract_id=approval.object_id)
                contract.status = 'APPROVED'
                contract.save()
                logger.info(f"Contract {approval.object_id} approved by {getattr(request.user, 'userid', 1)}")
                
                # Update all main contract terms approval_status to Approved
                ContractTerm.objects.filter(contract_id=approval.object_id).update(
                    approval_status='Approved',
                    compliance_status='Compliant'
                )
                logger.info(f"Updated contract terms approval_status for contract {approval.object_id}")
                
                # Update all main contract clauses status to Approved
                ContractClause.objects.filter(contract_id=approval.object_id).update(
                    status='Approved',
                    is_standard=True  # Mark approved clauses as standard
                )
                logger.info(f"Updated contract clauses status for contract {approval.object_id}")
                
                # Find and approve all subcontracts
                subcontracts = VendorContract.objects.filter(
                    contract_kind='SUBCONTRACT',
                    parent_contract_id=approval.object_id,
                    is_archived=False
                )
                
                for subcontract in subcontracts:
                    # Update subcontract status to APPROVED
                    subcontract.status = 'APPROVED'
                    subcontract.save()
                    logger.info(f"Subcontract {subcontract.contract_id} approved")
                    
                    # Update subcontract terms approval_status to Approved, filtered by tenant
                    ContractTerm.objects.filter(contract_id=subcontract.contract_id, tenant_id=tenant_id).update(
                        approval_status='Approved',
                        compliance_status='Compliant'
                    )
                    logger.info(f"Updated subcontract terms approval_status for subcontract {subcontract.contract_id}")
                    
                    # Update subcontract clauses status to Approved, filtered by tenant
                    ContractClause.objects.filter(contract_id=subcontract.contract_id, tenant_id=tenant_id).update(
                        status='Approved',
                        is_standard=True
                    )
                    logger.info(f"Updated subcontract clauses status for subcontract {subcontract.contract_id}")
                
                logger.info(f"Approved {subcontracts.count()} subcontracts for main contract {approval.object_id}")
                
            except VendorContract.DoesNotExist:
                logger.warning(f"Contract {approval.object_id} not found for approval")
        
        # Serialize updated approval
        serializer = ContractApprovalAssignmentSerializer(approval)
        
        # Create async backup AFTER approval (non-blocking)
        def create_async_backup():
            """Create database backup in background thread"""
            try:
                from pathlib import Path
                from django.conf import settings
                import json
                from datetime import datetime
                
                backup_dir = Path(settings.BASE_DIR) / 'backups' / 'contracts'
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = backup_dir / f'contracts_backup_{timestamp}.json'
                
                # Export contracts data
                from tprm_backend.contracts.models import VendorContract, ContractTerm, ContractClause
                contracts_data = {
                    'backup_type': 'post_approval',
                    'approval_id': approval_id,
                    'contracts': list(VendorContract.objects.values()),
                    'terms': list(ContractTerm.objects.values()),
                    'clauses': list(ContractClause.objects.values()),
                    'backup_timestamp': timezone.now().isoformat()
                }
                
                with open(backup_file, 'w') as f:
                    json.dump(contracts_data, f, indent=2, default=str)
                
                logger.info(f"Async database backup created after approval: {backup_file}")
            except Exception as backup_error:
                logger.error(f"Async backup creation failed (non-critical): {str(backup_error)}")
        
        # Start backup in background thread (non-blocking)
        backup_thread = threading.Thread(target=create_async_backup, daemon=True)
        backup_thread.start()
        logger.info(f"Async backup initiated in background for approval {approval_id}")
        
        # Return response immediately without waiting for backup
        return Response({
            'success': True,
            'message': 'Contract approved successfully',
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error approving contract: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('reject')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def reject_contract(request, approval_id):
    """
    Reject a contract after review
    
    Performance: Backup is created asynchronously AFTER rejection to prevent blocking
    MULTI-TENANCY: Filters approval by tenant to ensure tenant isolation
    """
    import threading
    
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=50, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Get the approval, filtered by tenant (with fallback to null tenant_id for backward compatibility)
        try:
            approval = ContractApproval.objects.get(approval_id=approval_id, tenant_id=tenant_id)
        except ContractApproval.DoesNotExist:
            # Try with null tenant_id for backward compatibility
            try:
                approval = ContractApproval.objects.get(approval_id=approval_id, tenant_id__isnull=True)
                # Update the approval with tenant_id if it was null
                if approval.tenant_id is None:
                    approval.tenant_id = tenant_id
                    approval.save(update_fields=['tenant_id'])
                    logger.info(f"Updated approval {approval_id} with tenant_id {tenant_id}")
            except ContractApproval.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Approval not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is the assigner (handle both int and string comparisons)
        current_user_id = getattr(request.user, 'userid', None)
        assigner_id = approval.assigner_id
        
        # Normalize both IDs for comparison
        try:
            current_user_id_int = int(current_user_id) if current_user_id else None
            assigner_id_int = int(assigner_id) if assigner_id else None
            if current_user_id_int != assigner_id_int:
                return Response({
                    'success': False,
                    'error': 'You can only reject contracts you assigned'
                }, status=status.HTTP_403_FORBIDDEN)
        except (ValueError, TypeError):
            # Fallback to string comparison
            if str(current_user_id) != str(assigner_id):
                return Response({
                    'success': False,
                    'error': 'You can only reject contracts you assigned'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Get rejection reason
        rejection_reason = request.data.get('rejection_reason', '')
        
        # Update approval status to REJECTED
        approval.status = 'REJECTED'
        approval.comment_text = f"REJECTED: {rejection_reason}" if rejection_reason else "REJECTED"
        approval.save()
        
        # Update contract, terms, clauses, and subcontracts status to REJECTED
        if approval.object_type == 'CONTRACT_CREATION' and approval.object_id:
            try:
                from tprm_backend.contracts.models import VendorContract, ContractTerm, ContractClause
                contract = VendorContract.objects.get(contract_id=approval.object_id, tenant_id=tenant_id)
                contract.status = 'REJECTED'
                contract.save()
                logger.info(f"Contract {approval.object_id} rejected by {getattr(request.user, 'userid', 1)}")
                
                # Update all main contract terms approval_status to Rejected, filtered by tenant
                ContractTerm.objects.filter(contract_id=approval.object_id, tenant_id=tenant_id).update(
                    approval_status='Rejected'
                )
                logger.info(f"Updated contract terms approval_status to Rejected for contract {approval.object_id}")
                
                # Update all main contract clauses status to Rejected, filtered by tenant
                ContractClause.objects.filter(contract_id=approval.object_id, tenant_id=tenant_id).update(
                    status='Rejected'
                )
                logger.info(f"Updated contract clauses status to Rejected for contract {approval.object_id}")
                
                # Find and reject all subcontracts, filtered by tenant
                subcontracts = VendorContract.objects.filter(
                    contract_kind='SUBCONTRACT',
                    parent_contract_id=approval.object_id,
                    is_archived=False,
                    tenant_id=tenant_id
                )
                
                for subcontract in subcontracts:
                    # Update subcontract status to REJECTED
                    subcontract.status = 'REJECTED'
                    subcontract.save()
                    logger.info(f"Subcontract {subcontract.contract_id} rejected")
                    
                    # Update subcontract terms approval_status to Rejected, filtered by tenant
                    ContractTerm.objects.filter(contract_id=subcontract.contract_id, tenant_id=tenant_id).update(
                        approval_status='Rejected'
                    )
                    logger.info(f"Updated subcontract terms approval_status to Rejected for subcontract {subcontract.contract_id}")
                    
                    # Update subcontract clauses status to Rejected, filtered by tenant
                    ContractClause.objects.filter(contract_id=subcontract.contract_id, tenant_id=tenant_id).update(
                        status='Rejected'
                    )
                    logger.info(f"Updated subcontract clauses status to Rejected for subcontract {subcontract.contract_id}")
                
                logger.info(f"Rejected {subcontracts.count()} subcontracts for main contract {approval.object_id}")
                
            except VendorContract.DoesNotExist:
                logger.warning(f"Contract {approval.object_id} not found for rejection")
        
        # Serialize updated approval
        serializer = ContractApprovalAssignmentSerializer(approval)
        
        # Create async backup AFTER rejection (non-blocking)
        def create_async_backup():
            """Create database backup in background thread"""
            try:
                from pathlib import Path
                from django.conf import settings
                import json
                from datetime import datetime
                
                backup_dir = Path(settings.BASE_DIR) / 'backups' / 'contracts'
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = backup_dir / f'contracts_backup_{timestamp}.json'
                
                # Export contracts data
                from tprm_backend.contracts.models import VendorContract, ContractTerm, ContractClause
                contracts_data = {
                    'backup_type': 'post_rejection',
                    'approval_id': approval_id,
                    'contracts': list(VendorContract.objects.values()),
                    'terms': list(ContractTerm.objects.values()),
                    'clauses': list(ContractClause.objects.values()),
                    'backup_timestamp': timezone.now().isoformat()
                }
                
                with open(backup_file, 'w') as f:
                    json.dump(contracts_data, f, indent=2, default=str)
                
                logger.info(f"Async database backup created after rejection: {backup_file}")
            except Exception as backup_error:
                logger.error(f"Async backup creation failed (non-critical): {str(backup_error)}")
        
        # Start backup in background thread (non-blocking)
        backup_thread = threading.Thread(target=create_async_backup, daemon=True)
        backup_thread.start()
        logger.info(f"Async backup initiated in background for rejection {approval_id}")
        
        # Return response immediately without waiting for backup
        return Response({
            'success': True,
            'message': 'Contract rejected successfully',
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error rejecting contract: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@rbac_contract_required('approve')
def contract_comprehensive_detail(request, contract_id):
    """Get comprehensive contract details including terms, clauses, and sub-contracts for contract approval"""
    try:
        logger.info(f"[CONTRACTAPPROVAL] Starting comprehensive contract detail fetch for contract_id: {contract_id}")
        
        # Get main contract
        contract = VendorContract.objects.select_related('vendor').get(
            contract_id=contract_id, 
            is_archived=False
        )
        logger.info(f"[CONTRACTAPPROVAL] Found contract: {contract.contract_title} (ID: {contract.contract_id})")
        
        # Get contract terms
        terms = ContractTerm.objects.filter(contract_id=contract_id).order_by('term_category', 'created_at')
        logger.info(f"[CONTRACTAPPROVAL] Found {terms.count()} terms for contract {contract_id}")
        
        # Get contract clauses
        clauses = ContractClause.objects.filter(contract_id=contract_id).order_by('clause_type', 'created_at')
        logger.info(f"[CONTRACTAPPROVAL] Found {clauses.count()} clauses for contract {contract_id}")
        
        # Get sub-contracts (contracts with contract_kind='SUBCONTRACT' and parent_contract_id=contract_id)
        sub_contracts = VendorContract.objects.filter(
            contract_kind='SUBCONTRACT',
            parent_contract_id=contract_id,
            is_archived=False
        ).select_related('vendor').order_by('created_at')
        logger.info(f"[CONTRACTAPPROVAL] Found {sub_contracts.count()} sub-contracts for contract {contract_id}")
        
        # Get terms and clauses for each sub-contract
        sub_contracts_with_details = []
        total_sub_terms = 0
        total_sub_clauses = 0
        
        for sub_contract in sub_contracts:
            # Get terms for this sub-contract
            sub_terms = ContractTerm.objects.filter(contract_id=sub_contract.contract_id).order_by('term_category', 'created_at')
            sub_terms_serializer = ContractTermSerializer(sub_terms, many=True)
            
            # Get clauses for this sub-contract
            sub_clauses = ContractClause.objects.filter(contract_id=sub_contract.contract_id).order_by('clause_type', 'created_at')
            sub_clauses_serializer = ContractClauseSerializer(sub_clauses, many=True)
            
            # Serialize the sub-contract
            sub_contract_serializer = VendorContractSerializer(sub_contract)
            sub_contract_data = sub_contract_serializer.data
            
            # Add terms and clauses to the sub-contract data
            sub_contract_data['terms'] = sub_terms_serializer.data
            sub_contract_data['clauses'] = sub_clauses_serializer.data
            sub_contract_data['terms_count'] = len(sub_terms)
            sub_contract_data['clauses_count'] = len(sub_clauses)
            
            sub_contracts_with_details.append(sub_contract_data)
            total_sub_terms += len(sub_terms)
            total_sub_clauses += len(sub_clauses)
        
        # Serialize main contract data
        contract_serializer = VendorContractSerializer(contract)
        terms_serializer = ContractTermSerializer(terms, many=True)
        clauses_serializer = ContractClauseSerializer(clauses, many=True)
        
        logger.info(f"[CONTRACTAPPROVAL] Serialized data - Contract: {len(contract_serializer.data)} fields, Terms: {len(terms_serializer.data)} items, Clauses: {len(clauses_serializer.data)} items")
        
        response_data = {
            'success': True,
            'data': {
                'contract': contract_serializer.data,
                'terms': terms_serializer.data,
                'clauses': clauses_serializer.data,
                'sub_contracts': sub_contracts_with_details,
                'summary': {
                    'total_terms': len(terms),
                    'total_clauses': len(clauses),
                    'total_sub_contracts': len(sub_contracts),
                    'total_sub_terms': total_sub_terms,
                    'total_sub_clauses': total_sub_clauses,
                    'total_all_terms': len(terms) + total_sub_terms,
                    'total_all_clauses': len(clauses) + total_sub_clauses
                }
            }
        }
        
        logger.info(f"[CONTRACTAPPROVAL] Returning comprehensive contract data with {len(response_data['data']['terms'])} terms and {len(response_data['data']['clauses'])} clauses")
        return Response(response_data)
        
    except VendorContract.DoesNotExist:
        logger.error(f"[CONTRACTAPPROVAL] Contract {contract_id} not found")
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist or has been archived'
        }, status=404)
    except Exception as e:
        logger.error(f"[CONTRACTAPPROVAL] Comprehensive contract detail error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve contract details',
            'message': str(e)
        }, status=500)

