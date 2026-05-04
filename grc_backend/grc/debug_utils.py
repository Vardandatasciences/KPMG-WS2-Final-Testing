"""
Debug utilities - only output when ENABLE_DEBUG_LOGGING is True.
Use debug_print() instead of print() for verbose logs that should be controllable via env.
"""
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def debug_print(*args, **kwargs):
    """
    Route-level verbose trace printing is gated behind a dedicated switch to prevent
    high-volume terminal spam during normal debugging.
    """
    debug_enabled = getattr(settings, 'ENABLE_DEBUG_LOGGING', False)
    verbose_route_enabled = getattr(settings, 'ENABLE_VERBOSE_ROUTE_DEBUG', False)
    if debug_enabled and verbose_route_enabled:
        try:
            # Keep as logger-based output (instead of raw print) so global logging controls apply.
            logger.debug(" ".join(str(arg) for arg in args))
        except UnicodeEncodeError:
            # Fallback for Windows terminals that don't support emojis
            clean_args = [str(arg).encode('ascii', 'ignore').decode('ascii') for arg in args]
            logger.debug(" ".join(clean_args))
        except Exception:
            pass
