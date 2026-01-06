"""
Database router for vendor management apps
Routes vendor-related models to the tprm_integration database
"""

class VendorDatabaseRouter:
    """
    A router to control all database operations on models for vendor apps
    """

    vendor_apps = {
        'apps.vendor_core',
        'apps.vendor_auth', 
        'apps.vendor_risk',
        'apps.vendor_questionnaire',
        'apps.vendor_dashboard',
        'apps.vendor_lifecycle',
        'apps.vendor_approval',
        'risk_analysis_vendor',
        
        # Alternative app names (in case they're registered differently)
        'vendor_core',
        'vendor_auth',
        'vendor_risk', 
        'vendor_questionnaire',
        'vendor_dashboard',
        'vendor_lifecycle',
        'vendor_approval',
    }

    def db_for_read(self, model, **hints):
        """Suggest the database to read from."""
        if model._meta.app_label in self.vendor_apps:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        """Suggest the database to write to."""
        if model._meta.app_label in self.vendor_apps:
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the same app."""
        db_set = {'default'}
        if obj1._meta.app_label in self.vendor_apps and obj2._meta.app_label in self.vendor_apps:
            return True
        elif obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that vendor apps' models get created on the default database."""
        if app_label in self.vendor_apps:
            return db == 'default'
        elif db == 'default':
            return False
        return None
