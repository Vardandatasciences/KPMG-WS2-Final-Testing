"""
AI Response Caching Layer using Redis (with in-memory fallback for Windows)
- Caches LLM responses to avoid redundant API calls
- 10-100x speed improvement on cache hits
- Falls back to in-memory cache if Redis is not available

Configuration:
- Set REDIS_URL in Django settings or environment
- Default: redis://localhost:6379/2 (uses DB 2 for AI cache)
- If Redis unavailable, uses in-memory cache (Windows-friendly)
"""

import hashlib
import json
import time
from typing import Any, Optional, Callable, Dict
import logging

logger = logging.getLogger(__name__)

# Try to import Redis, but don't fail if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️  Redis package not installed. Using in-memory cache fallback.")

# Try to import fakeredis (pure Python Redis - no server required)
try:
    import fakeredis
    FAKEREDIS_AVAILABLE = True
except ImportError:
    FAKEREDIS_AVAILABLE = False

# Redis connection - lazy initialization
_redis_client = None

# In-memory cache fallback (for Windows when Redis is not available)
_in_memory_cache: Dict[str, tuple[Any, float]] = {}  # {key: (value, expiry_time)}

def get_redis_client():
    """Get or create Redis client. Uses fakeredis (pure Python) if Redis server unavailable."""
    global _redis_client
    if not REDIS_AVAILABLE:
        # Try fakeredis if redis package not available
        if FAKEREDIS_AVAILABLE:
            logger.info("💡 Using fakeredis (pure Python Redis) - no server required")
            _redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
            return _redis_client
        return None
    
    if _redis_client is None:
        try:
            # Try to get settings, but handle if Django not configured
            try:
                from django.conf import settings
                redis_url = getattr(settings, 'REDIS_URL', None)
            except:
                redis_url = None
            
            # Fallback to environment variable or default
            if not redis_url:
                import os
                redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/2')
            
            # Parse and configure Redis URL
            # If REDIS_URL doesn't specify a database, use DB 2 for AI cache
            if redis_url.count('/') == 2:  # redis://host:port format
                redis_url = redis_url.rstrip('/') + '/2'
            
            # Create Redis client with proper configuration
            _redis_client = redis.Redis.from_url(
                redis_url, 
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=False,
                health_check_interval=30
            )
            
            # Test connection with short timeout
            _redis_client.ping()
            logger.info(f"✅ Redis cache connected (server): {redis_url}")
            logger.info(f"   Redis version: {_redis_client.info('server').get('redis_version', 'unknown')}")
        except (redis.ConnectionError, redis.TimeoutError, ConnectionRefusedError, OSError) as e:
            # Redis server not available - try fakeredis (pure Python)
            if FAKEREDIS_AVAILABLE:
                logger.warning(f"⚠️  Redis server not available: {e}")
                logger.info("💡 Using fakeredis (pure Python Redis) - no server required!")
                _redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
            else:
                logger.warning(f"⚠️  Redis server not available: {e}")
                logger.info("💡 Using in-memory cache fallback (Windows-friendly)")
                logger.info("   💡 Install fakeredis for better caching: pip install fakeredis")
                _redis_client = None
        except Exception as e:
            logger.warning(f"⚠️  Redis error: {e}")
            # Try fakeredis as fallback
            if FAKEREDIS_AVAILABLE:
                logger.info("💡 Using fakeredis (pure Python Redis) - no server required!")
                _redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
            else:
                logger.info("💡 Using in-memory cache fallback (Windows-friendly)")
                _redis_client = None
    return _redis_client

def generate_cache_key(model_name: str, prompt: str, document_hash: str = None) -> str:
    """
    Generate cache key from model, prompt, and document hash.
    
    Args:
        model_name: LLM model name (e.g., 'llama3.2:3b-instruct-q4_K_M')
        prompt: The prompt text
        document_hash: Optional hash of document content
    
    Returns:
        Cache key string
    """
    key_parts = [model_name, prompt]
    if document_hash:
        key_parts.append(document_hash)
    
    key_string = "|".join(key_parts)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()
    return f"ai_cache:{key_hash}"

def get_cached_response(cache_key: str) -> Optional[Any]:
    """Get cached response if exists (Redis or in-memory fallback)."""
    # Try Redis first
    client = get_redis_client()
    if client:
        try:
            cached = client.get(cache_key)
            if cached:
                logger.debug(f"✅ Cache HIT (Redis): {cache_key[:50]}...")
                return json.loads(cached)
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  Cache decode error for {cache_key[:50]}: {e}")
        except Exception as e:
            logger.warning(f"⚠️  Cache read error: {e}")
    
    # Fallback to in-memory cache
    if cache_key in _in_memory_cache:
        value, expiry = _in_memory_cache[cache_key]
        if expiry > time.time():
            logger.debug(f"✅ Cache HIT (Memory): {cache_key[:50]}...")
            return value
        else:
            # Expired, remove it
            del _in_memory_cache[cache_key]
    
    return None

