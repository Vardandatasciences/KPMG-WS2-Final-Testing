"""REST API for the generic scheduler microservice."""
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import config
import database
from schedule_logic import compute_next_run, day_to_cron_dow

logger = logging.getLogger(__name__)

app = FastAPI(title="Scheduler Microservice", version="1.0.0")

# --- Request/Response models ---


class ScheduleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    schedule_type: str = Field(
        ...,
        description="one_week | one_minute | exact_date | daily | monthly | recurring | every_minute | cron"
    )
    scheduled_at: Optional[str] = None
    cron_expression: Optional[str] = None
    start_date: Optional[str] = None
    # For daily: hour, minute; for monthly: day_of_month, hour, minute; for recurring: day_of_week, hour, minute
    hour: Optional[int] = Field(None, ge=0, le=23)
    minute: Optional[int] = Field(None, ge=0, le=59)
    day_of_month: Optional[int] = Field(None, ge=1, le=28)
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="0=Mon, 6=Sun")
    timezone_offset_minutes: Optional[int] = Field(None, description="Client offset (e.g. -getTimezoneOffset()); for daily/monthly/recurring local time")
    action_type: Optional[str] = Field("webhook", description="webhook | get_url | open_file | run_command")
    callback_url: Optional[str] = None
    target: Optional[str] = None
    payload: Optional[dict] = None


class ScheduleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    action_type: Optional[str] = None
    callback_url: Optional[str] = None
    target: Optional[str] = None
    payload: Optional[dict] = None


