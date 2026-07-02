"""Document Generator — receipts, invoices, contracts, statements, PDF."""

import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter
from app.services.document_service import DocumentService, DOCUMENT_TYPES
from app.services.customer_service import CustomerService


def setup_documents_page(frames, style_mgr, document_service: DocumentService,
                         customer_service: CustomerService, show_frame):
    frame = frames.get("documents")
    if not frame:
        return
    frame.configure(fg_color=style_mgr.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    for w in frame.winfo_children():
        w.destroy()

    header = style_mgr.create_frame(frame, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
    style_mgr.create_label(header, text="Document Generator", font_style="heading", anchor="w").pack(side="left")

    if not document_service.available:
        warn = style_mgr.create_frame(frame, fg_color=style_mgr.COLORS["warning"], corner_radius=8)
        warn.grid(row=1, column=0, sticky="ew", padx=20)
        style_mgr.create_label(warn, text="PDF backend not available. Install weasyprint or fpdf2 for PDF generation.",
                               text_color="#000000", anchor="w").pack(padx=16, pady=8)

    main = style_mgr.create_frame(frame, fg_color="transparent")
    main.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 16))
    main.grid_columnconfigure(0, weight=1)
    main.grid_rowconfigure(1, weight=1)

    # Generate form
    form = style_mgr.create_frame(main, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    form.grid(row=0, column=0, sticky="ew", pady=(0, 12))

    style_mgr.create_label(form, text="Generate Document", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=12, pady=(8, 4))

    r1 = style_mgr.create_frame(form, fg_color="transparent")
    r1.pack(fill="x", padx=12, pady=4)
    r1.grid_columnconfigure((0, 1, 2, 3), weight=1)

    style_mgr.create_label(r1, text="Document Type:", anchor="w").grid(row=0, column=0, sticky="w")
    type_var = tk.StringVar(value="receipt")
    customtkinter.CTkComboBox(r1, values=DOCUMENT_TYPES, variable=type_var, width=140).grid(row=0, column=1, sticky="ew", padx=(0, 8))

    style_mgr.create_label(r1, text="Customer ID:", anchor="w").grid(row=0, column=2, sticky="w")
    cid_entry = style_mgr.create_entry(r1, width=100)
    cid_entry.grid(row=0, column=3, sticky="ew")

    r2 = style_mgr.create_frame(form, fg_color="transparent")
    r2.pack(fill="x", padx=12, pady=4)

    style_mgr.create_label(r2, text="Extra data (JSON key=value):", anchor="w").grid(row=0, column=0, sticky="w")
    data_entry = style_mgr.create_entry(r2, width=400)
    data_entry.insert(0, "amount=100 description=Payment for services")
    data_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def generate():
        try:
            cid = int(cid_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Enter a valid customer ID")
            return
        doc_type = type_var.get()
        data = {}
        for pair in data_entry.get().strip().split():
            if "=" in pair:
                k, v = pair.split("=", 1)
                data[k] = v
        path = document_service.generate(doc_type, cid, data)
        if path:
            messagebox.showinfo("Success", f"Document generated:\n{path}")
            refresh_list()
        else:
            messagebox.showerror("Error", "Failed to generate document")

    style_mgr.create_button(r1, text="Generate", command=generate).grid(row=0, column=4, sticky="e", padx=(8, 0))

    # Document list
    list_frame = style_mgr.create_frame(main, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    list_frame.grid(row=1, column=0, sticky="nsew")
    list_frame.grid_columnconfigure(0, weight=1)
    list_frame.grid_rowconfigure(1, weight=1)

    style_mgr.create_label(list_frame, text="Generated Documents", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=16, pady=(12, 4))

    columns = ("type", "title", "customer", "created")
    tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
    for col in columns:
        tree.heading(col, text=col.title())
        tree.column(col, width=120)
    tree.pack(fill="both", expand=True, padx=16, pady=(8, 12))

    btn_row = style_mgr.create_frame(list_frame, fg_color="transparent")
    btn_row.pack(fill="x", padx=16, pady=(0, 12))
    style_mgr.create_button(btn_row, text="Refresh", command=lambda: refresh_list()).pack(side="left")

    def refresh_list():
        for item in tree.get_children():
            tree.delete(item)
        for d in document_service.get_documents():
            tree.insert("", "end", values=(d["document_type"], d["title"][:50],
                                            d.get("customer_id", ""), d["created_at"][:10]))

    refresh_list()

    nav_frame = style_mgr.create_frame(frame, fg_color="transparent")
    nav_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 16))
    style_mgr.create_button(nav_frame, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")
