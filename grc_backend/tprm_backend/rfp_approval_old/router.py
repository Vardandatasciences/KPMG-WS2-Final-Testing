"""
Database router for RFP Approval module to use tprm_rfp database
"""

class RFPApprovalRouter:
    """
    A router to control all database operations on models in the
    RFP Approval application.
    """
    
    def db_for_read(self, model, **hints):
        """Suggest the database to read from."""
        if model._meta.app_label == 'rfp_approval':
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        """Suggest the database to write to."""
        if model._meta.app_label == 'rfp_approval':
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if a model in the RFP Approval app is involved."""
        db_set = {'default'}
        if obj1._state.db in db_set or obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that the RFP Approval app's models get created on the default database."""
        if app_label == 'rfp_approval':
            return db == 'default'
        elif db == 'default':
            return False
        return None
