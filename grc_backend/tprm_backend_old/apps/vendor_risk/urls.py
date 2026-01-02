"""
Vendor Risk Assessment URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'assessments', views.VendorRiskAssessmentViewSet, basename='vendor-risk-assessment')
router.register(r'factors', views.VendorRiskFactorViewSet, basename='vendor-risk-factor')
router.register(r'thresholds', views.VendorRiskThresholdViewSet, basename='vendor-risk-threshold')
router.register(r'lifecycle-stages', views.VendorLifecycleStageViewSet, basename='vendor-lifecycle-stage')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom API endpoints
    path('dashboard/', views.VendorRiskDashboardAPIView.as_view(), name='vendor-risk-dashboard'),
    path('risks/', views.VendorRisksAPIView.as_view(), name='vendor-risks'),
    path('modules/', views.VendorModulesAPIView.as_view(), name='vendor-modules'),
    path('vendors/', views.VendorListAPIView.as_view(), name='vendor-list'),
    path('generate-risks/', views.VendorRiskGenerationAPIView.as_view(), name='vendor-risk-generation'),
    path('debug/', views.VendorRiskDebugAPIView.as_view(), name='vendor-risk-debug'),
]
