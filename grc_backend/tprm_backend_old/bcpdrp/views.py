"""
Function-based views for BCP/DRP API with RBAC integration
Following the pattern from rbac/example_views.py
"""
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.http import HttpRequest
from django.db.models import Q, Max
from django.db import models, connection
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime
import requests
import logging
import json
import jwt
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
import traceback
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# RBAC imports
from tprm_backend.rbac.tprm_decorators import rbac_bcp_drp_required

# Use Unified JWT Authentication from GRC
from grc.jwt_auth import UnifiedJWTAuthentication

logger = logging.getLogger(__name__)


class SimpleAuthenticatedPermission(BasePermission):
    """Custom permission class that checks for authenticated users"""
    def has_permission(self, request, view):
        # Just check if user object exists and is authenticated
        # UnifiedJWTAuthentication handles GRC/TPRM user verification
        if request.user and hasattr(request.user, 'is_authenticated'):
            return request.user.is_authenticated
        return False



@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def plan_list_view(request):
    """Get all plans with optional filtering - requires ViewPlansAndDocuments permission"""
    try:
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        plan_type = request.GET.get('plan_type', '').strip()
        status_filter = request.GET.get('status', '').strip()
        vendor_filter = request.GET.get('vendor', '').strip()
        scope_filter = request.GET.get('scope', '').strip()
        criticality_filter = request.GET.get('criticality', '').strip()
        
        # Start with all plans
        queryset = Plan.objects.all()
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def strategy_list_view(request):
    """Get all strategies with their associated plans, grouped by strategy - requires ViewPlansAndDocuments permission"""
    try:
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        plan_type = request.GET.get('plan_type', '').strip()
        status_filter = request.GET.get('status', '').strip()
        vendor_filter = request.GET.get('vendor', '').strip()
        scope_filter = request.GET.get('scope', '').strip()
        criticality_filter = request.GET.get('criticality', '').strip()
        
        # Start with all plans
        queryset = Plan.objects.all()
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_strategy')
def vendor_upload_view(request):
    """Upload vendor documents and create plan records - requires CreateBCPDRPStrategyAndPlans permission"""
    try:
        # Get the uploaded files and form data
        files = request.FILES
        strategy_name = request.data.get('strategyName', '').strip()
        plan_type = request.data.get('planType', '').strip()
        documents_str = request.data.get('documents', '[]')
        
        logger.info(f"Received upload request - Strategy: {strategy_name}, Plan Type: {plan_type}")
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
        
        if not strategy_name:
            return error_response("Strategy name is required", status.HTTP_400_BAD_REQUEST)
        
        if not plan_type or plan_type not in ['BCP', 'DRP']:
            return error_response("Valid plan type (BCP or DRP) is required", status.HTTP_400_BAD_REQUEST)
        
        if not documents:
            return error_response("At least one document is required", status.HTTP_400_BAD_REQUEST)
        
        # For now, use a default vendor_id (in real app, this would come from authentication)
        vendor_id = 1
        
        # Generate a strategy_id (in real app, this might be managed differently)
        strategy_id = Plan.objects.filter(strategy_name=strategy_name).first()
        if strategy_id:
            strategy_id = strategy_id.strategy_id
        else:
            # Generate new strategy_id based on existing max + 1
            max_strategy = Plan.objects.aggregate(max_id=models.Max('strategy_id'))
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
            logger.info(f"Available file keys: {list(files.keys())}")
            
            if file_key in files:
                uploaded_file = files[file_key]
                logger.info(f"Found file with key: {file_key}")
            else:
                # Fallback: try to find by original filename
                logger.info(f"File key {file_key} not found, trying fallback search")
                for key, file_obj in files.items():
                    if file_obj.name == file_name:
                        uploaded_file = file_obj
                        logger.info(f"Found file with fallback: {key}")
                        break
            
            if not uploaded_file:
                logger.warning(f"File not found for document: {file_name}")
                logger.warning(f"Available files: {[(k, f.name if hasattr(f, 'name') else str(f)) for k, f in files.items()]}")
                continue
            
            # Read file content once for both saving and hashing
            try:
                uploaded_file.seek(0)  # Reset file pointer to beginning if possible
            except (AttributeError, OSError):
                # File object doesn't support seeking, that's okay - read it fresh
                pass
            file_content = uploaded_file.read()
            
            # Validate file type - check content_type or infer from extension
            content_type = uploaded_file.content_type
            if not content_type:
                # Infer content type from extension if not provided
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                if file_extension == '.pdf':
                    content_type = 'application/pdf'
                elif file_extension == '.doc':
                    content_type = 'application/msword'
                elif file_extension == '.docx':
                    content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                else:
                    content_type = 'unknown'
            
            allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if content_type not in allowed_types:
                logger.error(f"Invalid file type: {content_type} for file: {uploaded_file.name}")
                return error_response(f"Invalid file type for {uploaded_file.name}. Only PDF, DOC, and DOCX files are allowed.", status.HTTP_400_BAD_REQUEST)
            
            # Validate file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            file_size = uploaded_file.size if hasattr(uploaded_file, 'size') and uploaded_file.size else len(file_content)
            if file_size > max_size:
                return error_response(f"File {uploaded_file.name} is too large. Maximum size is 10MB.", status.HTTP_400_BAD_REQUEST)
            
            # Generate file path
            file_extension = os.path.splitext(uploaded_file.name)[1]
            storage_file_name = f"vendor_{vendor_id}_{strategy_id}_{uploaded_file.name}"
            file_path = f"uploads/plans/{storage_file_name}"
            
            # Save file to storage using the already-read content
            saved_path = default_storage.save(file_path, ContentFile(file_content))
            
            # Calculate file hash using the already-read content
            sha256_hash = hashlib.sha256(file_content).hexdigest()
            
            # Get next plan_id
            max_plan = Plan.objects.aggregate(max_id=models.Max('plan_id'))
            plan_id = (max_plan['max_id'] or 0) + 1
            
            # Create plan record
            plan = Plan.objects.create(
                plan_id=plan_id,
                vendor_id=vendor_id,
                strategy_id=strategy_id,
                strategy_name=strategy_name,
                plan_type=plan_type,
                plan_name=doc_data.get('planName', ''),
                version='1.0',
                file_uri=saved_path,
                mime_type=content_type,
                sha256_checksum=sha256_hash,
                size_bytes=file_size,
                plan_scope=doc_data.get('scope', ''),
                criticality=doc_data.get('criticality', 'MEDIUM'),
                status='SUBMITTED',
                submitted_by=vendor_id  # In real app, this would be the authenticated user
            )
            
            created_plans.append({
                'plan_id': plan.plan_id,
                'plan_name': plan.plan_name,
                'file_name': uploaded_file.name,
                'status': plan.status
            })
        
        if not created_plans:
            return error_response("No documents were successfully uploaded. Please check that files are attached correctly.", status.HTTP_400_BAD_REQUEST)
        
        return success_response({
            'message': f'Successfully uploaded {len(created_plans)} document(s)',
            'strategy_name': strategy_name,
            'strategy_id': strategy_id,
            'plans': created_plans
        }, status.HTTP_201_CREATED)
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"Error uploading vendor documents: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        return error_response(f"Failed to upload documents: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# DROPDOWN VIEWS
# =============================================================================

