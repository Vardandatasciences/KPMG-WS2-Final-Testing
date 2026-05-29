"""Entry point: init DB, start background runner, run API server."""
import logging
import sys

import uvicorn

import api
import config
import database
from runner import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def on_startup():
    logger.info(
        "Config: MYSQL_HOST=%s MYSQL_PORT=%s MYSQL_DATABASE=%s API=%s:%s RUNNER_INTERVAL=%ss",
        config.MYSQL_HOST, config.MYSQL_PORT, config.MYSQL_DATABASE,
        config.API_HOST, config.API_PORT, config.RUNNER_INTERVAL_SECONDS,
    )
    logger.info("Application startup: initializing database...")
    database.init_db()
    logger.info("Application startup: starting scheduler runner...")
    start_scheduler()
    logger.info("Application startup: mounting static files...")
    api.mount_static()
    logger.info("Application startup complete. Open in browser: http://localhost:%s", config.API_PORT)


if __name__ == "__main__":
    api.app.add_event_handler("startup", on_startup)
    uvicorn.run(
        "api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,
    )
