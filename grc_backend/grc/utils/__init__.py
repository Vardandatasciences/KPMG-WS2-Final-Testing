"""
GRC Utils Package
Contains utility modules for AI optimization and document processing.

This package maintains backward compatibility with the original utils.py module.
All functions from utils.py are re-exported here.
"""

# Import from parent utils.py using importlib to avoid circular imports
import importlib.util
import sys
from pathlib import Path

# Get the parent directory where utils.py is located
_parent_dir = Path(__file__).parent.parent
_utils_py_path = _parent_dir / "utils.py"

# Load the original utils.py as a module (lazy loading to avoid Django setup issues)
_utils_module_cache = None

def _get_utils_module():
    """Lazy load the original utils.py module"""
    global _utils_module_cache
    if _utils_module_cache is None:
        if _utils_py_path.exists():
            module_name = "grc._utils_original"
            spec = importlib.util.spec_from_file_location(module_name, str(_utils_py_path))
            if spec and spec.loader:
                _utils_module_cache = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = _utils_module_cache
                spec.loader.exec_module(_utils_module_cache)
            else:
                raise ImportError(f"Could not load utils.py from {_utils_py_path}")
        else:
            raise ImportError(f"Could not find utils.py at {_utils_py_path}")
    return _utils_module_cache

# Create lazy accessors for backward compatibility
def parse_date(date_str):
    """Lazy wrapper for parse_date from utils.py"""
    return _get_utils_module().parse_date(date_str)

def safe_isoformat(val):
    """Lazy wrapper for safe_isoformat from utils.py"""
    return _get_utils_module().safe_isoformat(val)

def sanitize_ip_address(ip_address):
    """
    Lazy wrapper for sanitize_ip_address from the original utils.py.
    Kept here for backward compatibility with imports like:
        from grc.utils import sanitize_ip_address
    """
    return _get_utils_module().sanitize_ip_address(ip_address)

def send_log(*args, **kwargs):
    """Lazy wrapper for send_log from utils.py"""
    return _get_utils_module().send_log(*args, **kwargs)

def get_client_ip(request):
    """Lazy wrapper for get_client_ip from utils.py"""
    return _get_utils_module().get_client_ip(request)

# For LOGGING_SERVICE_URL, we'll use a module-level __getattr__ for lazy loading
def __getattr__(name):
    """Lazy load attributes from original utils.py"""
    if name == 'LOGGING_SERVICE_URL':
        return _get_utils_module().LOGGING_SERVICE_URL
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Also export the new Phase 2 utilities
from .ai_cache import (
    get_redis_client,
    generate_cache_key,
    get_cached_response,
    set_cached_response,
    cached_llm_call,
    clear_cache_pattern,
    get_cache_stats,
)

from .document_preprocessor import (
    normalize_whitespace,
    remove_control_characters,
    truncate_intelligently,
    preprocess_document,
    calculate_document_hash,
)

from .few_shot_prompts import (
    build_few_shot_prompt,
    get_field_extraction_prompt,
    get_risk_extraction_prompt,
    RISK_EXTRACTION_EXAMPLES,
    FIELD_EXTRACTION_EXAMPLES,
)

# Phase 3 utilities
try:
    from .rag_system import (
        get_chroma_client,
        get_chroma_collection,
        add_document_to_rag,
        retrieve_relevant_context,
        build_rag_prompt,
        is_rag_available,
        get_rag_stats,
        chunk_text,
    )
except ImportError:
    # RAG not available
    pass

try:
    from .model_router import (
        route_model,
        get_model_recommendation,
        track_system_load,
        get_current_system_load,
        MODEL_PROFILES,
    )
except ImportError:
    # Model router not available
    pass

try:
    from .request_queue import (
        rate_limit_decorator,
        process_with_queue,
        get_queue_status,
        get_queue_position,
        check_rate_limit,
        get_client_identifier,
        get_rate_limit_stats,
        clear_rate_limits,
    )
except ImportError:
    # Request queue not available
    pass

# Export all for backward compatibility
__all__ = [
    # Original utils.py functions
    'parse_date',
    'safe_isoformat',
    'sanitize_ip_address',
    'send_log',
    'get_client_ip',
    'LOGGING_SERVICE_URL',
    # Phase 2 utilities
    'get_redis_client',
    'generate_cache_key',
    'get_cached_response',
    'set_cached_response',
    'cached_llm_call',
    'clear_cache_pattern',
    'get_cache_stats',
    'normalize_whitespace',
    'remove_control_characters',
    'truncate_intelligently',
    'preprocess_document',
    'calculate_document_hash',
    'build_few_shot_prompt',
    'get_field_extraction_prompt',
    'get_risk_extraction_prompt',
    'RISK_EXTRACTION_EXAMPLES',
    'FIELD_EXTRACTION_EXAMPLES',
]

