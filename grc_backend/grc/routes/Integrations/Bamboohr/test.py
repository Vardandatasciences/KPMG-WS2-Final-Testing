import os
import re
import secrets
import urllib.parse as up

from flask import Flask, redirect, request, session, url_for, jsonify
import requests
from dotenv import load_dotenv
from html import escape as html_escape
from grc.utils.url_validator import validate_url, InvalidOutboundUrlError

load_dotenv()

try:
    from ....debug_utils import debug_print
except ImportError:
    def debug_print(*args, **kwargs):
        pass

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))


def _sanitize_bamboohr_subdomain(subdomain):
    """Allowlist tenant label for *.bamboohr.com (demo app; same rules as production OAuth server)."""
    s = (subdomain or "").strip().lower()
    if len(s) > 63:
        s = s[:63]
    if not s or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", s):
        return ""
    return s


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


# SECURITY: ensure this Flask service sends CSP + HSTS for browser responses.
@app.after_request
def apply_security_headers(response):
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

    try:
        if _request_is_https():
            response.headers["Strict-Transport-Security"] = _hsts_header_value()
    except Exception:
        pass

    return response

SUBDOMAIN     = os.environ["BAMBOOHR_SUBDOMAIN"].strip()
CLIENT_ID     = os.environ["BAMBOOHR_CLIENT_ID"].strip()
CLIENT_SECRET = os.environ["BAMBOOHR_CLIENT_SECRET"].strip()
REDIRECT_URI  = os.environ["BAMBOOHR_REDIRECT_URI"].strip()
SCOPES        = os.environ.get("BAMBOOHR_SCOPES", "email openid employee company:info employee:contact employee:job employee:name employee:photo employee_directory").split()

AUTH_BASE  = f"https://{SUBDOMAIN}.bamboohr.com/authorize.php"
TOKEN_BASE = f"https://{SUBDOMAIN}.bamboohr.com/token.php"
API_BASE   = f"https://{SUBDOMAIN}.bamboohr.com/api/v1"

def form_headers():
    return {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}

def auth_headers():
    return {"Authorization": f"Bearer {session.get('access_token')}", "Accept": "application/json"}

@app.route("/")
def home():
    return (
        "<h3>BambooHR OAuth Demo</h3>"
        "<p>Enter your BambooHR subdomain to get started:</p>"
        "<form method='post' action='/set-subdomain'>"
        "<input type='text' name='subdomain' placeholder='your-company' required>"
        "<span>.bamboohr.com</span><br><br>"
        "<button type='submit'>Continue to Login</button>"
        "</form>"
        "<hr>"
        "<ul>"
        "<li><a href='/me'>Fetch logged-in user (or company info)</a></li>"
        "<li><a href='/logout'>Logout</a></li>"
        "</ul>"
    )

@app.route("/set-subdomain", methods=["POST"])
def set_subdomain():
    raw = request.form.get("subdomain", "").strip()
    if not raw:
        return "Subdomain is required", 400
    subdomain = _sanitize_bamboohr_subdomain(raw)
    if not subdomain:
        return "Invalid subdomain (use letters, numbers, and hyphens only).", 400

    session["subdomain"] = subdomain
    return redirect(url_for("login"))

@app.route("/login")
def login():
    subdomain = _sanitize_bamboohr_subdomain(session.get("subdomain", ""))
    if not subdomain:
        session.pop("subdomain", None)
        return redirect(url_for("home"))

    session["subdomain"] = subdomain
    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state
    auth_base = f"https://{subdomain}.bamboohr.com/authorize.php"
    
    params = {
        "request": "authorize",
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": state,
    }
    return redirect(f"{auth_base}?{up.urlencode(params)}")

@app.route("/oauth/callback")
def oauth_callback():
    if request.args.get("state") != session.get("oauth_state"):
        return "State mismatch", 400

    code = request.args.get("code")
    if not code:
        return "Missing ?code", 400

    subdomain = _sanitize_bamboohr_subdomain(session.get("subdomain", ""))
    if not subdomain:
        return "Subdomain not set or invalid", 400

    session["subdomain"] = subdomain
    token_base = f"https://{subdomain}.bamboohr.com/token.php"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    token_resp = _safe_post(f"{token_base}?request=token", headers=form_headers(), data=data, timeout=30)
    if token_resp.status_code != 200:
        # SECURITY: escape any upstream response text before returning HTML/text to browser.
        return f"Token exchange failed: {token_resp.status_code} {html_escape(token_resp.text)}", 400

    tok = token_resp.json()
    session["access_token"] = tok.get("access_token")
    return redirect(url_for("me"))

