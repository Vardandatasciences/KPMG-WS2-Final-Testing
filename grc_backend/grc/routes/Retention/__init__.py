# Retention Management Module
from .retention_views import (
    get_module_configs,
    bulk_update_module_configs,
    get_page_configs,
    bulk_update_page_configs
)

__all__ = [
    'get_module_configs',
    'bulk_update_module_configs',
    'get_page_configs',
    'bulk_update_page_configs'
]
