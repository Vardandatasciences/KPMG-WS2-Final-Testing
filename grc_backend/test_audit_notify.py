"""Manual test for audit 5717 due-soon notification. Run from grc_backend folder."""
import datetime
import json
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.db import connection
from django.utils import timezone

from grc.models import Audit
from grc.routes.Global.notifications import get_user_email_from_id
from grc.services.audit_recurrence_service import store_in_app_audit_notification

AUDIT_ID = 5717
today = timezone.now().date()

a = Audit.objects.filter(AuditId=AUDIT_ID).select_related("Auditor", "FrameworkId").first()
if not a:
    print(f"ERROR: audit {AUDIT_ID} not found")
    raise SystemExit(1)

due_soon = (
    (a.Status or "").lower() != "completed"
    and a.DueDate
    and today <= a.DueDate <= today + datetime.timedelta(days=3)
)

print("=== Audit row ===")
print("  AuditId:", a.AuditId)
print("  DueDate:", a.DueDate, "  today:", today)
print("  Status:", a.Status)
print("  Frequency:", a.Frequency, "(must be > 0 for scheduler job)")
print("  Auditor_id:", a.Auditor_id)
print("  FrameworkId:", a.FrameworkId_id)
print("  due_soon_match:", due_soon)

if a.Auditor_id:
    email = get_user_email_from_id(int(a.Auditor_id))
    print("  auditor email (for notifications):", email or f"(none — will use user_{a.Auditor_id})")

if not due_soon:
    print("\nFIX: Due date must be between today and today+3 days:")
    print(f"  UPDATE audit SET DueDate = DATE_ADD(CURDATE(), INTERVAL 2 DAY) WHERE AuditId = {AUDIT_ID};")
    raise SystemExit(1)

if not (a.Frequency and int(a.Frequency) > 0):
    print("\nFIX: Frequency must be > 0:")
    print(f"  UPDATE audit SET Frequency = 30 WHERE AuditId = {AUDIT_ID};")
    raise SystemExit(1)

print("\n=== Insert one due-soon notification ===")
store_in_app_audit_notification(
    a.Auditor_id,
    "audit_due_reminder",
    "Audit due soon",
    f'Audit "{a.Title}" is due on {a.DueDate}.',
    a.FrameworkId_id,
    {"audit_id": a.AuditId, "due_date": a.DueDate.isoformat()},
)

with connection.cursor() as c:
    c.execute(
        "SELECT COUNT(*) FROM notifications WHERE type = %s",
        ["audit_due_reminder"],
    )
    count = c.fetchone()[0]
    print("  audit_due_reminder rows in DB:", count)
    c.execute(
        """
        SELECT id, recipient, type, created_at, LEFT(error, 120)
        FROM notifications
        WHERE type = %s
        ORDER BY id DESC LIMIT 3
        """,
        ["audit_due_reminder"],
    )
    for row in c.fetchall():
        print("  ", row)

print("\n=== Full scheduler (optional, slow if many audits) ===")
print("  python manage.py run_scheduled_audits")
print("\nUI: log in as auditor user", a.Auditor_id, "→ Notifications")
