"""
URL configuration for vendor TPRM project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Secure URL patterns with vendor prefix
urlpatterns = [
    # Admin interface (should be changed in production)
    path('vendor-admin/', admin.site.urls),
    
    # Authentication endpoints
    path('api/v1/vendor-auth/', include('tprm_backend.apps.vendor_auth.urls')),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='vendor_token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='vendor_token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='vendor_token_verify'),
    
    # Core application endpoints
    path('api/v1/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),
    path('api/v1/vendor-risk/', include('tprm_backend.apps.vendor_risk.urls')),
    path('api/v1/vendor-questionnaire/', include('tprm_backend.apps.vendor_questionnaire.urls')),
    path('api/v1/vendor-dashboard/', include('tprm_backend.apps.vendor_dashboard.urls')),
    path('api/v1/vendor-lifecycle/', include('tprm_backend.apps.vendor_lifecycle.urls')),
    path('api/v1/vendor-approval/', include('tprm_backend.apps.vendor_approval.urls')),
    
    # Notifications endpoints
    path('api/notifications/', include('tprm_backend.notifications.urls')),
    
    # OCR Microservice endpoints
    path('api/ocr/', include('tprm_backend.ocr_app.urls')),
    
    # Health check endpoint
    path('api/v1/health/', include('tprm_backend.apps.vendor_core.health_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler400 = 'utils.vendor_error_handlers.vendor_bad_request'
handler403 = 'utils.vendor_error_handlers.vendor_permission_denied'
handler404 = 'utils.vendor_error_handlers.vendor_not_found'
handler500 = 'utils.vendor_error_handlers.vendor_server_error'
