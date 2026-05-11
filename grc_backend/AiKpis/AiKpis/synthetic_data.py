"""
Synthetic dataset generation for KPIs
"""
import io
import re
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from .config import (
    OPENAI_AVAILABLE,
    OPENAI_CLIENT,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    TEMPERATURE,
    FPDF_AVAILABLE,
    FPDF,
    TARGET_S3_BUCKET,
    EVIDENCE_DATAFRAMES,
)
from .s3_handler import (
    get_cache_key,
    load_s3_cache,
    save_s3_cache,
    store_dataframe_for_document,
)
from .ollama_client import extract_json_from_text
from .kpi_validation import _extract_expression_columns
try:
    from grc.routes.Global.s3_fucntions_kpi import upload_bytes_via_microservice  # type: ignore[import-not-found]
except ImportError:
    try:
        from grc.routes.Global.s3_fucntions import upload_bytes_via_microservice  # type: ignore
    except ImportError:
        def upload_bytes_via_microservice(*args, **kwargs):  # type: ignore
            return {
                "success": False,
                "error": "upload_bytes_via_microservice unavailable in this environment"
            }

if OPENAI_AVAILABLE:
    from openai import OpenAI


def _sanitize_filename_component(value: Optional[str], fallback: str) -> str:
    """Sanitize filename component."""
    if not value:
        value = fallback
    value = re.sub(r"[^A-Za-z0-9]+", "_", str(value))
    value = value.strip("_")
    if not value:
        value = fallback
    return value.lower()


def _collect_from_where_dataframes(from_where: Optional[Any]) -> List[Tuple[str, pd.DataFrame]]:
    """Return any cached dataframes referenced in FromWhereToAccessData."""
    sources: List[Tuple[str, pd.DataFrame]] = []
    if not from_where:
        return sources

    def add_dataframe(label: str, dataframe: Optional[pd.DataFrame]) -> None:
        if dataframe is not None and not dataframe.empty:
            sources.append((label, dataframe))

    if isinstance(from_where, str):
        matches = re.findall(r"s3://([^/\s]+)/([^\s;]+)", from_where)
        for bucket, key in matches:
            dataset_id = f"{bucket}/{key}"
            add_dataframe(f"s3://{bucket}/{key}", EVIDENCE_DATAFRAMES.get(dataset_id))
    elif isinstance(from_where, dict):
        sources_list = from_where.get('sources') if isinstance(from_where, dict) else None
        if isinstance(sources_list, list):
            for entry in sources_list:
                if isinstance(entry, dict):
                    bucket = entry.get('bucket')
                    key = entry.get('key')
                    if bucket and key:
                        dataset_id = f"{bucket}/{key}"
                        add_dataframe(f"s3://{bucket}/{key}", EVIDENCE_DATAFRAMES.get(dataset_id))
                elif isinstance(entry, str):
                    match = re.match(r"s3://([^/\s]+)/([^\s;]+)", entry)
                    if match:
                        bucket, key = match.groups()
                        dataset_id = f"{bucket}/{key}"
                        add_dataframe(f"s3://{bucket}/{key}", EVIDENCE_DATAFRAMES.get(dataset_id))

    return sources


