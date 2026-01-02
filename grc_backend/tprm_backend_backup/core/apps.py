from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.core'
    label = 'tprm_core'
    verbose_name = 'TPRM Core'


