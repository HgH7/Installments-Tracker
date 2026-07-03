"""Task Manager — follow-up calls, meetings, document requests, callbacks."""

import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

import customtkinter
from app.services.task_service import TaskService, TASK_TYPES, TASK_PRIORITIES


def setup_tasks_page(frames, style_mgr, task_service: TaskService, show_frame,
                     customer_service=None, activity_service=None):
    frame = frames.get("tasks")
    if not frame:
        return
    frame.configure(fg_color=style_mgr.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    for w in frame.winfo_children():
        w.destroy()

    header = style_mgr.create_frame(frame, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
    style_mgr.create_label(header, text="Task Manager", font_style="heading", anchor="w").pack(side="left")

    scroll = customtkinter.CTkScrollableFrame(frame, fg_color="transparent")
    scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
    scroll.grid_columnconfigure(0, weight=1)

    # ── New Task Form ─────────────────────────────────────────────
    form = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    form.pack(fill="x", pady=(0, 12))
    style_mgr.create_label(form, text="New Task", font_style="subheading", anchor="w").pack(anchor="w", padx=12, pady=(8, 4))

    r1 = style_mgr.create_frame(form, fg_color="transparent")
    r1.pack(fill="x", padx=12, pady=4)
    r1.grid_columnconfigure((1, 3, 5), weight=1)

    style_mgr.create_label(r1, text="Title:", anchor="w").grid(row=0, column=0, sticky="w")
    title_entry = style_mgr.create_entry(r1, width=180)
    title_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

    style_mgr.create_label(r1, text="Type:", anchor="w").grid(row=0, column=2, sticky="w")
    type_var = tk.StringVar(value="general")
    customtkinter.CTkComboBox(r1, values=TASK_TYPES, variable=type_var, width=120).grid(row=0, column=3, sticky="ew", padx=(0, 8))

    style_mgr.create_label(r1, text="Priority:", anchor="w").grid(row=0, column=4, sticky="w")
    pri_var = tk.StringVar(value="medium")
    customtkinter.CTkComboBox(r1, values=TASK_PRIORITIES, variable=pri_var, width=100).grid(row=0, column=5, sticky="ew")

    r2 = style_mgr.create_frame(form, fg_color="transparent")
    r2.pack(fill="x", padx=12, pady=4)
    r2.grid_columnconfigure((1, 3, 5), weight=1)

    style_mgr.create_label(r2, text="Customer Name:", anchor="w").grid(row=0, column=0, sticky="w")
    cname_entry = style_mgr.create_entry(r2, width=140)
    cname_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

    cid_entry = style_mgr.create_entry(r2, width=60)
    cid_entry.grid(row=0, column=2, sticky="w", padx=(0, 4))
    cid_entry.configure(placeholder_text="ID")

    style_mgr.create_label(r2, text="Due:", anchor="w").grid(row=0, column=3, sticky="w")
    due_entry = style_mgr.create_entry(r2, width=120)
    due_entry.insert(0, (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))
    due_entry.grid(row=0, column=4, sticky="ew", padx=(0, 8))

    style_mgr.create_label(r2, text="Description:", anchor="w").grid(row=0, column=5, sticky="w")
    desc_entry = style_mgr.create_entry(r2, width=200)
    desc_entry.grid(row=0, column=6, sticky="ew")

    def get_customer_id():
        cname = cname_entry.get().strip()
        cid_str = cid_entry.get().strip()
        if cname:
            try:
                return task_service.get_customer_id_by_name(cname)
            except Exception:
                return None
        elif cid_str:
            try:
                return int(cid_str)
            except ValueError:
                return None
        return None

    def add_task():
        title = title_entry.get().strip()
        if not title:
            messagebox.showerror("Error", "Title is required")
            return
        cid = get_customer_id()
        try:
            task_id = task_service.create_task(title=title, customer_id=cid,
                                               description=desc_entry.get().strip(),
                                               due_date=due_entry.get().strip(),
                                               priority=pri_var.get(), task_type=type_var.get())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create task: {e}")
            return
        if activity_service:
            activity_service.log("TASK_CREATED", customer_id=cid, detail=f"Task: {title}")
        title_entry.delete(0, "end")
        desc_entry.delete(0, "end")
        cname_entry.delete(0, "end")
        cid_entry.delete(0, "end")
        messagebox.showinfo("Success", "Task created")
        refresh_list()

    style_mgr.create_button(form, text="Add Task", command=add_task).pack(anchor="w", padx=12, pady=(4, 10))

    # ── Task List ─────────────────────────────────────────────────
    list_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    list_section.pack(fill="both", expand=True)
    list_header = style_mgr.create_frame(list_section, fg_color="transparent")
    list_header.pack(fill="x", padx=16, pady=(12, 4))
    style_mgr.create_label(list_header, text="Tasks", font_style="subheading", anchor="w").pack(side="left")

    filter_var = tk.StringVar(value="all")
    filter_combo = customtkinter.CTkComboBox(
        list_header, values=["all", "pending", "in_progress", "completed", "overdue", "today"],
        variable=filter_var, width=120, command=lambda _: refresh_list(),
    )
    filter_combo.pack(side="right")

    columns = ("title", "type", "priority", "customer", "due", "status")
    tree = ttk.Treeview(list_section, columns=columns, show="headings", height=10)
    for col in columns:
        tree.heading(col, text=col.title())
        tree.column(col, width=100)
    tree.pack(fill="both", expand=True, padx=16, pady=(8, 8))

    empty_label = style_mgr.create_label(list_section, text="", font_style="small",
                                         text_color=style_mgr.COLORS["text_muted"])
    empty_label.pack(anchor="w", padx=16, pady=(0, 4))

    btn_row = style_mgr.create_frame(list_section, fg_color="transparent")
    btn_row.pack(fill="x", padx=16, pady=(0, 12))

    # ── Detail Dialog ─────────────────────────────────────────────
    def show_task_detail():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a task first.")
            return
        task_id = int(sel[0])
        task = task_service.get_task(task_id)
        if not task:
            messagebox.showerror("Error", "Task not found.")
            return

        d = customtkinter.CTkToplevel(frame)
        d.geometry("560x500")
        d.title(f"Task — {task['title'][:40]}")
        d.transient(frame)
        d.grab_set()

        body = style_mgr.create_frame(d, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)
        body.grid_columnconfigure(0, weight=1)

        style_mgr.create_label(body, text="Task Details", font_style="subheading").grid(
            row=0, column=0, sticky="w", pady=(0, 12))

        info = style_mgr.create_frame(body, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        info.grid(row=1, column=0, sticky="ew")
        info.grid_columnconfigure(1, weight=1)

        rows_data = [
            ("Title:", task.get("title", "")),
            ("Description:", task.get("description", "")),
            ("Type:", task.get("task_type", "")),
            ("Priority:", task.get("priority", "")),
            ("Status:", task.get("status", "")),
            ("Customer:", task.get("customer_name", f"ID:{task.get('customer_id', '')}")),
            ("Due Date:", task.get("due_date", "")[:10] if task.get("due_date") else ""),
            ("Created:", task.get("created_at", "")[:10]),
            ("Updated:", task.get("updated_at", "")[:10]),
        ]
        for i, (label, value) in enumerate(rows_data):
            style_mgr.create_label(info, text=label, font_style="body_bold").grid(
                row=i, column=0, sticky="w", padx=12, pady=(4, 0))
            style_mgr.create_label(info, text=value, font_style="small", wraplength=380).grid(
                row=i, column=1, sticky="w", padx=(8, 12), pady=(4, 0))

        btn_row_d = style_mgr.create_frame(body, fg_color="transparent")
        btn_row_d.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        btn_row_d.grid_columnconfigure((0, 1, 2), weight=1)

        def detail_edit():
            d.destroy()
            edit_task(task)

        def detail_delete():
            if messagebox.askyesno("Confirm Delete", f"Delete task '{task['title']}'?\nThis cannot be undone."):
                task_service.delete_task(task["id"])
                if activity_service:
                    activity_service.log("TASK_DELETED", customer_id=task.get("customer_id"),
                                         detail=f"Task: {task['title']}")
                refresh_list()

        def detail_toggle_status():
            new_status = "pending" if task["status"] == "completed" else "completed"
            task_service.update_task_status(task["id"], new_status)
            action = "TASK_COMPLETED" if new_status == "completed" else "TASK_REOPENED"
            if activity_service:
                activity_service.log(action, customer_id=task.get("customer_id"),
                                     detail=f"Task: {task['title']}")
            d.destroy()
            refresh_list()

        toggle_label = "Reopen" if task["status"] == "completed" else "Mark Completed"
        style_mgr.create_button(btn_row_d, text="Edit", command=detail_edit).grid(row=0, column=0, padx=4)
        style_mgr.create_button(btn_row_d, text=toggle_label, command=detail_toggle_status).grid(row=0, column=1, padx=4)
        style_mgr.create_button(btn_row_d, text="Delete", style="danger", command=detail_delete).grid(row=0, column=2, padx=4)
        style_mgr.create_button(btn_row_d, text="Close", style="secondary", command=d.destroy).grid(row=0, column=3, padx=4)

    # ── Edit Dialog ──────────────────────────────────────────────
    def edit_task(task):
        d = customtkinter.CTkToplevel(frame)
        d.geometry("480x440")
        d.title(f"Edit — {task['title'][:40]}")
        d.transient(frame)
        d.grab_set()

        body = style_mgr.create_frame(d, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)
        body.grid_columnconfigure(0, weight=1)

        style_mgr.create_label(body, text="Edit Task", font_style="subheading").grid(
            row=0, column=0, sticky="w", pady=(0, 12))

        ef = style_mgr.create_frame(body, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        ef.grid(row=1, column=0, sticky="ew")
        ef.grid_columnconfigure(1, weight=1)

        fields = [
            ("Title:", "title", task.get("title", "")),
            ("Description:", "description", task.get("description", "")),
            ("Due Date:", "due_date", (task.get("due_date") or "")[:10]),
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
        style_mgr.create_label(ef, text="Type:", font_style="body_bold").grid(
            row=r, column=0, sticky="w", padx=12, pady=(8, 0))
        type_var_e = tk.StringVar(value=task.get("task_type", "general"))
        customtkinter.CTkComboBox(ef, values=TASK_TYPES, variable=type_var_e, width=160).grid(
            row=r, column=1, sticky="w", padx=(8, 12), pady=(8, 0))

        style_mgr.create_label(ef, text="Priority:", font_style="body_bold").grid(
            row=r+1, column=0, sticky="w", padx=12, pady=(8, 0))
        pri_var_e = tk.StringVar(value=task.get("priority", "medium"))
        customtkinter.CTkComboBox(ef, values=TASK_PRIORITIES, variable=pri_var_e, width=120).grid(
            row=r+1, column=1, sticky="w", padx=(8, 12), pady=(8, 0))

        style_mgr.create_label(ef, text="Status:", font_style="body_bold").grid(
            row=r+2, column=0, sticky="w", padx=12, pady=(8, 12))
        status_var_e = tk.StringVar(value=task.get("status", "pending"))
        customtkinter.CTkComboBox(ef, values=["pending", "in_progress", "completed", "cancelled"],
                                  variable=status_var_e, width=120).grid(
            row=r+2, column=1, sticky="w", padx=(8, 12), pady=(8, 12))

        def save_edit():
            title = entries["title"].get().strip()
            if not title:
                messagebox.showerror("Error", "Title is required")
                return
            try:
                task_service.update_task(task["id"], title=title,
                                         description=entries["description"].get().strip(),
                                         due_date=entries["due_date"].get().strip(),
                                         priority=pri_var_e.get(), task_type=type_var_e.get())
                new_status = status_var_e.get()
                if new_status != task["status"]:
                    task_service.update_task_status(task["id"], new_status)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update: {e}")
                return
            if activity_service:
                activity_service.log("TASK_EDITED", customer_id=task.get("customer_id"),
                                     detail=f"Task: {title}")
            d.destroy()
            refresh_list()

        btn_row_e = style_mgr.create_frame(body, fg_color="transparent")
        btn_row_e.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        style_mgr.create_button(btn_row_e, text="Save", command=save_edit).pack(side="left", padx=(0, 8))
        style_mgr.create_button(btn_row_e, text="Cancel", style="secondary", command=d.destroy).pack(side="left")

    # ── Task List Actions ────────────────────────────────────────
    def mark_completed():
        sel = tree.selection()
        if not sel:
            return
        task_id = int(sel[0])
        task = task_service.get_task(task_id)
        if not task:
            return
        new_status = "pending" if task["status"] == "completed" else "completed"
        task_service.update_task_status(task_id, new_status)
        action = "TASK_COMPLETED" if new_status == "completed" else "TASK_REOPENED"
        if activity_service:
            activity_service.log(action, customer_id=task.get("customer_id"),
                                 detail=f"Task: {task['title']}")
        refresh_list()

    def delete_task():
        sel = tree.selection()
        if not sel:
            return
        task_id = int(sel[0])
        task = task_service.get_task(task_id)
        if not task:
            return
        if messagebox.askyesno("Confirm Delete", f"Delete task '{task['title']}'?\nThis cannot be undone."):
            task_service.delete_task(task_id)
            if activity_service:
                activity_service.log("TASK_DELETED", customer_id=task.get("customer_id"),
                                     detail=f"Task: {task['title']}")
            refresh_list()

    now_str = datetime.now().strftime("%Y-%m-%d")

    def refresh_list():
        for item in tree.get_children():
            tree.delete(item)
        f = filter_var.get()
        if f == "overdue":
            tasks = task_service.get_overdue_tasks()
        elif f == "today":
            tasks = task_service.get_tasks_by_date(now_str)
        else:
            tasks = task_service.get_tasks(status=f if f != "all" else "")
        count = 0
        for t in tasks:
            tags = ()
            is_overdue = (t.get("due_date") or "") < now_str and t["status"] in ("pending", "in_progress")
            tree.insert("", "end", iid=str(t["id"]), values=(
                t["title"][:50], t.get("task_type", ""), t.get("priority", ""),
                t.get("customer_name", ""), (t.get("due_date") or "")[:10], t["status"],
            ))
            if is_overdue:
                tree.tag_configure("overdue", foreground="red")
                tree.item(str(t["id"]), tags=("overdue",))
            count += 1
        if count == 0:
            empty_label.configure(text="No tasks found.")
        else:
            empty_label.configure(text=f"{count} task(s)")

    style_mgr.create_button(btn_row, text="View / Edit", command=show_task_detail).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Toggle Complete", command=mark_completed).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Delete", style="danger", command=delete_task).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Refresh", command=refresh_list).pack(side="left")
    style_mgr.create_button(btn_row, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")

    tree.bind("<Double-1>", lambda _e: show_task_detail())

    def navigate_to_customer(customer_id=None, customer_name=None, switch_to_frame=True):
        if customer_name and customer_service:
            cname_entry.delete(0, "end")
            cname_entry.insert(0, customer_name)
        elif customer_id is not None:
            if hasattr(task_service, 'get_customer_name_for_doc'):
                name = task_service.get_customer_name_for_doc(customer_id)
                if not name.startswith("ID:"):
                    cname_entry.delete(0, "end")
                    cname_entry.insert(0, name)
        if switch_to_frame:
            show_frame(frame)
        refresh_list()

    frame.navigate_to_customer_tasks = navigate_to_customer

    refresh_list()

    nav_frame = style_mgr.create_frame(frame, fg_color="transparent")
    nav_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
    style_mgr.create_button(nav_frame, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")
