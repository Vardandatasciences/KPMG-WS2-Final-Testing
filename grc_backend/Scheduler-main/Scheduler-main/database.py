"""MySQL connection and table setup for the scheduler microservice."""
import logging
import pymysql
from pymysql.cursors import DictCursor

import config

logger = logging.getLogger(__name__)


def get_connection():
    """Return a new MySQL connection (caller must close it)."""
    logger.debug("Opening MySQL connection to %s:%s/%s", config.MYSQL_HOST, config.MYSQL_PORT, config.MYSQL_DATABASE)
    return pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
    )


def init_db():
    """Create database if not exists, then create tables."""
    logger.info("Initializing database: %s@%s:%s", config.MYSQL_USER, config.MYSQL_HOST, config.MYSQL_PORT)
    conn = pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info("Database %s ensured", config.MYSQL_DATABASE)
        conn.select_db(config.MYSQL_DATABASE)
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    schedule_type VARCHAR(50) NOT NULL,
                    cron_expression VARCHAR(255) NULL,
                    scheduled_at DATETIME NULL,
                    start_date DATETIME NULL,
                    next_run_at DATETIME NULL,
                    last_run_at DATETIME NULL,
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
                    action_type VARCHAR(50) NOT NULL DEFAULT 'webhook',
                    callback_url VARCHAR(2048) NULL,
                    target VARCHAR(2048) NULL,
                    payload JSON NULL,
                    timezone_offset_minutes INT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_next_run (is_active, next_run_at),
                    INDEX idx_schedule_type (schedule_type)
                )
            """)
            logger.debug("Table schedules ensured")
            # Migration: add timezone_offset_minutes if missing (for daily/monthly/recurring local time)
            cur.execute(
                "SELECT COUNT(*) AS n FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'schedules' AND COLUMN_NAME = 'timezone_offset_minutes'",
                (config.MYSQL_DATABASE,),
            )
            row_tz = cur.fetchone()
            has_tz = (row_tz[0] if isinstance(row_tz, (list, tuple)) else row_tz.get("n", 0)) != 0
            if not has_tz:
                cur.execute("ALTER TABLE schedules ADD COLUMN timezone_offset_minutes INT NULL AFTER payload")
                logger.info("Added timezone_offset_minutes column to schedules")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schedule_runs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    schedule_id INT NOT NULL,
                    started_at DATETIME NOT NULL,
                    finished_at DATETIME NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'running',
                    response_summary JSON NULL,
                    error_message TEXT NULL,
                    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
                    INDEX idx_schedule_id (schedule_id),
                    INDEX idx_started_at (started_at)
                )
            """)
            logger.debug("Table schedule_runs ensured")
            # Migration: add action_type and target if missing (existing DBs)
            cur.execute(
                "SELECT COUNT(*) AS n FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'schedules' AND COLUMN_NAME = 'action_type'",
                (config.MYSQL_DATABASE,),
            )
            row = cur.fetchone()
            has_action_type = (row[0] if isinstance(row, (list, tuple)) else row.get("n", 0)) != 0
            if not has_action_type:
                cur.execute("ALTER TABLE schedules ADD COLUMN action_type VARCHAR(50) NOT NULL DEFAULT 'webhook' AFTER is_active")
                cur.execute("ALTER TABLE schedules ADD COLUMN target VARCHAR(2048) NULL AFTER callback_url")
                logger.info("Added action_type and target columns to schedules")
            # timezone_offset_minutes already added above if table was just created
        logger.info("Database and tables initialized successfully.")
    finally:
        conn.close()
