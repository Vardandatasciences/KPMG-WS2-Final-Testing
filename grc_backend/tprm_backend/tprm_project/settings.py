"""
Django settings for tprm_project project.
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-key-for-development-only')

# Encryption key for TPRM data encryption (reuses GRC encryption service)
# This key is used to encrypt/decrypt sensitive data at rest
# Generate a key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
GRC_ENCRYPTION_KEY = os.environ.get('GRC_ENCRYPTION_KEY', None)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,*').split(',')

# External URL for generating invitation links (frontend URL where vendors submit)
# Default to localhost:3000 for frontend, can be overridden via environment variable
# Force localhost (no ngrok) - replace ngrok URLs with localhost
_external_base_url = os.environ.get('EXTERNAL_BASE_URL', 'http://localhost:3000')
if 'ngrok' in _external_base_url.lower():
    EXTERNAL_BASE_URL = 'http://localhost:3000'
else:
    EXTERNAL_BASE_URL = _external_base_url

# Backend API URL for API endpoints (used for tracking URLs)
# Force localhost (no ngrok) - replace ngrok URLs with localhost
_backend_api_url = os.environ.get('BACKEND_API_URL', 'http://localhost:8000')
if 'ngrok' in _backend_api_url.lower():
    BACKEND_API_URL = 'http://localhost:8000'
else:
    BACKEND_API_URL = _backend_api_url

# Silence system checks for shared tables (intentionally sharing tables across modules)
SILENCED_SYSTEM_CHECKS = [
    'models.E028',  # db_table is used by multiple models (intentional for shared tables)
    'models.W042',  # AutoField used without primary_key
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'drf_yasg',
    
    # Local apps
    'rfp',  # RFP app (includes custom runserver command for graceful DB error handling)
    'rfp_approval',
    'rfp_risk_analysis',  # Risk Analysis Module
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'rfp.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'tprm_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR.parent / 'frontend' / 'dist',  # MPA HTML files
        ],
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

WSGI_APPLICATION = 'tprm_project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'tprm_integration'),
        'USER': os.environ.get('DB_USER', 'admin'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'rootroot'),
        'HOST': os.environ.get('DB_HOST', 'tprmintegration.c1womgmu83di.ap-south-1.rds.amazonaws.com'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'connect_timeout': 5,  # 5 second connection timeout
        },
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': False,  # Disable health checks to prevent startup failures
    }
}

# Make database connection optional during startup
# This allows the server to start even if database is unavailable
import os
if os.environ.get('SKIP_DB_CHECK', 'False').lower() == 'true':
    # Skip database connection during startup
    DATABASES['default']['OPTIONS']['init_command'] = None

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Additional static files directories for MPA
STATICFILES_DIRS = [
    # BASE_DIR.parent / 'frontend' / 'dist',  # MPA built files - commented out as directory doesn't exist
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rfp.authentication.CustomJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow unauthenticated access for development
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'NON_FIELD_ERRORS_KEY': 'error',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    },
    'EXCEPTION_HANDLER': 'rfp.utils.custom_exception_handler',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'userid',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8080',
    'http://127.0.0.1:8080',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# For development only
CORS_ALLOW_ALL_ORIGINS = True

# Security settings
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # CSRF settings
    CSRF_COOKIE_HTTPONLY = True
    CSRF_USE_SESSIONS = True
    
    # Session settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Rate limiting
    REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
        'anon': '20/minute',
        'user': '60/minute'
    }

# Email configuration - Azure AD OAuth2 with fallback
EMAIL_BACKEND = 'rfp.azure_email_backend.AzureADEmailBackend'
AZURE_AD_TENANT_ID = os.environ.get('AZURE_AD_TENANT_ID', 'aa7c8c45-41a3-4453-bc9a-3adfe8ff5fb6')
AZURE_AD_CLIENT_ID = os.environ.get('AZURE_AD_CLIENT_ID', '127107b0-7144-4246-b2f4-160263ceb3c9')
AZURE_AD_CLIENT_SECRET = os.environ.get('AZURE_AD_CLIENT_SECRET', 'sVr8Q~3b0OS~L5NFIaWGomhiGwSwFuNMnW7RPamR')
AZURE_AD_SCOPE = 'https://graph.microsoft.com/.default'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'praharshitha.d@vardaanglobal.com')

# Verify Azure AD configuration
print(f"🔧 [DEBUG] Azure AD Configuration:")
print(f"  Tenant ID: {AZURE_AD_TENANT_ID}")
print(f"  Client ID: {AZURE_AD_CLIENT_ID}")
print(f"  Client Secret: {'Set' if AZURE_AD_CLIENT_SECRET else 'Not Set'}")
print(f"  From Email: {DEFAULT_FROM_EMAIL}")
print(f"  Email Backend: {EMAIL_BACKEND}")

# Fallback email configuration for development
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.office365.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'praharshitha.d@vardaanglobal.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Ollama Configuration for Risk Analysis
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
LLAMA_MODEL_NAME = os.environ.get('LLAMA_MODEL_NAME', 'llama3.2:3b')

print(f"🤖 [DEBUG] Ollama Configuration:")
print(f"  Ollama URL: {OLLAMA_URL}")
print(f"  Model Name: {LLAMA_MODEL_NAME}")

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
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
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'rfp': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'rfp_risk_analysis': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}