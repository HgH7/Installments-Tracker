"""Financial Management — expense tracking, P&L, financial dashboard."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.database.database import DatabaseManager

logger = logging.getLogger(__name__)

EXPENSE_CATEGORIES = [
    "office",
    "salaries",
    "transportation",
    "marketing",
    "utilities",
    "rent",
    "supplies",
    "maintenance",
    "legal",
    "tax",
    "insurance",
    "miscellaneous",
]


class FinanceService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    # ── Expenses ──────────────────────────────────────────────────────────

    def add_expense(self, amount: float, category: str, description: str, expense_date: str) -> int:
        with self.db.transaction() as cur:
            cur.execute(
                "INSERT INTO expenses (amount, category, description, expense_date, created_at) "
                "VALUES (?, ?, ?, ?, datetime('now'))",
                (amount, category, description, expense_date),
            )
            return cur.lastrowid

    def get_expenses(self, start_date: str = "", end_date: str = "", category: str = "") -> List[dict]:
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []
        if start_date:
            query += " AND expense_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND expense_date <= ?"
            params.append(end_date)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY expense_date DESC"
        with self.db.transaction() as cur:
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]

    def get_monthly_expenses(self, year: int, month: int) -> List[dict]:
        start = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end = f"{year+1:04d}-01-01"
        else:
            end = f"{year:04d}-{month+1:02d}-01"
        return self.get_expenses(start_date=start, end_date=end)

    def get_expense_summary(self, start_date: str = "", end_date: str = "") -> dict:
        expenses = self.get_expenses(start_date, end_date)
        total = sum(e["amount"] for e in expenses)
        by_category: Dict[str, float] = {}
        for e in expenses:
            by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]
        return {"total": total, "count": len(expenses), "by_category": by_category}

    def delete_expense(self, expense_id: int) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            return cur.rowcount > 0

    # ── Financial Dashboard ───────────────────────────────────────────────

    def compute_dashboard(self) -> dict:
        now = datetime.now()
        month_start = now.replace(day=1).strftime("%Y-%m-%d")
        month_end = ((now.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")
        year_start = now.replace(month=1, day=1).strftime("%Y-%m-%d")

        with self.db.transaction() as cur:
            # Monthly income (paid installments this month)
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM installments "
                "WHERE status = 'paid' AND paid_date >= ? AND paid_date <= ?",
                (month_start, month_end),
            )
            monthly_income = cur.fetchone()[0]

            # Expected income this month (pending installments due this month)
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM installments "
                "WHERE status = 'pending' AND due_date >= ? AND due_date <= ?",
                (month_start, month_end),
            )
            expected_income = cur.fetchone()[0]

            # Outstanding balance (all pending)
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM installments WHERE status = 'pending'"
            )
            outstanding = cur.fetchone()[0]

            # Total collected (all time)
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM installments WHERE status = 'paid'"
            )
            total_collected = cur.fetchone()[0]

            # Total expected (all time)
            cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM customers")
            total_expected = cur.fetchone()[0]

            # Overdue amount
            today = now.strftime("%Y-%m-%d")
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM installments "
                "WHERE status = 'pending' AND due_date < ?",
                (today,),
            )
            overdue_amount = cur.fetchone()[0]

            # Monthly expenses
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM expenses "
                "WHERE expense_date >= ? AND expense_date <= ?",
                (month_start, month_end),
            )
            monthly_expenses = cur.fetchone()[0]

            # Yearly income
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM installments "
                "WHERE status = 'paid' AND paid_date >= ?",
                (year_start,),
            )
            yearly_income = cur.fetchone()[0]

            # Yearly expenses
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE expense_date >= ?",
                (year_start,),
            )
            yearly_expenses = cur.fetchone()[0]

            # Growth rate (compare this month to last month)
            last_month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
            last_month_end = now.replace(day=1) - timedelta(days=1)
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM installments "
                "WHERE status = 'paid' AND paid_date >= ? AND paid_date <= ?",
                (last_month_start.strftime("%Y-%m-%d"), last_month_end.strftime("%Y-%m-%d")),
            )
            last_month_income = cur.fetchone()[0]

        collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else 0
        growth = ((monthly_income - last_month_income) / last_month_income * 100) if last_month_income > 0 else 0
        net_profit = monthly_income - monthly_expenses

        return {
            "monthly_income": monthly_income,
            "expected_income": expected_income,
            "outstanding_balance": outstanding,
            "total_collected": total_collected,
            "total_expected": total_expected,
            "collection_rate": round(collection_rate, 1),
            "overdue_amount": overdue_amount,
            "monthly_expenses": monthly_expenses,
            "yearly_income": yearly_income,
            "yearly_expenses": yearly_expenses,
            "net_profit": net_profit,
            "monthly_growth": round(growth, 1),
            "period_start": month_start,
            "period_end": month_end,
        }

    def get_income_trend(self, months: int = 12) -> List[dict]:
        trend = []
        now = datetime.now()
        with self.db.transaction() as cur:
            for i in range(months - 1, -1, -1):
                m = (now.month - i - 1) % 12 + 1
                y = now.year + ((now.month - i - 1) // 12)
                start = f"{y:04d}-{m:02d}-01"
                end = (datetime(y, m, 28) + timedelta(days=4)).replace(day=1).strftime("%Y-%m-%d")
                cur.execute(
                    "SELECT COALESCE(SUM(amount), 0) FROM installments "
                    "WHERE status = 'paid' AND paid_date >= ? AND paid_date < ?",
                    (start, end),
                )
                income = cur.fetchone()[0]
                cur.execute(
                    "SELECT COALESCE(SUM(amount), 0) FROM expenses "
                    "WHERE expense_date >= ? AND expense_date < ?",
                    (start, end),
                )
                expenses = cur.fetchone()[0]
                trend.append({
                    "year": y, "month": m,
                    "label": f"{y}-{m:02d}",
                    "income": income,
                    "expenses": expenses,
                })
        return trend

    def get_collection_rate_trend(self, months: int = 6) -> List[dict]:
        trend = []
        now = datetime.now()
        with self.db.transaction() as cur:
            for i in range(months - 1, -1, -1):
                m = (now.month - i - 1) % 12 + 1
                y = now.year + ((now.month - i - 1) // 12)
                start = f"{y:04d}-{m:02d}-01"
                end = (datetime(y, m, 28) + timedelta(days=4)).replace(day=1).strftime("%Y-%m-%d")
                cur.execute(
                    "SELECT COUNT(*), COALESCE(SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END), 0) "
                    "FROM installments WHERE due_date >= ? AND due_date < ?",
                    (start, end),
                )
                total, paid = cur.fetchone()
                rate = round((paid / total * 100) if total > 0 else 0, 1)
                trend.append({"year": y, "month": m, "label": f"{y}-{m:02d}", "rate": rate})
        return trend
