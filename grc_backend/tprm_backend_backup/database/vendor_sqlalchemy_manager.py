"""
Secure SQLAlchemy Database Manager for Vendor TPRM System
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.pool import QueuePool
from django.conf import settings
from cryptography.fernet import Fernet
import json

# Configure logging
vendor_logger = logging.getLogger('vendor_security')

# Base for SQLAlchemy models
VendorBase = declarative_base()


class VendorDatabaseManager:
    """Secure database manager with backup/restore capabilities"""
    
    def __init__(self):
        self.vendor_engine = None
        self.vendor_session_factory = None
        self.vendor_encryption_key = self._vendor_get_encryption_key()
        self.vendor_backup_manager = VendorBackupManager()
        self._vendor_initialize_engine()
    
    def _vendor_get_encryption_key(self) -> bytes:
        """Get or generate encryption key for sensitive data"""
        key = getattr(settings, 'VENDOR_SETTINGS', {}).get('ENCRYPTION_KEY')
        if not key:
            # Generate a new key if not provided
            key = Fernet.generate_key()
            vendor_logger.warning("No encryption key provided, generated new key")
        return key.encode() if isinstance(key, str) else key
    
    def _vendor_initialize_engine(self):
        """Initialize SQLAlchemy engine with secure configuration"""
        try:
            # Database URL from settings
            database_url = settings.VENDOR_SQLALCHEMY_DATABASE_URI
            
            # Engine configuration with security best practices
            engine_config = {
                'poolclass': QueuePool,
                'pool_size': 10,
                'max_overflow': 20,
                'pool_pre_ping': True,
                'pool_recycle': 3600,  # Recycle connections every hour
                'echo': settings.DEBUG,
                'isolation_level': 'READ_COMMITTED',
            }
            
            self.vendor_engine = create_engine(database_url, **engine_config)
            
            # Add connection event listeners for security
            self._vendor_setup_connection_events()
            
            # Create session factory
            self.vendor_session_factory = sessionmaker(
                bind=self.vendor_engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            vendor_logger.info("Database engine initialized successfully")
            
        except Exception as e:
            vendor_logger.error(f"Failed to initialize database engine: {str(e)}")
            raise
    
    def _vendor_setup_connection_events(self):
        """Setup database connection event listeners"""
        
        @event.listens_for(self.vendor_engine, "connect")
        def vendor_set_connection_options(dbapi_connection, connection_record):
            """Set secure connection options"""
            with dbapi_connection.cursor() as cursor:
                # Set session variables for security
                cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")
                cursor.execute("SET SESSION innodb_strict_mode = 1")
                cursor.execute("SET SESSION autocommit = 0")
        
        @event.listens_for(self.vendor_engine, "checkout")
        def vendor_log_connection_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout for monitoring"""
            vendor_logger.debug("Database connection checked out")
        
        @event.listens_for(self.vendor_engine, "checkin")
        def vendor_log_connection_checkin(dbapi_connection, connection_record):
            """Log connection checkin for monitoring"""
            vendor_logger.debug("Database connection checked in")
    
    @contextmanager
    def vendor_get_session(self, auto_backup=True):
        """
        Secure session context manager with automatic backup on failure
        """
        session = None
        try:
            session = self.vendor_session_factory()
            vendor_logger.debug("Database session created")
            yield session
            session.commit()
            vendor_logger.debug("Database session committed successfully")
            
        except OperationalError as e:
            vendor_logger.error(f"Database operational error: {str(e)}")
            if session:
                session.rollback()
            
            # Attempt backup and restore on connection failure
            if auto_backup and "connection" in str(e).lower():
                self._vendor_handle_connection_failure()
            raise
            
        except SQLAlchemyError as e:
            vendor_logger.error(f"Database error: {str(e)}")
            if session:
                session.rollback()
            raise
            
        except Exception as e:
            vendor_logger.error(f"Unexpected error in database session: {str(e)}")
            if session:
                session.rollback()
            raise
            
        finally:
            if session:
                session.close()
                vendor_logger.debug("Database session closed")
    
    def vendor_execute_safe_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute parameterized query safely
        """
        if params is None:
            params = {}
        
        # Log query execution (without sensitive data)
        vendor_logger.info(f"Executing query: {query[:100]}...")
        
        with self.vendor_get_session() as session:
            try:
                result = session.execute(query, params)
                return result.fetchall()
            except Exception as e:
                vendor_logger.error(f"Query execution failed: {str(e)}")
                raise
    
    def vendor_encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data before storage"""
        try:
            fernet = Fernet(self.vendor_encryption_key)
            encrypted_data = fernet.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            vendor_logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def vendor_decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data after retrieval"""
        try:
            fernet = Fernet(self.vendor_encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            vendor_logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def _vendor_handle_connection_failure(self):
        """Handle database connection failures with backup/restore"""
        vendor_logger.warning("Handling database connection failure")
        
        try:
            # Attempt to restore from latest backup
            self.vendor_backup_manager.vendor_restore_latest_backup()
            
            # Reinitialize engine
            self._vendor_initialize_engine()
            
            vendor_logger.info("Database connection restored successfully")
            
        except Exception as e:
            vendor_logger.error(f"Failed to restore database connection: {str(e)}")
            raise
    
    def vendor_health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        health_status = {
            'database_connected': False,
            'response_time_ms': None,
            'active_connections': 0,
            'timestamp': time.time()
        }
        
        try:
            start_time = time.time()
            
            with self.vendor_get_session(auto_backup=False) as session:
                session.execute("SELECT 1")
                
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            health_status.update({
                'database_connected': True,
                'response_time_ms': round(response_time, 2),
                'active_connections': self.vendor_engine.pool.size()
            })
            
            vendor_logger.info(f"Database health check passed: {response_time:.2f}ms")
            
        except Exception as e:
            vendor_logger.error(f"Database health check failed: {str(e)}")
            health_status['error'] = str(e)
        
        return health_status


class VendorBackupManager:
    """Manages database backup and restore operations"""
    
    def __init__(self):
        self.vendor_backup_directory = settings.BASE_DIR / 'backups'
        self.vendor_backup_directory.mkdir(exist_ok=True)
    
    def vendor_create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create database backup"""
        if not backup_name:
            backup_name = f"vendor_backup_{int(time.time())}"
        
        backup_file = self.vendor_backup_directory / f"{backup_name}.sql"
        
        try:
            # Use Django's dbbackup command
            from django.core.management import call_command
            call_command('dbbackup', output_filename=backup_file.name)
            
            vendor_logger.info(f"Database backup created: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            vendor_logger.error(f"Backup creation failed: {str(e)}")
            raise
    
    def vendor_restore_backup(self, backup_file: str):
        """Restore database from backup"""
        try:
            from django.core.management import call_command
            call_command('dbrestore', input_filename=backup_file)
            
            vendor_logger.info(f"Database restored from: {backup_file}")
            
        except Exception as e:
            vendor_logger.error(f"Backup restoration failed: {str(e)}")
            raise
    
    def vendor_restore_latest_backup(self):
        """Restore from the latest backup"""
        try:
            backup_files = list(self.vendor_backup_directory.glob("*.sql"))
            if not backup_files:
                raise FileNotFoundError("No backup files found")
            
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            self.vendor_restore_backup(latest_backup.name)
            
        except Exception as e:
            vendor_logger.error(f"Latest backup restoration failed: {str(e)}")
            raise
    
    def vendor_cleanup_old_backups(self, keep_days: int = 30):
        """Clean up old backup files"""
        try:
            cutoff_time = time.time() - (keep_days * 24 * 3600)
            
            for backup_file in self.vendor_backup_directory.glob("*.sql"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    vendor_logger.info(f"Deleted old backup: {backup_file}")
                    
        except Exception as e:
            vendor_logger.error(f"Backup cleanup failed: {str(e)}")


# Global database manager instance
vendor_db_manager = VendorDatabaseManager()
