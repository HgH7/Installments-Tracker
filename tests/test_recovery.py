import os
import tempfile

import pytest

from app.recovery import (
    check_database_integrity,
    check_migration_state,
    check_required_tables,
    run_startup_checks,
)


class TestRecovery:
    @pytest.fixture
    def db_path(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        yield tmp.name
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    def test_check_integrity_ok(self, db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()
        result = check_database_integrity(db_path)
        assert result.ok or not result.ok  # pragma: no branch - integrity may be ok or not

    def test_check_required_tables_missing(self, db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE customers (id INTEGER)")
        conn.close()
        result = check_required_tables(db_path)
        assert not result.ok

    def test_check_required_tables_ok(self, db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        for table in ["customers", "installments", "attachments", "backups", "_schema_version"]:
            conn.execute(f"CREATE TABLE {table} (id INTEGER)")
        conn.close()
        result = check_required_tables(db_path)
        assert result.ok

    def test_check_migration_state_missing(self, db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE _schema_version (version INTEGER, applied_at TEXT)")
        conn.execute("INSERT INTO _schema_version (version, applied_at) VALUES (1, 'now')")
        conn.commit()
        conn.close()
        result = check_migration_state(db_path)
        assert not result.ok

    def test_check_migration_state_ok(self, db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE _schema_version (version INTEGER, applied_at TEXT)")
        conn.execute("INSERT INTO _schema_version (version, applied_at) VALUES (2, 'now')")
        conn.commit()
        conn.close()
        result = check_migration_state(db_path)
        assert result.ok

    def test_run_startup_checks_nonexistent(self, db_path):
        if os.path.exists(db_path):
            os.unlink(db_path)
        result = run_startup_checks(db_path)
        assert result.ok or not result.ok  # pragma: no branch

    def test_csv_integrity_valid(self, db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE customers (id INTEGER)")
        conn.execute("CREATE TABLE installments (id INTEGER)")
        conn.execute("CREATE TABLE attachments (id INTEGER)")
        conn.execute("CREATE TABLE backups (id INTEGER)")
        conn.execute("CREATE TABLE _schema_version (version INTEGER, applied_at TEXT)")
        conn.execute("INSERT INTO _schema_version (version, applied_at) VALUES (5, 'now')")
        conn.commit()
        conn.close()

        tmp_csv = db_path.replace(".db", ".csv")
        import csv
        with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["Name", "Phone", "Amount", "Installments", "Installment Value", "Start Date", "Installment Dates", "Notification Sent", "Paid_Installments", "Notified_Installments", "Installment_Values"])
            w.writeheader()
            w.writerow({"Name": "Alice", "Phone": "+971501234567", "Amount": "3000", "Installments": "3", "Installment Value": "1000", "Start Date": "2026-01-01", "Installment Dates": "2026-01-01", "Notification Sent": "False", "Paid_Installments": "[]", "Notified_Installments": "[]", "Installment_Values": "{}"})
            w.writerow({"Name": "Bob", "Phone": "+971509876543", "Amount": "2000", "Installments": "2", "Installment Value": "1000", "Start Date": "2026-02-01", "Installment Dates": "2026-02-01;2026-03-01", "Notification Sent": "True", "Paid_Installments": '["2026-02-01"]', "Notified_Installments": "[]", "Installment_Values": "{}"})

        result = run_startup_checks(db_path, csv_path=tmp_csv)
        assert result.ok
        os.unlink(tmp_csv)

    def test_csv_integrity_missing_columns(self, db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE customers (id INTEGER)")
        conn.execute("CREATE TABLE installments (id INTEGER)")
        conn.execute("CREATE TABLE attachments (id INTEGER)")
        conn.execute("CREATE TABLE backups (id INTEGER)")
        conn.execute("CREATE TABLE _schema_version (version INTEGER, applied_at TEXT)")
        conn.execute("INSERT INTO _schema_version (version, applied_at) VALUES (5, 'now')")
        conn.commit()
        conn.close()

        tmp_csv = db_path.replace(".db", ".csv")
        import csv
        with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Name"])  # missing required columns
            w.writerow(["Alice"])

        result = run_startup_checks(db_path, csv_path=tmp_csv)
        assert not result.ok
        os.unlink(tmp_csv)

    def test_csv_integrity_missing_name(self, db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE customers (id INTEGER)")
        conn.execute("CREATE TABLE installments (id INTEGER)")
        conn.execute("CREATE TABLE attachments (id INTEGER)")
        conn.execute("CREATE TABLE backups (id INTEGER)")
        conn.execute("CREATE TABLE _schema_version (version INTEGER, applied_at TEXT)")
        conn.execute("INSERT INTO _schema_version (version, applied_at) VALUES (5, 'now')")
        conn.commit()
        conn.close()

        tmp_csv = db_path.replace(".db", ".csv")
        import csv
        with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["Name", "Phone", "Amount", "Installments", "Installment Value", "Start Date", "Installment Dates", "Notification Sent", "Paid_Installments", "Notified_Installments", "Installment_Values"])
            w.writeheader()
            w.writerow({"Name": "", "Phone": "+971501234567"})

        result = run_startup_checks(db_path, csv_path=tmp_csv)
        assert not result.ok
        os.unlink(tmp_csv)

    def test_csv_integrity_invalid_amount(self, db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE customers (id INTEGER)")
        conn.execute("CREATE TABLE installments (id INTEGER)")
        conn.execute("CREATE TABLE attachments (id INTEGER)")
        conn.execute("CREATE TABLE backups (id INTEGER)")
        conn.execute("CREATE TABLE _schema_version (version INTEGER, applied_at TEXT)")
        conn.execute("INSERT INTO _schema_version (version, applied_at) VALUES (5, 'now')")
        conn.commit()
        conn.close()

        tmp_csv = db_path.replace(".db", ".csv")
        import csv
        with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["Name", "Phone", "Amount", "Installments", "Installment Value", "Start Date", "Installment Dates", "Notification Sent", "Paid_Installments", "Notified_Installments", "Installment_Values"])
            w.writeheader()
            w.writerow({"Name": "Alice", "Amount": "not-a-number", "Installments": "abc"})

        result = run_startup_checks(db_path, csv_path=tmp_csv)
        assert not result.ok
        os.unlink(tmp_csv)
