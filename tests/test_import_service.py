import os
import tempfile

import pytest

from app.services.import_service import ImportService, ImportResult


class TestImportResult:
    def test_total(self):
        r = ImportResult()
        assert r.total == 0
        r.success_count = 3
        r.error_count = 2
        assert r.total == 5


def write_csv(path, rows, headers=None):
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        if headers or rows:
            if not headers and rows:
                headers = list(rows[0].keys())
            writer = csv.DictWriter(f, fieldnames=headers)
            if headers:
                writer.writeheader()
            for row in rows:
                writer.writerow(row)


class TestImportCsv:
    @pytest.fixture
    def csv_path(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
        tmp.close()
        yield tmp.name
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    def test_import_valid(self, csv_path):
        write_csv(csv_path, [
            {"Name": "Alice", "Phone": "+971501234567", "Amount": "3000", "Installments": "3", "Start Date": "2026-01-01"},
            {"Name": "Bob", "Phone": "+971509876543", "Amount": "2000", "Installments": "2", "Start Date": "2026-02-01"},
        ])
        result = ImportService.import_csv(csv_path)
        assert result.success_count == 2
        assert result.error_count == 0
        assert len(result.records) == 2

    def test_import_missing_columns(self, csv_path):
        write_csv(csv_path, [
            {"Name": "Alice", "Phone": "+971501234567"},
        ])
        result = ImportService.import_csv(csv_path)
        assert result.success_count == 0
        assert len(result.errors) > 0
        assert "Missing columns" in result.errors[0]

    def test_import_invalid_data(self, csv_path):
        write_csv(csv_path, [
            {"Name": "", "Phone": "", "Amount": "abc", "Installments": "0", "Start Date": ""},
        ])
        result = ImportService.import_csv(csv_path)
        assert result.success_count == 0
        assert result.error_count >= 1

    def test_import_empty_file(self, csv_path):
        write_csv(csv_path, [], headers=["Name", "Phone", "Amount", "Installments", "Start Date"])
        result = ImportService.import_csv(csv_path)
        assert result.success_count == 0
        assert result.error_count == 0

    def test_import_file_not_found(self):
        result = ImportService.import_csv("/nonexistent/path.csv")
        assert result.success_count == 0
        assert len(result.errors) > 0

    def test_import_computes_installment_value(self, csv_path):
        write_csv(csv_path, [
            {"Name": "Alice", "Phone": "+971501234567", "Amount": "3000", "Installments": "3", "Start Date": "2026-01-01"},
        ])
        result = ImportService.import_csv(csv_path)
        assert result.records[0]["Installment Value"] == 1000.0

    def test_import_parses_notification_sent(self, csv_path):
        write_csv(csv_path, [
            {"Name": "Alice", "Phone": "+971501234567", "Amount": "3000", "Installments": "3", "Start Date": "2026-01-01", "Notification Sent": "True"},
        ])
        result = ImportService.import_csv(csv_path)
        assert result.records[0]["Notification Sent"] == True

    def test_import_notification_sent_false(self, csv_path):
        write_csv(csv_path, [
            {"Name": "Alice", "Phone": "+971501234567", "Amount": "3000", "Installments": "3", "Start Date": "2026-01-01", "Notification Sent": "false"},
        ])
        result = ImportService.import_csv(csv_path)
        assert result.records[0]["Notification Sent"] == False

    def test_import_preserves_tracking_fields(self, csv_path):
        write_csv(csv_path, [
            {"Name": "Alice", "Phone": "+971501234567", "Amount": "3000", "Installments": "3", "Start Date": "2026-01-01",
             "Paid_Installments": '["2026-01-01"]', "Notified_Installments": "[]", "Installment_Values": '{"2026-01-01": 1000.0}'},
        ])
        result = ImportService.import_csv(csv_path)
        record = result.records[0]
        assert "2026-01-01" in record["Paid_Installments"]
        assert "2026-01-01" in record["Installment_Values"]


class TestDetectDuplicates:
    def test_no_duplicates(self):
        class FakeRepo:
            @staticmethod
            def read_data():
                return [
                    {"Name": "Alice", "Phone": "+971501234567"},
                ]
        records = [
            {"Name": "Bob", "Phone": "+971509876543"},
        ]
        warnings = ImportService.detect_duplicates(FakeRepo(), records)
        assert warnings == []

    def test_duplicate_name(self):
        class FakeRepo:
            @staticmethod
            def read_data():
                return [
                    {"Name": "Alice", "Phone": "+971501234567"},
                ]
        records = [
            {"Name": "Alice", "Phone": "+971509876543"},
        ]
        warnings = ImportService.detect_duplicates(FakeRepo(), records)
        assert any("Duplicate name" in w for w in warnings)

    def test_duplicate_phone(self):
        class FakeRepo:
            @staticmethod
            def read_data():
                return [
                    {"Name": "Alice", "Phone": "+971501234567"},
                ]
        records = [
            {"Name": "Bob", "Phone": "+971501234567"},
        ]
        warnings = ImportService.detect_duplicates(FakeRepo(), records)
        assert any("Duplicate phone" in w for w in warnings)

    def test_empty_phone_no_warning(self):
        class FakeRepo:
            @staticmethod
            def read_data():
                return [
                    {"Name": "Alice", "Phone": ""},
                ]
        records = [
            {"Name": "Bob", "Phone": ""},
        ]
        warnings = ImportService.detect_duplicates(FakeRepo(), records)
        assert all("phone" not in w.lower() for w in warnings)
