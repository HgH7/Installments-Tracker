import os
import shutil
import tempfile

import pytest

from app.repositories.sqlite_repository import SQLiteRepository
from app.services.customer_service import CustomerService


SAMPLE = {
    "Name": "Alice",
    "Phone": "+971501234567",
    "Amount": 3000.0,
    "Installments": 3,
    "Installment Value": 1000.0,
    "Start Date": "2026-01-01",
    "Installment Dates": "2026-01-01;2026-02-01;2026-03-01",
    "Notification Sent": False,
    "Paid_Installments": "[]",
    "Notified_Installments": "[]",
    "Installment_Values": "{}",
}

SAMPLE2 = {
    "Name": "Bob",
    "Phone": "+971509876543",
    "Amount": 2000.0,
    "Installments": 2,
    "Installment Value": 1000.0,
    "Start Date": "2026-02-01",
    "Installment Dates": "2026-02-01;2026-03-01",
    "Notification Sent": False,
    "Paid_Installments": "[]",
    "Notified_Installments": "[]",
    "Installment_Values": "{}",
}


@pytest.fixture
def service():
    tmpdir = tempfile.mkdtemp(prefix="cust_test_")
    backup_dir = os.path.join(tmpdir, "backups")
    os.makedirs(backup_dir)
    csv_path = os.path.join(tmpdir, "customers.csv")
    repo = SQLiteRepository(csv_path, backup_dir)
    svc = CustomerService(repo)
    yield svc
    shutil.rmtree(tmpdir)


class TestAppendCustomer:
    def test_append_success(self, service):
        assert service.append_customer(SAMPLE)
        customers = service.get_all_customers()
        assert len(customers) == 1
        assert customers[0]["Name"] == "Alice"

    def test_append_multiple(self, service):
        assert service.append_customer(SAMPLE)
        assert service.append_customer(SAMPLE2)
        assert len(service.get_all_customers()) == 2

    def test_append_missing_columns(self, service, monkeypatch):
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *a, **kw: None)
        incomplete = {"Name": "NoPhone"}
        assert not service.append_customer(incomplete)


class TestGetCustomers:
    def test_get_all_empty(self, service):
        assert service.get_all_customers() == []

    def test_get_all_returns_all(self, service):
        service.append_customer(SAMPLE)
        service.append_customer(SAMPLE2)
        assert len(service.get_all_customers()) == 2

    def test_get_by_name_found(self, service):
        service.append_customer(SAMPLE)
        customer = service.get_customer_by_name("Alice")
        assert customer["Name"] == "Alice"
        assert customer["Phone"] == "+971501234567"

    def test_get_by_name_not_found(self, service):
        assert service.get_customer_by_name("Nobody") == {}

    def test_get_by_name_empty_db(self, service):
        assert service.get_customer_by_name("Alice") == {}


class TestUpdateCustomer:
    def test_update_name(self, service):
        service.append_customer(SAMPLE)
        assert service.update_customer("Alice", {"Name": "Alicia"})
        assert service.get_customer_by_name("Alicia")["Name"] == "Alicia"

    def test_update_phone(self, service):
        service.append_customer(SAMPLE)
        assert service.update_customer("Alice", {"Phone": "+971500000000"})
        assert service.get_customer_by_name("Alice")["Phone"] == "+971500000000"

    def test_update_not_found(self, service):
        assert not service.update_customer("Nobody", {"Name": "Someone"})

    def test_update_preserves_tracking_fields(self, service):
        paid = '["2026-01-01"]'
        notified = '["2026-01-01"]'
        cust = dict(SAMPLE)
        cust["Paid_Installments"] = paid
        cust["Notified_Installments"] = notified
        service.append_customer(cust)
        service.update_customer("Alice", {"Name": "Alicia", "Phone": "+971500000000"})
        updated = service.get_customer_by_name("Alicia")
        assert updated["Paid_Installments"] == paid
        assert updated["Notified_Installments"] == notified

    def test_update_preserves_notification_sent(self, service):
        cust = dict(SAMPLE)
        cust["Notification Sent"] = True
        cust["Notified_Installments"] = '["2026-01-01"]'
        service.append_customer(cust)
        service.update_customer("Alice", {"Phone": "+971500000000"})
        updated = service.get_customer_by_name("Alice")
        assert updated["Notification Sent"] == True


class TestDeleteCustomer:
    def test_delete_existing(self, service):
        service.append_customer(SAMPLE)
        assert service.delete_customer("Alice")
        assert service.get_all_customers() == []

    def test_delete_not_found(self, service):
        assert not service.delete_customer("Nobody")

    def test_delete_from_empty(self, service):
        assert not service.delete_customer("Alice")

    def test_delete_only_matching(self, service):
        service.append_customer(SAMPLE)
        service.append_customer(SAMPLE2)
        assert service.delete_customer("Alice")
        remaining = service.get_all_customers()
        assert len(remaining) == 1
        assert remaining[0]["Name"] == "Bob"


