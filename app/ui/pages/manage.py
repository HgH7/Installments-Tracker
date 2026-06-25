import logging
import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from customtkinter import CTkToplevel, CTkButton, CTkCheckBox

from app.utils.serialization import load_json_list


def setup_manage_installments_page(
    frames,
    StyleManager,
    customer_service,
    refresh_treeview,
    show_frame,
    app,
    DatePicker,
    refresh_payment_history_views,
):
    frame = frames["manage"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=0)
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_rowconfigure(2, weight=0)

    header_frame = StyleManager.create_section_header(
        frame,
        "Installments",
        "Review and manage current installments.",
    )
    header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(28, 16))

    table_frame = StyleManager.create_frame(frame)
    table_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 16))
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)

    columns = ("Name", "Phone", "Amount", "Installments", "Installment Value", "Next Due", "Paid")
    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        style="Custom.Treeview"
    )

    header_labels = {
        "Name": "Customer Name",
        "Phone": "Phone",
        "Amount": "Amount",
        "Installments": "Installments",
        "Installment Value": "Installment Value",
        "Next Due": "Next Due",
        "Paid": "Paid"
    }

    for col in columns:
        tree.column(col, width=140, anchor="center")
        tree.heading(col, text=header_labels[col])

    tree.grid(row=0, column=0, sticky="nsew")

    y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    y_scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=y_scrollbar.set)

    frame.tree = tree

    def load_data():
        for row in tree.get_children():
            tree.delete(row)

        data = customer_service.get_all_customers()
        today = datetime.now().date()

        try:
            for customer in data:
                installment_dates = customer.get("Installment Dates", "").split(";")
                paid_installments = load_json_list(customer.get("Paid_Installments", "[]"))
                total_installments = len(installment_dates)
                next_due = ""

                for date_str in installment_dates:
                    if not date_str:
                        continue
                    try:
                        due_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        if due_date >= today:
                            next_due = date_str
                            break
                    except ValueError:
                        continue

                is_paid = "Yes" if len(paid_installments) == total_installments and total_installments > 0 else "No"
                item = tree.insert("", "end", values=(
                    customer.get("Name", ""),
                    customer.get("Phone", ""),
                    customer.get("Amount", ""),
                    total_installments,
                    customer.get("Installment Value", ""),
                    next_due,
                    is_paid
                ))

                if is_paid == "Yes":
                    tree.item(item, tags=("paid",))
                else:
                    tree.item(item, tags=("unpaid",))

            tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
            tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
        except Exception as e:
            logging.error(f"Error loading installments data: {str(e)}")
            messagebox.showerror("Error", "An error occurred while loading data.")

    load_data()

    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 30))
    for column in range(5):
        buttons_frame.grid_columnconfigure(column, weight=1)

    def refresh_installments():
        load_data()
        messagebox.showinfo("Success", "Data refreshed successfully.")

    StyleManager.create_button(
        buttons_frame,
        text="Refresh Data",
        width=200,
        command=refresh_installments
    ).grid(row=0, column=0, padx=10, pady=10)

    def mark_as_paid():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Select an installment to mark as paid.")
            return

        try:
            for item in selected_items:
                if "header" in tree.item(item)["tags"]:
                    continue

                values = tree.item(item)["values"]
                customer_name = values[0]
                installment_date = values[5]

                if customer_service.mark_installment_as_paid(customer_name, installment_date):
                    tree.set(item, "Paid", "Yes")
                    tree.item(item, tags=("paid",))
                else:
                    messagebox.showerror("Error", f"Failed to mark installment as paid for customer {customer_name}")
                    return

            messagebox.showinfo("Success", "Selected installments marked as paid.")
            load_data()
            if "view" in frames:
                refresh_treeview(frames["view"].tree)
        except Exception as e:
            logging.error(f"Error marking installments as paid: {str(e)}")
            messagebox.showerror("Error", "An error occurred while marking installments as paid.")

    StyleManager.create_button(
        buttons_frame,
        text="Mark as Paid",
        width=200,
        command=mark_as_paid
    ).grid(row=0, column=1, padx=10, pady=10)

    def edit_installment():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Select an installment to edit.")
            return

        if len(selected_items) > 1:
            messagebox.showerror("Error", "Select only one installment to edit.")
            return

        try:
            item = selected_items[0]
            if "header" in tree.item(item)["tags"]:
                messagebox.showerror("Error", "Select an installment to edit.")
                return

            values = tree.item(item)["values"]
            customer_name = values[0]
            customer_phone = values[1]
            installment_date = values[5]
            installment_value = values[4]
            is_paid = values[6] == "Yes"

            edit_window = CTkToplevel(app)
            edit_window.geometry("500x450")
            edit_window.title("Edit Installment")
            edit_window.transient(app)
            edit_window.grab_set()

            main_frame = StyleManager.create_frame(edit_window)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            StyleManager.create_label(
                main_frame,
                text="Edit Installment Details",
                font_style="subheading"
            ).pack(pady=(0, 20))

            info_frame = StyleManager.create_frame(main_frame)
            info_frame.pack(fill="x", pady=10)

            StyleManager.create_label(
                info_frame,
                text=f"Customer: {customer_name}",
                font_style="body_bold"
            ).pack(anchor="w")

            StyleManager.create_label(
                info_frame,
                text=f"Phone: {customer_phone}",
                font_style="body"
            ).pack(anchor="w")

            fields_frame = StyleManager.create_frame(main_frame)
            fields_frame.pack(fill="x", pady=20)

            date_frame = StyleManager.create_frame(fields_frame)
            date_frame.pack(fill="x", pady=10)

            StyleManager.create_label(
                date_frame,
                text="Installment Date:",
                font_style="body"
            ).pack(side="left", padx=(0, 10))

            date_entry = StyleManager.create_entry(date_frame)
            date_entry.pack(side="left", fill="x", expand=True)
            date_entry.insert(0, installment_date)

            def open_date_picker():
                DatePicker(edit_window, date_entry)

            date_picker_btn = StyleManager.create_button(
                date_frame,
                text="Date",
                width=40,
                command=open_date_picker
            )
            date_picker_btn.pack(side="left", padx=(10, 0))

            amount_frame = StyleManager.create_frame(fields_frame)
            amount_frame.pack(fill="x", pady=10)

            StyleManager.create_label(
                amount_frame,
                text="Installment Value:",
                font_style="body"
            ).pack(side="left", padx=(0, 10))

            amount_entry = StyleManager.create_entry(amount_frame)
            amount_entry.pack(side="left", fill="x", expand=True)
            amount_entry.insert(0, str(installment_value))

            paid_frame = StyleManager.create_frame(fields_frame)
            paid_frame.pack(fill="x", pady=10)

            paid_status = tk.BooleanVar(value=is_paid)
            paid_checkbox = CTkCheckBox(
                paid_frame,
                text="Paid",
                variable=paid_status,
                onvalue=True,
                offvalue=False,
                checkbox_width=24,
                checkbox_height=24,
                corner_radius=5,
                border_width=2,
                fg_color=StyleManager.COLORS["primary"],
                hover_color=StyleManager.COLORS["secondary"],
                checkmark_color=StyleManager.COLORS["text"]
            )
            paid_checkbox.pack(anchor="w")

            buttons_frame = StyleManager.create_frame(main_frame)
            buttons_frame.pack(fill="x", pady=(20, 10))
            buttons_frame.grid_columnconfigure(0, weight=1)
            buttons_frame.grid_columnconfigure(1, weight=1)

            def save_changes():
                try:
                    new_date = date_entry.get().strip()
                    new_value_str = amount_entry.get().strip()
                    new_paid_status = paid_status.get()

                    try:
                        datetime.strptime(new_date, "%Y-%m-%d")
                    except ValueError:
                        messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
                        return

                    if not re.match(r"^\d+(\.\d{1,2})?$", new_value_str):
                        messagebox.showerror("Error", "Installment value must be a valid number.")
                        return

                    new_value = float(new_value_str)

                    if customer_service.update_installment(customer_name, installment_date, new_date, new_value):
                        if is_paid != new_paid_status:
                            if new_paid_status:
                                customer_service.mark_installment_as_paid(customer_name, new_date)
                            else:
                                customer_service.unmark_installment_as_paid(customer_name, new_date)
                        messagebox.showinfo("Success", "Installment updated successfully.")
                        edit_window.destroy()
                        load_data()
                        refresh_payment_history_views()
                    else:
                        messagebox.showerror("Error", "Failed to update installment.")
                except Exception as e:
                    logging.error(f"Error saving installment changes: {str(e)}")
                    messagebox.showerror("Error", f"An error occurred while saving changes: {str(e)}")

            StyleManager.create_button(
                buttons_frame,
                text="Save Changes",
                width=200,
                command=save_changes
            ).grid(row=0, column=0, padx=5, pady=5)

            StyleManager.create_button(
                buttons_frame,
                text="Cancel",
                width=200,
                style="secondary",
                command=edit_window.destroy
            ).grid(row=0, column=1, padx=5, pady=5)
        except Exception as e:
            logging.error(f"Error opening edit installment window: {str(e)}")
            messagebox.showerror("Error", f"An error occurred while opening the edit window: {str(e)}")

    StyleManager.create_button(
        buttons_frame,
        text="Edit Installment",
        width=200,
        command=edit_installment
    ).grid(row=0, column=2, padx=10, pady=10)

    def delete_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Select a customer to delete.")
            return

        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete customer {customer_name}\nThis action cannot be undone."):
            if customer_service.delete_customer(customer_name):
                messagebox.showinfo("Success", f"Deleted customer {customer_name} successfully.")
                refresh_treeview(tree)
            else:
                messagebox.showerror("Error", "Failed to delete customer.")

    StyleManager.create_button(
        buttons_frame,
        text="Delete Customer",
        style="danger",
        width=200,
        command=delete_customer
    ).grid(row=0, column=3, padx=10, pady=10)

    StyleManager.create_button(
        buttons_frame,
        text="Back",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    ).grid(row=0, column=4, padx=10, pady=10)
