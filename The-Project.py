import customtkinter
from customtkinter import *
from tkinter import messagebox, ttk
import re
import csv
import os
import pandas as pd
from datetime import datetime, timedelta
from tkcalendar import Calendar
import shutil
import threading
import pywhatkit as kit

# إنشاء النافذة الرئيسية
app = CTk()
app.geometry("900x650")  # تكبير النافذة

# Enable dark mode
customtkinter.set_appearance_mode("dark")  # Options: "dark", "light", "system"

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
page_names = ["home", "add", "delete", "edit", "view", "manage_installments", "backup_restore"]
for name in page_names:
    frame = CTkFrame(container)
    frame.grid(row=0, column=0, sticky="nsew")
    frames[name] = frame

container.grid_columnconfigure(0, weight=1)
container.grid_rowconfigure(0, weight=1)

csv_filename = "customers.csv"
excel_filename = "customers.xlsx"
backup_folder = "backups"

# Ensure CSV file exists
if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Phone", "Amount", "Installments", "Installment Value", "Start Date", "Installment Dates"])

# Ensure Excel file exists
if not os.path.exists(excel_filename):
    pd.DataFrame(columns=["Name", "Phone", "Amount", "Installments", "Installment Value", "Start Date", "Installment Dates"]).to_excel(excel_filename, index=False)

# Ensure backup folder exists
if not os.path.exists(backup_folder):
    os.makedirs(backup_folder)

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

def save_to_csv_and_excel(df):
    """Save the DataFrame to both CSV and Excel files."""
    try:
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        df.to_excel(excel_filename, index=False)
    except Exception as e:
        messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ البيانات: {e}")

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
    save_to_csv_and_excel(df)
    messagebox.showinfo("نجاح", "تم حفظ العميل بنجاح!")

    # Clear the input fields
    name_entry.delete(0, "end")
    phone_entry.delete(0, "end")
    amount_entry.delete(0, "end")
    installments_entry.delete(0, "end")
    start_date_entry.delete(0, "end")

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

    # Search Bar
    search_frame = CTkFrame(frame)
    search_frame.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

    CTkLabel(search_frame, text="بحث:", font=("Arial", 14)).grid(row=0, column=0, padx=5)
    search_entry = CTkEntry(search_frame, width=300)
    search_entry.grid(row=0, column=1, padx=5)
    search_button = CTkButton(search_frame, text="بحث", width=100, command=lambda: search_customers(search_entry.get(), tree))
    search_button.grid(row=0, column=2, padx=5)

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

    tree.grid(row=2, column=0, pady=10, padx=10, sticky="nsew")

    # Add a scrollbar
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar.grid(row=2, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)

    # Store the Treeview widget as an attribute of the frame
    frame.tree = tree

    # Refresh the Treeview with the latest data
    refresh_treeview(tree)

    # Search Functionality
    def search_customers(query, tree):
        for row in tree.get_children():
            tree.delete(row)
        df = read_csv_safely()
        results = df[df.apply(lambda row: query.lower() in str(row).lower(), axis=1)]
        for _, row in results.iterrows():
            tree.insert("", "end", values=list(row))

    # Payment History Button
    def show_payment_history():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("خطأ", "يرجى تحديد عميل لعرض سجل الدفع.")
            return
        customer_name = tree.item(selected_item)["values"][0]
        df = read_csv_safely()
        customer_data = df[df["Name"] == customer_name]
        if customer_data.empty:
            messagebox.showerror("خطأ", "العميل غير موجود.")
            return
        installment_dates = customer_data.iloc[0]["Installment Dates"].split(";")
        history_window = CTkToplevel(app)
        history_window.geometry("400x300")
        history_window.title(f"سجل الدفع لـ {customer_name}")

        history_text = CTkTextbox(history_window, width=350, height=250)
        history_text.pack(pady=10)
        history_text.insert("end", "تواريخ الأقساط:\n")
        for date in installment_dates:
            history_text.insert("end", f"{date}\n")

    CTkButton(frame, text="عرض سجل الدفع", width=250, height=50, font=("Arial", 16, "bold"),
              command=show_payment_history).grid(row=3, column=0, pady=10, padx=20, sticky="ew")

    # Back button
    back_button = CTkButton(frame, text="العودة", width=250, height=50, font=("Arial", 16, "bold"),
                            command=lambda: show_frame(frames["home"]))
    back_button.grid(row=4, column=0, pady=10, padx=20, sticky="ew")