def render_synthetic_pdf(kpi_name: str,
                         framework_info: Dict[str, Any],
                         dataframe: pd.DataFrame,
                         from_where: Optional[Any],
                         existing_dataframes: Optional[List[Tuple[str, pd.DataFrame]]] = None) -> Optional[bytes]:
    """Create a PDF that combines existing evidence data and synthetic dataset."""
    global FPDF_AVAILABLE, FPDF
    if not FPDF_AVAILABLE or FPDF is None:
        return None

    existing_dataframes = existing_dataframes or []

    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 10, f"Synthetic Evidence for KPI: {kpi_name}")

        framework_title = framework_info.get('FrameworkName') or ""
        if framework_title:
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 8, f"Framework: {framework_title}")

        if existing_dataframes:
            pdf.ln(4)
            pdf.set_font("Arial", "B", 12)
            pdf.multi_cell(0, 8, "Existing Data References")
            for label, df_existing in existing_dataframes:
                pdf.set_font("Arial", "B", 11)
                pdf.multi_cell(0, 7, f"Source: {label}")
                pdf.set_font("Arial", "", 9)
                columns_existing = list(df_existing.columns)
                header_line = " | ".join(columns_existing)
                pdf.multi_cell(0, 6, header_line)
                pdf.multi_cell(0, 6, "-" * min(len(header_line), 200))
                for idx in range(len(df_existing)):
                    row = df_existing.iloc[idx]
                    row_values = [str(row.get(col, "")) for col in columns_existing]
                    row_text = " | ".join(row_values)
                    pdf.multi_cell(0, 6, row_text)
                    if pdf.get_y() > 260 and idx < len(df_existing) - 1:
                        pdf.add_page()
                        pdf.set_font("Arial", "B", 11)
                        pdf.multi_cell(0, 8, f"Source (cont.): {label}")
                        pdf.set_font("Arial", "", 9)
                        pdf.multi_cell(0, 6, header_line)
                        pdf.multi_cell(0, 6, "-" * min(len(header_line), 200))

        pdf.ln(4)
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(0, 8, "Synthetic Dataset (Full)")
        pdf.set_font("Arial", "", 9)

        columns = list(dataframe.columns)
        header_line = " | ".join(columns)
        pdf.multi_cell(0, 6, header_line)
        pdf.multi_cell(0, 6, "-" * min(len(header_line), 200))

        for idx in range(len(dataframe)):
            row = dataframe.iloc[idx]
            row_values = [str(row.get(col, "")) for col in columns]
            row_text = " | ".join(row_values)
            pdf.multi_cell(0, 6, row_text)
            if pdf.get_y() > 260 and idx < len(dataframe) - 1:
                pdf.add_page()
                pdf.set_font("Arial", "B", 12)
                pdf.multi_cell(0, 8, "Synthetic Dataset (cont.)")
                pdf.set_font("Arial", "", 9)
                pdf.multi_cell(0, 6, header_line)
                pdf.multi_cell(0, 6, "-" * min(len(header_line), 200))

        return pdf.output(dest='S').encode('latin-1')
    except Exception as exc:
        print(f"[WARNING] [PDF] Failed to build synthetic PDF for KPI '{kpi_name}': {exc}")
        return None


