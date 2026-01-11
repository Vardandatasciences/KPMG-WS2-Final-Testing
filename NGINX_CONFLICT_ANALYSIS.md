# ⚠️ Nginx Configuration Conflict Analysis

## Critical Issues Found

### Issue 1: horilla and tinyllama CONFLICT ❌

**Problem:**
- **horilla**: `server_name 13.205.15.232` + location `/`
- **tinyllama**: `server_name 13.205.15.232` + location `/`

Both use the **SAME server_name** and **SAME root location `/`**. This means:
- ❌ **Only ONE will work** (whichever nginx matches first)
- ❌ The other will be **completely ignored**
- ❌ You cannot access both horilla and tinyllama

### Issue 2: grc-tprm Uses Different IP ⚠️

**Problem:**
- **horilla/tinyllama**: `server_name 13.205.15.232`
- **grc-tprm**: `server_name 13.203.184.82`

Different IPs mean:
- If you access via `13.203.184.82` → Only grc-tprm will work
- If you access via `13.205.15.232` → Only horilla OR tinyllama will work (they conflict!)

---

## What You Need to Fix

### Step 1: Determine Your Server's Actual IP

```bash
# Check what IPs your server has
ip addr show | grep "inet " | grep -v "127.0.0.1"

# Or check public IP
curl ifconfig.me
```

**Question:** What IP address should be used to access your server?
- Is it `13.203.184.82`? (for GRC/TPRM)
- Is it `13.205.15.232`? (for horilla/tinyllama)
- Or do you have multiple IPs?

### Step 2: Fix Based on Your Setup

---

## Solution Options

### Option A: All Apps on Same IP with Different Paths (RECOMMENDED)

If you want all apps on one IP (e.g., `13.203.184.82`):

1. **Update horilla** to use path `/horilla`:
```bash
sudo nano /etc/nginx/sites-available/horilla
```

```nginx
server {
    listen 80;
    server_name 13.203.184.82;  # Change to your IP
    
    location /horilla {
        rewrite ^/horilla/?(.*)$ /$1 break;
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/horilla/horilla.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /horilla/static/ {
        alias /var/www/horilla/staticfiles/;
    }
    
    location /horilla/media/ {
        alias /var/www/horilla/media/;
    }
}
```

2. **Update tinyllama** to use path `/tinyllama`:
```bash
sudo nano /etc/nginx/sites-available/tinyllama
```

```nginx
server {
    listen 80;
    server_name 13.203.184.82;  # Change to your IP
    
    location /tinyllama {
        rewrite ^/tinyllama/?(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. **Update grc-tprm** to use the same IP:
```bash
sudo nano /etc/nginx/sites-available/grc-tprm
```

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name 13.203.184.82;  # Same IP as others
    
    # ... rest of config stays the same
    # GRC on /, TPRM on /tprm
}
```

**Result:**
- `http://13.203.184.82/` → GRC
- `http://13.203.184.82/tprm/` → TPRM
- `http://13.203.184.82/horilla/` → Horilla
- `http://13.203.184.82/tinyllama/` → TinyLLama

---

### Option B: Use Different IPs (Current Setup)

If you want to keep different IPs:

1. **Keep horilla on `13.205.15.232`** (but fix conflict with tinyllama)
2. **Keep grc-tprm on `13.203.184.82`**
3. **Fix horilla/tinyllama conflict** by using different paths or disabling one

**Problem:** horilla and tinyllama still conflict on `13.205.15.232`. You must:
- Use different paths (Option A above)
- Use different ports (see Option C)
- Disable one of them

---

### Option C: Use Different Ports

If you want to keep current setup and just make GRC/TPRM work:

1. **Keep horilla/tinyllama on port 80** (they conflict, but one works)
2. **Put grc-tprm on port 8080**:

```bash
sudo nano /etc/nginx/sites-available/grc-tprm
```

Change:
```nginx
server {
    listen 8080;  # Different port
    listen [::]:8080;
    server_name 13.203.184.82;
    # ... rest of config
}
```

**Result:**
- `http://13.205.15.232/` → horilla OR tinyllama (one works)
- `http://13.203.184.82:8080/` → GRC
- `http://13.203.184.82:8080/tprm/` → TPRM

---

## Recommended Solution: Option A (Path-Based Routing)

**Why?**
- ✅ All apps accessible on same IP
- ✅ Clean URLs
- ✅ No port conflicts
- ✅ Easy to manage

**Quick Fix Script:**

```bash
# 1. Update horilla config
sudo cp /etc/nginx/sites-available/horilla /etc/nginx/sites-available/horilla.backup
sudo nano /etc/nginx/sites-available/horilla
# (Update as shown in Option A above)

# 2. Update tinyllama config
sudo cp /etc/nginx/sites-available/tinyllama /etc/nginx/sites-available/tinyllama.backup
sudo nano /etc/nginx/sites-available/tinyllama
# (Update as shown in Option A above)

# 3. Update grc-tprm server_name (if needed)
sudo nano /etc/nginx/sites-available/grc-tprm
# Change server_name to match your IP

# 4. Test all configs
sudo nginx -t

# 5. Reload nginx
sudo systemctl reload nginx
```

---

## Current Status Summary

| Config | Server Name | Location | Status |
|--------|-------------|----------|--------|
| **horilla** | 13.205.15.232 | `/` | ⚠️ Conflicts with tinyllama |
| **tinyllama** | 13.205.15.232 | `/` | ⚠️ Conflicts with horilla |
| **grc-tprm** | 13.203.184.82 | `/` and `/tprm/` | ✅ No conflict (different IP) |

---

## What Happens If You Enable grc-tprm Now?

**If your server IP is `13.203.184.82`:**
- ✅ grc-tprm will work fine
- ❌ horilla won't work (wrong server_name)
- ❌ tinyllama won't work (wrong server_name)

**If your server IP is `13.205.15.232`:**
- ❌ grc-tprm won't work (wrong server_name)
- ⚠️ horilla OR tinyllama works (but they conflict!)

**If you have both IPs:**
- Access via `13.203.184.82` → grc-tprm works
- Access via `13.205.15.232` → horilla OR tinyllama works (they conflict!)

---

## Action Required

1. **Determine your server's actual IP**
2. **Choose a solution** (Option A recommended)
3. **Fix the conflicts** before enabling grc-tprm
4. **Test everything** with `sudo nginx -t` and `curl`

Would you like me to create updated config files for Option A (path-based routing)?

