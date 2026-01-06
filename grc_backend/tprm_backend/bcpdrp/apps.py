from django.apps import AppConfig


class BcpdrpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.bcpdrp'
    label = 'tprm_bcpdrp'
    
    def ready(self):
        import tprm_backend.bcpdrp.signals  # noqa
