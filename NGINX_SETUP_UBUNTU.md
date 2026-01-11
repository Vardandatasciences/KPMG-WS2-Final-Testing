# Nginx Setup for GRC & TPRM on Ubuntu

## ⚠️ IMPORTANT: Check Existing Web Servers First!

**Before setting up nginx, check if other web servers are running that might conflict:**

### Quick Check (Run on Your Ubuntu Server)

```bash
# Check if nginx is running
sudo systemctl status nginx

# Check if Apache is running
sudo systemctl status apache2

# Check what's using port 80
sudo lsof -i :80 || sudo ss -tlnp | grep :80

# Check existing nginx configs
ls -la /etc/nginx/sites-available/ 2>/dev/null
ls -la /etc/nginx/sites-enabled/ 2>/dev/null
```

**OR run the diagnostic script:**
```bash
# Make it executable
chmod +x check-webservers.sh

# Run it
./check-webservers.sh
```

**✅ Your files in `/home/ubuntu/` (CashflowApp, horilla, Policy_Extractor, etc.) are 100% SAFE**
- Nginx only serves from `/var/www/html/` (system directory)
- Your apps are in `/home/ubuntu/` (user directory) - completely separate
- Nginx cannot access or affect files outside configured directories

**See `CHECK_EXISTING_WEBSERVERS.md` for detailed information about handling existing web servers.**

---

## Quick Setup Guide

### 1. Copy Nginx Configuration File

```bash
# SSH into your Ubuntu server
ssh -i "C:\Users\puttu\Downloads\grc_tprm_pem_key.pem" ubuntu@13.203.184.82

# Backup existing default config (if exists)
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# Copy the new config file
# (Upload nginx-grc-tprm.conf to server first, or create it on server)
sudo nano /etc/nginx/sites-available/grc-tprm
```

**Paste the contents of `nginx-grc-tprm.conf` file, then save (Ctrl+X, Y, Enter)**

### 2. Enable the Site

```bash
# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Create symlink to enable the new site
sudo ln -s /etc/nginx/sites-available/grc-tprm /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t
```

**Expected output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 3. Reload Nginx

```bash
# If test passes, reload nginx
sudo systemctl reload nginx

# Or restart nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

### 4. Update Server Name (Optional)

If you have a domain name, edit the config file:

```bash
sudo nano /etc/nginx/sites-available/grc-tprm
```

**Change line 9:**
```nginx
server_name your-domain.com www.your-domain.com;  # Replace with your domain
```

**Or keep IP address:**
```nginx
server_name 13.203.184.82 _;  # IP or any domain
```

### 5. Verify Deployment

**Check if nginx is serving files correctly:**
```bash
# Check GRC files
ls -la /var/www/html/grc/ | head -10

# Check TPRM files
ls -la /var/www/html/tprm/ | head -10

# Check nginx is running
sudo systemctl status nginx

# Check nginx error logs (if issues)
sudo tail -f /var/log/nginx/error.log

# Check nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### 6. Test in Browser

- **GRC Frontend:** `http://13.203.184.82/`
- **TPRM Frontend:** `http://13.203.184.82/tprm/`
- **API:** `http://13.203.184.82/api/`

---

## Environment Variable Setup

### For TPRM Frontend Build

Before building TPRM frontend, create or update `.env.production` file:

```bash
# On Windows (before building)
cd C:\Users\puttu\Videos\GRC_TPRM-1\grc_frontend\tprm_frontend

# Create .env.production file
notepad .env.production
```

**Add this line:**
```
VUE_APP_TPRM_BASE_URL=http://13.203.184.82/tprm
```

**Or if you have a domain:**
```
VUE_APP_TPRM_BASE_URL=http://your-domain.com/tprm
```

**Then rebuild TPRM:**
```powershell
npm run build
```

---

## Troubleshooting

### Issue: 404 Not Found for TPRM
**Solution:** 
1. Check files exist: `ls -la /var/www/html/tprm/`
2. Check permissions: `sudo chown -R www-data:www-data /var/www/html/tprm`
3. Check nginx config: `sudo nginx -t`
4. Check error logs: `sudo tail -f /var/log/nginx/error.log`

### Issue: Static Assets (JS/CSS) Not Loading
**Solution:**
1. Verify files are in correct location: `/var/www/html/tprm/assets/`
2. Check browser console for 404 errors
3. Verify TPRM was built with correct base path: `base: '/tprm/'` in vite.config.js

### Issue: API Calls Failing
**Solution:**
1. Verify backend is running: `docker ps | grep grc_tprm_backend`
2. Test backend directly: `curl http://localhost:8000/api/`
3. Check nginx proxy_pass config points to correct backend

### Issue: SPA Routing Not Working (404 on Refresh)
**Solution:**
- For GRC: Make sure `try_files $uri $uri/ /index.html;` is in location /
- For TPRM: Make sure `try_files $uri $uri/ /tprm/index.html;` is in location /tprm/

---

## Configuration Summary

**What this nginx config does:**

1. ✅ **Serves GRC** from `/` (root) → `/var/www/html/grc/`
2. ✅ **Serves TPRM** from `/tprm` → `/var/www/html/tprm/`
3. ✅ **Proxies API** from `/api/` → `http://localhost:8000/api/`
4. ✅ **SPA Routing** - Both apps support client-side routing
5. ✅ **Static Assets Caching** - JS/CSS/images cached for 1 year
6. ✅ **HTML No-Cache** - HTML files never cached (always fresh)
7. ✅ **Security Headers** - XSS protection, content-type sniffing protection
8. ✅ **Gzip Compression** - Reduces file sizes

**Location Priority (order matters in nginx):**

1. `/api/` - API proxy (highest priority)
2. `/tprm/assets/` - TPRM static assets
3. `/tprm/*.js|css|png|...` - TPRM static files
4. `/tprm/` - TPRM routes (SPA routing)
5. `/assets/` - GRC static assets
6. `/*.js|css|png|...` - GRC static files
7. `/` - GRC routes (SPA routing, lowest priority)

---

## File Structure Expected

```
/var/www/html/
├── grc/                    # GRC frontend dist files
│   ├── index.html
│   ├── assets/
│   │   ├── app.js
│   │   └── app.css
│   └── ...
└── tprm/                   # TPRM frontend dist files
    ├── index.html
    ├── assets/
    │   ├── vendor.js
    │   └── vendor.css
    └── ...
```

---

## Quick Deploy Commands (Summary)

```bash
# 1. SSH into server
ssh -i "C:\Users\puttu\Downloads\grc_tprm_pem_key.pem" ubuntu@13.203.184.82

# 2. Copy config (or create it)
sudo nano /etc/nginx/sites-available/grc-tprm
# (Paste nginx-grc-tprm.conf contents)

# 3. Enable site
sudo ln -s /etc/nginx/sites-available/grc-tprm /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default

# 4. Test and reload
sudo nginx -t
sudo systemctl reload nginx

# 5. Verify
curl http://localhost/
curl http://localhost/tprm/
```

