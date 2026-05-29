"""Configuration from environment."""
import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "scheduler_db")

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
RUNNER_INTERVAL_SECONDS = int(os.getenv("RUNNER_INTERVAL_SECONDS", "15"))
# Webhook POST timeout (GRC self-heal can be slow when sending many emails).
WEBHOOK_TIMEOUT_SECONDS = float(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "120"))

# GRC policy self-heal webhook (optional; used by fix_schedule_webhook.py)
GRC_SELF_HEAL_WEBHOOK_URL = os.getenv(
    "GRC_SELF_HEAL_WEBHOOK_URL",
    "http://127.0.0.1:8000/api/policies/self-healing/reminders/run/",
).strip()
GRC_SELF_HEAL_CRON_SECRET = os.getenv("GRC_SELF_HEAL_CRON_SECRET", "").strip()

# GRC scheduled audits webhook (optional; used by fix_schedule_webhook.py)
GRC_SCHEDULED_AUDITS_WEBHOOK_URL = os.getenv(
    "GRC_SCHEDULED_AUDITS_WEBHOOK_URL",
    "http://127.0.0.1:8000/api/audits/scheduling/run/",
).strip()
