"""Aggregates business metrics (collection rate, cash flow, trends) from raw data."""

from datetime import datetime, timedelta
from typing import Dict

from app.database.database import DatabaseManager
from app.logging.logger import logger
from app.utils.serialization import dict_factory


class AnalyticsService:
    def __init__(self, db: DatabaseManager):
        self._db = db

    def compute(self) -> Dict:
        try:
            conn = self._db.connect()
            old_factory = conn.row_factory
            conn.row_factory = dict_factory
            try:
                cur = conn.cursor()

                cur.execute("SELECT COUNT(*) as c FROM customers")
                total_customers = cur.fetchone()["c"]

                cur.execute("SELECT COUNT(*) as c FROM installments WHERE status='paid'")
                paid_insts = cur.fetchone()["c"]

                cur.execute("SELECT COUNT(*) as c FROM installments")
                total_insts = cur.fetchone()["c"]

                collection_rate = round((paid_insts / total_insts * 100) if total_insts else 0, 1)

                cur.execute(
                    "SELECT AVG(julianday(paid_date) - julianday(due_date)) as avg_delay FROM installments WHERE status='paid' AND paid_date IS NOT NULL"
                )
                row = cur.fetchone()
                avg_delay = round(row["avg_delay"], 1) if row and row["avg_delay"] else 0.0

                cur.execute(
                    "SELECT AVG(total_amount) as avg_contract FROM customers"
                )
                row = cur.fetchone()
                avg_contract = round(row["avg_contract"], 2) if row and row["avg_contract"] else 0.0

                today = datetime.now().date()
                thirty_days_ago = today - timedelta(days=30)
                cur.execute(
                    "SELECT COUNT(*) as c FROM customers WHERE created_at >= ?",
                    (thirty_days_ago.strftime("%Y-%m-%d"),),
                )
                new_customers_30d = cur.fetchone()["c"]

                cur.execute(
                    "SELECT customer_name, total_amount FROM customers ORDER BY total_amount DESC LIMIT 5"
                )
                top_customers = [dict(r) for r in cur.fetchall()]

                today_str = today.strftime("%Y-%m-%d")
                end_90d = (today + timedelta(days=90)).strftime("%Y-%m-%d")
                cur.execute(
                    "SELECT SUM(amount) as total FROM installments WHERE due_date BETWEEN ? AND ? AND status='pending'",
                    (today_str, end_90d),
                )
                row = cur.fetchone()
                upcoming_cash_flow = round(row["total"], 2) if row and row["total"] else 0.0

                cur.execute(
                    "SELECT SUM(total_amount) as total FROM customers"
                )
                row = cur.fetchone()
                total_outstanding = round(row["total"], 2) if row and row["total"] else 0.0

                cur.execute(
                    "SELECT SUM(amount) as total FROM installments WHERE status='paid' AND paid_date >= ?",
                    (thirty_days_ago.strftime("%Y-%m-%d"),),
                )
                row = cur.fetchone()
                collected_30d = round(row["total"], 2) if row and row["total"] else 0.0

                cur.execute(
                    "SELECT strftime('%m', due_date) as month, SUM(CASE WHEN status='paid' THEN amount ELSE 0 END) as collected, SUM(CASE WHEN status='pending' THEN amount ELSE 0 END) as expected FROM installments WHERE due_date >= ? GROUP BY month ORDER BY month",
                    ((today - timedelta(days=365)).strftime("%Y-%m-%d"),),
                )
                monthly = [dict(r) for r in cur.fetchall()]

                return {
                    "total_customers": total_customers,
                    "collection_rate": collection_rate,
                    "avg_payment_delay_days": avg_delay,
                    "avg_contract_value": avg_contract,
                    "new_customers_30d": new_customers_30d,
                    "total_outstanding": total_outstanding,
                    "collected_30d": collected_30d,
                    "upcoming_cash_flow_90d": upcoming_cash_flow,
                    "top_customers": top_customers,
                    "monthly": monthly,
                }
            finally:
                conn.row_factory = old_factory
        except Exception as e:
            logger.error(f"Analytics computation failed: {e}", component="analytics")
            return {}
