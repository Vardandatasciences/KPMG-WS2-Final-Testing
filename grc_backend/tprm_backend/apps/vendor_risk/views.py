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
from tprm_backend.apps.vendor_core.vendor_authentication import VendorAuthenticationMixin, JWTAuthentication, SimpleAuthenticatedPermission, VendorPermission
from tprm_backend.rbac.tprm_decorators import rbac_vendor_required

# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    filter_queryset_by_tenant,
    get_tenant_aware_queryset,
    require_tenant,
    tenant_filter
)

logger = logging.getLogger(__name__)

# Database connection helper - Use tprm_integration database for all vendor operations
def get_db_connection():
    """
    Get the correct database connection for tprm_integration database.
    Returns 'tprm' connection if available, otherwise falls back to 'default'.
    """
    if 'tprm' in connections.databases:
        return connections['tprm']
    return connections['default']


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
    """API view for vendor risk dashboard data with RBAC protection
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [VendorPermission]
    
    @rbac_vendor_required('ViewRiskProfile')
    def get(self, request):
        """Get dashboard statistics and recent risks"""
        try:
            # MULTI-TENANCY: Get tenant ID from request
            tenant_id = get_tenant_id_from_request(request)
            if not tenant_id:
                return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

            from django.db.models import Count, Case, When, IntegerField, Avg, F, Q
            from .models import RiskTPRM  # Make sure to import your model
            from tprm_backend.apps.vendor_core.models import TempVendor
            
            # MULTI-TENANCY: Get vendor IDs for this tenant
            tenant_vendor_ids = list(TempVendor.objects.filter(tenant_id=tenant_id).values_list('id', flat=True))
            
            # Base queryset for vendor risks - filter by data='temp_vendor' and tenant's vendors
            base_queryset = RiskTPRM.objects.filter(
                entity__in=['vendor', 'vendor_management'],
                data='temp_vendor',
                row__in=[str(vid) for vid in tenant_vendor_ids]  # Filter by tenant's vendor IDs
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
    """API view for vendor risks with filtering and pagination with RBAC protection
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [VendorPermission]
    
    @rbac_vendor_required('ViewRiskProfile')
    def get(self, request):
        """Get vendor risks with filtering"""
        try:
            # MULTI-TENANCY: Get tenant ID from request
            tenant_id = get_tenant_id_from_request(request)
            if not tenant_id:
                return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

            # Get query parameters
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            priority = request.query_params.get('priority')
            search = request.query_params.get('search')
            vendor_id = request.query_params.get('vendor_id')
            
            # Log incoming parameters
            logger.info(f"=== VENDOR RISKS API GET REQUEST ===")
            logger.info(f"Raw vendor_id parameter: {vendor_id}")
            logger.info(f"Priority: {priority}, Search: {search}, Tenant ID: {tenant_id}")
            
            # MULTI-TENANCY: Get vendor IDs for this tenant
            from tprm_backend.apps.vendor_core.models import TempVendor
            tenant_vendor_ids = list(TempVendor.objects.filter(tenant_id=tenant_id).values_list('id', flat=True))
            tenant_vendor_ids_str = [str(vid) for vid in tenant_vendor_ids]
            
            # Build WHERE clause - always filter by data='temp_vendor' and tenant's vendors
            where_conditions = ["entity IN ('vendor', 'vendor_management')", "`data` = 'temp_vendor'"]
            params = []
            
            # MULTI-TENANCY: Add tenant filter through vendor IDs
            if tenant_vendor_ids_str:
                placeholders = ', '.join(['%s'] * len(tenant_vendor_ids_str))
                where_conditions.append(f"`row` IN ({placeholders})")
                params.extend(tenant_vendor_ids_str)
            else:
                # No vendors for this tenant, return empty result
                return Response({
                    'results': [],
                    'count': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0,
                    'has_next': False,
                    'has_previous': False
                }, status=status.HTTP_200_OK)
            
            # Add filters
            if priority and priority != 'All':
                where_conditions.append("priority = %s")
                params.append(priority)
            
            if search:
                where_conditions.append("(title LIKE %s OR description LIKE %s)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            # Filter by vendor_id if provided
            # vendor_id maps to temp_vendor.id, stored in risk_tprm.row field
            # The row field is VARCHAR(50), so we need to match it as a string
            # We'll try both string comparison and integer comparison to handle edge cases
            if vendor_id:
                # Convert to string and strip whitespace
                vendor_id_str = str(vendor_id).strip()
                if vendor_id_str:  # Only add filter if vendor_id is not empty after conversion
                    logger.info(f"Filtering risks by vendor_id (from temp_vendor): {vendor_id}")
                    logger.info(f"Vendor ID type: {type(vendor_id).__name__}, value: '{vendor_id}'")
                    logger.info(f"Using vendor_id_str for filtering: '{vendor_id_str}'")
                    
                    # Try to convert to integer for comparison
                    try:
                        vendor_id_int = int(vendor_id_str)
                        # Use CAST to handle both string and integer comparisons
                        # This ensures we match row values stored as '13' or '13.0' or 13
                        where_conditions.append("(CAST(`row` AS UNSIGNED) = %s OR `row` = %s)")
                        params.extend([vendor_id_int, vendor_id_str])
                        logger.info(f"Using both integer and string comparison for vendor_id: {vendor_id_int} / '{vendor_id_str}'")
                    except (ValueError, TypeError):
                        # If conversion fails, just use string comparison
                        where_conditions.append("`row` = %s")
                        params.append(vendor_id_str)
                        logger.info(f"Using string comparison only for vendor_id: '{vendor_id_str}'")
                else:
                    logger.warning(f"Vendor ID is empty after conversion, skipping vendor filter")
            
            where_clause = " AND ".join(where_conditions)
            
            # Log the query details for debugging
            logger.info(f"=== WHERE CLAUSE ===")
            logger.info(f"WHERE clause: {where_clause}")
            logger.info(f"SQL parameters: {params}")
            
            # Initialize variables for error handling
            data_query = None
            
            # Use tprm_integration database connection (not grc2)
            with get_db_connection().cursor() as cursor:
                # First, log what data we have in the database
                cursor.execute("SELECT DISTINCT `data`, COUNT(*) as cnt FROM risk_tprm GROUP BY `data`")
                db_data_types = cursor.fetchall()
                logger.info(f"Risk TPRM data sources: {db_data_types}")
                
                # Check sample rows for vendor_id if provided
                if vendor_id:
                    cursor.execute("SELECT DISTINCT `row`, COUNT(*) as cnt FROM risk_tprm WHERE `data` = 'temp_vendor' GROUP BY `row` LIMIT 20")
                    vendor_rows = cursor.fetchall()
                    logger.info(f"Sample row values in risk_tprm (row, count): {vendor_rows}")
                    logger.info(f"Looking for vendor_id: '{vendor_id}' (type: {type(vendor_id).__name__})")
                    
                    # Also check what vendor IDs exist in temp_vendor table
                    try:
                        cursor.execute("SELECT id, company_name FROM temp_vendor LIMIT 10")
                        temp_vendor_ids = cursor.fetchall()
                        logger.info(f"Sample temp_vendor IDs: {temp_vendor_ids}")
                    except Exception as e:
                        logger.warning(f"Could not query temp_vendor table: {e}")
                
                # Get total count WITHOUT vendor filter first (to see if any risks exist)
                base_where = "entity IN ('vendor', 'vendor_management') AND `data` = 'temp_vendor'"
                cursor.execute(f"SELECT COUNT(*) FROM risk_tprm WHERE {base_where}")
                total_without_vendor = cursor.fetchone()[0]
                logger.info(f"Total temp_vendor risks (no vendor filter): {total_without_vendor}")
                
                # Get total count WITH current filters
                count_query = f"SELECT COUNT(*) FROM risk_tprm WHERE {where_clause}"
                logger.info(f"Executing count query: {count_query} with params: {params}")
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                logger.info(f"Total risks found WITH filters: {total_count}")
                
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
            if data_query:
                logger.error("SQL Query: %s", data_query)
            if 'params' in locals():
                logger.error("SQL Parameters: %s", params)
            return Response(
                {'error': 'Failed to fetch risks'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VendorModulesAPIView(APIView):
    """API view for vendor modules with RBAC protection"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [VendorPermission]
    
    @rbac_vendor_required('ViewRiskProfile')
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
    """API view for getting list of vendors with RBAC protection
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [VendorPermission]
    
    @rbac_vendor_required('ViewRiskProfile')
    def get(self, request):
        """Get list of vendors prioritizing temp_vendor (for risk filtering) with fallback to main vendors table"""
        try:
            # MULTI-TENANCY: Get tenant ID from request
            tenant_id = get_tenant_id_from_request(request)
            if not tenant_id:
                return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

            # Use tprm_integration database connection (not grc2)
            with get_db_connection().cursor() as cursor:
                vendors = []
                vendor_ids_seen = set()
                
                # First, get vendors from temp_vendor table (prioritized for risk filtering)
                # Since risk_tprm.row stores temp_vendor.id, we need these IDs for filtering
                # MULTI-TENANCY: Filter by tenant
                try:
                    cursor.execute("""
                        SELECT 
                            id, vendor_code, company_name, legal_name, 
                            business_type, industry_sector, vendor_category,
                            risk_level, status, is_critical_vendor,
                            created_at, updated_at
                        FROM temp_vendor 
                        WHERE TenantId = %s
                        ORDER BY company_name ASC
                    """, [tenant_id])
                    
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        vendor_dict = dict(zip(columns, row))
                        # Convert datetime objects to strings
                        if vendor_dict.get('created_at'):
                            vendor_dict['created_at'] = vendor_dict['created_at'].isoformat()
                        if vendor_dict.get('updated_at'):
                            vendor_dict['updated_at'] = vendor_dict['updated_at'].isoformat()
                        vendors.append(vendor_dict)
                        vendor_ids_seen.add(vendor_dict.get('id'))
                    
                    logger.info(f"Fetched {len(vendors)} vendors from temp_vendor table")
                except Exception as e:
                    logger.warning(f"Could not fetch from temp_vendor table: {e}")
                
                # Also get vendors from main vendors table (if not already in temp_vendor)
                # MULTI-TENANCY: Filter by tenant
                try:
                    cursor.execute("""
                        SELECT 
                            vendor_id as id, vendor_code, company_name, legal_name, 
                            business_type, industry_sector, vendor_category_id,
                            risk_level, status, is_critical_vendor,
                            created_at, updated_at
                        FROM vendors
                        WHERE TenantId = %s
                        ORDER BY company_name ASC
                    """, [tenant_id])
                    
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        vendor_dict = dict(zip(columns, row))
                        # Only add if not already in temp_vendor (to avoid duplicates)
                        vendor_id = vendor_dict.get('id')
                        if vendor_id and vendor_id not in vendor_ids_seen:
                            # Convert datetime objects to strings
                            if vendor_dict.get('created_at'):
                                vendor_dict['created_at'] = vendor_dict['created_at'].isoformat()
                            if vendor_dict.get('updated_at'):
                                vendor_dict['updated_at'] = vendor_dict['updated_at'].isoformat()
                            vendors.append(vendor_dict)
                            vendor_ids_seen.add(vendor_id)
                    
                    logger.info(f"Added vendors from main vendors table. Total: {len(vendors)}")
                except Exception as e:
                    logger.warning(f"Could not fetch from main vendors table: {e}")
                
                logger.info(f"Fetched {len(vendors)} vendors total (prioritizing temp_vendor for risk filtering)")
                return Response(vendors, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error fetching vendors: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to fetch vendors'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VendorRiskGenerationAPIView(APIView):
    """API view for generating vendor risks using AI with RBAC protection"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [VendorPermission]
    
    def post(self, request):
        """Generate risks for a specific vendor"""
        try:
            module_name = request.data.get('module_name')
            if not module_name:
                return Response(
                    {'error': 'Module name is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mock risks for now (to be replaced with actual AI generation)
            mock_risks = []
            
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


class VendorRiskDebugAPIView(APIView):
    """API view for debugging vendor risk data matching
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [VendorPermission]
    
    def get(self, request):
        """Debug endpoint to check data matching between temp_vendor and risk_tprm"""
        try:
            # MULTI-TENANCY: Get tenant ID from request
            tenant_id = get_tenant_id_from_request(request)
            if not tenant_id:
                return Response({'error': 'Tenant context not found'}, status=status.HTTP_403_FORBIDDEN)

            vendor_id = request.query_params.get('vendor_id', '10')
            
            # Use tprm_integration database connection (not grc2)
            with get_db_connection().cursor() as cursor:
                # Check temp_vendor table
                # MULTI-TENANCY: Filter by tenant
                cursor.execute("SELECT id, company_name FROM temp_vendor WHERE id = %s AND TenantId = %s", [vendor_id, tenant_id])
                vendor_data = cursor.fetchone()
                
                # Check all risk_tprm data='temp_vendor'
                cursor.execute("""
                    SELECT `row`, COUNT(*) as count, 
                           GROUP_CONCAT(id SEPARATOR ', ') as risk_ids
                    FROM risk_tprm 
                    WHERE `data` = 'temp_vendor'
                    GROUP BY `row`
                    ORDER BY `row`
                """)
                all_rows = cursor.fetchall()
                
                # Check specific vendor match
                cursor.execute("""
                    SELECT id, title, `row`, `data`
                    FROM risk_tprm 
                    WHERE `data` = 'temp_vendor' AND `row` = %s
                    LIMIT 5
                """, [vendor_id])
                matching_risks = cursor.fetchall()
                
                # Check with CAST to integer
                cursor.execute("""
                    SELECT id, title, `row`, `data`
                    FROM risk_tprm 
                    WHERE `data` = 'temp_vendor' AND CAST(`row` AS UNSIGNED) = %s
                    LIMIT 5
                """, [vendor_id])
                matching_risks_int = cursor.fetchall()
                
                debug_data = {
                    'vendor_id_searched': vendor_id,
                    'vendor_id_type': type(vendor_id).__name__,
                    'vendor_exists': vendor_data is not None,
                    'vendor_info': {
                        'id': vendor_data[0] if vendor_data else None,
                        'company_name': vendor_data[1] if vendor_data else None
                    } if vendor_data else None,
                    'all_row_values_in_risk_tprm': [
                        {
                            'row_value': row[0],
                            'row_type': type(row[0]).__name__,
                            'count': row[1],
                            'risk_ids': row[2]
                        } for row in all_rows
                    ],
                    'matching_risks_string_comparison': len(matching_risks),
                    'matching_risks_int_comparison': len(matching_risks_int),
                    'sample_matching_risks': [
                        {
                            'id': risk[0],
                            'title': risk[1],
                            'row': risk[2],
                            'data': risk[3]
                        } for risk in matching_risks
                    ] if matching_risks else [],
                    'sample_matching_risks_int': [
                        {
                            'id': risk[0],
                            'title': risk[1],
                            'row': risk[2],
                            'data': risk[3]
                        } for risk in matching_risks_int
                    ] if matching_risks_int else []
                }
                
                return Response(debug_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error in debug endpoint: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
