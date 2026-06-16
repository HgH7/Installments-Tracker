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
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=0)
    frame.grid_rowconfigure(1, weight=0)
    frame.grid_rowconfigure(2, weight=1)
    frame.grid_rowconfigure(3, weight=0)

    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 15))
    header_frame.grid_columnconfigure(0, weight=1)

    StyleManager.create_label(
        header_frame,
        text="عرض العملاء",
        font_style="heading"
    ).grid(row=0, column=0, pady=(5, 5), sticky="w")

    search_frame = StyleManager.create_frame(frame)
    search_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 15))
    search_frame.grid_columnconfigure(1, weight=1)

    StyleManager.create_label(
        search_frame,
        text="بحث:",
        font_style="body_bold"
    ).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")

    search_entry = StyleManager.create_entry(
        search_frame,
        width=400,
        font=("Arial", 14),
        height=35,
        placeholder_text="أدخل اسم العميل أو رقم الهاتف..."
    )
    search_entry.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ew")

    def perform_search():
        query = search_entry.get().strip()
        results = customer_service.search_customers(query)
        refresh_treeview(frame.tree, results)
        status_label.configure(text=f"العملاء: {len(results)}")

    search_entry.bind("<Return>", lambda event: perform_search())

    search_button = StyleManager.create_button(
        search_frame,
        text="بحث",
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
    table_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 20))
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)

    style = ttk.Style()
    style.configure(
        "Custom.Treeview",
        rowheight=40,
        font=("Arial", 12),
        background=StyleManager.COLORS["surface"],
        foreground=StyleManager.COLORS["text"],
        fieldbackground=StyleManager.COLORS["surface"]
    )
    style.configure(
        "Custom.Treeview.Heading",
        font=("Arial", 12, "bold"),
        background=StyleManager.COLORS["primary"],
        foreground=StyleManager.COLORS["text"]
    )
    style.map(
        "Custom.Treeview",
        background=[("selected", StyleManager.COLORS["primary"])],
        foreground=[("selected", StyleManager.COLORS["text"])]
    )

    column_headers = {
        "Name": "اسم العميل",
        "Phone": "رقم الهاتف",
        "Amount": "المبلغ",
        "Installments": "عدد الأقساط",
        "Installment Value": "قيمة القسط",
        "Start Date": "تاريخ البدء"
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
    status_label.configure(text=f"العملاء: {len(data)}")

    def edit_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد عميل للتعديل.")
            return

        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]

        customer = customer_service.get_customer_by_name(customer_name)
        if not customer:
            messagebox.showerror("خطأ", "لم يتم العثور على بيانات العميل.")
            return

        edit_window = CTkToplevel(app)
        edit_window.geometry("800x600")
        edit_window.title(f"تعديل بيانات العميل: {customer_name}")

        StyleManager.create_label(
            edit_window,
            text=f"تعديل بيانات العميل: {customer_name}",
            font_style="heading"
        ).pack(pady=(20, 10))

        form_frame = StyleManager.create_frame(edit_window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        fields = [
            {"label": "اسم العميل:", "key": "Name", "type": "text"},
            {"label": "رقم الهاتف:", "key": "Phone", "type": "phone"},
            {"label": "المبلغ:", "key": "Amount", "type": "number"},
            {"label": "عدد الأقساط:", "key": "Installments", "type": "number"}
        ]

        entries = {}

        for field in fields:
            field_frame = StyleManager.create_frame(form_frame)
            field_frame.pack(fill="x", padx=10, pady=10)
            field_frame.grid_columnconfigure(1, weight=1)

            StyleManager.create_label(
                field_frame,
                text=field["label"],
                font_style="body_bold"
            ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

            entry = StyleManager.create_entry(field_frame, width=300)
            entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
            entry.insert(0, str(customer.get(field["key"], "")))
            entries[field["key"]] = entry

        date_frame = StyleManager.create_frame(form_frame)
        date_frame.pack(fill="x", padx=10, pady=10)
        date_frame.grid_columnconfigure(1, weight=1)

        StyleManager.create_label(
            date_frame,
            text="تاريخ بدء الأقساط:",
            font_style="body_bold"
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        start_date_entry = StyleManager.create_entry(date_frame, width=200)
        start_date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        start_date_entry.insert(0, str(customer.get("Start Date", "")))
        entries["Start Date"] = start_date_entry

        date_picker_btn = StyleManager.create_button(
            date_frame,
            text="اختر التاريخ",
            style="secondary",
            command=lambda: DatePicker(edit_window, start_date_entry)
        )
        date_picker_btn.grid(row=0, column=2, padx=10, pady=5)

        buttons_frame = StyleManager.create_frame(edit_window)
        buttons_frame.pack(fill="x", padx=20, pady=20)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        def save_changes():
            name_pattern = r"^[A-Za-z؀-ۿ\s]+$"
            phone_pattern = r"^\+?\d{10,15}$"
            amount_pattern = r"^\d+(\.\d{1,2})?$"
            installments_pattern = r"^\d+$"

            name = entries["Name"].get().strip()
            phone = entries["Phone"].get().strip()
            amount = entries["Amount"].get().strip()
            installments = entries["Installments"].get().strip()
            start_date = entries["Start Date"].get().strip()

            if not re.fullmatch(name_pattern, name):
                messagebox.showerror("خطأ", "الاسم يجب أن يحتوي فقط على أحرف ومسافات.")
                return

            if not re.fullmatch(phone_pattern, phone):
                messagebox.showerror("خطأ", "رقم الهاتف يجب أن يحتوي على أرقام فقط ويبدأ بـ +.")
                return

            if not re.fullmatch(amount_pattern, amount):
                messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقمًا صالحًا.")
                return

            if not re.fullmatch(installments_pattern, installments):
                messagebox.showerror("خطأ", "عدد الأقساط يجب أن يكون رقمًا صحيحًا.")
                return

            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("خطأ", "تنسيق التاريخ غير صحيح. يجب أن يكون بهذا الشكل: YYYY-MM-DD")
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
                        messagebox.showinfo("نجاح", "تم تحديث بيانات العميل بنجاح!")
                        edit_window.destroy()
                        refresh_treeview(tree)
                        refresh_payment_history_views()
                    else:
                        messagebox.showerror("خطأ", "فشل في تحديث بيانات العميل.")
                else:
                    if customer_service.update_customer(customer_name, updated_data):
                        messagebox.showinfo("نجاح", "تم تحديث بيانات العميل بنجاح!")
                        edit_window.destroy()
                        refresh_treeview(tree)
                        refresh_payment_history_views()
                    else:
                        messagebox.showerror("خطأ", "فشل في تحديث بيانات العميل.")

            except ValueError as e:
                messagebox.showerror("خطأ", f"خطأ في البيانات المدخلة: {str(e)}")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")

        StyleManager.create_button(
            buttons_frame,
            text="حفظ التغييرات",
            width=200,
            command=save_changes
        ).grid(row=0, column=0, padx=10, pady=10)

        StyleManager.create_button(
            buttons_frame,
            text="إلغاء",
            style="secondary",
            width=200,
            command=edit_window.destroy
        ).grid(row=0, column=1, padx=10, pady=10)

        edit_window.transient(app)
        edit_window.grab_set()
        edit_window.focus_set()

    def delete_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد عميل للحذف.")
            return

        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]

        if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف العميل {customer_name}؟\nلا يمكن التراجع عن هذه العملية."):
            if customer_service.delete_customer(customer_name):
                messagebox.showinfo("نجاح", f"تم حذف العميل {customer_name} بنجاح.")
                refresh_treeview(tree)
            else:
                messagebox.showerror("خطأ", "فشل في حذف العميل.")

    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 30))
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)

    left_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    left_buttons.grid(row=0, column=0, sticky="w")

    right_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    right_buttons.grid(row=0, column=1, sticky="e")

    refresh_btn = StyleManager.create_button(
        left_buttons,
        text="تحديث",
        width=120,
        command=lambda: refresh_treeview(tree)
    )
    refresh_btn.pack(side="left", padx=(0, 10), pady=10)

    history_btn = StyleManager.create_button(
        left_buttons,
        text="سجل الدفع",
        width=120,
        command=show_payment_history
    )
    history_btn.pack(side="left", padx=(0, 10), pady=10)

    export_btn = StyleManager.create_button(
        left_buttons,
        text="تصدير Excel",
        width=120,
        command=export_to_excel
    )
    export_btn.pack(side="left", padx=(0, 10), pady=10)

    back_btn = StyleManager.create_button(
        right_buttons,
        text="العودة",
        style="secondary",
        width=120,
        command=lambda: show_frame(frames["home"])
    )
    back_btn.pack(side="right", padx=(0, 0), pady=10)

    delete_btn = StyleManager.create_button(
        right_buttons,
        text="حذف العميل",
        style="danger",
        width=120,
        command=delete_customer
    )
    delete_btn.pack(side="right", padx=(0, 10), pady=10)

    edit_btn = StyleManager.create_button(
        right_buttons,
        text="تعديل العميل",
        width=120,
        command=edit_customer
    )
    edit_btn.pack(side="right", padx=(0, 10), pady=10)
