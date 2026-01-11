#!/bin/bash

# Script to check existing nginx configs and update GRC/TPRM config safely

echo "=========================================="
echo "Checking Existing Nginx Configurations"
echo "=========================================="
echo ""

# Check horilla config
echo "1. Checking horilla configuration..."
echo "-----------------------------------"
if [ -f "/etc/nginx/sites-available/horilla" ]; then
    echo "Horilla config found:"
    echo "---"
    grep -E "server_name|listen|location|proxy_pass|root" /etc/nginx/sites-available/horilla | head -15
    echo ""
    
    # Check if horilla uses a specific path
    if grep -q "location.*horilla" /etc/nginx/sites-available/horilla; then
        HORILLA_PATH=$(grep "location.*horilla" /etc/nginx/sites-available/horilla | head -1)
        echo "📍 Horilla uses path: $HORILLA_PATH"
    elif grep -q "location.*/" /etc/nginx/sites-available/horilla; then
        echo "⚠️  Horilla might use root path /"
    fi
else
    echo "❌ Horilla config not found"
fi
echo ""

# Check tinyllama config
echo "2. Checking tinyllama configuration..."
echo "-----------------------------------"
if [ -f "/etc/nginx/sites-available/tinyllama" ]; then
    echo "TinyLLama config found:"
    echo "---"
    grep -E "server_name|listen|location|proxy_pass|root" /etc/nginx/sites-available/tinyllama | head -15
    echo ""
    
    # Check if tinyllama uses a specific path
    if grep -q "location.*tinyllama" /etc/nginx/sites-available/tinyllama; then
        TINYLLAMA_PATH=$(grep "location.*tinyllama" /etc/nginx/sites-available/tinyllama | head -1)
        echo "📍 TinyLLama uses path: $TINYLLAMA_PATH"
    elif grep -q "location.*/" /etc/nginx/sites-available/tinyllama; then
        echo "⚠️  TinyLLama might use root path /"
    fi
else
    echo "❌ TinyLLama config not found"
fi
echo ""

# Check existing grc-tprm config
echo "3. Checking existing grc-tprm configuration..."
echo "-----------------------------------"
if [ -f "/etc/nginx/sites-available/grc-tprm" ]; then
    echo "GRC-TPRM config found:"
    echo "---"
    grep -E "server_name|listen|location" /etc/nginx/sites-available/grc-tprm | head -20
    echo ""
    
    # Check if it's enabled
    if [ -L "/etc/nginx/sites-enabled/grc-tprm" ]; then
        echo "✅ GRC-TPRM is ENABLED"
    else
        echo "⚠️  GRC-TPRM is NOT ENABLED (available but not active)"
    fi
else
    echo "❌ GRC-TPRM config not found"
fi
echo ""

# Check server_name conflicts
echo "4. Checking for server_name conflicts..."
echo "-----------------------------------"
ALL_SERVER_NAMES=$(grep -h "server_name" /etc/nginx/sites-available/* 2>/dev/null | sort | uniq)
if [ -n "$ALL_SERVER_NAMES" ]; then
    echo "All server_name directives:"
    echo "$ALL_SERVER_NAMES"
    echo ""
    
    # Check for duplicates
    DUPLICATES=$(echo "$ALL_SERVER_NAMES" | cut -d' ' -f2- | sort | uniq -d)
    if [ -n "$DUPLICATES" ]; then
        echo "⚠️  WARNING: Duplicate server_names found:"
        echo "$DUPLICATES"
        echo "→ These sites might conflict!"
    else
        echo "✅ No duplicate server_names found"
    fi
else
    echo "⚠️  Could not read server_name directives"
fi
echo ""

# Check what ports are used
echo "5. Checking port usage..."
echo "-----------------------------------"
ALL_LISTEN=$(grep -h "listen" /etc/nginx/sites-available/* 2>/dev/null | grep -v "#" | sort | uniq)
if [ -n "$ALL_LISTEN" ]; then
    echo "All listen directives:"
    echo "$ALL_LISTEN"
else
    echo "⚠️  Could not read listen directives"
fi
echo ""

# Test current nginx config
echo "6. Testing nginx configuration..."
echo "-----------------------------------"
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx configuration is valid"
    sudo nginx -t 2>&1 | tail -1
else
    echo "❌ Nginx configuration has ERRORS:"
    sudo nginx -t 2>&1 | grep -i error
fi
echo ""

# Check active server blocks
echo "7. Active server blocks summary..."
echo "-----------------------------------"
echo "Enabled sites:"
ls -la /etc/nginx/sites-enabled/ | grep "^-" | awk '{print $9}' | grep -v "^$"
echo ""

echo "=========================================="
echo "Recommendations"
echo "=========================================="
echo ""

# Determine recommendation
if [ -f "/etc/nginx/sites-available/horilla" ] && [ -f "/etc/nginx/sites-available/tinyllama" ]; then
    if grep -q "location.*/" /etc/nginx/sites-available/horilla || grep -q "location.*/" /etc/nginx/sites-available/tinyllama; then
        echo "⚠️  WARNING: Horilla or TinyLLama might use root path /"
        echo ""
        echo "RECOMMENDATION: Update grc-tprm config to exclude horilla/tinyllama paths:"
        echo ""
        echo "Edit /etc/nginx/sites-available/grc-tprm and update GRC location block:"
        echo ""
        echo "  location / {"
        echo "      # Exclude other app paths"
        echo "      if (\$uri ~ ^/(horilla|tinyllama)) {"
        echo "          return 404;"
        echo "      }"
        echo "      root /var/www/html/grc;"
        echo "      index index.html;"
        echo "      try_files \$uri \$uri/ /index.html;"
        echo "  }"
        echo ""
    else
        echo "✅ Other apps likely use specific paths - GRC-TPRM config should work"
    fi
else
    echo "✅ Safe to enable GRC-TPRM configuration"
fi

echo ""
echo "Next steps:"
echo "1. Review the configurations above"
echo "2. Update /etc/nginx/sites-available/grc-tprm if needed"
echo "3. Test: sudo nginx -t"
echo "4. Enable: sudo ln -s /etc/nginx/sites-available/grc-tprm /etc/nginx/sites-enabled/grc-tprm"
echo "5. Reload: sudo systemctl reload nginx"
echo ""

