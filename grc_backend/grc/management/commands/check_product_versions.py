import json
from django.core.management.base import BaseCommand
from grc.models import ProductVersion


class Command(BaseCommand):
    help = "Show latest and minimum supported product versions for patch/token enforcement"

    def handle(self, *args, **options):
        latest = ProductVersion.get_latest()
        min_supported = ProductVersion.get_min_supported()

        data = {
            "latest_version": latest.version if latest else None,
            "latest_status": latest.status if latest else None,
            "latest_release_date": latest.release_date.isoformat() if latest and latest.release_date else None,
            "min_supported_version": min_supported.version if min_supported else None,
            "min_supported_status": min_supported.status if min_supported else None,
            "min_supported_release_date": min_supported.release_date.isoformat() if min_supported and min_supported.release_date else None,
        }

        self.stdout.write(json.dumps(data, indent=2))








