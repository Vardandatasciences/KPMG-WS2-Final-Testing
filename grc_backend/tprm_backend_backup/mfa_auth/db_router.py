class TPRMDatabaseRouter:
    """
    A router to control all database operations on models in the mfa_auth application.
    """
    
    def db_for_read(self, model, **hints):
        """Point all read operations on mfa_auth models to 'tprm' database."""
        if model._meta.app_label == 'mfa_auth':
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        """Point all write operations on mfa_auth models to 'tprm' database."""
        if model._meta.app_label == 'mfa_auth':
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if a model in the mfa_auth app is involved."""
        if obj1._meta.app_label == 'mfa_auth' or obj2._meta.app_label == 'mfa_auth':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that the mfa_auth app's models get created on the default database."""
        if app_label == 'mfa_auth':
            return db == 'default'
        elif db == 'default':
            return False
        return None
