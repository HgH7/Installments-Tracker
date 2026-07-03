"""Tests for the REST API server."""
import json
import os
import tempfile

import pytest

from app.database.database import DatabaseManager
from app.extensions.api.rest_api import RESTAPI, register_default_endpoints
from app.services.activity_service import ActivityService


def _setup_db(tmpdir):
    db_path = os.path.join(tmpdir, "test.db")
    db = DatabaseManager(db_path)
    db.initialize()
    with db.transaction() as cur:
        cur.execute(
            "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("Alice", "+971500000000", 1000.0, 1, "2026-01-01", "", "2026-01-01", "2026-01-01"),
        )
        cid = cur.lastrowid
        cur.execute(
            "INSERT INTO installments (customer_id, installment_number, due_date, amount, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (cid, 1, "2026-02-01", 1000.0, "pending"),
        )
        iid = cur.lastrowid
    return db, cid, iid


@pytest.fixture
def api():
    tmpdir = tempfile.mkdtemp(prefix="api_test_")
    db, cid, iid = _setup_db(tmpdir)
    api_obj = RESTAPI(db)
    services = {
        "activity_service": ActivityService(db),
        "app_name": "TestApp",
        "version": "1.0.0",
    }
    register_default_endpoints(api_obj, services)
    yield api_obj, cid, iid, db, tmpdir
    db.close()


# ── Helpers ──────────────────────────────────────────────────────────────

def _dispatch_get(api, path):
    return api._dispatch("GET", path)

def _dispatch_post(api, path, data=None):
    body = json.dumps(data).encode() if data else b"{}"
    return api._dispatch("POST", path, body)


# ── Health ───────────────────────────────────────────────────────────────

