"""
Management command to run scheduled AI audits.
Optional: A background scheduler runs automatically when Django starts (checks every 60 seconds).
You can also run this manually: python manage.py run_scheduled_ai_audits
"""
import re
import logging
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q
from django.utils import timezone

from grc.models import AIAuditSchedule, AIAuditScheduleRun, CompanyFolder, CompanySubfolder, FileOperations
from grc.utils.auto_decrypt_helper import decrypt_any_encrypted_value

logger = logging.getLogger(__name__)


def _sanitize_filename_part(value):
    """Sanitize string for filename prefix (matches DocumentHandling.upload_document)."""
    if not value:
        return 'na'
    value = str(value).strip().lower()
    value = re.sub(r'[^a-z0-9]+', '_', value)
    value = value.strip('_')
    return value or 'na'


def _compute_next_run(schedule):
    """Compute next_run_at for recurring schedules from schedule_type and cron_expression. Supports cron via croniter."""
    now = timezone.now()
    schedule_type = getattr(schedule, 'schedule_type', 'recurring')
    cron = (schedule.cron_expression or '').strip()
    parts = cron.split()

    if schedule_type == 'cron' and len(parts) == 5:
        try:
            from croniter import croniter
            it = croniter(cron, now)
            next_dt = it.get_next(datetime)
            if timezone.is_naive(next_dt) and getattr(settings, 'USE_TZ', True):
                next_dt = timezone.make_aware(next_dt)
            return next_dt
        except Exception:
            return None

    if schedule_type == 'every_minute':
        return now + timedelta(minutes=1)

    if schedule_type == 'daily' and len(parts) >= 2:
        try:
            minute, hour = int(parts[0]), int(parts[1])
            candidate = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            return candidate
        except (ValueError, IndexError):
            return None

    if schedule_type == 'monthly' and len(parts) >= 3:
        try:
            minute, hour, dom = int(parts[0]), int(parts[1]), int(parts[2])
            dom = max(1, min(28, dom))
            # Run 5 days before the selected day of month (audit done before target day)
            target = now.replace(day=min(dom, 28), hour=hour, minute=minute, second=0, microsecond=0)
            candidate = target - timedelta(days=5)
            if candidate <= now:
                if now.month == 12:
                    target = target.replace(year=now.year + 1, month=1)
                else:
                    target = target.replace(month=now.month + 1)
                candidate = target - timedelta(days=5)
            return candidate
        except (ValueError, IndexError, TypeError):
            return None

    # recurring (weekly): minute hour * * day_of_week
    if schedule_type == 'recurring' and len(parts) >= 5:
        try:
            minute = int(parts[0])
            hour = int(parts[1])
            dow = int(parts[4])
            cron_to_weekday = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
            target_weekday = cron_to_weekday.get(dow, dow)
            days_ahead = (target_weekday - now.weekday() + 7) % 7
            candidate = (now + timedelta(days=days_ahead)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            if candidate <= now:
                candidate += timedelta(days=7)
            return candidate
        except (ValueError, IndexError):
            pass

    # quarterly from start_date: every 3 months from schedule.start_date at same day and time
    if schedule_type == 'quarterly':
        start_date = getattr(schedule, 'start_date', None)
        if not start_date:
            return None
        if timezone.is_naive(start_date) and getattr(settings, 'USE_TZ', True):
            start_date = timezone.make_aware(start_date)
        minute, hour = 0, 9
        if len(parts) >= 2:
            try:
                minute, hour = int(parts[0]), int(parts[1])
            except (ValueError, TypeError):
                pass
        candidate = start_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        while candidate <= now:
            start_date = start_date + relativedelta(months=3)
            candidate = start_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if timezone.is_naive(candidate) and getattr(settings, 'USE_TZ', True):
                candidate = timezone.make_aware(candidate)
        return candidate

    # yearly: run 30 days before target date (schedule.start_date's month/day) each year
    if schedule_type == 'yearly':
        start_date = getattr(schedule, 'start_date', None)
        if not start_date:
            return None
        if timezone.is_naive(start_date) and getattr(settings, 'USE_TZ', True):
            start_date = timezone.make_aware(start_date)
        minute, hour = 0, 9
        if len(parts) >= 2:
            try:
                minute, hour = int(parts[0]), int(parts[1])
            except (ValueError, TypeError):
                pass
        target = now.replace(month=start_date.month, day=min(start_date.day, 28), hour=hour, minute=minute, second=0, microsecond=0)
        candidate = target - timedelta(days=30)
        if timezone.is_naive(candidate) and getattr(settings, 'USE_TZ', True):
            candidate = timezone.make_aware(candidate)
        if candidate <= now:
            target = target + relativedelta(years=1)
            candidate = target - timedelta(days=30)
            if timezone.is_naive(candidate) and getattr(settings, 'USE_TZ', True):
                candidate = timezone.make_aware(candidate)
        return candidate

    return None


def _get_compliance_ids_for_audit(audit_id):
    """Get all compliance IDs from ai_audit_data for an audit (live evidences)."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT c.ComplianceId
            FROM ai_audit_data d
            JOIN subpolicies sp ON sp.SubPolicyId = d.subpolicy_id AND sp.PolicyId = d.policy_id
            JOIN compliance c ON c.SubPolicyId = sp.SubPolicyId
            WHERE d.audit_id = %s
              AND d.subpolicy_id IS NOT NULL
              AND d.policy_id IS NOT NULL
            """,
            [int(audit_id)]
        )
        return [r[0] for r in cursor.fetchall()]


