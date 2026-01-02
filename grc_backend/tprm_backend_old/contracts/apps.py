from django.apps import AppConfig


class ContractsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.contracts'
    label = 'tprm_contracts'  # Unique label to avoid conflicts
    verbose_name = 'Contract Management System'
    
    def ready(self):
        import tprm_backend.contracts.signals