class TestBuildCustomerRecord:
    def test_calendar_month_default(self, service):
        record = service.build_customer_record("Alice", "+971501234567", "3000", "3", "2026-01-15")
        assert record["Name"] == "Alice"
        assert record["Amount"] == 3000.0
        assert record["Installments"] == 3
        assert record["Installment Value"] == 1000.0
        assert record["Start Date"] == "2026-01-15"
        dates = record["Installment Dates"].split(";")
        assert len(dates) == 3
        assert dates[0] == "2026-01-15"
        assert dates[1] == "2026-02-15"
        assert dates[2] == "2026-03-15"

    def test_thirty_day_strategy(self, service):
        record = service.build_customer_record("Bob", "+971501234567", "2000", "2", "2026-01-15", date_strategy="thirty_day")
        dates = record["Installment Dates"].split(";")
        assert len(dates) == 2

    def test_without_tracking_fields(self, service):
        record = service.build_customer_record("Alice", "+971501234567", "1000", "1", "2026-01-01", include_tracking_fields=False)
        assert "Notification Sent" not in record
        assert "Paid_Installments" not in record

    def test_with_tracking_fields(self, service):
        record = service.build_customer_record("Alice", "+971501234567", "1000", "1", "2026-01-01", include_tracking_fields=True)
        assert record["Notification Sent"] is False
        assert record["Paid_Installments"] == "[]"

    def test_installment_value_rounding(self, service):
        record = service.build_customer_record("Alice", "+971501234567", "100", "3", "2026-01-01")
        assert record["Installment Value"] == 33.33


class TestMarkInstallment:
    def test_mark_as_paid(self, service):
        service.append_customer(SAMPLE)
        assert service.mark_installment_as_paid("Alice", "2026-01-01")
        customer = service.get_customer_by_name("Alice")
        assert "2026-01-01" in customer["Paid_Installments"]

    def test_mark_already_paid(self, service):
        service.append_customer(SAMPLE)
        service.mark_installment_as_paid("Alice", "2026-01-01")
        assert service.mark_installment_as_paid("Alice", "2026-01-01")

    def test_mark_customer_not_found(self, service):
        assert not service.mark_installment_as_paid("Nobody", "2026-01-01")

    def test_mark_multiple(self, service):
        service.append_customer(SAMPLE)
        service.mark_installment_as_paid("Alice", "2026-01-01")
        service.mark_installment_as_paid("Alice", "2026-02-01")
        customer = service.get_customer_by_name("Alice")
        paid = __import__("app.utils.serialization", fromlist=["load_json_list"]).load_json_list(customer["Paid_Installments"])
        assert len(paid) == 2


class TestUnmarkInstallment:
    def test_unmark_paid(self, service):
        service.append_customer(SAMPLE)
        service.mark_installment_as_paid("Alice", "2026-01-01")
        assert service.unmark_installment_as_paid("Alice", "2026-01-01")
        customer = service.get_customer_by_name("Alice")
        assert "2026-01-01" not in customer["Paid_Installments"]

    def test_unmark_not_paid(self, service):
        service.append_customer(SAMPLE)
        assert service.unmark_installment_as_paid("Alice", "2026-01-01")

    def test_unmark_customer_not_found(self, service):
        assert not service.unmark_installment_as_paid("Nobody", "2026-01-01")


class TestUpdateInstallment:
    def test_update_date(self, service):
        service.append_customer(SAMPLE)
        assert service.update_installment("Alice", "2026-01-01", "2026-01-15", 1000.0)
        customer = service.get_customer_by_name("Alice")
        assert "2026-01-15" in customer["Installment Dates"]
        assert "2026-01-01" not in customer["Installment Dates"]

    def test_update_value_and_date(self, service):
        service.append_customer(SAMPLE)
        assert service.update_installment("Alice", "2026-01-01", "2026-01-15", 1500.0)
        customer = service.get_customer_by_name("Alice")
        values = __import__("app.utils.serialization", fromlist=["load_json_dict"]).load_json_dict(customer["Installment_Values"])
        assert "2026-01-01" not in values
        assert values["2026-01-15"] == 1500.0

    def test_update_customer_not_found(self, service):
        assert not service.update_installment("Nobody", "2026-01-01", "2026-01-15", 1000.0)

    def test_update_old_date_not_found(self, service):
        service.append_customer(SAMPLE)
        assert not service.update_installment("Alice", "2099-01-01", "2099-01-15", 1000.0)

    def test_update_no_dates(self, service):
        cust = dict(SAMPLE)
        cust["Installment Dates"] = ""
        service.append_customer(cust)
        assert not service.update_installment("Alice", "2026-01-01", "2026-01-15", 1000.0)

    def test_update_with_paid_migration(self, service):
        service.append_customer(SAMPLE)
        service.mark_installment_as_paid("Alice", "2026-01-01")
        service.update_installment("Alice", "2026-01-01", "2026-01-15", 1000.0)
        customer = service.get_customer_by_name("Alice")
        assert "2026-01-15" in customer["Paid_Installments"]
        assert "2026-01-01" not in customer["Paid_Installments"]
