"""Lightweight REST API server (no external dependencies)."""
import json
import logging
import re
import sqlite3
import sys
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

from app.database.database import DatabaseManager
from app.extensions.events import dispatcher
from app.core.settings import settings
from app.utils.serialization import dict_factory

logger = logging.getLogger(__name__)

RouteHandler = Callable[[Dict[str, Any], Dict[str, str]], Any]


class RESTAPI:
    """Minimal HTTP router built on Python's http.server."""

    def __init__(self, db: DatabaseManager, host: str = "127.0.0.1", port: int = 8765):
        self.db = db
        self.host = host
        self.port = port
        self._routes: Dict[str, List[tuple]] = {"GET": [], "POST": [], "PUT": [], "DELETE": []}
        self._server = None

    def route(self, method: str, path: str):
        def wrapper(fn: RouteHandler):
            pattern = re.compile(
                "^" + re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", path) + "$"
            )
            self._routes[method.upper()].append((pattern, fn))
            return fn
        return wrapper

    def _dispatch(self, method: str, path: str, body: bytes = b"") -> tuple:
        for pattern, handler in self._routes.get(method, []):
            m = pattern.match(path)
            if m:
                try:
                    params = m.groupdict()
                    data = json.loads(body) if body else {}
                except json.JSONDecodeError:
                    return (400, {"success": False, "error": "Invalid JSON body"})
                try:
                    result = handler(data, params)
                    if isinstance(result, tuple) and len(result) == 2:
                        return result
                    return (200, result)
                except Exception:
                    logger.exception("API handler error")
                    return (500, {"success": False, "error": "Internal server error"})
        return (404, {"success": False, "error": "Not found"})

    def start(self):
        from http.server import HTTPServer, BaseHTTPRequestHandler

        api = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, code, data):
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())

            def do_GET(self):
                parsed = urlparse(self.path)
                code, data = api._dispatch("GET", parsed.path)
                self._send(code, data)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else b"{}"
                parsed = urlparse(self.path)
                code, data = api._dispatch("POST", parsed.path, body)
                self._send(code, data)

            def do_PUT(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else b"{}"
                parsed = urlparse(self.path)
                code, data = api._dispatch("PUT", parsed.path, body)
                self._send(code, data)

            def do_DELETE(self):
                parsed = urlparse(self.path)
                code, data = api._dispatch("DELETE", parsed.path)
                self._send(code, data)

            def log_message(self, fmt, *args):
                logger.debug("HTTP: %s", fmt % args)

        self._server = HTTPServer((self.host, self.port), Handler)
        logger.info("REST API listening on http://%s:%s", self.host, self.port)
        self._server.serve_forever()

    def stop(self):
        if self._server:
            self._server.shutdown()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _query(self, sql: str, params=()) -> List[dict]:
        conn = self.db.connect()
        old_factory = conn.row_factory
        conn.row_factory = dict_factory
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.row_factory = old_factory

    def _query_one(self, sql: str, params=()) -> Optional[dict]:
        rows = self._query(sql, params)
        return rows[0] if rows else None

    def _execute(self, sql: str, params=()) -> int:
        conn = self.db.connect()
        try:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.lastrowid
        except Exception:
            conn.rollback()
            raise


def register_default_endpoints(api: RESTAPI, services: dict):
    svc_map = {k.lower(): v for k, v in services.items()}
    activity = svc_map.get("activity_service")

    @api.route("GET", "/api/health")
    def health(data, params):
        return {"status": "ok", "time": datetime.now().isoformat()}

    @api.route("GET", "/api/events")
    def list_events(data, params):
        from app.extensions.events.event import EVENTS
        return {"events": list(EVENTS.keys())}

    @api.route("GET", "/api/customers")
    def list_customers(data, params):
        rows = api._query("SELECT * FROM customers ORDER BY id DESC")
        return {"customers": rows, "total": len(rows)}

    @api.route("GET", "/api/customers/<customer_id>")
    def get_customer(data, params):
        try:
            cid = int(params["customer_id"])
        except (ValueError, TypeError):
            return (400, {"success": False, "error": "Invalid customer ID"})
        row = api._query_one("SELECT * FROM customers WHERE id = ?", (cid,))
        if not row:
            return (404, {"success": False, "error": "Customer not found"})
        inst = api._query("SELECT * FROM installments WHERE customer_id = ?", (cid,))
        return {"customer": row, "installments": inst}

    @api.route("POST", "/api/customers")
    def create_customer(data, params):
        from app.core.validation import ValidationService
        name = data.get("name", "")
        phone = data.get("phone", "")
        amount = str(data.get("total_amount", ""))
        installments = str(data.get("installment_count", ""))
        start_date = data.get("start_date", "")

        validation = ValidationService.validate_customer(name, phone, amount, installments, start_date)
        if not validation:
            return (400, {"success": False, "error": "; ".join(validation.errors)})

        now = datetime.now().isoformat()
        cid = api._execute(
            "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, phone, float(amount), int(installments), start_date, now, now)
        )
        dispatcher.emit("customer.created", {"customer_id": cid})
        if activity:
            activity.log("CUSTOMER_CREATED", customer_id=cid, detail=f"API — {name}")
        return {"id": cid}

    @api.route("GET", "/api/installments")
    def list_installments(data, params):
        rows = api._query("SELECT i.*, c.customer_name FROM installments i JOIN customers c ON i.customer_id = c.id ORDER BY i.id DESC LIMIT 200")
        return {"installments": rows}

    @api.route("GET", "/api/installments/<installment_id>")
    def get_installment(data, params):
        try:
            iid = int(params["installment_id"])
        except (ValueError, TypeError):
            return (400, {"success": False, "error": "Invalid installment ID"})
        row = api._query_one("SELECT i.*, c.customer_name FROM installments i JOIN customers c ON i.customer_id = c.id WHERE i.id = ?", (iid,))
        if not row:
            return (404, {"success": False, "error": "Installment not found"})
        return {"installment": row}

    @api.route("POST", "/api/installments")
    def create_installment(data, params):
        try:
            customer_id = int(data.get("customer_id", 0))
        except (ValueError, TypeError):
            return (400, {"success": False, "error": "customer_id must be an integer"})
        if customer_id <= 0:
            return (400, {"success": False, "error": "customer_id must be a positive integer"})
        customer = api._query_one("SELECT id FROM customers WHERE id = ?", (customer_id,))
        if not customer:
            return (404, {"success": False, "error": "Customer not found"})
        try:
            amount = float(data.get("amount", 0))
        except (ValueError, TypeError):
            return (400, {"success": False, "error": "amount must be a number"})
        if amount < 0:
            return (400, {"success": False, "error": "amount must be non-negative"})
        try:
            number = int(data.get("number", 1))
        except (ValueError, TypeError):
            return (400, {"success": False, "error": "number must be an integer"})
        due_date = data.get("due_date", "")
        if not due_date:
            return (400, {"success": False, "error": "due_date is required"})
        status = data.get("status", "pending")
        if status not in ("pending", "paid", "overdue", "cancelled"):
            return (400, {"success": False, "error": f"Invalid status '{status}'"})

        iid = api._execute(
            "INSERT INTO installments (customer_id, installment_number, due_date, amount, status) VALUES (?, ?, ?, ?, ?)",
            (customer_id, number, due_date, amount, status)
        )
        dispatcher.emit("installment.created", {"installment_id": iid})
        if activity:
            activity.log("INSTALLMENT_CREATED", customer_id=customer_id, detail=f"API — installment {iid}")
        return {"id": iid}

    @api.route("POST", "/api/installments/<installment_id>/pay")
    def pay_installment(data, params):
        try:
            iid = int(params["installment_id"])
        except (ValueError, TypeError):
            return (400, {"success": False, "error": "Invalid installment ID"})
        installment = api._query_one("SELECT * FROM installments WHERE id = ?", (iid,))
        if not installment:
            return (404, {"success": False, "error": "Installment not found"})
        if installment["status"] == "paid":
            return (409, {"success": False, "error": "Installment already paid"})
        now = datetime.now().strftime("%Y-%m-%d")
        api._execute("UPDATE installments SET status='paid', paid_date=? WHERE id=?", (now, iid))
        cid = installment.get("customer_id")
        dispatcher.emit("installment.paid", {"installment_id": iid})
        if activity:
            activity.log("INSTALLMENT_PAID", customer_id=cid, detail=f"API — installment {iid}")
        return {"status": "paid"}

    @api.route("GET", "/api/reports/overview")
    def report_overview(data, params):
        total_customers = api._query_one("SELECT COUNT(*) as c FROM customers")["c"]
        total_installments = api._query_one("SELECT COUNT(*) as c FROM installments")["c"]
        paid = api._query_one("SELECT COUNT(*) as c FROM installments WHERE status='paid'")["c"]
        pending = api._query_one("SELECT COUNT(*) as c FROM installments WHERE status='pending'")["c"]
        total_amount = api._query_one("SELECT COALESCE(SUM(amount), 0) as s FROM installments WHERE status='paid'")["s"]
        return {
            "total_customers": total_customers,
            "total_installments": total_installments,
            "paid": paid,
            "pending": pending,
            "total_collected": total_amount,
            "collection_rate": round(paid / total_installments * 100, 1) if total_installments else 0,
        }

    @api.route("POST", "/api/events/emit")
    def emit_event(data, params):
        from app.extensions.events.event import EVENTS
        event_name = data.get("event", "")
        if not event_name:
            return (400, {"success": False, "error": "event name is required"})
        if event_name not in EVENTS:
            return (400, {"success": False, "error": f"Unknown event '{event_name}'"})
        dispatcher.emit(event_name, data.get("data", {}))
        if activity:
            activity.log("EVENT_EMITTED", detail=f"API — {event_name}")
        return {"emitted": event_name}

    @api.route("GET", "/api/settings")
    def get_settings(data, params):
        return {k: str(v) for k, v in vars(settings).items() if not k.startswith("_")}

    @api.route("GET", "/api/system/info")
    def system_info(data, params):
        return {
            "python_version": sys.version,
            "sqlite_version": sqlite3.sqlite_version,
            "app": services.get("app_name", "Installments Tracker"),
            "version": services.get("version", "2.0.0"),
        }


def start_api_server(db: DatabaseManager, services: dict, host="127.0.0.1", port=8765):
    from threading import Thread
    api = RESTAPI(db, host, port)
    register_default_endpoints(api, services)
    t = Thread(target=api.start, daemon=True)
    t.start()
    return api
