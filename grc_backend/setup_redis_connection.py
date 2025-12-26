#!/usr/bin/env python
"""
Redis Connection Setup and Test Script
Tests and configures Redis connection for Phase 2 caching.
"""

import os
import sys

def test_redis_connection():
    """Test Redis connection with various configurations."""
    print("🔧 Testing Redis Connection Setup...\n")
    
    # Test 1: Check if redis package is installed
    print("1. Checking Redis package...")
    try:
        import redis
        print(f"   ✅ Redis package installed: {redis.__version__}")
    except ImportError:
        print("   ❌ Redis package not installed")
        print("   💡 Install with: pip install redis")
        return False
    
    # Test 2: Try different connection methods
    print("\n2. Testing connection methods...")
    
    # Method 1: Default localhost
    print("   Testing: redis://localhost:6379/2")
    try:
        client = redis.Redis(
            host='localhost',
            port=6379,
            db=2,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        client.ping()
        print("   ✅ Connected to Redis on localhost:6379")
        print(f"   📊 Redis version: {client.info('server').get('redis_version', 'unknown')}")
        print(f"   💾 Memory used: {client.info('memory').get('used_memory_human', 'unknown')}")
        return True
    except redis.ConnectionError as e:
        print(f"   ❌ Connection failed: {e}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Method 2: Try with environment variable
    print("\n   Testing: REDIS_URL from environment")
    redis_url = os.environ.get('REDIS_URL', None)
    if redis_url:
        print(f"   Found REDIS_URL: {redis_url}")
        try:
            client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2
            )
            client.ping()
            print("   ✅ Connected using REDIS_URL")
            return True
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
    else:
        print("   ℹ️  REDIS_URL not set in environment")
    
    # Method 3: Try WSL Redis
    print("\n   Testing: WSL Redis (if available)")
    try:
        import subprocess
        result = subprocess.run(['wsl', 'redis-cli', 'ping'], 
                               capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("   ✅ Redis is running in WSL")
            print("   💡 You can use: redis://localhost:6379/2")
            print("   💡 Or configure WSL port forwarding")
            return True
    except Exception as e:
        print(f"   ℹ️  WSL Redis check skipped: {e}")
    
    print("\n❌ Redis connection failed")
    print("\n💡 Solutions:")
    print("   1. Install Redis on Windows:")
    print("      - Use WSL: wsl sudo apt install redis-server")
    print("      - Or use Docker: docker run -d -p 6379:6379 redis")
    print("      - Or use Memurai: https://www.memurai.com/")
    print("\n   2. Start Redis service:")
    print("      - WSL: sudo service redis-server start")
    print("      - Docker: docker start <container-name>")
    print("\n   3. The code will use in-memory cache as fallback")
    print("      (caching will still work, just not persistent)")
    
    return False

def configure_redis_in_settings():
    """Add Redis configuration to Django settings if not present."""
    print("\n3. Checking Django settings...")
    
    settings_files = [
        'backend/settings.py',
        'tprm_backend/config/settings.py',
        'tprm_backend/config/settings.py'
    ]
    
    for settings_file in settings_files:
        if os.path.exists(settings_file):
            print(f"   Found: {settings_file}")
            try:
                with open(settings_file, 'r') as f:
                    content = f.read()
                    if 'REDIS_URL' in content:
                        print("   ✅ REDIS_URL already configured")
                        return True
                    else:
                        print("   ⚠️  REDIS_URL not found in settings")
                        print("   💡 Add this to your settings.py:")
                        print("      REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/2')")
            except Exception as e:
                print(f"   ⚠️  Could not read settings: {e}")
    
    return False

if __name__ == '__main__':
    print("="*60)
    print("Redis Connection Setup for Phase 2 Caching")
    print("="*60)
    print()
    
    connected = test_redis_connection()
    configure_redis_in_settings()
    
    print("\n" + "="*60)
    if connected:
        print("✅ Redis is ready for Phase 2 caching!")
    else:
        print("⚠️  Redis not available, but in-memory cache will work")
    print("="*60)
    
    # Test the actual cache module
    print("\n4. Testing cache module...")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from grc.utils.ai_cache import get_redis_client, get_cache_stats
        
        client = get_redis_client()
        if client:
            print("   ✅ Cache module can connect to Redis")
        else:
            print("   ⚠️  Cache module using in-memory fallback")
        
        stats = get_cache_stats()
        print(f"   📊 Cache stats: {stats}")
    except Exception as e:
        print(f"   ⚠️  Cache module test error: {e}")



