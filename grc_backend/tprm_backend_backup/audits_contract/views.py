"""
Views for the Audits app with JWT Authentication.
"""
import logging
import jwt
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

# Use Unified JWT Authentication from GRC
from grc.jwt_auth import UnifiedJWTAuthentication
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta

from .models import ContractAudit, ContractStaticQuestionnaire, ContractAuditVersion, ContractAuditFinding, ContractAuditReport
from .serializers import (
    ContractAuditSerializer, ContractAuditCreateSerializer, ContractAuditListSerializer,
    ContractAuditUpdateSerializer, ContractStaticQuestionnaireSerializer, ContractAuditVersionSerializer, 
    ContractAuditFindingSerializer, ContractAuditReportSerializer
)
from tprm_backend.contracts.models import VendorContract, ContractTerm

import re
def _normalize_term_id(term_id):
    if term_id is None:
        return ''
    return str(term_id).strip()


def _strip_term_prefix(value):
    if value.startswith('term_'):
        return value[5:]
    return value


def _strip_numeric_suffix(value):
    return re.sub(r'_[0-9]+$', '', value)


def _generate_term_variants(term_id):
    variants = set()
    value = _normalize_term_id(term_id)
    if not value:
        return variants

    lower_value = value.lower()
    variants.add(value)
    variants.add(lower_value)

    base = _strip_term_prefix(lower_value)
    variants.add(base)
    variants.add(base.replace('_', '.'))
    variants.add(base.replace('.', '_'))

    base_no_suffix = _strip_numeric_suffix(base)
    variants.add(base_no_suffix)
    variants.add(base_no_suffix.replace('_', '.'))
    variants.add(base_no_suffix.replace('.', '_'))

    if base.startswith('17'):
        without_17 = base[2:]
        variants.add(without_17)
        variants.add(_strip_numeric_suffix(without_17))
        variants.add(f'term_{without_17}')
        variants.add(f'term_{_strip_numeric_suffix(without_17)}')

    prefixed_variants = {f'term_{_strip_numeric_suffix(v)}' for v in variants if v}
    variants.update(prefixed_variants)

    return {v for v in variants if v}


logger = logging.getLogger(__name__)


class SimpleAuthenticatedPermission(BasePermission):
    """Custom permission class that checks for authenticated users"""
    def has_permission(self, request, view):
        # Just check if user object exists and is authenticated
        # UnifiedJWTAuthentication handles GRC/TPRM user verification
        if request.user and hasattr(request.user, 'is_authenticated'):
            return request.user.is_authenticated
        return False



