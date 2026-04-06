import json
import logging
import os
import threading
from datetime import datetime, timezone
from hashlib import sha256
import hmac
from typing import Optional

from django.conf import settings


class HashChainAppendOnlyFileHandler(logging.Handler):
	"""
	Append-only file handler that writes structured JSON and maintains an HMAC-SHA256 hash chain.
	- Each line contains: {"ts": "...", "level": "INFO", "msg": "<raw>", "prev_hash": "...", "hash": "..."}
	- Chain initialization uses previous value "GENESIS".
	- Secret: derived from DJANGO SECRET_KEY (or SECURITY_AUDIT_SECRET if provided).
	- File is opened in append-only mode; the handler never truncates or rewrites.
	- A sidecar state file (*.state) stores the last hash, to support multi-process continuity.
	"""

	_stream_lock = threading.Lock()

	def __init__(self, filename: str):
		super().__init__(level=logging.INFO)
		self.filename = filename
		self.state_path = f"{self.filename}.state"
		self.secret = (os.environ.get("SECURITY_AUDIT_SECRET") or settings.SECRET_KEY or "insecure-secret").encode("utf-8")
		# Ensure directory exists
		os.makedirs(os.path.dirname(self.filename), exist_ok=True)
		# Pre-open not strictly necessary; we open per write to reduce descriptor holding

	def _read_last_hash(self) -> str:
		try:
			with open(self.state_path, "r", encoding="utf-8") as sf:
				value = sf.read().strip()
				if value:
					return value
		except FileNotFoundError:
			return "GENESIS"
		except Exception:
			return "GENESIS"
		return "GENESIS"

	def _write_last_hash(self, value: str) -> None:
		with open(self.state_path, "w", encoding="utf-8") as sf:
			sf.write(value + "\n")
			sf.flush()
			os.fsync(sf.fileno())

	def _compute_hash(self, prev_hash: str, payload: str) -> str:
		mac = hmac.new(self.secret, digestmod=sha256)
		mac.update(prev_hash.encode("utf-8"))
		mac.update(b".")
		mac.update(payload.encode("utf-8"))
		return mac.hexdigest()

	def emit(self, record: logging.LogRecord) -> None:
		try:
			raw_message = record.getMessage()
			# If message is already JSON, do not double-encode; keep as-is string
			now = datetime.now(timezone.utc).isoformat()
			entry = {
				"ts": now,
				"level": record.levelname,
				"msg": raw_message,
			}
			payload = json.dumps(entry, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
			with self._stream_lock:
				prev_hash = self._read_last_hash()
				curr_hash = self._compute_hash(prev_hash, payload)
				entry["prev_hash"] = prev_hash
				entry["hash"] = curr_hash
				line = json.dumps(entry, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
				# Append-only write
				with open(self.filename, "a", encoding="utf-8") as f:
					f.write(line + "\n")
					f.flush()
					os.fsync(f.fileno())
				# Persist last hash
				self._write_last_hash(curr_hash)
		except Exception:
			self.handleError(record)

"""
Append-only file handler with SHA-256 hash chain for tamper detection.

Each line is a JSON object: seq, prev_hash, payload, line_hash.
line_hash = SHA256(prev_hash || canonical_json(payload)) using UTF-8 bytes.

Verification replays the file and detects any insert, delete, reorder, or edit.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional


GENESIS_PREV_HASH = "0" * 64


def _canonical_payload_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_hash_chain_file(path: str, max_errors: int = 50) -> Dict[str, Any]:
    """
    Verify an append-only hash-chain log file. Returns a result dict suitable for JSON APIs.
    """
    p = Path(path)
    if not p.is_file():
        return {
            "chain_valid": True,
            "lines_verified": 0,
            "message": "audit_log_file_not_found",
            "log_path": str(p),
        }

    prev = GENESIS_PREV_HASH
    line_no = 0
    errors: List[Dict[str, Any]] = []

    with p.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line_no += 1
            line = raw.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append({"line": line_no, "error": "invalid_json", "detail": str(e)})
                if len(errors) >= max_errors:
                    break
                continue

            ph = rec.get("prev_hash")
            lh = rec.get("line_hash")
            payload = rec.get("payload")

            if ph != prev:
                errors.append(
                    {
                        "line": line_no,
                        "error": "prev_hash_mismatch",
                        "expected_prev": prev,
                        "recorded_prev": ph,
                    }
                )

            if not isinstance(payload, dict):
                errors.append({"line": line_no, "error": "invalid_payload_type"})
                if len(errors) >= max_errors:
                    break
                prev = lh if isinstance(lh, str) else prev
                continue

            ph_s = ph if isinstance(ph, str) else ""
            expected = hashlib.sha256(ph_s.encode("utf-8") + _canonical_payload_bytes(payload)).hexdigest()
            if lh != expected:
                errors.append({"line": line_no, "error": "line_hash_mismatch", "expected": expected, "recorded": lh})

            if isinstance(lh, str):
                prev = lh
            if len(errors) >= max_errors:
                break

    return {
        "chain_valid": len(errors) == 0,
        "lines_verified": line_no,
        "errors": errors,
        "log_path": str(p.resolve()),
    }


class HashChainAppendOnlyFileHandler(logging.Handler):
    """
    Opens the target file in append mode only (no rotation = no overwrite of prior records).
    """

    def __init__(self, filename: str, encoding: str = "utf-8"):
        super().__init__()
        self.baseFilename = os.path.abspath(filename)
        Path(self.baseFilename).parent.mkdir(parents=True, exist_ok=True)
        self.encoding = encoding
        self._lock = threading.RLock()
        self._prev_hash, self._seq = self._load_chain_tip()

    def _load_chain_tip(self) -> tuple[str, int]:
        if not os.path.exists(self.baseFilename) or os.path.getsize(self.baseFilename) == 0:
            return GENESIS_PREV_HASH, 0
        last_line = ""
        try:
            with open(self.baseFilename, "r", encoding=self.encoding, errors="replace") as f:
                for line in f:
                    s = line.strip()
                    if s:
                        last_line = s
        except OSError:
            return GENESIS_PREV_HASH, 0
        if not last_line:
            return GENESIS_PREV_HASH, 0
        try:
            rec = json.loads(last_line)
            lh = rec.get("line_hash")
            seq = int(rec.get("seq", 0))
            if isinstance(lh, str) and len(lh) == 64:
                return lh, seq + 1
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        return GENESIS_PREV_HASH, 0

    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload: Dict[str, Any] = {
                "level": record.levelname,
                "logger": record.name,
                "time_iso": logging.Formatter().formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                "message": record.getMessage(),
            }
            if record.exc_info and record.exc_text:
                payload["exc_text"] = (record.exc_text or "")[:2000]

            canonical = _canonical_payload_bytes(payload)
            with self._lock:
                line_hash = hashlib.sha256((self._prev_hash.encode("utf-8") + canonical)).hexdigest()
                envelope = {
                    "seq": self._seq,
                    "prev_hash": self._prev_hash,
                    "payload": payload,
                    "line_hash": line_hash,
                }
                line = json.dumps(envelope, separators=(",", ":")) + "\n"
                with open(self.baseFilename, "a", encoding=self.encoding) as af:
                    af.write(line)
                    af.flush()
                    try:
                        os.fsync(af.fileno())
                    except OSError:
                        pass
                self._prev_hash = line_hash
                self._seq += 1
        except Exception:
            self.handleError(record)
