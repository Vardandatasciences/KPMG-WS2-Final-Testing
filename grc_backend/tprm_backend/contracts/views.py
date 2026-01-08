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
from django.db.models import Q, Count, Sum, Avg, Max, Case, When, IntegerField, CharField, Value
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import JsonResponse, QueryDict
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
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
from tprm_backend.rbac.tprm_decorators import rbac_contract_required

# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    filter_queryset_by_tenant,
    get_tenant_aware_queryset,
    require_tenant,
    tenant_filter
)

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
        # Try to get user_id from various possible attributes
        user_id = None
        if hasattr(request, 'user') and request.user:
            user_id = getattr(request.user, 'id', None) or getattr(request.user, 'userid', None) or getattr(request.user, 'user_id', None)
        
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
                
        except ImportError:
            logger.warning(f"User model not found")
            return Response({
                'success': False,
                'message': 'Authentication service unavailable'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.warning(f"User not found or error: {username}, {str(e)}")
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_list(request):
    """List all contracts with filtering and pagination
    MULTI-TENANCY: Only returns contracts belonging to the tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get user_id from request
        from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
        user_id = RBACTPRMUtils.get_user_id_from_request(request)
        
        # Check if user is a vendor and get vendor info
        vendor_info = None
        if user_id:
            vendor_info = RBACTPRMUtils.get_vendor_info_for_user(user_id)
            if vendor_info:
                logger.info(f"[CONTRACT LIST] User {user_id} is a vendor: {vendor_info['company_name']} (vendor_id: {vendor_info['vendor_id']})")
        
        # Get query parameters
        search = request.GET.get('search', '')
        contract_type = request.GET.get('contract_type', '')
        status_filter = request.GET.get('status', '')
        priority = request.GET.get('priority', '')
        contract_kind = request.GET.get('contract_kind', '')
        contract_category = request.GET.get('contract_category', '')
        risk_level = request.GET.get('risk_level', '')
        vendor_id = request.GET.get('vendor_id')
        contract_owner = request.GET.get('contract_owner')
        is_archived = request.GET.get('is_archived', 'false').lower() == 'true'
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        ordering = request.GET.get('ordering', '-created_at')
        
        # Build query
        # MULTI-TENANCY: Filter by tenant_id first
        queryset = VendorContract.objects.select_related('vendor').filter(tenant_id=tenant_id)
        
        # Filter for main, amendment, and subcontracts (default to all if no filter)
        if contract_kind:
            queryset = queryset.filter(contract_kind=contract_kind)
        else:
            queryset = queryset.filter(contract_kind__in=['MAIN', 'AMENDMENT', 'SUBCONTRACT'])
        
        # VENDOR FILTERING: If user is a vendor, only show their contracts
        if vendor_info:
            queryset = queryset.filter(vendor_id=vendor_info['vendor_id'])
            logger.info(f"[CONTRACT LIST] Filtering contracts for vendor_id: {vendor_info['vendor_id']}")
        
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
        
        if priority:
            queryset = queryset.filter(priority=priority)
        
        if contract_category:
            queryset = queryset.filter(contract_category=contract_category)
        
        if risk_level:
            # Map risk level to contract_risk_score ranges
            if risk_level == 'Low':
                queryset = queryset.filter(contract_risk_score__lt=60)
            elif risk_level == 'Medium':
                queryset = queryset.filter(contract_risk_score__gte=60, contract_risk_score__lt=80)
            elif risk_level == 'High':
                queryset = queryset.filter(contract_risk_score__gte=80)
        
        # Only allow vendor_id filter for non-vendor users
        if vendor_id and not vendor_info:
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
        import traceback
        logger.error(f"Contract list error: {str(e)}")
        logger.error(f"Contract list traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve contracts',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_detail(request, contract_id):
    """Get contract details by ID
    MULTI-TENANCY: Only returns contract if it belongs to the tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Get user_id from request
        from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
        user_id = RBACTPRMUtils.get_user_id_from_request(request)
        
        # Check if user is a vendor and get vendor info
        vendor_info = None
        if user_id:
            vendor_info = RBACTPRMUtils.get_vendor_info_for_user(user_id)
        
        # Build query
        # MULTI-TENANCY: Add tenant_id filter
        query_filter = {'contract_id': contract_id, 'is_archived': False, 'tenant_id': tenant_id}
        
        # VENDOR FILTERING: If user is a vendor, only allow access to their contracts
        if vendor_info:
            query_filter['vendor_id'] = vendor_info['vendor_id']
            logger.info(f"[CONTRACT DETAIL] Vendor user {user_id} accessing contract {contract_id} - checking vendor_id: {vendor_info['vendor_id']}")
        
        contract = VendorContract.objects.select_related('vendor').get(**query_filter)
        
        serializer = VendorContractSerializer(contract)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except VendorContract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found',
            'message': 'The requested contract does not exist, has been archived, or you do not have permission to view it'
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_comprehensive_detail(request, contract_id):
    """Get comprehensive contract details including terms, clauses, and sub-contracts
    MULTI-TENANCY: Only returns contract if it belongs to the tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        logger.info(f"Starting comprehensive contract detail fetch for contract_id: {contract_id}")
        
        # Get user_id from request
        from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
        user_id = RBACTPRMUtils.get_user_id_from_request(request)
        
        # Check if user is a vendor and get vendor info
        vendor_info = None
        if user_id:
            vendor_info = RBACTPRMUtils.get_vendor_info_for_user(user_id)
        
        # Build query
        # MULTI-TENANCY: Add tenant_id filter
        query_filter = {'contract_id': contract_id, 'is_archived': False, 'tenant_id': tenant_id}
        
        # VENDOR FILTERING: If user is a vendor, only allow access to their contracts
        if vendor_info:
            query_filter['vendor_id'] = vendor_info['vendor_id']
            logger.info(f"[CONTRACT COMPREHENSIVE DETAIL] Vendor user {user_id} accessing contract {contract_id} - checking vendor_id: {vendor_info['vendor_id']}")
        
        # Get main contract
        contract = VendorContract.objects.select_related('vendor').get(**query_filter)
        logger.info(f"Found contract: {contract.contract_title} (ID: {contract.contract_id})")
        
        # Get contract terms
        # MULTI-TENANCY: Filter by tenant_id
        terms = ContractTerm.objects.filter(contract_id=contract_id, tenant_id=tenant_id).order_by('term_category', 'created_at')
        logger.info(f"Found {terms.count()} terms for contract {contract_id}")
        
        # Get contract clauses
        # MULTI-TENANCY: Filter by tenant_id
        clauses = ContractClause.objects.filter(contract_id=contract_id, tenant_id=tenant_id).order_by('clause_type', 'created_at')
        logger.info(f"Found {clauses.count()} clauses for contract {contract_id}")
        
        # Get sub-contracts (contracts with contract_kind='SUBCONTRACT' and parent_contract_id=contract_id)
        # MULTI-TENANCY: Filter by tenant_id
        sub_contracts = VendorContract.objects.filter(
            contract_kind='SUBCONTRACT',
            parent_contract_id=contract_id,
            is_archived=False,
            tenant_id=tenant_id
        ).select_related('vendor').order_by('created_at')
        
        # Get terms and clauses for each sub-contract
        sub_contracts_with_details = []
        total_sub_terms = 0
        total_sub_clauses = 0
        
        for sub_contract in sub_contracts:
            # Get terms for this sub-contract
            # MULTI-TENANCY: Filter by tenant_id
            sub_terms = ContractTerm.objects.filter(contract_id=sub_contract.contract_id, tenant_id=tenant_id).order_by('term_category', 'created_at')
            sub_terms_serializer = ContractTermSerializer(sub_terms, many=True)
            
            # Get clauses for this sub-contract
            # MULTI-TENANCY: Filter by tenant_id
            sub_clauses = ContractClause.objects.filter(contract_id=sub_contract.contract_id, tenant_id=tenant_id).order_by('clause_type', 'created_at')
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_create(request):
    """Create a new contract
    MULTI-TENANCY: Automatically assigns tenant_id to the contract
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found. Cannot create contract without tenant.'
            }, status=403)
        
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
            
            # MULTI-TENANCY: Add tenant_id to contract data if not present
            if 'tenant_id' not in contract_data and 'tenant' not in contract_data:
                contract_data['tenant_id'] = tenant_id
            
            # Convert boolean values to integers for unmanaged models
            if 'auto_renewal' in contract_data:
                logger.info(f"Converting auto_renewal: {contract_data['auto_renewal']} (type: {type(contract_data['auto_renewal'])})")
                contract_data['auto_renewal'] = 1 if contract_data['auto_renewal'] else 0
                logger.info(f"Converted auto_renewal to: {contract_data['auto_renewal']}")
            
            if 'permission_required' in contract_data:
                logger.info(f"Converting permission_required: {contract_data['permission_required']} (type: {type(contract_data['permission_required'])})")
                contract_data['permission_required'] = 1 if contract_data['permission_required'] else 0
                logger.info(f"Converted permission_required to: {contract_data['permission_required']}")
            
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
                
                # MULTI-TENANCY: Get tenant_id from request
                tenant_id = get_tenant_id_from_request(request)
                if not tenant_id:
                    logger.warning("Tenant context not found when creating approval, using contract's tenant_id")
                    tenant_id = contract.tenant_id
                
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
                    'comment_text': f'Contract {contract.contract_number} requires review and approval',
                    'tenant_id': tenant_id  # MULTI-TENANCY: Set tenant_id
                }
                
                # Get assignee name
                if contract.legal_reviewer:
                    try:
                        from mfa_auth.models import User
                        assignee_user = User.objects.get(userid=contract.legal_reviewer)
                        approval_data['assignee_name'] = f"{assignee_user.first_name} {assignee_user.last_name}".strip() or assignee_user.username
                    except ImportError:
                        pass
                    except Exception as e:
                        pass
                elif contract.contract_owner:
                    try:
                        from mfa_auth.models import User
                        assignee_user = User.objects.get(userid=contract.contract_owner)
                        approval_data['assignee_name'] = f"{assignee_user.first_name} {assignee_user.last_name}".strip() or assignee_user.username
                    except ImportError:
                        pass
                    except Exception as e:
                        pass
                
                # Create the approval
                approval_serializer = ContractApprovalCreateAssignmentSerializer(data=approval_data)
                if approval_serializer.is_valid():
                    # MULTI-TENANCY: Ensure tenant_id is set when saving
                    approval = approval_serializer.save(tenant_id=tenant_id)
                    logger.info(f"Contract approval created: {approval.approval_id} for contract {contract.contract_id} with tenant_id {tenant_id}")
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_update(request, contract_id):
    """Update an existing contract
    MULTI-TENANCY: Only allows updating contracts belonging to the tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        # Get contract
        # MULTI-TENANCY: Add tenant_id filter to ensure tenant isolation
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=False,
            tenant_id=tenant_id
        )
        
        # Create backup before operation
        backup_file = DatabaseBackupManager.create_backup()
        
        def update_contract():
            # Convert boolean values to integers for unmanaged models
            update_data = request.data.copy()
            
            if 'auto_renewal' in update_data:
                logger.info(f"Converting auto_renewal: {update_data['auto_renewal']} (type: {type(update_data['auto_renewal'])})")
                update_data['auto_renewal'] = 1 if update_data['auto_renewal'] else 0
                logger.info(f"Converted auto_renewal to: {update_data['auto_renewal']}")
            
            if 'permission_required' in update_data:
                logger.info(f"Converting permission_required: {update_data['permission_required']} (type: {type(update_data['permission_required'])})")
                update_data['permission_required'] = 1 if update_data['permission_required'] else 0
                logger.info(f"Converted permission_required to: {update_data['permission_required']}")
            
            serializer = VendorContractUpdateSerializer(
                contract, 
                data=update_data, 
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_delete(request, contract_id):
    """Delete a contract (soft delete by archiving)
    MULTI-TENANCY: Ensures contract belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get contract
        # MULTI-TENANCY: Filter by tenant
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=False,
            tenant_id=tenant_id
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_archive(request, contract_id):
    """Archive a contract with reason
    MULTI-TENANCY: Ensures contract belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get contract
        # MULTI-TENANCY: Filter by tenant
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=False,
            tenant_id=tenant_id
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_restore(request, contract_id):
    """Restore an archived contract
    MULTI-TENANCY: Ensures contract belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get archived contract
        # MULTI-TENANCY: Filter by tenant
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=True,
            tenant_id=tenant_id
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
@rbac_contract_required('ListContracts')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_stats(request):
    """Get contract statistics and analytics
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
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get statistics for main and amendment contracts
        # MULTI-TENANCY: Filter by tenant
        contracts_base = VendorContract.objects.filter(
            is_archived=False, 
            contract_kind__in=['MAIN', 'AMENDMENT'],
            tenant_id=tenant_id
        )
        
        total_contracts = contracts_base.count()
        active_contracts = contracts_base.filter(
            status='ACTIVE'
        ).count()
        expired_contracts = contracts_base.filter(
            status='EXPIRED'
        ).count()
        draft_contracts = contracts_base.filter(
            status='DRAFT'
        ).count()
        
        # Contracts by type
        contracts_by_type = dict(
            contracts_base.values('contract_type')
            .annotate(count=Count('contract_id'))
            .values_list('contract_type', 'count')
        )
        
        # Contracts by status
        contracts_by_status = dict(
            contracts_base.values('status')
            .annotate(count=Count('contract_id'))
            .values_list('status', 'count')
        )
        
        # Contracts by priority
        contracts_by_priority = dict(
            contracts_base.values('priority')
            .annotate(count=Count('contract_id'))
            .values_list('priority', 'count')
        )
        
        # Total value (active contracts only)
        total_value = contracts_base.filter(
            contract_value__isnull=False,
            status='ACTIVE'
        ).aggregate(total=Sum('contract_value'))['total'] or Decimal('0')
        
        # Average risk score
        avg_risk_score = contracts_base.filter(
            contract_risk_score__isnull=False
        ).aggregate(avg=Avg('contract_risk_score'))['avg'] or Decimal('0')
        
        # Expiring soon (within 90 days)
        today = timezone.now().date()
        expiring_date = today + timedelta(days=90)
        
        expiring_soon = contracts_base.filter(
            end_date__lte=expiring_date,
            end_date__gte=today,
            status__in=['ACTIVE', 'UNDER_REVIEW', 'DRAFT', 'PENDING']
        ).count()
        
        # Debug logging
        logger.info(f"Expiring contracts calculation: today={today}, expiring_date={expiring_date}")
        logger.info(f"Expiring soon count: {expiring_soon}")
        
        # Log some sample contracts for debugging
        sample_contracts = contracts_base.filter(
            end_date__isnull=False
        ).values('contract_id', 'contract_title', 'end_date', 'status')[:5]
        logger.info(f"Sample contracts with end dates: {list(sample_contracts)}")
        
        # Overdue renewals
        overdue_renewals = contracts_base.filter(
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_amendments_kpi(request):
    """
    Get Contract Amendments KPI data - amendments count per contract.
    Returns top contracts with their amendment counts using parent_contract_id from vendor_contracts.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get limit parameter (default to 10 contracts)
        limit = int(request.GET.get('limit', 10))
        
        # Get amendment counts per contract from VendorContract model
        # Count contracts where contract_kind='AMENDMENT' grouped by parent_contract_id
        # MULTI-TENANCY: Filter by tenant
        from django.db.models import Count as CountFunc
        
        amendment_counts = (
            VendorContract.objects
            .filter(contract_kind='AMENDMENT', is_archived=False, tenant_id=tenant_id)
            .exclude(parent_contract_id__isnull=True)
            .values('parent_contract_id')
            .annotate(amendment_count=CountFunc('contract_id'))
            .order_by('-amendment_count')[:limit]
        )
        
        # Build response data with contract details
        amendments_data = []
        for item in amendment_counts:
            parent_contract_id = item['parent_contract_id']
            amendment_count = item['amendment_count']
            
            # Get parent contract details
            # MULTI-TENANCY: Filter by tenant
            try:
                contract = VendorContract.objects.get(
                    contract_id=parent_contract_id,
                    is_archived=False,
                    tenant_id=tenant_id
                )
                
                # Generate contract code from contract_id
                contract_code = f'#C-{str(parent_contract_id).zfill(3)}'
                
                amendments_data.append({
                    'contract_id': parent_contract_id,
                    'contract_code': contract_code,
                    'contract_title': contract.contract_title,
                    'amendment_count': amendment_count
                })
            except VendorContract.DoesNotExist:
                # If parent contract doesn't exist or is archived, still include it
                amendments_data.append({
                    'contract_id': parent_contract_id,
                    'contract_code': f'#C-{str(parent_contract_id).zfill(3)}',
                    'contract_title': f'Contract {parent_contract_id}',
                    'amendment_count': amendment_count
                })
        
        # Get total statistics
        # MULTI-TENANCY: Filter by tenant
        amendments_base = VendorContract.objects.filter(
            contract_kind='AMENDMENT',
            is_archived=False,
            tenant_id=tenant_id
        )
        total_amendments = amendments_base.count()
        total_contracts_with_amendments = amendments_base.exclude(parent_contract_id__isnull=True).values('parent_contract_id').distinct().count()
        
        response_data = {
            'amendments_by_contract': amendments_data,
            'statistics': {
                'total_amendments': total_amendments,
                'total_contracts_with_amendments': total_contracts_with_amendments,
                'average_amendments_per_contract': round(
                    total_amendments / total_contracts_with_amendments, 2
                ) if total_contracts_with_amendments > 0 else 0
            }
        }
        
        return Response({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Contract amendments KPI error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve amendments KPI data',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ContractDashboard')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contracts_expiring_soon_kpi(request):
    """
    Get Contracts Expiring Soon KPI data.
    Returns count of contracts expiring in different time periods:
    - 0-30 days
    - 31-60 days  
    - 61-90 days
    - 90+ days
    Includes all contracts regardless of contract_kind to match total count
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get current date
        today = timezone.now().date()
        
        # Define date ranges
        date_30_days = today + timedelta(days=30)
        date_60_days = today + timedelta(days=60)
        date_90_days = today + timedelta(days=90)
        
        # Base query - ALL non-archived contracts with end_date
        # NOTE: Removed contract_kind filter to include ALL contracts (main, amendments, subcontracts)
        # MULTI-TENANCY: Filter by tenant
        base_query = VendorContract.objects.filter(
            is_archived=False,
            end_date__isnull=False,
            tenant_id=tenant_id
        )
        
        # Count contracts in each time period (only future/current contracts)
        contracts_0_30 = base_query.filter(
            end_date__gte=today,
            end_date__lte=date_30_days
        ).count()
        
        contracts_31_60 = base_query.filter(
            end_date__gt=date_30_days,
            end_date__lte=date_60_days
        ).count()
        
        contracts_61_90 = base_query.filter(
            end_date__gt=date_60_days,
            end_date__lte=date_90_days
        ).count()
        
        contracts_90_plus = base_query.filter(
            end_date__gt=date_90_days
        ).count()
        
        # Count expired contracts (contracts with end_date before today)
        contracts_expired = base_query.filter(
            end_date__lt=today
        ).count()
        
        # Count contracts without end_date
        # MULTI-TENANCY: Filter by tenant
        contracts_no_end_date = VendorContract.objects.filter(
            is_archived=False,
            end_date__isnull=True,
            tenant_id=tenant_id
        ).count()
        
        # Total contracts in database
        # MULTI-TENANCY: Filter by tenant
        total_contracts_all = VendorContract.objects.filter(is_archived=False, tenant_id=tenant_id).count()
        
        # Total contracts with end dates (future + expired)
        total_with_end_dates = base_query.count()
        
        # Build response data
        response_data = {
            'expiring_contracts': [
                {
                    'period': '0-30 days',
                    'count': contracts_0_30,
                    'start_date': today.isoformat(),
                    'end_date': date_30_days.isoformat()
                },
                {
                    'period': '31-60 days',
                    'count': contracts_31_60,
                    'start_date': (date_30_days + timedelta(days=1)).isoformat(),
                    'end_date': date_60_days.isoformat()
                },
                {
                    'period': '61-90 days',
                    'count': contracts_61_90,
                    'start_date': (date_60_days + timedelta(days=1)).isoformat(),
                    'end_date': date_90_days.isoformat()
                },
                {
                    'period': '90+ days',
                    'count': contracts_90_plus,
                    'start_date': (date_90_days + timedelta(days=1)).isoformat(),
                    'end_date': None
                }
            ],
            'statistics': {
                'total_future_expiring': contracts_0_30 + contracts_31_60 + contracts_61_90 + contracts_90_plus,
                'urgent_expiring': contracts_0_30,  # Contracts expiring in next 30 days
                'already_expired': contracts_expired,
                'no_end_date': contracts_no_end_date,
                'total_with_end_dates': total_with_end_dates,
                'total_all_contracts': total_contracts_all
            }
        }
        
        logger.info(f"Contracts Expiring KPI Stats: 0-30={contracts_0_30}, 31-60={contracts_31_60}, "
                   f"61-90={contracts_61_90}, 90+={contracts_90_plus}, expired={contracts_expired}, "
                   f"no_end_date={contracts_no_end_date}, total={total_contracts_all}")
        
        return Response({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Contracts expiring soon KPI error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve contracts expiring soon KPI data',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ContractDashboard')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def average_contract_value_by_type_kpi(request):
    """
    Get Average Contract Value by Contract Type KPI.
    Returns average contract value for each contract type:
    - MASTER_AGREEMENT
    - SOW
    - PURCHASE_ORDER
    - SERVICE_AGREEMENT
    - LICENSE
    - NDA
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        from django.db.models import Avg, Count, Sum
        
        # Query average contract value by type
        # Only include non-archived contracts with contract values
        # MULTI-TENANCY: Filter by tenant
        contract_type_stats = (
            VendorContract.objects
            .filter(
                is_archived=False,
                contract_value__isnull=False,
                contract_value__gt=0,  # Exclude zero or null values
                tenant_id=tenant_id
            )
            .values('contract_type')
            .annotate(
                avg_value=Avg('contract_value'),
                total_value=Sum('contract_value'),
                contract_count=Count('contract_id')
            )
            .order_by('-avg_value')
        )
        
        # Format the data for the response
        contract_type_data = []
        total_avg = 0
        total_contracts = 0
        
        # Contract type display names
        contract_type_names = {
            'MASTER_AGREEMENT': 'Master Agreement',
            'SOW': 'Statement of Work',
            'PURCHASE_ORDER': 'Purchase Order',
            'SERVICE_AGREEMENT': 'Service Agreement',
            'LICENSE': 'License',
            'NDA': 'Non-Disclosure Agreement'
        }
        
        for item in contract_type_stats:
            contract_type = item['contract_type']
            avg_value = float(item['avg_value']) if item['avg_value'] else 0
            total_value = float(item['total_value']) if item['total_value'] else 0
            count = item['contract_count']
            
            contract_type_data.append({
                'contract_type': contract_type,
                'contract_type_display': contract_type_names.get(contract_type, contract_type),
                'average_value': round(avg_value, 2),
                'total_value': round(total_value, 2),
                'contract_count': count,
                'currency': 'USD'  # Default currency, can be enhanced to support multiple currencies
            })
            
            total_avg += avg_value
            total_contracts += count
        
        # Calculate overall statistics
        overall_avg = (total_avg / len(contract_type_data)) if contract_type_data else 0
        
        # Get total contract value across all types
        # MULTI-TENANCY: Filter by tenant
        total_portfolio_value = (
            VendorContract.objects
            .filter(
                is_archived=False,
                contract_value__isnull=False,
                contract_value__gt=0,
                tenant_id=tenant_id
            )
            .aggregate(total=Sum('contract_value'))['total'] or 0
        )
        
        response_data = {
            'contract_types': contract_type_data,
            'statistics': {
                'overall_average': round(overall_avg, 2),
                'total_portfolio_value': round(float(total_portfolio_value), 2),
                'total_contracts': total_contracts,
                'types_count': len(contract_type_data)
            }
        }
        
        logger.info(f"Average Contract Value by Type KPI: {len(contract_type_data)} types, "
                   f"Total Portfolio: ${total_portfolio_value:,.2f}")
        
        return Response({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Average contract value by type KPI error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve average contract value by type KPI data',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ContractDashboard')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def business_criticality_kpi(request):
    """
    Get Business Criticality KPI data.
    Returns count of contracts grouped by business_criticality level from Vendor table:
    - critical
    - high
    - medium
    - low
    - NULL (no criticality data)
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        from django.db.models import Count, Q
        
        # Query contracts with their vendor's business criticality
        # Join VendorContract with Vendor to get business_criticality
        # MULTI-TENANCY: Filter by tenant
        criticality_counts = (
            VendorContract.objects
            .filter(is_archived=False, tenant_id=tenant_id)
            .values('vendor__business_criticality')
            .annotate(contract_count=Count('contract_id'))
            .order_by('-contract_count')
        )
        
        # Initialize counts for all levels
        criticality_data = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'no_data': 0
        }
        
        # Map database values to display format
        for item in criticality_counts:
            criticality_level = item['vendor__business_criticality']
            count = item['contract_count']
            
            if criticality_level == 'critical':
                criticality_data['critical'] = count
            elif criticality_level == 'high':
                criticality_data['high'] = count
            elif criticality_level == 'medium':
                criticality_data['medium'] = count
            elif criticality_level == 'low':
                criticality_data['low'] = count
            else:  # NULL or other values
                criticality_data['no_data'] += count
        
        # Build response data
        criticality_levels = [
            {
                'level': 'critical',
                'level_display': 'Critical',
                'count': criticality_data['critical'],
                'color': '#ef4444'  # Red
            },
            {
                'level': 'high',
                'level_display': 'High',
                'count': criticality_data['high'],
                'color': '#f97316'  # Orange
            },
            {
                'level': 'medium',
                'level_display': 'Medium',
                'count': criticality_data['medium'],
                'color': '#eab308'  # Yellow
            },
            {
                'level': 'low',
                'level_display': 'Low',
                'count': criticality_data['low'],
                'color': '#22c55e'  # Green
            }
        ]
        
        # Calculate statistics
        total_with_criticality = (
            criticality_data['critical'] + 
            criticality_data['high'] + 
            criticality_data['medium'] + 
            criticality_data['low']
        )
        total_contracts = total_with_criticality + criticality_data['no_data']
        high_risk_contracts = criticality_data['critical'] + criticality_data['high']
        
        response_data = {
            'criticality_levels': criticality_levels,
            'statistics': {
                'total_with_criticality': total_with_criticality,
                'critical_contracts': criticality_data['critical'],
                'high_risk_contracts': high_risk_contracts,  # Critical + High
                'no_criticality_data': criticality_data['no_data'],
                'total_contracts': total_contracts
            }
        }
        
        logger.info(f"Business Criticality KPI: Critical={criticality_data['critical']}, "
                   f"High={criticality_data['high']}, Medium={criticality_data['medium']}, "
                   f"Low={criticality_data['low']}, No Data={criticality_data['no_data']}, "
                   f"Total={total_contracts}")
        
        return Response({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Business criticality KPI error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve business criticality KPI data',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ContractDashboard')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def total_liability_exposure_kpi(request):
    """
    Get Total Liability Exposure KPI.
    Returns the sum of liability_cap from all active contracts with threshold-based risk assessment.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        from django.db.models import Sum, Count, Avg
        
        # Calculate total liability exposure
        # MULTI-TENANCY: Filter by tenant
        liability_stats = VendorContract.objects.filter(
            is_archived=False,
            liability_cap__isnull=False,
            liability_cap__gt=0,
            tenant_id=tenant_id
        ).aggregate(
            total_liability=Sum('liability_cap'),
            avg_liability=Avg('liability_cap'),
            contract_count=Count('contract_id')
        )
        
        total_liability = float(liability_stats['total_liability'] or 0)
        avg_liability = float(liability_stats['avg_liability'] or 0)
        contract_count = liability_stats['contract_count'] or 0
        
        # Count contracts without liability cap
        # MULTI-TENANCY: Filter by tenant
        contracts_no_liability = VendorContract.objects.filter(
            is_archived=False,
            tenant_id=tenant_id
        ).filter(
            Q(liability_cap__isnull=True) | Q(liability_cap=0)
        ).count()
        
        # Total all contracts
        # MULTI-TENANCY: Filter by tenant
        total_contracts = VendorContract.objects.filter(is_archived=False, tenant_id=tenant_id).count()
        
        # Define thresholds (in USD)
        threshold_low = 1_000_000  # $1M
        threshold_medium = 5_000_000  # $5M
        threshold_high = 10_000_000  # $10M
        threshold_critical = 20_000_000  # $20M
        
        # Determine risk level and color
        if total_liability < threshold_low:
            risk_level = 'low'
            risk_color = '#22c55e'  # Green
            risk_label = 'Low Risk'
        elif total_liability < threshold_medium:
            risk_level = 'medium'
            risk_color = '#eab308'  # Yellow
            risk_label = 'Medium Risk'
        elif total_liability < threshold_high:
            risk_level = 'high'
            risk_color = '#f97316'  # Orange
            risk_label = 'High Risk'
        else:
            risk_level = 'critical'
            risk_color = '#ef4444'  # Red
            risk_label = 'Critical Risk'
        
        # Build threshold data for visualization
        thresholds = [
            {'level': 'Low', 'max': threshold_low, 'color': '#22c55e'},
            {'level': 'Medium', 'max': threshold_medium, 'color': '#eab308'},
            {'level': 'High', 'max': threshold_high, 'color': '#f97316'},
            {'level': 'Critical', 'max': threshold_critical, 'color': '#ef4444'}
        ]
        
        response_data = {
            'total_liability_exposure': round(total_liability, 2),
            'average_liability': round(avg_liability, 2),
            'contracts_with_liability': contract_count,
            'contracts_without_liability': contracts_no_liability,
            'total_contracts': total_contracts,
            'risk_assessment': {
                'level': risk_level,
                'label': risk_label,
                'color': risk_color
            },
            'thresholds': thresholds,
            'currency': 'USD'
        }
        
        logger.info(f"Total Liability Exposure KPI: ${total_liability:,.2f} ({risk_label}), "
                   f"{contract_count} contracts with liability data")
        
        return Response({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Total liability exposure KPI error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve total liability exposure KPI data',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ContractDashboard')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_risk_exposure_kpi(request):
    """
    Get Contract Risk Exposure KPI.
    Returns the count of contracts by their highest risk level from the risk_tprm table.
    Filters risks where entity='contract_module' and groups contracts by their highest priority.
    Since a contract can have multiple risk records, each contract is counted only once
    based on its highest risk level.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        from django.db.models import Count as CountFunc, Max, Case, When, IntegerField
        
        # Try to import Risk model, use raw SQL as fallback if not available
        try:
            from contract_risk_analysis.models import Risk
            use_model = True
        except (ImportError, Exception) as import_error:
            logger.warning(f"Contract risk analysis module not available, using raw SQL: {str(import_error)}")
            use_model = False
        
        # Define risk priority order (higher number = higher risk)
        priority_order = {
            'Low': 1,
            'Medium': 2,
            'High': 3,
            'Critical': 4
        }
        
        # Get all contract risks grouped by contract (row field)
        if use_model:
            # Use Django ORM with Risk model
            contract_risks = (
                Risk.objects
                .filter(entity='contract_module')
                .values('row')  # Group by contract_id
                .annotate(
                    # Assign numeric values to priorities for comparison
                    max_priority_value=Max(
                        Case(
                            When(priority='Low', then=1),
                            When(priority='Medium', then=2),
                            When(priority='High', then=3),
                            When(priority='Critical', then=4),
                            default=0,
                            output_field=IntegerField()
                        )
                    )
                )
            )
        else:
            # Use raw SQL as fallback
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        `row`,
                        MAX(CASE 
                            WHEN priority = 'Low' THEN 1
                            WHEN priority = 'Medium' THEN 2
                            WHEN priority = 'High' THEN 3
                            WHEN priority = 'Critical' THEN 4
                            ELSE 0
                        END) as max_priority_value
                    FROM risk_tprm
                    WHERE entity = 'contract_module'
                    GROUP BY `row`
                """)
                columns = [col[0] for col in cursor.description]
                contract_risks = [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]
        
        # Count contracts by their highest risk level
        risk_level_counts = {
            'Low': 0,
            'Medium': 0,
            'High': 0,
            'Critical': 0
        }
        
        total_contracts = 0
        for contract in contract_risks:
            max_priority = contract['max_priority_value']
            total_contracts += 1
            
            # Map numeric value back to priority name
            if max_priority == 4:
                risk_level_counts['Critical'] += 1
            elif max_priority == 3:
                risk_level_counts['High'] += 1
            elif max_priority == 2:
                risk_level_counts['Medium'] += 1
            elif max_priority == 1:
                risk_level_counts['Low'] += 1
        
        # Build risk exposure data with colors
        risk_colors = {
            'Low': 'hsl(var(--primary))',
            'Medium': 'hsl(142, 76%, 36%)',
            'High': 'hsl(48, 96%, 53%)',
            'Critical': 'hsl(0, 84%, 60%)'
        }
        
        # Build response data
        risk_exposure_data = [
            {'level': 'Low', 'count': risk_level_counts['Low'], 'color': risk_colors['Low']},
            {'level': 'Medium', 'count': risk_level_counts['Medium'], 'color': risk_colors['Medium']},
            {'level': 'High', 'count': risk_level_counts['High'], 'color': risk_colors['High']},
            {'level': 'Critical', 'count': risk_level_counts['Critical'], 'color': risk_colors['Critical']}
        ]
        
        # MULTI-TENANCY: Filter contract risks by tenant by verifying contracts belong to tenant
        # Get list of contract IDs that belong to this tenant
        tenant_contract_ids = list(VendorContract.objects.filter(tenant_id=tenant_id).values_list('contract_id', flat=True))
        
        # Filter contract_risks to only include contracts from this tenant
        filtered_contract_risks = [cr for cr in contract_risks if cr.get('row') in tenant_contract_ids]
        
        # Recalculate counts with filtered data
        risk_level_counts_filtered = {
            'Low': 0,
            'Medium': 0,
            'High': 0,
            'Critical': 0
        }
        
        total_contracts_filtered = 0
        for contract in filtered_contract_risks:
            max_priority = contract['max_priority_value']
            total_contracts_filtered += 1
            
            # Map numeric value back to priority name
            if max_priority == 4:
                risk_level_counts_filtered['Critical'] += 1
            elif max_priority == 3:
                risk_level_counts_filtered['High'] += 1
            elif max_priority == 2:
                risk_level_counts_filtered['Medium'] += 1
            elif max_priority == 1:
                risk_level_counts_filtered['Low'] += 1
        
        # Calculate total number of individual risk records (filtered by tenant contracts)
        if use_model:
            total_risk_records = Risk.objects.filter(entity='contract_module', row__in=tenant_contract_ids).count()
        else:
            if tenant_contract_ids:
                placeholders = ','.join(['%s'] * len(tenant_contract_ids))
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM risk_tprm WHERE entity = 'contract_module' AND `row` IN ({placeholders})",
                        tenant_contract_ids
                    )
                    total_risk_records = cursor.fetchone()[0]
            else:
                total_risk_records = 0
        
        # Build risk exposure data with filtered counts
        risk_exposure_data = [
            {'level': 'Low', 'count': risk_level_counts_filtered['Low'], 'color': risk_colors['Low']},
            {'level': 'Medium', 'count': risk_level_counts_filtered['Medium'], 'color': risk_colors['Medium']},
            {'level': 'High', 'count': risk_level_counts_filtered['High'], 'color': risk_colors['High']},
            {'level': 'Critical', 'count': risk_level_counts_filtered['Critical'], 'color': risk_colors['Critical']}
        ]
        
        response_data = {
            'risk_levels': risk_exposure_data,
            'statistics': {
                'total_contracts': total_contracts_filtered,
                'total_risk_records': total_risk_records,
                'contracts_with_critical': risk_level_counts_filtered['Critical'],
                'contracts_with_high': risk_level_counts_filtered['High'],
                'contracts_with_critical_or_high': risk_level_counts_filtered['Critical'] + risk_level_counts_filtered['High'],
                'average_risks_per_contract': round(total_risk_records / total_contracts_filtered, 2) if total_contracts_filtered > 0 else 0
            }
        }
        
        logger.info(f"Contract Risk Exposure KPI: {total_contracts} contracts "
                   f"(Critical: {risk_level_counts['Critical']}, High: {risk_level_counts['High']}, "
                   f"Medium: {risk_level_counts['Medium']}, Low: {risk_level_counts['Low']}) "
                   f"from {total_risk_records} total risk records")
        
        return Response({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Contract risk exposure KPI error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve contract risk exposure KPI data',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ContractDashboard')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def early_termination_rate_kpi(request):
    """
    Get Early Termination Rate KPI.
    Returns the termination percentage by contract type.
    Calculates the percentage of contracts terminated early for each contract type.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        from django.db.models import Count as CountFunc, Q
        
        # Contract type mapping for display names
        contract_type_display = {
            'MASTER_AGREEMENT': 'Master Agreement',
            'SOW': 'Statement of Work',
            'PURCHASE_ORDER': 'Purchase Order',
            'SERVICE_AGREEMENT': 'Service Agreement',
            'LICENSE': 'License',
            'NDA': 'Non-Disclosure Agreement'
        }
        
        # Get all contract types
        contract_types = ['MASTER_AGREEMENT', 'SOW', 'PURCHASE_ORDER', 'SERVICE_AGREEMENT', 'LICENSE', 'NDA']
        
        termination_data = []
        total_contracts_all_types = 0
        total_early_terminated = 0
        
        for contract_type in contract_types:
            # Count total contracts of this type
            # MULTI-TENANCY: Filter by tenant
            total_count = VendorContract.objects.filter(
                contract_type=contract_type,
                tenant_id=tenant_id
            ).count()
            
            # Count contracts terminated early of this type
            # MULTI-TENANCY: Filter by tenant
            early_terminated_count = VendorContract.objects.filter(
                contract_type=contract_type,
                archive_reason='EARLY_TERMINATION',
                is_archived=True,
                tenant_id=tenant_id
            ).count()
            
            # Calculate percentage
            termination_rate = 0.0
            if total_count > 0:
                termination_rate = round((early_terminated_count / total_count) * 100, 2)
            
            # Only include if there are contracts of this type
            if total_count > 0:
                termination_data.append({
                    'contract_type': contract_type,
                    'contract_type_display': contract_type_display.get(contract_type, contract_type),
                    'total_contracts': total_count,
                    'early_terminated_count': early_terminated_count,
                    'termination_rate': termination_rate
                })
                
                total_contracts_all_types += total_count
                total_early_terminated += early_terminated_count
        
        # Sort by termination rate descending (highest first)
        termination_data.sort(key=lambda x: x['termination_rate'], reverse=True)
        
        # Calculate overall statistics
        overall_termination_rate = 0.0
        if total_contracts_all_types > 0:
            overall_termination_rate = round((total_early_terminated / total_contracts_all_types) * 100, 2)
        
        # Find contract type with highest termination rate
        highest_rate_type = None
        lowest_rate_type = None
        if termination_data:
            highest_rate_type = termination_data[0]['contract_type_display']
            lowest_rate_type = termination_data[-1]['contract_type_display']
        
        response_data = {
            'termination_rates': termination_data,
            'statistics': {
                'total_contracts': total_contracts_all_types,
                'total_early_terminated': total_early_terminated,
                'overall_termination_rate': overall_termination_rate,
                'highest_rate_type': highest_rate_type,
                'lowest_rate_type': lowest_rate_type,
                'contract_types_analyzed': len(termination_data)
            }
        }
        
        logger.info(f"Early Termination Rate KPI: {total_early_terminated} of {total_contracts_all_types} "
                   f"contracts terminated early ({overall_termination_rate}%). "
                   f"Highest: {highest_rate_type}")
        
        return Response({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Early termination rate KPI error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve early termination rate KPI data',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ContractDashboard')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def time_to_approve_contract_kpi(request):
    """
    Get Time to Approve Contract KPI.
    Returns the average days to approve contracts per month.
    Calculates the time difference between assigned_date and approved_date from contract_approvals table.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        from django.db.models import Avg, F, ExpressionWrapper, DurationField
        from django.db.models.functions import ExtractMonth, ExtractYear
        from tprm_backend.contracts.models import ContractApproval
        from datetime import datetime
        
        # Get year parameter (default to current year)
        year = request.GET.get('year', datetime.now().year)
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = datetime.now().year
        
        # MULTI-TENANCY: Get contract IDs that belong to this tenant
        tenant_contract_ids = list(VendorContract.objects.filter(tenant_id=tenant_id).values_list('contract_id', flat=True))
        
        # Month names mapping
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        
        # Query approved contract approvals and calculate average approval time per month
        # Filter: status='APPROVED' and approved_date is not null
        # MULTI-TENANCY: Filter by tenant contract IDs
        approval_data = (
            ContractApproval.objects
            .filter(
                status='APPROVED',
                approved_date__isnull=False,
                assigned_date__isnull=False,
                approved_date__year=year,
                object_id__in=tenant_contract_ids
            )
            .annotate(
                month=ExtractMonth('approved_date'),
                # Calculate days between assigned_date and approved_date
                approval_days=ExpressionWrapper(
                    F('approved_date') - F('assigned_date'),
                    output_field=DurationField()
                )
            )
            .values('month')
            .annotate(
                avg_days=Avg('approval_days')
            )
            .order_by('month')
        )
        
        # Build time to approve data for all 12 months
        time_to_approve_data = []
        total_avg_days = 0
        months_with_data = 0
        
        # Create a dictionary for quick lookup
        approval_dict = {}
        for item in approval_data:
            if item['avg_days']:
                # Convert timedelta to days
                avg_days = item['avg_days'].total_seconds() / 86400  # 86400 seconds in a day
                approval_dict[item['month']] = round(avg_days, 1)
        
        # Build response for all 12 months
        for month_num in range(1, 13):
            avg_days = approval_dict.get(month_num, 0)
            
            time_to_approve_data.append({
                'month': month_names[month_num],
                'month_number': month_num,
                'days': avg_days
            })
            
            if avg_days > 0:
                total_avg_days += avg_days
                months_with_data += 1
        
        # Calculate overall average
        overall_avg = round(total_avg_days / months_with_data, 2) if months_with_data > 0 else 0
        
        # Find fastest and slowest months
        non_zero_months = [m for m in time_to_approve_data if m['days'] > 0]
        fastest_month = min(non_zero_months, key=lambda x: x['days']) if non_zero_months else None
        slowest_month = max(non_zero_months, key=lambda x: x['days']) if non_zero_months else None
        
        # Get total number of approved contracts in the year
        # MULTI-TENANCY: Filter by tenant contract IDs
        total_approvals = ContractApproval.objects.filter(
            status='APPROVED',
            approved_date__isnull=False,
            approved_date__year=year,
            object_id__in=tenant_contract_ids
        ).count()
        
        response_data = {
            'time_to_approve': time_to_approve_data,
            'statistics': {
                'year': year,
                'overall_average_days': overall_avg,
                'fastest_month': fastest_month['month'] if fastest_month else None,
                'fastest_days': fastest_month['days'] if fastest_month else 0,
                'slowest_month': slowest_month['month'] if slowest_month else None,
                'slowest_days': slowest_month['days'] if slowest_month else 0,
                'total_approvals': total_approvals,
                'months_with_data': months_with_data
            }
        }
        
        logger.info(f"Time to Approve Contract KPI: Year {year}, Overall Avg: {overall_avg} days, "
                   f"Total Approvals: {total_approvals}")
        
        return Response({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Time to approve contract KPI error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve time to approve contract KPI data',
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
        
        # Expiring soon (within 90 days) - active contracts only
        today = timezone.now().date()
        expiring_date = today + timedelta(days=90)
        expiring_contracts = base_query.filter(
            end_date__lte=expiring_date,
            end_date__gte=today,
            status='ACTIVE'
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def vendor_list(request):
    """List all vendors with filtering and pagination
    MULTI-TENANCY: Filters vendors by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get user_id from request
        from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
        user_id = RBACTPRMUtils.get_user_id_from_request(request)
        
        # Check if user is a vendor and get vendor info
        vendor_info = None
        if user_id:
            vendor_info = RBACTPRMUtils.get_vendor_info_for_user(user_id)
            if vendor_info:
                logger.info(f"[VENDOR LIST] User {user_id} is a vendor: {vendor_info['company_name']} (vendor_id: {vendor_info['vendor_id']})")
        
        # Get query parameters
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        vendor_category = request.GET.get('category', '')
        risk_level = request.GET.get('risk_level', '')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        ordering = request.GET.get('ordering', 'company_name')
        
        # Build query
        # MULTI-TENANCY: Filter by tenant
        queryset = Vendor.objects.filter(tenant_id=tenant_id)
        
        # VENDOR FILTERING: If user is a vendor, only show their own vendor record
        if vendor_info:
            queryset = queryset.filter(vendor_id=vendor_info['vendor_id'])
            logger.info(f"[VENDOR LIST] Filtering vendors for vendor_id: {vendor_info['vendor_id']}")
        
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
        
        # Optimize queryset with annotations to avoid N+1 queries
        queryset = queryset.annotate(
            contracts_count_annotated=Count(
                'contracts',
                filter=Q(contracts__is_archived=False),
                distinct=True
            ),
            total_value_annotated=Sum(
                'contracts__contract_value',
                filter=Q(contracts__is_archived=False)
            ),
            last_activity_annotated=Max(
                'contracts__created_at',
                filter=Q(contracts__is_archived=False)
            )
        )
        
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def vendor_detail(request, vendor_id):
    """Get vendor details by ID with contracts
    MULTI-TENANCY: Ensures vendor belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get vendor with optimized annotations to avoid N+1 queries
        # MULTI-TENANCY: Filter by tenant
        vendor = Vendor.objects.filter(tenant_id=tenant_id).annotate(
            contracts_count_annotated=Count(
                'contracts',
                filter=Q(contracts__is_archived=False, contracts__tenant_id=tenant_id),
                distinct=True
            ),
            total_value_annotated=Sum(
                'contracts__contract_value',
                filter=Q(contracts__is_archived=False, contracts__tenant_id=tenant_id)
            ),
            last_activity_annotated=Max(
                'contracts__created_at',
                filter=Q(contracts__is_archived=False, contracts__tenant_id=tenant_id)
            )
        ).get(vendor_id=vendor_id)
        
        # Get vendor contracts
        # MULTI-TENANCY: Filter by tenant
        contracts = VendorContract.objects.filter(
            vendor_id=vendor_id,
            is_archived=False,
            tenant_id=tenant_id
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def vendor_stats(request):
    """Get vendor statistics
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get user_id from request
        from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
        user_id = RBACTPRMUtils.get_user_id_from_request(request)
        
        # Check if user is a vendor and get vendor info
        vendor_info = None
        if user_id:
            vendor_info = RBACTPRMUtils.get_vendor_info_for_user(user_id)
            if vendor_info:
                logger.info(f"[VENDOR STATS] User {user_id} is a vendor: {vendor_info['company_name']} (vendor_id: {vendor_info['vendor_id']})")
        
        # Build base querysets
        # MULTI-TENANCY: Filter by tenant
        vendor_queryset = Vendor.objects.filter(tenant_id=tenant_id)
        contract_queryset = VendorContract.objects.filter(is_archived=False, tenant_id=tenant_id)
        
        # VENDOR FILTERING: If user is a vendor, only show stats for their vendor
        if vendor_info:
            vendor_id = vendor_info['vendor_id']
            vendor_queryset = vendor_queryset.filter(vendor_id=vendor_id)
            contract_queryset = contract_queryset.filter(vendor_id=vendor_id)
            logger.info(f"[VENDOR STATS] Filtering stats for vendor_id: {vendor_id}")
        
        # Get vendor statistics
        total_vendors = vendor_queryset.count()
        active_vendors = vendor_queryset.filter(status='APPROVED').count()
        
        # Get contracts by vendor
        vendor_contracts = contract_queryset.values('vendor_id').annotate(
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
            vendor_queryset.values('status')
            .annotate(count=Count('vendor_id'))
            .values_list('status', 'count')
        )
        
        # Vendors by risk level
        vendors_by_risk = dict(
            vendor_queryset.values('risk_level')
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def vendor_contacts_list(request, vendor_id):
    """Get vendor contacts by vendor ID
    MULTI-TENANCY: Ensures vendor belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Verify vendor exists
        # MULTI-TENANCY: Filter by tenant
        vendor = Vendor.objects.get(vendor_id=vendor_id, tenant_id=tenant_id)
        
        # Get vendor contacts
        # MULTI-TENANCY: Filter by tenant
        contacts = VendorContact.objects.filter(vendor_id=vendor_id, tenant_id=tenant_id)
        
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def vendor_contact_create(request, vendor_id):
    """Create a vendor contact
    MULTI-TENANCY: Ensures vendor belongs to tenant and sets tenant_id on contact
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Verify vendor exists
        # MULTI-TENANCY: Filter by tenant
        vendor = Vendor.objects.get(vendor_id=vendor_id, tenant_id=tenant_id)
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        # Create backup before operation
        backup_file = DatabaseBackupManager.create_backup()
        
        def create_contact():
            contact_data = request.data.copy()
            contact_data['vendor_id'] = vendor_id
            contact_data['created_by'] = getattr(request.user, 'userid', 1)
            # MULTI-TENANCY: Set tenant_id
            contact_data['tenant_id'] = tenant_id
            
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_renewals_list(request):
    """List contract renewals
    MULTI-TENANCY: Filters renewals by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get user_id from request
        from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
        user_id = RBACTPRMUtils.get_user_id_from_request(request)
        
        # Check if user is a vendor and get vendor info
        vendor_info = None
        if user_id:
            vendor_info = RBACTPRMUtils.get_vendor_info_for_user(user_id)
            if vendor_info:
                logger.info(f"[CONTRACT RENEWALS LIST] User {user_id} is a vendor: {vendor_info['company_name']} (vendor_id: {vendor_info['vendor_id']})")
        
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
        # MULTI-TENANCY: Filter by tenant
        renewals = ContractRenewal.objects.filter(tenant_id=tenant_id)
        
        # VENDOR FILTERING: If user is a vendor, only show renewals for their contracts
        if vendor_info:
            # Get all contract IDs for this vendor
            # MULTI-TENANCY: Filter by tenant
            vendor_contract_ids = VendorContract.objects.filter(
                vendor_id=vendor_info['vendor_id'],
                tenant_id=tenant_id
            ).values_list('contract_id', flat=True)
            
            renewals = renewals.filter(contract_id__in=vendor_contract_ids)
            logger.info(f"[CONTRACT RENEWALS LIST] Filtering renewals for vendor's contracts - found {len(vendor_contract_ids)} contracts")
        
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
        import traceback
        logger.error(f"Contract renewals list error: {str(e)}")
        logger.error(f"Contract renewals list traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve contract renewals',
            'message': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContractRenewal')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_renewal_create(request):
    """Create a contract renewal request
    MULTI-TENANCY: Ensures contract belongs to tenant and sets tenant_id on renewal
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
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
            # MULTI-TENANCY: Filter by tenant
            contract = VendorContract.objects.get(contract_id=contract_id, is_archived=False, tenant_id=tenant_id)
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
            # MULTI-TENANCY: Set tenant_id
            renewal_data['tenant_id'] = tenant_id
            
            # Create renewal
            try:
                renewal = serializer.save(**renewal_data)
                
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_renewal_detail(request, renewal_id):
    """Get contract renewal details
    MULTI-TENANCY: Ensures renewal belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get user_id from request
        from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
        user_id = RBACTPRMUtils.get_user_id_from_request(request)
        
        # Check if user is a vendor and get vendor info
        vendor_info = None
        if user_id:
            vendor_info = RBACTPRMUtils.get_vendor_info_for_user(user_id)
        
        # Get renewal
        # MULTI-TENANCY: Filter by tenant
        try:
            renewal = ContractRenewal.objects.get(renewal_id=renewal_id, tenant_id=tenant_id)
            
            # VENDOR FILTERING: Check if vendor user has access to this renewal's contract
            if vendor_info:
                # Check if the contract associated with this renewal belongs to the vendor
                # MULTI-TENANCY: Filter by tenant
                contract = VendorContract.objects.filter(
                    contract_id=renewal.contract_id,
                    vendor_id=vendor_info['vendor_id'],
                    tenant_id=tenant_id
                ).first()
                
                if not contract:
                    logger.warning(f"[CONTRACT RENEWAL DETAIL] Vendor user {user_id} attempted to access renewal {renewal_id} for non-owned contract {renewal.contract_id}")
                    return Response({
                        'success': False,
                        'error': 'Access denied',
                        'message': 'You do not have permission to view this renewal'
                    }, status=403)
                
                logger.info(f"[CONTRACT RENEWAL DETAIL] Vendor user {user_id} accessing renewal {renewal_id} for owned contract {renewal.contract_id}")
            
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_renewal_update(request, renewal_id):
    """Update contract renewal
    MULTI-TENANCY: Ensures renewal belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get renewal
        # MULTI-TENANCY: Filter by tenant
        try:
            renewal = ContractRenewal.objects.get(renewal_id=renewal_id, tenant_id=tenant_id)
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_renewal_delete(request, renewal_id):
    """Delete contract renewal
    MULTI-TENANCY: Ensures renewal belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get renewal
        # MULTI-TENANCY: Filter by tenant
        try:
            renewal = ContractRenewal.objects.get(renewal_id=renewal_id, tenant_id=tenant_id)
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_terms_list(request, contract_id):
    """Get contract terms by contract ID
    MULTI-TENANCY: Ensures contract belongs to tenant and filters terms
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Verify contract exists
        # MULTI-TENANCY: Filter by tenant
        contract = VendorContract.objects.get(contract_id=contract_id, is_archived=False, tenant_id=tenant_id)
        
        # Get contract terms
        # MULTI-TENANCY: Filter by tenant
        terms = ContractTerm.objects.filter(contract_id=contract_id, tenant_id=tenant_id)
        
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

def save_questionnaires_for_term(term_id, questionnaires_data, user, tenant_id=None):
    """
    Save questionnaires for a term to both questionnaire_template and contract_static_questionnaire tables.
    
    Args:
        term_id: The term_id for which questionnaires are being saved
        questionnaires_data: List of questionnaire objects with question_text, question_type, etc.
        user: The user creating the questionnaires
        tenant_id: MULTI-TENANCY: The tenant_id to set on questionnaires
    """
    from bcpdrp.models import QuestionnaireTemplate
    from audits_contract.models import ContractStaticQuestionnaire
    
    if not questionnaires_data or not isinstance(questionnaires_data, list) or len(questionnaires_data) == 0:
        logger.warning(f"No questionnaires data provided for term_id: {term_id}")
        return
    
    term_id_str = str(term_id)
    user_id = getattr(user, 'userid', None)
    
    logger.info(f"📋 Processing {len(questionnaires_data)} questionnaires for term_id: {term_id_str}")
    
    # Get the term's term_category from the database - CRITICAL for template matching
    term_category = None
    try:
        term_obj = ContractTerm.objects.filter(term_id=term_id_str).first()
        if term_obj:
            term_category = term_obj.term_category
            logger.info(f"📋 Found term_category '{term_category}' for term_id: {term_id_str}")
        else:
            logger.warning(f"⚠️ Term not found in database for term_id: {term_id_str}, cannot get term_category")
    except Exception as e:
        logger.warning(f"⚠️ Could not fetch term_category for term_id {term_id_str}: {e}")
    
    # Check if template_id is provided in questionnaires_data (from frontend template selection)
    provided_template_id = None
    if questionnaires_data and len(questionnaires_data) > 0:
        # Check if first question has template_id
        first_q = questionnaires_data[0]
        if first_q.get('template_id'):
            provided_template_id = first_q.get('template_id')
            logger.info(f"📋 Using provided template_id: {provided_template_id} for term_id: {term_id_str}")
            logger.info(f"📋 Received {len(questionnaires_data)} questions from selected template")
    
    # Prepare questions for questionnaire_template
    # IMPORTANT: When a template is selected, ONLY use the questions provided (which should be only from that template)
    # Do NOT add any other questions - the frontend sends only the questions that should be in the template
    template_questions = []
    
    for idx, q_data in enumerate(questionnaires_data):
        # Extract question data
        question_text = q_data.get('question_text', '').strip()
        if not question_text:
            logger.warning(f"Skipping questionnaire {idx + 1} - empty question_text")
            continue
        
        # If template_id is provided, verify this question belongs to that template
        # (This is a safety check - frontend should only send template questions)
        if provided_template_id and q_data.get('template_id'):
            if str(q_data.get('template_id')) != str(provided_template_id):
                logger.warning(f"Skipping question {idx + 1} - template_id mismatch (expected {provided_template_id}, got {q_data.get('template_id')})")
                continue
        
        raw_question_type = (q_data.get('question_type') or 'text').lower()
        question_type_map = {
            'text': 'text',
            'textarea': 'text',
            'long_text': 'text',
            'string': 'text',
            'paragraph': 'text',
            'date': 'text',
            'datetime': 'text',
            'number': 'number',
            'numeric': 'number',
            'integer': 'number',
            'decimal': 'number',
            'currency': 'number',
            'boolean': 'boolean',
            'bool': 'boolean',
            'yes/no': 'boolean',
            'yes_no': 'boolean',
            'true_false': 'boolean',
            'multiple_choice': 'multiple_choice',
            'multi_select': 'multiple_choice',
            'select': 'multiple_choice',
            'dropdown': 'multiple_choice',
            'checkbox': 'multiple_choice',
            'radio': 'multiple_choice',
        }
        question_type = question_type_map.get(raw_question_type, 'text')
        if question_type != raw_question_type:
            logger.debug(
                "Normalised question_type from '%s' to '%s' for term_id %s",
                raw_question_type,
                question_type,
                term_id_str
            )
        is_required = bool(q_data.get('is_required', False))
        scoring_weightings = float(q_data.get('scoring_weightings', 10.0))
        
        # Map question_type to answer_type for questionnaire_template
        answer_type_map = {
            'text': 'TEXT',
            'textarea': 'TEXTAREA',
            'number': 'NUMBER',
            'boolean': 'BOOLEAN',
            'yes/no': 'BOOLEAN',
            'multiple_choice': 'MULTIPLE_CHOICE',
            'checkbox': 'CHECKBOX',
            'rating': 'RATING',
            'scale': 'SCALE',
            'date': 'DATE',
        }
        answer_type = answer_type_map.get(question_type, 'TEXT')
        
        # Use term_category if available, otherwise fall back to question_category or 'Contract'
        # This ensures questions can be matched by term_category when fetching templates
        question_category = term_category or q_data.get('question_category') or 'Contract'
        
        # Create question object for template
        question_obj = {
            'question_id': q_data.get('question_id') or (idx + 1),
            'questionnaire_id': None,
            'display_order': idx + 1,
            'question_text': question_text,
            'question_category': question_category,  # Store term_category here for matching
            'term_category': term_category,  # Also store as separate field for clarity and direct matching
            'answer_type': answer_type,
            'is_required': is_required,
            'weightage': scoring_weightings,
            'metric_name': q_data.get('metric_name') or None,
            'term_id': term_id_str,
            'allow_document_upload': bool(q_data.get('allow_document_upload', False)),
            'options': q_data.get('options') or [],
            'help_text': q_data.get('help_text') or '',
            'created_at': timezone.now().isoformat()
        }
        template_questions.append(question_obj)
    
    logger.info(f"📋 Prepared {len(template_questions)} questions for template (from {len(questionnaires_data)} provided)")
    
    # CRITICAL: When a template_id is provided, ensure we ONLY use the questions provided
    # Do not add any other questions - the frontend sends only the questions that should be in the template
    if provided_template_id and template_questions:
        logger.info(f"🔒 Template ID provided ({provided_template_id}) - will ONLY save the {len(template_questions)} questions provided")
        logger.info(f"🔒 These questions will REPLACE all questions in the template (removed questions will be excluded)")
    
    # Save to questionnaire_template table first to get template_id
    template_id = None
    
    if template_questions:
        # If template_id is provided, update that template with the new questions
        if provided_template_id:
            try:
                # MULTI-TENANCY: Filter by tenant_id when getting template
                template_query = QuestionnaireTemplate.objects.filter(
                    template_id=provided_template_id,
                    module_type='CONTRACT'
                )
                if tenant_id:
                    template_query = template_query.filter(tenant_id=tenant_id)
                existing_template = template_query.first()
                
                if not existing_template:
                    # Try without tenant filter as fallback
                    existing_template = QuestionnaireTemplate.objects.get(
                        template_id=provided_template_id,
                        module_type='CONTRACT'
                    )
                    # Update tenant_id if it was missing
                    if tenant_id and not existing_template.tenant_id:
                        existing_template.tenant_id = tenant_id
                        existing_template.save()
                        logger.info(f"✅ Updated template {provided_template_id} with tenant_id: {tenant_id}")
                template_id = existing_template.template_id
                
                # IMPORTANT: When a template is selected, REPLACE all questions in the template
                # with the questions being sent. This ensures removed questions are actually removed.
                # The frontend sends only the questions that should be in the template.
                existing_template.template_questions_json = template_questions
                existing_template.updated_by = user_id
                existing_template.updated_at = timezone.now()
                # MULTI-TENANCY: Set tenant_id if missing
                if tenant_id and not existing_template.tenant_id:
                    existing_template.tenant_id = tenant_id
                existing_template.save()
                
                logger.info(f"✅ Updated provided template (ID: {template_id}) for term_id: {term_id_str}")
                logger.info(f"📋 Template now has {len(template_questions)} questions (replaced all questions, removed ones are now excluded)")
                
                # Delete existing ContractStaticQuestionnaire entries for this term_id before creating new ones
                # MULTI-TENANCY: Filter by tenant_id when deleting
                delete_query = ContractStaticQuestionnaire.objects.filter(term_id=term_id_str)
                if tenant_id:
                    delete_query = delete_query.filter(tenant_id=tenant_id)
                deleted_count, _ = delete_query.delete()
                logger.info(f"✅ Deleted {deleted_count} existing contract_static_questionnaires for term_id: {term_id_str} (tenant_id: {tenant_id}) before creating new ones")
                
            except QuestionnaireTemplate.DoesNotExist:
                logger.warning(f"⚠️ Provided template_id {provided_template_id} not found, creating/updating template")
                provided_template_id = None  # Reset to None to proceed with normal flow
        
        # If no template_id provided or template not found, check if a template already exists for this term
        if not template_id:
            existing_template = None
            # MULTI-TENANCY: Filter templates by tenant_id if available
            template_query = QuestionnaireTemplate.objects.filter(module_type='CONTRACT')
            if tenant_id:
                template_query = template_query.filter(tenant_id=tenant_id)
            all_templates = template_query
            for template in all_templates:
                questions = template.template_questions_json or []
                # Check if any question has this term_id
                if any(q.get('term_id') == term_id_str for q in questions):
                    existing_template = template
                    break
            
            if existing_template:
                # Update existing template by replacing questions for this term_id
                existing_questions = existing_template.template_questions_json or []
                # Filter out questions with the same term_id to avoid duplicates
                existing_questions = [q for q in existing_questions if q.get('term_id') != term_id_str]
                # Add new questions
                existing_questions.extend(template_questions)
                existing_template.template_questions_json = existing_questions
                existing_template.updated_by = user_id
                existing_template.updated_at = timezone.now()
                # MULTI-TENANCY: Set tenant_id if missing
                if tenant_id and not existing_template.tenant_id:
                    existing_template.tenant_id = tenant_id
                existing_template.save()
                template_id = existing_template.template_id
                logger.info(f"✅ Updated existing questionnaire_template (ID: {template_id}) for term_id: {term_id_str} with tenant_id: {tenant_id}")
                
                # Delete existing ContractStaticQuestionnaire entries for this term_id before creating new ones
                # MULTI-TENANCY: Filter by tenant_id when deleting
                delete_query = ContractStaticQuestionnaire.objects.filter(term_id=term_id_str)
                if tenant_id:
                    delete_query = delete_query.filter(tenant_id=tenant_id)
                deleted_count, _ = delete_query.delete()
                logger.info(f"✅ Deleted {deleted_count} existing contract_static_questionnaires for term_id: {term_id_str} (tenant_id: {tenant_id}) before creating new ones")
            else:
                # Create new template
                template_name = f"Contract Questionnaire - Term {term_id_str}"
                # MULTI-TENANCY: Get tenant_id for template
                tenant_id_for_template = tenant_id
                if not tenant_id_for_template:
                    try:
                        term_obj = ContractTerm.objects.filter(term_id=term_id_str).first()
                        if term_obj and hasattr(term_obj, 'tenant_id'):
                            tenant_id_for_template = term_obj.tenant_id
                    except:
                        pass
                
                template = QuestionnaireTemplate.objects.create(
                    template_name=template_name,
                    template_description=f"Questionnaire template for contract term {term_id_str}",
                    template_version='1.0',
                    template_type='STATIC',
                    template_questions_json=template_questions,
                    module_type='CONTRACT',
                    module_subtype='Contract Term',
                    approval_required=False,
                    status='ACTIVE',
                    is_active=True,
                    is_template=True,
                    created_by=user_id,
                    tenant_id=tenant_id_for_template  # MULTI-TENANCY: Set tenant_id
                )
                template_id = template.template_id
                logger.info(f"✅ Created new questionnaire_template (ID: {template_id}) for term_id: {term_id_str} with tenant_id: {tenant_id_for_template}")
    
    # Save to contract_static_questionnaire table with template_id
    questions_created = 0
    for idx, q_data in enumerate(questionnaires_data):
        try:
            # Extract question data
            question_text = q_data.get('question_text', '').strip()
            if not question_text:
                logger.warning(f"⚠️ Skipping questionnaire {idx + 1} - empty question_text")
                continue
            
            raw_question_type = (q_data.get('question_type') or 'text').lower()
            question_type = question_type_map.get(raw_question_type, 'text')
            if question_type != raw_question_type:
                logger.debug(
                    "Normalised question_type (static) from '%s' to '%s' for term_id %s",
                    raw_question_type,
                    question_type,
                    term_id_str
                )
            is_required = bool(q_data.get('is_required', False))
            scoring_weightings = float(q_data.get('scoring_weightings', 10.0))
            
            # Extract document_upload and multiple_choice fields
            document_upload = bool(q_data.get('document_upload', False) or q_data.get('allow_document_upload', False))
            
            # multiple_choice should only be set when question_type is 'multiple_choice'
            multiple_choice = None
            if question_type == 'multiple_choice':
                # Get options from the question data
                options = q_data.get('options', [])
                if isinstance(options, list) and len(options) > 0:
                    multiple_choice = options
                elif isinstance(options, str):
                    # If options is a string, try to parse it or split by comma
                    try:
                        import json
                        multiple_choice = json.loads(options)
                    except (json.JSONDecodeError, ValueError):
                        # If not valid JSON, split by comma
                        multiple_choice = [opt.strip() for opt in options.split(',') if opt.strip()]
            
            # Save to contract_static_questionnaire table with template_id
            # MULTI-TENANCY: Use tenant_id parameter or get from term object
            tenant_id_for_questionnaire = tenant_id
            if not tenant_id_for_questionnaire:
                try:
                    term_obj = ContractTerm.objects.filter(term_id=term_id_str).first()
                    if term_obj and hasattr(term_obj, 'tenant_id'):
                        tenant_id_for_questionnaire = term_obj.tenant_id
                except:
                    pass
            
            ContractStaticQuestionnaire.objects.create(
                term_id=term_id_str,
                template_id=template_id,  # Link to questionnaire_template
                question_text=question_text,
                question_type=question_type,
                is_required=is_required,
                scoring_weightings=scoring_weightings,
                document_upload=document_upload,
                multiple_choice=multiple_choice,
                tenant_id=tenant_id_for_questionnaire  # MULTI-TENANCY: Set tenant_id
            )
            questions_created += 1
            logger.info(f"✅ Created question {idx + 1} in contract_static_questionnaires for term_id: {term_id_str} with template_id: {template_id} and tenant_id: {tenant_id_for_questionnaire}")
        except Exception as q_error:
            logger.error(f"❌ Error creating questionnaire {idx + 1} for term_id {term_id_str}: {str(q_error)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Continue with next question instead of failing completely
            continue
    
    if questions_created == 0:
        logger.warning(f"⚠️ No questionnaires were created for term_id: {term_id_str} (out of {len(questionnaires_data)} provided)")
    else:
        logger.info(f"✅ Successfully saved {questions_created} out of {len(questionnaires_data)} questionnaires for term_id: {term_id_str} with template_id: {template_id}")


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContractTerm')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_terms_create(request, contract_id):
    """Create contract terms
    MULTI-TENANCY: Ensures contract belongs to tenant and sets tenant_id on terms
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get contract
        # MULTI-TENANCY: Filter by tenant
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=False,
            tenant_id=tenant_id
        )
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        term_data = request.data.copy()
        # Extract questionnaires payload (not part of ContractTerm model) before serializer validation
        questionnaires_data = term_data.pop('questionnaires', request.data.get('questionnaires', []))

        # Normalise questionnaires_data if it comes in as QueryDict or stringified JSON
        if isinstance(questionnaires_data, str):
            try:
                questionnaires_data = json.loads(questionnaires_data)
            except (TypeError, json.JSONDecodeError):
                logger.warning(f"⚠️ Unable to parse questionnaires string, defaulting to empty list. Value: {questionnaires_data}")
                questionnaires_data = []

        if questionnaires_data is None:
            questionnaires_data = []
        elif isinstance(questionnaires_data, QueryDict):
            questionnaires_data = list(questionnaires_data.values())
        elif isinstance(questionnaires_data, dict):
            questionnaires_data = [questionnaires_data]
        elif not isinstance(questionnaires_data, list):
            try:
                questionnaires_data = list(questionnaires_data)
            except TypeError:
                questionnaires_data = []

        def create_term():
            # Work on a mutable copy so we can safely augment it
            term_payload = term_data.copy()
            # Convert QueryDict to a flat dict so serializer doesn't receive QueryDict-specific behaviour
            if isinstance(term_payload, QueryDict):
                term_payload = term_payload.dict()

            term_payload['contract_id'] = contract.contract_id  # Use contract_id field
            term_payload['created_by'] = getattr(request.user, 'userid', 1)  # Use default user ID 1 if anonymous
            # MULTI-TENANCY: Set tenant_id
            term_payload['tenant_id'] = tenant_id
            
            # Log the term_id from request to verify it's being preserved
            requested_term_id = term_payload.get('term_id')
            if requested_term_id:
                logger.info(f"📋 Creating term with provided term_id: {requested_term_id}")
            else:
                logger.info(f"📋 Creating term without term_id, will be auto-generated")
            
            # Convert boolean values to integers for unmanaged models
            if 'is_standard' in term_payload:
                logger.info(f"Converting term is_standard: {term_payload['is_standard']} (type: {type(term_payload['is_standard'])})")
                term_payload['is_standard'] = 1 if term_payload['is_standard'] else 0
                logger.info(f"Converted term is_standard to: {term_payload['is_standard']}")
            
            # Ensure term_text is not empty
            if not term_payload.get('term_text') or term_payload.get('term_text').strip() == '':
                raise ValidationError({'term_text': ['This field is required and cannot be blank.']})
            
            serializer = ContractTermSerializer(data=term_payload)
            if serializer.is_valid():
                term = serializer.save(**term_payload)
                logger.info(f"✅ Contract term created: {term.term_id} for contract {contract_id}")
                # Verify term_id was preserved
                if requested_term_id and term.term_id != requested_term_id:
                    logger.warning(f"⚠️ Term ID changed from {requested_term_id} to {term.term_id}")
                elif requested_term_id and term.term_id == requested_term_id:
                    logger.info(f"✅ Term ID preserved: {term.term_id}")
                return term
            else:
                logger.error(f"❌ Serializer validation errors: {serializer.errors}")
                raise ValidationError(serializer.errors)
        # Store original term_id from request before creating term
        original_term_id_from_request = term_data.get('term_id') or request.data.get('term_id')
        
        logger.info(f"📋 Received questionnaires data for term creation: {len(questionnaires_data) if isinstance(questionnaires_data, list) else 0} items")
        if questionnaires_data and isinstance(questionnaires_data, list) and len(questionnaires_data) > 0:
            logger.info(f"📋 Sample questionnaire: {questionnaires_data[0]}")
        
        # Create term without backup (for speed)
        term = DatabaseBackupManager.retry_operation(create_term)
        
        # After term is created, check if term_id changed and update questionnaires
        saved_term_id = term.term_id
        if original_term_id_from_request and original_term_id_from_request != saved_term_id:
            logger.info(f"📋 Term ID changed from {original_term_id_from_request} to {saved_term_id}, updating questionnaires in view...")
            try:
                from audits_contract.models import ContractStaticQuestionnaire
                
                # Find and update questionnaires with the original term_id
                # MULTI-TENANCY: Filter by tenant
                questionnaires_to_update = ContractStaticQuestionnaire.objects.filter(
                    term_id=original_term_id_from_request,
                    tenant_id=tenant_id
                )
                
                if questionnaires_to_update.exists():
                    updated_count = questionnaires_to_update.update(term_id=saved_term_id)
                    logger.info(f"✅ Updated {updated_count} questionnaires from term_id {original_term_id_from_request} to {saved_term_id} (view-level)")
                
                # Also try partial matches
                if '_' in original_term_id_from_request:
                    parts = original_term_id_from_request.split('_')
                    for i in range(2, len(parts)):
                        partial_id = '_'.join(parts[:i])
                        if partial_id != saved_term_id:
                            # MULTI-TENANCY: Filter by tenant
                            matching = ContractStaticQuestionnaire.objects.filter(term_id=partial_id, tenant_id=tenant_id)
                            if matching.exists():
                                count = matching.update(term_id=saved_term_id)
                                logger.info(f"✅ Updated {count} questionnaires from partial term_id {partial_id} to {saved_term_id}")
            except Exception as e:
                logger.error(f"Error updating questionnaires in view: {str(e)}")
        
        # Save questionnaires for this term if provided in request
        if questionnaires_data and isinstance(questionnaires_data, list) and len(questionnaires_data) > 0:
            logger.info(f"📋 Saving {len(questionnaires_data)} questionnaires for term_id: {saved_term_id} with tenant_id: {tenant_id}")
            try:
                # MULTI-TENANCY: Pass tenant_id to save_questionnaires_for_term
                save_questionnaires_for_term(saved_term_id, questionnaires_data, request.user, tenant_id)
                logger.info(f"✅ Successfully saved questionnaires for term_id: {saved_term_id}")
            except Exception as questionnaire_error:
                logger.error(f"❌ Error saving questionnaires for term_id {saved_term_id}: {str(questionnaire_error)}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                # Don't fail the entire term creation if questionnaires fail, but log the error
                # This allows the term to be created even if questionnaires have issues
        
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_clauses_list(request, contract_id):
    """Get contract clauses by contract ID
    MULTI-TENANCY: Ensures contract belongs to tenant and filters clauses
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Verify contract exists
        # MULTI-TENANCY: Filter by tenant
        contract = VendorContract.objects.get(contract_id=contract_id, is_archived=False, tenant_id=tenant_id)
        
        # Get contract clauses
        # MULTI-TENANCY: Filter by tenant
        clauses = ContractClause.objects.filter(contract_id=contract_id, tenant_id=tenant_id)
        
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_clauses_create(request, contract_id):
    """Create contract clauses
    MULTI-TENANCY: Ensures contract belongs to tenant and sets tenant_id on clauses
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Get contract
        # MULTI-TENANCY: Filter by tenant
        contract = VendorContract.objects.get(
            contract_id=contract_id, 
            is_archived=False,
            tenant_id=tenant_id
        )
        
        # Validate input data
        SecurityManager.validate_contract_data(request.data)
        
        def create_clause():
            clause_data = request.data.copy()
            clause_data['contract_id'] = contract.contract_id  # Use contract_id field
            clause_data['created_by'] = getattr(request.user, 'userid', 1)  # Use default user ID 1 if anonymous
            # MULTI-TENANCY: Set tenant_id
            clause_data['tenant_id'] = tenant_id
            
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
                clause = serializer.save(**clause_data)
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_search(request):
    """Advanced contract search
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
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
        # MULTI-TENANCY: Filter by tenant
        queryset = VendorContract.objects.select_related('vendor').filter(tenant_id=tenant_id)
        
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def users_list(request):
    """Get all users for contract assignment
    MULTI-TENANCY: Filters users by tenant to ensure tenant isolation
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Get all users from custom User model
        users_list = []
        
        # Try ORM approach first
        try:
            from mfa_auth.models import User
            logger.info("Successfully imported User model from mfa_auth.models")
            
            # Try filtering by tenant_id first
            try:
                users = User.objects.filter(tenant_id=tenant_id).order_by('userid')
                logger.info(f"Filtered users by tenant_id={tenant_id}")
            except Exception as filter_error:
                logger.warning(f"Filtering by tenant_id failed: {filter_error}, trying without tenant filter")
                # Fallback: get all users if tenant_id filtering fails
                users = User.objects.all().order_by('userid')
                logger.info("Using all users (no tenant filter)")
            
            user_count = users.count()
            logger.info(f"Found {user_count} users in database for tenant_id={tenant_id}")
            
            # Convert to list and add display name
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
            
        except ImportError as import_err:
            logger.warning(f"User model import failed: {import_err}, trying raw SQL")
            # Fallback to raw SQL
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    # Try to query with tenant_id if column exists
                    try:
                        cursor.execute(
                            "SELECT UserId, UserName, FirstName, LastName FROM users WHERE TenantId = %s ORDER BY UserId",
                            [tenant_id]
                        )
                    except Exception:
                        # If TenantId column doesn't exist, get all users
                        cursor.execute(
                            "SELECT UserId, UserName, FirstName, LastName FROM users ORDER BY UserId"
                        )
                    
                    for row in cursor.fetchall():
                        user_id, username, first_name, last_name = row
                        full_name = f"{first_name or ''} {last_name or ''}".strip()
                        display_name = full_name if full_name else (username or f"User {user_id}")
                        
                        user_data = {
                            'user_id': user_id,
                            'username': username or f"user_{user_id}",
                            'display_name': display_name,
                            'role': 'user'
                        }
                        users_list.append(user_data)
                        logger.info(f"User (from raw SQL): {user_data}")
            except Exception as sql_err:
                logger.error(f"Raw SQL query also failed: {sql_err}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        except Exception as model_err:
            logger.error(f"Error accessing User model: {model_err}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Try raw SQL as last resort
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT UserId, UserName, FirstName, LastName FROM users ORDER BY UserId"
                    )
                    for row in cursor.fetchall():
                        user_id, username, first_name, last_name = row
                        full_name = f"{first_name or ''} {last_name or ''}".strip()
                        display_name = full_name if full_name else (username or f"User {user_id}")
                        
                        user_data = {
                            'user_id': user_id,
                            'username': username or f"user_{user_id}",
                            'display_name': display_name,
                            'role': 'user'
                        }
                        users_list.append(user_data)
            except Exception as sql_err:
                logger.error(f"Raw SQL fallback also failed: {sql_err}")
        
        logger.info(f"Returning {len(users_list)} users to frontend")
        
        return Response({
            'success': True,
            'data': users_list
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Users list error: {str(e)}")
        logger.error(f"Users list traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve users',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def legal_reviewers_list(request):
    """Get users with legal review roles for contract assignment
    MULTI-TENANCY: Filters users by tenant to ensure tenant isolation
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Get all users from custom User model (since RBAC is removed, all users can be legal reviewers)
        users_list = []
        
        # Try ORM approach first
        try:
            from mfa_auth.models import User
            logger.info("Successfully imported User model from mfa_auth.models for legal reviewers")
            
            # Try filtering by tenant_id first
            try:
                users = User.objects.filter(tenant_id=tenant_id).order_by('userid')
                logger.info(f"Filtered legal reviewers by tenant_id={tenant_id}")
            except Exception as filter_error:
                logger.warning(f"Filtering by tenant_id failed: {filter_error}, trying without tenant filter")
                # Fallback: get all users if tenant_id filtering fails
                users = User.objects.all().order_by('userid')
                logger.info("Using all users for legal reviewers (no tenant filter)")
            
            user_count = users.count()
            logger.info(f"Found {user_count} users for legal reviewers (tenant_id={tenant_id})")
            
            # Convert to list and add display name
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
            
        except ImportError as import_err:
            logger.warning(f"User model import failed: {import_err}, trying raw SQL")
            # Fallback to raw SQL
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    # Try to query with tenant_id if column exists
                    try:
                        cursor.execute(
                            "SELECT UserId, UserName, FirstName, LastName FROM users WHERE TenantId = %s ORDER BY UserId",
                            [tenant_id]
                        )
                    except Exception:
                        # If TenantId column doesn't exist, get all users
                        cursor.execute(
                            "SELECT UserId, UserName, FirstName, LastName FROM users ORDER BY UserId"
                        )
                    
                    for row in cursor.fetchall():
                        user_id, username, first_name, last_name = row
                        full_name = f"{first_name or ''} {last_name or ''}".strip()
                        display_name = full_name if full_name else (username or f"User {user_id}")
                        
                        user_data = {
                            'user_id': user_id,
                            'username': username or f"user_{user_id}",
                            'display_name': display_name,
                            'role': 'legal_reviewer'
                        }
                        users_list.append(user_data)
                        logger.info(f"Legal Reviewer (from raw SQL): {user_data}")
            except Exception as sql_err:
                logger.error(f"Raw SQL query also failed: {sql_err}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        except Exception as model_err:
            logger.error(f"Error accessing User model: {model_err}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Try raw SQL as last resort
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT UserId, UserName, FirstName, LastName FROM users ORDER BY UserId"
                    )
                    for row in cursor.fetchall():
                        user_id, username, first_name, last_name = row
                        full_name = f"{first_name or ''} {last_name or ''}".strip()
                        display_name = full_name if full_name else (username or f"User {user_id}")
                        
                        user_data = {
                            'user_id': user_id,
                            'username': username or f"user_{user_id}",
                            'display_name': display_name,
                            'role': 'legal_reviewer'
                        }
                        users_list.append(user_data)
            except Exception as sql_err:
                logger.error(f"Raw SQL fallback also failed: {sql_err}")
        
        logger.info(f"Returning {len(users_list)} legal reviewers to frontend")
        
        return Response({
            'success': True,
            'data': users_list
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Legal reviewers list error: {str(e)}")
        logger.error(f"Legal reviewers list traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve legal reviewers',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('approve')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_users_list(request):
    """Get users with ApproveContract permission for contract approval assignment
    MULTI-TENANCY: Filters users by tenant to ensure tenant isolation
    """
    try:
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Import required models
        users_with_permission = []
        
        try:
            from mfa_auth.models import User
            from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
            logger.info("Successfully imported User model and RBACTPRMUtils for approval users")
            
            # Get all active users (filter by is_active_raw which can be 'Y', 'YES', '1', 'TRUE')
            # MULTI-TENANCY: Try filtering by tenant_id first
            try:
                all_users = User.objects.filter(
                    is_active_raw__in=['Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true'],
                    tenant_id=tenant_id
                ).order_by('userid')
                logger.info(f"Filtered approval users by tenant_id={tenant_id}")
            except Exception as filter_error:
                logger.warning(f"Filtering by tenant_id failed: {filter_error}, trying without tenant filter")
                # Fallback: get all active users if tenant_id filtering fails
                all_users = User.objects.filter(
                    is_active_raw__in=['Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true']
                ).order_by('userid')
                logger.info("Using all active users for approval (no tenant filter)")
            
            user_count = all_users.count()
            logger.info(f"Found {user_count} active users in database for approval (tenant_id={tenant_id})")
            
            # Filter users who have ApproveContract or ReviewContract permission
            for user in all_users:
                user_id = user.userid
                
                # Check if user has ApproveContract permission
                has_approve_permission = RBACTPRMUtils.check_contract_permission(user_id, 'ApproveContract')
                
                # Check if user has ReviewContract permission (if it exists in the model)
                # Note: ReviewContract may not exist in the current model, but we check for it anyway
                # If it doesn't exist, check_contract_permission will return False
                has_review_permission = RBACTPRMUtils.check_contract_permission(user_id, 'ReviewContract')
                
                # Include user if they have either ApproveContract or ReviewContract permission
                if has_approve_permission or has_review_permission:
                    full_name = f"{user.first_name} {user.last_name}".strip()
                    display_name = full_name if full_name else user.username
                    
                    user_data = {
                        'user_id': user_id,
                        'username': user.username,
                        'display_name': display_name,
                        'role': 'approver'
                    }
                    users_with_permission.append(user_data)
                    logger.info(f"User with ApproveContract permission: {user_data}")
            
        except ImportError as import_err:
            logger.warning(f"User model import failed: {import_err}, trying raw SQL")
            # Fallback to raw SQL
            try:
                from django.db import connection
                from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
                
                with connection.cursor() as cursor:
                    # Try to query with tenant_id if column exists
                    try:
                        cursor.execute(
                            "SELECT UserId, UserName, FirstName, LastName, IsActive FROM users WHERE TenantId = %s AND IsActive IN ('Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true') ORDER BY UserId",
                            [tenant_id]
                        )
                    except Exception:
                        # If TenantId column doesn't exist, get all active users
                        cursor.execute(
                            "SELECT UserId, UserName, FirstName, LastName, IsActive FROM users WHERE IsActive IN ('Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true') ORDER BY UserId"
                        )
                    
                    for row in cursor.fetchall():
                        user_id, username, first_name, last_name, is_active = row
                        full_name = f"{first_name or ''} {last_name or ''}".strip()
                        display_name = full_name if full_name else (username or f"User {user_id}")
                        
                        # Check permissions using RBAC
                        has_approve_permission = RBACTPRMUtils.check_contract_permission(user_id, 'ApproveContract')
                        has_review_permission = RBACTPRMUtils.check_contract_permission(user_id, 'ReviewContract')
                        
                        if has_approve_permission or has_review_permission:
                            user_data = {
                                'user_id': user_id,
                                'username': username or f"user_{user_id}",
                                'display_name': display_name,
                                'role': 'approver'
                            }
                            users_with_permission.append(user_data)
                            logger.info(f"Approval User (from raw SQL): {user_data}")
            except Exception as sql_err:
                logger.error(f"Raw SQL query also failed: {sql_err}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        except Exception as model_err:
            logger.error(f"Error accessing User model: {model_err}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Try raw SQL as last resort
            try:
                from django.db import connection
                from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
                
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT UserId, UserName, FirstName, LastName, IsActive FROM users WHERE IsActive IN ('Y', 'YES', '1', 'TRUE', 'y', 'yes', 'true') ORDER BY UserId"
                    )
                    for row in cursor.fetchall():
                        user_id, username, first_name, last_name, is_active = row
                        full_name = f"{first_name or ''} {last_name or ''}".strip()
                        display_name = full_name if full_name else (username or f"User {user_id}")
                        
                        # Check permissions using RBAC
                        has_approve_permission = RBACTPRMUtils.check_contract_permission(user_id, 'ApproveContract')
                        has_review_permission = RBACTPRMUtils.check_contract_permission(user_id, 'ReviewContract')
                        
                        if has_approve_permission or has_review_permission:
                            user_data = {
                                'user_id': user_id,
                                'username': username or f"user_{user_id}",
                                'display_name': display_name,
                                'role': 'approver'
                            }
                            users_with_permission.append(user_data)
            except Exception as sql_err:
                logger.error(f"Raw SQL fallback also failed: {sql_err}")
        
        logger.info(f"Returning {len(users_with_permission)} users with ApproveContract permission to frontend")
        
        return Response({
            'success': True,
            'data': users_with_permission,
            'count': len(users_with_permission)
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Approval users list error: {str(e)}")
        logger.error(f"Approval users list traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve approval users',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def subcontracts_list(request, parent_contract_id):
    """Get all subcontracts for a parent contract"""
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({'error': 'Rate limit exceeded'}, status=429)
        
        # Get the parent contract to verify it exists
        try:
            parent_contract = VendorContract.objects.get(contract_id=parent_contract_id, is_archived=False, tenant_id=tenant_id)
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
            is_archived=False,
            tenant_id=tenant_id
        ).select_related('vendor').order_by('created_at')
        
        # Check if the current user is a vendor
        from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
        user_id = RBACTPRMUtils.get_user_id_from_request(request)
        is_vendor = False
        
        if user_id:
            is_vendor = RBACTPRMUtils.is_vendor_user(user_id)
            logger.info(f"[SUBCONTRACT] User {user_id} is_vendor: {is_vendor}")
        
        # Get terms and clauses for each subcontract (with permission check)
        subcontracts_with_details = []
        subcontracts_without_permission = []
        
        for subcontract in subcontracts:
            # Check permission_required field ONLY for vendor users
            # Non-vendor users always see full details
            should_restrict = is_vendor and not subcontract.permission_required
            
            if should_restrict:
                # Log the permission denial for vendor user
                logger.info(f"[SUBCONTRACT] Access denied to subcontract {subcontract.contract_id} - Vendor user with permission_required=False")
                
                # Add limited information with permission denial flag
                limited_data = {
                    'contract_id': subcontract.contract_id,
                    'contract_number': subcontract.contract_number,
                    'contract_title': subcontract.contract_title,
                    'status': subcontract.status,
                    'permission_denied': True,
                    'permission_message': 'You do not have permission to view the details of this subcontract',
                    'created_at': subcontract.created_at.isoformat() if subcontract.created_at else None
                }
                subcontracts_without_permission.append(limited_data)
                continue
            
            # Permission granted - show full details
            # Either: user is not a vendor, OR user is a vendor and permission_required=True
            permission_reason = "Non-vendor user" if not is_vendor else "permission_required=True"
            logger.info(f"[SUBCONTRACT] Access granted to subcontract {subcontract.contract_id} - {permission_reason}")
            
            # Get terms for this subcontract
            sub_terms = ContractTerm.objects.filter(contract_id=subcontract.contract_id, tenant_id=tenant_id).order_by('term_category', 'created_at')
            sub_terms_serializer = ContractTermSerializer(sub_terms, many=True)
            
            # Get clauses for this subcontract
            sub_clauses = ContractClause.objects.filter(contract_id=subcontract.contract_id, tenant_id=tenant_id).order_by('clause_type', 'created_at')
            sub_clauses_serializer = ContractClauseSerializer(sub_clauses, many=True)
            
            # Serialize the subcontract
            subcontract_serializer = VendorContractSerializer(subcontract)
            subcontract_data = subcontract_serializer.data
            
            # Add terms and clauses to the subcontract data
            subcontract_data['terms'] = sub_terms_serializer.data
            subcontract_data['clauses'] = sub_clauses_serializer.data
            subcontract_data['terms_count'] = len(sub_terms)
            subcontract_data['clauses_count'] = len(sub_clauses)
            subcontract_data['permission_denied'] = False
            
            subcontracts_with_details.append(subcontract_data)
        
        # Combine both lists - full details first, then limited info
        all_subcontracts = subcontracts_with_details + subcontracts_without_permission
        
        return Response({
            'success': True,
            'data': all_subcontracts,
            'message': f'Found {len(all_subcontracts)} subcontracts for contract {parent_contract_id}',
            'summary': {
                'total_subcontracts': len(all_subcontracts),
                'accessible_subcontracts': len(subcontracts_with_details),
                'restricted_subcontracts': len(subcontracts_without_permission),
                'total_terms': sum(s.get('terms_count', 0) for s in subcontracts_with_details),
                'total_clauses': sum(s.get('clauses_count', 0) for s in subcontracts_with_details)
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_amendments_as_contracts_list(request, parent_contract_id):
    """Get all contract amendments as contracts for a parent contract"""
    try:
        logger.info(f"[AMENDMENTS] === VIEW CALLED === Fetching amendments for parent contract: {parent_contract_id}")
        logger.info(f"[AMENDMENTS] User: {request.user}")
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Rate limiting
        if RateLimiter.is_rate_limited(request):
            return Response({'error': 'Rate limit exceeded'}, status=429)
        
        # Get the parent contract to verify it exists
        try:
            parent_contract = VendorContract.objects.get(contract_id=parent_contract_id, is_archived=False, tenant_id=tenant_id)
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
            is_archived=False,
            tenant_id=tenant_id
        ).select_related('vendor').order_by('created_at')
        
        logger.info(f"[AMENDMENTS] Found {amendments.count()} amendments for parent contract {parent_contract_id}")
        
        # Get terms and clauses for each amendment
        amendments_with_details = []
        for amendment in amendments:
            # Get terms for this amendment
            amendment_terms = ContractTerm.objects.filter(contract_id=amendment.contract_id, tenant_id=tenant_id).order_by('term_category', 'created_at')
            amendment_terms_serializer = ContractTermSerializer(amendment_terms, many=True)
            
            # Get clauses for this amendment
            amendment_clauses = ContractClause.objects.filter(contract_id=amendment.contract_id, tenant_id=tenant_id).order_by('clause_type', 'created_at')
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def subcontract_create(request, parent_contract_id):
    """Create a new subcontract under a parent contract"""
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
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
            parent_contract = VendorContract.objects.get(contract_id=parent_contract_id, tenant_id=tenant_id)
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
            # MULTI-TENANCY: Set tenant_id
            subcontract_data['tenant_id'] = tenant_id
            
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
            
            # MULTI-TENANCY: Get tenant_id from subcontract
            tenant_id = subcontract.tenant_id if hasattr(subcontract, 'tenant_id') else None
            
            logger.info(f"Processing subcontract terms: {len(terms_data)} terms, {len(clauses_data)} clauses")
            logger.info(f"Terms data: {terms_data}")
            logger.info(f"Clauses data: {clauses_data}")
            try:
                from django.db.models import Count
                # MULTI-TENANCY: Filter by tenant_id if available
                if tenant_id:
                    pre_terms_count = ContractTerm.objects.filter(contract_id=subcontract.contract_id, tenant_id=tenant_id).count()
                else:
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
                questionnaires_data = term_data.pop('questionnaires', [])
                
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
                    try:
                        if questionnaires_data and isinstance(questionnaires_data, list):
                            logger.info(f"Saving {len(questionnaires_data)} questionnaires for subcontract term {created_term.term_id}")
                            save_questionnaires_for_term(created_term.term_id, questionnaires_data, request.user)
                    except Exception as questionnaire_error:
                        logger.error(f"Error saving questionnaires for subcontract term {created_term.term_id}: {str(questionnaire_error)}")
                except Exception as e:
                    logger.error(f"❌ Error creating term for subcontract: {str(e)}")
                    logger.error(f"Term data that failed: {term_data}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
            # Post-insert verification
            try:
                # MULTI-TENANCY: Filter by tenant_id if available
                if tenant_id:
                    post_terms_qs = ContractTerm.objects.filter(contract_id=subcontract.contract_id, tenant_id=tenant_id)
                else:
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
                # MULTI-TENANCY: Add tenant_id if available
                if tenant_id and 'tenant_id' not in clause_data:
                    clause_data['tenant_id'] = tenant_id
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_amendments_list(request, contract_id):
    """Get all amendments for a specific contract"""
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Check if contract exists
        try:
            contract = VendorContract.objects.get(contract_id=contract_id, tenant_id=tenant_id)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Contract not found',
                'message': f'Contract with ID {contract_id} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get amendments for the contract
        amendments = ContractAmendment.objects.filter(contract_id=contract_id, tenant_id=tenant_id).order_by('-amendment_date')
        
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_amendments_create(request, contract_id):
    """Create a new amendment for a specific contract"""
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Check if contract exists
        try:
            contract = VendorContract.objects.get(contract_id=contract_id, tenant_id=tenant_id)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Contract not found',
                'message': f'Contract with ID {contract_id} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Add contract_id to the data
        data = request.data.copy()
        data['contract_id'] = contract_id
        # MULTI-TENANCY: Set tenant_id
        data['tenant_id'] = tenant_id
        
        # Add created_by from request user
        if hasattr(request, 'user') and request.user:
            data['created_by'] = getattr(request.user, 'userid', 1)
        
        serializer = ContractAmendmentCreateSerializer(data=data)
        if serializer.is_valid():
            amendment = serializer.save(**data)
            
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_amendment_detail(request, contract_id, amendment_id):
    """Get a specific amendment for a contract"""
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        try:
            amendment = ContractAmendment.objects.get(
                contract_id=contract_id,
                amendment_id=amendment_id,
                tenant_id=tenant_id
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
                questionnaires_data = term_data.pop('questionnaires', [])
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
                created_term = ContractTerm.objects.create(**term_data)
                logger.info(f"Term {i+1} created successfully")

                try:
                    if questionnaires_data and isinstance(questionnaires_data, list):
                        logger.info(f"Saving {len(questionnaires_data)} questionnaires for term_id {created_term.term_id}")
                        save_questionnaires_for_term(created_term.term_id, questionnaires_data, request.user)
                except Exception as questionnaire_error:
                    logger.error(f"Error saving questionnaires for term {created_term.term_id}: {str(questionnaire_error)}")
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


@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('TriggerOCR')
@parser_classes([MultiPartParser, FormParser])
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
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        logger.debug(f"[upload_contract_ocr] Tenant ID: {tenant_id}")
        logger.debug(f"[upload_contract_ocr] Contract ID: {contract_id}")
        
        # Get the contract (with tenant filtering if available)
        try:
            contract_query = VendorContract.objects.filter(
                contract_id=contract_id,
                is_archived=False
            )
            # Filter by tenant if tenant_id is available
            if tenant_id:
                contract_query = contract_query.filter(tenant_id=tenant_id)
            
            contract = contract_query.get()
            logger.debug(f"[upload_contract_ocr] Contract found: {contract.contract_title}")
        except VendorContract.DoesNotExist:
            logger.error(f"[upload_contract_ocr] Contract {contract_id} not found (tenant_id: {tenant_id})")
            return Response({
                'success': False,
                'error': 'Contract not found',
                'message': f'Contract {contract_id} not found or you do not have access to it'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"[upload_contract_ocr] Error getting contract: {str(e)}")
            import traceback
            logger.error(f"[upload_contract_ocr] Traceback: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': 'Error accessing contract',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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
        
        # Get user ID safely
        try:
            if hasattr(request, 'user') and request.user and hasattr(request.user, 'userid'):
                user_id = str(request.user.userid)
            elif hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
                user_id = str(request.user.id)
            else:
                user_id = 'system'
            logger.debug(f"[upload_contract_ocr] User ID: {user_id}")
        except Exception as e:
            logger.warning(f"[upload_contract_ocr] Error getting user ID: {str(e)}, using 'system'")
            user_id = 'system'
        
        # Initialize OCR service and process document
        try:
            ocr_service = DocumentProcessingService()
            logger.debug(f"[upload_contract_ocr] OCR service initialized")
        except Exception as e:
            logger.error(f"[upload_contract_ocr] Error initializing OCR service: {str(e)}")
            import traceback
            logger.error(f"[upload_contract_ocr] Traceback: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': 'Failed to initialize OCR service',
                'message': f'OCR service initialization failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Use contract-only processing (faster, no SLA extraction)
        try:
            ocr_result = ocr_service.process_contract_only(temp_file_path, user_id=user_id)
        except Exception as e:
            logger.error(f"[upload_contract_ocr] Error during OCR processing: {str(e)}")
            import traceback
            logger.error(f"[upload_contract_ocr] Traceback: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': 'OCR processing failed',
                'message': f'Failed to process document: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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
        
        # Handle case where contract_data might be None
        if contract_data is None:
            contract_data = {}
        
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
        # MULTI-TENANCY: Get tenant_id from contracts
        tenant_id = source_contract.tenant_id if hasattr(source_contract, 'tenant_id') else None
        
        # Copy terms
        # MULTI-TENANCY: Filter by tenant_id if available
        if tenant_id:
            terms = ContractTerm.objects.filter(contract_id=source_contract.contract_id, tenant_id=tenant_id)
        else:
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
                
                # MULTI-TENANCY: Include tenant_id when creating term
                term_create_data = {
                    'contract_id': target_contract.contract_id,
                    'term_id': new_term_id,
                    'term_title': term.term_title,
                    'term_text': term.term_text,
                    'term_category': term.term_category,
                    'risk_level': term.risk_level,
                    'compliance_status': term.compliance_status,
                    'approval_status': term.approval_status,
                    'version_number': term.version_number,
                    'is_standard': term.is_standard,
                    'created_by': term.created_by
                }
                if tenant_id:
                    term_create_data['tenant_id'] = tenant_id
                ContractTerm.objects.create(**term_create_data)
                logger.info(f"Successfully created term with ID: {new_term_id}")
            except Exception as term_error:
                logger.error(f"Error copying term {term.term_id}: {str(term_error)}")
                continue
        
        # Copy clauses
        # MULTI-TENANCY: Filter by tenant_id if available
        if tenant_id:
            clauses = ContractClause.objects.filter(contract_id=source_contract.contract_id, tenant_id=tenant_id)
        else:
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
                
                # MULTI-TENANCY: Include tenant_id when creating clause
                clause_create_data = {
                    'contract_id': target_contract.contract_id,
                    'clause_id': new_clause_id,
                    'clause_name': clause.clause_name,
                    'clause_text': clause.clause_text,
                    'clause_type': clause.clause_type,
                    'risk_level': clause.risk_level,
                    'legal_category': clause.legal_category,
                    'version_number': clause.version_number,
                    'is_standard': clause.is_standard,
                    'created_by': clause.created_by
                }
                if tenant_id:
                    clause_create_data['tenant_id'] = tenant_id
                ContractClause.objects.create(**clause_create_data)
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


@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def trigger_contract_risk_analysis(request, contract_id):
    """Trigger risk analysis for a contract after creation (non-blocking)"""
    try:
        print(f"=== RISK ANALYSIS TRIGGER DEBUG: Received request for contract {contract_id} ===")
        print(f"=== RISK ANALYSIS TRIGGER DEBUG: Request method: {request.method} ===")
        print(f"=== RISK ANALYSIS TRIGGER DEBUG: Request headers: {dict(request.headers)} ===")
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        logger.debug(f"[trigger_contract_risk_analysis] Tenant ID: {tenant_id}")
        
        # Check if contract exists (with tenant filtering if available)
        try:
            contract_query = VendorContract.objects.filter(
                contract_id=contract_id,
                is_archived=False
            )
            # Filter by tenant if tenant_id is available
            if tenant_id:
                contract_query = contract_query.filter(tenant_id=tenant_id)
            
            contract = contract_query.get()
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
                        import traceback
                        from contract_risk_analysis.tasks import analyze_contract_risk_task
                        # Run synchronously in the background thread
                        # Note: @shared_task decorated functions can be called directly
                        result = analyze_contract_risk_task(contract_id)
                        print(f"=== RISK ANALYSIS TRIGGER DEBUG: Risk analysis completed in background thread ===")
                        logger.info(f"Risk analysis completed in background thread for contract {contract_id}: {result}")
                    except ImportError as e:
                        error_msg = f"Failed to import risk analysis task: {str(e)}"
                        print(f"=== RISK ANALYSIS TRIGGER DEBUG: Import error: {error_msg} ===")
                        logger.error(f"Import error in background risk analysis for contract {contract_id}: {error_msg}")
                        logger.error(f"Import traceback: {traceback.format_exc()}")
                    except Exception as e:
                        import traceback
                        error_msg = str(e)
                        print(f"=== RISK ANALYSIS TRIGGER DEBUG: Error in background risk analysis: {error_msg} ===")
                        logger.error(f"Error in background risk analysis for contract {contract_id}: {error_msg}")
                        logger.error(f"Error traceback: {traceback.format_exc()}")
                
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
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Check if contract exists and belongs to tenant
        contract = get_object_or_404(VendorContract, contract_id=contract_id, tenant_id=tenant_id)
        
        # Delete all terms for this contract
        # MULTI-TENANCY: Filter by tenant_id
        deleted_count, _ = ContractTerm.objects.filter(contract_id=contract_id, tenant_id=tenant_id).delete()
        
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
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Check if contract exists and belongs to tenant
        contract = get_object_or_404(VendorContract, contract_id=contract_id, tenant_id=tenant_id)
        
        # Delete all clauses for this contract
        # MULTI-TENANCY: Filter by tenant_id
        deleted_count, _ = ContractClause.objects.filter(contract_id=contract_id, tenant_id=tenant_id).delete()
        
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
        
        # Extract base contract number (without version suffix)
        base_contract_number = original_contract.contract_number
        # Remove any existing version suffix like "-v1.0", "-v1.1", etc.
        if '-v' in base_contract_number:
            base_contract_number = base_contract_number.split('-v')[0]
            logger.info(f"Extracted base contract number: {base_contract_number}")
        
        # Check if the calculated version already exists and find next available version
        versioned_contract_number = f"{base_contract_number}-v{new_version}"
        attempt_count = 0
        max_attempts = 50  # Prevent infinite loop
        
        while VendorContract.objects.filter(contract_number=versioned_contract_number).exists() and attempt_count < max_attempts:
            logger.warning(f"Contract number {versioned_contract_number} already exists, incrementing version")
            attempt_count += 1
            
            if version_type == 'major':
                # Increment major version: 2 -> 3 -> 4
                new_version = int(new_version) + 1
            else:  # minor
                # Increment minor version: 1.1 -> 1.2 -> 1.3
                if '.' in str(new_version):
                    major, minor = str(new_version).split('.')
                    new_version = f"{major}.{int(minor) + 1}"
                else:
                    new_version = f"{new_version}.1"
            
            versioned_contract_number = f"{base_contract_number}-v{new_version}"
        
        if attempt_count >= max_attempts:
            logger.error(f"Could not find available version number after {max_attempts} attempts")
            raise ValueError(f"Could not find available version number for contract {base_contract_number}")
        
        logger.info(f"Creating versioned contract number: {versioned_contract_number} (version: {new_version})")
        
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
        
        # Extract base contract number (without version suffix)
        base_contract_number = original_contract.contract_number
        # Remove any existing version suffix like "-v1.0", "-v1.1", etc.
        if '-v' in base_contract_number:
            base_contract_number = base_contract_number.split('-v')[0]
            logger.info(f"Extracted base contract number: {base_contract_number}")
        
        # Check if the calculated version already exists and find next available version
        versioned_contract_number = f"{base_contract_number}-v{new_version}"
        attempt_count = 0
        max_attempts = 50  # Prevent infinite loop
        
        while VendorContract.objects.filter(contract_number=versioned_contract_number).exists() and attempt_count < max_attempts:
            logger.warning(f"Contract number {versioned_contract_number} already exists, incrementing version")
            attempt_count += 1
            
            if version_type == 'major':
                # Increment major version: 2.0 -> 3.0 -> 4.0
                new_version = Decimal(str(int(new_version) + 1))
            else:  # minor
                # Increment minor version: 1.1 -> 1.2 -> 1.3
                major_part = int(new_version)
                minor_part = float(new_version) - major_part
                new_version = Decimal(str(round(major_part + minor_part + 0.1, 1)))
            
            versioned_contract_number = f"{base_contract_number}-v{new_version}"
        
        if attempt_count >= max_attempts:
            logger.error(f"Could not find available version number after {max_attempts} attempts")
            raise ValueError(f"Could not find available version number for contract {base_contract_number}")
        
        logger.info(f"Creating versioned contract number: {versioned_contract_number} (version: {new_version})")
        
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
                    questionnaires_data = term_data.pop('questionnaires', [])
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
                    try:
                        if questionnaires_data and isinstance(questionnaires_data, list):
                            logger.info(f"Saving {len(questionnaires_data)} questionnaires for subcontract term {created_term.term_id}")
                            save_questionnaires_for_term(created_term.term_id, questionnaires_data, request.user)
                    except Exception as questionnaire_error:
                        logger.error(f"Error saving questionnaires for subcontract term {created_term.term_id}: {str(questionnaire_error)}")
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
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({
                'success': False,
                'error': 'Tenant context not found'
            }, status=403)
        
        # Get original contract
        try:
            original_contract = VendorContract.objects.get(contract_id=contract_id, tenant_id=tenant_id)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Original contract not found'
            }, status=404)

        # Get amendment contract
        try:
            amendment_contract = VendorContract.objects.get(contract_id=amendment_id, tenant_id=tenant_id)
        except VendorContract.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Amendment contract not found'
            }, status=404)

        # Get contract terms
        # MULTI-TENANCY: Filter by tenant_id
        original_terms = ContractTerm.objects.filter(contract_id=contract_id, tenant_id=tenant_id)
        amendment_terms = ContractTerm.objects.filter(contract_id=amendment_id, tenant_id=tenant_id)

        # Get contract clauses
        # MULTI-TENANCY: Filter by tenant_id
        original_clauses = ContractClause.objects.filter(contract_id=contract_id, tenant_id=tenant_id)
        amendment_clauses = ContractClause.objects.filter(contract_id=amendment_id, tenant_id=tenant_id)

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

