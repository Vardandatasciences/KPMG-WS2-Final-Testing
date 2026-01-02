from django.apps import AppConfig


class RfpApprovalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.rfp_approval'
    label = 'tprm_rfp_approval'
    verbose_name = 'RFP Approval'


