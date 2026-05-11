"""
KPI validation, alignment, and deduplication
"""
import re
import json
from typing import Dict, Any, List, Optional
import pandas as pd

from .config import EVIDENCE_DATAFRAMES
from .evidence import tokenize_text, select_matching_tables, select_matching_s3_semantic


def get_numeric_columns(table_name, schema_info):
    """Return list of numeric columns for a table based on schema metadata."""
    numeric_keywords = ('int', 'decimal', 'numeric', 'float', 'double', 'real')
    columns = schema_info.get(table_name, {}).get('column_details', [])
    numeric_cols = []
    for col in columns:
        col_type = (col.get('type') or '').lower()
        if any(keyword in col_type for keyword in numeric_keywords):
            numeric_cols.append(col['name'])
    return numeric_cols


def validate_formula_references(formula, schema_info):
    """Check if every table.column reference in formula exists in schema_info."""
    if not formula:
        return False
    table_column_pattern = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b")
    matches = table_column_pattern.findall(formula)
    if not matches:
        return False
    for table_name, column_name in matches:
        table_info = schema_info.get(table_name)
        if not table_info or column_name not in table_info.get('columns', []):
            return False
    return True


FORMULA_FUNCTIONS = {
    "average": lambda series: float(pd.to_numeric(series, errors='coerce').mean()),
    "avg": lambda series: float(pd.to_numeric(series, errors='coerce').mean()),
    "mean": lambda series: float(pd.to_numeric(series, errors='coerce').mean()),
    "sum": lambda series: float(pd.to_numeric(series, errors='coerce').sum()),
    "count": lambda series: int(pd.Series(series).count()),
    "max": lambda series: pd.to_numeric(series, errors='coerce').max(),
    "min": lambda series: pd.to_numeric(series, errors='coerce').min(),
    "median": lambda series: float(pd.to_numeric(series, errors='coerce').median()),
}

FORMULA_KEYWORDS = set(list(FORMULA_FUNCTIONS.keys()) + ["and", "or", "not", "abs"])


def _extract_expression_columns(formula: str) -> List[str]:
    """Extract column names from formula expression."""
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula or "")
    columns: List[str] = []
    for token in tokens:
        token_lower = token.lower()
        if token_lower in FORMULA_KEYWORDS:
            continue
        if token.isdigit():
            continue
        columns.append(token)
    return list(dict.fromkeys(columns))


def align_kpis_with_evidence(kpis, evidence_index, schema_info, framework_id):
    """Rewrite KPI formulas and FromWhereToAccessData using verified evidence."""
    if not kpis or not evidence_index:
        return kpis

    for kpi in kpis:
        name = kpi.get('Name', '')
        description = kpi.get('Description', '')
        original_formula = (kpi.get('Formula') or '').strip()
        keywords = tokenize_text(name)
        keywords.update(tokenize_text(description))

        table_matches = select_matching_tables(keywords, evidence_index)

        query_text = ' '.join(part for part in [name, description] if part)
        s3_matches = select_matching_s3_semantic(query_text, evidence_index)

        primary_table = table_matches[0] if table_matches else None
        selected_columns = []

        if not original_formula:
            kpi['Formula'] = "no formula"
        elif primary_table:
            info = primary_table['info']
            matched_columns = primary_table['matched_columns']
            if not matched_columns:
                matched_columns = info['columns'][:3]
            selected_columns = matched_columns[:3]

        lines = []
        if primary_table:
            table = primary_table['table']
            info = primary_table['info']
            matched_columns = selected_columns or info['columns'][:3]
            column_refs = ', '.join(f"{table}.{col}" for col in matched_columns)
            table_line = f"- {table}: columns {column_refs}"
            lines.append("Available data sources:")
            lines.append(table_line)

            secondary_tables = table_matches[1:3]
            for match in secondary_tables:
                table = match['table']
                info = match['info']
                columns = match['matched_columns'] or info['columns'][:2]
                column_refs = ', '.join(f"{table}.{col}" for col in columns)
                line = f"- {table}: columns {column_refs}"
                lines.append(line)

        # Skip overriding the LLM's FromWhereToAccessData; we only rewrite formulas if needed.

    return kpis


