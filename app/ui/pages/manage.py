import logging
import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from customtkinter import CTkToplevel, CTkButton, CTkCheckBox


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
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=0)
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_rowconfigure(2, weight=0)

    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 20))
    header_frame.grid_columnconfigure(0, weight=1)

    StyleManager.create_label(
        header_frame,
        text="إدارة الأقساط",
        font_style="heading"
    ).grid(row=0, column=0, pady=(0, 10), sticky="w")

    StyleManager.create_label(
        header_frame,
        text="عرض الأقساط الحالية وإدارتها بسهولة",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, pady=(0, 20), sticky="w")

    table_frame = StyleManager.create_frame(frame)
    table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
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
        "Name": "اسم العميل",
        "Phone": "رقم الهاتف",
        "Amount": "المبلغ",
        "Installments": "عدد الأقساط",
        "Installment Value": "قيمة القسط",
        "Next Due": "القسط التالي",
        "Paid": "مدفوع"
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
                paid_installments = eval(customer.get("Paid_Installments", "[]"))
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

                is_paid = "نعم" if len(paid_installments) == total_installments and total_installments > 0 else "لا"
                item = tree.insert("", "end", values=(
                    customer.get("Name", ""),
                    customer.get("Phone", ""),
                    customer.get("Amount", ""),
                    total_installments,
                    customer.get("Installment Value", ""),
                    next_due,
                    is_paid
                ))

                if is_paid == "نعم":
                    tree.item(item, tags=("paid",))
                else:
                    tree.item(item, tags=("unpaid",))

            tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
            tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
        except Exception as e:
            logging.error(f"Error loading installments data: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء تحميل البيانات.")

    load_data()

    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)
    buttons_frame.grid_columnconfigure(2, weight=1)
    buttons_frame.grid_columnconfigure(3, weight=1)

    def refresh_installments():
        load_data()
        messagebox.showinfo("نجاح", "تم تحديث البيانات بنجاح.")

    StyleManager.create_button(
        buttons_frame,
        text="تحديث البيانات",
        width=200,
        command=refresh_installments
    ).grid(row=0, column=0, padx=10, pady=10)

    def mark_as_paid():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد قسط لتمييزه كمُدفوع.")
            return

        try:
            for item in selected_items:
                if "header" in tree.item(item)["tags"]:
                    continue

                values = tree.item(item)["values"]
                parent = tree.parent(item)
                customer_name = tree.item(parent)["values"][0].replace("▼ ", "").replace("▶ ", "")
                installment_date = values[5]

                if customer_service.mark_installment_as_paid(customer_name, installment_date):
                    tree.set(item, "Paid", "نعم")
                    tree.item(item, tags=("paid",))
                else:
                    messagebox.showerror("خطأ", f"فشل في تمييز القسط كمدفوع للعميل {customer_name}")
                    return

            messagebox.showinfo("نجاح", "تم تمييز الأقساط المحددة كمُدفوعة.")
            load_data()
            if "view" in frames:
                refresh_treeview(frames["view"].tree)
        except Exception as e:
            logging.error(f"Error marking installments as paid: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء تمييز الأقساط كمدفوعة.")

    StyleManager.create_button(
        buttons_frame,
        text="تمييز كمُدفوع",
        width=200,
        command=mark_as_paid
    ).grid(row=0, column=1, padx=10, pady=10)

    def edit_installment():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد قسط للتعديل.")
            return

        if len(selected_items) > 1:
            messagebox.showerror("خطأ", "يرجى تحديد قسط واحد فقط للتعديل.")
            return

        try:
            item = selected_items[0]
            if "header" in tree.item(item)["tags"]:
                messagebox.showerror("خطأ", "يرجى تحديد قسط للتعديل.")
                return

            values = tree.item(item)["values"]
            parent = tree.parent(item)
            customer_name = tree.item(parent)["values"][0].replace("▼ ", "").replace("▶ ", "")
            customer_phone = tree.item(parent)["values"][1]
            installment_date = values[5]
            installment_value = values[4]
            is_paid = values[6] == "نعم"

            edit_window = CTkToplevel(app)
            edit_window.geometry("500x450")
            edit_window.title("تعديل القسط")
            edit_window.transient(app)
            edit_window.grab_set()

            main_frame = StyleManager.create_frame(edit_window)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            StyleManager.create_label(
                main_frame,
                text="تعديل بيانات القسط",
                font_style="subheading"
            ).pack(pady=(0, 20))

            info_frame = StyleManager.create_frame(main_frame)
            info_frame.pack(fill="x", pady=10)

            StyleManager.create_label(
                info_frame,
                text=f"العميل: {customer_name}",
                font_style="body_bold"
            ).pack(anchor="w")

            StyleManager.create_label(
                info_frame,
                text=f"رقم الهاتف: {customer_phone}",
                font_style="body"
            ).pack(anchor="w")

            fields_frame = StyleManager.create_frame(main_frame)
            fields_frame.pack(fill="x", pady=20)

            date_frame = StyleManager.create_frame(fields_frame)
            date_frame.pack(fill="x", pady=10)

            StyleManager.create_label(
                date_frame,
                text="تاريخ القسط:",
                font_style="body"
            ).pack(side="left", padx=(0, 10))

            date_entry = StyleManager.create_entry(date_frame)
            date_entry.pack(side="left", fill="x", expand=True)
            date_entry.insert(0, installment_date)

            def open_date_picker():
                DatePicker(edit_window, date_entry)

            date_picker_btn = StyleManager.create_button(
                date_frame,
                text="📅",
                width=40,
                command=open_date_picker
            )
            date_picker_btn.pack(side="left", padx=(10, 0))

            amount_frame = StyleManager.create_frame(fields_frame)
            amount_frame.pack(fill="x", pady=10)

            StyleManager.create_label(
                amount_frame,
                text="قيمة القسط:",
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
                text="مدفوع",
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
                        messagebox.showerror("خطأ", "تنسيق التاريخ غير صحيح. يجب أن يكون بهذا الشكل: YYYY-MM-DD")
                        return

                    if not re.match(r"^\d+(\.\d{1,2})?$", new_value_str):
                        messagebox.showerror("خطأ", "قيمة القسط يجب أن تكون رقمًا صالحًا.")
                        return

                    new_value = float(new_value_str)

                    if customer_service.update_installment(customer_name, installment_date, new_date, new_value):
                        if is_paid != new_paid_status:
                            if new_paid_status:
                                customer_service.mark_installment_as_paid(customer_name, new_date)
                            else:
                                customer_service.unmark_installment_as_paid(customer_name, new_date)
                        messagebox.showinfo("نجاح", "تم تحديث بيانات القسط بنجاح.")
                        edit_window.destroy()
                        load_data()
                        refresh_payment_history_views()
                    else:
                        messagebox.showerror("خطأ", "فشل في تحديث بيانات القسط.")
                except Exception as e:
                    logging.error(f"Error saving installment changes: {str(e)}")
                    messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ التغييرات: {str(e)}")

            StyleManager.create_button(
                buttons_frame,
                text="حفظ التغييرات",
                width=200,
                command=save_changes
            ).grid(row=0, column=0, padx=5, pady=5)

            StyleManager.create_button(
                buttons_frame,
                text="إلغاء",
                width=200,
                style="secondary",
                command=edit_window.destroy
            ).grid(row=0, column=1, padx=5, pady=5)
        except Exception as e:
            logging.error(f"Error opening edit installment window: {str(e)}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء فتح نافذة التعديل: {str(e)}")

    StyleManager.create_button(
        buttons_frame,
        text="تعديل القسط",
        width=200,
        command=edit_installment
    ).grid(row=0, column=2, padx=10, pady=10)

    def delete_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد عميل للحذف.")
            return

        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]

        if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف العميل {customer_name}?\nلا يمكن التراجع عن هذه العملية."):
            if customer_service.delete_customer(customer_name):
                messagebox.showinfo("نجاح", f"تم حذف العميل {customer_name} بنجاح.")
                refresh_treeview(tree)
            else:
                messagebox.showerror("خطأ", "فشل في حذف العميل.")

    StyleManager.create_button(
        buttons_frame,
        text="حذف العميل",
        style="danger",
        width=200,
        command=delete_customer
    ).grid(row=0, column=3, padx=10, pady=10)

    StyleManager.create_button(
        buttons_frame,
        text="العودة",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    ).grid(row=0, column=4, padx=10, pady=10)
