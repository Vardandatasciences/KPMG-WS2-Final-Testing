"""Background runner: every N seconds find due schedules and execute them."""
import ast
import json
import logging
import os
import platform
import subprocess
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

import httpx

import config
import database
from schedule_logic import compute_next_run

logger = logging.getLogger(__name__)
_scheduler_started = False
STALE_MINUTES = 30

VALID_ACTION_TYPES = ("webhook", "get_url", "open_file", "run_command")


def _normalize_webhook_payload(payload) -> dict:
    """Accept JSON object, JSON string, or Python dict literal from DB/UI."""
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(text)
                return parsed if isinstance(parsed, dict) else {}
            except (ValueError, SyntaxError):
                return {}
    return {}


def _execute_schedule(schedule: dict) -> dict:
    """Execute one schedule based on action_type. Return result dict."""
    action_type = (schedule.get("action_type") or "webhook").strip().lower()
    if action_type not in VALID_ACTION_TYPES:
        action_type = "webhook"

    sid = schedule.get("id")
    name = schedule.get("name")

    if action_type == "webhook":
        url = (schedule.get("callback_url") or "").strip()
        if not url:
            logger.warning("Schedule id=%s has no callback_url", sid)
            return {"success": False, "error": "No callback_url configured"}
        logger.info("Executing schedule id=%s name=%r [webhook] -> POST %s", sid, name, url)
        payload = _normalize_webhook_payload(schedule.get("payload"))
        headers = {}
        secret = None
        if isinstance(payload, dict):
            secret = (payload.get("secret") or payload.get("cron_secret") or "").strip() or None
        if secret:
            headers["X-Policy-Self-Heal-Secret"] = secret
        timeout_s = float(getattr(config, "WEBHOOK_TIMEOUT_SECONDS", 120) or 120)
        try:
            with httpx.Client(timeout=timeout_s, follow_redirects=False) as client:
                r = client.post(url, json=payload if isinstance(payload, dict) else (payload or {}), headers=headers)
                ok = 200 <= r.status_code < 300
                body_preview = (r.text or "")[:500]
                if ok:
                    logger.info("Webhook response id=%s: status=%s success=True", sid, r.status_code)
                else:
                    logger.warning(
                        "Webhook response id=%s: status=%s body=%s",
                        sid,
                        r.status_code,
                        body_preview,
                    )
                return {"success": ok, "status_code": r.status_code, "body": r.text[:2000] if r.text else None}
        except Exception as e:
            logger.exception("Webhook failed for schedule %s: %s", sid, e)
            return {"success": False, "error": str(e)}

    if action_type == "get_url":
        url = (schedule.get("callback_url") or schedule.get("target") or "").strip()
        if not url:
            logger.warning("Schedule id=%s has no URL for get_url", sid)
            return {"success": False, "error": "No URL configured"}
        logger.info("Executing schedule id=%s name=%r [get_url] -> GET %s", sid, name, url)
        try:
            with httpx.Client(timeout=30.0) as client:
                r = client.get(url)
                ok = 200 <= r.status_code < 300
                logger.info("GET response id=%s: status=%s success=%s", sid, r.status_code, ok)
                return {"success": ok, "status_code": r.status_code, "body": r.text[:2000] if r.text else None}
        except Exception as e:
            logger.exception("GET URL failed for schedule %s: %s", sid, e)
            return {"success": False, "error": str(e)}

    if action_type == "open_file":
        path = (schedule.get("target") or "").strip()
        if not path:
            logger.warning("Schedule id=%s has no target (file path) for open_file", sid)
            return {"success": False, "error": "No file path configured"}
        path = path.replace("file:///", "").strip()
        logger.info("Executing schedule id=%s name=%r [open_file] -> %s", sid, name, path)
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path], check=False, timeout=10)
            else:
                subprocess.run(["xdg-open", path], check=False, timeout=10)
            logger.info("Open file id=%s: opened", sid)
            return {"success": True, "message": "File opened with default app"}
        except Exception as e:
            logger.exception("Open file failed for schedule %s: %s", sid, e)
            return {"success": False, "error": str(e)}

    if action_type == "run_command":
        cmd = (schedule.get("target") or "").strip()
        if not cmd:
            logger.warning("Schedule id=%s has no target (command) for run_command", sid)
            return {"success": False, "error": "No command configured"}
        # If target is a URL, call it with GET (avoids Windows shell quoting issues)
        cmd_lower = cmd.lower().strip()
        if cmd_lower.startswith("http://") or cmd_lower.startswith("https://"):
            logger.info("Executing schedule id=%s name=%r [run_command as GET URL] -> %s", sid, name, cmd[:200])
            try:
                with httpx.Client(timeout=30.0) as client:
                    r = client.get(cmd)
                    ok = 200 <= r.status_code < 300
                    logger.info("Run command (GET URL) id=%s: status=%s success=%s", sid, r.status_code, ok)
                    return {
                        "success": ok,
                        "returncode": 0 if ok else 1,
                        "stdout": (r.text or "")[:1000],
                        "stderr": "" if ok else (r.text or "")[:500],
                    }
            except Exception as e:
                logger.exception("Run command (GET URL) failed for schedule %s: %s", sid, e)
                return {"success": False, "error": str(e)}
        logger.info("Executing schedule id=%s name=%r [run_command] -> %s", sid, name, cmd[:200])
        try:
            result = subprocess.run(cmd, shell=True, timeout=60, capture_output=True, text=True)
            ok = result.returncode == 0
            logger.info("Run command id=%s: returncode=%s success=%s", sid, result.returncode, ok)
            return {
                "success": ok,
                "returncode": result.returncode,
                "stdout": (result.stdout or "")[:1000],
                "stderr": (result.stderr or "")[:1000],
            }
        except subprocess.TimeoutExpired:
            logger.warning("Run command id=%s timed out", sid)
            return {"success": False, "error": "Command timed out (60s)"}
        except Exception as e:
            logger.exception("Run command failed for schedule %s: %s", sid, e)
            return {"success": False, "error": str(e)}

    return {"success": False, "error": f"Unknown action_type: {action_type}"}


