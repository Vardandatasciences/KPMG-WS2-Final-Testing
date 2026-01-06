"""
Vendor Dashboard Application Configuration
"""

from django.apps import AppConfig


class VendorDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.apps.vendor_dashboard'
    label = 'tprm_vendor_dashboard'
    verbose_name = 'Vendor Dashboard'
