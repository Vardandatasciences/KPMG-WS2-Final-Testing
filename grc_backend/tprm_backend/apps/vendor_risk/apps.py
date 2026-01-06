"""
Vendor Risk Assessment Application Configuration
"""

from django.apps import AppConfig


class VendorRiskConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.apps.vendor_risk'
    verbose_name = 'Vendor Risk Assessment'
