import logging
from datetime import datetime

logger = logging.getLogger(__name__)
from tkinter import messagebox, ttk

from customtkinter import CTkToplevel

from app.ui.dialogs.dialogs import EditInstallmentDialog
from app.ui.styles.style import StyleManager
from app.utils.serialization import load_json_dict, load_json_list


def show_payment_history(app, frames, csv_repository, customer_service):
    try:
        current_frame = None
        for frame in frames.values():
            if frame.winfo_ismapped():
                current_frame = frame
                break

        if not current_frame or not hasattr(current_frame, 'tree'):
            messagebox.showerror("Error", "Customer list was not found.")
            return

        tree = current_frame.tree
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a customer to view payment history.")
            return
        if len(selected) > 1:
            messagebox.showerror("Error", "Select only one customer.")
            return

        item = selected[0]
        customer_name = tree.item(item)["values"][0]

        data = csv_repository.read_data()
        customer_data = next((c for c in data if c["Name"] == customer_name), None)
        if not customer_data:
            messagebox.showerror("Error", "Customer data was not found.")
            return

        history_window = CTkToplevel(app)
        history_window.geometry("680x620")
        history_window.title(f"Payment History - {customer_name}")
        history_window.transient(app)
        history_window.grab_set()

        main_frame = StyleManager.create_frame(history_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        StyleManager.create_label(main_frame, text="Payment History", font_style="subheading").pack(pady=(0, 4))
        StyleManager.create_label(main_frame, text=customer_name, font_style="small",
                                  text_color=StyleManager.COLORS["text_muted"]).pack(pady=(0, 20))

        installment_dates = customer_data["Installment Dates"].split(";")
        default_value = float(customer_data["Installment Value"])
        paid_installments = load_json_list(customer_data.get("Paid_Installments", "[]"))
        installment_values = load_json_dict(customer_data.get("Installment_Values", "{}"))

        total_count = len(installment_dates)
        paid_count = len(paid_installments)
        total_amount = sum(float(installment_values.get(d, default_value)) for d in installment_dates)
        paid_amount = sum(float(installment_values.get(d, default_value)) for d in paid_installments)

        progress_section = StyleManager.create_frame(main_frame, fg_color="transparent", border_width=0)
        progress_section.pack(fill="x", pady=(0, 16))

        progress_bar = StyleManager.create_progress_bar(progress_section, width=0)
        progress_bar.pack(fill="x", pady=(0, 8))
        progress_bar.set(paid_count / total_count if total_count > 0 else 0)

        collected_pct = paid_amount / total_amount * 100 if total_amount > 0 else 0
        StyleManager.create_label(progress_section,
                                  text=f"{paid_count} of {total_count} installments paid - {collected_pct:.0f}% collected",
                                  font_style="body_bold").pack(anchor="w")
        remaining = total_amount - paid_amount
        StyleManager.create_label(progress_section,
                                  text=f"Collected: {paid_amount:.2f} / {total_amount:.2f}  |  Remaining: {remaining:.2f}",
                                  font_style="small", text_color=StyleManager.COLORS["text_muted"]).pack(anchor="w")

        table_frame = StyleManager.create_frame(main_frame)
        table_frame.pack(fill="both", expand=True, pady=10)

        columns = ("Date", "Value", "Status", "Action")
        table = ttk.Treeview(table_frame, columns=columns, show="headings", style="Custom.Treeview")
        col_widths = {"Date": 150, "Value": 150, "Status": 150, "Action": 150}
        col_headers = {"Date": "Installment Date", "Value": "Installment Value", "Status": "Status", "Action": "Action"}
        for col in columns:
            table.column(col, width=col_widths[col], anchor="center")
            table.heading(col, text=col_headers[col])

        today = datetime.now().strftime("%Y-%m-%d")
        for date in installment_dates:
            is_paid = date in paid_installments
            value = installment_values.get(date, default_value)
            is_future = date > today
            action = "" if is_paid else "Mark as Paid" if not is_future else "Future"
            tags = ("paid",) if is_paid else ("unpaid",)
            table.insert("", "end", values=(date, f"{value:.2f}", "Paid" if is_paid else "Unpaid", action), tags=tags)

        table.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        table.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        scrollbar.pack(side="right", fill="y")
        table.configure(yscrollcommand=scrollbar.set)
        table.pack(fill="both", expand=True)

        def mark_as_paid(event):
            try:
                item = table.identify_row(event.y)
                if not item:
                    return
                values = table.item(item)["values"]
                date = values[0]
                if values[3] == "Mark as Paid":
                    if customer_service.mark_installment_as_paid(customer_name, date):
                        table.item(item, values=(date, values[1], "Paid", ""), tags=("paid",))
                        messagebox.showinfo("Success", "Installment marked as paid.")
            except Exception as e:
                logger.exception("Failed to mark installment as paid")
                messagebox.showerror("Error", "An unexpected error occurred while marking the installment as paid.")

        def edit_installment(event):
            try:
                item = table.identify_row(event.y)
                if not item:
                    return
                values = table.item(item)["values"]
                date, val_str, status = values[0], values[1], values[2]
                is_paid = status == "Paid"

                def on_save(**kw):
                    if customer_service.update_installment(customer_name, date, kw["new_date"], kw["new_value"]):
                        if is_paid != kw["new_paid_status"]:
                            if kw["new_paid_status"]:
                                customer_service.mark_installment_as_paid(customer_name, kw["new_date"])
                            else:
                                customer_service.unmark_installment_as_paid(customer_name, kw["new_date"])
                        messagebox.showinfo("Success", "Installment updated.")
                        kw["dialog"].destroy()
                        history_window.destroy()
                        show_payment_history(app, frames, csv_repository, customer_service)

                dialog = EditInstallmentDialog(
                    history_window, customer_name, date, float(val_str), is_paid, on_save
                )
                dialog.show()
            except Exception as e:
                logger.exception("Failed to edit installment")
                messagebox.showerror("Error", "An unexpected error occurred while editing the installment.")

        table.bind("<Double-1>", mark_as_paid)
        table.bind("<Button-3>", edit_installment)

        button_row = StyleManager.create_frame(main_frame)
        button_row.pack(fill="x", pady=(20, 0))
        button_row.grid_columnconfigure(0, weight=1)
        left_side = StyleManager.create_frame(button_row, fg_color="transparent")
        left_side.grid(row=0, column=0, sticky="w")
        StyleManager.create_button(left_side, text="Close", style="secondary", width=120,
                                   command=history_window.destroy).pack(side="left", pady=10)
    except Exception as e:
        logger.exception("Failed to show payment history")
        messagebox.showerror("Error", "An unexpected error occurred while loading the payment history.")


def refresh_payment_history_views(app):
    for widget in app.winfo_children():
        if isinstance(widget, CTkToplevel) and "Payment History" in widget.title():
            widget.destroy()
