"""
Vendor Risk Assessment Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db.models import Q, Count, Avg
from django.db import connection
from django.db import connections
import json
import logging

from .models import VendorRiskAssessments, VendorRiskFactors, VendorRiskThresholds, VendorLifecycleStages, RiskTPRM
from .serializers import (
    VendorRiskAssessmentSerializer, 
    VendorRiskFactorSerializer,
    VendorRiskThresholdSerializer,
    VendorLifecycleStageSerializer
)

# RBAC imports
from tprm_backend.apps.vendor_core.vendor_authentication import VendorAuthenticationMixin, JWTAuthentication, SimpleAuthenticatedPermission

logger = logging.getLogger(__name__)


class VendorRiskAssessmentViewSet(VendorAuthenticationMixin, viewsets.ModelViewSet):
    """ViewSet for Vendor Risk Assessments with RBAC protection"""
    queryset = VendorRiskAssessments.objects.all()
    serializer_class = VendorRiskAssessmentSerializer
    
    def get_queryset(self):
        """Filter assessments based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by vendor if provided
        vendor_id = self.request.query_params.get('vendor_id')
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset


class VendorRiskFactorViewSet(VendorAuthenticationMixin, viewsets.ModelViewSet):
    """ViewSet for Vendor Risk Factors with RBAC protection"""
    queryset = VendorRiskFactors.objects.all()
    serializer_class = VendorRiskFactorSerializer
    
    def get_queryset(self):
        """Filter factors based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by assessment if provided
        assessment_id = self.request.query_params.get('assessment_id')
        if assessment_id:
            queryset = queryset.filter(assessment_id=assessment_id)
        
        return queryset


class VendorRiskThresholdViewSet(VendorAuthenticationMixin, viewsets.ModelViewSet):
    """ViewSet for Vendor Risk Thresholds with RBAC protection"""
    queryset = VendorRiskThresholds.objects.all()
    serializer_class = VendorRiskThresholdSerializer


class VendorLifecycleStageViewSet(VendorAuthenticationMixin, viewsets.ModelViewSet):
    """ViewSet for Vendor Lifecycle Stages with RBAC protection"""
    queryset = VendorLifecycleStages.objects.all()
    serializer_class = VendorLifecycleStageSerializer


class VendorRiskDashboardAPIView(APIView):
    """API view for vendor risk dashboard data with RBAC protection"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def get(self, request):
        """Get dashboard statistics and recent risks"""
        try:
            from django.db.models import Count, Case, When, IntegerField, Avg, F, Q
            from .models import RiskTPRM  # Make sure to import your model
            
            # Base queryset for vendor risks
            base_queryset = RiskTPRM.objects.filter(
                entity__in=['vendor', 'vendor_management']
            )
            
            # Get risk statistics using aggregation
            statistics = base_queryset.aggregate(
                total_risks=Count('id'),
                critical_risks=Count(Case(
                    When(priority='Critical', then=1),
                    output_field=IntegerField(),
                )),
                high_risks=Count(Case(
                    When(priority='High', then=1),
                    output_field=IntegerField(),
                )),
                medium_risks=Count(Case(
                    When(priority='Medium', then=1),
                    output_field=IntegerField(),
                )),
                low_risks=Count(Case(
                    When(priority='Low', then=1),
                    output_field=IntegerField(),
                )),
                average_score=Avg('score'),
            )
            
            # Round average score to 2 decimal places
            if statistics['average_score'] is not None:
                statistics['average_score'] = round(float(statistics['average_score']), 2)
            else:
                statistics['average_score'] = 0
                
            # Get recent risks
            recent_risks = base_queryset.order_by('-created_at')[:20].values(
                'id', 'title', 'description', 'likelihood', 'impact', 'score',
                'priority', 'ai_explanation', 'suggested_mitigations', 'status',
                'exposure_rating', 'risk_type', 'entity', 'data', 'row',
                'created_at', 'updated_at'
            )
            
            # Process recent risks
            recent_risks_list = []
            for risk in recent_risks:
                # Convert datetime objects to ISO format strings
                if risk.get('created_at'):
                    risk['created_at'] = risk['created_at'].isoformat()
                if risk.get('updated_at'):
                    risk['updated_at'] = risk['updated_at'].isoformat()
                    
                # Parse JSON fields
                if risk.get('suggested_mitigations'):
                    try:
                        if isinstance(risk['suggested_mitigations'], str):
                            risk['suggested_mitigations'] = json.loads(risk['suggested_mitigations'])
                        elif not isinstance(risk['suggested_mitigations'], list):
                            risk['suggested_mitigations'] = []
                    except (json.JSONDecodeError, TypeError):
                        if isinstance(risk['suggested_mitigations'], str):
                            mitigations = [m.strip() for m in risk['suggested_mitigations'].split('\n') if m.strip()]
                            risk['suggested_mitigations'] = mitigations
                        else:
                            risk['suggested_mitigations'] = []
                else:
                    risk['suggested_mitigations'] = []
                
                recent_risks_list.append(risk)
            
            # Get vendor modules (simplified for now)
            modules = [
                {
                    'module_id': 1,
                    'name': 'Vendor Management',
                    'description': 'Core vendor management functionality',
                    'created_at': '2024-01-01T00:00:00Z',
                    'updated_at': '2024-01-01T00:00:00Z'
                }
            ]
            
            dashboard_data = {
                'statistics': statistics,
                'recent_risks': recent_risks_list,
                'modules': modules
            }
            
            return Response(dashboard_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching vendor risk dashboard: {str(e)}", exc_info=True)
            logger.error("Query parameters: %s", request.query_params)
            return Response(
                {'error': 'Failed to fetch dashboard data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VendorRisksAPIView(APIView):
    """API view for vendor risks with filtering and pagination with RBAC protection"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def get(self, request):
        """Get vendor risks with filtering"""
        try:
            # Get query parameters
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            priority = request.query_params.get('priority')
            risk_type = request.query_params.get('risk_type')
            search = request.query_params.get('search')
            vendor_id = request.query_params.get('vendor_id')
            
            # Build WHERE clause
            where_conditions = ["entity IN ('vendor', 'vendor_management')"]
            params = []
            
            # Add filters
            if priority and priority != 'All':
                where_conditions.append("priority = %s")
                params.append(priority)
            
            if risk_type and risk_type != 'All':
                where_conditions.append("risk_type = %s")
                params.append(risk_type)
            
            if search:
                where_conditions.append("(title LIKE %s OR description LIKE %s)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            if vendor_id:
                where_conditions.append("`row` = %s")
                params.append(vendor_id)
            
            where_clause = " AND ".join(where_conditions)
            
            with connections['default'].cursor() as cursor:
                # Get total count
                count_query = f"SELECT COUNT(*) FROM risk_tprm WHERE {where_clause}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # Get paginated results
                offset = (page - 1) * page_size
                data_query = f"""
                    SELECT 
                        id, title, description, likelihood, impact, score, priority,
                        ai_explanation, suggested_mitigations, status, exposure_rating,
                        risk_type, entity, `data`, `row`, created_at, updated_at
                    FROM risk_tprm 
                    WHERE {where_clause}
                    ORDER BY id ASC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(data_query, params + [page_size, offset])
                
                columns = [col[0] for col in cursor.description]
                risks = []
                for row in cursor.fetchall():
                    risk_dict = dict(zip(columns, row))
                    # Parse JSON fields
                    if risk_dict.get('suggested_mitigations'):
                        try:
                            risk_dict['suggested_mitigations'] = json.loads(risk_dict['suggested_mitigations'])
                        except (json.JSONDecodeError, TypeError):
                            risk_dict['suggested_mitigations'] = []
                    else:
                        risk_dict['suggested_mitigations'] = []
                    
                    risks.append(risk_dict)
                
                # Calculate pagination info
                total_pages = (total_count + page_size - 1) // page_size
                has_next = page < total_pages
                has_previous = page > 1
                
                response_data = {
                    'results': risks,
                    'count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_previous': has_previous
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error fetching vendor risks: {str(e)}", exc_info=True)
            logger.error("Query parameters: %s", request.query_params)
            logger.error("SQL Query: %s", data_query)
            logger.error("SQL Parameters: %s", params)
            return Response(
                {'error': 'Failed to fetch risks'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VendorModulesAPIView(APIView):
    """API view for vendor modules with RBAC protection"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def get(self, request):
        """Get available vendor modules"""
        try:
            # For now, return a simple module list
            # In a real implementation, this would come from a modules table
            modules = [
                {
                    'module_id': 1,
                    'name': 'Vendor Management',
                    'description': 'Core vendor management functionality',
                    'created_at': '2024-01-01T00:00:00Z',
                    'updated_at': '2024-01-01T00:00:00Z'
                },
                {
                    'module_id': 2,
                    'name': 'Vendor Onboarding',
                    'description': 'Vendor onboarding and registration',
                    'created_at': '2024-01-01T00:00:00Z',
                    'updated_at': '2024-01-01T00:00:00Z'
                },
                {
                    'module_id': 3,
                    'name': 'Vendor Assessment',
                    'description': 'Vendor risk and compliance assessment',
                    'created_at': '2024-01-01T00:00:00Z',
                    'updated_at': '2024-01-01T00:00:00Z'
                }
            ]
            
            return Response(modules, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching vendor modules: {str(e)}")
            return Response(
                {'error': 'Failed to fetch modules'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VendorListAPIView(APIView):
    """API view for getting list of vendors with RBAC protection"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def get(self, request):
        """Get list of vendors from temp_vendor table"""
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        id, vendor_code, company_name, legal_name, 
                        business_type, industry_sector, vendor_category,
                        risk_level, status, is_critical_vendor,
                        created_at, updated_at
                    FROM temp_vendor 
                    ORDER BY company_name ASC
                """)
                
                columns = [col[0] for col in cursor.description]
                vendors = []
                for row in cursor.fetchall():
                    vendor_dict = dict(zip(columns, row))
                    # Convert datetime objects to strings
                    if vendor_dict.get('created_at'):
                        vendor_dict['created_at'] = vendor_dict['created_at'].isoformat()
                    if vendor_dict.get('updated_at'):
                        vendor_dict['updated_at'] = vendor_dict['updated_at'].isoformat()
                    vendors.append(vendor_dict)
                
                return Response(vendors, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error fetching vendors: {str(e)}")
            return Response(
                {'error': 'Failed to fetch vendors'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VendorRiskGenerationAPIView(APIView):
    """API view for generating vendor risks using AI with RBAC protection"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def post(self, request):
        """Generate risks for a specific vendor"""
        try:
            module_name = request.data.get('module_name')
            if not module_name:
                return Response(
                    {'error': 'Module name is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            
            response_data = {
                'message': f'Successfully generated risks for {module_name}',
                'module_name': module_name,
                'data_source': 'temp_vendor',
                'risk_types': {
                    'llama_generated': 1,
                    'mock_risks': 0
                },
                'risks': mock_risks
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating vendor risks: {str(e)}")
            return Response(
                {'error': 'Failed to generate risks'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
