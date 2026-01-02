"""
Threading-based async service for vendor risk generation

This module provides non-blocking risk generation using Python threading
instead of Celery/Redis, making it perfect for small to medium scale deployments.
"""

import threading
import logging
from typing import Dict, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


class VendorRiskThreadingService:
    """
    Service for running vendor risk generation in background threads
    
    This provides async-like behavior without requiring Redis/Celery:
    - Non-blocking user interface
    - Background processing
    - Proper error handling
    - Thread safety
    """
    
    def __init__(self):
        self.active_threads = {}  # Track active threads
        self.thread_results = {}  # Store thread results
    
    def trigger_vendor_risk_generation_async(self, approval_id: str) -> Dict:
        """
        Trigger vendor risk generation in a background thread
        
        Args:
            approval_id: The approval request ID that was just approved
            
        Returns:
            Dict with thread info and immediate status
        """
        try:
            # Check if already running for this approval
            if approval_id in self.active_threads:
                thread = self.active_threads[approval_id]
                if thread.is_alive():
                    logger.warning(f"Risk generation already running for approval {approval_id}")
                    return {
                        'status': 'already_running',
                        'approval_id': approval_id,
                        'message': 'Risk generation already in progress'
                    }
            
            # Create and start background thread
            thread = threading.Thread(
                target=self._run_vendor_risk_generation,
                args=(approval_id,),
                name=f"VendorRisk-{approval_id}",
                daemon=True  # Auto-cleanup when Django shuts down
            )
            
            # Store thread reference
            self.active_threads[approval_id] = thread
            
            # Start the thread
            thread.start()
            
            logger.info(f"Started vendor risk generation thread for approval: {approval_id}")
            
            return {
                'status': 'started',
                'approval_id': approval_id,
                'thread_name': thread.name,
                'message': 'Vendor risk generation started in background'
            }
            
        except Exception as e:
            logger.error(f"Failed to start vendor risk generation thread for {approval_id}: {str(e)}")
            return {
                'status': 'error',
                'approval_id': approval_id,
                'error': str(e),
                'message': 'Failed to start background risk generation'
            }
    
    def _run_vendor_risk_generation(self, approval_id: str):
        """
        Background thread function that runs vendor risk generation
        
        This runs in a separate thread and handles all errors gracefully
        """
        start_time = timezone.now()
        
        try:
            logger.info(f"Background thread starting vendor risk generation for approval: {approval_id}")
            
            # Import the risk analysis service
            from .services import RiskAnalysisService
            
            # Create service instance and run risk generation
            risk_service = RiskAnalysisService()
            result = risk_service.generate_vendor_risks(approval_id)
            
            # Calculate processing time
            end_time = timezone.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Store successful result
            self.thread_results[approval_id] = {
                'status': 'completed',
                'approval_id': approval_id,
                'result': result,
                'processing_time': processing_time,
                'completed_at': end_time.isoformat()
            }
            
            if result.get('status') == 'success':
                logger.info(f"Background vendor risk generation completed successfully for approval {approval_id} "
                          f"in {processing_time:.2f} seconds. Created {result.get('risks_created', 0)} risks.")
            else:
                logger.warning(f"Background vendor risk generation completed with issues for approval {approval_id}: "
                             f"{result.get('error', result.get('message', 'Unknown issue'))}")
            
        except Exception as e:
            # Calculate processing time even for errors
            end_time = timezone.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Store error result
            error_message = str(e)
            self.thread_results[approval_id] = {
                'status': 'error',
                'approval_id': approval_id,
                'error': error_message,
                'processing_time': processing_time,
                'completed_at': end_time.isoformat()
            }
            
            logger.error(f"Background vendor risk generation failed for approval {approval_id} "
                        f"after {processing_time:.2f} seconds: {error_message}")
            
        finally:
            # Clean up thread reference
            if approval_id in self.active_threads:
                del self.active_threads[approval_id]
            
            logger.debug(f"Cleaned up thread reference for approval {approval_id}")
    
    def get_thread_status(self, approval_id: str) -> Optional[Dict]:
        """
        Get status of risk generation thread for specific approval
        
        Args:
            approval_id: The approval request ID
            
        Returns:
            Dict with thread status or None if not found
        """
        # Check if thread is still running
        if approval_id in self.active_threads:
            thread = self.active_threads[approval_id]
            if thread.is_alive():
                return {
                    'status': 'running',
                    'approval_id': approval_id,
                    'thread_name': thread.name
                }
        
        # Check if we have results
        if approval_id in self.thread_results:
            return self.thread_results[approval_id]
        
        return None
    
    def get_all_active_threads(self) -> Dict:
        """
        Get status of all active risk generation threads
        
        Returns:
            Dict with information about all active threads
        """
        active = {}
        completed = {}
        
        # Check active threads
        for approval_id, thread in list(self.active_threads.items()):
            if thread.is_alive():
                active[approval_id] = {
                    'thread_name': thread.name,
                    'status': 'running'
                }
            else:
                # Thread finished but reference not cleaned up yet
                del self.active_threads[approval_id]
        
        # Get completed results
        for approval_id, result in self.thread_results.items():
            completed[approval_id] = result
        
        return {
            'active_threads': active,
            'completed_results': completed,
            'total_active': len(active),
            'total_completed': len(completed)
        }
    
    def cleanup_old_results(self, max_results: int = 100):
        """
        Clean up old thread results to prevent memory buildup
        
        Args:
            max_results: Maximum number of results to keep
        """
        if len(self.thread_results) > max_results:
            # Sort by completion time and keep the most recent
            sorted_items = sorted(
                self.thread_results.items(),
                key=lambda x: x[1].get('completed_at', ''),
                reverse=True
            )
            
            # Keep only the most recent results
            self.thread_results = dict(sorted_items[:max_results])
            
            logger.info(f"Cleaned up old thread results, keeping {len(self.thread_results)} most recent")


# Global service instance
vendor_risk_threading_service = VendorRiskThreadingService()


def trigger_vendor_risk_generation_async(approval_id: str) -> Dict:
    """
    Convenience function to trigger vendor risk generation in background thread
    
    Args:
        approval_id: The approval request ID that was just approved
        
    Returns:
        Dict with immediate status response
    """
    return vendor_risk_threading_service.trigger_vendor_risk_generation_async(approval_id)


def get_risk_generation_status(approval_id: str) -> Optional[Dict]:
    """
    Convenience function to get risk generation status
    
    Args:
        approval_id: The approval request ID
        
    Returns:
        Dict with status or None if not found
    """
    return vendor_risk_threading_service.get_thread_status(approval_id)
