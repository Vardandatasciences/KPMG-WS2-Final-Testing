"""
Management app configuration.

On startup, launches a background daemon thread that polls the
screening_schedules table every POLL_INTERVAL_SECONDS and executes
any due schedules.  This removes the need for an external cron job
or Celery Beat on the development machine.
"""

import logging
import threading
import datetime

from django.apps import AppConfig

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 60  # check every 60 seconds


def _run_due_schedules():
    """
    Core screening-schedule runner.  Imported lazily (inside the thread)
    so Django is fully initialised before we touch the ORM.
    """
    from django import db
    db.close_old_connections()
    try:
        from tprm_backend.apps.management.models import ScreeningSchedule
        from tprm_backend.apps.management.views import (
            TempVendorManagementViewSet,
            _get_next_run_from_cron,
        )

        now = datetime.datetime.now()
        due = list(
            ScreeningSchedule.objects.select_related('temp_vendor').filter(
                is_active=True,
                next_run_at__isnull=False,
                next_run_at__lte=now,
            )
        )

        if not due:
            return

        logger.info('[ScreeningScheduler] %d schedule(s) due — running now', len(due))

        for schedule in due:
            vendor = schedule.temp_vendor
            if not vendor:
                schedule.is_active = False
                schedule.status = 'completed'
                schedule.save(update_fields=['is_active', 'status', 'updated_at'])
                continue

            try:
                viewset = TempVendorManagementViewSet()
                results = viewset._perform_automatic_screening(vendor)
                run_status = 'ok'
                logger.info(
                    '[ScreeningScheduler] Screened %s — %d type(s)',
                    vendor.company_name, len(results) if results else 0,
                )
            except Exception as exc:
                run_status = f'error: {exc}'[:32]
                logger.exception(
                    '[ScreeningScheduler] Error screening %s (schedule %s): %s',
                    vendor.company_name, schedule.id, exc,
                )

            # Advance or complete
            schedule.last_run_at = now
            schedule.last_run_status = run_status

            if schedule.frequency == 'does_not_repeat':
                schedule.is_active = False
                schedule.status = 'completed'
                schedule.next_run_at = None
            elif schedule.cron_expression:
                nxt = _get_next_run_from_cron(schedule.cron_expression, now)
                if nxt:
                    schedule.next_run_at = nxt
                else:
                    schedule.is_active = False
                    schedule.status = 'completed'
            else:
                schedule.is_active = False
                schedule.status = 'completed'

            schedule.save(update_fields=[
                'last_run_at', 'last_run_status',
                'is_active', 'status', 'next_run_at', 'updated_at',
            ])

    except Exception as exc:
        logger.exception('[ScreeningScheduler] Unexpected error: %s', exc)


def _scheduler_loop():
    """Daemon thread: poll every POLL_INTERVAL_SECONDS."""
    logger.info(
        '[ScreeningScheduler] Background scheduler started — polling every %ds',
        POLL_INTERVAL_SECONDS,
    )
    while True:
        try:
            _run_due_schedules()
        except Exception as exc:
            logger.exception('[ScreeningScheduler] Loop error: %s', exc)
        # Sleep in small increments so the thread exits cleanly on shutdown
        for _ in range(POLL_INTERVAL_SECONDS):
            threading.Event().wait(1)


class ManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.apps.management'
    verbose_name = 'Management'

    def ready(self):
        """Start the background screening scheduler once on server startup.

        Django's dev-server reloader forks two processes:
          - parent (watcher): RUN_MAIN is not set
          - child  (worker):  RUN_MAIN = 'true'

        In production (gunicorn / uwsgi) RUN_MAIN is also not set, but there
        is no parent watcher process.

        Strategy: start the thread when we are the child worker OR when we are
        running outside the auto-reloader (production / manage.py shell).
        """
        import os
        import sys

        is_runserver = 'runserver' in sys.argv
        run_main = os.environ.get('RUN_MAIN') == 'true'

        # Skip only the reloader *parent* process
        if is_runserver and not run_main:
            return  # parent watcher process — child will pick this up

        t = threading.Thread(target=_scheduler_loop, daemon=True, name='ScreeningScheduler')
        t.start()
        logger.info('[ScreeningScheduler] Daemon thread started (pid=%s)', os.getpid())
