"""
Function-based views for BCP/DRP API with RBAC integration
Following the pattern from rbac/example_views.py
"""
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.http import HttpRequest
from django.db.models import Q, Max
from django.db import models, connection, transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime
import requests
import logging
import json
import jwt
import traceback
from tprm_backend.bcpdrp.utils import success_response, error_response, not_found_response, validation_error_response
from tprm_backend.bcpdrp.models import Plan, Dropdown, Questionnaire, Question, BcpDetails, DrpDetails, Evaluation, Users, BcpDrpApprovals, TestAssignmentsResponses, QuestionnaireTemplate
from tprm_backend.bcpdrp.serializers import (
    PlanListSerializer, PlanCreateSerializer,
    QuestionnaireListSerializer, QuestionnaireDetailSerializer, 
    QuestionnaireCreateSerializer, QuestionnaireUpdateSerializer,
    UserSerializer
)
from tprm_backend.audits.models import StaticQuestionnaire
from tprm_backend.audits_contract.models import ContractStaticQuestionnaire
import logging
import hashlib
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# RBAC imports
from tprm_backend.rbac.tprm_decorators import rbac_bcp_drp_required

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
        is_authenticated = bool(
            request.user and 
            request.user.is_authenticated and
            hasattr(request.user, 'userid')
        )
        
        # If not authenticated, we need to check if it's because no auth was provided
        # or because auth failed. If request.user is AnonymousUser, no auth was provided.
        if not is_authenticated:
            from django.contrib.auth.models import AnonymousUser
            if isinstance(request.user, AnonymousUser):
                # No authentication was provided - return 401
                from rest_framework.exceptions import NotAuthenticated
                raise NotAuthenticated('Authentication credentials were not provided.')
        
        return is_authenticated


class JWTAuthentication(BaseAuthentication):
    """Custom JWT authentication class for DRF"""
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        # Debug logging
        logger.info(f"[BCP JWT Auth] Path: {request.path}")
        logger.info(f"[BCP JWT Auth] Authorization header present: {bool(auth_header)}")
        if auth_header:
            logger.info(f"[BCP JWT Auth] Auth header starts with Bearer: {auth_header.startswith('Bearer ')}")
        
        # If no authorization header, return None to allow other auth methods
        if not auth_header:
            logger.warning(f"[BCP JWT Auth] No Authorization header for {request.path}")
            return None
        
        # If authorization header exists but doesn't start with Bearer, raise error
        if not auth_header.startswith('Bearer '):
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed('Invalid authentication header format. Expected: Bearer <token>')
        
        try:
            token = auth_header.split(' ')[1]
            logger.info(f"[BCP JWT Auth] Token extracted: {token[:20]}...")
            
            # Use JWT_SECRET_KEY from settings
            secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            logger.info(f"[BCP JWT Auth] Token decoded successfully, user_id: {user_id}")
            
            if user_id:
                try:
                    from mfa_auth.models import User
                    user = User.objects.get(userid=user_id)
                    # Add is_authenticated attribute for DRF compatibility
                    user.is_authenticated = True
                    logger.info(f"[BCP JWT Auth] User authenticated: {user.username}")
                    return (user, token)
                except ImportError:
                    # If User model import fails, create a mock user
                    logger.warning(f"[BCP JWT Auth] User model import failed, creating mock user for user_id: {user_id}")
                    class MockUser:
                        def __init__(self, user_id):
                            self.userid = user_id
                            self.username = f"user_{user_id}"
                            self.is_authenticated = True
                    
                    return (MockUser(user_id), token)
                except Exception as e:
                    # If User model doesn't exist or other error, create a mock user
                    logger.warning(f"[BCP JWT Auth] User {user_id} not found or error: {e}, creating mock user")
                    class MockUser:
                        def __init__(self, user_id):
                            self.userid = user_id
                            self.username = f"user_{user_id}"
                            self.is_authenticated = True
                    
                    return (MockUser(user_id), token)
            else:
                from rest_framework.exceptions import AuthenticationFailed
                logger.error("[BCP JWT Auth] Token does not contain user_id")
                raise AuthenticationFailed('Token does not contain user_id')
                
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            logger.error(f"JWT authentication error: {str(e)}")
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return 'Bearer realm="api"'


def get_comprehensive_plan_data(plan_id, evaluation_id=None, tenant_id=None):
    """
    Gather comprehensive plan data including plan info, extracted details, and evaluation data
    
    Args:
        plan_id: Plan ID
        evaluation_id: Optional evaluation ID
        tenant_id: Optional tenant ID for filtering
        
    Returns:
        dict: Comprehensive plan data for LLaMA analysis
    MULTI-TENANCY: Filters by tenant_id if provided
    """
    try:
        # Get plan basic info
        # MULTI-TENANCY: Filter by tenant if provided
        if tenant_id:
            plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
        else:
            plan = Plan.objects.get(plan_id=plan_id)
        plan_data = {
            'plan_id': plan.plan_id,
            'plan_name': plan.plan_name,
            'plan_type': plan.plan_type,
            'strategy_name': plan.strategy_name,
            'vendor_id': plan.vendor_id,
            'version': plan.version,
            'document_date': plan.document_date.isoformat() if plan.document_date else None,
            'criticality': plan.criticality,
            'status': plan.status,
            'submitted_at': plan.submitted_at.isoformat() if plan.submitted_at else None,
            'ocr_extracted': plan.ocr_extracted,
            'ocr_extracted_at': plan.ocr_extracted_at.isoformat() if plan.ocr_extracted_at else None
        }
        
        # Get extracted details from unified ocr_extracted_data field
        extracted_details = None
        if plan.ocr_extracted_data:
            extracted_details = plan.ocr_extracted_data.copy()
            extracted_details['type'] = plan.plan_type
            extracted_details['extracted_at'] = plan.ocr_extracted_at.isoformat() if plan.ocr_extracted_at else None
        else:
            logger.warning(f"No extracted data found for plan {plan_id} in ocr_extracted_data field")
        
        # Get evaluation data if evaluation_id is provided
        evaluation_data = None
        if evaluation_id:
            try:
                # MULTI-TENANCY: Filter by tenant if provided
                if tenant_id:
                    evaluation = Evaluation.objects.get(evaluation_id=evaluation_id, tenant_id=tenant_id)
                else:
                    evaluation = Evaluation.objects.get(evaluation_id=evaluation_id)
                evaluation_data = {
                    'evaluation_id': evaluation.evaluation_id,
                    'plan_id': evaluation.plan_id,
                    'assigned_to_user_id': evaluation.assigned_to_user_id,
                    'assigned_by_user_id': evaluation.assigned_by_user_id,
                    'assigned_at': evaluation.assigned_at.isoformat() if evaluation.assigned_at else None,
                    'due_date': evaluation.due_date.isoformat() if evaluation.due_date else None,
                    'status': evaluation.status,
                    'started_at': evaluation.started_at.isoformat() if evaluation.started_at else None,
                    'submitted_at': evaluation.submitted_at.isoformat() if evaluation.submitted_at else None,
                    'overall_score': float(evaluation.overall_score) if evaluation.overall_score else None,
                    'quality_score': float(evaluation.quality_score) if evaluation.quality_score else None,
                    'coverage_score': float(evaluation.coverage_score) if evaluation.coverage_score else None,
                    'recovery_capability_score': float(evaluation.recovery_capability_score) if evaluation.recovery_capability_score else None,
                    'compliance_score': float(evaluation.compliance_score) if evaluation.compliance_score else None,
                    'weighted_score': float(evaluation.weighted_score) if evaluation.weighted_score else None,
                    'criteria_json': evaluation.criteria_json,
                    'evaluator_comments': evaluation.evaluator_comments
                }
            except Evaluation.DoesNotExist:
                logger.warning(f"No evaluation found for evaluation_id {evaluation_id}")
        
        # Combine all data
        comprehensive_data = {
            'plan_info': plan_data,
            'extracted_details': extracted_details,
            'evaluation_data': evaluation_data
        }
        
        logger.info(f"Gathered comprehensive data for plan {plan_id} (evaluation: {evaluation_id})")
        return comprehensive_data
        
    except Plan.DoesNotExist:
        logger.error(f"Plan {plan_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error gathering comprehensive plan data for plan {plan_id}: {str(e)}")
        return None


def generate_risks_for_plan_evaluation(plan_id, evaluation_id=None, tenant_id=None):
    """
    Generate risks using comprehensive plan data (plan + extracted details + evaluation)
    
    Args:
        plan_id: Plan ID
        evaluation_id: Optional evaluation ID
        tenant_id: Optional tenant ID for filtering
        
    Returns:
        dict: Risk generation response or None if failed
    MULTI-TENANCY: Passes tenant_id to get_comprehensive_plan_data
    """
    try:
        # Get comprehensive plan data
        # MULTI-TENANCY: Pass tenant_id
        comprehensive_data = get_comprehensive_plan_data(plan_id, evaluation_id, tenant_id=tenant_id)
        if not comprehensive_data:
            return None
        
        # Call the risk generation service directly (no HTTP request)
        from risk_analysis.services import RiskAnalysisService
        
        service = RiskAnalysisService()
        result = service.analyze_comprehensive_plan_data(
            entity='bcp_drp_module',
            comprehensive_data=comprehensive_data
        )
        
        logger.info(f"Generated {len(result.get('risks', []))} risks for comprehensive plan {plan_id} data")
        return result
            
    except Exception as e:
        logger.error(f"Error calling comprehensive risk generation service: {str(e)}")
        return None


def sanitize_json_for_db(data):
    """
    Recursively sanitize JSON data to ensure it can be serialized to database JSONField.
    Removes undefined values, converts non-serializable types, and ensures dict/list structure.
    
    Args:
        data: The data to sanitize (dict, list, or primitive)
        
    Returns:
        Sanitized data that can be safely stored in JSONField
    """
    if data is None:
        return None
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Skip None keys or undefined-like values
            if key is None:
                continue
            # Recursively sanitize nested structures
            sanitized_value = sanitize_json_for_db(value)
            # Only include if value is not None (unless it's explicitly None in dict context)
            sanitized[key] = sanitized_value
        return sanitized
    
    elif isinstance(data, list):
        sanitized = []
        for item in data:
            sanitized_item = sanitize_json_for_db(item)
            sanitized.append(sanitized_item)
        return sanitized
    
    elif isinstance(data, (str, int, float, bool)):
        return data
    
    else:
        # Try to convert to string if it's not a basic type
        try:
            # Attempt JSON serialization to check if it's serializable
            json.dumps(data)
            return data
        except (TypeError, ValueError):
            # If not serializable, convert to string
            return str(data)


def generate_risks_for_entity(entity, table, row_id):
    """
    Helper function to call the Risk Generation service directly (legacy method)
    
    Args:
        entity: Entity name (e.g., 'bcp_drp_module')
        table: Table name (e.g., 'bcp_drp_plans', 'bcp_drp_evaluations')
        row_id: Row ID to analyze
        
    Returns:
        dict: Risk generation response or None if failed
    """
    try:
        # Call the risk generation service directly (no HTTP request)
        from risk_analysis.services import RiskAnalysisService
        
        service = RiskAnalysisService()
        result = service.analyze_entity_data_row(
            entity=entity,
            table=table,
            row_id=row_id
        )
        
        logger.info(f"Generated {len(result.get('risks', []))} risks for {entity} {table} row {row_id}")
        return result
            
    except Exception as e:
        logger.error(f"Error calling risk generation service: {str(e)}")
        return None




