import logging
import sqlite3
from datetime import datetime

from app.database.schema import (
    ALL_TABLES,
    CREATE_ACTIVITY_LOG,
    CREATE_REMINDER_HISTORY,
    SCHEMA_TABLE,
    V4_TABLES,
    V4_INDEXES,
    V5_TABLES,
    V5_INDEXES,
    EXISTING_INDEXES,
)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _get_current_version(cursor: sqlite3.Cursor) -> int:
    try:
        cursor.execute("SELECT MAX(version) FROM _schema_version")
        row = cursor.fetchone()
        return row[0] if row and row[0] else 0
    except sqlite3.OperationalError:
        return 0


def run_migrations(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute(SCHEMA_TABLE)
    current_version = _get_current_version(cursor)

    if current_version < 1:
        logging.info("Fresh install — applying schema v5")
        for stmt in ALL_TABLES:
            cursor.execute(stmt)
        for stmt in V5_TABLES:
            cursor.execute(stmt)
        for stmt in EXISTING_INDEXES + V4_INDEXES + V5_INDEXES:
            cursor.execute(stmt)
        cursor.execute(
            "INSERT INTO _schema_version (version, applied_at) VALUES (?, ?)",
            (5, _now()),
        )
        connection.commit()
        logging.info("Schema v5 applied (fresh install)")
        return

    if current_version == 1:
        logging.info("Migrating schema v1 → v2")
        cursor.execute("DROP TABLE IF EXISTS payments")
        cursor.execute("DROP TABLE IF EXISTS customer_files")
        cursor.execute("DROP TABLE IF EXISTS contracts")
        cursor.execute("DROP TABLE IF EXISTS installments")
        cursor.execute("DROP TABLE IF EXISTS customers")
        for stmt in ALL_TABLES:
            cursor.execute(stmt)
        for stmt in EXISTING_INDEXES + V4_INDEXES:
            cursor.execute(stmt)
        cursor.execute(
            "INSERT INTO _schema_version (version, applied_at) VALUES (?, ?)",
            (5, _now()),
        )
        connection.commit()
        logging.info("Schema v5 applied (migrated from v1)")
        return

    if current_version == 2:
        logging.info("Migrating schema v2 → v5")
        cursor.execute(CREATE_ACTIVITY_LOG)
        cursor.execute(CREATE_REMINDER_HISTORY)
        for stmt in EXISTING_INDEXES:
            if "activity_log" in stmt or "reminder_history" in stmt:
                cursor.execute(stmt)
        for stmt in V4_TABLES:
            cursor.execute(stmt)
        for stmt in V4_INDEXES:
            cursor.execute(stmt)
        for stmt in V5_TABLES:
            cursor.execute(stmt)
        for stmt in V5_INDEXES:
            cursor.execute(stmt)
        cursor.execute(
            "INSERT INTO _schema_version (version, applied_at) VALUES (?, ?)",
            (5, _now()),
        )
        connection.commit()
        logging.info("Schema v5 applied (migrated from v2)")
        return

    if current_version == 3:
        logging.info("Migrating schema v3 → v5")
        for stmt in V4_TABLES:
            cursor.execute(stmt)
        for stmt in V4_INDEXES:
            cursor.execute(stmt)
        for stmt in V5_TABLES:
            cursor.execute(stmt)
        for stmt in V5_INDEXES:
            cursor.execute(stmt)
        cursor.execute(
            "INSERT INTO _schema_version (version, applied_at) VALUES (?, ?)",
            (5, _now()),
        )
        connection.commit()
        logging.info("Schema v5 applied (migrated from v3)")
        return

    if current_version == 4:
        logging.info("Migrating schema v4 → v5 (Phase 8)")
        for stmt in V5_TABLES:
            cursor.execute(stmt)
        for stmt in V5_INDEXES:
            cursor.execute(stmt)
        cursor.execute(
            "INSERT INTO _schema_version (version, applied_at) VALUES (?, ?)",
            (5, _now()),
        )
        connection.commit()
        logging.info("Schema v5 applied (migrated from v4)")
        return

    logging.info(f"Schema already at version {current_version}, no migrations needed")
