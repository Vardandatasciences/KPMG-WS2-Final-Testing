from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Removed test import - using entity-data-row approach

# Create router and register viewsets
router = DefaultRouter()
router.register(r'risks', views.RiskViewSet, basename='risk')
router.register(r'heatmap', views.RiskHeatmapViewSet, basename='heatmap')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom API endpoints (old endpoints removed - using entity-data-row approach)
    path('statistics/', views.RiskStatisticsAPIView.as_view(), name='risk-statistics'),
    path('dashboard/', views.DashboardAPIView.as_view(), name='dashboard'),
    # BCP/DRP integration disabled - using entity-data-row approach
    
    # Entity-Data-Row endpoints
    path('entity-dropdown/', views.EntityDataDropdownAPIView.as_view(), name='entity-dropdown'),
    path('entity-risk-generation/', views.EntityRiskGenerationAPIView.as_view(), name='entity-risk-generation'),
    
    # Background task status endpoint
    path('task-status/<str:task_id>/', views.TaskStatusAPIView.as_view(), name='task-status'),
]
