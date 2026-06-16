import csv
import logging
import os
import re
import shutil
from datetime import datetime
from typing import Dict, List, Optional


class CSVRepository:
    """Handles low-level CSV persistence and backup operations."""
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
        self._cache: List[Dict] = []
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration = 60
        self._ensure_files_exist()

    def _is_cache_valid(self) -> bool:
        if not self._cache or not self._cache_timestamp:
            return False
        return (datetime.now() - self._cache_timestamp).seconds < self._cache_duration

    def _update_cache(self, data: List[Dict]):
        self._cache = data
        self._cache_timestamp = datetime.now()

    def read_data(self) -> List[Dict]:
        try:
            if self._is_cache_valid():
                return self._cache.copy()

            data: List[Dict] = []
            with open(self.csv_file, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    cleaned_row = self._clean_row_data(row)
                    if "Notified_Installments" not in cleaned_row:
                        cleaned_row["Notified_Installments"] = "[]"
                    data.append(cleaned_row)

            self._update_cache(data)
            return data
        except FileNotFoundError:
            logging.error(f"CSV file not found: {self.csv_file}")
            self._create_empty_csv()
            return []
        except Exception as e:
            logging.error(f"Error reading CSV file: {str(e)}")
            return []

    def _clean_row_data(self, row: Dict) -> Dict:
        cleaned_row = row.copy()
        if "Phone" in cleaned_row:
            cleaned_row["Phone"] = (
                f"+{cleaned_row['Phone']}"
                if not cleaned_row["Phone"].startswith("+")
                else cleaned_row["Phone"]
            )

        try:
            cleaned_row["Amount"] = float(cleaned_row.get("Amount", 0))
            cleaned_row["Installment Value"] = float(cleaned_row.get("Installment Value", 0))
            cleaned_row["Installments"] = int(cleaned_row.get("Installments", 0))
        except (ValueError, TypeError):
            logging.warning(f"Invalid numeric values in row: {row}")

        cleaned_row["Notification Sent"] = str(cleaned_row.get("Notification Sent", "")).lower() == "true"

        if "Paid_Installments" not in cleaned_row:
            cleaned_row["Paid_Installments"] = "[]"
        if "Notified_Installments" not in cleaned_row:
            cleaned_row["Notified_Installments"] = "[]"

        return cleaned_row

    def save_data(self, data: List[Dict]) -> bool:
        try:
            validated_data: List[Dict] = []
            for row in data:
                if self._validate_row(row):
                    validated_data.append(row)
                else:
                    logging.warning(f"Invalid row data skipped: {row}")

            self.create_backup()
            with open(self.csv_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.columns)
                writer.writeheader()
                writer.writerows(validated_data)

            self._update_cache(validated_data)
            return True
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            return False

    def _validate_row(self, row: Dict) -> bool:
        required_fields = ["Name", "Phone", "Amount", "Installments"]
        if not all(field in row for field in required_fields):
            return False

        try:
            float(row["Amount"])
            float(row["Installment Value"])
            int(row["Installments"])
        except (ValueError, TypeError):
            return False

        phone_pattern = r"^\+?\d{10,15}$"
        if not re.match(phone_pattern, str(row["Phone"])):
            return False

        if "Notification Sent" not in row:
            row["Notification Sent"] = False
        if "Paid_Installments" not in row:
            row["Paid_Installments"] = "[]"
        if "Notified_Installments" not in row:
            row["Notified_Installments"] = "[]"

        return True

    def _ensure_files_exist(self):
        try:
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
            if not os.path.exists(self.csv_file):
                self._create_empty_csv()
        except Exception as e:
            logging.error(f"Error ensuring files exist: {str(e)}")
            raise

    def _create_empty_csv(self):
        try:
            with open(self.csv_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(self.columns)
        except Exception as e:
            logging.error(f"Error creating empty CSV: {str(e)}")
            raise

    def append_record(self, customer_data: Dict) -> bool:
        try:
            missing_fields = [field for field in self.columns if field not in customer_data]
            if missing_fields:
                logging.error(f"Missing required fields: {missing_fields}")
                return False

            if not self.create_backup():
                logging.error("Failed to create backup before appending record")
                return False

            file_exists = os.path.exists(self.csv_file) and os.path.getsize(self.csv_file) > 0
            with open(self.csv_file, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.columns)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(customer_data)

            self._cache = []
            self._cache_timestamp = None
            return True
        except PermissionError:
            logging.error("Permission denied while writing to CSV file")
            raise
        except Exception as e:
            logging.error(f"Error appending record: {str(e)}")
            raise

    def create_backup(self) -> Optional[str]:
        try:
            if not os.path.exists(self.csv_file):
                logging.error("No data file to backup")
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = os.path.join(self.backup_folder, f"backup_{timestamp}.csv")
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
            shutil.copy2(self.csv_file, backup_filename)
            logging.info(f"Backup created: {backup_filename}")
            return backup_filename
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            return None

    def restore_backup(self, backup_file: str) -> bool:
        try:
            backup_path = os.path.join(self.backup_folder, backup_file)
            if not os.path.exists(backup_path):
                logging.error(f"Backup file not found: {backup_path}")
                return False

            self.create_backup()
            shutil.copy2(backup_path, self.csv_file)
            self._cache = []
            self._cache_timestamp = None
            return True
        except Exception as e:
            logging.error(f"Error restoring backup: {str(e)}")
            return False

    def get_backup_files(self) -> List[str]:
        try:
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
            return sorted(
                [f for f in os.listdir(self.backup_folder) if f.endswith(".csv")],
                reverse=True,
            )
        except Exception as e:
            logging.error(f"Error getting backup files: {str(e)}")
            return []
