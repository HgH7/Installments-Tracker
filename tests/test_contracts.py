import os
import sqlite3
import tempfile

from app.database.database import DatabaseManager
from app.services.contract_service import ContractService


def _create_customer(conn, name="Alice"):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (name, "+971500000000", 1000.0, 1, "2026-01-01", "", "2026-01-01 00:00:00", "2026-01-01 00:00:00"),
    )
    conn.commit()
    return cur.lastrowid


def _create_contract(service, customer_id):
    return service.create_contract(customer_id)


def test_create_contract_rejects_unknown_customer():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        db = DatabaseManager(tmp.name)
        db.initialize()
        service = ContractService(db)

        with sqlite3.connect(tmp.name) as conn:
            _create_customer(conn)

        try:
            service.create_contract(999)
            assert False, "Expected ValueError for unknown customer"
        except ValueError as exc:
            assert "Customer not found" in str(exc)
    finally:
        db.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def test_update_contract_details_and_status_validation():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        db = DatabaseManager(tmp.name)
        db.initialize()
        service = ContractService(db)

        with sqlite3.connect(tmp.name) as conn:
            customer_id = _create_customer(conn)

        contract = _create_contract(service, customer_id)
        assert service.update_contract(contract["id"], notes="Signed by client", signed_date="2026-02-15") is True
        updated = service.get_contract(contract["id"])
        assert updated["notes"] == "Signed by client"
        assert updated["signed_date"] == "2026-02-15"

        try:
            service.update_contract_status(contract["id"], "completed")
            assert False, "Expected ValueError for invalid transition"
        except ValueError as exc:
            assert "Invalid status transition" in str(exc)
    finally:
        db.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def test_template_duplicate_and_filtering():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        db = DatabaseManager(tmp.name)
        db.initialize()
        service = ContractService(db)

        template_id = service.create_template("Base", "Terms")
        duplicated = service.duplicate_template(template_id, "Base Copy")
        assert duplicated is not None
        assert duplicated["name"] == "Base Copy"

        with sqlite3.connect(tmp.name) as conn:
            customer_id = _create_customer(conn, name="Bob")

        contract = _create_contract(service, customer_id)
        results = service.find_contract(query="", status="draft")
        assert any(item["id"] == contract["id"] for item in results)
    finally:
        db.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def test_full_status_transition_workflow():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        db = DatabaseManager(tmp.name)
        db.initialize()
        service = ContractService(db)

        with sqlite3.connect(tmp.name) as conn:
            customer_id = _create_customer(conn)

        contract = _create_contract(service, customer_id)
        assert contract["status"] == "draft"

        assert service.update_contract_status(contract["id"], "pending") is True
        assert service.get_contract(contract["id"])["status"] == "pending"

        assert service.update_contract_status(contract["id"], "sent") is True
        assert service.get_contract(contract["id"])["status"] == "sent"

        assert service.update_contract_status(contract["id"], "signed") is True
        assert service.get_contract(contract["id"])["status"] == "signed"

        assert service.update_contract_status(contract["id"], "completed") is True
        assert service.get_contract(contract["id"])["status"] == "completed"
    finally:
        db.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def test_status_transition_cancellation():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        db = DatabaseManager(tmp.name)
        db.initialize()
        service = ContractService(db)

        with sqlite3.connect(tmp.name) as conn:
            customer_id = _create_customer(conn)

        contract = _create_contract(service, customer_id)

        assert service.update_contract_status(contract["id"], "pending") is True
        assert service.update_contract_status(contract["id"], "cancelled") is True
        assert service.get_contract(contract["id"])["status"] == "cancelled"

        try:
            service.update_contract_status(contract["id"], "pending")
            assert False, "Expected ValueError for transition from cancelled"
        except ValueError as exc:
            assert "Invalid status transition" in str(exc)
    finally:
        db.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def test_completed_or_cancelled_accept_no_transitions():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        db = DatabaseManager(tmp.name)
        db.initialize()
        service = ContractService(db)

        with sqlite3.connect(tmp.name) as conn:
            customer_id = _create_customer(conn)

        for terminal_status in ("completed", "cancelled"):
            contract = _create_contract(service, customer_id)
            if terminal_status == "completed":
                service.update_contract_status(contract["id"], "pending")
                service.update_contract_status(contract["id"], "sent")
                service.update_contract_status(contract["id"], "signed")
                service.update_contract_status(contract["id"], "completed")
            else:
                service.update_contract_status(contract["id"], "cancelled")

            for invalid_next in ("draft", "pending", "sent", "signed", "completed", "cancelled"):
                if invalid_next == terminal_status:
                    continue
                try:
                    service.update_contract_status(contract["id"], invalid_next)
                    assert False, f"Expected ValueError for {terminal_status} -> {invalid_next}"
                except ValueError:
                    pass
    finally:
        db.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def test_template_create_edit_delete():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        db = DatabaseManager(tmp.name)
        db.initialize()
        service = ContractService(db)

        tid = service.create_template("Test", "Content here")
        assert tid > 0

        t = service.get_template(tid)
        assert t["name"] == "Test"
        assert t["content"] == "Content here"

        assert service.update_template(tid, name="Updated") is True
        t = service.get_template(tid)
        assert t["name"] == "Updated"

        assert service.delete_template(tid) is True
        assert service.get_template(tid) is None
    finally:
        db.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def test_contract_customer_summary_and_id_lookup():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        db = DatabaseManager(tmp.name)
        db.initialize()
        service = ContractService(db)

        with sqlite3.connect(tmp.name) as conn:
            cid = _create_customer(conn, name="TestCustomer")

        summary = service.get_customer_summary(cid)
        assert summary is not None
        assert summary["customer_name"] == "TestCustomer"
        assert summary["phone_number"] == "+971500000000"

        found_id = service.get_customer_id_by_name("TestCustomer")
        assert found_id == cid

        assert service.get_customer_id_by_name("NonExistent") is None
        assert service.get_customer_summary(999) is None
    finally:
        db.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def test_contract_filtering_by_multiple_criteria():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        db = DatabaseManager(tmp.name)
        db.initialize()
        service = ContractService(db)

        with sqlite3.connect(tmp.name) as conn:
            cid1 = _create_customer(conn, name="Alice")
            cid2 = _create_customer(conn, name="Bob")

        c1 = _create_contract(service, cid1)
        c2 = _create_contract(service, cid2)

        service.update_contract_status(c1["id"], "pending")

        results = service.find_contract(query="Alice")
        assert len(results) == 1
        assert results[0]["id"] == c1["id"]

        results = service.find_contract(query="", status="pending")
        assert len(results) == 1
        assert results[0]["id"] == c1["id"]

        results = service.find_contract(query="", customer_id=cid2)
        assert len(results) == 1
        assert results[0]["id"] == c2["id"]

        results = service.get_all_contracts()
        assert len(results) == 2
    finally:
        db.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def test_contract_update_with_template_and_pdf_path():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        db = DatabaseManager(tmp.name)
        db.initialize()
        service = ContractService(db)

        with sqlite3.connect(tmp.name) as conn:
            customer_id = _create_customer(conn)

        tid = service.create_template("Base", "Template content")
        contract = _create_contract(service, customer_id)

        assert service.update_contract(contract["id"], template_id=tid, pdf_path="/tmp/test.pdf") is True
        updated = service.get_contract(contract["id"])
        assert updated["pdf_path"] == "/tmp/test.pdf"
        assert updated["template_id"] == tid
    finally:
        db.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
