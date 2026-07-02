import os
from tkinter import filedialog, messagebox, ttk


def setup_add_page(frames, StyleManager, app, validate_and_save, DatePicker, show_frame, csv_repository=None):
    frame = frames["add"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    header_frame = StyleManager.create_section_header(
        frame,
        "Add Customer",
        "Enter customer information and installment details",
    )
    header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))

    form_card = StyleManager.create_frame(frame)
    form_card.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
    form_card.grid_columnconfigure(0, weight=1)

    field_defs = [
        ("Customer Name:", "text", "e.g. Ahmed Mohammed"),
        ("Phone:", "phone", "e.g. +971501234567"),
        ("Amount:", "number", "e.g. 3000.00"),
        ("Installments:", "number", "e.g. 3"),
    ]

    entries = []
    error_labels = []

    def get_validate_fn(field_type):
        from app.validation import ValidationService as V
        if field_type == "phone":
            return lambda v: V.validate_phone(v)
        elif field_type == "number":
            return lambda v: V.validate_amount(v) if "." in v else (V.validate_amount(v) if v else V.ValidationResult(errors=["Required"]))
        return None

    def validate_field(idx, entry, field_type):
        val = entry.get().strip()
        fn = get_validate_fn(field_type)
        if fn:
            result = fn(val)
            if val and not result:
                entry.configure(border_color=StyleManager.COLORS["danger"])
                if idx < len(error_labels):
                    error_labels[idx].configure(text=result.errors[0])
                    error_labels[idx].grid()
            else:
                entry.configure(border_color=StyleManager.COLORS["border"])
                if idx < len(error_labels):
                    error_labels[idx].grid_remove()

    for i, (label, field_type, placeholder) in enumerate(field_defs):
        label_frame = StyleManager.create_frame(form_card, fg_color="transparent", border_width=0)
        label_frame.grid(row=i * 3, column=0, sticky="w", padx=16, pady=(16, 2))
        StyleManager.create_label(label_frame, text=label, font_style="label").pack(side="left")
        StyleManager.create_label(label_frame, text=" *", font_style="label",
                                  text_color=StyleManager.COLORS["danger"]).pack(side="left")

        entry = StyleManager.create_entry(form_card, placeholder_text=placeholder)
        entry.grid(row=i * 3 + 1, column=0, sticky="ew", padx=16, pady=(0, 2))

        err_label = StyleManager.create_label(form_card, text="", font_style="small",
                                              text_color=StyleManager.COLORS["danger"])
        err_label.grid(row=i * 3 + 2, column=0, sticky="w", padx=16, pady=(0, 2))
        err_label.grid_remove()

        entry.bind("<FocusOut>", lambda e, idx=i, ent=entry, ft=field_type: validate_field(idx, ent, ft))

        entries.append(entry)
        error_labels.append(err_label)

    row_offset = len(field_defs) * 3

    StyleManager.create_label(
        form_card,
        text="Installment Start Date:",
        font_style="label",
    ).grid(row=row_offset, column=0, sticky="w", padx=16, pady=(16, 4))

    date_row = StyleManager.create_frame(form_card, fg_color="transparent", border_width=0)
    date_row.grid(row=row_offset + 1, column=0, sticky="ew", padx=16, pady=(0, 4))
    date_row.grid_columnconfigure(0, weight=1)

    start_date_entry = StyleManager.create_entry(date_row, placeholder_text="YYYY-MM-DD")
    start_date_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    date_picker_btn = StyleManager.create_button(
        date_row, text="Select Date", style="secondary", width=120,
        command=lambda: DatePicker(app, start_date_entry)
    )
    date_picker_btn.grid(row=0, column=1)

    file_label_row = row_offset + 2
    StyleManager.create_label(
        form_card, text="Customer Files:", font_style="label",
    ).grid(row=file_label_row, column=0, sticky="w", padx=16, pady=(16, 4))

    file_area = StyleManager.create_frame(form_card, fg_color="transparent", border_width=0)
    file_area.grid(row=file_label_row + 1, column=0, sticky="ew", padx=16, pady=(0, 16))
    file_area.grid_columnconfigure(0, weight=1)

    file_list = StyleManager.create_textbox(file_area, height=80)
    file_list.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    scrollbar = ttk.Scrollbar(file_area, orient="vertical", command=file_list.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    file_list.configure(yscrollcommand=scrollbar.set)
    file_list.files = []

    file_buttons = StyleManager.create_frame(file_area, fg_color="transparent", border_width=0)
    file_buttons.grid(row=0, column=2, sticky="e")

    def add_files():
        files = filedialog.askopenfilenames(
            title="Select customer files",
            filetypes=[("All files", "*.*"), ("PDF files", "*.pdf"),
                       ("Image files", "*.png *.jpg *.jpeg"), ("Document files", "*.doc *.docx")],
        )
        if files:
            file_list.files.extend(files)
            file_list.configure(state="normal")
            file_list.delete("1.0", "end")
            for f in files:
                file_list.insert("end", f"{os.path.basename(f)}\n")
            file_list.configure(state="disabled")

    def clear_files():
        if file_list.files:
            if messagebox.askyesno("Confirm", "Remove all selected files?"):
                file_list.files = []
                file_list.configure(state="normal")
                file_list.delete("1.0", "end")
                file_list.configure(state="disabled")

    StyleManager.create_button(file_buttons, text="Add Files", width=100, command=add_files).pack(side="left", padx=(0, 6))
    StyleManager.create_button(file_buttons, text="Clear", style="secondary", width=80, command=clear_files).pack(side="left")

    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)

    left_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    left_buttons.grid(row=0, column=0, sticky="w")
    right_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    right_buttons.grid(row=0, column=1, sticky="e")

    def save_with_checks():
        phone = entries[1].get().strip()
        if csv_repository and phone:
            existing = csv_repository.read_data()
            for c in existing:
                if c.get("Phone", "").strip() == phone or c.get("Phone", "").strip().lstrip("+") == phone.lstrip("+"):
                    if not messagebox.askyesno("Duplicate Phone",
                                               f"Phone number {phone} already exists for {c['Name']}.\nContinue anyway?"):
                        return
        validate_and_save(*entries, start_date_entry, file_list)

    save_btn = StyleManager.create_button(left_buttons, text="Save Customer", width=160, command=save_with_checks)
    save_btn.pack(side="left", pady=10)

    back_btn = StyleManager.create_button(right_buttons, text="Back", style="secondary", width=120,
                                          command=lambda: show_frame(frames["home"]))
    back_btn.pack(side="right", pady=10)
