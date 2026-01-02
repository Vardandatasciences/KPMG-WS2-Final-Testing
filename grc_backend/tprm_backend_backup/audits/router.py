"""
Database router for Audits app to use tprm_integration database.
"""
class AuditsRouter:
    """
    A router to control all database operations on models in the audits application.
    """
    
    def db_for_read(self, model, **hints):
        """Suggest the database to read from for the audits app."""
        if model._meta.app_label == 'audits':
            return 'tprm_integration'
        return None

    def db_for_write(self, model, **hints):
        """Suggest the database to write to for the audits app."""
        if model._meta.app_label == 'audits':
            return 'tprm_integration'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the audits app."""
        db_set = {'tprm_integration'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that the audits app's models get created on the tprm_integration database."""
        if app_label == 'audits':
            return db == 'tprm_integration'
        elif db == 'tprm_integration':
            return False
        return None
