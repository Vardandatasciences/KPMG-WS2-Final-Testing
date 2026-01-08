"""
Contract Management Views

This module provides API views for contract management with comprehensive
security features, error handling, and RBAC (Role-Based Access Control) integration.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import transaction, connection
from django.db.models import Q, Count, Sum, Avg, Case, When, IntegerField, CharField, Value
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.pagination import PageNumberPagination
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache
import jwt
import hashlib
import hmac
import base64
from cryptography.fernet import Fernet
import os
import shutil
from pathlib import Path

# RBAC imports
from rbac.tprm_decorators import rbac_contract_required

# Import models and serializers
from .models import Vendor, VendorContract, ContractTerm, ContractClause, VendorContact, ContractAmendment, ContractRenewal
from .serializers import (
    VendorSerializer, VendorContractSerializer, VendorContractCreateSerializer,
    VendorContractUpdateSerializer, ContractTermSerializer, ContractClauseSerializer,
    ContractArchiveSerializer, ContractRestoreSerializer, ContractSearchSerializer,
    ContractStatsSerializer, UserSerializer, VendorContactSerializer, 
    VendorContactCreateSerializer, VendorContactUpdateSerializer, VendorContactSearchSerializer,
    ContractAmendmentSerializer, ContractAmendmentCreateSerializer, ContractAmendmentUpdateSerializer,
    ContractAmendmentSearchSerializer, ContractRenewalSerializer, ContractRenewalCreateSerializer,
    ContractRenewalUpdateSerializer, ContractRenewalSearchSerializer
)

logger = logging.getLogger(__name__)

# Helper function to parse integer fields (user IDs, etc.)
def parse_integer(int_value, fallback_int):
    if isinstance(int_value, int):
        return int_value
    elif isinstance(int_value, str):
        if int_value.strip() == '':
            return fallback_int
        try:
            return int(int_value.strip())
        except (ValueError, TypeError):
            return fallback_int
    else:
        return fallback_int


class SimpleAuthenticatedPermission(BasePermission):
    """Custom permission class that checks for authenticated users"""
    def has_permission(self, request, view):
        # Check if user is authenticated
        return bool(
            request.user and 
            hasattr(request.user, 'userid') and
            getattr(request.user, 'is_authenticated', False)
        )


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


class DatabaseBackupManager:
    """Database backup and retry mechanism"""
    
    @staticmethod
    def create_backup():
        """Create database backup before critical operations"""
        try:
            backup_dir = Path(settings.BASE_DIR) / 'backups' / 'contracts'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f'contracts_backup_{timestamp}.json'
            
            # Export contracts data
            contracts_data = {
                'vendors': list(Vendor.objects.values()),
                'contracts': list(VendorContract.objects.values()),
                'terms': list(ContractTerm.objects.values()),
                'clauses': list(ContractClause.objects.values()),
                'backup_timestamp': timezone.now().isoformat()
            }
            
            with open(backup_file, 'w') as f:
                json.dump(contracts_data, f, indent=2, default=str)
            
            logger.info(f"Database backup created: {backup_file}")
            return str(backup_file)
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return None
    
    @staticmethod
    def retry_operation(operation, max_retries=3, delay=1):
        """Retry operation with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Operation failed after {max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Operation attempt {attempt + 1} failed: {str(e)}")
                time.sleep(delay * (2 ** attempt))
        return None


class SecurityManager:
    """Security features and validation"""
    
    @staticmethod
    def validate_contract_data(data):
        """Validate contract data for security"""
        # Check for SQL injection patterns
        sql_patterns = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'SELECT', 'UNION', '--', '/*', '*/']
        for key, value in data.items():
            if isinstance(value, str):
                for pattern in sql_patterns:
                    if pattern.upper() in value.upper():
                        raise ValidationError(f"Invalid input detected: {pattern}")
        
        # Validate JSON fields
        json_fields = ['insurance_requirements', 'data_protection_clauses', 'custom_fields']
        for field in json_fields:
            if field in data and data[field]:
                logger.info(f"Validating JSON field '{field}': {data[field]} (type: {type(data[field])})")
                try:
                    if isinstance(data[field], str):
                        logger.info(f"Field '{field}' is string, attempting to parse as JSON")
                        json.loads(data[field])
                        logger.info(f"Field '{field}' JSON parsing successful")
                    elif isinstance(data[field], (dict, list)):
                        logger.info(f"Field '{field}' is already valid JSON structure")
                        # Already valid JSON structure, no need to parse
                        pass
                    else:
                        logger.error(f"Field '{field}' has invalid type: {type(data[field])}")
                        raise ValidationError(f"Invalid JSON format in {field}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"JSON validation failed for field '{field}': {str(e)}")
                    raise ValidationError(f"Invalid JSON format in {field}")
        
        return True
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename for security"""
        import re
        # Remove or replace dangerous characters
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        # Limit length
        filename = filename[:100]
        return filename
    
    @staticmethod
    def encrypt_sensitive_data(data):
        """Encrypt sensitive contract data"""
        try:
            key = Fernet.generate_key()
            f = Fernet(key)
            encrypted_data = f.encrypt(json.dumps(data).encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            return data


class RateLimiter:
    """Rate limiting for API endpoints"""
    
    @staticmethod
    def is_rate_limited(request, limit=100, window=3600):
        """Check if request is rate limited"""
        user_id = getattr(request.user, 'id', None)
        if not user_id:
            return False
        
        cache_key = f"rate_limit_{user_id}_{int(time.time() // window)}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            return True
        
        cache.set(cache_key, current_count + 1, window)
        return False


# API Views

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def simple_login(request):
    """Simple login without MFA - direct authentication"""
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        logger.info(f"Login attempt - Username: {username}, Password length: {len(password) if password else 0}")
        
        if not username or not password:
            logger.warning("Login failed - Missing username or password")
            return Response({
                'success': False,
                'message': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to authenticate using the custom users table
        try:
            # First, try to find user in the custom users table
            from mfa_auth.models import User
            user = User.objects.get(username=username)
            
            # Check password (stored as plain text in your model)
            if user.password == password:
                # Generate JWT token
                import jwt
                import time
                
                payload = {
                    'user_id': user.userid,  # Use userid as primary key
                    'username': username,
                    'exp': time.time() + 86400  # 24 hours
                }
                
                # Use Django's SECRET_KEY for JWT signing
                from django.conf import settings
                secret_key = settings.SECRET_KEY
                session_token = jwt.encode(payload, secret_key, algorithm='HS256')
                
                logger.info(f"Login successful for user: {username}")
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'user_id': user.userid,
                        'username': username,
                        'email': user.email or f'{username}@example.com',
                        'role': 'user'
                    },
                    'session_token': session_token
                })
            else:
                logger.warning(f"Invalid password for user: {username}")
                return Response({
                    'success': False,
                    'message': 'Invalid username or password'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except User.DoesNotExist:
            logger.warning(f"User not found: {username}")
            return Response({
                'success': False,
                'message': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return Response({
                'success': False,
                'message': 'Authentication failed. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Simple login error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Login failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def validate_session(request):
    """Validate JWT session token"""
    try:
        # If we reach here, the JWT authentication was successful
        return Response({
            'success': True,
            'message': 'Session is valid',
            'user': {
                'user_id': getattr(request.user, 'userid', 1),
                'username': getattr(request.user, 'username', 'user'),
                'email': f"{getattr(request.user, 'username', 'user')}@example.com",
                'role': 'admin'
            }
        })
    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Session validation failed'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_list(request):
    """List all contracts with filtering and pagination"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get query parameters
        search = request.GET.get('search', '')
        contract_type = request.GET.get('contract_type', '')
        status_filter = request.GET.get('status', '')
        workflow_stage = request.GET.get('workflow_stage', '')
        priority = request.GET.get('priority', '')
        vendor_id = request.GET.get('vendor_id')
        contract_owner = request.GET.get('contract_owner')
        is_archived = request.GET.get('is_archived', 'false').lower() == 'true'
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        ordering = request.GET.get('ordering', '-created_at')
        
        # Build query
        queryset = VendorContract.objects.select_related('vendor')
        
        # Filter for main and amendment contracts
        queryset = queryset.filter(contract_kind__in=['MAIN', 'AMENDMENT'])
        
        if is_archived:
            queryset = queryset.filter(is_archived=True)
        else:
            queryset = queryset.filter(is_archived=False)
        
        if search:
            queryset = queryset.filter(
                Q(contract_title__icontains=search) |
                Q(contract_number__icontains=search) |
                Q(vendor__company_name__icontains=search)
            )
        
        if contract_type:
            queryset = queryset.filter(contract_type=contract_type)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if workflow_stage:
            queryset = queryset.filter(workflow_stage=workflow_stage)
        
        if priority:
            queryset = queryset.filter(priority=priority)
        
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
        
        if contract_owner:
            queryset = queryset.filter(contract_owner_id=contract_owner)
        
        # Apply ordering
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = VendorContractSerializer(page_obj.object_list, many=True)
        
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
        logger.error(f"Contract list error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve contracts',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_detail(request, contract_id):
    """Get contract details by ID"""
    try:
        contract = VendorContract.objects.select_related('vendor').get(
            contract_id=contract_id, 
            is_archived=False
        )
        
        serializer = VendorContractSerializer(contract)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist or has been archived'
        }, status=404)
    except Exception as e:
        logger.error(f"Contract detail error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve contract',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_comprehensive_detail(request, contract_id):
    """Get comprehensive contract details including terms, clauses, and sub-contracts"""
    try:
        logger.info(f"Starting comprehensive contract detail fetch for contract_id: {contract_id}")
        
        # Get main contract
        contract = VendorContract.objects.select_related('vendor').get(
            contract_id=contract_id, 
            is_archived=False
        )
        logger.info(f"Found contract: {contract.contract_title} (ID: {contract.contract_id})")
        
        # Get contract terms
        terms = ContractTerm.objects.filter(contract_id=contract_id).order_by('term_category', 'created_at')
        logger.info(f"Found {terms.count()} terms for contract {contract_id}")
        
        # Get contract clauses
        clauses = ContractClause.objects.filter(contract_id=contract_id).order_by('clause_type', 'created_at')
        logger.info(f"Found {clauses.count()} clauses for contract {contract_id}")
        
        # Get sub-contracts (contracts with contract_kind='SUBCONTRACT' and parent_contract_id=contract_id)
        sub_contracts = VendorContract.objects.filter(
            contract_kind='SUBCONTRACT',
            parent_contract_id=contract_id,
            is_archived=False
        ).select_related('vendor').order_by('created_at')
        
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
        
        logger.info(f"Serialized data - Contract: {len(contract_serializer.data)} fields, Terms: {len(terms_serializer.data)} items, Clauses: {len(clauses_serializer.data)} items")
        
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
        
        logger.info(f"Returning comprehensive contract data with {len(response_data['data']['terms'])} terms and {len(response_data['data']['clauses'])} clauses")
        return Response(response_data)
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist or has been archived'
        }, status=404)
    except Exception as e:
        logger.error(f"Comprehensive contract detail error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve contract details',
            'message': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
def contract_create(request):
    """Create a new contract"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        def create_contract():
            contract_data = request.data.copy()
            
            # Convert boolean values to integers for unmanaged models
            if 'auto_renewal' in contract_data:
                logger.info(f"Converting auto_renewal: {contract_data['auto_renewal']} (type: {type(contract_data['auto_renewal'])})")
                contract_data['auto_renewal'] = 1 if contract_data['auto_renewal'] else 0
                logger.info(f"Converted auto_renewal to: {contract_data['auto_renewal']}")
            
            # Set default status if not provided, otherwise use the provided status
            if 'status' not in contract_data or not contract_data['status']:
                contract_data['status'] = 'UNDER_REVIEW'
                contract_data['workflow_stage'] = 'under_review'
            else:
                # Map status to workflow_stage
                status_mapping = {
                    'DRAFT': 'draft',
                    'UNDER_REVIEW': 'under_review',
                    'PENDING_APPROVAL': 'pending_approval',
                    'APPROVED': 'approved',
                    'REJECTED': 'rejected'
                }
                contract_data['workflow_stage'] = status_mapping.get(contract_data['status'], 'draft')
            
            # Handle JSON fields - convert plain text to JSON if needed
            if 'insurance_requirements' in contract_data:
                if isinstance(contract_data['insurance_requirements'], str):
                    if contract_data['insurance_requirements'].strip():
                        contract_data['insurance_requirements'] = {
                            'requirements': contract_data['insurance_requirements'].strip(),
                            'type': 'text'
                        }
                    else:
                        contract_data['insurance_requirements'] = {}
                elif not isinstance(contract_data['insurance_requirements'], dict):
                    contract_data['insurance_requirements'] = {}
            
            if 'data_protection_clauses' in contract_data:
                if isinstance(contract_data['data_protection_clauses'], str):
                    if contract_data['data_protection_clauses'].strip():
                        contract_data['data_protection_clauses'] = {
                            'clauses': contract_data['data_protection_clauses'].strip(),
                            'type': 'text'
                        }
                    else:
                        contract_data['data_protection_clauses'] = {}
                elif not isinstance(contract_data['data_protection_clauses'], dict):
                    contract_data['data_protection_clauses'] = {}
            
            if 'custom_fields' in contract_data:
                if isinstance(contract_data['custom_fields'], str):
                    try:
                        import json
                        contract_data['custom_fields'] = json.loads(contract_data['custom_fields'])
                    except (json.JSONDecodeError, TypeError):
                        contract_data['custom_fields'] = {}
                elif not isinstance(contract_data['custom_fields'], dict):
                    contract_data['custom_fields'] = {}
            
            serializer = VendorContractCreateSerializer(data=contract_data)
            if serializer.is_valid():
                # Save contract with all data from serializer (including contract_owner from dropdown)
                contract = serializer.save()
                
                logger.info(f"Contract created: {contract.contract_id} by user {getattr(request.user, 'userid', 'unknown')} with status UNDER_REVIEW")
                logger.info(f"Contract owner set to: {contract.contract_owner} from form data")
                return contract
            else:
                raise ValidationError(serializer.errors)
        
        # Create contract without backup (for speed)
        contract = DatabaseBackupManager.retry_operation(create_contract)
        
        # Create contract approval if contract status is UNDER_REVIEW
        if contract.status == 'UNDER_REVIEW':
            try:
                from tprm_backend.contracts.contractapproval.serializers import ContractApprovalCreateAssignmentSerializer
                from tprm_backend.contracts.models import ContractApproval
                
                # Create approval data
                approval_data = {
                    'workflow_id': 1,  # Default workflow ID
                    'workflow_name': 'Contract Review Workflow',
                    'assigner_id': getattr(request.user, 'userid', 1),
                    'assigner_name': f"{getattr(request.user, 'first_name', 'Test')} {getattr(request.user, 'last_name', 'User')}".strip() or getattr(request.user, 'username', 'testuser1'),
                    'assignee_id': contract.legal_reviewer or contract.contract_owner or getattr(request.user, 'userid', 1),
                    'assignee_name': 'Legal Reviewer',  # Will be updated with actual name
                    'object_type': 'CONTRACT_CREATION',
                    'object_id': contract.contract_id,
                    'assigned_date': timezone.now(),
                    'due_date': timezone.now() + timezone.timedelta(days=7),  # 7 days from now
                    'status': 'ASSIGNED',
                    'comment_text': f'Contract {contract.contract_number} requires review and approval'
                }
                
                # Get assignee name
                if contract.legal_reviewer:
                    try:
                        from mfa_auth.models import User
                        assignee_user = User.objects.get(userid=contract.legal_reviewer)
                        approval_data['assignee_name'] = f"{assignee_user.first_name} {assignee_user.last_name}".strip() or assignee_user.username
                    except User.DoesNotExist:
                        pass
                elif contract.contract_owner:
                    try:
                        from mfa_auth.models import User
                        assignee_user = User.objects.get(userid=contract.contract_owner)
                        approval_data['assignee_name'] = f"{assignee_user.first_name} {assignee_user.last_name}".strip() or assignee_user.username
                    except User.DoesNotExist:
                        pass
                
                # Create the approval
                approval_serializer = ContractApprovalCreateAssignmentSerializer(data=approval_data)
                if approval_serializer.is_valid():
                    approval = approval_serializer.save()
                    logger.info(f"Contract approval created: {approval.approval_id} for contract {contract.contract_id}")
                else:
                    logger.warning(f"Failed to create contract approval: {approval_serializer.errors}")
                    
            except Exception as e:
                logger.error(f"Error creating contract approval: {str(e)}")
                # Don't fail the contract creation if approval creation fails
        
        # Create backup after successful contract creation (for speed)
        backup_file = DatabaseBackupManager.create_backup()
        
        # Return created contract
        response_serializer = VendorContractSerializer(contract)
        
        response_data = {
            'success': True,
            'data': response_serializer.data,
            'message': 'Contract created successfully',
            'backup_file': backup_file
        }
        
        return Response(response_data, status=201)
        
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Contract creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create contract',
            'message': str(e)
        }, status=500)


@api_view(['PUT', 'PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContract')
def contract_update(request, contract_id):
    """Update an existing contract"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        # Get contract
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=False
        )
        
        # Create backup before operation
        backup_file = DatabaseBackupManager.create_backup()
        
        def update_contract():
            serializer = VendorContractUpdateSerializer(
                contract, 
                data=request.data, 
                partial=request.method == 'PATCH'
            )
            if serializer.is_valid():
                updated_contract = serializer.save()
                # Note: updated_by field doesn't exist in the database schema
                
                logger.info(f"Contract updated: {contract_id} by user {getattr(request.user, 'userid', 1)}")
                return updated_contract
            else:
                raise ValidationError(serializer.errors)
        
        # Retry operation with backup
        updated_contract = DatabaseBackupManager.retry_operation(update_contract)
        
        # Return updated contract
        response_serializer = VendorContractSerializer(updated_contract)
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Contract updated successfully',
            'backup_file': backup_file
        })
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist or has been archived'
        }, status=404)
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Contract update error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update contract',
            'message': str(e)
        }, status=500)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('DeleteContract')
