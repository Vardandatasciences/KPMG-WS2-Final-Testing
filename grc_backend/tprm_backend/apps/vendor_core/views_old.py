"""
Vendor Core Views - API endpoints for vendor management
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction, connection
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Q, Count
import logging
import os
import tempfile
import mimetypes
import json
from datetime import datetime

from .models import (
    VendorCategories, Vendors, VendorContacts, 
    VendorDocuments, VendorLifecycleStages, Users, TempVendor,
    ExternalScreeningResult, ScreeningMatch, LifecycleTracker, S3Files
)
from .serializers import (
    VendorCategoriesSerializer, VendorsSerializer, 
    VendorContactsSerializer, VendorDocumentsSerializer, TempVendorSerializer,
    ExternalScreeningResultSerializer, ScreeningMatchSerializer,
    ScreeningRequestSerializer, MatchUpdateSerializer, S3FilesSerializer,
    DocumentUploadSerializer
)
from .services import OFACService
from tprm_backend.utils.vendor_validators import vendor_validate_input

# RBAC imports
from tprm_backend.rbac.tprm_decorators import rbac_vendor_required
from .vendor_authentication import JWTAuthentication, SimpleAuthenticatedPermission, VendorAuthenticationMixin

# Initialize logger
vendor_logger = logging.getLogger('vendor_security')


class VendorCategoriesViewSet(VendorAuthenticationMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for vendor categories with vendor_ prefix
    Provides read-only access to vendor categories with RBAC protection
    """
    queryset = VendorCategories.objects.all()
    serializer_class = VendorCategoriesSerializer
    
    def vendor_get_queryset(self):
        """Get vendor categories with secure filtering"""
        vendor_queryset = self.queryset
        
        # Apply any additional filtering here
        vendor_search = self.request.query_params.get('search', None)
        if vendor_search:
            vendor_validated_search = vendor_validate_input(vendor_search, 'search_term')
            vendor_queryset = vendor_queryset.filter(
                category_name__icontains=vendor_validated_search
            )
        
        vendor_logger.info(f"Vendor categories requested by user {self.request.user}")
        return vendor_queryset
    
    @action(detail=False, methods=['get'])
    def vendor_active_categories(self, request):
        """Get only active vendor categories"""
        try:
            vendor_active_cats = self.get_queryset().filter(
                criticality_level__in=['high', 'medium', 'low']
            )
            vendor_serializer = self.get_serializer(vendor_active_cats, many=True)
            
            vendor_logger.info(f"Active vendor categories retrieved by {request.user}")
            return Response({
                'status': 'success',
                'data': vendor_serializer.data,
                'count': vendor_active_cats.count()
            })
            
        except Exception as e:
            vendor_logger.error(f"Error retrieving active vendor categories: {str(e)}")
            return Response(
                {'status': 'error', 'message': 'Failed to retrieve categories'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VendorsViewSet(VendorAuthenticationMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for vendors with vendor_ prefix
    Provides read-only access to vendor information with RBAC protection
    """
    queryset = Vendors.objects.select_related('vendor_category', 'created_by')
    serializer_class = VendorsSerializer
    
    def vendor_get_queryset(self):
        """Get vendors with secure filtering"""
        vendor_queryset = self.queryset
        
        # Apply filters
        vendor_status = self.request.query_params.get('status', None)
        vendor_risk_level = self.request.query_params.get('risk_level', None)
        vendor_category = self.request.query_params.get('category', None)
        
        if vendor_status:
            vendor_validated_status = vendor_validate_input(vendor_status, 'status')
            vendor_queryset = vendor_queryset.filter(status=vendor_validated_status)
            
        if vendor_risk_level:
            vendor_validated_risk = vendor_validate_input(vendor_risk_level, 'risk_level')
            vendor_queryset = vendor_queryset.filter(risk_level=vendor_validated_risk)
            
        if vendor_category:
            vendor_validated_category = vendor_validate_input(vendor_category, 'category_id')
            vendor_queryset = vendor_queryset.filter(vendor_category_id=vendor_validated_category)
        
        vendor_logger.info(f"Vendors list requested by user {self.request.user}")
        return vendor_queryset
    
    @action(detail=True, methods=['get'])
    def vendor_profile(self, request, pk=None):
        """Get complete vendor profile with related data"""
        try:
            vendor_instance = self.get_object()
            vendor_contacts = VendorContacts.objects.filter(vendor=vendor_instance, is_active=1)
            vendor_documents = VendorDocuments.objects.filter(vendor=vendor_instance)
            
            vendor_profile_data = {
                'vendor': self.get_serializer(vendor_instance).data,
                'contacts': VendorContactsSerializer(vendor_contacts, many=True).data,
                'documents': VendorDocumentsSerializer(vendor_documents, many=True).data
            }
            
            vendor_logger.info(f"Vendor profile {pk} accessed by {request.user}")
            return Response({
                'status': 'success',
                'data': vendor_profile_data
            })
            
        except Exception as e:
            vendor_logger.error(f"Error retrieving vendor profile {pk}: {str(e)}")
            return Response(
                {'status': 'error', 'message': 'Failed to retrieve vendor profile'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def vendor_dashboard_stats(self, request):
        """Get vendor statistics for dashboard"""
        try:
            vendor_total = self.get_queryset().count()
            vendor_active = self.get_queryset().filter(status='active').count()
            vendor_high_risk = self.get_queryset().filter(risk_level='high').count()
            vendor_critical = self.get_queryset().filter(is_critical_vendor=1).count()
            
            vendor_stats = {
                'total_vendors': vendor_total,
                'active_vendors': vendor_active,
                'high_risk_vendors': vendor_high_risk,
                'critical_vendors': vendor_critical,
                'inactive_vendors': vendor_total - vendor_active
            }
            
            vendor_logger.info(f"Dashboard stats requested by {request.user}")
            return Response({
                'status': 'success',
                'data': vendor_stats
            })
            
        except Exception as e:
            vendor_logger.error(f"Error retrieving vendor dashboard stats: {str(e)}")
            return Response(
                {'status': 'error', 'message': 'Failed to retrieve statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VendorContactsViewSet(VendorAuthenticationMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for vendor contacts with vendor_ prefix with RBAC protection
    """
    queryset = VendorContacts.objects.select_related('vendor')
    serializer_class = VendorContactsSerializer
    
    def vendor_get_queryset(self):
        """Get vendor contacts with filtering"""
        vendor_queryset = self.queryset
        
        vendor_vendor_id = self.request.query_params.get('vendor_id', None)
        vendor_is_primary = self.request.query_params.get('is_primary', None)
        
        if vendor_vendor_id:
            vendor_validated_id = vendor_validate_input(vendor_vendor_id, 'vendor_id')
            vendor_queryset = vendor_queryset.filter(vendor_id=vendor_validated_id)
            
        if vendor_is_primary:
            vendor_queryset = vendor_queryset.filter(is_primary=1)
        
        return vendor_queryset.filter(is_active=1)


class VendorDocumentsViewSet(VendorAuthenticationMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for vendor documents with vendor_ prefix with RBAC protection
    """
    queryset = VendorDocuments.objects.select_related('vendor', 'uploaded_by')
    serializer_class = VendorDocumentsSerializer
    
    def vendor_get_queryset(self):
        """Get vendor documents with filtering"""
        vendor_queryset = self.queryset
        
        vendor_vendor_id = self.request.query_params.get('vendor_id', None)
        vendor_doc_type = self.request.query_params.get('document_type', None)
        
        if vendor_vendor_id:
            vendor_validated_id = vendor_validate_input(vendor_vendor_id, 'vendor_id')
            vendor_queryset = vendor_queryset.filter(vendor_id=vendor_validated_id)
            
        if vendor_doc_type:
            vendor_validated_type = vendor_validate_input(vendor_doc_type, 'document_type')
            vendor_queryset = vendor_queryset.filter(document_type=vendor_validated_type)
        
        return vendor_queryset


@method_decorator(csrf_exempt, name='dispatch')
class TempVendorViewSet(VendorAuthenticationMixin, viewsets.ModelViewSet):
    """
    ViewSet for temporary vendor registration with vendor_ prefix
    Allows creating and managing temporary vendor registrations with RBAC protection
    """
    queryset = TempVendor.objects.all()
    serializer_class = TempVendorSerializer
    
    def get_queryset(self):
        """Get temp vendors with secure filtering and search"""
        queryset = self.queryset.order_by('-created_at')
        
        # Apply search filter
        search_term = self.request.query_params.get('search', None)
        if search_term:
            search_term = search_term.strip()
            if search_term:
                # Search across company_name, legal_name, and vendor_code
                queryset = queryset.filter(
                    Q(company_name__icontains=search_term) |
                    Q(legal_name__icontains=search_term) |
                    Q(vendor_code__icontains=search_term)
                )
                vendor_logger.info(f"Filtered temp vendors by search term: '{search_term}'")
        
        vendor_logger.info(f"Retrieved {queryset.count()} temp vendors")
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List temp vendors with proper response format"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            search_term = request.query_params.get('search', '')
            response_data = {
                'status': 'success',
                'count': len(serializer.data),
                'results': serializer.data
            }
            
            if search_term:
                response_data['search_term'] = search_term
                response_data['message'] = f"Found {len(serializer.data)} vendors matching '{search_term}'"
            else:
                response_data['message'] = f"Retrieved {len(serializer.data)} vendors"
            
            vendor_logger.info(f"Listed {len(serializer.data)} temp vendors (search: '{search_term}')")
            return Response(response_data)
            
        except Exception as e:
            vendor_logger.error(f"Error listing temp vendors: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to retrieve vendors',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search temp vendors by name or code"""
        try:
            search_term = request.query_params.get('q', request.query_params.get('search', ''))
            if not search_term:
                return Response({
                    'status': 'error',
                    'message': 'Search term is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            search_term = search_term.strip()
            queryset = self.queryset.filter(
                Q(company_name__icontains=search_term) |
                Q(legal_name__icontains=search_term) |
                Q(vendor_code__icontains=search_term)
            ).order_by('-created_at')
            
            serializer = self.get_serializer(queryset, many=True)
            
            vendor_logger.info(f"Search for '{search_term}' returned {len(serializer.data)} vendors")
            return Response({
                'status': 'success',
                'search_term': search_term,
                'count': len(serializer.data),
                'results': serializer.data,
                'message': f"Found {len(serializer.data)} vendors matching '{search_term}'"
            })
            
        except Exception as e:
            vendor_logger.error(f"Error searching temp vendors: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Search failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request, *args, **kwargs):
        """Create new temp vendor registration"""
        try:
            # Parse annual revenue if it's a string with currency symbols
            vendor_data = request.data.copy()
            if 'annual_revenue' in vendor_data and isinstance(vendor_data['annual_revenue'], str):
                # Remove currency symbols and commas
                revenue_str = vendor_data['annual_revenue'].replace('$', '').replace(',', '')
                try:
                    vendor_data['annual_revenue'] = float(revenue_str)
                except (ValueError, TypeError):
                    vendor_data['annual_revenue'] = None
            
            # Set default status if not provided
            if not vendor_data.get('status'):
                vendor_data['status'] = 'pending'
            
            # Convert boolean-like checkbox values
            checkbox_fields = ['is_critical_vendor', 'has_data_access', 'has_system_access']
            for field in checkbox_fields:
                if field in vendor_data:
                    vendor_data[field] = bool(vendor_data[field])
            
            vendor_serializer = self.get_serializer(data=vendor_data)
            vendor_serializer.is_valid(raise_exception=True)
            vendor_instance = vendor_serializer.save()
            
            vendor_logger.info(f"New temp vendor registration created: {vendor_instance.id}")
            
            # Trigger comprehensive automatic screening
            try:
                screening_results = self._perform_automatic_screening(vendor_instance)
                vendor_logger.info(f"Comprehensive screening completed for vendor {vendor_instance.id} with {len(screening_results)} results")
                
                # Update vendor status based on screening results
                self._update_vendor_status_based_on_screening(vendor_instance, screening_results)
                
            except Exception as e:
                vendor_logger.error(f"Automatic screening failed for vendor {vendor_instance.id}: {str(e)}")
                # Don't fail the registration if screening fails
                screening_results = []
            
            response_data = vendor_serializer.data
            if screening_results:
                response_data['screening_results'] = screening_results
                response_data['screening_status'] = 'completed'
                
                # Print detailed screening results to console
                self._print_screening_results(vendor_instance, screening_results)
            else:
                response_data['screening_status'] = 'failed'
                vendor_logger.warning(f"No screening results available for vendor {vendor_instance.id}")
            
            return Response({
                'status': 'success',
                'message': 'Vendor registration submitted successfully',
                'data': response_data
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            vendor_logger.warning(f"Validation error in temp vendor registration: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Validation failed',
                'errors': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            vendor_logger.error(f"Error creating temp vendor registration: {str(e)}")
            print(f"FULL ERROR: {str(e)}")  # Add console logging
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")  # Add full traceback
            return Response({
                'status': 'error',
                'message': f'Failed to submit vendor registration: {str(e)}',
                'error_details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def vendor_submit_registration(self, request):
        """Submit complete vendor registration with all tabs data"""
        try:
            with transaction.atomic():
                # Get form data from request
                vendor_form_data = request.data
                
                # Extract contacts and documents from the main form data
                vendor_contacts = vendor_form_data.pop('contacts', [])
                vendor_documents = vendor_form_data.pop('documents', [])
                
                # Prepare the data for serializer
                vendor_registration_data = {
                    **vendor_form_data,
                    'contacts': vendor_contacts,
                    'documents': vendor_documents,
                    'status': 'pending'
                }
                
                # Create the temp vendor record
                vendor_serializer = self.get_serializer(data=vendor_registration_data)
                vendor_serializer.is_valid(raise_exception=True)
                vendor_temp_record = vendor_serializer.save()
                
                vendor_logger.info(f"Complete vendor registration submitted: {vendor_temp_record.id}")
                
                # Trigger comprehensive automatic screening
                try:
                    screening_results = self._perform_automatic_screening(vendor_temp_record)
                    vendor_logger.info(f"Comprehensive screening completed for vendor {vendor_temp_record.id} with {len(screening_results)} results")
                    
                    # Update vendor status based on screening results
                    self._update_vendor_status_based_on_screening(vendor_temp_record, screening_results)
                    
                except Exception as e:
                    vendor_logger.error(f"Automatic screening failed for vendor {vendor_temp_record.id}: {str(e)}")
                    # Don't fail the registration if screening fails
                    screening_results = []
                
                response_data = vendor_serializer.data
                if screening_results:
                    response_data['screening_results'] = screening_results
                    response_data['screening_status'] = 'completed'
                    
                    # Print detailed screening results to console
                    self._print_screening_results(vendor_temp_record, screening_results)
                else:
                    response_data['screening_status'] = 'failed'
                    vendor_logger.warning(f"No screening results available for vendor {vendor_temp_record.id}")
                
                return Response({
                    'status': 'success',
                    'message': 'Vendor registration submitted successfully',
                    'registration_id': vendor_temp_record.id,
                    'data': response_data
                }, status=status.HTTP_201_CREATED)
                
        except ValidationError as e:
            vendor_logger.warning(f"Validation error in complete vendor registration: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Validation failed',
                'errors': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            vendor_logger.error(f"Error submitting complete vendor registration: {str(e)}")
            print(f"FULL SUBMIT ERROR: {str(e)}")  # Add console logging
            import traceback
            print(f"SUBMIT TRACEBACK: {traceback.format_exc()}")  # Add full traceback
            return Response({
                'status': 'error',
                'message': f'Failed to submit vendor registration: {str(e)}',
                'error_details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _perform_automatic_screening(self, vendor):
        """Perform comprehensive automatic screening for a vendor across multiple sources"""
        vendor_logger.info(f"Starting comprehensive screening for vendor {vendor.id}")
        
        # Perform multiple screening checks
        screening_results = []
        
        # 1. OFAC Screening
        ofac_result = self._perform_ofac_screening(vendor)
        if ofac_result:
            screening_results.append(ofac_result)
        
        # 2. PEP (Politically Exposed Person) Screening
        pep_result = self._perform_pep_screening(vendor)
        if pep_result:
            screening_results.append(pep_result)
        
        # 3. Sanctions Screening
        sanctions_result = self._perform_sanctions_screening(vendor)
        if sanctions_result:
            screening_results.append(sanctions_result)
        
        # 4. Adverse Media Screening
        adverse_media_result = self._perform_adverse_media_screening(vendor)
        if adverse_media_result:
            screening_results.append(adverse_media_result)
        
        vendor_logger.info(f"Completed comprehensive screening for vendor {vendor.id} with {len(screening_results)} results")
        return screening_results

    def _perform_ofac_screening(self, vendor):
        """Perform OFAC screening for a vendor"""
        try:
            vendor_logger.info(f"Starting OFAC screening for vendor {vendor.id}: {vendor.company_name}")
            
            ofac_service = OFACService()
            
            # Test OFAC API connection first
            connection_test = ofac_service.test_connection()
            vendor_logger.info(f"OFAC API connection test: {connection_test}")
            
            # Create screening record
            screening = ExternalScreeningResult.objects.create(
                vendor_id=vendor.id,
                screening_type='OFAC',
                search_terms={
                    'company_name': vendor.company_name,
                    'legal_name': vendor.legal_name,
                    'tax_id': vendor.tax_id
                },
                status='UNDER_REVIEW'
            )
            
            vendor_logger.info(f"Created screening record {screening.screening_id} for vendor {vendor.id}")
            
            # Search OFAC database with company name
            search_name = vendor.company_name or vendor.legal_name
            vendor_logger.info(f"Searching OFAC database for: {search_name}")
            
            search_results = ofac_service.search_entity(search_name)
            vendor_logger.info(f"OFAC search results: {search_results}")
            
            if 'error' in search_results:
                vendor_logger.warning(f"OFAC API error for vendor {vendor.id}: {search_results.get('error')}")
                screening.status = 'CLEAR'
                screening.save()
                return ExternalScreeningResultSerializer(screening).data
            
            matches = search_results.get('matches', [])
            vendor_logger.info(f"Found {len(matches)} matches for vendor {vendor.id}")
            
            high_risk_count = 0
            
            # Process matches
            for i, match in enumerate(matches):
                vendor_logger.info(f"Processing match {i+1} for vendor {vendor.id}: {match}")
                
                match_score = ofac_service.calculate_risk_score(match)
                risk_level = ofac_service.determine_risk_level(match_score)
                
                vendor_logger.info(f"Match {i+1} - Score: {match_score}, Risk Level: {risk_level}")
                
                if risk_level == 'HIGH':
                    high_risk_count += 1
                
                # Create match record
                match_record = ScreeningMatch.objects.create(
                    screening=screening,
                    match_type=f"OFAC - {match.get('source', 'Unknown')}",
                    match_score=match_score,
                    match_details={
                        **ofac_service.extract_match_details(match),
                        'risk_level': risk_level,
                        'screening_date': timezone.now().isoformat()
                    }
                )
                
                vendor_logger.info(f"Created match record {match_record.match_id} for screening {screening.screening_id}")
            
            # Update screening status
            screening.total_matches = len(matches)
            screening.high_risk_matches = high_risk_count
            
            if high_risk_count > 0:
                screening.status = 'POTENTIAL_MATCH'
                vendor_logger.warning(f"High risk matches found for vendor {vendor.id}: {high_risk_count}")
            elif len(matches) > 0:
                screening.status = 'UNDER_REVIEW'
                vendor_logger.info(f"Matches found for vendor {vendor.id}, status set to UNDER_REVIEW")
            else:
                screening.status = 'CLEAR'
                vendor_logger.info(f"No matches found for vendor {vendor.id}, status set to CLEAR")
                
            screening.save()
            vendor_logger.info(f"OFAC screening completed for vendor {vendor.id} with status: {screening.status}")
            
            return ExternalScreeningResultSerializer(screening).data
            
        except Exception as e:
            vendor_logger.error(f"OFAC screening failed for vendor {vendor.id}: {str(e)}")
            import traceback
            vendor_logger.error(f"OFAC screening traceback: {traceback.format_exc()}")
            return None

    def _perform_pep_screening(self, vendor):
        """Perform PEP (Politically Exposed Person) screening"""
        try:
            # Create PEP screening record
            screening = ExternalScreeningResult.objects.create(
                vendor_id=vendor.id,
                screening_type='PEP',
                search_terms={
                    'company_name': vendor.company_name,
                    'legal_name': vendor.legal_name,
                    'key_individuals': self._extract_key_individuals(vendor)
                },
                status='UNDER_REVIEW'
            )
            
            # Simulate PEP database search (replace with actual PEP API)
            pep_matches = self._simulate_pep_search(vendor)
            
            matches = pep_matches.get('matches', [])
            high_risk_count = 0
            
            # Process PEP matches
            for match in matches:
                match_score = match.get('score', 0)
                risk_level = 'HIGH' if match_score >= 85 else 'MEDIUM' if match_score >= 70 else 'LOW'
                
                if risk_level == 'HIGH':
                    high_risk_count += 1
                
                # Create match record
                ScreeningMatch.objects.create(
                    screening=screening,
                    match_type=f"PEP - {match.get('source', 'PEP Database')}",
                    match_score=match_score,
                    match_details={
                        'name': match.get('name'),
                        'position': match.get('position'),
                        'country': match.get('country'),
                        'risk_level': risk_level,
                        'screening_date': timezone.now().isoformat()
                    }
                )
            
            # Update screening status
            screening.total_matches = len(matches)
            screening.high_risk_matches = high_risk_count
            
            if high_risk_count > 0:
                screening.status = 'POTENTIAL_MATCH'
            elif len(matches) > 0:
                screening.status = 'UNDER_REVIEW'
            else:
                screening.status = 'CLEAR'
                
            screening.save()
            
            return ExternalScreeningResultSerializer(screening).data
            
        except Exception as e:
            vendor_logger.error(f"PEP screening failed for vendor {vendor.id}: {str(e)}")
            return None

    def _perform_sanctions_screening(self, vendor):
        """Perform sanctions screening"""
        try:
            # Create sanctions screening record
            screening = ExternalScreeningResult.objects.create(
                vendor_id=vendor.id,
                screening_type='SANCTIONS',
                search_terms={
                    'company_name': vendor.company_name,
                    'legal_name': vendor.legal_name,
                    'country': self._extract_country_from_address(vendor.headquarters_address)
                },
                status='UNDER_REVIEW'
            )
            
            # Simulate sanctions database search
            sanctions_matches = self._simulate_sanctions_search(vendor)
            
            matches = sanctions_matches.get('matches', [])
            high_risk_count = 0
            
            # Process sanctions matches
            for match in matches:
                match_score = match.get('score', 0)
                risk_level = 'HIGH' if match_score >= 85 else 'MEDIUM' if match_score >= 70 else 'LOW'
                
                if risk_level == 'HIGH':
                    high_risk_count += 1
                
                # Create match record
                ScreeningMatch.objects.create(
                    screening=screening,
                    match_type=f"Sanctions - {match.get('source', 'Sanctions List')}",
                    match_score=match_score,
                    match_details={
                        'name': match.get('name'),
                        'sanctions_type': match.get('sanctions_type'),
                        'country': match.get('country'),
                        'risk_level': risk_level,
                        'screening_date': timezone.now().isoformat()
                    }
                )
            
            # Update screening status
            screening.total_matches = len(matches)
            screening.high_risk_matches = high_risk_count
            
            if high_risk_count > 0:
                screening.status = 'POTENTIAL_MATCH'
            elif len(matches) > 0:
                screening.status = 'UNDER_REVIEW'
            else:
                screening.status = 'CLEAR'
                
            screening.save()
            
            return ExternalScreeningResultSerializer(screening).data
            
        except Exception as e:
            vendor_logger.error(f"Sanctions screening failed for vendor {vendor.id}: {str(e)}")
            return None

    def _perform_adverse_media_screening(self, vendor):
        """Perform adverse media screening"""
        try:
            # Create adverse media screening record
            screening = ExternalScreeningResult.objects.create(
                vendor_id=vendor.id,
                screening_type='ADVERSE_MEDIA',
                search_terms={
                    'company_name': vendor.company_name,
                    'legal_name': vendor.legal_name,
                    'key_individuals': self._extract_key_individuals(vendor)
                },
                status='UNDER_REVIEW'
            )
            
            # Simulate adverse media search
            adverse_media_matches = self._simulate_adverse_media_search(vendor)
            
            matches = adverse_media_matches.get('matches', [])
            high_risk_count = 0
            
            # Process adverse media matches
            for match in matches:
                match_score = match.get('score', 0)
                risk_level = 'HIGH' if match_score >= 85 else 'MEDIUM' if match_score >= 70 else 'LOW'
                
                if risk_level == 'HIGH':
                    high_risk_count += 1
                
                # Create match record
                ScreeningMatch.objects.create(
                    screening=screening,
                    match_type=f"Adverse Media - {match.get('source', 'Media Database')}",
                    match_score=match_score,
                    match_details={
                        'title': match.get('title'),
                        'publication': match.get('publication'),
                        'date': match.get('date'),
                        'risk_level': risk_level,
                        'screening_date': timezone.now().isoformat()
                    }
                )
            
            # Update screening status
            screening.total_matches = len(matches)
            screening.high_risk_matches = high_risk_count
            
            if high_risk_count > 0:
                screening.status = 'POTENTIAL_MATCH'
            elif len(matches) > 0:
                screening.status = 'UNDER_REVIEW'
            else:
                screening.status = 'CLEAR'
                
            screening.save()
            
            return ExternalScreeningResultSerializer(screening).data
            
        except Exception as e:
            vendor_logger.error(f"Adverse media screening failed for vendor {vendor.id}: {str(e)}")
            return None

    def _extract_key_individuals(self, vendor):
        """Extract key individuals from vendor data for screening"""
        individuals = []
        
        # Add company executives/contacts if available
        if hasattr(vendor, 'contacts') and vendor.contacts:
            for contact in vendor.contacts:
                if contact.get('isPrimary') or contact.get('role', '').lower() in ['ceo', 'president', 'director', 'owner']:
                    individuals.append({
                        'name': contact.get('name', ''),
                        'role': contact.get('role', ''),
                        'email': contact.get('email', '')
                    })
        
        return individuals

    def _extract_country_from_address(self, address):
        """Extract country from headquarters address"""
        if not address:
            return None
        
        # Simple country extraction (in production, use proper address parsing)
        address_lower = address.lower()
        countries = ['usa', 'united states', 'canada', 'uk', 'united kingdom', 'germany', 'france', 'china', 'india']
        
        for country in countries:
            if country in address_lower:
                return country.title()
        
        return None

    def _simulate_pep_search(self, vendor):
        """Simulate PEP database search (replace with actual PEP API)"""
        # This is a simulation - replace with actual PEP API integration
        import random
        
        # Simulate some PEP matches based on company name patterns
        company_name = (vendor.company_name or '').lower()
        matches = []
        
        # Simulate matches for certain patterns
        if any(keyword in company_name for keyword in ['government', 'ministry', 'department', 'agency']):
            matches.append({
                'name': f"{vendor.company_name} Executive",
                'position': 'Government Official',
                'country': 'Various',
                'score': random.randint(75, 95),
                'source': 'PEP Database'
            })
        
        return {'matches': matches}

    def _simulate_sanctions_search(self, vendor):
        """Simulate sanctions database search (replace with actual sanctions API)"""
        # This is a simulation - replace with actual sanctions API integration
        import random
        
        company_name = (vendor.company_name or '').lower()
        matches = []
        
        # Simulate matches for certain patterns
        if any(keyword in company_name for keyword in ['sanctions', 'embargo', 'restricted']):
            matches.append({
                'name': vendor.company_name,
                'sanctions_type': 'Trade Sanctions',
                'country': 'Various',
                'score': random.randint(80, 95),
                'source': 'Sanctions List'
            })
        
        return {'matches': matches}

    def _simulate_adverse_media_search(self, vendor):
        """Simulate adverse media search (replace with actual media API)"""
        # This is a simulation - replace with actual media API integration
        import random
        
        company_name = (vendor.company_name or '').lower()
        matches = []
        
        # Simulate matches for certain patterns
        if any(keyword in company_name for keyword in ['fraud', 'scam', 'illegal', 'criminal']):
            matches.append({
                'title': f"Investigation into {vendor.company_name}",
                'publication': 'Financial Times',
                'date': '2024-01-15',
                'score': random.randint(70, 90),
                'source': 'Media Database'
            })
        
        return {'matches': matches}

    def _update_vendor_status_based_on_screening(self, vendor, screening_results):
        """Update vendor status based on comprehensive screening results"""
        try:
            high_risk_count = 0
            total_matches = 0
            
            # Analyze all screening results
            for result in screening_results:
                if isinstance(result, dict):
                    total_matches += result.get('total_matches', 0)
                    high_risk_count += result.get('high_risk_matches', 0)
            
            # Update vendor status based on results
            if high_risk_count > 0:
                vendor.status = 'high_risk_pending'
                vendor.risk_level = 'high'
            elif total_matches > 0:
                vendor.status = 'under_review'
                vendor.risk_level = 'medium'
            else:
                vendor.status = 'cleared'
                vendor.risk_level = 'low'
            
            vendor.save()
            vendor_logger.info(f"Updated vendor {vendor.id} status to {vendor.status} based on screening results")
            
        except Exception as e:
            vendor_logger.error(f"Failed to update vendor status based on screening: {str(e)}")

    def _print_screening_results(self, vendor, screening_results):
        """Print detailed screening results to console for debugging and monitoring"""
        print("\n" + "="*80)
        print(f"🔍 EXTERNAL SCREENING RESULTS FOR VENDOR: {vendor.company_name}")
        print(f"📋 Vendor ID: {vendor.id}")
        print(f"📅 Screening Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        if not screening_results:
            print("❌ No screening results available")
            return
        
        total_matches = 0
        high_risk_matches = 0
        
        for i, result in enumerate(screening_results, 1):
            if not result:
                continue
                
            screening_type = result.get('screening_type', 'Unknown')
            status = result.get('status', 'Unknown')
            matches_count = result.get('total_matches', 0)
            high_risk_count = result.get('high_risk_matches', 0)
            
            total_matches += matches_count
            high_risk_matches += high_risk_count
            
            print(f"\n📊 SCREENING SOURCE #{i}: {screening_type}")
            print(f"   Status: {status}")
            print(f"   Total Matches: {matches_count}")
            print(f"   High Risk Matches: {high_risk_count}")
            
            # Print individual matches if available
            if 'matches' in result and result['matches']:
                print(f"   📋 Individual Matches:")
                for j, match in enumerate(result['matches'], 1):
                    match_type = match.get('match_type', 'Unknown')
                    match_score = match.get('match_score', 0)
                    resolution_status = match.get('resolution_status', 'PENDING')
                    
                    print(f"      {j}. {match_type}")
                    print(f"         Score: {match_score}")
                    print(f"         Status: {resolution_status}")
                    
                    # Print match details if available
                    match_details = match.get('match_details', {})
                    if match_details:
                        if 'name' in match_details:
                            print(f"         Name: {match_details['name']}")
                        if 'source' in match_details:
                            print(f"         Source: {match_details['source']}")
                        if 'risk_level' in match_details:
                            print(f"         Risk Level: {match_details['risk_level']}")
            else:
                print(f"   ✅ No matches found")
        
        # Print summary
        print(f"\n📈 SCREENING SUMMARY:")
        print(f"   Total Screening Sources: {len(screening_results)}")
        print(f"   Total Matches Found: {total_matches}")
        print(f"   High Risk Matches: {high_risk_matches}")
        
        # Determine overall risk assessment
        if high_risk_matches > 0:
            overall_status = "🔴 HIGH RISK - Requires immediate review"
        elif total_matches > 0:
            overall_status = "🟡 MEDIUM RISK - Under review"
        else:
            overall_status = "🟢 LOW RISK - Cleared"
        
        print(f"   Overall Assessment: {overall_status}")
        print("="*80)
        print("✅ Screening results printed successfully\n")
        
        # Also log to file for audit trail
        vendor_logger.info(f"Screening results for vendor {vendor.id}: {total_matches} total matches, {high_risk_matches} high risk")

    @action(detail=False, methods=['post'])
    def upload_document(self, request):
        """Upload document to S3 and save to database"""
        try:
            # Import S3 client here to avoid circular imports
            from s3 import create_direct_mysql_client
            
            # Validate request data
            serializer = DocumentUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Get the temp vendor - try by vendor_id first, then by user_id
            temp_vendor = None
            
            # Try to get by vendor_id
            if 'vendor_id' in validated_data and validated_data['vendor_id']:
                try:
                    temp_vendor = TempVendor.objects.get(id=validated_data['vendor_id'])
                except TempVendor.DoesNotExist:
                    pass
            
            # If not found and user_id is provided, try to find or create by user_id
            if not temp_vendor and 'user_id' in validated_data:
                user_id = validated_data['user_id']
                temp_vendor = TempVendor.objects.filter(userid=user_id).first()
                
                # If still not found, create a new temp vendor
                if not temp_vendor:
                    temp_vendor = TempVendor.objects.create(
                        userid=user_id,
                        company_name=f'Temp Vendor for User {user_id}',
                        status='draft',
                        created_at=timezone.now()
                    )
                    vendor_logger.info(f"Created new temp vendor {temp_vendor.id} for user {user_id}")
            
            if not temp_vendor:
                return Response({
                    'status': 'error',
                    'message': 'Vendor not found. Please provide valid vendor_id or user_id'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Save file to temporary location
            uploaded_file = validated_data['file']
            file_name = uploaded_file.name
            file_size = uploaded_file.size
            file_type = uploaded_file.content_type or mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Initialize S3 client
                s3_client = create_direct_mysql_client()
                
                # Generate unique file name for S3 (just the filename, no nested paths)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                s3_file_name = f"{timestamp}_{file_name}"
                
                # Upload to S3
                upload_result = s3_client.upload(
                    file_path=temp_file_path,
                    user_id=validated_data.get('user_id', str(temp_vendor.userid or 'unknown')),
                    custom_file_name=s3_file_name
                )
                
                if not upload_result.get('success'):
                    raise Exception(f"S3 upload failed: {upload_result.get('error', 'Unknown error')}")
                
                file_info = upload_result['file_info']
                
                # Save to s3_files table
                # Convert expiry_date to string for JSON serialization
                expiry_date_str = None
                if validated_data.get('expiry_date'):
                    expiry_date_str = validated_data['expiry_date'].isoformat()
                
                s3_file = S3Files.objects.create(
                    url=file_info['url'],
                    file_type=validated_data['document_type'].lower(),
                    file_name=validated_data['document_name'],
                    user_id=validated_data.get('user_id', str(temp_vendor.userid or '')),
                    metadata={
                        'original_filename': file_name,
                        's3_filename': s3_file_name,
                        's3_key': file_info['s3Key'],
                        's3_bucket': file_info.get('bucket', ''),
                        'file_size': file_size,
                        'content_type': file_type,
                        'document_type': validated_data['document_type'],
                        'version': validated_data.get('version', '1.0'),
                        'status': validated_data.get('status', 'Pending'),
                        'expiry_date': expiry_date_str,
                        'vendor_id': temp_vendor.id,
                        'upload_timestamp': timestamp,
                        'user_id': validated_data.get('user_id', str(temp_vendor.userid or ''))
                    }
                )
                
                # Update temp_vendor documents field
                current_documents = temp_vendor.documents or []
                
                # Create document entry for temp_vendor (matching expected format)
                document_entry = {
                    'status': validated_data.get('status', 'Pending'),
                    'version': validated_data.get('version', '1.0'),
                    's3_file_id': s3_file.id,
                    'expiry_date': validated_data.get('expiry_date').isoformat() if validated_data.get('expiry_date') else '',
                    'document_name': validated_data['document_name'],
                    'document_type': validated_data['document_type']
                }
                
                current_documents.append(document_entry)
                temp_vendor.documents = current_documents
                temp_vendor.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Document uploaded successfully',
                    'data': {
                        's3_file_id': s3_file.id,
                        'document': document_entry,
                        's3_url': file_info['url'],
                        'upload_info': {
                            'file_size': file_size,
                            'content_type': file_type,
                            's3_key': file_info['s3Key']
                        }
                    }
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                vendor_logger.error(f"Document upload error: {str(e)}")
                return Response({
                    'status': 'error',
                    'message': f'Upload failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            vendor_logger.error(f"Document upload error: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Upload failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def get_user_data(self, request):
        """Get user data based on UserId from temp_vendor and rfp_responses tables"""
        try:
            # Import RFPResponses from vendor_questionnaire
            from apps.vendor_questionnaire.models import RFPResponses
            from django.db import connection
            
            # Get UserId from query params, default to 64 (logged in user)
            user_id = request.query_params.get('user_id', '64')
            
            # Convert to integer
            try:
                user_id = int(user_id)
            except ValueError:
                return Response({
                    'status': 'error',
                    'message': 'Invalid user_id format'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            vendor_logger.info(f"Fetching user data for logged-in UserId: {user_id}")
            
            # Step 1: Get temp_vendor record by UserId
            temp_vendor = TempVendor.objects.filter(userid=user_id).first()
            response_id = None
            
            if temp_vendor:
                # Step 2: Get response_id from temp_vendor if it exists
                response_id = temp_vendor.response_id
            else:
                # If no temp_vendor record, try to find RFP response by vendor_id or other means
                # For now, we'll use a default response_id for testing
                # In production, you might want to implement different logic here
                vendor_logger.info(f"No temp_vendor found for UserId: {user_id}, checking for RFP responses...")
                
                # Try to find any RFP response that might be associated with this user
                # This is a fallback mechanism - you might want to implement your own logic
                with connection.cursor() as cursor:
                    cursor.execute("SELECT response_id FROM rfp_responses WHERE submitted_by LIKE %s ORDER BY submission_date DESC LIMIT 1", [f'%{user_id}%'])
                    result = cursor.fetchone()
                    if result:
                        response_id = result[0]
                        vendor_logger.info(f"Found RFP response {response_id} for UserId: {user_id}")
            
            if not response_id:
                # Return temp_vendor data only if no response_id found
                if temp_vendor:
                    vendor_serializer = self.get_serializer(temp_vendor)
                    return Response({
                        'status': 'success',
                        'message': 'Temp vendor data retrieved (no RFP response)',
                        'data': {
                            'temp_vendor': vendor_serializer.data,
                            'rfp_response': None
                        }
                    })
                else:
                    return Response({
                        'status': 'error',
                        'message': f'No vendor or RFP response found for UserId: {user_id}',
                        'data': None
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Step 3: Get RFP response data using response_id
            try:
                # Query rfp_responses table directly using raw SQL to get all fields
                with connection.cursor() as cursor:
                    # First, get the column names to avoid unknown column errors
                    cursor.execute("SHOW COLUMNS FROM rfp_responses")
                    available_columns = [row[0] for row in cursor.fetchall()]
                    
                    # Build the SELECT query with only existing columns
                    safe_columns = [
                        'response_id', 'rfp_id', 'vendor_id', 'invitation_id',
                        'submission_date', 'response_documents', 'document_urls',
                        'proposed_value', 'technical_score', 'commercial_score',
                        'overall_score', 'weighted_final_score', 'evaluation_status',
                        'auto_rejected', 'rejection_reason', 'submission_source',
                        'external_submission_data', 'draft_data', 'completion_percentage',
                        'last_saved_at', 'submitted_by', 'evaluated_by', 'evaluation_date',
                        'evaluation_comments', 'vendor_name', 'contact_email',
                        'contact_phone', 'proposal_data', 'submission_status',
                        'created_at', 'updated_at', 'submitted_at', 'ip_address', 'user_agent'
                    ]
                    
                    # Filter to only include columns that exist in the table
                    existing_columns = [col for col in safe_columns if col in available_columns]
                    
                    if not existing_columns:
                        raise Exception("No valid columns found in rfp_responses table")
                    
                    columns_str = ', '.join(existing_columns)
                    cursor.execute(f"""
                        SELECT {columns_str}
                        FROM rfp_responses
                        WHERE response_id = %s
                    """, [response_id])
                    
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    
                    if row:
                        # Convert row to dictionary
                        rfp_response_data = dict(zip(columns, row))
                        
                        # Convert datetime objects to ISO format strings and handle JSON fields
                        for key, value in rfp_response_data.items():
                            if hasattr(value, 'isoformat'):
                                rfp_response_data[key] = value.isoformat()
                            elif isinstance(value, bytes):
                                rfp_response_data[key] = value.decode('utf-8')
                            elif isinstance(value, str) and key in ['response_documents', 'document_urls', 'external_submission_data', 'draft_data', 'proposal_data']:
                                # Try to parse JSON fields
                                try:
                                    import json
                                    rfp_response_data[key] = json.loads(value) if value else None
                                except (json.JSONDecodeError, TypeError):
                                    # Keep as string if not valid JSON
                                    rfp_response_data[key] = value
                            elif value is None:
                                rfp_response_data[key] = None
                    else:
                        rfp_response_data = None
                        # Create test data if no RFP response found (for demonstration)
                        if response_id == 109:  # Only for testing
                            vendor_logger.info(f"Creating test RFP response data for response_id: {response_id}")
                            rfp_response_data = {
                                'response_id': response_id,
                                'rfp_id': 1001,
                                'vendor_id': 64,
                                'invitation_id': 2001,
                                'submission_date': '2025-01-15T10:30:00Z',
                                'response_documents': {
                                    'technical_proposal': {
                                        'name': 'Technical Proposal Document',
                                        'url': 'https://example.com/technical_proposal.pdf',
                                        'type': 'pdf',
                                        'size': '2.5MB',
                                        'upload_date': '2025-01-15T10:30:00Z'
                                    },
                                    'financial_proposal': {
                                        'name': 'Financial Proposal Document',
                                        'url': 'https://example.com/financial_proposal.pdf',
                                        'type': 'pdf',
                                        'size': '1.8MB',
                                        'upload_date': '2025-01-15T10:35:00Z'
                                    },
                                    'company_profile': {
                                        'name': 'Company Profile Document',
                                        'url': 'https://example.com/company_profile.pdf',
                                        'type': 'pdf',
                                        'size': '3.2MB',
                                        'upload_date': '2025-01-15T10:40:00Z'
                                    }
                                },
                                'document_urls': {
                                    'contract_document': 'https://vardaanwebsites.s3.ap-south-1.amazonaws.com/contracts/contract_109_2025.pdf',
                                    'license_certificate': 'https://vardaanwebsites.s3.ap-south-1.amazonaws.com/licenses/license_109_2025.pdf',
                                    'insurance_certificate': 'https://vardaanwebsites.s3.ap-south-1.amazonaws.com/insurance/insurance_109_2025.pdf',
                                    'compliance_certificate': 'https://vardaanwebsites.s3.ap-south-1.amazonaws.com/compliance/compliance_109_2025.pdf',
                                    'financial_statement': 'https://vardaanwebsites.s3.ap-south-1.amazonaws.com/financials/financial_109_2025.pdf'
                                },
                                'proposed_value': 150000.00,
                                'technical_score': 85.50,
                                'commercial_score': 92.00,
                                'overall_score': 88.75,
                                'weighted_final_score': 89.25,
                                'evaluation_status': 'UNDER_EVALUATION',
                                'auto_rejected': False,
                                'rejection_reason': None,
                                'submission_source': 'invited',
                                'external_submission_data': {'source': 'vendor_portal', 'version': '1.0'},
                                'draft_data': {'draft_saved': True, 'last_edit': '2025-01-15T11:00:00Z'},
                                'completion_percentage': 95.00,
                                'last_saved_at': '2025-01-15T11:00:00Z',
                                'submitted_by': 'vendor_user_64',
                                'evaluated_by': 1,
                                'evaluation_date': '2025-01-15T11:30:00Z',
                                'evaluation_comments': 'Initial evaluation completed. Technical proposal looks strong.',
                                'vendor_name': 'Test Vendor Corporation',
                                'contact_email': 'contact@testvendor.com',
                                'contact_phone': '+1-555-0123',
                                'proposal_data': {
                                    'project_scope': 'Complete software development and implementation',
                                    'timeline': '6 months',
                                    'team_size': '8 developers',
                                    'methodology': 'Agile',
                                    'deliverables': [
                                        'Software application',
                                        'Documentation',
                                        'Training materials',
                                        'Support for 1 year'
                                    ]
                                },
                                'submission_status': 'submitted',
                                'created_at': '2025-01-15T10:00:00Z',
                                'updated_at': '2025-01-15T11:00:00Z',
                                'submitted_at': '2025-01-15T10:30:00Z',
                                'ip_address': '192.168.1.100',
                                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            }
                
                # Serialize temp_vendor data (if exists)
                temp_vendor_data = None
                if temp_vendor:
                    vendor_serializer = self.get_serializer(temp_vendor)
                    temp_vendor_data = vendor_serializer.data
                
                return Response({
                    'status': 'success',
                    'message': 'User data retrieved successfully',
                    'data': {
                        'temp_vendor': temp_vendor_data,
                        'rfp_response': rfp_response_data,
                        'user_id': user_id,
                        'response_id': response_id
                    }
                })
                
            except Exception as rfp_error:
                vendor_logger.error(f"Error fetching RFP response: {str(rfp_error)}")
                # Return temp_vendor data even if RFP response fetch fails
                temp_vendor_data = None
                if temp_vendor:
                    vendor_serializer = self.get_serializer(temp_vendor)
                    temp_vendor_data = vendor_serializer.data
                
                return Response({
                    'status': 'partial_success',
                    'message': f'Temp vendor data retrieved, but RFP response fetch failed: {str(rfp_error)}',
                    'data': {
                        'temp_vendor': temp_vendor_data,
                        'rfp_response': None,
                        'error': str(rfp_error)
                    }
                })
                
        except Exception as e:
            vendor_logger.error(f"Error in get_user_data: {str(e)}")
            import traceback
            print(f"GET_USER_DATA ERROR: {str(e)}")
            print(f"TRACEBACK: {traceback.format_exc()}")
            return Response({
                'status': 'error',
                'message': f'Failed to fetch user data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'])
    def delete_document(self, request, pk=None):
        """Delete document from S3 and database"""
        try:
            # Get the temp vendor
            try:
                temp_vendor = TempVendor.objects.get(id=pk)
            except TempVendor.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Vendor not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            document_id = request.data.get('document_id')
            if not document_id:
                return Response({
                    'status': 'error',
                    'message': 'Document ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the S3 file record
            try:
                s3_file = S3Files.objects.get(id=document_id)
            except S3Files.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Document not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Remove from temp_vendor documents
            current_documents = temp_vendor.documents or []
            updated_documents = [doc for doc in current_documents if doc.get('id') != document_id]
            temp_vendor.documents = updated_documents
            temp_vendor.save()
            
            # Delete from s3_files table
            s3_file.delete()
            
            return Response({
                'status': 'success',
                'message': 'Document deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            vendor_logger.error(f"Document deletion error: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Deletion failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VendorScreeningViewSet(VendorAuthenticationMixin, viewsets.ModelViewSet):
    """
    ViewSet for vendor screening operations with RBAC protection
    """
    queryset = ExternalScreeningResult.objects.all()
    serializer_class = ExternalScreeningResultSerializer

    def get_queryset(self):
        """Get screening results with filters"""
        queryset = ExternalScreeningResult.objects.prefetch_related('matches')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Filter by screening type
        screening_type = self.request.query_params.get('type')
        if screening_type:
            queryset = queryset.filter(screening_type=screening_type)
            
        # Filter by vendor
        vendor_id = self.request.query_params.get('vendor_id')
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
            
        return queryset.order_by('-screening_date')

    @action(detail=False, methods=['post'])
    def screen_vendor(self, request):
        """Initiate screening for a vendor"""
        serializer = ScreeningRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vendor_id = serializer.validated_data['vendor_id']
        screening_types = serializer.validated_data.get('screening_types', ['OFAC'])
        threshold = serializer.validated_data.get('threshold', 85)
        
        try:
            vendor = TempVendor.objects.get(id=vendor_id)
            results = []
            
            for screening_type in screening_types:
                if screening_type == 'OFAC':
                    result = self._perform_ofac_screening(vendor, threshold)
                    results.append(result)
                # Add other screening types as needed
                
            return Response({
                'message': 'Screening initiated successfully',
                'results': results
            }, status=status.HTTP_201_CREATED)
            
        except TempVendor.DoesNotExist:
            return Response({
                'error': 'Vendor not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            vendor_logger.error(f"Screening failed for vendor {vendor_id}: {str(e)}")
            return Response({
                'error': f'Screening failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def update_match_status(self, request, pk=None):
        """Update the status of a specific match"""
        screening = self.get_object()
        serializer = MatchUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        match_id = serializer.validated_data['match_id']
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        
        try:
            match = ScreeningMatch.objects.get(
                match_id=match_id, 
                screening=screening
            )
            
            match.resolution_status = new_status
            match.resolution_notes = notes
            match.resolved_by = 1  # Default admin user for now
            match.resolved_date = timezone.now()
            match.save()
            
            # Update overall screening status
            self._update_screening_status(screening)
            
            return Response({
                'message': 'Match status updated successfully'
            })
            
        except ScreeningMatch.DoesNotExist:
            return Response({
                'error': 'Match not found'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def summary_stats(self, request):
        """Get summary statistics for screening results"""
        stats = ExternalScreeningResult.objects.aggregate(
            total_screenings=Count('screening_id'),
            clear_count=Count('screening_id', filter=Q(status='CLEAR')),
            under_review_count=Count('screening_id', filter=Q(status='UNDER_REVIEW')),
            potential_match_count=Count('screening_id', filter=Q(status='POTENTIAL_MATCH')),
            confirmed_match_count=Count('screening_id', filter=Q(status='CONFIRMED_MATCH')),
        )
        
        return Response(stats)

    @action(detail=False, methods=['get'])
    def latest_results(self, request):
        """Get latest screening results for the external screening page"""
        try:
            # Get recent screening results with vendor and match data
            results = self.get_queryset()[:20]  # Latest 20 results
            serializer = self.get_serializer(results, many=True)
            
            # Format data for frontend
            formatted_results = []
            for result in serializer.data:
                formatted_result = {
                    'id': result['screening_id'],
                    'companyName': result['vendor_name'],
                    'source': result['screening_type'],
                    'date': result['screening_date'][:10],  # Just date part
                    'status': result['status'].lower(),
                    'matchCount': result['total_matches'],
                    'vendor': result['vendor'],
                    'matches': result['matches']
                }
                formatted_results.append(formatted_result)
            
            return Response({
                'status': 'success',
                'data': formatted_results
            })
            
        except Exception as e:
            vendor_logger.error(f"Error fetching latest screening results: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to fetch screening results'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def vendor_screening_results(self, request):
        """Get screening results for a specific vendor"""
        vendor_id = request.query_params.get('vendor_id')
        if not vendor_id:
            return Response({
                'status': 'error',
                'message': 'vendor_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get all screening results for the vendor
            results = self.get_queryset().filter(vendor_id=vendor_id).order_by('-screening_date')
            serializer = self.get_serializer(results, many=True)
            
            # Print results to console for debugging
            self._print_vendor_screening_results(vendor_id, serializer.data)
            
            return Response({
                'status': 'success',
                'data': serializer.data,
                'count': results.count()
            })
            
        except Exception as e:
            vendor_logger.error(f"Error fetching screening results for vendor {vendor_id}: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to fetch vendor screening results'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def mark_as_cleared(self, request, pk=None):
        """Mark all screening results for a vendor as cleared"""
        try:
            vendor_id = pk
            # Update all screening results for this vendor to CLEAR status
            ExternalScreeningResult.objects.filter(vendor_id=vendor_id).update(
                status='CLEAR',
                last_updated=timezone.now()
            )
            
            # Also update any matches to CLEARED status
            ScreeningMatch.objects.filter(
                screening__vendor_id=vendor_id
            ).update(
                resolution_status='CLEARED',
                resolution_notes='Marked as cleared by user',
                resolved_date=timezone.now()
            )
            
            vendor_logger.info(f"Marked all screening results as cleared for vendor {vendor_id}")
            
            return Response({
                'status': 'success',
                'message': 'All screening results marked as cleared'
            })
            
        except Exception as e:
            vendor_logger.error(f"Error marking vendor {pk} as cleared: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Failed to mark as cleared: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """Add a note to screening results for a vendor"""
        try:
            vendor_id = pk
            note = request.data.get('note', '')
            
            if not note:
                return Response({
                    'status': 'error',
                    'message': 'Note is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update all screening results for this vendor with the note
            ExternalScreeningResult.objects.filter(vendor_id=vendor_id).update(
                review_comments=note,
                last_updated=timezone.now()
            )
            
            vendor_logger.info(f"Added note to screening results for vendor {vendor_id}: {note}")
            
            return Response({
                'status': 'success',
                'message': 'Note added successfully'
            })
            
        except Exception as e:
            vendor_logger.error(f"Error adding note for vendor {pk}: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Failed to add note: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def test_ofac_connection(self, request):
        """Test OFAC API connection"""
        try:
            ofac_service = OFACService()
            connection_test = ofac_service.test_connection()
            
            vendor_logger.info(f"OFAC API connection test requested: {connection_test}")
            
            return Response({
                'status': 'success' if connection_test.get('success') else 'error',
                'message': connection_test.get('message'),
                'data': connection_test
            })
            
        except Exception as e:
            vendor_logger.error(f"Error testing OFAC connection: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Failed to test OFAC connection: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def test_ofac_search(self, request):
        """Test OFAC search with a specific name"""
        try:
            search_name = request.data.get('name', 'Test Company')
            ofac_service = OFACService()
            
            vendor_logger.info(f"Testing OFAC search for: {search_name}")
            
            search_results = ofac_service.search_entity(search_name)
            vendor_logger.info(f"OFAC search test results: {search_results}")
            
            return Response({
                'status': 'success',
                'message': f'OFAC search test completed for: {search_name}',
                'data': search_results
            })
            
        except Exception as e:
            vendor_logger.error(f"Error testing OFAC search: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Failed to test OFAC search: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def print_screening_results(self, request):
        """Print screening results to console and return formatted data"""
        vendor_id = request.query_params.get('vendor_id')
        print_all = request.query_params.get('print_all', 'false').lower() == 'true'
        
        try:
            if print_all:
                # Print all screening results
                results = self.get_queryset().order_by('-screening_date')
                self._print_all_screening_results(results)
                
                return Response({
                    'status': 'success',
                    'message': 'All screening results printed to console',
                    'data': self.get_serializer(results, many=True).data,
                    'count': results.count()
                })
            elif vendor_id:
                # Print results for specific vendor
                results = self.get_queryset().filter(vendor_id=vendor_id).order_by('-screening_date')
                self._print_vendor_screening_results(vendor_id, self.get_serializer(results, many=True).data)
                
                return Response({
                    'status': 'success',
                    'message': f'Screening results for vendor {vendor_id} printed to console',
                    'data': self.get_serializer(results, many=True).data,
                    'count': results.count()
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Either vendor_id or print_all=true parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            vendor_logger.error(f"Error printing screening results: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to print screening results'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _print_all_screening_results(self, results):
        """Print all screening results to console"""
        print("\n" + "="*100)
        print("🔍 ALL EXTERNAL SCREENING RESULTS")
        print(f"📅 Retrieved: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)
        
        if not results.exists():
            print("❌ No screening results found in database")
            return
        
        print(f"📊 Total Screening Results: {results.count()}")
        print("-" * 100)
        
        for i, result in enumerate(results, 1):
            print(f"\n🔍 SCREENING RESULT #{i}")
            print(f"   ID: {result.screening_id}")
            print(f"   Vendor ID: {result.vendor_id}")
            print(f"   Type: {result.screening_type}")
            print(f"   Status: {result.status}")
            print(f"   Date: {result.screening_date}")
            print(f"   Total Matches: {result.total_matches}")
            print(f"   High Risk Matches: {result.high_risk_matches}")
            
            # Get matches for this screening
            matches = ScreeningMatch.objects.filter(screening=result)
            if matches.exists():
                print(f"   📋 Individual Matches ({matches.count()}):")
                for j, match in enumerate(matches, 1):
                    print(f"      {j}. {match.match_type}")
                    print(f"         Score: {match.match_score}")
                    print(f"         Status: {match.resolution_status}")
                    print(f"         Details: {match.match_details}")
            else:
                print(f"   ✅ No individual matches found")
        
        print("\n" + "="*100)
        print("✅ All screening results printed successfully")

    def _print_vendor_screening_results(self, vendor_id, screening_data):
        """Print screening results for a specific vendor"""
        print("\n" + "="*80)
        print(f"🔍 SCREENING RESULTS FOR VENDOR ID: {vendor_id}")
        print(f"📅 Retrieved: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        if not screening_data:
            print("❌ No screening results found for this vendor")
            return
        
        for i, result in enumerate(screening_data, 1):
            print(f"\n📊 SCREENING #{i}:")
            print(f"   Type: {result.get('screening_type', 'Unknown')}")
            print(f"   Status: {result.get('status', 'Unknown')}")
            print(f"   Date: {result.get('screening_date', 'Unknown')}")
            print(f"   Total Matches: {result.get('total_matches', 0)}")
            print(f"   High Risk Matches: {result.get('high_risk_matches', 0)}")
            
            # Print search terms used
            search_terms = result.get('search_terms', {})
            if search_terms and isinstance(search_terms, dict):
                print(f"   Search Terms:")
                for key, value in search_terms.items():
                    print(f"      {key}: {value}")
            elif search_terms:
                print(f"   Search Terms: {search_terms}")
            
            # Print individual matches
            matches = result.get('matches', [])
            if matches:
                print(f"   📋 Matches Found:")
                for j, match in enumerate(matches, 1):
                    print(f"      {j}. {match.get('match_type', 'Unknown')}")
                    print(f"         Score: {match.get('match_score', 0)}")
                    print(f"         Status: {match.get('resolution_status', 'PENDING')}")
                    
                    match_details = match.get('match_details', {})
                    if match_details:
                        for key, value in match_details.items():
                            if key not in ['screening_date']:  # Skip redundant date
                                print(f"         {key}: {value}")
            else:
                print(f"   ✅ No matches found")
        
        print("="*80)
        print("✅ Vendor screening results printed successfully\n")

    def _perform_ofac_screening(self, vendor, threshold=85):
        """Perform OFAC screening for a vendor"""
        ofac_service = OFACService()
        
        # Create screening record
        screening = ExternalScreeningResult.objects.create(
            vendor_id=vendor.id,
            screening_type='OFAC',
            search_terms={
                'company_name': vendor.company_name,
                'legal_name': vendor.legal_name,
                'tax_id': vendor.tax_id,
                'threshold': threshold
            },
            status='UNDER_REVIEW'
        )
        
        # Search OFAC database
        search_results = ofac_service.search_entity(
            vendor.company_name or vendor.legal_name, 
            threshold=threshold
        )
        
        if 'error' in search_results:
            screening.status = 'CLEAR'
            screening.save()
            return ExternalScreeningResultSerializer(screening).data
        
        matches = search_results.get('matches', [])
        high_risk_count = 0
        
        # Process matches
        for match in matches:
            match_score = ofac_service.calculate_risk_score(match)
            risk_level = ofac_service.determine_risk_level(match_score)
            
            if risk_level == 'HIGH':
                high_risk_count += 1
            
            # Create match record
            ScreeningMatch.objects.create(
                screening=screening,
                match_type=f"OFAC - {match.get('source', 'Unknown')}",
                match_score=match_score,
                match_details={
                    **ofac_service.extract_match_details(match),
                    'risk_level': risk_level,
                    'screening_date': timezone.now().isoformat()
                }
            )
        
        # Update screening status
        screening.total_matches = len(matches)
        screening.high_risk_matches = high_risk_count
        
        if high_risk_count > 0:
            screening.status = 'POTENTIAL_MATCH'
        elif len(matches) > 0:
            screening.status = 'UNDER_REVIEW'
        else:
            screening.status = 'CLEAR'
            
        screening.save()
        
        return ExternalScreeningResultSerializer(screening).data

    def _update_screening_status(self, screening):
        """Update overall screening status based on match statuses"""
        matches = screening.matches.all()
        
        if not matches.exists():
            screening.status = 'CLEAR'
        elif matches.filter(resolution_status='BLOCKED').exists():
            screening.status = 'CONFIRMED_MATCH'
        elif matches.filter(resolution_status='ESCALATED').exists():
            screening.status = 'POTENTIAL_MATCH'
        elif matches.filter(resolution_status='CLEARED').exists():
            screening.status = 'CLEAR'
        elif matches.filter(resolution_status='PENDING').exists():
            screening.status = 'UNDER_REVIEW'
        else:
            screening.status = 'CLEAR'
            
        screening.save()


# Lifecycle tracking utility functions
def update_temp_vendor_lifecycle_stage(vendor_id, new_stage_id, user_id=None):
    """
    Update temp vendor lifecycle stage and record in lifecycle_tracker
    """
    from django.utils import timezone
    from .models import TempVendor, LifecycleTracker, VendorLifecycleStages
    
    try:
        temp_vendor = TempVendor.objects.get(id=vendor_id)
        old_stage_id = temp_vendor.lifecycle_stage
        
        # End current lifecycle tracker entry if exists
        if old_stage_id:
            current_tracker = LifecycleTracker.objects.filter(
                vendor_id=vendor_id,
                lifecycle_stage=old_stage_id,
                ended_at__isnull=True
            ).first()
            if current_tracker:
                current_tracker.ended_at = timezone.now()
                current_tracker.save()
        
        # Update temp vendor lifecycle stage
        temp_vendor.lifecycle_stage = new_stage_id
        temp_vendor.updated_at = timezone.now()
        temp_vendor.save()
        
        # Create new lifecycle tracker entry
        LifecycleTracker.objects.create(
            vendor_id=vendor_id,
            lifecycle_stage=new_stage_id,
            started_at=timezone.now()
        )
        
        vendor_logger.info(f"Updated temp vendor {vendor_id} lifecycle stage from {old_stage_id} to {new_stage_id}")
        
        return {
            'success': True,
            'old_stage': old_stage_id,
            'new_stage': new_stage_id,
            'vendor_id': vendor_id
        }
        
    except TempVendor.DoesNotExist:
        vendor_logger.error(f"Temp vendor {vendor_id} not found")
        return {'success': False, 'error': 'Vendor not found'}
    except Exception as e:
        vendor_logger.error(f"Error updating lifecycle stage for vendor {vendor_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


def get_lifecycle_stage_id_by_code(stage_code):
    """
    Get lifecycle stage ID by stage code
    """
    try:
        stage = VendorLifecycleStages.objects.get(stage_code=stage_code, is_active=True)
        return stage.stage_id
    except VendorLifecycleStages.DoesNotExist:
        return None


def get_initial_lifecycle_stage():
    """
    Get the initial lifecycle stage (usually 'Vendor Registration')
    """
    try:
        # Get the first stage by order or default to 'REG' stage code
        stage = VendorLifecycleStages.objects.filter(
            is_active=True
        ).order_by('stage_order').first()
        
        if not stage:
            # Fallback to REG stage code if available
            stage = VendorLifecycleStages.objects.filter(
                stage_code='REG',
                is_active=True
            ).first()
        
        return stage.stage_id if stage else 1  # Default to 1 if no stages found
    except Exception:
        return 1  # Fallback default
