"""
Configuration settings for KPI Generator
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
# Prefer .env / environment variables first, then fall back to Django settings.
_env_openai_api_key = os.environ.get('OPENAI_API_KEY')
_env_openai_model = os.environ.get('OPENAI_MODEL')

if _env_openai_api_key or _env_openai_model:
    OPENAI_API_KEY = _env_openai_api_key or ''
    OPENAI_MODEL = _env_openai_model or 'gpt-4'
else:
    try:
        from backend.settings import OPENAI_API_KEY as _settings_openai_api_key, OPENAI_MODEL as _settings_openai_model  # type: ignore
        OPENAI_API_KEY = _settings_openai_api_key
        OPENAI_MODEL = _settings_openai_model
    except Exception:
        OPENAI_API_KEY = ''
        OPENAI_MODEL = 'gpt-4'

MAX_TOKENS = 16384
DEFAULT_PREDICT_TOKENS = 16384
MAX_RETRIES = 3
TEMPERATURE = 0.3

# Database Configuration
# Prefer .env / environment variables first, then fall back to Django settings.
_env_db_host = os.environ.get('DB_HOST')
_env_db_port = os.environ.get('DB_PORT')
_env_db_name = os.environ.get('DB_NAME')
_env_db_user = os.environ.get('DB_USER')
_env_db_password = os.environ.get('DB_PASSWORD')

if all([_env_db_host, _env_db_port, _env_db_name, _env_db_user]):
    DB_CONFIG = {
        'host': _env_db_host,
        'port': int(_env_db_port),
        'database': _env_db_name,
        'user': _env_db_user,
        'password': _env_db_password or '',
    }
else:
    try:
        from backend.settings import DATABASES  # type: ignore

        _DB_SETTINGS = DATABASES.get("default", {})
        DB_CONFIG = {
            'host': _DB_SETTINGS.get('HOST') or 'localhost',
            'port': int(_DB_SETTINGS.get('PORT') or 3306),
            'database': _DB_SETTINGS.get('NAME') or 'grc2',
            'user': _DB_SETTINGS.get('USER') or 'root',
            'password': _DB_SETTINGS.get('PASSWORD') or '',
        }
    except Exception:
        DB_CONFIG = {
            'host': _env_db_host or 'localhost',
            'port': int(_env_db_port or '3306'),
            'database': _env_db_name or 'grc2',
            'user': _env_db_user or 'root',
            'password': _env_db_password or '',
        }

S3_CONFIG = {
    'aws_access_key_id': 'AKIAW76SPJ4WJPMFJNNX',
    'aws_secret_access_key': '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',
    'region_name': 'ap-south-1'
}
TARGET_S3_BUCKET = os.environ.get("SYNTHETIC_S3_BUCKET", "kpistestingwithai")

# Framework ID to process (default, can be overridden by command-line argument)
FRAMEWORK_ID = 336

# Output directoryolikuj
OUTPUT_DIR = Path("excel_output_enhanced_NEW")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Cache files
S3_CACHE_FILE = OUTPUT_DIR / "s3_documents_cache.json"
OUTPUT_FILE = OUTPUT_DIR / "KPIs2.xlsx"
S3_CHUNK_CACHE_FILE = OUTPUT_DIR / "s3_chunk_cache.json"

# S3 document processing limit
DEFAULT_MAX_S3_DOCUMENTS = int(os.environ.get("MAX_S3_DOCUMENTS", "5"))

# Global caches for schema and staging metadata
CURRENT_SCHEMA_INFO = {}
EVIDENCE_DATAFRAMES = {}

# Feature flags for optional dependencies
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    print("[WARNING] boto3 not installed. S3 document analysis will be skipped.")
    print("[INFO] Install with: pip install boto3")
    BOTO3_AVAILABLE = False
    boto3 = None

try:
    from json_repair import repair_json
    JSON_REPAIR_AVAILABLE = True
except ImportError:
    JSON_REPAIR_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    print("[ERROR] requests library not installed. Install with: pip install requests")
    REQUESTS_AVAILABLE = False

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARNING] OpenAI SDK not installed. Install with: pip install openai langchain")

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    FPDF = None

# Global model instances
OPENAI_CLIENT = None
TEXT_SPLITTER = None
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI embedding model

