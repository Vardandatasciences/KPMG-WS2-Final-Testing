"""
Evidence indexing and S3 evidence attachment for KPI generation
"""
import json
import os
import re
import numpy as np
from typing import Dict, Any, List, Optional, Set

from .config import (
    OPENAI_AVAILABLE, OPENAI_CLIENT, TEXT_SPLITTER, EMBEDDING_MODEL,
    S3_CHUNK_CACHE_FILE, OUTPUT_DIR, OPENAI_API_KEY
)

if OPENAI_AVAILABLE:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from openai import OpenAI

EMBEDDING_CACHE = {}  # Cache embeddings to avoid redundant API calls


def load_s3_chunk_cache():
    """Load S3 chunk cache from file."""
    if not S3_CHUNK_CACHE_FILE.exists():
        return {}
    try:
        with open(S3_CHUNK_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] [CACHE] Error loading S3 chunk cache: {e}")
        return {}


def save_s3_chunk_cache(cache):
    """Save S3 chunk cache to file."""
    try:
        with open(S3_CHUNK_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, default=str)
    except Exception as e:
        print(f"[WARNING] [CACHE] Error saving S3 chunk cache: {e}")


def estimate_tokens(text):
    """Estimate token count (rough approximation: 1 token ≈ 4 characters)."""
    return len(text) // 4


def _ensure_openai_client():
    """Ensure OpenAI client is initialized."""
    global OPENAI_CLIENT
    if not OPENAI_AVAILABLE:
        return False
    if not OPENAI_API_KEY:
        print("[WARNING] [S3_EVIDENCE] OPENAI_API_KEY not configured. Semantic evidence scoring will be skipped.")
        return False
    if OPENAI_CLIENT is None:
        try:
            OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)
            print(f"[INFO] [S3_EVIDENCE] OpenAI client initialized for embeddings")
        except Exception as exc:
            print(f"[WARNING] [S3_EVIDENCE] Unable to initialize OpenAI client: {exc}")
            return False
    return True


def get_embedding(text: str) -> Optional[List[float]]:
    """Get OpenAI embedding for text with caching."""
    if not _ensure_openai_client():
        return None
    
    # Check cache first
    cache_key = hash(text)
    if cache_key in EMBEDDING_CACHE:
        return EMBEDDING_CACHE[cache_key]
    
    try:
        response = OPENAI_CLIENT.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text[:8000]  # Limit text length for embedding
        )
        embedding = response.data[0].embedding
        EMBEDDING_CACHE[cache_key] = embedding
        return embedding
    except Exception as exc:
        print(f"[WARNING] [EMBEDDING] Failed to get embedding: {exc}")
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    return float(np.dot(vec1_np, vec2_np) / (np.linalg.norm(vec1_np) * np.linalg.norm(vec2_np)))


def tokenize_text(text):
    """Tokenize text into lowercase keywords including alphanumeric clause IDs."""
    if not text:
        return set()
    token_pattern = re.compile(r"[A-Za-z0-9]+(?:[-_/\.][A-Za-z0-9]+)*")
    tokens = set()
    for match in token_pattern.findall(str(text)):
        token = match.strip().lower()
        if len(token) >= 2:
            tokens.add(token)
    return tokens


