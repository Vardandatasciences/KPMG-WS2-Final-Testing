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

# Import management views directly (workaround for app loading issue)
import logging
import sys
logger = logging.getLogger(__name__)

# Print to stdout so it's visible immediately when Django loads this file
print("\n" + "="*80, file=sys.stdout, flush=True)
print("🔧 [URLs] Loading management views...", file=sys.stdout, flush=True)

# Simple test endpoint that doesn't require imports
from django.http import JsonResponse

def management_test_endpoint(request):
    """Simple test endpoint to verify URLs are loading"""
    return JsonResponse({
        'status': 'ok', 
        'message': 'Management URLs are loaded',
        'timestamp': str(__import__('datetime').datetime.now())
    })

try:
    from tprm_backend.apps.management.views import AllVendorsListView, VendorDetailView
    
    def management_health_check(request):
        """Health check for management endpoints"""
        return JsonResponse({'status': 'ok', 'message': 'Management endpoints are working'})
    
    MANAGEMENT_VIEWS_AVAILABLE = True
    print("✅ [URLs] Successfully imported management views - direct routes will be available", file=sys.stdout, flush=True)
    logger.info("✅ Successfully imported management views - direct routes will be available")
except ImportError as e:
    MANAGEMENT_VIEWS_AVAILABLE = False
    print(f"❌ [URLs] Could not import management views: {e}", file=sys.stdout, flush=True)
    logger.error(f"❌ Could not import management views: {e}")
    import traceback
    print(traceback.format_exc(), file=sys.stdout, flush=True)
    logger.error(traceback.format_exc())
except Exception as e:
    MANAGEMENT_VIEWS_AVAILABLE = False
    print(f"❌ [URLs] Unexpected error importing management views: {e}", file=sys.stdout, flush=True)
    logger.error(f"❌ Unexpected error importing management views: {e}")
    import traceback
    print(traceback.format_exc(), file=sys.stdout, flush=True)
    logger.error(traceback.format_exc())

print("="*80 + "\n", file=sys.stdout, flush=True)

# Test RFI URL imports
print("🔧 [URLs] Testing RFI URL imports...", file=sys.stdout, flush=True)
try:
    from tprm_backend.rfp.rfi import urls as rfi_urls_module
    print(f"✅ [URLs] RFI URLs imported successfully. Patterns: {len(rfi_urls_module.urlpatterns)}", file=sys.stdout, flush=True)
    for pattern in rfi_urls_module.urlpatterns:
        print(f"   - {pattern.pattern}", file=sys.stdout, flush=True)
except Exception as e:
    print(f"❌ [URLs] Failed to import RFI URLs: {e}", file=sys.stdout, flush=True)
    import traceback
    print(traceback.format_exc(), file=sys.stdout, flush=True)

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
    # Procurement type URLs - support both /api/v1/ and /api/tprm/v1/ for compatibility
    path('api/v1/', include('tprm_backend.rfp.rfi.urls')),
    path('api/tprm/v1/', include('tprm_backend.rfp.rfi.urls')),  # Frontend uses this path
    path('api/v1/', include('tprm_backend.rfp.rfq.urls')),
    path('api/tprm/v1/', include('tprm_backend.rfp.rfq.urls')),
    path('api/v1/', include('tprm_backend.rfp.direct.urls')),
    path('api/tprm/v1/', include('tprm_backend.rfp.direct.urls')),
    path('api/v1/', include('tprm_backend.rfp.auction.urls')),
    path('api/tprm/v1/', include('tprm_backend.rfp.auction.urls')),
    path('api/v1/', include('tprm_backend.rfp.emergency.urls')),
    path('api/tprm/v1/', include('tprm_backend.rfp.emergency.urls')),
]

print(f"✅ [URLs] Total URL patterns registered: {len(urlpatterns)}", file=sys.stdout, flush=True)

# Add vendor-core and management URLs
urlpatterns.append(path('api/v1/vendor-core/', include('tprm_backend.apps.vendor_core.urls')))
urlpatterns.append(path('api/v1/management/', include('tprm_backend.apps.management.urls')))
urlpatterns.append(path('api/v1/management/test/', management_test_endpoint, name='management-test'))

# Add management direct routes if available
if MANAGEMENT_VIEWS_AVAILABLE:
    try:
        urlpatterns.append(path('api/v1/management/health/', management_health_check, name='management-health-direct'))
        urlpatterns.append(path('api/v1/management/vendors/all/', AllVendorsListView.as_view(), name='all-vendors-list-direct'))
        urlpatterns.append(path('api/v1/management/vendors/<str:vendor_code>/', VendorDetailView.as_view(), name='vendor-detail-direct'))
    except NameError:
        pass  # Variables not defined if import failed

urlpatterns.extend([
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

# Log URL registration status
if MANAGEMENT_VIEWS_AVAILABLE:
    logger.info(f"✅ Management direct routes registered. Total URL patterns: {len(urlpatterns)}")
else:
    logger.warning(f"⚠️ Management direct routes NOT registered. Total URL patterns: {len(urlpatterns)}")

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)