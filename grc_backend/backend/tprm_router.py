"""
Database router for TPRM models
Routes all TPRM-related models to the tprm_integration database
"""
import logging

logger = logging.getLogger(__name__)

class TPRMDatabaseRouter:
    """
    A router to control all database operations for TPRM models.
    """
    
    # TPRM app labels that should use the tprm database
    tprm_apps = {
        'tprm_rbac',
        'rbac',  # In case registered as just 'rbac'
        'tprm_backend',
        'tprm_backend.rbac',  # Full path
        'tprm_mfa_auth',
        'mfa_auth',
        'tprm_backend.mfa_auth',
        'tprm_slas',
        'slas',
        'tprm_backend.slas',
        'tprm_rfp',
        'rfp',
        'tprm_backend.rfp',
        'tprm_rfp_approval',
        'rfp_approval',
        'tprm_backend.rfp_approval',
        'tprm_contracts',
        'contracts',
        'tprm_backend.contracts',
        'tprm_vendor_core',
        'vendor_core',
        'tprm_backend.apps.vendor_core',
        'tprm_vendor_auth',
        'vendor_auth',
        'tprm_backend.apps.vendor_auth',
        'tprm_vendor_risk',
        'vendor_risk',
        'tprm_backend.apps.vendor_risk',
        'tprm_vendor_questionnaire',
        'vendor_questionnaire',
        'tprm_backend.apps.vendor_questionnaire',
        'tprm_vendor_dashboard',
        'vendor_dashboard',
        'tprm_backend.apps.vendor_dashboard',
        'tprm_vendor_lifecycle',
        'vendor_lifecycle',
        'tprm_backend.apps.vendor_lifecycle',
        'tprm_vendor_approval',
        'vendor_approval',
        'tprm_backend.apps.vendor_approval',
        'tprm_compliance',
        'compliance',
        'tprm_backend.compliance',
        'tprm_bcpdrp',
        'bcpdrp',
        'tprm_backend.bcpdrp',
        'tprm_risk_analysis',
        'risk_analysis',
        'tprm_backend.risk_analysis',
        'tprm_risk_analysis_vendor',
        'risk_analysis_vendor',
        'tprm_backend.risk_analysis_vendor',
        'tprm_contract_risk_analysis',
        'contract_risk_analysis',
        'tprm_backend.contract_risk_analysis',
        'tprm_notifications',
        'notifications',
        'tprm_backend.notifications',
        'tprm_audits',
        'audits',
        'tprm_backend.audits',
        'tprm_audits_contract',
        'audits_contract',
        'tprm_backend.audits_contract',
        'tprm_quick_access',
        'quick_access',
        'tprm_backend.quick_access',
        'tprm_admin_access',
        'admin_access',
        'tprm_backend.admin_access',
        'tprm_global_search',
        'global_search',
        'tprm_backend.global_search',
        'tprm_ocr_app',
        'ocr_app',
        'tprm_backend.ocr_app',
        'tprm_core',
        'core',
        'tprm_backend.core',
        # Management app (screening schedules, etc.)
        'management',
        'tprm_backend.apps.management',
    }
    
    def db_for_read(self, model, **hints):
        """
        Attempts to read tprm models go to tprm database.
        """
        app_label = model._meta.app_label
        db_name = 'tprm' if app_label in self.tprm_apps else 'default'
        logger.debug(f"[TPRM Router] db_for_read: model={model.__name__}, app_label={app_label}, database={db_name}")
        return db_name
    
    def db_for_write(self, model, **hints):
        """
        Attempts to write tprm models go to tprm database.
        """
        if model._meta.app_label in self.tprm_apps:
            return 'tprm'
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both models are in the same database.
        """
        db1 = 'tprm' if obj1._meta.app_label in self.tprm_apps else 'default'
        db2 = 'tprm' if obj2._meta.app_label in self.tprm_apps else 'default'
        return db1 == db2
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure tprm apps only appear in the 'tprm' database.
        """
        if app_label in self.tprm_apps:
            return db == 'tprm'
        return db == 'default'

