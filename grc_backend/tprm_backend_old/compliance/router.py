"""
Database router for Compliance module
Routes Compliance models to sla database
"""

class ComplianceRouter:
    """
    A router to control all database operations on Compliance models.
    """
    
    # Models that should be routed to sla database
    compliance_models = {
        'compliance',
    }
    
    def db_for_read(self, model, **hints):
        """Point Compliance models to default database."""
        if model._meta.app_label in self.compliance_models:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        """Point Compliance models to default database."""
        if model._meta.app_label in self.compliance_models:
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both models are in Compliance app."""
        db_set = {'default'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure Compliance models are only migrated to default database."""
        if app_label in self.compliance_models:
            return db == 'default'
        elif db == 'default':
            return False
        return None
