import os
import tempfile

from app.database.database import DatabaseManager
from app.services.finance_service import FinanceService
from app.services.analytics_service import AnalyticsService


def _setup_db(db_path):
    db = DatabaseManager(db_path)
    db.initialize()
    conn = db.connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
        ("Alice", "+971500000000", 1000.0, 1, "2026-01-01", ""),
    )
    cid = cur.lastrowid
    cur.execute(
        "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
        ("Bob", "+971500000001", 2000.0, 2, "2026-02-01", ""),
    )
    bob_id = cur.lastrowid
    cur.execute(
        "INSERT INTO installments (customer_id, installment_number, due_date, amount, status, paid_date) "
        "VALUES (?, 1, '2026-01-15', 500.0, 'paid', '2026-01-14')",
        (cid,),
    )
    cur.execute(
        "INSERT INTO installments (customer_id, installment_number, due_date, amount, status) "
        "VALUES (?, 2, '2026-02-15', 500.0, 'pending')",
        (cid,),
    )
    conn.commit()
    return db, cid, bob_id


def _add_expense(service, amount=100.0, category="office", description="Test", expense_date="2026-07-01"):
    return service.add_expense(amount, category, description, expense_date)


class TestFinanceService:
    def test_add_expense(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            exp_id = _add_expense(service)
            assert exp_id > 0
            exp = service.get_expense(exp_id)
            assert exp is not None
            assert exp["amount"] == 100.0
            assert exp["category"] == "office"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_expense_not_found(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            assert service.get_expense(999) is None
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_update_expense(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            exp_id = _add_expense(service)
            assert service.update_expense(exp_id, amount=200.0, category="rent") is True
            exp = service.get_expense(exp_id)
            assert exp["amount"] == 200.0
            assert exp["category"] == "rent"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_update_expense_no_changes(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            exp_id = _add_expense(service)
            assert service.update_expense(exp_id) is False
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_expenses_empty(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            assert service.get_expenses() == []
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_expenses_filters(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            _add_expense(service, amount=50.0, category="office", expense_date="2026-06-01")
            _add_expense(service, amount=75.0, category="rent", expense_date="2026-07-01")
            _add_expense(service, amount=100.0, category="office", expense_date="2026-07-15")
            all_exp = service.get_expenses()
            assert len(all_exp) == 3
            office = service.get_expenses(category="office")
            assert len(office) == 2
            june = service.get_expenses(start_date="2026-06-01", end_date="2026-06-30")
            assert len(june) == 1
            july = service.get_expenses(start_date="2026-07-01")
            assert len(july) == 2
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_delete_expense(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            exp_id = _add_expense(service)
            assert service.get_expense(exp_id) is not None
            assert service.delete_expense(exp_id) is True
            assert service.get_expense(exp_id) is None
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_delete_expense_non_existing(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            assert service.delete_expense(999) is False
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_monthly_expenses(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            _add_expense(service, expense_date="2026-06-15")
            _add_expense(service, expense_date="2026-07-05")
            _add_expense(service, expense_date="2026-07-20")
            june = service.get_monthly_expenses(2026, 6)
            assert len(june) == 1
            july = service.get_monthly_expenses(2026, 7)
            assert len(july) == 2
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_expense_summary(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            _add_expense(service, amount=100.0, category="office")
            _add_expense(service, amount=200.0, category="rent")
            _add_expense(service, amount=50.0, category="office")
            summary = service.get_expense_summary()
            assert summary["total"] == 350.0
            assert summary["count"] == 3
            assert summary["by_category"]["office"] == 150.0
            assert summary["by_category"]["rent"] == 200.0
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_compute_dashboard(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = FinanceService(db)
            _add_expense(service, amount=50.0, category="office")
            data = service.compute_dashboard()
            assert "monthly_income" in data
            assert "collection_rate" in data
            assert "net_profit" in data
            assert "outstanding_balance" in data
            assert data["total_collected"] > 0
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_income_trend(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = FinanceService(db)
            trend = service.get_income_trend(3)
            assert len(trend) == 3
            for t in trend:
                assert "income" in t
                assert "expenses" in t
                assert "label" in t
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_collection_rate_trend(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = FinanceService(db)
            trend = service.get_collection_rate_trend(3)
            assert len(trend) == 3
            for t in trend:
                assert "rate" in t
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_customer_financial_summary(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = FinanceService(db)
            summary = service.get_customer_financial_summary(cid)
            assert summary["total_paid"] == 500.0
            assert summary["total_pending"] == 500.0
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)


class TestAnalyticsService:
    def test_compute(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = AnalyticsService(db)
            result = service.compute()
            assert result["total_customers"] == 2
            assert result["collection_rate"] == 50.0
            assert result["total_outstanding"] == 3000.0
            assert len(result["top_customers"]) == 2
            assert "collected_30d" in result
            assert "upcoming_cash_flow_90d" in result
            assert "avg_contract_value" in result
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_compute_empty_db(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = AnalyticsService(db)
            result = service.compute()
            assert result["total_customers"] == 0
            assert result["collection_rate"] == 0
            assert result["avg_payment_delay_days"] == 0
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    # ── AnalyticsService edge cases ─────────────────────────────────

    def test_compute_no_installments(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            conn = db.connect()
            conn.execute(
                "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
                ("Alice", "+971500000000", 1000.0, 0, "2026-01-01", ""),
            )
            conn.commit()
            service = AnalyticsService(db)
            result = service.compute()
            assert result["total_customers"] == 1
            assert result["collection_rate"] == 0
            assert result["avg_payment_delay_days"] == 0
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_compute_all_paid(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            conn = db.connect()
            conn.execute("UPDATE installments SET status='paid', paid_date='2026-01-14' WHERE customer_id=?", (cid,))
            conn.commit()
            service = AnalyticsService(db)
            result = service.compute()
            assert result["collection_rate"] == 100.0
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_compute_top_customers_few(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            conn = db.connect()
            conn.execute(
                "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
                ("Alice", "+971500000000", 1000.0, 1, "2026-01-01", ""),
            )
            conn.commit()
            service = AnalyticsService(db)
            result = service.compute()
            assert len(result["top_customers"]) == 1
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    # ── FinanceService edge cases ──────────────────────────────────

    def test_update_expense_partial_amount_only(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            eid = service.add_expense(100.0, "office", "Test", "2026-07-01")
            assert service.update_expense(eid, amount=250.0) is True
            updated = service.get_expense(eid)
            assert updated["amount"] == 250.0
            assert updated["category"] == "office"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_update_expense_partial_category_only(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            eid = service.add_expense(100.0, "office", "Test", "2026-07-01")
            assert service.update_expense(eid, category="travel") is True
            updated = service.get_expense(eid)
            assert updated["amount"] == 100.0
            assert updated["category"] == "travel"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_expenses_empty_string_filters(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            service.add_expense(100.0, "office", "A", "2026-07-01")
            service.add_expense(200.0, "travel", "B", "2026-07-15")
            result = service.get_expenses(start_date="", end_date="", category="")
            assert len(result) == 2
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_customer_financial_summary_invalid(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = FinanceService(db)
            summary = service.get_customer_financial_summary(99999)
            assert summary["total_paid"] == 0.0
            assert summary["total_pending"] == 0.0
            assert summary["overdue"] == 0.0
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
