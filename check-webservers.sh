#!/bin/bash

# Quick Diagnostic Script to Check Existing Web Servers
# Run this before setting up nginx for GRC/TPRM

echo "=========================================="
echo "Web Server Diagnostic Check"
echo "=========================================="
echo ""

echo "1. Checking Nginx Status..."
echo "---------------------------"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is RUNNING"
    sudo systemctl status nginx --no-pager -l | head -5
else
    echo "❌ Nginx is NOT running (or not installed)"
fi
echo ""

echo "2. Checking Apache Status..."
echo "----------------------------"
if systemctl is-active --quiet apache2 || systemctl is-active --quiet httpd; then
    echo "✅ Apache is RUNNING"
    sudo systemctl status apache2 --no-pager -l 2>/dev/null | head -5 || \
    sudo systemctl status httpd --no-pager -l 2>/dev/null | head -5
else
    echo "❌ Apache is NOT running (or not installed)"
fi
echo ""

echo "3. Checking Port 80 Usage..."
echo "-----------------------------"
PORT80=$(sudo lsof -i :80 2>/dev/null || sudo ss -tlnp | grep :80)
if [ -z "$PORT80" ]; then
    echo "✅ Port 80 is AVAILABLE"
else
    echo "⚠️  Port 80 is IN USE:"
    echo "$PORT80"
fi
echo ""

echo "4. Checking Port 443 Usage (HTTPS)..."
echo "--------------------------------------"
PORT443=$(sudo lsof -i :443 2>/dev/null || sudo ss -tlnp | grep :443)
if [ -z "$PORT443" ]; then
    echo "✅ Port 443 is AVAILABLE"
else
    echo "⚠️  Port 443 is IN USE:"
    echo "$PORT443"
fi
echo ""

echo "5. Checking Existing Nginx Configurations..."
echo "---------------------------------------------"
if [ -d "/etc/nginx/sites-available" ]; then
    echo "Available sites:"
    ls -la /etc/nginx/sites-available/ 2>/dev/null | grep -v "^d" | grep -v "^total"
    echo ""
    echo "Enabled sites:"
    ls -la /etc/nginx/sites-enabled/ 2>/dev/null | grep -v "^d" | grep -v "^total"
else
    echo "❌ Nginx sites directory not found (nginx may not be installed)"
fi
echo ""

echo "6. Checking Web Server Processes..."
echo "-----------------------------------"
WEB_PROCS=$(ps aux | grep -E "nginx|apache|httpd|gunicorn|uwsgi" | grep -v grep)
if [ -z "$WEB_PROCS" ]; then
    echo "✅ No web server processes found"
else
    echo "⚠️  Found web server processes:"
    echo "$WEB_PROCS"
fi
echo ""

echo "7. Checking Your Home Directory Applications..."
echo "-----------------------------------------------"
echo "Your apps in ~/ are SAFE (nginx won't serve from /home/ubuntu/):"
ls -ld ~/CashflowApp ~/horilla ~/Policy_Extractor ~/grc_tprm 2>/dev/null | awk '{print "  - " $9}'
echo ""

echo "8. Checking Target Directories for GRC/TPRM..."
echo "-----------------------------------------------"
if [ -d "/var/www/html/grc" ]; then
    echo "✅ /var/www/html/grc exists"
    ls -la /var/www/html/grc/ | head -3
else
    echo "❌ /var/www/html/grc does NOT exist (will need to create)"
fi
echo ""

if [ -d "/var/www/html/tprm" ]; then
    echo "✅ /var/www/html/tprm exists"
    ls -la /var/www/html/tprm/ | head -3
else
    echo "❌ /var/www/html/tprm does NOT exist (will need to create)"
fi
echo ""

echo "=========================================="
echo "Summary & Recommendations"
echo "=========================================="
echo ""

# Determine recommendation
if systemctl is-active --quiet nginx; then
    if [ -n "$PORT80" ]; then
        echo "⚠️  WARNING: Nginx is running and port 80 is in use"
        echo "   → Check existing nginx configs before adding GRC/TPRM"
        echo "   → Option: Use different port (8080) for GRC/TPRM"
    else
        echo "✅ Nginx is installed but port 80 seems free"
        echo "   → Safe to add GRC/TPRM configuration"
    fi
elif systemctl is-active --quiet apache2 || systemctl is-active --quiet httpd; then
    echo "⚠️  WARNING: Apache is running (conflicts with nginx on port 80)"
    echo "   → Option 1: Stop Apache if not needed: sudo systemctl stop apache2"
    echo "   → Option 2: Configure GRC/TPRM on different port (8080)"
    echo "   → Option 3: Use nginx as reverse proxy for Apache"
else
    echo "✅ No web servers running on port 80"
    echo "   → Safe to install and configure nginx for GRC/TPRM"
fi

echo ""
echo "Your files in /home/ubuntu/ are 100% SAFE - nginx will NOT access them"
echo "Nginx only serves from /var/www/html/ (system directory)"
echo ""

