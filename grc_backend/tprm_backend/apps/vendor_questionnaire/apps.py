"""
Vendor Questionnaire Application Configuration
"""

from django.apps import AppConfig


class VendorQuestionnaireConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.apps.vendor_questionnaire'
    verbose_name = 'Vendor Questionnaire'
