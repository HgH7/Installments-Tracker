import customtkinter
from customtkinter import *
from tkinter import messagebox
import re

# إنشاء النافذة الرئيسية
app = CTk()
app.geometry("600x450")

# دالة لتغيير الصفحة
def show_frame(frame):
    frame.tkraise()

# إنشاء إطار رئيسي للحاوية
container = CTkFrame(app)
container.pack(fill="both", expand=True)

# إنشاء الإطارات (الصفحات)
frames = {}
page_names = ["home", "add", "delete", "edit", "view"]
for name in page_names:
    frame = CTkFrame(container)
    frame.grid(row=0, column=0, sticky="nsew")
    frames[name] = frame

container.grid_columnconfigure(0, weight=1)
container.grid_rowconfigure(0, weight=1)

# ========== الصفحة الرئيسية ==========
def setup_home():
    frame_home = frames["home"]
    frame_home.grid_columnconfigure(0, weight=1)

    label_home = CTkLabel(frame_home, text="الصفحة الرئيسية", font=("Arial", 24, "bold"))
    label_home.grid(row=0, column=0, pady=20, sticky="n")

    buttons = [
        ("إضافة عميل", "add"),
        ("حذف العملاء", "delete"),
        ("تعديل العملاء", "edit"),
        ("عرض العملاء", "view"),
    ]

    for i, (text, frame_name) in enumerate(buttons, start=1):
        btn = CTkButton(frame_home, text=text, width=250, height=50, font=("Arial", 16, "bold"),
                        command=lambda f=frames[frame_name]: show_frame(f))
        btn.grid(row=i, column=0, pady=10, padx=20, sticky="ew")

setup_home()
# ========== ما قبل إضافة عميل ==========
def validate_and_save(name_entry, phone_entry):
    name = name_entry.get().strip()
    phone = phone_entry.get().strip()

    # Define regex patterns
    name_pattern = r"^[\w\s\u0600-\u06FF]{2,50}$"  # Allows Arabic and English names (2-50 characters)
    phone_pattern = r"^\+?\d{10,15}$"  # Allows phone numbers (10-15 digits, optional + at start)

    # Validate name
    if not re.match(name_pattern, name):
        messagebox.showerror("خطأ", "الاسم يجب أن يحتوي على 2-50 حرفًا فقط بدون رموز خاصة.")
        return

    # Validate phone number
    if not re.match(phone_pattern, phone):
        messagebox.showerror("خطأ", "رقم الهاتف يجب أن يحتوي على 10-15 رقمًا ويمكن أن يبدأ بـ '+'.")
        return

    # If both are valid, save the data
    messagebox.showinfo("نجاح", "تم حفظ العميل بنجاح")
# ========== صفحة إضافة عميل ==========
def setup_add_page():
    frame = frames["add"]
    frame.grid_columnconfigure(0, weight=1)

    label = CTkLabel(frame, text="إضافة عميل جديد", font=("Arial", 18, "bold"))
    label.grid(row=0, column=0, pady=20, sticky="n")

    name_label = CTkLabel(frame, text="اسم العميل:", font=("Arial", 14))
    name_label.grid(row=1, column=0, pady=5, padx=20, sticky="w")
    name_entry = CTkEntry(frame, width=250)
    name_entry.grid(row=2, column=0, pady=5, padx=20)

    phone_label = CTkLabel(frame, text="رقم الهاتف:", font=("Arial", 14))
    phone_label.grid(row=3, column=0, pady=5, padx=20, sticky="w")
    phone_entry = CTkEntry(frame, width=250)
    phone_entry.grid(row=4, column=0, pady=5, padx=20)
    save_button = CTkButton(frame, text="حفظ العميل", width=250, height=50, font=("Arial", 16, "bold"),
                            command=lambda: messagebox.showinfo("نجاح", "تم حفظ العميل بنجاح"))
    save_button.grid(row=5, column=0, pady=20, padx=20, sticky="ew")

    back_button = CTkButton(frame, text="العودة", width=250, height=50, font=("Arial", 16, "bold"),
                            command=lambda: show_frame(frames["home"]))
    back_button.grid(row=6, column=0, pady=10, padx=20, sticky="ew")

setup_add_page()

# ========== الصفحات الأخرى ==========
def setup_delete_page():
    frame = frames["delete"]
    frame.grid_columnconfigure(0, weight=1)
    label = CTkLabel(frame, text="صفحة حذف العملاء", font=("Arial", 18, "bold"))
    label.grid(row=0, column=0, pady=20, sticky="n")
    back_button = CTkButton(frame, text="العودة", width=250, height=50, font=("Arial", 16, "bold"),
                            command=lambda: show_frame(frames["home"]))
    back_button.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
setup_delete_page()

def setup_edit_page():
    frame = frames["edit"]
    frame.grid_columnconfigure(0, weight=1)
    label = CTkLabel(frame, text="صفحة تعديل العملاء", font=("Arial", 18, "bold"))
    label.grid(row=0, column=0, pady=20, sticky="n")
    back_button = CTkButton(frame, text="العودة", width=250, height=50, font=("Arial", 16, "bold"),
                            command=lambda: show_frame(frames["home"]))
    back_button.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
setup_edit_page()

def setup_view_page():
    frame = frames["view"]
    frame.grid_columnconfigure(0, weight=1)
    label = CTkLabel(frame, text="صفحة عرض العملاء", font=("Arial", 18, "bold"))
    label.grid(row=0, column=0, pady=20, sticky="n")
    back_button = CTkButton(frame, text="العودة", width=250, height=50, font=("Arial", 16, "bold"),
                            command=lambda: show_frame(frames["home"]))
    back_button.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
setup_view_page()

# إظهار الصفحة الرئيسية عند التشغيل
show_frame(frames["home"])

app.mainloop()
# ana 27b omar