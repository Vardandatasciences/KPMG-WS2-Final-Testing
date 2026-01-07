import time
import logging
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import jwt

from .models import Risk
from .serializers import (
    RiskSerializer, RiskListSerializer, RiskDetailSerializer,
    RiskFilterSerializer, HeatmapDataSerializer
)
from .services import RiskAnalysisService
# BCP/DRP integration disabled - using entity-data-row approach
from .entity_service import EntityDataService

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


# Removed TPRMModuleViewSet and ModuleDataViewSet - using entity-data-row approach


class RiskViewSet(viewsets.ModelViewSet):
    """ViewSet for Risks
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['priority', 'status', 'risk_type', 'assigned_to']
    search_fields = ['title', 'description', 'ai_explanation']
    ordering_fields = ['id', 'created_at', 'updated_at', 'score', 'likelihood', 'impact', 'exposure_rating']
    ordering = ['id']
    
    def get_queryset(self):
        """Get filtered queryset based on request parameters
        MULTI-TENANCY: Filter by tenant
        """
        # MULTI-TENANCY: Filter by tenant
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            queryset = Risk.objects.filter(tenant_id=tenant_id)
        else:
            queryset = Risk.objects.all()
        
        # Apply custom filters (module filtering removed)
        priority = self.request.query_params.get('priority', None)
        status = self.request.query_params.get('status', None)
        risk_type = self.request.query_params.get('risk_type', None)
        min_score = self.request.query_params.get('min_score', None)
        max_score = self.request.query_params.get('max_score', None)
        min_likelihood = self.request.query_params.get('min_likelihood', None)
        max_likelihood = self.request.query_params.get('max_likelihood', None)
        min_impact = self.request.query_params.get('min_impact', None)
        max_impact = self.request.query_params.get('max_impact', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        assigned_to = self.request.query_params.get('assigned_to', None)
        
        # Removed module filtering since module_id no longer exists
        if priority:
            queryset = queryset.filter(priority=priority)
        if status:
            queryset = queryset.filter(status=status)
        if risk_type:
            queryset = queryset.filter(risk_type=risk_type)
        if min_score:
            queryset = queryset.filter(score__gte=min_score)
        if max_score:
            queryset = queryset.filter(score__lte=max_score)
        if min_likelihood:
            queryset = queryset.filter(likelihood__gte=min_likelihood)
        if max_likelihood:
            queryset = queryset.filter(likelihood__lte=max_likelihood)
        if min_impact:
            queryset = queryset.filter(impact__gte=min_impact)
        if max_impact:
            queryset = queryset.filter(impact__lte=max_impact)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        if assigned_to:
            queryset = queryset.filter(assigned_to=assigned_to)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return RiskListSerializer
        elif self.action == 'retrieve':
            return RiskDetailSerializer
        return RiskSerializer
    
    def perform_create(self, serializer):
        """Set created_by user when creating a risk
        MULTI-TENANCY: Set tenant_id on creation
        """
        tenant_id = get_tenant_id_from_request(self.request)
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            if tenant_id:
                serializer.save(created_by=self.request.user.id, tenant_id=tenant_id)
            else:
                serializer.save(created_by=self.request.user.id)
        else:
            if tenant_id:
                serializer.save(tenant_id=tenant_id)
            else:
                serializer.save()
    
    @action(detail=True, methods=['post'])
    def assign_owner(self, request, pk=None):
        """Assign an owner to a risk"""
        risk = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            risk.assigned_to = user_id
            risk.save()
            
            return Response({'message': 'Owner assigned successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to assign owner: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge a risk"""
        risk = self.get_object()
        risk.status = 'Acknowledged'
        risk.acknowledged_at = timezone.now()
        risk.save()
        
        return Response({'message': 'Risk acknowledged successfully'})
    
    @action(detail=True, methods=['post'])
    def mark_mitigated(self, request, pk=None):
        """Mark a risk as mitigated"""
        risk = self.get_object()
        risk.status = 'Mitigated'
        risk.mitigated_at = timezone.now()
        risk.save()
        
        return Response({'message': 'Risk marked as mitigated successfully'})