def _get_compliance_ids_from_framework(audit_id):
    """Get compliance IDs from audit's framework (for Document Handling evidence source)."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT c.ComplianceId
            FROM audit a
            JOIN compliance c ON c.FrameworkId = a.FrameworkId
            WHERE a.AuditId = %s AND a.FrameworkId IS NOT NULL
            """,
            [int(audit_id)]
        )
        return [r[0] for r in cursor.fetchall()]


def _get_document_ids_for_audit(audit_id):
    """Get distinct document IDs from ai_audit_data for an audit (for per-document checks)."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT document_id
            FROM ai_audit_data
            WHERE audit_id = %s AND document_id IS NOT NULL AND document_id > 0
            ORDER BY document_id
            """,
            [int(audit_id)]
        )
        return [r[0] for r in cursor.fetchall()]


def _ensure_document_handling_evidence(schedule):
    """
    When schedule has company_folder_id: fetch FileOperations docs (framework+company),
    upsert into ai_audit_data as evidence_attachment (use existing if audit_id+external_id match).
    Returns (document_ids, error). document_ids are the IDs to process - no cleanup (keep in ai_audit_data).
    """
    audit_id = schedule.audit_id
    company_folder_id = schedule.company_folder_id if hasattr(schedule, 'company_folder_id') else None
    if not company_folder_id:
        return [], None

    try:
        company_folder = CompanyFolder.objects.get(folder_id=company_folder_id, is_active=True)
    except CompanyFolder.DoesNotExist:
        return [], 'Company folder not found'

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT FrameworkId, PolicyId, SubPolicyId FROM audit WHERE AuditId = %s LIMIT 1",
            [int(audit_id)]
        )
        row = cursor.fetchone()
        if not row:
            return [], 'Audit not found'
        framework_id, policy_id, subpolicy_id = row[0], row[1], row[2]
        if not framework_id:
            return [], 'Audit has no framework'

    prefix = _sanitize_filename_part(company_folder.code) + '_'
    company_code_raw = _sanitize_filename_part(company_folder.code)  # e.g. sebi_company
    company_subfolder_id = getattr(schedule, 'company_subfolder_id', None)
    if company_subfolder_id:
        try:
            subfolder = CompanySubfolder.objects.get(
                subfolder_id=company_subfolder_id,
                company_folder_id=company_folder_id,
                is_active=True
            )
            sub_safe = _sanitize_filename_part(subfolder.code)
            prefix = f"{company_code_raw}_{sub_safe}_"
        except CompanySubfolder.DoesNotExist:
            pass
    # Match file_name (Document Handling uses company_ or company_subfolder_ prefix) OR stored_name/s3_key
    company_filter = (
        Q(file_name__istartswith=prefix) |
        Q(file_name__icontains=company_code_raw) |
        Q(stored_name__icontains=company_code_raw) |
        Q(s3_key__icontains=company_code_raw)
    )
    if getattr(schedule, 'company_subfolder_id', None):
        sub_prefix = prefix  # already set to company_subfolder_ prefix above
        company_filter = company_filter & (
            Q(file_name__istartswith=sub_prefix) |
            Q(stored_name__icontains=sub_prefix) |
            Q(s3_key__icontains=sub_prefix)
        )

    logger.info(
        "Document Handling lookup: audit=%s, company_folder=%s (code=%s), prefix=%s, framework_id=%s",
        audit_id, company_folder_id, company_folder.code, prefix, framework_id
    )

    file_ops = list(
        FileOperations.objects.filter(
            operation_type='upload',
            FrameworkId=framework_id,
            status='completed',
        ).filter(company_filter).exclude(user_id='export_user')[:500]
    )
    # Fallback: Document Handling may store uploads with different FrameworkId. Try company filter only.
    if not file_ops:
        file_ops = list(
            FileOperations.objects.filter(
                operation_type='upload',
                status='completed',
            ).filter(company_filter).exclude(user_id='export_user')[:500]
        )
        if file_ops:
            logger.info(
                "Using Document Handling docs by company filter only (FrameworkId mismatch). "
                "Docs found in folder '%s' but with different framework.",
                company_folder.code
            )
    if not file_ops:
        # Debug: log counts and sample filenames to help diagnose
        with connection.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM file_operations WHERE operation_type='upload' AND status='completed' AND FrameworkId=%s",
                [framework_id]
            )
            cnt_fw = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM file_operations WHERE operation_type='upload' AND status='completed'"
            )
            cnt_all = cur.fetchone()[0]
            # Sample filenames with matching framework (to see naming pattern)
            cur.execute(
                """SELECT file_name, s3_key FROM file_operations
                   WHERE operation_type='upload' AND status='completed' AND FrameworkId=%s
                   LIMIT 5""",
                [framework_id]
            )
            samples_fw = cur.fetchall()
            # Sample filenames with company in name (any framework)
            cur.execute(
                """SELECT file_name, s3_key, FrameworkId FROM file_operations
                   WHERE operation_type='upload' AND status='completed'
                     AND (file_name LIKE %s OR COALESCE(s3_key,'') LIKE %s)
                   LIMIT 5""",
                [f'%{company_code_raw}%', f'%{company_code_raw}%']
            )
            samples_company = cur.fetchall()
        logger.warning(
            "No Document Handling docs: audit=%s company_folder=%s (code=%s) prefix=%r framework_id=%s. "
            "Counts: %s uploads with framework_id=%s, %s total. "
            "Sample filenames (framework match): %s. Sample filenames (company match): %s.",
            audit_id, company_folder_id, company_folder.code, prefix, framework_id,
            cnt_fw, framework_id, cnt_all,
            [(r[0], (r[1] or '')[:80]) for r in samples_fw],
            [(r[0], (r[1] or '')[:80], r[2]) for r in samples_company]
        )
        return [], 'No documents found in Document Handling for this framework and company'

    logger.info("Document Handling: found %d docs for audit=%s (company=%s, framework=%s)", len(file_ops), audit_id, company_folder.code, framework_id)

    # ai_audit_data.uploaded_by expects integer user ID; FileOperations.user_id may be username string (e.g. vikram.patel)
    default_uploader_id = getattr(schedule, 'created_by_id', None) or 0

    # ai_audit_data.document_name / document_path may have varchar limit; truncate long filenames
    def _truncate(s, max_len=255):
        s = (s or '').strip()
        return (s[:max_len] if len(s) > max_len else s) or 'document'

    def _uploaded_by_id(fo):
        """Resolve integer user ID for uploaded_by; fo.user_id may be username string."""
        if fo.user_id and str(fo.user_id).strip().isdigit():
            return int(fo.user_id)
        return default_uploader_id

    document_ids = []
    for fo in file_ops:
        try:
            ext_id_str = str(fo.id)
            # Decrypt in case FileOperations stores file_name/s3_key encrypted (so UI and report show readable names)
            raw_name = fo.file_name or fo.original_name or 'document'
            raw_path = fo.s3_key or fo.s3_url or ''
            doc_name = _truncate((decrypt_any_encrypted_value(raw_name) if isinstance(raw_name, str) else raw_name) or 'document')
            doc_path = _truncate((decrypt_any_encrypted_value(raw_path) if isinstance(raw_path, str) else raw_path) or '', max_len=500)
            with connection.cursor() as cursor:
                # Upsert: use existing row if audit_id + external_source + external_id match (avoid duplicates)
                cursor.execute(
                    """
                    SELECT id FROM ai_audit_data
                    WHERE audit_id = %s AND external_source = 'evidence_attachment' AND external_id = %s
                    LIMIT 1
                    """,
                    [int(audit_id), ext_id_str]
                )
                existing = cursor.fetchone()
                if existing:
                    document_ids.append(existing[0])
                    continue
                cursor.execute(
                    """
                    INSERT INTO ai_audit_data
                    (audit_id, document_id, document_name, document_path, document_type, file_size, mime_type,
                     uploaded_by, ai_processing_status, uploaded_date, policy_id, subpolicy_id,
                     external_source, external_id, FrameworkId)
                    VALUES (%s, 0, %s, %s, %s, %s, %s, %s, 'pending', NOW(), %s, %s, 'evidence_attachment', %s, %s)
                    """,
                    [
                        int(audit_id),
                        doc_name,
                        doc_path,
                        fo.file_type or 'file',
                        fo.file_size or 0,
                        fo.content_type or 'application/octet-stream',
                        _uploaded_by_id(fo),
                        policy_id,
                        subpolicy_id,
                        ext_id_str,
                        framework_id,
                    ]
                )
                cursor.execute("SELECT LAST_INSERT_ID()")
                rid = cursor.fetchone()[0]
                cursor.execute("UPDATE ai_audit_data SET document_id = %s WHERE id = %s", [rid, rid])
                document_ids.append(rid)
        except Exception as e:
            logger.warning("Failed to upsert ai_audit_data for file_op %s: %s", fo.id, e)
    return document_ids, None


