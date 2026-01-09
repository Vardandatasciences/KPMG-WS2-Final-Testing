"""
URL configuration for vendor_guard_hub project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Vendor Guard Hub API",
        default_version='v1',
        description="Comprehensive SLA management and vendor performance monitoring API",
        terms_of_service="https://www.vendorguardhub.com/terms/",
        contact=openapi.Contact(email="api@vendorguardhub.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Authentication
    path('api/auth/', include('mfa_auth.urls')),
    
    # RBAC APIs
    path('api/rbac/', include('rbac.tprm_urls')),
    path('api/tprm/rbac/', include('rbac.tprm_urls')),  # TPRM API prefix for frontend compatibility
    path('rbac/', include('rbac.tprm_urls')),  # Legacy endpoint for backward compatibility
    path('rbac/example/', include('rbac.example_urls')),
    
    # Admin Access Control APIs (No RBAC/MFA dependency)
    path('api/admin-access/', include('admin_access.urls')),
    
    # Global Search APIs
    path('api/global-search/', include('global_search.urls')),
    
    # Core APIs
    path('api/', include('core.urls')),

    # OCR APIs
    path('api/ocr/', include('ocr_app.urls')),
    
    # SLA Management APIs
    path('api/slas/', include('slas.urls')),
    path('api/v1/sla-dashboard/', include('slas.urls')),
    path('api/tprm/v1/sla-dashboard/', include('slas.urls')),  # TPRM API prefix for frontend compatibility
    
    
    # Audit Management APIs
    path('api/audits/', include('audits.urls')),
    
    # Notifications APIs
    path('api/notifications/', include('notifications.urls')),
    
    # Quick Access APIs
    path('api/quick-access/', include('quick_access.urls')),
    
    # Performance & Monitoring APIs
    # path('api/performance/', include('performance.urls')),
    
    # Compliance & Audit APIs
    path('api/compliance/', include('compliance.urls')),
    
    # BCP/DRP Management APIs
    path('api/bcpdrp/', include('bcpdrp.urls')),
    
    # Risk Analysis APIs
    path('api/risk-analysis/', include('risk_analysis.urls')),
    
    # Contract Management APIs
    path('api/contracts/', include('contracts.urls')),
    
    # Contract Audit APIs
    path('api/audits-contract/', include('audits_contract.urls')),
    path('api/contract-risk-analysis/', include('contract_risk_analysis.urls')),
    
    # Analytics APIs
    # path('api/analytics/', include('analytics.urls')),
    
    # Vendor Management APIs
    path('api/v1/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),
    path('api/v1/vendor-auth/', include('tprm_backend.apps.vendor_auth.urls')),
    path('api/v1/vendor-risk/', include('tprm_backend.apps.vendor_risk.urls')),
    path('api/v1/vendor-questionnaire/', include('tprm_backend.apps.vendor_questionnaire.urls')),
    path('api/v1/vendor-dashboard/', include('tprm_backend.apps.vendor_dashboard.urls')),
    path('api/v1/vendor-lifecycle/', include('tprm_backend.apps.vendor_lifecycle.urls')),
    path('api/v1/vendor-approval/', include('tprm_backend.apps.vendor_approval.urls')),
    path('api/v1/risk-analysis-vendor/', include('risk_analysis_vendor.urls')),
    
    # Vendor API Aliases for frontend compatibility
    path('api/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),
    path('api/vendor-auth/', include('tprm_backend.apps.vendor_auth.urls')),
    path('api/vendor-risk/', include('tprm_backend.apps.vendor_risk.urls')),
    path('api/vendor-questionnaire/', include('tprm_backend.apps.vendor_questionnaire.urls')),
    path('api/vendor-dashboard/', include('tprm_backend.apps.vendor_dashboard.urls')),
    path('api/vendor-lifecycle/', include('tprm_backend.apps.vendor_lifecycle.urls')),
    path('api/vendor-approval/', include('tprm_backend.apps.vendor_approval.urls')),
    
    # RFP Management APIs
    path('api/v1/', include('rfp.urls')),
    path('api/approval/', include('rfp_approval.urls')),
    path('api/rfp-approval/', include('rfp_approval.urls')),  # Add this line for compatibility
    path('api/auth/', include('tprm_project.auth_urls')),
    
    # TPRM API prefix for approval endpoints (for frontend compatibility)
    path('api/tprm/approval/', include('rfp_approval.urls')),  # Maps /api/tprm/approval/* to rfp_approval.urls
    
    # TPRM API prefix routes (for frontend compatibility - /api/tprm/*)
    # IMPORTANT: More specific routes must come BEFORE general routes
    # Vendor-specific routes (most specific)
    path('api/tprm/v1/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),  # Maps /api/tprm/v1/vendor-core/* to vendor_core.urls (for frontend compatibility)
    path('api/tprm/v1/vendor-auth/', include('tprm_backend.apps.vendor_auth.urls')),  # Maps /api/tprm/v1/vendor-auth/* to vendor_auth.urls
    path('api/tprm/v1/vendor-risk/', include('tprm_backend.apps.vendor_risk.urls')),  # Maps /api/tprm/v1/vendor-risk/* to vendor_risk.urls
    path('api/tprm/v1/vendor-questionnaire/', include('tprm_backend.apps.vendor_questionnaire.urls')),  # Maps /api/tprm/v1/vendor-questionnaire/* to vendor_questionnaire.urls
    path('api/tprm/v1/vendor-dashboard/', include('tprm_backend.apps.vendor_dashboard.urls')),  # Maps /api/tprm/v1/vendor-dashboard/* to vendor_dashboard.urls
    path('api/tprm/v1/vendor-lifecycle/', include('tprm_backend.apps.vendor_lifecycle.urls')),  # Maps /api/tprm/v1/vendor-lifecycle/* to vendor_lifecycle.urls
    path('api/tprm/v1/vendor-approval/', include('tprm_backend.apps.vendor_approval.urls')),  # Maps /api/tprm/v1/vendor-approval/* to vendor_approval.urls
    path('api/tprm/v1/risk-analysis-vendor/', include('risk_analysis_vendor.urls')),  # Maps /api/tprm/v1/risk-analysis-vendor/* to risk_analysis_vendor.urls
    
    # Other specific routes
    path('api/tprm/global-search/', include('global_search.urls')),  # Maps /api/tprm/global-search/* to global_search.urls
    path('api/tprm/rfp/', include('rfp.urls')),  # Maps /api/tprm/rfp/* to rfp.urls
    
    # General vendor routes (without v1)
    path('api/tprm/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),  # Maps /api/tprm/vendor-core/* to vendor_core.urls
    path('api/tprm/vendor-auth/', include('tprm_backend.apps.vendor_auth.urls')),
    path('api/tprm/vendor-risk/', include('tprm_backend.apps.vendor_risk.urls')),
    path('api/tprm/vendor-questionnaire/', include('tprm_backend.apps.vendor_questionnaire.urls')),
    path('api/tprm/vendor-dashboard/', include('tprm_backend.apps.vendor_dashboard.urls')),
    path('api/tprm/vendor-lifecycle/', include('tprm_backend.apps.vendor_lifecycle.urls')),
    path('api/tprm/vendor-approval/', include('tprm_backend.apps.vendor_approval.urls')),
    path('api/tprm/risk-analysis-vendor/', include('risk_analysis_vendor.urls')),
    
    # General /api/tprm/v1/ route (must come LAST to avoid catching specific routes)
    path('api/tprm/v1/', include('rfp.urls')),  # Maps /api/tprm/v1/* to rfp.urls (for frontend compatibility - /api/tprm/v1/rfps/)
    path('api/tprm/slas/', include('slas.urls')),
    path('api/tprm/audits/', include('audits.urls')),
    path('api/tprm/notifications/', include('notifications.urls')),
    path('api/tprm/quick-access/', include('quick_access.urls')),
    path('api/tprm/compliance/', include('compliance.urls')),
    path('api/tprm/bcpdrp/', include('bcpdrp.urls')),
    path('api/tprm/risk-analysis/', include('risk_analysis.urls')),
    path('api/tprm/contracts/', include('contracts.urls')),
    path('api/tprm/audits-contract/', include('audits_contract.urls')),
    path('api/tprm/contract-risk-analysis/', include('contract_risk_analysis.urls')),
    path('api/tprm/rfp-approval/', include('rfp_approval.urls')),
    
    # Additional vendor-approval route for /api/tprm/vendor-approval/ (without /api/v1/)
    path('api/tprm/vendor-approval/', include('tprm_backend.apps.vendor_approval.urls')),
    
    # MPA Routes - serve HTML files for RFP
    path('rfp-dashboard/', TemplateView.as_view(template_name='rfp-dashboard.html'), name='rfp-dashboard'),
    path('rfp-workflow/', TemplateView.as_view(template_name='rfp-workflow.html'), name='rfp-workflow'),
    path('rfp-creation/', TemplateView.as_view(template_name='rfp-creation.html'), name='rfp-creation'),
    path('rfp-vendor-selection/', TemplateView.as_view(template_name='rfp-vendor-selection.html'), name='rfp-vendor-selection'),
    path('rfp-url-generation/', TemplateView.as_view(template_name='rfp-url-generation.html'), name='rfp-url-generation'),
    path('rfp-vendor-portal/', TemplateView.as_view(template_name='rfp-vendor-portal.html'), name='rfp-vendor-portal'),
    path('rfp-evaluation/', TemplateView.as_view(template_name='rfp-evaluation.html'), name='rfp-evaluation'),
    path('rfp-onboarding/', TemplateView.as_view(template_name='rfp-onboarding.html'), name='rfp-onboarding'),
    path('vendor-portal/<str:token>/', TemplateView.as_view(template_name='vendor-portal.html'), name='vendor-portal'),
    path('submit/', TemplateView.as_view(template_name='vendor-portal.html'), name='vendor-portal-submit'),
    path('submit/open/', TemplateView.as_view(template_name='vendor-portal.html'), name='vendor-portal-open'),
    path('my-approvals/', TemplateView.as_view(template_name='my-approvals.html'), name='my-approvals'),
    path('all-approvals/', TemplateView.as_view(template_name='all-approvals.html'), name='all-approvals'),
    path('approval-management/', TemplateView.as_view(template_name='approval-management.html'), name='approval-management'),
    path('stage-reviewer/', TemplateView.as_view(template_name='stage-reviewer.html'), name='stage-reviewer'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
