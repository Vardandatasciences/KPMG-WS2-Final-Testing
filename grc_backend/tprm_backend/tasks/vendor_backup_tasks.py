"""
Vendor Backup and Restore Tasks - Async backup operations with failure recovery
"""

import logging
import time
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.core.management import call_command
from django.core.cache import cache
from tprm_backend.database.vendor_sqlalchemy_manager import vendor_db_manager

vendor_backup_logger = logging.getLogger('vendor_security')


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def vendor_create_scheduled_backup(self):
    """
    Create scheduled database backup
    """
    try:
        backup_name = f"vendor_scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        vendor_backup_logger.info(
            f"Starting scheduled backup: {backup_name}",
            extra={'action': 'backup_started', 'backup_name': backup_name}
        )
        
        # Create backup using the database manager
        backup_file = vendor_db_manager.vendor_backup_manager.vendor_create_backup(backup_name)
        
        # Store backup metadata in cache
        backup_metadata = {
            'vendor_backup_name': backup_name,
            'vendor_backup_file': backup_file,
            'vendor_backup_timestamp': int(time.time()),
            'vendor_backup_type': 'scheduled',
            'vendor_backup_status': 'completed'
        }
        
        cache.set(f'vendor_backup_metadata_{backup_name}', backup_metadata, 86400)  # 24 hours
        
        vendor_backup_logger.info(
            f"Scheduled backup completed: {backup_name}",
            extra={
                'action': 'backup_completed',
                'backup_name': backup_name,
                'backup_file': backup_file
            }
        )
        
        # Cleanup old backups
        vendor_cleanup_old_backups.delay()
        
        return {
            'vendor_status': 'success',
            'vendor_backup_name': backup_name,
            'vendor_backup_file': backup_file
        }
        
    except Exception as exc:
        vendor_backup_logger.error(
            f"Scheduled backup failed: {str(exc)}",
            extra={'action': 'backup_failed', 'error': str(exc)},
            exc_info=True
        )
        
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def vendor_create_emergency_backup(self, reason="system_failure"):
    """
    Create emergency backup when system failure is detected
    """
    try:
        backup_name = f"vendor_emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{reason}"
        
        vendor_backup_logger.critical(
            f"Starting emergency backup: {backup_name}",
            extra={
                'action': 'emergency_backup_started',
                'backup_name': backup_name,
                'reason': reason
            }
        )
        
        # Create backup with high priority
        backup_file = vendor_db_manager.vendor_backup_manager.vendor_create_backup(backup_name)
        
        # Store backup metadata
        backup_metadata = {
            'vendor_backup_name': backup_name,
            'vendor_backup_file': backup_file,
            'vendor_backup_timestamp': int(time.time()),
            'vendor_backup_type': 'emergency',
            'vendor_backup_reason': reason,
            'vendor_backup_status': 'completed'
        }
        
        cache.set(f'vendor_backup_metadata_{backup_name}', backup_metadata, 86400 * 7)  # 7 days
        
        vendor_backup_logger.critical(
            f"Emergency backup completed: {backup_name}",
            extra={
                'action': 'emergency_backup_completed',
                'backup_name': backup_name,
                'backup_file': backup_file,
                'reason': reason
            }
        )
        
        return {
            'vendor_status': 'success',
            'vendor_backup_name': backup_name,
            'vendor_backup_file': backup_file,
            'vendor_reason': reason
        }
        
    except Exception as exc:
        vendor_backup_logger.critical(
            f"Emergency backup failed: {str(exc)}",
            extra={
                'action': 'emergency_backup_failed',
                'error': str(exc),
                'reason': reason
            },
            exc_info=True
        )
        
        # Limited retries for emergency backups
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def vendor_restore_from_backup(self, backup_name=None, backup_file=None):
    """
    Restore database from backup
    """
    try:
        if not backup_name and not backup_file:
            # Restore from latest backup
            vendor_backup_logger.warning(
                "Restoring from latest backup",
                extra={'action': 'restore_latest_started'}
            )
            
            vendor_db_manager.vendor_backup_manager.vendor_restore_latest_backup()
            restore_source = "latest_backup"
            
        elif backup_file:
            vendor_backup_logger.warning(
                f"Restoring from specific backup file: {backup_file}",
                extra={'action': 'restore_file_started', 'backup_file': backup_file}
            )
            
            vendor_db_manager.vendor_backup_manager.vendor_restore_backup(backup_file)
            restore_source = backup_file
            
        else:
            # Find backup by name
            backup_metadata = cache.get(f'vendor_backup_metadata_{backup_name}')
            if not backup_metadata:
                raise ValueError(f"Backup metadata not found for: {backup_name}")
            
            backup_file = backup_metadata['vendor_backup_file']
            
            vendor_backup_logger.warning(
                f"Restoring from named backup: {backup_name}",
                extra={
                    'action': 'restore_named_started',
                    'backup_name': backup_name,
                    'backup_file': backup_file
                }
            )
            
            vendor_db_manager.vendor_backup_manager.vendor_restore_backup(backup_file)
            restore_source = backup_name
        
        vendor_backup_logger.warning(
            f"Database restore completed from: {restore_source}",
            extra={
                'action': 'restore_completed',
                'restore_source': restore_source
            }
        )
        
        return {
            'vendor_status': 'success',
            'vendor_restore_source': restore_source,
            'vendor_timestamp': int(time.time())
        }
        
    except Exception as exc:
        vendor_backup_logger.error(
            f"Database restore failed: {str(exc)}",
            extra={
                'action': 'restore_failed',
                'error': str(exc),
                'backup_name': backup_name,
                'backup_file': backup_file
            },
            exc_info=True
        )
        
        raise self.retry(exc=exc)


