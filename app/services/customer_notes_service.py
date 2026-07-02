"""Customer Experience — notes, tags, profiles."""

import logging
from typing import List, Optional

from app.database.database import DatabaseManager

logger = logging.getLogger(__name__)

NOTE_CATEGORIES = ["general", "follow-up", "complaint", "meeting", "call", "payment", "other"]


class CustomerNotesService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def add_note(self, customer_id: int, content: str, category: str = "general") -> int:
        with self.db.transaction() as cur:
            cur.execute(
                "INSERT INTO customer_notes (customer_id, content, category, created_at, updated_at) "
                "VALUES (?, ?, ?, datetime('now'), datetime('now'))",
                (customer_id, content, category),
            )
            return cur.lastrowid

    def get_notes(self, customer_id: int) -> List[dict]:
        with self.db.transaction() as cur:
            cur.execute(
                "SELECT * FROM customer_notes WHERE customer_id = ? ORDER BY is_pinned DESC, created_at DESC",
                (customer_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def search_notes(self, query: str) -> List[dict]:
        with self.db.transaction() as cur:
            cur.execute(
                "SELECT n.*, c.customer_name FROM customer_notes n "
                "LEFT JOIN customers c ON n.customer_id = c.id "
                "WHERE n.content LIKE ? ORDER BY n.created_at DESC",
                (f"%{query}%",),
            )
            return [dict(r) for r in cur.fetchall()]

    def update_note(self, note_id: int, content: str = None, category: str = None) -> bool:
        updates = []
        params = []
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if not updates:
            return False
        updates.append("updated_at = datetime('now')")
        params.append(note_id)
        with self.db.transaction() as cur:
            cur.execute(f"UPDATE customer_notes SET {', '.join(updates)} WHERE id = ?", params)
            return cur.rowcount > 0

    def toggle_pin(self, note_id: int) -> bool:
        with self.db.transaction() as cur:
            cur.execute("UPDATE customer_notes SET is_pinned = CASE WHEN is_pinned THEN 0 ELSE 1 END WHERE id = ?",
                        (note_id,))
            return cur.rowcount > 0

    def delete_note(self, note_id: int) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM customer_notes WHERE id = ?", (note_id,))
            return cur.rowcount > 0


class CustomerTagsService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def add_tag(self, customer_id: int, tag: str) -> int:
        tag = tag.strip().lower()
        with self.db.transaction() as cur:
            existing = cur.execute(
                "SELECT id FROM customer_tags WHERE customer_id = ? AND tag = ?",
                (customer_id, tag),
            ).fetchone()
            if existing:
                return existing[0]
            cur.execute(
                "INSERT INTO customer_tags (customer_id, tag) VALUES (?, ?)",
                (customer_id, tag),
            )
            return cur.lastrowid

    def get_tags(self, customer_id: int) -> List[str]:
        with self.db.transaction() as cur:
            cur.execute("SELECT tag FROM customer_tags WHERE customer_id = ? ORDER BY tag", (customer_id,))
            return [r["tag"] for r in cur.fetchall()]

    def remove_tag(self, customer_id: int, tag: str) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM customer_tags WHERE customer_id = ? AND tag = ?", (customer_id, tag))
            return cur.rowcount > 0

    def get_all_tags(self) -> List[str]:
        with self.db.transaction() as cur:
            cur.execute("SELECT DISTINCT tag FROM customer_tags ORDER BY tag")
            return [r["tag"] for r in cur.fetchall()]

    def get_customers_by_tag(self, tag: str) -> List[dict]:
        with self.db.transaction() as cur:
            cur.execute(
                "SELECT c.* FROM customers c "
                "JOIN customer_tags t ON c.id = t.customer_id "
                "WHERE t.tag = ? ORDER BY c.customer_name",
                (tag,),
            )
            return [dict(r) for r in cur.fetchall()]
