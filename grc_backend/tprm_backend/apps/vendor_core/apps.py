"""
Vendor Core Application Configuration
"""

from django.apps import AppConfig


class VendorCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.apps.vendor_core'
    verbose_name = 'Vendor Core Management'
    
    def ready(self):
        """Initialize application when Django starts"""
        import tprm_backend.apps.vendor_core.signals  # noqa
