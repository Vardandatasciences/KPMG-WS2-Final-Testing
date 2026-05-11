"""
Module summary creation and chunking logic
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from .config import OUTPUT_DIR
from .evidence import estimate_tokens


def create_module_summaries(framework_data,
                            other_tables_data,
                            schema_info,
                            framework_info,
                            module_filter: Optional[List[str]] = None):
    """Create separate JSON files per module with full rows for selected tables.
    Modules and included tables are configured per user's instructions.
    """
    print(f"[INFO] [MODULE_SUMMARY] Creating per-module JSON summaries...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_framework_id = (framework_info or {}).get('FrameworkId')

    # Helper: collect rows for a table from framework_data or other_tables_data
    def table_rows(table_name: str):
        # From main framework_data keys if present
        key_map = {
            'policies': 'policies',
            'subpolicies': 'subpolicies',
            'compliance': 'compliances',
            'risk': 'risks',
            'incidents': 'incidents',
            'audit': 'audits'
        }
        if table_name in key_map and key_map[table_name] in framework_data:
            return framework_data.get(key_map[table_name], [])
        # Else from other_tables_data
        return other_tables_data.get(table_name, [])

    # Module configuration (updated per user)
    modules = {
        'policies': [
            'policies', 'policyversions', 'policycategories', 'subpolicies', 'policyapproval'
        ],
        'compliance': [
            'compliance', 'complianceapproval'
        ],
        'audit': [
            'audit', 'audit_version', 'audit_findings', 'audit_report', 'audit_reports',
            'audit_document', 'audit_documents', 'audit_document_mappings', 'audit_document_validation',
            'audit_review', 'audit_review_comments'
        ],
        'risk': [
            'risk', 'risk_instance', 'risk_approval'
        ],
        'incidents': [
            'incidents', 'incident_approval'
        ]
    }

    if module_filter:
        filter_set = {m.strip().lower() for m in module_filter if m.strip()}
        modules = {
            name: tables for name, tables in modules.items()
            if name.lower() in filter_set
        }
        print(f"[INFO] [MODULE_SUMMARY] Module filter active for summary creation: {filter_set}")

    # Build and save per-module summaries
    for module_name, tables in modules.items():
        module_data = {
            'framework': framework_info,
            'module': module_name,
            'tables': {},
            'schema': {}
        }

        for t in tables:
            # Include rows
            rows = table_rows(t)
            module_data['tables'][t] = rows
            # Include schema (columns and row_count)
            if t in schema_info:
                module_data['schema'][t] = {
                    'columns': schema_info[t].get('columns', []),
                    'row_count': schema_info[t].get('row_count', 0),
                    'column_details': schema_info[t].get('column_details', [])
                }
            else:
                module_data['schema'][t] = {
                    'columns': [],
                    'row_count': 0,
                    'column_details': []
                }

        # Include FrameworkId in filename to avoid mixing across frameworks
        if current_framework_id is not None:
            out_path = OUTPUT_DIR / f"module_summary_{current_framework_id}_{module_name}_{timestamp}.json"
        else:
            out_path = OUTPUT_DIR / f"module_summary_{module_name}_{timestamp}.json"
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(module_data, f, indent=2, default=str)
            print(f"[INFO] [MODULE_SUMMARY] Wrote {module_name} summary → {out_path}")
        except Exception as e:
            print(f"[WARNING] [MODULE_SUMMARY] Failed to write {module_name} summary: {e}")


def chunk_module_data(data_summary_json, max_tokens=110000, reserved_tokens=18000):
    """Intelligently chunk module data if it exceeds context window.
    
    Args:
        data_summary_json: JSON string or dict of module data
        max_tokens: Maximum tokens for the model (default 110K for 128K context with margin)
        reserved_tokens: Tokens reserved for prompt overhead (default 18K)
    
    Returns:
        List of chunked data (as JSON strings), or single-item list if no chunking needed
    """
    try:
        # Parse input
        if isinstance(data_summary_json, str):
            data = json.loads(data_summary_json)
        else:
            data = json.loads(json.dumps(data_summary_json, default=str))
        
        # Fix any non-list values in tables (convert int/float to empty list)
        tables_data = data.get('tables', {})
        for table_name, table_value in tables_data.items():
            if not isinstance(table_value, list):
                if isinstance(table_value, (int, float)):
                    print(f"[WARNING] [CHUNK] Table '{table_name}' has integer value {table_value} instead of list, converting to empty list")
                    tables_data[table_name] = []
                else:
                    print(f"[WARNING] [CHUNK] Table '{table_name}' has unexpected type {type(table_value)}, converting to empty list")
                    tables_data[table_name] = []
        
        # Calculate available tokens for data (subtract reserved for prompt)
        available_tokens = max_tokens - reserved_tokens
        
        # Estimate total size
        total_json = json.dumps(data, default=str)
        total_tokens = estimate_tokens(total_json)
        
        # If data fits, return as-is
        if total_tokens <= available_tokens:
            print(f"[INFO] [CHUNK] Data fits in context: {total_tokens:,} tokens (limit: {available_tokens:,})")
            return [data_summary_json if isinstance(data_summary_json, str) else json.dumps(data, default=str)]
        
        print(f"[INFO] [CHUNK] Data too large: {total_tokens:,} tokens (limit: {available_tokens:,})")
        print(f"[INFO] [CHUNK] Splitting into chunks...")
        
        # Extract base structure (framework, module, schema)
        base_data = {
            'framework': data.get('framework', {}),
            'module': data.get('module', ''),
            'schema': data.get('schema', {}),
            's3_evidence': data.get('s3_evidence', [])
        }
        base_tokens = estimate_tokens(json.dumps(base_data, default=str))
        
        # Chunk by tables - split large tables into smaller chunks
        chunks = []
        
        # Group tables by size
        tables_by_size = []
        for table_name, rows in tables_data.items():
            # Ensure rows is a list (not int or other type)
            if not isinstance(rows, list):
                print(f"[WARNING] [CHUNK] Table '{table_name}' has non-list data type: {type(rows)}, skipping")
                continue
            table_json = json.dumps({table_name: rows}, default=str)
            table_tokens = estimate_tokens(table_json)
            tables_by_size.append((table_name, rows, table_tokens))
        
        # Sort by size (largest first)
        tables_by_size.sort(key=lambda x: x[2], reverse=True)
        
        current_chunk = base_data.copy()
        current_chunk['tables'] = {}    
        current_tokens = base_tokens
        
        for table_name, rows, table_tokens in tables_by_size:
            # If single table is larger than available space, split the table
            if table_tokens > available_tokens:
                print(f"[INFO] [CHUNK] Table '{table_name}' is very large ({table_tokens:,} tokens), splitting rows...")
                
                # Calculate how many rows fit per chunk
                if rows and isinstance(rows, list) and len(rows) > 0:
                    sample_row_tokens = estimate_tokens(json.dumps(rows[0], default=str))
                    rows_per_chunk = max(1, (available_tokens - base_tokens) // sample_row_tokens)
                    rows_per_chunk = min(rows_per_chunk, len(rows))
                    num_chunks = (len(rows) + rows_per_chunk - 1) // rows_per_chunk
                else:
                    rows_per_chunk = 1
                    num_chunks = 1
                    rows = rows if isinstance(rows, list) else []
                
                for chunk_idx in range(num_chunks):
                    start_idx = chunk_idx * rows_per_chunk
                    end_idx = min(start_idx + rows_per_chunk, len(rows))
                    chunk_rows = rows[start_idx:end_idx]
                    
                    # Create new chunk for this table portion
                    table_chunk = base_data.copy()
                    table_chunk['tables'] = {table_name: chunk_rows}
                    table_chunk['_chunk_info'] = {
                        'table': table_name,
                        'chunk': f"{chunk_idx + 1}/{num_chunks}",
                        'rows': f"{start_idx + 1}-{end_idx} of {len(rows)}"
                    }
                    
                    chunks.append(json.dumps(table_chunk, indent=2, default=str))
                    print(f"[INFO] [CHUNK] Created chunk {len(chunks)}: {table_name} rows {start_idx + 1}-{end_idx}")
            
            # Try to add table to current chunk
            elif current_tokens + table_tokens <= available_tokens:
                # Fits in current chunk
                current_chunk['tables'][table_name] = rows
                current_tokens += table_tokens
            else:
                # Doesn't fit - save current chunk and start new one
                if current_chunk['tables']:
                    chunks.append(json.dumps(current_chunk, indent=2, default=str))
                    print(f"[INFO] [CHUNK] Created chunk {len(chunks)}: {len(current_chunk['tables'])} tables, {current_tokens:,} tokens")
                
                # Start new chunk with this table
                current_chunk = base_data.copy()
                current_chunk['tables'] = {table_name: rows}
                current_tokens = base_tokens + table_tokens
        
        # Add final chunk if it has data
        if current_chunk['tables']:
            chunks.append(json.dumps(current_chunk, indent=2, default=str))
            print(f"[INFO] [CHUNK] Created chunk {len(chunks)}: {len(current_chunk['tables'])} tables, {current_tokens:,} tokens")
        
        print(f"[INFO] [CHUNK] Split into {len(chunks)} chunks")
        return chunks
        
    except Exception as e:
        print(f"[WARNING] [CHUNK] Error chunking data: {e}")
        return [data_summary_json]  # Return original if chunking fails

