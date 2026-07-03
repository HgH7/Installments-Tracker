"""Document Generator — receipts, invoices, contracts, statements, PDF."""

import logging
import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter
from app.services.document_service import DocumentService, DOCUMENT_TYPES
from app.services.customer_service import CustomerService


def setup_documents_page(frames, style_mgr, document_service: DocumentService,
                         customer_service: CustomerService, show_frame,
                         filter_customer_id=None, activity_service=None):
    frame = frames.get("documents")
    if not frame:
        return
    frame.configure(fg_color=style_mgr.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(2, weight=1)

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

    # ── Generate form ──────────────────────────────────────────────
    form = style_mgr.create_frame(main, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    form.grid(row=0, column=0, sticky="ew", pady=(0, 12))

    style_mgr.create_label(form, text="Generate Document", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=12, pady=(8, 4))

    r1 = style_mgr.create_frame(form, fg_color="transparent")
    r1.pack(fill="x", padx=12, pady=4)
    r1.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

    style_mgr.create_label(r1, text="Document Type:", anchor="w").grid(row=0, column=0, sticky="w")
    type_var = tk.StringVar(value="receipt")
    customtkinter.CTkComboBox(r1, values=DOCUMENT_TYPES, variable=type_var, width=140).grid(row=0, column=1, sticky="ew", padx=(0, 8))

    style_mgr.create_label(r1, text="Customer Name:", anchor="w").grid(row=0, column=2, sticky="w")
    cname_entry = style_mgr.create_entry(r1, width=140)
    cname_entry.grid(row=0, column=3, sticky="ew")

    cid_entry = style_mgr.create_entry(r1, width=60)
    cid_entry.grid(row=0, column=4, sticky="ew", padx=(4, 0))
    cid_entry.insert(0, str(filter_customer_id) if filter_customer_id else "")
    cid_entry.configure(placeholder_text="ID")

    r2 = style_mgr.create_frame(form, fg_color="transparent")
    r2.pack(fill="x", padx=12, pady=(0, 8))
    r2.grid_columnconfigure(1, weight=1)

    style_mgr.create_label(r2, text="Extra data (key=value):", anchor="w").grid(row=0, column=0, sticky="w")
    data_entry = style_mgr.create_entry(r2, width=400)
    data_entry.insert(0, "amount=100 description=Payment for services")
    data_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def generate():
        doc_type = type_var.get()
        cname = cname_entry.get().strip()
        cid_str = cid_entry.get().strip()
        cid = None
        if cname:
            cid = document_service.get_customer_id_by_name(cname)
            if cid is None:
                messagebox.showerror("Error", f"Customer not found: {cname}")
                return
        elif cid_str:
            try:
                cid = int(cid_str)
            except ValueError:
                messagebox.showerror("Error", "Customer ID must be a number.")
                return
        else:
            messagebox.showerror("Error", "Enter a customer name or ID.")
            return
        data = {}
        for pair in data_entry.get().strip().split():
            if "=" in pair:
                k, v = pair.split("=", 1)
                data[k] = v
        path = document_service.generate(doc_type, cid, data)
        if path:
            messagebox.showinfo("Success", f"Document generated:\n{path}")
            if activity_service:
                activity_service.log("Document generated", customer_id=cid, detail=f"{doc_type} — {path}")
            refresh_list()
        else:
            messagebox.showerror("Error", "Failed to generate document. Check customer exists.")

    style_mgr.create_button(r1, text="Generate", command=generate).grid(row=0, column=5, sticky="e", padx=(8, 0))

    # ── Document list ──────────────────────────────────────────────
    list_frame = style_mgr.create_frame(main, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    list_frame.grid(row=1, column=0, sticky="nsew")
    list_frame.grid_columnconfigure(0, weight=1)
    list_frame.grid_rowconfigure(2, weight=1)

    style_mgr.create_label(list_frame, text="Generated Documents", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=16, pady=(12, 4))

    filter_row = style_mgr.create_frame(list_frame, fg_color="transparent")
    filter_row.pack(fill="x", padx=16, pady=(0, 8))
    filter_row.grid_columnconfigure((0, 1, 2), weight=0)

    style_mgr.create_label(filter_row, text="Filter type:", anchor="w").grid(row=0, column=0, sticky="w")
    filter_type_var = tk.StringVar(value="All")
    filter_type_menu = customtkinter.CTkOptionMenu(
        filter_row, values=["All"] + DOCUMENT_TYPES, variable=filter_type_var,
        fg_color=style_mgr.COLORS["surface_high"],
        button_color=style_mgr.COLORS["surface_highest"],
        button_hover_color=style_mgr.COLORS["border"],
        text_color=style_mgr.COLORS["text"], width=120,
    )
    filter_type_menu.grid(row=0, column=1, sticky="w", padx=(8, 16))

    style_mgr.create_label(filter_row, text="Customer:", anchor="w").grid(row=0, column=2, sticky="w")
    filter_customer_entry = style_mgr.create_entry(filter_row, width=160)
    filter_customer_entry.grid(row=0, column=3, sticky="w", padx=(8, 8))

    def apply_filter():
        refresh_list()

    style_mgr.create_button(filter_row, text="Filter", style="secondary", width=80, command=apply_filter).grid(row=0, column=4, sticky="w")

    columns = ("type", "title", "customer", "created", "path")
    tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
    tree.heading("type", text="Type")
    tree.heading("title", text="Title")
    tree.heading("customer", text="Customer")
    tree.heading("created", text="Created")
    tree.heading("path", text="File Path")
    tree.column("type", width=100)
    tree.column("title", width=200)
    tree.column("customer", width=140)
    tree.column("created", width=100)
    tree.column("path", width=300)
    tree.pack(fill="both", expand=True, padx=16, pady=(0, 8))

    empty_label = style_mgr.create_label(list_frame, text="", font_style="small",
                                         text_color=style_mgr.COLORS["text_muted"])
    empty_label.pack(anchor="w", padx=16, pady=(0, 4))

    btn_row = style_mgr.create_frame(list_frame, fg_color="transparent")
    btn_row.pack(fill="x", padx=16, pady=(0, 12))

    def get_selected_doc_id():
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a document first.")
            return None
        return int(selected[0])

    def open_selected_document():
        doc_id = get_selected_doc_id()
        if doc_id is None:
            return
        doc = document_service.get_document(doc_id)
        if not doc:
            messagebox.showerror("Error", "Document not found.")
            return
        file_path = doc.get("file_path", "")
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Document file not found on disk.")
            return
        try:
            subprocess.Popen(["open", file_path])
        except Exception as e:
            logging.warning(f"Failed to open document: {e}")
            messagebox.showinfo("Info", f"Document path:\n{file_path}")

    def show_document_detail():
        doc_id = get_selected_doc_id()
        if doc_id is None:
            return
        doc = document_service.get_document(doc_id)
        if not doc:
            messagebox.showerror("Error", "Document not found.")
            return

        d = customtkinter.CTkToplevel(frame)
        d.geometry("520x360")
        d.title(f"Document — {doc['title'][:40]}")
        d.transient(frame)
        d.grab_set()

        body = style_mgr.create_frame(d, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)
        body.grid_columnconfigure(0, weight=1)

        style_mgr.create_label(body, text="Document Details", font_style="subheading").grid(
            row=0, column=0, sticky="w", pady=(0, 12))

        info_frame = style_mgr.create_frame(body, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        info_frame.grid(row=1, column=0, sticky="ew")
        info_frame.grid_columnconfigure(1, weight=1)

        rows_data = [
            ("Type:", doc.get("document_type", "")),
            ("Title:", doc.get("title", "")),
            ("Customer:", document_service.get_customer_name_for_doc(doc.get("customer_id", 0))),
            ("Created:", doc.get("created_at", "")[:10]),
            ("File:", doc.get("file_path", "")),
        ]
        for i, (label, value) in enumerate(rows_data):
            style_mgr.create_label(info_frame, text=label, font_style="body_bold").grid(
                row=i, column=0, sticky="w", padx=12, pady=(8, 0))
            style_mgr.create_label(info_frame, text=value, font_style="small", wraplength=380).grid(
                row=i, column=1, sticky="w", padx=(8, 12), pady=(8, 0))

        btn_row_d = style_mgr.create_frame(body, fg_color="transparent")
        btn_row_d.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        btn_row_d.grid_columnconfigure((0, 1, 2), weight=1)

        def detail_open():
            fp = doc.get("file_path", "")
            if fp and os.path.exists(fp):
                try:
                    subprocess.Popen(["open", fp])
                except Exception:
                    messagebox.showinfo("Info", f"File path:\n{fp}")
            else:
                messagebox.showerror("Error", "File not found on disk.")

        def detail_delete():
            if messagebox.askyesno("Confirm Delete", f"Delete document '{doc['title']}'?\nThis cannot be undone."):
                document_service.delete_document(doc["id"])
                d.destroy()
                refresh_list()

        style_mgr.create_button(btn_row_d, text="Open File", command=detail_open).grid(row=0, column=0, padx=4)
        style_mgr.create_button(btn_row_d, text="Delete", style="danger", command=detail_delete).grid(row=0, column=1, padx=4)
        style_mgr.create_button(btn_row_d, text="Close", style="secondary", command=d.destroy).grid(row=0, column=2, padx=4)

    def delete_selected_document():
        doc_id = get_selected_doc_id()
        if doc_id is None:
            return
        doc = document_service.get_document(doc_id)
        if not doc:
            return
        if messagebox.askyesno("Confirm Delete", f"Delete document '{doc['title']}'?\nThis cannot be undone."):
            document_service.delete_document(doc_id)
            if activity_service:
                activity_service.log("Document deleted", customer_id=doc.get("customer_id"),
                                     detail=f"{doc['title']}")
            refresh_list()

    style_mgr.create_button(btn_row, text="View / Edit", command=show_document_detail).pack(side="left")
    style_mgr.create_button(btn_row, text="Open", command=open_selected_document).pack(side="left", padx=(8, 0))
    style_mgr.create_button(btn_row, text="Delete", style="danger", command=delete_selected_document).pack(side="left", padx=(8, 0))
    style_mgr.create_button(btn_row, text="Refresh", command=lambda: refresh_list()).pack(side="left", padx=(8, 0))
    style_mgr.create_button(btn_row, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")

    tree.bind("<Double-1>", lambda _e: show_document_detail())

    def refresh_list():
        for item in tree.get_children():
            tree.delete(item)
        filter_type = filter_type_var.get()
        filter_customer_name = filter_customer_entry.get().strip()
        filter_cid = None
        if filter_customer_name:
            filter_cid = document_service.get_customer_id_by_name(filter_customer_name)
        docs = document_service.get_documents(customer_id=filter_cid, doc_type=filter_type if filter_type != "All" else "")
        count = 0
        for d in docs:
            cname = document_service.get_customer_name_for_doc(d.get("customer_id", 0))
            tree.insert("", "end", iid=str(d["id"]), values=(
                d["document_type"],
                d["title"][:50],
                cname,
                d["created_at"][:10],
                d.get("file_path", "")[:80],
            ))
            count += 1
        if count == 0:
            empty_label.configure(text="No documents found. Generate one above.")
        else:
            empty_label.configure(text=f"{count} document(s)")

    refresh_list()

    def navigate_to_customer(customer_id=None, customer_name=None, switch_to_frame=True):
        if customer_name:
            filter_customer_entry.delete(0, "end")
            filter_customer_entry.insert(0, customer_name)
        elif customer_id is not None:
            name = document_service.get_customer_name_for_doc(customer_id)
            if not name.startswith("ID:"):
                filter_customer_entry.delete(0, "end")
                filter_customer_entry.insert(0, name)
        if switch_to_frame:
            show_frame(frame)
        refresh_list()

    frame.navigate_to_customer_docs = navigate_to_customer

    nav_frame = style_mgr.create_frame(frame, fg_color="transparent")
    nav_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 16))
    style_mgr.create_button(nav_frame, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")
