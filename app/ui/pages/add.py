import os
from tkinter import messagebox, filedialog, ttk


def setup_add_page(frames, StyleManager, app, validate_and_save, DatePicker, show_frame):
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

    fields = [
        ("Customer Name:", "text"),
        ("Phone:", "phone"),
        ("Amount:", "number"),
        ("Installments:", "number"),
    ]

    entries = []
    for i, (label, _) in enumerate(fields):
        StyleManager.create_label(
            form_card,
            text=label,
            font_style="label",
        ).grid(row=i * 2, column=0, sticky="w", padx=16, pady=(16, 4))

        entry = StyleManager.create_entry(form_card)
        entry.grid(row=i * 2 + 1, column=0, sticky="ew", padx=16, pady=(0, 4))
        entries.append(entry)

    row_offset = len(fields) * 2

    StyleManager.create_label(
        form_card,
        text="Installment Start Date:",
        font_style="label",
    ).grid(row=row_offset, column=0, sticky="w", padx=16, pady=(16, 4))

    date_row = StyleManager.create_frame(form_card, fg_color="transparent", border_width=0)
    date_row.grid(row=row_offset + 1, column=0, sticky="ew", padx=16, pady=(0, 4))
    date_row.grid_columnconfigure(0, weight=1)

    start_date_entry = StyleManager.create_entry(date_row)
    start_date_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    date_picker_btn = StyleManager.create_button(
        date_row,
        text="Select Date",
        style="secondary",
        width=120,
        command=lambda: DatePicker(app, start_date_entry)
    )
    date_picker_btn.grid(row=0, column=1)

    file_label_row = row_offset + 2
    StyleManager.create_label(
        form_card,
        text="Customer Files:",
        font_style="label",
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
            filetypes=[
                ("All files", "*.*"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.png *.jpg *.jpeg"),
                ("Document files", "*.doc *.docx"),
            ],
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
            if messagebox.askyesno("Confirm", "Are you sure you want to remove all selected files?"):
                file_list.files = []
                file_list.configure(state="normal")
                file_list.delete("1.0", "end")
                file_list.configure(state="disabled")

    StyleManager.create_button(
        file_buttons,
        text="Add Files",
        width=100,
        command=add_files,
    ).pack(side="left", padx=(0, 6))

    StyleManager.create_button(
        file_buttons,
        text="Clear",
        style="secondary",
        width=80,
        command=clear_files,
    ).pack(side="left")

    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)

    left_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    left_buttons.grid(row=0, column=0, sticky="w")

    right_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    right_buttons.grid(row=0, column=1, sticky="e")

    save_btn = StyleManager.create_button(
        left_buttons,
        text="Save Customer",
        width=160,
        command=lambda: validate_and_save(*entries, start_date_entry, file_list),
    )
    save_btn.pack(side="left", pady=10)

    back_btn = StyleManager.create_button(
        right_buttons,
        text="Back",
        style="secondary",
        width=120,
        command=lambda: show_frame(frames["home"]),
    )
    back_btn.pack(side="right", pady=10)
