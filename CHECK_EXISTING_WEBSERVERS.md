# Check Existing Web Servers Before Setup

## ⚠️ IMPORTANT: Check What's Already Running

Before setting up nginx for GRC/TPRM, let's check what web servers are already running on your system.

### Step 1: Check if Nginx is Already Running

```bash
# Check if nginx is installed and running
sudo systemctl status nginx

# Check what nginx is serving
sudo nginx -T 2>/dev/null | grep -E "server_name|root|listen" | head -20

# List all nginx site configurations
ls -la /etc/nginx/sites-available/
ls -la /etc/nginx/sites-enabled/
```

### Step 2: Check if Apache is Running

```bash
# Check if Apache is installed and running
sudo systemctl status apache2

# Or if it's called httpd (on some systems)
sudo systemctl status httpd

# Check Apache configurations
ls -la /etc/apache2/sites-available/ 2>/dev/null || echo "Apache not installed"
```

### Step 3: Check What Ports Are in Use

```bash
# Check what's listening on port 80 (HTTP)
sudo netstat -tlnp | grep :80
# OR
sudo ss -tlnp | grep :80
# OR
sudo lsof -i :80

# Check what's listening on port 443 (HTTPS)
sudo netstat -tlnp | grep :443
# OR
sudo ss -tlnp | grep :443
```

### Step 4: Check Your Applications in /home/ubuntu/

Your applications like **CashflowApp**, **horilla**, **Policy_Extractor**, etc. are **SAFE** because:

1. **They're in `/home/ubuntu/`** - Nginx will NOT serve files from your home directory
2. **Nginx only serves what you configure** - Our config only serves from `/var/www/html/grc` and `/var/www/html/tprm`
3. **Other apps might be using different ports** - If they're web apps, they probably run on ports 3000, 5000, 8000, etc.

### Step 5: Check if Your Other Apps Use Web Servers

```bash
# Check if horilla has nginx config
ls -la ~/horilla/*.conf 2>/dev/null | grep -i nginx
ls -la ~/horilla/*.conf 2>/dev/null | grep -i apache

# Check if CashflowApp has web server config
ls -la ~/CashflowApp/*.conf 2>/dev/null

# Check if any apps are running web servers
ps aux | grep -E "nginx|apache|httpd|gunicorn|uwsgi" | grep -v grep
```

---

## 🎯 What Will Happen

### Scenario 1: Nginx is NOT Installed (Clean Setup)
✅ **SAFE** - You'll install nginx fresh, only GRC/TPRM will be configured

### Scenario 2: Nginx IS Installed But Not Configured
✅ **SAFE** - Default nginx config usually serves from `/var/www/html/` or `/usr/share/nginx/html/`
- Our config will **replace** the default config
- Your other apps in `/home/ubuntu/` are **NOT affected**

### Scenario 3: Nginx IS Installed AND Already Serving Something
⚠️ **NEEDS ATTENTION** - We need to check:
- What domain/IP is it serving?
- What ports are in use?
- Can we use the same nginx with multiple configs?

**Solution:** We can configure nginx to serve multiple sites using different:
- **Ports** (e.g., 80 for GRC/TPRM, 8080 for horilla)
- **Server names** (e.g., domain1.com for GRC, domain2.com for horilla)
- **IP addresses** (if you have multiple IPs)

### Scenario 4: Apache is Running
⚠️ **CONFLICT** - Apache and Nginx both try to use port 80
- Option A: **Stop Apache** (if not needed)
- Option B: **Run Apache on different port** (e.g., 8080)
- Option C: **Use Nginx as reverse proxy** for Apache

---

## ✅ Safe Setup Strategy

### Option 1: Use Different Port (Safest)

If you have other web servers running, configure GRC/TPRM on a different port:

**Edit `nginx-grc-tprm.conf`:**
```nginx
server {
    listen 8080;  # Use port 8080 instead of 80
    listen [::]:8080;
    # ... rest of config
}
```

Then access: `http://13.203.184.82:8080/` and `http://13.203.184.82:8080/tprm/`

### Option 2: Check Existing Config First

