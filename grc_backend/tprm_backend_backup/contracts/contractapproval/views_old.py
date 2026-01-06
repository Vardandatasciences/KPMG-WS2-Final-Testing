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
def approval_list(request):
    """
    List all contract approvals with filtering and pagination
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=200, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
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
        
        logger.info(f"Contract approval list request - User: {getattr(request.user, 'userid', 'anonymous')}, assignee_id: {assignee_id}, filters: {request.GET}")
        
        # Build query - if assignee_id is provided, allow users to view their own approvals
        # even without general 'list' permission
        if assignee_id:
            # User is requesting their own approvals - allow this
            # Try both string and integer conversion to handle potential type mismatches
            try:
                assignee_id_int = int(assignee_id)
                queryset = ContractApproval.objects.filter(assignee_id=assignee_id_int)
                
                # If no results with int, try string
                if queryset.count() == 0:
                    queryset = ContractApproval.objects.filter(assignee_id=str(assignee_id))
                    
            except ValueError:
                queryset = ContractApproval.objects.filter(assignee_id=assignee_id)
        else:
            # User is requesting all approvals - RBAC removed, allowing all authenticated users
            queryset = ContractApproval.objects.all()
        
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
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def approval_detail(request, pk):
    """
    Get details of a specific contract approval
    """
    try:
        approval = ContractApproval.objects.get(approval_id=pk)
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
def approval_create(request):
    """
    Create a new contract approval
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=50, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Security validation
        SecurityManager.validate_contract_data(request.data)
        
        # Set assigned_date if not provided
        data = request.data.copy()
        if not data.get('assigned_date'):
            from django.utils import timezone
            data['assigned_date'] = timezone.now()
        
        # Auto-populate assigner_name and assignee_name from user IDs
        from mfa_auth.models import User
        
        if data.get('assigner_id') and not data.get('assigner_name'):
            try:
                assigner = User.objects.get(userid=data['assigner_id'])
                data['assigner_name'] = f"{assigner.first_name} {assigner.last_name}".strip() or assigner.username
            except User.DoesNotExist:
                data['assigner_name'] = f"User {data['assigner_id']}"
        
        if data.get('assignee_id') and not data.get('assignee_name'):
            try:
                assignee = User.objects.get(userid=data['assignee_id'])
                data['assignee_name'] = f"{assignee.first_name} {assignee.last_name}".strip() or assignee.username
            except User.DoesNotExist:
                data['assignee_name'] = f"User {data['assignee_id']}"
        
        serializer = ContractApprovalCreateAssignmentSerializer(data=data)
        
        if serializer.is_valid():
            approval = serializer.save()
            
            # Update contract status to UNDER_REVIEW if it's a contract creation approval
            if approval.object_type == 'CONTRACT_CREATION' and approval.object_id:
                try:
                    from contracts.models import VendorContract
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
                        from contracts.models import VendorContract
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
def approval_update(request, pk):
    """
    Update a contract approval (status, comments)
    """
    try:
        approval = ContractApproval.objects.get(approval_id=pk)
        
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
def approval_delete(request, pk):
    """
    Delete a contract approval
    """
    try:
        approval = ContractApproval.objects.get(approval_id=pk)
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
def approval_stats(request):
    """
    Get contract approval statistics
    """
    try:
        # Get base queryset
        queryset = ContractApproval.objects.all()
        
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
def contract_approvals_list(request, contract_id):
    """
    Get all approvals for a specific contract
    """
    try:
        # Verify contract exists
        try:
            contract = VendorContract.objects.get(contract_id=contract_id)
        except VendorContract.DoesNotExist:
            return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get approvals for this contract
        approvals = ContractApproval.objects.filter(object_id=contract_id)
        
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
def get_contract_approvals(request):
    """
    Get contract approvals for a specific contract by object_id
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=200, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Get query parameters
        object_id = request.GET.get('object_id')
        object_type = request.GET.get('object_type', 'CONTRACT_CREATION')
        
        if not object_id:
            return Response({'error': 'object_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Build query
        queryset = ContractApproval.objects.filter(
            object_type=object_type,
            object_id=object_id
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
def get_assigner_approvals(request):
    """
    Get contract approvals where the current user is the assigner (for review)
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=200, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Get query parameters
        assigner_id = request.GET.get('assigner_id')
        status_filter = request.GET.get('status')
        search = request.GET.get('search', '')
        ordering = request.GET.get('ordering', '-created_at')
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        
        if not assigner_id:
            return Response({'error': 'assigner_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Build query for approvals where user is the assigner
        queryset = ContractApproval.objects.filter(assigner_id=assigner_id)
        
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
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def approve_contract(request, approval_id):
    """
    Approve a contract after review
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=50, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Get the approval
        try:
            approval = ContractApproval.objects.get(approval_id=approval_id)
        except ContractApproval.DoesNotExist:
            return Response({'error': 'Approval not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is the assigner
        if approval.assigner_id != getattr(request.user, 'userid', 1):
            return Response({'error': 'You can only approve contracts you assigned'}, status=status.HTTP_403_FORBIDDEN)
        
        # Update approval status to APPROVED
        approval.status = 'APPROVED'
        approval.save()
        
        # Update contract, terms, clauses, and subcontracts status to APPROVED
        if approval.object_type == 'CONTRACT_CREATION' and approval.object_id:
            try:
                # Update main contract status to APPROVED
                from contracts.models import VendorContract, ContractTerm, ContractClause
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
                    
                    # Update subcontract terms approval_status to Approved
                    ContractTerm.objects.filter(contract_id=subcontract.contract_id).update(
                        approval_status='Approved',
                        compliance_status='Compliant'
                    )
                    logger.info(f"Updated subcontract terms approval_status for subcontract {subcontract.contract_id}")
                    
                    # Update subcontract clauses status to Approved
                    ContractClause.objects.filter(contract_id=subcontract.contract_id).update(
                        status='Approved',
                        is_standard=True
                    )
                    logger.info(f"Updated subcontract clauses status for subcontract {subcontract.contract_id}")
                
                logger.info(f"Approved {subcontracts.count()} subcontracts for main contract {approval.object_id}")
                
            except VendorContract.DoesNotExist:
                logger.warning(f"Contract {approval.object_id} not found for approval")
        
        # Serialize updated approval
        serializer = ContractApprovalAssignmentSerializer(approval)
        
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
def reject_contract(request, approval_id):
    """
    Reject a contract after review
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request, limit=50, window=3600):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Get the approval
        try:
            approval = ContractApproval.objects.get(approval_id=approval_id)
        except ContractApproval.DoesNotExist:
            return Response({'error': 'Approval not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is the assigner
        if approval.assigner_id != getattr(request.user, 'userid', 1):
            return Response({'error': 'You can only reject contracts you assigned'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get rejection reason
        rejection_reason = request.data.get('rejection_reason', '')
        
        # Update approval status to REJECTED
        approval.status = 'REJECTED'
        approval.comment_text = f"REJECTED: {rejection_reason}" if rejection_reason else "REJECTED"
        approval.save()
        
        # Update contract, terms, clauses, and subcontracts status to REJECTED
        if approval.object_type == 'CONTRACT_CREATION' and approval.object_id:
            try:
                from contracts.models import VendorContract, ContractTerm, ContractClause
                contract = VendorContract.objects.get(contract_id=approval.object_id)
                contract.status = 'REJECTED'
                contract.save()
                logger.info(f"Contract {approval.object_id} rejected by {getattr(request.user, 'userid', 1)}")
                
                # Update all main contract terms approval_status to Rejected
                ContractTerm.objects.filter(contract_id=approval.object_id).update(
                    approval_status='Rejected'
                )
                logger.info(f"Updated contract terms approval_status to Rejected for contract {approval.object_id}")
                
                # Update all main contract clauses status to Rejected
                ContractClause.objects.filter(contract_id=approval.object_id).update(
                    status='Rejected'
                )
                logger.info(f"Updated contract clauses status to Rejected for contract {approval.object_id}")
                
                # Find and reject all subcontracts
                subcontracts = VendorContract.objects.filter(
                    contract_kind='SUBCONTRACT',
                    parent_contract_id=approval.object_id,
                    is_archived=False
                )
                
                for subcontract in subcontracts:
                    # Update subcontract status to REJECTED
                    subcontract.status = 'REJECTED'
                    subcontract.save()
                    logger.info(f"Subcontract {subcontract.contract_id} rejected")
                    
                    # Update subcontract terms approval_status to Rejected
                    ContractTerm.objects.filter(contract_id=subcontract.contract_id).update(
                        approval_status='Rejected'
                    )
                    logger.info(f"Updated subcontract terms approval_status to Rejected for subcontract {subcontract.contract_id}")
                    
                    # Update subcontract clauses status to Rejected
                    ContractClause.objects.filter(contract_id=subcontract.contract_id).update(
                        status='Rejected'
                    )
                    logger.info(f"Updated subcontract clauses status to Rejected for subcontract {subcontract.contract_id}")
                
                logger.info(f"Rejected {subcontracts.count()} subcontracts for main contract {approval.object_id}")
                
            except VendorContract.DoesNotExist:
                logger.warning(f"Contract {approval.object_id} not found for rejection")
        
        # Serialize updated approval
        serializer = ContractApprovalAssignmentSerializer(approval)
        
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
@permission_classes([SimpleAuthenticatedPermission])
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

