"""
Database router for Risk Analysis module
Routes Risk Analysis models to tprm_main database
"""

class RiskAnalysisRouter:
    """
    A router to control all database operations on Risk Analysis models.
    """
    
    # Models that should be routed to tprm_main database
    risk_analysis_models = {
        'risk_analysis',
    }
    
    def db_for_read(self, model, **hints):
        """Point Risk Analysis models to tprm_main database."""
        if model._meta.app_label in self.risk_analysis_models:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        """Point Risk Analysis models to tprm_main database."""
        if model._meta.app_label in self.risk_analysis_models:
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both models are in Risk Analysis app."""
        db_set = {'default'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure Risk Analysis models are only migrated to default database."""
        if app_label in self.risk_analysis_models:
            return db == 'default'
        elif db == 'default':
            return False
        return None
