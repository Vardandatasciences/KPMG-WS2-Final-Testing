"""
Django settings for backend project.
"""

import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try multiple locations for .env file
    env_paths = [
        Path(__file__).resolve().parent.parent / '.env',  # backend/.env
        Path(__file__).resolve().parent.parent.parent / '.env',  # project root/.env
    ]
    env_loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            print(f"[INFO] ✓ Loaded environment variables from: {env_path}")
            env_loaded = True
            break
    if not env_loaded:
        # Try loading from current directory (fallback)
        load_dotenv(override=True)
        print("[INFO] Attempted to load .env from current directory")
except ImportError:
    print("[WARNING] python-dotenv not installed. Install with: pip install python-dotenv")
    print("[WARNING] Falling back to system environment variables only")
except Exception as e:
    print(f"[WARNING] Error loading .env file: {e}")
    print("[WARNING] Falling back to system environment variables only")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production-!@#$%^&*()')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['*']  # Configure appropriately for production

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'grc',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.parent / 'frontend' / 'dist'],  # Vue.js dist directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# Database Configuration
# Supports both local and RDS databases based on environment variables
USE_LOCAL_DB = os.environ.get('USE_LOCAL_DB', 'false').lower() == 'true'

if USE_LOCAL_DB:
    # Local database configuration
    DB_NAME = os.environ.get('DB_NAME', 'grc2')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    print("[INFO] Using LOCAL database configuration")
else:
    # RDS/AWS database configuration
    DB_NAME = os.environ.get('DB_NAME', 'grc2')
    DB_USER = os.environ.get('DB_USER', 'admin')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Vardaan123')
    DB_HOST = os.environ.get('DB_HOST', 'mydb.c1womgmu83di.ap-south-1.rds.amazonaws.com')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    print("[INFO] Using RDS/AWS database configuration")

# Debug: Print database configuration (without password)
print(f"[INFO] Database Configuration:")
print(f"  Host: {DB_HOST}")
print(f"  Port: {DB_PORT}")
print(f"  Database: {DB_NAME}")
print(f"  User: {DB_USER}")
print(f"  Password: {'*' * len(DB_PASSWORD) if DB_PASSWORD else 'Not set'}")
print(f"  Use Local DB: {USE_LOCAL_DB}")

# Test database connection (optional, can be disabled)
TEST_DB_CONNECTION = os.environ.get('TEST_DB_CONNECTION', 'false').lower() == 'true'
if TEST_DB_CONNECTION:
    try:
        import MySQLdb
        conn = MySQLdb.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            port=int(DB_PORT)
        )
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
        result = cursor.fetchone()
        if result:
            print(f"[INFO] ✓ Database '{DB_NAME}' exists")
        else:
            print(f"[WARNING] ⚠ Database '{DB_NAME}' does not exist on {DB_HOST}")
            print(f"[INFO] Available databases:")
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            for db in databases:
                print(f"  - {db[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[WARNING] Could not test database connection: {e}")

DATABASES = {
    "default": {
        "ENGINE": 'django.db.backends.mysql',
        "NAME": "grc2",
        "USER": "admin",
        "PASSWORD": "Vardaan123",
        "HOST": "grc.c1womgmu83di.ap-south-1.rds.amazonaws.com",
        "PORT": "3306",
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES', time_zone='+00:00'",
            "charset": "utf8mb4",
        }
    }
}

# ===== SESSION CONFIGURATION - CRITICAL FOR AUTHENTICATION! =====
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Use database sessions
SESSION_SAVE_EVERY_REQUEST = True  # Save session on every request to keep it active
SESSION_COOKIE_AGE = 86400  # Session expires after 1 day (86400 seconds)
SESSION_COOKIE_NAME = 'grc_sessionid'  # Custom session cookie name
SESSION_COOKIE_HTTPONLY = False  # Allow JavaScript access (needed for SPA)
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'  # Allow cross-site requests with same-site protection (will be overridden by middleware for OAuth)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Session persists after browser close
SESSION_COOKIE_DOMAIN = None  # Use default domain
SESSION_COOKIE_PATH = '/'  # Session cookie available for entire site



