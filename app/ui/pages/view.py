import logging
import re
from datetime import datetime
from tkinter import messagebox, ttk
from customtkinter import CTkToplevel, CTkButton, CTkEntry, CTkTextbox


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
        "Search, review, edit, export, and inspect payment history.",
    )
    header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))

    search_frame = StyleManager.create_frame(frame)
    search_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 14))
    search_frame.grid_columnconfigure(1, weight=1)

    StyleManager.create_label(
        search_frame,
        text="Search:",
        font_style="body_bold"
    ).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")

    search_entry = StyleManager.create_entry(
        search_frame,
        width=400,
        height=35,
        placeholder_text="Enter customer name or phone number..."
    )
    search_entry.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ew")

    def perform_search():
        query = search_entry.get().strip()
        results = customer_service.search_customers(query)
        refresh_treeview(frame.tree, results)
        status_label.configure(text=f"Customers: {len(results)}")

    search_entry.bind("<Return>", lambda event: perform_search())

    search_button = StyleManager.create_button(
        search_frame,
        text="Search",
        width=100,
        height=35,
        command=perform_search
    )
    search_button.grid(row=0, column=2, padx=(0, 0), pady=5)

    status_label = StyleManager.create_label(
        search_frame,
        text="",
        font_style="small",
        text_color=StyleManager.COLORS["text_secondary"]
    )
    status_label.grid(row=0, column=3, padx=(10, 0), pady=5, sticky="e")

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

        customer = customer_service.get_customer_by_name(customer_name)
        if not customer:
            messagebox.showerror("Error", "Customer data was not found.")
            return

        edit_window = CTkToplevel(app)
        edit_window.geometry("800x600")
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

                if customer_name != name:
                    if customer_service.delete_customer(customer_name) and customer_service.append_customer({
                        **updated_data,
                        "Notification Sent": customer.get("Notification Sent", False),
                        "Paid_Installments": customer.get("Paid_Installments", "[]"),
                        "Notified_Installments": customer.get("Notified_Installments", "[]"),
                        "Installment_Values": customer.get("Installment_Values", "{}"),
                    }):
                        messagebox.showinfo("Success", "Customer updated successfully.")
                        edit_window.destroy()
                        refresh_treeview(tree)
                        refresh_payment_history_views()
                    else:
                        messagebox.showerror("Error", "Failed to update customer.")
                else:
                    if customer_service.update_customer(customer_name, updated_data):
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

    def delete_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Select a customer to delete.")
            return

        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete customer {customer_name}?\nThis action cannot be undone."):
            if customer_service.delete_customer(customer_name):
                messagebox.showinfo("Success", f"Deleted customer {customer_name} successfully.")
                refresh_treeview(tree)
            else:
                messagebox.showerror("Error", "Failed to delete customer.")

    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 24))
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)

    left_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    left_buttons.grid(row=0, column=0, sticky="w")

    right_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    right_buttons.grid(row=0, column=1, sticky="e")

    refresh_btn = StyleManager.create_button(
        left_buttons,
        text="Refresh",
        width=120,
        command=lambda: refresh_treeview(tree)
    )
    refresh_btn.pack(side="left", padx=(0, 10), pady=10)

    history_btn = StyleManager.create_button(
        left_buttons,
        text="Payment History",
        width=120,
        command=show_payment_history
    )
    history_btn.pack(side="left", padx=(0, 10), pady=10)

    export_btn = StyleManager.create_button(
        left_buttons,
        text="Export Excel",
        width=120,
        command=export_to_excel
    )
    export_btn.pack(side="left", padx=(0, 10), pady=10)

    back_btn = StyleManager.create_button(
        right_buttons,
        text="Back",
        style="secondary",
        width=120,
        command=lambda: show_frame(frames["home"])
    )
    back_btn.pack(side="right", padx=(0, 0), pady=10)

    delete_btn = StyleManager.create_button(
        right_buttons,
        text="Delete Customer",
        style="danger",
        width=120,
        command=delete_customer
    )
    delete_btn.pack(side="right", padx=(0, 10), pady=10)

    edit_btn = StyleManager.create_button(
        right_buttons,
        text="Edit Customer",
        width=120,
        command=edit_customer
    )
    edit_btn.pack(side="right", padx=(0, 10), pady=10)
