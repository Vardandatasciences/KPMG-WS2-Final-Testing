#!/usr/bin/env python3
"""
BambooHR OAuth Flask Server
Integrates with Django backend for BambooHR OAuth flow
Based on the original test.py but modified for production integration
"""

import os
import re
import secrets
import urllib.parse as up
import requests
from flask import Flask, redirect, request, session, url_for, jsonify
from dotenv import load_dotenv
from grc.utils.url_validator import validate_url, InvalidOutboundUrlError

load_dotenv()

try:
    from ....debug_utils import debug_print
except ImportError:
    def debug_debug_print(*args, **kwargs): debug_print(*args, **kwargs)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))


def _sanitize_bamboohr_subdomain(subdomain):
    """Allowlist tenant label for *.bamboohr.com (avoids host injection in redirects/requests)."""
    s = (subdomain or "").strip().lower()
    if len(s) > 63:
        s = s[:63]
    if not s or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", s):
        return ""
    return s


def _sanitize_oauth_error_code(value):
    raw = "" if value is None else str(value)
    s = re.sub(r"[^\w.\-]", "", raw).strip() or "oauth_error"
    return s[:128]


def _safe_get(url, **kwargs):
    # SECURITY: guard against SSRF-style outbound URL abuse.
    try:
        validate_url(url)
    except InvalidOutboundUrlError as exc:
        raise requests.RequestException(str(exc)) from exc
    return requests.get(url, **kwargs)


def _safe_post(url, **kwargs):
    # SECURITY: guard against SSRF-style outbound URL abuse.
    try:
        validate_url(url)
    except InvalidOutboundUrlError as exc:
        raise requests.RequestException(str(exc)) from exc
    return requests.post(url, **kwargs)


def _request_is_https():
    if request.is_secure:
        return True
    return (request.headers.get("X-Forwarded-Proto") or "").lower() == "https"


def _hsts_header_value():
    max_age = (os.environ.get("HSTS_MAX_AGE") or "31536000").strip() or "31536000"
    include = os.environ.get("HSTS_INCLUDE_SUBDOMAINS", "true").lower() != "false"
    preload = os.environ.get("HSTS_PRELOAD", "true").lower() != "false"
    parts = [f"max-age={max_age}"]
    if include:
        parts.append("includeSubDomains")
    if preload:
        parts.append("preload")
    return "; ".join(parts)


# SECURITY: Apply missing/permissive HTTP security headers to all responses.
@app.after_request
def apply_security_headers(response):
    # CSP should be consistent for HTML responses returned by this service.
    response.headers['Content-Security-Policy'] = "; ".join([
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "img-src 'self' data: https:",
        "connect-src 'self'",
        "font-src 'self' data:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ])

    # HSTS only when the request is actually HTTPS (align with reverse-proxy reality).
    try:
        if _request_is_https():
            response.headers["Strict-Transport-Security"] = _hsts_header_value()
    except Exception:
        # Never fail the request if header computation errors.
        pass

    return response

# BambooHR OAuth Configuration
CLIENT_ID = os.environ.get("BAMBOOHR_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("BAMBOOHR_CLIENT_SECRET", "").strip()

# Get environment configuration
USE_LOCAL = os.environ.get("USE_LOCAL_DEVELOPMENT", "True").lower() == "true"

# Set URLs based on environment (non-local: no hardcoded tenant domains — require env).
if USE_LOCAL:
    _default_redirect = "http://127.0.0.1:8000/api/bamboohr/oauth-callback/"
    DJANGO_BACKEND_URL = os.environ.get("DJANGO_BACKEND_URL", "http://127.0.0.1:8000").strip()
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8080").strip()
    REDIRECT_URI = os.environ.get("BAMBOOHR_REDIRECT_URI", _default_redirect).strip()
    debug_print("🌍 Running in LOCAL development mode")
else:
    DJANGO_BACKEND_URL = os.environ.get("DJANGO_BACKEND_URL", "").strip()
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "").strip()
    REDIRECT_URI = os.environ.get("BAMBOOHR_REDIRECT_URI", "").strip()
    if not REDIRECT_URI or not DJANGO_BACKEND_URL or not FRONTEND_URL:
        raise RuntimeError(
            "Non-local BambooHR OAuth requires BAMBOOHR_REDIRECT_URI, DJANGO_BACKEND_URL, and FRONTEND_URL."
        )
    debug_print("🌍 Running in PRODUCTION mode")
SCOPES = os.environ.get("BAMBOOHR_SCOPES", "email openid employee company:info employee:contact employee:job employee:name employee:photo employee_directory").split()

def form_headers():
    return {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}

def auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

@app.route("/")
def home():
    return """
    <h3>BambooHR OAuth Integration Server</h3>
    <p>This server handles BambooHR OAuth flow for the GRC application.</p>
    <p><strong>Status:</strong> Running</p>
    <hr>
    <p><a href="/health">Health Check</a></p>
    """

@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "BambooHR OAuth Server",
        "version": "1.0.0"
    })

@app.route("/set-subdomain-and-login")
def set_subdomain_and_login():
    """Handle subdomain setting and initiate OAuth flow"""
    raw_sub = request.args.get("subdomain", "").strip()
    if not raw_sub:
        return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=missing_subdomain")
    subdomain = _sanitize_bamboohr_subdomain(raw_sub)
    if not subdomain:
        return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=invalid_subdomain")
    user_id = request.args.get("user_id", "1")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=oauth_not_configured")
    
    # Store subdomain and user_id in session
    session["subdomain"] = subdomain
    session["user_id"] = user_id
    
    # Initiate OAuth flow
    return redirect(url_for("login"))

