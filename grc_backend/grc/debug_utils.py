"""
Debug utilities - only output when ENABLE_DEBUG_LOGGING is True.
Use debug_print() instead of print() for verbose logs that should be controllable via env.
"""
from django.conf import settings


def debug_print(*args, **kwargs):
    """Only print when ENABLE_DEBUG_LOGGING is True in settings."""
    if getattr(settings, 'ENABLE_DEBUG_LOGGING', False):
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            # Fallback for Windows terminals that don't support emojis
            clean_args = [str(arg).encode('ascii', 'ignore').decode('ascii') for arg in args]
            print(*clean_args, **kwargs)
        except Exception:
            pass
