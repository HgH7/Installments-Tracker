import csv
import os
import sqlite3
from typing import List, Optional

from app.core.logging.logger import logger


class RecoveryError(Exception):
    pass


class RecoveryResult:
    def __init__(self):
        self.ok = True
        self.issues: List[str] = []
        self.repaired: List[str] = []

    def add_issue(self, issue: str):
        self.issues.append(issue)
        self.ok = False

    def add_repair(self, repair: str):
        self.repaired.append(repair)

    def __bool__(self):
        return self.ok


def check_database_integrity(db_path: str) -> RecoveryResult:
    result = RecoveryResult()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()
        if integrity and integrity[0] != "ok":
            result.add_issue(f"Integrity check failed: {integrity[0]}")
            logger.warning(f"Database integrity issue: {integrity[0]}", component="recovery")
        else:
            logger.info("Database integrity check passed", component="recovery")
    except sqlite3.Error as e:
        result.add_issue(f"Cannot open database: {e}")
        logger.error(f"Cannot open database for integrity check: {e}", component="recovery")
    finally:
        if conn:
            conn.close()
    return result


def check_required_tables(db_path: str, required: Optional[List[str]] = None) -> RecoveryResult:
    if required is None:
        required = ["customers", "installments", "attachments", "backups", "_schema_version"]
    result = RecoveryResult()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing = {row[0] for row in cursor.fetchall()}
        for table in required:
            if table not in existing:
                result.add_issue(f"Missing table: {table}")
    except sqlite3.Error as e:
        result.add_issue(f"Cannot check tables: {e}")
    finally:
        if conn:
            conn.close()
    return result


def check_migration_state(db_path: str) -> RecoveryResult:
    result = RecoveryResult()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(version) FROM _schema_version")
        row = cursor.fetchone()
        version = row[0] if row and row[0] else 0
        if version < 2:
            result.add_issue(f"Migration incomplete: schema version {version} < 2")
    except sqlite3.Error as e:
        result.add_issue(f"Cannot check migration state: {e}")
    finally:
        if conn:
            conn.close()
    return result


CSV_REQUIRED_COLUMNS = [
    "Name", "Phone", "Amount", "Installments",
    "Installment Value", "Start Date", "Installment Dates",
    "Notification Sent", "Paid_Installments",
    "Notified_Installments", "Installment_Values",
]


def check_csv_integrity(csv_path: str) -> RecoveryResult:
    """Validate CSV file structure and row integrity."""
    result = RecoveryResult()
    if not os.path.exists(csv_path):
        logger.info("CSV file does not exist yet, skipping integrity check", component="recovery")
        return result
    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            missing = [c for c in CSV_REQUIRED_COLUMNS if c not in headers]
            if missing:
                result.add_issue(f"CSV missing required columns: {missing}")
            row_count = 0
            for i, row in enumerate(reader, start=1):
                row_count += 1
                if not row.get("Name", "").strip():
                    result.add_issue(f"Row {i}: missing customer name")
                try:
                    if row.get("Amount"):
                        float(row["Amount"])
                except (ValueError, TypeError):
                    result.add_issue(f"Row {i}: invalid Amount value: {row.get('Amount')}")
                try:
                    if row.get("Installments"):
                        int(row["Installments"])
                except (ValueError, TypeError):
                    result.add_issue(f"Row {i}: invalid Installments value: {row.get('Installments')}")
            if row_count == 0:
                result.add_issue("CSV file is empty (no data rows)")
        if result.ok:
            logger.info(f"CSV integrity check passed: {row_count} rows", component="recovery")
        else:
            logger.warning(f"CSV integrity check found {len(result.issues)} issue(s)", component="recovery")
    except (OSError, csv.Error) as e:
        result.add_issue(f"Cannot read CSV file: {e}")
    return result


def run_startup_checks(db_path: str, csv_path: Optional[str] = None) -> RecoveryResult:
    logger.info("Running startup recovery checks", component="recovery")
    result = RecoveryResult()
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        result.add_repair(f"Created data directory: {db_dir}")
    if not os.path.exists(db_path):
        logger.info("Database does not exist yet, will be created on first use", component="recovery")
        result.add_repair("New database will be created")
        return result

    integrity = check_database_integrity(db_path)
    if not integrity:
        result.add_issue("Database integrity issues found")
    tables = check_required_tables(db_path)
    if not tables:
        result.add_issue("Required tables missing")
    migration = check_migration_state(db_path)
    if not migration:
        result.add_issue("Migration incomplete")

    if csv_path:
        csv_result = check_csv_integrity(csv_path)
        if not csv_result:
            result.issues.extend(csv_result.issues)
            result.repaired.extend(csv_result.repaired)
            result.ok = False

    if not result.ok:
        logger.warning(f"Startup checks found {len(result.issues)} issue(s)", component="recovery")
    else:
        logger.info("All startup checks passed", component="recovery")
    return result
