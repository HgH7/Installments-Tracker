import re
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

import customtkinter
from customtkinter import CTkToplevel

from app.ui.widgets.customer_timeline import show_customer_timeline
from app.utils.serialization import load_json_list


def setup_view_page(
    frames,
    StyleManager,
    customer_service,
    refresh_treeview,
    show_frame,
    app,
    DatePicker,
    refresh_payment_history_views,
    export_to_excel,
    show_payment_history,
    csv_repository=None,
    activity_service=None,
):
    frame = frames["view"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=0)
    frame.grid_rowconfigure(1, weight=0)
    frame.grid_rowconfigure(2, weight=1)
    frame.grid_rowconfigure(3, weight=0)

    header_frame = StyleManager.create_section_header(
        frame,
        "Customers",
        "Search, filter, review, and manage customers.",
    )
    header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))

    search_frame = StyleManager.create_frame(frame)
    search_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
    search_frame.grid_columnconfigure(1, weight=1)

    StyleManager.create_label(search_frame, text="Search:", font_style="body_bold").grid(row=0, column=0, padx=(0, 8), pady=5, sticky="w")

    search_entry = StyleManager.create_entry(search_frame, width=300, height=35,
                                             placeholder_text="Name, phone, notes, or due date...")
    search_entry.grid(row=0, column=1, padx=(0, 8), pady=5, sticky="ew")

    filter_var = tk.StringVar(value="All")
    filter_menu = customtkinter.CTkOptionMenu(search_frame, values=["All", "Active", "Completed", "Overdue", "Due Today", "Due This Week", "Due This Month"],
                                              variable=filter_var, font=StyleManager.FONTS["small"],
                                              fg_color=StyleManager.COLORS["surface_high"],
                                              button_color=StyleManager.COLORS["surface_highest"],
                                              button_hover_color=StyleManager.COLORS["border"],
                                              text_color=StyleManager.COLORS["text"])
    filter_menu.grid(row=0, column=2, padx=(0, 8), pady=5)

    def perform_search():
        query = search_entry.get().strip()
        fval = filter_var.get()

        all_data = customer_service.get_all_customers()
        today = datetime.now().date()

        filtered = []
        for c in all_data:
            dates_str = c.get("Installment Dates", "")
            dates = [d for d in dates_str.split(";") if d]
            paid = load_json_list(c.get("Paid_Installments", "[]"))
            total_inst = len(dates)
            paid_count = len(paid)

            if fval == "Active" and paid_count == total_inst:
                continue
            if fval == "Completed" and paid_count != total_inst:
                continue
            if fval == "Overdue":
                has_overdue = False
                for ds in dates:
                    try:
                        if datetime.strptime(ds, "%Y-%m-%d").date() < today and ds not in paid:
                            has_overdue = True
                            break
                    except ValueError:
                        continue
                if not has_overdue:
                    continue
            if fval == "Due Today":
                match = False
                for ds in dates:
                    try:
                        if datetime.strptime(ds, "%Y-%m-%d").date() == today and ds not in paid:
                            match = True
                            break
                    except ValueError:
                        continue
                if not match:
                    continue
            if fval == "Due This Week":
                match = False
                end = today + timedelta(days=7)
                for ds in dates:
                    try:
                        d = datetime.strptime(ds, "%Y-%m-%d").date()
                        if today <= d <= end and ds not in paid:
                            match = True
                            break
                    except ValueError:
                        continue
                if not match:
                    continue
            if fval == "Due This Month":
                match = False
                for ds in dates:
                    try:
                        d = datetime.strptime(ds, "%Y-%m-%d").date()
                        if d.month == today.month and d.year == today.year and ds not in paid:
                            match = True
                            break
                    except ValueError:
                        continue
                if not match:
                    continue

            filtered.append(c)

        if query:
            q = query.lower()
            filtered = [c for c in filtered if any(str(v).lower().find(q) != -1 for v in c.values())]

        refresh_treeview(frame.tree, filtered)
        status_label.configure(text=f"Customers: {len(filtered)}")

    search_entry.bind("<Return>", lambda event: perform_search())
    filter_var.trace_add("write", lambda *a: perform_search())

    search_button = StyleManager.create_button(search_frame, text="Search", width=90, height=35, command=perform_search)
    search_button.grid(row=0, column=3, padx=(0, 8), pady=5)

    status_label = StyleManager.create_label(search_frame, text="", font_style="small",
                                             text_color=StyleManager.COLORS["text_secondary"])
    status_label.grid(row=0, column=4, padx=(8, 0), pady=5, sticky="e")

    StyleManager.create_button(search_frame, text="Clear", width=70, height=35, style="secondary",
                               command=lambda: (search_entry.delete(0, "end"), filter_var.set("All"), perform_search())
                               ).grid(row=0, column=5, padx=(4, 0), pady=5)

    table_frame = StyleManager.create_frame(frame)
    table_frame.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 16))
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)

    column_headers = {
        "Name": "Customer Name",
        "Phone": "Phone",
        "Amount": "Amount",
        "Installments": "Installments",
        "Installment Value": "Installment Value",
        "Start Date": "Start Date"
    }

    tree = ttk.Treeview(
        table_frame,
        columns=list(column_headers.keys()),
        show="headings",
        style="Custom.Treeview"
    )

    column_weights = {
        "Name": 25,
        "Phone": 20,
        "Amount": 15,
        "Installments": 15,
        "Installment Value": 15,
        "Start Date": 10
    }

    for col in column_headers.keys():
        width = int((column_weights[col] / 100) * 1200)
        tree.column(col, width=width, minwidth=100)
        tree.heading(col, text=column_headers[col])

    tree.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

    y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    y_scrollbar.grid(row=0, column=1, sticky="ns")

    x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    x_scrollbar.grid(row=1, column=0, sticky="ew")

    tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
    frame.tree = tree

    refresh_treeview(tree)
    frame.page_on_show = lambda: refresh_treeview(frame.tree)

    data = customer_service.get_all_customers()
    status_label.configure(text=f"Customers: {len(data)}")

    def edit_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Select a customer to edit.")
            return

        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]

        if customer_name == "—":
            messagebox.showerror("Error", "Select a valid customer to edit.")
            return

        customer = customer_service.get_customer_by_name(customer_name)
        if not customer:
            messagebox.showerror("Error", "Customer data was not found.")
            return

        edit_window = CTkToplevel(app)
        edit_window.geometry("520x580")
        edit_window.title(f"Edit Customer Details: {customer_name}")

        StyleManager.create_label(
            edit_window,
            text=f"Edit Customer Details: {customer_name}",
            font_style="heading"
        ).pack(pady=(20, 10))

        form_frame = StyleManager.create_frame(edit_window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        fields = [
            {"label": "Customer Name:", "key": "Name", "type": "text"},
            {"label": "Phone:", "key": "Phone", "type": "phone"},
            {"label": "Amount:", "key": "Amount", "type": "number"},
            {"label": "Installments:", "key": "Installments", "type": "number"}
        ]

        entries = {}

        for field in fields:
            StyleManager.create_label(
                form_frame,
                text=field["label"],
                font_style="label",
            ).pack(anchor="w", padx=16, pady=(12, 4))

            entry = StyleManager.create_entry(form_frame)
            entry.pack(fill="x", padx=16, pady=(0, 4))
            entry.insert(0, str(customer.get(field["key"], "")))
            entries[field["key"]] = entry

        StyleManager.create_label(
            form_frame,
            text="Installment Start Date:",
            font_style="label",
        ).pack(anchor="w", padx=16, pady=(12, 4))

        date_row = StyleManager.create_frame(form_frame, fg_color="transparent", border_width=0)
        date_row.pack(fill="x", padx=16, pady=(0, 4))
        date_row.grid_columnconfigure(0, weight=1)

        start_date_entry = StyleManager.create_entry(date_row)
        start_date_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        start_date_entry.insert(0, str(customer.get("Start Date", "")))
        entries["Start Date"] = start_date_entry

        StyleManager.create_button(
            date_row,
            text="Select Date",
            style="secondary",
            width=120,
            command=lambda: DatePicker(edit_window, start_date_entry)
        ).grid(row=0, column=1)

        buttons_frame = StyleManager.create_frame(edit_window)
        buttons_frame.pack(fill="x", padx=20, pady=20)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        left_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
        left_side.grid(row=0, column=0, sticky="w")
        right_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
        right_side.grid(row=0, column=1, sticky="e")

        def save_changes():
            name_pattern = r"^[A-Za-z\u0600-\u06FF\s]+$"
            phone_pattern = r"^\+?\d{10,15}$"
            amount_pattern = r"^\d+(\.\d{1,2})?$"
            installments_pattern = r"^\d+$"

            name = entries["Name"].get().strip()
            phone = entries["Phone"].get().strip()
            amount = entries["Amount"].get().strip()
            installments = entries["Installments"].get().strip()
            start_date = entries["Start Date"].get().strip()

            if not re.fullmatch(name_pattern, name):
                messagebox.showerror("Error", "Name can contain only letters and spaces.")
                return

            if not re.fullmatch(phone_pattern, phone):
                messagebox.showerror("Error", "Phone number must contain digits only and may start with +.")
                return

            if not re.fullmatch(amount_pattern, amount):
                messagebox.showerror("Error", "Amount must be a valid number.")
                return

            if not re.fullmatch(installments_pattern, installments):
                messagebox.showerror("Error", "Installments must be a whole number.")
                return

            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
                return

            try:
                updated_data = customer_service.build_customer_record(
                    name,
                    phone,
                    amount,
                    installments,
                    start_date,
                    date_strategy="thirty_day",
                    include_tracking_fields=False,
                )

                if customer_service.update_customer(customer_name, updated_data):
                    if activity_service:
                        cid = csv_repository.get_customer_id_by_name(name)
                        activity_service.log("Customer edited", customer_id=cid, detail=f"{customer_name} → {name}")
                    messagebox.showinfo("Success", "Customer updated successfully.")
                    edit_window.destroy()
                    refresh_treeview(tree)
                    refresh_payment_history_views()
                else:
                    messagebox.showerror("Error", "Failed to update customer.")

            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input data: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

        StyleManager.create_button(
            left_side,
            text="Save Changes",
            width=160,
            command=save_changes
        ).pack(side="left", pady=10)

        StyleManager.create_button(
            right_side,
            text="Cancel",
            style="secondary",
            width=120,
            command=edit_window.destroy
        ).pack(side="right", pady=10)

        edit_window.transient(app)
        edit_window.grab_set()
        edit_window.focus_set()

    def show_timeline():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Select a customer to view timeline.")
            return
        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]
        if customer_name == "—":
            messagebox.showerror("Error", "Select a valid customer.")
            return
        show_customer_timeline(app, customer_name, activity_service, csv_repository, customer_service, StyleManager)

    def delete_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Select a customer to delete.")
            return

        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]

        if customer_name == "—":
            messagebox.showerror("Error", "Select a valid customer to delete.")
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete customer {customer_name}?\nThis action cannot be undone."):
            if customer_service.delete_customer(customer_name):
                if activity_service:
                    activity_service.log("Customer deleted", detail=customer_name)
                messagebox.showinfo("Success", f"Deleted customer {customer_name} successfully.")
                refresh_treeview(tree)
            else:
                messagebox.showerror("Error", "Failed to delete customer.")

    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 24))
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)
    buttons_frame.grid_columnconfigure(2, weight=1)

    left_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    left_side.grid(row=0, column=0, sticky="w")

    center = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    center.grid(row=0, column=1)

    right_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    right_side.grid(row=0, column=2, sticky="e")

    StyleManager.create_button(
        left_side,
        text="Refresh",
        width=110,
        command=lambda: refresh_treeview(tree)
    ).pack(side="left", padx=(0, 8), pady=10)

    StyleManager.create_button(
        left_side,
        text="Export Excel",
        width=110,
        command=export_to_excel
    ).pack(side="left", pady=10)

    StyleManager.create_button(
        center,
        text="Edit Customer",
        width=110,
        command=edit_customer
    ).pack(side="left", padx=(0, 8), pady=10)

    StyleManager.create_button(
        center,
        text="Payment History",
        width=110,
        command=show_payment_history
    ).pack(side="left", pady=10)

    StyleManager.create_button(
        center,
        text="Timeline",
        width=90,
        command=lambda: show_timeline()
    ).pack(side="left", padx=(8, 0), pady=10)

    StyleManager.create_button(
        right_side,
        text="Delete Customer",
        style="danger",
        width=120,
        command=delete_customer
    ).pack(side="left", padx=(0, 8), pady=10)

    StyleManager.create_button(
        right_side,
        text="Back",
        style="secondary",
        width=100,
        command=lambda: show_frame(frames["home"])
    ).pack(side="left", pady=10)
