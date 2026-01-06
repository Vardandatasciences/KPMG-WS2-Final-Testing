"""
Audits Contract app configuration.
"""
from django.apps import AppConfig


class AuditsContractConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.audits_contract'
    label = 'audits_contract'
    verbose_name = 'Contract Audits'
