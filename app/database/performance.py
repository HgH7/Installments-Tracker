"""Performance tuning: pagination, batch operations, indexing helpers."""

import logging
import time
from typing import Dict, List

from app.database.database import DatabaseManager
from app.database.schema import V5_INDEXES

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Apply performance optimizations to the database."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def ensure_v5_indexes(self):
        """Create Phase 8 performance indexes."""
        count = 0
        with self.db.transaction() as cur:
            for idx_sql in V5_INDEXES:
                try:
                    cur.execute(idx_sql)
                    count += 1
                except Exception as e:
                    logger.warning("Index creation failed: %s", e)
        logger.info("Ensured %d performance indexes", count)

    def analyze_tables(self):
        """Run ANALYZE for query planner optimization."""
        with self.db.transaction() as cur:
            cur.execute("ANALYZE")
        logger.info("Database analyzed for query optimization")

    def table_stats(self) -> Dict[str, dict]:
        """Return row counts and sizes for all tables."""
        stats = {}
        with self.db.transaction() as cur:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [r["name"] for r in cur.fetchall()]
            for tbl in tables:
                cur.execute(f"SELECT COUNT(*) as c FROM \"{tbl}\"")
                count = cur.fetchone()["c"]
                cur.execute(f"SELECT COALESCE(LENGTH(GROUP_CONCAT('')), 0) FROM pragma_table_info('{tbl}')")
                stats[tbl] = {"rows": count}
        return stats

    def paginate(self, sql: str, params: tuple = (),
                 page: int = 1, page_size: int = 50) -> Dict:
        """Execute a paginated query with total count."""
        with self.db.transaction() as cur:
            count_sql = f"SELECT COUNT(*) as c FROM ({sql})"
            cur.execute(count_sql, params)
            total = cur.fetchone()["c"]
            offset = (page - 1) * page_size
            paginated_sql = f"{sql} LIMIT ? OFFSET ?"
            cur.execute(paginated_sql, params + (page_size, offset))
            columns = [desc[0] for desc in cur.description]
            rows = [dict(r) for r in cur.fetchall()]
        return {
            "data": rows,
            "columns": columns,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, -(-total // page_size)),
        }

    def batch_insert(self, table: str, rows: List[Dict], batch_size: int = 100):
        """Insert many rows efficiently."""
        if not rows:
            return 0
        columns = list(rows[0].keys())
        placeholders = ", ".join(["?" for _ in columns])
        col_names = ", ".join(columns)
        sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
        total = 0
        with self.db.transaction() as cur:
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                cur.executemany(sql, [tuple(r[c] for c in columns) for r in batch])
                total += len(batch)
        logger.info("Batch inserted %d rows into %s", total, table)
        return total

    def timing(self, label: str):
        """Context manager for timing queries."""
        class _Timer:
            def __init__(self, lbl):
                self.lbl = lbl
            def __enter__(self):
                self.start = time.perf_counter()
                return self
            def __exit__(self, *a):
                ms = (time.perf_counter() - self.start) * 1000
                logger.info("TIMING [%s]: %.2fms", self.lbl, ms)
        return _Timer(label)
