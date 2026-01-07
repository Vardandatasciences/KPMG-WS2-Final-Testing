"""
AI Microservice Client

Client for communicating with AI microservice for async risk extraction.
This simulates the microservice pattern - in production, this would call a separate service.
"""
import requests
import os
import logging
from typing import Dict, Optional, Any
from django.conf import settings

logger = logging.getLogger(__name__)

# AI Microservice Configuration
AI_MICROSERVICE_URL = getattr(settings, 'AI_MICROSERVICE_URL', os.getenv('AI_MICROSERVICE_URL', 'http://localhost:8001'))
AI_MICROSERVICE_API_KEY = getattr(settings, 'AI_MICROSERVICE_API_KEY', os.getenv('AI_MICROSERVICE_API_KEY', 'your-secret-key-here'))


class AIServiceUnavailable(Exception):
    """Raised when AI microservice is unavailable"""
    pass


class AIMicroserviceClient:
    """
    Client for AI microservice.
    
    In a real implementation, this would call a separate microservice.
    For now, this can be used as a placeholder or can trigger local async processing.
    """
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or AI_MICROSERVICE_URL
        self.api_key = api_key or AI_MICROSERVICE_API_KEY
    
    def extract_risks(
        self,
        document_url: str,
        job_id: str,
        callback_url: str,
        organization_id: Optional[int] = None,
        document_type: str = 'risk_assessment',
        priority: str = 'normal'
    ) -> Dict[str, Any]:
        """
        Submit a document for async risk extraction.
        
        Args:
            document_url: S3 URL of the document
            job_id: Unique job identifier
            callback_url: URL for microservice to call when complete
            organization_id: Optional organization ID
            document_type: Type of document
            priority: Processing priority ('low', 'normal', 'high')
        
        Returns:
            Dict with job acceptance confirmation
        
        Raises:
            AIServiceUnavailable: If service is down
        """
        try:
            # In production, this would POST to the microservice
            # For now, we'll simulate or trigger local async processing
            payload = {
                'document_url': document_url,
                'job_id': job_id,
                'callback_url': callback_url,
                'organization_id': organization_id,
                'document_type': document_type,
                'priority': priority
            }
            
            headers = {
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            # Try to call microservice (if available)
            try:
                response = requests.post(
                    f"{self.base_url}/api/extract-risks",
                    json=payload,
                    headers=headers,
                    timeout=5
                )
                response.raise_for_status()
                return response.json()
            except (requests.exceptions.RequestException, requests.exceptions.Timeout):
                # Microservice not available - will be handled by local async processing
                logger.warning(f"AI microservice unavailable at {self.base_url}, will use local processing")
                raise AIServiceUnavailable(f"AI service at {self.base_url} is unavailable")
        
        except AIServiceUnavailable:
            raise
        except Exception as e:
            logger.error(f"Error calling AI microservice: {e}")
            raise AIServiceUnavailable(f"Failed to contact AI service: {str(e)}")
    
    def submit_feedback(
        self,
        job_id: str,
        document_hash: str,
        corrections: list,
        overall_rating: Optional[int] = None,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        is_expert_validated: bool = False,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit user feedback for AI learning.
        
        Args:
            job_id: Original job ID
            document_hash: Document hash for reference
            corrections: List of corrections made by user
            overall_rating: Overall rating (1-5)
            user_id: User ID
            user_role: User role
            is_expert_validated: Whether validated by expert
            comments: Additional comments
        
        Returns:
            Dict with feedback acceptance confirmation
        """
        try:
            payload = {
                'job_id': job_id,
                'document_hash': document_hash,
                'corrections': corrections,
                'overall_rating': overall_rating,
                'user_id': user_id,
                'user_role': user_role,
                'is_expert_validated': is_expert_validated,
                'comments': comments
            }
            
            headers = {
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.base_url}/api/feedback",
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            logger.error(f"Error submitting feedback to AI microservice: {e}")
            return {
                'status': 'error',
                'message': f'Failed to submit feedback: {str(e)}'
            }


# Singleton instance
_ai_client = None

def get_ai_client() -> AIMicroserviceClient:
    """Get singleton AI microservice client instance"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIMicroserviceClient()
    return _ai_client



