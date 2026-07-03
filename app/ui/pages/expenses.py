"""Expense Tracking — record and manage business expenses."""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import customtkinter
from app.services.finance_service import FinanceService, EXPENSE_CATEGORIES


def setup_expenses_page(frames, style_mgr, finance_service: FinanceService, show_frame,
                        activity_service=None):
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

    # ── Add Expense Form ──────────────────────────────────────────
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
        if amount <= 0:
            messagebox.showerror("Error", "Amount must be positive")
            return
        finance_service.add_expense(amount, cat_var.get(), desc_entry.get().strip(), date_entry.get().strip())
        if activity_service:
            activity_service.log("EXPENSE_CREATED", detail=f"{cat_var.get()} ${amount:.2f}")
        amount_entry.delete(0, "end")
        desc_entry.delete(0, "end")
        messagebox.showinfo("Success", "Expense added")
        refresh_list()

    style_mgr.create_button(form, text="Add Expense", command=add_expense).pack(anchor="w", padx=12, pady=(4, 10))

    # ── Expense List ──────────────────────────────────────────────
    list_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    list_section.pack(fill="both", expand=True)
    style_mgr.create_label(list_section, text="Expense History", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=16, pady=(12, 4))

    filter_row = style_mgr.create_frame(list_section, fg_color="transparent")
    filter_row.pack(fill="x", padx=16, pady=(0, 8))
    filter_row.grid_columnconfigure((1, 3), weight=0)

    style_mgr.create_label(filter_row, text="Category:", anchor="w").grid(row=0, column=0, sticky="w")
    filter_cat_var = tk.StringVar(value="All")
    customtkinter.CTkOptionMenu(
        filter_row, values=["All"] + EXPENSE_CATEGORIES, variable=filter_cat_var,
        fg_color=style_mgr.COLORS["surface_high"],
        button_color=style_mgr.COLORS["surface_highest"],
        button_hover_color=style_mgr.COLORS["border"],
        text_color=style_mgr.COLORS["text"], width=120,
    ).grid(row=0, column=1, sticky="w", padx=(8, 16))

    style_mgr.create_label(filter_row, text="From:", anchor="w").grid(row=0, column=2, sticky="w")
    filter_start_entry = style_mgr.create_entry(filter_row, width=100)
    filter_start_entry.grid(row=0, column=3, sticky="w", padx=(8, 8))
    filter_start_entry.insert(0, (datetime.now().replace(day=1)).strftime("%Y-%m-%d"))

    style_mgr.create_label(filter_row, text="To:", anchor="w").grid(row=0, column=4, sticky="w")
    filter_end_entry = style_mgr.create_entry(filter_row, width=100)
    filter_end_entry.grid(row=0, column=5, sticky="w", padx=(8, 8))
    filter_end_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    style_mgr.create_button(filter_row, text="Filter", style="secondary", width=80,
                            command=lambda: refresh_list()).grid(row=0, column=6, sticky="w", padx=(8, 0))

    columns = ("date", "category", "description", "amount")
    tree = ttk.Treeview(list_section, columns=columns, show="headings", height=10)
    for col in columns:
        tree.heading(col, text=col.title())
        tree.column(col, width=100)
    tree.pack(fill="both", expand=True, padx=16, pady=(8, 8))

    empty_label = style_mgr.create_label(list_section, text="", font_style="small",
                                         text_color=style_mgr.COLORS["text_muted"])
    empty_label.pack(anchor="w", padx=16, pady=(0, 2))

    summary_label = style_mgr.create_label(list_section, text="", font_style="small",
                                           text_color=style_mgr.COLORS["text_secondary"])
    summary_label.pack(anchor="w", padx=16, pady=(0, 4))

    btn_row = style_mgr.create_frame(list_section, fg_color="transparent")
    btn_row.pack(fill="x", padx=16, pady=(0, 12))

    # ── Edit / Detail Dialog ──────────────────────────────────────
    def show_expense_detail():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select an expense first.")
            return
        exp_id = int(sel[0])
        exp = finance_service.get_expense(exp_id)
        if not exp:
            messagebox.showerror("Error", "Expense not found.")
            return

        d = customtkinter.CTkToplevel(frame)
        d.geometry("480x360")
        d.title(f"Expense — ${exp['amount']:.2f}")
        d.transient(frame)
        d.grab_set()

        body = style_mgr.create_frame(d, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)
        body.grid_columnconfigure(0, weight=1)

        style_mgr.create_label(body, text="Expense Details", font_style="subheading").grid(
            row=0, column=0, sticky="w", pady=(0, 12))

        info = style_mgr.create_frame(body, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        info.grid(row=1, column=0, sticky="ew")
        info.grid_columnconfigure(1, weight=1)

        rows_data = [
            ("Amount:", f"${exp['amount']:.2f}"),
            ("Category:", exp.get("category", "")),
            ("Description:", exp.get("description", "")),
            ("Date:", exp.get("expense_date", "")),
            ("Created:", exp.get("created_at", "")[:10]),
        ]
        for i, (label, value) in enumerate(rows_data):
            style_mgr.create_label(info, text=label, font_style="body_bold").grid(
                row=i, column=0, sticky="w", padx=12, pady=(4, 0))
            style_mgr.create_label(info, text=value, font_style="small", wraplength=320).grid(
                row=i, column=1, sticky="w", padx=(8, 12), pady=(4, 0))

        btn_row_d = style_mgr.create_frame(body, fg_color="transparent")
        btn_row_d.grid(row=2, column=0, sticky="ew", pady=(16, 0))

        def detail_edit():
            d.destroy()
            edit_expense(exp)

        def detail_delete():
            if messagebox.askyesno("Confirm Delete", f"Delete ${exp['amount']:.2f} expense?\nThis cannot be undone."):
                finance_service.delete_expense(exp["id"])
                if activity_service:
                    activity_service.log("EXPENSE_DELETED", detail=f"{exp.get('category')} ${exp['amount']:.2f}")
                refresh_list()

        style_mgr.create_button(btn_row_d, text="Edit", command=detail_edit).pack(side="left", padx=(0, 8))
        style_mgr.create_button(btn_row_d, text="Delete", style="danger", command=detail_delete).pack(side="left", padx=(0, 8))
        style_mgr.create_button(btn_row_d, text="Close", style="secondary", command=d.destroy).pack(side="left")

    # ── Edit Dialog ──────────────────────────────────────────────
    def edit_expense(exp):
        d = customtkinter.CTkToplevel(frame)
        d.geometry("420x300")
        d.title(f"Edit Expense — ${exp['amount']:.2f}")
        d.transient(frame)
        d.grab_set()

        body = style_mgr.create_frame(d, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)
        body.grid_columnconfigure(0, weight=1)

        style_mgr.create_label(body, text="Edit Expense", font_style="subheading").grid(
            row=0, column=0, sticky="w", pady=(0, 12))

        ef = style_mgr.create_frame(body, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        ef.grid(row=1, column=0, sticky="ew")
        ef.grid_columnconfigure(1, weight=1)

        style_mgr.create_label(ef, text="Amount:", font_style="body_bold").grid(
            row=0, column=0, sticky="w", padx=12, pady=(8, 0))
        amt_e = style_mgr.create_entry(ef, width=160)
        amt_e.insert(0, str(exp["amount"]))
        amt_e.grid(row=0, column=1, sticky="w", padx=(8, 12), pady=(8, 0))

        style_mgr.create_label(ef, text="Category:", font_style="body_bold").grid(
            row=1, column=0, sticky="w", padx=12, pady=(8, 0))
        cat_var_e = tk.StringVar(value=exp.get("category", "miscellaneous"))
        customtkinter.CTkOptionMenu(ef, values=EXPENSE_CATEGORIES, variable=cat_var_e, width=140).grid(
            row=1, column=1, sticky="w", padx=(8, 12), pady=(8, 0))

        style_mgr.create_label(ef, text="Date:", font_style="body_bold").grid(
            row=2, column=0, sticky="w", padx=12, pady=(8, 0))
        date_e = style_mgr.create_entry(ef, width=120)
        date_e.insert(0, exp.get("expense_date", ""))
        date_e.grid(row=2, column=1, sticky="w", padx=(8, 12), pady=(8, 0))

        style_mgr.create_label(ef, text="Description:", font_style="body_bold").grid(
            row=3, column=0, sticky="w", padx=12, pady=(8, 12))
        desc_e = style_mgr.create_entry(ef, width=200)
        desc_e.insert(0, exp.get("description", ""))
        desc_e.grid(row=3, column=1, sticky="ew", padx=(8, 12), pady=(8, 12))

        def save_edit():
            try:
                amt = float(amt_e.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Invalid amount")
                return
            if amt <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
            finance_service.update_expense(exp["id"], amount=amt, category=cat_var_e.get(),
                                           expense_date=date_e.get().strip(), description=desc_e.get().strip())
            if activity_service:
                activity_service.log("EXPENSE_EDITED", detail=f"{cat_var_e.get()} ${amt:.2f}")
            d.destroy()
            refresh_list()

        btn_row_e = style_mgr.create_frame(body, fg_color="transparent")
        btn_row_e.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        style_mgr.create_button(btn_row_e, text="Save", command=save_edit).pack(side="left", padx=(0, 8))
        style_mgr.create_button(btn_row_e, text="Cancel", style="secondary", command=d.destroy).pack(side="left")

    # ── Action Buttons ────────────────────────────────────────────
    def delete_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select an expense")
            return
        exp_id = int(sel[0])
        exp = finance_service.get_expense(exp_id)
        if not exp:
            return
        if messagebox.askyesno("Confirm Delete", f"Delete ${exp['amount']:.2f} expense?\nThis cannot be undone."):
            finance_service.delete_expense(exp_id)
            if activity_service:
                activity_service.log("EXPENSE_DELETED", detail=f"{exp.get('category')} ${exp['amount']:.2f}")
            refresh_list()

    def refresh_list():
        for item in tree.get_children():
            tree.delete(item)
        fcat = filter_cat_var.get()
        fstart = filter_start_entry.get().strip()
        fend = filter_end_entry.get().strip()
        expenses = finance_service.get_expenses(
            start_date=fstart if fstart else "",
            end_date=fend if fend else "",
            category=fcat if fcat != "All" else "",
        )
        total = 0.0
        count = 0
        for e in expenses:
            total += e["amount"]
            count += 1
            tree.insert("", "end", iid=str(e["id"]), values=(
                e.get("expense_date", ""),
                e.get("category", ""),
                e.get("description", "")[:50],
                f"${e['amount']:.2f}",
            ))
        if count == 0:
            empty_label.configure(text="No expenses found.")
            summary_label.configure(text="")
        else:
            empty_label.configure(text="")
            summary_label.configure(text=f"{count} expense(s) — Total: ${total:.2f}")

    style_mgr.create_button(btn_row, text="View / Edit", command=show_expense_detail).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Delete Selected", style="danger",
                            command=delete_selected).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Refresh", command=refresh_list).pack(side="left")
    style_mgr.create_button(btn_row, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")

    tree.bind("<Double-1>", lambda _e: show_expense_detail())
    refresh_list()

    nav_frame = style_mgr.create_frame(frame, fg_color="transparent")
    nav_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
    style_mgr.create_button(nav_frame, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")
