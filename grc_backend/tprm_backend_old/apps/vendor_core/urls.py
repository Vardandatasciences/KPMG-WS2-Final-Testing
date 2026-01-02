"""
URL configuration for vendor_core app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .test_views import test_screening_data

# Create router with vendor_ prefix 

vendor_router = DefaultRouter()
vendor_router.register(r'vendor-categories', views.VendorCategoriesViewSet, basename='vendor-categories')
vendor_router.register(r'vendors', views.VendorsViewSet, basename='vendors')
vendor_router.register(r'vendor-contacts', views.VendorContactsViewSet, basename='vendor-contacts')
vendor_router.register(r'vendor-documents', views.VendorDocumentsViewSet, basename='vendor-documents')
vendor_router.register(r'temp-vendors', views.TempVendorViewSet, basename='temp-vendors')
vendor_router.register(r'screening-results', views.VendorScreeningViewSet, basename='screening-results')

app_name = 'vendor_core_api'

urlpatterns = [
    # API endpoints (without api/v1/ prefix since it's already in main URLs)
    path('', include(vendor_router.urls)),
    
    # Test endpoints (bypass authentication)
    path('test/screening-data/', test_screening_data, name='test-screening-data'),
    
    # Health check endpoints (commented out due to import issues)
    # path('health/', include('apps.vendor_core.health_urls')),
]
