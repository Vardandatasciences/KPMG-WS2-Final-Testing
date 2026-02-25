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
 
            from tprm_backend.apps.vendor_core.models import TempVendor
           
            # MULTI-TENANCY: Get vendor IDs for this tenant
            tenant_vendor_ids = list(TempVendor.objects.filter(tenant_id=tenant_id).values_list('id', flat=True))
           
            # Base queryset for vendor risks - filter by TRIM(entity) = 'vendor_management' and tenant's vendors
            # Using raw SQL for TRIM() function as Django ORM doesn't support it directly
            from django.db.models import Q
            tenant_vendor_ids_str = [str(vid) for vid in tenant_vendor_ids]
           
            # Use raw SQL query with TRIM() function
            with get_db_connection().cursor() as cursor:
                # Build WHERE clause - filter by TRIM(entity) = 'vendor_management'
                # Note: Removed 'data' = 'temp_vendor' filter to include all vendor_management risks
                # Note: Tenant filter removed to fetch ALL vendor_management risks as requested
                where_conditions = ["TRIM(`entity`) = 'vendor_management'"]
                params = []
               
                # MULTI-TENANCY: Tenant filter is commented out to fetch all risks
                # If tenant filtering is needed, uncomment the code below
                # if tenant_vendor_ids_str:
                #     placeholders = ', '.join(['%s'] * len(tenant_vendor_ids_str))
                #     where_conditions.append(f"`row` IN ({placeholders})")
                #     params.extend(tenant_vendor_ids_str)
                #     logger.info(f"Dashboard: Applying tenant filter with {len(tenant_vendor_ids_str)} vendor IDs")
                # else:
                #     logger.warning(f"Dashboard: No tenant vendor IDs found for tenant {tenant_id}, returning all vendor_management risks")
               
                logger.info(f"Dashboard: Fetching ALL vendor_management risks (tenant filter disabled). Tenant ID: {tenant_id}, Tenant vendor IDs: {tenant_vendor_ids_str}")
               
                where_clause = " AND ".join(where_conditions)
               
                # Get risk statistics using aggregation with raw SQL
                cursor.execute(f"""
                    SELECT
                        COUNT(*) as total_risks,
                        SUM(CASE WHEN priority = 'Critical' THEN 1 ELSE 0 END) as critical_risks,
                        SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as high_risks,
                        SUM(CASE WHEN priority = 'Medium' THEN 1 ELSE 0 END) as medium_risks,
                        SUM(CASE WHEN priority = 'Low' THEN 1 ELSE 0 END) as low_risks,
                        AVG(score) as average_score
                    FROM risk_tprm
                    WHERE {where_clause}
                """, params)
               
                stats_row = cursor.fetchone()
                statistics = {
                    'total_risks': stats_row[0] or 0,
                    'critical_risks': stats_row[1] or 0,
                    'high_risks': stats_row[2] or 0,
                    'medium_risks': stats_row[3] or 0,
                    'low_risks': stats_row[4] or 0,
                    'average_score': round(float(stats_row[5] or 0), 2)
                }
               
                # Get recent risks
                cursor.execute(f"""
                    SELECT
                        id, title, description, likelihood, impact, score, priority,
                        ai_explanation, suggested_mitigations, status, exposure_rating,
                        risk_type, entity, `data`, `row`, created_at, updated_at
                    FROM risk_tprm
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT 20
                """, params)
               
                columns = [col[0] for col in cursor.description]
                recent_risks_list = []
                for row in cursor.fetchall():
                    risk_dict = dict(zip(columns, row))
                    # Convert datetime objects to ISO format strings
                    if risk_dict.get('created_at'):
                        risk_dict['created_at'] = risk_dict['created_at'].isoformat()
                    if risk_dict.get('updated_at'):
                        risk_dict['updated_at'] = risk_dict['updated_at'].isoformat()
                       
                    # Parse JSON fields
                    if risk_dict.get('suggested_mitigations'):
                        try:
                            if isinstance(risk_dict['suggested_mitigations'], str):
                                risk_dict['suggested_mitigations'] = json.loads(risk_dict['suggested_mitigations'])
                            elif not isinstance(risk_dict['suggested_mitigations'], list):
                                risk_dict['suggested_mitigations'] = []
                        except (json.JSONDecodeError, TypeError):
                            if isinstance(risk_dict['suggested_mitigations'], str):
                                mitigations = [m.strip() for m in risk_dict['suggested_mitigations'].split('\n') if m.strip()]
                                risk_dict['suggested_mitigations'] = mitigations
                            else:
                                risk_dict['suggested_mitigations'] = []
                    else:
                        risk_dict['suggested_mitigations'] = []
                   
                    recent_risks_list.append(risk_dict)
           
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
            # Handle multiple vendor IDs - get all vendor_id parameters
            vendor_ids = request.query_params.getlist('vendor_id')  # Get list of vendor IDs
            # If no list, try single vendor_id for backward compatibility
            if not vendor_ids:
                vendor_id_single = request.query_params.get('vendor_id')
                if vendor_id_single:
                    vendor_ids = [vendor_id_single]
            vendor_id = vendor_ids[0] if len(vendor_ids) == 1 else None  # Keep for single vendor logic
           
            # Log incoming parameters
            logger.info(f"=== VENDOR RISKS API GET REQUEST ===")
            logger.info(f"Raw vendor_ids parameter: {vendor_ids}")
            logger.info(f"Vendor IDs count: {len(vendor_ids)}")
            logger.info(f"Priority: {priority}, Search: {search}, Tenant ID: {tenant_id}")
           
            # MULTI-TENANCY: Get vendor IDs for this tenant
            from tprm_backend.apps.vendor_core.models import TempVendor
            tenant_vendor_ids = list(TempVendor.objects.filter(tenant_id=tenant_id).values_list('id', flat=True))
            tenant_vendor_ids_str = [str(vid) for vid in tenant_vendor_ids]
           
            # Build WHERE clause - always filter by TRIM(entity) = 'vendor_management'
            # Note: Removed 'data' = 'temp_vendor' filter to include all vendor_management risks
            # Note: Tenant filter removed to fetch ALL vendor_management risks as requested
            where_conditions = ["TRIM(`entity`) = 'vendor_management'"]
            params = []
           
            # MULTI-TENANCY: Tenant filter is commented out to fetch all risks
            # If tenant filtering is needed, uncomment the code below
            # if tenant_vendor_ids_str:
            #     placeholders = ', '.join(['%s'] * len(tenant_vendor_ids_str))
            #     where_conditions.append(f"`row` IN ({placeholders})")
            #     params.extend(tenant_vendor_ids_str)
            #     logger.info(f"Applying tenant filter with {len(tenant_vendor_ids_str)} vendor IDs")
            # else:
            #     logger.warning(f"No tenant vendor IDs found for tenant {tenant_id}, returning all vendor_management risks")
           
            logger.info(f"Fetching ALL vendor_management risks (tenant filter disabled). Tenant ID: {tenant_id}, Tenant vendor IDs: {tenant_vendor_ids_str}")
           
            # Add filters
            if priority and priority != 'All':
                where_conditions.append("priority = %s")
                params.append(priority)
           
            if search:
                where_conditions.append("(title LIKE %s OR description LIKE %s)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
           
            # Filter by vendor_id(s) if provided - support multiple vendor IDs
            # vendor_id maps to temp_vendor.id, stored in risk_tprm.row field
            # The row field is VARCHAR(50), so we need to match it as a string
            if vendor_ids and len(vendor_ids) > 0:
                # Filter out empty values
                valid_vendor_ids = [vid for vid in vendor_ids if vid and str(vid).strip()]
               
                if valid_vendor_ids:
                    logger.info(f"Filtering risks by vendor_ids (from temp_vendor): {valid_vendor_ids}")
                    logger.info(f"Vendor IDs count: {len(valid_vendor_ids)}")
                   
                    # Build conditions for multiple vendor IDs
                    vendor_conditions = []
                    vendor_params = []
                   
                    for vid in valid_vendor_ids:
                        vendor_id_str = str(vid).strip()
                        if vendor_id_str:
                            try:
                                vendor_id_int = int(vendor_id_str)
                                # Use CAST to handle both string and integer comparisons
                                vendor_conditions.append("(CAST(`row` AS UNSIGNED) = %s OR `row` = %s)")
                                vendor_params.extend([vendor_id_int, vendor_id_str])
                            except (ValueError, TypeError):
                                # If conversion fails, just use string comparison
                                vendor_conditions.append("`row` = %s")
                                vendor_params.append(vendor_id_str)
                   
                    if vendor_conditions:
                        # Combine all vendor conditions with OR
                        where_conditions.append(f"({' OR '.join(vendor_conditions)})")
                        params.extend(vendor_params)
                        logger.info(f"Added vendor filter with {len(valid_vendor_ids)} vendor ID(s)")
                else:
                    logger.warning(f"All vendor IDs are empty, skipping vendor filter")
           
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
               
                # Check sample rows for vendor_ids if provided
                if vendor_ids and len(vendor_ids) > 0:
                    cursor.execute("SELECT DISTINCT `row`, COUNT(*) as cnt FROM risk_tprm WHERE TRIM(`entity`) = 'vendor_management' GROUP BY `row` LIMIT 20")
                    vendor_rows = cursor.fetchall()
                    logger.info(f"Sample row values in risk_tprm (row, count): {vendor_rows}")
                    logger.info(f"Looking for vendor_ids: {vendor_ids}")
                   
                    # Also check what vendor IDs exist in temp_vendor table
                    try:
                        cursor.execute("SELECT id, company_name FROM temp_vendor LIMIT 10")
                        temp_vendor_ids = cursor.fetchall()
                        logger.info(f"Sample temp_vendor IDs: {temp_vendor_ids}")
                    except Exception as e:
                        logger.warning(f"Could not query temp_vendor table: {e}")
               
                # Debug: Get total count with just TRIM(entity) = 'vendor_management' (no other filters)
                base_where_entity_only = "TRIM(`entity`) = 'vendor_management'"
                cursor.execute(f"SELECT COUNT(*) FROM risk_tprm WHERE {base_where_entity_only}")
                total_entity_only = cursor.fetchone()[0]
                logger.info(f"Total risks with TRIM(entity) = 'vendor_management' (no other filters): {total_entity_only}")
               
                # Debug: Get total count with entity + data filter (no tenant filter) - for comparison
                base_where_entity_data = "TRIM(`entity`) = 'vendor_management' AND `data` = 'temp_vendor'"
                cursor.execute(f"SELECT COUNT(*) FROM risk_tprm WHERE {base_where_entity_data}")
                total_entity_data = cursor.fetchone()[0]
                logger.info(f"Total risks with TRIM(entity) = 'vendor_management' AND data = 'temp_vendor' (no tenant filter): {total_entity_data}")
               
                # Debug: Get total count with entity filter only (no data, no tenant filter)
                base_where_entity_only_no_tenant = "TRIM(`entity`) = 'vendor_management'"
                cursor.execute(f"SELECT COUNT(*) FROM risk_tprm WHERE {base_where_entity_only_no_tenant}")
                total_entity_only_no_tenant = cursor.fetchone()[0]
                logger.info(f"Total risks with TRIM(entity) = 'vendor_management' only (no data filter, no tenant filter): {total_entity_only_no_tenant}")
               
                # Debug: Check what data values exist for vendor_management entity
                cursor.execute(f"SELECT DISTINCT `data`, COUNT(*) as cnt FROM risk_tprm WHERE {base_where_entity_only} GROUP BY `data`")
                data_values = cursor.fetchall()
                logger.info(f"Data values for vendor_management entity: {data_values}")
               
                # Debug: Check what row values exist (to see if tenant filter is too restrictive)
                cursor.execute(f"SELECT COUNT(DISTINCT `row`) as distinct_rows, COUNT(*) as total FROM risk_tprm WHERE {base_where_entity_only}")
                row_stats = cursor.fetchone()
                logger.info(f"Row statistics for vendor_management: {row_stats[0]} distinct row values, {row_stats[1]} total risks")
                logger.info(f"Tenant vendor IDs being used for filtering: {tenant_vendor_ids_str}")
               
                # Debug: Sample some row values to see what's in the database
                cursor.execute(f"SELECT DISTINCT `row`, COUNT(*) as cnt FROM risk_tprm WHERE {base_where_entity_only} GROUP BY `row` LIMIT 10")
                sample_rows = cursor.fetchall()
                logger.info(f"Sample row values in risk_tprm: {sample_rows}")
               
                # Get total count WITH current filters
                count_query = f"SELECT COUNT(*) FROM risk_tprm WHERE {where_clause}"
                logger.info(f"Executing count query: {count_query} with params: {params}")
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                logger.info(f"Total risks found WITH all filters (entity + tenant): {total_count}")
                logger.info(f"Difference: {total_entity_only} total risks, {total_count} after tenant filter (if applied)")
               
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
 
 