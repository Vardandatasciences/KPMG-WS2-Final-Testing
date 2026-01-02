"""
Vendor Lifecycle Management Application Configuration
"""

from django.apps import AppConfig


class VendorLifecycleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.apps.vendor_lifecycle'
    verbose_name = 'Vendor Lifecycle Management'
