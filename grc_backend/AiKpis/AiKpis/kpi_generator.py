"""
Main KPI generation pipeline
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from .config import (
        OUTPUT_DIR,
        FRAMEWORK_ID,
        OPENAI_MODEL,
        OPENAI_AVAILABLE,
        OPENAI_API_KEY,
        MAX_RETRIES,
    )
    from .database import (
        connect_to_database,
        get_framework_info,
        get_database_schema,
        get_framework_data,
        get_other_tables_data,
        ensure_kpis_module_column,
        write_kpis_to_database,
        save_schema_metadata,
    )
    from .s3_handler import get_s3_documents, fetch_single_s3_document
    from .module_summaries import create_module_summaries, chunk_module_data
    from .evidence import (
        attach_s3_evidence_to_summary,
        build_evidence_index,
        load_latest_module_summary,
    )
    from .ollama_client import generate_kpis_with_ollama as generate_kpis_with_openai
    from .kpi_validation import (
        align_kpis_with_evidence,
        validate_and_sanitize_formulas,
        deduplicate_kpis,
        _ensure_from_where_to_access_data,
        enforce_schema_sources,
    )
    from .synthetic_data import ensure_synthetic_sources_for_schema_plan_kpis
    from .formula_evaluator import populate_kpi_values_from_memory
except ImportError:
    from AiKpis.config import (
        OUTPUT_DIR,
        FRAMEWORK_ID,
        OPENAI_MODEL,
        OPENAI_AVAILABLE,
        OPENAI_API_KEY,
        MAX_RETRIES,
    )
    from AiKpis.database import (
        connect_to_database,
        get_framework_info,
        get_database_schema,
        get_framework_data,
        get_other_tables_data,
        ensure_kpis_module_column,
        write_kpis_to_database,
        save_schema_metadata,
    )
    from AiKpis.s3_handler import get_s3_documents, fetch_single_s3_document
    from AiKpis.module_summaries import create_module_summaries, chunk_module_data
    from AiKpis.evidence import (
        attach_s3_evidence_to_summary,
        build_evidence_index,
        load_latest_module_summary,
    )
    from AiKpis.ollama_client import generate_kpis_with_ollama as generate_kpis_with_openai
    from AiKpis.kpi_validation import (
        align_kpis_with_evidence,
        validate_and_sanitize_formulas,
        deduplicate_kpis,
        _ensure_from_where_to_access_data,
        enforce_schema_sources,
    )
    from AiKpis.synthetic_data import ensure_synthetic_sources_for_schema_plan_kpis
    from AiKpis.formula_evaluator import populate_kpi_values_from_memory


def generate_kpis_from_module_summaries(schema_info,
                                        s3_documents,
                                        framework_info,
                                        module_filter: Optional[List[str]] = None):
    """Load per-module JSON summaries and generate KPIs per module using focused prompts."""
    print(f"\n[INFO] [MODULE_SUMMARY] Generating KPIs from per-module summaries...")
    all_kpis = []

    try:
        current_framework_id = (framework_info or {}).get('FrameworkId')
        # Find module summary files in OUTPUT_DIR
        all_module_files = []
        for p in OUTPUT_DIR.iterdir():
            if not (p.is_file() and p.suffix == ".json"):
                continue
            # Only accept files with current FrameworkId: module_summary_{id}_{module}_{timestamp}.json
            if current_framework_id is not None:
                if p.name.startswith(f"module_summary_{current_framework_id}_"):
                    all_module_files.append(p)
            else:
                # If no framework_id specified, accept any module_summary files
                if p.name.startswith("module_summary_"):
                    all_module_files.append(p)
        
        # Group files by module name and keep only the LATEST one for each module
        # This prevents processing duplicate files from previous runs
        module_files_by_module = {}
        for p in all_module_files:
            # Extract module name from filename: module_summary_{framework_id}_{module_name}_{timestamp}.json
            name = p.stem  # Remove .json extension
            if current_framework_id is not None:
                # Format: module_summary_{id}_{module}_{timestamp}
                prefix = f"module_summary_{current_framework_id}_"
                if name.startswith(prefix):
                    rest = name[len(prefix):]
                    # Split by underscore, module name is the first part before timestamp
                    parts = rest.split('_')
                    if len(parts) >= 3:  # module_name + timestamp parts
                        module_name = parts[0]
                    else:
                        module_name = rest
            else:
                # Legacy format: module_summary_{module}_{timestamp}
                rest = name.replace("module_summary_", "")
                parts = rest.split('_')
                module_name = parts[0] if parts else rest
            
            # Keep only the latest file for each module (by modification time)
            if module_name not in module_files_by_module:
                module_files_by_module[module_name] = p
            else:
                # Compare modification times and keep the newer one
                if p.stat().st_mtime > module_files_by_module[module_name].stat().st_mtime:
                    module_files_by_module[module_name] = p
        
        module_files = sorted(module_files_by_module.values(), key=lambda p: p.name)
        print(f"[INFO] [MODULE_SUMMARY] Found {len(module_files)} unique module summaries (filtered from {len(all_module_files)} total files)")
        if len(all_module_files) > len(module_files):
            print(f"[INFO] [MODULE_SUMMARY] Removed {len(all_module_files) - len(module_files)} duplicate/old module summary files")

        module_entries = []
        for path in module_files:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    summary_text = f.read()
                try:
                    base_summary = json.loads(summary_text)
                except Exception as e:
                    print(f"[ERROR] Failed to parse JSON file {path.name}: {e}")
                    continue
                module_entries.append((path, summary_text, base_summary))
            except Exception as e:
                print(f"[WARNING] [MODULE_SUMMARY] Failed reading {path.name}: {e}")
                continue

        if module_filter:
            filter_set = {m.strip().lower() for m in module_filter if m.strip()}
            before = len(module_entries)
            module_entries = [
                (path, text, summary)
                for (path, text, summary) in module_entries
                if (summary.get('module') or '').strip().lower() in filter_set
            ]
            print(f"[INFO] [MODULE_SUMMARY] Module filter active: {filter_set}. Keeping {len(module_entries)} of {before} summaries.")

        existing_names = []
        total_selected = len(module_entries)
        for idx, (path, summary_text, base_summary) in enumerate(module_entries, 1):
            try:
                mod_name = base_summary.get('module', '')
                summary_text = attach_s3_evidence_to_summary(
                    summary_text,
                    s3_documents,
                    framework_info=framework_info,
                    module_name=mod_name
                )

                # Get module name from JSON content (required field)
                try:
                    summary_data = json.loads(summary_text)
                    s3_chunks = len(summary_data.get('s3_evidence', []))
                    if s3_chunks:
                        print(f"[INFO] [S3_EVIDENCE] Attached {s3_chunks} S3 chunks to {path.name}")
                    else:
                        print(f"[INFO] [S3_EVIDENCE] No S3 chunks attached for {path.name}")
                    mod_name = mod_name or summary_data.get('module', '')
                    if not mod_name:
                        print(f"[ERROR] Module name missing in JSON file: {path.name}")
                        continue
                except Exception as e:
                    print(f"[ERROR] Failed to parse JSON file {path.name}: {e}")
                    continue

                evidence_index = build_evidence_index(summary_data, schema_info)
                module_evidence = summary_data.get('s3_evidence', [])
                
                category_name = f"{mod_name.capitalize()} Module KPIs"
                print(f"[INFO] [MODULE_SUMMARY] [{idx}/{total_selected}] Generating for {category_name} from {path.name}")

                # Check data size and chunk if needed
                # llama3.1:8b has 128K context, reserve ~18K for prompt, use ~110K for data
                data_chunks = chunk_module_data(summary_text, max_tokens=110000, reserved_tokens=18000)
                
                if len(data_chunks) > 1:
                    print(f"[INFO] [CHUNK] Processing {len(data_chunks)} chunks for {category_name}...")
                
                module_kpis = []
                for chunk_idx, chunk_data in enumerate(data_chunks, 1):
                    chunk_context = f"{category_name}" + (f" (chunk {chunk_idx}/{len(data_chunks)})" if len(data_chunks) > 1 else "")
                    
                    if len(data_chunks) > 1:
                        print(f"[INFO] [CHUNK] Processing chunk {chunk_idx}/{len(data_chunks)} for {category_name}...")

                    kpis = []
                    from .config import MAX_RETRIES
                    import time
                    for attempt in range(1, MAX_RETRIES + 1):
                        print(f"[INFO] [RETRY] Attempt {attempt}/{MAX_RETRIES} for {chunk_context}")
                        kpis = generate_kpis_with_openai(
                            chunk_data,
                            chunk_context,
                            schema_info=schema_info,
                            existing_kpi_names=existing_names,
                            framework_id=framework_info.get('FrameworkId') if framework_info else None,
                            framework_info=framework_info,
                            s3_evidence=module_evidence
                        )
                        if kpis:
                            break
                        if attempt < MAX_RETRIES:
                            print(f"[WARNING] [RETRY] No KPIs generated, retrying in 2 seconds...")
                            time.sleep(2)
                        else:
                            print(f"[ERROR] [RETRY] Failed after {MAX_RETRIES} attempts for {chunk_context}")
                    
                    if kpis:
                        module_kpis.extend(kpis)
                        existing_names.extend([k.get('Name', '') for k in kpis if k.get('Name')])
                        if len(data_chunks) > 1:
                            print(f"[INFO] [CHUNK] Got {len(kpis)} KPIs from chunk {chunk_idx}/{len(data_chunks)}")
                
                if module_kpis:
                    module_kpis = align_kpis_with_evidence(
                        module_kpis,
                        evidence_index,
                        schema_info,
                        framework_info.get('FrameworkId') if framework_info else None
                    )
                    module_kpis = validate_and_sanitize_formulas(
                        module_kpis,
                        schema_info,
                        framework_info.get('FrameworkId') if framework_info else None
                    )
                    # Remove duplicates within module (same KPI from different chunks)
                    seen_names = set()
                    unique_kpis = []
                    for kpi in module_kpis:
                        kpi_name = kpi.get('Name', '').strip().lower()
                        if kpi_name and kpi_name not in seen_names:
                            seen_names.add(kpi_name)
                            unique_kpis.append(kpi)
                    
                    if len(module_kpis) > len(unique_kpis):
                        print(f"[INFO] [CHUNK] Removed {len(module_kpis) - len(unique_kpis)} duplicate KPIs from chunks")

                    for kpi in unique_kpis:
                        if not kpi.get('Module'):
                            kpi['Module'] = mod_name or ''
                    
                    all_kpis.extend(unique_kpis)
                    print(f"[INFO] [MODULE_SUMMARY] Added {len(unique_kpis)} unique KPIs from {category_name}")
                else:
                    print(f"[WARNING] [MODULE_SUMMARY] No KPIs generated for {category_name}")
            except Exception as e:
                print(f"[WARNING] [MODULE_SUMMARY] Failed processing {path.name}: {e}")
                continue
    except Exception as e:
        print(f"[WARNING] [MODULE_SUMMARY] Error scanning module summaries: {e}")

    return all_kpis


def refresh_single_kpi_with_s3(bucket: str,
                               key: str,
                               kpi_name: str,
                               module: str,
                               framework_id: Optional[int] = None) -> Dict[str, Any]:
    """Refresh a single KPI after an S3 upload."""
    result = {
        'success': False,
        'message': '',
        'excel_path': None,
        'updated_kpi': None
    }

    framework_id = framework_id if framework_id is not None else FRAMEWORK_ID
    if not kpi_name:
        result['message'] = "KPI name is required for targeted refresh."
        return result

    doc = fetch_single_s3_document(
        bucket,
        key,
        framework_id=framework_id,
        framework_name=None
    )
    if not doc:
        result['message'] = "Unable to process uploaded document."
        return result

    module_summary = load_latest_module_summary(framework_id, module)
    if not module_summary:
        result['message'] = "Module summary not found; run full generator first."
        return result

    connection = connect_to_database()
    if not connection:
        result['message'] = "Failed to connect to database."
        return result
    framework_info = None
    schema_info = None

    try:
        ensure_kpis_module_column(connection)

        framework_info = get_framework_info(connection, framework_id)
        if not framework_info:
            result['message'] = f"Framework {framework_id} not found."
            return result

        schema_info = get_database_schema(connection, framework_id)
        from .config import CURRENT_SCHEMA_INFO
        CURRENT_SCHEMA_INFO.clear()
        CURRENT_SCHEMA_INFO.update({k: v for k, v in schema_info.items()})

        summary_with_evidence = attach_s3_evidence_to_summary(
            json.dumps(module_summary, default=str),
            [doc],
            framework_info=framework_info,
            module_name=module
        )
        try:
            summary_data = json.loads(summary_with_evidence)
        except Exception as exc:
            result['message'] = f"Failed to parse augmented module summary: {exc}"
            return result

        evidence_index = build_evidence_index(summary_data, schema_info)

        existing_kpi_row = None
        kpi_module = module
        cursor_lookup = None
        try:
            from mysql.connector import Error
            cursor_lookup = connection.cursor(dictionary=True)
            cursor_lookup.execute(
                """
                SELECT Module, Description, Formula, DisplayType, FromWhereToAccessData
                FROM kpis
                WHERE FrameworkId=%s AND LOWER(Name)=LOWER(%s)
                LIMIT 1
                """,
                (framework_id, kpi_name)
            )
            existing_kpi_row = cursor_lookup.fetchone()
        except Error as exc:
            print(f"[WARNING] [KPI_LOOKUP] Failed to fetch existing KPI '{kpi_name}': {exc}")
        finally:
            if cursor_lookup:
                try:
                    cursor_lookup.close()
                except Exception:
                    pass

        if existing_kpi_row and existing_kpi_row.get('Module'):
            kpi_module = existing_kpi_row.get('Module')

        kpi_payload = {
            'Name': kpi_name,
            'Module': kpi_module,
            'Description': (existing_kpi_row or {}).get('Description', ''),
            'Formula': (existing_kpi_row or {}).get('Formula', ''),
            'DisplayType': (existing_kpi_row or {}).get('DisplayType', 'Metric Card'),
            'FromWhereToAccessData': (existing_kpi_row or {}).get('FromWhereToAccessData', '')
        }

        aligned = align_kpis_with_evidence(
            [dict(kpi_payload)],
            evidence_index,
            schema_info,
            framework_id
        )

        enforced = enforce_schema_sources(aligned, schema_info, framework_id)
        processed = enforced or [kpi_payload]
        processed = validate_and_sanitize_formulas(processed, schema_info, framework_id)
        _ensure_from_where_to_access_data(processed)
        processed = ensure_synthetic_sources_for_schema_plan_kpis(
            processed,
            framework_info
        )
        populate_kpi_values_from_memory(processed)
        upserted = write_kpis_to_database(connection, schema_info, framework_info, processed)
        updated_kpi = processed[0]

        result.update({
            'success': True,
            'message': 'KPI refreshed with new S3 evidence and stored in database.',
            'excel_path': None,
            'updated_kpi': updated_kpi,
            'upserted': upserted
        })
        return result
    finally:
        if connection and connection.is_connected():
            connection.close()


def generate_kpis_for_framework(framework_id=None,
                                module_filter: Optional[List[str]] = None,
                                max_s3_documents: Optional[int] = None):
    """Run the KPI generation pipeline for the specified framework.

    Args:
        framework_id: Optional override. Defaults to FRAMEWORK_ID constant.

    Returns:
        dict: {
            "kpis": List of KPI dicts,
            "excel_path": Path to generated Excel file,
            "framework_info": Framework metadata dict
        }

    Raises:
        RuntimeError: If any critical step fails.
    """
    framework_id = framework_id if framework_id is not None else FRAMEWORK_ID

    print("\n" + "=" * 70)
    print("KPI GENERATOR")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Framework ID: {framework_id}")
    if module_filter:
        print(f"Module filter: {module_filter}")
    if max_s3_documents is not None:
        print(f"Max S3 documents: {max_s3_documents}")
    print("=" * 70)

    print("\n[1/10] Connecting to database...")
    connection = connect_to_database()
    if not connection:
        raise RuntimeError("Failed to connect to database.")

    try:
        ensure_kpis_module_column(connection)

        print("\n[2/10] Getting framework information...")
        framework_info = get_framework_info(connection, framework_id)
        if not framework_info:
            raise RuntimeError("Framework not found.")

        print("\n[3/10] Retrieving S3 documents...")
        s3_documents = get_s3_documents(
            max_documents=max_s3_documents,
            framework_id=framework_id,
            framework_name=framework_info.get('FrameworkName') if framework_info else None
        )

        print("\n[4/10] Retrieving framework data...")
        framework_data = get_framework_data(connection, framework_id)

        print("\n[5/10] Retrieving database schema...")
        schema_info = get_database_schema(connection, framework_id)
        from .config import CURRENT_SCHEMA_INFO
        CURRENT_SCHEMA_INFO.clear()
        CURRENT_SCHEMA_INFO.update({k: v for k, v in schema_info.items()})
        save_schema_metadata(schema_info, framework_id, OUTPUT_DIR)

        print("\n[6/10] Retrieving data from other database tables...")
        other_tables_data = get_other_tables_data(connection, framework_id, schema_info)

        print("\n[7/10] Creating module summaries for OpenAI...")
        create_module_summaries(
            framework_data,
            other_tables_data,
            schema_info,
            framework_info,
            module_filter=module_filter
        )

        print("\n[8/10] Verifying OpenAI configuration...")
        if not OPENAI_AVAILABLE:
            print("[ERROR] OpenAI SDK not available. Install with: pip install openai")
            raise RuntimeError("OpenAI SDK not installed")
        
        if not OPENAI_API_KEY:
            print("[ERROR] OPENAI_API_KEY not configured")
            raise RuntimeError("OPENAI_API_KEY not configured")
        
        print(f"[INFO] OpenAI configuration verified")

        print("\n[9/10] Generating KPIs with OpenAI...")
        print(f"[INFO] Using OpenAI model: {OPENAI_MODEL}")
        kpis = generate_kpis_from_module_summaries(
            schema_info,
            s3_documents,
            framework_info,
            module_filter=module_filter
        )

        if not kpis:
            raise RuntimeError("No KPIs generated.")

        print("\n[POST] Removing duplicate KPIs...")
        kpis = deduplicate_kpis(kpis)

        if not kpis:
            raise RuntimeError("No KPIs remaining after deduplication.")

        kpis = validate_and_sanitize_formulas(kpis, schema_info, framework_info.get('FrameworkId'))
        _ensure_from_where_to_access_data(kpis)

        print("\n[POST] Ensuring live data sources for all KPIs...")
        kpis = ensure_synthetic_sources_for_schema_plan_kpis(
            kpis,
            framework_info
        )

        print("\n[POST] Calculating KPI values from database...")
        populate_kpi_values_from_memory(kpis)

        print("\n[POST] Writing KPIs to database...")
        upserted = write_kpis_to_database(connection, schema_info, framework_info, kpis)

        print("\n" + "=" * 70)
        print("KPI GENERATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Total KPIs generated: {len(kpis)}")
        print(f"Upserted rows: {upserted}")
        print("=" * 70)

        return {
            "kpis": kpis,
            "excel_path": None,
            "upserted": upserted,
            "framework_info": framework_info
        }
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\n[INFO] Database connection closed")


def refresh_kpis_after_upload(bucket,
                              key,
                              framework_id=None,
                              kpi_name: Optional[str] = None,
                              module: Optional[str] = None):
    """Refresh KPIs after a new S3 document upload.

    Args:
        bucket (str): S3 bucket where the document was uploaded.
        key (str): S3 object key.
        framework_id (int, optional): Framework to regenerate. Defaults to FRAMEWORK_ID.
        kpi_name (str, optional): KPI name to refresh (for targeted updates).
        module (str, optional): Module name associated with the KPI.

    Returns:
        dict: Result details.
    """
    print(f"\n[UPLOAD] Detected new S3 object: s3://{bucket}/{key}")

    if kpi_name and module:
        print(f"[UPLOAD] Attempting targeted refresh for KPI '{kpi_name}' (module {module})...")
        targeted_result = refresh_single_kpi_with_s3(bucket, key, kpi_name, module, framework_id)
        if targeted_result.get('success'):
            print("[UPLOAD] Targeted KPI refresh completed.")
            return targeted_result
        else:
            print(f"[UPLOAD] Targeted refresh failed: {targeted_result.get('message')}. Falling back to full regeneration.")

    print("[UPLOAD] Refreshing full KPI set so the new evidence can be evaluated...")
    result = generate_kpis_for_framework(framework_id)
    print("[UPLOAD] KPI refresh completed.")
    return result

