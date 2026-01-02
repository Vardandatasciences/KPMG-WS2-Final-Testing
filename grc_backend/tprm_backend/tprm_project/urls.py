"""
URL configuration for tprm_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="TPRM RFP API",
        default_version='v1',
        description="API for Third-Party Risk Management RFP System",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('tprm_backend.rfp.urls')),
    path('api/v1/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),
    path('api/approval/', include('tprm_backend.rfp_approval.urls')),
    path('api/rfp-approval/', include('tprm_backend.rfp_approval.urls')),  # Add this line for compatibility
    path('api/auth/', include('tprm_project.auth_urls')),
    
    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # MPA Routes - serve HTML files
    path('', TemplateView.as_view(template_name='index.html'), name='landing'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('workflow/', TemplateView.as_view(template_name='rfp-workflow.html'), name='workflow'),
    path('rfp-dashboard/', TemplateView.as_view(template_name='rfp-dashboard.html'), name='rfp-dashboard'),
    path('analytics/', TemplateView.as_view(template_name='analytics.html'), name='analytics'),
    path('drafts/', TemplateView.as_view(template_name='draft-manager.html'), name='drafts'),
    path('my-approvals/', TemplateView.as_view(template_name='my-approvals.html'), name='my-approvals'),
    path('all-approvals/', TemplateView.as_view(template_name='all-approvals.html'), name='all-approvals'),
    path('approval-management/', TemplateView.as_view(template_name='approval-management.html'), name='approval-management'),
    path('vendor-portal/<str:token>/', TemplateView.as_view(template_name='vendor-portal.html'), name='vendor-portal'),
    path('submit/', TemplateView.as_view(template_name='vendor-portal.html'), name='vendor-portal-submit'),
    path('submit/open/', TemplateView.as_view(template_name='vendor-portal.html'), name='vendor-portal-open'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)