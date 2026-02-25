"""
Django settings for vendor_guard_hub project.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

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
    'django_extensions',
    'debug_toolbar',
    'drf_yasg',
    'import_export',
    'simple_history',
    'constance',
    'constance.backends.database',
    'cacheops',
    'django_celery_beat',
    'django_celery_results',
    # 'defender',  # Temporarily disabled due to compatibility issues
    # 'dbbackup',  # Temporarily disabled due to compatibility issues
]

LOCAL_APPS = [
    'core',
    'slas',
    'audits',
    'notifications',
    'quick_access',
    'compliance',
    'bcpdrp',
    'risk_analysis',
    'contract_risk_analysis',
    'mfa_auth',
    'rbac',
    'admin_access',  # Admin Access Control - No RBAC/MFA dependency
    'contracts',
    'audits_contract',
    'rfp',
    'rfp_approval',
    'ocr_app',
    'global_search',
    # 'performance',  # Temporarily disabled due to model conflicts
    # 'analytics',    # Temporarily disabled due to model conflicts
    # 'vendors',      # Temporarily disabled due to model conflicts
    # 'users',        # Temporarily disabled due to model conflicts
]

VENDOR_APPS = [
    'tprm_backend.apps.vendor_core',
    'tprm_backend.apps.vendor_auth',
    'tprm_backend.apps.vendor_risk',
    'tprm_backend.apps.vendor_questionnaire',
    'tprm_backend.apps.vendor_dashboard',
    'tprm_backend.apps.vendor_lifecycle',
    'tprm_backend.apps.vendor_approval',
    'tprm_backend.apps.management',  # Management app for vendor listing
    'risk_analysis_vendor',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS + VENDOR_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # Temporarily disabled for debugging
    # 'middleware.vendor_security.VendorSecurityMiddleware',
    # 'middleware.vendor_input_validation.VendorInputValidationMiddleware',
    # 'middleware.vendor_rate_limiting.VendorRateLimitMiddleware',
    # 'middleware.vendor_access_control.VendorAccessControlMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'rfp.middleware.SecurityHeadersMiddleware',  # RFP security middleware
    # 'defender.middleware.FailedLoginMiddleware',  # Temporarily disabled
    # 'middleware.vendor_logging.VendorLoggingMiddleware',
]

ROOT_URLCONF = 'vendor_guard_hub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR.parent / 'frontend' / 'dist',  # MPA HTML files for RFP
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

WSGI_APPLICATION = 'vendor_guard_hub.wsgi.application'

# Database - Consolidated into single tprm_integration database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='tprm_integration'),
        'USER': config('DB_USER', default='admin'),
        'PASSWORD': config('DB_PASSWORD', default='rootroot'),
        'HOST': config('DB_HOST', default='tprmintegration.c1womgmu83di.ap-south-1.rds.amazonaws.com'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
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
    'rfp': None,
    'rfp_approval': None,
    'ocr_app': None,
}

# Database routing - DISABLED (using single tprm_integration database)
# DATABASE_ROUTERS = [
#     'ocr_app.router.OCRRouter',
#     'vendor_router.VendorDatabaseRouter',
#     'apps.vendor_approval.db_router.VendorApprovalRouter',
#     'slas.router.SLARouter',
#     'compliance.router.ComplianceRouter',
#     'notifications.router.NotificationsRouter',
#     'quick_access.router.QuickAccessRouter',
#     'audits.router.AuditsRouter',
#     'bcpdrp.router.BCPDRPRouter',
#     'risk_analysis.router.RiskAnalysisRouter',
#     'contracts.router.ContractsRouter',
#     'audits_contract.router.AuditsContractRouter',
#     'rfp.router.RFPRouter',
#     'rfp_approval.router.RFPApprovalRouter',
# ]
DATABASE_ROUTERS = []  # All data now in single tprm_integration database

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR.parent / 'frontend' / 'dist',  # RFP frontend assets
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

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
from datetime import timedelta
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
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000,https://grc-tprm.vardaands.com/tprm,,https://grc-tprm.vardaands.com,http://localhost:3000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173', cast=lambda v: [s.strip() for s in v.split(',')])
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

# Cache settings - Using dummy cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Cacheops settings - Disabled for development
# CACHEOPS_REDIS = config('REDIS_URL', default='redis://127.0.0.1:6379/2')
# CACHEOPS_DEFAULTS = {
#     'timeout': 60*15
# }

# Celery settings - Disabled for development
# CELERY_BROKER_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
# CELERY_RESULT_BACKEND = 'django-db'
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = TIME_ZONE

# Email settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='rfp.azure_email_backend.AzureADEmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.office365.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='praharshitha.d@vardaanglobal.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='preethibejadu@gmail.com')

# MFA-specific email configuration (for Gmail)
MFA_EMAIL_BACKEND = config('MFA_EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
MFA_EMAIL_HOST = config('MFA_EMAIL_HOST', default='smtp.gmail.com')
MFA_EMAIL_PORT = config('MFA_EMAIL_PORT', default=587, cast=int)
MFA_EMAIL_USE_TLS = config('MFA_EMAIL_USE_TLS', default=True, cast=bool)
MFA_EMAIL_HOST_USER = config('MFA_EMAIL_HOST_USER', default='preethibejadu@gmail.com')
MFA_EMAIL_HOST_PASSWORD = config('MFA_EMAIL_HOST_PASSWORD', default='lbhm ajjo ejjb slju')
MFA_DEFAULT_FROM_EMAIL = config('MFA_DEFAULT_FROM_EMAIL', default='preethibejadu@gmail.com')

# MFA Settings
MFA_OTP_EXPIRY_MINUTES = config('MFA_OTP_EXPIRY_MINUTES', default=10, cast=int)
MFA_MAX_ATTEMPTS = config('MFA_MAX_ATTEMPTS', default=3, cast=int)

# JWT Settings for MFA
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = config('JWT_EXPIRY_HOURS', default=24, cast=int)
JWT_REFRESH_EXPIRY_DAYS = config('JWT_REFRESH_EXPIRY_DAYS', default=7, cast=int)

# Logging
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
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Debug toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]

# Constance settings
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_CONFIG = {
    'SLA_REVIEW_TIMEOUT_HOURS': (24, 'SLA review timeout in hours'),
    'PERFORMANCE_DATA_RETENTION_DAYS': (365, 'Performance data retention in days'),
    'MAX_FILE_UPLOAD_SIZE_MB': (10, 'Maximum file upload size in MB'),
}

# File upload settings
MAX_UPLOAD_SIZE = config('MAX_UPLOAD_SIZE', default=10*1024*1024, cast=int)  # 10MB

# Custom user model
# AUTH_USER_MODEL = 'users.User'

# Swagger settings
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}

# SQLAlchemy Configuration for Vendor Module
VENDOR_SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{config('DB_USER', default='admin')}:{config('DB_PASSWORD', default='rootroot')}@{config('DB_HOST', default='tprmintegration.c1womgmu83di.ap-south-1.rds.amazonaws.com')}:{config('DB_PORT', default='3306')}/tprm_integration?charset=utf8mb4"

# Custom Vendor Settings
VENDOR_SETTINGS = {
    'ENCRYPTION_KEY': config('VENDOR_ENCRYPTION_KEY', default=''),
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

# Defender Settings (Brute Force Protection)
DEFENDER_REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/1')
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
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
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
            'handlers': ['vendor_file'],
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
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Custom Vendor Settings
VENDOR_SETTINGS = {
    'ENCRYPTION_KEY': config('VENDOR_ENCRYPTION_KEY', default=''),
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

# RFP-specific settings
EXTERNAL_BASE_URL = config('EXTERNAL_BASE_URL', default='http://localhost:8000')

# Frontend URLs
FRONTEND_URL = config('FRONTEND_URL', default='https://grc-tprm.vardaands.com/tprm')
LOGIN_REDIRECT_URL = config('LOGIN_REDIRECT_URL', default='http://localhost:3000/login')
# MFA removed from TPRM vendor experience (single-step login only)
ENABLE_VENDOR_MFA = False

# OCR Configuration
OCR_ENABLED = True
OCR_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
OCR_ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg']
OCR_TESSERACT_CMD = config('TESSERACT_CMD', default='tesseract')  # Path to tesseract executable

# Email configuration for RFP
EMAIL_BACKEND_RFP = 'rfp.azure_email_backend.AzureADEmailBackend'
AZURE_AD_TENANT_ID = config('AZURE_AD_TENANT_ID', default='aa7c8c45-41a3-4453-bc9a-3adfe8ff5fb6')
AZURE_AD_CLIENT_ID = config('AZURE_AD_CLIENT_ID', default='127107b0-7144-4246-b2f4-160263ceb3c9')
AZURE_AD_CLIENT_SECRET = config('AZURE_AD_CLIENT_SECRET', default='sVr8Q~3b0OS~L5NFIaWGomhiGwSwFuNMnW7RPamR')
AZURE_AD_SCOPE = 'https://graph.microsoft.com/.default'
DEFAULT_FROM_EMAIL_RFP = config('DEFAULT_FROM_EMAIL_RFP', default='noreply@vardaanglobal.com')

# Create logs directory
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(BASE_DIR / 'backups', exist_ok=True)