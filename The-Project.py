import customtkinter
from customtkinter import *
from tkinter import messagebox, ttk
import re
import csv
import os
import pandas as pd
from datetime import datetime, timedelta
from tkcalendar import Calendar

# إنشاء النافذة الرئيسية
app = CTk()
app.geometry("900x600")  # تكبير النافذة

def refresh_treeview(tree):
    """Clear and reload data in the Treeview."""
    for row in tree.get_children():
        tree.delete(row)  # Clear existing rows

    df = read_csv_safely()
    
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))  # Add new rows

def show_frame(frame):
    """Show the selected frame and refresh the view page if it's the view frame."""
    frame.tkraise()
    if frame == frames["view"] and hasattr(frame, 'tree'):
        refresh_treeview(frame.tree)

container = CTkFrame(app)
container.pack(fill="both", expand=True)

frames = {}
page_names = ["home", "add", "delete", "edit", "view"]
for name in page_names:
    frame = CTkFrame(container)
    frame.grid(row=0, column=0, sticky="nsew")
    frames[name] = frame

container.grid_columnconfigure(0, weight=1)
container.grid_rowconfigure(0, weight=1)

csv_filename = "customers.csv"
excel_filename = "customers.xlsx"

# Ensure CSV file exists
if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Phone", "Amount", "Installments", "Installment Value", "Start Date", "Installment Dates"])

# Ensure Excel file exists
if not os.path.exists(excel_filename):
    pd.DataFrame(columns=["Name", "Phone", "Amount", "Installments", "Installment Value", "Start Date", "Installment Dates"]).to_excel(excel_filename, index=False)

def read_csv_safely():
    try:
        df = pd.read_csv(csv_filename, on_bad_lines='skip')
        return df
    except pd.errors.ParserError:
        messagebox.showerror("خطأ", "حدثت مشكلة في قراءة ملف العملاء.")
        return pd.DataFrame()
    except FileNotFoundError:
        messagebox.showerror("خطأ", "ملف العملاء غير موجود.")
        return pd.DataFrame()

class DatePicker(CTkToplevel):
    """Popup calendar to select a date."""
    def __init__(self, parent, entry_widget):
        super().__init__(parent)
        self.entry_widget = entry_widget
        self.geometry("300x300")
        self.title("اختر التاريخ")

        self.cal = Calendar(self, selectmode="day", date_pattern="yyyy-mm-dd")
        self.cal.pack(pady=20)

        select_button = CTkButton(self, text="تحديد", command=self.select_date)
        select_button.pack(pady=10)

    def select_date(self):
        self.entry_widget.delete(0, "end")
        self.entry_widget.insert(0, self.cal.get_date())
        self.destroy()

def validate_and_save(name_entry, phone_entry, amount_entry, installments_entry, start_date_entry):
    name = name_entry.get().strip()
    phone = phone_entry.get().strip()
    amount = amount_entry.get().strip()
    installments = installments_entry.get().strip()
    start_date = start_date_entry.get().strip()

    # Validation patterns
    name_pattern = r"^[A-Za-z؀-ۿ\s]+$"
    phone_pattern = r"^\+?\d{10,15}$"
    amount_pattern = r"^\d+(\.\d{1,2})?$"
    installments_pattern = r"^\d+$"

    if not re.fullmatch(name_pattern, name):
        messagebox.showerror("خطأ", "الاسم يجب أن يحتوي فقط على أحرف ومسافات.")
        return

    if not re.fullmatch(phone_pattern, phone):
        messagebox.showerror("خطأ", "رقم الهاتف يجب أن يحتوي على أرقام فقط.")
        return

    if not re.fullmatch(amount_pattern, amount):
        messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقمًا صالحًا.")
        return

    if not re.fullmatch(installments_pattern, installments):
        messagebox.showerror("خطأ", "عدد الأقساط يجب أن يكون رقمًا صحيحًا.")
        return

    amount = float(amount)
    installments = int(installments)
    installment_value = round(amount / installments, 2)

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("خطأ", "تاريخ بدء الأقساط غير صحيح. يجب أن يكون بالصيغة YYYY-MM-DD.")
        return

    installment_dates = [(start_date_obj + timedelta(days=30 * i)).strftime("%Y-%m-%d") for i in range(installments)]
    file_is_empty = os.stat(csv_filename).st_size == 0
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if file_is_empty:
            writer.writerow(["Name", "Phone", "Amount", "Installments", "Installment Value", "Start Date", "Installment Dates"])
        writer.writerow([name, phone, amount, installments, installment_value, start_date, ";".join(installment_dates)])

    # Re-read the CSV file into a DataFrame
    df = read_csv_safely()

    # Save the updated DataFrame to Excel
    try:
        df.to_excel(excel_filename, index=False)
        messagebox.showinfo("نجاح", "تم حفظ العميل بنجاح!")

        # Clear the input fields
        name_entry.delete(0, "end")
        phone_entry.delete(0, "end")
        amount_entry.delete(0, "end")
        installments_entry.delete(0, "end")
        start_date_entry.delete(0, "end")
    except Exception as e:
        messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ البيانات في ملف Excel: {e}")


