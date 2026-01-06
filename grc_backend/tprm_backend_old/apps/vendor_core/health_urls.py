"""
Health check URLs for monitoring system status
"""

from django.urls import path
from . import health_views

urlpatterns = [
    path('', health_views.VendorHealthCheckView.as_view(), name='vendor_health_check'),
    path('database/', health_views.VendorDatabaseHealthView.as_view(), name='vendor_database_health'),
]
