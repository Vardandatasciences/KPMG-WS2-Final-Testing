"""
S3 document handling and text extraction
"""
import io
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from .config import (
    BOTO3_AVAILABLE,
    S3_CONFIG,
    S3_CACHE_FILE,
    DEFAULT_MAX_S3_DOCUMENTS,
    EVIDENCE_DATAFRAMES,
    boto3,
)

CACHE_VERSION = "v2"
DEFAULT_FRAMEWORK_KEY = "__global__"

if BOTO3_AVAILABLE:
    from botocore.exceptions import ClientError, NoCredentialsError


def _framework_cache_key(framework_id: Optional[int] = None, framework_name: Optional[str] = None) -> str:
    """Create a stable framework cache key."""
    if framework_id is not None:
        return f"id:{framework_id}"
    if framework_name:
        return f"name:{framework_name.strip().lower()}"
    return DEFAULT_FRAMEWORK_KEY


def _normalize_cache_structure(raw_cache: Any) -> Dict[str, Any]:
    """Upgrade legacy cache formats to the latest structure."""
    cache: Dict[str, Any] = {}
    if isinstance(raw_cache, dict):
        cache = dict(raw_cache)

    frameworks_section = cache.get("frameworks")

    # Legacy format: direct mapping cache_key -> doc_data
    if not isinstance(frameworks_section, dict):
        legacy_entries = cache if isinstance(cache, dict) else {}
        cache = {
            "version": CACHE_VERSION,
            "frameworks": {
                DEFAULT_FRAMEWORK_KEY: legacy_entries if isinstance(legacy_entries, dict) else {}
            },
        }
    else:
        cache = {
            "version": cache.get("version", CACHE_VERSION),
            "frameworks": dict(frameworks_section),
        }

    # Ensure version is present
    cache["version"] = cache.get("version", CACHE_VERSION)
    cache.setdefault("frameworks", {})

    # Guarantee nested dicts
    for fw_key, entries in list(cache["frameworks"].items()):
        if not isinstance(entries, dict):
            cache["frameworks"][fw_key] = {}

    return cache


def load_s3_cache() -> Dict[str, Any]:
    """Load S3 document cache from file."""
    if not S3_CACHE_FILE.exists():
        return {"version": CACHE_VERSION, "frameworks": {}}

    try:
        with open(S3_CACHE_FILE, "r", encoding="utf-8") as f:
            raw_cache = json.load(f)
        cache = _normalize_cache_structure(raw_cache)
        total_entries = sum(len(entries) for entries in cache.get("frameworks", {}).values())
        print(f"[INFO] [CACHE] Loaded S3 cache with {total_entries} cached documents across {len(cache.get('frameworks', {}))} frameworks")
        return cache
    except Exception as e:
        print(f"[WARNING] [CACHE] Error loading cache file: {e}")
        return {"version": CACHE_VERSION, "frameworks": {}}


def save_s3_cache(cache: Dict[str, Any]):
    """Save S3 document cache to file."""
    try:
        normalized = _normalize_cache_structure(cache)
        normalized["version"] = CACHE_VERSION
        with open(S3_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2, default=str)
        total_entries = sum(len(entries) for entries in normalized.get("frameworks", {}).values())
        print(f"[INFO] [CACHE] Saved S3 cache with {total_entries} documents across {len(normalized.get('frameworks', {}))} frameworks")
    except Exception as e:
        print(f"[WARNING] [CACHE] Error saving cache file: {e}")


def get_cache_key(bucket, key):
    """Generate cache key for a document."""
    return f"{bucket}:{key}"


def is_document_unchanged(cached_doc, s3_obj):
    """Check if document is unchanged by comparing metadata."""
    if not cached_doc:
        return False
    
    # Compare size and last modified
    cached_size = cached_doc.get('size')
    cached_last_modified = cached_doc.get('last_modified')
    
    s3_size = s3_obj.get('Size')
    s3_last_modified = s3_obj.get('LastModified')
    
    # Convert S3 LastModified to ISO string for comparison
    if s3_last_modified:
        s3_last_modified_str = s3_last_modified.isoformat() if hasattr(s3_last_modified, 'isoformat') else str(s3_last_modified)
    else:
        s3_last_modified_str = None
    
    # Document is unchanged if size and last_modified match
    return (cached_size == s3_size and 
            cached_last_modified == s3_last_modified_str and
            cached_doc.get('extracted_text') is not None)


