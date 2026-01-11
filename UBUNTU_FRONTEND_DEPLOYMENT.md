# Ubuntu Frontend Deployment Guide

## Overview
This guide will help you deploy both GRC and TPRM frontends to your new Ubuntu instance.

**Key Differences from Amazon Linux:**
- Default user: `ubuntu` (instead of `ec2-user`)
- Web server user: `www-data` (instead of `nginx`)
- Same directory structure: `/var/www/html/grc` and `/var/www/html/tprm`

---

## Prerequisites

### 1. Install nginx (if not already installed)
```bash
# SSH into your Ubuntu instance
ssh -i "C:\Users\puttu\Downloads\grc_tprm_pem_key.pem" ubuntu@13.203.184.82

# Update package list
sudo apt update

# Install nginx
sudo apt install nginx -y

# Start and enable nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

### 2. Create directories on Ubuntu server
```bash
# Create directories for both frontends
sudo mkdir -p /var/www/html/grc
sudo mkdir -p /var/www/html/tprm

# Set initial permissions (ubuntu user can write)
sudo chown -R ubuntu:ubuntu /var/www/html/grc
sudo chmod -R 775 /var/www/html/grc
sudo chown -R ubuntu:ubuntu /var/www/html/tprm
sudo chmod -R 775 /var/www/html/tprm
```

---

## Build Frontends Locally (Windows)

### Option 1: Build on Windows Machine

#### 1. Navigate to GRC Frontend Directory
```powershell
cd C:\Users\puttu\Videos\GRC_TPRM-1\grc_frontend
```

#### 2. Build GRC Frontend
```powershell
# Install dependencies (if not already installed)
npm install

# Build production version
npm run build

# This creates: grc_frontend\dist\
```

#### 3. Build TPRM Frontend
```powershell
# Navigate to TPRM frontend directory
cd tprm_frontend

# Install dependencies (if not already installed)
npm install

# Build production version
npm run build

# This creates: grc_frontend\tprm_frontend\dist\
```

#### 4. Verify Builds
```powershell
# Check GRC build
Test-Path "C:\Users\puttu\Videos\GRC_TPRM-1\grc_frontend\dist\index.html"

# Check TPRM build
Test-Path "C:\Users\puttu\Videos\GRC_TPRM-1\grc_frontend\tprm_frontend\dist\index.html"
```

---

## Deploy to Ubuntu Server

### Step 1: Set Permissions Before SCP (on Ubuntu server via SSH)

```bash
# SSH into server first
ssh -i "C:\Users\puttu\Downloads\grc_tprm_pem_key.pem" ubuntu@13.203.184.82

# Set permissions so ubuntu user can write
sudo chown -R ubuntu:ubuntu /var/www/html/grc
sudo chmod -R 775 /var/www/html/grc
sudo chown -R ubuntu:ubuntu /var/www/html/tprm
sudo chmod -R 775 /var/www/html/tprm
```

### Step 2: Copy GRC Frontend (from Windows PowerShell)

```powershell
# Copy GRC frontend dist files to server
scp -i "C:\Users\puttu\Downloads\grc_tprm_pem_key.pem" -r "C:\Users\puttu\Videos\GRC_TPRM-1\grc_frontend\dist\*" ubuntu@13.203.184.82:/var/www/html/grc
```

### Step 3: Copy TPRM Frontend (from Windows PowerShell)

```powershell
# Copy TPRM frontend dist files to server
scp -i "C:\Users\puttu\Downloads\grc_tprm_pem_key.pem" -r "C:\Users\puttu\Videos\GRC_TPRM-1\grc_frontend\tprm_frontend\dist\*" ubuntu@13.203.184.82:/var/www/html/tprm
```

### Step 4: Set Permissions After SCP (on Ubuntu server via SSH)

```bash
# SSH into server again
ssh -i "C:\Users\puttu\Downloads\grc_tprm_pem_key.pem" ubuntu@13.203.184.82

# Set proper ownership and permissions for nginx
sudo chown -R www-data:www-data /var/www/html/grc
sudo chmod -R 755 /var/www/html/grc
sudo chown -R www-data:www-data /var/www/html/tprm
sudo chmod -R 755 /var/www/html/tprm
```

---

## Configure Nginx

### Step 1: Create Nginx Configuration for GRC

```bash
# SSH into server
ssh -i "C:\Users\puttu\Downloads\grc_tprm_pem_key.pem" ubuntu@13.203.184.82