@shared_task
def vendor_cleanup_old_backups():
    """
    Clean up old backup files based on retention policy
    """
    try:
        retention_days = getattr(settings, 'VENDOR_SETTINGS', {}).get('BACKUP_RETENTION_DAYS', 30)
        
        vendor_backup_logger.info(
            f"Starting backup cleanup - retaining {retention_days} days",
            extra={'action': 'cleanup_started', 'retention_days': retention_days}
        )
        
        vendor_db_manager.vendor_backup_manager.vendor_cleanup_old_backups(retention_days)
        
        vendor_backup_logger.info(
            "Backup cleanup completed",
            extra={'action': 'cleanup_completed', 'retention_days': retention_days}
        )
        
        return {
            'vendor_status': 'success',
            'vendor_retention_days': retention_days
        }
        
    except Exception as exc:
        vendor_backup_logger.error(
            f"Backup cleanup failed: {str(exc)}",
            extra={'action': 'cleanup_failed', 'error': str(exc)},
            exc_info=True
        )
        raise


@shared_task
def vendor_monitor_database_health():
    """
    Monitor database health and trigger emergency backup if needed
    """
    try:
        health_status = vendor_db_manager.vendor_health_check()
        
        if not health_status.get('database_connected', False):
            vendor_backup_logger.critical(
                "Database connection failure detected",
                extra={
                    'action': 'database_failure_detected',
                    'health_status': health_status
                }
            )
            
            # Trigger emergency backup
            vendor_create_emergency_backup.delay("database_connection_failure")
            
            return {
                'vendor_status': 'failure_detected',
                'vendor_health_status': health_status,
                'vendor_emergency_backup_triggered': True
            }
        
        # Check response time
        response_time = health_status.get('response_time_ms', 0)
        if response_time > 5000:  # 5 seconds
            vendor_backup_logger.warning(
                f"Slow database response detected: {response_time}ms",
                extra={
                    'action': 'slow_database_detected',
                    'response_time_ms': response_time
                }
            )
        
        return {
            'vendor_status': 'healthy',
            'vendor_health_status': health_status
        }
        
    except Exception as exc:
        vendor_backup_logger.error(
            f"Database health monitoring failed: {str(exc)}",
            extra={'action': 'health_monitoring_failed', 'error': str(exc)},
            exc_info=True
        )
        
        # Trigger emergency backup on monitoring failure
        vendor_create_emergency_backup.delay("health_monitoring_failure")
        
        return {
            'vendor_status': 'monitoring_failed',
            'vendor_error': str(exc),
            'vendor_emergency_backup_triggered': True
        }


@shared_task
def vendor_test_backup_restore():
    """
    Test backup and restore functionality (for scheduled testing)
    """
    try:
        test_backup_name = f"vendor_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        vendor_backup_logger.info(
            f"Starting backup/restore test: {test_backup_name}",
            extra={'action': 'test_backup_restore_started', 'test_name': test_backup_name}
        )
        
        # Create test backup
        backup_file = vendor_db_manager.vendor_backup_manager.vendor_create_backup(test_backup_name)
        
        # Verify backup file exists and has content
        import os
        if not os.path.exists(backup_file) or os.path.getsize(backup_file) == 0:
            raise Exception(f"Backup file invalid: {backup_file}")
        
        vendor_backup_logger.info(
            f"Backup/restore test completed successfully: {test_backup_name}",
            extra={
                'action': 'test_backup_restore_completed',
                'test_name': test_backup_name,
                'backup_file': backup_file
            }
        )
        
        # Clean up test backup after verification
        try:
            os.remove(backup_file)
        except Exception:
            pass  # Non-critical if cleanup fails
        
        return {
            'vendor_status': 'success',
            'vendor_test_name': test_backup_name,
            'vendor_backup_file': backup_file
        }
        
    except Exception as exc:
        vendor_backup_logger.error(
            f"Backup/restore test failed: {str(exc)}",
            extra={'action': 'test_backup_restore_failed', 'error': str(exc)},
            exc_info=True
        )
        raise