def _cleanup_document_handling_evidence(inserted_ids):
    """Remove temporary ai_audit_data rows created for scheduled DH run."""
    if not inserted_ids:
        return
    try:
        with connection.cursor() as cursor:
            placeholders = ','.join(['%s'] * len(inserted_ids))
            cursor.execute(
                f"DELETE FROM ai_audit_data WHERE id IN ({placeholders})",
                inserted_ids
            )
    except Exception as e:
        logger.warning("Failed to cleanup ai_audit_data: %s", e)


def _run_scheduled_audit(schedule):
    """Execute the AI audit for a schedule using the same per-document check as on-demand (Check button)."""
    from grc.tenant_context import set_current_tenant
    from grc.routes.Audit.ai_audit_api import _check_document_compliance_internal
    from grc.routes.Audit.ai_audit_api import check_and_update_ai_audit_status

    audit_id = schedule.audit_id
    tenant_id = schedule.tenant_id if schedule.tenant_id else None
    user_id = schedule.created_by_id if schedule.created_by_id else None

    # Set tenant context for multi-tenancy
    if tenant_id:
        set_current_tenant(tenant_id)

    document_ids_to_cleanup = []  # Only used for legacy paths; DH docs are kept (no cleanup)
    company_folder_id = schedule.company_folder_id if hasattr(schedule, 'company_folder_id') else None

    # Document Handling path: use ONLY docs from company folder (framework+company); upsert, keep in ai_audit_data
    if company_folder_id:
        document_ids, err = _ensure_document_handling_evidence(schedule)
        if err:
            return {'success': False, 'error': err}
        logger.info("Schedule %s: processing %d document(s) from company folder only (not entire audit)", schedule.id, len(document_ids))
        # Use selected scope if set; otherwise all framework compliances
        selected_ids = getattr(schedule, 'selected_compliance_ids', None)
        if selected_ids and len(selected_ids) > 0:
            compliance_ids = [int(x) for x in selected_ids]
        else:
            compliance_ids = _get_compliance_ids_from_framework(audit_id)
    else:
        # Live evidences: get documents from ai_audit_data, use selected scope or from data
        document_ids = _get_document_ids_for_audit(audit_id)
        selected_ids = getattr(schedule, 'selected_compliance_ids', None)
        if selected_ids and len(selected_ids) > 0:
            compliance_ids = [int(x) for x in selected_ids]
        else:
            compliance_ids = _get_compliance_ids_for_audit(audit_id)

    if not compliance_ids:
        _cleanup_document_handling_evidence(document_ids_to_cleanup)
        return {'success': False, 'error': 'No compliance requirements found for this audit'}

    if not document_ids:
        _cleanup_document_handling_evidence(document_ids_to_cleanup)
        return {'success': False, 'error': 'No documents found for this audit'}

    # Build evidence snapshot from the documents selected for this schedule run (before we run checks).
    # This shows "these are the evidences for this run" — the same set chosen at schedule time, not after the run.
    evidence_snapshot = []
    try:
        from grc.routes.Audit.ai_audit_api import _check_ai_audit_data_has_compliance_id
        has_compliance_id = _check_ai_audit_data_has_compliance_id()
        id_list = [int(x) for x in document_ids]
        with connection.cursor() as cursor:
            placeholders = ','.join(['%s'] * len(id_list))
            if has_compliance_id:
                cols = "id, document_id, document_name, document_type, policy_id, subpolicy_id, compliance_id"
            else:
                cols = "id, document_id, document_name, document_type, policy_id, subpolicy_id"
            if company_folder_id:
                cursor.execute(
                    f"SELECT {cols} FROM ai_audit_data WHERE audit_id = %s AND id IN ({placeholders})",
                    [int(audit_id)] + id_list,
                )
            else:
                cursor.execute(
                    f"SELECT {cols} FROM ai_audit_data WHERE audit_id = %s AND document_id IN ({placeholders})",
                    [int(audit_id)] + id_list,
                )
            rows = cursor.fetchall()
            for row in rows:
                evidence_snapshot.append({
                    'ai_audit_data_id': int(row[0]) if row[0] is not None else None,
                    'document_id': int(row[1]) if row[1] is not None else None,
                    'document_name': str(row[2]) if row[2] is not None else None,
                    'document_type': str(row[3]) if row[3] is not None else None,
                    'policy_id': int(row[4]) if row[4] is not None else None,
                    'subpolicy_id': int(row[5]) if row[5] is not None else None,
                    'compliance_id': int(row[6]) if (has_compliance_id and len(row) > 6 and row[6] is not None) else None,
                })
            if rows:
                logger.info(
                    "Evidence snapshot (schedule scope) schedule_id=%s audit_id=%s docs=%d",
                    schedule.id, audit_id, len(evidence_snapshot),
                )
            else:
                logger.warning(
                    "Evidence snapshot empty at run start: schedule_id=%s audit_id=%s company_folder=%s id_list=%s",
                    schedule.id, audit_id, bool(company_folder_id), id_list[:10],
                )
    except Exception as e:
        logger.warning("Could not build evidence_snapshot at run start for schedule %s: %s", schedule.id, e)
        evidence_snapshot = []

    try:
        # Use the same per-document check as on-demand (Check button) so results and persistence are identical
        success_count = 0
        failed = []
        for doc_id in document_ids:
            result = _check_document_compliance_internal(
                audit_id=audit_id,
                document_id=doc_id,
                user_id=user_id,
                selected_compliance_ids=compliance_ids
            )
            if result.get('success'):
                success_count += 1
            else:
                failed.append({'document_id': doc_id, 'error': result.get('error', 'Unknown')})
        overall_success = success_count > 0  # Same as on-demand: success if at least one document checked
        if success_count > 0:
            try:
                check_and_update_ai_audit_status(audit_id)
            except Exception as e:
                logger.warning("Could not update AI audit status after check: %s", e)

        # evidence_snapshot was built at run start from the schedule's selected documents (see above)
        return {
            'success': overall_success,
            'documents_checked': len(document_ids),
            'succeeded': success_count,
            'failed': failed,
            'error': None if overall_success else (failed[0].get('error') if failed else 'No document succeeded'),
            # Historical evidence (read-only) for this run; UI can use last N runs.
            'evidence_snapshot': evidence_snapshot,
        }
    except Exception as e:
        logger.exception("Error running scheduled AI audit %s: %s", schedule.id, e)
        return {'success': False, 'error': str(e)}
    finally:
        _cleanup_document_handling_evidence(document_ids_to_cleanup)


