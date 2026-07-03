"""Reminder History — view, edit, resend, delete, and manage reminder status."""

import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter
from app.services.reminder_service import ReminderService
from app.services.notification_service import NotificationService


REMINDER_TRANSITIONS = {
    "draft": ["scheduled", "cancelled"],
    "scheduled": ["sent", "failed", "cancelled"],
    "sent": ["failed", "resent"],
    "failed": ["scheduled", "cancelled", "resent"],
    "cancelled": [],
}

REMINDER_STATUSES = list(REMINDER_TRANSITIONS.keys())


def setup_reminders_page(frames, style_mgr, reminder_service: ReminderService, show_frame,
                         activity_service=None, notification_service=None):
    frame = frames.get("reminders")
    if not frame:
        return
    frame.configure(fg_color=style_mgr.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    for w in frame.winfo_children():
        w.destroy()

    header = style_mgr.create_frame(frame, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
    style_mgr.create_label(header, text="Reminder History", font_style="heading", anchor="w").pack(side="left")

    scroll = customtkinter.CTkScrollableFrame(frame, fg_color="transparent")
    scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
    scroll.grid_columnconfigure(0, weight=1)

    list_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    list_section.pack(fill="both", expand=True)

    list_header = style_mgr.create_frame(list_section, fg_color="transparent")
    list_header.pack(fill="x", padx=16, pady=(12, 4))
    style_mgr.create_label(list_header, text="Reminders", font_style="subheading", anchor="w").pack(side="left")

    filter_row = style_mgr.create_frame(list_header, fg_color="transparent")
    filter_row.pack(side="right")

    style_mgr.create_label(filter_row, text="Customer:", anchor="w").pack(side="left", padx=(0, 4))
    search_customer_entry = style_mgr.create_entry(filter_row, width=120)
    search_customer_entry.pack(side="left", padx=(0, 8))

    style_mgr.create_label(filter_row, text="Status:", anchor="w").pack(side="left", padx=(0, 4))
    filter_status_var = tk.StringVar(value="all")
    filter_status_combo = customtkinter.CTkComboBox(
        filter_row, values=["all"] + REMINDER_STATUSES,
        variable=filter_status_var, width=100, command=lambda _: refresh_list(),
    )
    filter_status_combo.pack(side="left", padx=(0, 8))

    style_mgr.create_label(filter_row, text="Phone:", anchor="w").pack(side="left", padx=(0, 4))
    search_phone_entry = style_mgr.create_entry(filter_row, width=100)
    search_phone_entry.pack(side="left", padx=(0, 8))

    def do_search():
        refresh_list()

    style_mgr.create_button(filter_row, text="Search", width=70, command=do_search).pack(side="left")

    columns = ("customer", "phone", "date", "amount", "status", "sent_at")
    tree = ttk.Treeview(list_section, columns=columns, show="headings", height=10)
    col_widths = {"customer": 120, "phone": 110, "date": 100, "amount": 80, "status": 80, "sent_at": 120}
    col_labels = {"customer": "Customer", "phone": "Phone", "date": "Installment Date",
                  "amount": "Amount", "status": "Status", "sent_at": "Sent At"}
    for col in columns:
        tree.heading(col, text=col_labels[col])
        tree.column(col, width=col_widths[col])
    tree.pack(fill="both", expand=True, padx=16, pady=(8, 4))

    empty_label = style_mgr.create_label(list_section, text="", font_style="small",
                                         text_color=style_mgr.COLORS["text_muted"])
    empty_label.pack(anchor="w", padx=16, pady=(0, 2))

    btn_row = style_mgr.create_frame(list_section, fg_color="transparent")
    btn_row.pack(fill="x", padx=16, pady=(0, 12))

    ns = notification_service or NotificationService

    def show_reminder_detail():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a reminder first.")
            return
        reminder_id = int(sel[0])
        reminder = reminder_service.get_reminder(reminder_id)
        if not reminder:
            messagebox.showerror("Error", "Reminder not found.")
            return

        d = customtkinter.CTkToplevel(frame)
        d.geometry("560x500")
        d.title(f"Reminder — {reminder.get('customer_name', '')[:40]}")
        d.transient(frame)
        d.grab_set()

        body = style_mgr.create_frame(d, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)
        body.grid_columnconfigure(0, weight=1)

        style_mgr.create_label(body, text="Reminder Details", font_style="subheading").grid(
            row=0, column=0, sticky="w", pady=(0, 12))

        info = style_mgr.create_frame(body, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        info.grid(row=1, column=0, sticky="ew")
        info.grid_columnconfigure(1, weight=1)

        rows_data = [
            ("Customer:", reminder.get("customer_name", "")),
            ("Phone:", reminder.get("phone", "")),
            ("Installment Date:", reminder.get("installment_date", "")),
            ("Amount:", f"{reminder.get('amount', 0):.2f}"),
            ("Status:", reminder.get("status", "")),
            ("Message:", reminder.get("message", "")[:200]),
            ("Sent At:", reminder.get("sent_at", "")),
            ("Created:", (reminder.get("created_at") or "")[:19]),
        ]
        for i, (label, value) in enumerate(rows_data):
            style_mgr.create_label(info, text=label, font_style="body_bold").grid(
                row=i, column=0, sticky="w", padx=12, pady=(4, 0))
            style_mgr.create_label(info, text=value, font_style="small", wraplength=380).grid(
                row=i, column=1, sticky="w", padx=(8, 12), pady=(4, 0))

        btn_row_d = style_mgr.create_frame(body, fg_color="transparent")
        btn_row_d.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        btn_row_d.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def detail_edit():
            d.destroy()
            edit_reminder(reminder)

        def detail_delete():
            if messagebox.askyesno("Confirm Delete", f"Delete reminder for {reminder.get('customer_name', '')}?\nThis cannot be undone."):
                reminder_service.delete_reminder(reminder["id"])
                if activity_service:
                    activity_service.log("REMINDER_DELETED", customer_id=reminder.get("customer_id"),
                                         detail=f"Reminder: {reminder.get('customer_name', '')}")
                refresh_list()

        def detail_resend():
            phone = reminder.get("phone", "")
            message = reminder.get("message", "")
            if not phone:
                messagebox.showerror("Error", "No phone number for this reminder.")
                return
            if ns.open_whatsapp(phone, message):
                reminder_service.update_reminder_status(reminder["id"], "sent")
                if activity_service:
                    activity_service.log("REMINDER_RESENT", customer_id=reminder.get("customer_id"),
                                         detail=f"Reminder: {reminder.get('customer_name', '')}")
                d.destroy()
                refresh_list()

        def detail_advance():
            status = reminder.get("status", "draft")
            transitions = REMINDER_TRANSITIONS.get(status, [])
            if not transitions:
                messagebox.showinfo("Info", f"No transitions from '{status}'.")
                return
            adv = customtkinter.CTkToplevel(d)
            adv.geometry("320x200")
            adv.title("Advance Status")
            adv.transient(d)
            adv.grab_set()
            body_a = style_mgr.create_frame(adv, fg_color="transparent")
            body_a.pack(fill="both", expand=True, padx=20, pady=20)
            body_a.grid_columnconfigure(0, weight=1)
            style_mgr.create_label(body_a, text=f"Current: {status}", font_style="subheading").grid(
                row=0, column=0, sticky="w", pady=(0, 12))
            trans_var = tk.StringVar(value=transitions[0])
            trans_combo = customtkinter.CTkComboBox(body_a, values=transitions, variable=trans_var, width=160)
            trans_combo.grid(row=1, column=0, sticky="w", pady=(0, 16))

            def apply_transition():
                new_status = trans_var.get()
                reminder_service.update_reminder_status(reminder["id"], new_status)
                action_map = {"sent": "REMINDER_SENT", "cancelled": "REMINDER_CANCELLED"}
                action = action_map.get(new_status, "REMINDER_EDITED")
                if activity_service:
                    activity_service.log(action, customer_id=reminder.get("customer_id"),
                                         detail=f"Reminder {reminder.get('customer_name', '')} -> {new_status}")
                adv.destroy()
                d.destroy()
                refresh_list()

            style_mgr.create_button(body_a, text="Apply", command=apply_transition).grid(row=2, column=0, sticky="w")
            style_mgr.create_button(body_a, text="Cancel", style="secondary",
                                    command=adv.destroy).grid(row=2, column=0, sticky="e")

        can_edit = reminder.get("status") in ("draft", "scheduled")
        can_resend = reminder.get("status") in ("sent", "failed")
        can_advance = bool(REMINDER_TRANSITIONS.get(reminder.get("status", ""), []))

        if can_edit:
            style_mgr.create_button(btn_row_d, text="Edit", command=detail_edit).grid(row=0, column=0, padx=4)
        if can_advance:
            style_mgr.create_button(btn_row_d, text="Status", command=detail_advance).grid(row=0, column=1, padx=4)
        if can_resend:
            style_mgr.create_button(btn_row_d, text="Resend", command=detail_resend).grid(row=0, column=2, padx=4)
        style_mgr.create_button(btn_row_d, text="Delete", style="danger", command=detail_delete).grid(row=0, column=3, padx=4)
        style_mgr.create_button(btn_row_d, text="Close", style="secondary", command=d.destroy).grid(row=0, column=4, padx=4)

    def edit_reminder(reminder):
        if reminder.get("status") not in ("draft", "scheduled"):
            messagebox.showinfo("Info", "Only draft or scheduled reminders can be edited.")
            return

        d = customtkinter.CTkToplevel(frame)
        d.geometry("480x400")
        d.title(f"Edit Reminder — {reminder.get('customer_name', '')[:40]}")
        d.transient(frame)
        d.grab_set()

        body = style_mgr.create_frame(d, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)
        body.grid_columnconfigure(0, weight=1)

        style_mgr.create_label(body, text="Edit Reminder", font_style="subheading").grid(
            row=0, column=0, sticky="w", pady=(0, 12))

        ef = style_mgr.create_frame(body, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        ef.grid(row=1, column=0, sticky="ew")
        ef.grid_columnconfigure(1, weight=1)

        fields = [
            ("Customer Name:", "customer_name", reminder.get("customer_name", "")),
            ("Phone:", "phone", reminder.get("phone", "")),
            ("Installment Date:", "installment_date", reminder.get("installment_date", "")),
            ("Amount:", "amount", str(reminder.get("amount", 0))),
        ]
        entries = {}
        for i, (label, key, value) in enumerate(fields):
            style_mgr.create_label(ef, text=label, font_style="body_bold").grid(
                row=i, column=0, sticky="w", padx=12, pady=(8, 0))
            e = style_mgr.create_entry(ef, width=280)
            e.insert(0, value)
            e.grid(row=i, column=1, sticky="ew", padx=(8, 12), pady=(8, 0))
            entries[key] = e

        r = len(fields)
        style_mgr.create_label(ef, text="Message:", font_style="body_bold").grid(
            row=r, column=0, sticky="nw", padx=12, pady=(8, 0))
        msg_text = style_mgr.create_textbox(ef, width=280, height=80, readonly=False)
        msg_text.grid(row=r, column=1, sticky="ew", padx=(8, 12), pady=(8, 0))
        msg_text.insert("end", reminder.get("message", ""))

        def save_edit():
            customer_name = entries["customer_name"].get().strip()
            phone = entries["phone"].get().strip()
            if not customer_name:
                messagebox.showerror("Error", "Customer name is required")
                return
            try:
                amount = float(entries["amount"].get().strip()) if entries["amount"].get().strip() else 0.0
            except ValueError:
                messagebox.showerror("Error", "Amount must be a valid number")
                return
            message = msg_text.get("1.0", "end-1c").strip()
            reminder_service.update_reminder(
                reminder["id"],
                customer_name=customer_name,
                phone=phone,
                installment_date=entries["installment_date"].get().strip(),
                amount=amount,
                message=message,
            )
            if activity_service:
                activity_service.log("REMINDER_EDITED", customer_id=reminder.get("customer_id"),
                                     detail=f"Reminder: {customer_name}")
            d.destroy()
            refresh_list()

        btn_row_e = style_mgr.create_frame(body, fg_color="transparent")
        btn_row_e.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        style_mgr.create_button(btn_row_e, text="Save", command=save_edit).pack(side="left", padx=(0, 8))
        style_mgr.create_button(btn_row_e, text="Cancel", style="secondary", command=d.destroy).pack(side="left")

    def delete_reminder():
        sel = tree.selection()
        if not sel:
            return
        reminder_id = int(sel[0])
        reminder = reminder_service.get_reminder(reminder_id)
        if not reminder:
            return
        if messagebox.askyesno("Confirm Delete", f"Delete reminder for {reminder.get('customer_name', '')}?\nThis cannot be undone."):
            reminder_service.delete_reminder(reminder_id)
            if activity_service:
                activity_service.log("REMINDER_DELETED", customer_id=reminder.get("customer_id"),
                                     detail=f"Reminder: {reminder.get('customer_name', '')}")
            refresh_list()

    def resend_reminder():
        sel = tree.selection()
        if not sel:
            return
        reminder_id = int(sel[0])
        reminder = reminder_service.get_reminder(reminder_id)
        if not reminder:
            return
        phone = reminder.get("phone", "")
        message = reminder.get("message", "")
        if not phone:
            messagebox.showerror("Error", "No phone number for this reminder.")
            return
        if ns.open_whatsapp(phone, message):
            reminder_service.update_reminder_status(reminder_id, "sent")
            if activity_service:
                activity_service.log("REMINDER_RESENT", customer_id=reminder.get("customer_id"),
                                     detail=f"Reminder: {reminder.get('customer_name', '')}")
            refresh_list()

    def advance_reminder_status():
        sel = tree.selection()
        if not sel:
            return
        reminder_id = int(sel[0])
        reminder = reminder_service.get_reminder(reminder_id)
        if not reminder:
            return
        status = reminder.get("status", "draft")
        transitions = REMINDER_TRANSITIONS.get(status, [])
        if not transitions:
            messagebox.showinfo("Info", f"No transitions from '{status}'.")
            return
        d = customtkinter.CTkToplevel(frame)
        d.geometry("320x200")
        d.title("Advance Status")
        d.transient(frame)
        d.grab_set()
        body_a = style_mgr.create_frame(d, fg_color="transparent")
        body_a.pack(fill="both", expand=True, padx=20, pady=20)
        body_a.grid_columnconfigure(0, weight=1)
        style_mgr.create_label(body_a, text=f"Current: {status}", font_style="subheading").grid(
            row=0, column=0, sticky="w", pady=(0, 12))
        trans_var = tk.StringVar(value=transitions[0])
        trans_combo = customtkinter.CTkComboBox(body_a, values=transitions, variable=trans_var, width=160)
        trans_combo.grid(row=1, column=0, sticky="w", pady=(0, 16))

        def apply_transition():
            new_status = trans_var.get()
            reminder_service.update_reminder_status(reminder_id, new_status)
            action_map = {"sent": "REMINDER_SENT", "cancelled": "REMINDER_CANCELLED"}
            action = action_map.get(new_status, "REMINDER_EDITED")
            if activity_service:
                activity_service.log(action, customer_id=reminder.get("customer_id"),
                                     detail=f"Reminder {reminder.get('customer_name', '')} -> {new_status}")
            d.destroy()
            refresh_list()

        style_mgr.create_button(body_a, text="Apply", command=apply_transition).grid(row=2, column=0, sticky="w")
        style_mgr.create_button(body_a, text="Cancel", style="secondary",
                                command=d.destroy).grid(row=2, column=0, sticky="e")

    def refresh_list():
        for item in tree.get_children():
            tree.delete(item)
        customer_filter = search_customer_entry.get().strip()
        status_filter = filter_status_var.get()
        phone_filter = search_phone_entry.get().strip()
        if customer_filter or status_filter != "all" or phone_filter:
            reminders = reminder_service.search_reminders(
                customer_name=customer_filter or None,
                status=status_filter if status_filter != "all" else None,
                phone=phone_filter or None,
            )
        else:
            reminders = reminder_service.get_history(limit=200)
        count = 0
        for r in reminders:
            tree.insert("", "end", iid=str(r["id"]), values=(
                r.get("customer_name", ""),
                r.get("phone", ""),
                r.get("installment_date", ""),
                f"{r.get('amount', 0):.2f}",
                r.get("status", ""),
                (r.get("sent_at") or "")[:19],
            ))
            count += 1
        if count == 0:
            empty_label.configure(text="No reminders found.")
        else:
            empty_label.configure(text=f"{count} reminder(s)")

    style_mgr.create_button(btn_row, text="View / Edit", command=show_reminder_detail).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Delete", style="danger", command=delete_reminder).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Resend", command=resend_reminder).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Advance Status", command=advance_reminder_status).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Refresh", command=refresh_list).pack(side="left")
    style_mgr.create_button(btn_row, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")

    tree.bind("<Double-1>", lambda _e: show_reminder_detail())

    def navigate_to_customer_reminders(customer_name=None, switch_to_frame=True):
        if customer_name:
            search_customer_entry.delete(0, "end")
            search_customer_entry.insert(0, customer_name)
            filter_status_var.set("all")
            search_phone_entry.delete(0, "end")
        if switch_to_frame:
            show_frame(frame)
        refresh_list()

    frame.navigate_to_customer_reminders = navigate_to_customer_reminders

    refresh_list()

    nav_frame = style_mgr.create_frame(frame, fg_color="transparent")
    nav_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
    style_mgr.create_button(nav_frame, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")
