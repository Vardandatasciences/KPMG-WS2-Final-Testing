"""
Background scheduler for AI audit schedules.
Runs inside Django - checks every 60 seconds if any scheduled audits are due.
No cron or Task Scheduler needed.
"""
import logging
import sys
import threading
import time

logger = logging.getLogger(__name__)

_scheduler_started = False


def _run_check():
    """Run the scheduled AI audits check (same logic as management command)."""
    try:
        from django.db import connection
        from django.db import close_old_connections
        from django.utils import timezone

        close_old_connections()

        from grc.models import AIAuditSchedule, AIAuditScheduleRun
        from grc.management.commands.run_scheduled_ai_audits import (
            _compute_next_run,
            _run_scheduled_audit,
        )

        now = timezone.now()
        from datetime import timedelta
        from django.db.models import Exists, OuterRef
        stale_threshold = now - timedelta(minutes=30)
        # Mark stale "running" runs as failed so they don't block forever
        AIAuditScheduleRun.objects.filter(
            status='running', started_at__lt=stale_threshold
        ).update(status='failed', finished_at=now, error_message='Run timed out or was interrupted')
        # Exclude schedules that have an active (running) run - prevents concurrent processing
        running_run = AIAuditScheduleRun.objects.filter(
            schedule_id=OuterRef('pk'),
            status='running',
            started_at__gte=stale_threshold,
        )
        # Defer fields whose columns may not exist in DB (schema drift).
        qs = (
            AIAuditSchedule.objects.filter(
                is_active=True,
                next_run_at__lte=now,
                next_run_at__isnull=False,
            ).exclude(Exists(running_run))
            .select_related('audit', 'tenant', 'created_by', 'company_folder')
            .defer('company_subfolder_id', 'start_date')
        )
        schedules = list(qs)
        for s in schedules:
            if s.get_deferred_fields():
                s.company_subfolder_id = None

        if not schedules:
            return

        logger.info("Running %d scheduled AI audit(s)...", len(schedules))

        for schedule in schedules:
            run_record = AIAuditScheduleRun.objects.create(
                schedule=schedule,
                started_at=now,
                status='running',
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

            schedule.last_run_at = now
            if schedule.schedule_type in ('recurring', 'daily', 'monthly', 'every_minute', 'cron'):
                schedule.next_run_at = _compute_next_run(schedule)
            else:
                schedule.next_run_at = None
                schedule.is_active = False
            schedule.save(update_fields=['last_run_at', 'next_run_at', 'is_active'])

            logger.info("Schedule %s (audit %s): %s", schedule.id, schedule.audit_id, run_record.status)

    except Exception as e:
        logger.exception("Scheduled audit runner check failed: %s", e)


def _scheduler_loop():
    """Background loop: wait 60 seconds, run check, repeat."""
    while True:
        time.sleep(60)
        try:
            _run_check()
        except Exception as e:
            logger.exception("Scheduler loop error: %s", e)


def start_scheduler():
    """Start the background scheduler thread (only when running the web server)."""
    global _scheduler_started
    if _scheduler_started:
        return

    skip_commands = [
        'migrate', 'makemigrations', 'test', 'shell', 'createsuperuser',
        'collectstatic', 'flush', 'loaddata', 'dumpdata', 'run_scheduled_ai_audits',
    ]
    if len(sys.argv) > 1 and sys.argv[1] in skip_commands:
        return

    _scheduler_started = True
    thread = threading.Thread(target=_scheduler_loop, daemon=True, name='ScheduledAuditRunner')
    thread.start()
    logger.info("Scheduled AI audit runner started (checks every 60 seconds)")
