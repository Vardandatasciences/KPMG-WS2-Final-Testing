"""
Run scheduled questionnaire assignments: create QuestionnaireAssignments and send emails
when QuestionnaireAssignmentSchedule.next_run_at is due. For one-time schedules, deactivate
after run; for recurring (cron), compute next_run_at and update.

Usage:
  python manage.py run_scheduled_questionnaire_assignments
  python manage.py run_scheduled_questionnaire_assignments --dry-run
"""

import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_next_run_from_cron(cron_expression, after_dt):
    try:
        from croniter import croniter
        it = croniter(cron_expression, after_dt)
        return it.get_next(datetime)
    except Exception:
        return None


class Command(BaseCommand):
    help = 'Create questionnaire assignments from due schedules and send emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only list what would be run, do not create or send',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        from tprm_backend.apps.vendor_questionnaire.models import (
            QuestionnaireAssignmentSchedule,
            QuestionnaireAssignments,
            Questionnaires,
        )
        from tprm_backend.apps.vendor_core.models import TempVendor
        from tprm_backend.apps.vendor_questionnaire.views import (
            QuestionnaireAssignmentViewSet,
            send_assignment_notification_email,
        )

        now = timezone.now()
        due = list(
            QuestionnaireAssignmentSchedule.objects.filter(
                is_active=True,
                next_run_at__isnull=False,
                next_run_at__lte=now,
            ).select_related('questionnaire', 'temp_vendor', 'created_by')
        )
        if not due:
            if not dry_run:
                self.stdout.write('No scheduled questionnaire assignments due.')
            return

        self.stdout.write(f'Processing {len(due)} due schedule(s).')
        created = 0
        for schedule in due:
            try:
                questionnaire = schedule.questionnaire
                vendor = schedule.temp_vendor
                existing = QuestionnaireAssignments.objects.filter(
                    temp_vendor=vendor,
                    questionnaire=questionnaire,
                ).first()
                if existing:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping schedule {schedule.id}: assignment already exists for '
                            f'{vendor.company_name} / {questionnaire.questionnaire_name}'
                        )
                    )
                    if schedule.scheduled_at and not schedule.cron_expression:
                        schedule.is_active = False
                        schedule.save(update_fields=['is_active', 'updated_at'])
                    elif schedule.cron_expression:
                        next_run = get_next_run_from_cron(schedule.cron_expression, now)
                        if next_run and timezone.is_naive(next_run):
                            next_run = timezone.make_aware(next_run)
                        schedule.next_run_at = next_run
                        schedule.save(update_fields=['next_run_at', 'updated_at'])
                    continue

                if dry_run:
                    self.stdout.write(
                        f'[DRY-RUN] Would create assignment: {vendor.company_name} <- {questionnaire.questionnaire_name}'
                    )
                    created += 1
                    continue

                with transaction.atomic():
                    assigned_by_id = schedule.created_by_id or 1
                    assignment = QuestionnaireAssignments.objects.create(
                        temp_vendor=vendor,
                        questionnaire=questionnaire,
                        due_date=schedule.due_date,
                        notes=schedule.notes or '',
                        assigned_by_id=assigned_by_id,
                    )
                    created += 1

                    viewset = QuestionnaireAssignmentViewSet()
                    viewset._start_questionnaire_response_stage(vendor.id)

                    from django.conf import settings as django_settings
                    base_url = getattr(django_settings, 'PUBLIC_QUESTIONNAIRE_BASE_URL', 'http://localhost:3000').rstrip('/')
                    tprm_path = getattr(django_settings, 'PUBLIC_QUESTIONNAIRE_PATH', '/tprm/questionnaire-response-public')
                    from urllib.parse import urlencode
                    params = {
                        'assignmentId': str(assignment.assignment_id),
                        'vendorId': str(vendor.id),
                        'questionnaireId': str(questionnaire.questionnaire_id),
                    }
                    response_link = f"{base_url}{tprm_path}?{urlencode(params)}"
                    try:
                        send_assignment_notification_email(assignment, response_link)
                    except Exception as e:
                        logger.exception('Failed to send schedule assignment email: %s', e)

                    if schedule.scheduled_at and not schedule.cron_expression:
                        schedule.is_active = False
                        schedule.save(update_fields=['is_active', 'updated_at'])
                    elif schedule.cron_expression:
                        next_run = get_next_run_from_cron(schedule.cron_expression, now)
                        if next_run:
                            if timezone.is_naive(next_run):
                                next_run = timezone.make_aware(next_run)
                            schedule.next_run_at = next_run
                            schedule.save(update_fields=['next_run_at', 'updated_at'])
                        else:
                            schedule.is_active = False
                            schedule.save(update_fields=['is_active', 'updated_at'])

            except Exception as e:
                logger.exception('Error processing schedule %s: %s', schedule.id, e)
                self.stdout.write(self.style.ERROR(f'Schedule {schedule.id}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Created {created} assignment(s).'))
