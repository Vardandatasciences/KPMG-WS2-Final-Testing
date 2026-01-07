"""
Django Management Command: Encrypt Existing Data
Encrypts all existing plain text data in the database for configured fields.

Usage:
    python manage.py encrypt_existing_data
    python manage.py encrypt_existing_data --model Users --field Email
    python manage.py encrypt_existing_data --dry-run  # Preview changes without saving
"""

import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps
from grc.utils.encryption_config import get_encrypted_fields_for_model
from grc.utils.data_encryption import encrypt_data, is_encrypted_data

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Encrypt existing plain text data in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Specific model to encrypt (e.g., Users, Policy)',
        )
        parser.add_argument(
            '--field',
            type=str,
            help='Specific field to encrypt (requires --model)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving to database',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process at once (default: 100)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-encrypt already encrypted fields',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        force = options['force']
        model_name = options.get('model')
        field_name = options.get('field')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        # Get all models or specific model
        if model_name:
            try:
                model = apps.get_model('grc', model_name)
                models_to_process = [model]
            except LookupError:
                self.stdout.write(self.style.ERROR(f'Model {model_name} not found'))
                return
        else:
            # Get all models from grc app
            models_to_process = apps.get_app_config('grc').get_models()

        total_encrypted = 0
        total_skipped = 0
        total_errors = 0

        for model in models_to_process:
            model_name = model.__name__
            encrypted_fields = get_encrypted_fields_for_model(model_name)

            if not encrypted_fields:
                continue

            if field_name:
                if field_name not in encrypted_fields:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Field {field_name} is not configured for encryption in {model_name}'
                        )
                    )
                    continue
                encrypted_fields = [field_name]

            self.stdout.write(f'\nProcessing {model_name}...')

            try:
                # Get all instances
                queryset = model.objects.all()
                total_count = queryset.count()

                if total_count == 0:
                    self.stdout.write(f'  No records found')
                    continue

                self.stdout.write(f'  Found {total_count} records')

                # Process in batches
                for offset in range(0, total_count, batch_size):
                    batch = queryset[offset:offset + batch_size]
                    batch_encrypted = 0
                    batch_skipped = 0
                    batch_errors = 0

                    for instance in batch:
                        instance_updated = False

                        for field_name in encrypted_fields:
                            try:
                                if not hasattr(instance, field_name):
                                    continue

                                field_value = getattr(instance, field_name)

                                # Skip None, empty, or already encrypted (unless force)
                                if not field_value or field_value == '':
                                    continue

                                if is_encrypted_data(field_value) and not force:
                                    batch_skipped += 1
                                    continue

                                # Convert to string if needed
                                if not isinstance(field_value, str):
                                    if isinstance(field_value, (dict, list)):
                                        import json
                                        field_value = json.dumps(field_value)
                                    else:
                                        field_value = str(field_value)

                                # Encrypt
                                encrypted_value = encrypt_data(field_value)

                                if encrypted_value and encrypted_value != field_value:
                                    setattr(instance, field_name, encrypted_value)
                                    instance_updated = True

                            except Exception as e:
                                logger.error(f'Error encrypting {field_name} for {model_name} #{instance.pk}: {str(e)}')
                                batch_errors += 1

                        if instance_updated and not dry_run:
                            try:
                                # Save only the encrypted fields to avoid triggering other save logic
                                instance.save(update_fields=encrypted_fields)
                                batch_encrypted += 1
                            except Exception as e:
                                logger.error(f'Error saving {model_name} #{instance.pk}: {str(e)}')
                                batch_errors += 1
                        elif instance_updated:
                            batch_encrypted += 1

                    total_encrypted += batch_encrypted
                    total_skipped += batch_skipped
                    total_errors += batch_errors

                    if batch_encrypted > 0:
                        self.stdout.write(
                            f'  Batch {offset // batch_size + 1}: '
                            f'{batch_encrypted} encrypted, {batch_skipped} skipped, {batch_errors} errors'
                        )

                if not dry_run:
                    # Commit transaction after each model
                    transaction.commit()

            except Exception as e:
                logger.error(f'Error processing {model_name}: {str(e)}')
                self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))
                total_errors += 1

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('ENCRYPTION SUMMARY')
        self.stdout.write('=' * 60)
        self.stdout.write(f'Total encrypted: {total_encrypted}')
        self.stdout.write(f'Total skipped: {total_skipped}')
        self.stdout.write(f'Total errors: {total_errors}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nThis was a DRY RUN - no changes were saved'))
        else:
            self.stdout.write(self.style.SUCCESS('\nEncryption completed!'))


