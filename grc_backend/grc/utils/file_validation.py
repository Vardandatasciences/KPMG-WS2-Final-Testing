"""
Secure file upload validation utility.

Defends against:
  - Malicious SVG/HTML files that execute JavaScript when opened
  - File-extension/MIME spoofing (e.g. SVG disguised as a PDF)
  - Executable or script uploads

Strategy:
  1. Reject scriptable / dangerous MIME types outright.
  2. Reject dangerous extensions outright.
  3. Read the first 16 bytes (magic bytes) to determine the *real* file type.
  4. Confirm that the declared extension, declared Content-Type, and detected
     magic type are all consistent with an entry in ALLOWED_TYPES.
  5. For text-based safe types (PDF text header, CSV, TXT), scan for embedded
     script patterns.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Magic-byte signatures
# Each entry: (bytes_to_match_at_offset_0, canonical_type_label)
# We check magic bytes FIRST, then cross-check against the declared extension.
# ---------------------------------------------------------------------------
MAGIC_SIGNATURES = [
    (b"%PDF",                    "pdf"),
    (b"\xd0\xcf\x11\xe0",       "office_legacy"),   # DOC, XLS, PPT (old .doc/.xls)
    (b"PK\x03\x04",             "zip_based"),        # DOCX, XLSX, PPTX (Open XML = ZIP)
    (b"\xff\xd8\xff",           "jpeg"),
    (b"\x89PNG\r\n\x1a\n",     "png"),
    (b"GIF87a",                 "gif"),
    (b"GIF89a",                 "gif"),
    (b"BM",                     "bmp"),
    (b"RIFF",                   "riff"),             # WAV / AVI — blocked below
]

# ---------------------------------------------------------------------------
# Allowed upload profiles
# Maps a friendly label → (allowed_extensions, allowed_mime_types, magic_labels)
# ---------------------------------------------------------------------------
ALLOWED_TYPES = {
    "pdf": {
        "extensions": {".pdf"},
        "mimes": {"application/pdf"},
        "magic": {"pdf"},
    },
    "word": {
        "extensions": {".doc", ".docx"},
        "mimes": {
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        },
        "magic": {"office_legacy", "zip_based"},
    },
    "excel": {
        "extensions": {".xls", ".xlsx"},
        "mimes": {
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        },
        "magic": {"office_legacy", "zip_based"},
    },
    "powerpoint": {
        "extensions": {".ppt", ".pptx"},
        "mimes": {
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        },
        "magic": {"office_legacy", "zip_based"},
    },
    "image_jpeg": {
        "extensions": {".jpg", ".jpeg"},
        "mimes": {"image/jpeg"},
        "magic": {"jpeg"},
    },
    "image_png": {
        "extensions": {".png"},
        "mimes": {"image/png"},
        "magic": {"png"},
    },
    "csv": {
        "extensions": {".csv"},
        "mimes": {"text/csv", "text/plain", "application/csv"},
        "magic": None,  # no fixed magic bytes; validated by content scan
    },
    "text": {
        "extensions": {".txt"},
        "mimes": {"text/plain"},
        "magic": None,
    },
}

# Flat sets derived from ALLOWED_TYPES for quick rejection before deep checks
ALL_ALLOWED_EXTENSIONS: set = set()
ALL_ALLOWED_MIMES: set = set()
for _profile in ALLOWED_TYPES.values():
    ALL_ALLOWED_EXTENSIONS.update(_profile["extensions"])
    ALL_ALLOWED_MIMES.update(_profile["mimes"])

# ---------------------------------------------------------------------------
# Blocklists — these are ALWAYS rejected regardless of any other check
# ---------------------------------------------------------------------------
BLOCKED_EXTENSIONS = {
    ".svg", ".svgz",        # scriptable vector graphics
    ".html", ".htm",        # HTML — can execute JS
    ".xhtml",               # ditto
    ".xml",                 # can embed scripts / XXE
    ".js", ".mjs", ".cjs",  # JavaScript
    ".ts",                  # TypeScript
    ".vbs", ".vbe",         # VBScript
    ".hta",                 # HTML Application
    ".php", ".php3", ".php4", ".php5", ".phtml",
    ".asp", ".aspx",
    ".jsp", ".jspx",
    ".py", ".rb", ".pl", ".sh", ".bash", ".ps1", ".bat", ".cmd",
    ".exe", ".dll", ".so", ".dylib",
    ".jar", ".class",
    ".swf", ".fla",         # Flash
    ".xsl", ".xslt",        # XSLT — can execute
}

BLOCKED_MIMES = {
    "image/svg+xml",
    "text/html",
    "application/xhtml+xml",
    "text/xml",
    "application/xml",
    "application/javascript",
    "text/javascript",
    "application/x-javascript",
    "application/x-shockwave-flash",
    "application/x-php",
    "application/x-httpd-php",
    "application/octet-stream",   # generic binary — could be anything; reject
}

# Patterns that indicate embedded scripts inside otherwise "safe" text content
SCRIPT_PATTERNS = [
    re.compile(rb"<script", re.IGNORECASE),
    re.compile(rb"javascript\s*:", re.IGNORECASE),
    re.compile(rb"vbscript\s*:", re.IGNORECASE),
    re.compile(rb"on\w+\s*=", re.IGNORECASE),       # onclick=, onload=, etc.
    re.compile(rb"<\s*svg", re.IGNORECASE),          # SVG root element
    re.compile(rb"<\s*iframe", re.IGNORECASE),
    re.compile(rb"<\s*object", re.IGNORECASE),
    re.compile(rb"<\s*embed", re.IGNORECASE),
    re.compile(rb"<\s*link", re.IGNORECASE),
    re.compile(rb"<\s*meta", re.IGNORECASE),
    re.compile(rb"data:text/html", re.IGNORECASE),
    re.compile(rb"data:image/svg", re.IGNORECASE),
    re.compile(rb"<!DOCTYPE", re.IGNORECASE),
    re.compile(rb"<!ENTITY", re.IGNORECASE),         # XXE
    re.compile(rb"<\?xml", re.IGNORECASE),           # XML declaration
]


@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None
    detected_magic: Optional[str] = None


def _detect_magic(header: bytes) -> Optional[str]:
    """Return the canonical magic-type label for the given file header bytes."""
    for signature, label in MAGIC_SIGNATURES:
        if header[: len(signature)] == signature:
            return label
    return None


def _scan_for_scripts(content: bytes) -> bool:
    """Return True if any script-injection pattern is found in content."""
    for pattern in SCRIPT_PATTERNS:
        if pattern.search(content):
            return True
    return False


def validate_upload(
    file_obj,
    allowed_profiles: Optional[list] = None,
    max_size_mb: int = 25,
) -> ValidationResult:
    """
    Validate an uploaded file object (Django InMemoryUploadedFile or similar).

    Parameters
    ----------
    file_obj:
        The Django uploaded-file object (from request.FILES).
    allowed_profiles:
        Optional list of profile keys from ALLOWED_TYPES to restrict further.
        E.g. ['pdf', 'word'] for a document-only endpoint.
        If None, all profiles in ALLOWED_TYPES are considered valid.
    max_size_mb:
        Maximum allowed file size in megabytes (default 25 MB).

    Returns
    -------
    ValidationResult with is_valid=True on success, or is_valid=False + error
    message on failure.
    """
    try:
        filename: str = getattr(file_obj, "name", "") or ""
        declared_mime: str = (getattr(file_obj, "content_type", "") or "").lower().strip()
        file_size: int = getattr(file_obj, "size", 0) or 0

        import os
        ext = os.path.splitext(filename)[1].lower()

        # ------------------------------------------------------------------
        # 1. Reject blocked extensions immediately
        # ------------------------------------------------------------------
        if ext in BLOCKED_EXTENSIONS:
            logger.warning(
                "Blocked upload: extension '%s' is in the blocked list (file: %s)",
                ext, filename,
            )
            return ValidationResult(
                is_valid=False,
                error=(
                    f"File type '{ext}' is not allowed. "
                    "Scriptable or executable file types are prohibited."
                ),
            )

        # ------------------------------------------------------------------
        # 2. Reject blocked MIME types immediately
        # ------------------------------------------------------------------
        if declared_mime in BLOCKED_MIMES:
            logger.warning(
                "Blocked upload: MIME '%s' is in the blocked list (file: %s)",
                declared_mime, filename,
            )
            return ValidationResult(
                is_valid=False,
                error=(
                    f"Content-Type '{declared_mime}' is not allowed. "
                    "Scriptable or dangerous MIME types are prohibited."
                ),
            )

        # ------------------------------------------------------------------
        # 3. Extension must be in the allowed-extension whitelist
        # ------------------------------------------------------------------
        if ext not in ALL_ALLOWED_EXTENSIONS:
            logger.warning(
                "Blocked upload: extension '%s' not in whitelist (file: %s)",
                ext, filename,
            )
            return ValidationResult(
                is_valid=False,
                error=(
                    f"File extension '{ext}' is not permitted. "
                    f"Allowed types: {', '.join(sorted(ALL_ALLOWED_EXTENSIONS))}"
                ),
            )

        # ------------------------------------------------------------------
        # 4. MIME type must be in the allowed-MIME whitelist
        # ------------------------------------------------------------------
        if declared_mime and declared_mime not in ALL_ALLOWED_MIMES:
            logger.warning(
                "Blocked upload: MIME '%s' not in whitelist (file: %s)",
                declared_mime, filename,
            )
            return ValidationResult(
                is_valid=False,
                error=(
                    f"Content-Type '{declared_mime}' is not permitted. "
                    "Please upload a valid document file."
                ),
            )

        # ------------------------------------------------------------------
        # 5. File size check
        # ------------------------------------------------------------------
        max_bytes = max_size_mb * 1024 * 1024
        if file_size > max_bytes:
            return ValidationResult(
                is_valid=False,
                error=f"File size exceeds the maximum allowed size of {max_size_mb} MB.",
            )

        # ------------------------------------------------------------------
        # 6. Read file content for magic-byte + script scanning
        # ------------------------------------------------------------------
        file_obj.seek(0)
        # Read enough bytes for magic detection + script scanning
        content = file_obj.read(min(file_size, 1 * 1024 * 1024))  # up to 1 MB
        file_obj.seek(0)  # always reset pointer after reading

        header = content[:16]
        detected_magic = _detect_magic(header)

        # ------------------------------------------------------------------
        # 7. Magic-byte vs. extension consistency check
        # ------------------------------------------------------------------
        # Find which profile(s) match this extension
        matching_profiles = [
            (name, profile)
            for name, profile in ALLOWED_TYPES.items()
            if ext in profile["extensions"]
            and (allowed_profiles is None or name in allowed_profiles)
        ]

        if not matching_profiles:
            return ValidationResult(
                is_valid=False,
                error=f"Extension '{ext}' is not permitted for this upload.",
            )

        magic_ok = False
        for profile_name, profile in matching_profiles:
            expected_magic = profile.get("magic")
            if expected_magic is None:
                # Text-based type (CSV/TXT) — no magic, but scan for scripts below
                magic_ok = True
                break
            if detected_magic in expected_magic:
                magic_ok = True
                break

        if not magic_ok:
            logger.warning(
                "Magic-byte mismatch: extension '%s', detected magic '%s' (file: %s)",
                ext, detected_magic, filename,
            )
            return ValidationResult(
                is_valid=False,
                error=(
                    f"The file content does not match its extension '{ext}'. "
                    "The file may be spoofed or corrupted. Upload rejected."
                ),
                detected_magic=detected_magic,
            )

        # ------------------------------------------------------------------
        # 8. Script-injection scan
        #    Applies to text-based files (CSV, TXT) and as a belt-and-
        #    suspenders check on any file that passed magic checks.
        #    For binary types (PDF, DOCX, images) only scan the first 4 KB
        #    to catch polyglot attacks without significant overhead.
        # ------------------------------------------------------------------
        scan_bytes = content if ext in {".csv", ".txt"} else content[:4096]
        if _scan_for_scripts(scan_bytes):
            logger.warning(
                "Script pattern detected in upload (file: %s, ext: %s)",
                filename, ext,
            )
            return ValidationResult(
                is_valid=False,
                error=(
                    "The file contains potentially malicious content "
                    "(script tags or event handlers). Upload rejected."
                ),
            )

        logger.info(
            "File validation passed: '%s' (ext=%s, mime=%s, magic=%s)",
            filename, ext, declared_mime, detected_magic,
        )
        return ValidationResult(is_valid=True, detected_magic=detected_magic)

    except Exception as exc:
        logger.error("Unexpected error during file validation: %s", exc, exc_info=True)
        return ValidationResult(is_valid=False, error="File validation failed due to an internal error.")