def setup_add_page():
    frame = frames["add"]
    frame.grid_columnconfigure(0, weight=1)

    CTkLabel(frame, text="إضافة عميل جديد", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=20, sticky="n")

    labels = ["اسم العميل:", "رقم الهاتف:", "المبلغ:", "عدد الأقساط:"]
    entries = []

    for i, label_text in enumerate(labels):
        CTkLabel(frame, text=label_text, font=("Arial", 14)).grid(row=i*2+1, column=0, pady=5, padx=20, sticky="w")
        entry = CTkEntry(frame, width=250)
        entry.grid(row=i*2+2, column=0, pady=5, padx=20)
        entries.append(entry)

    # Date Picker Section
    CTkLabel(frame, text="تاريخ بدء الأقساط:", font=("Arial", 14)).grid(row=9, column=0, pady=5, padx=20, sticky="w")
    start_date_entry = CTkEntry(frame, width=200)
    start_date_entry.grid(row=10, column=0, pady=5, padx=20)
    CTkButton(frame, text="📅 اختر التاريخ", command=lambda: DatePicker(app, start_date_entry)).grid(row=10, column=1, pady=5, padx=10)

    # Save Button
    CTkButton(frame, text="حفظ العميل", width=250, height=50, font=("Arial", 16, "bold"),
              command=lambda: validate_and_save(*entries, start_date_entry)).grid(row=11, column=0, pady=20)

    CTkButton(frame, text="رجوع", width=250, height=50, font=("Arial", 16, "bold"),
          command=lambda: show_frame(frames["home"])).grid(row=12, column=0, pady=10)

def setup_view_page():
    frame = frames["view"]
    frame.grid_columnconfigure(0, weight=1)

    CTkLabel(frame, text="عرض العملاء", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=20, sticky="n")

    # Create a Treeview widget
    tree = ttk.Treeview(frame, columns=("Name", "Phone", "Amount", "Installments", "Installment Value", "Start Date", "Installment Dates"), show="headings")
    
    # Set column widths and headings
    tree.column("Name", width=150, anchor="center")
    tree.column("Phone", width=120, anchor="center")
    tree.column("Amount", width=100, anchor="center")
    tree.column("Installments", width=100, anchor="center")
    tree.column("Installment Value", width=120, anchor="center")
    tree.column("Start Date", width=120, anchor="center")
    tree.column("Installment Dates", width=200, anchor="center")

    tree.heading("Name", text="اسم العميل")
    tree.heading("Phone", text="رقم الهاتف")
    tree.heading("Amount", text="المبلغ")
    tree.heading("Installments", text="عدد الأقساط")
    tree.heading("Installment Value", text="قيمة القسط")
    tree.heading("Start Date", text="تاريخ البدء")
    tree.heading("Installment Dates", text="تواريخ الأقساط")

    tree.grid(row=1, column=0, pady=10, padx=10, sticky="nsew")

    # Add a scrollbar
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar.grid(row=1, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)

    # Store the Treeview widget as an attribute of the frame
    frame.tree = tree

    # Refresh the Treeview with the latest data
    refresh_treeview(tree)

    # Refresh button
    refresh_button = CTkButton(frame, text="تحديث", width=250, height=50, font=("Arial", 16, "bold"),
                               command=lambda: refresh_treeview(tree))
    refresh_button.grid(row=2, column=0, pady=10, padx=20, sticky="ew")

    # Back button
    back_button = CTkButton(frame, text="العودة", width=250, height=50, font=("Arial", 16, "bold"),
                            command=lambda: show_frame(frames["home"]))
    back_button.grid(row=3, column=0, pady=10, padx=20, sticky="ew")

def setup_home_page():
    frame = frames["home"]
    frame.grid_columnconfigure(0, weight=1)

    CTkLabel(frame, text="الصفحة الرئيسية", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=20, sticky="n")

    CTkButton(frame, text="إضافة عميل", width=250, height=50, font=("Arial", 16, "bold"),
              command=lambda: show_frame(frames["add"])).grid(row=1, column=0, pady=10)
    CTkButton(frame, text="عرض العملاء", width=250, height=50, font=("Arial", 16, "bold"),
          command=lambda: show_frame(frames["view"])).grid(row=2, column=0, pady=10)


setup_home_page()
setup_add_page()
setup_view_page()
show_frame(frames["home"])
app.mainloop()