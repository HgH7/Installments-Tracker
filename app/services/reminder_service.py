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
            try:
                old_factory = conn.row_factory
                conn.row_factory = dict_factory
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
            try:
                old_factory = conn.row_factory
                conn.row_factory = dict_factory
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

    def get_reminder(self, reminder_id: int) -> Optional[Dict]:
        try:
            conn = self._db.connect()
            try:
                old_factory = conn.row_factory
                conn.row_factory = dict_factory
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM reminder_history WHERE id=?",
                    (reminder_id,),
                )
                return cursor.fetchone()
            finally:
                conn.row_factory = old_factory
        except Exception as e:
            logger.error(f"Failed to get reminder {reminder_id}: {e}", component="reminder")
            return None

    def update_reminder(self, reminder_id: int, **kwargs) -> bool:
        try:
            allowed = {"customer_name", "phone", "installment_date", "amount", "message", "status"}
            updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
            if not updates:
                return False
            updates["id"] = reminder_id
            set_clause = ", ".join(f"{k}=?" for k in updates if k != "id")
            values = [v for k, v in updates.items() if k != "id"]
            values.append(reminder_id)
            with self._db.transaction() as cursor:
                cursor.execute(
                    f"UPDATE reminder_history SET {set_clause} WHERE id=?",
                    values,
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update reminder {reminder_id}: {e}", component="reminder")
            return False

    def delete_reminder(self, reminder_id: int) -> bool:
        try:
            with self._db.transaction() as cursor:
                cursor.execute("DELETE FROM reminder_history WHERE id=?", (reminder_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete reminder {reminder_id}: {e}", component="reminder")
            return False

    def update_reminder_status(self, reminder_id: int, status: str) -> bool:
        return self.update_reminder(reminder_id, status=status)

    def search_reminders(
        self,
        customer_name: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        phone: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        try:
            conn = self._db.connect()
            try:
                old_factory = conn.row_factory
                conn.row_factory = dict_factory
                cursor = conn.cursor()
                conditions = []
                values = []
                if customer_name:
                    conditions.append("customer_name LIKE ?")
                    values.append(f"%{customer_name}%")
                if status:
                    conditions.append("status=?")
                    values.append(status)
                if date_from:
                    conditions.append("installment_date>=?")
                    values.append(date_from)
                if date_to:
                    conditions.append("installment_date<=?")
                    values.append(date_to)
                if phone:
                    conditions.append("phone LIKE ?")
                    values.append(f"%{phone}%")
                where = ""
                if conditions:
                    where = "WHERE " + " AND ".join(conditions)
                cursor.execute(
                    f"SELECT * FROM reminder_history {where} ORDER BY created_at DESC LIMIT ?",
                    values + [limit],
                )
                return cursor.fetchall()
            finally:
                conn.row_factory = old_factory
        except Exception as e:
            logger.error(f"Failed to search reminders: {e}", component="reminder")
            return []
