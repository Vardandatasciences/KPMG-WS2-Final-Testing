"""
Tenant Context Manager for Automatic Tenant ID Assignment

This module provides a thread-local context to automatically set tenant_id
when creating model instances, so you don't need to manually set it in every view.
"""

import threading
from contextlib import contextmanager

# Thread-local storage for tenant_id
_thread_local = threading.local()


def set_current_tenant(tenant_id):
    """
    Set the current tenant_id in thread-local storage
    
    Args:
        tenant_id: The tenant ID to set as current
    """
    _thread_local.tenant_id = tenant_id


def get_current_tenant():
    """
    Get the current tenant_id from thread-local storage
    
    Returns:
        tenant_id (int) or None
    """
    return getattr(_thread_local, 'tenant_id', None)


def clear_current_tenant():
    """
    Clear the current tenant_id from thread-local storage
    """
    if hasattr(_thread_local, 'tenant_id'):
        delattr(_thread_local, 'tenant_id')


@contextmanager
def tenant_context(tenant_id):
    """
    Context manager to set tenant_id for a block of code
    
    Usage:
        with tenant_context(tenant_id):
            framework = Framework.objects.create(...)  # tenant_id automatically set
    """
    old_tenant_id = get_current_tenant()
    set_current_tenant(tenant_id)
    try:
        yield
    finally:
        if old_tenant_id is not None:
            set_current_tenant(old_tenant_id)
        else:
            clear_current_tenant()


def set_tenant_from_request(request):
    """
    Set current tenant from request object
    
    This should be called in middleware or view decorators
    
    Args:
        request: Django request object
    """
    from .tenant_utils import get_tenant_id_from_request
    tenant_id = get_tenant_id_from_request(request)
    if tenant_id:
        set_current_tenant(tenant_id)

