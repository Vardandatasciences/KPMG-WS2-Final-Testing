"""
Database Connection Cleanup Middleware
 
Ensures database connections are properly closed after each request
to prevent connection leaks, especially important when CONN_MAX_AGE is set.
"""
from django.db import connections
from django.db import close_old_connections
from django.conf import settings
from django.core.signals import request_finished
from django.dispatch import receiver
from django.utils.deprecation import MiddlewareMixin
import logging
import threading
 
logger = logging.getLogger(__name__)
 
# Thread-local storage to track connection cleanup
_local = threading.local()


def _aggressive_cleanup_enabled():
    """
    Keep aggressive per-request hard-closing configurable.
    Default OFF in DEBUG to avoid expensive reconnect/SSL handshakes.
    """
    configured = getattr(settings, "DB_AGGRESSIVE_CONNECTION_CLEANUP", None)
    if configured is not None:
        return bool(configured)
    return not bool(getattr(settings, "DEBUG", False))
 
 
def _force_close_all_connections():
    """
    Force close all database connections.
    This is called both from middleware and signal handlers.
    """
    closed_count = 0
    try:
        # Use Django's utility to close old connections first
        close_old_connections()
    except Exception as e:
        logger.debug(f"Error in close_old_connections(): {e}")
   
    # Explicitly close all connections for all databases
    for alias in list(connections.databases.keys()):
        try:
            db_conn = connections[alias]
            # Force close the connection regardless of state
            if hasattr(db_conn, 'close'):
                # Check if connection exists and is open
                if hasattr(db_conn, 'connection') and db_conn.connection is not None:
                    try:
                        db_conn.close()
                        closed_count += 1
                    except Exception:
                        # Connection might already be closed, try to ensure it's closed
                        try:
                            if hasattr(db_conn.connection, 'close'):
                                db_conn.connection.close()
                        except Exception:
                            pass
                else:
                    # Connection wrapper exists but no actual connection
                    # Still call close() to ensure cleanup
                    try:
                        db_conn.close()
                    except Exception:
                        pass
        except Exception as e:
            # Log error but don't fail
            logger.debug(f"Error closing database connection '{alias}': {e}")
   
    return closed_count
 
 
@receiver(request_finished)
def close_db_connections_signal(sender, **kwargs):
    """
    Signal handler to close database connections after request finishes.
    This is a backup to ensure connections are closed even if middleware fails.
    """
    try:
        if _aggressive_cleanup_enabled():
            _force_close_all_connections()
        else:
            close_old_connections()
    except Exception as e:
        logger.debug(f"Error in signal handler closing connections: {e}")
 
 
class DatabaseConnectionCleanupMiddleware(MiddlewareMixin):
    """
    Middleware to close database connections after each request.
   
    This prevents connection leaks when CONN_MAX_AGE is set to a non-zero value.
    Django normally handles this, but with persistent connections, explicit cleanup
    is needed to prevent accumulation of idle connections.
   
    This middleware aggressively closes all connections after each request to prevent
    connection pool exhaustion.
    """
   
    def process_request(self, request):
        """
        Clean up any stale connections before processing the request.
        This helps prevent connection accumulation from previous requests.
        """
        # Clean up old connections before starting new request
        try:
            close_old_connections()
        except Exception:
            pass
        return None
   
    def process_response(self, request, response):
        """
        Close all database connections after request processing.
        This ensures connections don't accumulate in the pool.
        """
        # Mark that we're processing this request
        if not hasattr(_local, 'cleanup_done'):
            _local.cleanup_done = False
       
        # Only cleanup once per request (in case middleware is called multiple times)
        if not _local.cleanup_done:
            if _aggressive_cleanup_enabled():
                closed_count = _force_close_all_connections()
            else:
                close_old_connections()
                closed_count = 0
            _local.cleanup_done = True
           
            # Log connection cleanup periodically (every 50th request to avoid spam)
            if not hasattr(_local, 'request_count'):
                _local.request_count = 0
            _local.request_count += 1
           
            if closed_count > 0 and _local.request_count % 50 == 0:
                logger.info(f"[DB Cleanup] Closed {closed_count} connection(s) after request #{_local.request_count}")
       
        return response
   
    def process_exception(self, request, exception):
        """
        Ensure connections are closed even when exceptions occur.
        """
        # Reset cleanup flag so we can cleanup on exception
        _local.cleanup_done = False
        if _aggressive_cleanup_enabled():
            _force_close_all_connections()
        else:
            close_old_connections()
        return None
 
 