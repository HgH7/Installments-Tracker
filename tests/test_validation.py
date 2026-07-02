
from app.core.validation import ValidationService


class TestValidationService:
    def test_validate_phone_valid(self):
        assert ValidationService.validate_phone("+971501234567")
        assert ValidationService.validate_phone("0501234567")

    def test_validate_phone_invalid(self):
        assert not ValidationService.validate_phone("")
        assert not ValidationService.validate_phone("abc")
        assert not ValidationService.validate_phone("123")

    def test_validate_amount_valid(self):
        assert ValidationService.validate_amount("1000")
        assert ValidationService.validate_amount("1000.50")
        assert ValidationService.validate_amount("0.99")

    def test_validate_amount_invalid(self):
        assert not ValidationService.validate_amount("")
        assert not ValidationService.validate_amount("abc")
        assert not ValidationService.validate_amount("1000.123")

    def test_validate_installment_count_valid(self):
        assert ValidationService.validate_installment_count("1")
        assert ValidationService.validate_installment_count("12")

    def test_validate_installment_count_invalid(self):
        assert not ValidationService.validate_installment_count("")
        assert not ValidationService.validate_installment_count("0")
        assert not ValidationService.validate_installment_count("-1")
        assert not ValidationService.validate_installment_count("abc")

    def test_validate_date_valid(self):
        assert ValidationService.validate_date("2026-01-15")

    def test_validate_date_invalid(self):
        assert not ValidationService.validate_date("")
        assert not ValidationService.validate_date("15-01-2026")
        assert not ValidationService.validate_date("not-a-date")

    def test_validate_name_valid(self):
        assert ValidationService.validate_name("Alice Smith")
        assert ValidationService.validate_name("أحمد")

    def test_validate_name_invalid(self):
        assert not ValidationService.validate_name("")
        assert not ValidationService.validate_name("John123")

    def test_normalize_phone(self):
        assert ValidationService.normalize_phone("0501234567") == "+0501234567"
        assert ValidationService.normalize_phone("+0501234567") == "+0501234567"

    def test_validate_customer_all_valid(self):
        result = ValidationService.validate_customer(
            "Alice", "+971501234567", "3000", "3", "2026-01-01"
        )
        assert result

    def test_validate_customer_with_errors(self):
        result = ValidationService.validate_customer("", "", "", "", "")
        assert not result
        assert len(result.errors) >= 3
