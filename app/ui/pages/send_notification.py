import logging
from datetime import datetime
from tkinter import messagebox, ttk

from customtkinter import CTkToplevel

from app.services.notification_service import NotificationService
from app.settings import settings


def setup_send_notification_page(frames, StyleManager, csv_repository, show_frame, app, reminder_service, activity_service):
    frame = frames["notifications"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    header_frame = StyleManager.create_section_header(
        frame,
        "Notification Center",
        "View due installments, generate reminders, and open WhatsApp Web.",
    )
    header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))

    table_frame = StyleManager.create_frame(frame)
    table_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)

    columns = ("Name", "Phone", "Installment Date", "Installment Value")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Custom.Treeview")

    column_widths = {"Name": 150, "Phone": 120, "Installment Date": 120, "Installment Value": 120}
    column_headers = {"Name": "Customer Name", "Phone": "Phone", "Installment Date": "Installment Date", "Installment Value": "Installment Value"}

    for col in columns:
        tree.column(col, width=column_widths[col], anchor="center")
        tree.heading(col, text=column_headers[col])

    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)
    frame.tree = tree

    def load_data():
        for row in tree.get_children():
            tree.delete(row)
        data = csv_repository.read_data()
        today = datetime.now().date()
        if not data:
            tree.insert("", "end", values=("—", "—", "—", "—"), tags=("empty",))
            return
        for customer in data:
            installment_dates = customer.get("Installment Dates", "").split(";")
            for date in installment_dates:
                try:
                    date_obj = datetime.strptime(date.strip(), "%Y-%m-%d").date()
                except ValueError:
                    continue
                if date_obj >= today:
                    tree.insert("", "end", values=(
                        customer.get("Name", ""), customer.get("Phone", ""), date, customer.get("Installment Value", "")
                    ))

    load_data()

    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)

    left_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    left_side.grid(row=0, column=0, sticky="w")
    right_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    right_side.grid(row=0, column=1, sticky="e")

    def show_reminder_history():
        history_window = CTkToplevel(app)
        history_window.geometry("700x500")
        history_window.title("Reminder History")
        history_window.transient(app)
        history_window.grab_set()

        main_frame = StyleManager.create_frame(history_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        hist_columns = ("Customer", "Phone", "Date", "Amount", "Status", "Sent At")
        hist_tree = ttk.Treeview(main_frame, columns=hist_columns, show="headings", style="Custom.Treeview")
        for col in hist_columns:
            hist_tree.column(col, width=100, anchor="center")
            hist_tree.heading(col, text=col)
        hist_tree.grid(row=0, column=0, sticky="nsew")

        hist_scroll = ttk.Scrollbar(main_frame, orient="vertical", command=hist_tree.yview)
        hist_scroll.grid(row=0, column=1, sticky="ns")
        hist_tree.configure(yscrollcommand=hist_scroll.set)

        reminders = reminder_service.get_history()
        for r in reminders:
            hist_tree.insert("", "end", values=(
                r.get("customer_name", ""), r.get("phone", ""),
                r.get("installment_date", ""), r.get("amount", 0),
                r.get("status", ""), r.get("sent_at", ""),
            ))

        btn_frame = StyleManager.create_frame(history_window)
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        StyleManager.create_button(btn_frame, text="Close", style="secondary", width=100,
                                   command=history_window.destroy).pack(side="right")

    def send_whatsapp_notification():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Select a customer to send a notification.")
            return
        item = tree.item(selected_item[0])
        values = item["values"]
        name = values[0]
        if name == "—":
            messagebox.showerror("Error", "Select a valid customer.")
            return

        phone = str(values[1])
        installment_date = values[2]
        installment_value = values[3]
        if not phone.startswith("+"):
            phone = "+" + phone

        preview_window = CTkToplevel(app)
        preview_window.geometry("520x620")
        preview_window.title("Message Preview")
        preview_window.transient(app)
        preview_window.grab_set()

        main_frame = StyleManager.create_frame(preview_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        StyleManager.create_label(main_frame, text="Message Preview", font_style="subheading").pack(pady=(0, 6))
        StyleManager.create_label(main_frame, text=f"Send WhatsApp reminder to {name}", font_style="small",
                                  text_color=StyleManager.COLORS["text_muted"]).pack(pady=(0, 20))

        template = settings.get("reminder_template",
                                "Hello {name},\nThis is a reminder for an installment payment of {value} SAR due on {date}.\nThank you for your business.")
        message_text = StyleManager.create_textbox(main_frame, width=460, height=140, readonly=False,
                                                   fg_color=StyleManager.COLORS["surface_high"], font=StyleManager.FONTS["body"])
        message_text.pack(pady=(0, 10))
        message_text.insert("end", template)

        tmpl_frame = StyleManager.create_frame(main_frame)
        tmpl_frame.pack(fill="x", pady=(0, 16))
        StyleManager.create_label(tmpl_frame, text="Template variables:  {name}  {date}  {value}",
                                  font_style="small", text_color=StyleManager.COLORS["text_muted"]).pack(anchor="w")

        button_frame = StyleManager.create_frame(main_frame)
        button_frame.pack(fill="x")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        left = StyleManager.create_frame(button_frame, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        right = StyleManager.create_frame(button_frame, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")

        def send_message():
            try:
                custom_message = message_text.get("1.0", "end-1c")
                message = custom_message.replace("{name}", name).replace("{date}", installment_date).replace("{value}", str(installment_value))
                cid = csv_repository.get_customer_id_by_name(name)
                reminder_id = reminder_service.save_reminder(
                    customer_id=cid or 0, customer_name=name, phone=phone,
                    installment_date=installment_date, amount=float(installment_value),
                    message=message, status="sent",
                )
                activity_service.log("Reminder generated", customer_id=cid, detail=f"{name} — {installment_date}")
                if NotificationService.open_whatsapp(phone, message):
                    messagebox.showinfo("Success", f"WhatsApp opened for {name}. Press Send manually.")
                    preview_window.destroy()
                    load_data()
                else:
                    messagebox.showerror("Error", "Failed to open WhatsApp Web.")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
                logging.error(f"Error in send_message: {str(e)}")

        StyleManager.create_button(left, text="Open WhatsApp", width=160, command=send_message).pack(side="left", pady=10)
        StyleManager.create_button(right, text="Cancel", style="secondary", width=120,
                                   command=preview_window.destroy).pack(side="right", pady=10)

    StyleManager.create_button(left_side, text="Refresh Data", width=140, command=load_data).pack(side="left", padx=(0, 10), pady=10)
    StyleManager.create_button(left_side, text="Send Notification", width=160, command=send_whatsapp_notification).pack(side="left", padx=(0, 10), pady=10)
    StyleManager.create_button(left_side, text="History", width=100, command=show_reminder_history).pack(side="left", padx=(0, 10), pady=10)
    StyleManager.create_button(right_side, text="Back", style="secondary", width=120,
                               command=lambda: show_frame(frames["home"])).pack(side="right", pady=10)
