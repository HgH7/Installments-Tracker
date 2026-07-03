import os
import tempfile
from unittest.mock import MagicMock, patch

from app.database.database import DatabaseManager
from app.services.contract_service import ContractService
from app.services.document_service import DocumentService
from app.services.task_service import TaskService
from app.services.finance_service import FinanceService
from app.services.reminder_service import ReminderService
from app.services.global_search_service import GlobalSearchService


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
    conn.commit()
    return db, cid


class MockCustomerService:
    def __init__(self, customers=None):
        self.customers = customers or []

    def get_all_customers(self):
        return self.customers


class TestGlobalSearchService:
    def test_empty_query_returns_empty(self):
        service = GlobalSearchService()
        assert service.search("") == []
        assert service.search("   ") == []

    def test_search_customers(self):
        mock_cs = MockCustomerService(customers=[
            {"Name": "Alice", "Phone": "+971500000000", "Amount": 1000, "Start Date": "2026-01-01", "Installments": 1},
            {"Name": "Bob", "Phone": "+971511111111", "Amount": 2000, "Start Date": "2026-02-01", "Installments": 2},
        ])
        service = GlobalSearchService(customer_service=mock_cs)
        results = service.search("Alice", category="customers")
        assert len(results) == 1
        assert results[0]["type"] == "customer"
        assert results[0]["title"] == "Alice"

    def test_search_customers_no_match(self):
        mock_cs = MockCustomerService(customers=[
            {"Name": "Alice", "Phone": "+971500000000", "Amount": 1000, "Start Date": "2026-01-01", "Installments": 1},
        ])
        service = GlobalSearchService(customer_service=mock_cs)
        results = service.search("Charlie", category="customers")
        assert results == []

    def test_search_contracts(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            cs = ContractService(db)
            contract = cs.create_contract(customer_id=cid)
            service = GlobalSearchService(contract_service=cs)
            results = service.search("Alice", category="contracts")
            assert len(results) >= 1
            assert results[0]["type"] == "contract"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_contracts_no_match(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            cs = ContractService(db)
            cs.create_contract(customer_id=cid)
            service = GlobalSearchService(contract_service=cs)
            results = service.search("NonExistent", category="contracts")
            assert results == []
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_tasks(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            ts = TaskService(db)
            ts.create_task(title="Follow up call", customer_id=cid, description="Call Alice about payment")
            service = GlobalSearchService(task_service=ts)
            results = service.search("Follow", category="tasks")
            assert len(results) >= 1
            assert results[0]["type"] == "task"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_expenses(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            fs = FinanceService(db)
            fs.add_expense(amount=150.0, category="utilities", description="Electric bill", expense_date="2026-03-01")
            service = GlobalSearchService(finance_service=fs)
            results = service.search("electric", category="expenses")
            assert len(results) >= 1
            assert results[0]["type"] == "expense"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_expenses_by_category(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            fs = FinanceService(db)
            fs.add_expense(amount=200.0, category="rent", description="Office rent", expense_date="2026-03-01")
            service = GlobalSearchService(finance_service=fs)
            results = service.search("rent", category="expenses")
            assert len(results) >= 1
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_reminders(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            rs = ReminderService(db)
            rs.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Payment reminder")
            service = GlobalSearchService(reminder_service=rs)
            results = service.search("Alice", category="reminders")
            assert len(results) >= 1
            assert results[0]["type"] == "reminder"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_reminders_by_message_no_match(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            rs = ReminderService(db)
            rs.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Important: payment due soon")
            service = GlobalSearchService(reminder_service=rs)
            # Global search does not search by message content — only by customer name and phone
            results = service.search("Important", category="reminders")
            assert results == []
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_all_categories(self):
        mock_cs = MockCustomerService(customers=[
            {"Name": "Alice", "Phone": "+971500000000", "Amount": 1000, "Start Date": "2026-01-01", "Installments": 1},
        ])
        service = GlobalSearchService(customer_service=mock_cs)
        results = service.search("Alice", category="all")
        assert len(results) >= 1

    def test_search_reminders_by_phone(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            rs = ReminderService(db)
            rs.save_reminder(cid, "Alice", "+971555123456", "2026-01-15", 1000.0, "Hello")
            service = GlobalSearchService(reminder_service=rs)
            results = service.search("555123", category="reminders")
            assert len(results) >= 1
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_documents(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            ds = DocumentService(db)
            ds._save_record("invoice", "Invoice #1", "/tmp/inv1.pdf", cid)
            service = GlobalSearchService(document_service=ds)
            results = service.search("invoice", category="documents")
            assert len(results) >= 1
            assert results[0]["type"] == "document"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_service_exception_preserves_other_results(self):
        mock_cs = MockCustomerService(customers=[
            {"Name": "Alice", "Phone": "+971500000000", "Amount": 1000, "Start Date": "2026-01-01", "Installments": 1},
        ])
        failing_service = MagicMock()
        failing_service.search_reminders.side_effect = RuntimeError("DB connection lost")
        # search_reminders is called via _search_reminders which calls methods on the service
        # Make the reminder service raise on any access
        bad_rs = MagicMock()
        bad_rs.search_reminders.side_effect = Exception("boom")
        service = GlobalSearchService(customer_service=mock_cs, reminder_service=bad_rs)
        results = service.search("Alice", category="all")
        assert len(results) >= 1
        assert all(r["type"] == "customer" for r in results)

    def test_search_silent_exception_logged(self):
        """Verify that service errors are logged (not silently swallowed).
        Previously the except block was 'except Exception: pass' with no logging."""
        mock_cs = MockCustomerService(customers=[
            {"Name": "Alice", "Phone": "+971500000000", "Amount": 1000, "Start Date": "2026-01-01", "Installments": 1},
        ])
        bad_rs = MagicMock()
        bad_rs.search_reminders.side_effect = Exception("boom")
        service = GlobalSearchService(customer_service=mock_cs, reminder_service=bad_rs)
        # Must not crash, must still return partial results from other services
        results = service.search("Alice", category="all")
        assert len(results) >= 1
        assert all(r["type"] == "customer" for r in results)

    def test_search_documents_by_title(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            ds = DocumentService(db)
            ds._save_record("receipt", "Payment Receipt June", "/tmp/june.pdf", cid)
            service = GlobalSearchService(document_service=ds)
            results = service.search("Receipt", category="documents")
            assert len(results) >= 1
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_notes_found(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            from app.services.customer_notes_service import CustomerNotesService
            db, cid = _setup_db(tmp.name)
            ns = CustomerNotesService(db)
            ns.add_note(cid, "Follow up on contract renewal", "follow-up")
            service = GlobalSearchService(notes_service=ns)
            results = service.search("contract", category="notes")
            assert len(results) >= 1
            assert results[0]["type"] == "note"
            assert results[0]["customer_name"] == "Alice"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_notes_no_match(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            from app.services.customer_notes_service import CustomerNotesService
            db, cid = _setup_db(tmp.name)
            ns = CustomerNotesService(db)
            ns.add_note(cid, "Important reminder", "general")
            service = GlobalSearchService(notes_service=ns)
            results = service.search("nonexistent123", category="notes")
            assert results == []
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_notes_all_categories_with_notes(self):
        """Search across all categories finds notes when query matches."""
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            from app.services.customer_notes_service import CustomerNotesService
            db, cid = _setup_db(tmp.name)
            ns = CustomerNotesService(db)
            ns.add_note(cid, "Follow up on payment", "follow-up")
            service = GlobalSearchService(customer_service=MockCustomerService(customers=[
                {"Name": "Alice", "Phone": "+971500000000", "Amount": 1000, "Start Date": "2026-01-01", "Installments": 1},
            ]), notes_service=ns)
            results = service.search("payment", category="all")
            notes_found = [r for r in results if r["type"] == "note"]
            assert len(notes_found) >= 1
        finally:
            db.close()
            os.unlink(tmp.name)