def _parse_datetime(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    s = str(s).strip().replace("Z", "").replace("+00:00", "").split(".")[0]
    for fmt in (
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y",
    ):
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _row_to_schedule(row: dict) -> dict:
    out = {
        "id": row["id"],
        "name": row["name"],
        "schedule_type": row["schedule_type"],
        "cron_expression": row["cron_expression"],
        "scheduled_at": row["scheduled_at"].isoformat() if row.get("scheduled_at") else None,
        "start_date": row["start_date"].isoformat() if row.get("start_date") else None,
        "next_run_at": row["next_run_at"].isoformat() if row.get("next_run_at") else None,
        "last_run_at": row["last_run_at"].isoformat() if row.get("last_run_at") else None,
        "is_active": bool(row["is_active"]),
        "action_type": row.get("action_type") or "webhook",
        "callback_url": row.get("callback_url"),
        "target": row.get("target"),
        "payload": row.get("payload"),
        "timezone_offset_minutes": row.get("timezone_offset_minutes"),
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }
    return out


VALID_SCHEDULE_TYPES = (
    "one_week", "one_minute", "exact_date", "daily", "monthly",
    "recurring", "every_minute", "cron"
)


@app.post("/api/schedules", status_code=201)
def create_schedule(body: ScheduleCreate):
    logger.info("POST /api/schedules: name=%r, schedule_type=%s", body.name, body.schedule_type)
    if body.schedule_type not in VALID_SCHEDULE_TYPES:
        logger.warning("Invalid schedule_type: %s", body.schedule_type)
        raise HTTPException(400, "Invalid schedule_type")

    scheduled_at = None
    cron_expression = None
    start_date = _parse_datetime(body.start_date)

    if body.schedule_type == "one_week":
        scheduled_at = _parse_datetime(body.scheduled_at) or (datetime.utcnow() + timedelta(days=7))
    elif body.schedule_type == "one_minute":
        scheduled_at = datetime.utcnow() + timedelta(minutes=1)
    elif body.schedule_type == "exact_date":
        if not body.scheduled_at:
            logger.warning("exact_date missing scheduled_at")
            raise HTTPException(400, "scheduled_at required for exact_date")
        scheduled_at = _parse_datetime(body.scheduled_at)
        if not scheduled_at:
            logger.warning("Invalid scheduled_at format: %r", body.scheduled_at)
            raise HTTPException(400, "Invalid scheduled_at format")
    elif body.schedule_type == "every_minute":
        cron_expression = "* * * * *"
    elif body.schedule_type == "daily":
        h = body.hour if body.hour is not None else 9
        m = body.minute if body.minute is not None else 0
        cron_expression = f"{m} {h} * * *"
    elif body.schedule_type == "monthly":
        dom = max(1, min(28, body.day_of_month or 1))
        h = body.hour if body.hour is not None else 9
        m = body.minute if body.minute is not None else 0
        cron_expression = f"{m} {h} {dom} * *"
    elif body.schedule_type == "recurring":
        dow = body.day_of_week if body.day_of_week is not None else 1
        h = body.hour if body.hour is not None else 9
        m = body.minute if body.minute is not None else 0
        cron_dow = day_to_cron_dow(dow)
        cron_expression = f"{m} {h} * * {cron_dow}"
    elif body.schedule_type == "cron":
        cron_expression = (body.cron_expression or "").strip()
        if not cron_expression:
            logger.warning("cron type missing cron_expression")
            raise HTTPException(400, "cron_expression required for cron (5 fields)")
        if len(cron_expression.split()) != 5:
            logger.warning("cron_expression invalid (not 5 fields): %r", cron_expression)
            raise HTTPException(400, "cron_expression must have 5 fields: minute hour day month day_of_week")

    base = start_date if (start_date and body.schedule_type in ("recurring", "daily", "monthly", "every_minute", "cron")) else None
    tz_offset = body.timezone_offset_minutes if body.timezone_offset_minutes is not None else None
    if body.schedule_type in ("daily", "monthly", "recurring"):
        logger.info("Schedule create: type=%s hour=%s minute=%s timezone_offset_minutes=%s", body.schedule_type, getattr(body, "hour", None), getattr(body, "minute", None), tz_offset)
    next_run = compute_next_run(body.schedule_type, scheduled_at, cron_expression, start_date=start_date, base_time=base, timezone_offset_minutes=tz_offset)
    if not next_run:
        logger.warning("Could not compute next_run for type=%s cron=%r", body.schedule_type, cron_expression)
        raise HTTPException(400, "Could not compute next run time. Check cron_expression or install croniter.")
    if start_date and next_run < start_date:
        next_run = start_date

    action_type = (body.action_type or "webhook").strip().lower()
    if action_type not in ("webhook", "get_url", "open_file", "run_command"):
        action_type = "webhook"
    if action_type == "webhook" and not (body.callback_url or "").strip():
        raise HTTPException(400, "callback_url required for action_type webhook")
    if action_type == "get_url" and not (body.callback_url or body.target or "").strip():
        raise HTTPException(400, "callback_url or target (URL) required for action_type get_url")
    if action_type == "open_file" and not (body.target or "").strip():
        raise HTTPException(400, "target (file path) required for action_type open_file")
    if action_type == "run_command" and not (body.target or "").strip():
        raise HTTPException(400, "target (command) required for action_type run_command")

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO schedules
                (name, schedule_type, cron_expression, scheduled_at, start_date, next_run_at, is_active, action_type, callback_url, target, payload, timezone_offset_minutes)
                VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s, %s, %s, %s)
                """,
                (
                    body.name,
                    body.schedule_type,
                    cron_expression or None,
                    scheduled_at,
                    start_date,
                    next_run,
                    action_type,
                    body.callback_url or None,
                    (body.target or "").strip() or None,
                    json.dumps(body.payload) if body.payload is not None else None,
                    tz_offset,
                ),
            )
            conn.commit()
            sid = cur.lastrowid
            cur.execute("SELECT * FROM schedules WHERE id = %s", (sid,))
            row = cur.fetchone()
        logger.info("Schedule created: id=%s name=%r next_run_at=%s", sid, body.name, next_run)
        return {"success": True, "schedule": _row_to_schedule(row)}
    except Exception as e:
        logger.exception("Create schedule failed: %s", e)
        raise HTTPException(500, str(e))
    finally:
        conn.close()


@app.get("/api/schedules")
def list_schedules(active_only: bool = False):
    logger.debug("GET /api/schedules active_only=%s", active_only)
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            if active_only:
                cur.execute("SELECT * FROM schedules WHERE is_active = 1 ORDER BY next_run_at ASC")
            else:
                cur.execute("SELECT * FROM schedules ORDER BY created_at DESC")
            rows = cur.fetchall()
        logger.debug("List schedules: count=%s", len(rows))
        return {"success": True, "schedules": [_row_to_schedule(r) for r in rows]}
    finally:
        conn.close()


@app.get("/api/schedules/{schedule_id}")
def get_schedule(schedule_id: int):
    logger.debug("GET /api/schedules/%s", schedule_id)
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM schedules WHERE id = %s", (schedule_id,))
            row = cur.fetchone()
        if not row:
            logger.warning("Schedule not found: id=%s", schedule_id)
            raise HTTPException(404, "Schedule not found")
        return {"success": True, "schedule": _row_to_schedule(row)}
    finally:
        conn.close()


@app.patch("/api/schedules/{schedule_id}")
def update_schedule(schedule_id: int, body: ScheduleUpdate):
    logger.info("PATCH /api/schedules/%s: name=%s is_active=%s", schedule_id, body.name, body.is_active)
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM schedules WHERE id = %s", (schedule_id,))
            row = cur.fetchone()
        if not row:
            logger.warning("Schedule not found for update: id=%s", schedule_id)
            raise HTTPException(404, "Schedule not found")
        updates = []
        params = []
        if body.name is not None:
            updates.append("name = %s")
            params.append(body.name)
        if body.is_active is not None:
            updates.append("is_active = %s")
            params.append(1 if body.is_active else 0)
        if body.action_type is not None:
            updates.append("action_type = %s")
            params.append((body.action_type or "webhook").strip().lower())
        if body.callback_url is not None:
            updates.append("callback_url = %s")
            params.append(body.callback_url)
        if body.target is not None:
            updates.append("target = %s")
            params.append(body.target)
        if body.payload is not None:
            updates.append("payload = %s")
            params.append(json.dumps(body.payload))
        if not updates:
            return {"success": True, "schedule": _row_to_schedule(row)}
        params.append(schedule_id)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE schedules SET " + ", ".join(updates) + " WHERE id = %s",
                params,
            )
            conn.commit()
            cur.execute("SELECT * FROM schedules WHERE id = %s", (schedule_id,))
            row = cur.fetchone()
        logger.info("Schedule updated: id=%s", schedule_id)
        return {"success": True, "schedule": _row_to_schedule(row)}
    finally:
        conn.close()


@app.delete("/api/schedules/{schedule_id}")
def delete_schedule(schedule_id: int):
    logger.info("DELETE /api/schedules/%s", schedule_id)
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
            conn.commit()
            if cur.rowcount == 0:
                logger.warning("Schedule not found for delete: id=%s", schedule_id)
                raise HTTPException(404, "Schedule not found")
        logger.info("Schedule deleted: id=%s", schedule_id)
        return {"success": True, "message": "Schedule deleted"}
    finally:
        conn.close()


@app.get("/api/schedules/{schedule_id}/runs")
def list_schedule_runs(schedule_id: int, limit: int = 20):
    logger.debug("GET /api/schedules/%s/runs limit=%s", schedule_id, limit)
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM schedules WHERE id = %s", (schedule_id,))
            if not cur.fetchone():
                logger.warning("Schedule not found for runs: id=%s", schedule_id)
                raise HTTPException(404, "Schedule not found")
            cur.execute(
                "SELECT * FROM schedule_runs WHERE schedule_id = %s ORDER BY started_at DESC LIMIT %s",
                (schedule_id, min(limit, 100)),
            )
            rows = cur.fetchall()
        logger.debug("List runs for schedule %s: count=%s", schedule_id, len(rows))
        runs = [
            {
                "id": r["id"],
                "schedule_id": r["schedule_id"],
                "started_at": r["started_at"].isoformat() if r.get("started_at") else None,
                "finished_at": r["finished_at"].isoformat() if r.get("finished_at") else None,
                "status": r["status"],
                "response_summary": r.get("response_summary"),
                "error_message": r.get("error_message"),
            }
            for r in rows
        ]
        return {"success": True, "runs": runs}
    finally:
        conn.close()


# --- Serve UI ---


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    logger.debug("GET / serving UI")
    path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    logger.warning("Static index.html not found at %s", path)
    return "<h1>Scheduler API</h1><p>API is running. Mount static files or add index.html.</p>"


def mount_static():
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info("Static files mounted at /static")
    else:
        logger.warning("Static directory not found: %s", static_dir)
