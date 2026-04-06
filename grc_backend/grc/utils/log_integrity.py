import hashlib
import hmac
import json
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.core.cache import cache


def _canonical_json(value: Any) -> str:
	"""
	Serialize value to a deterministic JSON string (sorted keys, no whitespace).
	"""
	return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _secret_bytes() -> bytes:
	secret = getattr(settings, "LOG_INTEGRITY_SECRET", None) or getattr(settings, "SECRET_KEY", "")
	if isinstance(secret, str):
		return secret.encode("utf-8")
	return bytes(secret)


def _chain_cache_key(chain_id: str) -> str:
	return f"log_chain_prev_hash::{chain_id}"


def get_prev_hash(chain_id: str = "grc_main") -> Optional[str]:
	"""
	Get previous hash for a chain from cache (fast path). Returns None if unknown.
	"""
	return cache.get(_chain_cache_key(chain_id))


def set_prev_hash(chain_id: str, prev_hash: Optional[str]) -> None:
	"""
	Update the last-seen hash for a chain. Stored with a long TTL so restarts retain continuity.
	"""
	# 30 days TTL; chain will continue as long as logs occur regularly
	cache.set(_chain_cache_key(chain_id), prev_hash, timeout=30 * 24 * 60 * 60)


def compute_entry_digest(payload: Dict[str, Any], prev_hash_hex: Optional[str]) -> Tuple[str, Dict[str, Any]]:
	"""
	Compute a tamper-evident digest for a log entry using HMAC-SHA256 over:
	- version, chain_id, prev_hash, and canonical payload snapshot
	Returns (current_hash_hex, integrity_metadata_dict).
	"""
	version = "v1"
	chain_id = str(payload.get("chain_id") or "grc_main")
	algo = "HMAC-SHA256"

	body = {
		"version": version,
		"chain_id": chain_id,
		"prev_hash": prev_hash_hex or "",
		"payload": {
			"Timestamp": payload.get("Timestamp"),
			"UserId": payload.get("UserId"),
			"UserName": payload.get("UserName"),
			"Module": payload.get("Module"),
			"ActionType": payload.get("ActionType"),
			"EntityId": payload.get("EntityId"),
			"EntityType": payload.get("EntityType"),
			"LogLevel": payload.get("LogLevel"),
			"Description": payload.get("Description"),
			"IPAddress": payload.get("IPAddress"),
			"AdditionalInfo": payload.get("AdditionalInfo") or {},
		},
	}
	msg = _canonical_json(body).encode("utf-8")
	mac = hmac.new(_secret_bytes(), msg, hashlib.sha256).hexdigest()
	integrity = {
		"version": version,
		"algo": algo,
		"chain_id": chain_id,
		"prev_hash": prev_hash_hex,
		"hash": mac,
	}
	return mac, integrity


def attach_integrity(log_data: Dict[str, Any], chain_id: str = "grc_main") -> Dict[str, Any]:
	"""
	Return a new dict with integrity metadata embedded under AdditionalInfo.integrity.
	Also advances the in-memory chain so subsequent calls link correctly.
	"""
	payload = dict(log_data)
	payload["chain_id"] = chain_id
	prev_hash = get_prev_hash(chain_id)
	# Timestamp should be present for stable digest; if not, leave as None (still part of canonical JSON)
	cur_hash, integrity = compute_entry_digest(payload, prev_hash)
	additional = payload.get("AdditionalInfo") or {}
	# Avoid mutating original AdditionalInfo
	new_additional = dict(additional)
	new_additional["integrity"] = integrity
	payload["AdditionalInfo"] = new_additional
	# Update chain tail for next entry
	set_prev_hash(chain_id, cur_hash)
	return payload


def verify_integrity_sequence(entries: Any, chain_id: str = "grc_main") -> bool:
	"""
	Verify a sequence of entries (iterable of mapping-like objects) forms a valid chain.
	Each entry must expose the same keys used in compute_entry_digest and contain
	AdditionalInfo.integrity with prev_hash/hash. Returns True if all link and verify.
	"""
	prev = None
	for entry in entries:
		payload = {
			"Timestamp": getattr(entry, "Timestamp", None) if hasattr(entry, "Timestamp") else entry.get("Timestamp"),
			"UserId": getattr(entry, "UserId", None) if hasattr(entry, "UserId") else entry.get("UserId"),
			"UserName": getattr(entry, "UserName", None) if hasattr(entry, "UserName") else entry.get("UserName"),
			"Module": getattr(entry, "Module", None) if hasattr(entry, "Module") else entry.get("Module"),
			"ActionType": getattr(entry, "ActionType", None) if hasattr(entry, "ActionType") else entry.get("ActionType"),
			"EntityId": getattr(entry, "EntityId", None) if hasattr(entry, "EntityId") else entry.get("EntityId"),
			"EntityType": getattr(entry, "EntityType", None) if hasattr(entry, "EntityType") else entry.get("EntityType"),
			"LogLevel": getattr(entry, "LogLevel", None) if hasattr(entry, "LogLevel") else entry.get("LogLevel"),
			"Description": getattr(entry, "Description", None) if hasattr(entry, "Description") else entry.get("Description"),
			"IPAddress": getattr(entry, "IPAddress", None) if hasattr(entry, "IPAddress") else entry.get("IPAddress"),
			"AdditionalInfo": getattr(entry, "AdditionalInfo", None) if hasattr(entry, "AdditionalInfo") else entry.get("AdditionalInfo"),
			"chain_id": chain_id,
		}
		info = None
		additional = payload.get("AdditionalInfo") or {}
		if isinstance(additional, dict):
			info = additional.get("integrity")
		if not info or "hash" not in info:
			return False
		expected_prev = prev
		_, recomputed = compute_entry_digest(payload, expected_prev)
		if recomputed["hash"] != info.get("hash") or info.get("prev_hash") != expected_prev:
			return False
		prev = recomputed["hash"]
	return True

