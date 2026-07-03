"""Productivity — task manager for follow-ups, meetings, callbacks."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from app.database.database import DatabaseManager

logger = logging.getLogger(__name__)

TASK_TYPES = ["general", "follow-up", "meeting", "document", "callback", "review"]
TASK_PRIORITIES = ["low", "medium", "high", "urgent"]
TASK_STATUSES = ["pending", "in_progress", "completed", "cancelled"]


class TaskService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_task(self, title: str, customer_id: int = None, description: str = "",
                    due_date: str = None, priority: str = "medium", task_type: str = "general") -> int:
        with self.db.transaction() as cur:
            cur.execute(
                "INSERT INTO tasks (customer_id, title, description, due_date, status, priority, task_type, "
                "created_at, updated_at) VALUES (?, ?, ?, ?, 'pending', ?, ?, datetime('now'), datetime('now'))",
                (customer_id, title, description, due_date, priority, task_type),
            )
            return cur.lastrowid

    def get_tasks(self, status: str = "", customer_id: int = None) -> List[dict]:
        query = "SELECT t.*, c.customer_name FROM tasks t LEFT JOIN customers c ON t.customer_id = c.id WHERE 1=1"
        params = []
        if status:
            query += " AND t.status = ?"
            params.append(status)
        if customer_id is not None:
            query += " AND t.customer_id = ?"
            params.append(customer_id)
        query += " ORDER BY t.due_date IS NULL, t.due_date ASC, t.priority DESC"
        with self.db.transaction() as cur:
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]

    def get_task(self, task_id: int) -> Optional[dict]:
        with self.db.transaction() as cur:
            cur.execute(
                "SELECT t.*, c.customer_name FROM tasks t LEFT JOIN customers c ON t.customer_id = c.id WHERE t.id = ?",
                (task_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def update_task_status(self, task_id: int, status: str) -> bool:
        if status not in TASK_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        with self.db.transaction() as cur:
            cur.execute("UPDATE tasks SET status = ?, updated_at = datetime('now') WHERE id = ?", (status, task_id))
            return cur.rowcount > 0

    def update_task(self, task_id: int, title: str = None, description: str = None,
                    due_date: str = None, priority: str = None, task_type: str = None) -> bool:
        updates = []
        params = []
        for field, value in [("title", title), ("description", description),
                              ("due_date", due_date), ("priority", priority), ("task_type", task_type)]:
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(value)
        if not updates:
            return False
        updates.append("updated_at = datetime('now')")
        params.append(task_id)
        with self.db.transaction() as cur:
            cur.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params)
            return cur.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cur.rowcount > 0

    def get_tasks_by_date(self, date: str) -> List[dict]:
        with self.db.transaction() as cur:
            cur.execute(
                "SELECT t.*, c.customer_name FROM tasks t LEFT JOIN customers c ON t.customer_id = c.id "
                "WHERE t.due_date = ? ORDER BY t.priority DESC",
                (date,),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_upcoming_tasks(self, days: int = 7) -> List[dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        with self.db.transaction() as cur:
            cur.execute(
                "SELECT t.*, c.customer_name FROM tasks t LEFT JOIN customers c ON t.customer_id = c.id "
                "WHERE t.due_date >= ? AND t.due_date <= ? AND t.status IN ('pending', 'in_progress') "
                "ORDER BY t.due_date ASC",
                (today, end),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_overdue_tasks(self) -> List[dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        with self.db.transaction() as cur:
            cur.execute(
                "SELECT t.*, c.customer_name FROM tasks t LEFT JOIN customers c ON t.customer_id = c.id "
                "WHERE t.due_date < ? AND t.status IN ('pending', 'in_progress') ORDER BY t.due_date ASC",
                (today,),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_customer_id_by_name(self, name: str) -> Optional[int]:
        with self.db.transaction() as cur:
            cur.execute("SELECT id FROM customers WHERE customer_name = ?", (name,))
            row = cur.fetchone()
            return row[0] if row else None

    def get_customer_name_for_doc(self, customer_id: int) -> str:
        with self.db.transaction() as cur:
            cur.execute("SELECT customer_name FROM customers WHERE id = ?", (customer_id,))
            row = cur.fetchone()
            return row[0] if row else f"ID:{customer_id}"
