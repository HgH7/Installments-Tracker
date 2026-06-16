import os
from tkinter import messagebox, filedialog, ttk
from customtkinter import CTkTextbox


def setup_add_page(frames, StyleManager, app, validate_and_save, DatePicker, show_frame):
    frame = frames["add"]
    frame.grid_columnconfigure(0, weight=1)

    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)

    StyleManager.create_label(
        header_frame,
        text="إضافة عميل جديد",
        font_style="heading"
    ).grid(row=0, column=0, pady=(20, 10))

    StyleManager.create_label(
        header_frame,
        text="أدخل بيانات العميل وتفاصيل الأقساط",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, pady=(0, 20))

    form_frame = StyleManager.create_frame(frame)
    form_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
    form_frame.grid_columnconfigure(0, weight=1)
    form_frame.grid_columnconfigure(1, weight=2)

    fields = [
        {"label": "اسم العميل:", "type": "text"},
        {"label": "رقم الهاتف:", "type": "phone"},
        {"label": "المبلغ:", "type": "number"},
        {"label": "عدد الأقساط:", "type": "number"}
    ]

    entries = []
    row = 0

    for field in fields:
        field_frame = StyleManager.create_frame(form_frame)
        field_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        field_frame.grid_columnconfigure(1, weight=1)

        StyleManager.create_label(
            field_frame,
            text=field["label"],
            font_style="body_bold"
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        entry = StyleManager.create_entry(field_frame, width=300)
        entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        entries.append(entry)

        row += 1

    date_frame = StyleManager.create_frame(form_frame)
    date_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
    date_frame.grid_columnconfigure(1, weight=1)

    StyleManager.create_label(
        date_frame,
        text="تاريخ بدء الأقساط:",
        font_style="body_bold"
    ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

    start_date_entry = StyleManager.create_entry(date_frame, width=200)
    start_date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

    date_picker_btn = StyleManager.create_button(
        date_frame,
        text="📅 اختر التاريخ",
        style="secondary",
        command=lambda: DatePicker(app, start_date_entry)
    )
    date_picker_btn.grid(row=0, column=2, padx=10, pady=5)

    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)

    save_btn = StyleManager.create_button(
        buttons_frame,
        text="حفظ العميل",
        width=200,
        command=lambda: validate_and_save(*entries, start_date_entry)
    )
    save_btn.grid(row=0, column=0, padx=10, pady=10)

    back_btn = StyleManager.create_button(
        buttons_frame,
        text="رجوع",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    )
    back_btn.grid(row=0, column=1, padx=10, pady=10)

    file_frame = StyleManager.create_frame(form_frame, fg_color="transparent")
    file_frame.grid(row=len(fields)*2+1, column=0, sticky="ew", pady=(20, 0))
    file_frame.grid_columnconfigure(1, weight=1)

    StyleManager.create_label(
        file_frame,
        text="📁 ملفات العميل",
        font_style="body_bold"
    ).grid(row=0, column=0, sticky="w", padx=(0, 10))

    file_list_frame = StyleManager.create_frame(file_frame, fg_color="transparent")
    file_list_frame.grid(row=0, column=1, sticky="ew", pady=(0, 10))
    file_list_frame.grid_columnconfigure(0, weight=1)

    file_list = CTkTextbox(
        file_list_frame,
        width=400,
        height=100,
        font=StyleManager.FONTS["body"],
        fg_color=StyleManager.COLORS["background"],
        border_color=StyleManager.COLORS["border"],
        state="disabled"
    )
    file_list.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    scrollbar = ttk.Scrollbar(file_list_frame, orient="vertical", command=file_list.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    file_list.configure(yscrollcommand=scrollbar.set)

    file_list.files = []

    file_buttons_frame = StyleManager.create_frame(file_frame, fg_color="transparent")
    file_buttons_frame.grid(row=0, column=2, sticky="e")

    def add_files():
        files = filedialog.askopenfilenames(
            title="اختر ملفات العميل",
            filetypes=[
                ("All files", "*.*"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.png *.jpg *.jpeg"),
                ("Document files", "*.doc *.docx")
            ]
        )
        if files:
            file_list.files.extend(files)
            file_list.configure(state="normal")
            file_list.delete("1.0", "end")
            for file in files:
                file_list.insert("end", f"{os.path.basename(file)}\n")
            file_list.configure(state="disabled")

    def clear_files():
        if file_list.files:
            if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف جميع الملفات المحددة؟"):
                file_list.files = []
                file_list.configure(state="normal")
                file_list.delete("1.0", "end")
                file_list.configure(state="disabled")

    StyleManager.create_button(
        file_buttons_frame,
        text="إضافة ملفات",
        width=120,
        command=add_files
    ).pack(side="left", padx=(0, 5))

    StyleManager.create_button(
        file_buttons_frame,
        text="مسح الملفات",
        style="secondary",
        width=120,
        command=clear_files
    ).pack(side="left")

    save_btn.configure(command=lambda: validate_and_save(*entries, start_date_entry, file_list))
