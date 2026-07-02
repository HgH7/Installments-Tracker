import os
import sqlite3
import tempfile

import pytest

from app.database.database import DatabaseManager


class TestDatabase:
    @pytest.fixture
    def db(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        manager = DatabaseManager(tmp.name)
        manager.initialize()
        yield manager
        manager.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    def test_initialize_creates_tables(self, db):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = {row[0] for row in cursor.fetchall()}
        assert "customers" in tables
        assert "installments" in tables
        assert "attachments" in tables
        assert "backups" in tables
        assert "_schema_version" in tables

    def test_schema_version(self, db):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(version) FROM _schema_version")
        version = cursor.fetchone()[0]
        assert version == 5

    def test_insert_and_read_customer(self, db):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("Alice", "+971501234567", 3000.0, 3, "2026-01-01", "", "2026-01-01 00:00:00", "2026-01-01 00:00:00"),
        )
        conn.commit()
        cursor.execute("SELECT * FROM customers WHERE customer_name=?", ("Alice",))
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "Alice"
        assert row[2] == "+971501234567"

    def test_insert_and_read_installments(self, db):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("Bob", "+971509876543", 2000.0, 2, "2026-02-01", "", "2026-02-01 00:00:00", "2026-02-01 00:00:00"),
        )
        cid = cursor.lastrowid
        cursor.execute(
            "INSERT INTO installments (customer_id, installment_number, due_date, amount, status, notified, paid_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (cid, 1, "2026-02-01", 1000.0, "paid", 0, "2026-02-01"),
        )
        cursor.execute(
            "INSERT INTO installments (customer_id, installment_number, due_date, amount, status, notified, paid_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (cid, 2, "2026-03-01", 1000.0, "pending", 0, None),
        )
        conn.commit()

        cursor.execute("SELECT * FROM installments WHERE customer_id=?", (cid,))
        rows = cursor.fetchall()
        assert len(rows) == 2
        assert rows[0][5] == "paid"

    def test_transaction_rollback(self, db):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("Charlie", "+971505555555", 1000.0, 1, "2026-03-01", "", "2026-03-01 00:00:00", "2026-03-01 00:00:00"),
        )
        conn.commit()

        try:
            with db.transaction() as tx:
                tx.execute("DELETE FROM customers")
                tx.execute("INSERT INTO nonexistent VALUES (1)")
        except Exception:
            pass

        cursor.execute("SELECT COUNT(*) FROM customers")
        count = cursor.fetchone()[0]
        assert count == 1, "Transaction did not rollback"

    def test_foreign_key_cascade(self, db):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("Diana", "+971506666666", 1500.0, 3, "2026-04-01", "", "2026-04-01 00:00:00", "2026-04-01 00:00:00"),
        )
        cid = cursor.lastrowid
        cursor.execute(
            "INSERT INTO installments (customer_id, installment_number, due_date, amount, status, notified, paid_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (cid, 1, "2026-04-01", 500.0, "pending", 0, None),
        )
        conn.commit()

        cursor.execute("DELETE FROM customers WHERE id=?", (cid,))
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM installments WHERE customer_id=?", (cid,))
        assert cursor.fetchone()[0] == 0

    def test_indexes_exist(self, db):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = {row[0] for row in cursor.fetchall()}
        expected = {
            "idx_customers_customer_name",
            "idx_customers_phone_number",
            "idx_installments_customer_id",
            "idx_installments_due_date",
            "idx_installments_status",
            "idx_attachments_customer_id",
        }
        assert expected.issubset(indexes), f"Missing indexes: {expected - indexes}"

    def test_foreign_key_enforcement(self, db):
        conn = db.connect()
        cursor = conn.cursor()
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO installments (customer_id, installment_number, due_date, amount) VALUES (?, ?, ?, ?)",
                (9999, 1, "2026-01-01", 100.0),
            )
            conn.commit()

    def test_customer_not_null_name(self, db):
        conn = db.connect()
        cursor = conn.cursor()
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO customers (customer_name, created_at, updated_at) VALUES (?, ?, ?)",
                (None, "now", "now"),
            )
            conn.commit()

    def test_customer_default_phone(self, db):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (customer_name, created_at, updated_at) VALUES (?, ?, ?)",
            ("NoPhone", "now", "now"),
        )
        conn.commit()
        cursor.execute("SELECT phone_number FROM customers WHERE customer_name=?", ("NoPhone",))
        assert cursor.fetchone()[0] == ""

    def test_installment_default_status(self, db):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (customer_name, created_at, updated_at) VALUES (?, ?, ?)",
            ("Test", "now", "now"),
        )
        cid = cursor.lastrowid
        cursor.execute(
            "INSERT INTO installments (customer_id, installment_number, due_date, amount) VALUES (?, ?, ?, ?)",
            (cid, 1, "2026-01-01", 100.0),
        )
        conn.commit()
        cursor.execute("SELECT status FROM installments WHERE customer_id=?", (cid,))
        assert cursor.fetchone()[0] == "pending"
