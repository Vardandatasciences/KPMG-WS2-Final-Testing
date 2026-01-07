"""
TPRM Encryption Initialization
Automatically adds _plain properties to all encrypted models at startup.
"""

import logging
from .encrypted_fields_mixin import add_plain_properties_to_model
from .encryption_config import get_all_encrypted_fields

logger = logging.getLogger(__name__)


def initialize_tprm_encryption():
    """
    Initialize encryption for all TPRM models.
    
    This function:
    1. Gets list of all models with encryption configured
    2. Dynamically adds _plain properties to each model
    3. Ensures decryption works seamlessly in serializers and views
    
    Should be called during app startup (in apps.py ready() method).
    """
    # Import all model modules to ensure they're loaded
    try:
        # User models
        from tprm_backend.users import models as user_models
        _add_properties_to_module(user_models)
        
        # Vendor models
        from tprm_backend.vendors import models as vendor_models
        _add_properties_to_module(vendor_models)
        
        # Contract models
        from tprm_backend.contracts import models as contract_models
        _add_properties_to_module(contract_models)
        
        # SLA models
        from tprm_backend.slas import models as sla_models
        _add_properties_to_module(sla_models)
        
        # Core models
        from tprm_backend.core import models as core_models
        _add_properties_to_module(core_models)
        
        # RFP models
        from tprm_backend.rfp import models as rfp_models
        _add_properties_to_module(rfp_models)
        
        # BCP/DRP models
        from tprm_backend.bcpdrp import models as bcpdrp_models
        _add_properties_to_module(bcpdrp_models)
        
        # MFA Auth models
        from tprm_backend.mfa_auth import models as mfa_models
        _add_properties_to_module(mfa_models)
        
        # OCR models
        from tprm_backend.ocr_app import models as ocr_models
        _add_properties_to_module(ocr_models)
        
        # Audit models
        from tprm_backend.audits import models as audit_models
        _add_properties_to_module(audit_models)
        
        # Contract Audit models
        from tprm_backend.audits_contract import models as contract_audit_models
        _add_properties_to_module(contract_audit_models)
        
        # Notification models
        from tprm_backend.notifications import models as notification_models
        _add_properties_to_module(notification_models)
        
        # Risk Analysis models
        from tprm_backend.risk_analysis import models as risk_models
        _add_properties_to_module(risk_models)
        
        # Risk Analysis Vendor models
        from tprm_backend.risk_analysis_vendor import models as risk_vendor_models
        _add_properties_to_module(risk_vendor_models)
        
        # RFP Risk Analysis models
        from tprm_backend.rfp_risk_analysis import models as rfp_risk_models
        _add_properties_to_module(rfp_risk_models)
        
        # Contract Risk Analysis models
        from tprm_backend.contract_risk_analysis import models as contract_risk_models
        _add_properties_to_module(contract_risk_models)
        
        # RFP Approval models
        from tprm_backend.rfp_approval import models as rfp_approval_models
        _add_properties_to_module(rfp_approval_models)
        
        # SLA Approval models
        from tprm_backend.slas.slaapproval import models as sla_approval_models
        _add_properties_to_module(sla_approval_models)
        
        # Compliance models
        from tprm_backend.compliance import models as compliance_models
        _add_properties_to_module(compliance_models)
        
        # Vendor Core models
        from tprm_backend.apps.vendor_core import models as vendor_core_models
        _add_properties_to_module(vendor_core_models)
        
        logger.info("✅ TPRM encryption initialization complete - all _plain properties added")
        
    except Exception as e:
        logger.error(f"Error initializing TPRM encryption: {str(e)}")
        # Don't fail startup, just log the error
        import traceback
        traceback.print_exc()


def _add_properties_to_module(module):
    """
    Add _plain properties to all encrypted models in a module.
    
    Args:
        module: Python module containing Django models
    """
    # Get all classes in the module
    import inspect
    from django.db import models as django_models
    
    for name, obj in inspect.getmembers(module):
        # Check if it's a Django model class
        if (inspect.isclass(obj) and 
            issubclass(obj, django_models.Model) and 
            obj != django_models.Model):
            
            # Check if model has encrypted fields configured
            try:
                if hasattr(obj, 'get_encrypted_fields'):
                    encrypted_fields = obj.get_encrypted_fields()
                    if encrypted_fields:
                        # Add _plain properties to this model
                        add_plain_properties_to_model(obj)
                        logger.debug(f"Added _plain properties to {obj.__name__}")
            except Exception as e:
                logger.warning(f"Could not add properties to {name}: {str(e)}")


# Auto-initialize flag
_initialized = False


def auto_initialize():
    """
    Auto-initialize encryption on first import.
    """
    global _initialized
    if not _initialized:
        initialize_tprm_encryption()
        _initialized = True


# Note: Don't auto-initialize on import to avoid issues during migrations
# Instead, call from apps.py ready() method

