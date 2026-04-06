import json
import os
from hashlib import sha256
import hmac
from typing import Tuple

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


def _compute(secret: bytes, prev_hash: str, payload: str) -> str:
	mac = hmac.new(secret, digestmod=sha256)
	mac.update(prev_hash.encode("utf-8"))
	mac.update(b".")
	mac.update(payload.encode("utf-8"))
	return mac.hexdigest()


class Command(BaseCommand):
	help = "Verify the hash-chain integrity of the security audit log."

	def add_arguments(self, parser):
		parser.add_argument(
			"--path",
			dest="path",
			default=getattr(settings, "SECURITY_AUDIT_LOG_PATH", ""),
			help="Path to the audit chain log file.",
		)
		parser.add_argument(
			"--secret",
			dest="secret",
			default=os.environ.get("SECURITY_AUDIT_SECRET") or settings.SECRET_KEY or "",
			help="Override secret (defaults to SECURITY_AUDIT_SECRET or SECRET_KEY).",
		)

	def handle(self, *args, **options):
		path = options["path"]
		if not path:
			raise CommandError("SECURITY_AUDIT_LOG_PATH not configured and no --path provided.")
		if not os.path.isfile(path):
			raise CommandError(f"Audit log file does not exist: {path}")

		secret = str(options["secret"]).encode("utf-8")
		prev = "GENESIS"
		ok = True
		line_no = 0
		with open(path, "r", encoding="utf-8") as f:
			for line in f:
				line_no += 1
				line = line.strip()
				if not line:
					continue
				try:
					obj = json.loads(line)
					msg_obj = {
						"k": "v"  # placeholder to stabilize key order below
					}
					# Rebuild payload exactly as handler used (ts, level, msg)
					payload_obj = {
						"level": obj.get("level"),
						"msg": obj.get("msg"),
						"ts": obj.get("ts"),
					}
					payload = json.dumps(payload_obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
					expect = _compute(secret, prev, payload)
					actual = obj.get("hash")
					if expect != actual:
						self.stderr.write(f"FAILED at line {line_no}: expected {expect}, got {actual}")
						ok = False
						break
					prev = actual
				except Exception as e:
					self.stderr.write(f"FAILED parsing line {line_no}: {e}")
					ok = False
					break
		if ok:
			self.stdout.write(self.style.SUCCESS(f"Integrity OK for {path} (verified {line_no} lines)"))
		else:
			raise CommandError("Integrity verification failed. See messages above.")