```bash
# Before installing/configuring, check existing nginx configs
cat /etc/nginx/sites-available/default 2>/dev/null
cat /etc/nginx/sites-enabled/* 2>/dev/null

# Backup existing configs
sudo cp -r /etc/nginx/sites-available /etc/nginx/sites-available.backup
sudo cp -r /etc/nginx/sites-enabled /etc/nginx/sites-enabled.backup
```

### Option 3: Multiple Server Blocks (Recommended if Other Apps Need Web Server)

If other apps need nginx/Apache, we can configure multiple server blocks:

```nginx
# Server block 1: GRC/TPRM
server {
    listen 80;
    server_name grc-tprm.example.com;  # Or use IP
    # ... GRC/TPRM config
}

# Server block 2: Horilla (if needed)
server {
    listen 8080;  # Different port
    server_name horilla.example.com;
    root /home/ubuntu/horilla;
    # ... horilla config
}
```

---

## 🔍 Quick Diagnostic Commands

Run these commands to get a complete picture:

```bash
# 1. Check all web servers
echo "=== Nginx Status ==="
sudo systemctl status nginx --no-pager -l 2>&1 | head -10

echo "=== Apache Status ==="
sudo systemctl status apache2 --no-pager -l 2>&1 | head -10

# 2. Check what's using port 80
echo "=== Port 80 Usage ==="
sudo lsof -i :80 2>/dev/null || sudo ss -tlnp | grep :80

# 3. Check existing nginx configs
echo "=== Nginx Configs ==="
sudo ls -la /etc/nginx/sites-available/ 2>/dev/null
sudo ls -la /etc/nginx/sites-enabled/ 2>/dev/null

# 4. Check if nginx is serving anything
echo "=== Nginx Active Sites ==="
sudo nginx -T 2>/dev/null | grep -A 5 "server {" | head -30

# 5. Check running web processes
echo "=== Web Server Processes ==="
ps aux | grep -E "nginx|apache|httpd" | grep -v grep
```

---

## 📋 Recommended Action Plan

1. **Run diagnostic commands above** to see what's running
2. **If nginx is not installed** → Install and configure (SAFE)
3. **If nginx is installed but empty** → Configure GRC/TPRM (SAFE)
4. **If nginx is serving other apps** → We'll add GRC/TPRM as additional server block (SAFE)
5. **If Apache is running** → We'll either:
   - Stop Apache (if not needed)
   - Configure Nginx on different port
   - Configure Nginx as reverse proxy

---

## ✅ Guarantee: Your Home Directory Files Are SAFE

**Your files in `/home/ubuntu/` are 100% SAFE** because:
- Nginx only serves from `/var/www/html/` (system directory)
- Your apps (CashflowApp, horilla, etc.) are in `/home/ubuntu/` (user directory)
- Nginx cannot access files outside configured root directories
- Even if misconfigured, nginx cannot read files outside its document root

**No web server configuration will:**
- ❌ Delete your files
- ❌ Modify your files
- ❌ Serve your files (unless explicitly configured)
- ❌ Affect your Python scripts
- ❌ Affect your databases

**The ONLY risk** is if:
- Port 80 is already in use → Solution: Use different port
- Existing web server config conflicts → Solution: Review and adjust configs

---

## 🚀 Quick Setup (After Verification)

Once you've verified what's running, proceed with:

```bash
# 1. Install nginx (if not installed)
sudo apt update
sudo apt install nginx -y

# 2. Check existing config (backup if needed)
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# 3. Create GRC/TPRM config
sudo nano /etc/nginx/sites-available/grc-tprm
# (Paste nginx-grc-tprm.conf contents)

# 4. Test config
sudo nginx -t

# 5. If test passes, enable site
sudo ln -s /etc/nginx/sites-available/grc-tprm /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Only if you want to remove default

# 6. Reload nginx
sudo systemctl reload nginx
```

---

## 💡 Pro Tip: Multiple Sites on Same Server

If you need to serve multiple applications, you can have multiple nginx configurations:

```bash
# Each app gets its own config file
/etc/nginx/sites-available/grc-tprm     → Port 80 (GRC/TPRM)
/etc/nginx/sites-available/horilla      → Port 8080 (Horilla)
/etc/nginx/sites-available/cashflow     → Port 8081 (CashflowApp)
```

All can run simultaneously without conflicts!

