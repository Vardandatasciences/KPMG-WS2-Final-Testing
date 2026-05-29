"""
Policy reminder date calculation + scheduler microservice integration.

When a policy is created/updated we:
1. Read its reminder_rules.
2. Back-calculate reminder datetimes from EndDate.
3. Call the scheduler microservice API to create one exact_date schedule per reminder.
4. Store the returned schedule_id in PolicyReminderSchedule for later cleanup.

The scheduler fires a webhook back to /api/policies/self-healing/reminders/run_single/
at the scheduled datetime.  That endpoint sends the actual notification.
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Date calculation
# ---------------------------------------------------------------------------

_START_UNIT_DELTA = {
    'year': relativedelta(years=1),
    'months': relativedelta(months=1),
    'weeks': relativedelta(weeks=1),
    'days': relativedelta(days=1),
    'hours': relativedelta(hours=1),
}

_FREQUENCY_DELTA = {
    'monthly': relativedelta(months=1),
    'quarterly': relativedelta(months=3),
    'half_yearly': relativedelta(months=6),
    'weekly': relativedelta(weeks=1),
    'daily': relativedelta(days=1),
    'hourly': relativedelta(hours=1),
}

_VALID_FREQ_BY_START = {
    'year': {'monthly', 'quarterly', 'half_yearly'},
    'months': {'monthly', 'quarterly', 'half_yearly', 'weekly'},
    'weeks': {'weekly', 'daily'},
    'days': {'daily', 'hourly'},
    'hours': {'hourly'},
}


def calculate_reminder_datetimes(end_date, rules):
    """
    Return a list of (rule_id, reminder_datetime) tuples.

    :param end_date: datetime or date — the policy EndDate.
    :param rules: iterable of dicts with keys start_value, start_unit, frequency_unit, id.
    :returns: list of (rule_id, datetime).
    """
    if not end_date:
        return []

    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # Work with datetime at end of day (UTC) for daily/weekly etc.
    # For hourly we keep the exact time, otherwise 23:59:00.
    base = datetime.combine(end_date, datetime.max_time()) if hasattr(end_date, 'year') else end_date

    reminders = []
    seen = set()

    for rule in rules:
        start_value = int(rule.get('start_value', 0))
        start_unit = rule.get('start_unit', 'months')
        frequency_unit = rule.get('frequency_unit', 'monthly')
        rule_id = rule.get('id')

        if start_value <= 0:
            continue

        # Validate frequency is allowed for this start unit
        allowed = _VALID_FREQ_BY_START.get(start_unit, set())
        if frequency_unit not in allowed:
            logger.warning(
                "Skipping rule %s: frequency %s not allowed for start_unit %s",
                rule_id, frequency_unit, start_unit,
            )
            continue

        # Reminder window: from (EndDate - start_value * start_unit) up to EndDate
        start_delta = _START_UNIT_DELTA.get(start_unit, relativedelta(months=1))
        # Multiply delta by start_value
        if start_unit == 'year':
            window_start = base - relativedelta(years=start_value)
        elif start_unit == 'months':
            window_start = base - relativedelta(months=start_value)
        elif start_unit == 'weeks':
            window_start = base - relativedelta(weeks=start_value)
        elif start_unit == 'days':
            window_start = base - relativedelta(days=start_value)
        elif start_unit == 'hours':
            window_start = base - relativedelta(hours=start_value)
        else:
            window_start = base - relativedelta(months=start_value)

        freq_delta = _FREQUENCY_DELTA.get(frequency_unit, relativedelta(months=1))

        # Generate dates backward from EndDate, but not before window_start
        current = base
        while current > window_start:
            dt_key = current.strftime('%Y-%m-%dT%H:%M')
            if dt_key not in seen:
                seen.add(dt_key)
                reminders.append((rule_id, current))
            # Step backward by frequency
            if frequency_unit == 'monthly':
                current = current - relativedelta(months=1)
            elif frequency_unit == 'quarterly':
                current = current - relativedelta(months=3)
            elif frequency_unit == 'half_yearly':
                current = current - relativedelta(months=6)
            elif frequency_unit == 'weekly':
                current = current - relativedelta(weeks=1)
            elif frequency_unit == 'daily':
                current = current - relativedelta(days=1)
            elif frequency_unit == 'hourly':
                current = current - relativedelta(hours=1)
            else:
                current = current - relativedelta(months=1)

    # Sort oldest first
    reminders.sort(key=lambda x: x[1])
    return reminders


# ---------------------------------------------------------------------------
# Scheduler API helpers
# ---------------------------------------------------------------------------

SCHEDULER_API_BASE = getattr(settings, 'SCHEDULER_API_BASE_URL', 'http://127.0.0.1:8000')
SELF_HEAL_SECRET = getattr(settings, 'POLICY_SELF_HEAL_CRON_SECRET', '')
WEBHOOK_URL_TEMPLATE = '{base_url}/api/policies/self-healing/reminders/run_single/'


def _scheduler_api(method, path, json_payload=None):
    """Call the scheduler microservice API."""
    url = f"{SCHEDULER_API_BASE}{path}"
    try:
        if method.upper() == 'POST':
            r = requests.post(url, json=json_payload, timeout=15)
        elif method.upper() == 'DELETE':
            r = requests.delete(url, timeout=10)
        else:
            r = requests.get(url, timeout=10)
        return r
    except Exception as e:
        logger.exception("Scheduler API call failed: %s %s", method, url)
        return None


def create_exact_date_schedule(name, scheduled_at, payload):
    """
    Create a one-time exact_date schedule in the scheduler microservice.
    Returns the schedule dict from the API or None.
    """
    iso_at = scheduled_at.strftime('%Y-%m-%dT%H:%M:%S')
    # The webhook URL must point back to the Django backend (not the frontend).
    django_base = getattr(settings, 'DJANGO_BASE_URL', '').rstrip('/')
    if not django_base:
        # Default assumption: Django runs on localhost:8000
        django_base = 'http://127.0.0.1:8000'
    webhook_url = f"{django_base}/api/policies/self-healing/reminders/run_single/"

    body = {
        "name": name,
        "schedule_type": "exact_date",
        "scheduled_at": iso_at,
        "action_type": "webhook",
        "callback_url": webhook_url,
        "payload": payload,
    }
    r = _scheduler_api('POST', '/api/schedules', body)
    if r is None:
        return None
    if r.status_code == 201:
        data = r.json()
        return data.get('schedule')
    logger.warning("Scheduler create_schedule failed: %s %s", r.status_code, r.text[:300])
    return None


def delete_scheduler_schedule(schedule_id):
    """Delete a schedule from the scheduler microservice."""
    r = _scheduler_api('DELETE', f'/api/schedules/{schedule_id}')
    if r is None:
        return False
    return r.status_code in (200, 204)


def update_scheduler_schedule_payload(schedule_id, payload):
    """PATCH a schedule's payload in the scheduler microservice."""
    r = _scheduler_api('PATCH', f'/api/schedules/{schedule_id}', {'payload': payload})
    if r is None:
        return False
    return r.status_code in (200, 204)


