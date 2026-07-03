import os
import shutil
import tempfile

import pytest

from app.repositories.sqlite_repository import SQLiteRepository

SAMPLE_CUSTOMER = {
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

SAMPLE_CUSTOMER2 = {
    "Name": "Bob",
    "Phone": "+971509876543",
    "Amount": 2000.0,
    "Installments": 2,
    "Installment Value": 1000.0,
    "Start Date": "2026-02-01",
    "Installment Dates": "2026-02-01;2026-03-01",
    "Notification Sent": True,
    "Paid_Installments": '["2026-02-01"]',
    "Notified_Installments": '["2026-02-01"]',
    "Installment_Values": '{"2026-02-01": 1000.0, "2026-03-01": 1000.0}',
}


@pytest.fixture
def repo():
    tmpdir = tempfile.mkdtemp(prefix="repo_test_")
    backup_dir = os.path.join(tmpdir, "backups")
    os.makedirs(backup_dir)
    csv_path = os.path.join(tmpdir, "customers.csv")
    r = SQLiteRepository(csv_path, backup_dir)
    yield r
    shutil.rmtree(tmpdir)


class TestSQLiteRepository:
    def test_read_empty(self, repo):
        assert repo.read_data() == []

    def test_append_and_read(self, repo):
        assert repo.append_record(SAMPLE_CUSTOMER)
        data = repo.read_data()
        assert len(data) == 1
        assert data[0]["Name"] == "Alice"

    def test_save_and_read(self, repo):
        assert repo.save_data([SAMPLE_CUSTOMER, SAMPLE_CUSTOMER2])
        data = repo.read_data()
        assert len(data) == 2

    def test_save_overwrites(self, repo):
        repo.save_data([SAMPLE_CUSTOMER])
        repo.save_data([SAMPLE_CUSTOMER2])
        data = repo.read_data()
        assert len(data) == 1
        assert data[0]["Name"] == "Bob"

    def test_notification_sent_flag(self, repo):
        repo.save_data([SAMPLE_CUSTOMER2])
        data = repo.read_data()
        assert data[0]["Notification Sent"] == True

    def test_paid_installments(self, repo):
        repo.save_data([SAMPLE_CUSTOMER2])
        data = repo.read_data()
        paid = data[0].get("Paid_Installments", "[]")
        assert "2026-02-01" in paid

    def test_columns_property(self, repo):
        assert len(repo.columns) == 11
        assert "Name" in repo.columns
        assert "Phone" in repo.columns

    def test_append_preserves_existing(self, repo):
        repo.append_record(SAMPLE_CUSTOMER)
        repo.append_record(SAMPLE_CUSTOMER2)
        data = repo.read_data()
        assert len(data) == 2

    def test_phone_normalization(self, repo):
        custom = dict(SAMPLE_CUSTOMER)
        custom["Phone"] = "0501234567"
        repo.append_record(custom)
        data = repo.read_data()
        assert data[0]["Phone"].startswith("+")

    def test_create_backup(self, repo):
        repo.save_data([SAMPLE_CUSTOMER])
        path = repo.create_backup()
        assert path is not None
        assert os.path.exists(path)

    def test_get_backup_files(self, repo):
        repo.save_data([SAMPLE_CUSTOMER])
        repo.create_backup()
        files = repo.get_backup_files()
        assert len(files) >= 1

    def test_restore_backup(self, repo):
        repo.save_data([SAMPLE_CUSTOMER])
        path = repo.create_backup()
        repo.save_data([SAMPLE_CUSTOMER2])
        assert repo.read_data()[0]["Name"] == "Bob"
        repo.restore_backup(os.path.basename(path))
        assert repo.read_data()[0]["Name"] == "Alice"

    def test_verify_backup(self, repo):
        repo.save_data([SAMPLE_CUSTOMER])
        path = repo.create_backup()
        assert repo.verify_backup(os.path.basename(path))

    def test_backup_rotation(self, repo):
        repo.save_data([SAMPLE_CUSTOMER])
        for _ in range(5):
            repo.create_backup()
        from app.core.settings import settings
        settings.set("backup_max_count", 3)
        repo.create_backup()
        files = repo.get_backup_files()
        assert len(files) <= 4  # 3 kept + 1 new

    def test_save_data_empty(self, repo):
        assert repo.save_data([])
        assert repo.read_data() == []

    def test_append_multiple_records(self, repo):
        repo.append_record(SAMPLE_CUSTOMER)
        repo.append_record(SAMPLE_CUSTOMER2)
        data = repo.read_data()
        assert len(data) == 2

    def test_read_data_after_save_returns_correct_fields(self, repo):
        repo.save_data([SAMPLE_CUSTOMER])
        data = repo.read_data()
        row = data[0]
        assert row["Name"] == "Alice"
        assert row["Phone"] == "+971501234567"
        assert row["Amount"] == 3000.0

    def test_columns_match_csv_headers(self, repo):
        assert repo.columns == [
            "Name", "Phone", "Amount", "Installments",
            "Installment Value", "Start Date", "Installment Dates",
            "Notification Sent", "Paid_Installments",
            "Notified_Installments", "Installment_Values",
        ]

    def test_get_customer_id_by_name(self, repo):
        repo.save_data([SAMPLE_CUSTOMER])
        cid = repo.get_customer_id_by_name("Alice")
        assert cid is not None
        assert isinstance(cid, int)

    def test_get_customer_id_by_name_not_found(self, repo):
        assert repo.get_customer_id_by_name("Nobody") is None

    def test_verify_backup_invalid(self, repo):
        assert not repo.verify_backup("nonexistent.csv")

    def test_restore_backup_nonexistent(self, repo):
        assert not repo.restore_backup("nonexistent.csv")

    def test_phone_normalization_empty(self, repo):
        custom = dict(SAMPLE_CUSTOMER)
        custom["Phone"] = ""
        repo.append_record(custom)
        data = repo.read_data()
        assert data[0]["Phone"] == ""

    def test_phone_normalization_already_has_plus(self, repo):
        custom = dict(SAMPLE_CUSTOMER)
        custom["Phone"] = "+971501234567"
        repo.append_record(custom)
        data = repo.read_data()
        assert data[0]["Phone"] == "+971501234567"

    def test_notification_sent_false(self, repo):
        repo.save_data([SAMPLE_CUSTOMER])
        data = repo.read_data()
        assert data[0]["Notification Sent"] == False

    def test_get_customer_by_id_found(self, repo):
        repo.save_data([SAMPLE_CUSTOMER])
        cid = repo.get_customer_id_by_name(SAMPLE_CUSTOMER["Name"])
        customer = repo.get_customer_by_id(cid)
        assert customer is not None
        assert customer["customer_name"] == SAMPLE_CUSTOMER["Name"]

    def test_get_customer_by_id_not_found(self, repo):
        customer = repo.get_customer_by_id(99999)
        assert customer is None
