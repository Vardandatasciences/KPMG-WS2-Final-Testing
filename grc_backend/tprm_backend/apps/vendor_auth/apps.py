"""
Vendor Authentication Application Configuration
"""

from django.apps import AppConfig


class VendorAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.apps.vendor_auth'
    verbose_name = 'Vendor Authentication'
