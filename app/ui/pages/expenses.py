"""Expense Tracking — record and manage business expenses."""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import customtkinter
from app.services.finance_service import FinanceService, EXPENSE_CATEGORIES


def setup_expenses_page(frames, style_mgr, finance_service: FinanceService, show_frame):
    frame = frames.get("expenses")
    if not frame:
        return
    frame.configure(fg_color=style_mgr.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    for w in frame.winfo_children():
        w.destroy()

    header = style_mgr.create_frame(frame, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
    style_mgr.create_label(header, text="Expense Tracking", font_style="heading", anchor="w").pack(side="left")

    scroll = customtkinter.CTkScrollableFrame(frame, fg_color="transparent")
    scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
    scroll.grid_columnconfigure(0, weight=1)

    form = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    form.pack(fill="x", pady=(0, 12))
    style_mgr.create_label(form, text="Add New Expense", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=12, pady=(8, 4))

    r1 = style_mgr.create_frame(form, fg_color="transparent")
    r1.pack(fill="x", padx=12, pady=4)
    r1.grid_columnconfigure((1, 3), weight=1)

    style_mgr.create_label(r1, text="Amount:", anchor="w").grid(row=0, column=0, sticky="w")
    amount_entry = style_mgr.create_entry(r1, width=120)
    amount_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

    style_mgr.create_label(r1, text="Category:", anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 0))
    cat_var = tk.StringVar(value="office")
    cat_combo = customtkinter.CTkComboBox(r1, values=EXPENSE_CATEGORIES, variable=cat_var, width=140)
    cat_combo.grid(row=0, column=3, sticky="ew")

    r2 = style_mgr.create_frame(form, fg_color="transparent")
    r2.pack(fill="x", padx=12, pady=4)
    r2.grid_columnconfigure((1, 3), weight=1)

    style_mgr.create_label(r2, text="Date:", anchor="w").grid(row=0, column=0, sticky="w")
    date_entry = style_mgr.create_entry(r2, width=120)
    date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
    date_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

    style_mgr.create_label(r2, text="Description:", anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 0))
    desc_entry = style_mgr.create_entry(r2, width=200)
    desc_entry.grid(row=0, column=3, sticky="ew")

    def add_expense():
        try:
            amount = float(amount_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Invalid amount")
            return
        finance_service.add_expense(amount, cat_var.get(), desc_entry.get().strip(), date_entry.get().strip())
        amount_entry.delete(0, "end")
        desc_entry.delete(0, "end")
        messagebox.showinfo("Success", "Expense added")
        refresh_list()

    style_mgr.create_button(form, text="Add Expense", command=add_expense).pack(anchor="w", padx=12, pady=(4, 10))

    list_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    list_section.pack(fill="both", expand=True)
    style_mgr.create_label(list_section, text="Expense History", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=16, pady=(12, 4))

    columns = ("date", "category", "description", "amount")
    tree = ttk.Treeview(list_section, columns=columns, show="headings", height=10)
    for col in columns:
        tree.heading(col, text=col.title())
        tree.column(col, width=100)
    tree.pack(fill="both", expand=True, padx=16, pady=(8, 8))

    btn_row = style_mgr.create_frame(list_section, fg_color="transparent")
    btn_row.pack(fill="x", padx=16, pady=(0, 12))

    def delete_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select an expense")
            return
        if messagebox.askyesno("Confirm", "Delete selected expense?"):
            values = tree.item(sel[0])["values"]
            exp_id = values[4] if len(values) > 4 else None
            if exp_id:
                finance_service.delete_expense(exp_id)
                refresh_list()

    def refresh_list():
        for item in tree.get_children():
            tree.delete(item)
        for e in finance_service.get_expenses():
            tree.insert("", "end", values=(e.get("expense_date", ""), e.get("category", ""),
                                            e.get("description", "")[:40], f"${e['amount']:.2f}", e["id"]))

    style_mgr.create_button(btn_row, text="Delete Selected", command=delete_selected,
                            fg_color=style_mgr.COLORS.get("danger", "#ef4444")).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Refresh", command=refresh_list).pack(side="left")
    refresh_list()

    nav_frame = style_mgr.create_frame(frame, fg_color="transparent")
    nav_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
    style_mgr.create_button(nav_frame, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")
