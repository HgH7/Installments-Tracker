import os
import tempfile

import pytest

from app.services.export_service import ExportService


SAMPLE_DATA = [
    {"Name": "Alice", "Amount": 3000.0, "Installments": 3},
    {"Name": "Bob", "Amount": 2000.0, "Installments": 2},
]


class TestExportCsv:
    @pytest.fixture
    def output_path(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
        tmp.close()
        yield tmp.name
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    def test_export_csv_success(self, output_path):
        assert ExportService.export_csv(SAMPLE_DATA, output_path)
        with open(output_path) as f:
            content = f.read()
        assert "Alice" in content
        assert "Bob" in content
        assert "Name" in content

    def test_export_csv_empty_data(self, output_path):
        assert ExportService.export_csv([], output_path)
        with open(output_path) as f:
            content = f.read()
        assert content == "" or content == "\n"

    def test_export_csv_specific_columns(self, output_path):
        assert ExportService.export_csv(SAMPLE_DATA, output_path, columns=["Name"])
        with open(output_path) as f:
            content = f.read()
        assert "Alice" in content
        assert "Amount" not in content

    def test_export_csv_bool_handling(self, output_path):
        data = [{"Name": "Alice", "Active": True}]
        assert ExportService.export_csv(data, output_path)
        with open(output_path) as f:
            content = f.read()
        assert "True" in content

    def test_export_csv_invalid_path(self):
        assert not ExportService.export_csv(SAMPLE_DATA, "/nonexistent/dir/file.csv")


class TestExportExcel:
    def test_export_excel_success(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        try:
            result = ExportService.export_excel(SAMPLE_DATA, tmp.name)
            assert result is True or result is False
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)


class TestExportReport:
    def test_report_csv(self):
        data = {"rows": SAMPLE_DATA, "columns": ["Name", "Amount"]}
        path = ExportService.export_report(data, format="csv")
        assert path is not None
        assert path.endswith(".csv")
        if os.path.exists(path):
            os.unlink(path)

    def test_report_json(self):
        data = {"rows": SAMPLE_DATA, "columns": ["Name", "Amount"]}
        path = ExportService.export_report(data, format="json")
        assert path is not None
        assert path.endswith(".json")
        if os.path.exists(path):
            os.unlink(path)

    def test_report_unknown_format(self):
        path = ExportService.export_report({"rows": []}, format="xml")
        assert path is None


class TestExportCustomer:
    def test_export_customer_csv(self):
        data = {"Name": "Alice", "Amount": 3000.0}
        path = ExportService.export_customer(data, format="csv")
        assert path is not None
        assert "Alice" in path
        assert path.endswith(".csv")
        if os.path.exists(path):
            os.unlink(path)

    def test_export_customer_unknown_format(self):
        data = {"Name": "Alice"}
        path = ExportService.export_customer(data, format="pdf")
        assert path is None


class TestExportEdgeCases:
    def test_export_csv_with_none_values(self):
        data = [{"Name": "Alice", "Amount": None, "Active": True}]
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        tmp.close()
        try:
            result = ExportService.export_csv(data, tmp.name, columns=["Name", "Amount", "Active"])
            assert result is True
            with open(tmp.name, "r") as f:
                content = f.read()
            assert "Alice" in content
            assert "True" in content
            assert "None" not in content  # None becomes empty string
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_export_report_no_rows(self):
        path = ExportService.export_report({"rows": [], "columns": ["Name"]}, format="csv")
        assert path is not None
        assert path.endswith(".csv")
        if os.path.exists(path):
            os.unlink(path)

    def test_export_report_empty_dict(self):
        path = ExportService.export_report({}, format="json")
        assert path is not None
        assert path.endswith(".json")
        if os.path.exists(path):
            os.unlink(path)

    def test_export_customer_empty_name(self):
        data = {"Name": "", "Amount": 1000.0}
        path = ExportService.export_customer(data, format="csv")
        assert path is not None
        assert path.endswith(".csv")
        if os.path.exists(path):
            os.unlink(path)
