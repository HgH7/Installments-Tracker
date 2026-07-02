"""Schedules and manages payment reminders and notifications."""

from datetime import datetime
from typing import Dict, List, Optional

from app.database.database import DatabaseManager
from app.core.logging.logger import logger
from app.utils.serialization import dict_factory


class ReminderService:
    def __init__(self, db: DatabaseManager):
        self._db = db

    def save_reminder(
        self,
        customer_id: int,
        customer_name: str,
        phone: str,
        installment_date: str,
        amount: float,
        message: str,
        status: str = "draft",
    ) -> Optional[int]:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self._db.transaction() as cursor:
                cursor.execute(
                    "INSERT INTO reminder_history (customer_id, customer_name, phone, installment_date, amount, message, status, sent_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (customer_id, customer_name, phone, installment_date, amount, message, status, None, now),
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to save reminder: {e}", component="reminder")
            return None

    def get_history(self, limit: int = 100) -> List[Dict]:
        try:
            conn = self._db.connect()
            old_factory = conn.row_factory
            conn.row_factory = dict_factory
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM reminder_history ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                )
                return cursor.fetchall()
            finally:
                conn.row_factory = old_factory
        except Exception as e:
            logger.error(f"Failed to get reminder history: {e}", component="reminder")
            return []

    def get_for_customer(self, customer_id: int, limit: int = 20) -> List[Dict]:
        try:
            conn = self._db.connect()
            old_factory = conn.row_factory
            conn.row_factory = dict_factory
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM reminder_history WHERE customer_id=? ORDER BY created_at DESC LIMIT ?",
                    (customer_id, limit),
                )
                return cursor.fetchall()
            finally:
                conn.row_factory = old_factory
        except Exception as e:
            logger.error(f"Failed to get reminders for customer: {e}", component="reminder")
            return []