# Add RBAC configuration for simplified decorator-based approach
RBAC_CONFIG = {
    'ENABLE_RBAC': True,  # Enable RBAC for proper access control
    'LOG_PERMISSIONS': True,  # Log permission checks for debugging
    'DEBUG_MODE': True,  # Enable detailed debug logging during development
}

# RBAC Decorator Bypass for development
RBAC_DECORATOR_BYPASS = False  # Enable RBAC decorators for proper access control

# Add logging configuration for RBAC - console only, no file logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'grc.rbac': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'  # For collectstatic command

# Additional locations for static files (includes Vue.js dist)
# Only include directories that exist to avoid warnings
STATICFILES_DIRS = []
static_dirs = [
    BASE_DIR.parent / 'frontend' / 'dist' / 'assets',  # Vue.js compiled assets
    BASE_DIR.parent / 'frontend' / 'dist' / 'css',     # Vue.js CSS
    BASE_DIR.parent / 'frontend' / 'dist' / 'js',      # Vue.js JS
]
for static_dir in static_dirs:
    if static_dir.exists():
        STATICFILES_DIRS.append(static_dir)
    else:
        print(f"[INFO] Static directory does not exist (skipped): {static_dir}")

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'MEDIA_ROOT'
TEMP_MEDIA_ROOT = BASE_DIR / 'TEMP_MEDIA_ROOT'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True  # For development only
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8081",  # Vue.js development server
    "http://localhost:8080",  # Alternative Vue.js port
    "http://15.207.108.158:8080",  # AWS deployment frontend (HTTP)
    "http://15.207.108.158:8081",  # AWS deployment frontend alternative (HTTP)
    "https://15.207.108.158:8080",  # AWS deployment frontend (HTTPS)
    "https://15.207.108.158:8081",  # AWS deployment frontend alternative (HTTPS)
    "https://43.205.117.41",  # Deployed frontend URL (HTTPS)
    "http://43.205.117.41",  # Deployed frontend URL
    "http://43.205.117.41:80",  # Deployed frontend URL with port
    "http://43.205.117.41:8080",  # Deployed frontend URL with port
    "http://43.205.117.41:8081",  # Deployed frontend URL with port
]

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8081",  # Vue.js development server
    "http://localhost:8080",  # Alternative Vue.js port
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "http://15.207.108.158:8080",  # AWS deployment frontend (HTTP)
    "http://15.207.108.158:8081",  # AWS deployment frontend alternative (HTTP)
    "https://15.207.108.158:8000",  # AWS backend HTTPS
    "https://15.207.108.158:8080",  # AWS frontend HTTPS
    "https://15.207.108.158:8081",  # AWS frontend alternative HTTPS
    "http://43.205.117.41",  # Deployed frontend URL
    "https://43.205.117.41",  # Deployed frontend URL (HTTPS)
    "http://43.205.117.41:80",  # Deployed frontend URL with port
    "http://43.205.117.41:8080",  # Deployed frontend URL with port
    "http://43.205.117.41:8081",  # Deployed frontend URL with port
]

# Additional CORS settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cookie',  # CRITICAL: Allow cookie header for session authentication
    'set-cookie',  # Allow set-cookie header responses
]

# HTTPS Security Settings
# Note: Set these to True when using valid SSL certificates in production
# For self-signed certificates in development, keep them as False
CSRF_COOKIE_SECURE = False  # Set to True with valid SSL certificates
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access to CSRF token

# Session settings for HTTPS (duplicate - remove if causing issues)
# SESSION_COOKIE_SECURE = False  # Set to True with valid SSL certificates
# SESSION_COOKIE_HTTPONLY = False  # Allow JavaScript access to session cookies
# SESSION_COOKIE_SAMESITE = 'Lax'  # Allow cross-site requests
# SESSION_COOKIE_DOMAIN = None  # Allow all domains in development

