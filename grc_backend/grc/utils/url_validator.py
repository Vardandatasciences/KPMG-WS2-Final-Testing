import ipaddress
import socket
import urllib.parse
from typing import Iterable, Optional

from django.conf import settings


class UnsafeRedirectError(ValueError):
    """Raised when a redirect target is not an allowed relative application path."""


class InvalidOutboundUrlError(ValueError):
    """
    Raised when an outbound URL fails security validation.

    This is used to guard against SSRF-style issues and misconfiguration
    (e.g. pointing integrations at localhost or private networks).
    """


def _resolve_ip(hostname: str) -> ipaddress._BaseAddress:
    """
    Resolve a hostname to an IP address object.

    Kept simple on purpose; if DNS resolution fails we treat the URL as invalid.
    """
    ip_str = socket.gethostbyname(hostname)
    return ipaddress.ip_address(ip_str)


def validate_url(
    url: str,
    *,
    allow_http_for: Optional[Iterable[str]] = None,
    allowed_domains_override: Optional[Iterable[str]] = None,
) -> None:
    """
    Validate an outbound URL for SSRF / misconfiguration safety.

    Rules:
    - Scheme must be https by default. http is allowed only for explicitly
      configured hosts (via allow_http_for or OUTBOUND_ALLOWED_HTTP_DOMAINS).
    - Hostname must resolve successfully.
    - IP must not be private, loopback, link-local, or multicast.
    - If an allowlist is configured (allowed_domains_override or
      OUTBOUND_ALLOWED_DOMAINS), the hostname must appear in it.

    Raises InvalidOutboundUrlError on any violation.
    """
    if not url:
        raise InvalidOutboundUrlError("URL must not be empty")

    parsed = urllib.parse.urlparse(url)

    if not parsed.scheme or not parsed.hostname:
        raise InvalidOutboundUrlError("URL must include scheme and hostname")

    hostname = parsed.hostname.lower()
    scheme = parsed.scheme.lower()

    if scheme not in ("http", "https"):
        raise InvalidOutboundUrlError(f"Unsupported URL scheme '{scheme}'")

    # HTTP is only allowed for specific hosts (typically internal services)
    allowed_http_hosts = set(h.lower() for h in (allow_http_for or []))
    http_domains_from_settings = getattr(settings, "OUTBOUND_ALLOWED_HTTP_DOMAINS", None)
    if http_domains_from_settings:
        allowed_http_hosts.update(d.lower() for d in http_domains_from_settings)

    if scheme == "http" and hostname not in allowed_http_hosts:
        raise InvalidOutboundUrlError(
            f"Plain HTTP is not allowed for host '{hostname}'. "
            "Use HTTPS or add the host to the HTTP allowlist."
        )

    # Resolve and check IP classification
    try:
        ip_obj = _resolve_ip(hostname)
    except Exception as exc:  # pragma: no cover - defensive
        raise InvalidOutboundUrlError(f"Unable to resolve hostname '{hostname}': {exc}") from exc

    if any(
        (
            ip_obj.is_private,
            ip_obj.is_loopback,
            ip_obj.is_link_local,
            ip_obj.is_multicast,
        )
    ):
        raise InvalidOutboundUrlError(
            f"Outbound calls to address '{ip_obj}' are not allowed "
            "(private, loopback, link-local, or multicast)"
        )

    # Optional domain allowlist: if configured, hostname must be in the list
    if allowed_domains_override is not None:
        allowed_domains = list(allowed_domains_override)
    else:
        allowed_domains = getattr(settings, "OUTBOUND_ALLOWED_DOMAINS", None)

    if allowed_domains:
        allowed_set = {d.lower() for d in allowed_domains}
        if hostname not in allowed_set:
            raise InvalidOutboundUrlError(
                f"Domain '{hostname}' is not in the configured outbound allowlist"
            )


def assert_safe_relative_redirect(
    url: str,
    *,
    allowed_path_prefixes: Iterable[str],
) -> str:
    """
    Ensure ``url`` is a same-site relative path suitable for HttpResponseRedirect.

    Rejects absolute URLs, protocol-relative URLs, backslash paths, and paths
    outside the configured prefix allowlist (open-redirect hardening).
    """
    if not url or not isinstance(url, str):
        raise UnsafeRedirectError("Redirect URL must be a non-empty string")

    u = url.strip()
    lowered = u.lower()
    if lowered.startswith(("http://", "https://", "//")):
        raise UnsafeRedirectError("Redirect must not be an absolute or protocol-relative URL")
    if "\\" in u or "\n" in u or "\r" in u:
        raise UnsafeRedirectError("Redirect contains illegal characters")
    if not u.startswith("/"):
        raise UnsafeRedirectError("Redirect must start with /")

    parsed = urllib.parse.urlparse(u)
    path = parsed.path or ""
    if not path.startswith("/"):
        raise UnsafeRedirectError("Invalid redirect path")

    prefixes = tuple(allowed_path_prefixes)
    if not prefixes:
        raise UnsafeRedirectError("No allowed path prefixes configured")

    if not any(path.startswith(p) for p in prefixes):
        raise UnsafeRedirectError("Redirect path is not in the allowed prefix list")

    return u