"""
Backfill DocumentLink in company_subfolder_documents from file_operations.s3_url.
Run manually when you want to populate DocumentLink for existing rows (no migration needed).

  python manage.py backfill_document_links
"""

from django.core.management.base import BaseCommand
from django.db.models import Q

from grc.models import CompanySubfolderDocument


class Command(BaseCommand):
    help = (
        "Backfill DocumentLink in company_subfolder_documents from file_operations.s3_url. "
        "Run when you want to populate DocumentLink for existing rows (no migration)."
    )

    def handle(self, *args, **options):
        qs = CompanySubfolderDocument.objects.filter(
            Q(document_link='') | Q(document_link__isnull=True)
        )
        updated = 0
        for csd in qs:
            try:
                fo = csd.file_operation
                if fo and getattr(fo, 's3_url', None):
                    csd.document_link = fo.s3_url or ''
                    csd.save(update_fields=['document_link'])
                    updated += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Skip id={csd.pk}: {e}"))
        self.stdout.write(
            self.style.SUCCESS(f"Backfilled DocumentLink for {updated} row(s).")
        )