"""
Django settings for vendor TPRM project with secure coding practices.
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
# Try multiple possible .env file locations
env_files = [
    BASE_DIR.parent / '.env',  # Project root
    BASE_DIR / '.env',  # Backend directory
    BASE_DIR / '(contract).env',  # Contract env file
]

# Load the first .env file that exists
for env_file in env_files:
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[SUCCESS] Loaded environment variables from: {env_file}")
        break

def env_config(key, default=None, cast=None):
    """Simple environment variable getter"""
    value = os.environ.get(key, default)
    if cast and value is not None:
        if cast == bool:
            if isinstance(value, bool):
                return value
            return str(value).lower() in ('true', '1', 'yes', 'on')
        return cast(value)
    return value

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env_config('DJANGO_SECRET_KEY', default='django-insecure-development-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = env_config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    # 'defender',  # Temporarily disabled due to compatibility issues
    # 'dbbackup',  # Temporarily disabled due to compatibility issues
]

LOCAL_APPS = [
    'apps.vendor_core',
    'apps.vendor_auth',
    'apps.vendor_risk',
    'apps.vendor_questionnaire',
    'apps.vendor_dashboard',
    'apps.vendor_lifecycle',
    'apps.vendor_approval',
    'risk_analysis_vendor',
    'rfp',  # Added RFP app
    'rfp_risk_analysis',  # RFP Risk Analysis Module - CRITICAL
    'notifications',  # Notifications app
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'middleware.vendor_security.VendorSecurityMiddleware',
    'middleware.vendor_input_validation.VendorInputValidationMiddleware',
    'middleware.vendor_rate_limiting.VendorRateLimitMiddleware',
    'middleware.vendor_access_control.VendorAccessControlMiddleware',  # Moved before auth middleware
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'defender.middleware.FailedLoginMiddleware',  # Temporarily disabled
    'middleware.vendor_logging.VendorLoggingMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database Configuration with SQLAlchemy
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env_config('DB_NAME', default='tprm_integration'),
        'USER': env_config('DB_USER', default='admin'),
        'PASSWORD': env_config('DB_PASSWORD', default='rootroot'),
        'HOST': env_config('DB_HOST', default='tprmintegration.c1womgmu83di.ap-south-1.rds.amazonaws.com'),
        'PORT': env_config('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'use_unicode': True,
        },
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Silence system checks for shared tables (intentionally sharing tables across modules)
SILENCED_SYSTEM_CHECKS = [
    'models.E028',  # db_table is used by multiple models (intentional for shared tables)
    'models.W042',  # AutoField used without primary_key
]

# Disable Django migrations - use existing database tables
MIGRATION_MODULES = {
    'admin': None,
    'auth': None,
    'contenttypes': None,
    'sessions': None,
    'messages': None,
    'staticfiles': None,
    'rest_framework': None,
    'rest_framework_simplejwt': None,
    'corsheaders': None,
    'django_filters': None,
    'apps.vendor_core': None,
    'apps.vendor_auth': None,
    'apps.vendor_risk': None,
    'apps.vendor_questionnaire': None,
    'apps.vendor_dashboard': None,
    'apps.vendor_lifecycle': None,
    'apps.vendor_approval': None,
    'risk_analysis_vendor': None,
    'notifications': None,
}

# SQLAlchemy Configuration
VENDOR_SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{env_config('DB_USER', default='admin')}:{env_config('DB_PASSWORD', default='rootroot')}@{env_config('DB_HOST', default='tprmintegration.c1womgmu83di.ap-south-1.rds.amazonaws.com')}:{env_config('DB_PORT', default='3306')}/{env_config('DB_NAME', default='tprm_integration')}?charset=utf8mb4"

# Password validation with secure practices
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    # {
    #     'NAME': 'vendor_validators.vendor_password_validator.VendorPasswordValidator',
    # },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# External Base URL for vendor invitations and public-facing URLs
_external_base_url = env_config('EXTERNAL_BASE_URL', default='http://localhost:3000')
if 'ngrok' in _external_base_url.lower():
    EXTERNAL_BASE_URL = 'http://localhost:3000'
else:
    EXTERNAL_BASE_URL = _external_base_url
# Email Configuration
EMAIL_BACKEND = env_config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env_config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env_config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = env_config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = env_config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env_config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env_config('DEFAULT_FROM_EMAIL', default='noreply@example.com')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
    'EXCEPTION_HANDLER': 'utils.vendor_exception_handler.vendor_custom_exception_handler',
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'userid',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1 hour

# CORS Settings
CORS_ALLOWED_ORIGINS = env_config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000,http://localhost:3000,http://localhost:8080,http://127.0.0.1:8080', cast=lambda v: [s.strip() for s in v.split(',')])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True  # For development only
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
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Defender Settings (Brute Force Protection)
DEFENDER_REDIS_URL = env_config('REDIS_URL', default='redis://localhost:6379/1')
DEFENDER_LOGIN_FAILURE_LIMIT = 5
DEFENDER_COOLOFF_TIME = 300  # 5 minutes
DEFENDER_LOCKOUT_TEMPLATE = 'vendor_auth/account_locked.html'

# Backup Settings
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': BASE_DIR / 'backups'}
DBBACKUP_CLEANUP_KEEP = 10
DBBACKUP_CLEANUP_FILTER = lambda: True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'vendor_json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(user_id)s %(ip_address)s %(action)s'
        },
        'vendor_standard': {
            'format': '{levelname} {asctime} {name} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'vendor_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'vendor_tprm.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'vendor_json',
        },
        'vendor_security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'vendor_security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'vendor_json',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'vendor_standard',
        },
    },
    'loggers': {
        'vendor_security': {
            'handlers': ['vendor_security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'vendor_audit': {
            'handlers': ['vendor_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['vendor_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'rfp': {
            'handlers': ['vendor_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'rfp_risk_analysis': {
            'handlers': ['vendor_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Celery Configuration (for async tasks and backups)
CELERY_BROKER_URL = env_config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env_config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Custom Vendor Settings
VENDOR_SETTINGS = {
    'ENCRYPTION_KEY': env_config('VENDOR_ENCRYPTION_KEY', default=''),
    'MAX_FILE_UPLOAD_SIZE': 10 * 1024 * 1024,  # 10MB
    'ALLOWED_FILE_TYPES': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv'],
    'BACKUP_RETENTION_DAYS': 30,
    'SESSION_TIMEOUT_MINUTES': 60,
    'MAX_LOGIN_ATTEMPTS': 5,
    'PASSWORD_EXPIRY_DAYS': 90,
}

# LLaMA/Ollama Configuration for Risk Analysis
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
LLAMA_MODEL_NAME = os.getenv('LLAMA_MODEL_NAME', 'llama3.2:3b')

# Print Ollama configuration on startup
print(f"🤖 [OLLAMA CONFIG] URL: {OLLAMA_URL}, Model: {LLAMA_MODEL_NAME}")

# Create logs directory
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(BASE_DIR / 'backups', exist_ok=True)
