import pandas as pd

data = [
    {
        "Module": "Cookie",
        "API Name": "Save Cookie Preferences",
        "API URL": "/api/cookie/preferences/save/",
        "Method": "POST",
        "Frequency": "1 on page load/consent",
        "State Management": "Yes",
        "Storage Location": "localStorage (cookie_preferences)",
        "Request Payload": '{ "essential_cookies": true, ... }',
        "Response Payload": '{ "status": "success", ... }',
        "Response Time": "725 ms"
    },
    {
        "Module": "Security",
        "API Name": "reCAPTCHA User Verify",
        "API URL": "google.com/recaptcha/.../userverify",
        "Method": "POST",
        "Frequency": "1 per login attempt",
        "State Management": "No",
        "Storage Location": "N/A",
        "Request Payload": "Encrypted reCAPTCHA token",
        "Response Payload": "Encoded verification result",
        "Response Time": "79 ms"
    },
    {
        "Module": "Security",
        "API Name": "reCAPTCHA Reload",
        "API URL": "google.com/recaptcha/.../reload",
        "Method": "GET",
        "Frequency": "On captcha expiration",
        "State Management": "No",
        "Storage Location": "N/A",
        "Request Payload": "Site key/Token",
        "Response Payload": "New Token",
        "Response Time": "98 ms"
    },
    {
        "Module": "Security",
        "API Name": "reCAPTCHA Clear",
        "API URL": "google.com/recaptcha/.../clr",
        "Method": "GET",
        "Frequency": "1 per session",
        "State Management": "No",
        "Storage Location": "N/A",
        "Request Payload": "Session context",
        "Response Payload": "Clear signal",
        "Response Time": "132 ms"
    },
    {
        "Module": "Login",
        "API Name": "JWT Login",
        "API URL": "/api/jwt/login/",
        "Method": "POST",
        "Frequency": "1 per login attempt",
        "State Management": "Yes",
        "Storage Location": "sessionStorage; localStorage",
        "Request Payload": '{ "username", "password", "login_type", "captcha_token" }',
        "Response Payload": '{ "access_token", "refresh_token", "user", "requires_mfa" }',
        "Response Time": "1.91 s"
    },
    {
        "Module": "Login",
        "API Name": "Verify MFA OTP",
        "API URL": "/api/jwt/mfa/verify-otp/",
        "Method": "POST",
        "Frequency": "1 if MFA is enabled",
        "State Management": "Yes",
        "Storage Location": "sessionStorage; localStorage",
        "Request Payload": '{ "username", "password", "otp", "login_type" }',
        "Response Payload": '{ "access_token", "refresh_token", "user" }',
        "Response Time": "N/A (Optional flow)"
    },
    {
        "Module": "Login",
        "API Name": "Resend MFA OTP",
        "API URL": "/api/jwt/mfa/resend-otp/",
        "Method": "POST",
        "Frequency": "On user request",
        "State Management": "No",
        "Storage Location": "N/A",
        "Request Payload": '{ "username", "password", "login_type" }',
        "Response Payload": '{ "status", "message" }',
        "Response Time": "N/A (Optional flow)"
    },
    {
        "Module": "Login",
        "API Name": "Initiate Google OAuth",
        "API URL": "/api/google-oauth/initiate/",
        "Method": "GET",
        "Frequency": "1 per SSO click",
        "State Management": "No",
        "Storage Location": "N/A",
        "Request Payload": "None",
        "Response Payload": '{ "authorization_url" }',
        "Response Time": "N/A (Optional flow)"
    },
    {
        "Module": "Login",
        "API Name": "Google OAuth Payload",
        "API URL": "/api/google/oauth-callback-payload/",
        "Method": "GET",
        "Frequency": "1 after SSO redirect",
        "State Management": "Yes",
        "Storage Location": "sessionStorage",
        "Request Payload": "None",
        "Response Payload": '{ "status", "data" }',
        "Response Time": "N/A (Optional flow)"
    },
    {
        "Module": "Auth",
        "API Name": "JWT Verify",
        "API URL": "/api/jwt/verify/",
        "Method": "GET",
        "Frequency": "1 on page load/refresh",
        "State Management": "Yes",
        "Storage Location": "Auth Interceptors",
        "Request Payload": "None (Bearer Token)",
        "Response Payload": '{ "valid": bool }',
        "Response Time": "N/A"
    },
    {
        "Module": "Post-Login",
        "API Name": "Get User Role",
        "API URL": "/api/grc/user-role/",
        "Method": "GET",
        "Frequency": "1 after successful login",
        "State Management": "Yes",
        "Storage Location": "localStorage (Role metadata)",
        "Request Payload": "None (Bearer Token)",
        "Response Payload": '{ "role", "user_id", "success" }',
        "Response Time": "720 ms"
    },
    {
        "Module": "Post-Login",
        "API Name": "Get User Profile",
        "API URL": "/api/user-profile/${userId}/",
        "Method": "GET",
        "Frequency": "1 on profile access/login",
        "State Management": "Yes",
        "Storage Location": "sessionStorage (current_user)",
        "Request Payload": "None (Bearer Token)",
        "Response Payload": '{ "data": { "email", "username", ... } }',
        "Response Time": "N/A"
    },
    {
        "Module": "Post-Login",
        "API Name": "Vendor Status Check",
        "API URL": "/api/v1/vendor-core/temp-vendors/get_user_data/",
        "Method": "GET",
        "Frequency": "1 if role is Vendor",
        "State Management": "Yes",
        "Storage Location": "Navigation logic",
        "Request Payload": "user_id query param",
        "Response Payload": '{ "lifecycle": { ... } }',
        "Response Time": "N/A"
    }
]

df = pd.DataFrame(data)
output_path = r"C:\Users\Admin\Desktop\GRC_TPRM-1\login_api_audit_complete.xlsx"
df.to_excel(output_path, index=False)
print(f"Complete Excel file created at: {output_path}")
