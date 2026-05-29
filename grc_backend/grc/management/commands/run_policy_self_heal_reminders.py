"""Run policy self-healing reminders (same logic as POST /api/policies/self-healing/reminders/run/)."""
from django.core.management.base import BaseCommand

from grc.routes.Policy.policy_self_healing import execute_policy_self_heal_reminders


class Command(BaseCommand):
    help = "Send policy review reminders to creators (frequency + final week). For cron without the scheduler microservice."

    def handle(self, *args, **options):
        result = execute_policy_self_heal_reminders()
        self.stdout.write(self.style.SUCCESS(str(result)))