# Additional HTTPS security headers (enable in production)
SECURE_SSL_REDIRECT = False  # Set to True to redirect all HTTP to HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # For reverse proxy
SECURE_HSTS_SECONDS = 0  # Set to 31536000 (1 year) in production with HTTPS
SECURE_HSTS_INCLUDE_SUBDOMAINS = False  # Set to True in production
SECURE_HSTS_PRELOAD = False  # Set to True in production

# JWT Settings
JWT_SECRET_KEY = SECRET_KEY
JWT_ACCESS_TOKEN_LIFETIME = 3600  # 1 hour in seconds
JWT_REFRESH_TOKEN_LIFETIME = 604800  # 7 days in seconds

# Rest Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',  # Add token auth as fallback
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Temporarily allow all for testing
    ],
    # Increase throttling and timeout settings
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/day',
        'anon': '500/day',
    },
    # Allow larger request size
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}
# Increase Django's data upload limit for large exports
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB (increased from 10MB)
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Maximum file upload size (for file uploads)
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB (increased from 10MB)
# S3 Microservice settings
S3_MICROSERVICE_URL = 'http://localhost:3000'  # Default URL for S3 microservice

# Report generation settings
REPORTS_DIR = Path(BASE_DIR) / 'Reports'
REPORTS_DIR.mkdir(exist_ok=True)  # Create Reports directory if it doesn't exist


# OpenAI API Configuration

# Licensing toggle: allow disabling external license checks temporarily
LICENSE_CHECK_ENABLED = os.environ.get('LICENSE_CHECK_ENABLED', 'true').lower() == 'true'
# Increase Django's data upload limit for large exports
 
LICENSE_CHECK_ENABLED = False
 
# Ollama configuration
# Ollama configuration
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://13.126.18.17:11434')
# Default timeout (seconds) for Ollama HTTP requests
OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', '600'))
# Default Ollama model to use (must exist on server per /api/tags)
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')

# ===== EMAIL AND NOTIFICATION CONFIGURATION =====

# SMTP Configuration for Gmail
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_EMAIL = 'loukyarao68@gmail.com'
SMTP_PASSWORD = 'vafx kqve dwmj mvjv'

# Gmail Configuration
GMAIL_USER = 'loukyarao68@gmail.com'
GMAIL_APP_PASSWORD = 'vafx kqve dwmj mvjv'

# Email Configuration
DEFAULT_FROM_EMAIL = 'loukyarao68@gmail.com'
DEFAULT_FROM_NAME = 'GRC System'

# Django Email Backend Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'loukyarao68@gmail.com'
EMAIL_HOST_PASSWORD = 'vafx kqve dwmj mvjv'

# WhatsApp API Configuration
WHATSAPP_API_URL = 'https://graph.facebook.com/v21.0/521803094347148/messages'
WHATSAPP_ACCESS_TOKEN = 'EAAZAFlVKZBf1EBOZBVRH0U6RCZAWfJQ79hzPCZCsZAdkQX9o5qcDRG7DZCanC8hoFZBOs7hrvoft0WiXMUXRDKmCfZAl26xLweNmxvkF5YJLwupO5KnbUqzNqj4WKIzq33ZAAFbaoP8z2F5zZCnUxy7MfookTQGRZCqvuzX1P60ZCWoZCr4KDZCyIZA8rX9r9k7jI4okVnEn3CnVNcZBMsSSaFo6RgAiUIcPsOcOy1ABgmEUZD'
WHATSAPP_PHONE_NUMBER_ID = '521803094347148'
WHATSAPP_SENDER_PHONE = '521803094347148'
TEMPLATE_NAME = 'hello_world'

# AWS S3 Configuration
AWS_BUCKET_NAME = "orcashoimages"
AWS_STORAGE_BUCKET_NAME = "orcashoimages"
AWS_ACCESS_KEY_ID = "AKIAUFKKTW4PVLTPXEMC"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = "ap-south-1"
AWS_S3_REGION_NAME = "ap-south-1"

