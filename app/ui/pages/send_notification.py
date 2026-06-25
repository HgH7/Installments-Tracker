import logging
import time
from datetime import datetime
from tkinter import messagebox, StringVar, BooleanVar, ttk
from customtkinter import CTkToplevel
import pywhatkit as kit


def setup_send_notification_page(frames, StyleManager, csv_repository, show_frame, app):
    frame = frames["send_notification"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    header_frame = StyleManager.create_section_header(
        frame,
        "Notifications",
        "Send installment reminders to customers through WhatsApp.",
    )
    header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))

    table_frame = StyleManager.create_frame(frame)
    table_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)

    columns = ("Name", "Phone", "Installment Date", "Installment Value")
    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        style="Custom.Treeview"
    )

    column_widths = {
        "Name": 150,
        "Phone": 120,
        "Installment Date": 120,
        "Installment Value": 120
    }

    column_headers = {
        "Name": "Customer Name",
        "Phone": "Phone",
        "Installment Date": "Installment Date",
        "Installment Value": "Installment Value"
    }

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

        for customer in data:
            installment_dates = customer.get("Installment Dates", "").split(";")
            for date in installment_dates:
                try:
                    date_obj = datetime.strptime(date.strip(), "%Y-%m-%d").date()
                except ValueError:
                    continue
                if date_obj >= today:
                    tree.insert("", "end", values=(
                        customer.get("Name", ""),
                        customer.get("Phone", ""),
                        date,
                        customer.get("Installment Value", "")
                    ))

        tree.tag_configure("sent", foreground=StyleManager.COLORS["success"])

    load_data()

    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)

    left_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    left_side.grid(row=0, column=0, sticky="w")
    right_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    right_side.grid(row=0, column=1, sticky="e")

    def send_whatsapp_notification():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Select a customer to send a notification.")
            return

        item = tree.item(selected_item[0])
        values = item["values"]
        name = values[0]
        phone = str(values[1])
        installment_date = values[2]
        installment_value = values[3]

        if not phone.startswith("+"):
            phone = "+" + phone

        preview_window = CTkToplevel(app)
        preview_window.geometry("520x560")
        preview_window.title("Message Preview")
        preview_window.transient(app)
        preview_window.grab_set()

        main_frame = StyleManager.create_frame(preview_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        StyleManager.create_label(
            main_frame,
            text="Message Preview",
            font_style="subheading"
        ).pack(pady=(0, 6))

        StyleManager.create_label(
            main_frame,
            text=f"Send WhatsApp reminder to {name}",
            font_style="small",
            text_color=StyleManager.COLORS["text_muted"]
        ).pack(pady=(0, 20))

        message_text = StyleManager.create_textbox(
            main_frame, width=460, height=140, readonly=False,
            fg_color=StyleManager.COLORS["surface_high"], font=StyleManager.FONTS["body"],
        )
        message_text.pack(pady=(0, 10))
        default_message = (
            f"Hello {name},\n"
            f"This is a reminder for an installment payment of {installment_value} SAR due on {installment_date}.\n"
            f"Thank you for your business."
        )
        message_text.insert("end", default_message)

        template_frame = StyleManager.create_frame(main_frame)
        template_frame.pack(fill="x", pady=(0, 16))

        StyleManager.create_label(
            template_frame,
            text="Template variables:  {name}  {date}  {value}",
            font_style="small",
            text_color=StyleManager.COLORS["text_muted"]
        ).pack(anchor="w")

        options_frame = StyleManager.create_frame(main_frame)
        options_frame.pack(fill="x", pady=(0, 16))

        retry_var = BooleanVar(value=True)
        retry_check = StyleManager.create_checkbox(
            options_frame, text="Retry if sending fails", variable=retry_var,
        )
        retry_check.pack(side="left", padx=(0, 20))

        StyleManager.create_label(
            options_frame,
            text="Attempts:",
            font_style="body"
        ).pack(side="left", padx=(0, 8))

        retry_count_var = StringVar(value="3")
        retry_count_entry = StyleManager.create_entry(
            options_frame,
            width=60,
            height=32,
            textvariable=retry_count_var
        )
        retry_count_entry.pack(side="left")

        status_label = StyleManager.create_label(
            main_frame,
            text="",
            font_style="small",
            text_color=StyleManager.COLORS["text_muted"]
        )
        status_label.pack(pady=(0, 12))

        button_frame = StyleManager.create_frame(main_frame)
        button_frame.pack(fill="x")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        left_side = StyleManager.create_frame(button_frame, fg_color="transparent")
        left_side.grid(row=0, column=0, sticky="w")
        right_side = StyleManager.create_frame(button_frame, fg_color="transparent")
        right_side.grid(row=0, column=1, sticky="e")

        def send_message():
            try:
                custom_message = message_text.get("1.0", "end-1c")
                message = custom_message.replace("{name}", name).replace("{date}", installment_date).replace("{value}", str(installment_value))
                should_retry = retry_var.get()
                max_retries = 1
                try:
                    max_retries = int(retry_count_var.get())
                    if max_retries < 1:
                        max_retries = 1
                except ValueError:
                    max_retries = 3

                for widget in button_frame.winfo_children():
                    widget.configure(state="disabled")

                attempts = 0
                success = False
                window_exists = True
                errors = []

                while attempts < max_retries and not success and window_exists:
                    attempts += 1
                    try:
                        if window_exists:
                            status_label.configure(text=f"Sending... attempt {attempts}/{max_retries}")
                            preview_window.update()

                        try:
                            kit.sendwhatmsg_instantly(
                                phone_no=phone,
                                message=message,
                                wait_time=15,
                                tab_close=True,
                                close_time=10
                            )
                        except Exception as e:
                            raise Exception(f"Failed to send message: {str(e)}")

                        data = csv_repository.read_data()
                        updated = False
                        for customer in data:
                            if customer.get("Name") == name:
                                customer["Notification Sent"] = True
                                updated = True
                                break

                        if updated and csv_repository.save_data(data):
                            success = True
                            if window_exists:
                                status_label.configure(text="Sent successfully.")
                                messagebox.showinfo("Success", f"Notification sent to {name} successfully.")
                                preview_window.destroy()
                                window_exists = False
                            load_data()
                            logging.info(f"Manual notification sent to {name} at {phone}")
                        else:
                            errors.append("Failed to update notification status.")
                    except Exception as e:
                        errors.append(str(e))
                        logging.error(f"Error in send_message attempt {attempts}: {str(e)}")
                        if attempts < max_retries and should_retry:
                            time.sleep(5)

                if not success:
                    error_message = "\n".join(errors)
                    messagebox.showerror("Error", f"Failed to send notification:\n{error_message}")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
                logging.error(f"Unexpected error in send_message: {str(e)}")
                try:
                    for widget in button_frame.winfo_children():
                        widget.configure(state="normal")
                except Exception:
                    pass

        StyleManager.create_button(
            left_side,
            text="Send",
            width=160,
            command=send_message
        ).pack(side="left", pady=10)

        StyleManager.create_button(
            right_side,
            text="Cancel",
            style="secondary",
            width=120,
            command=preview_window.destroy
        ).pack(side="right", pady=10)

    StyleManager.create_button(
        left_side,
        text="Refresh Data",
        width=140,
        command=load_data
    ).pack(side="left", padx=(0, 10), pady=10)

    StyleManager.create_button(
        left_side,
        text="Send Notification",
        width=160,
        command=send_whatsapp_notification
    ).pack(side="left", padx=(0, 10), pady=10)

    StyleManager.create_button(
        right_side,
        text="Back",
        style="secondary",
        width=120,
        command=lambda: show_frame(frames["home"])
    ).pack(side="right", pady=10)
