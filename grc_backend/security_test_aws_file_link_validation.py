"""
Automated security validation for aws-file_link URL tampering.

Purpose
-------
Tests whether incident-related APIs reject attacker-controlled evidence URLs.
This script is designed for local/manual security verification using a payload
captured from browser/Postman and a valid JWT.

What it does
------------
1) Discovers incident endpoints from frontend API config.
2) Loads your real JSON payload.
3) Replaces every `aws-file_link` value with a malicious URL.
4) Sends requests to each endpoint and reports PASS/FAIL.

Usage
-----
python security_test_aws_file_link_validation.py ^
  --token "<JWT_ACCESS_TOKEN>" ^
  --payload-file "C:\\temp\\incident_payload.json" ^
  --base-url "http://127.0.0.1:8000"

Optional:
  --malicious-url "https://evil-attacker.com/poc.pdf"
  --endpoint "/api/submit-incident-assessment/"
  --control
  --insecure
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import ssl
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Tuple
from urllib import error, request
from urllib.parse import urljoin


DEFAULT_MALICIOUS_URL = "https://evil-attacker.com/poc.pdf"
EXPECTED_ERROR_HINTS = ("invalid evidence url", "invalid url", "validation")


@dataclass
class TestResult:
    endpoint: str
    status_code: int
    blocked: bool
    reason: str
    response_snippet: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_incident_endpoints_from_api_js(api_js_path: Path) -> List[str]:
    """
    Pull likely incident endpoints from frontend config.
    Works with lines like:
      INCIDENT_AI_SAVE: `${API_BASE_URL}/api/ai-incident-save/`,
      SUBMIT_INCIDENT_ASSESSMENT: `${API_BASE_URL}/api/submit-incident-assessment/`,
    """
    text = read_text(api_js_path)
    pattern = re.compile(r"['\"`](/api/[^'\"`]*incident[^'\"`]*/?)['\"`]", re.IGNORECASE)
    candidates = pattern.findall(text)

    # Also include these explicit names in case regex misses due to formatting.
    explicit = [
        "/api/submit-incident-assessment/",
        "/api/ai-incident-upload/",
        "/api/ai-incident-save/",
    ]
    normalized = {normalize_endpoint(x) for x in candidates + explicit}
    return sorted(normalized)


def normalize_endpoint(endpoint: str) -> str:
    e = endpoint.strip()
    if not e.startswith("/"):
        e = "/" + e
    return e


def collect_aws_file_link_paths(node: Any, path: Tuple[Any, ...] = ()) -> List[Tuple[Any, ...]]:
    paths: List[Tuple[Any, ...]] = []
    if isinstance(node, dict):
        for k, v in node.items():
            current = path + (k,)
            if k == "aws-file_link":
                paths.append(current)
            paths.extend(collect_aws_file_link_paths(v, current))
    elif isinstance(node, list):
        for i, item in enumerate(node):
            paths.extend(collect_aws_file_link_paths(item, path + (i,)))
    return paths


def set_value_at_path(node: Any, path: Tuple[Any, ...], value: Any) -> None:
    cursor = node
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value


def get_value_at_path(node: Any, path: Tuple[Any, ...]) -> Any:
    cursor = node
    for key in path:
        cursor = cursor[key]
    return cursor


def path_to_str(path: Tuple[Any, ...]) -> str:
    out = []
    for p in path:
        if isinstance(p, int):
            out.append(f"[{p}]")
        else:
            out.append(str(p))
    return ".".join(out).replace(".[", "[")


def send_json_post(
    url: str,
    payload: dict,
    token: str,
    timeout: int,
    insecure: bool,
) -> Tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("Authorization", f"Bearer {token}")

    context = None
    if insecure and url.lower().startswith("https://"):
        context = ssl._create_unverified_context()  # noqa: SLF001 - deliberate for local self-signed

    try:
        with request.urlopen(req, timeout=timeout, context=context) as resp:
            status = int(resp.status)
            response_body = resp.read().decode("utf-8", errors="replace")
            return status, response_body
    except error.HTTPError as exc:
        status = int(exc.code)
        response_body = exc.read().decode("utf-8", errors="replace")
        return status, response_body


def classify_block(status_code: int, response_text: str) -> Tuple[bool, str]:
    response_low = (response_text or "").lower()
    if status_code == 400:
        return True, "Blocked with expected 400"
    if any(hint in response_low for hint in EXPECTED_ERROR_HINTS):
        return True, "Blocked with validation error message"
    if status_code in (401, 403):
        return False, "Auth/permission issue; cannot conclude vulnerability status"
    if 200 <= status_code < 300:
        return False, "Request accepted (possible validation bypass)"
    return False, f"Unexpected status {status_code}"


def run_test_for_endpoint(
    base_url: str,
    endpoint: str,
    token: str,
    payload: dict,
    malicious_url: str,
    timeout: int,
    insecure: bool,
    run_control: bool,
) -> TestResult:
    endpoint = normalize_endpoint(endpoint)
    full_url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))

    if run_control:
        control_status, _ = send_json_post(full_url, payload, token, timeout, insecure)
        if control_status in (401, 403):
            return TestResult(
                endpoint=endpoint,
                status_code=control_status,
                blocked=False,
                reason="Control request unauthorized/forbidden; refresh token or permissions",
                response_snippet="",
            )

    mutated = copy.deepcopy(payload)
    paths = collect_aws_file_link_paths(mutated)
    if not paths:
        return TestResult(
            endpoint=endpoint,
            status_code=0,
            blocked=False,
            reason="No aws-file_link fields found in payload",
            response_snippet="",
        )

    for p in paths:
        set_value_at_path(mutated, p, malicious_url)

    status, resp_text = send_json_post(full_url, mutated, token, timeout, insecure)
    blocked, reason = classify_block(status, resp_text)

    snippet = (resp_text or "").strip().replace("\n", " ")
    if len(snippet) > 220:
        snippet = snippet[:220] + "..."

    return TestResult(
        endpoint=endpoint,
        status_code=status,
        blocked=blocked,
        reason=reason,
        response_snippet=snippet,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Automated aws-file_link tampering test")
    parser.add_argument("--token", required=True, help="JWT access token (without 'Bearer ')")
    parser.add_argument("--payload-file", required=True, help="Path to captured JSON payload")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API host base URL")
    parser.add_argument("--malicious-url", default=DEFAULT_MALICIOUS_URL, help="Attacker URL to inject")
    parser.add_argument("--timeout", type=int, default=45, help="HTTP timeout seconds")
    parser.add_argument("--insecure", action="store_true", help="Skip TLS cert verification for HTTPS")
    parser.add_argument("--control", action="store_true", help="Send unmodified payload first")
    parser.add_argument(
        "--endpoint",
        action="append",
        default=[],
        help="Specific endpoint path(s), can pass multiple times",
    )
    parser.add_argument(
        "--api-config",
        default=str(Path(__file__).resolve().parents[1] / "grc_frontend" / "src" / "config" / "api.js"),
        help="Path to frontend api.js for endpoint auto-discovery",
    )
    args = parser.parse_args()

    payload_path = Path(args.payload_file).resolve()
    if not payload_path.exists():
        print(f"[ERROR] Payload file not found: {payload_path}")
        return 2

    try:
        payload = json.loads(read_text(payload_path))
    except json.JSONDecodeError as exc:
        print(f"[ERROR] Invalid JSON in payload file: {exc}")
        return 2

    aws_paths = collect_aws_file_link_paths(payload)
    if not aws_paths:
        print("[ERROR] Payload has no `aws-file_link` fields. Use the final assessment submit payload.")
        return 2

    print("=" * 88)
    print("AWS FILE LINK VALIDATION TEST")
    print("=" * 88)
    print(f"Base URL       : {args.base_url}")
    print(f"Payload file   : {payload_path}")
    print(f"Malicious URL  : {args.malicious_url}")
    print(f"aws-file_link paths found: {len(aws_paths)}")
    for p in aws_paths:
        print(f"  - {path_to_str(p)} = {repr(get_value_at_path(payload, p))}")
    print("=" * 88)

    discovered = []
    api_config_path = Path(args.api_config).resolve()
    if api_config_path.exists():
        discovered = parse_incident_endpoints_from_api_js(api_config_path)
        print(f"[INFO] Discovered incident endpoints from {api_config_path}:")
        for e in discovered:
            print(f"  - {e}")
    else:
        print(f"[WARN] API config not found: {api_config_path}")

    endpoints = [normalize_endpoint(e) for e in (args.endpoint or discovered)]
    endpoints = sorted(set(endpoints))
    if not endpoints:
        print("[ERROR] No endpoints to test. Provide --endpoint explicitly.")
        return 2

    print("=" * 88)
    results: List[TestResult] = []
    for endpoint in endpoints:
        result = run_test_for_endpoint(
            base_url=args.base_url,
            endpoint=endpoint,
            token=args.token,
            payload=payload,
            malicious_url=args.malicious_url,
            timeout=args.timeout,
            insecure=args.insecure,
            run_control=args.control,
        )
        results.append(result)

        status_icon = "PASS" if result.blocked else "FAIL"
        print(f"[{status_icon}] {result.endpoint}")
        print(f"       status={result.status_code} | {result.reason}")
        if result.response_snippet:
            print(f"       response={result.response_snippet}")

    total = len(results)
    passed = sum(1 for r in results if r.blocked)
    failed = total - passed
    print("=" * 88)
    print(f"SUMMARY: total={total}, passed={passed}, failed={failed}")
    if failed:
        print("Verdict: POSSIBLE VALIDATION GAPS on one or more endpoints.")
        return 1
    print("Verdict: All tested endpoints blocked malicious aws-file_link values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