# Microsoft Azure AD Configuration for Sentinel Integration
MICROSOFT_CLIENT_ID= "1d9fdf2e-ebc8-47e0-8e7d-4c4c41b6a616"
MICROSOFT_TENANT_ID= "aa7c8c45-41a3-4453-bc9a-3adfe8ff5fb6"
MICROSOFT_CLIENT_SECRET= "~2N8Q~NvXe1tEmlvG-jkOxYLPuvJazxN4Wwuzbyr"
REDIRECT_URI= "https://api-grc.vardaands.com/auth/sentinel/callback"
MICROSOFT_AUTHORITY = "https://login.microsoftonline.com/common"
MICROSOFT_USER = "likitha.r@vardaanglobal.com"
 
# Azure Sentinel Configuration
AZURE_SUBSCRIPTION_ID= "09160ce8-409e-4692-9dbf-318cfe354664"
AZURE_RESOURCE_GROUP= "riskavaire-rg"
AZURE_WORKSPACE_NAME= "riskavaire-2"

# Jira OAuth Configuration (HTTPS)
JIRA_CLIENT_ID="4P9O14ygMc08yy0BrBNPcTTpNlgjD1UQ"
JIRA_CLIENT_SECRET='ATOAoft2lTbUeJqpcveQQxwWHehH4MUlRGzjAY58TYHXR47tGEJrMW4_kOtsQORMwOqi1CD39C08'
JIRA_REDIRECT_URI='https://api-grc.vardaands.com/api/jira/oauth-callback/'

JIRA_SCOPES='read:jira-user read:jira-work'


DB_HOST = 'mydb.c1womgmu83di.ap-south-1.rds.amazonaws.com'
DB_USER = 'admin'
DB_PASSWORD = 'Vardaan123'
DB_NAME = 'grc2'
# BambooHR OAuth Configuration

 
BAMBOOHR_CLIENT_ID = "developer_portal-12062b68e6fd89aea7d83f9e218805ac6c448de9"
BAMBOOHR_CLIENT_SECRET = "a91f93594c9521800031c3e28719aff266df3922de3690bd0cb4f3aacf5fcb727b1fa3c7111d17da"
 
 
# Toggle between local and deployed environments
USE_LOCAL_DEVELOPMENT = True  # Set to False for production
 
# Frontend URL Configuration - conditional based on environment
if USE_LOCAL_DEVELOPMENT:
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:8080')  # Local development
else:
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://43.205.117.41')  # Deployed
 
 
# Conditional redirect URI based on environment
if USE_LOCAL_DEVELOPMENT:
    BAMBOOHR_REDIRECT_URI = 'http://127.0.0.1:8000/api/bamboohr/oauth-callback/'  # Local development
    BAMBOOHR_FLASK_SERVER_URL = 'http://127.0.0.1:5000'  # Local Flask OAuth server
else:
    BAMBOOHR_REDIRECT_URI = 'https://api-grc.vardaands.com/api/bamboohr/oauth-callback/'  # Deployed
    BAMBOOHR_FLASK_SERVER_URL = 'https://api-grc.vardaands.com'  # Deployed Flask OAuth server
 
BAMBOOHR_SCOPES = 'email openid employee company:info employee:contact employee:job employee:name employee:photo employee_directory'
 
 
 
 

 
# OAuth State Verification (set to 'true' to skip in development)
# WARNING: Only use this in local development! Always verify state in production
SKIP_OAUTH_STATE_VERIFICATION = os.environ.get('SKIP_OAUTH_STATE_VERIFICATION', 'true' if DEBUG else 'false')
 


# Set environment variables so they can be accessed via os.getenv() by notification_service.py
os.environ.setdefault('DB_HOST', DB_HOST)
os.environ.setdefault('DB_USER', DB_USER)
os.environ.setdefault('DB_PASSWORD', DB_PASSWORD)
os.environ.setdefault('DB_NAME', DB_NAME)

