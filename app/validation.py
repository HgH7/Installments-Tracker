"""Input validation for customer data, phone numbers, amounts, and dates."""

import re
from datetime import datetime
from typing import List, Optional

PHONE_PATTERN = re.compile(r"^\+?\d{10,15}$")
MONEY_PATTERN = re.compile(r"^\d+(\.\d{1,2})?$")
WHOLE_NUMBER_PATTERN = re.compile(r"^\d+$")
NAME_PATTERN = re.compile(r"^[A-Za-z\u0600-\u06FF\s]+$")
ASCII_NAME_PATTERN = re.compile(r"^[A-Za-z\s]+$")


class ValidationResult:
    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []

    def add_error(self, error: str):
        self.errors.append(error)
        self.is_valid = False

    def __bool__(self):
        return self.is_valid

    def __str__(self):
        if self.is_valid:
            return "Valid"
        return "; ".join(self.errors)


class ValidationService:
    @staticmethod
    def validate_phone(phone: str) -> ValidationResult:
        result = ValidationResult()
        if not phone:
            result.add_error("Phone number is required.")
            return result
        if not PHONE_PATTERN.match(phone):
            result.add_error("Phone must be 10-15 digits, optionally starting with +.")
        return result

    @staticmethod
    def validate_amount(amount: str) -> ValidationResult:
        result = ValidationResult()
        if not amount:
            result.add_error("Amount is required.")
            return result
        if not MONEY_PATTERN.match(amount):
            result.add_error("Amount must be a valid number with up to 2 decimal places.")
        return result

    @staticmethod
    def validate_installment_count(count: str) -> ValidationResult:
        result = ValidationResult()
        if not count:
            result.add_error("Installment count is required.")
            return result
        if not WHOLE_NUMBER_PATTERN.match(count) or int(count) <= 0:
            result.add_error("Installment count must be a whole number greater than zero.")
        return result

    @staticmethod
    def validate_date(date_str: str, fmt: str = "%Y-%m-%d") -> ValidationResult:
        result = ValidationResult()
        if not date_str:
            result.add_error("Date is required.")
            return result
        try:
            datetime.strptime(date_str, fmt)
        except ValueError:
            result.add_error(f"Invalid date format. Use {fmt}.")
        return result

    @staticmethod
    def validate_name(name: str, allow_unicode: bool = True) -> ValidationResult:
        result = ValidationResult()
        if not name:
            result.add_error("Name is required.")
            return result
        pattern = NAME_PATTERN if allow_unicode else ASCII_NAME_PATTERN
        if not pattern.match(name):
            result.add_error("Name can contain only letters and spaces.")
        return result

    @staticmethod
    def validate_installment_value(value: str) -> ValidationResult:
        result = ValidationResult()
        if not value:
            result.add_error("Installment value is required.")
            return result
        if not MONEY_PATTERN.match(value):
            result.add_error("Installment value must be a valid number with up to 2 decimal places.")
        return result

    @staticmethod
    def validate_customer(
        name: str,
        phone: str,
        amount: str,
        installments: str,
        start_date: str,
    ) -> ValidationResult:
        result = ValidationResult()
        result.errors.extend(ValidationService.validate_name(name).errors)
        result.errors.extend(ValidationService.validate_phone(phone).errors)
        result.errors.extend(ValidationService.validate_amount(amount).errors)
        result.errors.extend(ValidationService.validate_installment_count(installments).errors)
        result.errors.extend(ValidationService.validate_date(start_date).errors)
        if result.errors:
            result.is_valid = False
        return result

    @staticmethod
    def normalize_phone(phone: str) -> str:
        phone = phone.strip()
        if phone and not phone.startswith("+"):
            phone = "+" + phone
        return phone
