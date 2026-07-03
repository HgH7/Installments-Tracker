import os
import tempfile

from app.database.database import DatabaseManager
from app.services.reminder_service import ReminderService


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


class TestReminderService:
    def test_save_reminder_returns_id(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            rid = service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Test message")
            assert rid is not None
            assert isinstance(rid, int)
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_save_reminder_default_status(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Hello")
            history = service.get_history(limit=10)
            assert len(history) == 1
            assert history[0]["status"] == "draft"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_save_reminder_custom_status(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Test", status="sent")
            history = service.get_history(limit=10)
            assert history[0]["status"] == "sent"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_save_reminder_empty_phone(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            rid = service.save_reminder(cid, "Alice", "", "2026-01-15", 1000.0, "No phone")
            assert rid is not None
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_history_empty(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = ReminderService(db)
            assert service.get_history() == []
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_history_ordered_desc(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 500.0, "First")
            service.save_reminder(cid, "Alice", "+971500000000", "2026-02-15", 500.0, "Second")
            history = service.get_history()
            assert len(history) == 2
            assert history[0]["amount"] == 500.0  # second insert has amount 500
            assert history[1]["amount"] == 500.0
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_history_respects_limit(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            for i in range(5):
                service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 100.0 * i, f"Reminder {i}")
            history = service.get_history(limit=3)
            assert len(history) == 3
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_for_customer(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "For Alice")
            history = service.get_for_customer(cid)
            assert len(history) == 1
            assert history[0]["customer_id"] == cid
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_for_customer_no_reminders(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            assert service.get_for_customer(cid) == []
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_for_customer_invalid_id(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, _ = _setup_db(tmp.name)
            service = ReminderService(db)
            assert service.get_for_customer(99999) == []
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_reminder_found(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            rid = service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Test")
            reminder = service.get_reminder(rid)
            assert reminder is not None
            assert reminder["id"] == rid
            assert reminder["customer_name"] == "Alice"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_reminder_not_found(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, _ = _setup_db(tmp.name)
            service = ReminderService(db)
            assert service.get_reminder(99999) is None
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_update_reminder_partial(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            rid = service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Original")
            ok = service.update_reminder(rid, amount=1500.0, message="Updated")
            assert ok is True
            reminder = service.get_reminder(rid)
            assert reminder["amount"] == 1500.0
            assert reminder["message"] == "Updated"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_update_reminder_not_found(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, _ = _setup_db(tmp.name)
            service = ReminderService(db)
            assert service.update_reminder(99999, amount=500.0) is False
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_delete_reminder_existing(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            rid = service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "To delete")
            assert service.delete_reminder(rid) is True
            assert service.get_reminder(rid) is None
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_delete_reminder_not_found(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, _ = _setup_db(tmp.name)
            service = ReminderService(db)
            assert service.delete_reminder(99999) is False
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_update_reminder_status(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            rid = service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Status test")
            assert service.update_reminder_status(rid, "sent") is True
            reminder = service.get_reminder(rid)
            assert reminder["status"] == "sent"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_reminders_by_customer_name(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Alice reminder")
            results = service.search_reminders(customer_name="Ali")
            assert len(results) >= 1
            assert results[0]["customer_name"] == "Alice"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_reminders_by_status(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Draft reminder")
            service.save_reminder(cid, "Alice", "+971500000000", "2026-02-15", 500.0, "Sent reminder", status="sent")
            results = service.search_reminders(status="sent")
            assert len(results) == 1
            assert results[0]["status"] == "sent"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_reminders_by_phone(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Phone search")
            results = service.search_reminders(phone="+9715")
            assert len(results) >= 1
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_reminders_empty_results(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "No match")
            results = service.search_reminders(customer_name="NonExistent")
            assert results == []
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_search_reminders_combined_filters(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            service.save_reminder(cid, "Alice", "+971500000000", "2026-01-15", 1000.0, "Match", status="draft")
            service.save_reminder(cid, "Alice", "+971500000000", "2026-02-15", 500.0, "No match", status="sent")
            results = service.search_reminders(customer_name="Alice", status="draft")
            assert len(results) == 1
            assert results[0]["status"] == "draft"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_row_factory_restored_on_exception_in_get_history(self):
        """Verify that row_factory is restored even if an exception occurs
        during query execution (e.g. invalid limit value)."""
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            conn = service._db.connect()
            original = conn.row_factory
            # Call with a string limit that will cause SQLite to fail
            results = service.get_history(limit="invalid")
            assert results == []
            # row_factory must be restored after error
            conn = service._db.connect()
            assert conn.row_factory is original
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_row_factory_restored_on_exception_in_get_reminder(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            conn = service._db.connect()
            original = conn.row_factory
            result = service.get_reminder(9999)
            assert result is None
            conn = service._db.connect()
            assert conn.row_factory is original
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_row_factory_restored_on_exception_in_search_reminders(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ReminderService(db)
            conn = service._db.connect()
            original = conn.row_factory
            results = service.search_reminders(phone=12345)
            assert isinstance(results, list)
            conn = service._db.connect()
            assert conn.row_factory is original
        finally:
            db.close()
            os.unlink(tmp.name)
