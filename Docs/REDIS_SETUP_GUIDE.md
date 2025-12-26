# Redis Setup Guide for Phase 2 Caching

## 🎯 Overview

Redis is required for Phase 2 caching to work. This guide will help you install and configure Redis on Windows.

---

## 📋 Option 1: Redis for Windows (Recommended for Development)

### Step 1: Download Redis for Windows

**Option A: Using WSL (Windows Subsystem for Linux) - Recommended**
```bash
# Install WSL if not already installed
wsl --install

# In WSL, install Redis
sudo apt update
sudo apt install redis-server

# Start Redis
sudo service redis-server start

# Test Redis
redis-cli ping
# Should return: PONG
```

**Option B: Using Memurai (Redis-compatible for Windows)**
1. Download from: https://www.memurai.com/get-memurai
2. Install Memurai (it's Redis-compatible)
3. Start Memurai service (starts automatically)

**Option C: Using Docker (if you have Docker)**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

---

## 📋 Option 2: Quick Setup with Python Redis Package

If you just want to test, you can use a simple in-memory cache fallback, but for production, you need actual Redis.

### Step 1: Install Redis Python Package

```bash
pip install redis
```

### Step 2: Verify Installation

```python
python -c "import redis; print('Redis package installed')"
```

---

## ⚙️ Configuration

### Step 1: Update Django Settings

Check your `settings.py` for Redis configuration:

```python
# In tprm_backend/config/settings.py or your settings file

# Redis Configuration for AI Caching
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/2')
```

### Step 2: Set Environment Variable (Optional)

Create or update `.env` file:

```bash
REDIS_URL=redis://localhost:6379/2
```

---

## 🧪 Testing Redis Connection

### Test 1: Quick Python Test

```python
import redis

try:
    client = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)
    client.ping()
    print("✅ Redis is connected!")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
```

### Test 2: Using Phase 2 Test Script

```bash
python test_phase2.py
```

Look for:
```
✅ Redis connected: X cache keys
```

### Test 3: Using Django Shell

```bash
python manage.py shell
```

```python
from grc.utils.ai_cache import get_redis_client, get_cache_stats

client = get_redis_client()
if client:
    print("✅ Redis connected!")
    stats = get_cache_stats()
    print(stats)
else:
    print("❌ Redis not available")
```

---

## 🚀 Starting Redis

### WSL (Windows Subsystem for Linux)

```bash
# Start Redis
sudo service redis-server start

# Stop Redis
sudo service redis-server stop

# Check status
sudo service redis-server status
```

### Memurai (Windows Service)

- Memurai runs as a Windows service
- It should start automatically
- Check Windows Services: `services.msc` → Look for "Memurai"

### Docker

```bash
# Start Redis container
docker start redis

# Stop Redis container
docker stop redis

# Check if running
docker ps | grep redis
```

---

## 🔧 Troubleshooting

### Issue: "Connection refused" or "Error 10061"

**Solution:**
1. Check if Redis is running:
   ```bash
   # WSL
   sudo service redis-server status
   
   # Docker
   docker ps | grep redis
   ```

2. Check Redis port (default: 6379):
   ```bash
   # Test connection
   redis-cli ping
   # or
   telnet localhost 6379
   ```

3. Start Redis if not running:
   ```bash
   # WSL
   sudo service redis-server start
   
   # Docker
   docker start redis
   ```

### Issue: "Redis package not found"

**Solution:**
```bash
pip install redis
```

### Issue: "Permission denied"

**Solution (WSL):**
```bash
sudo service redis-server start
```

### Issue: Redis not starting automatically

**Solution:**
- **WSL**: Add to startup script or use systemd
- **Memurai**: Check Windows Services, set to "Automatic"
- **Docker**: Use `--restart=always` flag

---

## 📊 Verify Redis is Working with Phase 2

### Test Cache Operations

```python
from grc.utils.ai_cache import (
    get_redis_client,
    set_cached_response,
    get_cached_response,
    generate_cache_key
)

# Test cache write
client = get_redis_client()
if client:
    key = generate_cache_key("test-model", "test-prompt")
    set_cached_response(key, {"test": "data"}, ttl=60)
    
    # Test cache read
    cached = get_cached_response(key)
    if cached:
        print("✅ Cache is working!")
    else:
        print("❌ Cache read failed")
else:
    print("❌ Redis not available")
```

---

## 🎯 Recommended Setup for Production

### For EC2/Server Deployment:

1. **Install Redis on Linux:**
   ```bash
   sudo apt update
   sudo apt install redis-server
   sudo systemctl enable redis-server
   sudo systemctl start redis-server
   ```

2. **Configure Redis:**
   ```bash
   sudo nano /etc/redis/redis.conf
   # Set: bind 127.0.0.1 (or your server IP)
   # Set: maxmemory 256mb
   # Set: maxmemory-policy allkeys-lru
   ```

3. **Update Django Settings:**
   ```python
   REDIS_URL = os.environ.get('REDIS_URL', 'redis://your-server-ip:6379/2')
   ```

---

## ✅ Quick Start Checklist

- [ ] Install Redis (WSL, Memurai, or Docker)
- [ ] Install Python redis package: `pip install redis`
- [ ] Start Redis service
- [ ] Test connection: `redis-cli ping` (should return PONG)
- [ ] Update `.env` with `REDIS_URL` if needed
- [ ] Run `python test_phase2.py` to verify
- [ ] Check logs for "✅ Redis connected"

---

## 💡 Alternative: Use In-Memory Cache (Development Only)

If you can't install Redis right now, Phase 2 will still work but caching will be disabled. The code gracefully handles Redis unavailability:

- ✅ Document preprocessing: **Works**
- ✅ Few-shot prompts: **Works**
- ⚠️ Caching: **Disabled** (but no errors)

You can add Redis later to enable caching.

---

## 📚 Additional Resources

- Redis Windows: https://github.com/microsoftarchive/redis/releases
- Memurai: https://www.memurai.com/
- Redis Documentation: https://redis.io/docs/
- WSL Installation: https://learn.microsoft.com/en-us/windows/wsl/install

---

**Last Updated**: [Current Date]
**Status**: Ready for Setup