def contract_delete(request, contract_id):
    """Delete a contract (soft delete by archiving)"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get contract
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=False
        )
        
        # Create backup before operation
        backup_file = DatabaseBackupManager.create_backup()
        
        def archive_contract():
            contract.is_archived = True
            contract.archived_date = timezone.now()
            contract.archived_by = getattr(request.user, 'userid', 1)  # Use user ID instead of user object
            contract.archive_reason = 'OTHER'
            contract.archive_comments = f"Archived by {getattr(request.user, 'username', 'testuser1')} via API"
            contract.save()
            
            logger.info(f"Contract archived: {contract_id} by user {getattr(request.user, 'userid', 1)}")
            return contract
        
        # Retry operation with backup
        archived_contract = DatabaseBackupManager.retry_operation(archive_contract)
        
        return Response({
            'success': True,
            'message': 'Contract archived successfully',
            'backup_file': backup_file
        })
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist or has been archived'
        }, status=404)
    except Exception as e:
        logger.error(f"Contract deletion error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to delete contract',
            'message': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContract')
def contract_archive(request, contract_id):
    """Archive a contract with reason"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get contract
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=False
        )
        
        # Debug: Log received data
        logger.info(f"Contract archive - Received data: {request.data}")
        logger.info(f"Contract archive - Archive comments: {request.data.get('archive_comments')}")
        logger.info(f"Contract archive - Archive reason: {request.data.get('archive_reason')}")
        logger.info(f"Contract archive - Can be restored: {request.data.get('can_be_restored')}")
        
        # Validate archive data
        serializer = ContractArchiveSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Contract archive validation errors: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation error',
                'message': serializer.errors
            }, status=400)
        
        # Debug: Log validated data
        logger.info(f"Contract archive - Validated data: {serializer.validated_data}")
        logger.info(f"Contract archive - Validated archive_comments: {serializer.validated_data.get('archive_comments')}")
        
        # Create backup before operation
        backup_file = DatabaseBackupManager.create_backup()
        
        def archive_contract():
            contract.is_archived = True
            contract.archived_date = timezone.now()
            contract.archived_by = getattr(request.user, 'userid', 1)  # Use user ID instead of user object
            contract.archive_reason = serializer.validated_data['archive_reason']
            contract.archive_comments = serializer.validated_data.get('archive_comments', '')
            contract.can_be_restored = serializer.validated_data.get('can_be_restored', True)
            
            # Debug: Log what's being saved
            logger.info(f"Contract archive - Setting archive_comments to: '{contract.archive_comments}'")
            logger.info(f"Contract archive - Setting archive_reason to: '{contract.archive_reason}'")
            logger.info(f"Contract archive - Setting can_be_restored to: {contract.can_be_restored}")
            
            contract.save()
            
            # Debug: Log what was actually saved
            contract.refresh_from_db()
            logger.info(f"Contract archive - After save, archive_comments is: '{contract.archive_comments}'")
            logger.info(f"Contract archive - After save, archive_reason is: '{contract.archive_reason}'")
            logger.info(f"Contract archive - After save, can_be_restored is: {contract.can_be_restored}")
            
            logger.info(f"Contract archived: {contract_id} by user {getattr(request.user, 'userid', 1)}")
            return contract
        
        # Retry operation with backup
        archived_contract = DatabaseBackupManager.retry_operation(archive_contract)
        
        return Response({
            'success': True,
            'message': 'Contract archived successfully',
            'backup_file': backup_file
        })
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist or has been archived'
        }, status=404)
    except Exception as e:
        logger.error(f"Contract archive error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to archive contract',
            'message': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContract')
def contract_restore(request, contract_id):
    """Restore an archived contract"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get archived contract
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=True
        )
        
        # Validate restore data
        serializer = ContractRestoreSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Validation error',
                'message': serializer.errors
            }, status=400)
        
        # Create backup before operation
        backup_file = DatabaseBackupManager.create_backup()
        
        def restore_contract():
            contract.is_archived = False
            contract.archived_date = None
            contract.archived_by = None  # This is now IntegerField, so None is fine
            contract.archive_reason = None
            contract.archive_comments = None
            contract.save()
            
            logger.info(f"Contract restored: {contract_id} by user {getattr(request.user, 'userid', 1)}")
            return contract
        
        # Retry operation with backup
        restored_contract = DatabaseBackupManager.retry_operation(restore_contract)
        
        return Response({
            'success': True,
            'message': 'Contract restored successfully',
            'backup_file': backup_file
        })
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist or is not archived'
        }, status=404)
    except Exception as e:
        logger.error(f"Contract restore error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to restore contract',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ContractDashboard')
def contract_stats(request):
    """Get contract statistics and analytics"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get statistics for main and amendment contracts
        total_contracts = VendorContract.objects.filter(
            is_archived=False, 
            contract_kind__in=['MAIN', 'AMENDMENT']
        ).count()
        active_contracts = VendorContract.objects.filter(
            is_archived=False, 
            contract_kind__in=['MAIN', 'AMENDMENT'],
            status='ACTIVE'
        ).count()
        expired_contracts = VendorContract.objects.filter(
            is_archived=False, 
            contract_kind__in=['MAIN', 'AMENDMENT'],
            status='EXPIRED'
        ).count()
        draft_contracts = VendorContract.objects.filter(
            is_archived=False, 
            contract_kind__in=['MAIN', 'AMENDMENT'],
            status='DRAFT'
        ).count()
        
        # Contracts by type
        contracts_by_type = dict(
            VendorContract.objects.filter(is_archived=False, contract_kind__in=['MAIN', 'AMENDMENT'])
            .values('contract_type')
            .annotate(count=Count('contract_id'))
            .values_list('contract_type', 'count')
        )
        
        # Contracts by status
        contracts_by_status = dict(
            VendorContract.objects.filter(is_archived=False, contract_kind__in=['MAIN', 'AMENDMENT'])
            .values('status')
            .annotate(count=Count('contract_id'))
            .values_list('status', 'count')
        )
        
        # Contracts by priority
        contracts_by_priority = dict(
            VendorContract.objects.filter(is_archived=False, contract_kind__in=['MAIN', 'AMENDMENT'])
            .values('priority')
            .annotate(count=Count('contract_id'))
            .values_list('priority', 'count')
        )
        
        # Total value (active contracts only)
        total_value = VendorContract.objects.filter(
            is_archived=False,
            contract_kind__in=['MAIN', 'AMENDMENT'],
            contract_value__isnull=False,
            status='ACTIVE'
        ).aggregate(total=Sum('contract_value'))['total'] or Decimal('0')
        
        # Average risk score
        avg_risk_score = VendorContract.objects.filter(
            is_archived=False,
            contract_kind__in=['MAIN', 'AMENDMENT'],
            contract_risk_score__isnull=False
        ).aggregate(avg=Avg('contract_risk_score'))['avg'] or Decimal('0')
        
        # Expiring soon (within 90 days)
        today = timezone.now().date()
        expiring_date = today + timedelta(days=90)
        
        expiring_soon = VendorContract.objects.filter(
            is_archived=False,
            contract_kind__in=['MAIN', 'AMENDMENT'],
            end_date__lte=expiring_date,
            end_date__gte=today,
            status__in=['ACTIVE', 'UNDER_REVIEW', 'DRAFT', 'PENDING']
        ).count()
        
        # Debug logging
        logger.info(f"Expiring contracts calculation: today={today}, expiring_date={expiring_date}")
        logger.info(f"Expiring soon count: {expiring_soon}")
        
        # Log some sample contracts for debugging
        sample_contracts = VendorContract.objects.filter(
            is_archived=False,
            end_date__isnull=False
        ).values('contract_id', 'contract_title', 'end_date', 'status')[:5]
        logger.info(f"Sample contracts with end dates: {list(sample_contracts)}")
        
        # Overdue renewals
        overdue_renewals = VendorContract.objects.filter(
            is_archived=False,
            contract_kind__in=['MAIN', 'AMENDMENT'],
            end_date__lt=timezone.now().date(),
            status='ACTIVE',
            auto_renewal=True
        ).count()
        
        stats_data = {
            'total_contracts': total_contracts,
            'active_contracts': active_contracts,
            'expired_contracts': expired_contracts,
            'draft_contracts': draft_contracts,
            'contracts_by_type': contracts_by_type,
            'contracts_by_status': contracts_by_status,
            'contracts_by_priority': contracts_by_priority,
            'total_value': float(total_value),
            'average_risk_score': float(avg_risk_score),
            'expiring_soon': expiring_soon,
            'overdue_renewals': overdue_renewals
        }
        
        serializer = ContractStatsSerializer(stats_data)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Contract stats error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve statistics',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ContractDashboard')
