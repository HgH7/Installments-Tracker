"""Browse database tables and execute SQL queries."""

import logging
from typing import Dict, List, Optional

from app.database.database import DatabaseManager

logger = logging.getLogger(__name__)


class DatabaseExplorer:
    """Inspect database schema, tables, and run ad-hoc queries."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def list_tables(self) -> List[str]:
        with self.db.transaction() as cur:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return [r["name"] for r in cur.fetchall()]

    def table_info(self, table_name: str) -> List[dict]:
        with self.db.transaction() as cur:
            cur.execute(f"PRAGMA table_info(\"{table_name}\")")
            return [dict(r) for r in cur.fetchall()]

    def table_rows(self, table_name: str, limit: int = 100, offset: int = 0) -> Dict:
        with self.db.transaction() as cur:
            cur.execute(f"SELECT COUNT(*) as c FROM \"{table_name}\"")
            total = cur.fetchone()["c"]
            cur.execute(f"SELECT * FROM \"{table_name}\" LIMIT ? OFFSET ?", (limit, offset))
            columns = [desc[0] for desc in cur.description]
            rows = [dict(r) for r in cur.fetchall()]
        return {"columns": columns, "rows": rows, "total": total}

    def query(self, sql: str, params=()) -> Dict:
        try:
            with self.db.transaction() as cur:
                cur.execute(sql, params)
                if sql.strip().upper().startswith("SELECT"):
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    rows = [dict(r) for r in cur.fetchall()]
                    return {"success": True, "columns": columns, "rows": rows, "count": len(rows)}
                else:
                    return {"success": True, "affected": cur.rowcount}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def index_info(self, table_name: str) -> List[dict]:
        with self.db.transaction() as cur:
            cur.execute(f"PRAGMA index_list(\"{table_name}\")")
            return [dict(r) for r in cur.fetchall()]