os.environ.setdefault('SMTP_SERVER', SMTP_SERVER)
os.environ.setdefault('SMTP_PORT', str(SMTP_PORT))
os.environ.setdefault('SMTP_EMAIL', SMTP_EMAIL)
os.environ.setdefault('SMTP_PASSWORD', SMTP_PASSWORD)

os.environ.setdefault('GMAIL_USER', GMAIL_USER)
os.environ.setdefault('GMAIL_APP_PASSWORD', GMAIL_APP_PASSWORD)

os.environ.setdefault('DEFAULT_FROM_EMAIL', DEFAULT_FROM_EMAIL)
os.environ.setdefault('DEFAULT_FROM_NAME', DEFAULT_FROM_NAME)

os.environ.setdefault('WHATSAPP_PHONE_NUMBER_ID', WHATSAPP_PHONE_NUMBER_ID)
os.environ.setdefault('WHATSAPP_ACCESS_TOKEN', WHATSAPP_ACCESS_TOKEN)
os.environ.setdefault('WHATSAPP_SENDER_PHONE', WHATSAPP_SENDER_PHONE)

os.environ.setdefault('AWS_ACCESS_KEY_ID', AWS_ACCESS_KEY_ID)
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', AWS_SECRET_ACCESS_KEY)
os.environ.setdefault('AWS_STORAGE_BUCKET_NAME', AWS_STORAGE_BUCKET_NAME)
os.environ.setdefault('AWS_S3_REGION_NAME', AWS_S3_REGION_NAME)

os.environ.setdefault('MICROSOFT_CLIENT_ID', MICROSOFT_CLIENT_ID)
os.environ.setdefault('MICROSOFT_CLIENT_SECRET', MICROSOFT_CLIENT_SECRET)
os.environ.setdefault('MICROSOFT_TENANT_ID', MICROSOFT_TENANT_ID)
os.environ.setdefault('MICROSOFT_AUTHORITY', MICROSOFT_AUTHORITY)
os.environ.setdefault('MICROSOFT_USER', MICROSOFT_USER)

os.environ.setdefault('JIRA_CLIENT_ID', JIRA_CLIENT_ID)
os.environ.setdefault('JIRA_CLIENT_SECRET', JIRA_CLIENT_SECRET)
os.environ.setdefault('JIRA_REDIRECT_URI', JIRA_REDIRECT_URI)
os.environ.setdefault('JIRA_SCOPES', JIRA_SCOPES)
os.environ.setdefault('FRONTEND_URL', FRONTEND_URL)

os.environ.setdefault('BAMBOOHR_CLIENT_ID', BAMBOOHR_CLIENT_ID)
os.environ.setdefault('BAMBOOHR_CLIENT_SECRET', BAMBOOHR_CLIENT_SECRET)
os.environ.setdefault('BAMBOOHR_REDIRECT_URI', BAMBOOHR_REDIRECT_URI)
os.environ.setdefault('BAMBOOHR_SCOPES', BAMBOOHR_SCOPES)
os.environ.setdefault('USE_LOCAL_DEVELOPMENT', str(USE_LOCAL_DEVELOPMENT))
os.environ.setdefault('BAMBOOHR_FLASK_SERVER_URL', BAMBOOHR_FLASK_SERVER_URL)
os.environ.setdefault('SKIP_OAUTH_STATE_VERIFICATION', SKIP_OAUTH_STATE_VERIFICATION)
 

# Ollama configuration (fallback)
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://13.126.18.17:11434')
# Default timeout (seconds) for Ollama HTTP requests
OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', '600'))
# Default Ollama model to use (must exist on server per /api/tags)
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')
# AI consistency settings for reproducible results
OLLAMA_TEMPERATURE = float(os.environ.get('OLLAMA_TEMPERATURE', '0.1'))  # Low temperature for consistency
OLLAMA_SEED = int(os.environ.get('OLLAMA_SEED', '42'))  # Fixed seed for reproducibility