class ContractAuditListView(generics.ListCreateAPIView):
    """List and create contract audits."""
    queryset = ContractAudit.objects.all()
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'audit_type', 'frequency', 'auditor_id', 'reviewer_id', 'contract']
    search_fields = ['title', 'scope']
    ordering_fields = ['due_date', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ContractAuditCreateSerializer
        return ContractAuditListSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create method to provide better error handling."""
        try:
            print(f"Received audit creation request: {request.data}")
            return super().create(request, *args, **kwargs)
        except Exception as e:
            print(f"Error creating audit: {e}")
            return Response(
                {'error': str(e), 'details': 'Failed to create audit'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ContractAuditDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete contract audit."""
    queryset = ContractAudit.objects.all()
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ContractAuditUpdateSerializer
        return ContractAuditSerializer
    
    def update(self, request, *args, **kwargs):
        """Override update method to provide better error handling."""
        try:
            print(f"Received audit update request: {request.data}")
            print(f"Audit ID: {kwargs.get('pk')}")
            print(f"Request method: {request.method}")
            
            # Validate the data first
            serializer = self.get_serializer(data=request.data, partial=True)
            if not serializer.is_valid():
                print(f"Serializer validation errors: {serializer.errors}")
                return Response({
                    'error': 'Validation failed',
                    'details': serializer.errors,
                    'received_data': request.data
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return super().update(request, *args, **kwargs)
        except Exception as e:
            print(f"Error updating audit: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {'error': str(e), 'details': 'Failed to update audit'},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def start_audit(request, audit_id):
    """Start an audit by changing status to in_progress."""
    try:
        audit = get_object_or_404(ContractAudit, audit_id=audit_id)
        
        # Check if audit is in 'created' status
        if audit.status != 'created':
            return Response(
                {'error': f'Audit can only be started when status is "created". Current status: {audit.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update audit status to in_progress
        audit.status = 'in_progress'
        audit.save()
        
        print(f"Audit {audit_id} started - status changed to in_progress")
        
        return Response({
            'success': True,
            'message': f'Audit "{audit.title}" has been started successfully.',
            'audit': ContractAuditSerializer(audit).data
        })
        
    except Exception as e:
        print(f"Error starting audit {audit_id}: {e}")
        return Response(
            {'error': str(e), 'details': 'Failed to start audit'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ContractStaticQuestionnaireListView(generics.ListCreateAPIView):
    """List and create contract static questionnaires."""
    queryset = ContractStaticQuestionnaire.objects.all()
    serializer_class = ContractStaticQuestionnaireSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['term_id', 'question_type', 'is_required']


class ContractStaticQuestionnaireDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete contract static questionnaire."""
    queryset = ContractStaticQuestionnaire.objects.all()
    serializer_class = ContractStaticQuestionnaireSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]


class ContractAuditVersionListView(generics.ListCreateAPIView):
    """List and create contract audit versions."""
    queryset = ContractAuditVersion.objects.all()
    serializer_class = ContractAuditVersionSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'version_type', 'approval_status', 'user_id']
    ordering_fields = ['date_created', 'created_at']
    ordering = ['-created_at']


class ContractAuditVersionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete contract audit version."""
    queryset = ContractAuditVersion.objects.all()
    serializer_class = ContractAuditVersionSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]


class ContractAuditFindingListView(generics.ListCreateAPIView):
    """List and create contract audit findings."""
    queryset = ContractAuditFinding.objects.all()
    serializer_class = ContractAuditFindingSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'term_id', 'user_id']
    ordering_fields = ['check_date', 'created_at']
    ordering = ['-created_at']
    
    def list(self, request, *args, **kwargs):
        """Override list method to add debugging."""
        try:
            print(f"🔍 Listing audit findings with params: {request.query_params}")
            print(f"🔍 Audit ID filter: {request.query_params.get('audit_id')}")
            
            # Get the filtered queryset
            queryset = self.filter_queryset(self.get_queryset())
            print(f"🔍 Filtered queryset count: {queryset.count()}")
            
            # Get the results
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                print(f"🔍 Paginated results count: {len(serializer.data)}")
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            print(f"🔍 Serialized results count: {len(serializer.data)}")
            if serializer.data:
                first_result = serializer.data[0]
                print(f"🔍 First result sample: {first_result}")
                if 'questionnaire_responses' in first_result:
                    print(f"🔍 Questionnaire responses in first result: {first_result['questionnaire_responses']}")
            
            return Response(serializer.data)
            
        except Exception as e:
            print(f"❌ Error in list method: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Override create method to provide better error handling and logging."""
        try:
            print(f"📝 Creating audit finding with data: {request.data}")
            print(f"📝 Audit ID: {request.data.get('audit_id')}")
            print(f"📝 Term ID: {request.data.get('term_id')}")
            print(f"📝 User ID: {request.data.get('user_id')}")
            print(f"📝 Check Date: {request.data.get('check_date')}")
            print(f"📝 Evidence: {request.data.get('evidence')}")
            print(f"📝 How to Verify: {request.data.get('how_to_verify')}")
            print(f"📝 Impact Recommendations: {request.data.get('impact_recommendations')}")
            print(f"📝 Details of Finding: {request.data.get('details_of_finding')}")
            print(f"📝 Comment: {request.data.get('comment')}")
            print(f"📝 Questionnaire Responses: {request.data.get('questionnaire_responses')}")
            
            # Validate required fields
            required_fields = ['audit_id', 'term_id', 'evidence', 'user_id', 'how_to_verify', 
                             'impact_recommendations', 'details_of_finding', 'check_date']
            
            missing_fields = [field for field in required_fields if not request.data.get(field)]
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return Response({
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}',
                    'details': 'All required fields must be provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            response = super().create(request, *args, **kwargs)
            print(f"✅ Audit finding created successfully with ID: {response.data.get('finding_id', 'unknown')}")
            
            # Wrap response to match frontend expectations
            return Response({
                'success': True,
                'data': response.data,
                'message': 'Audit finding created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ Error creating audit finding: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': str(e),
                'details': 'Failed to create audit finding'
            }, status=status.HTTP_400_BAD_REQUEST)


class ContractAuditFindingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete contract audit finding."""
    queryset = ContractAuditFinding.objects.all()
    serializer_class = ContractAuditFindingSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]


class ContractAuditReportListView(generics.ListCreateAPIView):
    """List and create contract audit reports."""
    queryset = ContractAuditReport.objects.all()
    serializer_class = ContractAuditReportSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['audit_id', 'contract_id', 'term_id']
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']


class ContractAuditReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete contract audit report."""
    queryset = ContractAuditReport.objects.all()
    serializer_class = ContractAuditReportSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def contract_audit_dashboard_stats(request):
    """Get contract audit dashboard statistics."""
    total_audits = ContractAudit.objects.count()
    active_audits = ContractAudit.objects.filter(status__in=['created', 'in_progress']).count()
    completed_audits = ContractAudit.objects.filter(status='completed').count()
    overdue_audits = ContractAudit.objects.filter(
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
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def available_contracts(request):
    """Get available contracts for audit creation."""
    contracts = VendorContract.objects.select_related('vendor')
    
    contract_data = []
    for contract in contracts:
        terms_count = ContractTerm.objects.filter(contract_id=contract.contract_id).count()
        contract_data.append({
            'contract_id': contract.contract_id,
            'contract_title': contract.contract_title,
            'contract_type': getattr(contract, 'contract_type', 'Unknown'),
            'vendor_name': contract.vendor.company_name if contract.vendor else 'Unknown',
            'vendor_id': contract.vendor.vendor_id if contract.vendor else None,
            'start_date': getattr(contract, 'start_date', None),
            'end_date': getattr(contract, 'end_date', None),
            'status': getattr(contract, 'status', 'Active'),
            'terms_count': terms_count
        })
    
    return Response(contract_data)


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def contract_terms(request, contract_id):
    """Get terms for a specific contract."""
    try:
        contract = VendorContract.objects.get(contract_id=contract_id)
        terms = ContractTerm.objects.filter(contract_id=contract_id)
        
        terms_data = []
        for term in terms:
            terms_data.append({
                'term_id': term.term_id,
                'term_title': term.term_title,
                'term_type': term.term_category,
                'description': term.term_text,
                'compliance_requirement': term.compliance_status,
                'penalty_clause': '',  # Not available in current model
                'monitoring_frequency': 'Monthly',  # Default value since not in model
            })
        
        return Response({
            'contract': {
                'contract_id': contract.contract_id,
                'contract_title': contract.contract_title,
                'vendor_name': contract.vendor.company_name if contract.vendor else 'Unknown',
            },
            'terms': terms_data
        })
        
    except VendorContract.DoesNotExist:
        return Response(
            {'error': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def questionnaires_by_term_title(request):
    """Get questionnaires for terms matching by term_category or term_title.
    
    This endpoint finds terms in contract_terms by term_category (preferred) or term_title, 
    then returns questionnaires from contract_static_questionnaires that match those term_ids.
    """
    try:
        term_category = request.query_params.get('term_category', None)
        term_title = request.query_params.get('term_title', None)
        term_id = request.query_params.get('term_id', None)
        
        if not term_category and not term_title and not term_id:
            return Response(
                {'error': 'Either term_category, term_title, or term_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find matching term_ids in contract_terms
        if term_id:
            # Direct lookup by term_id
            matching_term_ids = [term_id]
            # Also get term_category if available for additional matching
            try:
                term_obj = ContractTerm.objects.filter(term_id=term_id).first()
                if term_obj:
                    term_category = term_obj.term_category
                    term_title = term_obj.term_title
            except:
                pass
        elif term_category:
            # Find by term_category (case-insensitive match) - PREFERRED METHOD
            matching_terms = ContractTerm.objects.filter(
                term_category__iexact=term_category
            )
            matching_term_ids = list(matching_terms.values_list('term_id', flat=True))
            logger.info(f"Found {len(matching_term_ids)} terms with category '{term_category}': {matching_term_ids}")
            
            # Also try to find questionnaires by looking up their term_ids in contract_terms
            # This handles cases where questionnaires might be linked to terms we haven't found yet
            # Get all unique term_ids from questionnaires that might match
            all_questionnaire_term_ids = ContractStaticQuestionnaire.objects.values_list('term_id', flat=True).distinct()
            logger.info(f"Total unique term_ids in questionnaires: {len(all_questionnaire_term_ids)}")
            
            # For each questionnaire term_id, check if it belongs to a term with matching category
            additional_term_ids = []
            for q_term_id in all_questionnaire_term_ids:
                try:
                    # Try to find a term with this term_id that has the matching category
                    term_with_category = ContractTerm.objects.filter(
                        term_id=q_term_id,
                        term_category__iexact=term_category
                    ).first()
                    if term_with_category:
                        additional_term_ids.append(q_term_id)
                        logger.info(f"Found questionnaire term_id '{q_term_id}' linked to term with category '{term_category}'")
                except Exception as e:
                    logger.debug(f"Error checking term_id {q_term_id}: {e}")
            
            # Add any additional term_ids we found
            if additional_term_ids:
                matching_term_ids.extend(additional_term_ids)
                matching_term_ids = list(set(matching_term_ids))  # Remove duplicates
                logger.info(f"Total matching term_ids after checking questionnaires: {len(matching_term_ids)}")
        else:
            # Fallback to term_title (case-insensitive match)
            matching_terms = ContractTerm.objects.filter(
                term_title__iexact=term_title
            )
            matching_term_ids = list(matching_terms.values_list('term_id', flat=True))
        
        # If no matching terms found in DB, but we have term_id or term_category,
        # still try to match questionnaires directly by term_id (for unsaved terms)
        if not matching_term_ids:
            logger.info(f"No terms found in DB for term_category: {term_category}, term_id: {term_id}")
            # If term_id is provided, try to match questionnaires directly by term_id
            # This handles the case where terms haven't been saved to DB yet
            if term_id:
                logger.info(f"Attempting to match questionnaires directly by term_id: {term_id}")
                # Build term_id variations
                tid_str = str(term_id)
                term_id_variations = [
                    tid_str,
                    f'term_{tid_str}',
                    f'term_17{tid_str}'
                ]
                if tid_str.startswith('term_'):
                    numeric_part = tid_str.replace('term_', '')
                    if numeric_part.startswith('17'):
                        numeric_part = numeric_part[2:]
                    term_id_variations.extend([numeric_part, f'term_{numeric_part}'])
                
                # Try to find questionnaires with matching term_id
                questionnaires_by_term_id = ContractStaticQuestionnaire.objects.filter(
                    term_id__in=term_id_variations
                ) | ContractStaticQuestionnaire.objects.filter(
                    term_id__iendswith=tid_str
                ) | ContractStaticQuestionnaire.objects.filter(
                    term_id__icontains=tid_str
                )
                
                if questionnaires_by_term_id.exists():
                    logger.info(f"Found {questionnaires_by_term_id.count()} questionnaires by direct term_id match")
                    serializer = ContractStaticQuestionnaireSerializer(questionnaires_by_term_id.distinct().order_by('question_id'), many=True)
                    return Response({
                        'term_category': term_category,
                        'term_title': term_title,
                        'term_ids': [term_id],
                        'questionnaires': serializer.data,
                        'count': len(serializer.data),
                        'message': f'Found questionnaires by direct term_id match (term not yet saved to DB)'
                    })
            
            # If no questionnaires found by term_id, return empty but don't error
            logger.info("No questionnaires found for unsaved term")
            return Response({
                'term_category': term_category,
                'term_title': term_title,
                'term_id': term_id,
                'questionnaires': [],
                'message': f'No terms found in DB matching term_category: {term_category or "N/A"} or term_id: {term_id or "N/A"}. Term may not be saved yet.'
            })
        
        # Build a list of all possible term_id formats to match
        # This handles format differences like:
        # - contract_terms: "9752260.987479"
        # - questionnaires: "term_1759752260.987479"
        all_possible_term_ids = []
        for tid in matching_term_ids:
            tid_str = str(tid)
            all_possible_term_ids.append(tid_str)
            # Add variations with "term_" prefix
            if not tid_str.startswith('term_'):
                all_possible_term_ids.append(f'term_{tid_str}')
                # Also try with "17" prefix (common in the data)
                all_possible_term_ids.append(f'term_17{tid_str}')
            # Try extracting numeric part from questionnaire format
            if tid_str.startswith('term_'):
                # Extract numeric part after "term_"
                numeric_part = tid_str.replace('term_', '')
                if numeric_part.startswith('17'):
                    # Remove "17" prefix if present
                    numeric_part = numeric_part[2:]
                all_possible_term_ids.append(numeric_part)
                all_possible_term_ids.append(f'term_{numeric_part}')
        
        # Get questionnaires using multiple matching strategies
        # 1. Exact match with term_ids
        questionnaires_exact = ContractStaticQuestionnaire.objects.filter(
            term_id__in=all_possible_term_ids
        )
        logger.info(f"Found {questionnaires_exact.count()} questionnaires by exact term_id match")
        
        # 2. Partial match - if term_id in questionnaires contains the term_id from contract_terms
        # This handles cases where questionnaire term_id is "term_1759752260.987479" 
        # and contract_terms term_id is "9752260.987479"
        # We check if the questionnaire term_id ends with the contract term_id
        questionnaires_partial = ContractStaticQuestionnaire.objects.none()
        for tid in matching_term_ids:
            tid_str = str(tid)
            # Match if questionnaire term_id ends with the contract term_id (most common case)
            # or contains it as a substring (for other variations)
            questionnaires_partial = questionnaires_partial | ContractStaticQuestionnaire.objects.filter(
                term_id__iendswith=tid_str
            ) | ContractStaticQuestionnaire.objects.filter(
                term_id__icontains=tid_str
            )
        logger.info(f"Found {questionnaires_partial.count()} questionnaires by partial term_id match")
        
        # 3. Direct lookup: Find questionnaires whose term_id exists in contract_terms with matching category
        # This is the most reliable method - it directly links questionnaires to terms by category
        if term_category:
            # Get all term_ids from contract_terms that have this category
            category_term_ids = list(ContractTerm.objects.filter(
                term_category__iexact=term_category
            ).values_list('term_id', flat=True))
            
            # Build all possible variations of these term_ids
            category_term_id_variations = []
            for tid in category_term_ids:
                tid_str = str(tid)
                category_term_id_variations.append(tid_str)
                if not tid_str.startswith('term_'):
                    category_term_id_variations.append(f'term_{tid_str}')
                    category_term_id_variations.append(f'term_17{tid_str}')
                if tid_str.startswith('term_'):
                    numeric_part = tid_str.replace('term_', '')
                    if numeric_part.startswith('17'):
                        numeric_part = numeric_part[2:]
                    category_term_id_variations.append(numeric_part)
                    category_term_id_variations.append(f'term_{numeric_part}')
            
            # Find questionnaires with any of these term_ids
            questionnaires_by_category = ContractStaticQuestionnaire.objects.filter(
                term_id__in=category_term_id_variations
            )
            logger.info(f"Found {questionnaires_by_category.count()} questionnaires by category lookup (term_ids: {category_term_ids[:5]}...)")
            
            # Also try reverse lookup: for each questionnaire term_id, check if it's in contract_terms with this category
            all_q_term_ids = set(ContractStaticQuestionnaire.objects.values_list('term_id', flat=True).distinct())
            matching_q_term_ids = []
            for q_term_id in all_q_term_ids:
                if ContractTerm.objects.filter(term_id=q_term_id, term_category__iexact=term_category).exists():
                    matching_q_term_ids.append(q_term_id)
            
            if matching_q_term_ids:
                questionnaires_by_category_reverse = ContractStaticQuestionnaire.objects.filter(
                    term_id__in=matching_q_term_ids
                )
                logger.info(f"Found {questionnaires_by_category_reverse.count()} questionnaires by reverse category lookup")
                questionnaires_by_category = questionnaires_by_category | questionnaires_by_category_reverse
        else:
            questionnaires_by_category = ContractStaticQuestionnaire.objects.none()
        
        # Combine all queries and remove duplicates
        questionnaires = (
            questionnaires_exact | 
            questionnaires_partial | 
            questionnaires_by_category
        ).distinct().order_by('question_id')
        
        logger.info(f"Total unique questionnaires found: {questionnaires.count()}")
        
        serializer = ContractStaticQuestionnaireSerializer(questionnaires, many=True)
        
        logger.info(f"Found {len(serializer.data)} questionnaires for {len(matching_term_ids)} matching term_ids")
        
        return Response({
            'term_category': term_category,
            'term_title': term_title,
            'term_ids': matching_term_ids,
            'questionnaires': serializer.data,
            'count': len(serializer.data)
        })
        
    except Exception as e:
        logger.error(f"Error getting questionnaires by term_title: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def questionnaires_by_term_ids(request):
    """Get questionnaires grouped by exact term_ids (with minimal normalization)."""
    try:
        term_ids_param = request.query_params.get('term_ids')
        if not term_ids_param:
            return Response(
                {'error': 'term_ids parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        term_ids_raw = [
            _normalize_term_id(term_id)
            for term_id in term_ids_param.split(',')
            if _normalize_term_id(term_id)
        ]

        if not term_ids_raw:
            return Response(
                {'error': 'No valid term_ids provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        variant_map = {term_id: _generate_term_variants(term_id) for term_id in term_ids_raw}
        search_ids = set()
        for variants in variant_map.values():
            search_ids.update(variants)

        questionnaires_queryset = ContractStaticQuestionnaire.objects.filter(
            term_id__in=list(search_ids)
        )

        serialized_questionnaires = ContractStaticQuestionnaireSerializer(
            questionnaires_queryset,
            many=True
        ).data

        grouped_questionnaires = {term_id: [] for term_id in term_ids_raw}

        for questionnaire in serialized_questionnaires:
            questionnaire_term = _normalize_term_id(questionnaire.get('term_id', '')).lower()
            for original_term_id, variants in variant_map.items():
                if questionnaire_term in {variant.lower() for variant in variants}:
                    grouped_questionnaires[original_term_id].append(questionnaire)

        return Response({
            'success': True,
            'data': {
                'term_ids': term_ids_raw,
                'questionnaires': grouped_questionnaires
            }
        })

    except Exception as e:
        logger.error(f"Error fetching questionnaires by term IDs: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def templates_by_term(request):
    """Get questionnaire templates for terms matching by term_category or term_id.
    
    This endpoint finds templates in questionnaire_templates that have questions
    matching the given term_category or term_id.
    """
    try:
        from tprm_backend.bcpdrp.models import QuestionnaireTemplate
        
        term_category = request.query_params.get('term_category', None)
        term_title = request.query_params.get('term_title', None)
        term_id = request.query_params.get('term_id', None)
        
        if not term_category and not term_title and not term_id:
            return Response(
                {'error': 'Either term_category, term_title, or term_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find matching templates
        templates = QuestionnaireTemplate.objects.filter(
            module_type='CONTRACT',
            is_active=True
        )
        
        matching_templates = []
        term_id_str = str(term_id) if term_id else None
        
        # Get all term_ids with matching term_category for efficient lookup
        matching_term_ids_by_category = []
        if term_category:
            try:
                matching_term_ids_by_category = list(ContractTerm.objects.filter(
                    term_category__iexact=term_category
                ).values_list('term_id', flat=True))
                logger.info(f"Found {len(matching_term_ids_by_category)} terms with category '{term_category}'")
            except Exception as e:
                logger.debug(f"Error fetching terms by category: {e}")
        
        # Prioritize term_category matching when provided
        for template in templates:
            questions = template.template_questions_json or []
            if not questions:
                continue
            
            # Check if any question matches the term criteria
            matches = False
            matched_by_category = False
            
            # First, prioritize term_category matching if provided
            if term_category:
                for question in questions:
                    # PRIMARY METHOD: Check term_category field directly (most reliable)
                    q_term_category = question.get('term_category', '')
                    if q_term_category and q_term_category.lower() == term_category.lower():
                        matches = True
                        matched_by_category = True
                        break
                    
                    # SECONDARY METHOD: Check question_category field (may contain term_category)
                    q_question_category = question.get('question_category', '')
                    if q_question_category and q_question_category.lower() == term_category.lower():
                        matches = True
                        matched_by_category = True
                        break
                    
                    # TERTIARY METHOD: Check if question's term_id belongs to a term with matching category
                    q_term_id = str(question.get('term_id', ''))
                    if q_term_id and matching_term_ids_by_category:
                        # Build term_id variations for matching
                        term_id_variations = [q_term_id]
                        if not q_term_id.startswith('term_'):
                            term_id_variations.append(f'term_{q_term_id}')
                            term_id_variations.append(f'term_17{q_term_id}')
                        
                        # Check if any variation matches a term with the category
                        for matching_term_id in matching_term_ids_by_category:
                            matching_term_id_str = str(matching_term_id)
                            for variation in term_id_variations:
                                if (variation == matching_term_id_str or 
                                    variation.endswith(matching_term_id_str) or 
                                    matching_term_id_str.endswith(variation)):
                                    matches = True
                                    matched_by_category = True
                                    break
                            if matches:
                                break
                        if matches:
                            break
            
            # If no category match and term_id is provided, try term_id matching
            if not matches and term_id_str:
                for question in questions:
                    q_term_id = str(question.get('term_id', ''))
                    # Match by term_id (exact or partial)
                    if (q_term_id == term_id_str or 
                        q_term_id.endswith(term_id_str) or 
                        term_id_str.endswith(q_term_id) or
                        q_term_id in term_id_str or
                        term_id_str in q_term_id):
                        matches = True
                        break
            
            # If still no match and term_title is provided, try term_title lookup
            if not matches and term_title:
                try:
                    term_obj = ContractTerm.objects.filter(term_title__iexact=term_title).first()
                    if term_obj:
                        term_obj_id_str = str(term_obj.term_id)
                        # Also check if term has matching category
                        if term_obj.term_category and term_category:
                            if term_obj.term_category.lower() == term_category.lower():
                                # Try to match by category in questions
                                for question in questions:
                                    q_term_category = question.get('question_category', '')
                                    if q_term_category and q_term_category.lower() == term_category.lower():
                                        matches = True
                                        matched_by_category = True
                                        break
                        
                        # If no category match, try term_id
                        if not matches:
                            for question in questions:
                                q_term_id = str(question.get('term_id', ''))
                                if (q_term_id == term_obj_id_str or 
                                    q_term_id.endswith(term_obj_id_str) or 
                                    term_obj_id_str.endswith(q_term_id)):
                                    matches = True
                                    break
                except Exception as e:
                    logger.debug(f"Error checking term_title: {e}")
                    pass
            
            if matches:
                # Count questions for display purposes
                # If template matched (has at least one question matching criteria), show total question count
                # The filtering by category/term_id happens when actually viewing/using questions via template_questions endpoint
                # This ensures the count reflects all questions available in the template
                question_count = len(questions)
                
                matching_templates.append({
                    'template_id': template.template_id,
                    'template_name': template.template_name,
                    'template_description': template.template_description,
                    'template_version': template.template_version,
                    'status': template.status,
                    'question_count': question_count,
                    'matched_by_category': matched_by_category,
                    'created_at': template.created_at.isoformat() if template.created_at else None,
                    'updated_at': template.updated_at.isoformat() if template.updated_at else None,
                })
        
        logger.info(f"Found {len(matching_templates)} templates for term_category: {term_category}, term_id: {term_id}")
        
        return Response({
            'term_category': term_category,
            'term_title': term_title,
            'term_id': term_id,
            'templates': matching_templates,
            'count': len(matching_templates)
        })
        
    except Exception as e:
        logger.error(f"Error getting templates by term: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def template_questions(request, template_id):
    """Get questions from a specific questionnaire template."""
    try:
        from tprm_backend.bcpdrp.models import QuestionnaireTemplate
        
        try:
            template = QuestionnaireTemplate.objects.get(
                template_id=template_id,
                module_type='CONTRACT'
            )
        except QuestionnaireTemplate.DoesNotExist:
            return Response(
                {'error': f'Template with ID {template_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        questions = template.template_questions_json or []
        
        # Filter questions by term_id or term_category if provided
        # IMPORTANT: When a template is selected, we return ALL questions from that template
        # The filtering is only for display/narrowing purposes, not for exclusion
        term_id = request.query_params.get('term_id', None)
        term_category = request.query_params.get('term_category', None)
        
        # If no filters provided, return all questions from template
        if not term_id and not term_category:
            filtered_questions = questions
        else:
            # When filters are provided, still return ALL questions from the template
            # The template was selected, so all its questions should be available
            # Filtering is only for informational purposes (to show which questions match)
            filtered_questions = questions
        
        return Response({
            'template_id': template.template_id,
            'template_name': template.template_name,
            'questions': filtered_questions,
            'count': len(filtered_questions)
        })
        
    except Exception as e:
        logger.error(f"Error getting template questions: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def available_users(request):
    """Get all available users for auditor and reviewer assignment."""
    # RBAC import removed - functionality preserved
    from django.db import connections
    
    try:
        # Get all active users from the users table
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT UserId, UserName, Email, FirstName, LastName, DepartmentId, IsActive
                FROM users 
                WHERE IsActive = 'Y' OR IsActive = '1' OR IsActive = 'true'
                ORDER BY FirstName, LastName
            """)
            
            users_data = []
            for row in cursor.fetchall():
                user_id, username, email, first_name, last_name, dept_id, is_active = row
                
                # Combine first and last name
                full_name = f"{first_name or ''} {last_name or ''}".strip()
                if not full_name:
                    full_name = username or f"User {user_id}"
                
                # RBAC removed - using default role assignment
                role = 'user'  # Default role for all users
                
                users_data.append({
                    'user_id': user_id,
                    'name': full_name,
                    'email': email or f"user{user_id}@example.com",
                    'role': role,
                    'department': f"Department {dept_id}" if dept_id else "Unknown",
                    'username': username
                })
            
            return Response(users_data)
            
    except Exception as e:
        # Fallback to mock data if database connection fails
        print(f"Error connecting to tprm_integration: {e}")
        users_data = [
            {
                'user_id': 1,
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'role': 'auditor',
                'department': 'IT',
                'username': 'johndoe'
            },
            {
                'user_id': 2,
                'name': 'Jane Smith',
                'email': 'jane.smith@example.com',
                'role': 'reviewer',
                'department': 'Compliance',
                'username': 'janesmith'
            },
            {
                'user_id': 3,
                'name': 'Mike Johnson',
                'email': 'mike.johnson@example.com',
                'role': 'auditor',
                'department': 'IT',
                'username': 'mikejohnson'
            },
            {
                'user_id': 4,
                'name': 'Sarah Wilson',
                'email': 'sarah.wilson@example.com',
                'role': 'reviewer',
                'department': 'Compliance',
                'username': 'sarahwilson'
            },
            {
                'user_id': 5,
                'name': 'David Brown',
                'email': 'david.brown@example.com',
                'role': 'user',
                'department': 'Finance',
                'username': 'davidbrown'
            },
            {
                'user_id': 6,
                'name': 'Lisa Davis',
                'email': 'lisa.davis@example.com',
                'role': 'user',
                'department': 'HR',
                'username': 'lisadavis'
            }
        ]
        return Response(users_data)


@api_view(['POST'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def submit_contract_audit_response(request, audit_id):
    """Submit responses for a contract audit."""
    try:
        audit = ContractAudit.objects.get(audit_id=audit_id)
        
        # For now, just update the audit status
        # In a full implementation, you would handle questionnaire responses here
        audit.status = 'under_review'
        audit.save()
        
        return Response({
            'message': 'Audit submitted for review successfully',
            'audit_id': audit_id,
            'status': audit.status
        })
        
    except ContractAudit.DoesNotExist:
        return Response(
            {'error': 'Contract audit not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def review_contract_audit(request, audit_id):
    """Review and approve/reject a contract audit."""
    try:
        audit = ContractAudit.objects.get(audit_id=audit_id)
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
            'message': f'Contract audit {action}d successfully',
            'audit_status': audit.status,
            'review_status': audit.review_status
        })
        
    except ContractAudit.DoesNotExist:
        return Response(
            {'error': 'Contract audit not found'},
            status=status.HTTP_404_NOT_FOUND
        )


