from django.core.management.base import BaseCommand
from django.conf import settings

from tprm_backend.apps.vendor_core.services import OFACService


class Command(BaseCommand):
    help = "Test OFAC API connectivity using OFACService (v4 search)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            default="Test",
            help="Entity name to search (default: Test).",
        )
        parser.add_argument(
            "--sources",
            default="SDN",
            help='Comma-separated sources (default: "SDN"). Example: "SDN,UK,EU".',
        )
        parser.add_argument(
            "--show-raw",
            action="store_true",
            help="Print the raw response payload (use carefully).",
        )

    def handle(self, *args, **options):
        name = (options.get("name") or "Test").strip()
        sources = [s.strip() for s in (options.get("sources") or "SDN").split(",") if s.strip()]
        show_raw = bool(options.get("show_raw"))

        self.stdout.write("=== OFAC API Test ===")
        self.stdout.write(f"OFAC_API_BASE_URL: {getattr(settings, 'OFAC_API_BASE_URL', '')}")

        key = getattr(settings, "OFAC_API_KEY", "") or ""
        if not key:
            self.stdout.write(self.style.ERROR("OFAC_API_KEY is NOT set. Add it to grc_backend/.env and restart server."))
            return

        # Don't print the full key
        self.stdout.write(f"OFAC_API_KEY: set (len={len(key)})")

        service = OFACService()
        # Exercise the v4 endpoint via search_entity
        result = service.search_entity(name, case_id="cli-test", sources=sources)

        if result.get("error"):
            self.stdout.write(self.style.ERROR(f"FAILED: {result.get('error')}"))
            if show_raw:
                self.stdout.write(f"Raw result: {result}")
            return

        matches = result.get("matches", [])
        self.stdout.write(self.style.SUCCESS("SUCCESS: Live OFAC API call completed."))
        self.stdout.write(f"Matches returned: {len(matches)}")
        if show_raw:
            # Avoid printing api keys (none should be present), but print the structure for debugging
            self.stdout.write(f"Raw result keys: {list(result.keys())}")
            if "results" in result:
                self.stdout.write(f"Raw results count: {len(result.get('results') or [])}")
                if result.get("results"):
                    self.stdout.write(f"First result keys: {list((result.get('results') or [{}])[0].keys())}")
        if matches:
            first = matches[0]
            self.stdout.write("First match summary:")
            self.stdout.write(f"  id: {first.get('id')}")
            self.stdout.write(f"  name: {first.get('name')}")
            self.stdout.write(f"  source: {first.get('source')}")
            self.stdout.write(f"  score: {first.get('score')}")

