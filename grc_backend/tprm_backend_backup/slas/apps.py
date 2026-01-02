from django.apps import AppConfig


class SlasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.slas'
    label = 'tprm_slas'
    verbose_name = 'TPRM SLAs'