def attach_s3_evidence_to_summary(
    summary_json_text,
    s3_documents,
    framework_info=None,
    module_name=None,
    chunk_size=2500,
    token_budget=30000,
    max_chunks=50,
    max_chunks_per_doc=50,
):
    """Augment a module summary JSON string with curated S3 evidence chunks filtered by relevance."""
    if not s3_documents:
        return summary_json_text

    try:
        summary = json.loads(summary_json_text)
    except Exception as e:
        print(f"[WARNING] [S3_EVIDENCE] Failed to parse module summary for S3 attachment: {e}")
        return summary_json_text

    if not OPENAI_AVAILABLE:
        print("[WARNING] OpenAI SDK not available for S3 evidence scoring. Skipping.")
        return summary_json_text

    if not _ensure_openai_client():
        return summary_json_text

    keywords = set()
    for field in ['FrameworkName', 'Category', 'Identifier']:
        value = (framework_info or {}).get(field)
        if value:
            for token in str(value).replace('-', ' ').replace('/', ' ').split():
                token_clean = token.strip().lower()
                if len(token_clean) >= 3:
                    keywords.add(token_clean)
    if module_name:
        for token in str(module_name).replace('-', ' ').split():
            token_clean = token.strip().lower()
            if len(token_clean) >= 3:
                keywords.add(token_clean)

    if not keywords:
        print("[WARNING] [S3_EVIDENCE] No keywords derived from framework/module metadata; skipping S3 evidence injection.")
        return summary_json_text

    global TEXT_SPLITTER
    if TEXT_SPLITTER is None:
        TEXT_SPLITTER = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=max(0, chunk_size // 5),
            separators=["\n\n", "\n", ". ", ".", "? ", "! ", " "]
        )
    text_splitter = TEXT_SPLITTER

    chunk_cache = load_s3_chunk_cache()
    cache_updated = False

    def compute_chunk_score(chunk_text: str) -> float:
        """Score chunk based on keyword overlap (simple token matching)."""
        if not chunk_text or not chunk_text.strip():
            return 0.0
        
        # Simple keyword matching score
        chunk_tokens = tokenize_text(chunk_text)
        overlap = chunk_tokens & keywords
        return float(len(overlap))

    ordered_docs = []
    total_docs = len(s3_documents)
    for doc_idx, doc in enumerate(s3_documents, start=1):
        extracted_text = doc.get('extracted_text') or ''
        print(f"[INFO] [S3_EVIDENCE] [{doc_idx}/{total_docs}] Evaluating {doc.get('key')}")
        if not extracted_text.strip():
            print(f"[INFO] [S3_EVIDENCE]   - Skipping (empty content)")
            continue
        chunks_preview = text_splitter.split_text(extracted_text.strip())
        if chunks_preview:
            print(f"[INFO] [S3_EVIDENCE]   - Candidate chunks: {len(chunks_preview)}")
            ordered_docs.append(doc)
        else:
            print(f"[INFO] [S3_EVIDENCE]   - Skipping (no chunkable text)")
    if not ordered_docs:
        print("[WARNING] [S3_EVIDENCE] No S3 documents produced valid chunks for this module.")
        return summary_json_text

    primary_chunks = []
    extra_chunks = []

    for doc_idx, doc in enumerate(ordered_docs, start=1):
        extracted = doc.get('extracted_text') or ''
        if not extracted.strip():
            primary_chunks.append({
                'bucket': doc.get('bucket'),
                'key': doc.get('key'),
                'content_type': doc.get('content_type'),
                'size': doc.get('size'),
                'chunk': 0,
                'chunks': 0,
                'excerpt': "[No text extracted – upload uses binary or unsupported format]",
                'embedding': None,
                'semantic_score': None,
                'score': 0.0
            })
            continue

        cache_key = f"{doc.get('bucket')}::{doc.get('key')}::{doc.get('last_modified')}"
        cached_entry = chunk_cache.get(cache_key)

        if cached_entry and cached_entry.get('chunk_size') == chunk_size and cached_entry.get('version') == 'v1':
            raw_chunks = cached_entry.get('chunks', [])
            if len(raw_chunks) > max_chunks_per_doc:
                raw_chunks = raw_chunks[:max_chunks_per_doc]
                print(f"[INFO] [S3_EVIDENCE]   - Using top {max_chunks_per_doc} cached chunks for {doc.get('key')}")
            chunk_entries = []
            print(f"[INFO] [S3_EVIDENCE]   - Re-scoring cached chunks ({len(raw_chunks)}) for {doc.get('key')}")
            for raw in raw_chunks:
                chunk_text = raw.get('excerpt', '')
                score = compute_chunk_score(chunk_text)
                chunk_entries.append({
                    'bucket': doc.get('bucket'),
                    'key': doc.get('key'),
                    'content_type': doc.get('content_type'),
                    'size': doc.get('size'),
                    'chunk': raw.get('chunk'),
                    'chunks': raw.get('chunks'),
                    'excerpt': chunk_text,
                    'score': score,
                    'embedding': None,
                    'semantic_score': None
                })
        else:
            cleaned_text = extracted.strip()
            chunks = text_splitter.split_text(cleaned_text)
            if not chunks:
                continue
            total_chunks = len(chunks)
            if total_chunks > max_chunks_per_doc:
                print(f"[INFO] [S3_EVIDENCE]   - Truncating chunks from {total_chunks} to {max_chunks_per_doc} for {doc.get('key')}")
                chunks = chunks[:max_chunks_per_doc]
                total_chunks = len(chunks)

            chunk_entries = []
            cache_chunks = []
            print(f"[INFO] [S3_EVIDENCE]   - Scoring {total_chunks} chunks for {doc.get('key')} ({doc_idx}/{total_docs})")
            for idx, chunk in enumerate(chunks, start=1):
                score = compute_chunk_score(chunk)
                print(f"[DEBUG] [S3_EVIDENCE]     Chunk {idx}/{len(chunks)} score={score:.4f}")
                chunk_entries.append({
                    'bucket': doc.get('bucket'),
                    'key': doc.get('key'),
                    'content_type': doc.get('content_type'),
                    'size': doc.get('size'),
                    'chunk': idx,
                    'chunks': len(chunks),
                    'excerpt': chunk,
                    'score': score,
                    'embedding': None,
                    'semantic_score': None
                })
                cache_chunks.append({
                    'chunk': idx,
                    'chunks': len(chunks),
                    'excerpt': chunk
                })

            chunk_cache[cache_key] = {
                'version': 'v1',
                'chunk_size': chunk_size,
                'chunks': cache_chunks
            }
            cache_updated = True

        if not chunk_entries:
            continue

        chunk_entries.sort(key=lambda x: x['score'], reverse=True)
        primary_chunk = chunk_entries[0]
        print(f"[INFO] [S3_EVIDENCE]   - Selected chunk {primary_chunk['chunk']} with score {primary_chunk['score']:.4f}")
        primary_chunks.append(primary_chunk)

        for entry in chunk_entries[1:]:
            extra_chunks.append(entry)

    curated_docs = []
    tokens_used = 0

    for entry in primary_chunks:
        entry_clean = {k: v for k, v in entry.items() if k not in ('score', 'embedding')}
        entry_tokens = estimate_tokens(entry_clean.get('excerpt', ''))
        if token_budget and tokens_used + entry_tokens > token_budget:
            print(f"[INFO] [S3_EVIDENCE]   - Token budget reached; skipping additional evidence")
            continue
        curated_docs.append(entry_clean)
        tokens_used += entry_tokens
        if len(curated_docs) >= max_chunks:
            break

    if len(curated_docs) < max_chunks:
        for entry in extra_chunks:
            if token_budget and tokens_used >= token_budget:
                break
            entry_clean = {k: v for k, v in entry.items() if k not in ('score', 'embedding')}
            entry_tokens = estimate_tokens(entry_clean.get('excerpt', ''))
            if token_budget and tokens_used + entry_tokens > token_budget:
                continue
            curated_docs.append(entry_clean)
            tokens_used += entry_tokens
            if len(curated_docs) >= max_chunks:
                break

    if cache_updated:
        save_s3_chunk_cache(chunk_cache)

    print(f"[INFO] [S3_EVIDENCE] Final curated chunks: {len(curated_docs)} (tokens used ~{tokens_used})")

    summary['s3_evidence'] = curated_docs

    try:
        return json.dumps(summary, indent=2, default=str)
    except TypeError:
        # if serialization fails due to non-serializable objects fall back
        print("[WARNING] [S3_EVIDENCE] Failed to serialize augmented summary; returning original text.")
        return summary_json_text


