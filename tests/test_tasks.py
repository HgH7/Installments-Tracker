import os
import tempfile

from app.database.database import DatabaseManager
from app.services.task_service import TaskService


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
    conn.commit()
    return db, cid, bob_id


def _create_task(service, title="TestTask", customer_id=None, due_date="2026-07-10",
                 priority="medium", task_type="general"):
    return service.create_task(title=title, customer_id=customer_id,
                               description="Test description",
                               due_date=due_date, priority=priority, task_type=task_type)


class TestTaskService:
    def test_create_task(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = TaskService(db)
            task_id = _create_task(service, customer_id=cid)
            assert task_id > 0
            task = service.get_task(task_id)
            assert task is not None
            assert task["title"] == "TestTask"
            assert task["customer_id"] == cid
            assert task["status"] == "pending"
            assert task["priority"] == "medium"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_create_task_no_customer(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = TaskService(db)
            task_id = _create_task(service)
            assert task_id > 0
            task = service.get_task(task_id)
            assert task["customer_id"] is None
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_task_not_found(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = TaskService(db)
            assert service.get_task(999) is None
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_tasks_empty(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = TaskService(db)
            assert service.get_tasks() == []
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_tasks_filters_by_status(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = TaskService(db)
            _create_task(service, customer_id=cid)
            _create_task(service, customer_id=cid, title="Task2")
            service.update_task_status(1, "completed")
            pending = service.get_tasks(status="pending")
            assert len(pending) == 1
            completed = service.get_tasks(status="completed")
            assert len(completed) == 1
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_tasks_filters_by_customer(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, alice_id, bob_id = _setup_db(tmp.name)
            service = TaskService(db)
            _create_task(service, customer_id=alice_id, title="AliceTask")
            _create_task(service, customer_id=bob_id, title="BobTask")
            alice_tasks = service.get_tasks(customer_id=alice_id)
            assert len(alice_tasks) == 1
            assert alice_tasks[0]["title"] == "AliceTask"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_update_task_status(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = TaskService(db)
            task_id = _create_task(service, customer_id=cid)
            assert service.update_task_status(task_id, "completed") is True
            task = service.get_task(task_id)
            assert task["status"] == "completed"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_update_task_status_invalid(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = TaskService(db)
            try:
                service.update_task_status(1, "invalid_status")
                assert False, "Expected ValueError"
            except ValueError:
                pass
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_update_task(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = TaskService(db)
            task_id = _create_task(service, customer_id=cid)
            assert service.update_task(task_id, title="Updated Title", priority="high") is True
            task = service.get_task(task_id)
            assert task["title"] == "Updated Title"
            assert task["priority"] == "high"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_delete_task(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = TaskService(db)
            task_id = _create_task(service, customer_id=cid)
            assert service.get_task(task_id) is not None
            assert service.delete_task(task_id) is True
            assert service.get_task(task_id) is None
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_delete_task_non_existing(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = TaskService(db)
            assert service.delete_task(999) is False
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_tasks_by_date(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = TaskService(db)
            _create_task(service, customer_id=cid, due_date="2026-07-15", title="DueJul15")
            _create_task(service, customer_id=cid, due_date="2026-07-10", title="DueJul10")
            tasks = service.get_tasks_by_date("2026-07-10")
            assert len(tasks) == 1
            assert tasks[0]["title"] == "DueJul10"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_upcoming_tasks(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = TaskService(db)
            _create_task(service, customer_id=cid, due_date="2026-07-15", title="DueJul15")
            _create_task(service, customer_id=cid, due_date="2026-08-20", title="DueAug20")
            tasks = service.get_upcoming_tasks(days=30)
            dates = [t["due_date"] for t in tasks if t["due_date"]]
            assert "2026-07-15" in dates
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_overdue_tasks(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = TaskService(db)
            _create_task(service, customer_id=cid, due_date="2020-01-01", title="Overdue")
            _create_task(service, customer_id=cid, due_date="2099-01-01", title="Future")
            overdue = service.get_overdue_tasks()
            titles = [t["title"] for t in overdue]
            assert "Overdue" in titles
            assert "Future" not in titles
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_customer_name_for_doc(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = TaskService(db)
            assert service.get_customer_name_for_doc(cid) == "Alice"
            assert service.get_customer_name_for_doc(999) == "ID:999"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_customer_id_by_name(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = TaskService(db)
            assert service.get_customer_id_by_name("Alice") == cid
            assert service.get_customer_id_by_name("NonExistent") is None
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_tasks_includes_customer_name(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = TaskService(db)
            task_id = _create_task(service, customer_id=cid)
            task = service.get_task(task_id)
            assert task["customer_name"] == "Alice"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
