from django.core.management.base import BaseCommand
from django.conf import settings

from grc.utils.integrity_log_handler import verify_hash_chain_file


class Command(BaseCommand):
    help = "Verify SHA-256 hash chain integrity of the security audit log file."

    def handle(self, *args, **options):
        path = getattr(settings, "SECURITY_AUDIT_LOG_PATH", "")
        if not path:
            self.stderr.write("SECURITY_AUDIT_LOG_PATH is not set.")
            return
        result = verify_hash_chain_file(path)
        self.stdout.write(str(result))
        if not result.get("chain_valid"):
            raise SystemExit(1)