def set_cached_response(cache_key: str, response: Any, ttl: int = 86400):
    """
    Cache response with TTL (Redis or in-memory fallback).
    
    Args:
        cache_key: Cache key
        response: Response to cache
        ttl: Time to live in seconds (default: 24 hours)
    """
    # Try Redis first
    client = get_redis_client()
    if client:
        try:
            client.setex(
                cache_key,
                ttl,
                json.dumps(response)
            )
            logger.debug(f"💾 Cached response (Redis): {cache_key[:50]}... (TTL: {ttl}s)")
            return
        except Exception as e:
            logger.warning(f"⚠️  Cache write error: {e}")
    
    # Fallback to in-memory cache
    expiry_time = time.time() + ttl
    _in_memory_cache[cache_key] = (response, expiry_time)
    
    # Limit in-memory cache size (keep last 1000 entries)
    if len(_in_memory_cache) > 1000:
        # Remove oldest entries
        sorted_items = sorted(_in_memory_cache.items(), key=lambda x: x[1][1])
        for key, _ in sorted_items[:100]:
            del _in_memory_cache[key]
    
    logger.debug(f"💾 Cached response (Memory): {cache_key[:50]}... (TTL: {ttl}s)")

def cached_llm_call(llm_function: Callable, model_name: str, prompt: str, 
                    document_hash: str = None, ttl: int = 86400, 
                    use_cache: bool = True, **kwargs) -> Any:
    """
    Wrapper for LLM calls with caching.
    
    Args:
        llm_function: The LLM call function (call_ollama_json or call_openai_json)
        model_name: Model name
        prompt: Prompt text
        document_hash: Optional document hash
        ttl: Cache TTL in seconds (default: 24 hours for documents, 3600 for queries)
        use_cache: Whether to use cache (can disable for testing)
        **kwargs: Additional arguments to pass to llm_function (e.g., model, retries, timeout)
    
    Returns:
        LLM response (from cache or fresh call)
    """
    if not use_cache:
        logger.debug("🚫 Cache disabled for this call")
        return llm_function(prompt, **kwargs)
    
    cache_key = generate_cache_key(model_name, prompt, document_hash)
    
    # Try cache first
    cached = get_cached_response(cache_key)
    if cached is not None:
        logger.info(f"⚡ Cache HIT for {model_name[:30]}... (saved API call)")
        return cached
    
    # Cache miss - call LLM
    logger.info(f"❌ Cache MISS for {model_name[:30]}... - calling LLM")
    # Pass all kwargs to the LLM function, but exclude caching-related ones
    call_kwargs = {k: v for k, v in kwargs.items() 
                   if k not in ['document_hash', 'use_cache', 'ttl']}
    response = llm_function(prompt, **call_kwargs)
    
    # Cache the response
    set_cached_response(cache_key, response, ttl)
    
    return response

def clear_cache_pattern(pattern: str = "ai_cache:*"):
    """Clear all cache entries matching pattern (Redis or in-memory)."""
    client = get_redis_client()
    deleted = 0
    
    if client:
        try:
            keys = client.keys(pattern)
            if keys:
                deleted = client.delete(*keys)
                logger.info(f"🗑️  Cleared {deleted} cache entries from Redis matching '{pattern}'")
                return deleted
        except Exception as e:
            logger.warning(f"⚠️  Cache clear error: {e}")
    else:
        # Clear in-memory cache
        if pattern == "ai_cache:*":
            deleted = len(_in_memory_cache)
            _in_memory_cache.clear()
            logger.info(f"🗑️  Cleared {deleted} cache entries from memory")
        else:
            # Pattern matching for in-memory (simple prefix match)
            prefix = pattern.replace("*", "")
            keys_to_delete = [k for k in _in_memory_cache.keys() if k.startswith(prefix)]
            deleted = len(keys_to_delete)
            for key in keys_to_delete:
                del _in_memory_cache[key]
            logger.info(f"🗑️  Cleared {deleted} cache entries from memory matching '{pattern}'")
    
    return deleted

def get_cache_stats() -> dict:
    """Get cache statistics (Redis, fakeredis, or in-memory)."""
    client = get_redis_client()
    if client:
        try:
            # Check if it's fakeredis (has _server attribute)
            is_fakeredis = hasattr(client, '_server') or type(client).__name__ == 'FakeStrictRedis'
            
            keys = client.keys("ai_cache:*")
            cache_type = "fakeredis" if is_fakeredis else "redis"
            
            stats = {
                "status": "available",
                "type": cache_type,
                "total_keys": len(keys),
            }
            
            # Try to get Redis info (fakeredis may not support all commands)
            try:
                if is_fakeredis:
                    stats["message"] = "Using fakeredis (pure Python Redis - no server required)"
                else:
                    stats["redis_info"] = client.info("memory")
            except:
                pass
            
            return stats
        except Exception as e:
            return {"status": "error", "message": str(e)}
    else:
        # Return in-memory cache stats
        # Clean expired entries first
        current_time = time.time()
        expired_keys = [k for k, (_, expiry) in _in_memory_cache.items() if expiry <= current_time]
        for key in expired_keys:
            del _in_memory_cache[key]
        
        return {
            "status": "available",
            "type": "in_memory",
            "total_keys": len(_in_memory_cache),
            "message": "Using in-memory cache (Redis not available)"
        }

