"""
Vendor Lifecycle Management URLs
"""

from django.urls import path
from . import views
from . import test_views

urlpatterns = [
    # Lifecycle tracker endpoints
    path('tracker/', views.lifecycle_tracker_data, name='lifecycle_tracker_data'),
    path('stages/', views.vendor_lifecycle_stages, name='vendor_lifecycle_stages'),
    path('timeline/<int:vendor_id>/', views.vendor_timeline, name='vendor_timeline'),
    path('update-stage/', views.update_vendor_stage, name='update_vendor_stage'),
    path('temp-vendor-stages/', views.temp_vendor_stages, name='temp_vendor_stages'),
    # New endpoints for enhanced tracking
    path('vendors-list/', views.get_vendors_list, name='get_vendors_list'),
    path('vendor-timeline/<int:vendor_id>/', views.get_vendor_lifecycle_timeline, name='get_vendor_lifecycle_timeline'),
    path('analytics/', views.get_lifecycle_analytics, name='get_lifecycle_analytics'),
    # Test endpoints without authentication
    path('test-data/', test_views.test_lifecycle_data, name='test_lifecycle_data'),
]
