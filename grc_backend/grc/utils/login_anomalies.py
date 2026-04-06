"""
Heuristic login anomaly detection (time-of-day, region change, concurrent regions).

Region is taken from X-Client-Region (for testing), CF-IPCountry, or a coarse IP bucket.
Not a replacement for SIEM/UEBA; complements audit logs and hash-chain integrity logs.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache

from grc.routes.Global.logging_service import get_client_ip

logger = logging.getLogger(__name__)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def resolve_login_region(request) -> str:
    for meta_key in (
        "HTTP_X_CLIENT_REGION",
        "HTTP_CF_IPCOUNTRY",
        "HTTP_X_APP_REGION",
        "HTTP_CLOUDFRONT_VIEWER_COUNTRY",
    ):
        raw = request.META.get(meta_key)
        if raw:
            v = str(raw).strip().upper()[:64]
            if v:
                return v
    ip = get_client_ip(request)
    if ip and ip != "unknown":
        parts = ip.replace(":", ".").split(".")
        if len(parts) >= 2:
            return f"IP_{parts[0]}_{parts[1]}"
    return "UNKNOWN"


def _circular_hour_diff(a: int, b: int) -> int:
    return min((a - b) % 24, (b - a) % 24)


def evaluate_login_anomalies(user_id: int, request, auth_method: str) -> List[Dict[str, Any]]:
    if not getattr(settings, "LOGIN_ANOMALY_DETECTION_ENABLED", True):
        return []

    min_baseline = int(getattr(settings, "LOGIN_ANOMALY_MIN_BASELINE_LOGINS", 3))
    hour_tol = int(getattr(settings, "LOGIN_ANOMALY_HOUR_TOLERANCE", 4))
    region_window = int(getattr(settings, "LOGIN_ANOMALY_REGION_WINDOW_SECONDS", 3600))
    impossible_travel_window = int(getattr(settings, "LOGIN_ANOMALY_IMPOSSIBLE_TRAVEL_WINDOW_SECONDS", 1800))

    now = _now_utc()
    hour = now.hour
    region = resolve_login_region(request)

    baseline_key = f"login_baseline_v1:{user_id}"
    regions_key = f"login_active_regions_v1:{user_id}"

    baseline: Dict[str, Any] = cache.get(baseline_key) or {"hours": [], "last_region": None, "count": 0, "last_ts": None}
    hours: List[int] = list(baseline.get("hours", []))
    last_region: Optional[str] = baseline.get("last_region")
    count: int = int(baseline.get("count", 0))
    last_ts_raw = baseline.get("last_ts")

    anomalies: List[Dict[str, Any]] = []

    if count >= min_baseline and hours:
        recent = sorted(hours[-20:])
        median_h = recent[len(recent) // 2]
        if _circular_hour_diff(hour, median_h) > hour_tol:
            anomalies.append(
                {
                    "type": "UNUSUAL_LOGIN_TIME",
                    "median_hour_utc": median_h,
                    "current_hour_utc": hour,
                    "auth_method": auth_method,
                }
            )

    if (
        last_region
        and region not in ("UNKNOWN",)
        and last_region not in ("UNKNOWN",)
        and region != last_region
    ):
        anomalies.append(
            {
                "type": "REGION_CHANGE",
                "previous_region": last_region,
                "current_region": region,
                "auth_method": auth_method,
            }
        )

    # Detect impossible travel: region changed within an unreasonably short window
    if last_ts_raw:
        try:
            # last_ts_raw stored as ISO string
            last_dt = datetime.fromisoformat(str(last_ts_raw))
            seconds_since_last = (now - last_dt).total_seconds()
            if (
                last_region
                and last_region not in ("UNKNOWN",)
                and region not in ("UNKNOWN",)
                and region != last_region
                and seconds_since_last >= 0
                and seconds_since_last <= impossible_travel_window
            ):
                anomalies.append(
                    {
                        "type": "IMPOSSIBLE_TRAVEL",
                        "previous_region": last_region,
                        "current_region": region,
                        "seconds_since_last_login": int(seconds_since_last),
                        "window_seconds": impossible_travel_window,
                        "auth_method": auth_method,
                    }
                )
        except Exception:
            # Ignore parsing errors; continue
            pass

    now_ts = now.timestamp()
    active: Dict[str, float] = cache.get(regions_key) or {}
    active = {r: exp for r, exp in active.items() if exp > now_ts}
    active[region] = now_ts + region_window
    distinct = sorted(active.keys())
    if len(distinct) >= 2:
        anomalies.append(
            {
                "type": "CONCURRENT_REGIONS",
                "regions": distinct,
                "window_seconds": region_window,
                "auth_method": auth_method,
            }
        )
    cache.set(regions_key, active, region_window + 120)

    hours.append(hour)
    baseline["hours"] = hours[-30:]
    baseline["last_region"] = region
    baseline["count"] = count + 1
    baseline["last_ts"] = now.isoformat()
    cache.set(baseline_key, baseline, int(getattr(settings, "LOGIN_ANOMALY_BASELINE_TTL", 86400 * 90)))

    return anomalies


def _emit_chain_record(level: int, payload: Dict[str, Any]) -> None:
    if not getattr(settings, "SECURITY_AUDIT_LOG_ENABLED", True):
        return
    audit = logging.getLogger("grc.security_audit")
    msg = json.dumps(payload, default=str, sort_keys=True)
    audit.log(level, msg)


def record_login_security_events(user_id: int, request, auth_method: str, username: Optional[str] = None) -> None:
    """
    Emit a structured LOGIN_SUCCESS audit line and evaluate anomalies (also chained + DB when possible).
    """
    region = resolve_login_region(request)
    ip = get_client_ip(request)

    _emit_chain_record(
        logging.INFO,
        {
            "event": "LOGIN_SUCCESS",
            "user_id": user_id,
            "username": username,
            "auth_method": auth_method,
            "region": region,
            "ip": ip,
        },
    )

    try:
        anomalies = evaluate_login_anomalies(user_id, request, auth_method)
    except Exception as ex:
        logger.warning("login anomaly evaluation failed: %s", ex, exc_info=True)
        return

    for item in anomalies:
        logger.warning("LOGIN_ANOMALY user_id=%s detail=%s", user_id, item)
        _emit_chain_record(logging.WARNING, {"event": "LOGIN_ANOMALY", "user_id": user_id, "detail": item})

        try:
            from grc.routes.Global.logging_service import send_log

            send_log(
                module="Authentication",
                actionType="LOGIN_ANOMALY",
                description=f"Login anomaly for user_id {user_id}: {item.get('type')}",
                userId=str(user_id),
                userName=username,
                logLevel="WARNING",
                ipAddress=ip,
                additionalInfo=item,
                frameworkId=None,
            )
        except Exception as ex:
            logger.warning("Could not persist LOGIN_ANOMALY to grc_logs: %s", ex)
