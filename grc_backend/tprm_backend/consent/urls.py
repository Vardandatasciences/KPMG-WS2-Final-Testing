"""
URL patterns for TPRM Consent Management
"""
from django.urls import path
from . import consent_views

app_name = 'tprm_consent'

urlpatterns = [
    # Consent Configuration Management
    path('configurations/', consent_views.get_consent_configurations, name='get_configurations'),
    path('configurations/<int:config_id>/', consent_views.update_consent_configuration, name='update_configuration'),
    path('configurations/bulk-update/', consent_views.bulk_update_consent_configurations, name='bulk_update'),
    
    # Consent Checking and Acceptance
    path('check-required/', consent_views.check_consent_required, name='check_required'),
    path('accept/', consent_views.record_consent_acceptance, name='record_acceptance'),
    
    # Consent History
    path('acceptances/', consent_views.get_consent_acceptances, name='get_acceptances'),
]

