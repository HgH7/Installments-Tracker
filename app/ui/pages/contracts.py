"""Contract Management — templates, contracts, status tracking."""

import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter
from app.services.contract_service import ContractService


def setup_contracts_page(frames, style_mgr, contract_service: ContractService, show_frame):
    frame = frames.get("contracts")
    if not frame:
        return
    frame.configure(fg_color=style_mgr.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    for w in frame.winfo_children():
        w.destroy()

    header = style_mgr.create_frame(frame, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
    style_mgr.create_label(header, text="Contract Management", font_style="heading", anchor="w").pack(side="left")

    scroll = customtkinter.CTkScrollableFrame(frame, fg_color="transparent")
    scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
    scroll.grid_columnconfigure(0, weight=1)

    list_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    list_section.pack(fill="x", pady=(0, 12))
    style_mgr.create_label(list_section, text="Contracts", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=16, pady=(12, 4))

    columns = ("number", "customer", "status", "created")
    tree = ttk.Treeview(list_section, columns=columns, show="headings", height=10)
    tree.heading("number", text="Contract #")
    tree.heading("customer", text="Customer")
    tree.heading("status", text="Status")
    tree.heading("created", text="Created")
    for col in columns:
        tree.column(col, width=120)
    tree.pack(fill="x", padx=16, pady=(8, 4))

    action_frame = style_mgr.create_frame(list_section, fg_color="transparent")
    action_frame.pack(fill="x", padx=16, pady=(0, 12))

    style_mgr.create_label(action_frame, text="Search:", anchor="w").pack(side="left")
    search_entry = style_mgr.create_entry(action_frame, width=200)
    search_entry.pack(side="left", padx=(8, 8))

    def search():
        q = search_entry.get().strip()
        results = contract_service.find_contract(q) if q else contract_service.get_all_contracts()
        for item in tree.get_children():
            tree.delete(item)
        for c in results:
            tree.insert("", "end", values=(c["contract_number"], c.get("customer_name", ""),
                                            c["status"], c["created_at"][:10]))

    style_mgr.create_button(action_frame, text="Search", command=search).pack(side="left")

    def show_new_contract_dialog():
        d = customtkinter.CTkToplevel(frame)
        d.geometry("400x200")
        d.title("New Contract")
        d.transient(frame)
        d.grab_set()
        style_mgr.create_label(d, text="Customer ID:", anchor="w").pack(anchor="w", padx=16, pady=(12, 4))
        cid_entry = style_mgr.create_entry(d, width=200)
        cid_entry.pack(anchor="w", padx=16, pady=4)

        def create():
            try:
                cid = int(cid_entry.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Enter a valid customer ID")
                return
            ct = contract_service.create_contract(cid)
            messagebox.showinfo("Success", f"Contract created: {ct['contract_number']}")
            d.destroy()
            refresh()

        style_mgr.create_button(d, text="Create", command=create).pack(anchor="w", padx=16, pady=12)

    style_mgr.create_button(action_frame, text="New Contract", command=show_new_contract_dialog).pack(side="right")

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        for c in contract_service.get_all_contracts():
            tree.insert("", "end", values=(c["contract_number"], c.get("customer_name", ""),
                                            c["status"], c["created_at"][:10]))

    refresh()

    nav_frame = style_mgr.create_frame(frame, fg_color="transparent")
    nav_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
    style_mgr.create_button(nav_frame, text="Refresh", command=refresh).pack(side="left")
    style_mgr.create_button(nav_frame, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")
