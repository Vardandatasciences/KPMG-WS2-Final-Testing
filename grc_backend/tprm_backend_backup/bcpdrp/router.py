"""
Database router for BCP/DRP module
Routes BCP/DRP models to tprm_integration database
"""

class BCPDRPRouter:
    """
    A router to control all database operations on BCP/DRP models.
    """
    
    # Models that should be routed to tprm_integration database
    bcpdrp_models = {
        'bcpdrp',
    }
    
    def db_for_read(self, model, **hints):
        """Point BCP/DRP models to tprm_integration database."""
        if model._meta.app_label in self.bcpdrp_models:
            return 'tprm_integration'
        return None

    def db_for_write(self, model, **hints):
        """Point BCP/DRP models to tprm_integration database."""
        if model._meta.app_label in self.bcpdrp_models:
            return 'tprm_integration'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both models are in BCP/DRP app."""
        db_set = {'tprm_integration'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure BCP/DRP models are only migrated to tprm_integration database."""
        if app_label in self.bcpdrp_models:
            return db == 'tprm_integration'
        elif db == 'tprm_integration':
            return False
        return None
