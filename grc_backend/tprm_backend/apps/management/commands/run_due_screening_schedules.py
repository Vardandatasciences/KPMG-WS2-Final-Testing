"""
Run due screening schedules: execute external screening for every
ScreeningSchedule whose next_run_at is <= now and is_active=True.

After each run:
  - One-time schedules  → mark is_active=False, status='completed'
  - Recurring schedules → advance next_run_at via croniter, keep active

Usage:
  python manage.py run_due_screening_schedules
  python manage.py run_due_screening_schedules --dry-run
"""

import logging
from datetime import datetime

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


def _get_next_run_from_cron(cron_expression, after_dt):
    """Return the next naive datetime for a cron expression.

    USE_TZ = False — always work with naive datetimes so MySQL accepts them.
    """
    try:
        from croniter import croniter
        # Ensure base is naive
        naive_base = after_dt.replace(tzinfo=None) if getattr(after_dt, 'tzinfo', None) else after_dt
        it = croniter(cron_expression, naive_base)
        return it.get_next(datetime)
    except Exception as exc:
        logger.warning('_get_next_run_from_cron failed for %r: %s', cron_expression, exc)
        return None


class Command(BaseCommand):
    help = 'Execute due external screening schedules and update next_run_at'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List due schedules without executing them',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        from tprm_backend.apps.management.models import ScreeningSchedule
        from tprm_backend.apps.management.views import TempVendorManagementViewSet

        now = datetime.now()

        due = list(
            ScreeningSchedule.objects.select_related('temp_vendor').filter(
                is_active=True,
                next_run_at__isnull=False,
                next_run_at__lte=now,
            )
        )

        if not due:
            self.stdout.write('No screening schedules due.')
            return

        self.stdout.write(f'Processing {len(due)} due schedule(s).')
        ran = 0

        for schedule in due:
            vendor = schedule.temp_vendor
            if not vendor:
                self.stdout.write(
                    self.style.WARNING(
                        f'Schedule {schedule.id}: vendor not found, deactivating.'
                    )
                )
                schedule.is_active = False
                schedule.status = 'completed'
                if not dry_run:
                    schedule.save(update_fields=['is_active', 'status', 'updated_at'])
                continue

            if dry_run:
                self.stdout.write(
                    f'[DRY-RUN] Would run screening for vendor '
                    f'{vendor.company_name} (schedule {schedule.id}, '
                    f'freq={schedule.frequency})'
                )
                ran += 1
                continue

            # ---- Execute screening ----
            try:
                viewset = TempVendorManagementViewSet()
                results = viewset._perform_automatic_screening(vendor)
                run_status = 'ok'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Schedule {schedule.id}: screened {vendor.company_name}, '
                        f'{len(results) if results else 0} type(s).'
                    )
                )
            except Exception as exc:
                logger.exception(
                    'run_due_screening_schedules: error screening vendor %s (schedule %s): %s',
                    vendor.id, schedule.id, exc,
                )
                run_status = f'error: {exc}'
                self.stdout.write(
                    self.style.ERROR(
                        f'Schedule {schedule.id}: error – {exc}'
                    )
                )

            # ---- Advance or complete schedule ----
            schedule.last_run_at = now
            schedule.last_run_status = run_status[:32]

            if schedule.frequency == 'does_not_repeat':
                # One-time → mark done
                schedule.is_active = False
                schedule.status = 'completed'
                schedule.next_run_at = None
            elif schedule.cron_expression:
                # Recurring → compute next run
                next_run = _get_next_run_from_cron(schedule.cron_expression, now)
                if next_run:
                    # next_run is always naive (USE_TZ=False) — store directly
                    schedule.next_run_at = next_run
                else:
                    # Couldn't compute – deactivate to avoid infinite loop
                    schedule.is_active = False
                    schedule.status = 'completed'
                    logger.warning(
                        'Could not compute next_run_at for schedule %s; deactivating.',
                        schedule.id,
                    )
            else:
                # No cron expression for a recurring schedule – deactivate
                schedule.is_active = False
                schedule.status = 'completed'

            schedule.save(update_fields=[
                'last_run_at', 'last_run_status',
                'is_active', 'status', 'next_run_at', 'updated_at',
            ])
            ran += 1

        self.stdout.write(self.style.SUCCESS(f'Processed {ran} schedule(s).'))
