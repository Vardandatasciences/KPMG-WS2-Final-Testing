"""
Custom runserver command that handles database connection errors gracefully.
Allows the server to start even when the database is unavailable.
"""
from django.core.management.commands.runserver import Command as BaseRunserverCommand
from django.db import connection
from django.db.utils import OperationalError
import logging

logger = logging.getLogger(__name__)


class Command(BaseRunserverCommand):
    """Custom runserver that skips migration checks if database is unavailable"""
    
    def check_migrations(self):
        """Override to handle database connection errors gracefully"""
        try:
            # Try to check migrations normally
            super().check_migrations()
        except OperationalError as e:
            error_str = str(e).lower()
            # Check if it's a connection error (hostname resolution, connection timeout, etc.)
            if any(keyword in error_str for keyword in ['unknown server host', '11001', '2005', 'can\'t connect', 'connection refused']):
                logger.warning(
                    f"⚠️  Database connection error during migration check: {e}\n"
                    f"⚠️  Skipping migration check. Server will start but database operations may fail.\n"
                    f"⚠️  Please ensure the database is accessible and try again."
                )
                # Don't raise the error - allow server to start
                return
            else:
                # Re-raise other database errors
                raise
        except Exception as e:
            # Check if it's a database-related error
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['database', 'connection', 'mysql', 'operationalerror']):
                logger.warning(
                    f"⚠️  Database error during migration check: {e}\n"
                    f"⚠️  Skipping migration check. Server will start but database operations may fail."
                )
                return
            else:
                # Re-raise non-database errors
                raise
