"""
Vendor Dashboard URLs
"""

from django.urls import path
from .views import (
    ScreeningMatchRateAPIView, 
    QuestionnaireOverdueRateAPIView, 
    VendorsFlaggedOFACPEPAPIView, 
    VendorAcceptanceTimeAPIView, 
    DashboardMetricsAPIView, 
    VendorAlertsAPIView, 
    VendorKPICategoriesAPIView,
    VendorRegistrationCompletionRateAPIView,
    VendorRegistrationTimeAPIView,
    VendorDashboardExportPDFAPIView,
    VendorDashboardExportExcelAPIView
)

urlpatterns = [
    path('screening-match-rate/', ScreeningMatchRateAPIView.as_view(), name='screening-match-rate'),
    path('questionnaire-overdue-rate/', QuestionnaireOverdueRateAPIView.as_view(), name='questionnaire-overdue-rate'),
    path('vendors-flagged-ofac-pep/', VendorsFlaggedOFACPEPAPIView.as_view(), name='vendors-flagged-ofac-pep'),
    path('vendor-acceptance-time/', VendorAcceptanceTimeAPIView.as_view(), name='vendor-acceptance-time'),
    path('vendor-registration-completion-rate/', VendorRegistrationCompletionRateAPIView.as_view(), name='vendor-registration-completion-rate'),
    path('vendor-registration-time/', VendorRegistrationTimeAPIView.as_view(), name='vendor-registration-time'),
    path('api/dashboard/', DashboardMetricsAPIView.as_view(), name='dashboard-metrics'),
    path('alerts/', VendorAlertsAPIView.as_view(), name='vendor-alerts'),
    path('kpi-categories/', VendorKPICategoriesAPIView.as_view(), name='vendor-kpi-categories'),
    path('export/pdf/', VendorDashboardExportPDFAPIView.as_view(), name='vendor-dashboard-export-pdf'),
    path('export/excel/', VendorDashboardExportExcelAPIView.as_view(), name='vendor-dashboard-export-excel'),
]
