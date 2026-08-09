"""
One-time migration: convert daily_logs.log_date from VARCHAR to DATE.

Existing values must be in 'YYYY-MM-DD' format (the HTML date input already
produces this), so MySQL can coerce them in place. Safe to run repeatedly.

Usage (from the backend/ directory):
    python migrate_log_date.py
"""
import logging

from sqlalchemy import text
from core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_log_date")


def main():
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE daily_logs MODIFY COLUMN log_date DATE NULL"
        ))
    logger.info("OK: daily_logs.log_date is now DATE.")


if __name__ == "__main__":
    main()
