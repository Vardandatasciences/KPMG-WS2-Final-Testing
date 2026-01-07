"""
TPRM Backend Application Configuration
"""

from django.apps import AppConfig


class TprmBackendConfig(AppConfig):
    """
    Configuration for TPRM Backend application.
    
    This AppConfig initializes encryption properties for all TPRM models
    when the application starts up.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend'
    verbose_name = 'TPRM Backend'
    
    def ready(self):
        """
        Called when Django starts.
        Initialize encryption for all TPRM models.
        """
        # Import and initialize encryption
        try:
            from .utils.encryption_init import initialize_tprm_encryption
            initialize_tprm_encryption()
        except Exception as e:
            # Log error but don't fail startup
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not initialize TPRM encryption: {str(e)}")

