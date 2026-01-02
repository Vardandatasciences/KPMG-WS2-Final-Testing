"""
Database router for Contract Risk Analysis module
Routes Contract Risk Analysis models to tprm_integration database
"""

class ContractRiskAnalysisRouter:
    """
    A router to control all database operations on Contract Risk Analysis models.
    """
    
    # Models that should be routed to tprm_integration database
    contract_risk_analysis_models = {
        'contract_risk_analysis',
    }
    
    def db_for_read(self, model, **hints):
        """Point Contract Risk Analysis models to tprm_integration database."""
        if model._meta.app_label in self.contract_risk_analysis_models:
            return 'tprm_integration'
        return None

    def db_for_write(self, model, **hints):
        """Point Contract Risk Analysis models to tprm_integration database."""
        if model._meta.app_label in self.contract_risk_analysis_models:
            return 'tprm_integration'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both models are in Contract Risk Analysis app."""
        db_set = {'tprm_integration'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure Contract Risk Analysis models are only migrated to tprm_integration database."""
        if app_label in self.contract_risk_analysis_models:
            return db == 'tprm_integration'
        elif db == 'tprm_integration':
            return False
        return None

