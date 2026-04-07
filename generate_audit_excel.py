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
        "Request Payload": '{ "essential_cookies": true, "functional_cookies": false, ... }',
        "Response Payload": '{ "status": "success", "message": "..." }',
        "Response Time (ms)": "725 ms"
    },
    {
        "Module": "Security",
        "API Name": "reCAPTCHA User Verify",
        "API URL": ".../userverify?k=...",
        "Method": "XHR",
        "Frequency": "1 per login attempt",
        "State Management": "No",
        "Storage Location": "N/A",
        "Request Payload": "Encrypted reCAPTCHA token",
        "Response Payload": "Encoded verification result",
        "Response Time (ms)": "79 ms"
    },
    {
        "Module": "Security",
        "API Name": "reCAPTCHA Reload",
        "API URL": ".../reload?k=...",
        "Method": "XHR",
        "Frequency": "On captcha expiration",
        "State Management": "No",
        "Storage Location": "N/A",
        "Request Payload": "Token regeneration params",
        "Response Payload": "New site key/token",
        "Response Time (ms)": "98 ms"
    },
    {
        "Module": "Login",
        "API Name": "JWT Login",
        "API URL": "/api/jwt/login/",
        "Method": "POST",
        "Frequency": "1 per login attempt",
        "State Management": "Yes",
        "Storage Location": "sessionStorage; localStorage",
        "Request Payload": '{ "username": "...", "password": "...", "login_type": "...", "captcha_token": "..." }',
        "Response Payload": '{ "access_token": "...", "refresh_token": "...", "user": { ... }, "requires_mfa": bool }',
        "Response Time (ms)": "1.91 s"
    },
    {
        "Module": "Post-Login",
        "API Name": "Get User Role",
        "API URL": "/api/grc/user-role/",
        "Method": "GET",
        "Frequency": "1 after login",
        "State Management": "Yes",
        "Storage Location": "localStorage (Role metadata)",
        "Request Payload": "None (Bearer Token)",
        "Response Payload": '{ "role": "...", "user_id": "...", "success": bool }',
        "Response Time (ms)": "720 ms"
    }
]

df = pd.DataFrame(data)
output_path = r"C:\Users\Admin\Desktop\GRC_TPRM-1\login_api_audit_with_timings.xlsx"
df.to_excel(output_path, index=False)
print(f"Excel file with timings created at: {output_path}")
