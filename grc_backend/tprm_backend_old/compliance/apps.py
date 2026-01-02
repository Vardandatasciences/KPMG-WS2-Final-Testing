from django.apps import AppConfig


class ComplianceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.compliance'
    label = 'tprm_compliance'
    verbose_name = 'TPRM Compliance'


