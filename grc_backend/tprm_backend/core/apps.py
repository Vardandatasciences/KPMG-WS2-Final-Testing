from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tprm_backend.core"
    
    def ready(self):
        # MULTI-TENANCY: Import tenant signals for automatic tenant_id assignment
        import tprm_backend.core.tenant_signals  # This registers the auto_set_tenant signal

