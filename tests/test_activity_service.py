import os
import tempfile

from app.database.database import DatabaseManager
from app.services.activity_service import ActivityService, ACTIONS


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


class TestActivityService:
    def test_log_creates_entry(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ActivityService(db)
            rid = service.log("Test action", customer_id=cid, detail="Test detail")
            assert rid is None  # log() returns None

            entries = service.get_all()
            assert len(entries) >= 1
            newest = entries[0]
            assert newest["action"] == "Test action"
            assert newest["customer_id"] == cid
            assert newest["detail"] == "Test detail"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_log_without_customer(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, _ = _setup_db(tmp.name)
            service = ActivityService(db)
            service.log("Anonymous action", detail="No customer")
            entries = service.get_all()
            assert len(entries) >= 1
            assert entries[0]["customer_id"] is None
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_all_returns_ordered(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ActivityService(db)
            service.log("First", customer_id=cid)
            service.log("Second", customer_id=cid)
            entries = service.get_all()
            assert len(entries) >= 2
            assert entries[0]["action"] == "Second"
            assert entries[1]["action"] == "First"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_all_empty(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = ActivityService(db)
            assert service.get_all() == []
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_all_respects_limit(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ActivityService(db)
            for i in range(5):
                service.log(f"Event {i}", customer_id=cid)
            entries = service.get_all(limit=3)
            assert len(entries) == 3
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_for_customer(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ActivityService(db)
            service.log("For Alice", customer_id=cid)
            service.log("No customer")
            entries = service.get_for_customer(cid)
            assert len(entries) == 1
            assert entries[0]["action"] == "For Alice"
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_for_customer_no_activity(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ActivityService(db)
            assert service.get_for_customer(cid) == []
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_for_customer_invalid_id(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, _ = _setup_db(tmp.name)
            service = ActivityService(db)
            assert service.get_for_customer(99999) == []
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_get_recent_calls_get_all(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid = _setup_db(tmp.name)
            service = ActivityService(db)
            for i in range(25):
                service.log(f"Event {i}", customer_id=cid)
            recent = service.get_recent()
            assert len(recent) == 20
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_actions_dict_contains_expected_keys(self):
        assert "CUSTOMER_CREATED" in ACTIONS
        assert "CUSTOMER_EDITED" in ACTIONS
        assert "CUSTOMER_DELETED" in ACTIONS
        assert "INSTALLMENT_PAID" in ACTIONS
        assert "TASK_CREATED" in ACTIONS
        assert "TASK_DELETED" in ACTIONS
        assert "EXPENSE_CREATED" in ACTIONS
        assert "EXPENSE_DELETED" in ACTIONS
        assert "REMINDER_CREATED" in ACTIONS
        assert "REMINDER_EDITED" in ACTIONS
        assert "REMINDER_SENT" in ACTIONS
        assert "REMINDER_RESENT" in ACTIONS
        assert "REMINDER_DELETED" in ACTIONS
        assert "REMINDER_CANCELLED" in ACTIONS
