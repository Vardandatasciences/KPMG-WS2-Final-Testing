import os
import sys
import threading
import time

from django.apps import AppConfig


def _run_scheduled_ai_audits_loop():
    """Background loop: every 60 seconds run due AI audit schedules (only when Django runserver is used)."""
    time.sleep(15)  # Let DB and app finish starting
    while True:
        try:
            from django.core.management import call_command
            call_command("run_scheduled_ai_audits", verbosity=0)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Scheduled AI audits check failed: %s", e)
        time.sleep(60)


def _run_policy_self_heal_loop():
    """Background loop: run policy review reminders on an interval (default once per day)."""
    import logging

    logger = logging.getLogger(__name__)
    try:
        interval = int(os.environ.get("POLICY_SELF_HEAL_INTERVAL_SECONDS", "86400"))
    except (TypeError, ValueError):
        interval = 86400
    interval = max(60, interval)  # allow 60s for dev; default 86400 for prod-like runs
    time.sleep(min(30, interval))  # short startup delay before first run
    logger.warning(
        "Policy self-heal inline scheduler started (interval=%ss). "
        "Set ENABLE_POLICY_SELF_HEAL_SCHEDULER=false when using Scheduler microservice.",
        interval,
    )
    while True:
        try:
            from grc.routes.Policy.policy_self_healing import execute_policy_self_heal_reminders

            result = execute_policy_self_heal_reminders()
            msg = (
                f"Policy self-heal reminders: date={result.get('date')} "
                f"sent={result.get('sent')} skipped={result.get('skipped')}"
            )
            logger.warning(msg)
            print(f"[POLICY_SELF_HEAL] {msg}", flush=True)
        except Exception as e:
            logger.warning("Policy self-heal reminder run failed: %s", e)
            print(f"[POLICY_SELF_HEAL] run failed: {e}", flush=True)
        time.sleep(interval)


def _run_scheduled_audits_loop():
    """Background loop: recurring audits, due reminders, overdue escalation."""
    import logging

    logger = logging.getLogger(__name__)
    try:
        interval = int(os.environ.get("SCHEDULED_AUDITS_INTERVAL_SECONDS", "86400"))
    except (TypeError, ValueError):
        interval = 86400
    interval = max(300, interval)
    time.sleep(min(45, interval))
    logger.warning(
        "Scheduled audits inline scheduler started (interval=%ss). "
        "Set ENABLE_SCHEDULED_AUDITS_SCHEDULER=false when using Scheduler microservice.",
        interval,
    )
    while True:
        try:
            from grc.services.audit_recurrence_service import process_audit_recurrence_and_escalations

            result = process_audit_recurrence_and_escalations()
            msg = (
                f"Scheduled audits: reminders={result.get('reminders')} "
                f"escalations={result.get('escalations')} recurrences={result.get('recurrences_created')}"
            )
            logger.warning(msg)
            print(f"[SCHEDULED_AUDITS] {msg}", flush=True)
        except Exception as e:
            logger.warning("Scheduled audits run failed: %s", e)
            print(f"[SCHEDULED_AUDITS] run failed: {e}", flush=True)
        time.sleep(interval)


class GrcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "grc"

    def ready(self):
        # Import signal handlers when the app is ready
        import grc.signals.event_signals
        # MULTI-TENANCY: Import tenant signals for automatic tenant_id assignment
        import grc.tenant_signals  # This registers the auto_set_tenant signal

        # Start background scheduler for AI audit schedules when running under runserver.
        # In local debug, default OFF to avoid adding DB load to request latency tests.
        scheduler_enabled = os.environ.get("ENABLE_INLINE_AUDIT_SCHEDULER")
        if scheduler_enabled is None:
            scheduler_enabled = "false" if os.environ.get("DJANGO_DEBUG", "false").lower() == "true" else "true"

        if (
            scheduler_enabled.lower() == "true"
            and "runserver" in sys.argv
            and os.environ.get("RUN_MAIN") == "true"
        ):
            thread = threading.Thread(target=_run_scheduled_ai_audits_loop, daemon=True)
            thread.start()

        # Policy renewal reminders (daily by default). Manual: manage.py run_policy_self_heal_reminders
        self_heal_enabled = os.environ.get("ENABLE_POLICY_SELF_HEAL_SCHEDULER")
        if self_heal_enabled is None:
            self_heal_enabled = "false" if os.environ.get("DJANGO_DEBUG", "false").lower() == "true" else "true"

        if (
            self_heal_enabled.lower() == "true"
            and "runserver" in sys.argv
            and os.environ.get("RUN_MAIN") == "true"
        ):
            threading.Thread(target=_run_policy_self_heal_loop, daemon=True).start()

        # Default OFF: run via cron/webhook (manage.py run_scheduled_audits) to avoid flooding logs on dev
        audits_scheduler_enabled = os.environ.get("ENABLE_SCHEDULED_AUDITS_SCHEDULER", "false")

        if (
            audits_scheduler_enabled.lower() == "true"
            and "runserver" in sys.argv
            and os.environ.get("RUN_MAIN") == "true"
        ):
            threading.Thread(target=_run_scheduled_audits_loop, daemon=True).start()

        # Pre-warm embedding model on startup so first API request doesn't OOM
        if os.environ.get("RUN_MAIN") == "true":
            def _prewarm_embedding():
                try:
                    from grc.services.embedding_service import EmbeddingService
                    EmbeddingService()
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"[Startup] Embedding model pre-warm failed: {e}")
            threading.Thread(target=_prewarm_embedding, daemon=True).start()