def validate_and_sanitize_formulas(kpis: List[Dict[str, Any]],
                                   schema_info: Dict[str, Any],
                                   framework_id: Optional[int]) -> List[Dict[str, Any]]:
    """Validate formulas against available datasets."""
    if not kpis:
        return kpis

    for kpi in kpis:
        formula = (kpi.get('Formula') or '').strip()
        if not formula or formula.lower() == "no formula":
            kpi['Formula'] = "no formula"
            continue

        column_tokens = _extract_expression_columns(formula)
        if not column_tokens:
            kpi['Formula'] = formula
            continue

        dataset_matches = False
        for df in EVIDENCE_DATAFRAMES.values():
            if set(column_tokens).issubset(set(df.columns)):
                dataset_matches = True
                break

        if not dataset_matches:
            # Always save the original formula before replacing
            if formula and formula != "columns do not match":
                kpi['_OriginalFormula'] = formula
            kpi['Formula'] = "columns do not match"
            continue

            kpi['Formula'] = formula

    return kpis


def deduplicate_kpis(kpis):
    """Remove duplicate KPIs based on name (case-insensitive) and keep the first occurrence."""
    print(f"[INFO] [DEDUPE] Starting deduplication of KPIs...")
    
    seen_names = set()
    deduplicated_kpis = []
    duplicates_removed = 0
    
    for kpi in kpis:
        kpi_name = kpi.get('Name', '').strip()
        if not kpi_name:
            print(f"[WARNING] [DEDUPE] Skipping KPI with empty name")
            continue
        
        # Normalize name for comparison (lowercase, remove extra spaces)
        normalized_name = ' '.join(kpi_name.lower().split())
        
        if normalized_name not in seen_names:
            seen_names.add(normalized_name)
            deduplicated_kpis.append(kpi)
        else:
            duplicates_removed += 1
            print(f"[INFO] [DEDUPE] Removed duplicate: '{kpi_name}'")
    
    print(f"[INFO] [DEDUPE] Removed {duplicates_removed} duplicate KPIs")
    print(f"[INFO] [DEDUPE] Final unique KPIs: {len(deduplicated_kpis)} (from {len(kpis)} total)")
    
    return deduplicated_kpis


def _ensure_from_where_to_access_data(kpis: List[Dict[str, Any]]) -> None:
    """Ensure each KPI carries provenance guidance."""
    for kpi in kpis:
        if kpi.get('FromWhereToAccessData'):
            continue
        name = kpi.get('Name') or "KPI"
        kpi['FromWhereToAccessData'] = {
            "status": "schema_plan",
            "schema_plan": f"Define structured dataset for {name} aligned to regulatory reporting.",
            "data_acquisition": "Coordinate with responsible system owners to populate the dataset and expose it via curated evidence uploads.",
            "s3_evidence_plan": "Upload certified evidence files to S3 and package both structured data and narrative context within a single PDF."
        }


def _from_where_is_schema_plan(from_where: Optional[str]) -> bool:
    """Check if the FromWhereToAccessData field only contains guidance (no live data)."""
    if not from_where:
        return False
    if isinstance(from_where, dict):
        if from_where.get("status") == "schema_plan":
            return True
        if not from_where.get("sources"):
            return True
        return False
    if isinstance(from_where, str):
        try:
            parsed = json.loads(from_where)
            return _from_where_is_schema_plan(parsed)
        except Exception:
            return "Schema plan ->" in from_where
    return False


def enforce_schema_sources(kpis, schema_info=None, framework_id=None):
    """Schema enforcement disabled per user request; return KPIs unchanged."""
    if not kpis:
        return kpis

    print("[INFO] [VALIDATE] Schema enforcement skipped – returning KPIs as generated.")
    return kpis


def filter_kpis_with_actual_sources(kpis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove KPIs that only contain placeholder schema plans or lack formulas/data."""
    filtered = []
    dropped = 0
    for kpi in kpis:
        value = kpi.get('Value')
        formula = (kpi.get('Formula') or '').strip()
        from_where = kpi.get('FromWhereToAccessData')

        if isinstance(from_where, (dict, list)):
            try:
                from_where_text = json.dumps(from_where, ensure_ascii=False)
            except TypeError:
                from_where_text = str(from_where)
        else:
            from_where_text = (from_where or '')

        has_schema_plan = "schema plan ->" in from_where_text.lower()
        has_data_acquisition = "data acquisition ->" in from_where_text.lower()

        if value is not None:
            filtered.append(kpi)
        elif formula and not has_schema_plan and not has_data_acquisition:
            filtered.append(kpi)
        else:
            dropped += 1

    if dropped:
        print(f"[INFO] [FILTER] Dropped {dropped} placeholder KPIs lacking live data sources.")
    return filtered