def generate_llm_synthetic_dataframe(kpi: Dict[str, Any],
                                     framework_info: Dict[str, Any],
                                     required_columns: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
    """Ask the LLM to craft a synthetic dataset for the KPI."""
    if not OPENAI_AVAILABLE:
        print("[WARNING] [SYNTHETIC_LLM] OpenAI SDK not available")
        return None
    
    if not OPENAI_API_KEY:
        print("[WARNING] [SYNTHETIC_LLM] OPENAI_API_KEY not configured")
        return None
    
    global OPENAI_CLIENT
    if OPENAI_CLIENT is None:
        OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

    kpi_name = (kpi.get('Name') or "KPI").strip() or "KPI"
    description = kpi.get('Description') or ""
    from_where = kpi.get('FromWhereToAccessData') or ""
    formula = (kpi.get('_OriginalFormula') or kpi.get('Formula') or "").strip()
    framework_name = (framework_info or {}).get('FrameworkName') or "Unknown Framework"

    required_columns = [col for col in (required_columns or []) if col]
    required_columns_section = ""
    if required_columns:
        required_columns_section = (
            "The dataset MUST include the following columns exactly as named "
            "(case-sensitive, no additional spaces or suffixes). Populate every row with these columns: "
            f"{', '.join(required_columns)}.\n"
        )

    prompt = f"""You are generating a synthetic evidence dataset for the KPI "{kpi_name}" in the "{framework_name}" framework.
The KPI description is: {description}
The existing formula is: {formula}
FromWhereToAccessData guidance: {from_where}
{required_columns_section}

Produce a JSON object ONLY in the following structure (no extra text):
{{
  "metadata": {{
    "columns": [
      {{"name":"ColumnName","type":"TYPE","description":"short description"}}
    ]
  }},
  "rows": [
    {{"SampleDate":"YYYY-MM-DD","MetricValue":float,"ConfidenceScore":float,"Notes":"string", "... additional columns as needed ..."}},
    ...
  ]
}}

Requirements:
- Output at least 100 rows (more is acceptable).
- All column names must align with those referenced or implied by the KPI formula. If the formula references multiple variables, include columns for each variable so the formula can be evaluated directly.
- SampleDate must be in ISO format (YYYY-MM-DD) and span a realistic time range.
- Provide realistic MetricValue (or equivalent) ranges based on the KPI semantics.
- ConfidenceScore should be between 0 and 1 with two decimal places.
- Add any additional columns referenced in the formula or required to compute the KPI (e.g., numerators, denominators, categories).
- Notes should briefly describe each row (<= 100 characters).
- metadata.columns must describe every column you include, with type and description.
- Do NOT include any keys other than "metadata" and "rows".
- Ensure rows are consistent and usable to compute the formula deterministically.
"""

    try:
        response = OPENAI_CLIENT.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You output ONLY valid JSON. No text before or after the JSON. "
                        "If you cannot comply, return {\"metadata\":{\"columns\":[]},\"rows\":[]}."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=min(TEMPERATURE + 0.3, 0.9),
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        if not content:
            print("[WARNING] [SYNTHETIC_LLM] Empty response from OpenAI")
            return None

        json_text = extract_json_from_text(content)
        if not json_text:
            print("[WARNING] [SYNTHETIC_LLM] Could not extract JSON from response")
            return None

        parsed = json.loads(json_text)
        metadata = parsed.get('metadata', {}) if isinstance(parsed, dict) else {}
        rows = parsed.get('rows') if isinstance(parsed, dict) else None
        if not rows or not isinstance(rows, list):
            print("[WARNING] [SYNTHETIC_LLM] JSON missing 'rows' array")
            return None

        df = pd.DataFrame(rows)
        if df.empty:
            print("[WARNING] [SYNTHETIC_LLM] Generated dataframe is empty")
            return None

        column_meta = metadata.get('columns') if isinstance(metadata, dict) else None
        if column_meta and isinstance(column_meta, list):
            for column_info in column_meta:
                name = column_info.get("name")
                if name and name not in df.columns:
                    df[name] = None
            df.attrs['column_metadata'] = column_meta

        # Normalize date column if present
        if 'SampleDate' in df.columns:
            try:
                df['SampleDate'] = pd.to_datetime(df['SampleDate']).dt.date.astype(str)
            except Exception:
                pass

        return df
    except Exception as exc:
        print(f"[WARNING] [SYNTHETIC_LLM] Unexpected error: {exc}")
        import traceback
        traceback.print_exc()
        return None


def create_synthetic_dataset_for_kpi(kpi: Dict[str, Any],
                                     framework_info: Dict[str, Any],
                                     s3_cache: Dict[str, Any],
                                     required_columns: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """Generate, upload, and ingest a synthetic dataset for KPIs lacking real sources."""
    framework_id = framework_info.get('FrameworkId')
    if framework_id is None:
        print("[WARNING] Synthetic dataset generation skipped (missing FrameworkId).")
        return None

    kpi_name = (kpi.get('Name') or "kpi").strip() or "kpi"
    module_name = kpi.get('Module') or kpi.get('module') or "module"
    framework_component = _sanitize_filename_component(
        framework_info.get('FrameworkName'),
        f"framework_{framework_id}"
    )
    module_component = _sanitize_filename_component(module_name, "module")
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d&%H%M%S")
    base_file_name = f"{framework_component}_{module_component}_{timestamp_str}"

    df = generate_llm_synthetic_dataframe(
        kpi,
        framework_info,
        required_columns=required_columns
    )

    if df is None or df.empty:
        message = f"Synthetic data generation failed for KPI '{kpi_name}' – LLM returned no usable rows."
        print(f"[ERROR] [SYNTHETIC] {message}")
        raise RuntimeError(message)

    metric_values: List[float] = []
    if 'MetricValue' in df.columns:
        try:
            metric_values = pd.to_numeric(df['MetricValue'], errors='coerce').dropna().tolist()
        except Exception:
            metric_values = []

    if 'FrameworkId' not in df.columns:
        df.insert(0, 'FrameworkId', int(framework_id))

    # Prepare CSV payload
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_text = csv_buffer.getvalue()
    csv_bytes = csv_text.encode('utf-8')

    csv_file_name = f"{base_file_name}.csv"
    print(f"[INFO] [SYNTHETIC] Uploading synthetic CSV via microservice for KPI '{kpi_name}' ({csv_file_name})")
    upload_csv = upload_bytes_via_microservice(
        csv_bytes,
        csv_file_name,
        user_id="synthetic-generator",
        module="synthetic",
        framework_id=framework_id,
        refresh_kpis=False
    )

    if not upload_csv.get('success'):
        error_msg = upload_csv.get('error') or 'Unknown error from microservice'
        print(f"[ERROR] [SYNTHETIC] Failed to upload synthetic CSV via microservice: {error_msg}")
        return None

    csv_info = upload_csv.get('file_info') or {}
    csv_bucket = (
        csv_info.get('bucket')
        or csv_info.get('bucketName')
        or csv_info.get('s3Bucket')
        or TARGET_S3_BUCKET
    )
    csv_key = (
        csv_info.get('s3Key')
        or csv_info.get('key')
        or csv_info.get('fileKey')
        or csv_info.get('storedName')
    )

    if not csv_bucket or not csv_key:
        print("[ERROR] [SYNTHETIC] Microservice response missing bucket/key for CSV upload.")
        return None

    print(f"[INFO] [SYNTHETIC] Uploaded synthetic CSV via microservice to s3://{csv_bucket}/{csv_key}")

    dataset_id = store_dataframe_for_document(csv_bucket, csv_key, df)

    cache_key = get_cache_key(csv_bucket, csv_key)
    doc_entry = {
        'bucket': csv_bucket,
        'key': csv_key,
        'size': len(csv_bytes),
        'last_modified': datetime.now(timezone.utc).isoformat(),
        'content_type': 'text/csv',
        'extracted_text': csv_text,
        'dataset_id': dataset_id
    }
    s3_cache[cache_key] = doc_entry
    save_s3_cache(s3_cache)

    existing_dataframes = _collect_from_where_dataframes(kpi.get('FromWhereToAccessData'))

    pdf_bytes = render_synthetic_pdf(
        kpi_name=kpi_name,
        framework_info=framework_info,
        dataframe=df,
        from_where=kpi.get('FromWhereToAccessData'),
        existing_dataframes=existing_dataframes
    )

    pdf_key = None
    if pdf_bytes:
        pdf_file_name = f"{base_file_name}.pdf"
        print(f"[INFO] [SYNTHETIC] Uploading synthetic PDF via microservice for KPI '{kpi_name}' ({pdf_file_name})")
        upload_pdf = upload_bytes_via_microservice(
            pdf_bytes,
            pdf_file_name,
            user_id="synthetic-generator",
            module="synthetic",
            framework_id=framework_id,
            refresh_kpis=False
        )
        if upload_pdf.get('success'):
            pdf_info = upload_pdf.get('file_info') or {}
            pdf_bucket = (
                pdf_info.get('bucket')
                or pdf_info.get('bucketName')
                or pdf_info.get('s3Bucket')
                or csv_bucket
            )
            pdf_key = (
                pdf_info.get('s3Key')
                or pdf_info.get('key')
                or pdf_info.get('fileKey')
                or pdf_info.get('storedName')
            )
            if pdf_bucket and pdf_key:
                print(f"[INFO] [SYNTHETIC] Uploaded synthetic PDF via microservice to s3://{pdf_bucket}/{pdf_key}")
        else:
            print(f"[WARNING] [SYNTHETIC] Failed to upload synthetic PDF via microservice: {upload_pdf.get('error')}")
            pdf_key = None

    return {
        'dataset_id': dataset_id,
        'bucket': csv_bucket,
        's3_key': csv_key,
        'pdf_key': pdf_key,
        'metric_values': metric_values
    }


def ensure_synthetic_sources_for_schema_plan_kpis(kpis: List[Dict[str, Any]],
                                                  framework_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Guarantee every KPI has executable data sources by injecting synthetic datasets when needed."""
    from .kpi_validation import _from_where_is_schema_plan
    from .formula_evaluator import evaluate_formula_against_dataframe
    
    if not kpis:
        return kpis

    framework_id = framework_info.get('FrameworkId')
    if framework_id is None:
        return kpis

    s3_cache = load_s3_cache()
    synthetic_created = False

    for kpi in kpis:
        if not kpi:
            continue
        formula_text = (kpi.get('Formula') or '').strip().lower()
        needs_synthetic = _from_where_is_schema_plan(kpi.get('FromWhereToAccessData')) or formula_text == "columns do not match"
        if not needs_synthetic:
            continue

        print(f"[INFO] [SYNTHETIC] KPI '{kpi.get('Name')}' requires synthetic dataset (reason: {'schema plan' if _from_where_is_schema_plan(kpi.get('FromWhereToAccessData')) else 'columns do not match'}).")

        kpi_for_generation = dict(kpi)
        if kpi.get('_OriginalFormula'):
            kpi_for_generation['Formula'] = kpi['_OriginalFormula']

        required_columns = list(dict.fromkeys(_extract_expression_columns(kpi_for_generation.get('Formula') or "")))

        print(f"[INFO] [SYNTHETIC] Requesting LLM-generated dataset for KPI '{kpi.get('Name')}'...")
        synthetic_payload = create_synthetic_dataset_for_kpi(
            kpi_for_generation,
            framework_info,
            s3_cache,
            required_columns=required_columns
        )

        if not synthetic_payload:
            print(f"[WARNING] [SYNTHETIC] Synthetic dataset generation failed for KPI '{kpi.get('Name')}'.")
            continue

        print(f"[INFO] [SYNTHETIC] Synthetic dataset generated for KPI '{kpi.get('Name')}'.")

        dataset_id = synthetic_payload.get('dataset_id')
        df = EVIDENCE_DATAFRAMES.get(dataset_id) if dataset_id else None

        original_formula = kpi.get('_OriginalFormula')
        if original_formula:
            tokens = set(_extract_expression_columns(original_formula))
            if not tokens or (df is not None and tokens.issubset(set(df.columns))):
                kpi['Formula'] = original_formula
                print(f"[INFO] [SYNTHETIC] Restored original formula for KPI '{kpi.get('Name')}'.")
        if not kpi.get('Formula') or kpi['Formula'].lower() in ("no formula", "columns do not match"):
            if df is not None:
                numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                if numeric_cols:
                    kpi['Formula'] = f"{numeric_cols[0]}.mean()"
                    print(f"[INFO] [SYNTHETIC] Assigned fallback formula '{kpi['Formula']}' for KPI '{kpi.get('Name')}'.")
                else:
                    kpi['Formula'] = "no formula"
                    print(f"[WARNING] [SYNTHETIC] No numeric columns available for KPI '{kpi.get('Name')}'. Formula remains 'no formula'.")

        pdf_note = ""
        if synthetic_payload.get('pdf_key'):
            pdf_note = f"; Evidence -> s3://{synthetic_payload['bucket']}/{synthetic_payload['pdf_key']}"

        kpi['DisplayType'] = kpi.get('DisplayType') or "Metric Card"
        kpi['FromWhereToAccessData'] = (
            f"Synthetic dataset -> s3://{synthetic_payload['bucket']}/{synthetic_payload['s3_key']}{pdf_note}"
        )

        if df is not None and kpi['Formula'] not in ("no formula", "columns do not match"):
            value, data_type = evaluate_formula_against_dataframe(kpi['Formula'], df)
            if value is not None:
                kpi['Value'] = value
            if data_type:
                kpi['DataType'] = data_type
        elif synthetic_payload['metric_values']:
            avg_value = sum(synthetic_payload['metric_values']) / len(synthetic_payload['metric_values'])
            kpi['Value'] = round(avg_value, 2)
            kpi['DataType'] = "Decimal"

        synthetic_created = True

    return kpis

