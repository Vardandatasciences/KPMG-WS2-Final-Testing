"""
URL configuration for mfa_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('tprm_backend.mfa_auth.urls')),
    path('rbac/', include('tprm_backend.rbac.tprm_urls')),
    path('rbac/example/', include('tprm_backend.rbac.example_urls')),
    path('api/contracts/', include('tprm_backend.contracts.urls')),
    path('api/v1/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.MEDIA_ROOT)