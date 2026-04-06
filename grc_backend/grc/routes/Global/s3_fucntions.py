
#!/usr/bin/env python3
"""
S3 Microservice Client for Direct Deployment with MySQL Database
Direct URL: http://15.207.1.40:3000
MySQL Database for operation trftg6hy7uracking (uses Django settings)
No AWS credentials required - handled by the microservice

================================================================================
ENHANCED PDF PROCESSING FEATURE
================================================================================

Automatic PDF processing after successful upload to S3:

1. SMART TEXT EXTRACTION (Cost & Time Optimized)
   - Small documents (1-5 pages): Extract ALL pages
   - Medium documents (6-20 pages): Extract first 5, last 1, and 2 middle pages
   - Large documents (20+ pages): Extract first 3, last 1, and 3 strategic samples
   
2. COMPREHENSIVE METADATA EXTRACTION
   - Core metadata: title, author, subject, keywords
   - Technical metadata: creator, producer, PDF version, encryption status
   - Document info: page count, file size (bytes/KB/MB), creation date
   - Processing info: extraction strategy, processing timestamp
   - Auto-categorization: policy, audit, risk, incident, or general

3. AI-POWERED SUMMARY GENERATION
   - Uses OpenAI GPT-3.5-turbo for intelligent summarization
   - Small documents: Detailed summary with key points
   - Medium documents: Structured summary with main sections
   - Large documents: High-level overview with critical highlights
   - All summaries limited to max 10 lines
   - Fallback handling if OpenAI unavailable or fails

4. DATABASE INTEGRATION
   - Saves metadata JSON to file_operations.metadata column
   - Saves AI summary to file_operations.summary column (max 2000 chars)
   - Updates status to 'completed' or 'failed'
   - Records processing timestamps and AI model used
   
5. BACKGROUND PROCESSING
   - Runs in separate thread - non-blocking
   - Upload returns immediately
   - Processing happens asynchronously
   - Check status with get_pdf_processing_status(operation_id)

USAGE:
    # Upload triggers automatic processing for PDFs
    result = client.upload(
        file_path='/path/to/document.pdf',
        user_id='user123',
        module='policy'
    )
    
    if result['success']:
        operation_id = result['operation_id']
        # PDF processing started in background
        
        # Later, check processing status
        status = client.get_pdf_processing_status(operation_id)
        if status['status'] == 'completed':
            metadata = status['metadata']
            summary = status['summary']

REQUIREMENTS:
    - PyPDF2 or pdfplumber for PDF text extraction
    - OpenAI library with configured API key in Django settings
    - MySQL database with file_operations table
    
ERROR HANDLING:
    - Graceful fallback if libraries not available
    - Detailed error logging for debugging
    - Partial results saved even if processing fails
    
================================================================================
"""

import requests
import os
import json
import re
import ipaddress
import socket
from urllib.parse import urlparse
from ...debug_utils import debug_print
from ...utils.csv_security import sanitize_csv_dataset, sanitize_export_filename
import mimetypes
from typing import Dict, List, Optional, Union, Any
import datetime
import mysql.connector
from mysql.connector import pooling
import threading
import tempfile
import io
from io import BytesIO

# Export libraries
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import xmltodict
    XMLTODICT_AVAILABLE = True
except ImportError:
    XMLTODICT_AVAILABLE = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# PDF Processing libraries
try:
    import PyPDF2
    PDF_LIBRARY_AVAILABLE = True
except ImportError:
    PDF_LIBRARY_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# OpenAI library
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Ollama configuration
OLLAMA_BASE_URL = "http://13.205.15.232:11434"
OLLAMA_MODEL = "llama3:8b-instruct-q4_K_M"
OLLAMA_AVAILABLE = True  # Assume available if server is running

# Import Django settings for database configuration
try:
    from django.conf import settings
    DJANGO_SETTINGS_AVAILABLE = True
except ImportError:
    DJANGO_SETTINGS_AVAILABLE = False
    settings = None

# Shared export payload limits (DoS guardrails)
EXPORT_MAX_DATA_BYTES = 40 * 1024 * 1024
EXPORT_MAX_RECORDS = 10_000
EXPORT_MAX_NESTED_DEPTH = 8
EXPORT_MAX_DICT_KEYS = 300
EXPORT_MAX_LIST_ITEMS = 10_000
EXPORT_MAX_STRING_LEN = 10_000
TEMPLATE_TOKEN_RE = re.compile(r"(\{\{|\}\}|\{\%|\%\}|\{\#|\#\})")
URL_CANDIDATE_RE = re.compile(r"(?i)\b(?:https?|ftp|file|gopher|dict|ldap|ldaps|smb|sftp)://[^\s<>'\"]+")
SCRIPT_URL_RE = re.compile(r"(?i)\b(?:javascript|data|vbscript):")

def _normalize_domain_entries(raw_values: Any) -> set:
    """Normalize allowlist entries from settings/env into a lowercase set."""
    if raw_values is None:
        return set()
    if isinstance(raw_values, str):
        raw_values = [item.strip() for item in raw_values.split(",")]
    if not isinstance(raw_values, (list, tuple, set)):
        return set()
    normalized = set()
    for item in raw_values:
        if item is None:
            continue
        value = str(item).strip().lower()
        if value:
            normalized.add(value.lstrip("."))
    return normalized

def _get_export_allowed_domains() -> set:
    """
    Resolve export URL allowlist from settings/env.
    Priority:
      1) EXPORT_ALLOWED_DOMAINS
      2) OUTBOUND_ALLOWED_DOMAINS
      3) TRUSTED_EVIDENCE_URL_HOSTS / TRUSTED_EVIDENCE_URL_HOST_SUFFIXES
    """
    domain_values: List[Any] = []

    settings_obj = settings if DJANGO_SETTINGS_AVAILABLE else None
    if settings_obj is not None:
        domain_values.extend([
            getattr(settings_obj, "EXPORT_ALLOWED_DOMAINS", None),
            getattr(settings_obj, "OUTBOUND_ALLOWED_DOMAINS", None),
            getattr(settings_obj, "TRUSTED_EVIDENCE_URL_HOSTS", None),
            getattr(settings_obj, "TRUSTED_EVIDENCE_URL_HOST_SUFFIXES", None),
        ])

    domain_values.extend([
        os.environ.get("EXPORT_ALLOWED_DOMAINS"),
        os.environ.get("OUTBOUND_ALLOWED_DOMAINS"),
    ])

    allowed: set = set()
    for entry in domain_values:
        allowed.update(_normalize_domain_entries(entry))
    return allowed

def _host_matches_allowlist(hostname: str, allowed_domains: set) -> bool:
    """Check exact/suffix host match against allowlist domains."""
    if not hostname:
        return False
    host = hostname.strip().lower().rstrip(".")
    if not host:
        return False
    if host in allowed_domains:
        return True
    for domain in allowed_domains:
        if host.endswith(f".{domain}"):
            return True
    return False

def _is_private_or_internal_host(hostname: str) -> bool:
    """Return True if hostname resolves to internal/private/link-local/loopback."""
    if not hostname:
        return True

    host = hostname.strip().lower()
    if host in {"localhost", "localhost.localdomain"}:
        return True

    try:
        ip_obj = ipaddress.ip_address(host)
        return (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        )
    except ValueError:
        pass

    try:
        resolved = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except Exception:
        # Fail closed for unknown/unresolvable hosts.
        return True

    for entry in resolved:
        try:
            addr = entry[4][0]
            ip_obj = ipaddress.ip_address(addr)
            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_multicast
                or ip_obj.is_reserved
                or ip_obj.is_unspecified
            ):
                return True
        except Exception:
            return True

    return False

def _sanitize_potential_urls(text: str) -> str:
    """Neutralize risky URL/script patterns to reduce SSRF risk during exports."""
    if not text:
        return text

    sanitized = SCRIPT_URL_RE.sub("[blocked-uri]:", text)
    allowed_domains = _get_export_allowed_domains()

    def _replace_match(match):
        raw_url = match.group(0)
        try:
            parsed = urlparse(raw_url)
            host = parsed.hostname
            if parsed.scheme.lower() not in {"http", "https"}:
                return "[blocked-url]"
            if _is_private_or_internal_host(host):
                return "[blocked-url]"
            # If allowlist is configured, permit only listed domains.
            if allowed_domains and not _host_matches_allowlist(host, allowed_domains):
                return "[blocked-url]"
            return raw_url
        except Exception:
            return "[blocked-url]"

    return URL_CANDIDATE_RE.sub(_replace_match, sanitized)

def _sanitize_export_scalar(value):
    """Sanitize scalar values before export rendering."""
    if value is None:
        return ""
    if isinstance(value, (bool, int, float)):
        return value
    text = str(value).replace("\x00", "")
    text = TEMPLATE_TOKEN_RE.sub("", text)
    text = _sanitize_potential_urls(text)
    if len(text) > EXPORT_MAX_STRING_LEN:
        text = text[:EXPORT_MAX_STRING_LEN]
    return text

def _sanitize_export_payload(value, depth=0):
    """Recursively sanitize payload and enforce structural limits."""
    if depth > EXPORT_MAX_NESTED_DEPTH:
        raise ValueError("Export payload too deeply nested")

    if isinstance(value, dict):
        if len(value) > EXPORT_MAX_DICT_KEYS:
            raise ValueError("Export payload object has too many keys")
        sanitized = {}
        for key, nested_value in value.items():
            safe_key = _sanitize_export_scalar(key)
            sanitized[safe_key] = _sanitize_export_payload(nested_value, depth + 1)
        return sanitized

    if isinstance(value, list):
        if len(value) > EXPORT_MAX_LIST_ITEMS:
            raise ValueError("Export payload list has too many items")
        return [_sanitize_export_payload(item, depth + 1) for item in value]

    return _sanitize_export_scalar(value)

def convert_safe_string(value):
    """Convert Django SafeString objects to regular strings for MySQL compatibility"""
    if value is None:
        return None
    
    # Import Django's SafeString to check instance
    try:
        from django.utils.safestring import SafeString
        if isinstance(value, SafeString):
            return str(value)
    except ImportError:
        pass
    
    # Handle HTML escaped strings
    if hasattr(value, '__html__'):
        return str(value)
    
    # Handle Django SafeString specifically
    if hasattr(value, 'mark_safe'):
        return str(value)
    
    # Handle other types that might cause issues
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    
    # Convert any object to string, ensuring it's a regular Python string
    return str(value)

