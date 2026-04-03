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


class GrcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "grc"

    def ready(self):
        # Import signal handlers when the app is ready
        import grc.signals.event_signals
        # MULTI-TENANCY: Import tenant signals for automatic tenant_id assignment
        import grc.tenant_signals  # This registers the auto_set_tenant signal

        # Start background scheduler for AI audit schedules when running under runserver
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") == "true":
            thread = threading.Thread(target=_run_scheduled_ai_audits_loop, daemon=True)
            thread.start()
