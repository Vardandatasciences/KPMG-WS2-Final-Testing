"""
Framework context module for storing and retrieving framework ID
This provides a persistent storage backed by Django's cache
"""
import logging
from typing import Optional
from django.core.cache import cache

logger = logging.getLogger(__name__)

def set_framework_context(user_id: str, framework_id: str, request=None) -> None:
    """
    Store framework ID for a user in the centralized cache
    
    Args:
        user_id: The user ID
        framework_id: The framework ID
        request: Optional Django request object to also clear session
    """
    # Normalize user_id and framework_id to strings for consistency
    user_id_str = str(user_id)
    framework_id_str = str(framework_id)
    
    # Store in cache for 7 days (matching session lifetime)
    cache_key = f"framework_context_{user_id_str}"
    try:
        cache.set(cache_key, framework_id_str, 7 * 24 * 60 * 60)
        logger.info(f"✅ Framework context set in cache: User {user_id_str}, Framework {framework_id_str}")
    except Exception as e:
        logger.error(f"❌ Failed to set framework context in cache for user {user_id_str}: {e}")
    
    # Clear session if provided (to prevent conflicts)
    if request and hasattr(request, 'session'):
        try:
            modified = False
            if 'selected_framework_id' in request.session:
                del request.session['selected_framework_id']
                modified = True
            if 'grc_framework_selected' in request.session:
                del request.session['grc_framework_selected']
                modified = True
            
            if modified:
                request.session.save()
                logger.debug(f"🧹 Cleared old session data when setting new framework context")
        except Exception as e:
            logger.warning(f"⚠️ Could not clear session: {str(e)}")

def get_framework_context(user_id: str) -> Optional[str]:
    """
    Get framework ID for a user from the centralized cache
    
    Args:
        user_id: The user ID
        
    Returns:
        The framework ID or None if not found
    """
    # Ensure user_id is a string for consistent comparison
    user_id_str = str(user_id)
    cache_key = f"framework_context_{user_id_str}"
    
    try:
        framework_id = cache.get(cache_key)
        if framework_id:
            logger.debug(f"✅ Framework context retrieved from cache: User {user_id_str}, Framework {framework_id}")
            return str(framework_id)
    except Exception as e:
        logger.error(f"❌ Error retrieving framework context from cache for user {user_id_str}: {e}")
    
    logger.debug(f"❌ Framework context not found in cache for user {user_id_str}")
    return None

def clear_framework_context(user_id: str, request=None) -> None:
    """
    Clear framework ID for a user from the centralized cache
    
    Args:
        user_id: The user ID
        request: Optional Django request object to also clear session
    """
    user_id_str = str(user_id)
    cache_key = f"framework_context_{user_id_str}"
    
    try:
        cache.delete(cache_key)
        logger.info(f"✅ Framework context cleared in cache for user {user_id_str}")
    except Exception as e:
        logger.error(f"❌ Failed to clear framework context in cache for user {user_id_str}: {e}")
    
    # Clear from session if provided
    if request and hasattr(request, 'session'):
        try:
            modified = False
            if 'selected_framework_id' in request.session:
                del request.session['selected_framework_id']
                modified = True
            if 'grc_framework_selected' in request.session:
                del request.session['grc_framework_selected']
                modified = True
            
            if modified:
                request.session.save()
                logger.debug(f"🧹 Cleared framework keys from session")
        except Exception as e:
            logger.warning(f"⚠️ Could not clear session: {str(e)}")
