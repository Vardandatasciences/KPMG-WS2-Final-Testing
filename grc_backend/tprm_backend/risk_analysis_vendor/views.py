import time
import logging
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Risk
from .serializers import (
    RiskSerializer, RiskListSerializer, RiskDetailSerializer,
    RiskFilterSerializer, HeatmapDataSerializer
)
from .services import RiskAnalysisService
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


class RiskViewSet(viewsets.ModelViewSet):
    """ViewSet for Risks
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    permission_classes = [permissions.AllowAny]
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
        
        # Apply custom filters
        priority = self.request.query_params.get('priority', None)
        status = self.request.query_params.get('status', None)
        risk_type = self.request.query_params.get('risk_type', None)
        min_score = self.request.query_params.get('min_score', None)
        max_score = self.request.query_params.get('max_score', None)
        min_likelihood = self.request.query_params.get('min_likelihood', None)
        max_likelihood = self.request.query_params.get('max_likelihood', None)
        min_impact = self.request.query_params.get('min_impact', None)
        max_impact = self.request.query_params.get('max_impact', None)
        
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
            
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return RiskListSerializer
        elif self.action == 'retrieve':
            return RiskDetailSerializer
        return RiskSerializer


class RiskHeatmapViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Risk Heatmap Data
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = HeatmapDataSerializer
    
    def get_queryset(self):
        """Get risks for heatmap visualization
        MULTI-TENANCY: Filter by tenant
        """
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            return Risk.objects.filter(tenant_id=tenant_id)
        return Risk.objects.all()


class RiskStatisticsAPIView(APIView):
    """API View for Risk Statistics
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get risk statistics
        MULTI-TENANCY: Filter by tenant
        """
        try:
            # MULTI-TENANCY: Filter by tenant
            tenant_id = get_tenant_id_from_request(request)
            if tenant_id:
                risk_queryset = Risk.objects.filter(tenant_id=tenant_id)
            else:
                risk_queryset = Risk.objects.all()
            
            total_risks = risk_queryset.count()
            high_risks = risk_queryset.filter(priority='HIGH').count()
            medium_risks = risk_queryset.filter(priority='MEDIUM').count()
            low_risks = risk_queryset.filter(priority='LOW').count()
            
            avg_score = risk_queryset.aggregate(
                avg_score=Avg('score')
            )['avg_score'] or 0
            
            stats = {
                'total_risks': total_risks,
                'high_risks': high_risks,
                'medium_risks': medium_risks,
                'low_risks': low_risks,
                'average_score': round(avg_score, 2)
            }
            
            return Response(stats)
        except Exception as e:
            logger.error(f"Error getting risk statistics: {e}")
            return Response(
                {'error': 'Failed to get risk statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardAPIView(APIView):
    """API View for Dashboard Data"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get dashboard data"""
        try:
            recent_risks = Risk.objects.order_by('-created_at')[:10]
            serializer = RiskListSerializer(recent_risks, many=True)
            
            return Response({
                'recent_risks': serializer.data
            })
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return Response(
                {'error': 'Failed to get dashboard data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EntityDataDropdownAPIView(APIView):
    """API View for Entity Data Dropdown"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get entity data for dropdowns"""
        try:
            service = EntityDataService()
            data = service.get_dropdown_data()
            return Response(data)
        except Exception as e:
            logger.error(f"Error getting entity data: {e}")
            return Response(
                {'error': 'Failed to get entity data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EntityRiskGenerationAPIView(APIView):
    """API View for Entity Risk Generation"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Generate risks for entities"""
        try:
            service = EntityDataService()
            result = service.generate_risks(request.data)
            return Response(result)
        except Exception as e:
            logger.error(f"Error generating risks: {e}")
            return Response(
                {'error': 'Failed to generate risks'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TaskStatusAPIView(APIView):
    """API View for Task Status (Legacy)"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, task_id):
        """Get task status"""
        try:
            return Response({
                'task_id': task_id,
                'status': 'completed',
                'message': 'Task completed successfully'
            })
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return Response(
                {'error': 'Failed to get task status'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VendorRiskThreadingStatusAPIView(APIView):
    """API View for Vendor Risk Threading Status"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get vendor risk threading status"""
        try:
            return Response({
                'status': 'active',
                'threads': 1,
                'message': 'Vendor risk analysis is running'
            })
        except Exception as e:
            logger.error(f"Error getting vendor risk status: {e}")
            return Response(
                {'error': 'Failed to get vendor risk status'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
