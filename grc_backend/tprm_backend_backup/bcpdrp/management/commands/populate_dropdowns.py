"""
Management command to populate dropdown table with sample data
"""
from django.core.management.base import BaseCommand
from tprm_backend.bcpdrp.models import Dropdown


class Command(BaseCommand):
    help = 'Populate dropdown table with sample data'

    def handle(self, *args, **options):
        # Sample plan_scope values
        plan_scope_values = [
            'cloud',
            'physical_server',
            'physical_device',
            'application',
            'network',
            'other'
        ]

        # Create dropdown entries for plan_scope
        created_count = 0
        for value in plan_scope_values:
            dropdown, created = Dropdown.objects.get_or_create(
                source='plan_scope',
                value=value,
                defaults={'source': 'plan_scope', 'value': value}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created dropdown: {dropdown}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Dropdown already exists: {dropdown}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new dropdown entries')
        )
