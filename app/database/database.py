import logging
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

from app.database.migrations import run_migrations

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "installment_tracker.db",
)


class DatabaseManager:
    """Manages the SQLite connection, transactions, and lifecycle."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._ensure_data_directory()
        self._connection: sqlite3.Connection | None = None

    def _ensure_data_directory(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logging.info(f"Created data directory: {db_dir}")

    def connect(self) -> sqlite3.Connection:
        """Open (or return existing) connection with foreign keys enabled."""
        if self._connection is not None:
            return self._connection
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON;")
        self._connection.execute("PRAGMA journal_mode = WAL;")
        logging.info(f"Connected to database: {self.db_path}")
        return self._connection

    def initialize(self) -> None:
        """Ensure the database exists and all migrations are applied."""
        conn = self.connect()
        run_migrations(conn)
        logging.info("Database initialized successfully")

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logging.info("Database connection closed")

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager that commits on success, rolls back on error."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    @property
    def connection(self) -> sqlite3.Connection:
        return self.connect()
