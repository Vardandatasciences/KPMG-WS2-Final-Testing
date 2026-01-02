"""
Audits app configuration.
"""
from django.apps import AppConfig


class AuditsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.audits'
    label = 'tprm_audits'  # Unique label to avoid conflicts
    verbose_name = 'TPRM Audits'
