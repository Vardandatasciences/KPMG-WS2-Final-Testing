"""
Database router for contracts app to use the 'tprm' database
"""

class ContractsRouter:
    """
    A router to control all database operations on contracts models.
    """
    
    # Database to use for contracts models
    contracts_db = 'default'
    
    # List of apps that should use the contracts database
    contracts_apps = ['contracts']
    
    def db_for_read(self, model, **hints):
        """Point all read operations on contracts models to 'default' database."""
        if model._meta.app_label in self.contracts_apps:
            return self.contracts_db
        return None
    
    def db_for_write(self, model, **hints):
        """Point all write operations on contracts models to 'default' database."""
        if model._meta.app_label in self.contracts_apps:
            return self.contracts_db
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both models are in the contracts app."""
        if (obj1._meta.app_label in self.contracts_apps and 
            obj2._meta.app_label in self.contracts_apps):
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that contracts app models are created in the 'default' database."""
        if app_label in self.contracts_apps:
            return db == self.contracts_db
        elif db == self.contracts_db:
            return False
        return None