class RiskHeatmapViewSet(viewsets.ViewSet):
    """ViewSet for Risk Heatmap - dynamically generated from Risk data"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def list(self, request):
        """Get heatmap data dynamically from risk records"""
        try:
            service = RiskAnalysisService()
            module_name = request.query_params.get('module', None)
            
            if module_name:
                module = get_object_or_404(TPRMModule, name=module_name)
                heatmap_data = service.get_heatmap_data(module)
            else:
                heatmap_data = service.get_heatmap_data()
            
            serializer = HeatmapDataSerializer(heatmap_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting heatmap data: {e}")
            return Response(
                {'error': 'Failed to get heatmap data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Removed RiskPredictionAPIView and LlamaRiskGenerationAPIView - replaced by EntityRiskGenerationAPIView


class RiskStatisticsAPIView(APIView):
    """API view for risk statistics"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def get(self, request):
        """Get risk statistics"""
        try:
            service = RiskAnalysisService()
            module_name = request.query_params.get('module', None)
            
            # Module filtering removed - using entity-data-row approach
            stats = service.get_risk_statistics()
            
            return Response(stats)
        except Exception as e:
            logger.error(f"Error getting risk statistics: {e}")
            return Response(
                {'error': 'Failed to get risk statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardAPIView(APIView):
    """API view for dashboard data"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def get(self, request):
        """Get dashboard data including risks, heatmap, and statistics"""
        try:
            # Get risk statistics
            service = RiskAnalysisService()
            stats = service.get_risk_statistics()
            
            # Get recent risks
            recent_risks = Risk.objects.all()[:10]
            risk_serializer = RiskListSerializer(recent_risks, many=True)
            
            # Get heatmap data dynamically
            service = RiskAnalysisService()
            heatmap_data = service.get_heatmap_data()
            heatmap_serializer = HeatmapDataSerializer(heatmap_data, many=True)
            
            # Entity list now comes from EntityDataService
            entity_service = EntityDataService()
            entities = entity_service.get_available_entities()
            
            return Response({
                'statistics': stats,
                'recent_risks': risk_serializer.data,
                'heatmap_data': heatmap_serializer.data,
                'entities': entities
            })
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return Response(
                {'error': 'Failed to get dashboard data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# BCP/DRP integration disabled - replaced by EntityRiskGenerationAPIView using entity-data-row approach


class EntityDataDropdownAPIView(APIView):
    """API view for entity-data-row dropdown functionality"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def get(self, request):
        """Get dropdown data based on query parameters"""
        try:
            service = EntityDataService()
            action = request.query_params.get('action')
            
            if action == 'entities':
                # Get available entities
                entities = service.get_available_entities()
                return Response({
                    'entities': entities,
                    'message': f'Found {len(entities)} available entities'
                })
            
            elif action == 'tables':
                # Get tables for specific entity
                entity = request.query_params.get('entity')
                if not entity:
                    return Response(
                        {'error': 'entity parameter is required for tables action'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                tables = service.get_tables_for_entity(entity)
                return Response({
                    'entity': entity,
                    'tables': tables,
                    'message': f'Found {len(tables)} tables for {entity}'
                })
            
            elif action == 'rows':
                # Get rows for specific table
                table_name = request.query_params.get('table')
                if not table_name:
                    return Response(
                        {'error': 'table parameter is required for rows action'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                limit = int(request.query_params.get('limit', 50))
                rows = service.get_rows_for_table(table_name, limit)
                return Response({
                    'table_name': table_name,
                    'rows': rows,
                    'message': f'Found {len(rows)} rows for {table_name}'
                })
            
            else:
                return Response(
                    {'error': 'Invalid action. Use: entities, tables, or rows'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error in entity data dropdown API: {e}")
            return Response(
                {'error': 'Failed to get dropdown data', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EntityRiskGenerationAPIView(APIView):
    """
    API view for generating risks from entity-data-row selection - Microservice endpoint
    
    INTEGRATION GUIDE FOR OTHER MODULES:
    ====================================
    
    This is the MAIN API endpoint that other modules should use to generate risks.
    It accepts standardized requests and returns standardized risk responses.
    
    USAGE FROM YOUR MODULE:
    ----------------------
    
    # In your module's views.py or services.py:
    from contract_risk_analysis.services import RiskAnalysisService
    
    def your_module_function():
        service = RiskAnalysisService()
        result = service.analyze_entity_data_row(
            entity='your_module_name',      # e.g., 'vendor_management'
            table='your_table_name',        # e.g., 'vendor_profiles' 
            row_id='your_row_id'            # e.g., '123'
        )
        risks = result.get('risks', [])
        # Process the risks...
    
    # Or call directly via HTTP:
    import requests
    response = requests.post('/api/risk-analysis/entity-risk-generation/', {
        'entity': 'vendor_management',
        'table': 'vendor_profiles',
        'row_id': '123'
    })
    risks = response.json()['risks']
    
    See INTEGRATION_GUIDE.md for complete examples!
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def post(self, request):
        """
        Generate risks for specific entity-data-row selection
        
        Expected payload:
        {
          "entity": "contract_module",
          "table": "vendor_contracts", 
          "row_id": 101
        }
        
        OR comprehensive payload:
        {
          "entity": "contract_module",
          "table": "comprehensive_contract_data",
          "row_id": 101,
          "comprehensive_data": {
            "plan_info": {...},
            "extracted_details": {...},
            "evaluation_data": {...}
          }
        }
        
        Response format:
        {
          "risks": [
            {
              "id": "R-0105",
              "title": "Outdated Recovery Plan",
              "description": "The plan has not been updated in over 18 months.",
              "likelihood": 4,
              "impact": 5,
              "exposure_rating": 3,
              "score": 80,
              "priority": "Critical",
              "ai_explanation": "BCP plans must be tested and refreshed regularly...",
              "suggested_mitigations": [
                "Review and update recovery strategy",
                "Conduct a new plan evaluation"
              ]
            }
          ]
        }
        """
        try:
            entity = request.data.get('entity')
            table = request.data.get('table')
            row_id = request.data.get('row_id')
            comprehensive_data = request.data.get('comprehensive_data')
            
            # Validate required parameters
            if not all([entity, table, row_id]):
                return Response(
                    {'error': 'entity, table, and row_id are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use the main microservice function
            service = RiskAnalysisService()
            
            # Check if this is a comprehensive data request
            if table == 'comprehensive_plan_data' and comprehensive_data:
                result = service.analyze_comprehensive_plan_data(
                    entity=entity,
                    comprehensive_data=comprehensive_data
                )
            else:
                result = service.analyze_entity_data_row(
                    entity=entity,
                    table=table,
                    row_id=row_id
                )
            
            return Response(result)
            
        except ValueError as e:
            logger.error(f"Validation error in entity risk generation: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error generating risks from entity-data-row: {e}")
            return Response(
                {'error': 'Failed to generate risks', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """Get full row data for preview"""
        try:
            table_name = request.query_params.get('table')
            row_id = request.query_params.get('row_id')
            
            if not all([table_name, row_id]):
                return Response(
                    {'error': 'table and row_id parameters are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service = EntityDataService()
            row_data = service.get_full_row_data(table_name, row_id)
            
            return Response({
                'table_name': table_name,
                'row_id': row_id,
                'row_data': row_data
            })
            
        except Exception as e:
            logger.error(f"Error getting row data: {e}")
            return Response(
                {'error': 'Failed to get row data', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TaskStatusAPIView(APIView):
    """API view for checking background task status"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    
    def get(self, request, task_id):
        """Get status of a background task"""
        try:
            from celery.result import AsyncResult
            
            # Get task result
            task_result = AsyncResult(task_id)
            
            response_data = {
                'task_id': task_id,
                'status': task_result.status,
                'ready': task_result.ready()
            }
            
            if task_result.ready():
                if task_result.successful():
                    response_data['result'] = task_result.result
                else:
                    response_data['error'] = str(task_result.result)
            else:
                response_data['message'] = 'Task is still processing...'
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error checking task status for {task_id}: {e}")
            return Response(
                {'error': 'Failed to check task status', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
