from django.apps import AppConfig


class RfpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.rfp'
    label = 'tprm_rfp'  # Unique label to avoid conflicts
    
    def ready(self):
        import tprm_backend.rfp.signals  # noqa