def setup_manage_installments_page():
    frame = frames["manage_installments"]
    frame.grid_columnconfigure(0, weight=1)

    CTkLabel(frame, text="إدارة الأقساط", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=20, sticky="n")

    # Create a Treeview widget
    tree = ttk.Treeview(frame, columns=("Name", "Phone", "Installment Date", "Installment Value", "Paid"), show="headings")
    
    # Set column widths and headings
    tree.column("Name", width=150, anchor="center")
    tree.column("Phone", width=120, anchor="center")
    tree.column("Installment Date", width=120, anchor="center")
    tree.column("Installment Value", width=120, anchor="center")
    tree.column("Paid", width=100, anchor="center")

    tree.heading("Name", text="اسم العميل")
    tree.heading("Phone", text="رقم الهاتف")
    tree.heading("Installment Date", text="تاريخ القسط")
    tree.heading("Installment Value", text="قيمة القسط")
    tree.heading("Paid", text="مدفوع")

    tree.grid(row=1, column=0, pady=10, padx=10, sticky="nsew")

    # Add a scrollbar
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar.grid(row=1, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)

    # Store the Treeview widget as an attribute of the frame
    frame.tree = tree

    # Load data into the Treeview
    def load_data():
        for row in tree.get_children():
            tree.delete(row)
        df = read_csv_safely()
        for _, row in df.iterrows():
            installment_dates = row["Installment Dates"].split(";")
            for date in installment_dates:
                tree.insert("", "end", values=(row["Name"], row["Phone"], date, row["Installment Value"], "لا"))

    load_data()

    # Refresh button
    def refresh_installments():
        load_data()
        messagebox.showinfo("نجاح", "تم تحديث البيانات بنجاح.")

    CTkButton(frame, text="تحديث", width=250, height=50, font=("Arial", 16, "bold"),
              command=refresh_installments).grid(row=2, column=0, pady=10, padx=20, sticky="ew")

    # Mark as paid button
    def mark_as_paid():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("خطأ", "يرجى تحديد قسط لتمييزه كمُدفوع.")
            return
        for item in selected_item:
            tree.set(item, "Paid", "نعم")
        messagebox.showinfo("نجاح", "تم تمييز الأقساط المحددة كمُدفوعة.")

    # Delete selected installments
    def delete_installments():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد أقساط لحذفها.")
            return
        for item in selected_items:
            tree.delete(item)
        messagebox.showinfo("نجاح", "تم حذف الأقساط المحددة.")

    # Edit installment details
    def edit_installment():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("خطأ", "يرجى تحديد قسط لتعديله.")
            return
        item = tree.item(selected_item)
        values = item["values"]

        # Create a popup window for editing
        edit_window = CTkToplevel(app)
        edit_window.geometry("400x300")
        edit_window.title("تعديل القسط")

        CTkLabel(edit_window, text="تاريخ القسط:", font=("Arial", 14)).grid(row=0, column=0, pady=5, padx=10, sticky="w")
        date_entry = CTkEntry(edit_window, width=200)
        date_entry.grid(row=0, column=1, pady=5, padx=10)
        date_entry.insert(0, values[2])

        CTkLabel(edit_window, text="قيمة القسط:", font=("Arial", 14)).grid(row=1, column=0, pady=5, padx=10, sticky="w")
        value_entry = CTkEntry(edit_window, width=200)
        value_entry.grid(row=1, column=1, pady=5, padx=10)
        value_entry.insert(0, values[3])

        CTkLabel(edit_window, text="حالة الدفع:", font=("Arial", 14)).grid(row=2, column=0, pady=5, padx=10, sticky="w")
        paid_var = StringVar(value=values[4])
        paid_menu = CTkOptionMenu(edit_window, variable=paid_var, values=["نعم", "لا"])
        paid_menu.grid(row=2, column=1, pady=5, padx=10)

        def save_changes():
            new_date = date_entry.get().strip()
            new_value = value_entry.get().strip()
            new_paid = paid_var.get()

            if not new_date or not new_value:
                messagebox.showerror("خطأ", "يرجى ملء جميع الحقول.")
                return

            tree.set(selected_item, column="Installment Date", value=new_date)
            tree.set(selected_item, column="Installment Value", value=new_value)
            tree.set(selected_item, column="Paid", value=new_paid)
            edit_window.destroy()
            messagebox.showinfo("نجاح", "تم تعديل القسط بنجاح.")

        CTkButton(edit_window, text="حفظ التعديلات", width=200, height=40, font=("Arial", 14, "bold"),
                  command=save_changes).grid(row=3, column=0, columnspan=2, pady=20)

    # Buttons
    CTkButton(frame, text="تمييز كمُدفوع", width=250, height=50, font=("Arial", 16, "bold"),
              command=mark_as_paid).grid(row=3, column=0, pady=10, padx=20, sticky="ew")
    CTkButton(frame, text="حذف الأقساط", width=250, height=50, font=("Arial", 16, "bold"),
              command=delete_installments).grid(row=4, column=0, pady=10, padx=20, sticky="ew")
    CTkButton(frame, text="تعديل القسط", width=250, height=50, font=("Arial", 16, "bold"),
              command=edit_installment).grid(row=5, column=0, pady=10, padx=20, sticky="ew")
    CTkButton(frame, text="العودة", width=250, height=50, font=("Arial", 16, "bold"),
              command=lambda: show_frame(frames["home"])).grid(row=6, column=0, pady=10, padx=20, sticky="ew")

