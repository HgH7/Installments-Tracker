import logging
import re
from tkinter import messagebox
from typing import Dict, List

from app.repositories.csv_repository import CSVRepository


class CustomerService:
    """Handles customer-related business logic using a CSV repository."""
    def __init__(self, repository: CSVRepository):
        self.repository = repository

    def append_customer(self, customer_data: Dict) -> bool:
        missing_fields = [field for field in self.repository.columns if field not in customer_data]
        if missing_fields:
            logging.error(f"Missing required fields: {missing_fields}")
            messagebox.showerror("خطأ", f"الحقول التالية مطلوبة: {', '.join(missing_fields)}")
            return False

        try:
            if not self.repository.create_backup():
                logging.error("Failed to create backup before appending customer")
                messagebox.showerror("خطأ", "فشل في إنشاء نسخة احتياطية")
                return False

            if self.repository.append_record(customer_data):
                return True
            logging.error("Failed to append customer record")
            messagebox.showerror("خطأ", "حدث خطأ أثناء حفظ البيانات")
            return False
        except PermissionError:
            messagebox.showerror("خطأ", "لا يوجد صلاحية للوصول إلى ملف البيانات")
            return False
        except Exception as e:
            logging.error(f"Error appending customer: {str(e)}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ البيانات: {str(e)}")
            return False

    def update_customer(self, name: str, updated_data: Dict) -> bool:
        try:
            data = self.repository.read_data()
            customer_found = False
            for i, row in enumerate(data):
                if row["Name"] == name:
                    preserved_fields = {
                        "Notification Sent": row.get("Notification Sent", False),
                        "Paid_Installments": row.get("Paid_Installments", "[]"),
                        "Notified_Installments": row.get("Notified_Installments", "[]"),
                        "Installment_Values": row.get("Installment_Values", "{}"),
                    }
                    data[i] = {**row, **updated_data, **preserved_fields}
                    customer_found = True
                    break

            if not customer_found:
                logging.error(f"Customer not found: {name}")
                return False

            success = self.repository.save_data(data)
            if success:
                logging.info(f"Successfully updated customer: {name}")
            return success
        except Exception as e:
            logging.error(f"Error updating customer: {str(e)}")
            return False

    def delete_customer(self, name: str) -> bool:
        try:
            data = self.repository.read_data()
            original_length = len(data)
            data = [row for row in data if row["Name"] != name]
            if len(data) == original_length:
                logging.error(f"Customer not found: {name}")
                return False
            return self.repository.save_data(data)
        except Exception as e:
            logging.error(f"Error deleting customer: {str(e)}")
            return False

    def search_customers(self, query: str) -> List[Dict]:
        try:
            data = self.repository.read_data()
            query = query.lower()
            return [
                row for row in data
                if any(str(value).lower().find(query) != -1 for value in row.values())
            ]
        except Exception as e:
            logging.error(f"Error searching customers: {str(e)}")
            return []

    def mark_installment_as_paid(self, customer_name: str, installment_date: str) -> bool:
        try:
            data = self.repository.read_data()
            for i, row in enumerate(data):
                if row["Name"] == customer_name:
                    try:
                        paid_installments = eval(row.get("Paid_Installments", "[]"))
                        if not isinstance(paid_installments, list):
                            paid_installments = []
                    except Exception:
                        paid_installments = []

                    if installment_date not in paid_installments:
                        paid_installments.append(installment_date)
                        data[i]["Paid_Installments"] = str(paid_installments)
                        return self.repository.save_data(data)
                    logging.info(f"Installment already paid: {installment_date}")
                    return True

            logging.warning(f"Customer not found: {customer_name}")
            return False
        except Exception as e:
            logging.error(f"Error marking installment as paid: {str(e)}")
            return False

    def get_payment_status(self, customer_name: str, installment_date: str) -> bool:
        try:
            data = self.repository.read_data()
            for customer in data:
                if customer["Name"] == customer_name:
                    try:
                        paid_installments = eval(customer.get("Paid_Installments", "[]"))
                        return installment_date in paid_installments
                    except Exception:
                        return False
            return False
        except Exception as e:
            logging.error(f"Error checking payment status: {str(e)}")
            return False

    def update_installment(
        self,
        customer_name: str,
        old_date: str,
        new_date: str,
        new_value: float,
    ) -> bool:
        try:
            data = self.repository.read_data()
            for i, customer in enumerate(data):
                if customer["Name"] == customer_name:
                    dates_str = customer.get("Installment Dates", "")
                    if not dates_str:
                        logging.warning(f"Customer {customer_name} has no installment dates")
                        return False

                    installment_dates = dates_str.split(";")
                    if old_date not in installment_dates:
                        logging.warning(
                            f"Installment date {old_date} not found for customer {customer_name}"
                        )
                        return False

                    installment_dates[installment_dates.index(old_date)] = new_date
                    data[i]["Installment Dates"] = ";".join(installment_dates)

                    try:
                        installment_values = eval(customer.get("Installment_Values", "{}"))
                        if old_date in installment_values:
                            installment_values[new_date] = new_value
                            del installment_values[old_date]
                        else:
                            installment_values[new_date] = new_value
                        data[i]["Installment_Values"] = str(installment_values)
                    except Exception:
                        data[i]["Installment_Values"] = str({new_date: new_value})

                    try:
                        paid_installments = eval(customer.get("Paid_Installments", "[]"))
                        if old_date in paid_installments:
                            paid_installments.remove(old_date)
                            paid_installments.append(new_date)
                            data[i]["Paid_Installments"] = str(paid_installments)
                    except Exception as e:
                        logging.error(f"Error updating paid status: {str(e)}")

                    return self.repository.save_data(data)

            logging.warning(f"Customer not found: {customer_name}")
            return False
        except Exception as e:
            logging.error(f"Error updating installment: {str(e)}")
            return False

    def unmark_installment_as_paid(
        self,
        customer_name: str,
        installment_date: str,
    ) -> bool:
        try:
            data = self.repository.read_data()
            for i, row in enumerate(data):
                if row["Name"] == customer_name:
                    try:
                        paid_installments = eval(row.get("Paid_Installments", "[]"))
                        if not isinstance(paid_installments, list):
                            paid_installments = []
                    except Exception:
                        paid_installments = []

                    if installment_date in paid_installments:
                        paid_installments.remove(installment_date)
                        data[i]["Paid_Installments"] = str(paid_installments)
                        return self.repository.save_data(data)
                    logging.info(f"Installment wasn't marked as paid: {installment_date}")
                    return True

            logging.warning(f"Customer not found: {customer_name}")
            return False
        except Exception as e:
            logging.error(f"Error unmarking installment as paid: {str(e)}")
            return False
