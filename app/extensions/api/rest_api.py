"""Lightweight REST API server (no external dependencies)."""

import io
import json
import logging
import mimetypes
import os
import re
import sqlite3
import sys
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from app.database.database import DatabaseManager
from app.extensions.events import dispatcher
from app.core.settings import settings

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
                    result = handler(data, params)
                    return (200, result)
                except Exception as e:
                    logger.error("API error: %s\n%s", e, traceback.format_exc())
                    return (500, {"error": str(e)})
        return (404, {"error": "Not found"})

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
        conn.row_factory = lambda c, r: {col[0]: r[idx] for idx, col in enumerate(c.description)}
        return conn.execute(sql, params).fetchall()

    def _query_one(self, sql: str, params=()) -> Optional[dict]:
        rows = self._query(sql, params)
        return rows[0] if rows else None

    def _execute(self, sql: str, params=()) -> int:
        conn = self.db.connect()
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def register_default_endpoints(api: RESTAPI, services: dict):
    svc_map = {k.lower(): v for k, v in services.items()}

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
        row = api._query_one("SELECT * FROM customers WHERE id = ?", (params["customer_id"],))
        if not row:
            return {"error": "Not found"}
        inst = api._query("SELECT * FROM installments WHERE customer_id = ?", (params["customer_id"],))
        return {"customer": row, "installments": inst}

    @api.route("POST", "/api/customers")
    def create_customer(data, params):
        now = datetime.now().isoformat()
        cid = api._execute(
            "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (data.get("name", ""), data.get("phone", ""), float(data.get("total_amount", 0)),
             int(data.get("installment_count", 0)), data.get("start_date", ""), now, now)
        )
        dispatcher.emit("customer.created", {"customer_id": cid})
        return {"id": cid}

    @api.route("GET", "/api/installments")
    def list_installments(data, params):
        rows = api._query("SELECT i.*, c.customer_name FROM installments i JOIN customers c ON i.customer_id = c.id ORDER BY i.id DESC LIMIT 200")
        return {"installments": rows}

    @api.route("GET", "/api/installments/<installment_id>")
    def get_installment(data, params):
        row = api._query_one("SELECT i.*, c.customer_name FROM installments i JOIN customers c ON i.customer_id = c.id WHERE i.id = ?", (params["installment_id"],))
        return {"installment": row} if row else {"error": "Not found"}

    @api.route("POST", "/api/installments")
    def create_installment(data, params):
        iid = api._execute(
            "INSERT INTO installments (customer_id, installment_number, due_date, amount, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (int(data.get("customer_id", 0)), int(data.get("number", 1)),
             data.get("due_date", ""), float(data.get("amount", 0)),
             data.get("status", "pending"), datetime.now().isoformat())
        )
        dispatcher.emit("installment.created", {"installment_id": iid})
        return {"id": iid}

    @api.route("POST", "/api/installments/<installment_id>/pay")
    def pay_installment(data, params):
        now = datetime.now().strftime("%Y-%m-%d")
        api._execute("UPDATE installments SET status='paid', paid_date=? WHERE id=?", (now, params["installment_id"]))
        dispatcher.emit("installment.paid", {"installment_id": int(params["installment_id"])})
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
        dispatcher.emit(data.get("event", ""), data.get("data", {}))
        return {"emitted": data.get("event")}

    @api.route("GET", "/api/settings")
    def get_settings(data, params):
        return {k: str(v) for k, v in vars(settings).items() if not k.startswith("_")}

    @api.route("GET", "/api/system/info")
    def system_info(data, params):
        import sys, sqlite3
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