class Command(BaseCommand):
    help = "Run scheduled AI audits (due schedules). Add to crontab: * * * * * python manage.py run_scheduled_ai_audits"

    def handle(self, *args, **options):
        from django.db.models import Exists, OuterRef
        from datetime import timedelta

        now = timezone.now()
        # Exclude schedules that have an active (running) run - prevents concurrent processing
        stale_threshold = now - timedelta(minutes=30)
        running_run = AIAuditScheduleRun.objects.filter(
            schedule_id=OuterRef('pk'),
            status='running',
            started_at__gte=stale_threshold,
        )
        schedules = AIAuditSchedule.objects.filter(
            is_active=True,
            next_run_at__lte=now,
            next_run_at__isnull=False
        ).exclude(Exists(running_run)).select_related('audit', 'tenant', 'created_by', 'company_folder')

        count = schedules.count()
        if count == 0:
            logger.debug("No scheduled AI audits due.")
            return

        self.stdout.write(f"Running {count} scheduled AI audit(s)...")

        for schedule in schedules:
            run_record = AIAuditScheduleRun.objects.create(
                schedule=schedule,
                started_at=now,
                status='running'
            )
            try:
                result = _run_scheduled_audit(schedule)
                run_record.finished_at = timezone.now()
                run_record.status = 'success' if result.get('success') else 'failed'
                run_record.result_summary = result
                if not result.get('success'):
                    run_record.error_message = result.get('error', 'Unknown error')
            except Exception as e:
                run_record.finished_at = timezone.now()
                run_record.status = 'failed'
                run_record.error_message = str(e)
                run_record.result_summary = {'success': False, 'error': str(e)}
                logger.exception("Scheduled audit %s failed: %s", schedule.id, e)
            run_record.save()

            # Update schedule
            schedule.last_run_at = now
            if schedule.schedule_type in ('recurring', 'daily', 'monthly', 'every_minute'):
                schedule.next_run_at = _compute_next_run(schedule)
            else:
                # one_week, one_minute, exact_date - run once, deactivate
                schedule.next_run_at = None
                schedule.is_active = False
            schedule.save()

            self.stdout.write(
                self.style.SUCCESS(f"  Schedule {schedule.id} (audit {schedule.audit_id}): {run_record.status}")
            )

        self.stdout.write(self.style.SUCCESS(f"Completed {count} scheduled AI audit(s)."))
