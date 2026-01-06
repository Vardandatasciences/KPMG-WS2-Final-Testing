"""
Django Signals for Automatic Tenant ID Assignment

This module uses Django signals to automatically set tenant_id when creating
model instances, so you don't need to manually set it in every view.
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import (
    Framework, Policy, SubPolicy, Compliance, Audit, Incident, Risk,
    RiskInstance, AuditFinding, Notification, Department, Event, Users,
    FrameworkApproval, PolicyApproval, FrameworkVersion
)
from .tenant_context import get_current_tenant


# List of models that have tenant field
TENANT_AWARE_MODELS = [
    Framework, Policy, SubPolicy, Compliance, Audit, Incident, Risk,
    RiskInstance, AuditFinding, Notification, Department, Event, Users,
    FrameworkApproval, PolicyApproval, FrameworkVersion
]


@receiver(pre_save)
def auto_set_tenant(sender, instance, **kwargs):
    """
    Automatically set tenant_id when creating new records
    
    This signal fires before any model is saved. It checks if:
    1. The model has a 'tenant' field
    2. The tenant is not already set
    3. This is a new record (pk is None)
    4. There's a current tenant in context
    
    If all conditions are met, it automatically sets the tenant.
    """
    # Only process models that have tenant field
    if not hasattr(instance, 'tenant'):
        return
    
    # Only set tenant if:
    # 1. tenant is not already set
    # 2. This is a new record (pk is None)
    if instance.tenant is None and instance.pk is None:
        tenant_id = get_current_tenant()
        
        if tenant_id:
            try:
                from .models import Tenant
                tenant = Tenant.objects.get(tenant_id=tenant_id)
                instance.tenant = tenant
            except Tenant.DoesNotExist:
                pass  # Tenant not found, skip auto-assignment
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"[Tenant Signals] Error auto-setting tenant for {sender.__name__}: {e}")