@app.route("/login")
def login():
    """Initiate OAuth flow with BambooHR"""
    # Check if subdomain is set
    subdomain = _sanitize_bamboohr_subdomain(session.get("subdomain", ""))
    if not subdomain:
        return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=session_expired")
    
    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state
    
    session["subdomain"] = subdomain
    auth_base = f"https://{subdomain}.bamboohr.com/authorize.php"
    
    params = {
        "request": "authorize",
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": state,
    }
    
    oauth_url = f"{auth_base}?{up.urlencode(params)}"
    debug_print(f"🔗 Redirecting to BambooHR OAuth: {oauth_url}")
    
    return redirect(oauth_url)

@app.route("/oauth/callback")
def oauth_callback():
    """Handle OAuth callback from BambooHR"""
    try:
        # Verify state parameter
        if request.args.get("state") != session.get("oauth_state"):
            debug_print("❌ OAuth state mismatch")
            return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=state_mismatch")

        code = request.args.get("code")
        if not code:
            oauth_error = _sanitize_oauth_error_code(request.args.get("error"))
            error_description = request.args.get("error_description", "Missing authorization code")
            error_description = str(error_description).replace("\r", "").replace("\n", "").strip()[:500]
            debug_print(f"❌ OAuth error: {oauth_error} — {error_description}")
            return redirect(
                f"{FRONTEND_URL}/integration/bamboohr?"
                f"{up.urlencode({'error': oauth_error, 'error_description': error_description})}"
            )

        # Check if subdomain and user_id are in session
        subdomain = _sanitize_bamboohr_subdomain(session.get("subdomain"))
        user_id = session.get("user_id", "1")
        
        if not subdomain:
            return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=session_expired")

        # Exchange code for access token
        token_base = f"https://{subdomain}.bamboohr.com/token.php"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        
        debug_print(f"🔄 Exchanging code for token with {subdomain}.bamboohr.com")
        token_resp = _safe_post(f"{token_base}?request=token", headers=form_headers(), data=data, timeout=30)
        
        if token_resp.status_code != 200:
            debug_print(f"❌ Token exchange failed: {token_resp.status_code} {token_resp.text}")
            return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=token_exchange_failed")

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            debug_print("❌ No access token in response")
            return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=no_access_token")

        debug_print(f"✅ Access token received: {access_token[:20]}...")
        
        # Store access token in session
        session["access_token"] = access_token
        
        # Test the token by fetching basic data
        api_base = f"https://{subdomain}.bamboohr.com/api/v1"
        headers = auth_headers(access_token)
        
        # Try to fetch company info to verify token works
        try:
            company_resp = _safe_get(f"{api_base}/meta/company", headers=headers, timeout=30)
            if company_resp.status_code == 200:
                company_info = company_resp.json()
                debug_print(f"✅ Token verified with company: {company_info}")
            else:
                debug_print(f"⚠️ Could not verify token with company API: {company_resp.status_code}")
        except Exception as e:
            debug_print(f"⚠️ Error verifying token: {e}")
        
        # Notify Django backend about successful connection
        try:
            callback_url = f"{DJANGO_BACKEND_URL}/api/bamboohr/oauth-callback/"
            callback_data = {
                "access_token": access_token,
                "user_id": user_id,
                "subdomain": subdomain,
                "account_info": {
                    "account_id": f"bamboohr_{subdomain}_{user_id}",
                    "account_type": "bamboohr",
                    "name": f"{subdomain}.bamboohr.com"
                }
            }
            
            debug_print(f"📡 Notifying Django backend: {callback_url}")
            django_resp = _safe_post(callback_url, json=callback_data, timeout=30)
            
            if django_resp.status_code == 200:
                debug_print("✅ Django backend notified successfully")
            else:
                debug_print(f"⚠️ Django backend notification failed: {django_resp.status_code}")
        
        except Exception as e:
            debug_print(f"⚠️ Error notifying Django backend: {e}")
        
        # Redirect back to frontend with success
        frontend_callback_url = f"{FRONTEND_URL}/integration/bamboohr?{up.urlencode({'token': access_token, 'user_id': user_id, 'subdomain': subdomain, 'success': 'true'})}"
        debug_print(f"🔗 Redirecting to frontend: {frontend_callback_url}")
        
        # Clear sensitive session data
        session.pop("oauth_state", None)
        session.pop("access_token", None)
        
        return redirect(frontend_callback_url)
        
    except Exception as e:
        debug_print(f"❌ OAuth callback error: {str(e)}")
        return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=callback_error")

@app.route("/test-connection")
def test_connection():
    """Test endpoint to verify server is running"""
    return jsonify({
        "status": "ok",
        "message": "BambooHR OAuth server is running",
        "endpoints": {
            "health": "/health",
            "oauth_initiate": "/set-subdomain-and-login",
            "oauth_callback": "/oauth/callback"
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint was not found",
        "available_endpoints": ["/", "/health", "/test-connection"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": "An internal server error occurred"
    }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    debug_print(f"🚀 Starting BambooHR OAuth Server on port {port}")
    debug_print(f"🔧 Debug mode: {debug}")
    debug_print(f"🌍 Environment: {'LOCAL' if USE_LOCAL else 'PRODUCTION'}")
    debug_print(f"🌐 Django Backend: {DJANGO_BACKEND_URL}")
    debug_print(f"🌐 Frontend URL: {FRONTEND_URL}")
    debug_print(f"🔗 Redirect URI: {REDIRECT_URI}")
    debug_print(f"🔑 Client ID configured: {'Yes' if CLIENT_ID else 'No'}")
    debug_print(f"🔐 Client Secret configured: {'Yes' if CLIENT_SECRET else 'No'}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)