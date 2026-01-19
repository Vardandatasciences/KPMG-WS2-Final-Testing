"""
Background Job Tracker for Compliance Checks
Tracks job status and progress for async compliance processing
"""
import threading
import uuid
import time
import logging
from datetime import datetime
from typing import Dict, Optional
from django.db import connection

logger = logging.getLogger(__name__)

# In-memory job storage (can be moved to database if needed)
_job_storage = {}
_job_lock = threading.Lock()


class ComplianceJobTracker:
    """Tracks background compliance check jobs"""
    
    @staticmethod
    def create_job(audit_id: int, document_id: int, total_requirements: int, tenant_id: int) -> str:
        """Create a new job and return job_id"""
        job_id = str(uuid.uuid4())
        with _job_lock:
            _job_storage[job_id] = {
                'job_id': job_id,
                'audit_id': audit_id,
                'document_id': document_id,
                'tenant_id': tenant_id,
                'status': 'pending',  # pending, processing, completed, failed
                'total_requirements': total_requirements,
                'processed_requirements': 0,
                'completed_requirements': 0,
                'failed_requirements': 0,
                'progress_percent': 0,
                'started_at': datetime.now().isoformat(),
                'completed_at': None,
                'error': None,
                'results': None
            }
        logger.info(f"✅ Created compliance job {job_id} for audit {audit_id}, document {document_id}, {total_requirements} requirements")
        return job_id
    
    @staticmethod
    def get_job(job_id: str) -> Optional[Dict]:
        """Get job status"""
        with _job_lock:
            return _job_storage.get(job_id)
    
    @staticmethod
    def update_progress(job_id: str, processed: int, completed: int, failed: int = 0):
        """Update job progress"""
        with _job_lock:
            if job_id in _job_storage:
                job = _job_storage[job_id]
                job['processed_requirements'] = processed
                job['completed_requirements'] = completed
                job['failed_requirements'] = failed
                if job['total_requirements'] > 0:
                    job['progress_percent'] = int((processed / job['total_requirements']) * 100)
                job['status'] = 'processing'
                logger.debug(f"📊 Job {job_id} progress: {processed}/{job['total_requirements']} ({job['progress_percent']}%)")
    
    @staticmethod
    def complete_job(job_id: str, results: Dict, success: bool = True):
        """Mark job as completed"""
        with _job_lock:
            if job_id in _job_storage:
                job = _job_storage[job_id]
                job['status'] = 'completed' if success else 'failed'
                job['completed_at'] = datetime.now().isoformat()
                job['results'] = results
                job['progress_percent'] = 100
                logger.info(f"✅ Job {job_id} completed: {job['status']}")
    
    @staticmethod
    def fail_job(job_id: str, error: str):
        """Mark job as failed"""
        with _job_lock:
            if job_id in _job_storage:
                job = _job_storage[job_id]
                job['status'] = 'failed'
                job['error'] = error
                job['completed_at'] = datetime.now().isoformat()
                logger.error(f"❌ Job {job_id} failed: {error}")
    
    @staticmethod
    def cleanup_old_jobs(max_age_hours: int = 24):
        """Clean up jobs older than max_age_hours"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        with _job_lock:
            to_remove = []
            for job_id, job in _job_storage.items():
                try:
                    started = datetime.fromisoformat(job['started_at']).timestamp()
                    if started < cutoff_time:
                        to_remove.append(job_id)
                except:
                    to_remove.append(job_id)
            
            for job_id in to_remove:
                del _job_storage[job_id]
            
            if to_remove:
                logger.info(f"🧹 Cleaned up {len(to_remove)} old jobs")
