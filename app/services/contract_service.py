"""Contract Management — templates, numbering, status tracking."""

import json
import logging
import os
from datetime import datetime
from typing import List, Optional

from app.database.database import DatabaseManager
from app.utils.paths import DATA_DIR

logger = logging.getLogger(__name__)

CONTRACT_STATUSES = ["draft", "pending", "sent", "signed", "completed", "cancelled"]
CONTRACT_STATUS_TRANSITIONS = {
    "draft": {"pending", "cancelled"},
    "pending": {"sent", "cancelled"},
    "sent": {"signed", "cancelled"},
    "signed": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def generate_contract_number(year: Optional[int] = None) -> str:
    """Generate a unique contract ID: CTR-YYYY-SEQ (6-digit zero-padded)."""
    if year is None:
        year = datetime.now().year
    return f"CTR-{year}-{_next_sequence(year):06d}"


def _next_sequence(year: int) -> int:
    """Return the next sequence number for the given year (in-memory counter)."""
    seq_file = os.path.join(DATA_DIR, f"contract_seq_{year}.txt")
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

    def duplicate_template(self, template_id: int, name: str) -> Optional[dict]:
        template = self.get_template(template_id)
        if not template:
            return None
        new_id = self.create_template(name, template.get("content", ""), fields=json.loads(template.get("fields_json", "[]")))
        return self.get_template(new_id)

    # ── Contracts ─────────────────────────────────────────────────────────

    def create_contract(self, customer_id: int, template_id: int = None,
                        content: dict = None) -> dict:
        number = generate_contract_number()
        with self.db.transaction() as cur:
            cur.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
            if cur.fetchone() is None:
                raise ValueError(f"Customer not found: {customer_id}")
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
                "SELECT c.*, cust.customer_name FROM contracts c "
                "LEFT JOIN customers cust ON c.customer_id = cust.id "
                "WHERE c.customer_id = ? ORDER BY c.created_at DESC",
                (customer_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_all_contracts(self, status: str = "") -> List[dict]:
        query = "SELECT c.*, cust.customer_name FROM contracts c LEFT JOIN customers cust ON c.customer_id = cust.id"
        params = []
        if status:
            query += " WHERE c.status = ?"
            params.append(status)
        query += " ORDER BY c.created_at DESC"
        with self.db.transaction() as cur:
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]

    def update_contract_status(self, contract_id: int, status: str) -> bool:
        if status not in CONTRACT_STATUSES:
            raise ValueError(f"Invalid contract status: {status}")
        with self.db.transaction() as cur:
            cur.execute("SELECT status FROM contracts WHERE id = ?", (contract_id,))
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"Contract not found: {contract_id}")
            current = row[0]
            if status not in CONTRACT_STATUS_TRANSITIONS.get(current, set()):
                raise ValueError(f"Invalid status transition: {current} -> {status}")
            cur.execute(
                "UPDATE contracts SET status = ?, updated_at = datetime('now') WHERE id = ?",
                (status, contract_id),
            )
            return cur.rowcount > 0

    def update_contract(self, contract_id: int, content: dict = None,
                        notes: str = None, pdf_path: str = None,
                        signed_date: str = None, template_id: int = None) -> bool:
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
        if signed_date is not None:
            updates.append("signed_date = ?")
            params.append(signed_date)
        if template_id is not None:
            updates.append("template_id = ?")
            params.append(template_id)
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

    def get_customer_summary(self, customer_id: int) -> Optional[dict]:
        with self.db.transaction() as cur:
            cur.execute(
                "SELECT id, customer_name, phone_number, total_amount, installment_count, start_date "
                "FROM customers WHERE id = ?",
                (customer_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_customer_id_by_name(self, name: str) -> Optional[int]:
        with self.db.transaction() as cur:
            cur.execute("SELECT id FROM customers WHERE customer_name = ?", (name,))
            row = cur.fetchone()
            return row[0] if row else None

    def delete_contract(self, contract_id: int) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
            return cur.rowcount > 0

    def find_contract(self, query: str, status: str = "", template_id: int = None,
                      customer_id: int = None, created_on: str = "") -> List[dict]:
        clauses = []
        params = []
        if query:
            clauses.append("(c.contract_number LIKE ? OR c.status LIKE ? OR cust.customer_name LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
        if status:
            clauses.append("c.status = ?")
            params.append(status)
        if template_id is not None:
            clauses.append("c.template_id = ?")
            params.append(template_id)
        if customer_id is not None:
            clauses.append("c.customer_id = ?")
            params.append(customer_id)
        if created_on:
            clauses.append("date(c.created_at) = ?")
            params.append(created_on)
        where_clause = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.db.transaction() as cur:
            cur.execute(
                f"SELECT c.*, cust.customer_name FROM contracts c "
                f"LEFT JOIN customers cust ON c.customer_id = cust.id {where_clause} "
                f"ORDER BY c.created_at DESC",
                params,
            )
            return [dict(r) for r in cur.fetchall()]
