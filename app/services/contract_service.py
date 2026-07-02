"""Contract Management — templates, numbering, status tracking."""

import json
import logging
import os
from datetime import datetime
from typing import List, Optional

from app.database.database import DatabaseManager

logger = logging.getLogger(__name__)

CONTRACT_STATUSES = ["draft", "active", "completed", "cancelled", "overdue", "suspended"]


def generate_contract_number(year: Optional[int] = None) -> str:
    """Generate a unique contract ID: CTR-YYYY-SEQ (6-digit zero-padded)."""
    if year is None:
        year = datetime.now().year
    return f"CTR-{year}-{_next_sequence(year):06d}"


def _next_sequence(year: int) -> int:
    """Return the next sequence number for the given year (in-memory counter)."""
    seq_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        f"contract_seq_{year}.txt",
    )
    try:
        os.makedirs(os.path.dirname(seq_file), exist_ok=True)
        if os.path.exists(seq_file):
            with open(seq_file) as f:
                seq = int(f.read().strip())
        else:
            seq = 0
    except (OSError, ValueError):
        seq = 0
    seq += 1
    try:
        with open(seq_file, "w") as f:
            f.write(str(seq))
    except OSError:
        pass
    return seq


class ContractService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    # ── Templates ─────────────────────────────────────────────────────────

    def create_template(self, name: str, content: str, fields: List[dict] = None) -> int:
        with self.db.transaction() as cur:
            cur.execute(
                "INSERT INTO contract_templates (name, content, fields_json, created_at, updated_at) "
                "VALUES (?, ?, ?, datetime('now'), datetime('now'))",
                (name, content, json.dumps(fields or [])),
            )
            return cur.lastrowid

    def get_templates(self) -> List[dict]:
        with self.db.transaction() as cur:
            cur.execute("SELECT * FROM contract_templates ORDER BY name")
            return [dict(r) for r in cur.fetchall()]

    def get_template(self, template_id: int) -> Optional[dict]:
        with self.db.transaction() as cur:
            cur.execute("SELECT * FROM contract_templates WHERE id = ?", (template_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def update_template(self, template_id: int, name: str = None, content: str = None,
                        fields: List[dict] = None) -> bool:
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if fields is not None:
            updates.append("fields_json = ?")
            params.append(json.dumps(fields))
        if not updates:
            return False
        updates.append("updated_at = datetime('now')")
        params.append(template_id)
        with self.db.transaction() as cur:
            cur.execute(
                f"UPDATE contract_templates SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            return cur.rowcount > 0

    def delete_template(self, template_id: int) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM contract_templates WHERE id = ?", (template_id,))
            return cur.rowcount > 0

    # ── Contracts ─────────────────────────────────────────────────────────

    def create_contract(self, customer_id: int, template_id: int = None,
                        content: dict = None) -> dict:
        number = generate_contract_number()
        with self.db.transaction() as cur:
            cur.execute(
                "INSERT INTO contracts (customer_id, contract_number, template_id, "
                "content_json, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 'draft', datetime('now'), datetime('now'))",
                (customer_id, number, template_id, json.dumps(content or {})),
            )
            contract_id = cur.lastrowid
        return self.get_contract(contract_id)

    def get_contract(self, contract_id: int) -> Optional[dict]:
        with self.db.transaction() as cur:
            cur.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,))
            row = cur.fetchone()
            if row:
                d = dict(row)
                d["content"] = json.loads(d.get("content_json", "{}"))
                return d
            return None

    def get_customer_contracts(self, customer_id: int) -> List[dict]:
        with self.db.transaction() as cur:
            cur.execute(
                "SELECT * FROM contracts WHERE customer_id = ? ORDER BY created_at DESC",
                (customer_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_all_contracts(self, status: str = "") -> List[dict]:
        query = "SELECT * FROM contracts"
        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        with self.db.transaction() as cur:
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]

    def update_contract_status(self, contract_id: int, status: str) -> bool:
        if status not in CONTRACT_STATUSES:
            raise ValueError(f"Invalid contract status: {status}")
        with self.db.transaction() as cur:
            cur.execute(
                "UPDATE contracts SET status = ?, updated_at = datetime('now') WHERE id = ?",
                (status, contract_id),
            )
            return cur.rowcount > 0

    def update_contract(self, contract_id: int, content: dict = None,
                        notes: str = None, pdf_path: str = None) -> bool:
        updates = []
        params = []
        if content is not None:
            updates.append("content_json = ?")
            params.append(json.dumps(content))
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if pdf_path is not None:
            updates.append("pdf_path = ?")
            params.append(pdf_path)
        if not updates:
            return False
        updates.append("updated_at = datetime('now')")
        params.append(contract_id)
        with self.db.transaction() as cur:
            cur.execute(
                f"UPDATE contracts SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            return cur.rowcount > 0

    def delete_contract(self, contract_id: int) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
            return cur.rowcount > 0

    def find_contract(self, query: str) -> List[dict]:
        with self.db.transaction() as cur:
            cur.execute(
                "SELECT c.*, cust.customer_name FROM contracts c "
                "LEFT JOIN customers cust ON c.customer_id = cust.id "
                "WHERE c.contract_number LIKE ? OR c.status LIKE ? OR cust.customer_name LIKE ? "
                "ORDER BY c.created_at DESC",
                (f"%{query}%", f"%{query}%", f"%{query}%"),
            )
            return [dict(r) for r in cur.fetchall()]