def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF bytes."""
    try:
        try:
            import PyPDF2
        except ImportError:
            print("[WARNING] PyPDF2 not installed. Install with: pip install PyPDF2")
            return "[PDF content extraction requires PyPDF2 library]"
        
        import io
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        # Process all pages
        for page_num, page in enumerate(pdf_reader.pages):
            text += page.extract_text() + "\n"
        return text  # Return full extracted text
    except Exception as e:
        print(f"[WARNING] Error extracting PDF text: {e}")
        return ""


def extract_text_from_txt(txt_bytes):
    """Extract text from TXT file."""
    try:
        return txt_bytes.decode('utf-8', errors='ignore')  # Return full text
    except Exception as e:
        print(f"[WARNING] Error extracting TXT text: {e}")
        return ""


def extract_text_from_excel(excel_bytes, filename=""):
    """Extract text from Excel file by concatenating sheet data."""
    import io

    try:
        buffer = io.BytesIO(excel_bytes)
        sheets = pd.read_excel(buffer, sheet_name=None, dtype=str)
    except ImportError:
        print("[WARNING] openpyxl or xlrd not installed. Install with: pip install openpyxl xlrd")
        return f"[Excel content extraction requires openpyxl/xlrd library for {filename}]"
    except Exception as e:
        print(f"[WARNING] Error extracting Excel text from {filename}: {e}")
        return ""

    extracted_sections = []
    for sheet_name, df in sheets.items():
        if df is None or df.empty:
            continue
        df_clean = df.fillna("")
        csv_text = df_clean.to_csv(index=False)
        extracted_sections.append(f"[Sheet: {sheet_name}]")
        extracted_sections.append(csv_text.strip())

    if not extracted_sections:
        return f"[Excel file {filename} contains no readable data]"
    return "\n".join(extracted_sections)


def _load_dataframe_from_bytes(file_bytes: bytes, key: str) -> Optional[pd.DataFrame]:
    """Load an Excel/CSV file into a DataFrame."""
    extension = Path(key).suffix.lower()
    buffer = io.BytesIO(file_bytes)

    try:
        if extension in ('.xlsx', '.xls'):
            data = pd.read_excel(buffer)
            if isinstance(data, dict):
                # If multiple sheets returned, use the first
                for _, df in data.items():
                    data = df
                    break
            df = data
        elif extension == '.csv':
            df = pd.read_csv(buffer)
        else:
            return None
    except Exception as exc:
        print(f"[WARNING] [INGEST] Failed to read {key}: {exc}")
        return None

    if df is None or df.empty:
        return None

    df = df.reset_index(drop=True)
    return df


def store_dataframe_for_document(bucket: str, key: str, df: Optional[pd.DataFrame]) -> Optional[str]:
    """Persist extracted tabular data from a document into in-memory cache."""
    if df is None:
        return None
    if df.empty:
        return None
    dataset_id = f"{bucket}/{key}"
    try:
        EVIDENCE_DATAFRAMES[dataset_id] = df.copy()
        return dataset_id
    except Exception as exc:
        print(f"[WARNING] [DATAFRAME_STORE] Failed to cache dataframe for {dataset_id}: {exc}")
        return None


def ensure_dataframe_for_document(bucket: str, key: str, file_bytes: Optional[bytes] = None) -> Optional[str]:
    """Ensure structured data for the document is cached in memory."""
    dataset_id = f"{bucket}/{key}"
    if dataset_id in EVIDENCE_DATAFRAMES:
        return dataset_id

    extension = Path(key).suffix.lower()
    if extension not in ('.xlsx', '.xls', '.csv'):
        return None

    data_bytes = file_bytes
    if data_bytes is None:
        if not BOTO3_AVAILABLE:
            return None
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=S3_CONFIG['aws_access_key_id'],
                aws_secret_access_key=S3_CONFIG['aws_secret_access_key'],
                region_name=S3_CONFIG['region_name']
            )
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            data_bytes = obj['Body'].read()
        except Exception as exc:
            print(f"[WARNING] [DATAFRAME_STORE] Unable to download {key} for dataframe caching: {exc}")
            return None

    df = _load_dataframe_from_bytes(data_bytes, key)
    return store_dataframe_for_document(bucket, key, df)


def get_s3_documents(
    max_documents: Optional[int] = None,
    framework_id: Optional[int] = None,
    framework_name: Optional[str] = None,
):
    """Get documents from S3 bucket and extract their content.
    Uses caching to avoid re-extracting unchanged documents."""
    print(f"[INFO] [STEP] Starting S3 document retrieval and content extraction...")
    print(f"[INFO] [CACHE] Loading S3 document cache...")
    
    # Load cache
    cache = load_s3_cache()
    frameworks_cache = cache.setdefault("frameworks", {})
    framework_key = _framework_cache_key(framework_id, framework_name)
    framework_cache = frameworks_cache.setdefault(framework_key, {})
    legacy_cache = None
    if framework_key != DEFAULT_FRAMEWORK_KEY:
        legacy_cache = frameworks_cache.get(DEFAULT_FRAMEWORK_KEY)
    
    documents = []
    cached_count = 0
    new_count = 0
    updated_count = 0
    
    if not BOTO3_AVAILABLE:
        print("[INFO] [SKIP] Skipping S3 document retrieval (boto3 not available)")
        return documents
    
    try:
        print(f"[INFO] [CONNECT] Connecting to S3 service...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=S3_CONFIG['aws_access_key_id'],
            aws_secret_access_key=S3_CONFIG['aws_secret_access_key'],
            region_name=S3_CONFIG['region_name']
        )
        print(f"[INFO] [SUCCESS] Connected to S3")
        
        # List buckets
        print(f"[INFO] [QUERY] Listing S3 buckets...")
        buckets = s3_client.list_buckets()
        bucket_list = buckets.get('Buckets', [])
        print(f"[INFO] [SUCCESS] Found {len(bucket_list)} S3 buckets")
        
        # Filter to only process "kpistestingwithai" bucket
        target_bucket_name = "kpistestingwithai"
        target_bucket = None
        for bucket in bucket_list:
            if bucket['Name'] == target_bucket_name:
                target_bucket = bucket
                break
        
        if not target_bucket:
            print(f"[WARNING] Bucket '{target_bucket_name}' not found. Available buckets: {[b['Name'] for b in bucket_list]}")
            return documents
        
        print(f"[INFO] [CONFIG] Processing all documents from bucket: {target_bucket_name} only")
        
        # List objects in the target bucket (process all documents)
        bucket_name = target_bucket_name
        print(f"[INFO] [BUCKET] Processing bucket: {bucket_name}")
        try:
            print(f"[INFO] [QUERY] Listing all objects in bucket: {bucket_name}")
            objects = []
            continuation_token = None
            page_count = 0
            while True:
                page_count += 1
                if continuation_token:
                    response = s3_client.list_objects_v2(Bucket=bucket_name, ContinuationToken=continuation_token)
                else:
                    response = s3_client.list_objects_v2(Bucket=bucket_name)
                
                page_objects = response.get('Contents', [])
                objects.extend(page_objects)
                print(f"[INFO] [QUERY] Page {page_count}: Found {len(page_objects)} objects (Total so far: {len(objects)})")
                
                if not response.get('IsTruncated'):
                    break
                continuation_token = response.get('NextContinuationToken')
            
            print(f"[INFO] [SUCCESS] Found {len(objects)} total objects in bucket {bucket_name}")
            
            # First pass: Count valid documents
            print(f"[INFO] [COUNT] Counting valid documents (PDF, TXT, DOC, DOCX)...")
            valid_documents = []
            for obj in objects:
                key = obj['Key']
                file_ext = key.lower()
                if file_ext.endswith(('.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.csv')):
                    valid_documents.append((obj, key))

            valid_documents.sort(
                key=lambda entry: entry[0].get('LastModified') or datetime.min,
                reverse=True
            )
            max_limit = max_documents if max_documents is not None else DEFAULT_MAX_S3_DOCUMENTS
            if len(valid_documents) > max_limit:
                print(f"[INFO] [COUNT] Limiting to most recent {max_limit} documents out of {len(valid_documents)} valid files.")
                valid_documents = valid_documents[:max_limit]
            
            total_docs = len(valid_documents)
            print(f"[INFO] [COUNT] Found {total_docs} valid documents to process out of {len(objects)} total objects (limited to most recent {max_limit})")
            print(f"[INFO] [PROGRESS] Starting document processing: 0/{total_docs} (Remaining: {total_docs})")
            
            # Second pass: Process documents
            doc_count = 0
            last_progress_time = time.time()
            
            for obj, key in valid_documents:
                doc_count += 1
                file_ext = key.lower()
                remaining = total_docs - doc_count
                
                # Show progress every document and also every 5 seconds
                current_time = time.time()
                show_detailed = (doc_count % 10 == 0) or (current_time - last_progress_time >= 5.0)
                
                if show_detailed:
                    last_progress_time = current_time
                    progress_pct = (doc_count / total_docs * 100) if total_docs > 0 else 0
                    print(f"[INFO] [PROGRESS] [{doc_count}/{total_docs}] ({progress_pct:.1f}%) - Remaining: {remaining} documents")
                
                # Check cache first
                cache_key = get_cache_key(bucket_name, key)
                cached_doc = framework_cache.get(cache_key)
                if not cached_doc and legacy_cache:
                    cached_doc = legacy_cache.get(cache_key)
                    if cached_doc:
                        print(f"[INFO] [CACHE] Migrating legacy cache entry for {key} into framework scope {framework_key}")
                        cached_doc.setdefault("framework_key", framework_key)
                        framework_cache[cache_key] = cached_doc
                
                # Check if document is unchanged
                if is_document_unchanged(cached_doc, obj):
                    # Use cached data
                    print(f"[INFO] [CACHE] [{doc_count}/{total_docs}] Using cached data for: {key}")
                    if cached_doc.get('dataset_id'):
                        ensure_dataframe_for_document(bucket_name, key)
                    documents.append(cached_doc)
                    cached_count += 1
                else:
                    # Document is new or changed - download and extract
                    if cached_doc:
                        print(f"[INFO] [UPDATE] [{doc_count}/{total_docs}] Document changed, re-extracting: {key}")
                        updated_count += 1
                    else:
                        print(f"[INFO] [NEW] [{doc_count}/{total_docs}] New document, extracting: {key}")
                        new_count += 1
                    
                    try:
                        # Download object
                        obj_response = s3_client.get_object(Bucket=bucket_name, Key=key)
                        file_bytes = obj_response['Body'].read()
                        print(f"[INFO] [DOWNLOAD] Downloaded {len(file_bytes)} bytes from {key}")
                        
                        # Extract text based on file type
                        print(f"[INFO] [EXTRACT] Extracting text content from {key}...")
                        extracted_text = ""
                        structured_df: Optional[pd.DataFrame] = None
                        dataset_id: Optional[str] = None

                        if file_ext.endswith('.pdf'):
                            extracted_text = extract_text_from_pdf(file_bytes)
                            print(f"[INFO] [EXTRACT] PDF: Extracted {len(extracted_text)} characters from {key}")
                        elif file_ext.endswith('.txt'):
                            extracted_text = extract_text_from_txt(file_bytes)
                            print(f"[INFO] [EXTRACT] TXT: Extracted {len(extracted_text)} characters from {key}")
                        elif file_ext.endswith('.csv'):
                            try:
                                extracted_text = file_bytes.decode('utf-8', errors='ignore')
                            except Exception:
                                extracted_text = extract_text_from_txt(file_bytes)
                            structured_df = _load_dataframe_from_bytes(file_bytes, key)
                            print(f"[INFO] [EXTRACT] CSV: Extracted {len(extracted_text)} characters from {key}")
                        elif file_ext.endswith(('.doc', '.docx')):
                            # For DOC/DOCX, we'll just note the file (requires python-docx)
                            extracted_text = f"[DOC/DOCX file: {key} - content extraction requires python-docx library]"
                            print(f"[INFO] [SKIP] DOC/DOCX extraction requires python-docx library for {key}")
                        elif file_ext.endswith(('.xls', '.xlsx')):
                            extracted_text = extract_text_from_excel(file_bytes, key)
                            print(f"[INFO] [EXTRACT] Excel: Extracted {len(extracted_text)} characters from {key}")
                            structured_df = _load_dataframe_from_bytes(file_bytes, key)

                        if structured_df is not None:
                            dataset_id = store_dataframe_for_document(bucket_name, key, structured_df)
                            if dataset_id:
                                print(f"[INFO] [DATAFRAME] Cached structured dataset for {dataset_id} with {len(structured_df)} rows")
                        
                        # Get metadata
                        metadata = s3_client.head_object(Bucket=bucket_name, Key=key)

                        # Prepare document data
                        doc_data = {
                            'bucket': bucket_name,
                            'key': key,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat() if hasattr(obj['LastModified'], 'isoformat') else str(obj['LastModified']),
                            'content_type': metadata.get('ContentType', 'unknown'),
                            'extracted_text': extracted_text if extracted_text else "",  # Full text
                            'dataset_id': dataset_id
                        }
                        
                        # Update cache
                        doc_data["framework_key"] = framework_key
                        framework_cache[cache_key] = doc_data
                        
                    except Exception as e:
                        print(f"[WARNING] [ERROR] Error processing {key}: {e}")
                        continue
                    
                    # Success message for newly extracted documents
                    print(f"[INFO] [SUCCESS] Processed [{doc_count}/{total_docs}]: {key} ({len(extracted_text)} chars extracted) - Remaining: {remaining}")
                    time.sleep(0.1)  # Small delay to show progress
                        
        except ClientError as e:
            print(f"[WARNING] [ERROR] Error accessing bucket {bucket_name}: {e}")
        
        # Save updated cache
        print(f"[INFO] [CACHE] Saving updated cache...")
        cache["frameworks"][framework_key] = framework_cache
        save_s3_cache(cache)
        
        # Print summary
        print(f"\n[INFO] [COMPLETE] Finished processing S3 documents:")
        print(f"[INFO]   - Total documents: {len(documents)}")
        print(f"[INFO]   - From cache: {cached_count}")
        print(f"[INFO]   - New documents: {new_count}")
        print(f"[INFO]   - Updated documents: {updated_count}")
        print(f"[INFO]   - Cache saved to: {S3_CACHE_FILE}")
        
        return documents
    except NoCredentialsError:
        print("[WARNING] AWS credentials not configured properly")
        return []
    except Exception as e:
        print(f"[WARNING] Error accessing S3: {e}")
        return []


def fetch_single_s3_document(
    bucket: str,
    key: str,
    framework_id: Optional[int] = None,
    framework_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Download a single S3 object, extract text, update cache, and return doc metadata."""
    if not BOTO3_AVAILABLE:
        print("[WARNING] [S3_SINGLE] boto3 not available; cannot process uploaded document.")
        return None

    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=S3_CONFIG['aws_access_key_id'],
            aws_secret_access_key=S3_CONFIG['aws_secret_access_key'],
            region_name=S3_CONFIG['region_name']
        )

        metadata = s3_client.head_object(Bucket=bucket, Key=key)
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        file_bytes = obj['Body'].read()

        last_modified = metadata.get('LastModified')
        if hasattr(last_modified, 'isoformat'):
            last_modified = last_modified.isoformat()
        else:
            last_modified = str(last_modified)

        content_type = metadata.get('ContentType', 'unknown')
        size = metadata.get('ContentLength', 0)

        extracted_text = ""
        key_lower = key.lower()
        structured_df: Optional[pd.DataFrame] = None
        dataset_id: Optional[str] = None

        if key_lower.endswith('.pdf'):
            extracted_text = extract_text_from_pdf(file_bytes)
        elif key_lower.endswith('.txt'):
            extracted_text = extract_text_from_txt(file_bytes)
        elif key_lower.endswith('.csv'):
            try:
                extracted_text = file_bytes.decode('utf-8', errors='ignore')
            except Exception:
                extracted_text = extract_text_from_txt(file_bytes)
            structured_df = _load_dataframe_from_bytes(file_bytes, key)
        elif key_lower.endswith(('.doc', '.docx')):
            extracted_text = f"[DOC/DOCX file: {key} - content extraction requires python-docx library]"
        elif key_lower.endswith(('.xls', '.xlsx')):
            extracted_text = extract_text_from_excel(file_bytes, key)
            structured_df = _load_dataframe_from_bytes(file_bytes, key)
        else:
            print(f"[WARNING] [S3_SINGLE] Unsupported file extension for {key}; treating as empty text.")

        if structured_df is not None:
            dataset_id = store_dataframe_for_document(bucket, key, structured_df)

        framework_key = _framework_cache_key(framework_id, framework_name)

        doc_data = {
            'bucket': bucket,
            'key': key,
            'size': size,
            'last_modified': last_modified,
            'content_type': content_type,
            'extracted_text': extracted_text if extracted_text else "",
            'dataset_id': dataset_id,
            'framework_key': framework_key
        }

        cache = load_s3_cache()
        frameworks_cache = cache.setdefault("frameworks", {})
        framework_cache = frameworks_cache.setdefault(framework_key, {})
        framework_cache[get_cache_key(bucket, key)] = doc_data
        cache["frameworks"][framework_key] = framework_cache
        save_s3_cache(cache)

        print(f"[INFO] [S3_SINGLE] Processed uploaded document {key} ({len(extracted_text)} chars).")
        return doc_data
    except Exception as exc:
        print(f"[WARNING] [S3_SINGLE] Failed to process {key}: {exc}")
        return None

