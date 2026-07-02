import csv
import gzip
import json
import os
import shutil
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from app.database.database import DatabaseManager
from app.logging.logger import logger
from app.settings import settings
from app.utils.serialization import dict_factory, dump_json, load_json_dict, load_json_list

BACKUP_MAX_COUNT_DEFAULT = 50


class BackupError(Exception):
    pass


class RepositoryError(Exception):
    pass


class SQLiteRepository:
    """SQLite-backed repository exposing CSV-compatible dict interface."""
    def __init__(self, csv_file: str, backup_folder: str):
        self.csv_file = csv_file
        self.backup_folder = backup_folder
        self.columns = [
            "Name",
            "Phone",
            "Amount",
            "Installments",
            "Installment Value",
            "Start Date",
            "Installment Dates",
            "Notification Sent",
            "Paid_Installments",
            "Notified_Installments",
            "Installment_Values",
        ]
        db_dir = os.path.dirname(csv_file) or "."
        db_path = os.path.join(db_dir, "installment_tracker.db")
        self._db = DatabaseManager(db_path)
        self._db.initialize()
        self._ensure_backup_folder()

    def _ensure_backup_folder(self):
        try:
            os.makedirs(self.backup_folder, exist_ok=True)
        except OSError as e:
            logger.error(f"Error ensuring backup folder: {e}", component="backup")

    def _log(self, level: str, message: str, **extra):
        getattr(logger, level)(message, component="repository", **extra)

    def read_data(self) -> List[Dict]:
        try:
            conn = self._db.connect()
        except sqlite3.Error as e:
            self._log("error", f"Database error connecting: {e}")
            return []
        original_rf = conn.row_factory
        conn.row_factory = dict_factory
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM customers ORDER BY id")
            customer_rows = cursor.fetchall()

            result = []
            for c in customer_rows:
                cursor.execute(
                    "SELECT * FROM installments WHERE customer_id = ? ORDER BY installment_number",
                    (c["id"],),
                )
                inst_rows = cursor.fetchall()

                installment_dates = []
                paid_dates = []
                notified_dates = []
                installment_values = {}

                for inst in inst_rows:
                    due_date = inst["due_date"]
                    installment_dates.append(due_date)
                    installment_values[due_date] = inst["amount"]
                    if inst["status"] == "paid":
                        paid_dates.append(due_date)
                    if inst["notified"]:
                        notified_dates.append(due_date)

                inst_count = c["installment_count"] or len(installment_dates)
                total_amount = c["total_amount"] or 0
                default_value = round(total_amount / inst_count, 2) if inst_count > 0 else 0

                row = {
                    "Name": c["customer_name"],
                    "Phone": c["phone_number"],
                    "Amount": total_amount,
                    "Installments": inst_count,
                    "Installment Value": default_value,
                    "Start Date": c["start_date"],
                    "Installment Dates": ";".join(installment_dates),
                    "Notification Sent": len(notified_dates) > 0,
                    "Paid_Installments": dump_json(paid_dates),
                    "Notified_Installments": dump_json(notified_dates),
                    "Installment_Values": dump_json(installment_values),
                }
                result.append(row)

            self._clean_phone_numbers(result)
            return result
        except sqlite3.Error as e:
            self._log("error", f"Database error reading data: {e}")
            return []
        except (ValueError, TypeError) as e:
            self._log("error", f"Data conversion error reading data: {e}")
            return []
        finally:
            conn.row_factory = original_rf

    def _clean_phone_numbers(self, data: List[Dict]):
        for row in data:
            phone = row.get("Phone", "")
            if phone and not phone.startswith("+"):
                row["Phone"] = "+" + phone

    def save_data(self, data: List[Dict]) -> bool:
        try:
            with self._db.transaction() as cursor:
                cursor.execute("DELETE FROM installments")
                cursor.execute("DELETE FROM customers")
                self._insert_customers(cursor, data)
            return True
        except (sqlite3.Error, ValueError, TypeError) as e:
            self._log("error", f"Error saving data: {e}")
            return False

    def _insert_customers(self, cursor, data: List[Dict]):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row in data:
            dates_str = row.get("Installment Dates", "")
            dates = [d for d in dates_str.split(";") if d]
            inst_count = row.get("Installments", len(dates))
            total_amount = float(row.get("Amount", 0))

            cursor.execute(
                """INSERT INTO customers
                   (customer_name, phone_number, total_amount,
                    installment_count, start_date, notes,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row.get("Name", ""),
                    self._normalize_phone(row.get("Phone", "")),
                    total_amount,
                    int(inst_count),
                    row.get("Start Date", ""),
                    "",
                    now,
                    now,
                ),
            )
            customer_id = cursor.lastrowid

            inst_values = load_json_dict(row.get("Installment_Values", "{}"))
            paid = load_json_list(row.get("Paid_Installments", "[]"))
            notified = load_json_list(row.get("Notified_Installments", "[]"))
            default_value = float(row.get("Installment Value", 0))

            for i, date in enumerate(dates):
                amount = float(inst_values.get(date, default_value))
                is_paid = date in paid
                is_notified = date in notified
                paid_date = date if is_paid else None

                cursor.execute(
                    """INSERT INTO installments
                       (customer_id, installment_number, due_date,
                        amount, status, notified, paid_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        customer_id,
                        i + 1,
                        date,
                        amount,
                        "paid" if is_paid else "pending",
                        1 if is_notified else 0,
                        paid_date,
                    ),
                )

    def append_record(self, customer_data: Dict) -> bool:
        try:
            data = self.read_data()
            data.append(customer_data)
            with self._db.transaction() as cursor:
                cursor.execute("DELETE FROM installments")
                cursor.execute("DELETE FROM customers")
                self._insert_customers(cursor, data)
            return True
        except (sqlite3.Error, ValueError, TypeError) as e:
            self._log("error", f"Error appending record: {e}")
            return False

    def create_backup(self) -> Optional[str]:
        tmp_files = []
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            csv_path = os.path.join(self.backup_folder, f"{backup_name}.csv")
            gz_path = os.path.join(self.backup_folder, f"{backup_name}.csv.gz")

            data = self.read_data()

            csv_tmp = csv_path + ".tmp"
            with open(csv_tmp, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)
                writer.writeheader()
                for row in data:
                    out = {}
                    for col in self.columns:
                        val = row.get(col, "")
                        if isinstance(val, bool):
                            val = str(val)
                        out[col] = val
                    writer.writerow(out)
            tmp_files.append(csv_tmp)

            if settings.get("backup_compress", True):
                gz_tmp = gz_path + ".tmp"
                with open(csv_tmp, "rb") as f_in:
                    with gzip.open(gz_tmp, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                tmp_files.append(gz_tmp)
                os.replace(csv_tmp, csv_path)
                os.replace(gz_tmp, gz_path)
                os.unlink(csv_path)
                final_path = gz_path
            else:
                os.replace(csv_tmp, csv_path)
                final_path = csv_path

            metadata = {
                "timestamp": timestamp,
                "file": os.path.basename(final_path),
                "size": os.path.getsize(final_path),
                "records": len(data),
            }
            meta_path = os.path.join(self.backup_folder, f"{backup_name}.meta.json")
            meta_tmp = meta_path + ".tmp"
            with open(meta_tmp, "w", encoding="utf-8") as f:
                json.dump(metadata, f)
            os.replace(meta_tmp, meta_path)

            self._rotate_backups()
            logger.backup(f"Backup created: {os.path.basename(final_path)}", records=len(data), size=metadata["size"])
            return final_path
        except (OSError, csv.Error) as e:
            self._log("error", f"Error creating backup: {e}")
            for p in tmp_files:
                try:
                    os.unlink(p)
                except OSError:
                    pass
            return None

    def _rotate_backups(self):
        max_count = settings.get("backup_max_count", BACKUP_MAX_COUNT_DEFAULT)
        backups = self.get_backup_files()
        if len(backups) <= max_count:
            return
        to_remove = backups[max_count:]
        for name in to_remove:
            path = os.path.join(self.backup_folder, name)
            try:
                os.unlink(path)
            except OSError:
                pass
            base = name.replace(".csv.gz", "").replace(".csv", "")
            meta = os.path.join(self.backup_folder, f"{base}.meta.json")
            if os.path.exists(meta):
                try:
                    os.unlink(meta)
                except OSError:
                    pass
        self._log("info", f"Rotated {len(to_remove)} old backups, keeping {max_count}")

    def restore_backup(self, backup_file: str) -> bool:
        try:
            backup_path = os.path.join(self.backup_folder, backup_file)
            if not os.path.exists(backup_path):
                self._log("error", f"Backup file not found: {backup_path}")
                return False

            if backup_file.endswith(".gz"):
                csv_path = backup_path[:-3]
                if not os.path.exists(csv_path):
                    with gzip.open(backup_path, "rb") as f_in:
                        with open(csv_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    extracted = True
                else:
                    extracted = False
                read_path = csv_path
            else:
                extracted = False
                read_path = backup_path

            try:
                with open(read_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    data = []
                    for row in reader:
                        cleaned = dict(row)
                        try:
                            cleaned["Amount"] = float(cleaned.get("Amount", 0))
                            cleaned["Installment Value"] = float(cleaned.get("Installment Value", 0))
                            cleaned["Installments"] = int(cleaned.get("Installments", 0))
                        except (ValueError, TypeError):
                            pass
                        cleaned["Notification Sent"] = str(cleaned.get("Notification Sent", "")).lower() == "true"
                        for k in ("Paid_Installments", "Notified_Installments", "Installment_Values"):
                            if k not in cleaned:
                                cleaned[k] = "[]" if k != "Installment_Values" else "{}"
                        data.append(cleaned)

                if not self.save_data(data):
                    return False

                shutil.copy2(read_path, self.csv_file)
                logger.backup(f"Backup restored: {backup_file}", records=len(data))
                return True
            finally:
                if extracted:
                    try:
                        os.unlink(read_path)
                    except OSError:
                        pass
        except (OSError, csv.Error, sqlite3.Error) as e:
            self._log("error", f"Error restoring backup: {e}")
            return False

    def get_backup_files(self) -> List[str]:
        try:
            if not os.path.isdir(self.backup_folder):
                return []
            files = []
            for f in os.listdir(self.backup_folder):
                if f.endswith(".csv") or f.endswith(".csv.gz"):
                    files.append(f)
            return sorted(files, reverse=True)
        except OSError as e:
            self._log("error", f"Error getting backup files: {e}")
            return []

    def verify_backup(self, backup_file: str) -> bool:
        """Verify a backup file is valid by reading and parsing it."""
        try:
            backup_path = os.path.join(self.backup_folder, backup_file)
            if not os.path.exists(backup_path):
                return False
            if backup_file.endswith(".gz"):
                opener = gzip.open(backup_path, "rt", encoding="utf-8")
            else:
                opener = open(backup_path, "r", encoding="utf-8")
            with opener as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            return len(rows) > 0
        except (OSError, csv.Error):
            return False

    def get_customer_id_by_name(self, name: str) -> Optional[int]:
        try:
            conn = self._db.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM customers WHERE customer_name=?", (name,))
            row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error:
            return None

    def get_customer_by_id(self, customer_id: int) -> Optional[dict]:
        try:
            conn = self._db.connect()
            original_rf = conn.row_factory
            conn.row_factory = dict_factory
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM customers WHERE id=?", (customer_id,))
                return cursor.fetchone()
            finally:
                conn.row_factory = original_rf
        except sqlite3.Error:
            return None

    def _normalize_phone(self, phone: str) -> str:
        phone = phone.strip()
        if phone and not phone.startswith("+"):
            phone = "+" + phone
        return phone