def build_evidence_index(summary_data, schema_info):
    """Construct searchable evidence index for module tables and S3 excerpts."""
    tables_index = {}
    module_tables = summary_data.get('tables', {}) or {}
    module_schema = summary_data.get('schema', {}) or {}

    for table_name, rows in module_tables.items():
        table_tokens = tokenize_text(table_name)
        column_tokens = {}
        column_details = schema_info.get(table_name, {}).get('column_details', [])
        column_types = {col['name']: col.get('type', '').lower() for col in column_details} if column_details else {}

        schema_columns = module_schema.get(table_name, {}).get('columns')
        if not schema_columns:
            schema_columns = schema_info.get(table_name, {}).get('columns', [])

        for column in schema_columns or []:
            column_tokens[column] = tokenize_text(column)
            table_tokens.update(column_tokens[column])

        # Sample up to 50 rows to collect keywords from values
        for row in rows[:50]:
            if not isinstance(row, dict):
                continue
            for column, value in row.items():
                if value is None:
                    continue
                value_tokens = tokenize_text(value)
                if not value_tokens:
                    continue
                column_tokens.setdefault(column, set()).update(value_tokens)
                table_tokens.update(value_tokens)

        tables_index[table_name] = {
            'columns': schema_columns or [],
            'column_tokens': column_tokens,
            'table_tokens': table_tokens,
            'column_types': column_types
        }

    s3_index = []
    for doc in summary_data.get('s3_evidence', []) or []:
        excerpt = doc.get('excerpt', '')
        key = doc.get('key', '')
        tokens = tokenize_text(excerpt)
        tokens.update(tokenize_text(key))
        s3_entry = dict(doc)
        s3_entry['tokens'] = tokens
        s3_entry['embedding'] = None
        s3_index.append(s3_entry)

    return {'tables': tables_index, 's3': s3_index}


