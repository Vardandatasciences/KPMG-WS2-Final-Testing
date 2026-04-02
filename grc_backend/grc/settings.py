# Add CORS configuration
# Security hardening: never use wildcard origin when credentials are enabled.
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://test-riskavaire.vardaands.com",
]

INSTALLED_APPS = [
    # ... existing apps ...
    'corsheaders',
    'rest_framework',
    # ... your apps ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add this at the top
    'django.middleware.common.CommonMiddleware',
    # ... rest of middleware ...
] 