from django.apps import AppConfig


class RbacConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.rbac'
    label = 'tprm_rbac'
    verbose_name = 'TPRM RBAC'