def setup_backup_restore_page():
    frame = frames["backup_restore"]
    frame.grid_columnconfigure(0, weight=1)

    CTkLabel(frame, text="النسخ الاحتياطي واستعادة البيانات", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=20, sticky="n")

    # Backup Button
    def create_backup():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = os.path.join(backup_folder, f"backup_{timestamp}.csv")
        shutil.copy(csv_filename, backup_filename)
        messagebox.showinfo("نجاح", f"تم إنشاء نسخة احتياطية في: {backup_filename}")

    CTkButton(frame, text="إنشاء نسخة احتياطية", width=250, height=50, font=("Arial", 16, "bold"),
              command=create_backup).grid(row=1, column=0, pady=10, padx=20, sticky="ew")

    # Restore Button
    def restore_backup():
        backup_files = [f for f in os.listdir(backup_folder) if f.endswith(".csv")]
        if not backup_files:
            messagebox.showerror("خطأ", "لا توجد نسخ احتياطية.")
            return

        restore_window = CTkToplevel(app)
        restore_window.geometry("400x300")
        restore_window.title("استعادة نسخة احتياطية")

        CTkLabel(restore_window, text="اختر النسخة الاحتياطية:", font=("Arial", 14)).grid(row=0, column=0, pady=10, padx=10, sticky="w")
        backup_var = StringVar(value=backup_files[0])
        backup_menu = CTkOptionMenu(restore_window, variable=backup_var, values=backup_files)
        backup_menu.grid(row=0, column=1, pady=10, padx=10)

        def confirm_restore():
            selected_backup = backup_var.get()
            shutil.copy(os.path.join(backup_folder, selected_backup), csv_filename)
            messagebox.showinfo("نجاح", "تم استعادة النسخة الاحتياطية بنجاح.")
            restore_window.destroy()

        CTkButton(restore_window, text="تأكيد الاستعادة", width=200, height=40, font=("Arial", 14, "bold"),
                  command=confirm_restore).grid(row=1, column=0, columnspan=2, pady=20)

    CTkButton(frame, text="استعادة نسخة احتياطية", width=250, height=50, font=("Arial", 16, "bold"),
              command=restore_backup).grid(row=2, column=0, pady=10, padx=20, sticky="ew")

    # Back button
    CTkButton(frame, text="العودة", width=250, height=50, font=("Arial", 16, "bold"),
              command=lambda: show_frame(frames["home"])).grid(row=3, column=0, pady=10, padx=20, sticky="ew")

def check_due_installments():
    """Check for installments due in 3 days and send notifications."""
    df = read_csv_safely()
    today = datetime.now()
    for _, row in df.iterrows():
        installment_dates = row["Installment Dates"].split(";")
        for date_str in installment_dates:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if (date - today).days == 3:
                send_whatsapp_notification(row["Name"], row["Phone"], date_str, row["Installment Value"])

def send_whatsapp_notification(name, phone, date, amount):
    """Send a WhatsApp notification to the customer."""
    message = f"مرحبًا {name},\nتذكير بدفع قسط بقيمة {amount} ريال في تاريخ {date}.\nشكرًا لتعاملك معنا!"
    try:
        kit.sendwhatmsg_instantly(phone, message)
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")

def start_notification_thread():
    """Start a background thread to check for due installments."""
    threading.Thread(target=check_due_installments, daemon=True).start()

def setup_home_page():
    frame = frames["home"]
    frame.grid_columnconfigure(0, weight=1)

    CTkLabel(frame, text="الصفحة الرئيسية", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=20, sticky="n")

    CTkButton(frame, text="إضافة عميل", width=250, height=50, font=("Arial", 16, "bold"),
              command=lambda: show_frame(frames["add"])).grid(row=1, column=0, pady=10)
    CTkButton(frame, text="عرض العملاء", width=250, height=50, font=("Arial", 16, "bold"),
          command=lambda: show_frame(frames["view"])).grid(row=2, column=0, pady=10)
    CTkButton(frame, text="إدارة الأقساط", width=250, height=50, font=("Arial", 16, "bold"),
          command=lambda: show_frame(frames["manage_installments"])).grid(row=3, column=0, pady=10)
    CTkButton(frame, text="النسخ الاحتياطي واستعادة البيانات", width=250, height=50, font=("Arial", 16, "bold"),
          command=lambda: show_frame(frames["backup_restore"])).grid(row=4, column=0, pady=10)

setup_home_page()
setup_add_page()
setup_view_page()
setup_manage_installments_page()
setup_backup_restore_page()
show_frame(frames["home"])

# Start the notification thread
start_notification_thread()

app.mainloop()