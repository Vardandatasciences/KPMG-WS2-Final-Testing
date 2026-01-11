# Setup GRC/TPRM on Port 8080

## Quick Setup Guide

Since **tinyllama** is using port 80, we'll configure **GRC/TPRM on port 8080**.

---

## Step 1: Update grc-tprm Config File

```bash
# SSH into your server
ssh -i "C:\Users\puttu\Downloads\grc_tprm_pem_key.pem" ubuntu@13.203.184.82

# Backup existing config (if you want)
sudo cp /etc/nginx/sites-available/grc-tprm /etc/nginx/sites-available/grc-tprm.backup

# Edit the config file
sudo nano /etc/nginx/sites-available/grc-tprm
```

**Change these lines:**

**From:**
```nginx
listen 80;
listen [::]:80;
```

**To:**
```nginx
listen 8080;
listen [::]:8080;
```

**Save:** `Ctrl+X`, then `Y`, then `Enter`

---

## Step 2: Disable horilla (Optional - Since You Don't Need It)

```bash
# Remove horilla from enabled sites
sudo rm /etc/nginx/sites-enabled/horilla

# Or keep it disabled (it's not in use anyway)
# No action needed
```

---

## Step 3: Test Configuration

```bash
# Test nginx configuration
sudo nginx -t
```

**Expected output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

## Step 4: Enable grc-tprm Site

```bash
# Enable grc-tprm (create symlink)
sudo ln -s /etc/nginx/sites-available/grc-tprm /etc/nginx/sites-enabled/grc-tprm

# Verify it's enabled
ls -la /etc/nginx/sites-enabled/

# You should see:
# grc-tprm -> /etc/nginx/sites-available/grc-tprm
# tinyllama -> /etc/nginx/sites-available/tinyllama
```

---

## Step 5: Reload Nginx

```bash
# Reload nginx to apply changes
sudo systemctl reload nginx

# Check status
sudo systemctl status nginx
```

---

## Step 6: Verify It Works

```bash
# Test GRC frontend (port 8080)
curl http://localhost:8080/

# Test TPRM frontend (port 8080)
curl http://localhost:8080/tprm/

# Test API (should proxy to backend on port 8000)
curl http://localhost:8080/api/

# Test tinyllama still works (port 80)
curl http://localhost/
```

---

## Step 7: Open Firewall Port 8080 (If Needed)

```bash
# Check if firewall is active
sudo ufw status

# If firewall is active, allow port 8080
sudo ufw allow 8080/tcp

# Verify
sudo ufw status
```

---

## Final Configuration Summary

| Service | Port | URL | Status |
|---------|------|-----|--------|
| **tinyllama** | 80 | `http://13.203.184.82/` | ✅ Active |
| **GRC Frontend** | 8080 | `http://13.203.184.82:8080/` | ✅ Active |
| **TPRM Frontend** | 8080 | `http://13.203.184.82:8080/tprm/` | ✅ Active |
| **API Backend** | 8080 → 8000 | `http://13.203.184.82:8080/api/` | ✅ Active |
| **horilla** | - | - | ❌ Disabled (not needed) |

---

## Access URLs

- **GRC Frontend:** `http://13.203.184.82:8080/`
- **TPRM Frontend:** `http://13.203.184.82:8080/tprm/`
- **API:** `http://13.203.184.82:8080/api/`
- **tinyllama:** `http://13.203.184.82/` (port 80)

---

## Troubleshooting

### Issue: Port 8080 Already in Use

```bash
# Check what's using port 8080
sudo lsof -i :8080
# OR
sudo ss -tlnp | grep :8080

# If something else is using it, either:
# 1. Stop that service, OR
# 2. Use a different port (like 8081)
```

### Issue: Can't Access Port 8080 from Browser

```bash
# Check if port is open
sudo netstat -tlnp | grep :8080

# Check firewall
sudo ufw status

# Allow port 8080
sudo ufw allow 8080/tcp

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Issue: tinyllama Stopped Working

```bash
# Check if tinyllama is still enabled
ls -la /etc/nginx/sites-enabled/ | grep tinyllama

# Check nginx config
sudo nginx -t

# Check tinyllama config
cat /etc/nginx/sites-available/tinyllama

# Restart nginx if needed
sudo systemctl restart nginx
```

---

## Quick Commands Summary

```bash
# 1. Edit config
sudo nano /etc/nginx/sites-available/grc-tprm
# (Change listen 80 to listen 8080)

# 2. Test config
sudo nginx -t

# 3. Enable site
sudo ln -s /etc/nginx/sites-available/grc-tprm /etc/nginx/sites-enabled/grc-tprm

# 4. Reload nginx
sudo systemctl reload nginx

# 5. Test access
curl http://localhost:8080/
curl http://localhost:8080/tprm/

# 6. Open firewall (if needed)
sudo ufw allow 8080/tcp
```

---

## Environment Variable Update

Don't forget to update your TPRM environment variable:

**In `.env.production` file (before building TPRM):**
```
VUE_APP_TPRM_BASE_URL=http://13.203.184.82:8080/tprm
```

Then rebuild TPRM frontend:
```bash
cd grc_frontend/tprm_frontend
npm run build
```

---

## ✅ Done!

Your setup is complete:
- ✅ tinyllama on port 80 (unchanged)
- ✅ GRC/TPRM on port 8080 (new)
- ✅ horilla disabled (not needed)
- ✅ No conflicts!