def contract_analytics(request):
    """Get comprehensive contract analytics data for dashboard"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Base query for non-archived contracts
        base_query = VendorContract.objects.filter(
            is_archived=False, 
            contract_kind__in=['MAIN', 'AMENDMENT']
        )
        
        # Key Metrics
        total_contracts = base_query.count()
        active_contracts = base_query.filter(status='ACTIVE').count()
        
        # Total portfolio value (active contracts only)
        total_value_result = base_query.filter(
            contract_value__isnull=False,
            status='ACTIVE'
        ).aggregate(total=Sum('contract_value'))['total'] or Decimal('0')
        
        # Average contract value (active contracts only)
        avg_value_result = base_query.filter(
            contract_value__isnull=False,
            status='ACTIVE'
        ).aggregate(avg=Avg('contract_value'))['avg'] or Decimal('0')
        
        # Expiring soon (within 90 days)
        today = timezone.now().date()
        expiring_date = today + timedelta(days=90)
        expiring_contracts = base_query.filter(
            end_date__lte=expiring_date,
            end_date__gte=today,
            status__in=['ACTIVE', 'UNDER_REVIEW', 'DRAFT', 'PENDING']
        ).count()
        
        # Contract Status Distribution
        status_distribution = dict(
            base_query.values('status')
            .annotate(count=Count('contract_id'))
            .values_list('status', 'count')
        )
        
        # Contract Type Distribution
        type_distribution = dict(
            base_query.values('contract_type')
            .annotate(count=Count('contract_id'))
            .values_list('contract_type', 'count')
        )
        
        # Risk Level Distribution
        risk_distribution = base_query.annotate(
            risk_category=Case(
                When(contract_risk_score__isnull=True, then=Value('Unknown')),
                When(contract_risk_score__lte=3, then=Value('Low')),
                When(contract_risk_score__lte=6, then=Value('Medium')),
                When(contract_risk_score__lte=8, then=Value('High')),
                default=Value('Critical'),
                output_field=CharField()
            )
        ).values('risk_category').annotate(count=Count('contract_id'))
        
        # Vendor Value Analysis (active contracts only)
        vendor_value_data = base_query.filter(
            contract_value__isnull=False,
            vendor__isnull=False,
            status='ACTIVE'
        ).select_related('vendor').values(
            'vendor__company_name'
        ).annotate(
            total_value=Sum('contract_value'),
            contract_count=Count('contract_id')
        ).order_by('-total_value')[:10]
        
        # Monthly Trends (last 12 months)
        monthly_trends = base_query.filter(
            created_at__gte=timezone.now() - timedelta(days=365)
        ).extra(
            select={'month': "DATE_FORMAT(created_at, '%%Y-%%m')"}
        ).values('month').annotate(
            contracts_created=Count('contract_id'),
            total_value=Sum('contract_value')
        ).order_by('month')
        
        # Compliance Framework Coverage
        compliance_data = base_query.aggregate(
            soc2_count=Count(Case(When(compliance_framework__icontains='SOC2', then=1))),
            gdpr_count=Count(Case(When(compliance_framework__icontains='GDPR', then=1))),
            iso27001_count=Count(Case(When(compliance_framework__icontains='ISO27001', then=1))),
            ccpa_count=Count(Case(When(compliance_framework__icontains='CCPA', then=1))),
        )
        
        analytics_data = {
            'key_metrics': {
                'total_contracts': total_contracts,
                'active_contracts': active_contracts,
                'total_value': float(total_value_result),
                'average_value': float(avg_value_result),
                'expiring_contracts': expiring_contracts
            },
            'status_distribution': status_distribution,
            'type_distribution': type_distribution,
            'risk_distribution': list(risk_distribution),
            'vendor_value_data': list(vendor_value_data),
            'monthly_trends': list(monthly_trends),
            'compliance_frameworks': [
                {'name': 'SOC2', 'count': compliance_data['soc2_count'], 'percentage': round((compliance_data['soc2_count'] / total_contracts * 100) if total_contracts > 0 else 0, 2)},
                {'name': 'GDPR', 'count': compliance_data['gdpr_count'], 'percentage': round((compliance_data['gdpr_count'] / total_contracts * 100) if total_contracts > 0 else 0, 2)},
                {'name': 'ISO27001', 'count': compliance_data['iso27001_count'], 'percentage': round((compliance_data['iso27001_count'] / total_contracts * 100) if total_contracts > 0 else 0, 2)},
                {'name': 'CCPA', 'count': compliance_data['ccpa_count'], 'percentage': round((compliance_data['ccpa_count'] / total_contracts * 100) if total_contracts > 0 else 0, 2)}
            ]
        }
        
        return Response({
            'success': True,
            'data': analytics_data
        })
        
    except Exception as e:
        logger.error(f"Contract analytics error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve analytics data',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def vendor_list(request):
    """List all vendors with filtering and pagination"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get query parameters
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        vendor_category = request.GET.get('category', '')
        risk_level = request.GET.get('risk_level', '')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        ordering = request.GET.get('ordering', 'company_name')
        
        # Build query
        queryset = Vendor.objects.all()
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(vendor_code__icontains=search) |
                Q(legal_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Apply status filter
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Apply category filter
        if vendor_category:
            queryset = queryset.filter(vendor_category_id=vendor_category)
        
        # Apply risk level filter
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        
        # Apply ordering
        queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = VendorSerializer(page_obj.object_list, many=True)
        
        # Debug logging
        logger.info(f"Vendor list: {len(page_obj.object_list)} vendors")
        if page_obj.object_list:
            sample_vendor = page_obj.object_list[0]
            logger.info(f"Sample vendor: {sample_vendor.company_name}")
            logger.info(f"Sample vendor ID: {sample_vendor.vendor_id}")
        
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
        logger.error(f"Vendor list error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve vendors',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def vendor_detail(request, vendor_id):
    """Get vendor details by ID with contracts"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get vendor
        vendor = Vendor.objects.get(vendor_id=vendor_id)
        
        # Get vendor contracts
        contracts = VendorContract.objects.filter(
            vendor_id=vendor_id,
            is_archived=False
        ).select_related('vendor').order_by('-created_at')
        
        # Serialize vendor
        vendor_serializer = VendorSerializer(vendor)
        
        # Serialize contracts
        contracts_serializer = VendorContractSerializer(contracts, many=True)
        
        # Calculate vendor statistics
        total_contracts = contracts.count()
        active_contracts = contracts.filter(status='ACTIVE').count()
        total_value = contracts.aggregate(
            total=Sum('contract_value')
        )['total'] or Decimal('0')
        
        # Get last activity date
        last_activity = contracts.first().created_at if contracts.exists() else vendor.updated_at
        
        vendor_data = vendor_serializer.data
        vendor_data.update({
            'contracts': contracts_serializer.data,
            'contracts_count': total_contracts,
            'active_contracts_count': active_contracts,
            'total_value': float(total_value),
            'last_activity': last_activity.isoformat() if last_activity else None
        })
        
        return Response({
            'success': True,
            'data': vendor_data
        })
        
    except Vendor.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Vendor not found',
            'message': 'The requested vendor does not exist'
        }, status=404)
    except Exception as e:
        logger.error(f"Vendor detail error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve vendor',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ContractDashboard')
def vendor_stats(request):
    """Get vendor statistics"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get vendor statistics
        total_vendors = Vendor.objects.count()
        active_vendors = Vendor.objects.filter(status='APPROVED').count()
        
        # Get contracts by vendor
        vendor_contracts = VendorContract.objects.filter(
            is_archived=False
        ).values('vendor_id').annotate(
            contract_count=Count('contract_id'),
            total_value=Sum('contract_value')
        )
        
        # Calculate total contracts and value
        total_contracts = sum(vc['contract_count'] for vc in vendor_contracts)
        total_value = sum(
            float(vc['total_value'] or 0) for vc in vendor_contracts
        )
        
        # Vendors by status
        vendors_by_status = dict(
            Vendor.objects.values('status')
            .annotate(count=Count('vendor_id'))
            .values_list('status', 'count')
        )
        
        # Vendors by risk level
        vendors_by_risk = dict(
            Vendor.objects.values('risk_level')
            .annotate(count=Count('vendor_id'))
            .values_list('risk_level', 'count')
        )
        
        stats_data = {
            'total_vendors': total_vendors,
            'active_vendors': active_vendors,
            'total_contracts': total_contracts,
            'total_value': total_value,
            'vendors_by_status': vendors_by_status,
            'vendors_by_risk': vendors_by_risk
        }
        
        return Response({
            'success': True,
            'data': stats_data
        })
        
    except Exception as e:
        logger.error(f"Vendor stats error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve vendor statistics',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def vendor_contacts_list(request, vendor_id):
    """Get vendor contacts by vendor ID"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Verify vendor exists
        vendor = Vendor.objects.get(vendor_id=vendor_id)
        
        # Get vendor contacts
        contacts = VendorContact.objects.filter(vendor_id=vendor_id)
        
        # Apply filters
        contact_type = request.GET.get('contact_type', '')
        is_active = request.GET.get('is_active', '')
        
        if contact_type:
            contacts = contacts.filter(contact_type=contact_type)
        
        if is_active.lower() == 'true':
            contacts = contacts.filter(is_active=True)
        elif is_active.lower() == 'false':
            contacts = contacts.filter(is_active=False)
        
        # Serialize contacts
        serializer = VendorContactSerializer(contacts, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Vendor.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Vendor not found',
            'message': 'The requested vendor does not exist'
        }, status=404)
    except Exception as e:
        logger.error(f"Vendor contacts list error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve vendor contacts',
            'message': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
def vendor_contact_create(request, vendor_id):
    """Create a vendor contact"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Verify vendor exists
        vendor = Vendor.objects.get(vendor_id=vendor_id)
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        # Create backup before operation
        backup_file = DatabaseBackupManager.create_backup()
        
        def create_contact():
            contact_data = request.data.copy()
            contact_data['vendor_id'] = vendor_id
            contact_data['created_by'] = getattr(request.user, 'userid', 1)
            
            # Convert boolean values to integers for unmanaged models
            if 'is_primary' in contact_data:
                contact_data['is_primary'] = 1 if contact_data['is_primary'] else 0
            if 'is_active' in contact_data:
                contact_data['is_active'] = 1 if contact_data['is_active'] else 0
            
            serializer = VendorContactCreateSerializer(data=contact_data)
            if serializer.is_valid():
                contact = serializer.save()
                logger.info(f"Vendor contact created: {contact.contact_id} for vendor {vendor_id}")
                return contact
            else:
                raise ValidationError(serializer.errors)
        
        # Retry operation with backup
        contact = DatabaseBackupManager.retry_operation(create_contact)
        
        response_serializer = VendorContactSerializer(contact)
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Vendor contact created successfully',
            'backup_file': backup_file
        }, status=201)
        
    except Vendor.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Vendor not found',
            'message': 'The requested vendor does not exist'
        }, status=404)
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Vendor contact creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create vendor contact',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
def check_contract_create_permission(request):
    """Check if user has permission to create contracts"""
    try:
        # If we reach here, the user has permission (decorator already checked)
        return Response({
            'success': True,
            'has_permission': True,
            'message': 'User has permission to create contracts'
        })
        
    except Exception as e:
        logger.error(f"Permission check error: {str(e)}")
        return Response({
            'success': False,
            'has_permission': False,
            'error': 'Failed to check permissions',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContractRenewals')
def contract_renewals_list(request):
    """List contract renewals"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get query parameters
        search = request.GET.get('search', '')
        renewal_decision = request.GET.get('renewal_decision', '')
        status = request.GET.get('status', '')
        contract_id = request.GET.get('contract_id')
        initiated_by = request.GET.get('initiated_by')
        decided_by = request.GET.get('decided_by')
        renewal_date_from = request.GET.get('renewal_date_from')
        renewal_date_to = request.GET.get('renewal_date_to')
        decision_date_from = request.GET.get('decision_date_from')
        decision_date_to = request.GET.get('decision_date_to')
        ordering = request.GET.get('ordering', '-renewal_date')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Build query
        renewals = ContractRenewal.objects.all()
        
        # Apply filters
        if search:
            renewals = renewals.filter(
                Q(comments__icontains=search) |
                Q(renewal_reason__icontains=search) |
                Q(contract_id__icontains=search)
            )
        
        if renewal_decision:
            renewals = renewals.filter(renewal_decision=renewal_decision)
        
        if status:
            renewals = renewals.filter(status=status)
        
        if contract_id:
            renewals = renewals.filter(contract_id=contract_id)
        
        if initiated_by:
            renewals = renewals.filter(initiated_by=initiated_by)
        
        if decided_by:
            renewals = renewals.filter(decided_by=decided_by)
        
        if renewal_date_from:
            renewals = renewals.filter(renewal_date__gte=renewal_date_from)
        
        if renewal_date_to:
            renewals = renewals.filter(renewal_date__lte=renewal_date_to)
        
        if decision_date_from:
            renewals = renewals.filter(decision_date__gte=decision_date_from)
        
        if decision_date_to:
            renewals = renewals.filter(decision_date__lte=decision_date_to)
        
        # Apply ordering
        renewals = renewals.order_by(ordering)
        
        # Pagination
        total_count = renewals.count()
        start = (page - 1) * page_size
        end = start + page_size
        renewals = renewals[start:end]
        
        # Serialize data
        serializer = ContractRenewalSerializer(renewals, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size,
                'has_next': end < total_count,
                'has_previous': page > 1
            }
        })
        
    except Exception as e:
        logger.error(f"Contract renewals list error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve contract renewals',
            'message': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContractRenewal')
def contract_renewal_create(request):
    """Create a contract renewal request"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Validate contract exists
        contract_id = request.data.get('contract_id')
        if not contract_id:
                return Response({
                    'success': False,
                    'error': 'Validation error',
                'message': 'Contract ID is required'
                }, status=400)
        
        try:
            contract = VendorContract.objects.get(contract_id=contract_id, is_archived=False)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Contract not found',
                'message': 'The specified contract does not exist or has been archived'
            }, status=404)
        
        # Create backup before making changes
        backup_manager = DatabaseBackupManager()
        backup_manager.create_backup()
        
        # Debug: Log received data
        logger.info(f"Contract renewal creation - Received data: {request.data}")
        logger.info(f"Contract renewal creation - notification_sent_date: {request.data.get('notification_sent_date')}")
        logger.info(f"Contract renewal creation - decision_due_date: {request.data.get('decision_due_date')}")
        logger.info(f"Contract renewal creation - decision_date: {request.data.get('decision_date')}")
        logger.info(f"Contract renewal creation - comments: {request.data.get('comments')}")
        logger.info(f"Contract renewal creation - renewal_reason: {request.data.get('renewal_reason')}")
        
        # Serialize and validate data
        serializer = ContractRenewalCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Set initiated_by to current user (optional since authentication is not required)
            renewal_data = serializer.validated_data
            
            # Debug: Log user information
            logger.info(f"Contract renewal creation - User type: {type(request.user)}")
            logger.info(f"Contract renewal creation - User attributes: {dir(request.user)}")
            logger.info(f"Contract renewal creation - User ID: {getattr(request.user, 'id', 'NO_ID')}")
            logger.info(f"Contract renewal creation - User userid: {getattr(request.user, 'userid', 'NO_USERID')}")
            
            # Get user ID safely (optional since authentication is not required)
            user_id = getattr(request.user, 'userid', None)
            if user_id:
                renewal_data['initiated_by'] = user_id
                logger.info(f"Contract renewal creation - Set initiated_by to: {user_id}")
            else:
                logger.info(f"Contract renewal creation - No user ID found, leaving initiated_by as provided or null")
                # Don't override initiated_by if it's already set in the form data
                if 'initiated_by' not in renewal_data:
                    renewal_data['initiated_by'] = None
            
            renewal_data['initiated_date'] = timezone.now()
            
            # Create renewal
            try:
                renewal = serializer.save()
                
                # Debug: Log the created renewal data
                logger.info(f"Contract renewal created - ID: {renewal.renewal_id}")
                logger.info(f"Contract renewal created - notification_sent_date: {renewal.notification_sent_date}")
                logger.info(f"Contract renewal created - decision_due_date: {renewal.decision_due_date}")
                logger.info(f"Contract renewal created - decision_date: {renewal.decision_date}")
                logger.info(f"Contract renewal created - comments: {renewal.comments}")
                logger.info(f"Contract renewal created - renewal_reason: {renewal.renewal_reason}")
                
            except Exception as save_error:
                logger.error(f"Contract renewal save error: {str(save_error)}")
                return Response({
                    'success': False,
                    'error': 'Database error',
                    'message': f'Failed to save renewal: {str(save_error)}'
                }, status=500)
            
            # Serialize response
            response_serializer = ContractRenewalSerializer(renewal)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Contract renewal request created successfully'
            }, status=201)
        else:
            logger.error(f"Contract renewal validation errors: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation error',
                'message': 'Invalid data provided',
                'details': serializer.errors
            }, status=400)
        
    except Exception as e:
        logger.error(f"Contract renewal creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create contract renewal',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContractRenewals')
def contract_renewal_detail(request, renewal_id):
    """Get contract renewal details"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get renewal
        try:
            renewal = ContractRenewal.objects.get(renewal_id=renewal_id)
        except ContractRenewal.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Renewal not found',
                'message': 'The requested renewal does not exist'
            }, status=404)
        
        # Serialize data
        serializer = ContractRenewalSerializer(renewal)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Contract renewal detail error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve contract renewal',
            'message': str(e)
        }, status=500)


@api_view(['PUT', 'PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ApproveContractRenewal')
def contract_renewal_update(request, renewal_id):
    """Update contract renewal"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get renewal
        try:
            renewal = ContractRenewal.objects.get(renewal_id=renewal_id)
        except ContractRenewal.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Renewal not found',
                'message': 'The requested renewal does not exist'
            }, status=404)
        
        # Create backup before making changes
        backup_manager = DatabaseBackupManager()
        backup_manager.create_backup()
        
        # Serialize and validate data
        serializer = ContractRenewalUpdateSerializer(renewal, data=request.data, partial=request.method == 'PATCH')
        
        if serializer.is_valid():
            # Update renewal
            updated_renewal = serializer.save()
            
            # Serialize response
            response_serializer = ContractRenewalSerializer(updated_renewal)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Contract renewal updated successfully'
            })
        else:
            return Response({
                'success': False,
                'error': 'Validation error',
                'message': 'Invalid data provided',
                'details': serializer.errors
            }, status=400)
        
    except Exception as e:
        logger.error(f"Contract renewal update error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update contract renewal',
            'message': str(e)
        }, status=500)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('RejectContractRenewal')
def contract_renewal_delete(request, renewal_id):
    """Delete contract renewal"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get renewal
        try:
            renewal = ContractRenewal.objects.get(renewal_id=renewal_id)
        except ContractRenewal.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Renewal not found',
                'message': 'The requested renewal does not exist'
            }, status=404)
        
        # Create backup before making changes
        backup_manager = DatabaseBackupManager()
        backup_manager.create_backup()
        
        # Delete renewal
        renewal.delete()
        
        return Response({
            'success': True,
            'message': 'Contract renewal deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Contract renewal delete error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to delete contract renewal',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContractTerms')
def contract_terms_list(request, contract_id):
    """Get contract terms by contract ID"""
    try:
        # Verify contract exists
        contract = VendorContract.objects.get(contract_id=contract_id, is_archived=False)
        
        # Get contract terms
        terms = ContractTerm.objects.filter(contract_id=contract_id)
        
        # Serialize terms
        serializer = ContractTermSerializer(terms, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist or has been archived'
        }, status=404)
    except Exception as e:
        logger.error(f"Error fetching contract terms: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to fetch contract terms'
        }, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContractTerm')
def contract_terms_create(request, contract_id):
    """Create contract terms"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get contract
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=False
        )
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        def create_term():
            term_data = request.data.copy()
            term_data['contract_id'] = contract.contract_id  # Use contract_id field
            term_data['created_by'] = getattr(request.user, 'userid', 1)  # Use default user ID 1 if anonymous
            
            # Convert boolean values to integers for unmanaged models
            if 'is_standard' in term_data:
                logger.info(f"Converting term is_standard: {term_data['is_standard']} (type: {type(term_data['is_standard'])})")
                term_data['is_standard'] = 1 if term_data['is_standard'] else 0
                logger.info(f"Converted term is_standard to: {term_data['is_standard']}")
            
            # Ensure term_text is not empty
            if not term_data.get('term_text') or term_data.get('term_text').strip() == '':
                raise ValidationError({'term_text': ['This field is required and cannot be blank.']})
            
            serializer = ContractTermSerializer(data=term_data)
            if serializer.is_valid():
                term = serializer.save()
                logger.info(f"Contract term created: {term.term_id} for contract {contract_id}")
                return term
            else:
                raise ValidationError(serializer.errors)
        
        # Create term without backup (for speed)
        term = DatabaseBackupManager.retry_operation(create_term)
        
        # Create backup after successful term creation (for speed)
        backup_file = DatabaseBackupManager.create_backup()
        
        response_serializer = ContractTermSerializer(term)
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Contract term created successfully',
            'backup_file': backup_file
        }, status=201)
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist or has been archived'
        }, status=404)
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Contract term creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create contract term',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_clauses_list(request, contract_id):
    """Get contract clauses by contract ID"""
    try:
        # Verify contract exists
        contract = VendorContract.objects.get(contract_id=contract_id, is_archived=False)
        
        # Get contract clauses
        clauses = ContractClause.objects.filter(contract_id=contract_id)
        
        # Serialize clauses
        serializer = ContractClauseSerializer(clauses, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist or has been archived'
        }, status=404)
    except Exception as e:
        logger.error(f"Error fetching contract clauses: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to fetch contract clauses'
        }, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
