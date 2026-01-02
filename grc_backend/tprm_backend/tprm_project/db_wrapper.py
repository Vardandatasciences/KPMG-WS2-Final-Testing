"""
Database connection wrapper that handles connection errors gracefully.
Makes database connections lazy and provides fallback behavior.
"""
from django.db import connections
from django.db.utils import OperationalError
import logging

logger = logging.getLogger(__name__)


def get_database_connection(alias='default'):
    """
    Get database connection with error handling.
    Returns None if connection cannot be established.
    """
    try:
        connection = connections[alias]
        # Try to ensure connection is established
        connection.ensure_connection()
        return connection
    except OperationalError as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['unknown server host', '11001', '2005', 'can\'t connect', 'connection refused']):
            logger.warning(f"Database connection error: {e}. Database may be unreachable.")
            return None
        else:
            raise
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['database', 'connection', 'mysql']):
            logger.warning(f"Database error: {e}")
            return None
        else:
            raise


def is_database_available(alias='default'):
    """Check if database is available without raising exceptions"""
    try:
        connection = connections[alias]
        connection.ensure_connection()
        return True
    except Exception:
        return False

