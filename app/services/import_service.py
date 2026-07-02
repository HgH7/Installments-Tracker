"""Imports customer records from CSV with validation and duplicate detection."""

import csv
import logging
from typing import Dict, List

from app.core.validation import ValidationService

logger = logging.getLogger(__name__)


class ImportResult:
    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.errors: List[str] = []
        self.records: List[Dict] = []

    @property
    def total(self) -> int:
        return self.success_count + self.error_count


class ImportService:
    @staticmethod
    def import_csv(filepath: str) -> ImportResult:
        result = ImportResult()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                required = {"Name", "Phone", "Amount", "Installments", "Start Date"}
                headers = set(reader.fieldnames or [])
                missing = required - headers
                if missing:
                    result.errors.append(f"Missing columns: {', '.join(missing)}")
                    return result

                for row_num, row in enumerate(reader, start=2):
                    try:
                        name = row.get("Name", "").strip()
                        phone = row.get("Phone", "").strip()
                        amount = row.get("Amount", "").strip()
                        installments = row.get("Installments", "").strip()
                        start_date = row.get("Start Date", "").strip()

                        val = ValidationService.validate_customer(name, phone, amount, installments, start_date)
                        if not val:
                            result.errors.append(f"Row {row_num}: {val.errors[0]}")
                            result.error_count += 1
                            continue

                        dates_str = row.get("Installment Dates", "")
                        paid_raw = row.get("Paid_Installments", "[]")
                        notified_raw = row.get("Notified_Installments", "[]")
                        values_raw = row.get("Installment_Values", "{}")

                        record = {
                            "Name": name,
                            "Phone": phone,
                            "Amount": float(amount),
                            "Installments": int(installments),
                            "Installment Value": round(float(amount) / int(installments), 2) if int(installments) else 0,
                            "Start Date": start_date,
                            "Installment Dates": dates_str,
                            "Notification Sent": str(row.get("Notification Sent", "")).lower() == "true",
                            "Paid_Installments": paid_raw,
                            "Notified_Installments": notified_raw,
                            "Installment_Values": values_raw,
                        }
                        result.records.append(record)
                        result.success_count += 1
                    except (ValueError, TypeError) as e:
                        result.errors.append(f"Row {row_num}: {e}")
                        result.error_count += 1

        except (OSError, csv.Error) as e:
            result.errors.append(f"File error: {e}")
        if result.success_count:
            logger.info(f"CSV import: {result.success_count} records loaded, {result.error_count} errors")
        elif result.error_count:
            logger.warning(f"CSV import failed or no records loaded: {result.success_count} success, {result.error_count} errors")
        return result

    @staticmethod
    def detect_duplicates(repo, records: List[Dict]) -> List[str]:
        existing = repo.read_data()
        existing_names = {c.get("Name", "").strip().lower() for c in existing}
        existing_phones = {c.get("Phone", "").strip() for c in existing}
        warnings = []
        for r in records:
            name = r.get("Name", "").strip().lower()
            phone = r.get("Phone", "").strip()
            if name in existing_names:
                warnings.append(f"Duplicate name: {r.get('Name')}")
            if phone and phone in existing_phones:
                warnings.append(f"Duplicate phone: {phone}")
        return warnings