@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def dropdown_list_view(request):
    """Get dropdown values by source"""
    try:
        source = request.GET.get('source', '').strip()
        
        if not source:
            return error_response("Source parameter is required", status.HTTP_400_BAD_REQUEST)
        
        # Get dropdown values for the specified source
        dropdowns = Dropdown.objects.filter(source=source).order_by('value')
        
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


# =============================================================================
# QUESTIONNAIRE VIEWS
# =============================================================================

@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
def questionnaire_list_view(request):
    """Get all questionnaires with optional filtering - requires ViewAllQuestionnaires permission"""
    try:
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        plan_type = request.GET.get('plan_type', '').strip()
        status_filter = request.GET.get('status', '').strip()
        owner_filter = request.GET.get('owner', '').strip()
        
        # Start with all questionnaires
        queryset = Questionnaire.objects.all()
        
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
            question_count = Question.objects.filter(questionnaire_id=questionnaire.questionnaire_id).count()
            
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('review_answers')
def questionnaire_detail_view(request, questionnaire_id):
    """Get detailed questionnaire information including questions - requires AssignQuestionnairesForReview permission"""
    try:
        questionnaire = Questionnaire.objects.get(questionnaire_id=questionnaire_id)
        questions = Question.objects.filter(questionnaire_id=questionnaire_id).order_by('seq_no')
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('review_answers')
def questionnaire_review_save_view(request, questionnaire_id):
    """Save reviewer comment for a questionnaire - requires ReviewQuestionnaireAnswers permission"""
    try:
        # Get the questionnaire
        questionnaire = Questionnaire.objects.get(questionnaire_id=questionnaire_id)
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('ocr_extraction')
def ocr_plans_list_view(request):
    """Get plans that need OCR processing - requires OCRExtractionAndReview permission"""
    try:
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        plan_type = request.GET.get('plan_type', '').strip()
        status_filter = request.GET.get('status', '').strip()
        vendor_filter = request.GET.get('vendor', '').strip()
        strategy_filter = request.GET.get('strategy', '').strip()
        
        # Start with plans that need OCR processing
        queryset = Plan.objects.filter(
            status__in=['SUBMITTED', 'OCR_IN_PROGRESS', 'OCR_COMPLETED']
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def comprehensive_plan_detail_view(request, plan_id):
    """
    Get comprehensive plan details including plan info, extracted details, and evaluations
    """
    try:
        # Get plan basic info
        plan = Plan.objects.get(plan_id=plan_id)
        
        # Get extracted details based on plan type
        extracted_details = None
        if plan.plan_type == 'BCP':
            try:
                bcp_details = BcpDetails.objects.get(plan_id=plan_id)
                extracted_details = {
                    'purpose_scope': bcp_details.purpose_scope,
                    'regulatory_references': bcp_details.regulatory_references,
                    'critical_services': bcp_details.critical_services,
                    'dependencies_internal': bcp_details.dependencies_internal,
                    'dependencies_external': bcp_details.dependencies_external,
                    'risk_assessment_summary': bcp_details.risk_assessment_summary,
                    'bia_summary': bcp_details.bia_summary,
                    'rto_targets': bcp_details.rto_targets,
                    'rpo_targets': bcp_details.rpo_targets,
                    'incident_types': bcp_details.incident_types,
                    'alternate_work_locations': bcp_details.alternate_work_locations,
                    'communication_plan_internal': bcp_details.communication_plan_internal,
                    'communication_plan_bank': bcp_details.communication_plan_bank,
                    'roles_responsibilities': bcp_details.roles_responsibilities,
                    'training_testing_schedule': bcp_details.training_testing_schedule,
                    'maintenance_review_cycle': bcp_details.maintenance_review_cycle,
                    'extracted_at': bcp_details.extracted_at.isoformat() if bcp_details.extracted_at else None,
                    'extractor_version': bcp_details.extractor_version
                }
            except BcpDetails.DoesNotExist:
                extracted_details = None
        else:  # DRP
            try:
                drp_details = DrpDetails.objects.get(plan_id=plan_id)
                extracted_details = {
                    'purpose_scope': drp_details.purpose_scope,
                    'regulatory_references': drp_details.regulatory_references,
                    'critical_systems': drp_details.critical_systems,
                    'critical_applications': drp_details.critical_applications,
                    'databases_list': drp_details.databases_list,
                    'supporting_infrastructure': drp_details.supporting_infrastructure,
                    'third_party_services': drp_details.third_party_services,
                    'rto_targets': drp_details.rto_targets,
                    'rpo_targets': drp_details.rpo_targets,
                    'disaster_scenarios': drp_details.disaster_scenarios,
                    'disaster_declaration_process': drp_details.disaster_declaration_process,
                    'data_backup_strategy': drp_details.data_backup_strategy,
                    'recovery_site_details': drp_details.recovery_site_details,
                    'failover_procedures': drp_details.failover_procedures,
                    'failback_procedures': drp_details.failback_procedures,
                    'network_recovery_steps': drp_details.network_recovery_steps,
                    'application_restoration_order': drp_details.application_restoration_order,
                    'testing_validation_schedule': drp_details.testing_validation_schedule,
                    'maintenance_review_cycle': drp_details.maintenance_review_cycle,
                    'extracted_at': drp_details.extracted_at.isoformat() if drp_details.extracted_at else None,
                    'extractor_version': drp_details.extractor_version
                }
            except DrpDetails.DoesNotExist:
                extracted_details = None
        
        # Get evaluations for this plan
        evaluations = Evaluation.objects.filter(plan_id=plan_id).order_by('-assigned_at')
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('ocr_extraction')
def ocr_plan_detail_view(request, plan_id):
    """Get detailed plan information for OCR processing - requires OCRExtractionAndReview permission"""
    try:
        plan = Plan.objects.get(plan_id=plan_id)
        
        # Get extracted details based on plan type
        extracted_data = None
        if plan.plan_type == 'BCP':
            try:
                bcp_details = BcpDetails.objects.get(plan_id=plan_id)
                logger.info(f"Found BCP details for plan {plan_id}: {bcp_details}")
                extracted_data = {
                    'purpose_scope': bcp_details.purpose_scope,
                    'regulatory_references': bcp_details.regulatory_references,
                    'critical_services': bcp_details.critical_services,
                    'dependencies_internal': bcp_details.dependencies_internal,
                    'dependencies_external': bcp_details.dependencies_external,
                    'risk_assessment_summary': bcp_details.risk_assessment_summary,
                    'bia_summary': bcp_details.bia_summary,
                    'rto_targets': bcp_details.rto_targets,
                    'rpo_targets': bcp_details.rpo_targets,
                    'incident_types': bcp_details.incident_types,
                    'alternate_work_locations': bcp_details.alternate_work_locations,
                    'communication_plan_internal': bcp_details.communication_plan_internal,
                    'communication_plan_bank': bcp_details.communication_plan_bank,
                    'roles_responsibilities': bcp_details.roles_responsibilities,
                    'training_testing_schedule': bcp_details.training_testing_schedule,
                    'maintenance_review_cycle': bcp_details.maintenance_review_cycle
                }
                logger.info(f"Extracted data for plan {plan_id}: {extracted_data}")
            except BcpDetails.DoesNotExist:
                logger.warning(f"No BCP details found for plan {plan_id}")
                extracted_data = {}
        else:  # DRP
            try:
                drp_details = DrpDetails.objects.get(plan_id=plan_id)
                extracted_data = {
                    'purpose_scope': drp_details.purpose_scope,
                    'regulatory_references': drp_details.regulatory_references,
                    'critical_systems': drp_details.critical_systems,
                    'critical_applications': drp_details.critical_applications,
                    'databases_list': drp_details.databases_list,
                    'supporting_infrastructure': drp_details.supporting_infrastructure,
                    'third_party_services': drp_details.third_party_services,
                    'rto_targets': drp_details.rto_targets,
                    'rpo_targets': drp_details.rpo_targets,
                    'disaster_scenarios': drp_details.disaster_scenarios,
                    'disaster_declaration_process': drp_details.disaster_declaration_process,
                    'data_backup_strategy': drp_details.data_backup_strategy,
                    'recovery_site_details': drp_details.recovery_site_details,
                    'failover_procedures': drp_details.failover_procedures,
                    'failback_procedures': drp_details.failback_procedures,
                    'network_recovery_steps': drp_details.network_recovery_steps,
                    'application_restoration_order': drp_details.application_restoration_order,
                    'testing_validation_schedule': drp_details.testing_validation_schedule,
                    'maintenance_review_cycle': drp_details.maintenance_review_cycle
                }
            except DrpDetails.DoesNotExist:
                extracted_data = {}
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('ocr_extraction')
def ocr_extraction_save_view(request, plan_id):
    """Save extracted OCR data - requires OCRExtractionAndReview permission"""
    try:
        plan = Plan.objects.get(plan_id=plan_id)
        extracted_data = request.data.get('extracted_data', {})
        
        if plan.plan_type == 'BCP':
            # Create or update BCP extracted details
            bcp_details, created = BcpDetails.objects.get_or_create(
                plan_id=plan_id,
                defaults={
                    'purpose_scope': extracted_data.get('purpose_scope', ''),
                    'regulatory_references': extracted_data.get('regulatory_references', []),
                    'critical_services': extracted_data.get('critical_services', []),
                    'dependencies_internal': extracted_data.get('dependencies_internal', []),
                    'dependencies_external': extracted_data.get('dependencies_external', []),
                    'risk_assessment_summary': extracted_data.get('risk_assessment_summary', ''),
                    'bia_summary': extracted_data.get('bia_summary', ''),
                    'rto_targets': extracted_data.get('rto_targets', {}),
                    'rpo_targets': extracted_data.get('rpo_targets', {}),
                    'incident_types': extracted_data.get('incident_types', []),
                    'alternate_work_locations': extracted_data.get('alternate_work_locations', []),
                    'communication_plan_internal': extracted_data.get('communication_plan_internal', ''),
                    'communication_plan_bank': extracted_data.get('communication_plan_bank', ''),
                    'roles_responsibilities': extracted_data.get('roles_responsibilities', []),
                    'training_testing_schedule': extracted_data.get('training_testing_schedule', ''),
                    'maintenance_review_cycle': extracted_data.get('maintenance_review_cycle', '')
                }
            )
            
            if not created:
                # Update existing record
                bcp_details.purpose_scope = extracted_data.get('purpose_scope', bcp_details.purpose_scope)
                bcp_details.regulatory_references = extracted_data.get('regulatory_references', bcp_details.regulatory_references)
                bcp_details.critical_services = extracted_data.get('critical_services', bcp_details.critical_services)
                bcp_details.dependencies_internal = extracted_data.get('dependencies_internal', bcp_details.dependencies_internal)
                bcp_details.dependencies_external = extracted_data.get('dependencies_external', bcp_details.dependencies_external)
                bcp_details.risk_assessment_summary = extracted_data.get('risk_assessment_summary', bcp_details.risk_assessment_summary)
                bcp_details.bia_summary = extracted_data.get('bia_summary', bcp_details.bia_summary)
                bcp_details.rto_targets = extracted_data.get('rto_targets', bcp_details.rto_targets)
                bcp_details.rpo_targets = extracted_data.get('rpo_targets', bcp_details.rpo_targets)
                bcp_details.incident_types = extracted_data.get('incident_types', bcp_details.incident_types)
                bcp_details.alternate_work_locations = extracted_data.get('alternate_work_locations', bcp_details.alternate_work_locations)
                bcp_details.communication_plan_internal = extracted_data.get('communication_plan_internal', bcp_details.communication_plan_internal)
                bcp_details.communication_plan_bank = extracted_data.get('communication_plan_bank', bcp_details.communication_plan_bank)
                bcp_details.roles_responsibilities = extracted_data.get('roles_responsibilities', bcp_details.roles_responsibilities)
                bcp_details.training_testing_schedule = extracted_data.get('training_testing_schedule', bcp_details.training_testing_schedule)
                bcp_details.maintenance_review_cycle = extracted_data.get('maintenance_review_cycle', bcp_details.maintenance_review_cycle)
                bcp_details.save()
            
        else:  # DRP
            # Create or update DRP extracted details
            drp_details, created = DrpDetails.objects.get_or_create(
                plan_id=plan_id,
                defaults={
                    'purpose_scope': extracted_data.get('purpose_scope', ''),
                    'regulatory_references': extracted_data.get('regulatory_references', []),
                    'critical_systems': extracted_data.get('critical_systems', []),
                    'critical_applications': extracted_data.get('critical_applications', []),
                    'databases_list': extracted_data.get('databases_list', []),
                    'supporting_infrastructure': extracted_data.get('supporting_infrastructure', []),
                    'third_party_services': extracted_data.get('third_party_services', []),
                    'rto_targets': extracted_data.get('rto_targets', {}),
                    'rpo_targets': extracted_data.get('rpo_targets', {}),
                    'disaster_scenarios': extracted_data.get('disaster_scenarios', []),
                    'disaster_declaration_process': extracted_data.get('disaster_declaration_process', ''),
                    'data_backup_strategy': extracted_data.get('data_backup_strategy', ''),
                    'recovery_site_details': extracted_data.get('recovery_site_details', ''),
                    'failover_procedures': extracted_data.get('failover_procedures', ''),
                    'failback_procedures': extracted_data.get('failback_procedures', ''),
                    'network_recovery_steps': extracted_data.get('network_recovery_steps', ''),
                    'application_restoration_order': extracted_data.get('application_restoration_order', []),
                    'testing_validation_schedule': extracted_data.get('testing_validation_schedule', ''),
                    'maintenance_review_cycle': extracted_data.get('maintenance_review_cycle', '')
                }
            )
            
            if not created:
                # Update existing record
                for field, value in extracted_data.items():
                    if hasattr(drp_details, field):
                        setattr(drp_details, field, value)
                drp_details.save()
        
        return success_response({
            'message': 'Extracted data saved successfully',
            'plan_id': plan_id,
            'plan_type': plan.plan_type
        }, status.HTTP_201_CREATED)
        
    except Plan.DoesNotExist:
        return not_found_response("Plan not found")
    except Exception as e:
        logger.error(f"Error saving extracted data: {str(e)}")
        return error_response("Failed to save extracted data", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('ocr_extraction')
def ocr_status_update_view(request, plan_id):
    """Update OCR status of plans - requires OCRExtractionAndReview permission"""
    try:
        plan = Plan.objects.get(plan_id=plan_id)
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('assign_evaluation')
def evaluation_list_view(request, plan_id):
    """Get evaluations for a specific plan - requires AssignPlansForEvaluation permission"""
    try:
        # Check if plan exists
        try:
            plan = Plan.objects.get(plan_id=plan_id)
        except Plan.DoesNotExist:
            return not_found_response("Plan not found")
        
        # Get evaluations for this plan
        evaluations = Evaluation.objects.filter(plan_id=plan_id).order_by('-assigned_at')
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('assign_evaluation')
def evaluation_save_view(request, plan_id):
    """Save evaluation data for a plan - requires AssignPlansForEvaluation permission"""
    try:
        # Check if plan exists
        try:
            plan = Plan.objects.get(plan_id=plan_id)
        except Plan.DoesNotExist:
            return not_found_response("Plan not found")
        
        # Get evaluation data from request
        evaluation_data = request.data
        logger.info(f"Received evaluation data for plan {plan_id}: {evaluation_data}")
        logger.info(f"Score values - overall: {evaluation_data.get('overall_score')}, quality: {evaluation_data.get('quality_score')}, coverage: {evaluation_data.get('coverage_score')}, compliance: {evaluation_data.get('compliance_score')}, weighted: {evaluation_data.get('weighted_score')}")
        
        # Create or update evaluation
        try:
            evaluation = Evaluation.objects.get(plan_id=plan_id)
            created = False
        except Evaluation.DoesNotExist:
            # Get the next evaluation_id manually since auto-increment might not be working
            max_id = Evaluation.objects.aggregate(max_id=models.Max('evaluation_id'))['max_id']
            next_id = (max_id or 0) + 1
            
            logger.info(f"Creating new evaluation {next_id} for plan {plan_id}")
            
            # Convert scores to proper types (handle 0 values correctly)
            overall_score = float(evaluation_data.get('overall_score')) if evaluation_data.get('overall_score') is not None and evaluation_data.get('overall_score') != '' else None
            quality_score = float(evaluation_data.get('quality_score')) if evaluation_data.get('quality_score') is not None and evaluation_data.get('quality_score') != '' else None
            coverage_score = float(evaluation_data.get('coverage_score')) if evaluation_data.get('coverage_score') is not None and evaluation_data.get('coverage_score') != '' else None
            recovery_capability_score = float(evaluation_data.get('recovery_capability_score')) if evaluation_data.get('recovery_capability_score') is not None and evaluation_data.get('recovery_capability_score') != '' else None
            compliance_score = float(evaluation_data.get('compliance_score')) if evaluation_data.get('compliance_score') is not None and evaluation_data.get('compliance_score') != '' else None
            weighted_score = float(evaluation_data.get('weighted_score')) if evaluation_data.get('weighted_score') is not None and evaluation_data.get('weighted_score') != '' else None
            
            evaluation = Evaluation.objects.create(
                evaluation_id=next_id,
                plan_id=plan_id,
                assigned_to_user_id=evaluation_data.get('assigned_to_user_id', 1),
                assigned_by_user_id=evaluation_data.get('assigned_by_user_id', 1),
                status='IN_PROGRESS',
                started_at=timezone.now(),
                overall_score=overall_score,
                quality_score=quality_score,
                coverage_score=coverage_score,
                recovery_capability_score=recovery_capability_score,
                compliance_score=compliance_score,
                weighted_score=weighted_score,
                criteria_json=evaluation_data.get('criteria_json', {}),
                evaluator_comments=evaluation_data.get('evaluator_comments', '')
            )
            created = True
            logger.info(f"Successfully created evaluation {evaluation.evaluation_id}")
        
        if not created:
            # Update existing evaluation
            logger.info(f"Updating existing evaluation {evaluation.evaluation_id} for plan {plan_id}")
            
            # Update scores with proper type conversion (handle 0 values correctly)
            if 'overall_score' in evaluation_data and evaluation_data['overall_score'] is not None and evaluation_data['overall_score'] != '':
                evaluation.overall_score = float(evaluation_data['overall_score'])
            if 'quality_score' in evaluation_data and evaluation_data['quality_score'] is not None and evaluation_data['quality_score'] != '':
                evaluation.quality_score = float(evaluation_data['quality_score'])
            if 'coverage_score' in evaluation_data and evaluation_data['coverage_score'] is not None and evaluation_data['coverage_score'] != '':
                evaluation.coverage_score = float(evaluation_data['coverage_score'])
            if 'recovery_capability_score' in evaluation_data and evaluation_data['recovery_capability_score'] is not None and evaluation_data['recovery_capability_score'] != '':
                evaluation.recovery_capability_score = float(evaluation_data['recovery_capability_score'])
            if 'compliance_score' in evaluation_data and evaluation_data['compliance_score'] is not None and evaluation_data['compliance_score'] != '':
                evaluation.compliance_score = float(evaluation_data['compliance_score'])
            if 'weighted_score' in evaluation_data and evaluation_data['weighted_score'] is not None and evaluation_data['weighted_score'] != '':
                evaluation.weighted_score = float(evaluation_data['weighted_score'])
            
            # Update other fields
            if 'criteria_json' in evaluation_data:
                evaluation.criteria_json = evaluation_data['criteria_json']
            if 'evaluator_comments' in evaluation_data:
                evaluation.evaluator_comments = evaluation_data['evaluator_comments']
            
            # Update status based on whether it's a draft or final submission
            if evaluation_data.get('is_final_submission', False):
                evaluation.status = 'SUBMITTED'
                evaluation.submitted_at = timezone.now()
                logger.info(f"Setting evaluation {evaluation.evaluation_id} status to SUBMITTED")
                
                # Update corresponding approval status to 'COMMENTED'
                try:
                    approval = BcpDrpApprovals.objects.filter(
                        object_type='PLAN',
                        object_id=plan_id,
                        status__in=['ASSIGNED', 'IN_PROGRESS']  # Only update if not already commented/completed
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
            except Exception as save_error:
                logger.error(f"Error saving evaluation: {str(save_error)}")
                raise
        
        # Generate risks if this is a final submission (background task)
        task_info = None
        if evaluation_data.get('is_final_submission', False):
            logger.info(f"Triggering background comprehensive risk generation for completed evaluation {evaluation.evaluation_id} of plan {plan_id}")
            
            try:
                # Import the background task
                from risk_analysis.tasks import generate_comprehensive_risks_task
                
                # Start background task
                task = generate_comprehensive_risks_task.delay(
                    plan_id=plan_id,
                    evaluation_id=evaluation.evaluation_id
                )
                
                task_info = {
                    'task_id': task.id,
                    'status': 'started',
                    'message': 'Comprehensive risk generation started in background'
                }
                
                logger.info(f"Started background risk generation task {task.id} for plan {plan_id}")
                
            except Exception as task_error:
                logger.warning(f"Background task system not available, will generate risks after response: {task_error}")
                
                # Instead of blocking, we'll generate risks after sending the response
                task_info = {
                    'task_id': 'deferred',
                    'status': 'deferred',
                    'message': 'Risk generation will start after evaluation save completes'
                }
        
        response_data = {
            'evaluation_id': evaluation.evaluation_id,
            'plan_id': evaluation.plan_id,
            'status': evaluation.status,
            'message': 'Evaluation saved successfully'
        }
        
        # Include background task info in response
        if task_info:
            response_data['risk_generation'] = task_info
            if task_info['status'] == 'deferred':
                response_data['risk_message'] = "Evaluation saved! Comprehensive risk generation will start shortly - check Risk Analytics in a few minutes"
            else:
                response_data['risk_message'] = "Comprehensive risk generation started in background - risks will appear in Risk Analytics shortly"
        elif evaluation_data.get('is_final_submission', False):
            response_data['risk_message'] = "Risk generation task could not be started - check logs"
        
        # Create response first
        response = success_response(response_data)
        
        # Start deferred risk generation after response (if needed)
        if task_info and task_info['status'] == 'deferred' and evaluation_data.get('is_final_submission', False):
            import threading
            
            def deferred_risk_generation():
                try:
                    logger.info(f"Starting deferred risk generation for evaluation {evaluation.evaluation_id} of plan {plan_id}")
                    sync_result = generate_risks_for_plan_evaluation(
                        plan_id=plan_id,
                        evaluation_id=evaluation.evaluation_id
                    )
                    if sync_result:
                        logger.info(f"Deferred risk generation completed: {len(sync_result.get('risks', []))} risks created")
                    else:
                        logger.error("Deferred risk generation failed")
                except Exception as e:
                    logger.error(f"Error in deferred risk generation: {str(e)}")
            
            # Start the risk generation in a separate thread
            thread = threading.Thread(target=deferred_risk_generation)
            thread.daemon = True  # Thread will die when main process dies
            thread.start()
            logger.info("Started deferred risk generation thread")
        
        return response
        
    except Exception as e:
        logger.error(f"Error saving evaluation: {str(e)}")
        return error_response("Failed to save evaluation", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('approve_evaluations')
def plan_decision_view(request, plan_id):
    """Update plan status based on final decision - requires ApproveOrRejectPlanEvaluations permission"""
    try:
        plan = Plan.objects.get(plan_id=plan_id)
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
        
        # Generate risks for rejected or revision-requested plans (background task)
        task_info = None
        if decision in ['REJECT', 'REVISE']:
            logger.info(f"Triggering background comprehensive risk generation for {decision.lower()}d plan {plan_id}")
            
            try:
                # Import the background task
                from risk_analysis.tasks import generate_comprehensive_risks_task
                
                # Start background task
                task = generate_comprehensive_risks_task.delay(
                    plan_id=plan_id,
                    evaluation_id=None  # No specific evaluation, analyze plan + extracted details
                )
                
                task_info = {
                    'task_id': task.id,
                    'status': 'started',
                    'message': f'Risk generation started for {decision.lower()}d plan'
                }
                
                logger.info(f"Started background risk generation task {task.id} for {decision.lower()}d plan {plan_id}")
                
            except Exception as task_error:
                logger.warning(f"Background task system not available, will generate risks after response: {task_error}")
                
                # Instead of blocking, we'll generate risks after sending the response
                task_info = {
                    'task_id': 'deferred',
                    'status': 'deferred',
                    'message': f'Risk generation will start after {decision.lower()} decision completes'
                }
        
        response_data = {
            'message': f'Plan {decision}D successfully',
            'plan_id': plan_id,
            'decision': decision,
            'new_status': new_status,
            'comment': comment if comment else None
        }
        
        # Include background task info in response
        if task_info:
            response_data['risk_generation'] = task_info
            if task_info['status'] == 'deferred':
                response_data['risk_message'] = f"Plan {decision.lower()}d! Comprehensive risk generation will start shortly - check Risk Analytics in a few minutes"
            else:
                response_data['risk_message'] = "Comprehensive risk generation started in background - risks will appear in Risk Analytics shortly"
        elif decision in ['REJECT', 'REVISE']:
            response_data['risk_message'] = "Risk generation task could not be started - check logs"
        
        # Create response first
        response = success_response(response_data)
        
        # Start deferred risk generation after response (if needed)
        if task_info and task_info['status'] == 'deferred' and decision in ['REJECT', 'REVISE']:
            import threading
            
            def deferred_plan_risk_generation():
                try:
                    logger.info(f"Starting deferred risk generation for {decision.lower()}d plan {plan_id}")
                    sync_result = generate_risks_for_plan_evaluation(
                        plan_id=plan_id,
                        evaluation_id=None
                    )
                    if sync_result:
                        logger.info(f"Deferred plan risk generation completed: {len(sync_result.get('risks', []))} risks created")
                    else:
                        logger.error("Deferred plan risk generation failed")
                except Exception as e:
                    logger.error(f"Error in deferred plan risk generation: {str(e)}")
            
            # Start the risk generation in a separate thread
            thread = threading.Thread(target=deferred_plan_risk_generation)
            thread.daemon = True  # Thread will die when main process dies
            thread.start()
            logger.info("Started deferred plan risk generation thread")
        
        return response
        
    except Plan.DoesNotExist:
        return not_found_response("Plan not found")
    except Exception as e:
        logger.error(f"Error making plan decision: {str(e)}")
        return error_response("Failed to make plan decision", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
def questionnaire_save_view(request):
    """Save questionnaire and its questions - requires CreateQuestionnaire permission"""
    try:
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
            try:
                questionnaire = Questionnaire.objects.get(questionnaire_id=questionnaire_id)
                questionnaire.title = questionnaire_data.get('title')
                questionnaire.description = questionnaire_data.get('description', '')
                questionnaire.plan_type = questionnaire_data.get('planType')
                questionnaire.plan_id = questionnaire_data.get('plan_id')
                questionnaire.status = 'DRAFT'  # Keep as draft when updating
                questionnaire.save()
               
                # Delete existing questions for this questionnaire
                Question.objects.filter(questionnaire_id=questionnaire_id).delete()
               
                logger.info(f"Updated existing questionnaire {questionnaire_id}")
            except Questionnaire.DoesNotExist:
                return error_response(f"Questionnaire with ID {questionnaire_id} not found", status.HTTP_404_NOT_FOUND)
        else:
            # Create new questionnaire
            questionnaire = Questionnaire.objects.create(
                title=questionnaire_data.get('title'),
                description=questionnaire_data.get('description', ''),
                plan_type=questionnaire_data.get('planType'),
                plan_id=questionnaire_data.get('plan_id'),  # Save the selected plan ID
                created_by_user_id=questionnaire_data.get('created_by_user_id', 1),
                status='DRAFT'
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
           
            question = Question.objects.create(
                questionnaire_id=questionnaire.questionnaire_id,
                seq_no=index,
                question_text=question_text_with_metadata,
                answer_type=question_data.get('type', 'TEXT'),
                is_required=question_data.get('required', True),
                weight=question_data.get('weight', 1.0)
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def users_list_view(request):
    """Get all users from Users table for dropdowns"""
    try:
        # Get all active users from Users table
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('assign_evaluation')
def approval_assignment_create_view(request):
    """Create new approval assignment - requires ApprovalAssignment permission"""
    try:
        # Get assignment data from request
        data = request.data
        
        # Get no_approval_needed flag
        no_approval_needed = data.get('no_approval_needed', False)
        
        # If no approval needed, ensure assigner and assignee are the same
        # Set assignee to assigner if not provided
        if no_approval_needed:
            if not data.get('assignee_id'):
                data['assignee_id'] = data.get('assigner_id')
            if not data.get('assignee_name'):
                data['assignee_name'] = data.get('assigner_name')
            if data.get('assigner_id') != data.get('assignee_id'):
                return validation_error_response("When 'no approval needed' is checked, assigner and assignee must be the same")
        
        # Validate required fields
        required_fields = ['workflow_name', 'plan_type', 'assigner_id', 'assigner_name', 
                          'object_type', 'object_id', 'due_date', 'assignee_id', 'assignee_name']
        
        for field in required_fields:
            if not data.get(field):
                return validation_error_response(f"{field.replace('_', ' ').title()} is required")
        
        # Validate user IDs exist
        try:
            assigner = Users.objects.get(user_id=data['assigner_id'])
            # Always validate assignee (it's required by the model)
            assignee = Users.objects.get(user_id=data['assignee_id'])
        except Users.DoesNotExist as e:
            logger.error(f"User not found: {str(e)}")
            return validation_error_response("Invalid assigner or assignee user ID")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid user ID format: {str(e)}")
            return validation_error_response("Invalid assigner or assignee user ID format")
        
        # Validate object type
        valid_object_types = ['PLAN', 'QUESTIONNAIRE', 'ASSIGNMENT_RESPONSE']
        if data['object_type'] not in valid_object_types:
            return validation_error_response(f"Object type must be one of: {', '.join(valid_object_types)}")
        
        # Validate plan type
        valid_plan_types = ['BCP', 'DRP']
        if data['plan_type'] not in valid_plan_types:
            return validation_error_response(f"Plan type must be one of: {', '.join(valid_plan_types)}")
        
        # Generate workflow_id (simple auto-increment for now)
        max_workflow_id = BcpDrpApprovals.objects.aggregate(max_id=models.Max('workflow_id'))['max_id']
        next_workflow_id = (max_workflow_id or 0) + 1
        
        # Parse and convert due_date to naive datetime (MySQL with USE_TZ=False doesn't support timezone-aware)
        due_date_str = data['due_date']
        try:
            # Parse the datetime string from the frontend (format: "2025-10-02T08:35" or "2025-10-02T08:35:00")
            # Handle both with and without seconds
            if 'T' in due_date_str:
                # ISO format with time
                if due_date_str.count(':') == 1:
                    # Format: "2025-10-02T08:35" - add seconds
                    due_date_str = due_date_str + ':00'
                
                # Remove timezone info if present (Z or +00:00 or -05:00)
                if 'Z' in due_date_str:
                    due_date_str = due_date_str.replace('Z', '')
                elif '+' in due_date_str:
                    due_date_str = due_date_str.split('+')[0]
                elif due_date_str.count('-') > 2:  # Has timezone offset like -05:00
                    # Split by last '-' and take everything before it
                    parts = due_date_str.rsplit('-', 1)
                    if ':' in parts[-1]:  # Last part is timezone offset
                        due_date_str = parts[0]
                
                due_date = datetime.fromisoformat(due_date_str)
            else:
                # Date only format
                due_date = datetime.fromisoformat(due_date_str)
            
            # Ensure it's naive (not timezone-aware) for MySQL backend
            if timezone.is_aware(due_date):
                due_date = timezone.make_naive(due_date)
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing due_date '{due_date_str}': {str(e)}")
            return validation_error_response(f"Invalid due_date format: {due_date_str}. Expected format: YYYY-MM-DDTHH:MM")
        
        # Create approval assignment
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
            status='ASSIGNED'
        )
        
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
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error creating approval assignment: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        return error_response(f"Failed to create approval assignment: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


def auto_approve_object(approval):
    """Auto-approve object when no approval is needed"""
    from django.utils import timezone
    
    if approval.object_type == 'PLAN':
        plan = Plan.objects.get(plan_id=approval.object_id)
        plan.status = 'APPROVED'
        plan.approved_by = approval.assignee_id
        plan.approval_date = timezone.now()
        plan.save()
        logger.info(f"Auto-approved plan {approval.object_id} for user {approval.assignee_id}")
        
    elif approval.object_type == 'QUESTIONNAIRE':
        questionnaire = Questionnaire.objects.get(questionnaire_id=approval.object_id)
        questionnaire.status = 'APPROVED'
        questionnaire.approved_by_user_id = approval.assignee_id
        questionnaire.approved_at = timezone.now()
        questionnaire.save()
        logger.info(f"Auto-approved questionnaire {approval.object_id} for user {approval.assignee_id}")
        
    elif approval.object_type == 'ASSIGNMENT_RESPONSE':
        assignment = TestAssignmentsResponses.objects.get(
            assignment_response_id=approval.object_id
        )
        assignment.status = 'APPROVED'
        assignment.owner_decision = 'APPROVED'
        assignment.save()
        logger.info(f"Auto-approved assignment response {approval.object_id} for user {approval.assignee_id}")


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def approval_assignments_list_view(request):
    """Get all approval assignments with optional filtering - requires ViewPlansAndDocuments permission"""
    try:
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '').strip()
        plan_type_filter = request.GET.get('plan_type', '').strip()
        object_type_filter = request.GET.get('object_type', '').strip()
        assignee_filter = request.GET.get('assignee', '').strip()
        
        # Start with all approvals
        queryset = BcpDrpApprovals.objects.all()
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('approve_evaluations')
def my_approvals_view(request):
    """Get approvals assigned to a specific user"""
    try:
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
        queryset = BcpDrpApprovals.objects.filter(assignee_id=user_id)
        
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


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('review_answers')
def questionnaire_assignments_list_view(request):
    """
    Fetch questionnaire assignments from test_assignments_responses table
    """
    try:
        # Get query parameters for filtering
        search_term = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '').strip()
        plan_id_filter = request.GET.get('plan_id', '').strip()
        user_id_filter = request.GET.get('user_id', '').strip()
        
        # Start with all assignments
        queryset = TestAssignmentsResponses.objects.select_related().all()
        
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
        
        # Transform the data
        assignments_data = []
        for assignment in queryset:
            # Parse the answer_text JSON to get question count and metadata
            questions_data = {}
            total_questions = 0
            try:
                if assignment.answer_text:
                    answer_data = json.loads(assignment.answer_text)
                    questions_data = answer_data.get('questions_data', {})
                    total_questions = answer_data.get('assignment_metadata', {}).get('total_questions', 0)
            except (json.JSONDecodeError, KeyError):
                questions_data = {}
                total_questions = 0
            
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
                'owner_comment': assignment.owner_comment,
                'response_status': assignment.response_status,
                'answer_text': assignment.answer_text,
                'reason_comment': assignment.reason_comment,
                'evidence_uri': assignment.evidence_uri,
                'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
                'updated_at': assignment.updated_at.isoformat() if assignment.updated_at else None,
                'total_questions': total_questions,
                'questions_data': questions_data
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('review_answers')
def questionnaire_assignment_save_answers_view(request, assignment_id):
    """
    Save answers for a questionnaire assignment to test_assignments_responses table
    """
    try:
        # Get assignment data from request
        # Use request.data instead of request.body when using DRF's @api_view decorator
        data = request.data
        logger.info(f"Saving answers for assignment {assignment_id}: {data}")
        
        # Validate required fields
        if 'answers' not in data:
            return error_response("Missing required field: answers", status.HTTP_400_BAD_REQUEST)
        
        # Handle reviewer comment
        reviewer_comment = data.get('reviewer_comment', '')
        
        # Get the assignment record
        try:
            assignment = TestAssignmentsResponses.objects.get(assignment_response_id=assignment_id)
        except TestAssignmentsResponses.DoesNotExist:
            return error_response("Assignment not found", status.HTTP_404_NOT_FOUND)
        
        # Parse existing answer_text if it exists
        existing_data = {}
        if assignment.answer_text:
            try:
                existing_data = json.loads(assignment.answer_text)
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
                approval_record = BcpDrpApprovals.objects.filter(
                    object_type='ASSIGNMENT_RESPONSE',
                    object_id=assignment_id,
                    status='ASSIGNED'
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
                        logger.info(f"Assignment {assignment_id} requires manual approval")
                else:
                    logger.info(f"No approval record found for assignment {assignment_id}")
                    
            except Exception as e:
                logger.error(f"Error checking auto-approval for assignment {assignment_id}: {str(e)}")
                # Continue with normal submission even if auto-approval check fails
        
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
        logger.error(f"Error saving assignment answers: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return error_response(f"Failed to save answers: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
def questionnaire_assignment_create_view(request):
    """Create new questionnaire assignment - saves to test_assignments_responses table"""
    try:
        logger.info("Creating questionnaire assignment")
        
        # Get assignment data from request
        # Use request.data instead of request.body when using DRF's @api_view decorator
        data = request.data
        logger.info(f"Assignment data: {data}")
        
        # Validate required fields
        required_fields = ['plan_id', 'questionnaire_id', 'assigned_to_user_id', 'due_date']
        for field in required_fields:
            if field not in data:
                return error_response(f"Missing required field: {field}", status.HTTP_400_BAD_REQUEST)
        
        # Get the assigner user ID from request data or use default
        assigned_by_user_id = data.get('assigned_by_user_id', 1)
        
        # Get all questions for the questionnaire to create a single assignment record with JSON data
        # Use tprm database connection to access test_questions table (in tprm_integration database)
        from django.db import connections
        # Try to use 'tprm' connection if available, otherwise fall back to 'default'
        db_connection = 'tprm' if 'tprm' in connections else 'default'
        with connections[db_connection].cursor() as cursor:
            cursor.execute("""
                SELECT question_id, question_text, answer_type, is_required
                FROM test_questions 
                WHERE questionnaire_id = %s 
                ORDER BY seq_no, question_id
            """, [data['questionnaire_id']])
            
            questions = cursor.fetchall()
            
            if not questions:
                return error_response("No questions found for this questionnaire", status.HTTP_400_BAD_REQUEST)
            
            # Prepare questions data as JSON
            questions_data = []
            question_ids = []
            
            for question_row in questions:
                question_id, question_text, answer_type, is_required = question_row
                question_ids.append(question_id)
                
                # Parse metadata from question_text if it exists
                question_text_clean = question_text
                choice_options = []
                allow_document_upload = False
                
                if '<!--METADATA:' in question_text:
                    parts = question_text.split('<!--METADATA:')
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
                })
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
def plan_approve_view(request, plan_id):
    """Approve a plan - updates status to APPROVED"""
    try:
        plan = Plan.objects.get(plan_id=plan_id)
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
def plan_reject_view(request, plan_id):
    """Reject a plan - updates status to REJECTED"""
    try:
        plan = Plan.objects.get(plan_id=plan_id)
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
def questionnaire_approve_view(request, questionnaire_id):
    """Approve a questionnaire - updates status to APPROVED"""
    try:
        questionnaire = Questionnaire.objects.get(questionnaire_id=questionnaire_id)
        
        # Update questionnaire status
        questionnaire.status = 'APPROVED'
        questionnaire.approved_by_user_id = request.data.get('approved_by', 1)  # Default to user 1 if not provided
        questionnaire.approved_at = models.functions.Now()
        questionnaire.save()
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
def questionnaire_reject_view(request, questionnaire_id):
    """Reject a questionnaire - updates status to ARCHIVED"""
    try:
        questionnaire = Questionnaire.objects.get(questionnaire_id=questionnaire_id)
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
def assignment_approve_view(request, assignment_id):
    """Approve an assignment response - updates status to APPROVED"""
    try:
        assignment = TestAssignmentsResponses.objects.get(assignment_response_id=assignment_id)
        
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('final_approval')
def assignment_reject_view(request, assignment_id):
    """Reject an assignment response - updates status to REJECTED"""
    try:
        assignment = TestAssignmentsResponses.objects.get(assignment_response_id=assignment_id)
        
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
 
@api_view(['POST'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
def questionnaire_template_save_view(request):
    """
    Create a QuestionnaireTemplate row using provided payload.
    Expects JSON body with fields matching the model. Minimal validation only.
    
    If module_type is 'SLA', also populates static_questionnaires table for metric tracking.
    """
    try:
        data = request.data or {}
 
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
                    StaticQuestionnaire.objects.create(
                        metric_name=metric_name,
                        question_text=question.get('question_text', ''),
                        question_type=question_type,
                        is_required=bool(question.get('is_required', False)),
                        scoring_weightings=float(question.get('weightage', 0.0)) if question.get('weightage') else 0.0,
                    )
                    questions_created += 1
            
            logger.info(f"Created {questions_created} questions in static_questionnaires for SLA metric(s)")
 
        return success_response({
            'template_id': template.template_id,
            'template_name': template.template_name,
            'template_version': template.template_version,
            'status': template.status,
            'module_type': template.module_type,
            'created_at': template.created_at,
            'questions_created': questions_created if template.module_type == 'SLA' else 0,
        }, status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Error saving questionnaire template: {str(e)}")
        return error_response("Failed to save questionnaire template", status.HTTP_500_INTERNAL_SERVER_ERROR)

# =============================================================================
# QUESTIONNAIRE TEMPLATE VIEWS
# =============================================================================
 
@api_view(['POST'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
def questionnaire_template_save_view(request):
    """
    Create a QuestionnaireTemplate row using provided payload.
    Expects JSON body with fields matching the model. Minimal validation only.
   
    If module_type is 'SLA', also populates static_questionnaires table for metric tracking.
    """
    try:
        data = request.data or {}
 
        # Get status - if is_active is checked, set to ACTIVE; otherwise use provided status
        final_status = 'ACTIVE' if data.get('is_active', False) else data.get('status', 'DRAFT')
       
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
            status=final_status,  # Use ACTIVE if is_active is checked
            is_active=bool(data.get('is_active', True)),
            is_template=bool(data.get('is_template', True)),
            created_by=getattr(request.user, 'userid', None),
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
                    StaticQuestionnaire.objects.create(
                        metric_name=metric_name,
                        question_text=question.get('question_text', ''),
                        question_type=question_type,
                        is_required=bool(question.get('is_required', False)),
                        scoring_weightings=float(question.get('weightage', 0.0)) if question.get('weightage') else 0.0,
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
                    ContractStaticQuestionnaire.objects.create(
                        term_id=term_id_str,  # Store term_id as string
                        question_text=question.get('question_text', ''),
                        question_type=question_type,
                        is_required=bool(question.get('is_required', False)),
                        scoring_weightings=float(question.get('weightage', 0.0)) if question.get('weightage') else 0.0,
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
def questionnaire_template_list_view(request):
    """
    List questionnaire templates, optionally filtered by module_type.
    Query params: module_type (BCP, DRP, etc.), status, is_active
    """
    try:
        # Get query parameters
        module_type = request.GET.get('module_type')
        status_filter = request.GET.get('status')
        is_active = request.GET.get('is_active')
       
        # Build query
        query = Q(is_template=True)
       
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
def questionnaire_template_get_view(request, template_id):
    """
    Get a single questionnaire template by ID, including full questions JSON.
    """
    try:
        template = QuestionnaireTemplate.objects.get(template_id=template_id, is_template=True)
       
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