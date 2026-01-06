class NotificationsRouter:
    """
    A router to control all database operations on models in the
    notifications application.
    """
    route_app_labels = {'notifications'}

    def db_for_read(self, model, **hints):
        """
        Attempts to read notifications models go to notifications database.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write notifications models go to notifications database.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the notifications app is involved.
        """
        if obj1._meta.app_label in self.route_app_labels or \
           obj2._meta.app_label in self.route_app_labels:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the notifications app only appears in the default database.
        """
        if app_label in self.route_app_labels:
            return db == 'default'
        elif db == 'default':
            return False
        return None