@app.route("/me")
def me():
    if "access_token" not in session:
        return redirect(url_for("login"))
    
    subdomain = _sanitize_bamboohr_subdomain(session.get("subdomain", ""))
    if not subdomain:
        session.pop("subdomain", None)
        return redirect(url_for("home"))
    api_base = f"https://{subdomain}.bamboohr.com/api/v1"
    
    headers = auth_headers()
    data_collected = {}
    access_token = session.get('access_token', 'None')[:20]
    subdomain_safe = html_escape(subdomain)
    access_token_safe = html_escape(access_token)

    # Step 1: Try to get logged-in user from /meta/users
    try:
        users_resp = _safe_get(f"{api_base}/meta/users", headers=headers, timeout=30)
        debug_print(f"Users API response: {users_resp.status_code}")
        
        if users_resp.status_code == 200:
            users = users_resp.json().get("users", [])
            debug_print(f"Found {len(users)} users")
            data_collected["users_info"] = users_resp.json()
            current_user = next((u for u in users if u.get("self")), None)

            if current_user:
                employee_id = current_user["employeeId"]
                debug_print("Current user employee ID resolved (value not logged)")
                fields = [
                    "id","displayName","firstName","lastName","jobTitle","department",
                    "division","location","workEmail","mobilePhone","workPhone","hireDate",
                    "supervisor","supervisorId","status"
                ]
                emp_resp = _safe_get(
                    f"{api_base}/employees/{employee_id}",
                    params={"fields": ",".join(fields)},
                    headers=headers,
                    timeout=30
                )
                debug_print(f"Employee API response: {emp_resp.status_code}")
                if emp_resp.status_code == 200:
                    profile = emp_resp.json()
                    data_collected["current_user_profile"] = profile
                    _prof_info = (
                        f"{len(profile)} top-level keys"
                        if isinstance(profile, dict)
                        else "non-dict body"
                    )
                    debug_print(f"Logged-in user profile received ({_prof_info})")
                else:
                    debug_print(f"Employee API error: HTTP {emp_resp.status_code}")
        elif users_resp.status_code == 401:
            debug_print(f"Users API error: {users_resp.status_code} - Unauthorized")
        else:
            debug_print(f"Users API error: HTTP {users_resp.status_code}")
    except Exception:
        debug_print("Exception in users API call (details not logged)")

    # Step 2: Try to get company information
    try:
        company_resp = _safe_get(f"{api_base}/meta/company", headers=headers, timeout=30)
        debug_print(f"Company API response: {company_resp.status_code}")
        if company_resp.status_code == 200:
            data_collected["company_info"] = company_resp.json()
            debug_print("✓ Company info retrieved")
        else:
            debug_print(f"Company API error: {company_resp.status_code}")
    except Exception as e:
        debug_print(f"Exception in company API call: {e}")

    # Step 3: Try to get employee directory
    try:
        directory_resp = _safe_get(f"{api_base}/employees/directory", headers=headers, timeout=30)
        debug_print(f"Directory API response: {directory_resp.status_code}")
        if directory_resp.status_code == 200:
            data_collected["employee_directory"] = directory_resp.json()
            debug_print("✓ Employee directory retrieved")
        else:
            debug_print(f"Directory API error: {directory_resp.status_code}")
    except Exception:
        debug_print("Exception in directory API call (details not logged)")

    # Step 4: Try to get reports list
    try:
        reports_resp = _safe_get(f"{api_base}/reports", headers=headers, timeout=30)
        debug_print(f"Reports API response: {reports_resp.status_code}")
        if reports_resp.status_code == 200:
            data_collected["reports"] = reports_resp.json()
            debug_print("✓ Reports retrieved")
        else:
            debug_print(f"Reports API error: {reports_resp.status_code}")
    except Exception:
        debug_print("Exception in reports API call (details not logged)")

    # If we got any data, display it
    if data_collected:
        keys_html = ''.join([
            f'<li><strong>{html_escape(key.replace("_", " ").title())}:</strong> Retrieved ✓</li>'
            for key in data_collected.keys()
        ])
        raw_json = jsonify(data_collected).get_data(as_text=True)
        raw_json_safe = html_escape(raw_json)

        return f"""
        <h2>BambooHR Data Retrieved Successfully!</h2>
        <h3>Company: {subdomain_safe}.bamboohr.com</h3>
        <h3>Access Token: {access_token_safe}...</h3>
        <hr>
        <h3>Available Data:</h3>
        <ul>
        {keys_html}
        </ul>
        <hr>
        <h3>Raw Data:</h3>
        <pre>{raw_json_safe}</pre>
        <hr>
        <p><a href="/">← Back to Home</a> | <a href="/logout">Logout</a></p>
        """
    else:
        # If no data was retrieved, show error and redirect
        return f"""
        <h2>No Data Retrieved</h2>
        <p>Company: {subdomain_safe}.bamboohr.com</p>
        <p>The access token may not have sufficient permissions for any of the available endpoints.</p>
        <p>Access Token: {access_token_safe}...</p>
        <p>Try logging in again or check your BambooHR app permissions.</p>
        <p><a href="/">← Back to Home</a> | <a href="/logout">Logout</a></p>
        """

@app.route("/logout")
def logout():
    session.clear()
    return "Logged out."

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=app.config.get("DEBUG", False),
    )