def select_matching_tables(keywords, evidence_index):
    """Select tables matching keywords from evidence index."""
    matches = []
    for table_name, info in evidence_index.get('tables', {}).items():
        score = len(keywords & info['table_tokens'])
        matched_columns = []
        for column, tokens in info['column_tokens'].items():
            overlap = keywords & tokens
            if overlap:
                score += len(overlap) * 2
                matched_columns.append(column)
        if score > 0:
            matches.append({
                'table': table_name,
                'score': score,
                'matched_columns': matched_columns,
                'info': info
            })
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches


def select_matching_s3_semantic(query_text, evidence_index):
    """Select S3 documents matching query using OpenAI embeddings."""
    if not query_text.strip():
        return []
    if not OPENAI_AVAILABLE:
        print("[WARNING] [S3_EVIDENCE] Semantic matching skipped (OpenAI SDK not available).")
        return []
    if not _ensure_openai_client():
        return []

    query_emb = get_embedding(query_text)
    if query_emb is None:
        return []
    
    matches = []
    for doc in evidence_index.get('s3', []):
        excerpt = doc.get('excerpt', '')
        if not excerpt or not excerpt.strip():
            continue
        if doc.get('embedding') is None:
            doc['embedding'] = get_embedding(excerpt)
        if doc['embedding'] is None:
            continue
        
        score = cosine_similarity(query_emb, doc['embedding'])
        if score > 0:
            doc_entry = dict(doc)
            doc_entry['semantic_score'] = score
            matches.append(doc_entry)
    matches.sort(key=lambda x: x['semantic_score'], reverse=True)
    return matches


def load_latest_module_summary(framework_id: int, module: str) -> Optional[Dict[str, Any]]:
    """Load the latest module summary JSON for the framework/module."""
    pattern = f"module_summary_{framework_id}_{module.lower()}_*.json"
    candidates = list(OUTPUT_DIR.glob(pattern))
    if not candidates:
        print(f"[WARNING] [MODULE_LOAD] No module summaries found for {module} (framework {framework_id})")
        return None

    latest_path = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        with open(latest_path, 'r', encoding='utf-8') as f:
            module_summary = json.load(f)
        print(f"[INFO] [MODULE_LOAD] Loaded module summary {latest_path.name}")
        return module_summary
    except Exception as exc:
        print(f"[ERROR] [MODULE_LOAD] Failed to read {latest_path}: {exc}")
        return None

