"""
URL patterns for the SLAs app matching MySQL schema.
"""
from django.urls import path, include
from . import views

app_name = 'slas'

urlpatterns = [
    # Vendor endpoints
    path('vendors/', views.VendorListView.as_view(), name='vendor-list'),
    path('vendors/<int:pk>/', views.VendorDetailView.as_view(), name='vendor-detail'),
    
    # Contract endpoints
    path('contracts/', views.ContractListView.as_view(), name='contract-list'),
    path('contracts/<int:pk>/', views.ContractDetailView.as_view(), name='contract-detail'),
    
    # VendorSLA endpoints
    path('', views.VendorSLAListView.as_view(), name='sla-list'),
    path('<int:pk>/', views.VendorSLADetailView.as_view(), name='sla-detail'),
    path('<int:sla_id>/submit/', views.VendorSLASubmitView.as_view(), name='sla-submit'),
    path('<int:sla_id>/approve/', views.VendorSLAApproveView.as_view(), name='sla-approve'),
    
    # SLA Metrics endpoints
    path('metrics/', views.SLAMetricListView.as_view(), name='metric-list'),
    path('metrics/<int:pk>/', views.SLAMetricDetailView.as_view(), name='metric-detail'),
    path('<int:sla_id>/metrics/', views.SLAMetricsBySLAView.as_view(), name='sla-metrics'),
    
    # SLA Document endpoints
    path('documents/', views.SLADocumentListView.as_view(), name='document-list'),
    path('documents/<int:pk>/', views.SLADocumentDetailView.as_view(), name='document-detail'),
    
    # SLA Compliance endpoints
    path('compliance/', views.SLAComplianceListView.as_view(), name='compliance-list'),
    path('compliance/<int:pk>/', views.SLAComplianceDetailView.as_view(), name='compliance-detail'),
    
    # SLA Violations endpoints
    path('violations/', views.SLAViolationListView.as_view(), name='violation-list'),
    path('violations/<int:pk>/', views.SLAViolationDetailView.as_view(), name='violation-detail'),
    
    # SLA Reviews endpoints
    path('reviews/', views.SLAReviewListView.as_view(), name='review-list'),
    path('reviews/<int:pk>/', views.SLAReviewDetailView.as_view(), name='review-detail'),
    
    # Analytics and Summary endpoints
    path('compliance-summary/', views.sla_compliance_summary, name='compliance-summary'),
    path('vendor-summary/', views.vendor_summary, name='vendor-summary'),
    path('dashboard-stats/', views.sla_dashboard_stats, name='dashboard-stats'),
    path('trends/', views.sla_trends, name='trends'),
    path('performance-dashboard/', views.sla_performance_dashboard, name='performance-dashboard'),
    path('kpi-data/', views.sla_kpi_data, name='kpi-data'),
    
    # Dashboard API endpoints
    path('dashboard/summary/', views.SLADashboardSummaryView.as_view(), name='dashboard-summary'),
    path('dashboard/framework-distribution/', views.SLAFrameworkDistributionView.as_view(), name='framework-distribution'),
    path('dashboard/sla-status-distribution/', views.SLAStatusDistributionView.as_view(), name='sla-status-distribution'),
    path('dashboard/sla-types-distribution/', views.SLATypesDistributionView.as_view(), name='sla-types-distribution'),
    path('dashboard/risk-level-distribution/', views.SLARiskLevelDistributionView.as_view(), name='risk-level-distribution'),
    path('dashboard/top-performing-vendors/', views.SLATopPerformingVendorsView.as_view(), name='top-performing-vendors'),
    path('dashboard/compliance-metrics/', views.SLAComplianceMetricsView.as_view(), name='compliance-metrics'),
    path('dashboard/sla-performance-categories/', views.SLAPerformanceCategoriesView.as_view(), name='performance-categories'),
    
    # Bulk operations
    path('bulk-upload/', views.bulk_sla_upload, name='bulk-upload'),
    path('export/', views.sla_export, name='export'),
    
    # SLA Approval endpoints
    path('approvals/', include('tprm_backend.slas.slaapproval.urls')),
]