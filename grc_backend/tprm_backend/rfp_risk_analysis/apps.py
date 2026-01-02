from django.apps import AppConfig


class RiskAnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.rfp_risk_analysis'  # Full dotted path - CRITICAL!
    verbose_name = 'RFP Risk Analysis'
