"""
Management app configuration
"""

from django.apps import AppConfig


class ManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.apps.management'
    verbose_name = 'Management'
