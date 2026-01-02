"""
Database router for OCR app
Routes all OCR models to the 'udm' database
"""


class OCRRouter:
    """
    Router to direct OCR app database operations to the udm database.
    """
    
    route_app_labels = {'ocr_app'}
    
    def db_for_read(self, model, **hints):
        """
        Route read operations for OCR app to udm database.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'default'
        return None
    
    def db_for_write(self, model, **hints):
        """
        Route write operations for OCR app to udm database.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'default'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both models are in the OCR app.
        """
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Ensure OCR app migrations only run on the default database.
        """
        if app_label in self.route_app_labels:
            return db == 'default'
        return None

