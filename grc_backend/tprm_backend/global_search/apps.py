from django.apps import AppConfig


class GlobalSearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.global_search'
    verbose_name = 'Global Search'
    
    def ready(self):
        """Import signals when the app is ready."""
        import tprm_backend.global_search.signals
