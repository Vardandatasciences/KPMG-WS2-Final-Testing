"""
Vendor Questionnaire Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import Http404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.utils import ProgrammingError
import os
import tempfile
import json

from .models import Questionnaires, QuestionnaireQuestions, QuestionnaireAssignments, QuestionnaireResponseSubmissions, RFPResponses
from tprm_backend.apps.vendor_core.models import VendorCategories, TempVendor, ExternalScreeningResult, S3Files
from django.db import connection
from tprm_backend.s3 import create_direct_mysql_client
from django.db.models import Q
from .serializers import (
    QuestionnaireSerializer,
    QuestionnaireListSerializer,
    QuestionnaireCreateSerializer,
    QuestionnaireQuestionSerializer
)

# RBAC imports
from tprm_backend.apps.vendor_core.vendor_authentication import VendorAuthenticationMixin
from tprm_backend.rbac.tprm_decorators import rbac_vendor_required

# MULTI-TENANCY: Import tenant utilities
from tprm_backend.core.tenant_utils import get_tenant_id_from_request

# Database connection helper - Use tprm_integration database for all vendor operations
from django.db import connections

def get_db_connection():
    """
    Get the correct database connection for tprm_integration database.
    Returns 'tprm' if available, otherwise falls back to 'default'.
    """
    if 'tprm' in connections.databases:
        return connections['tprm']
    return connections['default']


class QuestionnaireViewSet(VendorAuthenticationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing questionnaires with RBAC protection
    """
    queryset = Questionnaires.objects.all().prefetch_related('questions')
    
    def create(self, request, *args, **kwargs):
        """Override create to add debug logging"""
        print(f"DEBUG - QuestionnaireViewSet.create() called")
        print(f"DEBUG - request.data: {request.data}")
        print(f"DEBUG - vendor_id in request.data: {request.data.get('vendor_id')}")
        return super().create(request, *args, **kwargs)
    
    def get_object(self):
        """Override get_object to provide better error handling"""
        try:
            return super().get_object()
        except Http404:
            # Provide more specific error information
            pk = self.kwargs.get('pk')
            raise Http404(f"Questionnaire with ID {pk} does not exist")
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return QuestionnaireListSerializer
        elif self.action == 'create':
            return QuestionnaireCreateSerializer
        return QuestionnaireSerializer
    
    def perform_create(self, serializer):
        """Set created_by field when creating questionnaire"""
        # Clean vendor_category_id and vendor_id - set to None if empty or invalid
        validated_data = serializer.validated_data
        print(f"DEBUG - perform_create validated_data: {validated_data}")
        
        if 'vendor_category_id' in validated_data:
            vendor_cat_id = validated_data['vendor_category_id']
            if vendor_cat_id == '' or vendor_cat_id == 0:
                validated_data['vendor_category_id'] = None
        
        if 'vendor_id' in validated_data:
            vendor_id = validated_data['vendor_id']
            print(f"DEBUG - vendor_id in validated_data: {vendor_id}")
            if vendor_id == '' or vendor_id == 0:
                validated_data['vendor_id'] = None
                print(f"DEBUG - vendor_id cleaned to None")
            else:
                print(f"DEBUG - vendor_id kept as: {vendor_id}")
        else:
            print(f"DEBUG - vendor_id not in validated_data")
        
        print(f"DEBUG - Final validated_data before save: {validated_data}")
        serializer.save(created_by=self.request.user.id if hasattr(self.request.user, 'id') else 1)
    
    @action(detail=True, methods=['post'])
    def add_question(self, request, pk=None):
        """Add a single question to an existing questionnaire"""
        questionnaire = self.get_object()
        
        # Set the questionnaire and sequence
        question_data = request.data.copy()
        
        # Auto-set display_order if not provided
        if 'display_order' not in question_data:
            last_question = questionnaire.questions.order_by('display_order').last()
            question_data['display_order'] = (last_question.display_order + 1) if last_question else 1
        
        serializer = QuestionnaireQuestionSerializer(data=question_data)
        if serializer.is_valid():
            serializer.save(questionnaire=questionnaire)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put'])
    def update_questions(self, request, pk=None):
        """Update all questions for a questionnaire"""
        questionnaire = self.get_object()
        questions_data = request.data.get('questions', [])
        
        with transaction.atomic():
            # Delete existing questions
            questionnaire.questions.all().delete()
            
            # Create new questions
            created_questions = []
            for i, question_data in enumerate(questions_data):
                # Clean the question data and ensure display_order
                scoring_weight = float(question_data.get('scoring_weight', 1.0))
                # Clamp scoring_weight to valid range (0.01 to 9.99)
                scoring_weight = max(0.01, min(scoring_weight, 9.99))
                
                clean_data = {
                    'question_text': question_data.get('question_text', ''),
                    'question_type': question_data.get('question_type', 'TEXT'),
                    'question_category': question_data.get('question_category', ''),
                    'is_required': question_data.get('is_required', False),
                    'display_order': question_data.get('display_order', i + 1),
                    'scoring_weight': scoring_weight,
                    'options': question_data.get('options', {}),
                    'conditional_logic': question_data.get('conditional_logic', {}),
                    'help_text': question_data.get('help_text', '')
                }
                
                serializer = QuestionnaireQuestionSerializer(data=clean_data)
                if serializer.is_valid():
                    question = serializer.save(questionnaire=questionnaire)
                    created_questions.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'questions': created_questions}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def save_draft(self, request, pk=None):
        """Save questionnaire as draft with all questions"""
        questionnaire = self.get_object()
        questions_data = request.data.get('questions', [])
        
        with transaction.atomic():
            # Update questionnaire basic info
            questionnaire.questionnaire_name = request.data.get('questionnaire_name', questionnaire.questionnaire_name)
            questionnaire.description = request.data.get('description', questionnaire.description)
            questionnaire.questionnaire_type = request.data.get('questionnaire_type', questionnaire.questionnaire_type)
            vendor_cat_id = request.data.get('vendor_category_id', questionnaire.vendor_category_id)
            questionnaire.vendor_category_id = None if vendor_cat_id == '' or vendor_cat_id == 0 else vendor_cat_id
            vendor_id = request.data.get('vendor_id', questionnaire.vendor_id)
            questionnaire.vendor_id = None if vendor_id == '' or vendor_id == 0 else vendor_id
            questionnaire.status = 'DRAFT'
            questionnaire.save()
            
            # Update questions
            if questions_data:
                questionnaire.questions.all().delete()
                for question_data in questions_data:
                    # Clean the question data to only include valid fields
                    scoring_weight = float(question_data.get('scoring_weight', 1.0))
                    # Clamp scoring_weight to valid range (0.01 to 9.99)
                    scoring_weight = max(0.01, min(scoring_weight, 9.99))
                    
                    clean_data = {
                        'question_text': question_data.get('question_text', ''),
                        'question_type': question_data.get('question_type', 'TEXT'),
                        'question_category': question_data.get('question_category', ''),
                        'is_required': question_data.get('is_required', False),
                        'display_order': question_data.get('display_order', 1),
                        'scoring_weight': scoring_weight,
                        'options': question_data.get('options', {}),
                        'conditional_logic': question_data.get('conditional_logic', {}),
                        'help_text': question_data.get('help_text', '')
                    }
                    QuestionnaireQuestions.objects.create(
                        questionnaire=questionnaire,
                        **clean_data
                    )
        
        # Return updated questionnaire
        serializer = QuestionnaireSerializer(questionnaire)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate questionnaire (change status to ACTIVE)"""
        questionnaire = self.get_object()
        questions_data = request.data.get('questions', [])
        
        with transaction.atomic():
            # Update questionnaire details if provided
            if 'questionnaire_name' in request.data:
                questionnaire.questionnaire_name = request.data['questionnaire_name']
            if 'description' in request.data:
                questionnaire.description = request.data['description']
            if 'questionnaire_type' in request.data:
                questionnaire.questionnaire_type = request.data['questionnaire_type']
            if 'vendor_category_id' in request.data:
                vendor_cat_id = request.data['vendor_category_id']
                questionnaire.vendor_category_id = None if vendor_cat_id == '' or vendor_cat_id == 0 else vendor_cat_id
            if 'vendor_id' in request.data:
                vendor_id = request.data['vendor_id']
                questionnaire.vendor_id = None if vendor_id == '' or vendor_id == 0 else vendor_id
            
            # Update questions if provided
            if questions_data:
                questionnaire.questions.all().delete()
                for i, question_data in enumerate(questions_data):
                    scoring_weight = float(question_data.get('scoring_weight', 1.0))
                    # Clamp scoring_weight to valid range (0.01 to 9.99)
                    scoring_weight = max(0.01, min(scoring_weight, 9.99))
                    
                    clean_data = {
                        'question_text': question_data.get('question_text', ''),
                        'question_type': question_data.get('question_type', 'TEXT'),
                        'question_category': question_data.get('question_category', ''),
                        'is_required': question_data.get('is_required', False),
                        'display_order': question_data.get('display_order', i + 1),
                        'scoring_weight': scoring_weight,
                        'options': question_data.get('options', {}),
                        'conditional_logic': question_data.get('conditional_logic', {}),
                        'help_text': question_data.get('help_text', '')
                    }
                    QuestionnaireQuestions.objects.create(
                        questionnaire=questionnaire,
                        **clean_data
                    )
            
            # Validate that questionnaire has questions
            if not questionnaire.questions.exists():
                return Response(
                    {'error': 'Cannot activate questionnaire without questions'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            questionnaire.status = 'ACTIVE'
            questionnaire.save()
        
        serializer = QuestionnaireSerializer(questionnaire)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive questionnaire (change status to ARCHIVED)"""
        questionnaire = self.get_object()
        questionnaire.status = 'ARCHIVED'
        questionnaire.save()
        
        serializer = QuestionnaireSerializer(questionnaire)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def get_question_types(self, request):
        """Get available question types"""
        question_types = [
            {'value': 'TEXT', 'label': 'Text'},
            {'value': 'MULTIPLE_CHOICE', 'label': 'Multiple Choice'},
            {'value': 'CHECKBOX', 'label': 'Checkbox'},
            {'value': 'RATING', 'label': 'Rating'},
            {'value': 'FILE_UPLOAD', 'label': 'File Upload'},
            {'value': 'DATE', 'label': 'Date'},
            {'value': 'NUMBER', 'label': 'Number'},
        ]
        return Response(question_types)
    
    @action(detail=False, methods=['get'])
    def get_questionnaire_types(self, request):
        """Get available questionnaire types"""
        questionnaire_types = [
            {'value': 'ONBOARDING', 'label': 'Onboarding'},
            {'value': 'ANNUAL', 'label': 'Annual Review'},
            {'value': 'INCIDENT', 'label': 'Incident Response'},
            {'value': 'CUSTOM', 'label': 'Custom'},
        ]
        return Response(questionnaire_types)
    
    @action(detail=False, methods=['get'])
    def get_vendor_categories(self, request):
        """Get available vendor categories"""
        categories = VendorCategories.objects.all()
        category_list = [
            {
                'value': str(cat.category_id),
                'label': cat.category_name,
                'code': cat.category_code,
                'risk_level': cat.criticality_level
            }
            for cat in categories
        ]
        return Response(category_list)
    
    @action(detail=False, methods=['get'])
    def get_vendors(self, request):
        """Get list of available vendors from temp_vendor table"""
        vendors = TempVendor.objects.all().order_by('company_name')
        vendor_list = [
            {
                'id': vendor.id,
                'vendor_code': vendor.vendor_code,
                'company_name': vendor.company_name,
                'legal_name': vendor.legal_name,
                'status': vendor.status,
                'risk_level': vendor.risk_level,
                'vendor_category': vendor.vendor_category,
                'business_type': vendor.business_type,
                'industry_sector': vendor.industry_sector
            }
            for vendor in vendors
        ]
        return Response(vendor_list)
    
    @action(detail=False, methods=['get'])
    def get_vendor_rfp_data(self, request):
        """Get RFP response data for a specific vendor using temp_vendor.response_id"""
        vendor_id_param = request.query_params.get('vendor_id')
        if not vendor_id_param:
            return Response(
                {'error': 'vendor_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Convert vendor_id to integer
            try:
                vendor_id = int(vendor_id_param)
            except (ValueError, TypeError):
                return Response(
                    {'error': f'Invalid vendor_id: {vendor_id_param}. Must be a valid integer.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Debug logging
            print(f"DEBUG - get_vendor_rfp_data: vendor_id={vendor_id} (type: {type(vendor_id)})")
            
            # Get the TempVendor to access response_id
            try:
                temp_vendor = TempVendor.objects.get(id=vendor_id)
                print(f"DEBUG - Found TempVendor: {temp_vendor.company_name}, response_id={temp_vendor.response_id}")
            except TempVendor.DoesNotExist:
                print(f"DEBUG - TempVendor with id={vendor_id} not found")
                return Response(
                    {'error': f'Vendor with id {vendor_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if temp_vendor has a response_id
            if not temp_vendor.response_id:
                print(f"DEBUG - TempVendor {vendor_id} has no response_id")
                return Response([])  # Return empty array if no response_id
            
            # Query RFP responses using the response_id from temp_vendor
            rfp_responses = RFPResponses.objects.filter(response_id=temp_vendor.response_id).order_by('-submission_date')
            print(f"DEBUG - Query by response_id={temp_vendor.response_id} found {rfp_responses.count()} responses")
            
            # If no results found by response_id, try fallback methods
            if not rfp_responses.exists():
                print(f"DEBUG - No RFP responses found by response_id, trying fallback methods...")
                
                # Fallback 1: Try by vendor_id in rfp_responses table
                rfp_responses = RFPResponses.objects.filter(vendor_id=vendor_id).order_by('-submission_date')
                print(f"DEBUG - Fallback: Query by vendor_id={vendor_id} found {rfp_responses.count()} responses")
                
                # Fallback 2: If still no results and we have userid, try by user_id
                if not rfp_responses.exists() and temp_vendor.userid:
                    user_id = temp_vendor.userid
                    print(f"DEBUG - Fallback: Trying by userid={user_id}")
                    try:
                        with get_db_connection().cursor() as cursor:
                            cursor.execute("""
                                SELECT DISTINCT rr.response_id
                                FROM rfp_responses rr
                                LEFT JOIN rfp_invitations ri ON rr.invitation_id = ri.invitation_id
                                WHERE (rr.invitation_id IS NOT NULL AND ri.user_id = %s)
                                   OR (rr.submitted_by IS NOT NULL AND rr.submitted_by LIKE %s)
                            """, [user_id, f'%{user_id}%'])
                            response_ids = [row[0] for row in cursor.fetchall()]
                            
                            if response_ids:
                                rfp_responses = RFPResponses.objects.filter(response_id__in=response_ids).order_by('-submission_date')
                                print(f"DEBUG - Fallback: Query by userid found {rfp_responses.count()} responses")
                    except Exception as e:
                        print(f"DEBUG - Fallback query by userid failed: {str(e)}")
            
            print(f"DEBUG - Total RFP responses found: {rfp_responses.count()}")
            rfp_data = []
            
            for response in rfp_responses:
                # Parse response_documents if it's a string
                response_docs = response.response_documents
                if isinstance(response_docs, str):
                    try:
                        response_docs = json.loads(response_docs)
                    except (json.JSONDecodeError, TypeError):
                        response_docs = {}
                
                # Parse document_urls if it exists and is a string
                document_urls = getattr(response, 'document_urls', None)
                if document_urls and isinstance(document_urls, str):
                    try:
                        document_urls = json.loads(document_urls)
                    except (json.JSONDecodeError, TypeError):
                        document_urls = None
                
                # Extract documents array from response_documents or document_urls
                documents = []
                
                # First try response_documents
                if response_docs:
                    if isinstance(response_docs, dict):
                        # Check various possible structures
                        documents = (
                            response_docs.get('documents', []) or
                            response_docs.get('document_urls', []) or
                            (list(response_docs.values()) if response_docs.values() and not isinstance(list(response_docs.values())[0] if response_docs.values() else None, dict) else [])
                        )
                    elif isinstance(response_docs, list):
                        documents = response_docs
                
                # If no documents from response_documents, try document_urls
                if not documents and document_urls:
                    if isinstance(document_urls, list):
                        documents = document_urls
                    elif isinstance(document_urls, dict):
                        documents = document_urls.get('documents', []) or document_urls.get('urls', []) or (list(document_urls.values()) if document_urls.values() else [])
                
                # Combine both into a unified structure for frontend
                # Keep document_urls separate and accessible for frontend
                combined_docs = {
                    'documents': documents,  # Legacy support - extracted file references
                    'response_documents': response_docs if response_docs else None,  # Original JSON data
                    'document_urls': document_urls if document_urls else None  # Document URLs for file access
                }
                
                # Also include document_urls at the top level for easier access
                response_document_urls = document_urls if document_urls else None
                
                # Get additional JSON fields
                proposal_data = getattr(response, 'proposal_data', None)
                external_submission_data = getattr(response, 'external_submission_data', None)
                draft_data = getattr(response, 'draft_data', None)
                completion_percentage = getattr(response, 'completion_percentage', None)
                
                rfp_data.append({
                    'response_id': response.response_id,
                    'rfp_id': response.rfp_id,
                    'submission_date': response.submission_date.isoformat() if response.submission_date else None,
                    'proposed_value': float(response.proposed_value) if response.proposed_value else None,
                    'technical_score': float(response.technical_score) if response.technical_score else None,
                    'commercial_score': float(response.commercial_score) if response.commercial_score else None,
                    'overall_score': float(response.overall_score) if response.overall_score else None,
                    'evaluation_status': response.evaluation_status,
                    'evaluation_date': response.evaluation_date.isoformat() if response.evaluation_date else None,
                    'evaluation_comments': response.evaluation_comments,
                    'completion_percentage': float(completion_percentage) if completion_percentage else None,
                    'response_documents': combined_docs,  # Unified structure with documents array and data
                    'document_urls': response_document_urls,  # Direct access to document URLs
                    'proposal_data': proposal_data,  # Include proposal data
                    'external_submission_data': external_submission_data,  # Include external submission data
                    'draft_data': draft_data,  # Include draft data
                    'response_documents_count': len(documents) if documents else 0
                })
            
            print(f"DEBUG - Returning {len(rfp_data)} RFP data entries")
            return Response(rfp_data)
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"ERROR - get_vendor_rfp_data failed: {str(e)}")
            print(f"ERROR - Traceback: {error_trace}")
            return Response(
                {'error': f'Failed to fetch RFP data: {str(e)}', 'traceback': error_trace},
                status=status.HTTP_200_OK
            )
    
    @action(detail=False, methods=['get'])
    def get_vendor_screening_data(self, request):
        """Get external screening data for a specific vendor"""
        vendor_id = request.query_params.get('vendor_id')
        if not vendor_id:
            return Response(
                {'error': 'vendor_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            screening_results = ExternalScreeningResult.objects.filter(vendor_id=vendor_id).order_by('-screening_date')
            screening_data = []
            
            for result in screening_results:
                screening_data.append({
                    'screening_id': result.screening_id,
                    'screening_type': result.screening_type,
                    'screening_date': result.screening_date,
                    'search_terms': result.search_terms,
                    'total_matches': result.total_matches,
                    'high_risk_matches': result.high_risk_matches,
                    'status': result.status,
                    'last_updated': result.last_updated,
                    'review_date': result.review_date,
                    'review_comments': result.review_comments
                })
            
            return Response(screening_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch screening data: {str(e)}'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=False, methods=['get'])
    def get_templates(self, request):
        """
        List questionnaire templates for VENDOR module_type.
        Query params: status, is_active
        NOTE: Templates are stored in tprm_integration database, not default database
        """
        try:
            from tprm_backend.bcpdrp.models import QuestionnaireTemplate
            import logging
            logger = logging.getLogger(__name__)
            
            # Get query parameters
            status_filter = request.query_params.get('status')
            is_active = request.query_params.get('is_active')
            
            # Build query - always filter by VENDOR module_type and is_template=True
            query = Q(module_type='VENDOR', is_template=True)
            
            # MULTI-TENANCY: Filter by tenant if available, but also include NULL tenant_id (shared templates)
            tenant_id = get_tenant_id_from_request(request)
            if tenant_id:
                # Include templates for this tenant OR templates with NULL tenant_id (shared templates)
                query &= (Q(tenant_id=tenant_id) | Q(tenant_id__isnull=True))
                logger.info(f'[Get Templates] Filtering templates by tenant_id: {tenant_id} (including shared templates)')
                print(f'Filtering templates by tenant_id: {tenant_id} (including shared templates)')
            else:
                logger.warning('[Get Templates] No tenant_id found in request - returning all templates')
                print('Warning: No tenant_id found in request - returning all templates')
            
            if status_filter:
                query &= Q(status=status_filter)
            
            if is_active is not None:
                is_active_bool = is_active.lower() == 'true'
                query &= Q(is_active=is_active_bool)
            
            # Use tprm database connection explicitly since templates are in tprm_integration database
            # Check if 'tprm' connection exists
            db_alias = 'tprm'
            if 'tprm' not in connections.databases:
                logger.warning('[Get Templates] tprm database connection not found, using default')
                print('Warning: tprm database connection not found, using default')
                db_alias = 'default'
            else:
                logger.info('[Get Templates] Using tprm database connection for questionnaire_templates table')
                print('Using tprm database connection for questionnaire_templates table')
            
            # Fetch templates using the correct database
            templates = QuestionnaireTemplate.objects.using(db_alias).filter(query).order_by('-created_at')
            template_count = templates.count()
            
            logger.info(f'[Get Templates] Found {template_count} templates matching query')
            print(f'Found {template_count} templates matching query')
            
            # Debug: Check total templates in database
            all_templates_count = QuestionnaireTemplate.objects.using(db_alias).filter(
                module_type='VENDOR', is_template=True
            ).count()
            logger.info(f'[Get Templates] Total VENDOR templates in database: {all_templates_count}')
            print(f'[DEBUG] Total VENDOR templates in database: {all_templates_count}')
            
            # If no templates found, try without tenant filter for debugging
            if template_count == 0:
                logger.warning(f'[Get Templates] No templates found with current filters')
                print(f'Warning: No templates found with current filters')
                # Try query without tenant filter to see if templates exist
                query_without_tenant = Q(module_type='VENDOR', is_template=True)
                if status_filter:
                    query_without_tenant &= Q(status=status_filter)
                if is_active is not None:
                    is_active_bool = is_active.lower() == 'true'
                    query_without_tenant &= Q(is_active=is_active_bool)
                templates_without_tenant = QuestionnaireTemplate.objects.using(db_alias).filter(query_without_tenant).order_by('-created_at')
                count_without_tenant = templates_without_tenant.count()
                logger.info(f'[Get Templates] Found {count_without_tenant} templates without tenant filter')
                print(f'[DEBUG] Found {count_without_tenant} templates without tenant filter')
                
                # If templates exist without tenant filter, use them (templates might not have tenant_id set)
                if count_without_tenant > 0:
                    logger.warning('[Get Templates] Using templates without tenant filter (templates may not have tenant_id set)')
                    print('[DEBUG] Using templates without tenant filter (templates may not have tenant_id set)')
                    templates = templates_without_tenant
                    template_count = count_without_tenant
            
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
            
            return Response({
                'success': True,
                'templates': templates_data,
                'count': len(templates_data)
            }, status=status.HTTP_200_OK)
        except ProgrammingError as e:
            # Handle case where table doesn't exist yet
            error_msg = str(e)
            if "doesn't exist" in error_msg.lower() or "1146" in error_msg:
                print(f"Questionnaire templates table doesn't exist yet. Returning empty list.")
                return Response({
                    'success': True,
                    'templates': [],
                    'count': 0
                }, status=status.HTTP_200_OK)
            else:
                # Re-raise if it's a different ProgrammingError
                raise
        except Exception as e:
            import traceback
            print(f"Error listing questionnaire templates: {str(e)}")
            print(traceback.format_exc())
            return Response({'success': True, 'templates': [], 'count': 0, 'message': 'Templates temporarily unavailable'},  
                status=status.HTTP_200_OK
            )
    
    @action(detail=False, methods=['get'])
    def get_template(self, request):
        """
        Get a specific questionnaire template by template_id.
        Query params: template_id
        """
        try:
            from tprm_backend.bcpdrp.models import QuestionnaireTemplate
            
            template_id = request.query_params.get('template_id')
            if not template_id:
                return Response(
                    {'error': 'template_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                template = QuestionnaireTemplate.objects.get(
                    template_id=template_id,
                    module_type='VENDOR',
                    is_template=True
                )
            except QuestionnaireTemplate.DoesNotExist:
                return Response(
                    {'error': f'Template with ID {template_id} not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get questions from template
            questions = template.template_questions_json or []
            
            return Response({
                'success': True,
                'template_id': template.template_id,
                'template_name': template.template_name,
                'template_description': template.template_description,
                'template_version': template.template_version,
                'template_type': template.template_type,
                'module_type': template.module_type,
                'module_subtype': template.module_subtype,
                'status': template.status,
                'is_active': template.is_active,
                'questions': questions,
                'question_count': len(questions)
            }, status=status.HTTP_200_OK)
        except ProgrammingError as e:
            # Handle case where table doesn't exist yet
            error_msg = str(e)
            if "doesn't exist" in error_msg.lower() or "1146" in error_msg:
                print(f"Questionnaire templates table doesn't exist yet.")
                return Response(
                    {'error': 'Questionnaire templates table does not exist yet'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            else:
                # Re-raise if it's a different ProgrammingError
                raise
        except Exception as e:
            import traceback
            print(f"Error getting questionnaire template: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Failed to get questionnaire template: {str(e)}'}, 
                status=status.HTTP_200_OK
            )


class QuestionnaireQuestionViewSet(VendorAuthenticationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing individual questionnaire questions with RBAC protection
    """
    queryset = QuestionnaireQuestions.objects.all()
    serializer_class = QuestionnaireQuestionSerializer
    
    def get_queryset(self):
        """Filter questions by questionnaire if provided"""
        queryset = super().get_queryset()
        questionnaire_id = self.request.query_params.get('questionnaire_id')
        if questionnaire_id:
            queryset = queryset.filter(questionnaire_id=questionnaire_id)
        return queryset
    
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """Reorder question within questionnaire"""
        question = self.get_object()
        new_order = request.data.get('display_order')
        
        if new_order is None:
            return Response(
                {'error': 'display_order is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Get all questions in the same questionnaire
            questions = QuestionnaireQuestions.objects.filter(
                questionnaire=question.questionnaire
            ).exclude(question_id=question.question_id)
            
            # Reorder other questions
            for q in questions:
                if q.display_order >= new_order:
                    q.display_order += 1
                    q.save()
            
            # Update current question
            question.display_order = new_order
            question.save()
        
        serializer = QuestionnaireQuestionSerializer(question)
        return Response(serializer.data)


class QuestionnaireAssignmentViewSet(VendorAuthenticationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing questionnaire assignments to vendors with RBAC protection
    """
    queryset = QuestionnaireAssignments.objects.all().select_related('temp_vendor', 'questionnaire')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        from .serializers import QuestionnaireAssignmentSerializer
        return QuestionnaireAssignmentSerializer
    
    @rbac_vendor_required('AssignQuestionnaires')
    @action(detail=False, methods=['post'])
    def assign_questionnaire(self, request):
        """Assign questionnaire to multiple vendors"""
        questionnaire_id = request.data.get('questionnaire_id')
        vendor_ids = request.data.get('vendor_ids', [])
        due_date = request.data.get('due_date')
        notes = request.data.get('notes', '')
        
        if not questionnaire_id or not vendor_ids:
            return Response(
                {'error': 'questionnaire_id and vendor_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        questionnaire = get_object_or_404(Questionnaires, questionnaire_id=questionnaire_id)
        created_assignments = []
        errors = []
        
        with transaction.atomic():
            for vendor_id in vendor_ids:
                try:
                    vendor = get_object_or_404(TempVendor, id=vendor_id)
                    
                    # Check if assignment already exists
                    existing = QuestionnaireAssignments.objects.filter(
                        temp_vendor=vendor,
                        questionnaire=questionnaire
                    ).first()
                    
                    if existing:
                        errors.append(f"Assignment already exists for {vendor.company_name}")
                        continue
                    
                    assignment = QuestionnaireAssignments.objects.create(
                        temp_vendor=vendor,
                        questionnaire=questionnaire,
                        due_date=due_date,
                        notes=notes,
                        assigned_by_id=1  # TODO: Use actual user ID
                    )
                    created_assignments.append(assignment)
                    
                    # Start Questionnaire Response lifecycle stage
                    self._start_questionnaire_response_stage(vendor.id)
                    
                except Exception as e:
                    errors.append(f"Error assigning to vendor {vendor_id}: {str(e)}")
        
        from .serializers import QuestionnaireAssignmentSerializer
        serializer = QuestionnaireAssignmentSerializer(created_assignments, many=True)
        
        response_data = {
            'assignments': serializer.data,
            'created_count': len(created_assignments),
            'errors': errors
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    def _start_questionnaire_response_stage(self, vendor_id):
        """Start Questionnaire Response lifecycle stage when questionnaire is assigned"""
        try:
            from apps.vendor_core.models import LifecycleTracker, VendorLifecycleStages
            from apps.vendor_core.views import get_lifecycle_stage_id_by_code
            from django.utils import timezone
            
            ques_response_stage_id = get_lifecycle_stage_id_by_code('QUES_RES')
            if not ques_response_stage_id:
                print(f"Warning: Could not find QUES_RES stage for vendor {vendor_id}")
                return
            
            # Check if Questionnaire Response stage is already started for this vendor
            existing_entry = LifecycleTracker.objects.filter(
                vendor_id=vendor_id,
                lifecycle_stage=ques_response_stage_id,
                ended_at__isnull=True
            ).first()
            
            if not existing_entry:
                # Start the Questionnaire Response stage
                LifecycleTracker.objects.create(
                    vendor_id=vendor_id,
                    lifecycle_stage=ques_response_stage_id,
                    started_at=timezone.now()
                )
                print(f"Started Questionnaire Response stage for vendor {vendor_id}")
            else:
                print(f"Questionnaire Response stage already started for vendor {vendor_id}")
                
        except Exception as e:
            print(f"Error starting questionnaire response stage for vendor {vendor_id}: {str(e)}")
    
    def _end_questionnaire_response_start_response_approval(self, vendor_id):
        """End Questionnaire Response stage and start Response Approval stage"""
        try:
            from apps.vendor_core.models import LifecycleTracker, TempVendor
            from apps.vendor_core.views import get_lifecycle_stage_id_by_code
            from django.utils import timezone
            
            print(f"Debug - Starting lifecycle transition for vendor {vendor_id}: Questionnaire Response -> Response Approval")
            current_time = timezone.now()
            
            # Get stage IDs - Questionnaire Response (4) -> Response Approval (5)
            ques_response_stage_id = get_lifecycle_stage_id_by_code('QUES_RES')
            response_approval_stage_id = get_lifecycle_stage_id_by_code('RES_APP')
            
            print(f"Debug - Stage IDs: QUES_RES={ques_response_stage_id}, RES_APP={response_approval_stage_id}")
            
            if not ques_response_stage_id or not response_approval_stage_id:
                print(f"ERROR - Could not find stage IDs for vendor {vendor_id}")
                print(f"  QUES_RES ID: {ques_response_stage_id}")
                print(f"  RES_APP ID: {response_approval_stage_id}")
                return
            
            # End Questionnaire Response stage
            response_stage_entry = LifecycleTracker.objects.filter(
                vendor_id=vendor_id,
                lifecycle_stage=ques_response_stage_id,
                ended_at__isnull=True
            ).first()
            
            if response_stage_entry:
                response_stage_entry.ended_at = current_time
                response_stage_entry.save()
                print(f"✓ Successfully ended Questionnaire Response stage for vendor {vendor_id} at {current_time}")
            else:
                print(f"WARNING - No active Questionnaire Response stage found for vendor {vendor_id}")
                # Check if there are any lifecycle entries for this vendor
                all_entries = LifecycleTracker.objects.filter(vendor_id=vendor_id)
                print(f"Debug - All lifecycle entries for vendor {vendor_id}: {list(all_entries.values('id', 'lifecycle_stage', 'started_at', 'ended_at'))}")
            
            # Start Response Approval stage
            new_entry = LifecycleTracker.objects.create(
                vendor_id=vendor_id,
                lifecycle_stage=response_approval_stage_id,
                started_at=current_time
            )
            print(f"✓ Successfully created Response Approval stage entry (ID: {new_entry.id}) for vendor {vendor_id}")
            
            # Update temp vendor current stage
            try:
                temp_vendor = TempVendor.objects.get(id=vendor_id)
                old_stage = temp_vendor.lifecycle_stage
                temp_vendor.lifecycle_stage = response_approval_stage_id
                temp_vendor.save()
                print(f"✓ Successfully updated temp vendor {vendor_id} lifecycle stage from {old_stage} to {response_approval_stage_id}")
            except TempVendor.DoesNotExist:
                print(f"ERROR - Temp vendor {vendor_id} not found")
            
            print(f"✓ COMPLETED - Successfully transitioned vendor {vendor_id} from Questionnaire Response to Response Approval stage")
            
        except Exception as e:
            print(f"ERROR - Failed to transition lifecycle stages for vendor {vendor_id}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _end_questionnaire_approval_start_response_approval(self, vendor_id):
        """End Questionnaire Approval stage and start Response Approval stage"""
        try:
            from apps.vendor_core.models import LifecycleTracker, TempVendor
            from apps.vendor_core.views import get_lifecycle_stage_id_by_code
            from django.utils import timezone
            
            current_time = timezone.now()
            
            # Get stage IDs
            ques_approval_stage_id = get_lifecycle_stage_id_by_code('QUES_APP')
            response_approval_stage_id = get_lifecycle_stage_id_by_code('RES_APP')
            
            if not ques_approval_stage_id or not response_approval_stage_id:
                print(f"Warning: Could not find stage IDs for vendor {vendor_id}")
                return
            
            # End Questionnaire Approval stage
            approval_stage_entry = LifecycleTracker.objects.filter(
                vendor_id=vendor_id,
                lifecycle_stage=ques_approval_stage_id,
                ended_at__isnull=True
            ).first()
            
            if approval_stage_entry:
                approval_stage_entry.ended_at = current_time
                approval_stage_entry.save()
                print(f"Ended Questionnaire Approval stage for vendor {vendor_id}")
            
            # Start Response Approval stage
            LifecycleTracker.objects.create(
                vendor_id=vendor_id,
                lifecycle_stage=response_approval_stage_id,
                started_at=current_time
            )
            
            # Update temp vendor current stage
            temp_vendor = TempVendor.objects.get(id=vendor_id)
            temp_vendor.lifecycle_stage = response_approval_stage_id
            temp_vendor.save()
            
            print(f"Started Response Approval stage for vendor {vendor_id}")
            
        except Exception as e:
            print(f"Error transitioning lifecycle stages for vendor {vendor_id}: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def get_vendors(self, request):
        """Get list of available vendors for assignment from tprm_integration database"""
        vendors = TempVendor.objects.using('tprm').all()
        vendor_list = [
            {
                'id': vendor.id,
                'vendor_code': vendor.vendor_code,
                'company_name': vendor.company_name,
                'status': vendor.status,
                'risk_level': vendor.risk_level,
                'vendor_category': vendor.vendor_category
            }
            for vendor in vendors
        ]
        return Response(vendor_list)
    
    @action(detail=False, methods=['get'])
    def get_active_questionnaires(self, request):
        """Get list of active questionnaires for assignment from tprm_integration database"""
        questionnaires = Questionnaires.objects.using('tprm').filter(status='ACTIVE')
        questionnaire_list = [
            {
                'questionnaire_id': q.questionnaire_id,
                'questionnaire_name': q.questionnaire_name,
                'questionnaire_type': q.questionnaire_type,
                'description': q.description,
                'question_count': q.questions.count()
            }
            for q in questionnaires
        ]
        return Response(questionnaire_list)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update assignment status"""
        assignment = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['ASSIGNED', 'IN_PROGRESS', 'SUBMITTED', 'RESPONDED', 'COMPLETED', 'OVERDUE']:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assignment.status = new_status
        if new_status in ['SUBMITTED', 'RESPONDED']:
            assignment.submission_date = timezone.now()
        elif new_status == 'COMPLETED':
            assignment.completion_date = timezone.now()
            
            # End Questionnaire Approval and start Response Approval lifecycle stage
            try:
                self._end_questionnaire_approval_start_response_approval(assignment.temp_vendor.id)
            except Exception as e:
                # Don't fail the status update if lifecycle stage update fails
                print(f"Warning: Error updating vendor lifecycle stage on questionnaire completion: {str(e)}")
        
        assignment.save()
        
        from .serializers import QuestionnaireAssignmentSerializer
        serializer = QuestionnaireAssignmentSerializer(assignment)
        return Response(serializer.data)


class QuestionnaireResponseViewSet(VendorAuthenticationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing questionnaire responses with RBAC protection
    """
    queryset = QuestionnaireResponseSubmissions.objects.all().select_related(
        'assignment', 'question', 'assignment__temp_vendor', 'assignment__questionnaire'
    )
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        from .serializers import QuestionnaireResponseSerializer
        return QuestionnaireResponseSerializer
    
    @action(detail=False, methods=['get'])
    def get_vendor_assignments(self, request):
        """Get assignments for a specific vendor from tprm_integration database"""
        vendor_id = request.query_params.get('vendor_id')
        if not vendor_id:
            return Response(
                {'error': 'vendor_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Convert vendor_id to integer
            try:
                vendor_id = int(vendor_id)
            except (ValueError, TypeError):
                return Response(
                    {'error': f'Invalid vendor_id: {vendor_id}. Must be a valid integer.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print(f"[GET_VENDOR_ASSIGNMENTS] Fetching assignments for vendor_id: {vendor_id}")
            
            # Use 'tprm' database to query from tprm_integration
            # Try both temp_vendor_id and temp_vendor__id in case of field name differences
            assignments = QuestionnaireAssignments.objects.using('tprm').filter(
                temp_vendor_id=vendor_id
            ).select_related('questionnaire', 'temp_vendor')
            
            print(f"[GET_VENDOR_ASSIGNMENTS] Found {assignments.count()} assignments for vendor_id: {vendor_id}")
            
            assignment_list = []
            for assignment in assignments:
                try:
                    assignment_data = {
                        'assignment_id': assignment.assignment_id,
                        'questionnaire_id': assignment.questionnaire.questionnaire_id,
                        'questionnaire_name': assignment.questionnaire.questionnaire_name,
                        'status': assignment.status,
                        'assigned_date': assignment.assigned_date.isoformat() if assignment.assigned_date else None,
                        'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                        'vendor_name': assignment.temp_vendor.company_name if assignment.temp_vendor else 'Unknown Vendor'
                    }
                    assignment_list.append(assignment_data)
                except Exception as e:
                    print(f"[GET_VENDOR_ASSIGNMENTS] Error processing assignment {assignment.assignment_id}: {str(e)}")
                    continue
            
            print(f"[GET_VENDOR_ASSIGNMENTS] Returning {len(assignment_list)} assignments")
            return Response(assignment_list)
            
        except Exception as e:
            print(f"[GET_VENDOR_ASSIGNMENTS] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to fetch vendor assignments: {str(e)}'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=False, methods=['get'])
    def get_assignment_responses(self, request):
        """Get responses for a specific assignment"""
        assignment_id = request.query_params.get('assignment_id')
        if not assignment_id:
            return Response(
                {'error': 'assignment_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use 'tprm' database to query from tprm_integration
        assignment = get_object_or_404(QuestionnaireAssignments.objects.using('tprm'), assignment_id=assignment_id)
        questions = assignment.questionnaire.questions.all().order_by('display_order')
        
        # Get existing responses from tprm_integration database
        existing_responses = {
            r.question_id: r for r in 
            QuestionnaireResponseSubmissions.objects.using('tprm').filter(assignment=assignment)
        }
        
        responses_data = []
        for question in questions:
            existing_response = existing_responses.get(question.question_id)
            
            response_data = {
                'id': question.question_id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'is_required': question.is_required,
                'help_text': question.help_text,
                'vendor_response': existing_response.vendor_response if existing_response else '',
                'vendor_comment': existing_response.vendor_comment if existing_response else '',
                'reviewer_comment': existing_response.reviewer_comment if existing_response else '',
                'is_completed': existing_response.is_completed if existing_response else False,
                'options': question.options,
                'uploaded_files': existing_response.file_uploads if existing_response and existing_response.file_uploads else []
            }
            responses_data.append(response_data)
        
        return Response({
            'assignment': {
                'assignment_id': assignment.assignment_id,
                'questionnaire_name': assignment.questionnaire.questionnaire_name,
                'vendor_name': assignment.temp_vendor.company_name,
                'status': assignment.status,
                'due_date': assignment.due_date,
                'submission_date': assignment.submission_date,
                'is_locked': assignment.status in ['SUBMITTED', 'RESPONDED']
            },
            'responses': responses_data
        })
    
    @rbac_vendor_required('SubmitQuestionnaireResponses')
    @action(detail=False, methods=['post'])
    def save_responses(self, request):
        """Save responses for an assignment"""
        assignment_id = request.data.get('assignment_id')
        responses = request.data.get('responses', [])
        
        if not assignment_id:
            return Response(
                {'error': 'assignment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assignment = get_object_or_404(QuestionnaireAssignments, assignment_id=assignment_id)
        
        # Check if assignment is locked (already submitted or responded)
        if assignment.status in ['SUBMITTED', 'RESPONDED']:
            return Response(
                {'error': 'Cannot modify responses for a responded questionnaire'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            for response_data in responses:
                question_id = response_data.get('question_id')
                if not question_id:
                    continue
                
                question = get_object_or_404(QuestionnaireQuestions, question_id=question_id)
                
                response_obj, created = QuestionnaireResponseSubmissions.objects.get_or_create(
                    assignment=assignment,
                    question=question,
                    defaults={
                        'vendor_response': response_data.get('vendor_response', ''),
                        'vendor_comment': response_data.get('vendor_comment', ''),
                        'is_completed': bool(str(response_data.get('vendor_response', '')).strip())
                    }
                )
                
                if not created:
                    response_obj.vendor_response = response_data.get('vendor_response', '')
                    response_obj.vendor_comment = response_data.get('vendor_comment', '')
                    response_obj.is_completed = bool(str(response_data.get('vendor_response', '')).strip())
                    response_obj.save()
            
            # Update assignment status to IN_PROGRESS if user has started filling it out
            # Do NOT set to RESPONDED here - that should only happen in submit_final_responses
            if assignment.status == 'ASSIGNED':
                assignment.status = 'IN_PROGRESS'
                assignment.save()
            
            # Note: We don't automatically set status to RESPONDED here even if all questions are completed
            # The user must explicitly call submit_final_responses to finalize the submission
        
        return Response({'message': 'Responses saved successfully'}, status=status.HTTP_200_OK)
    
    @rbac_vendor_required('SubmitQuestionnaireResponses')
    @action(detail=False, methods=['post'])
    def submit_final_responses(self, request):
        """Submit questionnaire responses as final - locks the assignment"""
        assignment_id = request.data.get('assignment_id')
        if not assignment_id:
            return Response(
                {'error': 'Assignment ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assignment = get_object_or_404(QuestionnaireAssignments, assignment_id=assignment_id)
        
        # Debug logging
        print(f"=== SUBMIT FINAL RESPONSES DEBUG ===")
        print(f"Assignment ID: {assignment_id}")
        print(f"Current Status: {assignment.status}")
        print(f"Submission Date: {assignment.submission_date}")
        print(f"Vendor ID: {assignment.temp_vendor.id if assignment.temp_vendor else 'None'}")
        print(f"Questionnaire ID: {assignment.questionnaire.questionnaire_id if assignment.questionnaire else 'None'}")
        
        # Check if already submitted or responded
        # Only block if status is SUBMITTED/RESPONDED AND there's a submission_date
        # This handles cases where status might be incorrectly set but no actual submission occurred
        if assignment.status in ['SUBMITTED', 'RESPONDED'] and assignment.submission_date:
            print(f"❌ BLOCKED: Assignment already has status {assignment.status} with submission_date {assignment.submission_date}")
            return Response(
                {'error': 'This questionnaire has already been responded'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If status is SUBMITTED/RESPONDED but no submission_date, reset status to allow submission
        # This handles data inconsistency issues
        if assignment.status in ['SUBMITTED', 'RESPONDED'] and not assignment.submission_date:
            print(f"⚠️ Assignment {assignment_id} has status {assignment.status} but no submission_date. Resetting status to IN_PROGRESS.")
            assignment.status = 'IN_PROGRESS'
            assignment.save()
            print(f"✅ Status reset to IN_PROGRESS. Allowing submission to proceed.")
        
        print(f"✅ Proceeding with submission...")
        
        # Validate that all required questions are completed
        required_questions = assignment.questionnaire.questions.filter(is_required=True)
        completed_required = QuestionnaireResponseSubmissions.objects.filter(
            assignment=assignment,
            question__in=required_questions,
            is_completed=True
        ).count()
        
        if completed_required < required_questions.count():
            return Response(
                {'error': 'Please complete all required questions before submitting'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update assignment status and set submission timestamp
        assignment.status = 'RESPONDED'
        assignment.submission_date = timezone.now()
        assignment.save()
        
        print(f"✓ Assignment {assignment_id} status updated to RESPONDED")
        print(f"  Vendor ID: {assignment.temp_vendor.id}")
        print(f"  Submission Date: {assignment.submission_date}")
        
        # End Questionnaire Response and start Response Approval lifecycle stage
        try:
            print(f"Initiating lifecycle stage transition for vendor {assignment.temp_vendor.id}")
            self._end_questionnaire_response_start_response_approval(assignment.temp_vendor.id)
            print(f"✓ Lifecycle stage transition completed successfully")
        except Exception as e:
            # Don't fail the submission process if lifecycle stage update fails
            print(f"ERROR - Failed to update vendor lifecycle stage on questionnaire submission: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return Response({
            'message': 'Questionnaire responded successfully',
            'submission_date': assignment.submission_date,
            'status': assignment.status
        }, status=status.HTTP_200_OK)
    
    def _end_questionnaire_response_start_response_approval(self, vendor_id):
        """End Questionnaire Response stage and start Response Approval stage"""
        try:
            from apps.vendor_core.models import LifecycleTracker, TempVendor
            from apps.vendor_core.views import get_lifecycle_stage_id_by_code
            from django.utils import timezone
            
            print(f"Debug - Starting lifecycle transition for vendor {vendor_id}: Questionnaire Response -> Response Approval")
            current_time = timezone.now()
            
            # Get stage IDs - Questionnaire Response (4) -> Response Approval (5)
            ques_response_stage_id = get_lifecycle_stage_id_by_code('QUES_RES')
            response_approval_stage_id = get_lifecycle_stage_id_by_code('RES_APP')
            
            print(f"Debug - Stage IDs: QUES_RES={ques_response_stage_id}, RES_APP={response_approval_stage_id}")
            
            if not ques_response_stage_id or not response_approval_stage_id:
                print(f"ERROR - Could not find stage IDs for vendor {vendor_id}")
                print(f"  QUES_RES ID: {ques_response_stage_id}")
                print(f"  RES_APP ID: {response_approval_stage_id}")
                return
            
            # End Questionnaire Response stage
            response_stage_entry = LifecycleTracker.objects.filter(
                vendor_id=vendor_id,
                lifecycle_stage=ques_response_stage_id,
                ended_at__isnull=True
            ).first()
            
            if response_stage_entry:
                response_stage_entry.ended_at = current_time
                response_stage_entry.save()
                print(f"✓ Successfully ended Questionnaire Response stage for vendor {vendor_id} at {current_time}")
            else:
                print(f"WARNING - No active Questionnaire Response stage found for vendor {vendor_id}")
                # Check if there are any lifecycle entries for this vendor
                all_entries = LifecycleTracker.objects.filter(vendor_id=vendor_id)
                print(f"Debug - All lifecycle entries for vendor {vendor_id}: {list(all_entries.values('id', 'lifecycle_stage', 'started_at', 'ended_at'))}")
            
            # Start Response Approval stage
            new_entry = LifecycleTracker.objects.create(
                vendor_id=vendor_id,
                lifecycle_stage=response_approval_stage_id,
                started_at=current_time
            )
            print(f"✓ Successfully created Response Approval stage entry (ID: {new_entry.id}) for vendor {vendor_id}")
            
            # Update temp vendor current stage
            try:
                temp_vendor = TempVendor.objects.get(id=vendor_id)
                old_stage = temp_vendor.lifecycle_stage
                temp_vendor.lifecycle_stage = response_approval_stage_id
                temp_vendor.save()
                print(f"✓ Successfully updated temp vendor {vendor_id} lifecycle stage from {old_stage} to {response_approval_stage_id}")
            except TempVendor.DoesNotExist:
                print(f"ERROR - Temp vendor {vendor_id} not found")
            
            print(f"✓ COMPLETED - Successfully transitioned vendor {vendor_id} from Questionnaire Response to Response Approval stage")
            
        except Exception as e:
            print(f"ERROR - Failed to transition lifecycle stages for vendor {vendor_id}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    @action(detail=False, methods=['post'])
    def upload_files(self, request):
        """Upload files for a specific questionnaire question using S3"""
        assignment_id = request.data.get('assignment_id')
        question_id = request.data.get('question_id')
        user_id = request.data.get('user_id', 'default-user')
        
        if not assignment_id or not question_id:
            return Response(
                {'error': 'Assignment ID and Question ID are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the assignment and question
        try:
            assignment = QuestionnaireAssignments.objects.get(assignment_id=assignment_id)
            question = QuestionnaireQuestions.objects.get(question_id=question_id)
        except (QuestionnaireAssignments.DoesNotExist, QuestionnaireQuestions.DoesNotExist):
            return Response(
                {'error': 'Assignment or question not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if question is file upload type
        if question.question_type != 'FILE_UPLOAD':
            return Response(
                {'error': 'This question is not a file upload question'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get file upload configuration from question options
        file_config = {}
        if question.options:
            if isinstance(question.options, str):
                try:
                    options = json.loads(question.options)
                    file_config = options.get('file', {})
                except json.JSONDecodeError:
                    file_config = {}
            elif isinstance(question.options, dict):
                file_config = question.options.get('file', {})
        
        # Get files from request
        files = request.FILES.getlist('files')
        if not files:
            return Response(
                {'error': 'No files provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get existing response submission
        response_submission, created = QuestionnaireResponseSubmissions.objects.get_or_create(
            assignment=assignment,
            question=question,
            defaults={
                'vendor_response': '',
                'vendor_comment': '',
                'is_completed': False,
                'file_uploads': []
            }
        )
        
        # Get existing uploaded files
        existing_files = response_submission.file_uploads or []
        existing_file_count = len(existing_files)
        
        # Validate file count limit
        max_files = file_config.get('maxFiles', 1)
        if existing_file_count + len(files) > max_files:
            return Response(
                {'error': f'Maximum {max_files} file(s) allowed. Currently have {existing_file_count}, trying to add {len(files)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size and type
        max_size_mb = file_config.get('maxSize', 10)
        allowed_types = file_config.get('allowedTypes', '')
        max_size_bytes = max_size_mb * 1024 * 1024
        
        uploaded_s3_files = []
        
        try:
            # Initialize S3 client
            s3_client = create_direct_mysql_client()
            
            for file in files:
                # Validate file size
                if file.size > max_size_bytes:
                    return Response(
                        {'error': f'File {file.name} exceeds maximum size of {max_size_mb}MB'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate file type
                if allowed_types:
                    file_extension = file.name.split('.')[-1].lower() if '.' in file.name else ''
                    allowed_extensions = [ext.strip().lower() for ext in allowed_types.split(',')]
                    if file_extension not in allowed_extensions:
                        return Response(
                            {'error': f'File type .{file_extension} not allowed. Allowed types: {allowed_types}'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file.name.split(".")[-1]}' if '.' in file.name else '') as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                
                try:
                    # Upload to S3
                    upload_result = s3_client.upload(
                        file_path=temp_file_path,
                        user_id=user_id,
                        custom_file_name=file.name
                    )
                    
                    if upload_result.get('success'):
                        file_info = upload_result['file_info']
                        
                        # Save to S3Files table
                        s3_file = S3Files.objects.create(
                            url=file_info['url'],
                            file_type=file_info.get('fileType', ''),
                            file_name=file_info.get('storedName', file.name),
                            user_id=user_id,
                            metadata={
                                'original_name': file.name,
                                'file_size': file.size,
                                'content_type': file.content_type,
                                's3_key': file_info.get('s3Key', ''),
                                's3_bucket': file_info.get('bucket', ''),
                                'questionnaire_assignment_id': assignment_id,
                                'question_id': question_id,
                                'upload_result': upload_result
                            }
                        )
                        
                        # Add to uploaded files list
                        uploaded_s3_files.append({
                            's3_file_id': s3_file.id,
                            'original_name': file.name,
                            'stored_name': file_info.get('storedName', file.name),
                            'file_size': file.size,
                            'content_type': file.content_type,
                            's3_url': file_info['url'],
                            's3_key': file_info.get('s3Key', ''),
                            'uploaded_at': s3_file.uploaded_at.isoformat()
                        })
                        
                    else:
                        return Response(
                            {'error': f'Failed to upload {file.name}: {upload_result.get("error", "Unknown error")}'}, 
                            status=status.HTTP_200_OK
                        )
                        
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
            
            # Update response submission with uploaded files
            all_files = existing_files + uploaded_s3_files
            response_submission.file_uploads = all_files
            response_submission.vendor_response = ', '.join([f['original_name'] for f in all_files])
            response_submission.is_completed = len(all_files) > 0
            response_submission.save()
            
            return Response({
                'success': True,
                'message': f'Successfully uploaded {len(uploaded_s3_files)} file(s)',
                'uploaded_files': uploaded_s3_files,
                'total_files': len(all_files),
                'storage_method': 'S3'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'}, 
                status=status.HTTP_200_OK
            )
    
    @action(detail=False, methods=['delete'])
    def remove_file(self, request):
        """Remove a file from a questionnaire response"""
        assignment_id = request.data.get('assignment_id')
        question_id = request.data.get('question_id')
        s3_file_id = request.data.get('s3_file_id')
        
        if not all([assignment_id, question_id, s3_file_id]):
            return Response(
                {'error': 'Assignment ID, Question ID, and S3 File ID are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the response submission
            response_submission = QuestionnaireResponseSubmissions.objects.get(
                assignment__assignment_id=assignment_id,
                question__question_id=question_id
            )
            
            # Get the S3 file
            s3_file = S3Files.objects.get(id=s3_file_id)
            
            # Remove file from the file_uploads list
            if response_submission.file_uploads:
                updated_files = [f for f in response_submission.file_uploads if f.get('s3_file_id') != s3_file_id]
                response_submission.file_uploads = updated_files
                response_submission.vendor_response = ', '.join([f['original_name'] for f in updated_files])
                response_submission.is_completed = len(updated_files) > 0
                response_submission.save()
            
            # Delete the S3 file record (optional - you might want to keep it for audit purposes)
            # s3_file.delete()
            
            return Response({
                'success': True,
                'message': 'File removed successfully',
                'remaining_files': len(response_submission.file_uploads or [])
            }, status=status.HTTP_200_OK)
            
        except QuestionnaireResponseSubmissions.DoesNotExist:
            return Response(
                {'error': 'Response submission not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except S3Files.DoesNotExist:
            return Response(
                {'error': 'File not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to remove file: {str(e)}'}, 
                status=status.HTTP_200_OK
            )