def _seconds_until_next_due(conn) -> Optional[float]:
    """Seconds until the earliest active schedule's next_run_at (UTC), or None."""
    now = datetime.utcnow()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT next_run_at FROM schedules
                WHERE is_active = 1 AND next_run_at IS NOT NULL
                ORDER BY next_run_at ASC LIMIT 1
                """
            )
            row = cur.fetchone()
        if not row or not row.get("next_run_at"):
            return None
        return (row["next_run_at"] - now).total_seconds()
    except Exception:
        return None


def _log_next_due_hint(conn, now: datetime) -> None:
    """INFO log so the console shows the runner is alive when nothing is due yet."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, next_run_at FROM schedules
                WHERE is_active = 1 AND next_run_at IS NOT NULL
                ORDER BY next_run_at ASC LIMIT 1
                """
            )
            row = cur.fetchone()
        if not row:
            logger.info("Runner check: no active schedules (create one at http://localhost:%s)", config.API_PORT)
            return
        nra = row.get("next_run_at")
        if nra and nra <= now:
            logger.info("Runner check: schedule id=%s %r should be due (next_run_at=%s)", row["id"], row.get("name"), nra)
        else:
            secs = int((nra - now).total_seconds()) if nra else None
            logger.info(
                "Runner check: nothing due yet — next id=%s %r at %s UTC (~%ss)",
                row["id"],
                row.get("name"),
                nra,
                secs if secs is not None else "?",
            )
    except Exception as e:
        logger.debug("Could not log next due hint: %s", e)


def _run_check():
    """Find due schedules, execute them, update next_run_at and run history."""
    logger.debug("Runner check: looking for due schedules")
    conn = database.get_connection()
    try:
        now = datetime.utcnow()
        stale = now - timedelta(minutes=STALE_MINUTES)
        with conn.cursor() as cur:
            # Mark stale running runs as failed
            cur.execute(
                "UPDATE schedule_runs SET status = 'failed', finished_at = %s, error_message = 'Run timed out or interrupted' WHERE status = 'running' AND started_at < %s",
                (now, stale),
            )
            if cur.rowcount > 0:
                logger.info("Marked %s stale run(s) as failed", cur.rowcount)
            conn.commit()
            # Schedules that are due and don't have a recent running run
            cur.execute(
                """
                SELECT s.* FROM schedules s
                WHERE s.is_active = 1 AND s.next_run_at IS NOT NULL AND s.next_run_at <= %s
                AND NOT EXISTS (
                    SELECT 1 FROM schedule_runs r
                    WHERE r.schedule_id = s.id AND r.status = 'running' AND r.started_at >= %s
                )
                ORDER BY s.next_run_at ASC
                """,
                (now, stale),
            )
            rows = cur.fetchall()
        if not rows:
            _log_next_due_hint(conn, now)
            return 0
        logger.info("Found %d due schedule(s), executing...", len(rows))
        executed = 0
        for row in rows:
            sid = row["id"]
            run_id = None
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO schedule_runs (schedule_id, started_at, status) VALUES (%s, %s, 'running')",
                        (sid, now),
                    )
                    conn.commit()
                    run_id = cur.lastrowid
                result = _execute_schedule(row)
                summary = json.dumps(result)
                status = "success" if result.get("success") else "failed"
                err = None if result.get("success") else result.get("error") or result.get("body") or "Unknown"
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE schedule_runs SET finished_at = %s, status = %s, response_summary = %s, error_message = %s WHERE id = %s",
                        (now, status, summary, err, run_id),
                    )
                    cur.execute(
                        "UPDATE schedules SET last_run_at = %s WHERE id = %s",
                        (now, sid),
                    )
                    schedule_type = row.get("schedule_type") or ""
                    if schedule_type in ("recurring", "daily", "monthly", "every_minute", "cron"):
                        next_run = compute_next_run(
                            schedule_type,
                            row.get("scheduled_at"),
                            row.get("cron_expression"),
                            row.get("start_date"),
                            base_time=now,
                            timezone_offset_minutes=row.get("timezone_offset_minutes"),
                        )
                        cur.execute(
                            "UPDATE schedules SET next_run_at = %s WHERE id = %s",
                            (next_run, sid),
                        )
                    else:
                        cur.execute(
                            "UPDATE schedules SET next_run_at = NULL, is_active = 0 WHERE id = %s",
                            (sid,),
                        )
                    conn.commit()
                logger.info("Schedule id=%s name=%r completed: status=%s", sid, row.get("name"), status)
                executed += 1
            except Exception as e:
                logger.exception("Schedule %s run failed: %s", sid, e)
                if run_id and conn:
                    try:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE schedule_runs SET finished_at = %s, status = 'failed', error_message = %s WHERE id = %s",
                                (now, str(e), run_id),
                            )
                            conn.commit()
                    except Exception:
                        pass
        return executed
    except Exception as e:
        logger.exception("Runner check failed: %s", e)
        return 0
    finally:
        if conn:
            conn.close()


def _sleep_until_next_due() -> None:
    """Align checks with next_run_at so every_minute jobs are not missed between polls."""
    conn = None
    try:
        conn = database.get_connection()
        secs = _seconds_until_next_due(conn)
    except Exception:
        secs = None
    finally:
        if conn:
            conn.close()

    interval = max(1, config.RUNNER_INTERVAL_SECONDS)
    if secs is None:
        time.sleep(interval)
        return
    if secs <= 0:
        return
    # Wake shortly after next_run_at, but never sleep longer than one poll interval
    wait = min(interval, max(0.25, secs + 0.25))
    if wait < interval:
        logger.info("Runner sleeping %.1fs until next due schedule", wait)
    time.sleep(wait)


def _loop():
    while True:
        try:
            _run_check()
        except Exception as e:
            logger.exception("Scheduler loop error: %s", e)
        _sleep_until_next_due()


def start_scheduler():
    """Start the background scheduler thread."""
    global _scheduler_started
    if _scheduler_started:
        return
    _scheduler_started = True
    t = threading.Thread(target=_loop, daemon=True, name="SchedulerRunner")
    t.start()
    logger.info("Scheduler runner started (interval=%s seconds)", config.RUNNER_INTERVAL_SECONDS)
