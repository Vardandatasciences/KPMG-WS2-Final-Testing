"""
Management command to update expired SLAs.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tprm_backend.slas.models import VendorSLA
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update SLA status to EXPIRED for SLAs that have passed their expiry date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        today = timezone.now().date()
        
        # Find SLAs that are expired but not marked as EXPIRED
        expired_slas = VendorSLA.objects.filter(
            expiry_date__lt=today,
            status__in=['ACTIVE', 'PENDING']
        ).select_related('vendor', 'contract')
        
        if verbose:
            self.stdout.write(f"Found {expired_slas.count()} SLAs that need to be marked as expired")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would update {expired_slas.count()} SLAs to EXPIRED status")
            )
            for sla in expired_slas:
                self.stdout.write(f"  - {sla.sla_name} (ID: {sla.sla_id}) - Expired on {sla.expiry_date}")
        else:
            updated_count = 0
            for sla in expired_slas:
                try:
                    if sla.update_status_if_expired():
                        updated_count += 1
                        if verbose:
                            self.stdout.write(
                                f"Updated {sla.sla_name} (ID: {sla.sla_id}) to EXPIRED status"
                            )
                        logger.info(f"SLA {sla.sla_id} ({sla.sla_name}) marked as EXPIRED")
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error updating SLA {sla.sla_id}: {str(e)}")
                    )
                    logger.error(f"Error updating SLA {sla.sla_id}: {str(e)}")
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully updated {updated_count} SLAs to EXPIRED status")
            )
        
        # Also check for SLAs that should be marked as ACTIVE (if they have a future effective date)
        future_slas = VendorSLA.objects.filter(
            effective_date__lte=today,
            expiry_date__gte=today,
            status='PENDING'
        )
        
        if verbose and future_slas.exists():
            self.stdout.write(f"Found {future_slas.count()} SLAs that should be marked as ACTIVE")
        
        if not dry_run and future_slas.exists():
            active_count = 0
            for sla in future_slas:
                try:
                    sla.status = 'ACTIVE'
                    sla.save(update_fields=['status'])
                    active_count += 1
                    if verbose:
                        self.stdout.write(
                            f"Updated {sla.sla_name} (ID: {sla.sla_id}) to ACTIVE status"
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error updating SLA {sla.sla_id}: {str(e)}")
                    )
            
            if active_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully updated {active_count} SLAs to ACTIVE status")
                )