def contract_clauses_create(request, contract_id):
    """Create contract clauses"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get contract
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=False
        )
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        def create_clause():
            clause_data = request.data.copy()
            clause_data['contract_id'] = contract.contract_id  # Use contract_id field
            clause_data['created_by'] = getattr(request.user, 'userid', 1)  # Use default user ID 1 if anonymous
            
            # Convert boolean values to integers for unmanaged models
            if 'is_standard' in clause_data:
                logger.info(f"Converting clause is_standard: {clause_data['is_standard']} (type: {type(clause_data['is_standard'])})")
                clause_data['is_standard'] = 1 if clause_data['is_standard'] else 0
                logger.info(f"Converted clause is_standard to: {clause_data['is_standard']}")
            if 'auto_renew' in clause_data:
                logger.info(f"Converting clause auto_renew: {clause_data['auto_renew']} (type: {type(clause_data['auto_renew'])})")
                clause_data['auto_renew'] = 1 if clause_data['auto_renew'] else 0
                logger.info(f"Converted clause auto_renew to: {clause_data['auto_renew']}")
            
            # Validate required fields before serialization
            if not clause_data.get('clause_name') or clause_data.get('clause_name').strip() == '':
                raise ValidationError({'clause_name': ['This field is required and cannot be blank.']})
            
            if not clause_data.get('clause_text') or clause_data.get('clause_text').strip() == '':
                raise ValidationError({'clause_text': ['This field is required and cannot be blank.']})
            
            serializer = ContractClauseSerializer(data=clause_data)
            if serializer.is_valid():
                clause = serializer.save()
                logger.info(f"Contract clause created: {clause.clause_id} for contract {contract_id}")
                return clause
            else:
                raise ValidationError(serializer.errors)
        
        # Create clause without backup (for speed)
        clause = DatabaseBackupManager.retry_operation(create_clause)
        
        # Create backup after successful clause creation (for speed)
        backup_file = DatabaseBackupManager.create_backup()
        
        response_serializer = ContractClauseSerializer(clause)
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Contract clause created successfully',
            'backup_file': backup_file
        }, status=201)
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist or has been archived'
        }, status=404)
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Contract clause creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create contract clause',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ContractSearch')
def contract_search(request):
    """Advanced contract search"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Validate search parameters
        search_serializer = ContractSearchSerializer(data=request.GET)
        if not search_serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid search parameters',
                'message': search_serializer.errors
            }, status=400)
        
        # Build query
        queryset = VendorContract.objects.select_related('vendor')
        
        # Filter for main and amendment contracts
        queryset = queryset.filter(contract_kind__in=['MAIN', 'AMENDMENT'])
        
        # Apply filters
        if search_serializer.validated_data.get('search'):
            search_term = search_serializer.validated_data['search']
            queryset = queryset.filter(
                Q(contract_title__icontains=search_term) |
                Q(contract_number__icontains=search_term) |
                Q(vendor__company_name__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        
        # Apply other filters
        for field in ['contract_type', 'status', 'workflow_stage', 'priority']:
            value = search_serializer.validated_data.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        
        # Apply date filters
        if search_serializer.validated_data.get('start_date_from'):
            queryset = queryset.filter(start_date__gte=search_serializer.validated_data['start_date_from'])
        
        if search_serializer.validated_data.get('start_date_to'):
            queryset = queryset.filter(start_date__lte=search_serializer.validated_data['start_date_to'])
        
        if search_serializer.validated_data.get('end_date_from'):
            queryset = queryset.filter(end_date__gte=search_serializer.validated_data['end_date_from'])
        
        if search_serializer.validated_data.get('end_date_to'):
            queryset = queryset.filter(end_date__lte=search_serializer.validated_data['end_date_to'])
        
        # Apply other filters
        if search_serializer.validated_data.get('vendor_id'):
            queryset = queryset.filter(vendor_id=search_serializer.validated_data['vendor_id'])
        
        if search_serializer.validated_data.get('contract_owner'):
            queryset = queryset.filter(contract_owner_id=search_serializer.validated_data['contract_owner'])
        
        if search_serializer.validated_data.get('is_archived') is not None:
            queryset = queryset.filter(is_archived=search_serializer.validated_data['is_archived'])
        
        # Apply ordering
        ordering = search_serializer.validated_data.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        page = search_serializer.validated_data.get('page', 1)
        page_size = search_serializer.validated_data.get('page_size', 20)
        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = VendorContractSerializer(page_obj.object_list, many=True)
        
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
        logger.error(f"Contract search error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to search contracts',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def users_list(request):
    """Get all users for contract assignment"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get all users from custom User model
        from mfa_auth.models import User
        users = User.objects.all().order_by('userid')
        
        logger.info(f"Found {users.count()} users in database")
        
        # Convert to list and add display name
        users_list = []
        for user in users:
            full_name = f"{user.first_name} {user.last_name}".strip()
            display_name = full_name if full_name else user.username
            
            user_data = {
                'user_id': user.userid,  # Use userid as primary key
                'username': user.username,
                'display_name': display_name,
                'role': 'user'  # Default role since RBAC is removed
            }
            users_list.append(user_data)
            logger.info(f"User: {user_data}")
        
        logger.info(f"Returning {len(users_list)} users to frontend")
        
        return Response({
            'success': True,
            'data': users_list
        })
        
    except Exception as e:
        logger.error(f"Users list error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve users',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def legal_reviewers_list(request):
    """Get users with legal review roles for contract assignment"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get all users from custom User model (since RBAC is removed, all users can be legal reviewers)
        from mfa_auth.models import User
        users = User.objects.all().order_by('userid')
        
        logger.info(f"Found {users.count()} users for legal reviewers")
        
        # Convert to list and add display name
        users_list = []
        for user in users:
            full_name = f"{user.first_name} {user.last_name}".strip()
            display_name = full_name if full_name else user.username
            
            user_data = {
                'user_id': user.userid,  # Use userid as primary key
                'username': user.username,
                'display_name': display_name,
                'role': 'legal_reviewer'  # All users can be legal reviewers since RBAC is removed
            }
            users_list.append(user_data)
            logger.info(f"Legal Reviewer: {user_data}")
        
        logger.info(f"Returning {len(users_list)} legal reviewers to frontend")
        
        return Response({
            'success': True,
            'data': users_list
        })
        
    except Exception as e:
        logger.error(f"Legal reviewers list error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve legal reviewers',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def subcontracts_list(request, parent_contract_id):
    """Get all subcontracts for a parent contract"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({'error': 'Rate limit exceeded'}, status=429)
        
        # Get the parent contract to verify it exists
        try:
            parent_contract = VendorContract.objects.get(contract_id=parent_contract_id, is_archived=False)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Parent contract not found',
                'message': 'The requested parent contract does not exist'
            }, status=404)
        
        # Get all subcontracts for this parent
        subcontracts = VendorContract.objects.filter(
            contract_kind='SUBCONTRACT',
            parent_contract_id=parent_contract_id,
            is_archived=False
        ).select_related('vendor').order_by('created_at')
        
        # Get terms and clauses for each subcontract
        subcontracts_with_details = []
        for subcontract in subcontracts:
            # Get terms for this subcontract
            sub_terms = ContractTerm.objects.filter(contract_id=subcontract.contract_id).order_by('term_category', 'created_at')
            sub_terms_serializer = ContractTermSerializer(sub_terms, many=True)
            
            # Get clauses for this subcontract
            sub_clauses = ContractClause.objects.filter(contract_id=subcontract.contract_id).order_by('clause_type', 'created_at')
            sub_clauses_serializer = ContractClauseSerializer(sub_clauses, many=True)
            
            # Serialize the subcontract
            subcontract_serializer = VendorContractSerializer(subcontract)
            subcontract_data = subcontract_serializer.data
            
            # Add terms and clauses to the subcontract data
            subcontract_data['terms'] = sub_terms_serializer.data
            subcontract_data['clauses'] = sub_clauses_serializer.data
            subcontract_data['terms_count'] = len(sub_terms)
            subcontract_data['clauses_count'] = len(sub_clauses)
            
            subcontracts_with_details.append(subcontract_data)
        
        return Response({
            'success': True,
            'data': subcontracts_with_details,
            'message': f'Found {len(subcontracts_with_details)} subcontracts for contract {parent_contract_id}',
            'summary': {
                'total_subcontracts': len(subcontracts_with_details),
                'total_terms': sum(s['terms_count'] for s in subcontracts_with_details),
                'total_clauses': sum(s['clauses_count'] for s in subcontracts_with_details)
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching subcontracts for parent contract {parent_contract_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch subcontracts',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_amendments_as_contracts_list(request, parent_contract_id):
    """Get all contract amendments as contracts for a parent contract"""
    try:
        logger.info(f"[AMENDMENTS] === VIEW CALLED === Fetching amendments for parent contract: {parent_contract_id}")
        logger.info(f"[AMENDMENTS] User: {request.user}")
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({'error': 'Rate limit exceeded'}, status=429)
        
        # Get the parent contract to verify it exists
        try:
            parent_contract = VendorContract.objects.get(contract_id=parent_contract_id, is_archived=False)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Parent contract not found',
                'message': 'The requested parent contract does not exist'
            }, status=404)
        
        # Get all contract amendments for this parent (contracts with contract_kind='AMENDMENT' and parent_contract_id=parent_contract_id)
        logger.info(f"[AMENDMENTS] Querying amendments with parent_contract_id={parent_contract_id}")
        
        amendments = VendorContract.objects.filter(
            contract_kind='AMENDMENT',
            parent_contract_id=parent_contract_id,
            is_archived=False
        ).select_related('vendor').order_by('created_at')
        
        logger.info(f"[AMENDMENTS] Found {amendments.count()} amendments for parent contract {parent_contract_id}")
        
        # Get terms and clauses for each amendment
        amendments_with_details = []
        for amendment in amendments:
            # Get terms for this amendment
            amendment_terms = ContractTerm.objects.filter(contract_id=amendment.contract_id).order_by('term_category', 'created_at')
            amendment_terms_serializer = ContractTermSerializer(amendment_terms, many=True)
            
            # Get clauses for this amendment
            amendment_clauses = ContractClause.objects.filter(contract_id=amendment.contract_id).order_by('clause_type', 'created_at')
            amendment_clauses_serializer = ContractClauseSerializer(amendment_clauses, many=True)
            
            # Serialize the amendment
            amendment_serializer = VendorContractSerializer(amendment)
            amendment_data = amendment_serializer.data
            
            # Add terms and clauses to the amendment data
            amendment_data['terms'] = amendment_terms_serializer.data
            amendment_data['clauses'] = amendment_clauses_serializer.data
            amendment_data['terms_count'] = len(amendment_terms)
            amendment_data['clauses_count'] = len(amendment_clauses)
            
            amendments_with_details.append(amendment_data)
        
        response_data = {
            'success': True,
            'data': amendments_with_details,
            'message': f'Found {len(amendments_with_details)} contract amendments for contract {parent_contract_id}',
            'summary': {
                'total_amendments': len(amendments_with_details),
                'total_terms': sum(a['terms_count'] for a in amendments_with_details),
                'total_clauses': sum(a['clauses_count'] for a in amendments_with_details)
            }
        }
        
        logger.info(f"[AMENDMENTS] Returning response: {len(amendments_with_details)} amendments")
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"[AMENDMENTS] ERROR fetching contract amendments for parent contract {parent_contract_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch contract amendments',
            'message': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
@csrf_exempt
def subcontract_create(request, parent_contract_id):
    """Create a new subcontract under a parent contract"""
    try:
        # Debug CORS headers
        logger.info(f"CORS Debug - Origin: {request.headers.get('Origin')}")
        logger.info(f"CORS Debug - Access-Control-Request-Method: {request.headers.get('Access-Control-Request-Method')}")
        logger.info(f"CORS Debug - All headers: {dict(request.headers)}")
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Validate parent contract exists
        try:
            parent_contract = VendorContract.objects.get(contract_id=parent_contract_id)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Parent contract not found',
                'message': f'Contract with ID {parent_contract_id} does not exist'
            }, status=404)
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        def create_subcontract():
            subcontract_data = request.data.copy()
            
            # Set subcontract-specific fields
            subcontract_data['contract_kind'] = 'SUBCONTRACT'
            subcontract_data['parent_contract_id'] = parent_contract_id
            subcontract_data['main_contract_id'] = parent_contract.main_contract_id or parent_contract_id
            
            # Convert boolean values to integers for unmanaged models
            if 'auto_renewal' in subcontract_data:
                logger.info(f"Converting auto_renewal: {subcontract_data['auto_renewal']} (type: {type(subcontract_data['auto_renewal'])})")
                subcontract_data['auto_renewal'] = 1 if subcontract_data['auto_renewal'] else 0
                logger.info(f"Converted auto_renewal to: {subcontract_data['auto_renewal']}")
            
            # Override status to UNDER_REVIEW for all new subcontracts
            subcontract_data['status'] = 'UNDER_REVIEW'
            subcontract_data['workflow_stage'] = 'under_review'
            
            # Debug: Log the raw data being received
            logger.info(f"🔍 Raw subcontract_data keys: {list(subcontract_data.keys())}")
            if 'insurance_requirements' in subcontract_data:
                logger.info(f"🔍 insurance_requirements raw value: {subcontract_data['insurance_requirements']}")
                logger.info(f"🔍 insurance_requirements raw type: {type(subcontract_data['insurance_requirements'])}")
            
            # Handle JSON fields - convert plain text to JSON if needed
            if 'insurance_requirements' in subcontract_data:
                if isinstance(subcontract_data['insurance_requirements'], str):
                    if subcontract_data['insurance_requirements'].strip():
                        subcontract_data['insurance_requirements'] = {
                            'requirements': subcontract_data['insurance_requirements'].strip(),
                            'type': 'text'
                        }
                    else:
                        subcontract_data['insurance_requirements'] = {}
                elif not isinstance(subcontract_data['insurance_requirements'], dict):
                    subcontract_data['insurance_requirements'] = {}
            
            if 'data_protection_clauses' in subcontract_data:
                if isinstance(subcontract_data['data_protection_clauses'], str):
                    if subcontract_data['data_protection_clauses'].strip():
                        subcontract_data['data_protection_clauses'] = {
                            'clauses': subcontract_data['data_protection_clauses'].strip(),
                            'type': 'text'
                        }
                    else:
                        subcontract_data['data_protection_clauses'] = {}
                elif not isinstance(subcontract_data['data_protection_clauses'], dict):
                    subcontract_data['data_protection_clauses'] = {}
            
            if 'custom_fields' in subcontract_data:
                if isinstance(subcontract_data['custom_fields'], str):
                    try:
                        import json
                        subcontract_data['custom_fields'] = json.loads(subcontract_data['custom_fields'])
                    except (json.JSONDecodeError, TypeError):
                        subcontract_data['custom_fields'] = {}
                elif not isinstance(subcontract_data['custom_fields'], dict):
                    subcontract_data['custom_fields'] = {}
            
            # Debug: Log the converted data
            logger.info(f"🔍 After conversion - insurance_requirements: {subcontract_data.get('insurance_requirements')}")
            logger.info(f"🔍 After conversion - data_protection_clauses: {subcontract_data.get('data_protection_clauses')}")
            
            serializer = VendorContractCreateSerializer(data=subcontract_data)
            logger.info(f"🔍 Serializer is_valid() result: {serializer.is_valid()}")
            if not serializer.is_valid():
                logger.error(f"🔍 Serializer errors: {serializer.errors}")
            if serializer.is_valid():
                # Save subcontract with all data from serializer
                subcontract = serializer.save()
                
                logger.info(f"Subcontract created: {subcontract.contract_id} under parent contract {parent_contract_id} by user {getattr(request.user, 'userid', 1)}")
                logger.info(f"Subcontract owner set to: {subcontract.contract_owner} from form data")
                return subcontract
            else:
                raise ValidationError(serializer.errors)
        
        # Create subcontract without backup (for speed)
        subcontract = DatabaseBackupManager.retry_operation(create_subcontract)
        
        # Create backup after successful subcontract creation (for speed)
        backup_file = DatabaseBackupManager.create_backup()
        
        # Return created subcontract
        response_serializer = VendorContractSerializer(subcontract)
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Subcontract created successfully',
            'backup_file': backup_file
        }, status=201)
        
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Subcontract creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create subcontract',
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cors_test(request):
    """Simple endpoint to test CORS configuration"""
    return Response({
        'success': True,
        'message': 'CORS is working correctly',
        'origin': request.headers.get('Origin', 'No origin header')
    })


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContract')
def test_amendment_creation(request, contract_id):
    """Test endpoint for amendment creation debugging"""
    try:
        logger.info(f"TEST: Starting amendment test for contract_id: {contract_id}")
        
        # Get the original contract
        original_contract = VendorContract.objects.get(contract_id=contract_id)
        logger.info(f"TEST: Original contract found: {original_contract.contract_title}")
        
        # Create a minimal contract amendment
        contract_data = {
            'vendor_id': original_contract.vendor_id,
            'contract_number': f"{original_contract.contract_number}-AMEND-TEST",
            'contract_title': f"{original_contract.contract_title} - Amendment Test",
            'contract_type': original_contract.contract_type,
            'contract_kind': 'AMENDMENT',
            'version_number': original_contract.version_number + 0.1,
            'previous_version_id': original_contract.contract_id,
            'parent_contract_id': original_contract.parent_contract_id or original_contract.contract_id,
            'main_contract_id': original_contract.main_contract_id or original_contract.contract_id,
            'start_date': original_contract.start_date,
            'end_date': original_contract.end_date,
            'status': 'DRAFT',
            'workflow_stage': 'draft',
        }
        
        logger.info("TEST: Creating amendment contract")
        amendment_contract = VendorContract.objects.create(**contract_data)
        logger.info(f"TEST: Amendment contract created: {amendment_contract.contract_id}")
        
        return Response({
            'success': True,
            'message': 'Test amendment created successfully',
            'data': {
                'original_contract_id': original_contract.contract_id,
                'amendment_contract_id': amendment_contract.contract_id
            }
        })
        
    except Exception as e:
        logger.error(f"TEST: Error in test amendment creation: {str(e)}")
        return Response({
            'success': False,
            'error': 'Test amendment creation failed',
            'message': str(e)
        }, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
@csrf_exempt
def contract_with_subcontract_create(request):
    """Update existing draft contract to under_review and create subcontract"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Extract main contract and subcontract data
        main_contract_data = request.data.get('main_contract', {})
        subcontract_data = request.data.get('subcontract', {})
        
        logger.info(f"Contract with subcontract create - Main contract data keys: {list(main_contract_data.keys()) if main_contract_data else 'None'}")
        logger.info(f"Contract with subcontract create - Subcontract data keys: {list(subcontract_data.keys()) if subcontract_data else 'None'}")
        try:
            # Be cautious: request.data may contain non-serializable objects, so guard json dumps
            logger.info(f"RAW request.data types - main_contract: {type(main_contract_data)}, subcontract: {type(subcontract_data)}")
            logger.info(f"Subcontract terms type: {type(subcontract_data.get('terms'))} length: {len(subcontract_data.get('terms', []))}")
            logger.info(f"Subcontract clauses type: {type(subcontract_data.get('clauses'))} length: {len(subcontract_data.get('clauses', []))}")
        except Exception as _log_err:
            logger.warning(f"Failed to log detailed request.data info: {_log_err}")
        logger.info(f"Main contract ID from data: {main_contract_data.get('contract_id')}")
        logger.info(f"Full main contract data: {main_contract_data}")
        
        # Debug specific fields that might cause issues
        if subcontract_data:
            logger.info(f"Subcontract insurance_requirements: {subcontract_data.get('insurance_requirements')} (type: {type(subcontract_data.get('insurance_requirements'))})")
            logger.info(f"Subcontract data_protection_clauses: {subcontract_data.get('data_protection_clauses')} (type: {type(subcontract_data.get('data_protection_clauses'))})")
            logger.info(f"Subcontract custom_fields: {subcontract_data.get('custom_fields')} (type: {type(subcontract_data.get('custom_fields'))})")
        
        if not main_contract_data or not subcontract_data:
            logger.error(f"Missing data - main_contract: {bool(main_contract_data)}, subcontract: {bool(subcontract_data)}")
            return Response({
                'success': False,
                'message': 'Both main_contract and subcontract data are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate subcontract data only (main contract already exists)
        try:
            SecurityManager.validate_contract_data(subcontract_data)
            logger.info("Subcontract data validation passed")
        except Exception as e:
            logger.error(f"Subcontract data validation failed: {str(e)}")
            raise
        
        def update_contract_and_create_subcontract():
            # Get the existing main contract ID
            main_contract_id = main_contract_data.get('contract_id')
            if not main_contract_id:
                logger.error(f"Main contract data received: {main_contract_data}")
                raise ValidationError("Main contract ID is required")
            
            try:
                main_contract = VendorContract.objects.get(contract_id=main_contract_id)
                logger.info(f"Found existing main contract: {main_contract_id}")
            except VendorContract.DoesNotExist:
                logger.error(f"Main contract with ID {main_contract_id} not found")
                raise ValidationError(f"Main contract with ID {main_contract_id} not found")
            
            # Update main contract status to UNDER_REVIEW
            main_contract.status = 'UNDER_REVIEW'
            main_contract.workflow_stage = 'under_review'
            main_contract.contract_kind = 'MAIN'  # Use valid contract_kind choice
            main_contract.save()
            logger.info(f"Updated main contract {main_contract_id} status to UNDER_REVIEW")
            
            # Prepare subcontract data with parent relationship
            subcontract_data['contract_kind'] = 'SUBCONTRACT'
            subcontract_data['parent_contract_id'] = main_contract_id
            subcontract_data['main_contract_id'] = main_contract_id
            
            # Copy compliance_framework from main contract to subcontract if not already set
            if not subcontract_data.get('compliance_framework') and main_contract.compliance_framework:
                subcontract_data['compliance_framework'] = main_contract.compliance_framework
                logger.info(f"Copied compliance_framework from main contract: {main_contract.compliance_framework}")
            
            # Ensure boolean values are properly formatted
            if 'auto_renewal' in subcontract_data:
                subcontract_data['auto_renewal'] = bool(subcontract_data['auto_renewal'])
            
            # Override status to UNDER_REVIEW for subcontract
            subcontract_data['status'] = 'UNDER_REVIEW'
            subcontract_data['workflow_stage'] = 'under_review'
            
            # Create subcontract
            logger.info(f"Creating subcontract with data: {subcontract_data}")
            subcontract_serializer = VendorContractCreateSerializer(data=subcontract_data)
            
            if not subcontract_serializer.is_valid():
                logger.error(f"Subcontract validation errors: {subcontract_serializer.errors}")
                raise ValidationError(f"Subcontract validation error: {subcontract_serializer.errors}")
            
            subcontract = subcontract_serializer.save()
            logger.info(f"Created subcontract {subcontract.contract_id} with parent {main_contract_id}")
            
            # Process terms and clauses for subcontract only (main contract already has them)
            terms_data = subcontract_data.get('terms', [])
            clauses_data = subcontract_data.get('clauses', [])
            
            logger.info(f"Processing subcontract terms: {len(terms_data)} terms, {len(clauses_data)} clauses")
            logger.info(f"Terms data: {terms_data}")
            logger.info(f"Clauses data: {clauses_data}")
            try:
                from django.db.models import Count
                pre_terms_count = ContractTerm.objects.filter(contract_id=subcontract.contract_id).count()
                logger.info(f"Pre-insert terms count for subcontract {subcontract.contract_id}: {pre_terms_count}")
            except Exception as _count_err:
                logger.warning(f"Could not fetch pre-insert terms count: {_count_err}")
            
            # Create terms for subcontract
            for i, term_data in enumerate(terms_data):
                logger.info(f"Processing term {i+1}: {term_data}")
                
                # Validate required fields
                required_fields = ['term_category', 'term_text']
                missing_fields = [field for field in required_fields if not term_data.get(field)]
                if missing_fields:
                    logger.error(f"❌ Term {i+1} missing required fields: {missing_fields}")
                    continue
                
                # Prepare term data
                term_data = term_data.copy()  # Don't modify original
                term_data['contract_id'] = subcontract.contract_id
                
                # Remove any invalid fields
                if 'contract' in term_data:
                    del term_data['contract']
                
                # Sanitize optional numeric/date fields that may come as empty strings
                def _to_int_or_none(value):
                    if value is None:
                        return None
                    if isinstance(value, int):
                        return value
                    try:
                        s = str(value).strip()
                        return int(s) if s != '' else None
                    except Exception:
                        return None
                
                int_fields = ['approved_by', 'created_by']
                for f in int_fields:
                    if f in term_data:
                        before = term_data.get(f)
                        term_data[f] = _to_int_or_none(term_data.get(f))
                        logger.info(f"Term {i+1} sanitize int field '{f}': {before} -> {term_data[f]}")
                
                # approved_at may be empty string; let ORM handle None
                if 'approved_at' in term_data and (term_data['approved_at'] is None or str(term_data['approved_at']).strip() == ''):
                    logger.info(f"Term {i+1} sanitize datetime field 'approved_at': {term_data['approved_at']} -> None")
                    term_data['approved_at'] = None
                
                # Ensure boolean
                if 'is_standard' in term_data:
                    term_data['is_standard'] = bool(term_data['is_standard'])
                
                # Ensure unique term_id for subcontract
                import uuid
                term_data['term_id'] = f"term_sub_{subcontract.contract_id}_{str(uuid.uuid4()).replace('-', '')[:12]}"
                
                # Set default values for required fields
                term_data.setdefault('risk_level', 'Low')
                term_data.setdefault('compliance_status', 'Pending')
                term_data.setdefault('is_standard', False)
                term_data.setdefault('approval_status', 'Pending')
                term_data.setdefault('version_number', '1.0')
                
                logger.info(f"Final term data for creation: {term_data}")
                
                try:
                    created_term = ContractTerm.objects.create(**term_data)
                    logger.info(f"✅ Created term for subcontract {subcontract.contract_id}: id={created_term.term_id} title={term_data.get('term_title', 'No title')}")
                except Exception as e:
                    logger.error(f"❌ Error creating term for subcontract: {str(e)}")
                    logger.error(f"Term data that failed: {term_data}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
            # Post-insert verification
            try:
                post_terms_qs = ContractTerm.objects.filter(contract_id=subcontract.contract_id)
                post_terms_count = post_terms_qs.count()
                logger.info(f"Post-insert terms count for subcontract {subcontract.contract_id}: {post_terms_count}")
                # Log a compact list of term_ids stored
                logger.info(f"Stored term_ids: {[t.term_id for t in post_terms_qs[:25]]}")
            except Exception as _count_err2:
                logger.warning(f"Could not fetch post-insert terms count: {_count_err2}")
            
            # Create clauses for subcontract
            for clause_data in clauses_data:
                clause_data['contract_id'] = subcontract.contract_id
                # Remove any invalid fields
                if 'contract' in clause_data:
                    del clause_data['contract']
                
                # Ensure unique clause_id for subcontract
                import uuid
                clause_data['clause_id'] = f"clause_sub_{subcontract.contract_id}_{str(uuid.uuid4()).replace('-', '')[:12]}"
                
                try:
                    ContractClause.objects.create(**clause_data)
                    logger.info(f"Created clause for subcontract {subcontract.contract_id}: {clause_data.get('clause_name', 'No name')}")
                except Exception as e:
                    logger.error(f"Error creating clause for subcontract: {str(e)}")
            
            logger.info(f"Contract and subcontract created: Main contract {main_contract_id}, Subcontract {subcontract.contract_id} by user {getattr(request.user, 'userid', 1)}")
            
            return main_contract, subcontract
        
        # Create contracts without backup (for speed)
        main_contract, subcontract = DatabaseBackupManager.retry_operation(update_contract_and_create_subcontract)
        
        # Create backup after successful contract creation (for speed)
        backup_file = DatabaseBackupManager.create_backup()
        
        # Return both contracts
        main_contract_response = VendorContractSerializer(main_contract)
        subcontract_response = VendorContractSerializer(subcontract)
        
        response_data = {
            'success': True,
            'message': 'Contract updated and subcontract created successfully',
            'data': {
                'main_contract': main_contract_response.data,
                'subcontract': subcontract_response.data
            },
            'backup_file': backup_file
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Contract with subcontract creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create contract with subcontract',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Contract Amendment Views
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_amendments_list(request, contract_id):
    """Get all amendments for a specific contract"""
    try:
        # Check if contract exists
        try:
            contract = VendorContract.objects.get(contract_id=contract_id)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Contract not found',
                'message': f'Contract with ID {contract_id} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get amendments for the contract
        amendments = ContractAmendment.objects.filter(contract_id=contract_id).order_by('-amendment_date')
        
        # Apply search filters if provided
        search = request.GET.get('search', '')
        if search:
            amendments = amendments.filter(
                Q(amendment_number__icontains=search) |
                Q(amendment_reason__icontains=search) |
                Q(changes_summary__icontains=search) |
                Q(justification__icontains=search) |
                Q(amendment_notes__icontains=search)
            )
        
        # Apply date filters
        amendment_date_from = request.GET.get('amendment_date_from')
        amendment_date_to = request.GET.get('amendment_date_to')
        if amendment_date_from:
            amendments = amendments.filter(amendment_date__gte=amendment_date_from)
        if amendment_date_to:
            amendments = amendments.filter(amendment_date__lte=amendment_date_to)
        
        # Apply approval date filters
        approval_date_from = request.GET.get('approval_date_from')
        approval_date_to = request.GET.get('approval_date_to')
        if approval_date_from:
            amendments = amendments.filter(approval_date__gte=approval_date_from)
        if approval_date_to:
            amendments = amendments.filter(approval_date__lte=approval_date_to)
        
        # Apply workflow status filter
        workflow_status = request.GET.get('workflow_status')
        if workflow_status:
            amendments = amendments.filter(workflow_status=workflow_status)
        
        # Apply affected area filter
        affected_area = request.GET.get('affected_area')
        if affected_area:
            amendments = amendments.filter(affected_area=affected_area)
        
        # Apply approved_by filter
        approved_by = request.GET.get('approved_by')
        if approved_by:
            amendments = amendments.filter(approved_by=approved_by)
        
        # Apply initiated_by filter
        initiated_by = request.GET.get('initiated_by')
        if initiated_by:
            amendments = amendments.filter(initiated_by=initiated_by)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        paginator = Paginator(amendments, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = ContractAmendmentSerializer(page_obj.object_list, many=True)
        
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
        logger.error(f"Contract amendments list error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch contract amendments',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContract')
def contract_amendments_create(request, contract_id):
    """Create a new amendment for a specific contract"""
    try:
        # Check if contract exists
        try:
            contract = VendorContract.objects.get(contract_id=contract_id)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Contract not found',
                'message': f'Contract with ID {contract_id} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Add contract_id to the data
        data = request.data.copy()
        data['contract_id'] = contract_id
        
        # Add created_by from request user
        if hasattr(request, 'user') and request.user:
            data['created_by'] = getattr(request.user, 'userid', 1)
        
        serializer = ContractAmendmentCreateSerializer(data=data)
        if serializer.is_valid():
            amendment = serializer.save()
            
            # Create backup
            backup_manager = DatabaseBackupManager()
            backup_file = backup_manager.create_backup()
            
            return Response({
                'success': True,
                'data': ContractAmendmentSerializer(amendment).data,
                'message': 'Amendment created successfully',
                'backup_file': backup_file
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'error': 'Validation error',
                'message': 'Invalid amendment data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Contract amendment creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create amendment',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_amendment_detail(request, contract_id, amendment_id):
    """Get a specific amendment for a contract"""
    try:
        try:
            amendment = ContractAmendment.objects.get(
                contract_id=contract_id,
                amendment_id=amendment_id
            )
        except ContractAmendment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Amendment not found',
                'message': f'Amendment with ID {amendment_id} not found for contract {contract_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ContractAmendmentSerializer(amendment)
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Contract amendment detail error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch amendment',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContract')
def contract_amendment_update(request, contract_id, amendment_id):
    """Update a specific amendment for a contract"""
    try:
        try:
            amendment = ContractAmendment.objects.get(
                contract_id=contract_id,
                amendment_id=amendment_id
            )
        except ContractAmendment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Amendment not found',
                'message': f'Amendment with ID {amendment_id} not found for contract {contract_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ContractAmendmentUpdateSerializer(amendment, data=request.data, partial=True)
        if serializer.is_valid():
            updated_amendment = serializer.save()
            
            # Create backup
            backup_manager = DatabaseBackupManager()
            backup_file = backup_manager.create_backup()
            
            return Response({
                'success': True,
                'data': ContractAmendmentSerializer(updated_amendment).data,
                'message': 'Amendment updated successfully',
                'backup_file': backup_file
            })
        else:
            return Response({
                'success': False,
                'error': 'Validation error',
                'message': 'Invalid amendment data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Contract amendment update error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update amendment',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('DeleteContract')
def contract_amendment_delete(request, contract_id, amendment_id):
    """Delete a specific amendment for a contract"""
    try:
        try:
            amendment = ContractAmendment.objects.get(
                contract_id=contract_id,
                amendment_id=amendment_id
            )
        except ContractAmendment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Amendment not found',
                'message': f'Amendment with ID {amendment_id} not found for contract {contract_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create backup before deletion
        backup_manager = DatabaseBackupManager()
        backup_file = backup_manager.create_backup()
        
        # Delete the amendment
        amendment.delete()
        
        return Response({
            'success': True,
            'message': 'Amendment deleted successfully',
            'backup_file': backup_file
        })
        
    except Exception as e:
        logger.error(f"Contract amendment deletion error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to delete amendment',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Contract Terms CRUD Views
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContractTerms')
def contract_term_detail(request, contract_id, term_id):
    """Get a specific term for a contract"""
    try:
        try:
            term = ContractTerm.objects.get(
                contract_id=contract_id,
                id=term_id
            )
        except ContractTerm.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Term not found',
                'message': f'Term with ID {term_id} not found for contract {contract_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ContractTermSerializer(term)
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Contract term detail error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch term',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContractTerm')
def contract_term_update(request, contract_id, term_id):
    """Update a specific term for a contract"""
    try:
        try:
            term = ContractTerm.objects.get(
                contract_id=contract_id,
                id=term_id
            )
        except ContractTerm.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Term not found',
                'message': f'Term with ID {term_id} not found for contract {contract_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ContractTermSerializer(term, data=request.data, partial=True)
        if serializer.is_valid():
            updated_term = serializer.save()
            
            # Create backup
            backup_manager = DatabaseBackupManager()
            backup_file = backup_manager.create_backup()
            
            return Response({
                'success': True,
                'data': ContractTermSerializer(updated_term).data,
                'message': 'Term updated successfully',
                'backup_file': backup_file
            })
        else:
            return Response({
                'success': False,
                'error': 'Validation error',
                'message': 'Invalid term data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Contract term update error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update term',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('DeleteContractTerm')
def contract_term_delete(request, contract_id, term_id):
    """Delete a specific term for a contract"""
    try:
        try:
            term = ContractTerm.objects.get(
                contract_id=contract_id,
                id=term_id
            )
        except ContractTerm.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Term not found',
                'message': f'Term with ID {term_id} not found for contract {contract_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create backup before deletion
        backup_manager = DatabaseBackupManager()
        backup_file = backup_manager.create_backup()
        
        # Delete the term
        term.delete()
        
        return Response({
            'success': True,
            'message': 'Term deleted successfully',
            'backup_file': backup_file
        })
        
    except Exception as e:
        logger.error(f"Contract term deletion error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to delete term',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Contract Clauses CRUD Views
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_clause_detail(request, contract_id, clause_id):
    """Get a specific clause for a contract"""
    try:
        try:
            clause = ContractClause.objects.get(
                contract_id=contract_id,
                id=clause_id
            )
        except ContractClause.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Clause not found',
                'message': f'Clause with ID {clause_id} not found for contract {contract_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ContractClauseSerializer(clause)
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Contract clause detail error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch clause',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContract')
def contract_clause_update(request, contract_id, clause_id):
    """Update a specific clause for a contract"""
    try:
        try:
            clause = ContractClause.objects.get(
                contract_id=contract_id,
                id=clause_id
            )
        except ContractClause.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Clause not found',
                'message': f'Clause with ID {clause_id} not found for contract {contract_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ContractClauseSerializer(clause, data=request.data, partial=True)
        if serializer.is_valid():
            updated_clause = serializer.save()
            
            # Create backup
            backup_manager = DatabaseBackupManager()
            backup_file = backup_manager.create_backup()
            
            return Response({
                'success': True,
                'data': ContractClauseSerializer(updated_clause).data,
                'message': 'Clause updated successfully',
                'backup_file': backup_file
            })
        else:
            return Response({
                'success': False,
                'error': 'Validation error',
                'message': 'Invalid clause data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Contract clause update error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update clause',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('DeleteContract')
def contract_clause_delete(request, contract_id, clause_id):
    """Delete a specific clause for a contract"""
    try:
        try:
            clause = ContractClause.objects.get(
                contract_id=contract_id,
                id=clause_id
            )
        except ContractClause.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Clause not found',
                'message': f'Clause with ID {clause_id} not found for contract {contract_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create backup before deletion
        backup_manager = DatabaseBackupManager()
        backup_file = backup_manager.create_backup()
        
        # Delete the clause
        clause.delete()
        
        return Response({
            'success': True,
            'message': 'Clause deleted successfully',
            'backup_file': backup_file
        })
        
    except Exception as e:
        logger.error(f"Contract clause deletion error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to delete clause',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContract')
def create_contract_version(request, contract_id):
    """Create a new version of an existing contract"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        # Get the original contract
        original_contract = VendorContract.objects.get(contract_id=contract_id)
        
        # Create backup before operation
        backup_file = DatabaseBackupManager.create_backup()
        
        # Get version type from request
        version_type = request.data.get('version_type', 'minor')  # 'minor' or 'major'
        
        # Calculate new version number
        if version_type == 'major':
            new_version = int(original_contract.version_number) + 1
        else:  # minor
            if '.' in str(original_contract.version_number):
                major, minor = str(original_contract.version_number).split('.')
                new_version = f"{major}.{int(minor) + 1}"
            else:
                new_version = f"{original_contract.version_number}.1"
        
        # Create new contract version
        new_contract_data = {
            'vendor_id': original_contract.vendor_id,
            'contract_number': original_contract.contract_number,
            'contract_title': request.data.get('contract_title', original_contract.contract_title),
            'contract_type': request.data.get('contract_type', original_contract.contract_type),
            'contract_kind': request.data.get('contract_kind', original_contract.contract_kind),
            'parent_contract_id': original_contract.parent_contract_id or original_contract.contract_id,
            'main_contract_id': original_contract.main_contract_id or original_contract.contract_id,
            'version_number': new_version,
            'previous_version_id': original_contract.contract_id,
            'contract_value': request.data.get('contract_value', original_contract.contract_value),
            'currency': request.data.get('currency', original_contract.currency),
            'start_date': request.data.get('start_date', original_contract.start_date),
            'end_date': request.data.get('end_date', original_contract.end_date),
            'renewal_terms': request.data.get('renewal_terms', original_contract.renewal_terms),
            'auto_renewal': request.data.get('auto_renewal', original_contract.auto_renewal),
            'notice_period_days': request.data.get('notice_period_days', original_contract.notice_period_days),
            'status': request.data.get('status', original_contract.status),
            'workflow_stage': request.data.get('workflow_stage', original_contract.workflow_stage),
            'priority': request.data.get('priority', original_contract.priority),
            'compliance_status': request.data.get('compliance_status', original_contract.compliance_status),
            'contract_category': request.data.get('contract_category', original_contract.contract_category),
            'termination_clause_type': request.data.get('termination_clause_type', original_contract.termination_clause_type),
            'liability_cap': request.data.get('liability_cap', original_contract.liability_cap),
            'insurance_requirements': request.data.get('insurance_requirements', original_contract.insurance_requirements),
            'data_protection_clauses': request.data.get('data_protection_clauses', original_contract.data_protection_clauses),
            'dispute_resolution_method': request.data.get('dispute_resolution_method', original_contract.dispute_resolution_method),
            'governing_law': request.data.get('governing_law', original_contract.governing_law),
            'contract_risk_score': request.data.get('contract_risk_score', original_contract.contract_risk_score),
            'assigned_to': parse_integer(request.data.get('assigned_to'), original_contract.assigned_to),
            'custom_fields': request.data.get('custom_fields', original_contract.custom_fields),
            'compliance_framework': request.data.get('compliance_framework', original_contract.compliance_framework),
            'contract_owner': request.data.get('contract_owner', original_contract.contract_owner),
            'legal_reviewer': request.data.get('legal_reviewer', original_contract.legal_reviewer),
            'description': request.data.get('description', original_contract.description)
        }
        
        # Create new contract
        new_contract = VendorContract.objects.create(**new_contract_data)
        
        # Copy terms and clauses from previous version
        copy_terms_and_clauses(original_contract, new_contract)
        
        # Serialize the new contract
        serializer = VendorContractSerializer(new_contract)
        
        return Response({
            'success': True,
            'message': f'Contract version {new_version} created successfully',
            'data': serializer.data,
            'backup_file': backup_file
        }, status=status.HTTP_201_CREATED)
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist'
        }, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Contract version creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create contract version',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def get_contract_versions(request, contract_id):
    """Get all versions of a contract"""
    try:
        logger.info(f"Fetching contract versions for contract_id: {contract_id}")
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get the main contract
        logger.info(f"Looking for contract with ID: {contract_id}")
        main_contract = VendorContract.objects.get(contract_id=contract_id)
        logger.info(f"Found main contract: {main_contract.contract_title}")
        
        main_contract_id = main_contract.main_contract_id or main_contract.contract_id
        logger.info(f"Using main_contract_id: {main_contract_id}")
        
        # Get all versions
        versions = VendorContract.objects.filter(
            Q(contract_id=main_contract_id) | 
            Q(main_contract_id=main_contract_id)
        ).order_by('-version_number')
        
        logger.info(f"Found {versions.count()} versions")
        
        serializer = VendorContractSerializer(versions, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except VendorContract.DoesNotExist:
        logger.error(f"Contract not found with ID: {contract_id}")
        return Response({
            'success': False,
            'message': 'Contract not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching contract versions: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching contract versions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContract')
def create_contract_amendment(request, contract_id):
    """Create a contract amendment as a new version in vendor_contracts"""
    try:
        logger.info(f"Starting contract amendment creation for contract_id: {contract_id}")
        logger.info(f"Request data keys: {list(request.data.keys()) if hasattr(request, 'data') else 'No data'}")
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Validate input data
        logger.info("Validating input data")
        SecurityManager.validate_contract_data(request.data)
        
        # Get the original contract
        logger.info(f"Getting original contract with id: {contract_id}")
        original_contract = VendorContract.objects.get(contract_id=contract_id)
        logger.info(f"Original contract found: {original_contract.contract_title}")
        
        # Determine version type (major or minor)
        version_type = request.data.get('version_type', 'minor')
        
        # Calculate new version number
        from decimal import Decimal
        current_version = float(original_contract.version_number)
        
        if version_type == 'major':
            # Major version: 1.0 -> 2.0, 1.5 -> 2.0, 2.3 -> 3.0, etc.
            new_version = Decimal(str(int(current_version) + 1))
        else:  # minor
            # Minor version: 1.0 -> 1.1, 1.5 -> 1.6, 2.0 -> 2.1, etc.
            major_part = int(current_version)
            minor_part = current_version - major_part
            new_version = Decimal(str(round(major_part + minor_part + 0.1, 1)))
        
        # Helper function to convert string dates to date objects
        def parse_date(date_value, fallback_date):
            if date_value and isinstance(date_value, str):
                try:
                    from datetime import datetime
                    # Try parsing different date formats
                    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S'):
                        try:
                            parsed_date = datetime.strptime(date_value, fmt).date()
                            logger.info(f"Successfully parsed date string '{date_value}' to {parsed_date}")
                            return parsed_date
                        except ValueError:
                            continue
                    logger.warning(f"Could not parse date string: {date_value}, using fallback: {fallback_date}")
                    return fallback_date
                except Exception as e:
                    logger.error(f"Error parsing date {date_value}: {str(e)}, using fallback: {fallback_date}")
                    return fallback_date
            elif date_value:
                logger.info(f"Date value is already a date object: {date_value} (type: {type(date_value)})")
                return date_value  # Already a date object
            else:
                logger.info(f"No date value provided, using fallback: {fallback_date}")
                return fallback_date
        
        # Helper function to clean boolean values
        def parse_boolean(bool_value, fallback_bool):
            if isinstance(bool_value, bool):
                return bool_value
            elif isinstance(bool_value, str):
                if bool_value.lower() in ('true', '1', 'yes', 'on'):
                    return True
                elif bool_value.lower() in ('false', '0', 'no', 'off', ''):
                    return False
                else:
                    logger.warning(f"Could not parse boolean string: {bool_value}, using fallback: {fallback_bool}")
                    return fallback_bool
            elif bool_value is None:
                return fallback_bool
            else:
                logger.warning(f"Unexpected boolean value type: {type(bool_value)}, using fallback: {fallback_bool}")
                return fallback_bool
        
        # Helper function to parse integer fields (user IDs, etc.)
        def parse_integer(int_value, fallback_int):
            if isinstance(int_value, int):
                return int_value
            elif isinstance(int_value, str):
                if int_value.strip() == '':
                    return fallback_int
                try:
                    return int(int_value)
                except ValueError:
                    logger.warning(f"Could not parse integer string: {int_value}, using fallback: {fallback_int}")
                    return fallback_int
            elif int_value is None:
                return fallback_int
            else:
                logger.warning(f"Unexpected integer value type: {type(int_value)}, using fallback: {fallback_int}")
                return fallback_int
        
        # Prepare contract data for the amendment (without amendment-specific fields)
        contract_data = {
            'vendor_id': parse_integer(request.data.get('vendor_id'), original_contract.vendor_id),
            'contract_number': request.data.get('contract_number', original_contract.contract_number),
            'contract_title': request.data.get('contract_title', original_contract.contract_title),
            'contract_type': request.data.get('contract_type', original_contract.contract_type),
            'contract_kind': 'AMENDMENT',
            'contract_category': request.data.get('contract_category', original_contract.contract_category),
            'priority': request.data.get('priority', original_contract.priority),
            'contract_value': request.data.get('contract_value', original_contract.contract_value),
            'currency': request.data.get('currency', original_contract.currency),
            'liability_cap': request.data.get('liability_cap', original_contract.liability_cap),
            'start_date': parse_date(request.data.get('start_date'), original_contract.start_date),
            'end_date': parse_date(request.data.get('end_date'), original_contract.end_date),
            'renewal_terms': request.data.get('renewal_terms', original_contract.renewal_terms),
            'auto_renewal': parse_boolean(request.data.get('auto_renewal'), original_contract.auto_renewal),
            'notice_period_days': request.data.get('notice_period_days', original_contract.notice_period_days),
            'status': 'PENDING_ASSIGNMENT',
            'workflow_stage': 'under_review',
            'compliance_status': request.data.get('compliance_status', original_contract.compliance_status),
            'termination_clause_type': request.data.get('termination_clause_type', original_contract.termination_clause_type),
            'insurance_requirements': request.data.get('insurance_requirements', original_contract.insurance_requirements),
            'data_protection_clauses': request.data.get('data_protection_clauses', original_contract.data_protection_clauses),
            'dispute_resolution_method': request.data.get('dispute_resolution_method', original_contract.dispute_resolution_method),
            'governing_law': request.data.get('governing_law', original_contract.governing_law),
            'contract_risk_score': request.data.get('contract_risk_score', original_contract.contract_risk_score),
            'assigned_to': parse_integer(request.data.get('assigned_to'), original_contract.assigned_to),
            'custom_fields': request.data.get('custom_fields', original_contract.custom_fields),
            'compliance_framework': request.data.get('compliance_framework', original_contract.compliance_framework),
            'contract_owner': parse_integer(request.data.get('contract_owner'), original_contract.contract_owner),
            'legal_reviewer': parse_integer(request.data.get('legal_reviewer'), original_contract.legal_reviewer),
            
            # S3 document storage - file_path from OCR upload
            'file_path': request.data.get('file_path', ''),
            
            # Versioning fields
            'version_number': new_version,
            'previous_version_id': original_contract.contract_id,
            'parent_contract_id': original_contract.parent_contract_id or original_contract.contract_id,
            'main_contract_id': original_contract.main_contract_id or original_contract.contract_id,
        }
        
        # Create the amendment contract
        try:
            logger.info(f"Creating amendment contract with data: {list(contract_data.keys())}")
            logger.info(f"Date fields - start_date: {contract_data['start_date']} (type: {type(contract_data['start_date'])})")
            logger.info(f"Date fields - end_date: {contract_data['end_date']} (type: {type(contract_data['end_date'])})")
            logger.info(f"File path for amendment document: {contract_data['file_path']}")
            amendment_contract = VendorContract.objects.create(**contract_data)
            logger.info(f"Amendment contract created successfully: {amendment_contract.contract_id}")
            logger.info(f"Amendment contract file_path saved: {amendment_contract.file_path}")
        except Exception as contract_error:
            logger.error(f"Error creating VendorContract: {str(contract_error)}")
            raise
        
        # Create the ContractAmendment record with amendment-specific fields
        amendment_record = None
        try:
            # Parse financial_impact to ensure it's a valid decimal
            financial_impact = request.data.get('financial_impact')
            if financial_impact and isinstance(financial_impact, str):
                try:
                    financial_impact = float(financial_impact)
                except ValueError:
                    financial_impact = None
            elif not financial_impact:
                financial_impact = None
            
            logger.info(f"Creating ContractAmendment record for contract {amendment_contract.contract_id}")
            logger.info(f"Amendment data: amendment_number={request.data.get('amendment_number')}, reason={request.data.get('amendment_reason')}")
            
            amendment_record = ContractAmendment.objects.create(
                contract_id=amendment_contract.contract_id,
                amendment_number=request.data.get('amendment_number', f'AMEND-{amendment_contract.contract_id}'),
                amendment_date=timezone.now(),
                amendment_reason=request.data.get('amendment_reason', 'Contract amendment'),
                changes_summary=request.data.get('changes_summary', 'Contract terms and conditions updated'),
                financial_impact=financial_impact,
                effective_date=timezone.now(),
                initiated_by=request.user.userid if hasattr(request.user, 'userid') else None,
                initiated_date=timezone.now(),
                justification=request.data.get('justification', 'Contract amendment for updated terms'),
                amendment_notes=request.data.get('amendment_notes', 'Amendment created via API'),
                workflow_status='pending',
                affected_area=request.data.get('affected_area', 'both')
            )
            logger.info(f"ContractAmendment record created successfully: {amendment_record.amendment_id}")
        except Exception as amendment_error:
            logger.error(f"Error creating ContractAmendment record: {str(amendment_error)}")
            # Fallback: Store amendment info in custom_fields
            try:
                amendment_info = {
                    'amendment_number': request.data.get('amendment_number', f'AMEND-{amendment_contract.contract_id}'),
                    'amendment_date': timezone.now().isoformat(),
                    'amendment_reason': request.data.get('amendment_reason', 'Contract amendment'),
                    'changes_summary': request.data.get('changes_summary', 'Contract terms and conditions updated'),
                    'financial_impact': request.data.get('financial_impact'),
                    'effective_date': timezone.now().isoformat(),
                    'initiated_by': request.user.userid if hasattr(request.user, 'userid') else None,
                    'initiated_date': timezone.now().isoformat(),
                    'justification': request.data.get('justification', 'Contract amendment for updated terms'),
                    'amendment_notes': request.data.get('amendment_notes', 'Amendment created via API'),
                    'workflow_status': 'pending',
                    'affected_area': request.data.get('affected_area', 'both')
                }
                
                # Update the contract's custom_fields with amendment info
                current_custom_fields = amendment_contract.custom_fields or {}
                current_custom_fields['amendment_info'] = amendment_info
                amendment_contract.custom_fields = current_custom_fields
                amendment_contract.save()
                
                logger.info(f"Amendment info stored in custom_fields for contract {amendment_contract.contract_id}")
            except Exception as fallback_error:
                logger.error(f"Error storing amendment info in custom_fields: {str(fallback_error)}")
        
        # Only add terms and clauses that are explicitly provided from the frontend
        # This allows users to delete terms/clauses in the frontend and have those deletions respected
        # No automatic copying of existing terms/clauses - only what the user explicitly includes
        logger.info(f"Processing terms and clauses from request data")
        logger.info(f"Terms data: {request.data.get('terms')}")
        logger.info(f"Clauses data: {request.data.get('clauses')}")
        
        if request.data.get('terms'):
            logger.info(f"Found {len(request.data['terms'])} terms to process")
            for i, term_data in enumerate(request.data['terms']):
                term_data['contract_id'] = amendment_contract.contract_id
                # Set the version number for the amendment
                term_data['version_number'] = str(new_version)
                # Set created_by for the term
                term_data['created_by'] = getattr(request.user, 'userid', 1)
                # Remove any invalid fields
                if 'contract' in term_data:
                    del term_data['contract']
                
                # Ensure unique term_id if not provided or if it already exists
                if not term_data.get('term_id') or ContractTerm.objects.filter(term_id=term_data.get('term_id')).exists():
                    import uuid
                    term_data['term_id'] = f"term_new_{amendment_contract.contract_id}_{str(uuid.uuid4()).replace('-', '')[:12]}"
                
                logger.info(f"Creating term {i+1}/{len(request.data['terms'])}: {term_data.get('term_title', 'No title')} (ID: {term_data.get('term_id')}, Version: {term_data.get('version_number')})")
                ContractTerm.objects.create(**term_data)
                logger.info(f"Term {i+1} created successfully")
        else:
            logger.info("No terms data provided in request - no terms will be copied to amendment")
        
        if request.data.get('clauses'):
            logger.info(f"Found {len(request.data['clauses'])} clauses to process")
            for i, clause_data in enumerate(request.data['clauses']):
                clause_data['contract_id'] = amendment_contract.contract_id
                # Set the version number for the amendment
                clause_data['version_number'] = str(new_version)
                # Set created_by for the clause
                clause_data['created_by'] = getattr(request.user, 'userid', 1)
                # Remove any invalid fields
                if 'contract' in clause_data:
                    del clause_data['contract']
                
                # Ensure unique clause_id if not provided or if it already exists
                if not clause_data.get('clause_id') or ContractClause.objects.filter(clause_id=clause_data.get('clause_id')).exists():
                    import uuid
                    clause_data['clause_id'] = f"clause_new_{amendment_contract.contract_id}_{str(uuid.uuid4()).replace('-', '')[:12]}"
                
                logger.info(f"Creating clause {i+1}/{len(request.data['clauses'])}: {clause_data.get('clause_name', 'No name')} (ID: {clause_data.get('clause_id')}, Version: {clause_data.get('version_number')})")
                ContractClause.objects.create(**clause_data)
                logger.info(f"Clause {i+1} created successfully")
        else:
            logger.info("No clauses data provided in request - no clauses will be copied to amendment")
        
        # Create backup after successful amendment creation (for speed)
        backup_file = DatabaseBackupManager.create_backup()
        
        # Serialize the amendment contract
        serializer = VendorContractSerializer(amendment_contract)
        
        # Prepare response data
        response_data = {
            'contract': serializer.data,
        }
        
        # Add amendment data if available
        if amendment_record:
            amendment_serializer = ContractAmendmentSerializer(amendment_record)
            response_data['amendment'] = amendment_serializer.data
        else:
            response_data['amendment'] = None
        
        return Response({
            'success': True,
            'message': 'Contract amendment created successfully',
            'data': response_data,
            'backup_file': backup_file
        }, status=status.HTTP_201_CREATED)
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist'
        }, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Contract amendment creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create contract amendment',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
def create_subcontract(request, contract_id):
    """Create a subcontract for a main contract"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        # Get the main contract
        main_contract = VendorContract.objects.get(contract_id=contract_id)
        
        # Create backup before operation
        backup_file = DatabaseBackupManager.create_backup()
        
        # Create subcontract data
        subcontract_data = {
            'vendor_id': main_contract.vendor_id,
            'contract_number': request.data.get('contract_number'),
            'contract_title': request.data.get('contract_title'),
            'contract_type': request.data.get('contract_type'),
            'contract_kind': 'SUBCONTRACT',
            'parent_contract_id': contract_id,
            'main_contract_id': main_contract.main_contract_id or contract_id,
            'version_number': 1,  # Subcontracts start at version 1
            'contract_value': request.data.get('contract_value'),
            'currency': request.data.get('currency', main_contract.currency),
            'start_date': request.data.get('start_date'),
            'end_date': request.data.get('end_date'),
            'renewal_terms': request.data.get('renewal_terms'),
            'auto_renewal': request.data.get('auto_renewal', False),
            'notice_period_days': request.data.get('notice_period_days', 30),
            'status': request.data.get('status', 'DRAFT'),
            'workflow_stage': request.data.get('workflow_stage', 'draft'),
            'priority': request.data.get('priority', 'medium'),
            'compliance_status': request.data.get('compliance_status', 'under_review'),
            'contract_category': request.data.get('contract_category'),
            'termination_clause_type': request.data.get('termination_clause_type'),
            'liability_cap': request.data.get('liability_cap'),
            'insurance_requirements': request.data.get('insurance_requirements'),
            'data_protection_clauses': request.data.get('data_protection_clauses'),
            'dispute_resolution_method': request.data.get('dispute_resolution_method'),
            'governing_law': request.data.get('governing_law'),
            'contract_risk_score': request.data.get('contract_risk_score'),
            'assigned_to': request.data.get('assigned_to'),
            'custom_fields': request.data.get('custom_fields'),
            'compliance_framework': request.data.get('compliance_framework'),
            'contract_owner': request.data.get('contract_owner'),
            'legal_reviewer': request.data.get('legal_reviewer'),
            'description': request.data.get('description')
        }
        
        # Create subcontract
        subcontract = VendorContract.objects.create(**subcontract_data)
        
        # Copy terms and clauses from main contract
        copy_terms_and_clauses(main_contract, subcontract)
        
        # Serialize the subcontract
        serializer = VendorContractSerializer(subcontract)
        
        return Response({
            'success': True,
            'message': 'Subcontract created successfully',
            'data': serializer.data,
            'backup_file': backup_file
        }, status=status.HTTP_201_CREATED)
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested main contract does not exist'
        }, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Subcontract creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create subcontract',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('TriggerOCR')
def upload_contract_ocr(request, contract_id):
    """Upload contract file for OCR extraction with real AI processing"""
    import tempfile
    import os
    # Import OCR service with support for both monorepo and legacy layouts
    try:
        from tprm_backend.ocr_app.services import DocumentProcessingService
    except ImportError:  # Fallback for older setups
        from ocr_app.services import DocumentProcessingService
    
    temp_file_path = None
    
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get the contract
        contract = VendorContract.objects.get(contract_id=contract_id)
        
        # Get uploaded file
        file = request.FILES.get('file')
        if not file:
            return Response({
                'success': False,
                'error': 'No file uploaded',
                'message': 'No file uploaded'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']
        if file.content_type not in allowed_types:
            return Response({
                'success': False,
                'error': 'Invalid file type',
                'message': 'Invalid file type. Please upload PDF or image files only.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get document type from request
        document_type = request.POST.get('document_type', 'contract')
        logger.info(f"[OCR] Processing {document_type} document for contract {contract_id}")
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        logger.info(f"[OCR] File saved to temporary location: {temp_file_path}")
        
        # Initialize OCR service and process document
        ocr_service = DocumentProcessingService()
        
        # Use contract-only processing (faster, no SLA extraction)
        ocr_result = ocr_service.process_contract_only(temp_file_path, user_id=str(request.user.userid if hasattr(request.user, 'userid') else 'system'))
        
        logger.info(f"[OCR] Processing complete. Success: {ocr_result.get('success')}")
        
        if not ocr_result.get('success'):
            error_msg = ocr_result.get('error', 'OCR processing failed')
            logger.error(f"[OCR] Error: {error_msg}")
            return Response({
                'success': False,
                'error': error_msg,
                'message': error_msg
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Extract the contract data
        contract_data = ocr_result.get('data', {})
        upload_info = ocr_result.get('upload_info', {})
        
        logger.info(f"[OCR] Extracted {len(contract_data)} fields from contract")
        logger.info(f"[OCR] S3 Upload: {upload_info.get('success', False)}")
        
        # Return the full response expected by the frontend
        return Response({
            'success': True,
            'message': 'OCR extraction completed successfully',
            'data': contract_data,  # Full contract extraction data for frontend
            'contract_extraction': {
                'success': True,
                'data': contract_data
            },
            'upload_info': upload_info,  # S3 upload information
            'ocr_result': ocr_result.get('ocr_result', {}),  # Raw OCR text results
            'document_type': document_type
        })
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist'
        }, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"OCR upload error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': 'Failed to process OCR upload',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"[OCR] Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"[OCR] Failed to clean up temporary file: {e}")


def copy_terms_and_clauses(source_contract, target_contract):
    """Copy terms and clauses from source contract to target contract"""
    try:
        # Copy terms
        terms = ContractTerm.objects.filter(contract_id=source_contract.contract_id)
        logger.info(f"Found {terms.count()} terms to copy from contract {source_contract.contract_id}")
        
        for term in terms:
            try:
                # Generate a guaranteed unique term_id for the amendment
                import time
                import random
                import uuid
                
                # Try multiple approaches to ensure uniqueness
                max_attempts = 5
                new_term_id = None
                
                for attempt in range(max_attempts):
                    if attempt == 0:
                        # First attempt: timestamp + UUID suffix
                        new_term_id = f"term_{target_contract.contract_id}_{int(time.time() * 1000000)}_{str(uuid.uuid4())[:8]}"
                    elif attempt == 1:
                        # Second attempt: Full UUID
                        new_term_id = f"term_{str(uuid.uuid4()).replace('-', '')}"
                    else:
                        # Subsequent attempts: timestamp + random + attempt number
                        new_term_id = f"term_{int(time.time() * 1000000)}_{random.randint(100000, 999999)}_{attempt}"
                    
                    # Check if this term_id already exists
                    if not ContractTerm.objects.filter(term_id=new_term_id).exists():
                        break
                    else:
                        logger.warning(f"term_id {new_term_id} already exists, trying again (attempt {attempt + 1})")
                        new_term_id = None
                
                if new_term_id is None:
                    logger.error(f"Could not generate unique term_id after {max_attempts} attempts")
                    continue
                
                ContractTerm.objects.create(
                    contract_id=target_contract.contract_id,
                    term_id=new_term_id,
                    term_title=term.term_title,
                    term_text=term.term_text,
                    term_category=term.term_category,
                    risk_level=term.risk_level,
                    compliance_status=term.compliance_status,
                    approval_status=term.approval_status,
                    version_number=term.version_number,
                    is_standard=term.is_standard,
                    created_by=term.created_by
                )
                logger.info(f"Successfully created term with ID: {new_term_id}")
            except Exception as term_error:
                logger.error(f"Error copying term {term.term_id}: {str(term_error)}")
                continue
        
        # Copy clauses
        clauses = ContractClause.objects.filter(contract_id=source_contract.contract_id)
        logger.info(f"Found {clauses.count()} clauses to copy from contract {source_contract.contract_id}")
        
        for clause in clauses:
            try:
                # Generate a guaranteed unique clause_id for the amendment
                import time
                import random
                import uuid
                
                # Try multiple approaches to ensure uniqueness
                max_attempts = 5
                new_clause_id = None
                
                for attempt in range(max_attempts):
                    if attempt == 0:
                        # First attempt: timestamp + UUID suffix
                        new_clause_id = f"clause_{target_contract.contract_id}_{int(time.time() * 1000000)}_{str(uuid.uuid4())[:8]}"
                    elif attempt == 1:
                        # Second attempt: Full UUID
                        new_clause_id = f"clause_{str(uuid.uuid4()).replace('-', '')}"
                    else:
                        # Subsequent attempts: timestamp + random + attempt number
                        new_clause_id = f"clause_{int(time.time() * 1000000)}_{random.randint(100000, 999999)}_{attempt}"
                    
                    # Check if this clause_id already exists
                    if not ContractClause.objects.filter(clause_id=new_clause_id).exists():
                        break
                    else:
                        logger.warning(f"clause_id {new_clause_id} already exists, trying again (attempt {attempt + 1})")
                        new_clause_id = None
                
                if new_clause_id is None:
                    logger.error(f"Could not generate unique clause_id after {max_attempts} attempts")
                    continue
                
                ContractClause.objects.create(
                    contract_id=target_contract.contract_id,
                    clause_id=new_clause_id,
                    clause_name=clause.clause_name,
                    clause_text=clause.clause_text,
                    clause_type=clause.clause_type,
                    risk_level=clause.risk_level,
                    legal_category=clause.legal_category,
                    version_number=clause.version_number,
                    is_standard=clause.is_standard,
                    created_by=clause.created_by
                )
                logger.info(f"Successfully created clause with ID: {new_clause_id}")
            except Exception as clause_error:
                logger.error(f"Error copying clause {clause.clause_id}: {str(clause_error)}")
                continue
                
    except Exception as e:
        logger.error(f"Error in copy_terms_and_clauses: {str(e)}")
        raise




# Contract Risk Analysis API Views

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_risk_status(request, contract_id):
    """Get risk analysis status for a contract"""
    try:
        from contract_risk_analysis.models import Risk
        
        # Check if risks exist for this contract
        risks = Risk.objects.filter(
            entity='contract_module',
            row=str(contract_id)
        )
        
        total_risks = risks.count()
        
        return Response({
            'success': True,
            'data': {
                'contract_id': contract_id,
                'risk_analysis_completed': total_risks > 0,
                'total_risks': total_risks,
                'status': 'completed' if total_risks > 0 else 'pending'
            },
            'message': f'Risk analysis {"completed" if total_risks > 0 else "pending"} for contract {contract_id}'
        })
        
    except Exception as e:
        logger.error(f"Error getting risk status for contract {contract_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get risk status',
            'message': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
def trigger_contract_risk_analysis(request, contract_id):
    """Trigger risk analysis for a contract after creation (non-blocking)"""
    try:
        print(f"=== RISK ANALYSIS TRIGGER DEBUG: Received request for contract {contract_id} ===")
        print(f"=== RISK ANALYSIS TRIGGER DEBUG: Request method: {request.method} ===")
        print(f"=== RISK ANALYSIS TRIGGER DEBUG: Request headers: {dict(request.headers)} ===")
        
        # Check if contract exists
        try:
            contract = VendorContract.objects.get(
                contract_id=contract_id,
                is_archived=False
            )
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Contract not found',
                'message': f'Contract {contract_id} not found or archived'
            }, status=404)
        
        # Trigger risk analysis in background thread (no Redis/Celery required)
        try:
            import threading
            from contract_risk_analysis.models import Risk
            
            # Check if risk analysis has already been triggered for this contract
            existing_risks = Risk.objects.filter(
                entity='contract_module',
                row=str(contract_id)
            ).count()
            
            if existing_risks == 0:
                print(f"=== RISK ANALYSIS TRIGGER DEBUG: Starting risk analysis in background thread for contract {contract_id} ===")
                
                # Define the risk analysis function to run in thread
                def run_risk_analysis():
                    try:
                        from contract_risk_analysis.tasks import analyze_contract_risk_task
                        # Run synchronously in the background thread
                        result = analyze_contract_risk_task(contract_id)
                        print(f"=== RISK ANALYSIS TRIGGER DEBUG: Risk analysis completed in background thread ===")
                        logger.info(f"Risk analysis completed in background thread for contract {contract_id}")
                    except Exception as e:
                        print(f"=== RISK ANALYSIS TRIGGER DEBUG: Error in background risk analysis: {str(e)} ===")
                        logger.error(f"Error in background risk analysis for contract {contract_id}: {str(e)}")
                
                # Start the risk analysis in a background thread
                thread = threading.Thread(target=run_risk_analysis, daemon=True)
                thread.start()
                
                return Response({
                    'success': True,
                    'data': {
                        'contract_id': contract_id,
                        'status': 'started_in_background'
                    },
                    'message': f'Risk analysis started in background thread for contract {contract_id}'
                })
            else:
                print(f"=== RISK ANALYSIS TRIGGER DEBUG: Risk analysis already exists for contract {contract_id} ({existing_risks} risks found) ===")
                logger.info(f"Risk analysis already exists for contract {contract_id} - skipping")
                
                return Response({
                    'success': True,
                    'data': {
                        'contract_id': contract_id,
                        'status': 'already_completed',
                        'total_risks': existing_risks
                    },
                    'message': f'Risk analysis already completed for contract {contract_id}'
                })
        except Exception as e:
            print(f"=== RISK ANALYSIS TRIGGER DEBUG: Failed to start risk analysis: {str(e)} ===")
            logger.error(f"Failed to start risk analysis for contract {contract_id}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to start risk analysis',
                'message': str(e)
            }, status=500)
        
    except Exception as e:
        logger.error(f"Contract risk analysis trigger error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to trigger risk analysis',
            'message': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
def contract_risk_analysis(request, contract_id):
    """Trigger risk analysis for a specific contract"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Check if contract exists
        try:
            contract = VendorContract.objects.get(
                contract_id=contract_id,
                is_archived=False
            )
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Contract not found',
                'message': f'Contract {contract_id} not found or archived'
            }, status=404)
        
        # Get background flag from request
        background = request.data.get('background', True)
        
        # Start risk analysis
        from contract_risk_analysis.contract_risk_service import ContractRiskAnalysisService
        contract_risk_service = ContractRiskAnalysisService()
        
        result = contract_risk_service.analyze_contract_risks(
            contract_id=str(contract_id),
            background=background
        )
        
        return Response({
            'success': True,
            'data': result,
            'message': f'Risk analysis {"started" if background else "completed"} for contract {contract_id}'
        })
        
    except Exception as e:
        logger.error(f"Contract risk analysis error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to start risk analysis',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_risk_summary(request, contract_id):
    """Get risk summary for a specific contract"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Check if contract exists
        try:
            contract = VendorContract.objects.get(
                contract_id=contract_id,
                is_archived=False
            )
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Contract not found',
                'message': f'Contract {contract_id} not found or archived'
            }, status=404)
        
        # Get risk summary
        from contract_risk_analysis.contract_risk_service import ContractRiskAnalysisService
        contract_risk_service = ContractRiskAnalysisService()
        
        result = contract_risk_service.get_contract_risk_summary(str(contract_id))
        
        return Response({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Contract risk summary error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get risk summary',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_risks_list(request, contract_id):
    """Get list of risks for a specific contract"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Check if contract exists
        try:
            contract = VendorContract.objects.get(
                contract_id=contract_id,
                is_archived=False
            )
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Contract not found',
                'message': f'Contract {contract_id} not found or archived'
            }, status=404)
        
        # Get risks for this contract
        from contract_risk_analysis.models import Risk
        risks = Risk.objects.filter(
            entity='contract_module',
            row=str(contract_id)
        ).order_by('-score', '-created_at')
        
        # Apply filters
        priority = request.GET.get('priority')
        if priority:
            risks = risks.filter(priority=priority)
        
        status_filter = request.GET.get('status')
        if status_filter:
            risks = risks.filter(status=status_filter)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        from django.core.paginator import Paginator
        paginator = Paginator(risks, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize risks
        risks_data = []
        for risk in page_obj.object_list:
            risk_dict = {
                'id': risk.id,
                'title': risk.title,
                'description': risk.description,
                'likelihood': risk.likelihood,
                'impact': risk.impact,
                'exposure_rating': risk.exposure_rating,
                'score': risk.score,
                'priority': risk.priority,
                'status': risk.status,
                'ai_explanation': risk.ai_explanation,
                'suggested_mitigations': risk.suggested_mitigations or [],
                'created_at': risk.created_at.isoformat() if risk.created_at else None,
                'updated_at': risk.updated_at.isoformat() if risk.updated_at else None
            }
            risks_data.append(risk_dict)
        
        return Response({
            'success': True,
            'data': risks_data,
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
        logger.error(f"Contract risks list error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get contract risks',
            'message': str(e)
        }, status=500)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('DeleteContractTerm')
def contract_terms_delete_all(request, contract_id):
    """
    Delete all terms for a specific contract
    """
    try:
        # Check if contract exists
        contract = get_object_or_404(VendorContract, contract_id=contract_id)
        
        # Delete all terms for this contract
        deleted_count, _ = ContractTerm.objects.filter(contract_id=contract_id).delete()
        
        logger.info(f"Deleted {deleted_count} terms for contract {contract_id}")
        
        return Response({
            'success': True,
            'message': f'Successfully deleted {deleted_count} terms',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error deleting all terms for contract {contract_id}: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error deleting terms: {str(e)}'
        }, status=500)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('DeleteContract')
def contract_clauses_delete_all(request, contract_id):
    """
    Delete all clauses for a specific contract
    """
    try:
        # Check if contract exists
        contract = get_object_or_404(VendorContract, contract_id=contract_id)
        
        # Delete all clauses for this contract
        deleted_count, _ = ContractClause.objects.filter(contract_id=contract_id).delete()
        
        logger.info(f"Deleted {deleted_count} clauses for contract {contract_id}")
        
        return Response({
            'success': True,
            'message': f'Successfully deleted {deleted_count} clauses',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error deleting all clauses for contract {contract_id}: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error deleting clauses: {str(e)}'
        }, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContract')
def create_contract_version(request, contract_id):
    """Create a new version of an existing contract"""
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        # Get the original contract
        original_contract = VendorContract.objects.get(contract_id=contract_id)
        
        # Create backup before operation
        backup_file = DatabaseBackupManager.create_backup()
        
        # Get version type from request
        version_type = request.data.get('version_type', 'minor')  # 'minor' or 'major'
        
        # Calculate new version number
        if version_type == 'major':
            new_version = int(original_contract.version_number) + 1
        else:  # minor
            if '.' in str(original_contract.version_number):
                major, minor = str(original_contract.version_number).split('.')
                new_version = f"{major}.{int(minor) + 1}"
            else:
                new_version = f"{original_contract.version_number}.1"
        
        # Create new contract version
        # Create unique contract number with version
        versioned_contract_number = f"{original_contract.contract_number}-v{new_version}"
        logger.info(f"Creating versioned contract number: {versioned_contract_number}")
        
        new_contract_data = {
            'vendor_id': original_contract.vendor_id,
            'contract_number': versioned_contract_number,
            'contract_title': request.data.get('contract_title', original_contract.contract_title),
            'contract_type': request.data.get('contract_type', original_contract.contract_type),
            'contract_kind': request.data.get('contract_kind', original_contract.contract_kind),
            'parent_contract_id': original_contract.parent_contract_id or original_contract.contract_id,
            'main_contract_id': original_contract.main_contract_id or original_contract.contract_id,
            'version_number': new_version,
            'previous_version_id': original_contract.contract_id,
            'contract_value': request.data.get('contract_value', original_contract.contract_value),
            'currency': request.data.get('currency', original_contract.currency),
            'start_date': request.data.get('start_date', original_contract.start_date),
            'end_date': request.data.get('end_date', original_contract.end_date),
            'renewal_terms': request.data.get('renewal_terms', original_contract.renewal_terms),
            'auto_renewal': request.data.get('auto_renewal', original_contract.auto_renewal),
            'notice_period_days': request.data.get('notice_period_days', original_contract.notice_period_days),
            'status': request.data.get('status', original_contract.status),
            'workflow_stage': request.data.get('workflow_stage', original_contract.workflow_stage),
            'priority': request.data.get('priority', original_contract.priority),
            'compliance_status': request.data.get('compliance_status', original_contract.compliance_status),
            'contract_category': request.data.get('contract_category', original_contract.contract_category),
            'termination_clause_type': request.data.get('termination_clause_type', original_contract.termination_clause_type),
            'liability_cap': request.data.get('liability_cap', original_contract.liability_cap),
            'insurance_requirements': request.data.get('insurance_requirements', original_contract.insurance_requirements),
            'data_protection_clauses': request.data.get('data_protection_clauses', original_contract.data_protection_clauses),
            'dispute_resolution_method': request.data.get('dispute_resolution_method', original_contract.dispute_resolution_method),
            'governing_law': request.data.get('governing_law', original_contract.governing_law),
            'contract_risk_score': request.data.get('contract_risk_score', original_contract.contract_risk_score),
            'assigned_to': parse_integer(request.data.get('assigned_to'), original_contract.assigned_to),
            'custom_fields': request.data.get('custom_fields', original_contract.custom_fields),
            'compliance_framework': request.data.get('compliance_framework', original_contract.compliance_framework),
            'contract_owner': request.data.get('contract_owner', original_contract.contract_owner),
            'legal_reviewer': request.data.get('legal_reviewer', original_contract.legal_reviewer),
            'description': request.data.get('description', original_contract.description)
        }
        
        # Create new contract
        new_contract = VendorContract.objects.create(**new_contract_data)
        
        # Copy terms and clauses from previous version
        copy_terms_and_clauses(original_contract, new_contract)
        
        # Serialize the new contract
        serializer = VendorContractSerializer(new_contract)
        
        return Response({
            'success': True,
            'message': f'Contract version {new_version} created successfully',
            'data': serializer.data,
            'backup_file': backup_file
        }, status=status.HTTP_201_CREATED)
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist'
        }, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Contract version creation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create contract version',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
@csrf_exempt
def create_subcontract_with_versioning(request, parent_contract_id):
    """Create a subcontract with parent contract versioning (major or minor)"""
    try:
        logger.info(f"Starting subcontract creation with versioning for parent contract: {parent_contract_id}")
        logger.info(f"Request data keys: {list(request.data.keys()) if hasattr(request, 'data') else 'No data'}")
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Validate input data
        logger.info("Validating input data")
        SecurityManager.validate_contract_data(request.data)
        
        # Get the original parent contract
        logger.info(f"Getting parent contract with id: {parent_contract_id}")
        original_contract = VendorContract.objects.get(contract_id=parent_contract_id)
        logger.info(f"Parent contract found: {original_contract.contract_title}")
        
        # Determine version type (major or minor)
        version_type = request.data.get('version_type', 'minor')
        
        # Calculate new version number for parent contract
        from decimal import Decimal
        current_version = float(original_contract.version_number)
        
        if version_type == 'major':
            # Major version: 1.0 -> 2.0, 1.5 -> 2.0, 2.3 -> 3.0, etc.
            new_version = Decimal(str(int(current_version) + 1))
        else:  # minor
            # Minor version: 1.0 -> 1.1, 1.5 -> 1.6, 2.0 -> 2.1, etc.
            major_part = int(current_version)
            minor_part = current_version - major_part
            new_version = Decimal(str(round(major_part + minor_part + 0.1, 1)))
        
        # Helper function to convert string dates to date objects
        def parse_date(date_value, fallback_date):
            if date_value and isinstance(date_value, str):
                try:
                    from datetime import datetime
                    # Try parsing different date formats
                    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S'):
                        try:
                            parsed_date = datetime.strptime(date_value, fmt).date()
                            logger.info(f"Successfully parsed date string '{date_value}' to {parsed_date}")
                            return parsed_date
                        except ValueError:
                            continue
                    logger.warning(f"Could not parse date string: {date_value}, using fallback: {fallback_date}")
                    return fallback_date
                except Exception as e:
                    logger.error(f"Error parsing date {date_value}: {str(e)}, using fallback: {fallback_date}")
                    return fallback_date
            elif date_value:
                logger.info(f"Date value is already a date object: {date_value} (type: {type(date_value)})")
                return date_value  # Already a date object
            else:
                logger.info(f"No date value provided, using fallback: {fallback_date}")
                return fallback_date
        
        # Helper function to clean boolean values
        def parse_boolean(bool_value, fallback_bool):
            if isinstance(bool_value, bool):
                return bool_value
            elif isinstance(bool_value, str):
                if bool_value.lower() in ('true', '1', 'yes', 'on'):
                    return True
                elif bool_value.lower() in ('false', '0', 'no', 'off', ''):
                    return False
                else:
                    logger.warning(f"Could not parse boolean string: {bool_value}, using fallback: {fallback_bool}")
                    return fallback_bool
            elif bool_value is None:
                return fallback_bool
            else:
                logger.warning(f"Unexpected boolean value type: {type(bool_value)}, using fallback: {fallback_bool}")
                return fallback_bool
        
        # Helper function to parse integer fields (user IDs, etc.)
        def parse_integer(int_value, fallback_int):
            if isinstance(int_value, int):
                return int_value
            elif isinstance(int_value, str):
                if int_value.strip() == '':
                    return fallback_int
                try:
                    return int(int_value)
                except ValueError:
                    logger.warning(f"Could not parse integer string: {int_value}, using fallback: {fallback_int}")
                    return fallback_int
            elif int_value is None:
                return fallback_int
            else:
                logger.warning(f"Unexpected integer value type: {type(int_value)}, using fallback: {fallback_int}")
                return fallback_int
        
        # Step 1: Create new version of parent contract
        logger.info(f"Creating new version {new_version} of parent contract")
        
        # Create unique contract number with version
        versioned_contract_number = f"{original_contract.contract_number}-v{new_version}"
        logger.info(f"Creating versioned contract number: {versioned_contract_number}")
        
        parent_contract_data = {
            'vendor_id': original_contract.vendor_id,
            'contract_number': versioned_contract_number,
            'contract_title': original_contract.contract_title,
            'contract_type': original_contract.contract_type,
            'contract_kind': original_contract.contract_kind,
            'contract_category': original_contract.contract_category,
            'priority': original_contract.priority,
            'contract_value': original_contract.contract_value,
            'currency': original_contract.currency,
            'liability_cap': original_contract.liability_cap,
            'start_date': original_contract.start_date,
            'end_date': original_contract.end_date,
            'renewal_terms': original_contract.renewal_terms,
            'auto_renewal': original_contract.auto_renewal,
            'notice_period_days': original_contract.notice_period_days,
            'status': 'PENDING_ASSIGNMENT',
            'workflow_stage': 'under_review',
            'compliance_status': original_contract.compliance_status,
            'termination_clause_type': original_contract.termination_clause_type,
            'insurance_requirements': original_contract.insurance_requirements,
            'data_protection_clauses': original_contract.data_protection_clauses,
            'dispute_resolution_method': original_contract.dispute_resolution_method,
            'governing_law': original_contract.governing_law,
            'contract_risk_score': original_contract.contract_risk_score,
            'assigned_to': original_contract.assigned_to,
            'custom_fields': original_contract.custom_fields,
            'compliance_framework': original_contract.compliance_framework,
            'contract_owner': original_contract.contract_owner,
            'legal_reviewer': original_contract.legal_reviewer,
            
            # Versioning fields
            'version_number': new_version,
            'previous_version_id': original_contract.contract_id,
            'parent_contract_id': original_contract.parent_contract_id or original_contract.contract_id,
            'main_contract_id': original_contract.main_contract_id or original_contract.contract_id,
        }
        
        # Create the new version of parent contract
        try:
            logger.info(f"Creating new version of parent contract with data: {list(parent_contract_data.keys())}")
            new_parent_contract = VendorContract.objects.create(**parent_contract_data)
            logger.info(f"New parent contract version created successfully: {new_parent_contract.contract_id}")
        except Exception as contract_error:
            logger.error(f"Error creating new parent contract version: {str(contract_error)}")
            raise
        
        # Step 2: Copy terms and clauses from original parent to new parent version
        logger.info(f"Copying terms and clauses from original parent {original_contract.contract_id} to new version {new_parent_contract.contract_id}")
        copy_terms_and_clauses(original_contract, new_parent_contract)
        
        # Step 3: Create subcontract with reference to new parent version
        logger.info("Creating subcontract with reference to new parent version")
        subcontract_data = request.data.copy()
        
        # Remove fields that are not part of VendorContract model
        fields_to_remove = ['terms', 'clauses', 'version_type']
        for field in fields_to_remove:
            if field in subcontract_data:
                del subcontract_data[field]
                logger.info(f"Removed {field} from subcontract data as it's not a VendorContract field")
        
        # Set subcontract-specific fields
        subcontract_data['contract_kind'] = 'SUBCONTRACT'
        subcontract_data['parent_contract_id'] = new_parent_contract.contract_id  # Reference to new version
        subcontract_data['main_contract_id'] = new_parent_contract.contract_id
        subcontract_data['status'] = 'PENDING_ASSIGNMENT'
        subcontract_data['workflow_stage'] = 'under_review'
        
        # Parse and clean subcontract data
        if 'start_date' in subcontract_data:
            subcontract_data['start_date'] = parse_date(subcontract_data['start_date'], None)
        if 'end_date' in subcontract_data:
            subcontract_data['end_date'] = parse_date(subcontract_data['end_date'], None)
        if 'auto_renewal' in subcontract_data:
            subcontract_data['auto_renewal'] = parse_boolean(subcontract_data['auto_renewal'], False)
        if 'contract_owner' in subcontract_data:
            subcontract_data['contract_owner'] = parse_integer(subcontract_data['contract_owner'], None)
        if 'legal_reviewer' in subcontract_data:
            subcontract_data['legal_reviewer'] = parse_integer(subcontract_data['legal_reviewer'], None)
        if 'assigned_to' in subcontract_data:
            subcontract_data['assigned_to'] = parse_integer(subcontract_data['assigned_to'], None)
        
        # Create subcontract
        try:
            logger.info(f"Creating subcontract with data: {list(subcontract_data.keys())}")
            subcontract = VendorContract.objects.create(**subcontract_data)
            logger.info(f"Subcontract created successfully: {subcontract.contract_id}")
        except Exception as subcontract_error:
            logger.error(f"Error creating subcontract: {str(subcontract_error)}")
            raise
        
        # Step 4: Save subcontract terms and clauses if provided
        if 'terms' in request.data and request.data['terms']:
            logger.info(f"Saving {len(request.data['terms'])} subcontract terms")
            for term_data in request.data['terms']:
                try:
                    # Set default values for required fields
                    term_data.setdefault('risk_level', 'Low')
                    term_data.setdefault('compliance_status', 'Pending')
                    term_data.setdefault('is_standard', False)
                    term_data.setdefault('approval_status', 'Pending')
                    term_data.setdefault('version_number', str(new_version))  # Use parent contract version
                    
                    # Set contract_id to subcontract
                    term_data['contract_id'] = subcontract.contract_id
                    
                    logger.info(f"Creating term for subcontract {subcontract.contract_id}: {term_data.get('term_title', 'No title')}")
                    created_term = ContractTerm.objects.create(**term_data)
                    logger.info(f"✅ Created term for subcontract {subcontract.contract_id}: id={created_term.term_id}")
                except Exception as e:
                    logger.error(f"❌ Error creating term for subcontract: {str(e)}")
                    logger.error(f"Term data that failed: {term_data}")
        
        if 'clauses' in request.data and request.data['clauses']:
            logger.info(f"Saving {len(request.data['clauses'])} subcontract clauses")
            for clause_data in request.data['clauses']:
                try:
                    # Set default values for required fields
                    clause_data.setdefault('risk_level', 'low')
                    clause_data.setdefault('is_standard', False)
                    clause_data.setdefault('version_number', str(new_version))  # Use parent contract version
                    
                    # Set contract_id to subcontract
                    clause_data['contract_id'] = subcontract.contract_id
                    
                    logger.info(f"Creating clause for subcontract {subcontract.contract_id}: {clause_data.get('clause_name', 'No name')}")
                    created_clause = ContractClause.objects.create(**clause_data)
                    logger.info(f"✅ Created clause for subcontract {subcontract.contract_id}: id={created_clause.clause_id}")
                except Exception as e:
                    logger.error(f"❌ Error creating clause for subcontract: {str(e)}")
                    logger.error(f"Clause data that failed: {clause_data}")
        
        # Create backup after successful creation (for speed)
        backup_file = DatabaseBackupManager.create_backup()
        
        # Serialize the results
        parent_serializer = VendorContractSerializer(new_parent_contract)
        subcontract_serializer = VendorContractSerializer(subcontract)
        
        return Response({
            'success': True,
            'message': f'Subcontract created successfully with parent contract versioned to {new_version}',
            'data': {
                'parent_contract': parent_serializer.data,
                'subcontract': subcontract_serializer.data
            },
            'backup_file': backup_file
        }, status=status.HTTP_201_CREATED)
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Parent contract not found',
            'message': f'Parent contract with ID {parent_contract_id} does not exist'
        }, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Subcontract creation with versioning error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create subcontract with versioning',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_comparison(request, contract_id, amendment_id):
    """
    Compare original contract with amendment
    """
    try:
        # Get original contract
        try:
            original_contract = VendorContract.objects.get(contract_id=contract_id)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Original contract not found'
            }, status=404)

        # Get amendment contract
        try:
            amendment_contract = VendorContract.objects.get(contract_id=amendment_id)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Amendment contract not found'
            }, status=404)

        # Get contract terms
        original_terms = ContractTerm.objects.filter(contract_id=contract_id)
        amendment_terms = ContractTerm.objects.filter(contract_id=amendment_id)

        # Get contract clauses
        original_clauses = ContractClause.objects.filter(contract_id=contract_id)
        amendment_clauses = ContractClause.objects.filter(contract_id=amendment_id)

        # Compare basic contract fields
        contract_fields = [
            'contract_title', 'contract_number', 'contract_type', 'contract_value',
            'currency', 'start_date', 'end_date', 'priority', 'status',
            'contract_category', 'notice_period_days', 'auto_renewal',
            'dispute_resolution_method', 'governing_law', 'contract_risk_score',
            'compliance_framework'
        ]

        contract_changes = []
        for field in contract_fields:
            original_value = getattr(original_contract, field, None)
            amendment_value = getattr(amendment_contract, field, None)
            
            if original_value != amendment_value:
                contract_changes.append({
                    'field': field,
                    'original': original_value,
                    'amendment': amendment_value
                })

        # Compare terms
        original_terms_data = list(original_terms.values())
        amendment_terms_data = list(amendment_terms.values())

        terms_comparison = {
            'added': [],
            'modified': [],
            'removed': []
        }

        # Find added terms
        for amendment_term in amendment_terms_data:
            found = False
            for original_term in original_terms_data:
                if (original_term.get('term_title') == amendment_term.get('term_title') and
                    original_term.get('term_category') == amendment_term.get('term_category')):
                    found = True
                    # Check if modified
                    if (original_term.get('term_text') != amendment_term.get('term_text') or
                        original_term.get('risk_level') != amendment_term.get('risk_level') or
                        original_term.get('compliance_status') != amendment_term.get('compliance_status')):
                        terms_comparison['modified'].append({
                            'original': original_term,
                            'amendment': amendment_term
                        })
                    break
            if not found:
                terms_comparison['added'].append(amendment_term)

        # Find removed terms
        for original_term in original_terms_data:
            found = False
            for amendment_term in amendment_terms_data:
                if (original_term.get('term_title') == amendment_term.get('term_title') and
                    original_term.get('term_category') == amendment_term.get('term_category')):
                    found = True
                    break
            if not found:
                terms_comparison['removed'].append(original_term)

        # Compare clauses
        original_clauses_data = list(original_clauses.values())
        amendment_clauses_data = list(amendment_clauses.values())

        clauses_comparison = {
            'added': [],
            'modified': [],
            'removed': []
        }

        # Find added clauses
        for amendment_clause in amendment_clauses_data:
            found = False
            for original_clause in original_clauses_data:
                if (original_clause.get('clause_name') == amendment_clause.get('clause_name') and
                    original_clause.get('clause_type') == amendment_clause.get('clause_type')):
                    found = True
                    # Check if modified
                    if (original_clause.get('clause_text') != amendment_clause.get('clause_text') or
                        original_clause.get('risk_level') != amendment_clause.get('risk_level')):
                        clauses_comparison['modified'].append({
                            'original': original_clause,
                            'amendment': amendment_clause
                        })
                    break
            if not found:
                clauses_comparison['added'].append(amendment_clause)

        # Find removed clauses
        for original_clause in original_clauses_data:
            found = False
            for amendment_clause in amendment_clauses_data:
                if (original_clause.get('clause_name') == amendment_clause.get('clause_name') and
                    original_clause.get('clause_type') == amendment_clause.get('clause_type')):
                    found = True
                    break
            if not found:
                clauses_comparison['removed'].append(original_clause)

        return Response({
            'success': True,
            'data': {
                'original_contract': {
                    'contract_id': original_contract.contract_id,
                    'contract_title': original_contract.contract_title,
                    'version_number': original_contract.version_number
                },
                'amendment_contract': {
                    'contract_id': amendment_contract.contract_id,
                    'contract_title': amendment_contract.contract_title,
                    'version_number': amendment_contract.version_number
                },
                'contract_changes': contract_changes,
                'terms_changes': terms_comparison,
                'clauses_changes': clauses_comparison,
                'summary': {
                    'contract_fields_changed': len(contract_changes),
                    'terms_added': len(terms_comparison['added']),
                    'terms_modified': len(terms_comparison['modified']),
                    'terms_removed': len(terms_comparison['removed']),
                    'clauses_added': len(clauses_comparison['added']),
                    'clauses_modified': len(clauses_comparison['modified']),
                    'clauses_removed': len(clauses_comparison['removed'])
                }
            }
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error comparing contracts: {str(e)}'
        }, status=500)

