from datetime import datetime, timedelta
from typing import List


def generate_calendar_month_installment_dates(start_date: str, installments: int) -> List[str]:
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    installment_dates = []
    current_date = start_date_obj

    for _ in range(installments):
        installment_dates.append(current_date.strftime("%Y-%m-%d"))
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    return installment_dates


def generate_thirty_day_installment_dates(start_date: str, installments: int) -> List[str]:
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    return [
        (start_date_obj + timedelta(days=30 * i)).strftime("%Y-%m-%d")
        for i in range(installments)
    ]
