

"""
Formula evaluation against dataframes
"""
import re
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from .config import EVIDENCE_DATAFRAMES
from .kpi_validation import FORMULA_FUNCTIONS, FORMULA_KEYWORDS, _extract_expression_columns


def _infer_data_type_from_value(value: Any) -> Optional[str]:
    """Infer a friendly data type label from a SQL result."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "Boolean"
    if isinstance(value, int):
        return "Integer"
    if isinstance(value, float):
        return "Float"
    if isinstance(value, Decimal):
        return "Decimal"
    if isinstance(value, datetime):
        return "Datetime"
    if isinstance(value, date):
        return "Date"
    return "String"


def _sanitize_formula_expression(formula: str) -> str:
    """Return a cleaned expression suitable for eval-based execution."""
    expression = formula.replace("\n", " ").strip()
    if ".days" in expression:
        expression = re.sub(r"(?<!\.dt)\.days\b", ".dt.days", expression)
    return expression


def _normalize_series(series: Any) -> pd.Series:
    """Normalize various types to pandas Series."""
    if isinstance(series, pd.Series):
        return series
    if isinstance(series, (list, tuple, set)):
        return pd.Series(list(series))
    return pd.Series([series])


def _finalize_formula_result(result: Any) -> Tuple[Optional[Any], Optional[str]]:
    """Convert formula evaluation result to final value and data type."""
    if isinstance(result, pd.Series):
        numeric = pd.to_numeric(result, errors='coerce')
        if numeric.notna().any():
            return float(numeric.mean()), "Float"
        non_null = result.dropna()
        if not non_null.empty:
            value = non_null.iloc[0]
            return value, _infer_data_type_from_value(value)
        return None, None

    if isinstance(result, (list, tuple, set)):
        normalized = _normalize_series(result)
        return _finalize_formula_result(normalized)

    if isinstance(result, Decimal):
        return float(result), "Decimal"

    data_type = _infer_data_type_from_value(result)
    if isinstance(result, (datetime, pd.Timestamp)):
        return result.isoformat(), data_type
    if isinstance(result, date):
        return result.isoformat(), data_type
    if isinstance(result, (int, float)):
        return float(result), data_type or "Float"
    return result, data_type


def evaluate_formula_against_dataframe(formula: str, dataframe: pd.DataFrame) -> Tuple[Optional[Any], Optional[str]]:
    """Evaluate a pandas-style formula against a dataframe."""
    expression = _sanitize_formula_expression(formula)
    if not expression:
        return None, None

    token_columns = _extract_expression_columns(expression)
    df_for_eval = dataframe
    coerced_copy = None
    for col in token_columns:
        if col in df_for_eval.columns:
            series = df_for_eval[col]
            if isinstance(series, pd.Series) and series.dtype == object:
                parsed = pd.to_datetime(series, errors='coerce')
                if parsed.notna().any():
                    if coerced_copy is None:
                        coerced_copy = df_for_eval.copy()
                        df_for_eval = coerced_copy
                    df_for_eval[col] = parsed

    local_env: Dict[str, Any] = {col: df_for_eval[col] for col in df_for_eval.columns}
    safe_env: Dict[str, Any] = {}
    safe_env.update(FORMULA_FUNCTIONS)
    safe_env.update({"abs": lambda series: _normalize_series(series).abs()})

    try:
        result = eval(expression, {"__builtins__": {}}, {**safe_env, **local_env})
    except Exception as exc:
        print(f"[WARNING] [FORMULA] Evaluation failed for expression '{expression}': {exc}")
        return None, None

    value, dtype = _finalize_formula_result(result)
    if value is not None:
        print(f"[INFO] [FORMULA] Evaluated expression '{expression}' -> {value} ({dtype})")
    else:
        print(f"[WARNING] [FORMULA] Expression '{expression}' did not return a numeric result.")
    return value, dtype


def populate_kpi_values_from_memory(kpis: List[Dict[str, Any]]) -> None:
    """Populate Value/DataType using in-memory dataframes rather than SQL execution."""
    if not kpis:
        return
    if not EVIDENCE_DATAFRAMES:
        print("[INFO] [VALUE] No in-memory datasets available; skipping KPI value computation.")
        return

    for kpi in kpis:
        formula = (kpi.get('Formula') or '').strip()
        if not formula:
            continue
        if formula.lower() in ("no formula", "columns do not match"):
            continue
        from_where = kpi.get('FromWhereToAccessData')
        if from_where and _from_where_is_schema_plan(str(from_where)):
            continue

        columns_needed = set(_extract_expression_columns(formula))
        dataset_id = None
        dataframe = None

        # First pass: prefer datasets explicitly mentioned in FromWhereToAccessData
        if isinstance(from_where, str):
            matches = re.findall(r"s3://([^\s/]+)/([^\s;]+)", from_where)
            for bucket, key in matches:
                candidate_id = f"{bucket}/{key}"
                dataset_id = candidate_id
                dataframe = EVIDENCE_DATAFRAMES.get(candidate_id)
                if dataframe is not None:
                    break

        # Second pass: pick any dataframe that contains required columns
        if dataframe is None:
            for candidate_id, df in EVIDENCE_DATAFRAMES.items():
                if columns_needed and not columns_needed.issubset(set(df.columns)):
                    continue
                dataset_id = candidate_id
                dataframe = df
                break

        if dataframe is None:
            print(f"[INFO] [VALUE] No dataframe found for KPI '{kpi.get('Name')}'")
            continue

        value, data_type = evaluate_formula_against_dataframe(formula, dataframe)
        if value is not None:
            kpi['Value'] = value
        else:
            kpi.setdefault('Value', None)
        if data_type:
            kpi['DataType'] = data_type
        else:
            kpi.setdefault('DataType', None)


def _from_where_is_schema_plan(from_where: Optional[str]) -> bool:
    """Check if the FromWhereToAccessData field only contains guidance (no live data)."""
    if not from_where:
        return False
    import json
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

