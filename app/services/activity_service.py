"""Tracks user actions in the activity_log table for audit history."""

from datetime import datetime
from typing import Dict, List, Optional

from app.database.database import DatabaseManager
from app.core.logging.logger import logger
from app.utils.serialization import dict_factory

ACTIONS = {
    "CUSTOMER_CREATED": "Customer created",
    "CUSTOMER_EDITED": "Customer edited",
    "CUSTOMER_DELETED": "Customer deleted",
    "INSTALLMENT_PAID": "Installment paid",
    "INSTALLMENT_EDITED": "Installment edited",
    "REMINDER_GENERATED": "Reminder generated",
    "BACKUP_CREATED": "Backup created",
    "BACKUP_RESTORED": "Backup restored",
    "EXPORT_CSV": "Data exported (CSV)",
    "EXPORT_EXCEL": "Data exported (Excel)",
    "EXPORT_PDF": "Data exported (PDF)",
    "IMPORT_CSV": "Data imported (CSV)",
    "IMPORT_EXCEL": "Data imported (Excel)",
}


class ActivityService:
    def __init__(self, db: DatabaseManager):
        self._db = db

    def log(self, action: str, customer_id: Optional[int] = None, detail: str = ""):
        try:
            with self._db.transaction() as cursor:
                cursor.execute(
                    "INSERT INTO activity_log (customer_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
                    (customer_id, action, detail, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                )
        except Exception as e:
            logger.error(f"Failed to log activity: {e}", component="activity")

    def get_all(self, limit: int = 200) -> List[Dict]:
        try:
            conn = self._db.connect()
            old_factory = conn.row_factory
            conn.row_factory = dict_factory
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT a.*, c.customer_name FROM activity_log a "
                    "LEFT JOIN customers c ON a.customer_id = c.id "
                    "ORDER BY a.created_at DESC LIMIT ?",
                    (limit,),
                )
                return cursor.fetchall()
            finally:
                conn.row_factory = old_factory
        except Exception as e:
            logger.error(f"Failed to read activity log: {e}", component="activity")
            return []

    def get_for_customer(self, customer_id: int, limit: int = 50) -> List[Dict]:
        try:
            conn = self._db.connect()
            old_factory = conn.row_factory
            conn.row_factory = dict_factory
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM activity_log WHERE customer_id = ? ORDER BY created_at DESC LIMIT ?",
                    (customer_id, limit),
                )
                return cursor.fetchall()
            finally:
                conn.row_factory = old_factory
        except Exception as e:
            logger.error(f"Failed to read activity for customer: {e}", component="activity")
            return []

    def get_recent(self, limit: int = 20) -> List[Dict]:
        return self.get_all(limit)