def test_health(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/health")
    assert code == 200
    assert data["status"] == "ok"
    assert "time" in data


# ── Events ───────────────────────────────────────────────────────────────

def test_list_events(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/events")
    assert code == 200
    assert isinstance(data["events"], list)
    assert "customer.created" in data["events"]


# ── Customers ────────────────────────────────────────────────────────────

def test_list_customers(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/customers")
    assert code == 200
    assert len(data["customers"]) == 1
    assert data["total"] == 1
    assert data["customers"][0]["customer_name"] == "Alice"


def test_list_customers_empty_db():
    tmpdir = tempfile.mkdtemp(prefix="api_test_")
    try:
        db_path = os.path.join(tmpdir, "empty.db")
        db = DatabaseManager(db_path)
        db.initialize()
        api_obj = RESTAPI(db)
        register_default_endpoints(api_obj, {})
        code, data = _dispatch_get(api_obj, "/api/customers")
        assert code == 200
        assert data["customers"] == []
        assert data["total"] == 0
        db.close()
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def test_get_customer_found(api):
    api_obj, cid, *_ = api
    code, data = _dispatch_get(api_obj, f"/api/customers/{cid}")
    assert code == 200
    assert data["customer"]["customer_name"] == "Alice"
    assert len(data["installments"]) == 1


def test_get_customer_not_found(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/customers/99999")
    assert code == 404
    assert data["success"] is False
    assert "not found" in data["error"].lower()


def test_get_customer_invalid_id(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/customers/abc")
    assert code == 400
    assert data["success"] is False


def test_create_customer_success(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/customers", {
        "name": "Bob",
        "phone": "+971511111111",
        "total_amount": 2000.0,
        "installment_count": 2,
        "start_date": "2026-03-01",
    })
    assert code == 200
    assert "id" in data


def test_create_customer_missing_name(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/customers", {
        "phone": "+971511111111",
        "total_amount": 2000.0,
        "installment_count": 2,
        "start_date": "2026-03-01",
    })
    assert code == 400
    assert data["success"] is False


def test_create_customer_invalid_amount(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/customers", {
        "name": "Bob",
        "phone": "+971511111111",
        "total_amount": "not-a-number",
        "installment_count": 2,
        "start_date": "2026-03-01",
    })
    assert code == 400
    assert data["success"] is False


def test_create_customer_invalid_phone(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/customers", {
        "name": "Bob",
        "phone": "abc",
        "total_amount": 2000.0,
        "installment_count": 2,
        "start_date": "2026-03-01",
    })
    assert code == 400
    assert data["success"] is False


# ── Installments ─────────────────────────────────────────────────────────

def test_list_installments(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/installments")
    assert code == 200
    assert len(data["installments"]) >= 1


def test_get_installment_found(api):
    api_obj, cid, iid, db, tmpdir = api
    code, data = _dispatch_get(api_obj, f"/api/installments/{iid}")
    assert code == 200
    assert data["installment"]["customer_name"] == "Alice"


def test_get_installment_not_found(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/installments/99999")
    assert code == 404
    assert data["success"] is False


def test_get_installment_invalid_id(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/installments/abc")
    assert code == 400
    assert data["success"] is False


def test_create_installment_success(api):
    api_obj, cid, *_ = api
    code, data = _dispatch_post(api_obj, "/api/installments", {
        "customer_id": cid,
        "number": 2,
        "due_date": "2026-03-01",
        "amount": 500.0,
        "status": "pending",
    })
    assert code == 200
    assert "id" in data


def test_create_installment_missing_customer(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/installments", {
        "customer_id": 99999,
        "number": 2,
        "due_date": "2026-03-01",
        "amount": 500.0,
        "status": "pending",
    })
    assert code == 404
    assert data["success"] is False


def test_create_installment_invalid_customer_id(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/installments", {
        "customer_id": "abc",
        "number": 2,
        "due_date": "2026-03-01",
        "amount": 500.0,
        "status": "pending",
    })
    assert code == 400
    assert data["success"] is False


def test_create_installment_negative_customer_id(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/installments", {
        "customer_id": -1,
        "number": 2,
        "due_date": "2026-03-01",
        "amount": 500.0,
        "status": "pending",
    })
    assert code == 400
    assert data["success"] is False


def test_create_installment_negative_amount(api):
    api_obj, cid, *_ = api
    code, data = _dispatch_post(api_obj, "/api/installments", {
        "customer_id": cid,
        "number": 2,
        "due_date": "2026-03-01",
        "amount": -100,
        "status": "pending",
    })
    assert code == 400
    assert data["success"] is False


def test_create_installment_missing_due_date(api):
    api_obj, cid, *_ = api
    code, data = _dispatch_post(api_obj, "/api/installments", {
        "customer_id": cid,
        "number": 2,
        "amount": 500.0,
        "status": "pending",
    })
    assert code == 400
    assert data["success"] is False


def test_create_installment_invalid_status(api):
    api_obj, cid, *_ = api
    code, data = _dispatch_post(api_obj, "/api/installments", {
        "customer_id": cid,
        "number": 2,
        "due_date": "2026-03-01",
        "amount": 500.0,
        "status": "bogus_status",
    })
    assert code == 400
    assert data["success"] is False


# ── Pay Installment ──────────────────────────────────────────────────────

def test_pay_installment_success(api):
    api_obj, cid, iid, db, tmpdir = api
    code, data = _dispatch_post(api_obj, f"/api/installments/{iid}/pay")
    assert code == 200
    assert data["status"] == "paid"


def test_pay_installment_not_found(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/installments/99999/pay")
    assert code == 404
    assert data["success"] is False


def test_pay_installment_invalid_id(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/installments/abc/pay")
    assert code == 400
    assert data["success"] is False


def test_pay_installment_already_paid(api):
    api_obj, cid, iid, db, tmpdir = api
    _dispatch_post(api_obj, f"/api/installments/{iid}/pay")
    code, data = _dispatch_post(api_obj, f"/api/installments/{iid}/pay")
    assert code == 409
    assert data["success"] is False
    assert "already" in data["error"].lower()


# ── Reports ──────────────────────────────────────────────────────────────

def test_report_overview(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/reports/overview")
    assert code == 200
    assert "total_customers" in data
    assert "collection_rate" in data


# ── Events Emit ──────────────────────────────────────────────────────────

def test_emit_event_valid(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/events/emit", {
        "event": "customer.created",
        "data": {"customer_id": 1},
    })
    assert code == 200
    assert data["emitted"] == "customer.created"


def test_emit_event_missing_name(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/events/emit", {"data": {}})
    assert code == 400
    assert data["success"] is False


def test_emit_event_unknown(api):
    api_obj, *_ = api
    code, data = _dispatch_post(api_obj, "/api/events/emit", {
        "event": "nonexistent.event",
        "data": {},
    })
    assert code == 400
    assert data["success"] is False


# ── Settings ─────────────────────────────────────────────────────────────

def test_get_settings(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/settings")
    assert code == 200
    assert isinstance(data, dict)


# ── System Info ──────────────────────────────────────────────────────────

def test_system_info(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/system/info")
    assert code == 200
    assert "python_version" in data
    assert "sqlite_version" in data
    assert data["app"] == "TestApp"


# ── Routing ──────────────────────────────────────────────────────────────

def test_unknown_route(api):
    api_obj, *_ = api
    code, data = _dispatch_get(api_obj, "/api/nonexistent")
    assert code == 404
    assert data["success"] is False


# ── Malformed JSON ───────────────────────────────────────────────────────

def test_malformed_json_body(api):
    api_obj, *_ = api
    code, data = api_obj._dispatch("POST", "/api/customers", b"not-json")
    assert code == 400
    assert data["success"] is False
    assert "JSON" in data.get("error", "")


# ── Activity Logging ─────────────────────────────────────────────────────

def test_create_customer_logs_activity(api):
    api_obj, *_ = api
    _dispatch_post(api_obj, "/api/customers", {
        "name": "Bob",
        "phone": "+971511111111",
        "total_amount": 2000.0,
        "installment_count": 2,
        "start_date": "2026-03-01",
    })
    activity = api_obj.db.connect().execute(
        "SELECT action, detail FROM activity_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert activity is not None
    assert "API" in activity["detail"]


def test_pay_installment_logs_activity(api):
    api_obj, cid, iid, db, tmpdir = api
    _dispatch_post(api_obj, f"/api/installments/{iid}/pay")
    activity = api_obj.db.connect().execute(
        "SELECT action, detail FROM activity_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert activity is not None
    assert activity["action"] == "INSTALLMENT_PAID"
