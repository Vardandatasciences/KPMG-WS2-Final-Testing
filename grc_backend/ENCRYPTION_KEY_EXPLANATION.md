# GRC Encryption Key - How It Works

## Key Lookup Order (Priority)

The code checks for the encryption key in this order:

1. **First**: `settings.GRC_ENCRYPTION_KEY` (Django settings file)
2. **Second**: `os.environ.get('GRC_ENCRYPTION_KEY')` (Environment variable)
3. **Last (FALLBACK)**: **Auto-generates from `SECRET_KEY`** ⚠️

## The Problem

If `GRC_ENCRYPTION_KEY` is **NOT found** in settings or environment:
- The code **AUTO-GENERATES** a new key from `SECRET_KEY`
- This means **EVERY TIME** the server starts, it might use a **DIFFERENT KEY**
- **Result**: Data encrypted with one key **CANNOT** be decrypted with a different key!

## How to Verify Your Key is Being Used

### Option 1: Check Environment Variable (Easiest)

```bash
# Windows PowerShell
echo $env:GRC_ENCRYPTION_KEY

# Windows CMD
echo %GRC_ENCRYPTION_KEY%

# Linux/Mac
echo $GRC_ENCRYPTION_KEY
```

If this shows nothing or is empty → **Your key is NOT being loaded!**

### Option 2: Check Django Settings

Look in your `backend/settings.py` or wherever your Django settings are:

```python
# Should have this:
GRC_ENCRYPTION_KEY = os.environ.get('GRC_ENCRYPTION_KEY', '')
# OR
GRC_ENCRYPTION_KEY = 'your-actual-key-here'
```

### Option 3: Check Server Logs

When the server starts, if you see this warning:
```
WARNING: No GRC_ENCRYPTION_KEY found. Generating from SECRET_KEY (NOT RECOMMENDED for production)
```

This means **your key is NOT being loaded** and it's auto-generating!

## Solution: Set the Key Correctly

### Step 1: Generate a Key (if you don't have one)

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Copy this output
```

### Step 2: Set in Environment

**Windows (.env file or system environment):**
```
GRC_ENCRYPTION_KEY=your-generated-key-here
```

**Or in PowerShell:**
```powershell
$env:GRC_ENCRYPTION_KEY = "your-generated-key-here"
```

**Linux/Mac (.env file):**
```bash
export GRC_ENCRYPTION_KEY="your-generated-key-here"
```

### Step 3: Verify It's Loaded

Restart your Django server and check the logs - you should **NOT** see the warning about auto-generating from SECRET_KEY.

## Important Notes

1. **Same Key for GRC and TPRM**: If TPRM decryption works but GRC doesn't, they might be using different keys
2. **Key Must Match**: The key used to decrypt must be the **EXACT SAME** key used to encrypt
3. **No Auto-Generation in Production**: Always set `GRC_ENCRYPTION_KEY` explicitly in production

## Quick Test

Add this to your Django view temporarily to see what key is being used:

```python
from grc.utils.data_encryption import get_encryption_service
import os
from django.conf import settings

def check_key(request):
    service = get_encryption_service()
    env_key = os.environ.get('GRC_ENCRYPTION_KEY', 'NOT FOUND')
    settings_key = getattr(settings, 'GRC_ENCRYPTION_KEY', 'NOT FOUND')
    actual_key = service.encryption_key.decode() if isinstance(service.encryption_key, bytes) else service.encryption_key
    
    return Response({
        'env_key': env_key[:20] + '...' if env_key != 'NOT FOUND' else 'NOT FOUND',
        'settings_key': settings_key[:20] + '...' if settings_key != 'NOT FOUND' else 'NOT FOUND',
        'actual_key_used': actual_key[:20] + '...',
        'key_source': 'ENV' if env_key != 'NOT FOUND' else ('SETTINGS' if settings_key != 'NOT FOUND' else 'AUTO-GENERATED')
    })
```


