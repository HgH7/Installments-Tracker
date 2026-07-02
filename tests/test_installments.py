
from app.utils.installments import (
    generate_calendar_month_installment_dates,
    generate_thirty_day_installment_dates,
)


class TestInstallmentGeneration:
    def test_calendar_month_3_installments(self):
        dates = generate_calendar_month_installment_dates("2026-01-15", 3)
        assert len(dates) == 3
        assert dates[0] == "2026-01-15"
        assert dates[1] == "2026-02-15"
        assert dates[2] == "2026-03-15"

    def test_calendar_month_cross_year(self):
        dates = generate_calendar_month_installment_dates("2026-11-01", 3)
        assert len(dates) == 3
        assert dates[0] == "2026-11-01"
        assert dates[1] == "2026-12-01"
        assert dates[2] == "2027-01-01"

    def test_thirty_day_3_installments(self):
        dates = generate_thirty_day_installment_dates("2026-01-15", 3)
        assert len(dates) == 3
        assert dates[0] == "2026-01-15"
        assert dates[1] == "2026-02-14"
        assert dates[2] == "2026-03-16"

    def test_thirty_day_single(self):
        dates = generate_thirty_day_installment_dates("2026-06-01", 1)
        assert len(dates) == 1
        assert dates[0] == "2026-06-01"