# Create nginx config for GRC
sudo nano /etc/nginx/sites-available/grc
```

**Add this configuration:**
```nginx
server {
    listen 80;
    server_name 13.203.184.82;  # Replace with your domain if you have one

    root /var/www/html/grc;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Main location - SPA routing support
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy to backend (if backend is on same server)
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security - deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Error pages
    error_page 404 /index.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

### Step 2: Create Nginx Configuration for TPRM

```bash
# Create nginx config for TPRM
sudo nano /etc/nginx/sites-available/tprm
```

**Add this configuration:**
```nginx
server {
    listen 80;
    server_name 13.203.184.82;  # Replace with your domain if you have one

    root /var/www/html/tprm;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # TPRM routes - SPA routing support
    location /tprm/ {
        alias /var/www/html/tprm/;
        try_files $uri $uri/ /tprm/index.html;
        
        # Remove /tprm prefix for file access
        rewrite ^/tprm/(.*)$ /$1 break;
    }

    # Main TPRM location
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security - deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Error pages
    error_page 404 /index.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

### Step 3: Enable Sites and Configure Main Server

**Option A: Separate Domains/Ports (Recommended)**
```bash
# Enable GRC site (accessible at root /)
sudo ln -s /etc/nginx/sites-available/grc /etc/nginx/sites-enabled/

# Enable TPRM site (accessible at /tprm/)
sudo ln -s /etc/nginx/sites-available/tprm /etc/nginx/sites-enabled/

# Remove default nginx site (optional)
sudo rm /etc/nginx/sites-enabled/default
```

**Option B: Single Server Block with Multiple Locations (Alternative)**
If you want both on the same server block, create a combined config:

```bash
sudo nano /etc/nginx/sites-available/grc_tprm
```

```nginx
server {
    listen 80;
    server_name 13.203.184.82;

    # GRC Frontend (root)
    location / {
        root /var/www/html/grc;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # TPRM Frontend
    location /tprm/ {
        alias /var/www/html/tprm/;
        index index.html;
        try_files $uri $uri/ /tprm/index.html;
        
        # Remove /tprm prefix for file access
        rewrite ^/tprm/(.*)$ /$1 break;
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Then enable it:
```bash
sudo ln -s /etc/nginx/sites-available/grc_tprm /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
```

### Step 4: Test and Restart Nginx

```bash
# Test nginx configuration
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx

# Or restart nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

---

## Verify Deployment

### 1. Check Files are Deployed
```bash
# Check GRC files
ls -la /var/www/html/grc/

# Check TPRM files
ls -la /var/www/html/tprm/

# Check permissions
ls -la /var/www/html/grc/ | head -5
ls -la /var/www/html/tprm/ | head -5
```

### 2. Test in Browser
- GRC Frontend: `http://13.203.184.82/`
- TPRM Frontend: `http://13.203.184.82/tprm/` (if using combined config)

### 3. Check Nginx Logs (if issues)
```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

---

## Quick Deployment Script (All-in-One)

Create a deployment script on Windows to automate the process:

**Save as `deploy-frontend.ps1`:**
```powershell
# Frontend Deployment Script for Ubuntu
$PEM_KEY = "C:\Users\puttu\Downloads\grc_tprm_pem_key.pem"
$SERVER = "ubuntu@13.203.184.82"
$GRC_DIST = "C:\Users\puttu\Videos\GRC_TPRM-1\grc_frontend\dist\*"
$TPRM_DIST = "C:\Users\puttu\Videos\GRC_TPRM-1\grc_frontend\tprm_frontend\dist\*"

Write-Host "=== Building Frontends ===" -ForegroundColor Green

# Build GRC
Write-Host "Building GRC frontend..." -ForegroundColor Yellow
cd "C:\Users\puttu\Videos\GRC_TPRM-1\grc_frontend"
npm run build

# Build TPRM
Write-Host "Building TPRM frontend..." -ForegroundColor Yellow
cd "tprm_frontend"
npm run build
cd ..

Write-Host "=== Setting Permissions (Before SCP) ===" -ForegroundColor Green
ssh -i $PEM_KEY $SERVER "sudo chown -R ubuntu:ubuntu /var/www/html/grc && sudo chmod -R 775 /var/www/html/grc && sudo chown -R ubuntu:ubuntu /var/www/html/tprm && sudo chmod -R 775 /var/www/html/tprm"

Write-Host "=== Copying GRC Frontend ===" -ForegroundColor Green
scp -i $PEM_KEY -r $GRC_DIST "$SERVER:/var/www/html/grc"

Write-Host "=== Copying TPRM Frontend ===" -ForegroundColor Green
scp -i $PEM_KEY -r $TPRM_DIST "$SERVER:/var/www/html/tprm"

Write-Host "=== Setting Permissions (After SCP) ===" -ForegroundColor Green
ssh -i $PEM_KEY $SERVER "sudo chown -R www-data:www-data /var/www/html/grc && sudo chmod -R 755 /var/www/html/grc && sudo chown -R www-data:www-data /var/www/html/tprm && sudo chmod -R 755 /var/www/html/tprm"

Write-Host "=== Reloading Nginx ===" -ForegroundColor Green
ssh -i $PEM_KEY $SERVER "sudo nginx -t && sudo systemctl reload nginx"

Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
```

**Run the script:**
```powershell
.\deploy-frontend.ps1
```

---

## Troubleshooting

### Issue: Permission Denied on SCP
**Solution:** Make sure you set permissions BEFORE SCP:
```bash
sudo chown -R ubuntu:ubuntu /var/www/html/grc
sudo chmod -R 775 /var/www/html/grc
```

### Issue: 403 Forbidden in Browser
**Solution:** Check permissions and ownership:
```bash
sudo chown -R www-data:www-data /var/www/html/grc
sudo chmod -R 755 /var/www/html/grc
```

### Issue: 404 Not Found
**Solution:** 
1. Check nginx configuration: `sudo nginx -t`
2. Verify files exist: `ls -la /var/www/html/grc/`
3. Check nginx error logs: `sudo tail -f /var/log/nginx/error.log`

### Issue: SPA Routing Not Working
**Solution:** Make sure nginx config has `try_files $uri $uri/ /index.html;` for SPA routing support.

### Issue: API Calls Failing
**Solution:** 
1. Verify backend is running: `docker ps | grep grc_tprm_backend`
2. Check backend port: Should be accessible at `http://localhost:8000`
3. Verify nginx proxy_pass is correct in config

---

## Summary

**For each deployment:**
1. ✅ Build frontends locally (`npm run build`)
2. ✅ Set permissions before SCP (ubuntu:ubuntu, 775)
3. ✅ Copy files via SCP
4. ✅ Set permissions after SCP (www-data:www-data, 755)
5. ✅ Reload nginx

**Key Ubuntu Differences:**
- User: `ubuntu` (not `ec2-user`)
- Web server user: `www-data` (not `nginx`)
- Package manager: `apt` (not `yum`)

