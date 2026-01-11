# Multi-Site Nginx Setup Guide
## Configuring GRC/TPRM with Existing Sites (horilla, tinyllama)

Based on your diagnostic output, you have:
- ✅ **horilla** - Currently ENABLED
- ✅ **tinyllama** - Currently ENABLED  
- ⚠️ **grc-tprm** - Available but NOT ENABLED

## Step 1: Check Existing Configurations

First, let's see what the existing sites are configured for:

```bash
# Check horilla config (currently active)
cat /etc/nginx/sites-available/horilla

# Check tinyllama config (currently active)
cat /etc/nginx/sites-available/tinyllama

# Check existing grc-tprm config (not enabled)
cat /etc/nginx/sites-available/grc-tprm

# See the full nginx configuration to understand routing
sudo nginx -T | grep -A 20 "server {" | head -80
```

## Step 2: Understanding How Sites Work Together

Nginx uses **server blocks** to route requests. Multiple server blocks can coexist on port 80 if they:
1. Use different `server_name` (domains)
2. Use different paths (location blocks)
3. Use different ports

**Most likely scenario:**
- `horilla` might be on path `/horilla` or a specific domain
- `tinyllama` might be on path `/tinyllama` or a specific domain
- `grc-tprm` should handle root `/` and `/tprm`

## Step 3: Update GRC/TPRM Configuration

We need to make sure GRC/TPRM config **doesn't conflict** with existing sites. 

### Option A: If horilla/tinyllama use specific paths

If they use paths like `/horilla` and `/tinyllama`, update our config to exclude those paths:

```bash
# Backup existing grc-tprm config first
sudo cp /etc/nginx/sites-available/grc-tprm /etc/nginx/sites-available/grc-tprm.backup

# Edit the config
sudo nano /etc/nginx/sites-available/grc-tprm
```

**Update the GRC location block to exclude horilla and tinyllama paths:**

```nginx
# GRC Main location - SPA routing (but NOT horilla or tinyllama)
location / {
    # Exclude other app paths
    if ($uri ~ ^/(horilla|tinyllama)) {
        return 404;
    }
    
    root /var/www/html/grc;
    index index.html;
    try_files $uri $uri/ /index.html;
}
```

**OR better approach - make location blocks more specific:**

```nginx
# GRC Main location - SPA routing (exclude other app paths)
location ~ ^(?!/(horilla|tinyllama|tprm)).*$ {
    root /var/www/html/grc;
    index index.html;
    try_files $uri $uri/ /index.html;
}
```

### Option B: If horilla/tinyllama use different server_name

If they use different domains/server names, make sure our config uses a specific server_name:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name 13.203.184.82 your-domain.com;  # Your specific domain/IP
    
    # ... rest of config
}
```

### Option C: Path-based routing (Recommended)

If you want all apps on the same server, configure them with specific paths:

**Current setup:**
- Root `/` → GRC Frontend
- `/tprm` → TPRM Frontend
- `/horilla` → Horilla (if it uses this path)
- `/tinyllama` → TinyLLama (if it uses this path)

## Step 4: Test and Enable

```bash
# 1. Test the configuration syntax
sudo nginx -t

# 2. If test passes, enable grc-tprm
sudo ln -s /etc/nginx/sites-available/grc-tprm /etc/nginx/sites-enabled/grc-tprm

# 3. Verify all enabled sites
ls -la /etc/nginx/sites-enabled/

# 4. Reload nginx
sudo systemctl reload nginx

# 5. Check status
sudo systemctl status nginx

# 6. Test the sites
curl http://localhost/
curl http://localhost/tprm/
curl http://localhost/horilla/  # If horilla is on /horilla path
```

## Step 5: Verify No Conflicts

```bash
# Check nginx error logs for any conflicts
sudo tail -f /var/log/nginx/error.log

# In another terminal, test access
curl -I http://localhost/
curl -I http://localhost/tprm/
curl -I http://localhost/horilla/
```

## Troubleshooting

### Issue: 404 for horilla/tinyllama after enabling grc-tprm

**Solution:** The GRC root location `/` is catching all requests. Update config to exclude those paths:

```nginx
# Before the GRC location / block, add:
location /horilla {
    # Let horilla config handle this (or proxy to horilla)
    proxy_pass http://localhost:PORT;  # Replace PORT with horilla's port
}

location /tinyllama {
    # Let tinyllama config handle this
    proxy_pass http://localhost:PORT;  # Replace PORT with tinyllama's port
}
```

### Issue: Server name conflicts

**Solution:** Make sure each server block has a unique `server_name` or use `default_server` flag:

```nginx
# In grc-tprm config, make it default
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    # ... rest of config
}
```

### Issue: Port already in use

**Solution:** If other apps need port 80, use different ports:

```nginx
# GRC/TPRM on port 80 (default)
server {
    listen 80;
    # ... config
}

# Horilla on port 8080
server {
    listen 8080;
    # ... horilla config
}
```

## Quick Fix Commands

If you want to quickly check and fix:

```bash
# 1. View current active configs
sudo nginx -T 2>/dev/null | grep -E "server_name|listen|location" | head -40

# 2. Check what path horilla uses
grep -r "location" /etc/nginx/sites-available/horilla

# 3. Check what path tinyllama uses  
grep -r "location" /etc/nginx/sites-available/tinyllama

# 4. Update grc-tprm config based on findings
sudo nano /etc/nginx/sites-available/grc-tprm

# 5. Test and reload
sudo nginx -t && sudo systemctl reload nginx
```

## Recommended Configuration Structure

Based on what you likely have, here's the recommended structure:

```
/etc/nginx/sites-available/
├── horilla        → Path /horilla or different port
├── tinyllama      → Path /tinyllama or different port
└── grc-tprm       → Root / and /tprm (default server)

/etc/nginx/sites-enabled/
├── horilla        → Enabled
├── tinyllama      → Enabled
└── grc-tprm       → Will be enabled
```

All can work together! 🎯