# =============================================================================
# PLAN VIEWS
# =============================================================================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def plan_list_view(request):
    """Get all plans with optional filtering - requires ViewPlansAndDocuments permission
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        plan_type = request.GET.get('plan_type', '').strip()
        status_filter = request.GET.get('status', '').strip()
        vendor_filter = request.GET.get('vendor', '').strip()
        scope_filter = request.GET.get('scope', '').strip()
        criticality_filter = request.GET.get('criticality', '').strip()
        
        # Start with all plans
        # MULTI-TENANCY: Filter by tenant
        queryset = Plan.objects.filter(tenant_id=tenant_id)
        
        # Apply filters
        if search_term:
            queryset = queryset.filter(
                Q(plan_name__icontains=search_term) |
                Q(strategy_name__icontains=search_term)
            )
        
        if plan_type and plan_type != 'all':
            queryset = queryset.filter(plan_type=plan_type)
        
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        if vendor_filter and vendor_filter != 'all':
            queryset = queryset.filter(vendor_id=vendor_filter)
        
        if scope_filter and scope_filter != 'all':
            queryset = queryset.filter(plan_scope=scope_filter)
        
        if criticality_filter and criticality_filter != 'all':
            queryset = queryset.filter(criticality=criticality_filter)
        
        # Transform the data
        plans_data = []
        for plan in queryset:
            plan_data = {
                'plan_id': plan.plan_id,
                'vendor_id': plan.vendor_id,
                'strategy_id': plan.strategy_id,
                'strategy_name': plan.strategy_name,
                'plan_type': plan.plan_type,
                'plan_name': plan.plan_name,
                'vendor_name': f"Vendor {plan.vendor_id}",
                'status': plan.status,
                'criticality': plan.criticality,
                'plan_scope': plan.plan_scope,
                'submitted_at': plan.submitted_at
            }
            plans_data.append(plan_data)
        
        logger.info(f"Plan list view returning {len(plans_data)} plans")
        logger.debug(f"Plans data: {plans_data}")
        
        return success_response({
            'plans': plans_data,
            'total_count': len(plans_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching plans: {str(e)}")
        return error_response("Failed to fetch plans", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def strategy_list_view(request):
    """Get all strategies with their associated plans, grouped by strategy - requires ViewPlansAndDocuments permission
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        plan_type = request.GET.get('plan_type', '').strip()
        status_filter = request.GET.get('status', '').strip()
        vendor_filter = request.GET.get('vendor', '').strip()
        scope_filter = request.GET.get('scope', '').strip()
        criticality_filter = request.GET.get('criticality', '').strip()
        
        # Start with all plans
        # MULTI-TENANCY: Filter by tenant
        queryset = Plan.objects.filter(tenant_id=tenant_id)
        
        # Apply filters
        if search_term:
            queryset = queryset.filter(
                Q(plan_name__icontains=search_term) |
                Q(strategy_name__icontains=search_term)
            )
        
        if plan_type and plan_type != 'all':
            queryset = queryset.filter(plan_type=plan_type)
        
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        if vendor_filter and vendor_filter != 'all':
            queryset = queryset.filter(vendor_id=vendor_filter)
        
        if scope_filter and scope_filter != 'all':
            queryset = queryset.filter(plan_scope=scope_filter)
        
        if criticality_filter and criticality_filter != 'all':
            queryset = queryset.filter(criticality=criticality_filter)
        
        # Group plans by strategy
        strategies_dict = {}
        for plan in queryset:
            strategy_key = f"{plan.strategy_id}_{plan.strategy_name}"
            
            if strategy_key not in strategies_dict:
                strategies_dict[strategy_key] = {
                    'strategy_id': plan.strategy_id,
                    'strategy_name': plan.strategy_name,
                    'vendor_id': plan.vendor_id,
                    'vendor_name': f"Vendor {plan.vendor_id}",
                    'plans': [],
                    'plan_count': 0,
                    'bcp_count': 0,
                    'drp_count': 0,
                    'latest_submission': None,
                    'status_summary': {}
                }
            
            # Add plan to strategy
            plan_data = {
                'plan_id': plan.plan_id,
                'plan_name': plan.plan_name,
                'plan_type': plan.plan_type,
                'status': plan.status,
                'criticality': plan.criticality,
                'plan_scope': plan.plan_scope,
                'submitted_at': plan.submitted_at
            }
            
            strategies_dict[strategy_key]['plans'].append(plan_data)
            strategies_dict[strategy_key]['plan_count'] += 1
            
            # Count by type
            if plan.plan_type == 'BCP':
                strategies_dict[strategy_key]['bcp_count'] += 1
            else:
                strategies_dict[strategy_key]['drp_count'] += 1
            
            # Track latest submission
            if not strategies_dict[strategy_key]['latest_submission'] or plan.submitted_at > strategies_dict[strategy_key]['latest_submission']:
                strategies_dict[strategy_key]['latest_submission'] = plan.submitted_at
            
            # Status summary
            status = plan.status
            if status not in strategies_dict[strategy_key]['status_summary']:
                strategies_dict[strategy_key]['status_summary'][status] = 0
            strategies_dict[strategy_key]['status_summary'][status] += 1
        
        # Convert to list and sort by latest submission
        strategies_data = list(strategies_dict.values())
        strategies_data.sort(key=lambda x: x['latest_submission'] or '', reverse=True)
        
        # Calculate overall statistics
        total_strategies = len(strategies_data)
        total_plans = sum(s['plan_count'] for s in strategies_data)
        total_bcp = sum(s['bcp_count'] for s in strategies_data)
        total_drp = sum(s['drp_count'] for s in strategies_data)
        
        return success_response({
            'strategies': strategies_data,
            'summary': {
                'total_strategies': total_strategies,
                'total_plans': total_plans,
                'total_bcp': total_bcp,
                'total_drp': total_drp
            },
            'total_count': total_strategies
        })
        
    except Exception as e:
        logger.error(f"Error fetching strategies: {str(e)}")
        return error_response("Failed to fetch strategies", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_strategy')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def vendor_upload_view(request):
    """Upload vendor documents and create plan records - requires CreateBCPDRPStrategyAndPlans permission
    MULTI-TENANCY: Ensures plans are created with tenant_id
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get the uploaded files and form data
        files = request.FILES
        strategy_name = request.data.get('strategyName', '').strip()
        documents_str = request.data.get('documents', '[]')
        
        logger.info(f"Received upload request - Strategy: {strategy_name}")
        logger.info(f"Files received: {list(files.keys())}")
        logger.info(f"Files details: {[(key, obj.name, obj.size) for key, obj in files.items()]}")
        logger.info(f"Documents string: {documents_str}")
        
        # Debug: Check if files are being received at all
        if not files:
            logger.warning("No files received in request!")
        else:
            logger.info(f"Total files received: {len(files)}")
        
        # Parse the documents JSON string
        try:
            import json
            documents = json.loads(documents_str)
            logger.info(f"Parsed documents: {documents}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error parsing documents JSON: {e}")
            documents = []
        
        # Get data_inventory from request
        data_inventory_str = request.data.get('data_inventory', '{}')
        try:
            data_inventory = json.loads(data_inventory_str) if isinstance(data_inventory_str, str) else data_inventory_str
            if not isinstance(data_inventory, dict):
                data_inventory = {}
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error parsing data_inventory JSON: {e}")
            data_inventory = {}
        
        if not strategy_name:
            return error_response("Strategy name is required", status.HTTP_400_BAD_REQUEST)
        
        if not documents:
            return error_response("At least one document is required", status.HTTP_400_BAD_REQUEST)
        
        # Validate that each document has a plan type
        for doc_data in documents:
            doc_plan_type = doc_data.get('planType', '').strip()
            if not doc_plan_type:
                return error_response("Plan type is required for each document", status.HTTP_400_BAD_REQUEST)
            
            # Check if plan type exists in dropdown table
            # MULTI-TENANCY: Filter by tenant
            if not Dropdown.objects.filter(source='plan_type', value=doc_plan_type, tenant_id=tenant_id).exists():
                # MULTI-TENANCY: Filter by tenant
                valid_types = list(Dropdown.objects.filter(source='plan_type', tenant_id=tenant_id).values_list('value', flat=True))
                return error_response(
                    f"Invalid plan type '{doc_plan_type}' for document '{doc_data.get('planName', 'Unknown')}'. Valid types are: {', '.join(valid_types)}",
                    status.HTTP_400_BAD_REQUEST
                )
        
        # For now, use a default vendor_id (in real app, this would come from authentication)
        vendor_id = 1
        
        # Generate a strategy_id (in real app, this might be managed differently)
        # MULTI-TENANCY: Filter by tenant
        strategy_id = Plan.objects.filter(strategy_name=strategy_name, tenant_id=tenant_id).first()
        if strategy_id:
            strategy_id = strategy_id.strategy_id
        else:
            # Generate new strategy_id based on existing max + 1
            # MULTI-TENANCY: Filter by tenant
            max_strategy = Plan.objects.filter(tenant_id=tenant_id).aggregate(max_id=models.Max('strategy_id'))
            strategy_id = (max_strategy['max_id'] or 0) + 1
        
        created_plans = []
        
        for doc_data in documents:
            # Find the corresponding file by matching the filename
            file_name = doc_data.get('fileName', '')
            uploaded_file = None
            
            # Look for the file in the uploaded files
            # Frontend sends files with key format: file_${fileName}
            file_key = f"file_{file_name}"
            logger.info(f"Looking for file with key: {file_key}, fileName: {file_name}")
            if file_key in files:
                uploaded_file = files[file_key]
                logger.info(f"Found file with key: {file_key}")
            else:
                # Fallback: try to find by original filename
                logger.info(f"File key {file_key} not found, trying fallback search")
                for file_key, file_obj in files.items():
                    if file_obj.name == file_name:
                        uploaded_file = file_obj
                        logger.info(f"Found file with fallback: {file_key}")
                        break
            
            if not uploaded_file:
                logger.warning(f"File not found for document: {file_name}")
                continue
            
            # Validate file type (case-insensitive check)
            allowed_types = [
                'application/pdf', 
                'application/msword', 
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            content_type = uploaded_file.content_type.lower() if uploaded_file.content_type else ''
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            allowed_extensions = ['.pdf', '.doc', '.docx']
            
            # Check both content type and file extension
            is_valid_type = any(allowed.lower() == content_type for allowed in allowed_types)
            is_valid_extension = file_extension in allowed_extensions
            
            if not (is_valid_type or is_valid_extension):
                return error_response(
                    f"Invalid file type for {uploaded_file.name} (type: {uploaded_file.content_type}). Only PDF, DOC, and DOCX files are allowed.", 
                    status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if uploaded_file.size > max_size:
                return error_response(f"File {uploaded_file.name} is too large. Maximum size is 10MB.", status.HTTP_400_BAD_REQUEST)
            
            # Generate file path
            file_extension = os.path.splitext(uploaded_file.name)[1]
            storage_file_name = f"vendor_{vendor_id}_{strategy_id}_{uploaded_file.name}"
            file_path = f"uploads/plans/{storage_file_name}"
            
            # Save file to storage
            saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
            
            # Calculate file hash
            uploaded_file.seek(0)  # Reset file pointer
            file_content = uploaded_file.read()
            sha256_hash = hashlib.sha256(file_content).hexdigest()
            
            # Get next plan_id
            # NOTE: plan_id is PRIMARY KEY and must be unique across ALL tenants, not per-tenant
            max_plan = Plan.objects.aggregate(max_id=models.Max('plan_id'))
            plan_id = (max_plan['max_id'] or 0) + 1
            
            # Get data_inventory from document data or use the one from request
            plan_data_inventory = doc_data.get('data_inventory', data_inventory)
            if not isinstance(plan_data_inventory, dict):
                plan_data_inventory = {}
            # Get plan type from document data (per-document plan type)
            doc_plan_type = doc_data.get('planType', '').strip()
            
            # Create plan record
            # MULTI-TENANCY: Set tenant_id
            plan = Plan.objects.create(
                plan_id=plan_id,
                vendor_id=vendor_id,
                strategy_id=strategy_id,
                strategy_name=strategy_name,
                plan_type=doc_plan_type,
                plan_name=doc_data.get('planName', ''),
                version='1.0',
                file_uri=saved_path,
                mime_type=uploaded_file.content_type,
                sha256_checksum=sha256_hash,
                size_bytes=uploaded_file.size,
                plan_scope=doc_data.get('scope', ''),
                criticality=doc_data.get('criticality', 'MEDIUM'),
                status='SUBMITTED',
                submitted_by=vendor_id,  # In real app, this would be the authenticated user
                data_inventory=plan_data_inventory,
                tenant_id=tenant_id  # MULTI-TENANCY: Set tenant_id
            )
            
            created_plans.append({
                'plan_id': plan.plan_id,
                'plan_name': plan.plan_name,
                'file_name': uploaded_file.name,
                'status': plan.status
            })
        
        return success_response({
            'message': f'Successfully uploaded {len(created_plans)} document(s)',
            'strategy_name': strategy_name,
            'strategy_id': strategy_id,
            'plans': created_plans
        }, status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error uploading vendor documents: {str(e)}")
        logger.error(f"Traceback: {error_details}")
        return error_response(
            f"Failed to upload documents: {str(e)}", 
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================================================================
# DROPDOWN VIEWS
# =============================================================================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def dropdown_list_view(request):
    """Get dropdown values by source
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        source = request.GET.get('source', '').strip()
        
        if not source:
            return error_response("Source parameter is required", status.HTTP_400_BAD_REQUEST)
        
        # Get dropdown values for the specified source
        # MULTI-TENANCY: Filter by tenant
        dropdowns = Dropdown.objects.filter(source=source, tenant_id=tenant_id).order_by('value')
        
        # Transform the data
        dropdown_data = []
        for dropdown in dropdowns:
            dropdown_data.append({
                'id': dropdown.id,
                'source': dropdown.source,
                'value': dropdown.value
            })
        
        return success_response({
            'data': dropdown_data,
            'source': source,
            'total_count': len(dropdown_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching dropdown values: {str(e)}")
        return error_response("Failed to fetch dropdown values", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def plan_types_list_view(request):
    """Get all plan types from dropdown table
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get plan types from dropdown table
        # MULTI-TENANCY: Filter by tenant
        plan_types = Dropdown.objects.filter(source='plan_type', tenant_id=tenant_id).order_by('value')
        
        # Transform the data
        plan_types_data = []
        for plan_type in plan_types:
            plan_types_data.append({
                'id': plan_type.id,
                'value': plan_type.value
            })
        
        return success_response({
            'plan_types': plan_types_data,
            'total_count': len(plan_types_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching plan types: {str(e)}")
        return error_response("Failed to fetch plan types", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_plans')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def plan_type_create_view(request):
    """Create a new plan type in dropdown table
    MULTI-TENANCY: Sets tenant_id on creation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        value = request.data.get('value', '').strip()
        
        if not value:
            return error_response("Plan type value is required", status.HTTP_400_BAD_REQUEST)
        
        # Check if plan type already exists
        # MULTI-TENANCY: Filter by tenant
        if Dropdown.objects.filter(source='plan_type', value=value, tenant_id=tenant_id).exists():
            return error_response(f"Plan type '{value}' already exists", status.HTTP_400_BAD_REQUEST)
        
        # Create new plan type
        # MULTI-TENANCY: Set tenant_id
        dropdown = Dropdown.objects.create(
            source='plan_type',
            value=value,
            tenant_id=tenant_id
        )
        
        return success_response({
            'id': dropdown.id,
            'source': dropdown.source,
            'value': dropdown.value
        }, status_code=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating plan type: {str(e)}")
        return error_response("Failed to create plan type", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_plans')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def plan_type_update_view(request, plan_type_id):
    """Update a plan type in dropdown table
    MULTI-TENANCY: Ensures dropdown belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        value = request.data.get('value', '').strip()
        
        if not value:
            return error_response("Plan type value is required", status.HTTP_400_BAD_REQUEST)
        
        # Get the dropdown entry
        # MULTI-TENANCY: Filter by tenant
        try:
            dropdown = Dropdown.objects.get(id=plan_type_id, source='plan_type', tenant_id=tenant_id)
        except Dropdown.DoesNotExist:
            return not_found_response("Plan type not found")
        
        # Check if new value already exists (excluding current entry)
        # MULTI-TENANCY: Filter by tenant
        if Dropdown.objects.filter(source='plan_type', value=value, tenant_id=tenant_id).exclude(id=plan_type_id).exists():
            return error_response(f"Plan type '{value}' already exists", status.HTTP_400_BAD_REQUEST)
        
        # Update the value
        dropdown.value = value
        dropdown.save()
        
        return success_response({
            'id': dropdown.id,
            'source': dropdown.source,
            'value': dropdown.value
        })
        
    except Exception as e:
        logger.error(f"Error updating plan type: {str(e)}")
        return error_response("Failed to update plan type", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_plans')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def plan_type_delete_view(request, plan_type_id):
    """Delete a plan type from dropdown table
    MULTI-TENANCY: Ensures dropdown belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get the dropdown entry
        # MULTI-TENANCY: Filter by tenant
        try:
            dropdown = Dropdown.objects.get(id=plan_type_id, source='plan_type', tenant_id=tenant_id)
        except Dropdown.DoesNotExist:
            return not_found_response("Plan type not found")
        
        # Check if plan type is being used in any plans
        # MULTI-TENANCY: Filter by tenant
        plan_count = Plan.objects.filter(plan_type=dropdown.value, tenant_id=tenant_id).count()
        if plan_count > 0:
            return error_response(
                f"Cannot delete plan type '{dropdown.value}' because it is used in {plan_count} plan(s)",
                status.HTTP_400_BAD_REQUEST
            )
        
        # Delete the plan type
        value = dropdown.value
        dropdown.delete()
        
        return success_response({
            'message': f"Plan type '{value}' deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting plan type: {str(e)}")
        return error_response("Failed to delete plan type", status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# QUESTIONNAIRE VIEWS
# =============================================================================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_list_view(request):
    """Get all questionnaires with optional filtering - requires ViewAllQuestionnaires permission
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        plan_type = request.GET.get('plan_type', '').strip()
        status_filter = request.GET.get('status', '').strip()
        owner_filter = request.GET.get('owner', '').strip()
        
        # Start with all questionnaires
        # MULTI-TENANCY: Filter by tenant
        queryset = Questionnaire.objects.filter(tenant_id=tenant_id)
        
        # Apply filters
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        
        if plan_type and plan_type != 'ALL':
            queryset = queryset.filter(plan_type=plan_type)
        
        if status_filter and status_filter != 'ALL':
            queryset = queryset.filter(status=status_filter)
        
        if owner_filter and owner_filter != 'ALL':
            if owner_filter == 'ME':
                # In real app, this would filter by current user
                queryset = queryset.filter(created_by_user_id=1)  # Placeholder
            else:
                # Filter by specific owner
                owner_id = owner_filter.replace('Owner ', '')
                try:
                    queryset = queryset.filter(created_by_user_id=int(owner_id))
                except ValueError:
                    pass
        
        # Get all questionnaires (no family grouping needed)
        questionnaires_list = list(queryset)
        
        # Transform the data to match frontend expectations
        questionnaires_data = []
        for questionnaire in questionnaires_list:
            # Get question count
            # MULTI-TENANCY: Filter by tenant
            question_count = Question.objects.filter(questionnaire_id=questionnaire.questionnaire_id, tenant_id=tenant_id).count()
            
            # Get assignment count (placeholder - would need to join with assignments table)
            assignments = 0  # Placeholder
            
            questionnaire_data = {
                'questionnaire_id': questionnaire.questionnaire_id,
                'title': questionnaire.title,
                'version': questionnaire.version,
                'status': questionnaire.status,
                'planType': questionnaire.plan_type,
                'plan_id': questionnaire.plan_id,  # Include plan_id in response
                'owner': f"Owner {questionnaire.created_by_user_id}",
                'questionCount': question_count,
                'tags': _get_questionnaire_tags(questionnaire),
                'assignments': assignments,
                'updated': questionnaire.approved_at.strftime('%Y-%m-%d') if questionnaire.approved_at else 'N/A'
            }
            questionnaires_data.append(questionnaire_data)
        
        # Calculate summary statistics
        total_questionnaires = len(questionnaires_data)
        approved_count = len([q for q in questionnaires_data if q['status'] == 'APPROVED'])
        draft_count = len([q for q in questionnaires_data if q['status'] == 'DRAFT'])
        in_review_count = len([q for q in questionnaires_data if q['status'] == 'IN_REVIEW'])
        archived_count = len([q for q in questionnaires_data if q['status'] == 'ARCHIVED'])
        used_in_assignments = sum(q['assignments'] for q in questionnaires_data)
        reuse_rate = round((used_in_assignments / total_questionnaires * 100) if total_questionnaires > 0 else 0)
        
        response_data = {
            'questionnaires': questionnaires_data,
            'summary': {
                'total_questionnaires': total_questionnaires,
                'approved': approved_count,
                'used_in_assignments': used_in_assignments,
                'drafts': draft_count,
                'in_review': in_review_count,
                'archived': archived_count,
                'reuse_rate': f"{reuse_rate}%"
            },
            'total_count': total_questionnaires
        }
        
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching questionnaires: {str(e)}")
        return error_response("Failed to fetch questionnaires", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('review_answers')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_detail_view(request, questionnaire_id):
    """Get detailed questionnaire information including questions - requires AssignQuestionnairesForReview permission
    MULTI-TENANCY: Ensures questionnaire belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        questionnaire = Questionnaire.objects.get(questionnaire_id=questionnaire_id, tenant_id=tenant_id)
        # MULTI-TENANCY: Filter by tenant
        questions = Question.objects.filter(questionnaire_id=questionnaire_id, tenant_id=tenant_id).order_by('seq_no')
        
        # Serialize questionnaire
        questionnaire_serializer = QuestionnaireDetailSerializer(questionnaire)
        
        # Serialize questions
        questions_data = []
        for question in questions:
            # Parse metadata from question_text if it exists
            question_text_clean = question.question_text
            choice_options = []
            allow_document_upload = False
            
            if '<!--METADATA:' in question.question_text:
                parts = question.question_text.split('<!--METADATA:')
                if len(parts) > 1:
                    question_text_clean = parts[0].strip()
                    metadata_str = parts[1].replace('-->', '').strip()
                    try:
                        metadata = json.loads(metadata_str)
                        choice_options = metadata.get('choice_options', [])
                        allow_document_upload = metadata.get('allow_document_upload', False)
                    except json.JSONDecodeError:
                        pass
            
            question_data = {
                'id': question.seq_no,
                'text': question_text_clean,
                'type': question.answer_type,
                'required': question.is_required,
                'weight': float(question.weight) if question.weight else 1.0,
                'choice_options': choice_options,
                'allow_document_upload': allow_document_upload,
                'tags': _get_question_tags(question)
            }
            questions_data.append(question_data)
        
        return success_response({
            'questionnaire': questionnaire_serializer.data,
            'questions': questions_data
        })
        
    except Questionnaire.DoesNotExist:
        return not_found_response("Questionnaire not found")
    except Exception as e:
        logger.error(f"Error fetching questionnaire details: {str(e)}")
        return error_response("Failed to fetch questionnaire details", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('review_answers')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_review_save_view(request, questionnaire_id):
    """Save reviewer comment for a questionnaire - requires ReviewQuestionnaireAnswers permission
    MULTI-TENANCY: Ensures questionnaire belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get the questionnaire
        # MULTI-TENANCY: Filter by tenant
        questionnaire = Questionnaire.objects.get(questionnaire_id=questionnaire_id, tenant_id=tenant_id)
        
        # Get the reviewer comment from request data
        reviewer_comment = request.data.get('reviewer_comment', '').strip()
        
        if not reviewer_comment:
            return error_response("Reviewer comment is required", status.HTTP_400_BAD_REQUEST)
        
        # Update the questionnaire with the reviewer comment
        questionnaire.reviewer_comment = reviewer_comment
        
        # Update the reviewer_user_id to track who made the review
        reviewer_user_id = request.data.get('reviewer_user_id', 1)
        questionnaire.reviewer_user_id = reviewer_user_id
        
        # Save the questionnaire
        questionnaire.save()
        
        logger.info(f"Successfully saved review comment for questionnaire {questionnaire_id}")
        
        return success_response({
            'message': 'Review comment saved successfully',
            'questionnaire_id': questionnaire_id,
            'reviewer_comment': reviewer_comment
        })
        
    except Questionnaire.DoesNotExist:
        return not_found_response("Questionnaire not found")
    except Exception as e:
        logger.error(f"Error saving review comment for questionnaire {questionnaire_id}: {str(e)}")
        return error_response("Failed to save review comment", status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# OCR VIEWS
# =============================================================================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('ocr_extraction')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def ocr_plans_list_view(request):
    """Get plans that need OCR processing - requires OCRExtractionAndReview permission
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        plan_type = request.GET.get('plan_type', '').strip()
        status_filter = request.GET.get('status', '').strip()
        vendor_filter = request.GET.get('vendor', '').strip()
        strategy_filter = request.GET.get('strategy', '').strip()
        
        # Start with plans that need OCR processing
        # MULTI-TENANCY: Filter by tenant
        queryset = Plan.objects.filter(
            status__in=['SUBMITTED', 'OCR_IN_PROGRESS', 'OCR_COMPLETED'],
            tenant_id=tenant_id
        )
        
        # Apply filters
        if search_term:
            queryset = queryset.filter(
                Q(plan_name__icontains=search_term) |
                Q(strategy_name__icontains=search_term)
            )
        
        if plan_type and plan_type != 'all':
            queryset = queryset.filter(plan_type=plan_type)
        
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        if vendor_filter and vendor_filter != 'all':
            queryset = queryset.filter(vendor_id=vendor_filter)
        
        if strategy_filter:
            queryset = queryset.filter(
                Q(strategy_name__icontains=strategy_filter) |
                Q(strategy_id=strategy_filter)
            )
        
        # Transform the data
        plans_data = []
        for plan in queryset:
            plan_data = {
                'plan_id': plan.plan_id,
                'strategy_id': plan.strategy_id,
                'strategy_name': plan.strategy_name,
                'plan_name': plan.plan_name,
                'plan_type': plan.plan_type,
                'version': plan.version,
                'vendor_id': plan.vendor_id,
                'vendor_name': f"Vendor {plan.vendor_id}",
                'status': plan.status,
                'plan_scope': plan.plan_scope,
                'criticality': plan.criticality,
                'submitted_at': plan.submitted_at
            }
            plans_data.append(plan_data)
        
        return success_response({
            'plans': plans_data,
            'total_count': len(plans_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching OCR plans: {str(e)}")
        return error_response("Failed to fetch plans", status.HTTP_500_INTERNAL_SERVER_ERROR)




# =============================================================================
# MISSING VIEWS - Additional function-based views
# =============================================================================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def comprehensive_plan_detail_view(request, plan_id):
    """
    Get comprehensive plan details including plan info, extracted details, and evaluations
    MULTI-TENANCY: Ensures plan belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get plan basic info
        # MULTI-TENANCY: Filter by tenant
        plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
        
        # Get extracted details from unified ocr_extracted_data field
        extracted_details = None
        if plan.ocr_extracted_data:
            extracted_details = plan.ocr_extracted_data.copy()
            extracted_details['extracted_at'] = plan.ocr_extracted_at.isoformat() if plan.ocr_extracted_at else None
            extracted_details['extractor_version'] = 'AI_LLAMA'
        else:
            extracted_details = None
        
        # Get evaluations for this plan
        # MULTI-TENANCY: Filter by tenant
        evaluations = Evaluation.objects.filter(plan_id=plan_id, tenant_id=tenant_id).order_by('-assigned_at')
        evaluations_data = []
        for evaluation in evaluations:
            evaluation_data = {
                'evaluation_id': evaluation.evaluation_id,
                'assigned_to_user_id': evaluation.assigned_to_user_id,
                'assigned_by_user_id': evaluation.assigned_by_user_id,
                'assigned_at': evaluation.assigned_at.isoformat() if evaluation.assigned_at else None,
                'due_date': evaluation.due_date.isoformat() if evaluation.due_date else None,
                'status': evaluation.status,
                'started_at': evaluation.started_at.isoformat() if evaluation.started_at else None,
                'submitted_at': evaluation.submitted_at.isoformat() if evaluation.submitted_at else None,
                'reviewed_by_user_id': evaluation.reviewed_by_user_id,
                'reviewed_at': evaluation.reviewed_at.isoformat() if evaluation.reviewed_at else None,
                'overall_score': float(evaluation.overall_score) if evaluation.overall_score else None,
                'quality_score': float(evaluation.quality_score) if evaluation.quality_score else None,
                'coverage_score': float(evaluation.coverage_score) if evaluation.coverage_score else None,
                'compliance_score': float(evaluation.compliance_score) if evaluation.compliance_score else None,
                'weighted_score': float(evaluation.weighted_score) if evaluation.weighted_score else None,
                'criteria_json': evaluation.criteria_json,
                'evaluator_comments': evaluation.evaluator_comments
            }
            evaluations_data.append(evaluation_data)
        
        # Combine all data
        comprehensive_data = {
            'plan_info': {
                'plan_id': plan.plan_id,
                'strategy_id': plan.strategy_id,
                'strategy_name': plan.strategy_name,
                'plan_name': plan.plan_name,
                'plan_type': plan.plan_type,
                'version': plan.version,
                'vendor_id': plan.vendor_id,
                'vendor_name': f"Vendor {plan.vendor_id}",
                'status': plan.status,
                'plan_scope': plan.plan_scope,
                'criticality': plan.criticality,
                'submitted_at': plan.submitted_at.isoformat() if plan.submitted_at else None,
                'document_date': plan.document_date.isoformat() if plan.document_date else None,
                'file_uri': plan.file_uri,
                'mime_type': plan.mime_type,
                'sha256_checksum': plan.sha256_checksum,
                'size_bytes': plan.size_bytes,
                'ocr_extracted': plan.ocr_extracted,
                'ocr_by_user_id': plan.ocr_by_user_id,
                'ocr_extracted_at': plan.ocr_extracted_at.isoformat() if plan.ocr_extracted_at else None,
                'approved_by': plan.approved_by,
                'approval_date': plan.approval_date.isoformat() if plan.approval_date else None,
                'rejection_reason': plan.rejection_reason
            },
            'extracted_details': extracted_details,
            'evaluations': evaluations_data,
            'evaluation_count': len(evaluations_data)
        }
        
        logger.info(f"Returning comprehensive plan data for plan {plan_id}")
        return success_response(comprehensive_data)
        
    except Plan.DoesNotExist:
        return not_found_response("Plan not found")
    except Exception as e:
        logger.error(f"Error fetching comprehensive plan details: {str(e)}")
        return error_response("Failed to fetch plan details", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('ocr_extraction')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def ocr_plan_detail_view(request, plan_id):
    """Get detailed plan information for OCR processing - requires OCRExtractionAndReview permission
    MULTI-TENANCY: Ensures plan belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
        
        # Get extracted details from unified ocr_extracted_data field
        extracted_data = {}
        if plan.ocr_extracted_data:
            extracted_data = plan.ocr_extracted_data.copy()
            logger.info(f"Found extracted data for plan {plan_id} in ocr_extracted_data field")
        else:
            logger.warning(f"No extracted data found for plan {plan_id} in ocr_extracted_data field")
        
        plan_data = {
            'plan_id': plan.plan_id,
            'strategy_id': plan.strategy_id,
            'strategy_name': plan.strategy_name,
            'plan_name': plan.plan_name,
            'plan_type': plan.plan_type,
            'version': plan.version,
            'vendor_id': plan.vendor_id,
            'vendor_name': f"Vendor {plan.vendor_id}",
            'status': plan.status,
            'plan_scope': plan.plan_scope,
            'criticality': plan.criticality,
            'submitted_at': plan.submitted_at,
            'file_uri': plan.file_uri,
            'extracted_data': extracted_data
        }
        
        logger.info(f"Returning plan data for plan {plan_id}: extracted_data keys = {list(extracted_data.keys()) if extracted_data else 'None'}")
        return success_response(plan_data)
        
    except Plan.DoesNotExist:
        return not_found_response("Plan not found")
    except Exception as e:
        logger.error(f"Error fetching plan details: {str(e)}")
        return error_response("Failed to fetch plan details", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('ocr_extraction')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def ocr_extraction_save_view(request, plan_id):
    """Save extracted OCR data to ocr_extracted_data field - unified for all plan types
    MULTI-TENANCY: Ensures plan belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
        extracted_data = request.data.get('extracted_data', {})
        
        # Helper function to check if a value is empty/null
        def is_empty_value(val):
            if val is None:
                return True
            if isinstance(val, str) and val.strip() == '':
                return True
            if isinstance(val, list) and len(val) == 0:
                return True
            if isinstance(val, dict) and len(val) == 0:
                return True
            return False
        
        # Prepare unified data structure - include all fields from extracted_data (including custom fields)
        # Only include fields that have non-empty values
        unified_data = {'plan_id': plan_id}
        
        # Process all fields from extracted_data (including custom fields)
        for key, value in extracted_data.items():
            # Skip plan_id as it's already set
            if key == 'plan_id':
                continue
            
            # Only add non-empty values
            if not is_empty_value(value):
                unified_data[key] = value
        
        logger.info(f"[INFO] Saving {len(unified_data) - 1} non-empty fields for plan {plan_id} (including custom fields)")
        
        # Save to ocr_extracted_data field
        plan.ocr_extracted_data = unified_data
        plan.ocr_extracted = True
        if not plan.ocr_extracted_at:
            from django.utils import timezone
            plan.ocr_extracted_at = timezone.now()
        plan.save()
        
        # Generate risks after OCR data is saved (background task)
        task_info = None
        try:
            logger.info(f"Triggering background comprehensive risk generation for OCR completed plan {plan_id}")
            
            # Import the background task
            from risk_analysis.tasks import generate_comprehensive_risks_task
            
            # Start background task - analyze plan with extracted OCR data (no evaluation yet)
            task = generate_comprehensive_risks_task.delay(
                plan_id=plan_id,
                evaluation_id=None  # No evaluation at OCR stage, only plan + extracted details
            )
            
            task_info = {
                'task_id': task.id,
                'status': 'started',
                'message': 'Comprehensive risk generation started in background'
            }
            
            logger.info(f"Started background risk generation task {task.id} for OCR completed plan {plan_id}")
            
        except Exception as task_error:
            logger.warning(f"Background task system not available, will generate risks after response: {task_error}")
            
            # Instead of blocking, we'll generate risks after sending the response
            task_info = {
                'task_id': 'deferred',
                'status': 'deferred',
                'message': 'Risk generation will start after OCR save completes'
            }
        
        response_data = {
            'message': 'Extracted data saved successfully',
            'plan_id': plan_id,
            'plan_type': plan.plan_type
        }
        
        # Include background task info in response
        if task_info:
            response_data['risk_generation'] = task_info
            if task_info['status'] == 'deferred':
                response_data['risk_message'] = "OCR data saved! Comprehensive risk generation will start shortly - check Risk Analytics in a few minutes"
            else:
                response_data['risk_message'] = "Comprehensive risk generation started in background - risks will appear in Risk Analytics shortly"
        else:
            response_data['risk_message'] = "Risk generation task could not be started - check logs"
        
        # Create response first
        response = success_response(response_data, status.HTTP_201_CREATED)
        
        # Start deferred risk generation after response (if needed)
        if task_info and task_info['status'] == 'deferred':
            import threading
            
            def deferred_ocr_risk_generation():
                try:
                    logger.info(f"Starting deferred risk generation for OCR completed plan {plan_id}")
                    # MULTI-TENANCY: Pass tenant_id
                    sync_result = generate_risks_for_plan_evaluation(
                        plan_id=plan_id,
                        evaluation_id=None,  # No evaluation at OCR stage
                        tenant_id=tenant_id
                    )
                    if sync_result:
                        logger.info(f"Deferred OCR risk generation completed: {len(sync_result.get('risks', []))} risks created")
                    else:
                        logger.error("Deferred OCR risk generation failed")
                except Exception as e:
                    logger.error(f"Error in deferred OCR risk generation: {str(e)}")
            
            # Start the risk generation in a separate thread
            thread = threading.Thread(target=deferred_ocr_risk_generation)
            thread.daemon = True  # Thread will die when main process dies
            thread.start()
            logger.info("Started deferred OCR risk generation thread")
        
        return response
        
    except Plan.DoesNotExist:
        return not_found_response("Plan not found")
    except Exception as e:
        logger.error(f"Error saving extracted data: {str(e)}")
        return error_response("Failed to save extracted data", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('ocr_extraction')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def ocr_status_update_view(request, plan_id):
    """Update OCR status of plans - requires OCRExtractionAndReview permission
    MULTI-TENANCY: Ensures plan belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
        new_status = request.data.get('status', '').strip()
        
        valid_statuses = ['OCR_IN_PROGRESS', 'OCR_COMPLETED', 'ASSIGNED_FOR_EVALUATION']
        if new_status not in valid_statuses:
            return error_response(f"Invalid status. Must be one of: {', '.join(valid_statuses)}", status.HTTP_400_BAD_REQUEST)
        
        plan.status = new_status
        if new_status == 'OCR_COMPLETED':
            plan.ocr_extracted = True
            plan.ocr_extracted_at = models.functions.Now()
            plan.ocr_by_user_id = request.data.get('ocr_by_user_id', 1)
        plan.save()
        
        return success_response({
            'message': f'Plan status updated to {new_status}',
            'plan_id': plan_id,
            'new_status': new_status
        })
        
    except Plan.DoesNotExist:
        return not_found_response("Plan not found")
    except Exception as e:
        logger.error(f"Error updating plan status: {str(e)}")
        return error_response("Failed to update plan status", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('assign_evaluation')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def evaluation_list_view(request, plan_id):
    """Get evaluations for a specific plan - requires AssignPlansForEvaluation permission
    MULTI-TENANCY: Ensures plan belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Check if plan exists
        # MULTI-TENANCY: Filter by tenant
        try:
            plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
        except Plan.DoesNotExist:
            return not_found_response("Plan not found")
        
        # Get evaluations for this plan
        # MULTI-TENANCY: Filter by tenant
        evaluations = Evaluation.objects.filter(plan_id=plan_id, tenant_id=tenant_id).order_by('-assigned_at')
        
        # Transform the data
        evaluations_data = []
        for evaluation in evaluations:
            evaluation_data = {
                'evaluation_id': evaluation.evaluation_id,
                'plan_id': evaluation.plan_id,
                'assigned_to_user_id': evaluation.assigned_to_user_id,
                'assigned_by_user_id': evaluation.assigned_by_user_id,
                'assigned_at': evaluation.assigned_at,
                'due_date': evaluation.due_date,
                'status': evaluation.status,
                'started_at': evaluation.started_at,
                'submitted_at': evaluation.submitted_at,
                'reviewed_by_user_id': evaluation.reviewed_by_user_id,
                'reviewed_at': evaluation.reviewed_at,
                'overall_score': float(evaluation.overall_score) if evaluation.overall_score else None,
                'quality_score': float(evaluation.quality_score) if evaluation.quality_score else None,
                'coverage_score': float(evaluation.coverage_score) if evaluation.coverage_score else None,
                'recovery_capability_score': float(evaluation.recovery_capability_score) if evaluation.recovery_capability_score else None,
                'compliance_score': float(evaluation.compliance_score) if evaluation.compliance_score else None,
                'weighted_score': float(evaluation.weighted_score) if evaluation.weighted_score else None,
                'criteria_json': evaluation.criteria_json,
                'evaluator_comments': evaluation.evaluator_comments
            }
            evaluations_data.append(evaluation_data)
        
        return success_response({
            'plan': {
                'plan_id': plan.plan_id,
                'plan_name': plan.plan_name,
                'plan_type': plan.plan_type,
                'strategy_name': plan.strategy_name,
                'vendor_id': plan.vendor_id,
                'status': plan.status,
                'criticality': plan.criticality,
                'submitted_at': plan.submitted_at
            },
            'evaluations': evaluations_data,
            'total_count': len(evaluations_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching evaluations: {str(e)}")
        return error_response("Failed to fetch evaluations", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('assign_evaluation')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def evaluation_save_view(request, plan_id):
    """Save evaluation data for a plan - requires AssignPlansForEvaluation permission
    MULTI-TENANCY: Ensures plan belongs to tenant and sets tenant_id on evaluation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Check if plan exists
        # MULTI-TENANCY: Filter by tenant
        try:
            plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
        except Plan.DoesNotExist:
            return not_found_response("Plan not found")
        
        # Get evaluation data from request
        evaluation_data = request.data
        logger.info(f"Received evaluation data for plan {plan_id}: {evaluation_data}")
        logger.info(f"Score values - overall: {evaluation_data.get('overall_score')}, quality: {evaluation_data.get('quality_score')}, coverage: {evaluation_data.get('coverage_score')}, compliance: {evaluation_data.get('compliance_score')}, weighted: {evaluation_data.get('weighted_score')}")
        
        # Create or update evaluation
        # MULTI-TENANCY: Filter by tenant
        try:
            evaluation = Evaluation.objects.get(plan_id=plan_id, tenant_id=tenant_id)
            created = False
        except Evaluation.DoesNotExist:
            # Get the next evaluation_id manually since auto-increment might not be working
            # Get max_id from ALL evaluations (not filtered by tenant) since evaluation_id is a global primary key
            # Use database transaction to prevent race conditions
            with transaction.atomic():
                # Get the maximum evaluation_id from ALL evaluations to ensure uniqueness
                max_id_result = Evaluation.objects.aggregate(max_id=models.Max('evaluation_id'))
                max_id = max_id_result['max_id']
                next_id = (max_id or 0) + 1
                
                # Check if this ID already exists (race condition protection)
                max_retries = 10
                retry_count = 0
                while Evaluation.objects.filter(evaluation_id=next_id).exists() and retry_count < max_retries:
                    next_id += 1
                    retry_count += 1
                    logger.warning(f"Evaluation ID {next_id - 1} already exists, trying {next_id}")
                
                if retry_count >= max_retries:
                    logger.error(f"Could not find available evaluation_id after {max_retries} retries")
                    return error_response("Failed to generate unique evaluation ID. Please try again.", status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            logger.info(f"Creating new evaluation {next_id} for plan {plan_id} (max_id was {max_id})")
            
            # Convert scores to proper types (handle 0 values correctly)
            overall_score = float(evaluation_data.get('overall_score')) if evaluation_data.get('overall_score') is not None and evaluation_data.get('overall_score') != '' else None
            quality_score = float(evaluation_data.get('quality_score')) if evaluation_data.get('quality_score') is not None and evaluation_data.get('quality_score') != '' else None
            coverage_score = float(evaluation_data.get('coverage_score')) if evaluation_data.get('coverage_score') is not None and evaluation_data.get('coverage_score') != '' else None
            recovery_capability_score = float(evaluation_data.get('recovery_capability_score')) if evaluation_data.get('recovery_capability_score') is not None and evaluation_data.get('recovery_capability_score') != '' else None
            compliance_score = float(evaluation_data.get('compliance_score')) if evaluation_data.get('compliance_score') is not None and evaluation_data.get('compliance_score') != '' else None
            weighted_score = float(evaluation_data.get('weighted_score')) if evaluation_data.get('weighted_score') is not None and evaluation_data.get('weighted_score') != '' else None
            
            # Get data_inventory from evaluation_data
            eval_data_inventory = evaluation_data.get('data_inventory', {})
            if not isinstance(eval_data_inventory, dict):
                eval_data_inventory = {}
            
            # Sanitize criteria_json to ensure it can be serialized
            criteria_json_data = evaluation_data.get('criteria_json', {})
            if not isinstance(criteria_json_data, dict):
                criteria_json_data = {}
            else:
                # Sanitize the criteria_json to remove any non-serializable values
                try:
                    criteria_json_data = sanitize_json_for_db(criteria_json_data)
                    # Verify it can be serialized
                    json.dumps(criteria_json_data)
                except Exception as json_error:
                    logger.warning(f"Error sanitizing criteria_json, using empty dict: {str(json_error)}")
                    criteria_json_data = {}
            
            # Determine initial status based on is_final_submission
            is_final = evaluation_data.get('is_final_submission', False)
            initial_status = 'SUBMITTED' if is_final else 'IN_PROGRESS'
            
            # Get current datetime based on USE_TZ setting
            if settings.USE_TZ:
                current_datetime = timezone.now()
            else:
                from datetime import datetime
                current_datetime = datetime.now()
            
            # MULTI-TENANCY: Set tenant_id
            # Validate and get user IDs
            assigned_to_user_id = evaluation_data.get('assigned_to_user_id')
            if assigned_to_user_id is None:
                # Try to get from request user if available
                if hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
                    assigned_to_user_id = request.user.id
                else:
                    assigned_to_user_id = 1  # Default fallback
            try:
                assigned_to_user_id = int(assigned_to_user_id)
            except (ValueError, TypeError):
                assigned_to_user_id = 1
            
            assigned_by_user_id = evaluation_data.get('assigned_by_user_id')
            if assigned_by_user_id is None:
                # Try to get from request user if available
                if hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
                    assigned_by_user_id = request.user.id
                else:
                    assigned_by_user_id = 1  # Default fallback
            try:
                assigned_by_user_id = int(assigned_by_user_id)
            except (ValueError, TypeError):
                assigned_by_user_id = 1
            
            # Use transaction to ensure atomic creation
            try:
                with transaction.atomic():
                    evaluation = Evaluation.objects.create(
                        evaluation_id=next_id,
                        plan_id=plan_id,
                        assigned_to_user_id=assigned_to_user_id,
                        assigned_by_user_id=assigned_by_user_id,
                        status=initial_status,
                        started_at=current_datetime,
                        submitted_at=current_datetime if is_final else None,
                        tenant_id=tenant_id,  # MULTI-TENANCY: Set tenant_id
                        overall_score=overall_score,
                        quality_score=quality_score,
                        coverage_score=coverage_score,
                        recovery_capability_score=recovery_capability_score,
                        compliance_score=compliance_score,
                        weighted_score=weighted_score,
                        criteria_json=criteria_json_data,
                        evaluator_comments=evaluation_data.get('evaluator_comments', ''),
                        data_inventory=eval_data_inventory
                    )
                created = True
                logger.info(f"Successfully created evaluation {evaluation.evaluation_id} with status {initial_status}")
            except Exception as create_error:
                error_message = str(create_error)
                logger.error(f"Error creating evaluation: {error_message}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                logger.error(f"Evaluation data: plan_id={plan_id}, tenant_id={tenant_id}, next_id={next_id}, started_at={current_datetime}, submitted_at={current_datetime if is_final else None}")
                logger.error(f"criteria_json type: {type(criteria_json_data)}, value: {criteria_json_data}")
                
                # If it's a duplicate key error, try to get the existing evaluation for this plan
                if 'Duplicate entry' in error_message or '1062' in error_message:
                    logger.warning(f"Duplicate key error detected, attempting to retrieve existing evaluation for plan {plan_id}")
                    try:
                        # Double-check if evaluation exists now (might have been created by concurrent request)
                        evaluation = Evaluation.objects.get(plan_id=plan_id, tenant_id=tenant_id)
                        created = False
                        logger.info(f"Found existing evaluation {evaluation.evaluation_id} for plan {plan_id}, will update instead")
                    except Evaluation.DoesNotExist:
                        # If still doesn't exist, it's a real error
                        logger.error(f"Evaluation still doesn't exist after duplicate key error - this is unexpected")
                        return error_response(f"Failed to create evaluation due to ID conflict. Please try again. Error: {error_message}", status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    # For other errors, re-raise
                    raise
            
            # If it's a final submission, update approval status
            if is_final:
                try:
                    # MULTI-TENANCY: Filter by tenant
                    approval = BcpDrpApprovals.objects.filter(
                        object_type='PLAN EVALUATION',
                        object_id=plan_id,
                        status__in=['ASSIGNED', 'IN_PROGRESS'],
                        tenant_id=tenant_id
                    ).first()
                
                    if approval:
                        approval.status = 'COMMENTED'
                        approval.comment_text = evaluation_data.get('evaluator_comments', 'Evaluation submitted')
                        approval.save()
                        logger.info(f"Updated approval {approval.approval_id} status to COMMENTED for plan {plan_id}")
                    else:
                        logger.warning(f"No active approval found for plan {plan_id}")
                except Exception as approval_error:
                    logger.error(f"Error updating approval status for plan {plan_id}: {str(approval_error)}")
        
        if not created:
            # Update existing evaluation
            logger.info(f"Updating existing evaluation {evaluation.evaluation_id} for plan {plan_id}")
            logger.info(f"Current scores before update - overall: {evaluation.overall_score}, quality: {evaluation.quality_score}, coverage: {evaluation.coverage_score}, compliance: {evaluation.compliance_score}, weighted: {evaluation.weighted_score}")
            logger.info(f"Scores in request data - overall: {evaluation_data.get('overall_score')}, quality: {evaluation_data.get('quality_score')}, coverage: {evaluation_data.get('coverage_score')}, compliance: {evaluation_data.get('compliance_score')}, weighted: {evaluation_data.get('weighted_score')}")
            
            # Update scores with proper type conversion (handle 0 values correctly)
            # Note: We need to check if the key exists and the value is not None/empty string
            # But we also need to allow 0 as a valid score value (0 is falsy but valid)
            score_fields = [
                'overall_score', 'quality_score', 'coverage_score', 
                'recovery_capability_score', 'compliance_score', 'weighted_score'
            ]
            
            for score_field in score_fields:
                if score_field in evaluation_data:
                    score_value = evaluation_data[score_field]
                    # Check if value is not None and not empty string
                    # Note: 0 is a valid score, so we check explicitly for None and empty string
                    if score_value is not None and score_value != '':
                        try:
                            float_value = float(score_value)
                            setattr(evaluation, score_field, float_value)
                            logger.info(f"Updated {score_field} to {float_value}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid {score_field} value: {score_value} (type: {type(score_value)}), error: {e}")
                    elif score_value == '' or score_value is None:
                        # Explicitly set to None if empty string or None is provided
                        setattr(evaluation, score_field, None)
                        logger.info(f"Set {score_field} to None (empty value provided)")
            
            # Update other fields
            if 'criteria_json' in evaluation_data:
                criteria_json_data = evaluation_data['criteria_json']
                if not isinstance(criteria_json_data, dict):
                    criteria_json_data = {}
                else:
                    # Sanitize the criteria_json to remove any non-serializable values
                    try:
                        criteria_json_data = sanitize_json_for_db(criteria_json_data)
                        # Verify it can be serialized
                        json.dumps(criteria_json_data)
                    except Exception as json_error:
                        logger.warning(f"Error sanitizing criteria_json, using existing value: {str(json_error)}")
                        # If sanitization fails, try to keep existing value or use empty dict
                        if not hasattr(evaluation, 'criteria_json') or not isinstance(evaluation.criteria_json, dict):
                            criteria_json_data = {}
                        else:
                            criteria_json_data = evaluation.criteria_json
                evaluation.criteria_json = criteria_json_data
            if 'evaluator_comments' in evaluation_data:
                evaluation.evaluator_comments = evaluation_data['evaluator_comments']
            if 'data_inventory' in evaluation_data:
                eval_data_inventory = evaluation_data.get('data_inventory', {})
                if not isinstance(eval_data_inventory, dict):
                    eval_data_inventory = {}
                evaluation.data_inventory = eval_data_inventory
            
            # Update status based on whether it's a draft or final submission
            if evaluation_data.get('is_final_submission', False):
                evaluation.status = 'SUBMITTED'
                # Get current datetime based on USE_TZ setting
                if settings.USE_TZ:
                    evaluation.submitted_at = timezone.now()
                else:
                    from datetime import datetime
                    evaluation.submitted_at = datetime.now()
                logger.info(f"Setting evaluation {evaluation.evaluation_id} status to SUBMITTED")
                
                # Update corresponding approval status to 'COMMENTED'
                try:
                    # MULTI-TENANCY: Filter by tenant
                    approval = BcpDrpApprovals.objects.filter(
                        object_type='PLAN EVALUATION',
                        object_id=plan_id,
                        status__in=['ASSIGNED', 'IN_PROGRESS'],  # Only update if not already commented/completed
                        tenant_id=tenant_id
                    ).first()
                    
                    if approval:
                        approval.status = 'COMMENTED'
                        approval.comment_text = evaluation_data.get('evaluator_comments', 'Evaluation submitted')
                        approval.save()
                        logger.info(f"Updated approval {approval.approval_id} status to COMMENTED for plan {plan_id}")
                    else:
                        logger.warning(f"No active approval found for plan {plan_id}")
                except Exception as approval_error:
                    logger.error(f"Error updating approval status for plan {plan_id}: {str(approval_error)}")
                    # Don't fail the evaluation submission if approval update fails
            else:
                evaluation.status = 'IN_PROGRESS'
                logger.info(f"Setting evaluation {evaluation.evaluation_id} status to IN_PROGRESS")
            
            try:
                evaluation.save()
                logger.info(f"Successfully saved evaluation {evaluation.evaluation_id}")
                logger.info(f"Scores after save - overall: {evaluation.overall_score}, quality: {evaluation.quality_score}, coverage: {evaluation.coverage_score}, compliance: {evaluation.compliance_score}, weighted: {evaluation.weighted_score}")
            except Exception as save_error:
                logger.error(f"Error saving evaluation: {str(save_error)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
        
        response_data = {
            'evaluation_id': evaluation.evaluation_id,
            'plan_id': evaluation.plan_id,
            'status': evaluation.status,
            'message': 'Evaluation saved successfully'
        }
        
        return success_response(response_data)
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"Error saving evaluation: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        logger.error(f"Request data: {request.data}")
        # Include error details in response for debugging (only in DEBUG mode)
        error_message = f"Failed to save evaluation: {str(e)}"
        try:
            if settings.DEBUG:
                error_message = f"{error_message}\n\nTraceback:\n{error_traceback}"
        except:
            pass
        return error_response(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('approve_evaluations')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def plan_decision_view(request, plan_id):
    """Update plan status based on final decision - requires ApproveOrRejectPlanEvaluations permission
    MULTI-TENANCY: Ensures plan belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
        decision = request.data.get('decision', '').strip().upper()
        comment = request.data.get('comment', '').strip()
        
        # Map decisions to status values
        decision_status_map = {
            'APPROVE': 'APPROVED',
            'REJECT': 'REJECTED', 
            'REVISE': 'REVISION_REQUESTED'
        }
        
        if decision not in decision_status_map:
            return error_response(
                f"Invalid decision. Must be one of: {', '.join(decision_status_map.keys())}", 
                status.HTTP_400_BAD_REQUEST
            )
        
        # Validate comment requirement for REJECT/REVISE
        if decision in ['REJECT', 'REVISE'] and not comment:
            return error_response(
                "Comment is required for REJECT and REVISE decisions", 
                status.HTTP_400_BAD_REQUEST
            )
        
        # Update plan status
        new_status = decision_status_map[decision]
        plan.status = new_status
        
        # Set approval/rejection details
        approved_by_user_id = request.data.get('approved_by_user_id', 1)
        if decision == 'APPROVE':
            plan.approved_by = approved_by_user_id
            plan.approval_date = models.functions.Now()
            plan.rejection_reason = None
        elif decision in ['REJECT', 'REVISE']:
            plan.rejection_reason = comment
            plan.approved_by = None
            plan.approval_date = None
        
        plan.save()
        
        response_data = {
            'message': f'Plan {decision}D successfully',
            'plan_id': plan_id,
            'decision': decision,
            'new_status': new_status,
            'comment': comment if comment else None
        }
        
        return success_response(response_data)
        
    except Plan.DoesNotExist:
        return not_found_response("Plan not found")
    except Exception as e:
        logger.error(f"Error making plan decision: {str(e)}")
        return error_response("Failed to make plan decision", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_save_view(request):
    """Save questionnaire and its questions - requires CreateQuestionnaire permission
    MULTI-TENANCY: Ensures questionnaire belongs to tenant and sets tenant_id on creation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get questionnaire data from request
        questionnaire_data = request.data.get('questionnaire', {})
        questions_data = request.data.get('questions', [])
       
        # Validate required fields
        if not questionnaire_data.get('title'):
            return error_response("Questionnaire title is required", status.HTTP_400_BAD_REQUEST)
       
        if not questionnaire_data.get('planType'):
            return error_response("Plan type is required", status.HTTP_400_BAD_REQUEST)
       
        # Check if we're updating an existing questionnaire or creating a new one
        questionnaire_id = questionnaire_data.get('questionnaire_id')
       
        if questionnaire_id:
            # Update existing questionnaire
            # MULTI-TENANCY: Filter by tenant
            try:
                questionnaire = Questionnaire.objects.get(questionnaire_id=questionnaire_id, tenant_id=tenant_id)
                questionnaire.title = questionnaire_data.get('title')
                questionnaire.description = questionnaire_data.get('description', '')
                questionnaire.plan_type = questionnaire_data.get('planType')
                questionnaire.plan_id = questionnaire_data.get('plan_id')
                questionnaire.status = 'DRAFT'  # Keep as draft when updating
                questionnaire.save()
               
                # Delete existing questions for this questionnaire
                # MULTI-TENANCY: Filter by tenant
                Question.objects.filter(questionnaire_id=questionnaire_id, tenant_id=tenant_id).delete()
               
                logger.info(f"Updated existing questionnaire {questionnaire_id}")
            except Questionnaire.DoesNotExist:
                return error_response(f"Questionnaire with ID {questionnaire_id} not found", status.HTTP_404_NOT_FOUND)
        else:
            # Create new questionnaire
            # MULTI-TENANCY: Set tenant_id
            questionnaire = Questionnaire.objects.create(
                title=questionnaire_data.get('title'),
                description=questionnaire_data.get('description', ''),
                plan_type=questionnaire_data.get('planType'),
                plan_id=questionnaire_data.get('plan_id'),  # Save the selected plan ID
                created_by_user_id=questionnaire_data.get('created_by_user_id', 1),
                status='DRAFT',
                tenant_id=tenant_id  # MULTI-TENANCY: Set tenant_id
            )
            logger.info(f"Created new questionnaire {questionnaire.questionnaire_id}")
       
        # Create questions
        created_questions = []
        for index, question_data in enumerate(questions_data, 1):
            # Store additional data in question_text as JSON if needed
            question_text = question_data.get('text', '')
            additional_data = {}
           
            # Store choice options and document upload settings in additional_data
            if question_data.get('choice_options'):
                additional_data['choice_options'] = question_data.get('choice_options', [])
            if question_data.get('allow_document_upload'):
                additional_data['allow_document_upload'] = question_data.get('allow_document_upload', False)
           
            # If we have additional data, append it to question_text as a JSON comment
            if additional_data:
                question_text_with_metadata = f"{question_text}\n<!--METADATA:{json.dumps(additional_data)}-->"
            else:
                question_text_with_metadata = question_text
           
            # MULTI-TENANCY: Set tenant_id
            question = Question.objects.create(
                questionnaire_id=questionnaire.questionnaire_id,
                seq_no=index,
                question_text=question_text_with_metadata,
                answer_type=question_data.get('type', 'TEXT'),
                is_required=question_data.get('required', True),
                weight=question_data.get('weight', 1.0),
                tenant_id=tenant_id  # MULTI-TENANCY: Set tenant_id
            )
            # Parse metadata from question_text if it exists
            question_text_clean = question.question_text
            choice_options = []
            allow_document_upload = False
           
            if '<!--METADATA:' in question.question_text:
                parts = question.question_text.split('<!--METADATA:')
                if len(parts) > 1:
                    question_text_clean = parts[0].strip()
                    metadata_str = parts[1].replace('-->', '').strip()
                    try:
                        metadata = json.loads(metadata_str)
                        choice_options = metadata.get('choice_options', [])
                        allow_document_upload = metadata.get('allow_document_upload', False)
                    except json.JSONDecodeError:
                        pass
           
            created_questions.append({
                'question_id': question.question_id,
                'seq_no': question.seq_no,
                'text': question_text_clean,
                'type': question.answer_type,
                'required': question.is_required,
                'weight': float(question.weight),
                'choice_options': choice_options,
                'allow_document_upload': allow_document_upload
            })
       
        # Determine if it was an update or creation
        http_status = status.HTTP_200_OK if questionnaire_id else status.HTTP_201_CREATED
        message = 'Questionnaire updated successfully' if questionnaire_id else 'Questionnaire saved successfully'
       
        return success_response({
            'questionnaire_id': questionnaire.questionnaire_id,
            'title': questionnaire.title,
            'plan_type': questionnaire.plan_type,
            'plan_id': questionnaire.plan_id,
            'status': questionnaire.status,
            'questions': created_questions,
            'message': message,
            'is_update': bool(questionnaire_id)
        }, http_status)
       
    except Exception as e:
        logger.error(f"Error saving questionnaire: {str(e)}")
        return error_response("Failed to save questionnaire", status.HTTP_500_INTERNAL_SERVER_ERROR)


        
# =============================================================================
# USER MANAGEMENT VIEWS
# =============================================================================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def users_list_view(request):
    """Get all users from Users table for dropdowns
    MULTI-TENANCY: Note - Users table may not have tenant field, filtering by tenant context
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request (for future use if Users table gets tenant field)
        tenant_id = get_tenant_id_from_request(request)
        
        # Get all active users from Users table
        # Note: Users table may not have tenant field yet, so we don't filter by tenant_id
        users = Users.objects.filter(is_active='Y').order_by('user_name')
        
        # Transform the data for dropdown use
        users_data = []
        for user in users:
            users_data.append({
                'user_id': user.user_id,
                'username': user.user_name,
                'display_name': f"{user.user_id} - {user.user_name}"
            })
        
        return success_response({
            'users': users_data,
            'total_count': len(users_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return error_response("Failed to fetch users", status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_questionnaire_tags(questionnaire):
    """Generate tags based on questionnaire properties"""
    tags = []
    if questionnaire.plan_type == 'BCP':
        tags.extend(['BCP', 'Business'])
    else:
        tags.extend(['DRP', 'Disaster'])
    
    if 'failover' in questionnaire.title.lower():
        tags.append('Failover')
    if 'backup' in questionnaire.title.lower():
        tags.append('Backup')
    if 'network' in questionnaire.title.lower():
        tags.append('Network')
    if 'cloud' in questionnaire.title.lower():
        tags.append('Cloud')
    
    return tags[:3]  # Limit to 3 tags


def _get_question_tags(question):
    """Generate tags based on question content"""
    tags = []
    text_lower = question.question_text.lower()
    
    if 'rto' in text_lower:
        tags.append('RTO')
    if 'rpo' in text_lower:
        tags.append('RPO')
    if 'dr' in text_lower or 'disaster' in text_lower:
        tags.append('DR')
    if 'failover' in text_lower:
        tags.append('Failover')
    if 'backup' in text_lower:
        tags.append('Backup')
    if 'network' in text_lower:
        tags.append('Network')
    if 'cloud' in text_lower:
        tags.append('Cloud')
    if 'evidence' in text_lower:
        tags.append('Evidence')
    if 'test' in text_lower:
        tags.append('Testing')
    
    return tags[:2]  # Limit to 2 tags


# =============================================================================
# APPROVAL ASSIGNMENT VIEWS
# =============================================================================

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('assign_evaluation')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_assignment_create_view(request):
    """Create new approval assignment - requires ApprovalAssignment permission
    MULTI-TENANCY: Sets tenant_id on approval creation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get assignment data from request
        data = request.data
        
        # Log received data for debugging
        logger.info(f"Received assignment data: {json.dumps(data, default=str)}")
        logger.info(f"Request data type: {type(data)}, Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        
        # Get no_approval_needed flag
        no_approval_needed = data.get('no_approval_needed', False)
        logger.info(f"no_approval_needed flag: {no_approval_needed}")
        
        # If no approval needed, set assignee to same as assigner
        if no_approval_needed:
            if not data.get('assignee_id') or data.get('assignee_id') != data.get('assigner_id'):
                # Auto-set assignee to assigner when no approval needed
                data['assignee_id'] = data['assigner_id']
                data['assignee_name'] = data.get('assigner_name', '')
                logger.info(f"Auto-setting assignee to assigner ({data['assigner_id']}) for no-approval assignment")
        elif data.get('assigner_id') != data.get('assignee_id'):
            # Only validate if no_approval_needed is False
            pass  # This is fine, different assigner and assignee
        
        # Validate required fields
        required_fields = ['workflow_name', 'plan_type', 'assigner_id', 'assigner_name', 
                          'object_type', 'object_id', 'due_date']
        
        # Only require assignee if no_approval_needed is False
        if not no_approval_needed:
            required_fields.extend(['assignee_id', 'assignee_name'])
        
        # Check each required field and log which ones are missing
        missing_fields = []
        for field in required_fields:
            field_value = data.get(field)
            # Check if field is missing, None, or empty string (but allow 0 and False as valid values)
            if field_value is None or (isinstance(field_value, str) and field_value.strip() == ''):
                missing_fields.append(field)
                logger.warning(f"Missing required field: {field} (value: {field_value}, type: {type(field_value)})")
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join([f.replace('_', ' ').title() for f in missing_fields])}"
            logger.error(f"Validation failed: {error_msg}")
            logger.error(f"Received data: {json.dumps(data, default=str)}")
            return validation_error_response(error_msg)
        
        # Validate user IDs exist
        try:
            # MULTI-TENANCY: Try to filter by tenant if available, but allow without tenant for backward compatibility
            # Users model has a 'tenant' ForeignKey, so use tenant_id (Django auto-created field)
            try:
                if tenant_id:
                    assigner = Users.objects.get(user_id=data['assigner_id'], tenant_id=tenant_id)
                else:
                    assigner = Users.objects.get(user_id=data['assigner_id'])
            except Users.DoesNotExist:
                # Fallback: try without tenant filter
                try:
                    assigner = Users.objects.get(user_id=data['assigner_id'])
                except Users.DoesNotExist:
                    logger.error(f"Assigner user not found - assigner_id: {data.get('assigner_id')}, tenant_id: {tenant_id}")
                    return validation_error_response(f"Invalid assigner user ID: {data.get('assigner_id')}")
            
            # Only validate assignee if provided
            if data.get('assignee_id'):
                try:
                    if tenant_id:
                        assignee = Users.objects.get(user_id=data['assignee_id'], tenant_id=tenant_id)
                    else:
                        assignee = Users.objects.get(user_id=data['assignee_id'])
                except Users.DoesNotExist:
                    # Fallback: try without tenant filter
                    try:
                        assignee = Users.objects.get(user_id=data['assignee_id'])
                    except Users.DoesNotExist:
                        logger.error(f"Assignee user not found - assignee_id: {data.get('assignee_id')}, tenant_id: {tenant_id}")
                        return validation_error_response(f"Invalid assignee user ID: {data.get('assignee_id')}")
        except Exception as user_error:
            logger.error(f"Error validating users: {str(user_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return error_response(f"Error validating users: {str(user_error)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Validate object type
        valid_object_types = ['PLAN EVALUATION', 'NEW QUESTIONNAIRE', 'QUESTIONNAIRE RESPONSE']
        if data['object_type'] not in valid_object_types:
            return validation_error_response(f"Object type must be one of: {', '.join(valid_object_types)}")
        
        # Validate plan type
        # Get valid plan types from dropdown table
        # MULTI-TENANCY: Filter by tenant
        try:
            if tenant_id:
                valid_plan_types = list(Dropdown.objects.filter(source='plan_type', tenant_id=tenant_id).values_list('value', flat=True))
            else:
                # Fallback: get all plan types without tenant filter
                valid_plan_types = list(Dropdown.objects.filter(source='plan_type').values_list('value', flat=True))
            
            if not valid_plan_types:
                logger.warning(f"No plan types found in dropdown for tenant {tenant_id}, allowing any plan type")
                # Don't validate if no plan types found (backward compatibility)
            elif data['plan_type'] not in valid_plan_types:
                return validation_error_response(f"Plan type must be one of: {', '.join(valid_plan_types)}")
        except Exception as plan_type_error:
            logger.warning(f"Error validating plan type: {plan_type_error}, allowing plan type: {data['plan_type']}")
            # Continue with validation if plan type check fails
        
        # Generate workflow_id (simple auto-increment for now)
        # MULTI-TENANCY: Filter by tenant
        try:
            if tenant_id:
                max_workflow_id = BcpDrpApprovals.objects.filter(tenant_id=tenant_id).aggregate(max_id=models.Max('workflow_id'))['max_id']
            else:
                max_workflow_id = BcpDrpApprovals.objects.aggregate(max_id=models.Max('workflow_id'))['max_id']
            next_workflow_id = (max_workflow_id or 0) + 1
        except Exception as workflow_error:
            logger.error(f"Error generating workflow_id: {workflow_error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback: use a simple increment
            next_workflow_id = 1
        
        # Parse and convert due_date to datetime
        # Handle timezone based on USE_TZ setting
        due_date_str = data['due_date']
        try:
            # Parse the datetime string from the frontend (format: "2025-10-02T08:35")
            due_date_naive = datetime.fromisoformat(due_date_str)
            
            # Check if USE_TZ is enabled in settings
            if settings.USE_TZ:
                # Make it timezone-aware if USE_TZ is True
                due_date = timezone.make_aware(due_date_naive)
            else:
                # Keep it naive if USE_TZ is False (MySQL requirement)
                due_date = due_date_naive
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing due_date: {str(e)}, due_date_str: {due_date_str}")
            return validation_error_response(f"Invalid due_date format: {due_date_str}")
        
        # Create approval assignment
        # MULTI-TENANCY: Set tenant_id
        try:
            approval = BcpDrpApprovals.objects.create(
                workflow_id=next_workflow_id,
                workflow_name=data['workflow_name'],
                assigner_id=data['assigner_id'],
                assigner_name=data['assigner_name'],
                assignee_id=data['assignee_id'],
                assignee_name=data['assignee_name'],
                object_type=data['object_type'],
                object_id=data['object_id'],
                plan_type=data['plan_type'],
                due_date=due_date,
                status='ASSIGNED',
                tenant_id=tenant_id  # MULTI-TENANCY: Set tenant_id
            )
            logger.info(f"Successfully created approval assignment {approval.approval_id} for plan {data['object_id']}")
        except Exception as create_error:
            logger.error(f"Error creating approval assignment: {str(create_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Data being saved: workflow_id={next_workflow_id}, workflow_name={data['workflow_name']}, tenant_id={tenant_id}")
            raise  # Re-raise to be caught by outer exception handler
        
        # If no approval needed, auto-approve the object
        if no_approval_needed:
            try:
                auto_approve_object(approval)
            except Exception as e:
                logger.error(f"Error auto-approving object: {str(e)}")
                # Continue even if auto-approval fails
        
        return success_response({
            'approval_id': approval.approval_id,
            'workflow_id': approval.workflow_id,
            'workflow_name': approval.workflow_name,
            'assigner_name': approval.assigner_name,
            'assignee_name': approval.assignee_name,
            'object_type': approval.object_type,
            'object_id': approval.object_id,
            'plan_type': approval.plan_type,
            'status': approval.status,
            'assigned_date': approval.assigned_date.isoformat() if approval.assigned_date else None,
            'due_date': approval.due_date.isoformat() if approval.due_date else None,
            'message': 'Approval assignment created successfully'
        }, status.HTTP_201_CREATED)
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"Error creating approval assignment: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        logger.error(f"Request data: {request.data}")
        # Include error details in response for debugging (only in DEBUG mode)
        error_message = f"Failed to create approval assignment: {str(e)}"
        try:
            from django.conf import settings as django_settings
            if django_settings.DEBUG:
                error_message = f"{error_message}\n\nTraceback:\n{error_traceback}"
        except:
            pass
        return error_response(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)


def auto_approve_object(approval):
    """Auto-approve object when no approval is needed
    MULTI-TENANCY: Ensures objects belong to the same tenant as approval
    """
    from django.utils import timezone
    
    # MULTI-TENANCY: Get tenant_id from approval
    tenant_id = approval.tenant_id if hasattr(approval, 'tenant_id') else None
    
    if approval.object_type == 'PLAN EVALUATION':
        # MULTI-TENANCY: Filter by tenant
        if tenant_id:
            plan = Plan.objects.get(plan_id=approval.object_id, tenant_id=tenant_id)
        else:
            plan = Plan.objects.get(plan_id=approval.object_id)
        plan.status = 'APPROVED'
        plan.approved_by = approval.assignee_id
        plan.approval_date = timezone.now()
        plan.save()
        logger.info(f"Auto-approved plan {approval.object_id} for user {approval.assignee_id}")
        
    elif approval.object_type == 'NEW QUESTIONNAIRE':
        # Do NOT auto-approve questionnaires - they should remain in DRAFT status
        # The "No Approval Needed" flag only affects the approval workflow, not the questionnaire status
        # Questionnaires should be explicitly approved through the approval workflow
        # MULTI-TENANCY: Filter by tenant
        if tenant_id:
            questionnaire = Questionnaire.objects.get(questionnaire_id=approval.object_id, tenant_id=tenant_id)
        else:
            questionnaire = Questionnaire.objects.get(questionnaire_id=approval.object_id)
        # Keep questionnaire status as DRAFT - do not change to APPROVED
        logger.info(f"Skipping auto-approval for questionnaire {approval.object_id} - keeping status as DRAFT")
        
    elif approval.object_type == 'QUESTIONNAIRE RESPONSE':
        # MULTI-TENANCY: Filter by tenant
        if tenant_id:
            assignment = TestAssignmentsResponses.objects.get(
                assignment_response_id=approval.object_id,
                tenant_id=tenant_id
            )
        else:
            assignment = TestAssignmentsResponses.objects.get(
                assignment_response_id=approval.object_id
            )
        assignment.status = 'APPROVED'
        assignment.owner_decision = 'APPROVED'
        assignment.save()
        logger.info(f"Auto-approved assignment response {approval.object_id} for user {approval.assignee_id}")


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_assignments_list_view(request):
    """Get all approval assignments with optional filtering - requires ViewPlansAndDocuments permission
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '').strip()
        plan_type_filter = request.GET.get('plan_type', '').strip()
        object_type_filter = request.GET.get('object_type', '').strip()
        assignee_filter = request.GET.get('assignee', '').strip()
        
        # Start with all approvals
        # MULTI-TENANCY: Filter by tenant
        queryset = BcpDrpApprovals.objects.filter(tenant_id=tenant_id)
        
        # Apply filters
        if search_term:
            queryset = queryset.filter(
                Q(workflow_name__icontains=search_term) |
                Q(assigner_name__icontains=search_term) |
                Q(assignee_name__icontains=search_term)
            )
        
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        if plan_type_filter and plan_type_filter != 'all':
            queryset = queryset.filter(plan_type=plan_type_filter)
        
        if object_type_filter and object_type_filter != 'all':
            queryset = queryset.filter(object_type=object_type_filter)
        
        if assignee_filter and assignee_filter != 'all':
            queryset = queryset.filter(assignee_id=assignee_filter)
        
        # Order by most recent first
        queryset = queryset.order_by('-created_at')
        
        # Transform the data
        approvals_data = []
        for approval in queryset:
            approval_data = {
                'approval_id': approval.approval_id,
                'workflow_id': approval.workflow_id,
                'workflow_name': approval.workflow_name,
                'assigner_id': approval.assigner_id,
                'assigner_name': approval.assigner_name,
                'assignee_id': approval.assignee_id,
                'assignee_name': approval.assignee_name,
                'object_type': approval.object_type,
                'object_id': approval.object_id,
                'plan_type': approval.plan_type,
                'assigned_date': approval.assigned_date.isoformat() if approval.assigned_date else None,
                'due_date': approval.due_date.isoformat() if approval.due_date else None,
                'status': approval.status,
                'comment_text': approval.comment_text,
                'created_at': approval.created_at.isoformat() if approval.created_at else None,
                'updated_at': approval.updated_at.isoformat() if approval.updated_at else None
            }
            approvals_data.append(approval_data)
        
        return success_response({
            'approvals': approvals_data,
            'total_count': len(approvals_data),
            'filters': {
                'search': search_term,
                'status': status_filter,
                'plan_type': plan_type_filter,
                'object_type': object_type_filter,
                'assignee': assignee_filter
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching approval assignments: {str(e)}")
        return error_response("Failed to fetch approval assignments", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('approve_evaluations')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def my_approvals_view(request):
    """Get approvals assigned to a specific user
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get user_id from authenticated user or query parameters
        user_id = request.GET.get('user_id')
        
        # If no user_id provided, use the authenticated user's ID
        if not user_id:
            if hasattr(request.user, 'userid'):
                user_id = request.user.userid
            elif hasattr(request.user, 'id'):
                user_id = request.user.id
            else:
                return error_response("Unable to determine user_id", status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"[BCP My Approvals] Fetching approvals for user_id: {user_id}")
        
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '').strip()
        plan_type_filter = request.GET.get('plan_type', '').strip()
        object_type_filter = request.GET.get('object_type', '').strip()
        
        # Filter approvals by user's assignee_id
        # MULTI-TENANCY: Filter by tenant
        queryset = BcpDrpApprovals.objects.filter(assignee_id=user_id, tenant_id=tenant_id)
        
        # Apply additional filters
        if search_term:
            queryset = queryset.filter(
                Q(workflow_name__icontains=search_term) |
                Q(assigner_name__icontains=search_term) |
                Q(comment_text__icontains=search_term)
            )
        
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        if plan_type_filter and plan_type_filter != 'all':
            queryset = queryset.filter(plan_type=plan_type_filter)
        
        if object_type_filter and object_type_filter != 'all':
            queryset = queryset.filter(object_type=object_type_filter)
        
        # Order by most recent first
        queryset = queryset.order_by('-assigned_date')
        
        # Transform the data
        approvals_data = []
        for approval in queryset:
            # Calculate days until due date
            days_until_due = None
            is_overdue = False
            if approval.due_date:
                due_date = approval.due_date.date() if hasattr(approval.due_date, 'date') else approval.due_date
                today = timezone.now().date()
                days_until_due = (due_date - today).days
                is_overdue = days_until_due < 0
            
            approval_data = {
                'approval_id': approval.approval_id,
                'workflow_id': approval.workflow_id,
                'workflow_name': approval.workflow_name,
                'assigner_id': approval.assigner_id,
                'assigner_name': approval.assigner_name,
                'assignee_id': approval.assignee_id,
                'assignee_name': approval.assignee_name,
                'object_type': approval.object_type,
                'object_id': approval.object_id,
                'plan_type': approval.plan_type,
                'assigned_date': approval.assigned_date.isoformat() if approval.assigned_date else None,
                'due_date': approval.due_date.isoformat() if approval.due_date else None,
                'status': approval.status,
                'comment_text': approval.comment_text,
                'created_at': approval.created_at.isoformat() if approval.created_at else None,
                'updated_at': approval.updated_at.isoformat() if approval.updated_at else None,
                'days_until_due': days_until_due,
                'is_overdue': is_overdue
            }
            approvals_data.append(approval_data)
        
        return success_response({
            'approvals': approvals_data,
            'total_count': len(approvals_data),
            'user_id': user_id,
            'filters': {
                'search': search_term,
                'status': status_filter,
                'plan_type': plan_type_filter,
                'object_type': object_type_filter
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching user approvals: {str(e)}")
        return error_response("Failed to fetch user approvals", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('approve_evaluations')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_status_update_view(request, approval_id):
    """Update approval status and handle related object status changes
    MULTI-TENANCY: Ensures approval belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get approval record
        # MULTI-TENANCY: Filter by tenant
        try:
            approval = BcpDrpApprovals.objects.get(approval_id=approval_id, tenant_id=tenant_id)
        except BcpDrpApprovals.DoesNotExist:
            return not_found_response("Approval not found")
        
        # Get new status from request
        new_status = request.data.get('status', '').strip().upper()
        comment_text = request.data.get('comment_text', '').strip()
        
        # Validate status
        valid_statuses = ['ASSIGNED', 'IN_PROGRESS', 'COMMENTED', 'SKIPPED', 'EXPIRED', 'CANCELLED']
        if new_status not in valid_statuses:
            return error_response(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}", 
                status.HTTP_400_BAD_REQUEST
            )
        
        # Update approval status
        old_status = approval.status
        approval.status = new_status
        
        # Update comment if provided
        if comment_text:
            approval.comment_text = comment_text
        
        approval.save()
        logger.info(f"Updated approval {approval_id} status from {old_status} to {new_status}")
        
        # Handle related object status changes based on object_type
        if approval.object_type == 'NEW QUESTIONNAIRE':
            try:
                # MULTI-TENANCY: Filter by tenant
                questionnaire = Questionnaire.objects.get(questionnaire_id=approval.object_id, tenant_id=tenant_id)
                
                if new_status == 'IN_PROGRESS' and old_status == 'ASSIGNED':
                    # When assignee starts working, change questionnaire status to IN_REVIEW
                    questionnaire.status = 'IN_REVIEW'
                    questionnaire.save()
                    logger.info(f"Updated questionnaire {approval.object_id} status to IN_REVIEW when approval status changed to IN_PROGRESS")
                
                elif new_status == 'COMMENTED':
                    # When assignee completes review with comment, change questionnaire status to APPROVED
                    questionnaire.status = 'APPROVED'
                    questionnaire.approved_by_user_id = approval.assignee_id
                    questionnaire.approved_at = timezone.now()
                    questionnaire.reviewer_user_id = approval.assignee_id
                    questionnaire.reviewer_comment = comment_text or 'Questionnaire reviewed and approved'
                    questionnaire.save()
                    logger.info(f"Updated questionnaire {approval.object_id} status to APPROVED when approval status changed to COMMENTED")
                    
            except Questionnaire.DoesNotExist:
                logger.warning(f"Questionnaire {approval.object_id} not found when updating approval status")
        
        return success_response({
            'message': 'Approval status updated successfully',
            'approval_id': approval_id,
            'old_status': old_status,
            'new_status': new_status,
            'object_type': approval.object_type,
            'object_id': approval.object_id
        })
        
    except Exception as e:
        logger.error(f"Error updating approval status: {str(e)}")
        return error_response("Failed to update approval status", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('review_answers')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_assignments_list_view(request):
    """
    Fetch questionnaire assignments from test_assignments_responses table
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '').strip()
        plan_id_filter = request.GET.get('plan_id', '').strip()
        user_id_filter = request.GET.get('user_id', '').strip()
        
        # Start with all assignments
        # MULTI-TENANCY: Filter by tenant
        queryset = TestAssignmentsResponses.objects.select_related().filter(tenant_id=tenant_id)
        
        # Apply filters
        if search_term:
            queryset = queryset.filter(
                Q(plan_id__icontains=search_term) |
                Q(questionnaire_id__icontains=search_term)
            )
        
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        if plan_id_filter:
            queryset = queryset.filter(plan_id=plan_id_filter)
        
        if user_id_filter:
            queryset = queryset.filter(assigned_to_user_id=user_id_filter)
        
        # Order by most recent first
        queryset = queryset.order_by('-assigned_at')
        
        # Import decrypt function for question_text decryption
        from tprm_backend.utils.data_encryption import decrypt_data
        
        # Transform the data
        assignments_data = []
        for assignment in queryset:
            # Parse the answer_text JSON to get question count and metadata
            # Use answer_text_plain to get decrypted JSON (answer_text field is encrypted)
            questions_data = {}
            total_questions = 0
            decrypted_answer_text = None
            
            try:
                # Get decrypted answer_text using _plain property
                answer_text_value = getattr(assignment, 'answer_text_plain', None) or assignment.answer_text
                
                if answer_text_value:
                    answer_data = json.loads(answer_text_value)
                    raw_questions_data = answer_data.get('questions_data', [])
                    total_questions = answer_data.get('assignment_metadata', {}).get('total_questions', 0)
                    
                    # Decrypt question_text values inside the JSON
                    # Questions were encrypted when stored from the Question model
                    if isinstance(raw_questions_data, list):
                        questions_data = []
                        for question in raw_questions_data:
                            decrypted_question = question.copy()
                            # Decrypt question_text if it's encrypted
                            if 'question_text' in decrypted_question and decrypted_question['question_text']:
                                try:
                                    # Try to decrypt - if it fails, use original value
                                    decrypted_text = decrypt_data(decrypted_question['question_text'])
                                    decrypted_question['question_text'] = decrypted_text
                                except Exception as decrypt_error:
                                    # If decryption fails, use original (might already be decrypted)
                                    logger.debug(f"Could not decrypt question_text for question {decrypted_question.get('question_id')}: {decrypt_error}")
                            questions_data.append(decrypted_question)
                    elif isinstance(raw_questions_data, dict):
                        # Handle dict format
                        questions_data = {}
                        for key, question in raw_questions_data.items():
                            decrypted_question = question.copy() if isinstance(question, dict) else question
                            if isinstance(question, dict) and 'question_text' in decrypted_question and decrypted_question['question_text']:
                                try:
                                    decrypted_text = decrypt_data(decrypted_question['question_text'])
                                    decrypted_question['question_text'] = decrypted_text
                                except Exception as decrypt_error:
                                    logger.debug(f"Could not decrypt question_text for question {key}: {decrypt_error}")
                            questions_data[key] = decrypted_question
                    
                    # Store decrypted answer_text for response
                    answer_data['questions_data'] = questions_data
                    decrypted_answer_text = json.dumps(answer_data)
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Error parsing answer_text for assignment {assignment.assignment_response_id}: {e}")
                questions_data = {}
                total_questions = 0
                decrypted_answer_text = assignment.answer_text
            
            # Get decrypted owner_comment using _plain property
            owner_comment_decrypted = getattr(assignment, 'owner_comment_plain', None) or assignment.owner_comment
            reason_comment_decrypted = getattr(assignment, 'reason_comment_plain', None) or assignment.reason_comment
            
            assignment_data = {
                'assignment_response_id': assignment.assignment_response_id,
                'plan_id': assignment.plan_id,
                'questionnaire_id': assignment.questionnaire_id,
                'question_id': assignment.question_id,
                'assigned_to_user_id': assignment.assigned_to_user_id,
                'assigned_by_user_id': assignment.assigned_by_user_id,
                'assigned_at': assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                'status': assignment.status,
                'started_at': assignment.started_at.isoformat() if assignment.started_at else None,
                'submitted_at': assignment.submitted_at.isoformat() if assignment.submitted_at else None,
                'owner_decision': assignment.owner_decision,
                'owner_comment': owner_comment_decrypted,  # Use decrypted value
                'response_status': assignment.response_status,
                'answer_text': decrypted_answer_text,  # Use decrypted JSON
                'reason_comment': reason_comment_decrypted,  # Use decrypted value
                'evidence_uri': assignment.evidence_uri,
                'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
                'updated_at': assignment.updated_at.isoformat() if assignment.updated_at else None,
                'total_questions': total_questions,
                'questions_data': questions_data  # Contains decrypted question_text values
            }
            assignments_data.append(assignment_data)
        
        return success_response({
            'assignments': assignments_data,
            'total_count': len(assignments_data),
            'filters': {
                'search': search_term,
                'status': status_filter,
                'plan_id': plan_id_filter,
                'user_id': user_id_filter
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching questionnaire assignments: {str(e)}")
        return error_response("Failed to fetch questionnaire assignments", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('review_answers')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_assignment_save_answers_view(request, assignment_id):
    """
    Save answers for a questionnaire assignment to test_assignments_responses table
    MULTI-TENANCY: Ensures assignment belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get assignment data from request
        data = json.loads(request.body)
        logger.info(f"Saving answers for assignment {assignment_id}: {data}")
        
        # Validate required fields
        if 'answers' not in data:
            return error_response("Missing required field: answers", status.HTTP_400_BAD_REQUEST)
        
        # Handle reviewer comment
        reviewer_comment = data.get('reviewer_comment', '')
        
        # Get the assignment record
        # MULTI-TENANCY: Filter by tenant
        try:
            assignment = TestAssignmentsResponses.objects.get(assignment_response_id=assignment_id, tenant_id=tenant_id)
        except TestAssignmentsResponses.DoesNotExist:
            return error_response("Assignment not found", status.HTTP_404_NOT_FOUND)
        
        # Parse existing answer_text if it exists
        # Use answer_text_plain to get decrypted JSON (answer_text field is encrypted)
        existing_data = {}
        answer_text_value = getattr(assignment, 'answer_text_plain', None) or assignment.answer_text
        if answer_text_value:
            try:
                existing_data = json.loads(answer_text_value)
                logger.info(f"Parsed existing data structure: {type(existing_data.get('questions_data', {}))}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse existing answer_text: {e}")
                existing_data = {}
        
        # Update the answers in the existing data structure
        if 'questions_data' not in existing_data:
            existing_data['questions_data'] = {}
        
        # Ensure questions_data is a dictionary
        if not isinstance(existing_data['questions_data'], dict):
            logger.warning(f"questions_data is not a dict, converting from {type(existing_data['questions_data'])}")
            if isinstance(existing_data['questions_data'], list):
                # Convert list to dict using question_id as key
                questions_dict = {}
                for q in existing_data['questions_data']:
                    if isinstance(q, dict) and 'question_id' in q:
                        questions_dict[str(q['question_id'])] = q
                existing_data['questions_data'] = questions_dict
            else:
                existing_data['questions_data'] = {}
        
        # Update answers for each question
        answers_data = data['answers']
        logger.info(f"Updating answers for {len(answers_data)} questions")
        
        for question_id, answer_data in answers_data.items():
            question_key = str(question_id)
            if question_key in existing_data['questions_data']:
                existing_data['questions_data'][question_key].update({
                    'answer': answer_data.get('answer', ''),
                    'reason': answer_data.get('reason', ''),
                    'answered_at': timezone.now().isoformat(),
                    'evidence_documents': answer_data.get('evidence_documents', [])
                })
                logger.info(f"Updated answer for question {question_key}")
            else:
                # Create question data if it doesn't exist
                logger.warning(f"Question {question_key} not found in existing questions_data, creating new entry")
                existing_data['questions_data'][question_key] = {
                    'question_text': f'Question {question_key}',
                    'question_type': 'TEXT',
                    'answer': answer_data.get('answer', ''),
                    'reason': answer_data.get('reason', ''),
                    'answered_at': timezone.now().isoformat(),
                    'evidence_documents': answer_data.get('evidence_documents', [])
                }
        
        # Update assignment metadata
        if 'assignment_metadata' not in existing_data:
            existing_data['assignment_metadata'] = {}
        
        # Calculate total answered questions safely
        total_answered = 0
        if 'questions_data' in existing_data:
            questions_data = existing_data['questions_data']
            if isinstance(questions_data, dict):
                total_answered = len([q for q in questions_data.values() if q.get('answer') and str(q.get('answer', '')).strip()])
            elif isinstance(questions_data, list):
                total_answered = len([q for q in questions_data if q.get('answer') and str(q.get('answer', '')).strip()])
        
        existing_data['assignment_metadata'].update({
            'last_answered_at': timezone.now().isoformat(),
            'total_answered': total_answered
        })
        
        # Save the updated data
        assignment.answer_text = json.dumps(existing_data)
        assignment.status = 'IN_PROGRESS'
        
        # Save reviewer comment to owner_comment field
        assignment.owner_comment = reviewer_comment
        
        # If this is a final submission
        if data.get('is_final_submission', False):
            assignment.status = 'SUBMITTED'
            assignment.submitted_at = timezone.now()
            assignment.response_status = 'SUBMITTED'
            
            # Check if there's a corresponding approval record with no_approval_needed
            # and auto-approve the assignment if so
            try:
                # MULTI-TENANCY: Filter by tenant
                approval_record = BcpDrpApprovals.objects.filter(
                    object_type='QUESTIONNAIRE RESPONSE',
                    object_id=assignment_id,
                    status__in=['ASSIGNED', 'IN_PROGRESS'],  # Check both ASSIGNED and IN_PROGRESS
                    tenant_id=tenant_id
                ).first()
                
                if approval_record:
                    # Check if this approval was created with no_approval_needed flag
                    # We can determine this by checking if assigner_id == assignee_id
                    if approval_record.assigner_id == approval_record.assignee_id:
                        # Auto-approve the assignment
                        assignment.status = 'APPROVED'
                        assignment.owner_decision = 'APPROVED'
                        assignment.approved_at = timezone.now()
                        
                        # Also update the approval record status
                        approval_record.status = 'APPROVED'
                        approval_record.approved_at = timezone.now()
                        approval_record.save()
                        
                        logger.info(f"Auto-approved assignment response {assignment_id} due to no approval needed")
                    else:
                        # Update approval status to COMMENTED for normal submissions
                        approval_record.status = 'COMMENTED'
                        approval_record.comment_text = reviewer_comment or 'Questionnaire response submitted'
                        approval_record.save()
                        logger.info(f"Updated approval {approval_record.approval_id} status to COMMENTED for assignment {assignment_id}")
                else:
                    logger.info(f"No active approval record found for assignment {assignment_id}")
                    
            except Exception as e:
                logger.error(f"Error updating approval status for assignment {assignment_id}: {str(e)}")
                # Continue with normal submission even if approval update fails
        
        assignment.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Answers saved successfully for assignment {assignment_id}',
            'data': {
                'assignment_id': assignment_id,
                'status': assignment.status,
                'submitted_at': assignment.submitted_at.isoformat() if assignment.submitted_at else None,
                'total_answered': existing_data['assignment_metadata'].get('total_answered', 0)
            }
        })
        
    except json.JSONDecodeError:
        return error_response("Invalid JSON data", status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error saving assignment answers: {str(e)}")
        return error_response("Failed to save answers", status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_assignment_create_view(request):
    """Create new questionnaire assignment - saves to test_assignments_responses table
    MULTI-TENANCY: Sets tenant_id on assignment creation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        logger.info("Creating questionnaire assignment")
        
        # Get assignment data from request
        data = json.loads(request.body)
        logger.info(f"Assignment data: {data}")
        
        # Validate required fields
        required_fields = ['plan_id', 'questionnaire_id', 'assigned_to_user_id', 'due_date']
        for field in required_fields:
            if field not in data:
                return error_response(f"Missing required field: {field}", status.HTTP_400_BAD_REQUEST)
        
        # Get the assigner user ID from request data or use default
        assigned_by_user_id = data.get('assigned_by_user_id', 1)
        
        # Verify plan and questionnaire belong to tenant
        # MULTI-TENANCY: Filter by tenant
        try:
            plan = Plan.objects.get(plan_id=data['plan_id'], tenant_id=tenant_id)
        except Plan.DoesNotExist:
            return error_response("Plan not found or does not belong to tenant", status.HTTP_404_NOT_FOUND)
        
        try:
            questionnaire = Questionnaire.objects.get(questionnaire_id=data['questionnaire_id'], tenant_id=tenant_id)
        except Questionnaire.DoesNotExist:
            return error_response("Questionnaire not found or does not belong to tenant", status.HTTP_404_NOT_FOUND)
        
        # Get all questions for the questionnaire to create a single assignment record with JSON data
        # Use tprm database connection to access test_questions table (in tprm_integration database)
        # The test_questions table is in tprm_integration database, not grc2
        # MULTI-TENANCY: Filter by tenant in SQL query
        from django.db import connections
        from django.conf import settings
        
        # Use 'tprm' connection for test_questions table (in tprm_integration database)
        # Fall back to 'default' if 'tprm' connection is not available
        db_connection = 'tprm'
        try:
            # Check if 'tprm' connection exists in settings
            if 'tprm' not in settings.DATABASES:
                logger.warning("'tprm' database connection not found in settings, falling back to 'default'")
                db_connection = 'default'
            else:
                logger.info(f"Using 'tprm' database connection for test_questions table (tprm_integration)")
        except Exception as db_check_error:
            logger.warning(f"Error checking database connections: {db_check_error}, using 'tprm' connection")
        
        # Query test_questions table - try tprm connection first, fallback to default
        questions = None
        try:
            with connections[db_connection].cursor() as cursor:
                cursor.execute("""
                    SELECT q.question_id, q.question_text, q.answer_type, q.is_required
                    FROM test_questions q
                    INNER JOIN test_questionnaires tq ON q.questionnaire_id = tq.questionnaire_id
                    WHERE q.questionnaire_id = %s 
                    AND tq.TenantId = %s
                    ORDER BY q.seq_no, q.question_id
                """, [data['questionnaire_id'], tenant_id])
                
                questions = cursor.fetchall()
        except Exception as db_error:
            # If tprm connection fails, try default connection as fallback
            if db_connection == 'tprm':
                logger.warning(f"Failed to query test_questions using 'tprm' connection: {db_error}, trying 'default' connection")
                db_connection = 'default'
                try:
                    with connections[db_connection].cursor() as cursor:
                        cursor.execute("""
                            SELECT q.question_id, q.question_text, q.answer_type, q.is_required
                            FROM test_questions q
                            INNER JOIN test_questionnaires tq ON q.questionnaire_id = tq.questionnaire_id
                            WHERE q.questionnaire_id = %s 
                            AND tq.TenantId = %s
                            ORDER BY q.seq_no, q.question_id
                        """, [data['questionnaire_id'], tenant_id])
                        
                        questions = cursor.fetchall()
                except Exception as fallback_error:
                    # Re-raise the error if default connection also fails
                    logger.error(f"Failed to query test_questions with both connections: {fallback_error}")
                    raise
            else:
                # Re-raise the error if default connection also fails
                logger.error(f"Failed to query test_questions: {db_error}")
                raise
        
        # Validate that questions were found
        if not questions:
            return error_response("No questions found for this questionnaire", status.HTTP_400_BAD_REQUEST)
        
        # Import decrypt function for question_text decryption
        from tprm_backend.utils.data_encryption import decrypt_data
        
        # Prepare questions data as JSON
        questions_data = []
        question_ids = []
        
        for question_row in questions:
            question_id, question_text, answer_type, is_required = question_row
            question_ids.append(question_id)
            
            # Decrypt question_text (it's encrypted in the database)
            try:
                decrypted_question_text = decrypt_data(question_text)
            except Exception as decrypt_error:
                # If decryption fails, use original (might already be decrypted or not encrypted)
                logger.debug(f"Could not decrypt question_text for question {question_id}: {decrypt_error}")
                decrypted_question_text = question_text
            
            # Parse metadata from question_text if it exists
            question_text_clean = decrypted_question_text
            choice_options = []
            allow_document_upload = False
            
            if '<!--METADATA:' in decrypted_question_text:
                parts = decrypted_question_text.split('<!--METADATA:')
                if len(parts) > 1:
                    question_text_clean = parts[0].strip()
                    metadata_str = parts[1].replace('-->', '').strip()
                    try:
                        metadata = json.loads(metadata_str)
                        choice_options = metadata.get('choice_options', [])
                        allow_document_upload = metadata.get('allow_document_upload', False)
                    except json.JSONDecodeError:
                        pass
            
            questions_data.append({
                'question_id': question_id,
                'question_text': question_text_clean,
                'answer_type': answer_type,
                'is_required': bool(is_required),
                'choice_options': choice_options,
                'allow_document_upload': allow_document_upload,
                'answer': None,  # Will be filled when user responds
                'status': 'PENDING'
            })
        
        # Create a single assignment record with all questions as JSON
        # MULTI-TENANCY: Set tenant_id
        assignment = TestAssignmentsResponses.objects.create(
            plan_id=data['plan_id'],
            questionnaire_id=data['questionnaire_id'],
            question_id=question_ids[0] if question_ids else None,  # Store first question_id for compatibility
            assigned_to_user_id=data['assigned_to_user_id'],
            assigned_by_user_id=assigned_by_user_id,
            due_date=data['due_date'],
            status='ASSIGNED',
            response_status='IN_PROGRESS',
            answer_text=json.dumps({
                'question_ids': question_ids,
                'questions_data': questions_data,
                'assignment_metadata': {
                    'total_questions': len(questions_data),
                    'assigned_at': timezone.now().isoformat(),
                    'questionnaire_version': 'current'
                }
            }),
            tenant_id=tenant_id  # MULTI-TENANCY: Set tenant_id
        )
        
        assignment_id = assignment.assignment_response_id
        logger.info(f"Created single assignment record {assignment_id} with {len(question_ids)} questions as JSON")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Questionnaire assignment created successfully for {len(question_ids)} questions',
            'data': {
                'assignment_id': assignment_id,
                'questionnaire_id': data['questionnaire_id'],
                'plan_id': data['plan_id'],
                'assigned_to_user_id': data['assigned_to_user_id'],
                'question_count': len(question_ids),
                'question_ids': question_ids
            }
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in questionnaire assignment: {str(e)}")
        return error_response("Invalid JSON data", status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating questionnaire assignment: {str(e)}", exc_info=True)
        return error_response(f"Failed to create questionnaire assignment: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# APPROVE/REJECT ENDPOINTS
# =============================================================================

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def plan_approve_view(request, plan_id):
    """Approve a plan - updates status to APPROVED
    MULTI-TENANCY: Ensures plan belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
        
        # Update plan status
        plan.status = 'APPROVED'
        plan.approved_by = request.data.get('approved_by', 1)  # Default to user 1 if not provided
        plan.approval_date = models.functions.Now()
        plan.rejection_reason = None
        plan.save()
        
        return success_response({
            'message': 'Plan approved successfully',
            'plan_id': plan_id,
            'new_status': 'APPROVED'
        })
        
    except Plan.DoesNotExist:
        return not_found_response("Plan not found")
    except Exception as e:
        logger.error(f"Error approving plan: {str(e)}")
        return error_response("Failed to approve plan", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def plan_reject_view(request, plan_id):
    """Reject a plan - updates status to REJECTED
    MULTI-TENANCY: Ensures plan belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
        
        # Update plan status
        plan.status = 'REJECTED'
        plan.approved_by = None
        plan.approval_date = None
        plan.rejection_reason = request.data.get('rejection_reason', 'No reason provided')
        plan.save()
        
        return success_response({
            'message': 'Plan rejected successfully',
            'plan_id': plan_id,
            'new_status': 'REJECTED',
            'rejection_reason': plan.rejection_reason
        })
        
    except Plan.DoesNotExist:
        return not_found_response("Plan not found")
    except Exception as e:
        logger.error(f"Error rejecting plan: {str(e)}")
        return error_response("Failed to reject plan", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_approve_view(request, questionnaire_id):
    """Approve a questionnaire - updates status to APPROVED
    MULTI-TENANCY: Ensures questionnaire belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        questionnaire = Questionnaire.objects.get(questionnaire_id=questionnaire_id, tenant_id=tenant_id)
        
        # Update questionnaire status
        questionnaire.status = 'APPROVED'
        questionnaire.approved_by_user_id = request.data.get('approved_by', 1)  # Default to user 1 if not provided
        questionnaire.approved_at = models.functions.Now()
        questionnaire.save()
        
        # Update corresponding approval status to 'COMMENTED'
        try:
            # MULTI-TENANCY: Filter by tenant
            approval = BcpDrpApprovals.objects.filter(
                object_type='NEW QUESTIONNAIRE',
                object_id=questionnaire_id,
                status__in=['ASSIGNED', 'IN_PROGRESS'],  # Only update if not already commented/completed
                tenant_id=tenant_id
            ).first()
            
            if approval:
                approval.status = 'COMMENTED'
                approval.comment_text = request.data.get('comment', 'Questionnaire approved')
                approval.save()
                logger.info(f"Updated approval {approval.approval_id} status to COMMENTED for questionnaire {questionnaire_id}")
            else:
                logger.warning(f"No active approval found for questionnaire {questionnaire_id}")
        except Exception as approval_error:
            logger.error(f"Error updating approval status for questionnaire {questionnaire_id}: {str(approval_error)}")
            # Don't fail the questionnaire approval if approval update fails
        
        return success_response({
            'message': 'Questionnaire approved successfully',
            'questionnaire_id': questionnaire_id,
            'new_status': 'APPROVED'
        })
        
    except Questionnaire.DoesNotExist:
        return not_found_response("Questionnaire not found")
    except Exception as e:
        logger.error(f"Error approving questionnaire: {str(e)}")
        return error_response("Failed to approve questionnaire", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_reject_view(request, questionnaire_id):
    """Reject a questionnaire - updates status to ARCHIVED
    MULTI-TENANCY: Ensures questionnaire belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        questionnaire = Questionnaire.objects.get(questionnaire_id=questionnaire_id, tenant_id=tenant_id)
        
        # Update questionnaire status
        questionnaire.status = 'ARCHIVED'
        questionnaire.approved_by_user_id = None
        questionnaire.approved_at = None
        questionnaire.reviewer_comment = request.data.get('rejection_reason', 'No reason provided')
        questionnaire.save()
        
        return success_response({
            'message': 'Questionnaire rejected successfully',
            'questionnaire_id': questionnaire_id,
            'new_status': 'ARCHIVED',
            'rejection_reason': questionnaire.reviewer_comment
        })
        
    except Questionnaire.DoesNotExist:
        return not_found_response("Questionnaire not found")
    except Exception as e:
        logger.error(f"Error rejecting questionnaire: {str(e)}")
        return error_response("Failed to reject questionnaire", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def assignment_approve_view(request, assignment_id):
    """Approve an assignment response - updates status to APPROVED
    MULTI-TENANCY: Ensures assignment belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        assignment = TestAssignmentsResponses.objects.get(assignment_response_id=assignment_id, tenant_id=tenant_id)
        
        # Update assignment status
        assignment.status = 'APPROVED'
        assignment.owner_decision = 'APPROVED'
        assignment.save()
        
        return success_response({
            'message': 'Assignment response approved successfully',
            'assignment_id': assignment_id,
            'new_status': 'APPROVED'
        })
        
    except TestAssignmentsResponses.DoesNotExist:
        return not_found_response("Assignment response not found")
    except Exception as e:
        logger.error(f"Error approving assignment response: {str(e)}")
        return error_response("Failed to approve assignment response", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def assignment_reject_view(request, assignment_id):
    """Reject an assignment response - updates status to REJECTED
    MULTI-TENANCY: Ensures assignment belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        assignment = TestAssignmentsResponses.objects.get(assignment_response_id=assignment_id, tenant_id=tenant_id)
        
        # Update assignment status
        assignment.status = 'REJECTED'
        assignment.owner_decision = 'REJECTED'
        assignment.owner_comment = request.data.get('rejection_reason', 'No reason provided')
        assignment.save()
        
        return success_response({
            'message': 'Assignment response rejected successfully',
            'assignment_id': assignment_id,
            'new_status': 'REJECTED',
            'rejection_reason': assignment.owner_comment
        })
        
    except TestAssignmentsResponses.DoesNotExist:
        return not_found_response("Assignment response not found")
    except Exception as e:
        logger.error(f"Error rejecting assignment response: {str(e)}")
        return error_response("Failed to reject assignment response", status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# QUESTIONNAIRE TEMPLATE VIEWS
# =============================================================================
 
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_template_save_view(request):
    """
    Create a QuestionnaireTemplate row using provided payload.
    Expects JSON body with fields matching the model. Minimal validation only.
    
    If module_type is 'SLA', also populates static_questionnaires table for metric tracking.
    MULTI-TENANCY: Sets tenant_id on template and static questionnaire creation
    """
    try:
        # DEBUG: Log request details
        logger.info(f"[Questionnaire Template Save] Request received from user: {getattr(request.user, 'userid', 'unknown')}")
        logger.info(f"[Questionnaire Template Save] Request tenant_id: {getattr(request, 'tenant_id', 'not set')}")
        logger.info(f"[Questionnaire Template Save] Request data keys: {list(request.data.keys()) if request.data else 'no data'}")
        
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            logger.error(f"[Questionnaire Template Save] No tenant_id found for user {getattr(request.user, 'userid', 'unknown')}")
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        data = request.data or {}
 
        # MULTI-TENANCY: Set tenant_id
        template = QuestionnaireTemplate.objects.create(
            template_name=(data.get('template_name') or '').strip(),
            template_description=data.get('template_description') or None,
            template_version=data.get('template_version', '1.0'),
            template_type=data.get('template_type', 'STATIC'),
            template_questions_json=data.get('template_questions_json') or [],
            module_type=data.get('module_type', 'GENERAL'),
            module_subtype=data.get('module_subtype') or None,
            approval_required=bool(data.get('approval_required', False)),
            assigner_id=data.get('assigner_id'),
            assignee_id=data.get('assignee_id'),
            status=data.get('status', 'DRAFT'),
            is_active=bool(data.get('is_active', True)),
            is_template=bool(data.get('is_template', True)),
            created_by=getattr(request.user, 'userid', None),
            tenant_id=tenant_id  # MULTI-TENANCY: Set tenant_id
        )
        
        # If module_type is 'SLA', populate static_questionnaires table
        questions_created = 0
        if template.module_type == 'SLA':
            questions_json = data.get('template_questions_json') or []
            
            for question in questions_json:
                metric_name = question.get('metric_name')
                if metric_name:
                    # Map answer_type to question_type
                    answer_type = question.get('answer_type', 'TEXT').upper()
                    question_type_map = {
                        'TEXT': 'text',
                        'TEXTAREA': 'text',
                        'NUMBER': 'number',
                        'BOOLEAN': 'boolean',
                        'YES_NO': 'boolean',
                        'MULTIPLE_CHOICE': 'multiple_choice',
                        'CHECKBOX': 'multiple_choice',
                        'RATING': 'number',
                        'SCALE': 'number',
                        'DATE': 'text',
                    }
                    question_type = question_type_map.get(answer_type, 'text')
                    
                    # Create entry in static_questionnaires
                    # MULTI-TENANCY: Set tenant_id
                    StaticQuestionnaire.objects.create(
                        metric_name=metric_name,
                        question_text=question.get('question_text', ''),
                        question_type=question_type,
                        is_required=bool(question.get('is_required', False)),
                        scoring_weightings=float(question.get('weightage', 0.0)) if question.get('weightage') else 0.0,
                        tenant_id=tenant_id  # MULTI-TENANCY: Set tenant_id
                    )
                    questions_created += 1
            
            logger.info(f"Created {questions_created} questions in static_questionnaires for SLA metric(s)")

        # If module_type is 'CONTRACT' and status is 'ACTIVE', populate contract_static_questionnaires table
        contract_questions_created = 0
        if template.module_type == 'CONTRACT' and template.status == 'ACTIVE':
            questions_json = data.get('template_questions_json') or []
           
            # Collect all unique term_ids from questions
            term_ids_used = set()
            for question in questions_json:
                term_id = question.get('term_id')
                if term_id:
                    term_ids_used.add(str(term_id))
           
            logger.info(f"Processing {len(questions_json)} questions for CONTRACT module with term_ids: {term_ids_used}")
           
            for question in questions_json:
                term_id = question.get('term_id')
                if term_id:
                    term_id_str = str(term_id)
                   
                    # Map answer_type to question_type
                    answer_type = question.get('answer_type', 'TEXT').upper()
                    question_type_map = {
                        'TEXT': 'text',
                        'TEXTAREA': 'text',
                        'NUMBER': 'number',
                        'BOOLEAN': 'boolean',
                        'YES_NO': 'boolean',
                        'MULTIPLE_CHOICE': 'multiple_choice',
                        'CHECKBOX': 'multiple_choice',
                        'RATING': 'number',
                        'SCALE': 'number',
                        'DATE': 'text',
                    }
                    question_type = question_type_map.get(answer_type, 'text')
                   
                    # Create entry in contract_static_questionnaires
                    # Note: term_id may not exist in contract_terms yet if contract is being created
                    # We still create the questionnaire with the provided term_id
                    # MULTI-TENANCY: Set tenant_id
                    ContractStaticQuestionnaire.objects.create(
                        term_id=term_id_str,  # Store term_id as string
                        template_id=template.template_id,
                        question_text=question.get('question_text', ''),
                        question_type=question_type,
                        is_required=bool(question.get('is_required', False)),
                        scoring_weightings=float(question.get('weightage', 0.0)) if question.get('weightage') else 0.0,
                        tenant_id=tenant_id  # MULTI-TENANCY: Set tenant_id
                    )
                    contract_questions_created += 1
                    logger.info(f"Created question in contract_static_questionnaires for term_id {term_id_str}")
           
            logger.info(f"Created {contract_questions_created} questions in contract_static_questionnaires for CONTRACT module")

        return success_response({
            'template_id': template.template_id,
            'template_name': template.template_name,
            'template_version': template.template_version,
            'status': template.status,
            'module_type': template.module_type,
            'created_at': template.created_at,
            'questions_created': questions_created if template.module_type == 'SLA' else 0,
            'contract_questions_created': contract_questions_created if template.module_type == 'CONTRACT' else 0,
        }, status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Error saving questionnaire template: {str(e)}")
        return error_response("Failed to save questionnaire template", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_template_list_view(request):
    """
    List questionnaire templates, optionally filtered by module_type.
    Query params: module_type (PLANS, VENDOR, CONTRACT, SLA, etc.), status, is_active
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Get query parameters
        module_type = request.GET.get('module_type')
        status_filter = request.GET.get('status')
        is_active = request.GET.get('is_active')
       
        # Build query
        # MULTI-TENANCY: Filter by tenant
        query = Q(is_template=True, tenant_id=tenant_id)
       
        if module_type:
            query &= Q(module_type=module_type)
       
        if status_filter:
            query &= Q(status=status_filter)
       
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query &= Q(is_active=is_active_bool)
       
        # Fetch templates
        templates = QuestionnaireTemplate.objects.filter(query).order_by('-created_at')
       
        # Serialize templates
        templates_data = []
        for template in templates:
            templates_data.append({
                'template_id': template.template_id,
                'template_name': template.template_name,
                'template_description': template.template_description,
                'template_version': template.template_version,
                'template_type': template.template_type,
                'module_type': template.module_type,
                'module_subtype': template.module_subtype,
                'status': template.status,
                'is_active': template.is_active,
                'created_at': template.created_at,
                'updated_at': template.updated_at,
                'created_by': template.created_by,
                'question_count': len(template.template_questions_json) if template.template_questions_json else 0,
            })
       
        return success_response({
            'templates': templates_data,
            'count': len(templates_data)
        })
    except Exception as e:
        logger.error(f"Error listing questionnaire templates: {str(e)}", exc_info=True)
        return error_response(f"Failed to list questionnaire templates: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def questionnaire_template_get_view(request, template_id):
    """
    Get a single questionnaire template by ID, including full questions JSON.
    MULTI-TENANCY: Ensures template belongs to tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # MULTI-TENANCY: Filter by tenant
        template = QuestionnaireTemplate.objects.get(template_id=template_id, is_template=True, tenant_id=tenant_id)
       
        template_data = {
            'template_id': template.template_id,
            'template_name': template.template_name,
            'template_description': template.template_description,
            'template_version': template.template_version,
            'template_type': template.template_type,
            'template_questions_json': template.template_questions_json,
            'module_type': template.module_type,
            'module_subtype': template.module_subtype,
            'approval_required': template.approval_required,
            'assigner_id': template.assigner_id,
            'assignee_id': template.assignee_id,
            'status': template.status,
            'is_active': template.is_active,
            'created_at': template.created_at,
            'updated_at': template.updated_at,
            'created_by': template.created_by,
        }
       
        return success_response(template_data)
    except QuestionnaireTemplate.DoesNotExist:
        return not_found_response("Questionnaire template not found")
    except Exception as e:
        logger.error(f"Error getting questionnaire template: {str(e)}", exc_info=True)
        return error_response(f"Failed to get questionnaire template: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def plan_risks_view(request, plan_id):
    """
    Get all risks associated with a specific plan
    Query: entity='bcp_drp_module' AND row=plan_id (as string)
    MULTI-TENANCY: Ensures plan belongs to tenant and filters risks by tenant
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return error_response("Tenant context not found", status.HTTP_403_FORBIDDEN)
        
        # Verify plan belongs to tenant
        try:
            plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
        except Plan.DoesNotExist:
            return not_found_response("Plan not found")
        
        from apps.vendor_risk.models import RiskTPRM
        
        # Convert plan_id to string for comparison (row field is varchar)
        plan_id_str = str(plan_id)
        
        logger.info(f"Fetching risks for plan_id: {plan_id} (as string: '{plan_id_str}')")
        logger.info(f"Query: entity='bcp_drp_module' AND row='{plan_id_str}'")
        
        # Get all risks where entity is "bcp_drp_module" and row matches the plan_id
        # MULTI-TENANCY: Filter by tenant
        risks = RiskTPRM.objects.filter(
            entity='bcp_drp_module',
            row=plan_id_str,
            tenant_id=tenant_id
        ).order_by('-created_at')
        
        # Count the risks
        risk_count = risks.count()
        logger.info(f"Found {risk_count} risks for plan_id {plan_id}")
        
        risk_data = []
        for risk in risks:
            # Safely parse suggested_mitigations
            mitigations = []
            if risk.suggested_mitigations:
                try:
                    if isinstance(risk.suggested_mitigations, str):
                        mitigations = json.loads(risk.suggested_mitigations)
                    elif isinstance(risk.suggested_mitigations, list):
                        mitigations = risk.suggested_mitigations
                    else:
                        mitigations = []
                except (json.JSONDecodeError, TypeError):
                    mitigations = []
            
            risk_data.append({
                'id': risk.id,
                'title': risk.title,
                'description': risk.description or '',
                'likelihood': risk.likelihood,
                'impact': risk.impact,
                'score': float(risk.score) if risk.score else 0.0,
                'priority': risk.priority,
                'ai_explanation': risk.ai_explanation or '',
                'suggested_mitigations': mitigations,
                'status': risk.status,
                'exposure_rating': risk.exposure_rating,
                'risk_type': risk.risk_type,
                'entity': risk.entity,
                'row': risk.row,
                'created_at': risk.created_at.isoformat() if risk.created_at else None,
                'updated_at': risk.updated_at.isoformat() if risk.updated_at else None,
            })
        
        return success_response({
            'risks': risk_data,
            'count': risk_count,
            'plan_id': plan_id
        })
    except Exception as e:
        logger.error(f"Error fetching risks for plan {plan_id}: {str(e)}", exc_info=True)
        return error_response(f"Failed to fetch risks: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)