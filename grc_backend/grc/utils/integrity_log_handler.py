from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from .log_sanitize import sanitize_for_log


GENESIS_PREV_HASH = "0" * 64


def _canonical_payload_bytes(payload: Dict[str, Any]) -> bytes:
    """
    Returns the canonical JSON representation of the payload as UTF-8 bytes.
    Ensures consistent hashing across different platforms/JSON encoders.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_hash_chain_file(path: str, max_errors: int = 50) -> Dict[str, Any]:
    """
    Verify an append-only hash-chain log file. Returns a result dict suitable for JSON APIs.
    
    Checks:
    1. JSON validity per line
    2. Sequence continuity (prev_hash matches previous line's hash)
    3. Hash integrity (line_hash matches computed hash of prev_hash + payload)
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
    Logging handler that opens the target file in append mode only and maintains a SHA-256 hash chain.
    Each log entry is protected against tampering, deletion, or reordering by including the 
    hash of the previous record.
    """

    def __init__(self, filename: str, encoding: str = "utf-8"):
        super().__init__()
        self.baseFilename = os.path.abspath(filename)
        # Ensure the directory exists
        Path(self.baseFilename).parent.mkdir(parents=True, exist_ok=True)
        self.encoding = encoding
        self._lock = threading.RLock()
        # Initialize the chain by loading the last record's hash and sequence number
        self._prev_hash, self._seq = self._load_chain_tip()

    def _load_chain_tip(self) -> tuple[str, int]:
        """
        Reads the last line of the file to resume the hash chain.
        Returns (last_hash, next_sequence_number).
        """
        if not os.path.exists(self.baseFilename) or os.path.getsize(self.baseFilename) == 0:
            return GENESIS_PREV_HASH, 0
        
        last_line = ""
        try:
            with open(self.baseFilename, "r", encoding=self.encoding, errors="replace") as f:
                # We iterate to find the last non-empty line. 
                # For very large files, a seek-from-end approach would be more efficient.
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
        """
        Writes a new log record with its hash and the previous record's hash.
        """
        try:
            payload: Dict[str, Any] = {
                "level": record.levelname,
                "logger": sanitize_for_log(record.name, max_len=256),
                "time_iso": logging.Formatter().formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                "message": sanitize_for_log(record.getMessage(), max_len=4000),
            }
            # Include exception text if present, but truncate to avoid massive log entries
            if record.exc_info and record.exc_text:
                payload["exc_text"] = sanitize_for_log((record.exc_text or "")[:2000], max_len=2000)

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
                
                # Use 'a' mode for append-only behavior
                with open(self.baseFilename, "a", encoding=self.encoding) as af:
                    af.write(line)
                    af.flush()
                    try:
                        os.fsync(af.fileno())
                    except OSError:
                        pass
                
                # Update state for next record
                self._prev_hash = line_hash
                self._seq += 1
        except Exception:
            self.handleError(record)