class RenderS3Client:
    """
    Python client for S3 microservice deployed on Direct
    With local MySQL database for operation tracking
    AWS credentials are handled by the microservice itself
    """
    
    def __init__(self, 
                 api_base_url: str = "http://15.207.1.40:3000",
                 mysql_config: Optional[Dict] = None):
        """
        Initialize the Direct S3 client with local MySQL
        
        Args:
            api_base_url: Your Direct deployment URL
            mysql_config: MySQL database configuration (optional)
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.db_pool = None
        
        # Initialize MySQL connection if config provided
        if mysql_config:
            self._setup_mysql_database(mysql_config)
        else:
            self._setup_default_mysql()
    
    def _setup_default_mysql(self):
        """Setup MySQL using Django settings configuration"""
        try:
            # Try to get database config from Django settings
            if DJANGO_SETTINGS_AVAILABLE and hasattr(settings, 'DATABASES'):
                db_config = settings.DATABASES.get('default', {})
                
                mysql_config = {
                    'host': db_config.get('HOST', 'localhost'),
                    'user': db_config.get('USER', 'root'),
                    'password': db_config.get('PASSWORD', 'root'),
                    'database': db_config.get('NAME', 'grc'),
                    'port': int(db_config.get('PORT', 3306)),
                    'autocommit': True,
                    'charset': 'utf8mb4',
                    'collation': 'utf8mb4_unicode_ci'
                }
                
                debug_print(f"🔧 Using Django settings for MySQL: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
            else:
                # Fallback to environment variables if Django settings not available
                mysql_config = {
                    'host': os.environ.get('DB_HOST', 'localhost'),
                    'user': os.environ.get('DB_USER', 'root'),
                    'password': os.environ.get('DB_PASSWORD', 'root'),
                    'database': os.environ.get('DB_NAME', 'grc'),
                    'port': int(os.environ.get('DB_PORT', 3306)),
                    'autocommit': True,
                    'charset': 'utf8mb4',
                    'collation': 'utf8mb4_unicode_ci'
                }
                
                debug_print(f"⚠️  Django settings not available, using environment variables")
            
            self._setup_mysql_database(mysql_config)
            
        except Exception as e:
            debug_print(f"ERROR MySQL setup failed: {str(e)}")
            self.db_pool = None
    
    def _setup_mysql_database(self, mysql_config: Dict):
        """Setup MySQL connection pool"""
        try:
            # Test connection first
            test_conn = mysql.connector.connect(**mysql_config)
            test_conn.close()
            
            # Create connection pool
            self.db_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="render_s3_pool",
                pool_size=5,
                pool_reset_session=True,
                **mysql_config
            )
            
            debug_print("SUCCESS MySQL connection pool initialized successfully")
            
            # Create table if it doesn't exist
            self._create_table_if_not_exists()
            
        except mysql.connector.Error as e:
            debug_print(f"ERROR MySQL connection failed: {str(e)}")
            debug_print("💡 Make sure MySQL is running and credentials are correct")
            self.db_pool = None
        except Exception as e:
            debug_print(f"ERROR Database setup error: {str(e)}")
            self.db_pool = None
    
    def _create_table_if_not_exists(self):
        """Create the file_operations table if it doesn't exist"""
        if not self.db_pool:
            return
        
        conn = self._get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        try:
            # Create unified file_operations table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS file_operations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                operation_type ENUM('upload', 'download', 'export') NOT NULL,
                module VARCHAR(45) NULL,
                user_id VARCHAR(255) NOT NULL,
                file_name VARCHAR(500) NOT NULL,
                original_name VARCHAR(500),
                stored_name VARCHAR(500),
                s3_url TEXT,
                s3_key VARCHAR(1000),
                s3_bucket VARCHAR(255),
                file_type VARCHAR(50),
                file_size BIGINT,
                content_type VARCHAR(255),
                export_format VARCHAR(20),
                record_count INT,
                status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
                error TEXT,
                metadata JSON,
                platform VARCHAR(50) DEFAULT 'Render',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                
                INDEX idx_user_id (user_id),
                INDEX idx_operation_type (operation_type),
                INDEX idx_module (module),
                INDEX idx_status (status),
                INDEX idx_created_at (created_at),
                INDEX idx_file_type (file_type),
                INDEX idx_platform (platform),
                INDEX idx_s3_key (s3_key(255))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_table_query)
            conn.commit()
            debug_print("SUCCESS Database table verified/created successfully")
            
        except mysql.connector.Error as e:
            debug_print(f"ERROR Table creation error: {str(e)}")
        except Exception as e:
            debug_print(f"ERROR Unexpected error creating table: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    

    
    def _get_db_connection(self):
        """Get database connection from pool"""
        if not self.db_pool:
            return None
        
        try:
            return self.db_pool.get_connection()
        except Exception as e:
            debug_print(f"ERROR Failed to get DB connection: {str(e)}")
            return None
    
    def _save_operation_record(self, operation_type: str, operation_data: Dict) -> Optional[int]:
        """Save operation record to MySQL database"""
        if not self.db_pool:
            return None
        
        conn = self._get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        try:
            query = """
            INSERT INTO file_operations 
            (operation_type, user_id, file_name, original_name, stored_name, s3_url, s3_key, s3_bucket,
             file_type, file_size, content_type, export_format, record_count, status, metadata, platform,
             module, FrameworkId, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            now = datetime.datetime.now()
            
            params = (
                operation_type,
                convert_safe_string(operation_data.get('user_id')),
                convert_safe_string(operation_data.get('file_name')),
                convert_safe_string(operation_data.get('original_name')),
                convert_safe_string(operation_data.get('stored_name')),
                convert_safe_string(operation_data.get('s3_url', '')),
                convert_safe_string(operation_data.get('s3_key', '')),
                convert_safe_string(operation_data.get('s3_bucket', '')),
                convert_safe_string(operation_data.get('file_type')),
                operation_data.get('file_size'),
                convert_safe_string(operation_data.get('content_type')),
                convert_safe_string(operation_data.get('export_format')),
                operation_data.get('record_count'),
                convert_safe_string(operation_data.get('status', 'pending')),
                json.dumps(operation_data.get('metadata', {})),
                'Direct',
                convert_safe_string(operation_data.get('module', 'general')),
                operation_data.get('framework_id'),  # FrameworkId
                now,
                now
            )
            
            cursor.execute(query, params)
            conn.commit()
            operation_id = cursor.lastrowid
            
            debug_print(f"📝 Operation recorded in MySQL: ID {operation_id}")
            return operation_id
            
        except mysql.connector.Error as e:
            debug_print(f"ERROR MySQL save error: {str(e)}")
            return None
        except Exception as e:
            debug_print(f"ERROR Database save error: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def _update_operation_record(self, operation_id: int, operation_data: Dict):
        """Update operation record with complete information"""
        if not self.db_pool or not operation_id:
            return
        
        conn = self._get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        try:
            # Build dynamic update query
            update_fields = []
            update_values = []
            
            field_mapping = {
                'stored_name': 'stored_name',
                's3_url': 's3_url', 
                's3_key': 's3_key',
                's3_bucket': 's3_bucket',
                'file_type': 'file_type',
                'file_size': 'file_size',
                'content_type': 'content_type',
                'export_format': 'export_format',
                'record_count': 'record_count',
                'status': 'status',
                'error': 'error'
            }
            
            for key, db_field in field_mapping.items():
                if key in operation_data:
                    update_fields.append(f"{db_field} = %s")
                    # Convert SafeString objects to regular strings for MySQL compatibility
                    value = operation_data[key]
                    if key in ['stored_name', 's3_url', 's3_key', 's3_bucket', 'file_type', 'content_type', 'export_format', 'status', 'error']:
                        value = convert_safe_string(value)
                    update_values.append(value)
            
            # Always update metadata and timestamp
            if 'metadata' in operation_data:
                update_fields.append("metadata = %s")
                update_values.append(json.dumps(operation_data['metadata']))
            
            update_fields.append("updated_at = %s")
            update_values.append(datetime.datetime.now())
            
            # Add completed_at if status is completed
            if operation_data.get('status') == 'completed':
                update_fields.append("completed_at = %s")
                update_values.append(datetime.datetime.now())
            
            # Add operation_id at the end
            update_values.append(operation_id)
            
            query = f"UPDATE file_operations SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, update_values)
            conn.commit()
            
            debug_print(f"📝 Operation {operation_id} updated in MySQL")
            
        except mysql.connector.Error as e:
            debug_print(f"ERROR MySQL update error: {str(e)}")
        except Exception as e:
            debug_print(f"ERROR Database update error: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    def _extract_text_from_pdf(self, pdf_content: bytes, smart_extract: bool = True) -> tuple:
        """
        Extract text from PDF bytes using available PDF libraries
        Returns: (text, page_count, extraction_strategy)
        
        Smart extraction logic:
        - Small docs (1-5 pages): Extract all pages
        - Medium docs (6-20 pages): Extract first 5, last 1, and sample 2 from middle
        - Large docs (20+ pages): Extract first 3, last 1, and sample 3 from throughout
        """
        text = ""
        total_pages = 0
        extraction_strategy = "full"
        
        try:
            # Determine total pages first
            if PDFPLUMBER_AVAILABLE:
                with io.BytesIO(pdf_content) as pdf_buffer:
                    with pdfplumber.open(pdf_buffer) as pdf:
                        total_pages = len(pdf.pages)
                        
                        # Determine extraction strategy based on document size
                        if total_pages <= 5:
                            # Small document - extract all pages
                            pages_to_extract = list(range(total_pages))
                            extraction_strategy = "full"
                            debug_print(f"📄 Small document ({total_pages} pages) - extracting all pages")
                        elif total_pages <= 20:
                            # Medium document - extract first 5, last 1, and 2 from middle
                            middle_start = total_pages // 3
                            middle_end = 2 * total_pages // 3
                            pages_to_extract = [0, 1, 2, 3, 4, middle_start, middle_end, total_pages - 1]
                            pages_to_extract = sorted(list(set([p for p in pages_to_extract if p < total_pages])))
                            extraction_strategy = "medium"
                            debug_print(f"📄 Medium document ({total_pages} pages) - extracting {len(pages_to_extract)} pages")
                        else:
                            # Large document - extract first 3, last 1, and 3 from throughout
                            sample_indices = [
                                0, 1, 2,  # First 3 pages
                                total_pages // 4,  # 25% mark
                                total_pages // 2,  # 50% mark
                                3 * total_pages // 4,  # 75% mark
                                total_pages - 1  # Last page
                            ]
                            pages_to_extract = sorted(list(set([p for p in sample_indices if p < total_pages])))
                            extraction_strategy = "large_sample"
                            debug_print(f"📄 Large document ({total_pages} pages) - extracting {len(pages_to_extract)} key pages")
                        
                        # Extract text from selected pages
                        for page_num in pages_to_extract:
                            try:
                                page = pdf.pages[page_num]
                                page_text = page.extract_text()
                                if page_text:
                                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                            except Exception as page_error:
                                debug_print(f"⚠️  Error extracting page {page_num + 1}: {str(page_error)}")
                        
                        debug_print(f"✅ Extracted text from {len(pages_to_extract)} pages using pdfplumber")
            
            # Fallback to PyPDF2
            elif PDF_LIBRARY_AVAILABLE:
                pdf_buffer = io.BytesIO(pdf_content)
                pdf_reader = PyPDF2.PdfReader(pdf_buffer)
                total_pages = len(pdf_reader.pages)
                
                # Same extraction strategy
                if total_pages <= 5:
                    pages_to_extract = list(range(total_pages))
                    extraction_strategy = "full"
                elif total_pages <= 20:
                    middle_start = total_pages // 3
                    middle_end = 2 * total_pages // 3
                    pages_to_extract = [0, 1, 2, 3, 4, middle_start, middle_end, total_pages - 1]
                    pages_to_extract = sorted(list(set([p for p in pages_to_extract if p < total_pages])))
                    extraction_strategy = "medium"
                else:
                    sample_indices = [0, 1, 2, total_pages // 4, total_pages // 2, 3 * total_pages // 4, total_pages - 1]
                    pages_to_extract = sorted(list(set([p for p in sample_indices if p < total_pages])))
                    extraction_strategy = "large_sample"
                
                for page_num in pages_to_extract:
                    try:
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as page_error:
                        debug_print(f"⚠️  Error extracting page {page_num + 1}: {str(page_error)}")
                
                debug_print(f"✅ Extracted text from {len(pages_to_extract)} pages using PyPDF2")
            
            else:
                debug_print("⚠️  No PDF library available for text extraction")
                return "", 0, "none"
            
            # Limit text length to avoid token limits (approximately 4000 words for safety)
            words = text.split()
            if len(words) > 4000:
                text = ' '.join(words[:4000]) + "\n\n... [Content truncated to fit within processing limits]"
                debug_print(f"📄 Text truncated to 4000 words for processing")
            
            return text.strip(), total_pages, extraction_strategy
            
        except Exception as e:
            debug_print(f"ERROR Failed to extract text from PDF: {str(e)}")
            return "", 0, "error"
    
    def _extract_pdf_metadata(self, pdf_content: bytes, file_name: str, total_pages: int = None, extraction_strategy: str = None) -> Dict:
        """
        Extract comprehensive metadata from PDF
        
        Metadata includes:
        - Basic info: title, author, subject, keywords
        - Technical info: creator, producer, PDF version
        - Document info: page count, file size, creation/modification dates
        - Processing info: extraction strategy, text density
        """
        metadata = {
            'document_name': file_name,
            'file_type': 'PDF',
            'processing_timestamp': datetime.datetime.now().isoformat()
        }
        
        try:
            # Use PyPDF2 to extract PDF metadata
            if PDF_LIBRARY_AVAILABLE:
                pdf_buffer = io.BytesIO(pdf_content)
                pdf_reader = PyPDF2.PdfReader(pdf_buffer)
                
                # Get basic PDF info
                page_count = total_pages or len(pdf_reader.pages)
                metadata['page_count'] = page_count
                
                # Categorize document size
                if page_count <= 5:
                    metadata['document_size_category'] = 'small'
                elif page_count <= 20:
                    metadata['document_size_category'] = 'medium'
                else:
                    metadata['document_size_category'] = 'large'
                
                # Get PDF metadata if available
                if pdf_reader.metadata:
                    pdf_meta = pdf_reader.metadata
                    
                    # Core metadata
                    if pdf_meta.title:
                        metadata['title'] = str(pdf_meta.title)
                    if pdf_meta.author:
                        metadata['author'] = str(pdf_meta.author)
                    if pdf_meta.subject:
                        metadata['subject'] = str(pdf_meta.subject)
                    if hasattr(pdf_meta, 'keywords') and pdf_meta.keywords:
                        metadata['keywords'] = str(pdf_meta.keywords)
                    
                    # Technical metadata
                    if pdf_meta.creator:
                        metadata['creator_application'] = str(pdf_meta.creator)
                    if pdf_meta.producer:
                        metadata['pdf_producer'] = str(pdf_meta.producer)
                    
                    # Date metadata
                    if pdf_meta.creation_date:
                        metadata['creation_date'] = str(pdf_meta.creation_date)
                    if hasattr(pdf_meta, 'modification_date') and pdf_meta.modification_date:
                        metadata['modification_date'] = str(pdf_meta.modification_date)
                
                # Get PDF version
                if hasattr(pdf_reader, 'pdf_header'):
                    metadata['pdf_version'] = pdf_reader.pdf_header
                
                # Check if encrypted
                metadata['is_encrypted'] = pdf_reader.is_encrypted
                
                debug_print(f"📋 Extracted comprehensive metadata: {page_count} pages, {metadata.get('document_size_category', 'unknown')} document")
            
            elif PDFPLUMBER_AVAILABLE:
                with io.BytesIO(pdf_content) as pdf_buffer:
                    with pdfplumber.open(pdf_buffer) as pdf:
                        page_count = total_pages or len(pdf.pages)
                        metadata['page_count'] = page_count
                        
                        # Categorize document size
                        if page_count <= 5:
                            metadata['document_size_category'] = 'small'
                        elif page_count <= 20:
                            metadata['document_size_category'] = 'medium'
                        else:
                            metadata['document_size_category'] = 'large'
                        
                        # Extract metadata from pdfplumber
                        if pdf.metadata:
                            for key, value in pdf.metadata.items():
                                if value and key not in metadata:
                                    metadata[key] = str(value)
                
                debug_print(f"📋 Extracted metadata: {page_count} pages")
            
            # Add file size information
            metadata['file_size_bytes'] = len(pdf_content)
            metadata['file_size_kb'] = round(len(pdf_content) / 1024, 2)
            metadata['file_size_mb'] = round(len(pdf_content) / (1024 * 1024), 2)
            
            # Add extraction strategy info
            if extraction_strategy:
                metadata['extraction_strategy'] = extraction_strategy
                metadata['full_text_extracted'] = (extraction_strategy == 'full')
            
            # Use filename as title if title not found
            if 'title' not in metadata:
                metadata['title'] = os.path.splitext(file_name)[0].replace('_', ' ').title()
            
            # Add document classification hints
            file_name_lower = file_name.lower()
            if any(term in file_name_lower for term in ['policy', 'policies']):
                metadata['suggested_category'] = 'policy'
            elif any(term in file_name_lower for term in ['audit', 'compliance', 'finding']):
                metadata['suggested_category'] = 'audit'
            elif any(term in file_name_lower for term in ['risk', 'assessment']):
                metadata['suggested_category'] = 'risk'
            elif any(term in file_name_lower for term in ['incident', 'report']):
                metadata['suggested_category'] = 'incident'
            else:
                metadata['suggested_category'] = 'general'
            
            return metadata
            
        except Exception as e:
            debug_print(f"ERROR Failed to extract PDF metadata: {str(e)}")
            return metadata
    
    def _generate_summary_with_ollama(self, text: str, metadata: Dict) -> str:
        """
        Generate an intelligent summary of the document using Ollama
        
        Summary approach:
        - Small documents (1-5 pages): Detailed summary with key points
        - Medium documents (6-20 pages): Structured summary with main sections
        - Large documents (20+ pages): High-level overview with critical highlights
        
        All summaries limited to maximum 10 lines for consistency
        """
        
        if not OLLAMA_AVAILABLE:
            debug_print("⚠️  Ollama not available")
            return "Summary unavailable: Ollama server not available"
        
        try:
            
            # Determine document size and extraction strategy
            page_count = metadata.get('page_count', 0)
            doc_size = metadata.get('document_size_category', 'unknown')
            extraction_strategy = metadata.get('extraction_strategy', 'unknown')
            full_text = metadata.get('full_text_extracted', False)
            
            # Create context-aware prompt based on document size
            if doc_size == 'small':
                summary_instruction = """Provide a comprehensive summary that includes:
1. Main purpose and subject of the document
2. Key points and important details
3. Notable findings or recommendations
4. Target audience or intended use
Maximum 10 lines."""
            elif doc_size == 'medium':
                summary_instruction = """Provide a structured summary that includes:
1. Document overview and main purpose
2. Key sections and their main topics
3. Critical findings or recommendations
4. Overall conclusions
Maximum 10 lines."""
            else:  # large documents
                summary_instruction = """Provide a high-level overview that includes:
1. Document type and primary purpose
2. Main themes and topics covered
3. Most critical findings or conclusions
4. Key takeaways
Maximum 10 lines. Note: This is a sampled summary from key sections."""
            
            # Add extraction context for transparency
            extraction_note = ""
            if not full_text:
                extraction_note = f"\nNote: This is a {page_count}-page document. Summary based on key sections (pages extracted using {extraction_strategy} strategy)."
            
            # Create comprehensive prompt
            prompt = f"""Please analyze and summarize this document.

Document Information:
- Title: {metadata.get('title', 'Unknown')}
- Type: PDF
- Pages: {page_count}
- Size Category: {doc_size.upper()}
- Author: {metadata.get('author', 'Not specified')}
- Subject: {metadata.get('subject', 'Not specified')}
- Suggested Category: {metadata.get('suggested_category', 'general')}
{extraction_note}

Document Content:
{text[:4500]}

{summary_instruction}

Important: Keep the summary concise, professional, and actionable. Focus on what matters most."""

            debug_print(f"🤖 Generating intelligent summary using Ollama ({OLLAMA_MODEL})...")
            debug_print(f"   Document: {page_count} pages ({doc_size}), Extraction: {extraction_strategy}")
            
            system_message = """You are an expert document analyst specializing in creating concise, professional summaries for compliance, governance, risk, and policy documents. 
Your summaries should be:
- Highly informative and actionable
- Structured and easy to scan
- Maximum 10 lines
- Focused on key points, findings, and recommendations
- Professional and objective in tone"""
            
            # Call Ollama API
            summary = self._call_ollama(
                prompt=prompt,
                system_message=system_message,
                max_tokens=600,
                temperature=0.3
            )
            
            if not summary:
                raise Exception("Ollama returned empty response")
            
            # Ensure summary is not more than 10 lines
            lines = [line.strip() for line in summary.split('\n') if line.strip()]
            if len(lines) > 10:
                summary = '\n'.join(lines[:10])
            else:
                summary = '\n'.join(lines)
            
            # Add metadata footer if it was a sampled extraction
            if not full_text and page_count > 5:
                summary += f"\n\n[Summary generated from {extraction_strategy} extraction of {page_count}-page document]"
            
            debug_print(f"✅ Intelligent summary generated: {len(summary)} characters, {len(lines)} lines")
            
            return summary
            
        except Exception as e:
            error_msg = f"Failed to generate summary: {str(e)}"
            debug_print(f"ERROR {error_msg}")
            
            # Provide a fallback summary with available metadata
            fallback = f"Document: {metadata.get('title', 'Unknown')} ({metadata.get('page_count', '?')} pages)\n"
            if metadata.get('subject'):
                fallback += f"Subject: {metadata.get('subject')}\n"
            if metadata.get('author'):
                fallback += f"Author: {metadata.get('author')}\n"
            fallback += f"\nAutomatic summary generation failed. Please review document manually.\nError: {str(e)}"
            
            return fallback
    
    def _process_pdf_after_upload(self, operation_id: int, s3_url: str, file_name: str):
        """
        Enhanced PDF processing after upload:
        1. Download PDF from S3
        2. Extract text using intelligent strategy (small vs large document)
        3. Extract comprehensive metadata
        4. Generate AI-powered summary using OpenAI GPT-3.5-turbo
        5. Update database with all information
        
        This runs in a background thread to not block the upload response
        """
        try:
            debug_print(f"\n{'='*60}")
            debug_print(f"🔄 Starting Enhanced PDF Processing")
            debug_print(f"📄 Operation ID: {operation_id}")
            debug_print(f"📂 File: {file_name}")
            debug_print(f"{'='*60}")
            
            # Step 1: Download PDF content from S3
            debug_print(f"\n[Step 1/5] ⬇️  Downloading PDF from S3...")
            debug_print(f"   URL: {s3_url}")
            response = requests.get(s3_url, timeout=90)
            response.raise_for_status()
            pdf_content = response.content
            
            file_size_mb = round(len(pdf_content) / (1024 * 1024), 2)
            debug_print(f"   ✅ Downloaded: {len(pdf_content)} bytes ({file_size_mb} MB)")
            
            # Step 2: Extract text using intelligent strategy
            debug_print(f"\n[Step 2/5] 📄 Extracting text from PDF (smart extraction)...")
            text, total_pages, extraction_strategy = self._extract_text_from_pdf(pdf_content)
            
            if not text:
                debug_print("   ⚠️  No text extracted from PDF")
                # Still extract metadata even if no text
                debug_print(f"\n[Step 3/5] 📋 Extracting metadata (text-less document)...")
                metadata = self._extract_pdf_metadata(pdf_content, file_name, total_pages, extraction_strategy)
                
                debug_print(f"\n[Step 5/5] 💾 Updating database...")
                self._update_pdf_metadata_in_db(
                    operation_id, 
                    metadata, 
                    "No text content available for summary. Document may be image-based or encrypted."
                )
                debug_print(f"\n⚠️  PDF processing completed with limited results (no text extracted)")
                return
            
            # Step 3: Extract comprehensive metadata
            debug_print(f"\n[Step 3/5] 📋 Extracting comprehensive metadata...")
            metadata = self._extract_pdf_metadata(pdf_content, file_name, total_pages, extraction_strategy)
            
            debug_print(f"   Document Details:")
            debug_print(f"   - Pages: {metadata.get('page_count', 'Unknown')}")
            debug_print(f"   - Size Category: {metadata.get('document_size_category', 'Unknown')}")
            debug_print(f"   - Extraction Strategy: {metadata.get('extraction_strategy', 'Unknown')}")
            debug_print(f"   - Title: {metadata.get('title', 'Unknown')}")
            debug_print(f"   - Category: {metadata.get('suggested_category', 'Unknown')}")
            
            # Step 4: Generate AI summary using OpenAI
            debug_print(f"\n[Step 4/5] 🤖 Generating AI-powered summary...")
            summary = self._generate_summary_with_ollama(text, metadata)
            
            if summary and not summary.startswith("Summary unavailable"):
                debug_print(f"   ✅ Summary generated successfully")
                debug_print(f"   - Length: {len(summary)} characters")
                debug_print(f"   - Lines: {len(summary.split(chr(10)))}")
            else:
                debug_print(f"   ⚠️  Summary generation had issues: {summary[:100]}...")
            
            # Step 5: Update database with all information
            debug_print(f"\n[Step 5/5] 💾 Updating database with metadata and summary...")
            self._update_pdf_metadata_in_db(operation_id, metadata, summary)
            
            # Step 6: Analyze audit relevance (runs in background thread)
            debug_print(f"\n[Step 6/6] 🔍 Starting audit relevance analysis in background...")
            try:
                # Get framework_id from file_operations
                framework_id = self._get_file_framework_id(operation_id)
                if framework_id:
                    # Start background thread for audit relevance analysis
                    analysis_thread = threading.Thread(
                        target=self._analyze_audit_relevance_background,
                        args=(operation_id, summary, metadata, framework_id),
                        daemon=True
                    )
                    analysis_thread.start()
                    debug_print(f"   ✅ Background analysis started for framework {framework_id}")
                else:
                    debug_print(f"   ⚠️  No framework_id found, skipping audit relevance analysis")
            except Exception as e:
                debug_print(f"   ⚠️  Failed to start audit relevance analysis: {str(e)}")
            
            debug_print(f"\n{'='*60}")
            debug_print(f"✅ PDF PROCESSING COMPLETED SUCCESSFULLY")
            debug_print(f"   Operation ID: {operation_id}")
            debug_print(f"   File: {file_name}")
            debug_print(f"   Pages: {total_pages}")
            debug_print(f"   Strategy: {extraction_strategy}")
            debug_print(f"   Summary Length: {len(summary)} chars")
            debug_print(f"{'='*60}\n")
            
        except requests.exceptions.RequestException as req_error:
            error_msg = f"Failed to download PDF from S3: {str(req_error)}"
            debug_print(f"\n❌ ERROR: {error_msg}")
            try:
                self._update_pdf_metadata_in_db(
                    operation_id, 
                    {'error': error_msg, 'processing_failed': True}, 
                    f"Processing failed: Unable to download file from S3"
                )
            except:
                pass
                
        except Exception as e:
            error_msg = f"PDF processing error: {str(e)}"
            debug_print(f"\n❌ ERROR: PDF processing failed for operation {operation_id}")
            debug_print(f"   Error: {str(e)}")
            debug_print(f"   Type: {type(e).__name__}")
            
            # Update database with error information
            try:
                self._update_pdf_metadata_in_db(
                    operation_id, 
                    {
                        'error': error_msg, 
                        'processing_failed': True,
                        'error_type': type(e).__name__
                    }, 
                    f"Automatic processing failed. Please review document manually.\nError: {str(e)}"
                )
            except Exception as db_error:
                debug_print(f"   ⚠️  Also failed to update database: {str(db_error)}")
    
    def _update_pdf_metadata_in_db(self, operation_id: int, metadata: Dict, summary: str):
        """
        Update the file_operations record with PDF metadata and summary
        
        Updates:
        - metadata: Comprehensive JSON metadata about the document
        - summary: AI-generated summary (up to 2000 characters)
        - status: Set to 'completed' if processing was successful
        - updated_at: Current timestamp
        """
        if not self.db_pool or not operation_id:
            debug_print("⚠️  Database pool not available or invalid operation_id")
            return
        
        conn = self._get_db_connection()
        if not conn:
            debug_print("⚠️  Could not get database connection")
            return
        
        cursor = conn.cursor()
        
        try:
            # Determine status based on whether we have a valid summary
            processing_status = 'completed'
            if 'error' in metadata or 'processing_failed' in metadata:
                processing_status = 'failed'
            elif summary.startswith("Summary unavailable") or summary.startswith("No text content"):
                processing_status = 'completed'  # Completed but with limited results
            
            # Add processing completion timestamp to metadata
            metadata['processing_completed_at'] = datetime.datetime.now().isoformat()
            metadata['ai_processing_used'] = True
            metadata['ai_model'] = 'gpt-3.5-turbo'
            
            # Update metadata, summary, and status columns
            query = """
            UPDATE file_operations 
            SET metadata = %s, 
                summary = %s, 
                status = %s,
                updated_at = %s,
                completed_at = %s
            WHERE id = %s
            """
            
            params = (
                json.dumps(metadata),
                summary[:2000],  # Limit summary to 2000 characters for database
                processing_status,
                datetime.datetime.now(),
                datetime.datetime.now() if processing_status == 'completed' else None,
                operation_id
            )
            
            cursor.execute(query, params)
            conn.commit()
            
            debug_print(f"✅ Database updated successfully:")
            debug_print(f"   - Operation ID: {operation_id}")
            debug_print(f"   - Status: {processing_status}")
            debug_print(f"   - Metadata fields: {len(metadata)}")
            debug_print(f"   - Summary length: {len(summary)} characters")
            
        except mysql.connector.Error as e:
            debug_print(f"❌ MySQL update error: {str(e)}")
            debug_print(f"   - Operation ID: {operation_id}")
            debug_print(f"   - Error Code: {e.errno if hasattr(e, 'errno') else 'N/A'}")
        except Exception as e:
            debug_print(f"❌ Database update error: {str(e)}")
            debug_print(f"   - Operation ID: {operation_id}")
            debug_print(f"   - Error Type: {type(e).__name__}")
        finally:
            cursor.close()
            conn.close()
    
    def _process_excel_after_upload(self, operation_id: int, s3_url: str, file_name: str):
        """
        Process Excel file after upload:
        1. Download Excel from S3
        2. Extract text from all sheets
        3. Extract metadata
        4. Generate AI-powered summary using OpenAI GPT-3.5-turbo
        5. Update database with all information
        6. Analyze audit relevance
        
        This runs in a background thread to not block the upload response
        """
        try:
            debug_print(f"\n{'='*60}")
            debug_print(f"🔄 Starting Excel Processing")
            debug_print(f"📄 Operation ID: {operation_id}")
            debug_print(f"📂 File: {file_name}")
            debug_print(f"{'='*60}")
            
            # Step 1: Download Excel content from S3
            debug_print(f"\n[Step 1/6] ⬇️  Downloading Excel from S3...")
            debug_print(f"   URL: {s3_url}")
            response = requests.get(s3_url, timeout=90)
            response.raise_for_status()
            excel_content = response.content
            
            file_size_mb = round(len(excel_content) / (1024 * 1024), 2)
            debug_print(f"   ✅ Downloaded: {len(excel_content)} bytes ({file_size_mb} MB)")
            
            # Step 2: Extract text from Excel
            debug_print(f"\n[Step 2/6] 📊 Extracting text from Excel...")
            text = self._extract_text_from_excel(excel_content, file_name)
            
            if not text:
                debug_print("   ⚠️  No text extracted from Excel")
                metadata = {
                    'file_type': 'excel',
                    'file_name': file_name,
                    'file_size_bytes': len(excel_content),
                    'file_size_mb': file_size_mb,
                    'sheet_count': 0,
                    'extraction_failed': True
                }
                
                debug_print(f"\n[Step 6/6] 💾 Updating database...")
                self._update_pdf_metadata_in_db(
                    operation_id, 
                    metadata, 
                    "No text content available for summary. Excel file may be empty or corrupted."
                )
                debug_print(f"\n⚠️  Excel processing completed with limited results (no text extracted)")
                return
            
            # Step 3: Extract metadata
            debug_print(f"\n[Step 3/6] 📋 Extracting metadata...")
            metadata = self._extract_excel_metadata(excel_content, file_name, text)
            
            debug_print(f"   Document Details:")
            debug_print(f"   - Sheets: {metadata.get('sheet_count', 'Unknown')}")
            debug_print(f"   - Rows: {metadata.get('total_rows', 'Unknown')}")
            debug_print(f"   - File Size: {file_size_mb} MB")
            
            # Step 4: Generate AI summary using OpenAI
            debug_print(f"\n[Step 4/6] 🤖 Generating AI-powered summary...")
            summary = self._generate_summary_with_ollama(text, metadata)
            
            if summary and not summary.startswith("Summary unavailable"):
                debug_print(f"   ✅ Summary generated successfully")
                debug_print(f"   - Length: {len(summary)} characters")
            else:
                debug_print(f"   ⚠️  Summary generation had issues: {summary[:100]}...")
            
            # Step 5: Update database with all information
            debug_print(f"\n[Step 5/6] 💾 Updating database with metadata and summary...")
            self._update_pdf_metadata_in_db(operation_id, metadata, summary)
            
            # Step 6: Analyze audit relevance (runs in background thread)
            debug_print(f"\n[Step 6/6] 🔍 Starting audit relevance analysis in background...")
            try:
                # Get framework_id from file_operations
                framework_id = self._get_file_framework_id(operation_id)
                if framework_id:
                    # Start background thread for audit relevance analysis
                    analysis_thread = threading.Thread(
                        target=self._analyze_audit_relevance_background,
                        args=(operation_id, summary, metadata, framework_id),
                        daemon=True
                    )
                    analysis_thread.start()
                    debug_print(f"   ✅ Background analysis started for framework {framework_id}")
                else:
                    debug_print(f"   ⚠️  No framework_id found, skipping audit relevance analysis")
            except Exception as e:
                debug_print(f"   ⚠️  Failed to start audit relevance analysis: {str(e)}")
            
            debug_print(f"\n{'='*60}")
            debug_print(f"✅ EXCEL PROCESSING COMPLETED SUCCESSFULLY")
            debug_print(f"   Operation ID: {operation_id}")
            debug_print(f"   File: {file_name}")
            debug_print(f"   Summary Length: {len(summary)} chars")
            debug_print(f"{'='*60}\n")
            
        except requests.exceptions.RequestException as req_error:
            error_msg = f"Failed to download Excel from S3: {str(req_error)}"
            debug_print(f"\n❌ ERROR: {error_msg}")
            try:
                self._update_pdf_metadata_in_db(
                    operation_id, 
                    {'error': error_msg, 'processing_failed': True}, 
                    f"Processing failed: Unable to download file from S3"
                )
            except:
                pass
                
        except Exception as e:
            error_msg = f"Excel processing error: {str(e)}"
            debug_print(f"\n❌ ERROR: Excel processing failed for operation {operation_id}")
            debug_print(f"   Error: {str(e)}")
            debug_print(f"   Type: {type(e).__name__}")
            
            # Update database with error information
            try:
                self._update_pdf_metadata_in_db(
                    operation_id, 
                    {
                        'error': error_msg, 
                        'processing_failed': True,
                        'error_type': type(e).__name__
                    }, 
                    f"Automatic processing failed. Please review document manually.\nError: {str(e)}"
                )
            except Exception as db_error:
                debug_print(f"   ⚠️  Also failed to update database: {str(db_error)}")
    
    def _extract_text_from_excel(self, excel_content: bytes, file_name: str) -> str:
        """Extract text content from Excel file"""
        try:
            if not PANDAS_AVAILABLE:
                debug_print("⚠️  pandas not available, cannot extract Excel content")
                return ""
            
            import io
            import pandas as pd
            
            # Read Excel file from bytes
            excel_file = io.BytesIO(excel_content)
            
            # Read all sheets
            excel_data = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl' if '.xlsx' in file_name.lower() else None)
            
            # Combine text from all sheets
            text_parts = []
            for sheet_name, df in excel_data.items():
                text_parts.append(f"Sheet: {sheet_name}")
                # Convert DataFrame to string representation
                text_parts.append(df.to_string())
                text_parts.append("")  # Empty line between sheets
            
            combined_text = "\n".join(text_parts)
            
            # Limit text length for processing (similar to PDF extraction)
            max_text_length = 50000  # Limit to ~50k characters
            if len(combined_text) > max_text_length:
                combined_text = combined_text[:max_text_length] + "\n\n[Content truncated for processing...]"
            
            debug_print(f"   ✅ Extracted {len(combined_text)} characters from {len(excel_data)} sheet(s)")
            return combined_text
            
        except Exception as e:
            debug_print(f"⚠️  Error extracting text from Excel: {str(e)}")
            return ""
    
    def _extract_excel_metadata(self, excel_content: bytes, file_name: str, text: str) -> Dict:
        """Extract metadata from Excel file"""
        try:
            import io
            import pandas as pd
            
            metadata = {
                'file_type': 'excel',
                'file_name': file_name,
                'file_size_bytes': len(excel_content),
                'file_size_mb': round(len(excel_content) / (1024 * 1024), 2),
                'document_size_category': 'medium',  # Default
                'extraction_strategy': 'full_extraction',
                'full_text_extracted': True
            }
            
            if PANDAS_AVAILABLE:
                excel_file = io.BytesIO(excel_content)
                excel_data = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl' if '.xlsx' in file_name.lower() else None)
                
                metadata['sheet_count'] = len(excel_data)
                metadata['sheet_names'] = list(excel_data.keys())
                
                total_rows = sum(len(df) for df in excel_data.values())
                metadata['total_rows'] = total_rows
                metadata['total_columns'] = sum(len(df.columns) for df in excel_data.values())
                
                # Determine size category
                if total_rows < 100:
                    metadata['document_size_category'] = 'small'
                elif total_rows < 1000:
                    metadata['document_size_category'] = 'medium'
                else:
                    metadata['document_size_category'] = 'large'
            
            # Add text length info
            metadata['extracted_text_length'] = len(text)
            
            return metadata
            
        except Exception as e:
            debug_print(f"⚠️  Error extracting Excel metadata: {str(e)}")
            return {
                'file_type': 'excel',
                'file_name': file_name,
                'file_size_bytes': len(excel_content),
                'error': str(e)
            }
    
    def _get_file_framework_id(self, operation_id: int) -> Optional[int]:
        """Get framework_id from file_operations record"""
        if not self.db_pool or not operation_id:
            return None
        
        conn = self._get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT FrameworkId FROM file_operations WHERE id = %s", (operation_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return None
        except Exception as e:
            debug_print(f"⚠️  Error getting framework_id: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def _get_all_database_data(self, framework_id: int) -> Dict:
        """Get all database data relevant to audits: policies, subpolicies, compliances, findings, incidents, risks, events"""
        if not self.db_pool:
            return {}
        
        conn = self._get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor(dictionary=True)
        data = {
            "policies": [],
            "subpolicies": [],
            "compliances": [],
            "audit_findings": [],
            "incidents": [],
            "risks": [],
            "events": []
        }
        
        try:
            # Get all policies
            cursor.execute("""
                SELECT PolicyId, PolicyName, PolicyDescription, Scope, Objective
                FROM policies WHERE FrameworkId = %s
            """, (framework_id,))
            data["policies"] = cursor.fetchall()
            
            # Get all subpolicies
            cursor.execute("""
                SELECT sp.SubPolicyId, sp.SubPolicyName, sp.Description, sp.PolicyId
                FROM subpolicies sp
                JOIN policies p ON sp.PolicyId = p.PolicyId
                WHERE p.FrameworkId = %s
            """, (framework_id,))
            data["subpolicies"] = cursor.fetchall()
            
            # Get all compliances
            cursor.execute("""
                SELECT c.ComplianceId, c.ComplianceTitle, c.ComplianceItemDescription, 
                       c.SubPolicyId, sp.PolicyId, c.Scope, c.Objective
                FROM compliance c
                JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                JOIN policies p ON sp.PolicyId = p.PolicyId
                WHERE p.FrameworkId = %s
            """, (framework_id,))
            data["compliances"] = cursor.fetchall()
            
            # Get all audit findings
            cursor.execute("""
                SELECT af.AuditFindingsId, af.AuditId, af.ComplianceId, af.DetailsOfFinding, 
                       af.Evidence, af.Impact, af.Recommendation, af.FrameworkId
                FROM audit_findings af
                WHERE af.FrameworkId = %s
            """, (framework_id,))
            data["audit_findings"] = cursor.fetchall()
            
            # Get all incidents (table name is 'incidents' plural)
            # NOTE: Incident model does not have Impact/Resolution columns; use existing fields.
            cursor.execute("""
                SELECT IncidentId, IncidentTitle, Description, Status, CostOfIncident, FrameworkId
                FROM incidents WHERE FrameworkId = %s
            """, (framework_id,))
            data["incidents"] = cursor.fetchall()
            
            # Get all risks
            # NOTE: Risk model uses RiskTitle, BusinessImpact, RiskLikelihood, RiskImpact instead of RiskName/Impact/Probability.
            cursor.execute("""
                SELECT RiskId, RiskTitle, RiskDescription, BusinessImpact, RiskLikelihood, RiskImpact, FrameworkId
                FROM risk WHERE FrameworkId = %s
            """, (framework_id,))
            data["risks"] = cursor.fetchall()
            
            # Get all events
            # NOTE: Physical table name is likely 'events' (plural) in grc2; avoid selecting non-existent columns.
            cursor.execute("""
                SELECT EventId, EventTitle, Description, FrameworkId
                FROM events WHERE FrameworkId = %s
            """, (framework_id,))
            data["events"] = cursor.fetchall()
            
        except Exception as e:
            debug_print(f"⚠️  Error getting database data: {str(e)}")
        finally:
            cursor.close()
            conn.close()
        
        return data
    
    def _get_all_documents_from_file_operations(self, framework_id: int) -> List[Dict]:
        """Get all documents from file_operations table for this framework"""
        if not self.db_pool:
            return []
        
        conn = self._get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT id, file_name, original_name, s3_url, s3_key, file_size, 
                       file_type, content_type, stored_name, user_id, FrameworkId,
                       summary, metadata, status, created_at
                FROM file_operations 
                WHERE FrameworkId = %s AND operation_type = 'upload' AND status = 'completed'
                ORDER BY created_at DESC
            """, (framework_id,))
            return cursor.fetchall()
        except Exception as e:
            debug_print(f"⚠️  Error getting documents from file_operations: {str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()

    def _get_db_record_id(self, table_name: str, record: Dict) -> Optional[int]:
        """
        Helper to consistently resolve the primary key field for a given table's record.
        This is used both when writing JSON indexes and when doing incremental filtering.
        """
        pk_fields = {
            "policies": "PolicyId",
            "subpolicies": "SubPolicyId",
            "compliances": "ComplianceId",
            "audit_findings": "AuditFindingsId",
            "incidents": "IncidentId",
            "risks": "RiskId",
            "events": "EventId",
        }
        col = pk_fields.get(table_name)
        if col and isinstance(record, dict):
            rid = record.get(col)
        else:
            rid = record.get("id") if isinstance(record, dict) else None
        try:
            return int(rid) if rid is not None else None
        except (TypeError, ValueError):
            return None

    def _analyze_database_data_relevance(self, audit_id: int, audit_details: Dict, database_data: Dict) -> Dict:
        """Analyze relevance of database data to audit"""
        results = {
            "policies": [],
            "subpolicies": [],
            "compliances": [],
            "audit_findings": [],
            "incidents": [],
            "risks": [],
            "events": []
        }
        
        # Build audit context
        audit_context = f"=== AUDIT PURPOSE AND CONTEXT ===\n"
        audit_context += f"Audit Title: {audit_details.get('audit_title', 'Not specified')}\n"
        if audit_details.get('audit_objective'):
            audit_context += f"Audit Objective: {audit_details.get('audit_objective')[:800]}\n"
        if audit_details.get('audit_scope'):
            audit_context += f"Audit Scope: {audit_details.get('audit_scope')[:800]}\n"

        # Add explicit list of compliance requirements (with IDs) so the model can map DB rows to them
        compliances = audit_details.get('compliances') or []
        if compliances:
            audit_context += "\n=== RELEVANT COMPLIANCE REQUIREMENTS (use these IDs in matched_compliances) ===\n"
            # Support both dicts with keys like 'compliance_id' / 'ComplianceId'
            for c in compliances[:100]:
                if not isinstance(c, dict):
                    continue
                cid = c.get('compliance_id') or c.get('ComplianceId') or c.get('id')
                title = c.get('title') or c.get('ComplianceTitle') or c.get('name') or ''
                desc = c.get('description') or c.get('ComplianceItemDescription') or ''
                desc = str(desc)[:200]
                audit_context += f"- [ComplianceId:{cid}] {title} - {desc}\n"
            if len(compliances) > 100:
                audit_context += f"... and {len(compliances) - 100} more compliances not listed here\n"
        
        # Analyze each table's data
        for table_name, records in database_data.items():
            if not records:
                continue
            
            debug_print(f"      📊 Analyzing {len(records)} {table_name} records for database relevance...")
            
            analyzed_count = 0
            relevant_count_60 = 0
            relevant_count_80 = 0

            for record in records[:50]:  # Limit to first 50 per table
                try:
                    # Build content string from record
                    content_parts = []
                    for key, value in record.items():
                        if value and isinstance(value, (str, int, float)):
                            content_parts.append(f"{key}: {str(value)[:200]}")
                    content = "\n".join(content_parts)
                    
                    prompt = f"""Analyze if this database record is relevant to this audit.

{audit_context}

Database Record ({table_name}):
{content[:2000]}

You are given the list of compliance requirements above with explicit ComplianceId values.
If (and only if) this database record clearly provides evidence for one or more of those
requirements, include their numeric ComplianceId values in matched_compliances.

Return ONLY valid JSON (no markdown, no explanations outside the JSON) exactly in this shape:
{{
    "relevance_score": 0.0-1.0,
    "relevance_reason": "brief explanation",
    "matched_policies": [],
    "matched_subpolicies": [],
    "matched_compliances": []
}}"""
                    
                    result_text = self._call_ollama(
                        prompt=prompt,
                        system_message="You are an expert GRC auditor. Return only valid JSON.",
                        max_tokens=400,
                        temperature=0.3
                    )
                    
                    if result_text:
                        import re
                        analysis = None
                        
                        # Try to extract JSON from markdown code blocks
                        json_code_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
                        if json_code_block:
                            try:
                                analysis = json.loads(json_code_block.group(1))
                            except:
                                pass
                        
                        # If not found, try to extract JSON object directly
                        if not analysis:
                            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
                            if json_match:
                                try:
                                    analysis = json.loads(json_match.group())
                                except:
                                    pass
                        
                        # If still not found, try parsing markdown format
                        if not analysis:
                            try:
                                score_match = re.search(r'(?:relevance_score|Relevance Score)[:\s]*([0-9.]+)', result_text, re.IGNORECASE)
                                score = float(score_match.group(1)) if score_match else 0.0
                                
                                reason_match = re.search(r'(?:relevance_reason|Relevance Reason)[:\s]*(.+?)(?:\n\n|\n\*\*|$)', result_text, re.IGNORECASE | re.DOTALL)
                                reason = reason_match.group(1).strip() if reason_match else ""
                                
                                analysis = {
                                    "relevance_score": score,
                                    "relevance_reason": reason,
                                    "matched_policies": [],
                                    "matched_subpolicies": [],
                                    "matched_compliances": []
                                }
                            except:
                                pass
                        
                        if analysis:
                            analyzed_count += 1
                            record_id = self._get_db_record_id(table_name, record)
                            analysis["record_id"] = record_id if record_id is not None else 0
                            score = float(analysis.get("relevance_score", 0.0) or 0.0)

                            # Simple counters for how many DB rows are actually "relevant"
                            if score >= 0.6:
                                relevant_count_60 += 1
                            if score >= 0.8:
                                relevant_count_80 += 1

                            # Compact, easy-to-read log for every analyzed DB row
                            reason_preview = (analysis.get("relevance_reason") or "").replace("\n", " ")
                            if len(reason_preview) > 140:
                                reason_preview = reason_preview[:140] + "..."
                            debug_print(
                                f"         💾 [{table_name}] record_id={record_id} "
                                f"score={score:.2f} | reason={reason_preview}"
                            )

                            results[table_name].append(analysis)
                            
                except Exception as e:
                    # Stop immediately on any unexpected error so it is clearly visible
                    debug_print(f"      ❌ Fatal error analyzing {table_name} record: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    raise
            
            # Per-table summary so you can quickly see how many DB rows were relevant
            if analyzed_count:
                debug_print(
                    f"      ✅ {table_name}: analyzed={analyzed_count}, "
                    f"relevant_>=0.6={relevant_count_60}, relevant_>=0.8={relevant_count_80}"
                )
            else:
                debug_print(f"      ℹ️  No {table_name} records could be analyzed for relevance.")

        return results
    
    def _analyze_audit_relevance_background(self, operation_id: int, summary: str, metadata: Dict, framework_id: int):
        """
        Background function to analyze ALL documents and database data relevance to all active audits.
        Also creates ai_audit_data evidence from relevant database records and can update
        lastchecklistitemverified for high-confidence matches.
        """
        try:
            debug_print(f"\n{'='*60}")
            debug_print(f"🔍 Starting Comprehensive Audit Relevance Analysis")
            debug_print(f"   Framework ID: {framework_id}")
            debug_print(f"{'='*60}\n")
            
            # Get all active audits for this framework
            audits = self._get_active_ai_audits(framework_id)
            
            if not audits:
                debug_print(f"   ℹ️  No active audits found for framework {framework_id}")
                return
            
            debug_print(f"   📋 Found {len(audits)} active audits to analyze")
            
            # Get ALL documents from file_operations
            all_documents = self._get_all_documents_from_file_operations(framework_id)
            debug_print(f"   📄 Found {len(all_documents)} documents in file_operations")
            
            # Get ALL database data
            all_database_data = self._get_all_database_data(framework_id)
            db_count = sum(len(v) for v in all_database_data.values())
            debug_print(f"   💾 Found {db_count} database records across all tables")
            
            # Analyze relevance for each audit
            for audit in audits:
                try:
                    audit_id = audit['audit_id']
                    debug_print(f"\n   🔍 Analyzing Audit ID: {audit_id} - {audit.get('audit_title', 'No Title')[:50]}")
                    
                    # Get audit details
                    audit_details = self._get_audit_details(audit_id)
                    audit_framework_id = audit_details.get('framework_id')
                    
                    # Load JSON indexes
                    docs_index_path = self._get_json_index_path(framework_id, audit_id, "documents")
                    db_index_path = self._get_json_index_path(framework_id, audit_id, "database")
                    docs_index = self._load_json_index(docs_index_path)
                    db_index = self._load_json_index(db_index_path)
                    
                    # Track analyzed documents by s3_key/stored_name (not operation_id) to handle same file uploaded with different modules
                    # This ensures the same physical file is not re-analyzed when uploaded with different module selections
                    analyzed_file_keys = set()
                    analyzed_operation_ids = set()  # Also track by operation_id for backward compatibility
                    for d in docs_index.get("documents", []):
                        # Check both s3_key and stored_name for deduplication (preferred method)
                        file_key = d.get("s3_key") or d.get("stored_name")
                        if file_key:
                            analyzed_file_keys.add(file_key)
                        # Also track by operation_id for backward compatibility (old entries might not have s3_key/stored_name)
                        op_id = d.get("operation_id")
                        if op_id:
                            analyzed_operation_ids.add(op_id)
                    
                    # Analyze ALL documents (incremental via docs_index)
                    debug_print(f"      📄 Analyzing {len(all_documents)} documents...")
                    for doc in all_documents:
                        doc_id = doc.get('id')
                        # Use s3_key or stored_name as the unique identifier (not operation_id)
                        doc_s3_key = doc.get('s3_key')
                        doc_stored_name = doc.get('stored_name')
                        file_key = doc_s3_key or doc_stored_name
                        
                        # Check if already analyzed by file_key (s3_key/stored_name) - preferred method
                        if file_key and file_key in analyzed_file_keys:
                            debug_print(f"      ⏭️  Skipping document {doc_id} (s3_key/stored_name='{file_key[:50]}...' already analyzed)")
                            continue
                        
                        # Fallback: Check if already analyzed by operation_id (for backward compatibility with old JSON entries)
                        if doc_id in analyzed_operation_ids:
                            debug_print(f"      ⏭️  Skipping document {doc_id} (operation_id already analyzed - backward compatibility check)")
                            continue
                        
                        doc_summary = doc.get('summary') or summary
                        doc_metadata = json.loads(doc.get('metadata', '{}')) if isinstance(doc.get('metadata'), str) else doc.get('metadata', {})
                        if not doc_metadata:
                            doc_metadata = {
                                'title': doc.get('file_name', 'Unknown'),
                                'file_name': doc.get('file_name', 'Unknown')
                            }
                        
                        debug_print(f"      🔍 Analyzing document {doc_id} (file_name='{doc.get('file_name', 'unknown')[:50]}...', s3_key='{doc_s3_key[:50] if doc_s3_key else 'none'}...', stored_name='{doc_stored_name[:50] if doc_stored_name else 'none'}...')")
                        relevance_result = self._analyze_document_audit_relevance(
                            summary=doc_summary,
                            metadata=doc_metadata,
                            audit_id=audit_id,
                            audit_details=audit_details
                        )
                        
                        if relevance_result:
                            # Update JSON index (pass s3_key/stored_name for deduplication)
                            self._update_json_index_document(framework_id, audit_id, doc_id, relevance_result, doc_s3_key=doc_s3_key, doc_stored_name=doc_stored_name)
                            
                            # Store in database if relevant
                            if relevance_result.get('relevance_score', 0) >= 0.6:
                                self._store_audit_relevance(doc_id, audit_id, relevance_result, doc_s3_key=doc_s3_key, doc_stored_name=doc_stored_name)
                            else:
                                debug_print(f"      ⏭️  Document {doc_id} relevance score {relevance_result.get('relevance_score', 0):.2f} < 0.6, not storing in database")
                        else:
                            debug_print(f"      ⚠️  Document {doc_id} analysis returned no result")
                    # Analyze ALL database data (incremental using existing db_index)
                    debug_print(f"      💾 Analyzing database data...")

                    # Build a quick lookup of which (table, record_id) are already analyzed.
                    # The JSON structure groups records under data["database_data"][table_name].
                    already_analyzed_db = {}
                    db_data = db_index.get("database_data", {}) or {}
                    for t, records_list in db_data.items():
                        if not isinstance(records_list, list):
                            continue
                        for existing in records_list:
                            if not isinstance(existing, dict):
                                continue
                            rid = existing.get("record_id")
                            if rid is None:
                                continue
                            already_analyzed_db.setdefault(t, set()).add(rid)

                    # How many DB records are already cached for this audit (from previous runs)
                    cached_total = sum(len(ids) for ids in already_analyzed_db.values())

                    # Filter database_data to only NEW records for this audit
                    incremental_db_data = {}
                    new_total = 0
                    for table_name, records in all_database_data.items():
                        if not records:
                            continue
                        seen_ids = already_analyzed_db.get(table_name, set())
                        new_records = []
                        for record in records:
                            # Resolve primary key for this table's record
                            record_id = self._get_db_record_id(table_name, record)
                            if record_id is None:
                                continue
                            if record_id in seen_ids:
                                continue
                            new_records.append(record)
                        if new_records:
                            incremental_db_data[table_name] = new_records
                            new_total += len(new_records)

                    debug_print(f"      💾 Database incremental mode: {new_total} new record(s) to analyze")
                    debug_print(f"      💾 Using {cached_total} cached database record(s) from JSON index")

                    # Run relevance only on new DB records
                    db_results = {}
                    if incremental_db_data:
                        db_results = self._analyze_database_data_relevance(audit_id, audit_details, incremental_db_data)
                    
                    # Update database JSON index with new analyses
                    for table_name, analyses in db_results.items():
                        for analysis in analyses:
                            record_id = analysis.get("record_id", 0)
                            if record_id:
                                self._update_json_index_database(framework_id, audit_id, table_name, record_id, analysis)

                    # Reload the full DB index so we have BOTH cached and newly-added records
                    db_index = self._load_json_index(db_index_path)
                    full_db_results = db_index.get("database_data", {}) or {}
                    
                    # Create ai_audit_data evidence from ALL relevant DB records
                    # (cached ones from previous runs + any new ones from this run)
                    self._create_ai_evidence_from_database_results(
                        framework_id=audit_framework_id or framework_id,
                        audit_id=audit_id,
                        db_results=full_db_results
                    )
                    
                    # Determine overall relevance
                    all_doc_scores = [d.get("relevance_score", 0) for d in docs_index.get("documents", [])]
                    all_db_scores = []
                    for table_analyses in full_db_results.values():
                        if not isinstance(table_analyses, list):
                            continue
                        all_db_scores.extend([a.get("relevance_score", 0) for a in table_analyses if isinstance(a, dict)])
                    
                    overall_score = 0.0
                    if all_doc_scores or all_db_scores:
                        all_scores = all_doc_scores + all_db_scores
                        overall_score = max(all_scores) if all_scores else 0.0  # Use max score
                    
                    debug_print(f"      📊 Overall Relevance Score: {overall_score:.2f}")
                    
                    # Determine what evidence exists
                    has_document_evidence = len(all_doc_scores) > 0
                    has_database_evidence = len(all_db_scores) > 0
                    
                    debug_print(f"      📊 Evidence summary: {len(all_doc_scores)} document(s), {len(all_db_scores)} database record(s)")
                    
                    # Trigger audit if relevant
                    if overall_score >= 0.6:
                        debug_print(f"      ✅ Audit {audit_id} is relevant - triggering audit execution")
                        
                        # Get best document for mapping creation
                        best_doc = max(
                            docs_index.get("documents", []),
                            key=lambda x: x.get("relevance_score", 0),
                            default=None
                        )
                        
                        # Determine check type based on available evidence
                        if has_document_evidence and has_database_evidence:
                            # BOTH exist → trigger combined check
                            debug_print(f"      🔄 BOTH document and database evidence found → triggering COMBINED EVIDENCE check")
                            if best_doc:
                                try:
                                    relevance_result = {
                                        "relevance_score": best_doc.get("relevance_score", 0),
                                        "relevance_reason": best_doc.get("relevance_reason", ""),
                                        "matched_policies": best_doc.get("matched_policies", []),
                                        "matched_subpolicies": best_doc.get("matched_subpolicies", []),
                                        "matched_compliances": best_doc.get("matched_compliances", [])
                                    }
                                    import threading
                                    threading.Thread(
                                        target=self._auto_process_relevant_document,
                                        args=(best_doc.get("operation_id"), audit_id, relevance_result),
                                        daemon=True
                                    ).start()
                                    debug_print(f"      ✅ Auto-processing triggered - compliance check will use COMBINED EVIDENCE (document + database)")
                                except Exception as e:
                                    debug_print(f"      ⚠️  Error triggering combined check: {str(e)}")
                            else:
                                debug_print(f"      ⚠️  No document found to trigger combined check (database evidence exists but no document)")
                        elif has_document_evidence:
                            # Only document → trigger document-only check
                            debug_print(f"      📄 Only document evidence found → triggering DOCUMENT-ONLY check")
                            if best_doc:
                                try:
                                    relevance_result = {
                                        "relevance_score": best_doc.get("relevance_score", 0),
                                        "relevance_reason": best_doc.get("relevance_reason", ""),
                                        "matched_policies": best_doc.get("matched_policies", []),
                                        "matched_subpolicies": best_doc.get("matched_subpolicies", []),
                                        "matched_compliances": best_doc.get("matched_compliances", [])
                                    }
                                    import threading
                                    threading.Thread(
                                        target=self._auto_process_relevant_document,
                                        args=(best_doc.get("operation_id"), audit_id, relevance_result),
                                        daemon=True
                                    ).start()
                                    debug_print(f"      ✅ Auto-processing triggered - compliance check will use DOCUMENT-ONLY evidence")
                                except Exception as e:
                                    debug_print(f"      ⚠️  Error triggering document-only check: {str(e)}")
                        elif has_database_evidence:
                            # Only database → database evidence already created, will be checked when document is uploaded
                            debug_print(f"      💾 Only database evidence found → database evidence created in ai_audit_data")
                            debug_print(f"      💡 Database evidence will be checked when a document is uploaded or manually checked")
                        else:
                            debug_print(f"      ⚠️  No evidence found to trigger audit")
                    
                except Exception as e:
                    # Treat any error in a given audit as fatal for this background run
                    debug_print(f"      ❌ Fatal error analyzing audit {audit.get('audit_id', 'unknown')}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # Stop processing further audits so the first error is clearly visible
                    raise
            
            debug_print(f"\n{'='*60}")
            debug_print(f"✅ Comprehensive Audit Relevance Analysis Completed")
            debug_print(f"{'='*60}\n")
            
        except Exception as e:
            debug_print(f"\n❌ Error in audit relevance analysis: {str(e)}")
            import traceback
            traceback.print_exc()

    def _create_ai_evidence_from_database_results(self, framework_id: Optional[int], audit_id: int, db_results: Dict):
        """
        Create ai_audit_data evidence (and optionally checklist entries) from relevant
        database records. This makes DB records first-class evidence alongside documents.
        """
        if not self.db_pool or not framework_id:
            return
        
        conn = self._get_db_connection()
        if not conn:
            return
        
        # Thresholds
        evidence_threshold = 0.6  # create ai_audit_data when score >= 0.6
        checklist_threshold = 0.8  # update checklist when score >= 0.8
        
        try:
            cursor = conn.cursor()
            dict_cursor = conn.cursor(dictionary=True)
            
            for table_name, analyses in db_results.items():
                for analysis in analyses:
                    try:
                        score = float(analysis.get("relevance_score", 0) or 0)
                        record_id = analysis.get("record_id")
                        if not record_id or score < evidence_threshold:
                            continue
                        
                        # Attempt to resolve one primary compliance/policy/subpolicy from matched_compliances.
                        # Ollama sometimes returns this as:
                        #   - a plain integer ID:       1798
                        #   - a numeric string:         "1798"
                        #   - an object:                {"ComplianceId": 1798, ...}
                        #   - an object:                {"compliance_id": 1798, ...}
                        #   - or even a nested object with generic "id" field.
                        primary_policy_id = None
                        primary_subpolicy_id = None
                        primary_compliance_id = None
                        matched_compliances = analysis.get("matched_compliances") or []

                        def _extract_compliance_id(raw_val: Any) -> Optional[int]:
                            """Normalize different Ollama structures into a numeric ComplianceId."""
                            try:
                                # Direct int
                                if isinstance(raw_val, int):
                                    return raw_val
                                # String that might be an int
                                if isinstance(raw_val, str):
                                    return int(raw_val.strip())
                                # Dict-like structures
                                if isinstance(raw_val, dict):
                                    for key in ["ComplianceId", "compliance_id", "id"]:
                                        if key in raw_val and raw_val[key] is not None:
                                            try:
                                                return int(raw_val[key])
                                            except (TypeError, ValueError):
                                                continue
                            except Exception:
                                return None
                            return None

                        comp_id: Optional[int] = None
                        # For entries coming directly from the `compliances` table,
                        # the record_id itself *is* the ComplianceId, so prefer that.
                        if table_name == "compliances" and record_id:
                            try:
                                comp_id = int(record_id)
                            except (TypeError, ValueError):
                                comp_id = None

                        # Otherwise, or if that failed, try to extract from matched_compliances.
                        if not comp_id and matched_compliances:
                            for mc in matched_compliances:
                                comp_id = _extract_compliance_id(mc)
                                if comp_id:
                                    break

                        if comp_id:
                            try:
                                # Use your actual table name: `compliance` (singular)
                                dict_cursor.execute("""
                                    SELECT c.ComplianceId, c.SubPolicyId, sp.PolicyId
                                    FROM compliance c
                                    LEFT JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                                    WHERE c.ComplianceId = %s
                                """, (comp_id,))
                                comp_row = dict_cursor.fetchone()
                                if comp_row:
                                    primary_compliance_id = comp_row.get("ComplianceId")
                                    primary_subpolicy_id = comp_row.get("SubPolicyId")
                                    primary_policy_id = comp_row.get("PolicyId")
                                else:
                                    debug_print(f"      ⚠️  No compliance row found for ComplianceId={comp_id}")
                            except Exception as comp_err:
                                debug_print(f"      ⚠️  Error resolving compliance mapping for {comp_id}: {str(comp_err)}")

                        # If we still don't have a concrete compliance mapping, keep the relevance in JSON
                        # but do NOT create a first-class evidence record to avoid "unmapped" noise.
                        if not primary_compliance_id:
                            continue

                        # Build identifiers (generic names without table/record mentions)
                        doc_name = f"Evidence {record_id}"
                        document_path = f"{table_name}:{record_id}"
                        external_id = f"{table_name}:{record_id}"
                        evidence_reason = analysis.get("relevance_reason", "")[:500]

                        # Prepare a lightweight analysis payload so the UI can show "Details"
                        # for database evidence similar to uploaded documents.
                        try:
                            import json as _json
                            db_compliance_analysis = [{
                                "source": "database_record",
                                "table_name": table_name,
                                "record_id": record_id,
                                "compliance_id": primary_compliance_id,
                                "relevance_score": score,
                                "relevance_reason": evidence_reason,
                                "status": "EVIDENCE_ONLY"
                            }]
                            db_compliance_analysis_json = _json.dumps({
                                "compliance_analyses": db_compliance_analysis
                            })
                        except Exception:
                            db_compliance_analysis_json = None
                        
                        # Check if evidence already exists for this audit + DB record
                        try:
                            check_sql = """
                                SELECT id, policy_id, subpolicy_id, compliance_analyses
                                FROM ai_audit_data
                                WHERE audit_id = %s AND external_source = 'database_record' AND external_id = %s
                                LIMIT 1
                            """
                            cursor.execute(check_sql, (audit_id, external_id))
                            existing = cursor.fetchone()
                            if existing:
                                # If an old row exists without mapping or analysis data, update it
                                existing_id = existing[0]
                                existing_policy_id = existing[1] if len(existing) > 1 else None
                                existing_subpolicy_id = existing[2] if len(existing) > 2 else None
                                existing_analyses = existing[3] if len(existing) > 3 else None
                                
                                needs_update = False
                                update_fields = []
                                update_values = []
                                
                                # Update mapping if missing
                                if not existing_policy_id or not existing_subpolicy_id:
                                    needs_update = True
                                    update_fields.append("policy_id = %s")
                                    update_fields.append("subpolicy_id = %s")
                                    update_values.extend([primary_policy_id, primary_subpolicy_id])
                                
                                # Update document name
                                needs_update = True
                                update_fields.append("document_name = %s")
                                update_values.append(doc_name)
                                
                                # Update compliance_analyses if missing or empty
                                if not existing_analyses and db_compliance_analysis_json:
                                    needs_update = True
                                    update_fields.append("compliance_analyses = %s")
                                    update_values.append(db_compliance_analysis_json)
                                
                                if needs_update:
                                    try:
                                        update_sql = f"""
                                            UPDATE ai_audit_data
                                            SET {', '.join(update_fields)}
                                            WHERE id = %s
                                        """
                                        update_values.append(existing_id)
                                        cursor.execute(update_sql, tuple(update_values))
                                        debug_print(f"      ✅ Updated existing ai_audit_data record {existing_id} with analysis data")
                                    except Exception as upd_err:
                                        debug_print(f"      ⚠️  Error updating existing ai_audit_data mapping for {external_id}: {str(upd_err)}")
                                # Either way, we don't insert a duplicate row
                                continue
                        except Exception as check_err:
                            debug_print(f"      ⚠️  Error checking existing ai_audit_data for {external_id}: {str(check_err)}")

                        # Insert ai_audit_data entry to represent this DB record as evidence
                        insert_query = """
                            INSERT INTO ai_audit_data 
                            (audit_id, document_id, document_name, document_path, document_type, 
                             file_size, mime_type, uploaded_by, ai_processing_status, uploaded_date,
                             policy_id, subpolicy_id, upload_status, external_source, external_id,
                             FrameworkId, compliance_analyses, processing_completed_at, created_at, updated_at)
                            VALUES (%s, 0, %s, %s, %s, %s, %s, %s, 'completed', NOW(),
                                   %s, %s, 'uploaded', 'database_record', %s, %s, %s, NOW(), NOW(), NOW())
                        """
                        
                        params_with_framework = [
                            audit_id,
                            doc_name,
                            document_path,
                            'db_record',
                            0,  # file_size
                            'application/json',  # mime_type
                            None,  # uploaded_by
                            primary_policy_id,
                            primary_subpolicy_id,
                            external_id,
                            framework_id,
                            db_compliance_analysis_json,
                        ]
                        
                        try:
                            cursor.execute(insert_query, params_with_framework)
                        except mysql.connector.Error as framework_err:
                            # Handle missing FrameworkId column (older schema)
                            if 'Unknown column' in str(framework_err) and 'FrameworkId' in str(framework_err):
                                fallback_query = """
                                    INSERT INTO ai_audit_data 
                                    (audit_id, document_id, document_name, document_path, document_type, 
                                     file_size, mime_type, uploaded_by, ai_processing_status, uploaded_date,
                                     policy_id, subpolicy_id, upload_status, external_source, external_id,
                                     compliance_analyses, processing_completed_at, created_at, updated_at)
                                    VALUES (%s, 0, %s, %s, %s, %s, %s, %s, 'completed', NOW(),
                                           %s, %s, 'uploaded', 'database_record', %s, %s, NOW(), NOW(), NOW())
                                """
                                cursor.execute(fallback_query, [
                                    audit_id,
                                    doc_name,
                                    document_path,
                                    'db_record',
                                    0,
                                    'application/json',
                                    None,
                                    primary_policy_id,
                                    primary_subpolicy_id,
                                    external_id,
                                    db_compliance_analysis_json,
                                ])
                            else:
                                raise
                        
                        # Get the created document_id (ai_audit_data.id) and update document_id column
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        row = cursor.fetchone()
                        if row:
                            new_doc_id = row[0]
                            try:
                                cursor.execute(
                                    "UPDATE ai_audit_data SET document_id = %s WHERE id = %s",
                                    (new_doc_id, new_doc_id),
                                )
                            except Exception as upd_err:
                                debug_print(f"      ⚠️  Error updating document_id for DB evidence row {new_doc_id}: {str(upd_err)}")
                        
                        # Optionally, for very high scores and known compliance, update checklist
                        if score >= checklist_threshold and primary_compliance_id:
                            try:
                                now_date = datetime.datetime.now().date()
                                now_time = datetime.datetime.now().time()
                                comments = f"Auto evidence from {table_name} record {record_id}: {evidence_reason}"
                                
                                # Check if an entry already exists
                                cursor.execute(
                                    """
                                    SELECT ComplianceId FROM lastchecklistitemverified
                                    WHERE ComplianceId = %s AND FrameworkId = %s
                                          AND PolicyId = %s AND SubPolicyId = %s
                                    """,
                                    (
                                        primary_compliance_id,
                                        framework_id,
                                        primary_policy_id or 0,
                                        primary_subpolicy_id or 0,
                                    ),
                                )
                                existing_row = cursor.fetchone()
                                
                                complied_value = '1'  # Conservative: mark as partially compliant based on DB evidence
                                
                                if existing_row:
                                    cursor.execute(
                                        """
                                        UPDATE lastchecklistitemverified
                                        SET Date = %s,
                                            Time = %s,
                                            Complied = %s,
                                            Comments = %s,
                                            Count = IFNULL(Count, 0) + 1
                                        WHERE ComplianceId = %s AND FrameworkId = %s
                                          AND PolicyId = %s AND SubPolicyId = %s
                                        """,
                                        (
                                            now_date,
                                            now_time,
                                            complied_value,
                                            comments,
                                            primary_compliance_id,
                                            framework_id,
                                            primary_policy_id or 0,
                                            primary_subpolicy_id or 0,
                                        ),
                                    )
                                else:
                                    cursor.execute(
                                        """
                                        INSERT INTO lastchecklistitemverified
                                            (ComplianceId, SubPolicyId, PolicyId, FrameworkId,
                                             Date, Time, User, Complied, Comments, Count)
                                        VALUES (%s, %s, %s, %s,
                                                %s, %s, %s, %s, %s, %s)
                                        """,
                                        (
                                            primary_compliance_id,
                                            primary_subpolicy_id or 0,
                                            primary_policy_id or 0,
                                            framework_id,
                                            now_date,
                                            now_time,
                                            None,
                                            complied_value,
                                            comments,
                                            1,
                                        ),
                                    )
                            except Exception as checklist_err:
                                debug_print(f"      ⚠️  Error updating lastchecklistitemverified for compliance {primary_compliance_id}: {str(checklist_err)}")
                        
                    except Exception as per_record_err:
                        debug_print(f"      ⚠️  Error creating DB evidence for {table_name} record {analysis.get('record_id')}: {str(per_record_err)}")
                        import traceback
                        traceback.print_exc()
                        continue
            
            conn.commit()
        
        except Exception as e:
            debug_print(f"      ❌ Error while creating ai_audit_data evidence from database results: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                dict_cursor.close()
            except Exception:
                pass
            try:
                cursor.close()
            except Exception:
                pass
            conn.close()
    
    def _get_active_ai_audits(self, framework_id: int) -> List[Dict]:
        """Get all active audits for a given framework (matching what's shown in dropdown)
        
        The dropdown shows all audits (AI, Internal, External, etc.) that are:
        - In the same framework
        - Not completed
        - Assigned to users, for review, or public
        
        This function gets ALL audits in the framework (not just AI) to match dropdown behavior.
        """
        if not self.db_pool:
            return []
        
        conn = self._get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        try:
            # Get ALL audits in framework that are not completed (matching dropdown logic)
            # This includes AI, Internal, External, Regular, Self-Audit types
            # FILTER: Only process audit 2318 (testing mode)
            query = """
            SELECT a.AuditId as audit_id, a.FrameworkId, a.PolicyId, a.SubPolicyId,
                   a.Title as audit_title, a.Objective as audit_objective, a.Scope as audit_scope,
                   a.AuditType, a.Status,
                   f.FrameworkName, p.PolicyName, sp.SubPolicyName
            FROM audit a
            LEFT JOIN frameworks f ON a.FrameworkId = f.FrameworkId
            LEFT JOIN policies p ON a.PolicyId = p.PolicyId
            LEFT JOIN subpolicies sp ON a.SubPolicyId = sp.SubPolicyId
            WHERE a.FrameworkId = %s
              AND (a.Status != 'Completed' OR a.Status IS NULL)
              AND a.AuditId = 2318
            ORDER BY a.AuditId DESC
            """
            cursor.execute(query, (framework_id,))
            return cursor.fetchall()
        except Exception as e:
            debug_print(f"⚠️  Error getting active AI audits: {str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def trigger_audit_relevance_analysis_for_framework(self, framework_id: int):
        """
        Manually trigger comprehensive audit relevance analysis for a framework
        This can be called when new database data is added (policies, incidents, etc.)
        """
        try:
            debug_print(f"\n{'='*60}")
            debug_print(f"🔄 Manual Trigger: Audit Relevance Analysis for Framework {framework_id}")
            debug_print(f"{'='*60}\n")
            
            # Get all active audits
            audits = self._get_active_ai_audits(framework_id)
            if not audits:
                debug_print(f"   ℹ️  No active audits found")
                return
            
            # Get all documents
            all_documents = self._get_all_documents_from_file_operations(framework_id)
            debug_print(f"   📄 Found {len(all_documents)} documents")
            
            # Get all database data
            all_database_data = self._get_all_database_data(framework_id)
            db_count = sum(len(v) for v in all_database_data.values())
            debug_print(f"   💾 Found {db_count} database records")
            
            # Analyze each audit
            for audit in audits:
                audit_id = audit['audit_id']
                audit_details = self._get_audit_details(audit_id)
                
                # Analyze all documents
                for doc in all_documents:
                    doc_summary = doc.get('summary', '')
                    doc_metadata = json.loads(doc.get('metadata', '{}')) if isinstance(doc.get('metadata'), str) else doc.get('metadata', {})
                    if not doc_metadata:
                        doc_metadata = {'title': doc.get('file_name', 'Unknown')}
                    
                    relevance_result = self._analyze_document_audit_relevance(
                        summary=doc_summary,
                        metadata=doc_metadata,
                        audit_id=audit_id,
                        audit_details=audit_details
                    )
                    
                    if relevance_result:
                        doc_s3_key = doc.get('s3_key')
                        doc_stored_name = doc.get('stored_name')
                        self._update_json_index_document(framework_id, audit_id, doc.get('id'), relevance_result, doc_s3_key=doc_s3_key, doc_stored_name=doc_stored_name)
                        if relevance_result.get('relevance_score', 0) >= 0.6:
                            self._store_audit_relevance(doc.get('id'), audit_id, relevance_result, doc_s3_key=doc_s3_key, doc_stored_name=doc_stored_name)
                
                # Analyze all database data
                db_results = self._analyze_database_data_relevance(audit_id, audit_details, all_database_data)
                for table_name, analyses in db_results.items():
                    for analysis in analyses:
                        record_id = analysis.get("record_id", 0)
                        if record_id:
                            self._update_json_index_database(framework_id, audit_id, table_name, record_id, analysis)
            
            debug_print(f"\n✅ Manual analysis completed for framework {framework_id}\n")
            
        except Exception as e:
            debug_print(f"❌ Error in manual analysis: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _get_audit_details(self, audit_id: int) -> Dict:
        """Get detailed audit information including policies, subpolicies, and compliances"""
        if not self.db_pool:
            return {}
        
        conn = self._get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor(dictionary=True)
        try:
            # Get audit basic info
            cursor.execute("""
                SELECT a.AuditId, a.FrameworkId, a.PolicyId, a.SubPolicyId,
                       a.Title as audit_title, a.Objective as audit_objective, a.Scope as audit_scope,
                       f.FrameworkName, p.PolicyName, sp.SubPolicyName
                FROM audit a
                LEFT JOIN frameworks f ON a.FrameworkId = f.FrameworkId
                LEFT JOIN policies p ON a.PolicyId = p.PolicyId
                LEFT JOIN subpolicies sp ON a.SubPolicyId = sp.SubPolicyId
                WHERE a.AuditId = %s
            """, (audit_id,))
            audit_info = cursor.fetchone()
            
            if not audit_info:
                return {}
            
            framework_id = audit_info.get('FrameworkId')
            
            result = {
                'audit_id': audit_id,
                'audit_title': audit_info.get('audit_title'),
                'audit_objective': audit_info.get('audit_objective'),
                'audit_scope': audit_info.get('audit_scope'),
                'framework_id': framework_id,
                'framework_name': audit_info.get('FrameworkName'),
                'policy_id': audit_info.get('PolicyId'),
                'policy_name': audit_info.get('PolicyName'),
                'subpolicy_id': audit_info.get('SubPolicyId'),
                'subpolicy_name': audit_info.get('SubPolicyName'),
                'policies': [],
                'subpolicies': [],
                'compliances': []
            }
            
            # Get ALL policies for this framework (user can select any in AI audit page)
            cursor.execute("""
                SELECT PolicyId, PolicyName, PolicyDescription
                FROM policies
                WHERE FrameworkId = %s
                ORDER BY PolicyName
            """, (framework_id,))
            policies = cursor.fetchall()
            result['policies'] = [
                {
                    'policy_id': p['PolicyId'],
                    'name': p['PolicyName'],
                    'description': p.get('PolicyDescription', '')
                }
                for p in policies
            ]
            
            # Get ALL subpolicies for this framework (user can select any in AI audit page)
            cursor.execute("""
                SELECT sp.SubPolicyId, sp.SubPolicyName, sp.Description, sp.PolicyId
                FROM subpolicies sp
                JOIN policies p ON sp.PolicyId = p.PolicyId
                WHERE p.FrameworkId = %s
                ORDER BY sp.SubPolicyName
            """, (framework_id,))
            subpolicies = cursor.fetchall()
            result['subpolicies'] = [
                {
                    'subpolicy_id': sp['SubPolicyId'],
                    'name': sp['SubPolicyName'],
                    'description': sp.get('Description', ''),
                    'policy_id': sp['PolicyId']
                }
                for sp in subpolicies
            ]
            
            # Get ALL compliances for this framework (user can select any in AI audit page)
            cursor.execute("""
                SELECT c.ComplianceId, c.ComplianceTitle, c.ComplianceItemDescription, 
                       c.SubPolicyId, sp.PolicyId
                FROM compliance c
                JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                JOIN policies p ON sp.PolicyId = p.PolicyId
                WHERE p.FrameworkId = %s
                ORDER BY c.ComplianceTitle
            """, (framework_id,))
            compliances = cursor.fetchall()
            result['compliances'] = [
                {
                    'compliance_id': c['ComplianceId'],
                    'title': c['ComplianceTitle'],
                    'description': c['ComplianceItemDescription'],
                    'subpolicy_id': c['SubPolicyId'],
                    'policy_id': c['PolicyId']
                }
                for c in compliances
            ]
            
            return result
            
        except Exception as e:
            debug_print(f"⚠️  Error getting audit details: {str(e)}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def _call_ollama(self, prompt: str, system_message: str = None, max_tokens: int = 800, temperature: float = 0.3) -> Optional[str]:
        """
        Call Ollama API instead of OpenAI
        Returns the response text or None if failed
        """
        try:
            url = f"{OLLAMA_BASE_URL}/api/chat"
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            if 'message' in result and 'content' in result['message']:
                return result['message']['content'].strip()
            return None
            
        except Exception as e:
            debug_print(f"⚠️  Error calling Ollama: {str(e)}")
            return None
    
    def _get_json_index_path(self, framework_id: int, audit_id: int, index_type: str = "documents") -> str:
        """
        Get path for JSON index file
        index_type: "documents" or "database"
        """
        if DJANGO_SETTINGS_AVAILABLE and hasattr(settings, 'MEDIA_ROOT'):
            base_dir = settings.MEDIA_ROOT
        else:
            base_dir = os.path.join(os.path.dirname(__file__), '../../MEDIA_ROOT')
        
        index_dir = os.path.join(base_dir, 'audit_indexes', f'framework_{framework_id}', f'audit_{audit_id}')
        os.makedirs(index_dir, exist_ok=True)
        
        filename = f"{index_type}_analysis.json"
        return os.path.join(index_dir, filename)
    
    def _load_json_index(self, file_path: str) -> Dict:
        """Load JSON index file, return empty dict if not exists"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            debug_print(f"⚠️  Error loading JSON index {file_path}: {str(e)}")
        return {
            "framework_id": None,
            "audit_id": None,
            "last_updated": None,
            "documents": [] if "documents" in file_path else {},
            "database_data": {} if "database" in file_path else []
        }
    
    def _save_json_index(self, file_path: str, data: Dict):
        """Save JSON index file"""
        try:
            data["last_updated"] = datetime.datetime.now().isoformat()
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Extract audit_id and framework_id from file path or data to trigger re-processing
            audit_id = data.get("audit_id")
            framework_id = data.get("framework_id")
            
            # Trigger audit re-processing when JSON is updated
            if audit_id and framework_id:
                try:
                    # Run in background thread to avoid blocking JSON save
                    def trigger_processing():
                        try:
                            # Use direct database call to avoid circular imports
                            if self.db_pool:
                                conn = self.db_pool.get_connection()
                                try:
                                    cursor = conn.cursor()
                                    # Mark all documents in ai_audit_data for this audit as 'pending'
                                    # This will cause them to be re-processed with the new matched compliances from JSON
                                    cursor.execute("""
                                        UPDATE ai_audit_data
                                        SET ai_processing_status = 'pending',
                                            updated_at = NOW()
                                        WHERE audit_id = %s
                                          AND (external_source != 'database_record' AND document_type != 'db_record')
                                          AND ai_processing_status != 'failed'
                                    """, [int(audit_id) if str(audit_id).isdigit() else audit_id])
                                    
                                    updated_count = cursor.rowcount
                                    conn.commit()
                                    debug_print(f"✅ Marked {updated_count} document(s) as 'pending' for re-processing in audit {audit_id}")
                                except Exception as db_err:
                                    conn.rollback()
                                    debug_print(f"⚠️  Database error triggering re-processing: {str(db_err)}")
                                finally:
                                    cursor.close()
                                    conn.close()
                            else:
                                debug_print(f"⚠️  No database pool available to trigger re-processing")
                        except Exception as trigger_err:
                            debug_print(f"⚠️  Error in background trigger: {str(trigger_err)}")
                    
                    trigger_thread = threading.Thread(target=trigger_processing, daemon=True)
                    trigger_thread.start()
                    debug_print(f"🔄 Started background thread to trigger audit re-processing for audit {audit_id}")
                except Exception as trigger_err:
                    # Don't fail JSON save if trigger fails
                    debug_print(f"⚠️  Error triggering audit re-processing (non-fatal): {str(trigger_err)}")
                    
        except Exception as e:
            debug_print(f"⚠️  Error saving JSON index {file_path}: {str(e)}")
    
    def _update_json_index_document(self, framework_id: int, audit_id: int, operation_id: int, analysis_result: Dict, doc_s3_key: str = None, doc_stored_name: str = None):
        """Update documents JSON index with new document analysis
        
        Uses s3_key/stored_name for deduplication instead of operation_id to handle
        same file uploaded with different modules.
        """
        file_path = self._get_json_index_path(framework_id, audit_id, "documents")
        data = self._load_json_index(file_path)
        
        if "documents" not in data:
            data["documents"] = []
        
        # Use s3_key or stored_name as the unique identifier (not operation_id)
        file_key = doc_s3_key or doc_stored_name
        
        # Find existing entry by s3_key/stored_name (preferred) or operation_id (fallback for backward compatibility)
        doc_index = None
        if file_key:
            doc_index = next((i for i, d in enumerate(data["documents"]) 
                            if (d.get("s3_key") == doc_s3_key) or (d.get("stored_name") == doc_stored_name)), None)
        
        # Fallback to operation_id if not found by file_key (for backward compatibility)
        if doc_index is None:
            doc_index = next((i for i, d in enumerate(data["documents"]) if d.get("operation_id") == operation_id), None)
        
        doc_entry = {
            "operation_id": operation_id,  # Keep for reference
            "s3_key": doc_s3_key,  # Add for deduplication
            "stored_name": doc_stored_name,  # Add for deduplication
            "analyzed_at": datetime.datetime.now().isoformat(),
            "relevance_score": analysis_result.get("relevance_score", 0),
            "relevance_reason": analysis_result.get("relevance_reason", ""),
            "matched_policies": analysis_result.get("matched_policies", []),
            "matched_subpolicies": analysis_result.get("matched_subpolicies", []),
            "matched_compliances": analysis_result.get("matched_compliances", [])
        }
        
        if doc_index is not None:
            # Update existing entry (preserve operation_id if it was different)
            existing = data["documents"][doc_index]
            if existing.get("operation_id") != operation_id:
                debug_print(f"      🔄 Updating existing document entry: s3_key/stored_name='{file_key[:50] if file_key else 'none'}...' (operation_id: {existing.get('operation_id')} -> {operation_id})")
            data["documents"][doc_index] = doc_entry
        else:
            data["documents"].append(doc_entry)
        
        data["framework_id"] = framework_id
        data["audit_id"] = audit_id
        self._save_json_index(file_path, data)
    
    def _update_json_index_database(self, framework_id: int, audit_id: int, table_name: str, record_id: int, analysis_result: Dict):
        """Update database data JSON index with new database record analysis"""
        file_path = self._get_json_index_path(framework_id, audit_id, "database")
        data = self._load_json_index(file_path)
        
        if "database_data" not in data:
            data["database_data"] = {}
        
        if table_name not in data["database_data"]:
            data["database_data"][table_name] = []
        
        # Update or add database record entry
        record_key = f"{table_name}_{record_id}"
        record_index = next((i for i, r in enumerate(data["database_data"][table_name]) if r.get("record_id") == record_id), None)
        record_entry = {
            "table_name": table_name,
            "record_id": record_id,
            "analyzed_at": datetime.datetime.now().isoformat(),
            "relevance_score": analysis_result.get("relevance_score", 0),
            "relevance_reason": analysis_result.get("relevance_reason", ""),
            "matched_policies": analysis_result.get("matched_policies", []),
            "matched_subpolicies": analysis_result.get("matched_subpolicies", []),
            "matched_compliances": analysis_result.get("matched_compliances", [])
        }
        
        if record_index is not None:
            data["database_data"][table_name][record_index] = record_entry
        else:
            data["database_data"][table_name].append(record_entry)
        
        data["framework_id"] = framework_id
        data["audit_id"] = audit_id
        self._save_json_index(file_path, data)
    
    def _analyze_document_audit_relevance(self, summary: str, metadata: Dict, audit_id: int, audit_details: Dict) -> Optional[Dict]:
        """
        Use Ollama to analyze if document is relevant to a specific audit
        Returns relevance score, reason, and matched policies/compliances
        """
        if not OLLAMA_AVAILABLE:
            return None
        
        try:
            
            # Build audit context - emphasize audit purpose and why it's being conducted
            audit_context = f"=== AUDIT PURPOSE AND CONTEXT ===\n"
            audit_context += f"Audit Title: {audit_details.get('audit_title', 'Not specified')}\n"
            if audit_details.get('audit_objective'):
                audit_context += f"Audit Objective (WHY this audit is being conducted): {audit_details.get('audit_objective')[:800]}\n"
            if audit_details.get('audit_scope'):
                audit_context += f"Audit Scope (WHAT is being audited): {audit_details.get('audit_scope')[:800]}\n"
            audit_context += f"\nFramework: {audit_details.get('framework_name', 'Unknown')}\n"
            if audit_details.get('policy_name'):
                audit_context += f"Assigned Policy: {audit_details.get('policy_name')}\n"
            if audit_details.get('subpolicy_name'):
                audit_context += f"Assigned Subpolicy: {audit_details.get('subpolicy_name')}\n"
            
            # Add ALL policies in framework (user can select any in AI audit page)
            policies = audit_details.get('policies', [])
            if policies:
                audit_context += f"\nAll Available Policies in Framework ({len(policies)} total):\n"
                # Include all policies but limit description length
                for i, policy in enumerate(policies[:50], 1):  # Limit to first 50 for token management
                    desc = policy.get('description', '')[:150] if policy.get('description') else 'No description'
                    audit_context += f"{i}. [ID:{policy.get('policy_id')}] {policy.get('name', 'Unknown')}: {desc}\n"
                if len(policies) > 50:
                    audit_context += f"... and {len(policies) - 50} more policies\n"
            
            # Add ALL subpolicies in framework
            subpolicies = audit_details.get('subpolicies', [])
            if subpolicies:
                audit_context += f"\nAll Available Subpolicies in Framework ({len(subpolicies)} total):\n"
                for i, subpolicy in enumerate(subpolicies[:50], 1):  # Limit to first 50
                    desc = subpolicy.get('description', '')[:150] if subpolicy.get('description') else 'No description'
                    audit_context += f"{i}. [ID:{subpolicy.get('subpolicy_id')}] {subpolicy.get('name', 'Unknown')}: {desc}\n"
                if len(subpolicies) > 50:
                    audit_context += f"... and {len(subpolicies) - 50} more subpolicies\n"
            
            # Add ALL compliance requirements in framework
            compliances = audit_details.get('compliances', [])
            if compliances:
                audit_context += f"\nAll Available Compliance Requirements in Framework ({len(compliances)} total):\n"
                for i, comp in enumerate(compliances[:150], 1):  # Increased limit to 150 for better coverage
                    comp_id = comp.get('compliance_id') or comp.get('ComplianceId')
                    comp_title = comp.get('title') or comp.get('ComplianceTitle') or 'Unknown'
                    desc = comp.get('description') or comp.get('ComplianceItemDescription') or 'No description'
                    desc_short = desc[:200] if desc else 'No description'  # Increased length
                    audit_context += f"{i}. [ID:{comp_id}] {comp_title}: {desc_short}\n"
                if len(compliances) > 150:
                    audit_context += f"... and {len(compliances) - 150} more compliance requirements\n"
            
            # Create prompt
            prompt = f"""You are an expert GRC auditor. Analyze if this document is useful for conducting this audit.

CRITICAL: First understand WHAT this audit is about and WHY it's being conducted by reading the Audit Purpose and Context section below.
Then determine if the document helps achieve the audit's objectives and addresses what needs to be audited.

IMPORTANT: In the AI audit page, users can select ANY policies, subpolicies, and compliances from the framework. 
Therefore, analyze the document's relevance against ALL available framework elements, not just the audit's assigned ones.

Document Information:
- Title: {metadata.get('title', 'Unknown')}
- Summary: {summary[:1000]}

Audit Context:
{audit_context}

Analyze and determine:
1. How relevant is this document for conducting this audit? (Score: 0.0 to 1.0)
   - FIRST: Consider if the document helps achieve the audit's OBJECTIVE and addresses what's in the audit's SCOPE
   - Consider if the document addresses ANY of the policies, subpolicies, or compliance requirements listed above
   - Score higher if the document directly supports the audit's purpose and addresses multiple framework elements, especially compliance requirements
   - A document is highly relevant if it provides evidence or information needed to fulfill the audit's objective
2. Why is it relevant or not relevant?
   - Explain how the document relates to the audit's OBJECTIVE and SCOPE
   - Explain which specific policies/subpolicies/compliances the document addresses
   - Be specific about which compliance requirements are addressed and how they relate to the audit's purpose
3. Which specific policies/subpolicies/compliances does this document address? 
   - CRITICAL: You MUST identify compliances if the document addresses any compliance requirements
   - Match the document content to compliance requirements by their titles and descriptions
   - Consider how these framework elements relate to the audit's objective
   - Only use IDs from the lists provided above. Do NOT use IDs from other frameworks.
   - Only include IDs that appear in the "All Available Policies", "All Available Subpolicies", or "All Available Compliance Requirements" lists shown above.
   - If an ID is not in the lists above, do NOT include it in the matched arrays.
   - IMPORTANT: Always include matched_compliances array, even if empty. If the document addresses compliance requirements, you MUST include their IDs.

Return ONLY valid JSON in this exact format:
{{
    "relevance_score": 0.85,
    "relevance_reason": "Document contains detailed access control procedures that directly address compliance requirements for user authentication. Specifically addresses Policy ID 5, Subpolicy ID 12, and Compliance IDs 30, 31.",
    "matched_policies": [5],
    "matched_subpolicies": [12],
    "matched_compliances": [30, 31]
}}

Focus on content relevance, not just keyword matching. Score based on how well the document addresses ANY of the audit's framework requirements that users might select.
IMPORTANT: Only return IDs that are present in the framework lists provided above."""

            system_message = "You are an expert GRC auditor specializing in document-audit relevance analysis. Always return valid JSON with matched_policies, matched_subpolicies, and matched_compliances arrays. You MUST identify specific compliance requirements that the document addresses."
            
            result_text = self._call_ollama(
                prompt=prompt,
                system_message=system_message,
                max_tokens=800,
                temperature=0.3
            )
            
            if not result_text:
                return None
            
            # Parse JSON response - handle both pure JSON and markdown responses
            import re
            result_json = None
            
            # First, try to extract JSON from markdown code blocks
            json_code_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_code_block:
                try:
                    result_json = json.loads(json_code_block.group(1))
                except:
                    pass
            
            # If not found, try to extract JSON object directly
            if not result_json:
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
                if json_match:
                    try:
                        result_json = json.loads(json_match.group())
                    except:
                        pass
            
            # If still not found, try parsing markdown format and convert to JSON
            if not result_json:
                try:
                    # Extract relevance_score from markdown
                    score_match = re.search(r'(?:relevance_score|Relevance Score)[:\s]*([0-9.]+)', result_text, re.IGNORECASE)
                    score = float(score_match.group(1)) if score_match else 0.0
                    
                    # Extract relevance_reason
                    reason_match = re.search(r'(?:relevance_reason|Relevance Reason)[:\s]*(.+?)(?:\n\n|\n\*\*|$)', result_text, re.IGNORECASE | re.DOTALL)
                    reason = reason_match.group(1).strip() if reason_match else ""
                    
                    # Extract matched arrays
                    policies_match = re.search(r'(?:matched_policies|Matched Policies)[:\s]*\[?([0-9,\s]+)\]?', result_text, re.IGNORECASE)
                    policies = []
                    if policies_match:
                        policies = [int(x.strip()) for x in policies_match.group(1).split(',') if x.strip().isdigit()]
                    
                    subpolicies_match = re.search(r'(?:matched_subpolicies|Matched Subpolicies)[:\s]*\[?([0-9,\s]+)\]?', result_text, re.IGNORECASE)
                    subpolicies = []
                    if subpolicies_match:
                        subpolicies = [int(x.strip()) for x in subpolicies_match.group(1).split(',') if x.strip().isdigit()]
                    
                    compliances_match = re.search(r'(?:matched_compliances|Matched Compliances)[:\s]*\[?([0-9,\s]+)\]?', result_text, re.IGNORECASE)
                    compliances = []
                    if compliances_match:
                        compliances = [int(x.strip()) for x in compliances_match.group(1).split(',') if x.strip().isdigit()]
                    
                    result_json = {
                        "relevance_score": score,
                        "relevance_reason": reason,
                        "matched_policies": policies,
                        "matched_subpolicies": subpolicies,
                        "matched_compliances": compliances
                    }
                except Exception as parse_err:
                    debug_print(f"      ⚠️  Failed to parse markdown response: {str(parse_err)}")
                    return None
            
            if not result_json:
                debug_print(f"      ⚠️  Could not parse response as JSON or markdown")
                debug_print(f"      Response preview: {result_text[:200]}")
                return None
            
            # Validate and filter matched IDs to ensure they belong to the current framework
            framework_policy_ids = {p.get('policy_id') or p.get('PolicyId') for p in audit_details.get('policies', [])}
            framework_subpolicy_ids = {sp.get('subpolicy_id') or sp.get('SubPolicyId') for sp in audit_details.get('subpolicies', [])}
            framework_compliance_ids = {c.get('compliance_id') or c.get('ComplianceId') for c in audit_details.get('compliances', [])}
            
            debug_print(f"      📊 Framework has {len(framework_policy_ids)} policies, {len(framework_subpolicy_ids)} subpolicies, {len(framework_compliance_ids)} compliances")
            
            # Filter matched policies - only keep IDs that exist in this framework
            matched_policies = result_json.get('matched_policies', [])
            if isinstance(matched_policies, list):
                original_policies = matched_policies.copy()
                result_json['matched_policies'] = [pid for pid in matched_policies if pid in framework_policy_ids]
                filtered_policies = set(original_policies) - set(result_json['matched_policies'])
                if filtered_policies:
                    debug_print(f"      ⚠️  Filtered out policy IDs from other frameworks: {filtered_policies}")
                debug_print(f"      ✅ Matched {len(result_json['matched_policies'])} policies: {result_json['matched_policies']}")
            
            # Filter matched subpolicies - only keep IDs that exist in this framework
            matched_subpolicies = result_json.get('matched_subpolicies', [])
            if isinstance(matched_subpolicies, list):
                original_subpolicies = matched_subpolicies.copy()
                result_json['matched_subpolicies'] = [sid for sid in matched_subpolicies if sid in framework_subpolicy_ids]
                filtered_subpolicies = set(original_subpolicies) - set(result_json['matched_subpolicies'])
                if filtered_subpolicies:
                    debug_print(f"      ⚠️  Filtered out subpolicy IDs from other frameworks: {filtered_subpolicies}")
                debug_print(f"      ✅ Matched {len(result_json['matched_subpolicies'])} subpolicies: {result_json['matched_subpolicies']}")
            
            # Filter matched compliances - only keep IDs that exist in this framework
            matched_compliances = result_json.get('matched_compliances', [])
            if not matched_compliances:
                matched_compliances = []  # Ensure it's always a list
            if isinstance(matched_compliances, list):
                original_compliances = matched_compliances.copy()
                result_json['matched_compliances'] = [cid for cid in matched_compliances if cid in framework_compliance_ids]
                filtered_compliances = set(original_compliances) - set(result_json['matched_compliances'])
                if filtered_compliances:
                    debug_print(f"      ⚠️  Filtered out compliance IDs from other frameworks: {filtered_compliances}")
                debug_print(f"      ✅ Matched {len(result_json['matched_compliances'])} compliances: {result_json['matched_compliances']}")
            else:
                result_json['matched_compliances'] = []
                debug_print(f"      ⚠️  matched_compliances was not a list, reset to empty array")
            
            return result_json
                
        except json.JSONDecodeError as e:
            debug_print(f"⚠️  Failed to parse AI response as JSON: {str(e)}")
            debug_print(f"   Response: {result_text[:200]}")
            return None
        except Exception as e:
            debug_print(f"⚠️  Error in audit relevance analysis: {str(e)}")
            return None
    
    def _store_audit_relevance(self, operation_id: int, audit_id: int, relevance_result: Dict, doc_s3_key: str = None, doc_stored_name: str = None):
        """Store audit relevance analysis in document_audit_relevance table
        
        Checks for existing records by s3_key/stored_name to avoid duplicates when
        the same file is uploaded with different modules.
        """
        if not self.db_pool:
            return
        
        conn = self._get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        try:
            # Get S3 URL and s3_key/stored_name from file_operations
            s3_url = None
            s3_key_from_db = None
            stored_name_from_db = None
            cursor.execute("SELECT s3_url, s3_key, stored_name FROM file_operations WHERE id = %s", (operation_id,))
            result = cursor.fetchone()
            if result:
                s3_url = result[0] if len(result) > 0 else None
                s3_key_from_db = result[1] if len(result) > 1 else None
                stored_name_from_db = result[2] if len(result) > 2 else None
            
            # Use provided values or fallback to database values
            file_s3_key = doc_s3_key or s3_key_from_db
            file_stored_name = doc_stored_name or stored_name_from_db
            
            # Check if a record already exists for this s3_key/stored_name + audit_id combination
            # This prevents duplicate analysis when the same file is uploaded with different modules
            # We check by looking up other file_operations with the same s3_key/stored_name, then checking if they have relevance records
            existing_relevance_id = None
            if file_s3_key or file_stored_name:
                # Find other file_operations with the same s3_key or stored_name
                if file_s3_key:
                    cursor.execute("""
                        SELECT id FROM file_operations 
                        WHERE (s3_key = %s OR stored_name = %s) AND id != %s AND status = 'completed'
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (file_s3_key, file_s3_key, operation_id))
                else:
                    cursor.execute("""
                        SELECT id FROM file_operations 
                        WHERE stored_name = %s AND id != %s AND status = 'completed'
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (file_stored_name, operation_id))
                
                other_operation = cursor.fetchone()
                if other_operation:
                    other_op_id = other_operation[0]
                    # Check if that other operation_id already has a relevance record for this audit
                    cursor.execute("""
                        SELECT file_operation_id FROM document_audit_relevance 
                        WHERE file_operation_id = %s AND audit_id = %s
                        LIMIT 1
                    """, (other_op_id, audit_id))
                    existing = cursor.fetchone()
                    if existing:
                        existing_relevance_id = existing[0]
                        file_key_display = (file_s3_key or file_stored_name or 'none')[:50] if (file_s3_key or file_stored_name) else 'none'
                        debug_print(f"      🔄 Found existing relevance record for same file (s3_key/stored_name='{file_key_display}...') (file_operation_id={existing_relevance_id}, current operation_id={operation_id})")
            
            # Prepare JSON arrays for matched items
            matched_policies = json.dumps(relevance_result.get('matched_policies', []))
            matched_subpolicies = json.dumps(relevance_result.get('matched_subpolicies', []))
            matched_compliances = json.dumps(relevance_result.get('matched_compliances', []))
            
            # If existing record found, update it instead of creating duplicate
            if existing_relevance_id:
                # Update the existing record (may have different file_operation_id but same s3_key/stored_name)
                # Try to update with s3_key/stored_name columns if they exist, otherwise just update basic fields
                try:
                    query = """
                    UPDATE document_audit_relevance 
                    SET file_operation_id = %s,
                        s3_url = %s,
                        s3_key = %s,
                        stored_name = %s,
                        relevance_score = %s,
                        relevance_reason = %s,
                        matched_policies = %s,
                        matched_subpolicies = %s,
                        matched_compliances = %s,
                        analyzed_at = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE file_operation_id = %s AND audit_id = %s
                    """
                    params = (
                        operation_id,  # Update to latest operation_id
                        s3_url,
                        file_s3_key,
                        file_stored_name,
                        float(relevance_result.get('relevance_score', 0)),
                        relevance_result.get('relevance_reason', '')[:1000],
                        matched_policies,
                        matched_subpolicies,
                        matched_compliances,
                        datetime.datetime.now(),
                        existing_relevance_id,
                        audit_id
                    )
                    cursor.execute(query, params)
                    debug_print(f"      ✅ Updated existing relevance record (same file, different module upload)")
                except mysql.connector.Error as col_err:
                    # If s3_key/stored_name columns don't exist, update without them
                    if 'Unknown column' in str(col_err):
                        query = """
                        UPDATE document_audit_relevance 
                        SET file_operation_id = %s,
                            s3_url = %s,
                            relevance_score = %s,
                            relevance_reason = %s,
                            matched_policies = %s,
                            matched_subpolicies = %s,
                            matched_compliances = %s,
                            analyzed_at = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE file_operation_id = %s AND audit_id = %s
                        """
                        params = (
                            operation_id,
                            s3_url,
                            float(relevance_result.get('relevance_score', 0)),
                            relevance_result.get('relevance_reason', '')[:1000],
                            matched_policies,
                            matched_subpolicies,
                            matched_compliances,
                            datetime.datetime.now(),
                            existing_relevance_id,
                            audit_id
                        )
                        cursor.execute(query, params)
                        debug_print(f"      ✅ Updated existing relevance record (s3_key/stored_name columns not available)")
                    else:
                        raise
            else:
                # Insert new record - try with s3_key/stored_name first, fallback if columns don't exist
                try:
                    query = """
                    INSERT INTO document_audit_relevance 
                    (file_operation_id, audit_id, s3_url, s3_key, stored_name, relevance_score, relevance_reason, 
                     matched_policies, matched_subpolicies, matched_compliances, analyzed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        s3_url = VALUES(s3_url),
                        s3_key = VALUES(s3_key),
                        stored_name = VALUES(stored_name),
                        relevance_score = VALUES(relevance_score),
                        relevance_reason = VALUES(relevance_reason),
                        matched_policies = VALUES(matched_policies),
                        matched_subpolicies = VALUES(matched_subpolicies),
                        matched_compliances = VALUES(matched_compliances),
                        analyzed_at = VALUES(analyzed_at),
                        updated_at = CURRENT_TIMESTAMP
                    """
                    params = (
                        operation_id,
                        audit_id,
                        s3_url,
                        file_s3_key,
                        file_stored_name,
                        float(relevance_result.get('relevance_score', 0)),
                        relevance_result.get('relevance_reason', '')[:1000],
                        matched_policies,
                        matched_subpolicies,
                        matched_compliances,
                        datetime.datetime.now()
                    )
                    cursor.execute(query, params)
                    debug_print(f"      💾 Stored new relevance in database")
                except mysql.connector.Error as col_err:
                    # If s3_key/stored_name columns don't exist, insert without them
                    if 'Unknown column' in str(col_err):
                        query = """
                        INSERT INTO document_audit_relevance 
                        (file_operation_id, audit_id, s3_url, relevance_score, relevance_reason, 
                         matched_policies, matched_subpolicies, matched_compliances, analyzed_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            s3_url = VALUES(s3_url),
                            relevance_score = VALUES(relevance_score),
                            relevance_reason = VALUES(relevance_reason),
                            matched_policies = VALUES(matched_policies),
                            matched_subpolicies = VALUES(matched_subpolicies),
                            matched_compliances = VALUES(matched_compliances),
                            analyzed_at = VALUES(analyzed_at),
                            updated_at = CURRENT_TIMESTAMP
                        """
                        params = (
                            operation_id,
                            audit_id,
                            s3_url,
                            float(relevance_result.get('relevance_score', 0)),
                            relevance_result.get('relevance_reason', '')[:1000],
                            matched_policies,
                            matched_subpolicies,
                            matched_compliances,
                            datetime.datetime.now()
                        )
                        cursor.execute(query, params)
                        debug_print(f"      💾 Stored new relevance in database (s3_key/stored_name columns not available)")
                    else:
                        raise
            
            conn.commit()
            
            # Auto-process: Create ai_audit_data entries for ALL audit types
            # This automatically links relevant documents to audits without user interaction
            try:
                debug_print(f"      🤖 Triggering auto-processing for audit {audit_id}")
                # Trigger auto-processing in background thread for all audit types
                import threading
                auto_process_thread = threading.Thread(
                    target=self._auto_process_relevant_document,
                    args=(operation_id, audit_id, relevance_result),
                    daemon=True,
                    name=f"AutoProcess-{operation_id}-{audit_id}"
                )
                auto_process_thread.start()
                debug_print(f"      ✅ Auto-processing thread started")
            except Exception as auto_err:
                debug_print(f"      ⚠️  Error starting auto-processing: {str(auto_err)}")
                import traceback
                traceback.print_exc()
                # Don't fail the whole operation if auto-processing fails
            
        except mysql.connector.Error as e:
            debug_print(f"      ❌ Database error storing relevance: {str(e)}")
        except Exception as e:
            debug_print(f"      ❌ Error storing relevance: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    def _auto_process_relevant_document(self, operation_id: int, audit_id: int, relevance_result: Dict):
        """
        Automatically create ai_audit_data entries and trigger compliance checks
        for documents from Document Handling that are relevant to an AI audit.
        This runs in a background thread after relevance is stored.
        
        CRITICAL: This now processes ALL relevant documents from documents_analysis.json,
        not just the one that was uploaded. This ensures all matched documents are processed.
        """
        try:
            debug_print(f"\n{'='*60}")
            debug_print(f"🤖 AUTO-PROCESSING: Will process ALL relevant documents from JSON for Audit {audit_id}")
            debug_print(f"   (Triggered by document {operation_id})")
            debug_print(f"{'='*60}")
            
            if not self.db_pool:
                debug_print(f"      ❌ Database pool not available")
                return
            
            conn = self._get_db_connection()
            if not conn:
                debug_print(f"      ❌ Database connection failed")
                return
            
            cursor = conn.cursor(dictionary=True)
            
            try:
                # Get framework_id first (needed for JSON path)
                cursor.execute("SELECT FrameworkId FROM audit WHERE AuditId = %s", (audit_id,))
                audit_row = cursor.fetchone()
                if not audit_row or not audit_row.get('FrameworkId'):
                    debug_print(f"      ❌ No FrameworkId found for audit {audit_id}")
                    return
                
                framework_id = audit_row.get('FrameworkId')
                
                # STEP 1: Read documents_analysis.json to find ALL relevant documents
                all_relevant_documents_to_process = []  # List of (operation_id, matched_compliances) tuples
                
                try:
                    import os
                    import json
                    from django.conf import settings
                    
                    # Construct path to documents_analysis.json
                    json_path = os.path.join(
                        settings.MEDIA_ROOT,
                        'audit_indexes',
                        f'framework_{framework_id}',
                        f'audit_{audit_id}',
                        'documents_analysis.json'
                    )
                    
                    debug_print(f"      📋 Looking for documents_analysis.json at: {json_path}")
                    
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                json_data = json.load(f)
                            
                            documents_in_json = json_data.get('documents', [])
                            debug_print(f"      📋 Found {len(documents_in_json)} document(s) in documents_analysis.json - will process ALL documents with matched compliances")
                            
                            for doc_entry in documents_in_json:
                                doc_operation_id = doc_entry.get('operation_id')
                                matched_compliances_for_doc = doc_entry.get('matched_compliances', [])
                                
                                if matched_compliances_for_doc and doc_operation_id:
                                    # This document is relevant - add it to the processing list
                                    all_relevant_documents_to_process.append((doc_operation_id, matched_compliances_for_doc))
                                    debug_print(f"      📋 Document operation_id={doc_operation_id} has {len(matched_compliances_for_doc)} matched compliances: {matched_compliances_for_doc} - will be processed")
                                elif doc_operation_id:
                                    debug_print(f"      📋 Document operation_id={doc_operation_id} has NO matched compliances - skipping")
                            
                            debug_print(f"      ✅✅✅ WILL PROCESS {len(all_relevant_documents_to_process)} relevant document(s) from JSON")
                            
                        except Exception as json_err:
                            debug_print(f"      ⚠️ Could not read/parse documents_analysis.json: {json_err}")
                            import traceback
                            traceback.print_exc()
                    else:
                        debug_print(f"      ℹ️ documents_analysis.json not found at {json_path}, will process only uploaded document")
                
                except Exception as json_read_err:
                    debug_print(f"      ⚠️ Error reading documents_analysis.json: {json_read_err}")
                    import traceback
                    traceback.print_exc()
                
                # STEP 2: If no documents found in JSON, add the uploaded document to processing list
                if not all_relevant_documents_to_process:
                    debug_print(f"      📋 No relevant documents found in JSON - will process only the uploaded document (file_operation_id={operation_id})")
                    # Get matched compliances from relevance_result for the uploaded document
                    matched_compliances_for_uploaded = relevance_result.get('matched_compliances', [])
                    if matched_compliances_for_uploaded:
                        all_relevant_documents_to_process.append((operation_id, matched_compliances_for_uploaded))
                        debug_print(f"      ✅✅✅ MATCHED COMPLIANCES FOUND for file_operation_id={operation_id}, audit_id={audit_id}")
                        debug_print(f"      📋 Found {len(matched_compliances_for_uploaded)} matched compliances: {matched_compliances_for_uploaded}")
                    else:
                        # Add with empty compliances (will be processed but might not have matches)
                        all_relevant_documents_to_process.append((operation_id, []))
                
                # STEP 3: Also ensure the uploaded document is in the processing list (if it's not already there)
                uploaded_doc_in_list = any(op_id == operation_id for op_id, _ in all_relevant_documents_to_process)
                if not uploaded_doc_in_list:
                    debug_print(f"      📋 Adding uploaded document (file_operation_id={operation_id}) to processing list")
                    matched_compliances_for_uploaded = relevance_result.get('matched_compliances', [])
                    all_relevant_documents_to_process.append((operation_id, matched_compliances_for_uploaded))
                
                # STEP 4: Log what documents we found
                debug_print(f"      🔄 Found {len(all_relevant_documents_to_process)} relevant document(s) to process from JSON:")
                for op_id, comps in all_relevant_documents_to_process:
                    debug_print(f"        - operation_id={op_id} with {len(comps)} matched compliances: {comps}")
                
                # STEP 5: Process ALL documents from the list
                all_created_document_ids = []  # Accumulate all document IDs created
                
                # Get user_id once (will be used for all documents)
                # First, get it from the uploaded document
                cursor.execute("""
                    SELECT user_id FROM file_operations WHERE id = %s
                """, (operation_id,))
                uploaded_file_op = cursor.fetchone()
                raw_user_id = uploaded_file_op.get('user_id') if uploaded_file_op else None

                # Normalize uploaded_by user_id (ai_audit_data.uploaded_by is INT)
                uploaded_by = None
                if raw_user_id is not None:
                    try:
                        uploaded_by = int(raw_user_id)
                        debug_print(f"      👤 Using numeric user_id: {uploaded_by}")
                    except (ValueError, TypeError):
                        try:
                            cursor.execute("SELECT UserId FROM users WHERE UserName = %s LIMIT 1", (raw_user_id,))
                            user_row = cursor.fetchone()
                            if user_row and user_row.get('UserId'):
                                uploaded_by = int(user_row.get('UserId'))
                                debug_print(f"      👤 Resolved username '{raw_user_id}' to UserId {uploaded_by}")
                            else:
                                cursor.execute("SELECT UserId FROM users WHERE LOWER(UserName) = LOWER(%s) LIMIT 1", (raw_user_id,))
                                user_row = cursor.fetchone()
                                if user_row and user_row.get('UserId'):
                                    uploaded_by = int(user_row.get('UserId'))
                                    debug_print(f"      👤 Resolved username '{raw_user_id}' (case-insensitive) to UserId {uploaded_by}")
                        except Exception as user_lookup_err:
                            debug_print(f"      ⚠️  Error in user lookup query: {str(user_lookup_err)}")
                
                if not uploaded_by:
                    debug_print(f"      ⚠️  Could not resolve user_id (raw_user_id={raw_user_id}); notifications will be skipped")
                
                # Track processed operation_ids to avoid duplicates
                processed_operation_ids = set()
                
                # Process each document from the list
                for doc_operation_id, doc_matched_compliances in all_relevant_documents_to_process:
                    try:
                        # Skip if already processed in this batch
                        if doc_operation_id in processed_operation_ids:
                            debug_print(f"      ⏭️ Skipping duplicate document operation_id={doc_operation_id} (already processed in this batch)")
                            continue
                        
                        debug_print(f"      📄 Processing document operation_id={doc_operation_id} with {len(doc_matched_compliances)} matched compliances: {doc_matched_compliances}")
                        
                        # Get file information for this document
                        cursor.execute("""
                            SELECT file_name, original_name, s3_url, s3_key, file_size, 
                                   file_type, content_type, stored_name, user_id
                            FROM file_operations 
                            WHERE id = %s AND status = 'completed'
                        """, (doc_operation_id,))
                        file_op = cursor.fetchone()
                        
                        if not file_op:
                            debug_print(f"      ⚠️ File operation {doc_operation_id} not found or not completed - skipping")
                            continue
                        
                        file_name = file_op.get('file_name') or file_op.get('original_name') or 'Unknown Document'
                        # ai_audit_data.document_name has limited length (e.g. 255) - truncate to avoid Data too long
                        document_name_truncated = (file_name or '')[:255]
                        s3_url = file_op.get('s3_url')
                        s3_key = file_op.get('s3_key')
                        file_size = file_op.get('file_size') or 0
                        file_type = file_op.get('file_type') or 'pdf'
                        content_type = file_op.get('content_type') or 'application/pdf'
                        stored_name = file_op.get('stored_name')
                        
                        # Determine external_id for duplicate check
                        external_id = str(doc_operation_id)  # Use operation_id for lookup
                        compact_external_id = s3_key or stored_name or external_id
                        if compact_external_id and len(compact_external_id) > 100:
                            compact_external_id = compact_external_id[-100:]
                        
                        # Check if this document is already processed for this audit
                        cursor.execute("""
                            SELECT COUNT(*) as count FROM ai_audit_data 
                            WHERE audit_id = %s 
                              AND external_source = 'evidence_attachment'
                              AND (external_id = %s OR external_id = %s OR external_id = %s)
                              AND ai_processing_status != 'failed'
                        """, (audit_id, external_id, compact_external_id, stored_name if stored_name else ''))
                        count_result = cursor.fetchone()
                        existing_count = count_result.get('count', 0) if count_result else 0
                        
                        if existing_count > 0:
                            debug_print(f"      ⏭️ Document operation_id={doc_operation_id} already exists in ai_audit_data for audit {audit_id} ({existing_count} record(s)) - skipping to avoid duplicate")
                            processed_operation_ids.add(doc_operation_id)
                            continue
                        
                        # Mark as processed to avoid duplicates within this batch
                        processed_operation_ids.add(doc_operation_id)
                        
                        # Get matched compliances, policies, and subpolicies for this document
                        matched_compliances = doc_matched_compliances
                        # Get policies/subpolicies from compliances
                        matched_policies = []
                        matched_subpolicies = []
                        if matched_compliances:
                            cursor.execute(f"""
                                SELECT DISTINCT c.SubPolicyId, sp.PolicyId
                                FROM compliance c
                                LEFT JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                                WHERE c.ComplianceId IN ({','.join(['%s'] * len(matched_compliances))})
                            """, matched_compliances)
                            comp_infos = cursor.fetchall()
                            matched_policies = list(set([info.get('PolicyId') for info in comp_infos if info.get('PolicyId')]))
                            matched_subpolicies = list(set([info.get('SubPolicyId') for info in comp_infos if info.get('SubPolicyId')]))
                        
                        debug_print(f"        📋 Matched Compliances: {len(matched_compliances)}")
                        debug_print(f"        📋 Matched Policies: {len(matched_policies)}")
                        debug_print(f"        📋 Matched Subpolicies: {len(matched_subpolicies)}")
                        
                        # Determine document_path (external_id already set above for duplicate check)
                        document_path = s3_key or stored_name or f"file_operations/{doc_operation_id}/{file_name}"
                        
                        # Create mappings: one per compliance for this document
                        mappings_to_create = []
                        
                        if matched_compliances:
                            # Create one mapping per compliance
                            for compliance_id in matched_compliances:
                                cursor.execute("""
                                    SELECT c.SubPolicyId, sp.PolicyId
                                    FROM compliance c
                                    LEFT JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                                    WHERE c.ComplianceId = %s
                                """, (compliance_id,))
                                comp_info = cursor.fetchone()
                                policy_id = comp_info.get('PolicyId') if comp_info else None
                                subpolicy_id = comp_info.get('SubPolicyId') if comp_info else None
                                
                                mappings_to_create.append({
                                    'policy_id': policy_id,
                                    'subpolicy_id': subpolicy_id,
                                    'compliance_id': compliance_id
                                })
                        elif matched_subpolicies:
                            # Fallback: create one mapping per subpolicy
                            for subpolicy_id in matched_subpolicies:
                                cursor.execute("SELECT PolicyId FROM subpolicies WHERE SubPolicyId = %s", (subpolicy_id,))
                                sub_info = cursor.fetchone()
                                policy_id = sub_info.get('PolicyId') if sub_info else None
                                
                                mappings_to_create.append({
                                    'policy_id': policy_id,
                                    'subpolicy_id': subpolicy_id,
                                    'compliance_id': None
                                })
                        elif matched_policies:
                            # Fallback: create one mapping per policy
                            for policy_id in matched_policies:
                                mappings_to_create.append({
                                    'policy_id': policy_id,
                                    'subpolicy_id': None,
                                    'compliance_id': None
                                })
                        else:
                            # No matches - create a single unmapped entry
                            mappings_to_create.append({
                                'policy_id': None,
                                'subpolicy_id': None,
                                'compliance_id': None
                            })
                        
                        debug_print(f"        📝 Creating {len(mappings_to_create)} mapping(s) for document operation_id={doc_operation_id}")
                        
                        # Create ai_audit_data entries for this document
                        doc_created_document_ids = []
                        cursor.close()  # Close dictionary cursor
                        cursor = conn.cursor()  # Use regular cursor for inserts
                        
                        for mapping in mappings_to_create:
                            try:
                                # Determine mime_type from content_type or file_type
                                mime_type = content_type
                                if not mime_type:
                                    if file_type.lower() == 'pdf':
                                        mime_type = 'application/pdf'
                                    elif file_type.lower() in ['doc', 'docx']:
                                        mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                                    elif file_type.lower() in ['xls', 'xlsx']:
                                        mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                                    else:
                                        mime_type = 'application/octet-stream'
                                
                                # Insert into ai_audit_data
                                # Try with compliance_id and FrameworkId first
                                insert_query = """
                                    INSERT INTO ai_audit_data 
                                    (audit_id, document_id, document_name, document_path, document_type, 
                                     file_size, mime_type, uploaded_by, ai_processing_status, uploaded_date,
                                     policy_id, subpolicy_id, compliance_id, upload_status, external_source, external_id,
                                     FrameworkId, created_at, updated_at)
                                    VALUES (%s, 0, %s, %s, %s, %s, %s, %s, 'pending', NOW(),
                                           %s, %s, %s, 'uploaded', 'evidence_attachment', %s, %s, NOW(), NOW())
                                """
                                
                                try:
                                    cursor.execute(insert_query, [
                                        audit_id,
                                        document_name_truncated,
                                        document_path,
                                        file_type[:50],  # Truncate to fit varchar(50)
                                        file_size,
                                        mime_type,
                                        uploaded_by,
                                        mapping['policy_id'],
                                        mapping['subpolicy_id'],
                                        mapping['compliance_id'],  # Store compliance_id from matched compliances
                                        external_id,
                                        framework_id
                                    ])
                                except mysql.connector.Error as insert_err:
                                    error_str = str(insert_err).lower()
                                    # Handle missing compliance_id column
                                    if 'unknown column' in error_str and 'compliance_id' in error_str:
                                        insert_query_no_compliance = """
                                            INSERT INTO ai_audit_data 
                                            (audit_id, document_id, document_name, document_path, document_type, 
                                             file_size, mime_type, uploaded_by, ai_processing_status, uploaded_date,
                                             policy_id, subpolicy_id, upload_status, external_source, external_id,
                                             FrameworkId, created_at, updated_at)
                                            VALUES (%s, 0, %s, %s, %s, %s, %s, %s, 'pending', NOW(),
                                                   %s, %s, 'uploaded', 'evidence_attachment', %s, %s, NOW(), NOW())
                                        """
                                        cursor.execute(insert_query_no_compliance, [
                                            audit_id,
                                            document_name_truncated,
                                            document_path,
                                            file_type[:50],
                                            file_size,
                                            mime_type,
                                            uploaded_by,
                                            mapping['policy_id'],
                                            mapping['subpolicy_id'],
                                            external_id,
                                            framework_id
                                        ])
                                        debug_print(f"        ⚠️ compliance_id column not found - inserted without it")
                                    # Handle missing FrameworkId column
                                    elif 'unknown column' in error_str and 'frameworkid' in error_str:
                                        insert_query_no_framework = """
                                            INSERT INTO ai_audit_data 
                                            (audit_id, document_id, document_name, document_path, document_type, 
                                             file_size, mime_type, uploaded_by, ai_processing_status, uploaded_date,
                                             policy_id, subpolicy_id, compliance_id, upload_status, external_source, external_id,
                                             created_at, updated_at)
                                            VALUES (%s, 0, %s, %s, %s, %s, %s, %s, 'pending', NOW(),
                                                   %s, %s, %s, 'uploaded', 'evidence_attachment', %s, NOW(), NOW())
                                        """
                                        cursor.execute(insert_query_no_framework, [
                                            audit_id,
                                            document_name_truncated,
                                            document_path,
                                            file_type[:50],
                                            file_size,
                                            mime_type,
                                            uploaded_by,
                                            mapping['policy_id'],
                                            mapping['subpolicy_id'],
                                            mapping['compliance_id'],
                                            external_id
                                        ])
                                        debug_print(f"        ⚠️ FrameworkId column not found - inserted without it")
                                    # Handle both missing
                                    elif 'unknown column' in error_str:
                                        insert_query_minimal = """
                                            INSERT INTO ai_audit_data 
                                            (audit_id, document_id, document_name, document_path, document_type, 
                                             file_size, mime_type, uploaded_by, ai_processing_status, uploaded_date,
                                             policy_id, subpolicy_id, upload_status, external_source, external_id,
                                             created_at, updated_at)
                                            VALUES (%s, 0, %s, %s, %s, %s, %s, %s, 'pending', NOW(),
                                                   %s, %s, 'uploaded', 'evidence_attachment', %s, NOW(), NOW())
                                        """
                                        cursor.execute(insert_query_minimal, [
                                            audit_id,
                                            document_name_truncated,
                                            document_path,
                                            file_type[:50],
                                            file_size,
                                            mime_type,
                                            uploaded_by,
                                            mapping['policy_id'],
                                            mapping['subpolicy_id'],
                                            external_id
                                        ])
                                        debug_print(f"        ⚠️ Some columns not found - inserted with minimal columns")
                                    else:
                                        raise
                                
                                # Get the created document_id
                                cursor.execute("SELECT LAST_INSERT_ID()")
                                result = cursor.fetchone()
                                document_id = result[0] if result else None
                                
                                if document_id:
                                    # Update document_id column
                                    cursor.execute("""
                                        UPDATE ai_audit_data 
                                        SET document_id = %s 
                                        WHERE id = %s
                                    """, [document_id, document_id])
                                    
                                    doc_created_document_ids.append(document_id)
                                    all_created_document_ids.append(document_id)
                                    debug_print(f"        ✅ Created mapping: document_id={document_id}, policy_id={mapping['policy_id']}, subpolicy_id={mapping['subpolicy_id']}, compliance_id={mapping['compliance_id']}")
                            
                            except Exception as mapping_err:
                                debug_print(f"        ❌ Error creating mapping: {str(mapping_err)}")
                                import traceback
                                traceback.print_exc()
                                continue
                        
                        conn.commit()
                        debug_print(f"        ✅ Finished processing document operation_id={doc_operation_id} - created {len(doc_created_document_ids)} record(s)")
                        
                        # Re-open dictionary cursor for next document
                        cursor.close()
                        cursor = conn.cursor(dictionary=True)
                        
                    except Exception as doc_process_err:
                        debug_print(f"      ❌ Error processing document {doc_operation_id}: {doc_process_err}")
                        import traceback
                        traceback.print_exc()
                        # Re-open dictionary cursor for next document
                        try:
                            cursor.close()
                        except:
                            pass
                        cursor = conn.cursor(dictionary=True)
                        continue
                
                cursor.close()
                debug_print(f"      ✅✅✅ Processed ALL {len(all_relevant_documents_to_process)} relevant document(s) from JSON - created {len(all_created_document_ids)} total record(s)")
                
                # Automatically trigger compliance checks for all created documents
                # Note: The compliance check will automatically detect if database evidence exists
                # and use COMBINED EVIDENCE approach (both document + database) if both are available
                if all_created_document_ids:
                    debug_print(f"      🔍 Triggering automatic compliance checks for {len(all_created_document_ids)} document(s)...")
                    debug_print(f"      📋 Note: Checks will automatically use COMBINED EVIDENCE if both document and database evidence exist")
                    
                    # Store compliance_ids for each document
                    # We need to track which compliance_id each document_id corresponds to
                    # Since we process documents in order, we can track this during creation
                    doc_compliance_map = {}
                    
                    # Re-query to get compliance_id (if column exists) and policy/subpolicy for each document_id
                    cursor = conn.cursor(dictionary=True)
                    for doc_id in all_created_document_ids:
                        compliance_id = None
                        policy_id = None
                        subpolicy_id = None
                        try:
                            # Try selecting with compliance_id first (newer schema)
                            cursor.execute("SELECT compliance_id, policy_id, subpolicy_id FROM ai_audit_data WHERE id = %s", (doc_id,))
                            doc_row = cursor.fetchone()
                            if doc_row:
                                compliance_id = doc_row.get('compliance_id')
                                policy_id = doc_row.get('policy_id')
                                subpolicy_id = doc_row.get('subpolicy_id')
                        except Exception as e:
                            # Older schema: compliance_id column may not exist, fall back to policy/subpolicy only
                            if 'unknown column' in str(e).lower() and 'compliance_id' in str(e).lower():
                                try:
                                    cursor.execute("SELECT policy_id, subpolicy_id FROM ai_audit_data WHERE id = %s", (doc_id,))
                                    doc_row = cursor.fetchone()
                                    if doc_row:
                                        policy_id = doc_row.get('policy_id')
                                        subpolicy_id = doc_row.get('subpolicy_id')
                                except Exception:
                                    pass
                            else:
                                # Any other SQL error - log minimal info and continue
                                debug_print(f"      ⚠️ Error reading ai_audit_data for auto-check (id={doc_id}): {str(e)}")
                        
                        doc_compliance_map[doc_id] = {
                            'compliance_id': compliance_id,
                            'policy_id': policy_id,
                            'subpolicy_id': subpolicy_id
                        }
                    cursor.close()
                    
                    def trigger_compliance_check(doc_id, audit_id_val, user_id_val, doc_info):
                        """Run compliance check in background thread"""
                        try:
                            import time
                            # Small delay to ensure database transaction is committed
                            time.sleep(2)
                            
                            compliance_id_val = doc_info.get('compliance_id')
                            policy_id_val = doc_info.get('policy_id')
                            subpolicy_id_val = doc_info.get('subpolicy_id')
                            
                            # Skip auto-check if no compliance_id AND no policy/subpolicy mapping
                            # (This means the document has no matched compliances from relevance analysis)
                            if not compliance_id_val and not policy_id_val and not subpolicy_id_val:
                                debug_print(f"      ⏭️ Skipping auto-check for document_id={doc_id} - no compliance_id, policy_id, or subpolicy_id (document has no matched compliances)")
                                return
                            
                            # Import the internal compliance check function
                            import sys
                            import os
                            # Add the Django project root to path
                            django_project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                            if django_project_path not in sys.path:
                                sys.path.insert(0, django_project_path)
                            
                            # Setup Django environment
                            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grc.settings')
                            import django
                            django.setup()
                            
                            # Now import and call the internal function
                            from grc.routes.Audit.ai_audit_api import _check_document_compliance_internal
                            
                            # Call internal compliance check
                            # Pass compliance_id if available, otherwise let it use policy/subpolicy defaults
                            result = _check_document_compliance_internal(
                                audit_id=audit_id_val,
                                document_id=doc_id,
                                user_id=user_id_val,
                                selected_compliance_ids=[compliance_id_val] if compliance_id_val else None
                            )
                            
                            if result.get('success'):
                                debug_print(f"      ✅ Auto-compliance check completed for document_id={doc_id} (compliance_id={compliance_id_val}, policy_id={policy_id_val}, subpolicy_id={subpolicy_id_val})")
                            else:
                                debug_print(f"      ⚠️ Auto-compliance check failed for document_id={doc_id}: {result.get('error', 'Unknown error')}")
                        except Exception as check_err:
                            debug_print(f"      ❌ Error in auto-compliance check for document_id={doc_id}: {str(check_err)}")
                            import traceback
                            traceback.print_exc()
                    
                    # Start compliance checks in background threads
                    # Use uploaded_by (resolved UserId) or raw_user_id for the compliance check
                    user_id_for_check = uploaded_by if uploaded_by else raw_user_id
                    for doc_id in all_created_document_ids:
                        doc_info = doc_compliance_map.get(doc_id, {'compliance_id': None, 'policy_id': None, 'subpolicy_id': None})
                        check_thread = threading.Thread(
                            target=trigger_compliance_check,
                            args=(doc_id, audit_id, user_id_for_check, doc_info),
                            daemon=True,
                            name=f"AutoComplianceCheck-{doc_id}"
                        )
                        check_thread.start()
                        debug_print(f"      🚀 Started compliance check thread for document_id={doc_id} (compliance_id={doc_info.get('compliance_id')})")
                
                debug_print(f"{'='*60}")
                debug_print(f"✅ AUTO-PROCESSING COMPLETED")
                debug_print(f"   Processed: {len(all_relevant_documents_to_process)} document(s) from JSON")
                debug_print(f"   Created: {len(all_created_document_ids)} ai_audit_data record(s)")
                debug_print(f"   Checked: {len(all_created_document_ids)} document(s)")
                debug_print(f"{'='*60}\n")
                
                # Create notification for audit completion
                # Wait a bit for compliance checks to complete, then send notification
                def send_audit_completion_notification(audit_id_val, doc_count, user_id_val):
                    """Send notification after auto-processing completes"""
                    try:
                        import time
                        import os
                        import sys
                        import django
                        
                        # Setup Django environment for background thread
                        if not django.apps.apps.ready:
                            django_project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                            if django_project_path not in sys.path:
                                sys.path.insert(0, django_project_path)
                            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grc.settings')
                            django.setup()
                        
                        # Wait 5 seconds to allow compliance checks to start
                        time.sleep(5)
                        
                        # Get audit name for notification
                        conn_notif = self._get_db_connection()
                        if conn_notif:
                            cursor_notif = conn_notif.cursor(dictionary=True)
                            try:
                                cursor_notif.execute("""
                                    SELECT Title, FrameworkId 
                                    FROM audit 
                                    WHERE AuditId = %s
                                """, (audit_id_val,))
                                audit_info = cursor_notif.fetchone()
                                audit_name = audit_info.get('Title', f'Audit {audit_id_val}') if audit_info else f'Audit {audit_id_val}'
                                
                                # Import notification helper using proper import (not dynamic file loading)
                                # This ensures we use the same notifications_storage instance
                                try:
                                    from grc.routes.Global.notifications import create_audit_completion_notification
                                    
                                    # Create notification using helper function
                                    debug_print(f"      🔔 Calling create_audit_completion_notification: audit_id={audit_id_val}, user_id={user_id_val}, doc_count={doc_count}")
                                    notification = create_audit_completion_notification(
                                        audit_id=audit_id_val,
                                        audit_name=audit_name,
                                        document_count=len(all_created_document_ids) if 'all_created_document_ids' in locals() else doc_count,
                                        user_id=user_id_val
                                    )
                                    
                                    if notification:
                                        debug_print(f"      📬 Notification created successfully for audit {audit_id_val}: {audit_name}")
                                        debug_print(f"      📬 Notification details: user_id={notification.get('user_id')}, title={notification.get('title')}")
                                    else:
                                        debug_print(f"      ⚠️  Notification creation returned None for audit {audit_id_val}")
                                except ImportError as import_err:
                                    debug_print(f"      ⚠️  Could not import notifications module: {str(import_err)}")
                                    import traceback
                                    traceback.print_exc()
                                except Exception as notif_create_err:
                                    debug_print(f"      ⚠️  Error creating notification: {str(notif_create_err)}")
                                    import traceback
                                    traceback.print_exc()
                            finally:
                                cursor_notif.close()
                                conn_notif.close()
                    except Exception as notif_err:
                        debug_print(f"      ⚠️ Error creating notification: {str(notif_err)}")
                        import traceback
                        traceback.print_exc()
                        # Don't fail auto-processing if notification fails
                
                # Start notification thread (non-blocking)
                # Use uploaded_by (numeric UserId) for notifications, not username string
                notification_user_id = uploaded_by if uploaded_by else None
                if all_created_document_ids:
                    if notification_user_id:
                        debug_print(f"      📬 Will create notification for user_id={notification_user_id} (numeric UserId)")
                        notif_thread = threading.Thread(
                            target=send_audit_completion_notification,
                            args=(audit_id, len(all_created_document_ids), notification_user_id),
                            daemon=True,
                            name=f"Notification-{audit_id}"
                        )
                        notif_thread.start()
                    else:
                        debug_print(f"      ⚠️  Skipping notification: Could not resolve user_id (raw_user_id={raw_user_id}, uploaded_by={uploaded_by})")
                
            except Exception as e:
                debug_print(f"      ❌ Error in auto-processing: {str(e)}")
                import traceback
                traceback.print_exc()
            finally:
                cursor.close()
                conn.close()
                
        except Exception as e:
            debug_print(f"      ❌ Fatal error in auto-processing: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def get_pdf_processing_status(self, operation_id: int) -> Dict:
        """Check if PDF processing is complete and get metadata/summary"""
        if not self.db_pool:
            return {'status': 'error', 'message': 'Database not available'}
        
        conn = self._get_db_connection()
        if not conn:
            return {'status': 'error', 'message': 'Database connection failed'}
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            query = """
            SELECT metadata, summary, status, file_name, updated_at 
            FROM file_operations 
            WHERE id = %s
            """
            cursor.execute(query, (operation_id,))
            result = cursor.fetchone()
            
            if not result:
                return {'status': 'error', 'message': 'Operation not found'}
            
            # Check if metadata and summary are populated
            has_metadata = result['metadata'] is not None and result['metadata'] != '{}'
            has_summary = result['summary'] is not None and result['summary'] != ''
            
            if has_metadata and has_summary:
                return {
                    'status': 'completed',
                    'file_name': result['file_name'],
                    'metadata': json.loads(result['metadata']) if isinstance(result['metadata'], str) else result['metadata'],
                    'summary': result['summary'],
                    'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
                }
            else:
                return {
                    'status': 'processing',
                    'file_name': result['file_name'],
                    'message': 'PDF processing in progress...'
                }
            
        except Exception as e:
            debug_print(f"ERROR Failed to check processing status: {str(e)}")
            return {'status': 'error', 'message': str(e)}
        finally:
            cursor.close()
            conn.close()
    
    def get_operation_history(self, user_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get recent operation history from MySQL"""
        if not self.db_pool:
            return []
        
        conn = self._get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            if user_id:
                query = """
                SELECT * FROM file_operations 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
                """
                cursor.execute(query, (user_id, limit))
            else:
                query = """
                SELECT * FROM file_operations 
                ORDER BY created_at DESC 
                LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            results = cursor.fetchall()
            
            # Convert datetime objects to strings for JSON serialization
            for result in results:
                for key, value in result.items():
                    if isinstance(value, datetime.datetime):
                        result[key] = value.isoformat()
            
            return results
            
        except mysql.connector.Error as e:
            debug_print(f"ERROR MySQL query error: {str(e)}")
            return []
        except Exception as e:
            debug_print(f"ERROR Database query error: {str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def get_operation_stats(self) -> Dict:
        """Get operation statistics from MySQL"""
        if not self.db_pool:
            return {}
        
        conn = self._get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get overall stats
            cursor.execute("""
                SELECT 
                    operation_type,
                    COUNT(*) as total_count,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                    AVG(file_size) as avg_file_size,
                    SUM(file_size) as total_file_size
                FROM file_operations 
                GROUP BY operation_type
            """)
            
            stats = {
                'operations_by_type': cursor.fetchall(),
                'total_operations': 0,
                'total_completed': 0,
                'total_failed': 0
            }
            
            # Calculate totals
            for op_stat in stats['operations_by_type']:
                stats['total_operations'] += op_stat['total_count']
                stats['total_completed'] += op_stat['completed_count']
                stats['total_failed'] += op_stat['failed_count']
            
            # Get recent activity
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as operations
                FROM file_operations 
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            stats['recent_activity'] = cursor.fetchall()
            
            return stats
            
        except mysql.connector.Error as e:
            debug_print(f"ERROR MySQL stats query error: {str(e)}")
            return {}
        except Exception as e:
            debug_print(f"ERROR Database stats error: {str(e)}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def test_connection(self) -> Dict:
        """Test connection to Render microservice and MySQL database"""
        result = {
            'render_status': 'unknown',
            'mysql_status': 'unknown',
            'overall_success': False
        }
        
        # Test Direct microservice
        try:
            debug_print("🧪 Testing Direct microservice connection...")
            response = requests.get(f"{self.api_base_url}/health", timeout=30)
            response.raise_for_status()
            
            health_info = response.json()
            result['direct_status'] = 'connected'
            result['direct_info'] = health_info
            debug_print("SUCCESS Direct microservice: Connected")
            
        except requests.exceptions.Timeout:
            result['direct_status'] = 'timeout'
            result['direct_error'] = 'Connection timed out (Direct service may be unavailable)'
            debug_print("PENDING Direct microservice: Timeout (may be unavailable)")
        except Exception as e:
            result['direct_status'] = 'failed'
            result['direct_error'] = str(e)
            debug_print(f"ERROR Direct microservice: Failed - {str(e)}")
        
        # Test MySQL database
        try:
            debug_print("🧪 Testing MySQL database connection...")
            if self.db_pool:
                conn = self._get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    result['mysql_status'] = 'connected'
                    debug_print("SUCCESS MySQL database: Connected")
                else:
                    result['mysql_status'] = 'failed'
                    result['mysql_error'] = 'Failed to get connection from pool'
                    debug_print("ERROR MySQL database: Connection pool failed")
            else:
                result['mysql_status'] = 'not_configured'
                result['mysql_error'] = 'Database pool not initialized'
                debug_print("⚠️  MySQL database: Not configured")
                
        except mysql.connector.Error as e:
            result['mysql_status'] = 'failed'
            result['mysql_error'] = str(e)
            debug_print(f"ERROR MySQL database: Failed - {str(e)}")
        except Exception as e:
            result['mysql_status'] = 'failed'
            result['mysql_error'] = str(e)
            debug_print(f"ERROR MySQL database: Error - {str(e)}")
        
        # Overall success
        result['overall_success'] = (
            result['direct_status'] == 'connected' and 
            result['mysql_status'] in ['connected', 'not_configured']
        )
        
        return result
    
    def upload(self, file_path: str, user_id: str = "default-user", 
               custom_file_name: Optional[str] = None, module: str = None, 
               framework_id: Optional[int] = None) -> Dict:
        """Upload a file to S3 via Render microservice with MySQL tracking
        
        Args:
            file_path: Path to the file to upload
            user_id: User ID performing the upload
            custom_file_name: Custom name for the file (optional)
            module: Module name (policy, audit, incident, risk, framework, event)
        """
        operation_id = None
        
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Get original file name and extension
            original_file_name = os.path.basename(file_path)
            debug_print(f"Original file name: {original_file_name}---------------------------------------")
            file_name = custom_file_name or original_file_name
            file_size = os.path.getsize(file_path)
            
            # Create timestamp for naming
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create the new naming convention: original_filename_username_module_timestamp
            file_name_without_ext = os.path.splitext(original_file_name)[0]
            debug_print(f"File name without extension: {file_name_without_ext}---------------------------------------")
            file_extension = os.path.splitext(original_file_name)[1]
            new_original_name = f"{file_name_without_ext}_{user_id}_{module or 'general'}_{timestamp}{file_extension}"
            
            debug_print(f"📤 Uploading {file_name} ({file_size} bytes) via Direct...")
            debug_print(f"📂 Module: {module or 'general'}")
            debug_print(f"📄 Original name: {original_file_name}")
            debug_print(f"📄 New original name: {new_original_name}")
            
            # Save initial operation record with module
            operation_data = {
                'user_id': user_id,
                'file_name': original_file_name,  # Keep original filename for S3 upload
                'original_name': original_file_name,  # Store actual original filename
                'module': module or 'general',  # Store module name
                'framework_id': framework_id,  # Store framework ID
                'file_type': os.path.splitext(file_name)[1][1:].lower() if '.' in file_name else '',
                'file_size': file_size,
                'content_type': mimetypes.guess_type(file_path)[0],
                'status': 'pending',
                'metadata': {
                    'original_path': file_path,
                    'custom_file_name': custom_file_name,
                    'platform': 'Direct',
                    'direct_url': self.api_base_url,
                    'module': module or 'general',
                    'framework_id': framework_id,
                    'naming_convention': 'original_filename_username_module_timestamp',
                    'modified_name': new_original_name  # Store the modified name for reference
                }
            }
            operation_id = self._save_operation_record('upload', operation_data)
            
            # Upload to Direct service
            url = f"{self.api_base_url}/api/upload/{user_id}/{file_name}"
            
            debug_print(f"📍 Upload URL: {url}")
            
            with open(file_path, 'rb') as file:
                files = {'file': (file_name, file, mimetypes.guess_type(file_path)[0])}
                
                debug_print(f"📁 File details: name={file_name}, size={file_size}, type={mimetypes.guess_type(file_path)[0]}")
                
                try:
                    upload_start_time = datetime.datetime.now()
                    debug_print(f"⏱️  [UPLOAD] Starting upload at {upload_start_time.strftime('%H:%M:%S')}")
                    debug_print(f"⏱️  [UPLOAD] Timeout set to: 600 seconds (10 minutes)")
                    debug_print(f"⏱️  [UPLOAD] File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
                    
                    # Increased timeout for large files (10 minutes)
                    response = requests.post(url, files=files, timeout=600)
                    
                    upload_elapsed = (datetime.datetime.now() - upload_start_time).total_seconds()
                    debug_print(f"⏱️  [UPLOAD] Upload completed in {upload_elapsed:.2f} seconds")
                    debug_print(f"📊 [UPLOAD] Response status: {response.status_code}")
                    debug_print(f"📝 [UPLOAD] Response headers: {dict(response.headers)}")
                    
                    if response.status_code != 200:
                        debug_print(f"❌ [UPLOAD] ERROR Response content: {response.text}")
                        
                    response.raise_for_status()
                    result = response.json()
                    debug_print(f"✅ [UPLOAD] SUCCESS Upload response: {result}")
                    
                except requests.exceptions.Timeout as timeout_error:
                    upload_elapsed = (datetime.datetime.now() - upload_start_time).total_seconds()
                    debug_print(f"❌ [UPLOAD] TIMEOUT after {upload_elapsed:.2f} seconds")
                    debug_print(f"❌ [UPLOAD] Microservice at {url} did not respond within 600 seconds")
                    raise Exception(f"Upload timeout: Microservice did not respond within 10 minutes. File size: {file_size / (1024*1024):.2f} MB")
                    
                except requests.exceptions.RequestException as e:
                    upload_elapsed = (datetime.datetime.now() - upload_start_time).total_seconds() if 'upload_start_time' in locals() else 0
                    debug_print(f"❌ [UPLOAD] Request failed after {upload_elapsed:.2f} seconds: {str(e)}")
                    debug_print(f"❌ [UPLOAD] Error type: {type(e).__name__}")
                    if hasattr(e, 'response') and e.response is not None:
                        debug_print(f"❌ [UPLOAD] Error response status: {e.response.status_code}")
                        debug_print(f"❌ [UPLOAD] Error response content: {e.response.text}")
                    import traceback
                    traceback.print_exc()
                    raise
            
            if result.get('success'):
                file_info = result['file']
                
                # Update MySQL with success
                if operation_id:
                    update_data = {
                        'stored_name': file_info['storedName'],
                        's3_url': file_info['url'],
                        's3_key': file_info['s3Key'],
                        's3_bucket': file_info.get('bucket', ''),
                        'status': 'completed',
                        'metadata': {
                            'original_path': file_path,
                            'platform': 'Direct',
                            'direct_url': self.api_base_url,
                            'upload_response': file_info,
                            'modified_name': new_original_name  # Include modified name for reference
                        }
                    }
                    self._update_operation_record(operation_id, update_data)
                
                debug_print(f"SUCCESS Upload successful! File: {file_info['storedName']}")
                
                # Check if file is PDF or Excel and trigger background processing
                file_extension = os.path.splitext(file_name)[1].lower()
                if file_extension == '.pdf' and operation_id:
                    debug_print(f"📄 PDF detected, starting background processing...")
                    # Start PDF processing in a background thread (non-blocking)
                    processing_thread = threading.Thread(
                        target=self._process_pdf_after_upload,
                        args=(operation_id, file_info['url'], file_name),
                        daemon=True
                    )
                    processing_thread.start()
                    debug_print(f"✅ PDF processing thread started for operation {operation_id}")
                elif file_extension in ['.xlsx', '.xls'] and operation_id:
                    debug_print(f"📊 Excel file detected, starting background processing...")
                    # Start Excel processing in a background thread (non-blocking)
                    processing_thread = threading.Thread(
                        target=self._process_excel_after_upload,
                        args=(operation_id, file_info['url'], file_name),
                        daemon=True
                    )
                    processing_thread.start()
                    debug_print(f"✅ Excel processing thread started for operation {operation_id}")
                
                return {
                    'success': True,
                    'operation_id': operation_id,
                    'file_info': file_info,
                    'platform': 'Direct',
                    'database': 'MySQL',
                    'message': 'File uploaded successfully to Direct/S3',
                    'pdf_processing': 'started' if file_extension == '.pdf' else ('started' if file_extension in ['.xlsx', '.xls'] else 'not_applicable')
                }
            else:
                # Update MySQL with failure
                if operation_id:
                    self._update_operation_record(operation_id, {
                        'status': 'failed', 
                        'error': result.get('error')
                    })
                
                return result
                
        except Exception as e:
            error_msg = str(e)
            debug_print(f"ERROR Upload failed: {error_msg}")
            
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'failed',
                    'error': error_msg
                })
            
            return {
                'success': False,
                'operation_id': operation_id,
                'error': error_msg
            }

    def get_presigned_download_url(self, s3_key: str, file_name: str) -> str:
        """Get a short-lived presigned URL for viewing/downloading a file. Returns the URL or raises."""
        from urllib.parse import quote
        encoded_s3_key = quote(s3_key, safe='')
        encoded_file_name = quote(file_name, safe='')
        url = f"{self.api_base_url}/api/download/{encoded_s3_key}/{encoded_file_name}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        download_info = response.json()
        if not download_info.get('success'):
            raise Exception(download_info.get('error', 'Failed to get download URL'))
        return download_info.get('downloadUrl') or ''

    def presign_get(self, bucket: str = '', key: str = '', file_name: str = '', expires_in: int = 900, disposition: str = 'inline') -> str:
        """Return a presigned URL for inline viewing or download. Uses microservice /api/download."""
        s3_key = (key or '').strip()
        name = (file_name or 'document').strip() or 'document'
        if not s3_key:
            raise ValueError('s3_key is required')
        return self.get_presigned_download_url(s3_key, name)
    
    def download(self, s3_key: str, file_name: str, 
                 destination_path: str = "./downloads", 
                 user_id: str = "default-user") -> Dict:
        """Download a file from S3 via Direct with MySQL tracking"""
        operation_id = None
        
        try:
            debug_print(f"⬇️  Downloading {file_name} via Direct...")
            
            # Save initial operation record
            operation_data = {
                'user_id': user_id,
                'file_name': file_name,
                'original_name': file_name,
                's3_key': s3_key,
                'status': 'pending',
                'metadata': {
                    'destination_path': destination_path,
                    'platform': 'Direct',
                    'direct_url': self.api_base_url
                }
            }
            operation_id = self._save_operation_record('download', operation_data)
            
            # Get download URL from Direct service
            # URL encode the s3_key and file_name to handle special characters
            from urllib.parse import quote
            encoded_s3_key = quote(s3_key, safe='')
            encoded_file_name = quote(file_name, safe='')
            url = f"{self.api_base_url}/api/download/{encoded_s3_key}/{encoded_file_name}"
            
            debug_print(f"DEBUG: Download URL: {url}")
            debug_print(f"DEBUG: Original s3_key: {s3_key}, encoded: {encoded_s3_key}")
            debug_print(f"DEBUG: Original file_name: {file_name}, encoded: {encoded_file_name}")
            
            response = requests.get(url, timeout=60)
            # Fallback: if 404 and file_name differs from s3_key basename (e.g. document_3034.pdf vs parent.docx),
            # try downloading the main S3 object using its actual filename
            if response.status_code == 404:
                s3_basename = s3_key.split('/')[-1] if '/' in s3_key else s3_key
                if s3_basename and s3_basename != file_name and '.' in s3_basename:
                    debug_print(f"DEBUG: 404 on first attempt - retrying with s3_key basename: {s3_basename}")
                    encoded_file_name = quote(s3_basename, safe='')
                    url = f"{self.api_base_url}/api/download/{encoded_s3_key}/{encoded_file_name}"
                    response = requests.get(url, timeout=60)
                    if response.status_code == 200:
                        file_name = s3_basename  # use for local save
            response.raise_for_status()
            
            download_info = response.json()
            
            if not download_info.get('success'):
                raise Exception(f"Failed to get download URL: {download_info.get('error')}")
            
            # Download file
            download_url = download_info['downloadUrl']
            file_response = requests.get(download_url, timeout=300)
            file_response.raise_for_status()
            
            # Save locally
            os.makedirs(destination_path, exist_ok=True)
            local_file_path = os.path.join(destination_path, file_name) if os.path.isdir(destination_path) else destination_path
            
            with open(local_file_path, 'wb') as f:
                f.write(file_response.content)
            
            # Update MySQL with success
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'completed',
                    'file_size': len(file_response.content),
                                            'metadata': {
                            'destination_path': destination_path,
                            'local_file_path': local_file_path,
                            'platform': 'Direct',
                            'direct_url': self.api_base_url,
                            'download_info': download_info
                        }
                })
            
            debug_print(f"SUCCESS Download successful! Saved to: {local_file_path}")
            
            return {
                'success': True,
                'operation_id': operation_id,
                'file_path': local_file_path,
                'file_size': len(file_response.content),
                'platform': 'Direct',
                'database': 'MySQL',
                'message': 'File downloaded successfully from Direct/S3'
            }
            
        except Exception as e:
            error_msg = str(e)
            debug_print(f"ERROR Download failed: {error_msg}")
            
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'failed',
                    'error': error_msg
                })
            
            return {
                'success': False,
                'operation_id': operation_id,
                'error': error_msg
            }
    
    def export(self, data: Union[List[Dict], Dict], export_format: str, 
               file_name: str, user_id: str = "default-user") -> Dict:
        """Export data via Direct microservice with MySQL tracking"""
        operation_id = None
        
        try:
            # Validate format - all formats supported by the microservice
            microservice_supported_formats = ['json', 'csv', 'xml', 'txt', 'pdf']
            all_supported_formats = ['json', 'csv', 'xml', 'txt', 'pdf', 'xlsx']
            
            if export_format.lower() not in all_supported_formats:
                raise ValueError(f"Unsupported format: {export_format}. Supported: {all_supported_formats}")
            
            # Check if format is supported by microservice
            if export_format.lower() not in microservice_supported_formats:
                raise ValueError(f"Format {export_format} is not supported by the S3 microservice. Use local export instead.")
            # SSRF mitigation: force PDF rendering to local reportlab path.
            if export_format.lower() == 'pdf':
                raise ValueError("PDF export via S3 microservice is disabled for SSRF mitigation. Use local export.")
            
            record_count = len(data) if isinstance(data, list) else 1
            debug_print(f"📊 Exporting {record_count} records as {export_format.upper()} via Direct...")
            
            # Save initial operation record
            operation_data = {
                'user_id': user_id,
                'file_name': file_name,
                'original_name': file_name,
                'export_format': export_format,
                'record_count': record_count,
                'status': 'pending',
                'metadata': {
                    'export_format': export_format,
                    'data_size': len(str(data)),
                    'platform': 'Direct',
                    'direct_url': self.api_base_url
                }
            }
            operation_id = self._save_operation_record('export', operation_data)
            
            # Export via Direct
            url = f"{self.api_base_url}/api/export/{export_format}/{user_id}/{file_name}"
            
            # Format data based on export type (similar to test file)
            if export_format.lower() in ['csv', 'xlsx']:
                # For CSV/XLSX exports, send just the records array
                payload = {'data': data if isinstance(data, list) else [data]}
            else:
                # For other formats, send the full data structure
                payload = {'data': data}
            
            from .microservice_aws_payload import aws_credentials_for_microservice_export

            aws_credentials = aws_credentials_for_microservice_export()
            payload.update(aws_credentials)

            debug_print(f"🔗 Export URL: {url}")
            debug_print(f"📦 Payload size: {len(str(payload))} characters")
            debug_print("🔑 Using AWS credentials from environment for microservice export")
            
            # Increased timeout for large exports (10 minutes)
            # Note: For very large datasets (>1000 records), use local export instead
            response = requests.post(url, json=payload, timeout=600)
            debug_print(f"📊 Response status: {response.status_code}")
            
            if response.status_code != 200:
                debug_print(f"ERROR Response content: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                export_info = result.get('export') or result.get('file') or result
                
                # Update MySQL with success
                if operation_id:
                    update_data = {
                        'stored_name': export_info.get('storedName') or export_info.get('fileName') or file_name,
                        's3_url': export_info.get('url') or export_info.get('fileUrl') or export_info.get('downloadUrl'),
                        's3_key': export_info.get('s3Key') or export_info.get('key') or export_info.get('fileKey'),
                        's3_bucket': export_info.get('bucket') or export_info.get('bucketName'),
                        'file_size': export_info.get('size') or export_info.get('fileSize'),
                        'content_type': export_info.get('contentType') or export_info.get('mimeType'),
                        'status': 'completed',
                        'metadata': {
                            'export_format': export_format,
                            'data_size': len(str(data)),
                            'platform': 'Direct',
                            'direct_url': self.api_base_url,
                            'export_response': export_info
                        }
                    }
                    self._update_operation_record(operation_id, update_data)
                
                debug_print(f"SUCCESS Export successful! File: {export_info['storedName']}")
                
                return {
                    'success': True,
                    'operation_id': operation_id,
                    'export_info': export_info,
                    'platform': 'Direct',
                    'database': 'MySQL',
                    'message': f'Data exported successfully as {export_format.upper()} via Direct'
                }
            else:
                # Update MySQL with failure
                error_msg = result.get('error') or result.get('message') or 'Unknown error'
                if operation_id:
                    self._update_operation_record(operation_id, {
                        'status': 'failed',
                        'error': error_msg
                    })
                
                return {
                    'success': False,
                    'operation_id': operation_id,
                    'error': error_msg,
                    'response': result
                }
                
        except Exception as e:
            error_msg = str(e)
            debug_print(f"ERROR Export failed: {error_msg}")
            debug_print(f"📝 Full error details: {type(e).__name__}: {error_msg}")
            
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'failed',
                    'error': error_msg
                })
            
            return {
                'success': False,
                'operation_id': operation_id,
                'error': error_msg,
                'error_type': type(e).__name__
            }

# ============================================================================
# EXPORT FUNCTIONS - All export formats handled here
# ============================================================================

def export_to_excel(data):
    """Export data to Excel format with enhanced formatting"""
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for Excel export. Install with: pip install pandas")
    
    try:
        debug_print(f"📝 [EXCEL EXPORT] Processing data...")
        debug_print(f"   ├─ Data type: {type(data)}")
        debug_print(f"   ├─ Is list: {isinstance(data, list)}")
        debug_print(f"   ├─ Is dict: {isinstance(data, dict)}")

        # Formula-injection hardening for spreadsheet exports (Excel also evaluates formulas).
        data = sanitize_csv_dataset(data)
        
        # Convert data to DataFrame
        if isinstance(data, list):
            if len(data) == 0:
                debug_print(f"   ⚠️  Empty list provided, creating empty DataFrame")
                df = pd.DataFrame()
            else:
                debug_print(f"   ├─ List length: {len(data)}")
                debug_print(f"   ├─ First item type: {type(data[0])}")
                if isinstance(data[0], dict):
                    debug_print(f"   ├─ First item keys: {list(data[0].keys())[:5]}...")  # Show first 5 keys
                df = pd.DataFrame(data)
        elif isinstance(data, dict):
            debug_print(f"   ├─ Dict keys: {list(data.keys())[:5]}...")
            df = pd.DataFrame([data])
        else:
            debug_print(f"   ├─ Converting to DataFrame from: {type(data)}")
            df = pd.DataFrame(data)
        
        debug_print(f"   ├─ DataFrame shape: {df.shape}")
        if len(df.columns) > 0:
            debug_print(f"   ├─ DataFrame columns: {list(df.columns)[:10]}...")  # Show first 10 columns
        
        # Clean the data: Replace NaN, None, and INF values with empty string
        df = df.replace([np.nan, np.inf, -np.inf, None], '')
        
        # Convert all data to string to avoid type issues, then back to appropriate types
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col])
            except:
                pass
        
        output = BytesIO()
        
        # Try to use xlsxwriter engine first (preferred for formatting)
        try:
            debug_print("Attempting Excel export with xlsxwriter...")
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                workbook = writer.book
                worksheet = workbook.add_worksheet('Export')
                
                # Format the header
                header_format = workbook.add_format({
                    'bold': True, 
                    'bg_color': '#4F6CFF',
                    'font_color': 'white',
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter'
                })
                
                # Add alternating row colors for better readability
                row_format_even = workbook.add_format({'bg_color': '#F8F9FA'})
                row_format_odd = workbook.add_format({'bg_color': '#FFFFFF'})
                
                # Write headers (only if DataFrame has columns)
                if len(df.columns) > 0:
                    for col_num, value in enumerate(df.columns.values):
                        worksheet.write(0, col_num, str(value), header_format)
                    
                    # Adjust column widths dynamically
                    for i, col in enumerate(df.columns):
                        try:
                            if len(df) > 0:
                                max_length = max(
                                    df[col].astype(str).map(len).max(),
                                    len(str(col))
                                )
                            else:
                                max_length = len(str(col))
                            worksheet.set_column(i, i, min(max_length + 3, 50))
                        except:
                            worksheet.set_column(i, i, 15)
                    
                    # Write data with safe handling
                    if len(df) > 0:
                        for row_num in range(len(df)):
                            row_format = (
                                row_format_even if (row_num + 1) % 2 == 0 else row_format_odd
                            )
                            for col_num in range(len(df.columns)):
                                cell_value = df.iloc[row_num, col_num]

                                # Normalize unsupported types before writing
                                if isinstance(cell_value, dict):
                                    # Prefer a stable string representation over raw dict
                                    cell_value = json.dumps(cell_value, ensure_ascii=False)
                                elif isinstance(cell_value, (list, tuple, set)):
                                    cell_value = ", ".join(
                                        [str(item) for item in cell_value]
                                    )

                                if cell_value is None or cell_value == '':
                                    cell_value = ''
                                elif pd.isna(cell_value):
                                    cell_value = ''
                                elif isinstance(cell_value, (float, np.floating)):
                                    if np.isnan(cell_value) or np.isinf(cell_value):
                                        cell_value = ''

                                worksheet.write(row_num + 1, col_num, cell_value, row_format)
                    else:
                        # Empty DataFrame - just write headers
                        debug_print(f"   ⚠️  Empty DataFrame - only headers will be written")
                else:
                    # No columns - write a message
                    worksheet.write(0, 0, "No data available for export.", header_format)
                        
            debug_print(f"✅ Excel export successful with xlsxwriter. File size: {len(output.getvalue())} bytes")
            
        except ImportError:
            # Fall back to openpyxl if xlsxwriter is not available
            debug_print("xlsxwriter not found, trying openpyxl instead...")
            try:
                from openpyxl import Workbook
                from openpyxl.styles import Font, PatternFill, Alignment
                
                output = BytesIO()
                df_clean = df.replace([np.nan, np.inf, -np.inf, None], '')
                
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_clean.to_excel(writer, sheet_name='Export', index=False)
                    worksheet = writer.sheets['Export']
                    
                    # Style the header row
                    header_fill = PatternFill(start_color='4F6CFF', end_color='4F6CFF', fill_type='solid')
                    header_font = Font(bold=True, color='FFFFFF')
                    header_alignment = Alignment(horizontal='center', vertical='center')
                    
                    for cell in worksheet[1]:
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = header_alignment
                    
                    # Adjust column widths
                    for i, col in enumerate(df.columns):
                        try:
                            max_length = max(
                                df_clean[col].astype(str).map(len).max(),
                                len(str(col))
                            )
                            worksheet.column_dimensions[chr(65 + i)].width = min(max_length + 3, 50)
                        except:
                            worksheet.column_dimensions[chr(65 + i)].width = 15
                
                debug_print(f"✅ Excel export successful with openpyxl. File size: {len(output.getvalue())} bytes")
                
            except ImportError as openpyxl_error:
                raise ImportError("Excel export requires either xlsxwriter or openpyxl. Install: pip install xlsxwriter or pip install openpyxl")
    
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        debug_print(f"❌ Excel export error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Excel export failed: {str(e)}")

def export_to_csv(data):
    """Export data to CSV format"""
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for CSV export. Install with: pip install pandas")
    
    try:
        debug_print(f"📝 [CSV EXPORT] Processing data...")
        debug_print(f"   ├─ Data type: {type(data)}")
        debug_print(f"   ├─ Is list: {isinstance(data, list)}")
        debug_print(f"   ├─ Is dict: {isinstance(data, dict)}")
        
        # Handle empty data
        if not data:
            debug_print(f"   ⚠️  Empty data provided, creating empty CSV with headers")
            # Create empty DataFrame with default columns if needed
            df = pd.DataFrame()
        elif isinstance(data, list):
            if len(data) == 0:
                debug_print(f"   ⚠️  Empty list provided")
                df = pd.DataFrame()
            else:
                debug_print(f"   ├─ List length: {len(data)}")
                debug_print(f"   ├─ First item type: {type(data[0])}")
                if isinstance(data[0], dict):
                    debug_print(f"   ├─ First item keys: {list(data[0].keys())[:5]}...")  # Show first 5 keys
                df = pd.DataFrame(data)
        elif isinstance(data, dict):
            debug_print(f"   ├─ Dict keys: {list(data.keys())[:5]}...")
            df = pd.DataFrame([data])
        else:
            debug_print(f"   ├─ Converting to DataFrame from: {type(data)}")
            df = pd.DataFrame(data)
        
        debug_print(f"   ├─ DataFrame shape: {df.shape}")
        debug_print(f"   ├─ DataFrame columns: {list(df.columns)[:10]}...")  # Show first 10 columns
        
        # Clean the data: Replace NaN, None, and INF values with empty string
        df = df.replace([np.nan, np.inf, -np.inf, None], '')
        
        sanitized_data = sanitize_csv_dataset(data)
        df = pd.DataFrame(sanitized_data)

        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        result = output.getvalue()
        debug_print(f"   └─ ✅ CSV export successful. File size: {len(result)} bytes")
        return result
        
    except Exception as e:
        debug_print(f"   └─ ❌ CSV export error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"CSV export failed: {str(e)}")

def export_to_json(data):
    """Export data to JSON format"""
    return json.dumps(data, indent=2).encode('utf-8')

def export_to_xml(data):
    """Export data to XML format"""
    if not XMLTODICT_AVAILABLE:
        raise ImportError("xmltodict is required for XML export. Install with: pip install xmltodict")
    
    root_name = 'export'
    if isinstance(data, list):
        xml_data = {root_name: {'item': data}}
    else:
        xml_data = {root_name: data}
    
    xml_string = xmltodict.unparse(xml_data, pretty=True)
    return xml_string.encode('utf-8')

def export_to_pdf(data):
    """Export data to PDF format"""
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")
    
    try:
        debug_print(f"📝 [PDF EXPORT] Processing data...")
        debug_print(f"   ├─ Data type: {type(data)}")
        debug_print(f"   ├─ Is list: {isinstance(data, list)}")
        debug_print(f"   ├─ Is dict: {isinstance(data, dict)}")
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(width/2 - 50, height - 50, "Export Report")
        
        # Add data
        c.setFont("Helvetica", 12)
        y_position = height - 100
        
        # Handle empty data
        if not data:
            c.drawString(50, y_position, "No data available for export.")
            y_position -= 20
        elif isinstance(data, list):
            if len(data) == 0:
                c.drawString(50, y_position, "No data available for export.")
                y_position -= 20
            else:
                debug_print(f"   ├─ List length: {len(data)}")
                for i, item in enumerate(data):
                    if not isinstance(item, dict):
                        # Convert non-dict items to string representation
                        c.drawString(50, y_position, f"Item {i+1}: {str(item)}")
                        y_position -= 20
                    else:
                        c.drawString(50, y_position, f"Item {i+1}:")
                        y_position -= 20
                        
                        for key, value in item.items():
                            # Handle None, NaN, and other non-string values
                            value_str = str(value) if value is not None else ''
                            if len(value_str) > 80:  # Truncate very long values
                                value_str = value_str[:77] + '...'
                            c.drawString(70, y_position, f"{key}: {value_str}")
                            y_position -= 20
                            
                            if y_position < 50:  # Add a new page if needed
                                c.showPage()
                                y_position = height - 50
        elif isinstance(data, dict):
            debug_print(f"   ├─ Dict keys: {list(data.keys())[:5]}...")
            for key, value in data.items():
                # Handle None, NaN, and other non-string values
                value_str = str(value) if value is not None else ''
                if len(value_str) > 80:  # Truncate very long values
                    value_str = value_str[:77] + '...'
                c.drawString(50, y_position, f"{key}: {value_str}")
                y_position -= 20
                
                if y_position < 50:  # Add a new page if needed
                    c.showPage()
                    y_position = height - 50
        else:
            # Handle other data types
            c.drawString(50, y_position, f"Data: {str(data)}")
            y_position -= 20
        
        c.save()
        buffer.seek(0)
        result = buffer.getvalue()
        debug_print(f"   └─ ✅ PDF export successful. File size: {len(result)} bytes")
        return result
        
    except Exception as e:
        debug_print(f"   └─ ❌ PDF export error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"PDF export failed: {str(e)}")

def export_to_txt(data):
    """Export data to Text format"""
    buffer = BytesIO()
    
    buffer.write(b"Export Report\n")
    buffer.write(b"=" * 50 + b"\n\n")
    buffer.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n".encode('utf-8'))
    
    def format_item(item, level=0):
        indent = "  " * level
        
        if isinstance(item, list):
            for i, element in enumerate(item):
                buffer.write(f"{indent}Item {i+1}:\n".encode('utf-8'))
                format_item(element, level + 1)
        elif isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, (dict, list)):
                    buffer.write(f"{indent}{key}:\n".encode('utf-8'))
                    format_item(value, level + 1)
                else:
                    buffer.write(f"{indent}{key}: {value}\n".encode('utf-8'))
        else:
            buffer.write(f"{indent}{item}\n".encode('utf-8'))
    
    format_item(data)
    
    buffer.write(b"\n" + b"=" * 50 + b"\n")
    buffer.write(b"End of Report")
    
    buffer.seek(0)
    return buffer.getvalue()

def get_content_type(file_type):
    """Get content type based on file extension"""
    content_types = {
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'csv': 'text/csv',
        'json': 'application/json',
        'xml': 'application/xml',
        'txt': 'text/plain'
    }
    
    return content_types.get(file_type, 'application/octet-stream')

def export_data(data=None, file_format='xlsx', user_id='user123', options=None, s3_client_instance=None):
    """
    COMPREHENSIVE EXPORT FUNCTION - All export formats handled here
    Uses local export for large datasets to avoid timeout
    
    Args:
        data: The data to export
        file_format: Format to export (xlsx, pdf, csv, json, xml, txt)
        user_id: ID of the user requesting the export
        options: Additional export options (file_name, etc.)
        s3_client_instance: RenderS3Client instance (optional, will create if not provided)
        
    Returns:
        Dictionary with export results
    """
    start_time_total = datetime.datetime.now()
    debug_print(f"\n{'='*80}")
    debug_print(f"🚀 [EXPORT] Starting export process at {start_time_total.strftime('%Y-%m-%d %H:%M:%S')}")
    debug_print(f"{'='*80}")
    
    if data is None:
        data = []
        debug_print(f"⚠️  [EXPORT] No data provided, using empty list")
        
    if options is None:
        options = {}
        debug_print(f"ℹ️  [EXPORT] No options provided, using defaults")
    else:
        debug_print(f"ℹ️  [EXPORT] Options received: {options}")

    # Centralized sanitization for every export caller (incident/compliance/risk/etc.).
    data = _sanitize_export_payload(data)
    if isinstance(data, list) and len(data) > EXPORT_MAX_RECORDS:
        raise ValueError(f"Export record count exceeds allowed maximum ({EXPORT_MAX_RECORDS})")
    options = _sanitize_export_payload(options)

    # Formula-injection hardening for any export that embeds user strings (CSV/Excel/JSON/XML/TXT).
    if str(file_format).lower() in ('csv', 'xlsx', 'json', 'xml', 'txt'):
        data = sanitize_csv_dataset(data)
    
    # Validate data size to prevent 413 errors
    data_size = len(str(data))
    max_size = EXPORT_MAX_DATA_BYTES  # 40MB limit
    record_count = len(data) if isinstance(data, list) else 1
    
    debug_print(f"\n📊 [EXPORT] Data validation:")
    debug_print(f"   ├─ Data size: {data_size:,} bytes ({data_size / (1024*1024):.2f} MB)")
    debug_print(f"   ├─ Record count: {record_count:,}")
    debug_print(f"   ├─ Format: {file_format}")
    debug_print(f"   └─ User ID: {user_id}")
    
    if data_size > max_size:
        error_msg = f'Data too large for export ({data_size} bytes). Maximum allowed: {max_size} bytes. Please reduce the data size or use pagination.'
        debug_print(f"❌ [EXPORT] {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }
    
    timestamp = datetime.datetime.now().timestamp()
    
    # Generate filename with proper extension
    debug_print(f"\n📝 [EXPORT] Generating filename...")
    if options.get('file_name'):
        base_name = options.get('file_name')
        if '.' in base_name:
            base_name = base_name.rsplit('.', 1)[0]
        base_name = sanitize_export_filename(base_name)
        file_name = f"{base_name}.{file_format}"
        debug_print(f"   └─ Using provided filename: {file_name}")
    else:
        file_name = f"export_{user_id}_{int(timestamp)}.{file_format}"
        debug_print(f"   └─ Generated filename: {file_name}")
    
    # Get or create S3 client instance
    debug_print(f"\n🔧 [EXPORT] Initializing S3 client...")
    if s3_client_instance is None:
        try:
            debug_print(f"   ├─ S3 client not provided, creating new instance...")
            from django.conf import settings
            db_config = settings.DATABASES['default']
            mysql_config = {
                'host': db_config['HOST'],
                'user': db_config['USER'],
                'password': db_config['PASSWORD'],
                'database': db_config['NAME'],
                'port': db_config.get('PORT', 3306)
            }
            debug_print(f"   ├─ MySQL config: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
            s3_client_instance = create_direct_mysql_client(mysql_config)
            debug_print(f"   └─ ✅ S3 client created successfully")
        except Exception as e:
            debug_print(f"   └─ ❌ Could not create S3 client: {str(e)}")
            import traceback
            traceback.print_exc()
            s3_client_instance = None
    else:
        debug_print(f"   └─ ✅ Using provided S3 client instance")
    
    try:
        # Check if S3 client is available
        debug_print(f"\n🔍 [EXPORT] Checking S3 client availability...")
        if not s3_client_instance:
            debug_print(f"   └─ ⚠️  S3 client not available, using local export only")
            return local_export_fallback(data, file_format, user_id, options)
        debug_print(f"   └─ ✅ S3 client available")
        
        # Validate format
        debug_print(f"\n✅ [EXPORT] Validating export format...")
        all_supported_formats = ['json', 'csv', 'xml', 'txt', 'pdf', 'xlsx']
        if file_format.lower() not in all_supported_formats:
            error_msg = f"Unsupported export format: {file_format}. Supported: {all_supported_formats}"
            debug_print(f"   └─ ❌ {error_msg}")
            raise ValueError(error_msg)
        debug_print(f"   └─ ✅ Format '{file_format}' is supported")
        
        # Check if dataset is too large for microservice
        # For large datasets (>1000 records or >1MB), use local export to avoid timeout
        # Also use local export for empty datasets (microservice can't handle empty data)
        debug_print(f"\n📏 [EXPORT] Analyzing dataset size...")
        data_size_mb = data_size / (1024 * 1024)
        microservice_supported = ['json', 'csv', 'xml', 'txt', 'pdf']
        format_supported_by_microservice = file_format.lower() in microservice_supported
        
        use_local_export = (
            file_format.lower() == 'pdf' or  # SSRF mitigation: avoid remote HTML/PDF rendering
            file_format.lower() == 'csv' or  # Force local sanitized CSV generation
            not format_supported_by_microservice or  # xlsx always local
            record_count > 1000 or  # More than 1000 records
            data_size_mb > 1.0 or  # More than 1MB of data
            record_count == 0  # Empty dataset - microservice can't handle this
        )
        
        debug_print(f"   ├─ Format supported by microservice: {format_supported_by_microservice}")
        debug_print(f"   ├─ Record count: {record_count:,}")
        debug_print(f"   ├─ Data size: {data_size_mb:.2f} MB")
        debug_print(f"   ├─ Threshold check: records > 1000? {record_count > 1000}, size > 1MB? {data_size_mb > 1.0}, records == 0? {record_count == 0}")
        debug_print(f"   └─ Use local export: {use_local_export}")
        
        if use_local_export:
            # Use local export for unsupported formats OR large datasets to avoid timeout
            # OR empty datasets (microservice can't handle empty data)
            debug_print(f"\n🏠 [EXPORT] Using LOCAL EXPORT strategy")
            if record_count == 0:
                debug_print(f"   └─ Reason: Empty dataset (0 records) - microservice cannot handle empty data")
            elif not format_supported_by_microservice:
                debug_print(f"   └─ Reason: Format '{file_format}' not supported by microservice")
            else:
                debug_print(f"   └─ Reason: Large dataset detected ({record_count:,} records, {data_size_mb:.2f}MB)")
            
            # Export to file locally
            debug_print(f"\n📄 [EXPORT] Step 1/3: Converting data to {file_format.upper()} format locally...")
            debug_print(f"   ├─ Filename: {file_name}")
            start_time = datetime.datetime.now()
            debug_print(f"   └─ Started at: {start_time.strftime('%H:%M:%S')}")
            
            export_functions = {
                'xlsx': export_to_excel,
                'pdf': export_to_pdf,
                'csv': export_to_csv,
                'json': export_to_json,
                'xml': export_to_xml,
                'txt': export_to_txt
            }
            
            try:
                export_func = export_functions[file_format.lower()]
                debug_print(f"   ├─ Calling export function: {export_func.__name__}")
                debug_print(f"   ├─ Data before export: type={type(data)}, is_list={isinstance(data, list)}, length={len(data) if isinstance(data, list) else 'N/A'}")
                if isinstance(data, list) and len(data) > 0:
                    debug_print(f"   ├─ First record type: {type(data[0])}")
                    if isinstance(data[0], dict):
                        debug_print(f"   ├─ First record keys: {list(data[0].keys())[:10]}")
                        debug_print(f"   ├─ First record sample: {str(data[0])[:200]}...")
                file_buffer = export_func(data)
                conversion_time = (datetime.datetime.now() - start_time).total_seconds()
                debug_print(f"   ├─ ✅ Conversion completed in {conversion_time:.2f} seconds")
                debug_print(f"   └─ File size: {len(file_buffer):,} bytes ({len(file_buffer) / (1024*1024):.2f} MB)")
            except Exception as conv_error:
                debug_print(f"   └─ ❌ Conversion failed: {str(conv_error)}")
                import traceback
                traceback.print_exc()
                raise
            
            # Upload to S3 using microservice
            debug_print(f"\n☁️  [EXPORT] Step 2/3: Uploading file to S3...")
            upload_start = datetime.datetime.now()
            debug_print(f"   └─ Started at: {upload_start.strftime('%H:%M:%S')}")
            
            try:
                content_type = get_content_type(file_format)
                debug_print(f"   ├─ Content type: {content_type}")
                
                # Convert file buffer to temporary file for upload
                file_extension = file_name.split('.')[-1] if '.' in file_name else 'bin'
                debug_print(f"   ├─ Creating temporary file with extension: .{file_extension}")
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                    temp_file.write(file_buffer)
                    temp_file_path = temp_file.name
                debug_print(f"   ├─ Temporary file created: {temp_file_path}")
                debug_print(f"   ├─ File size: {os.path.getsize(temp_file_path):,} bytes")
                
                # Check microservice health first
                debug_print(f"   ├─ Checking microservice health...")
                try:
                    health_url = f"{s3_client_instance.api_base_url}/health"
                    health_response = requests.get(health_url, timeout=10)
                    if health_response.status_code == 200:
                        debug_print(f"   ├─ ✅ Microservice is reachable")
                    else:
                        debug_print(f"   ├─ ⚠️  Microservice health check returned status {health_response.status_code}")
                except Exception as health_error:
                    debug_print(f"   ├─ ⚠️  Microservice health check failed: {str(health_error)}")
                    debug_print(f"   ├─ ⚠️  Will still attempt upload, but may timeout")
                
                # Upload using S3 microservice
                debug_print(f"   ├─ Calling S3 upload...")
                debug_print(f"   ├─ Temp file: {temp_file_path}")
                debug_print(f"   ├─ File size: {os.path.getsize(temp_file_path):,} bytes")
                debug_print(f"   ├─ User ID: {user_id}")
                debug_print(f"   └─ Custom filename: {file_name}")
                
                upload_call_start = datetime.datetime.now()
                try:
                    upload_result = s3_client_instance.upload(temp_file_path, user_id=user_id, custom_file_name=file_name)
                    upload_call_time = (datetime.datetime.now() - upload_call_start).total_seconds()
                    debug_print(f"   ├─ Upload call completed in {upload_call_time:.2f} seconds")
                except Exception as upload_ex:
                    upload_call_time = (datetime.datetime.now() - upload_call_start).total_seconds()
                    debug_print(f"   └─ ❌ Upload call failed after {upload_call_time:.2f} seconds: {str(upload_ex)}")
                    import traceback
                    traceback.print_exc()
                    raise
                
                # Clean up temporary file
                os.unlink(temp_file_path)
                debug_print(f"   ├─ Temporary file deleted")
                
                upload_time = (datetime.datetime.now() - upload_start).total_seconds()
                debug_print(f"   ├─ Upload completed in {upload_time:.2f} seconds")
                
                if upload_result['success']:
                    file_info = upload_result['file_info']
                    total_duration = (datetime.datetime.now() - start_time).total_seconds()
                    
                    debug_print(f"   └─ ✅ Upload successful!")
                    debug_print(f"\n📊 [EXPORT] Step 3/3: Finalizing...")
                    debug_print(f"   ├─ S3 URL: {file_info['url']}")
                    debug_print(f"   ├─ Stored name: {file_info.get('storedName', file_name)}")
                    debug_print(f"   ├─ Total time: {total_duration:.2f} seconds")
                    debug_print(f"   └─ ✅ Export completed successfully!")
                    
                    total_time = (datetime.datetime.now() - start_time_total).total_seconds()
                    debug_print(f"\n{'='*80}")
                    debug_print(f"✅ [EXPORT] SUCCESS - Total time: {total_time:.2f} seconds")
                    debug_print(f"{'='*80}\n")
                    
                    return {
                        'success': True,
                        'file_url': file_info['url'],
                        'file_name': file_info.get('storedName', file_name),
                        'metadata': {
                            'file_size': len(file_buffer),
                            'format': file_format,
                            'record_count': record_count,
                            'export_duration': total_duration,
                            'method': 'local_export_upload'
                        }
                    }
                else:
                    error_msg = f"Upload failed: {upload_result.get('error', 'Unknown error')}"
                    debug_print(f"   └─ ❌ {error_msg}")
                    raise Exception(error_msg)
                    
            except Exception as s3_error:
                upload_time = (datetime.datetime.now() - upload_start).total_seconds()
                debug_print(f"   └─ ❌ S3 upload failed after {upload_time:.2f} seconds: {str(s3_error)}")
                import traceback
                traceback.print_exc()
                debug_print(f"\n🔄 [EXPORT] Falling back to local export...")
                # Fallback to local save
                return local_export_fallback(data, file_format, user_id, options)
        
        else:
            # Use microservice directly for small supported formats
            debug_print(f"\n🌐 [EXPORT] Using MICROSERVICE DIRECT strategy")
            debug_print(f"   └─ Reason: Small dataset ({record_count:,} records, {data_size_mb:.2f}MB)")
            
            # Export using microservice
            debug_print(f"\n📡 [EXPORT] Calling S3 microservice...")
            start_time = datetime.datetime.now()
            debug_print(f"   ├─ Started at: {start_time.strftime('%H:%M:%S')}")
            debug_print(f"   ├─ Format: {file_format}")
            debug_print(f"   ├─ Filename: {file_name}")
            debug_print(f"   └─ User ID: {user_id}")
            
            try:
                export_result = s3_client_instance.export(data, file_format, file_name, user_id)
                duration = (datetime.datetime.now() - start_time).total_seconds()
                
                debug_print(f"   ├─ Microservice call completed in {duration:.2f} seconds")
                
                if export_result['success']:
                    export_info = export_result['export_info']
                    debug_print(f"   └─ ✅ Export successful!")
                    debug_print(f"\n📊 [EXPORT] Finalizing...")
                    debug_print(f"   ├─ S3 URL: {export_info['url']}")
                    debug_print(f"   ├─ File size: {export_info.get('size', 0):,} bytes")
                    debug_print(f"   └─ ✅ Export completed successfully!")
                    
                    total_time = (datetime.datetime.now() - start_time_total).total_seconds()
                    debug_print(f"\n{'='*80}")
                    debug_print(f"✅ [EXPORT] SUCCESS - Total time: {total_time:.2f} seconds")
                    debug_print(f"{'='*80}\n")
                    
                    return {
                        'success': True,
                        'file_url': export_info['url'],
                        'file_name': export_info.get('storedName', file_name),
                        'metadata': {
                            'file_size': export_info.get('size', 0),
                            'format': file_format,
                            'record_count': record_count,
                            'export_duration': duration,
                            'method': 'microservice_direct'
                        }
                    }
                else:
                    error_msg = export_result.get('error', 'Unknown error')
                    debug_print(f"   └─ ❌ Export failed: {error_msg}")
                    total_time = (datetime.datetime.now() - start_time_total).total_seconds()
                    debug_print(f"\n{'='*80}")
                    debug_print(f"❌ [EXPORT] FAILED after {total_time:.2f} seconds")
                    debug_print(f"{'='*80}\n")
                    return {
                        'success': False,
                        'error': error_msg
                    }
            except Exception as microservice_error:
                duration = (datetime.datetime.now() - start_time).total_seconds()
                debug_print(f"   └─ ❌ Microservice call failed after {duration:.2f} seconds: {str(microservice_error)}")
                import traceback
                traceback.print_exc()
                debug_print(f"\n🔄 [EXPORT] Falling back to local export...")
                return local_export_fallback(data, file_format, user_id, options)
        
    except Exception as e:
        total_time = (datetime.datetime.now() - start_time_total).total_seconds()
        debug_print(f"\n{'='*80}")
        debug_print(f"❌ [EXPORT] EXCEPTION after {total_time:.2f} seconds: {str(e)}")
        debug_print(f"{'='*80}")
        import traceback
        traceback.print_exc()
        debug_print(f"\n🔄 [EXPORT] Falling back to local export...")
        # Fallback to local export
        return local_export_fallback(data, file_format, user_id, options)

def local_export_fallback(data, file_format, user_id, options):
    """Local export fallback when S3 microservice is not available"""
    try:
        debug_print(f"🔄 Using local export fallback for format: {file_format}")
        
        # Generate filename
        timestamp = datetime.datetime.now().timestamp()
        if options and options.get('file_name'):
            base_name = options.get('file_name')
            if '.' in base_name:
                base_name = base_name.rsplit('.', 1)[0]
            file_name = f"{base_name}.{file_format}"
        else:
            file_name = f"export_{user_id}_{int(timestamp)}.{file_format}"
        
        # Export locally
        export_functions = {
            'xlsx': export_to_excel,
            'pdf': export_to_pdf,
            'csv': export_to_csv,
            'json': export_to_json,
            'xml': export_to_xml,
            'txt': export_to_txt
        }
        
        if file_format.lower() not in export_functions:
            return {
                'success': False,
                'error': f'Unsupported export format: {file_format}. Supported: {list(export_functions.keys())}'
            }
        
        file_buffer = export_functions[file_format.lower()](data)
        
        # Save locally as fallback
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        local_path = os.path.join(downloads_path, file_name)
        
        with open(local_path, 'wb') as f:
            f.write(file_buffer)
        
        debug_print(f"✅ Local export successful: {local_path}")
        
        return {
            'success': True,
            'file_url': f"file://{local_path}",
            'file_name': file_name,
            'file_size': len(file_buffer),
            'metadata': {
                'file_size': len(file_buffer),
                'format': file_format,
                'record_count': len(data) if isinstance(data, list) else 1,
                'method': 'local_fallback',
                'local_path': local_path
            }
        }
        
    except Exception as e:
        debug_print(f"❌ Local export fallback failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'Local export failed: {str(e)}'
        }

def create_direct_mysql_client(mysql_config: Optional[Dict] = None) -> RenderS3Client:
    """Create RenderS3Client with Direct URL and MySQL from Django settings"""
    try:
        if not mysql_config:
            # Try to use Django settings first
            if DJANGO_SETTINGS_AVAILABLE and hasattr(settings, 'DATABASES'):
                db_config = settings.DATABASES.get('default', {})
                
                mysql_config = {
                    'host': db_config.get('HOST', 'localhost'),
                    'user': db_config.get('USER', 'root'),
                    'password': db_config.get('PASSWORD', 'root'),
                    'database': db_config.get('NAME', 'grc'),
                    'port': int(db_config.get('PORT', 3306))
                }
                
                debug_print(f"🔧 Using Django settings for MySQL: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
            else:
                # Fallback to environment variables
                mysql_config = {
                    'host': os.environ.get('DB_HOST', 'localhost'),
                    'user': os.environ.get('DB_USER', 'root'),
                    'password': os.environ.get('DB_PASSWORD', 'root'),
                    'database': os.environ.get('DB_NAME', 'grc'),
                    'port': int(os.environ.get('DB_PORT', 3306))
                }
                
                debug_print(f"WARNING: Django settings not available, using environment variables: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
        
        debug_print(f"Creating S3 client with MySQL config: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
        client = RenderS3Client("http://15.207.1.40:3000", mysql_config)
        debug_print("S3 client created successfully")
        return client
        
    except ImportError as import_e:
            debug_print(f"ERROR: Import error creating S3 client: {import_e}")
            debug_print("INFO: Trying to create client without MySQL...")
            try:
                client = RenderS3Client("http://15.207.1.40:3000", None)
                debug_print("WARNING: S3 client created without MySQL (fallback mode)")
                return client
            except Exception as fallback_e:
                debug_print(f"ERROR: Fallback S3 client creation failed: {fallback_e}")
                raise Exception(f"S3 client creation failed: {import_e}, Fallback failed: {fallback_e}")
        
    except mysql.connector.Error as mysql_e:
        debug_print(f"ERROR: MySQL connection error: {mysql_e}")
        debug_print("INFO: Creating S3 client without MySQL...")
        try:
            client = RenderS3Client("http://15.207.1.40:3000", None)
            debug_print("WARNING: S3 client created without MySQL (fallback mode)")
            return client
        except Exception as fallback_e:
            debug_print(f"ERROR: Fallback S3 client creation failed: {fallback_e}")
            raise Exception(f"MySQL error: {mysql_e}, Fallback failed: {fallback_e}")
    
    except Exception as e:
        debug_print(f"ERROR: General error creating S3 client: {e}")
        debug_print("INFO: Trying to create client without MySQL...")
        try:
            client = RenderS3Client("http://15.207.1.40:3000", None)
            debug_print("WARNING: S3 client created without MySQL (fallback mode)")
            return client
        except Exception as fallback_e:
            debug_print(f"ERROR: Fallback S3 client creation failed: {fallback_e}")
            raise Exception(f"S3 client creation failed: {e}, Fallback failed: {fallback_e}")

def quick_test():
    """Quick test function"""
    debug_print("Quick Test: Direct S3 Client with Local MySQL")
    debug_print("=" * 60)
    
    # Create client
    client = create_direct_mysql_client()
    
    # Test connections
    result = client.test_connection()
    
    if result['overall_success']:
        debug_print("SUCCESS All systems operational!")
        
        # Show operation stats
        stats = client.get_operation_stats()
        if stats:
            debug_print(f"\n📊 Database Stats:")
            debug_print(f"   Total operations: {stats.get('total_operations', 0)}")
            debug_print(f"   Completed: {stats.get('total_completed', 0)}")
            debug_print(f"   Failed: {stats.get('total_failed', 0)}")
    else:
        debug_print("ERROR Some systems need attention")
        if result['direct_status'] != 'connected':
            debug_print(f"   Direct: {result.get('direct_error', 'Unknown error')}")
        if result['mysql_status'] != 'connected':
            debug_print(f"   MySQL: {result.get('mysql_error', 'Unknown error')}")

# Example usage
def test_all_export_formats():
    """Comprehensive test for all export formats"""
    
    debug_print("🚀 Testing All Export Formats")
    debug_print("🌐 Direct URL: http://15.207.1.40:3000")
    debug_print("📊 Testing: JSON, CSV, XML, TXT, PDF")
    debug_print("=" * 60)
    
    # Create client (will use Django settings automatically)
    client = create_direct_mysql_client()
    
    # Test connections
    debug_print("1. Testing connections...")
    result = client.test_connection()
    
    if not result['overall_success']:
        debug_print("ERROR Cannot proceed - fix connection issues first")
        return
    
    # Sample data for testing all formats
    sample_data = [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@company.com",
            "department": "Engineering",
            "position": "Senior Developer",
            "salary": "$85,000",
            "hire_date": "2022-01-15",
            "status": "Active"
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane.smith@company.com",
            "department": "Marketing",
            "position": "Marketing Manager",
            "salary": "$75,000",
            "hire_date": "2021-08-20",
            "status": "Active"
        },
        {
            "id": 3,
            "name": "Bob Johnson",
            "email": "bob.johnson@company.com",
            "department": "Sales",
            "position": "Sales Representative",
            "salary": "$65,000",
            "hire_date": "2023-03-10",
            "status": "Active"
        },
        {
            "id": 4,
            "name": "Alice Brown",
            "email": "alice.brown@company.com",
            "department": "HR",
            "position": "HR Specialist",
            "salary": "$70,000",
            "hire_date": "2022-11-05",
            "status": "Active"
        },
        {
            "id": 5,
            "name": "Charlie Wilson",
            "email": "charlie.wilson@company.com",
            "department": "Finance",
            "position": "Financial Analyst",
            "salary": "$80,000",
            "hire_date": "2021-12-01",
            "status": "Active"
        }
    ]
    
    # Test all supported formats
    export_formats = ['json', 'csv', 'xml', 'txt', 'pdf']
    results = {}
    
    debug_print(f"\n2. Testing {len(export_formats)} export formats...")
    debug_print(f"📊 Data: {len(sample_data)} employee records")
    
    for i, export_format in enumerate(export_formats, 1):
        debug_print(f"\n--- Test {i}/{len(export_formats)}: {export_format.upper()} Export ---")
        
        try:
            file_name = f"employee_report_{export_format}"
            user_id = "export_test_user"
            
            debug_print(f"📤 Exporting as {export_format.upper()}...")
            export_result = client.export(sample_data, export_format, file_name, user_id)
            
            if export_result['success']:
                debug_print(f"SUCCESS {export_format.upper()} Export: SUCCESS")
                debug_print(f"   📄 File: {export_result['export_info']['storedName']}")
                debug_print(f"   💾 Size: {export_result['export_info']['size']} bytes")
                debug_print(f"   🔗 URL: {export_result['export_info']['url']}")
                debug_print(f"   🆔 Operation ID: {export_result['operation_id']}")
                
                # Test download of exported file
                try:
                    download_url = export_result['export_info']['downloadUrl']
                    download_response = requests.get(download_url, timeout=30)
                    
                    if download_response.status_code == 200:
                        debug_print(f"   📥 Download: SUCCESS ({len(download_response.content)} bytes)")
                        
                        # Save file locally for verification
                        local_filename = f"test_export_{export_format}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
                        with open(local_filename, 'wb') as f:
                            f.write(download_response.content)
                        debug_print(f"   💾 Saved locally: {local_filename}")
                    else:
                        debug_print(f"   ERROR Download: FAILED (Status: {download_response.status_code})")
                        
                except Exception as download_error:
                    debug_print(f"   ERROR Download: ERROR - {download_error}")
                
                results[export_format] = {
                    'status': 'success',
                    'operation_id': export_result['operation_id'],
                    'file_info': export_result['export_info']
                }
                
            else:
                debug_print(f"ERROR {export_format.upper()} Export: FAILED")
                debug_print(f"   Error: {export_result['error']}")
                results[export_format] = {
                    'status': 'failed',
                    'error': export_result['error']
                }
                
        except Exception as e:
            debug_print(f"ERROR {export_format.upper()} Export: EXCEPTION")
            debug_print(f"   Error: {str(e)}")
            results[export_format] = {
                'status': 'exception',
                'error': str(e)
            }
    
    # Summary report
    debug_print("\n" + "=" * 60)
    debug_print("📊 EXPORT TEST SUMMARY")
    debug_print("=" * 60)
    
    successful_formats = []
    failed_formats = []
    
    for format_name, result in results.items():
        if result['status'] == 'success':
            successful_formats.append(format_name.upper())
            debug_print(f"SUCCESS {format_name.upper()}: SUCCESS")
        else:
            failed_formats.append(format_name.upper())
            debug_print(f"ERROR {format_name.upper()}: FAILED - {result.get('error', 'Unknown error')}")
    
    debug_print(f"\n📈 Results:")
    debug_print(f"   SUCCESS Successful: {len(successful_formats)}/{len(export_formats)}")
    debug_print(f"   ERROR Failed: {len(failed_formats)}/{len(export_formats)}")
    
    if successful_formats:
        debug_print(f"   🎉 Working formats: {', '.join(successful_formats)}")
    
    if failed_formats:
        debug_print(f"   ⚠️  Failed formats: {', '.join(failed_formats)}")
    
    # Show operation history
    debug_print(f"\n📋 Recent operation history:")
    history = client.get_operation_history('export_test_user', 10)
    
    if history:
        for i, op in enumerate(history, 1):
            status_emoji = "SUCCESS" if op['status'] == 'completed' else "ERROR" if op['status'] == 'failed' else "PENDING"
            debug_print(f"   {i}. {status_emoji} {op['operation_type']} - {op['file_name']} ({op['status']})")
    else:
        debug_print("   No operations found in database")
    
    debug_print(f"\n🎉 Export format testing completed!")
    return results

def main():
    """Example usage of Direct S3 Client with MySQL from Django settings"""
    
    debug_print("🚀 Direct S3 Microservice Client with MySQL")
    debug_print("🌐 Direct URL: http://15.207.1.40:3000")
    debug_print("🗄️  Database: MySQL (from Django settings)")
    debug_print("🔐 AWS Credentials: Handled by microservice")
    debug_print("=" * 60)
    
    # Create client (will use Django settings automatically)
    client = create_direct_mysql_client()
    
    # Test connections
    debug_print("1. Testing connections...")
    result = client.test_connection()
    
    if not result['overall_success']:
        debug_print("ERROR Cannot proceed - fix connection issues first")
        return
    
    # Example operations
    sample_data = [
        {"id": 1, "name": "MySQL Test", "platform": "Render", "status": "active"},
        {"id": 2, "name": "S3 Integration", "platform": "AWS", "status": "deployed"},
        {"id": 3, "name": "Database Tracking", "platform": "MySQL", "status": "operational"}
    ]
    
    debug_print("\n2. Testing export functionality...")
    export_result = client.export(sample_data, 'json', 'mysql_render_test', 'test_user')
    
    if export_result['success']:
        debug_print(f"SUCCESS Export successful!")
        debug_print(f"   Operation ID: {export_result['operation_id']}")
        debug_print(f"   File: {export_result['export_info']['storedName']}")
        debug_print(f"   URL: {export_result['export_info']['url']}")
        
        # Test download
        debug_print("\n3. Testing download functionality...")
        s3_key = export_result['export_info']['s3Key']
        file_name = export_result['export_info']['storedName']
        
        download_result = client.download(s3_key, file_name, './mysql_downloads', 'test_user')
        
        if download_result['success']:
            debug_print(f"SUCCESS Download successful!")
            debug_print(f"   Operation ID: {download_result['operation_id']}")
            debug_print(f"   File saved: {download_result['file_path']}")
        else:
            debug_print(f"ERROR Download failed: {download_result['error']}")
    else:
        debug_print(f"ERROR Export failed: {export_result['error']}")
    
    # Show operation history
    debug_print("\n4. Operation history from MySQL:")
    history = client.get_operation_history('test_user', 5)
    
    if history:
        for i, op in enumerate(history, 1):
            debug_print(f"   {i}. {op['operation_type']} - {op['file_name']} - {op['status']} ({op['created_at']})")
    else:
        debug_print("   No operations found in database")
    
    # Show statistics
    debug_print("\n5. Database statistics:")
    stats = client.get_operation_stats()
    
    if stats:
        debug_print(f"   Total operations: {stats.get('total_operations', 0)}")
        debug_print(f"   Completed: {stats.get('total_completed', 0)}")
        debug_print(f"   Failed: {stats.get('total_failed', 0)}")
        
        if stats.get('operations_by_type'):
            debug_print("   Operations by type:")
            for op_stat in stats['operations_by_type']:
                debug_print(f"     - {op_stat['operation_type']}: {op_stat['total_count']} total")
    
    debug_print("\n🎉 Render + MySQL integration test completed!")

def test_pdf_processing():
    """Test PDF upload with automatic metadata extraction and summary generation"""
    
    debug_print("🚀 Testing PDF Processing with OpenAI Summarization")
    debug_print("🌐 Direct URL: http://15.207.1.40:3000")
    debug_print("🤖 AI: OpenAI for document summarization")
    debug_print("=" * 60)
    
    # Create client (will use Django settings automatically)
    client = create_direct_mysql_client()
    
    # Test connections
    debug_print("\n1. Testing connections...")
    result = client.test_connection()
    
    if not result['overall_success']:
        debug_print("ERROR Cannot proceed - fix connection issues first")
        return
    
    # Check for PDF processing libraries
    debug_print("\n2. Checking PDF processing libraries...")
    debug_print(f"   PyPDF2: {'✅ Available' if PDF_LIBRARY_AVAILABLE else '❌ Not available'}")
    debug_print(f"   pdfplumber: {'✅ Available' if PDFPLUMBER_AVAILABLE else '❌ Not available'}")
    debug_print(f"   OpenAI: {'✅ Available' if OPENAI_AVAILABLE else '❌ Not available'}")
    
    if not PDF_LIBRARY_AVAILABLE and not PDFPLUMBER_AVAILABLE:
        debug_print("\n⚠️  WARNING: No PDF processing library available!")
        debug_print("   Install PyPDF2 or pdfplumber: pip install PyPDF2 pdfplumber")
        return
    
    if not OPENAI_AVAILABLE:
        debug_print("\n⚠️  WARNING: OpenAI library not available!")
        debug_print("   Install OpenAI: pip install openai")
        return
    
    # You would need to provide a test PDF file path
    debug_print("\n3. Upload a PDF file to test...")
    debug_print("   📝 Note: Provide a PDF file path to test the feature")
    debug_print("   📝 Example usage:")
    debug_print("""
    # Upload PDF
    upload_result = client.upload(
        file_path='/path/to/your/document.pdf',
        user_id='test_user',
        module='policy'
    )
    
    if upload_result['success']:
        operation_id = upload_result['operation_id']
        debug_print(f"✅ Upload successful! Operation ID: {operation_id}")
        debug_print(f"📄 PDF processing: {upload_result.get('pdf_processing', 'N/A')}")
        
        # Wait a few seconds for processing
        import time
        debug_print("⏳ Waiting for PDF processing to complete...")
        time.sleep(10)
        
        # Check processing status
        status = client.get_pdf_processing_status(operation_id)
        debug_print(f"\\n📊 Processing Status: {status['status']}")
        
        if status['status'] == 'completed':
            debug_print(f"\\n📋 Metadata:")
            for key, value in status['metadata'].items():
                debug_print(f"   {key}: {value}")
            
            debug_print(f"\\n📝 Summary:")
            debug_print(f"   {status['summary']}")
    """)
    
    debug_print("\n✅ PDF processing feature is ready to use!")
    debug_print("\n💡 Tips:")
    debug_print("   - Processing happens in background (non-blocking)")
    debug_print("   - Smart extraction: Small docs fully processed, large docs sampled")
    debug_print("   - Summary is limited to 10 lines maximum")
    debug_print("   - Metadata includes: title, author, page count, file size, category, etc.")
    debug_print("   - Check processing status using: client.get_pdf_processing_status(operation_id)")

def test_enhanced_pdf_processing_with_sample(pdf_path: str = None):
    """
    Test the ENHANCED PDF processing feature with a sample PDF
    
    This demonstrates the new intelligent features:
    - Smart text extraction (small vs large documents)
    - Comprehensive metadata extraction
    - AI-powered summary generation using GPT-3.5-turbo
    - Automatic categorization
    - Database integration
    
    Args:
        pdf_path: Path to a PDF file to test. If None, instructions are provided.
    """
    
    debug_print("="*80)
    debug_print("🚀 ENHANCED PDF PROCESSING TEST")
    debug_print("="*80)
    debug_print("\nThis test demonstrates the NEW intelligent PDF processing features:")
    debug_print("✅ Smart extraction strategy (optimized for cost & time)")
    debug_print("✅ Comprehensive metadata extraction")
    debug_print("✅ AI-powered summary generation (GPT-3.5-turbo)")
    debug_print("✅ Automatic document categorization")
    debug_print("✅ Full database integration")
    debug_print("="*80)
    
    # Create client
    debug_print("\n[1] Creating S3 client...")
    client = create_direct_mysql_client()
    
    # Test connections
    debug_print("\n[2] Testing connections...")
    result = client.test_connection()
    
    if not result['overall_success']:
        debug_print("❌ Cannot proceed - fix connection issues first")
        return
    
    debug_print("✅ All connections successful!")
    
    # Check for required libraries
    debug_print("\n[3] Checking required libraries...")
    debug_print(f"   PyPDF2: {'✅ Available' if PDF_LIBRARY_AVAILABLE else '❌ Not available'}")
    debug_print(f"   pdfplumber: {'✅ Available' if PDFPLUMBER_AVAILABLE else '❌ Not available'}")
    debug_print(f"   OpenAI: {'✅ Available' if OPENAI_AVAILABLE else '❌ Not available'}")
    
    if not (PDF_LIBRARY_AVAILABLE or PDFPLUMBER_AVAILABLE):
        debug_print("\n⚠️  WARNING: No PDF processing library available!")
        debug_print("   Install: pip install PyPDF2 pdfplumber")
        return
    
    if not OPENAI_AVAILABLE:
        debug_print("\n⚠️  WARNING: OpenAI library not available!")
        debug_print("   Install: pip install openai")
        return
    
    # Check for PDF file
    if not pdf_path or not os.path.exists(pdf_path):
        debug_print("\n[4] No PDF file provided for testing")
        debug_print("\n📝 To test with your own PDF, run:")
        debug_print("""
from grc.routes.Global.s3_fucntions import test_enhanced_pdf_processing_with_sample

# Test with a small document (1-5 pages)
test_enhanced_pdf_processing_with_sample('/path/to/small_policy.pdf')

# Test with a large document (20+ pages)
test_enhanced_pdf_processing_with_sample('/path/to/large_manual.pdf')
        """)
        debug_print("\n✅ Enhanced PDF processing feature is READY and CONFIGURED!")
        debug_print("\n📊 Feature Summary:")
        debug_print("   - Smart Extraction: Optimized for different document sizes")
        debug_print("   - AI Summary: Using GPT-3.5-turbo")
        debug_print("   - Auto-categorization: policy, audit, risk, incident")
        debug_print("   - Background Processing: Non-blocking upload")
        debug_print("   - Database Storage: metadata + summary fields")
        return
    
    # Test with actual PDF
    debug_print(f"\n[4] Testing with PDF: {os.path.basename(pdf_path)}")
    debug_print(f"   File size: {round(os.path.getsize(pdf_path) / (1024 * 1024), 2)} MB")
    
    # Upload the PDF
    debug_print("\n[5] Uploading PDF to S3...")
    upload_result = client.upload(
        file_path=pdf_path,
        user_id='test_enhanced_user',
        module='policy'  # Change as needed
    )
    
    if not upload_result['success']:
        debug_print(f"❌ Upload failed: {upload_result.get('error')}")
        return
    
    operation_id = upload_result['operation_id']
    debug_print(f"✅ Upload successful!")
    debug_print(f"   Operation ID: {operation_id}")
    debug_print(f"   S3 URL: {upload_result['file_info']['url']}")
    debug_print(f"   PDF Processing: {upload_result.get('pdf_processing', 'N/A')}")
    
    # Wait for processing
    debug_print("\n[6] Waiting for background processing to complete...")
    import time
    
    max_wait = 60  # Maximum 60 seconds
    wait_interval = 5  # Check every 5 seconds
    elapsed = 0
    
    while elapsed < max_wait:
        time.sleep(wait_interval)
        elapsed += wait_interval
        
        debug_print(f"   ⏳ Checking status... ({elapsed}s elapsed)")
        status = client.get_pdf_processing_status(operation_id)
        
        if status['status'] == 'completed':
            debug_print(f"   ✅ Processing completed in {elapsed} seconds!")
            break
        elif status['status'] == 'error' or status['status'] == 'failed':
            debug_print(f"   ❌ Processing failed: {status.get('message')}")
            return
        else:
            debug_print(f"   ⏳ Still processing...")
    
    # Display results
    if status['status'] == 'completed':
        debug_print("\n" + "="*80)
        debug_print("✅ PROCESSING COMPLETED SUCCESSFULLY!")
        debug_print("="*80)
        
        debug_print("\n📋 EXTRACTED METADATA:")
        debug_print("-"*80)
        metadata = status.get('metadata', {})
        for key, value in sorted(metadata.items()):
            if isinstance(value, dict):
                debug_print(f"   {key}: {json.dumps(value, indent=2)}")
            else:
                debug_print(f"   {key}: {value}")
        
        debug_print("\n📝 AI-GENERATED SUMMARY:")
        debug_print("-"*80)
        summary = status.get('summary', 'No summary available')
        for line in summary.split('\n'):
            debug_print(f"   {line}")
        
        debug_print("\n" + "="*80)
        debug_print("🎉 TEST COMPLETED SUCCESSFULLY!")
        debug_print("="*80)
        debug_print("\n📊 Feature Highlights Demonstrated:")
        debug_print(f"   ✅ Document Size: {metadata.get('document_size_category', 'unknown').upper()}")
        debug_print(f"   ✅ Extraction Strategy: {metadata.get('extraction_strategy', 'unknown')}")
        debug_print(f"   ✅ Pages Processed: {metadata.get('page_count', 'unknown')}")
        debug_print(f"   ✅ AI Model Used: {metadata.get('ai_model', 'unknown')}")
        debug_print(f"   ✅ Auto-Category: {metadata.get('suggested_category', 'unknown')}")
        debug_print(f"   ✅ Summary Generated: Yes ({len(summary)} characters)")
    else:
        debug_print(f"\n⏳ Processing is taking longer than expected...")
        debug_print(f"   Check status later using: client.get_pdf_processing_status({operation_id})")

# if __name__ == "__main__":
#     # Run the comprehensive export format test
#     # test_all_export_formats()
#     
#     # OR run the PDF processing test
#     # test_pdf_processing()
#     
#     # OR run the NEW enhanced PDF processing test
#     # test_enhanced_pdf_processing_with_sample('/path/to/your/pdf/file.pdf')