# ---------------------------------------------------------------------------
# Policy-level helpers
# ---------------------------------------------------------------------------

def sync_policy_reminder_schedules(policy):
    """
    Called after a policy is created/updated.
    1. Cancel old PolicyReminderSchedule rows (and delete scheduler jobs).
    2. Recalculate reminder datetimes from current rules + EndDate.
    3. Create new exact_date schedules in the scheduler microservice.
    4. Store new PolicyReminderSchedule rows.
    """
    from grc.models import PolicyReminderSchedule

    # 1. Cancel old
    old_schedules = PolicyReminderSchedule.objects.filter(
        policy=policy,
        status='scheduled',
    )
    for old in old_schedules:
        if old.schedule_id:
            delete_scheduler_schedule(old.schedule_id)
        old.status = PolicyReminderSchedule.STATUS_CANCELLED
        old.save(update_fields=['status', 'updated_at'])

    # 2. Recalculate
    rules = list(policy.reminder_rules.values('id', 'start_value', 'start_unit', 'frequency_unit'))
    if not rules or not policy.EndDate:
        return []

    reminder_list = calculate_reminder_datetimes(policy.EndDate, rules)
    created_rows = []

    for rule_id, dt in reminder_list:
        name = f"Policy-{policy.PolicyId}-reminder-{dt.strftime('%Y%m%d%H%M')}"
        # Create schedule with minimal payload first
        initial_payload = {
            "secret": SELF_HEAL_SECRET,
            "policy_id": policy.PolicyId,
            "rule_id": rule_id,
        }
        sched = create_exact_date_schedule(name, dt, initial_payload)
        if sched:
            schedule_id = sched.get('id')
            # PATCH payload to include schedule_id so the webhook knows exactly which schedule fired
            updated_payload = {
                **initial_payload,
                "schedule_id": schedule_id,
            }
            update_scheduler_schedule_payload(schedule_id, updated_payload)
            row = PolicyReminderSchedule.objects.create(
                policy=policy,
                reminder_rule_id=rule_id,
                schedule_id=schedule_id,
                scheduled_at=dt,
                status=PolicyReminderSchedule.STATUS_SCHEDULED,
            )
            created_rows.append(row)

    return created_rows


def cancel_all_policy_reminder_schedules(policy):
    """Called when a policy is deleted or EndDate is cleared."""
    from grc.models import PolicyReminderSchedule
    old_schedules = PolicyReminderSchedule.objects.filter(
        policy=policy,
        status='scheduled',
    )
    for old in old_schedules:
        if old.schedule_id:
            delete_scheduler_schedule(old.schedule_id)
        old.status = PolicyReminderSchedule.STATUS_CANCELLED
        old.save(update_fields=['status', 'updated_at'])
