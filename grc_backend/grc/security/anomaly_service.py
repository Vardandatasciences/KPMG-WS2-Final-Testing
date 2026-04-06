import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _cache_key_user_profile(user_id: str) -> str:
	return f"login_profile::{user_id}"


def _get_client_ip(request) -> str:
	# Align with existing utility if present
	try:
		from grc.utils import get_client_ip as _g
		return _g(request)
	except Exception:
		pass
	meta = getattr(request, "META", {}) or {}
	for header in ("HTTP_X_FORWARDED_FOR", "HTTP_X_REAL_IP", "REMOTE_ADDR"):
		val = meta.get(header)
		if val:
			return str(val).split(",")[0].strip()
	return ""


def _resolve_country(request) -> Optional[str]:
	# Prefer CDN-provided header if behind Cloudflare/CloudFront
	meta = getattr(request, "META", {}) or {}
	cf_country = meta.get("HTTP_CF_IPCOUNTRY")
	if cf_country:
		return str(cf_country)
	# Optional: ipinfo token path; skip external calls by default
	return None


def _get_profile(user_id: str) -> Dict:
	return cache.get(_cache_key_user_profile(user_id)) or {"hours": {}, "countries": {}}


def _update_profile(user_id: str, now: datetime, country: Optional[str]) -> Dict:
	profile = _get_profile(user_id)
	hour = now.hour
	profile["hours"][hour] = int(profile["hours"].get(hour, 0)) + 1
	if country:
		profile["countries"][country] = int(profile["countries"].get(country, 0)) + 1
	cache.set(_cache_key_user_profile(user_id), profile, timeout=30 * 24 * 60 * 60)
	return profile


def _is_unusual_hour(profile: Dict, hour: int) -> bool:
	if not profile.get("hours"):
		return False
	total = sum(profile["hours"].values())
	if total < 10:
		# Not enough history to judge
		return False
	freq = profile["hours"].get(hour, 0) / float(total)
	return freq < 0.05  # bottom 5% of observed hours


def _is_new_country(profile: Dict, country: Optional[str]) -> bool:
	if not country:
		return False
	seen = profile.get("countries") or {}
	if not seen:
		return False
	return country not in seen


def detect_and_alert_on_login(request, user, login_dt: Optional[datetime] = None) -> Dict[str, bool]:
	"""
	Detect simple per-account anomalies and send email alerts:
	- Unusual login hour (rare for this user)
	- New country for this user (if available)
	Returns flags indicating which anomalies were detected.
	"""
	now = login_dt or datetime.utcnow()
	user_id = getattr(user, "UserId", None) or getattr(user, "userid", None) or getattr(user, "id", None)
	user_email = getattr(user, "Email", None) or getattr(user, "email", None)
	if not user_id:
		return {"unusual_hour": False, "new_country": False}

	country = _resolve_country(request)
	# IMPORTANT: Evaluate anomalies against the PREVIOUS profile,
	# then update the profile after computing flags.
	prev_profile = _get_profile(str(user_id))
	flags = {
		"unusual_hour": _is_unusual_hour(prev_profile, now.hour),
		"new_country": _is_new_country(prev_profile, country),
	}
	# Now record this login into the profile
	_update_profile(str(user_id), now, country)

	if any(flags.values()):
		try:
			recipients = []
			security_email = getattr(settings, "SECURITY_ALERT_EMAIL", None)
			if security_email:
				recipients.append(security_email)
			if user_email and getattr(settings, "ALERT_USER_ON_LOGIN_ANOMALY", True):
				recipients.append(user_email)
			if recipients:
				subject = "Security alert: unusual login activity detected"
				details = []
				if flags["unusual_hour"]:
					details.append(f"Unusual login hour: {now.hour:02d}:00")
				if flags["new_country"]:
					details.append(f"New login country observed: {country or 'Unknown'}")
				body = (
					f"User ID: {user_id}\n"
					f"Time (UTC): {now.isoformat()}Z\n"
					f"IP: {_get_client_ip(request)}\n"
					f"{'; '.join(details)}\n"
				)
				send_mail(subject, body, getattr(settings, "DEFAULT_FROM_EMAIL", None), recipients, fail_silently=True)
		except Exception as e:
			logger.warning(f"Failed to send anomaly alert: {e}")

	return flags

