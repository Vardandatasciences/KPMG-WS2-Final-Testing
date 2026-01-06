"""
Database router for vendor approval app
Routes vendor approval models to the tprm_integration database
"""

from django.conf import settings


class VendorApprovalRouter:
    """
    Database router for vendor approval models
    Routes all vendor approval models to the tprm_integration database
    """
    
    # Models that should use the tprm_integration database
    vendor_approval_models = {
        'approvalrequest',
        'approvalworkflow',
        'approvalstage',
        'approvalrequestversions',
        'tempvendor',
        'tprmrisk',
    }
    
    def db_for_read(self, model, **hints):
        """Suggest the database to read from for a model"""
        if model._meta.app_label == 'vendor_approval':
            return 'default'
        return None
    
    def db_for_write(self, model, **hints):
        """Suggest the database to write to for a model"""
        if model._meta.app_label == 'vendor_approval':
            return 'default'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both models are in the same database"""
        db_set = {'default'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that vendor approval models are only migrated to default database"""
        if app_label == 'vendor_approval':
            return db == 'default'
        return None
