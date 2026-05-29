"""Compute next run time from schedule type and parameters (generic, no audit logic)."""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from croniter import croniter
    HAS_CRONITER = True
except ImportError:
    HAS_CRONITER = False


def compute_next_run(schedule_type, scheduled_at=None, cron_expression=None, start_date=None, base_time=None, timezone_offset_minutes=None):
    """
    Compute next_run_at from schedule_type and params.
    base_time: datetime to use as "now" (e.g. for start_date); defaults to now.
    timezone_offset_minutes: client's getTimezoneOffset() (e.g. -330 for IST); if set, hour/minute are local time.
    Returns datetime (UTC) or None.
    """
    now = base_time if base_time else datetime.utcnow()
    cron = (cron_expression or "").strip() if cron_expression else ""
    parts = cron.split() if cron else []
    logger.debug("compute_next_run: type=%s, scheduled_at=%s, cron=%s, start_date=%s, tz_offset=%s", schedule_type, scheduled_at, cron or None, start_date, timezone_offset_minutes)

    def _utc_to_local(dt_utc):
        if timezone_offset_minutes is None:
            return dt_utc
        return dt_utc + timedelta(minutes=-timezone_offset_minutes)

    def _local_to_utc(dt_local):
        if timezone_offset_minutes is None:
            return dt_local
        return dt_local + timedelta(minutes=timezone_offset_minutes)

    # Custom 5-field cron (interpret in local time if timezone_offset_minutes set)
    if schedule_type == "cron" and cron and len(parts) == 5 and HAS_CRONITER:
        try:
            if timezone_offset_minutes is not None:
                now_local = _utc_to_local(now)
                it = croniter(cron, now_local)
                next_local = it.get_next(datetime)
                next_utc = _local_to_utc(next_local)
                logger.debug("cron next_run (local)=%s -> UTC=%s", next_local, next_utc)
                return next_utc
            it = croniter(cron, now)
            next_dt = it.get_next(datetime)
            logger.debug("cron next_run=%s", next_dt)
            return next_dt
        except Exception as e:
            logger.warning("croniter failed for expression %r: %s", cron, e)
            return None

    if schedule_type == "one_week":
        return scheduled_at if scheduled_at else now + timedelta(days=7)
    if schedule_type == "one_minute":
        return now + timedelta(minutes=1)
    if schedule_type == "exact_date":
        return scheduled_at
    if schedule_type == "every_minute":
        return now + timedelta(minutes=1)

    if schedule_type == "daily" and len(parts) >= 2:
        try:
            minute, hour = int(parts[0]), int(parts[1])
            if timezone_offset_minutes is not None:
                now_local = _utc_to_local(now)
                candidate_local = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if candidate_local <= now_local:
                    candidate_local += timedelta(days=1)
                return _local_to_utc(candidate_local)
            candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            return candidate
        except (ValueError, IndexError):
            return None

    if schedule_type == "monthly" and len(parts) >= 3:
        try:
            minute, hour, dom = int(parts[0]), int(parts[1]), int(parts[2])
            dom = max(1, min(28, dom))
            if timezone_offset_minutes is not None:
                now_local = _utc_to_local(now)
                candidate_local = now_local.replace(day=dom, hour=hour, minute=minute, second=0, microsecond=0)
                if candidate_local <= now_local:
                    if now_local.month == 12:
                        candidate_local = candidate_local.replace(year=now_local.year + 1, month=1)
                    else:
                        candidate_local = candidate_local.replace(month=now_local.month + 1)
                return _local_to_utc(candidate_local)
            candidate = now.replace(day=dom, hour=hour, minute=minute, second=0, microsecond=0)
            if candidate <= now:
                if now.month == 12:
                    candidate = candidate.replace(year=now.year + 1, month=1)
                else:
                    candidate = candidate.replace(month=now.month + 1)
            return candidate
        except (ValueError, IndexError, TypeError):
            return None

    # recurring weekly: minute hour * * day_of_week (cron dow: 0=Sun, 1=Mon, ...)
    if schedule_type == "recurring" and len(parts) >= 5:
        try:
            minute, hour = int(parts[0]), int(parts[1])
            dow = int(parts[4])
            cron_to_weekday = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
            target_weekday = cron_to_weekday.get(dow, dow)
            if timezone_offset_minutes is not None:
                now_local = _utc_to_local(now)
                days_ahead = (target_weekday - now_local.weekday() + 7) % 7
                candidate_local = (now_local + timedelta(days=days_ahead)).replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                if candidate_local <= now_local:
                    candidate_local += timedelta(days=7)
                logger.debug("recurring next_run=%s", _local_to_utc(candidate_local))
                return _local_to_utc(candidate_local)
            days_ahead = (target_weekday - now.weekday() + 7) % 7
            candidate = (now + timedelta(days=days_ahead)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            if candidate <= now:
                candidate += timedelta(days=7)
            logger.debug("recurring next_run=%s", candidate)
            return candidate
        except (ValueError, IndexError) as e:
            logger.warning("recurring parse failed for cron %r: %s", cron, e)
            return None

    logger.debug("compute_next_run: no match, returning None")
    return None


def day_to_cron_dow(weekday_py):
    """Python weekday (Mon=0, Sun=6) to cron dow (Sun=0, Mon=1, ..., Sat=6)."""
    return {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}.get(weekday_py, 1)
