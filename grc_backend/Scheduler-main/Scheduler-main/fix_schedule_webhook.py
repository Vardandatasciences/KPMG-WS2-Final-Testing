"""
Update GRC webhook schedule(s) with correct URL and cron secret.

Usage (from Scheduler-main/Scheduler-main):
  python fix_schedule_webhook.py 703          # policy self-heal
  python fix_schedule_webhook.py 704 --audits # scheduled audits
  python fix_schedule_webhook.py 703 704 --audits 704 only audits URL for 704
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

import config
import database

def _load_secret_from_grc_env() -> str:
    if config.GRC_SELF_HEAL_CRON_SECRET:
        return config.GRC_SELF_HEAL_CRON_SECRET
    grc_env = Path(__file__).resolve().parents[2] / ".env"
    if grc_env.is_file():
        for line in grc_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("POLICY_SELF_HEAL_CRON_SECRET="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
            if line.startswith("SCHEDULED_AUDITS_CRON_SECRET="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val
    return ""


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--audits"]
    audits_mode_ids = set()
    if "--audits" in sys.argv[1:]:
        # --audits applies to all ids listed after it, or all ids if flag present
        audits_mode_ids = {int(x) for x in args if x.isdigit()}

    schedule_ids = [int(x) for x in args if x.isdigit()] if args else [703]
    secret = _load_secret_from_grc_env()
    if not secret:
        print("ERROR: Set POLICY_SELF_HEAL_CRON_SECRET in grc_backend/.env")
        sys.exit(1)

    policy_url = config.GRC_SELF_HEAL_WEBHOOK_URL
    audits_url = config.GRC_SCHEDULED_AUDITS_WEBHOOK_URL
    for u in (policy_url, audits_url):
        if u and not u.endswith("/"):
            pass  # Django accepts both; keep as configured

    payload_json = json.dumps({"secret": secret})

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            for sid in schedule_ids:
                use_audits = sid in audits_mode_ids or (
                    "--audits" in sys.argv[1:] and len(schedule_ids) == 1
                )
                # If only one id and name suggests audits, or explicit --audits with that id
                if not use_audits and len(schedule_ids) == 1 and sid == schedule_ids[0]:
                    cur.execute("SELECT name, callback_url FROM schedules WHERE id = %s", (sid,))
                    row = cur.fetchone()
                    if row:
                        name = (row.get("name") or "").lower()
                        cb = (row.get("callback_url") or "").lower()
                        if "audit" in name or "audits/scheduling" in cb or "<django_port>" in cb:
                            use_audits = True
                url = audits_url if use_audits else policy_url
                if not url.endswith("/"):
                    url = url + "/"
                cur.execute(
                    """
                    UPDATE schedules
                    SET callback_url = %s, payload = CAST(%s AS JSON), action_type = 'webhook', is_active = 1
                    WHERE id = %s
                    """,
                    (url, payload_json, sid),
                )
                print(f"Updated schedule id={sid} -> {url}")
        conn.commit()
    finally:
        conn.close()

    test_url = audits_url if 704 in schedule_ids or audits_mode_ids else policy_url
    if not test_url.endswith("/"):
        test_url += "/"
    print("Testing webhook...")
    try:
        r = httpx.post(
            test_url,
            json={"secret": secret},
            headers={"X-Policy-Self-Heal-Secret": secret},
            timeout=30.0,
            follow_redirects=False,
        )
        print(f"HTTP {r.status_code}: {(r.text or '')[:300]}")
        if r.status_code >= 400:
            sys.exit(1)
    except httpx.ConnectError as e:
        print(f"ERROR: Cannot reach Django at {test_url} — start runserver on port 8000. ({e})")
        sys.exit(1)


if __name__ == "__main__":
    main()
