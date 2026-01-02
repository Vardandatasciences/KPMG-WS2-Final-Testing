"""
Database router for Audits Contract app to use tprm_integration database.
"""
class AuditsContractRouter:
    """
    A router to control all database operations on models in the audits_contract application.
    """
    
    def db_for_read(self, model, **hints):
        """Suggest the database to read from for the audits_contract app."""
        if model._meta.app_label == 'audits_contract':
            return 'tprm_integration'
        return None

    def db_for_write(self, model, **hints):
        """Suggest the database to write to for the audits_contract app."""
        if model._meta.app_label == 'audits_contract':
            return 'tprm_integration'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the audits_contract app."""
        db_set = {'tprm_integration'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that the audits_contract app's models get created on the tprm_integration database."""
        if app_label == 'audits_contract':
            return db == 'tprm_integration'
        elif db == 'tprm_integration':
            return False
        return None
