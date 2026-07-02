"""Task Manager — follow-up calls, meetings, document requests, callbacks."""

import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

import customtkinter
from app.services.task_service import TaskService, TASK_TYPES, TASK_PRIORITIES


def setup_tasks_page(frames, style_mgr, task_service: TaskService, show_frame):
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

    style_mgr.create_label(r2, text="Customer ID:", anchor="w").grid(row=0, column=0, sticky="w")
    cid_entry = style_mgr.create_entry(r2, width=80)
    cid_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

    style_mgr.create_label(r2, text="Due:", anchor="w").grid(row=0, column=2, sticky="w")
    due_entry = style_mgr.create_entry(r2, width=120)
    due_entry.insert(0, (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))
    due_entry.grid(row=0, column=3, sticky="ew", padx=(0, 8))

    style_mgr.create_label(r2, text="Description:", anchor="w").grid(row=0, column=4, sticky="w")
    desc_entry = style_mgr.create_entry(r2, width=200)
    desc_entry.grid(row=0, column=5, sticky="ew")

    def add_task():
        title = title_entry.get().strip()
        if not title:
            messagebox.showerror("Error", "Title is required")
            return
        try:
            cid = int(cid_entry.get().strip()) if cid_entry.get().strip() else None
        except ValueError:
            cid = None
        task_service.create_task(title=title, customer_id=cid, description=desc_entry.get().strip(),
                                  due_date=due_entry.get().strip(), priority=pri_var.get(), task_type=type_var.get())
        title_entry.delete(0, "end")
        desc_entry.delete(0, "end")
        cid_entry.delete(0, "end")
        messagebox.showinfo("Success", "Task created")
        refresh_list()

    style_mgr.create_button(form, text="Add Task", command=add_task).pack(anchor="w", padx=12, pady=(4, 10))

    list_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    list_section.pack(fill="both", expand=True)
    list_header = style_mgr.create_frame(list_section, fg_color="transparent")
    list_header.pack(fill="x", padx=16, pady=(12, 4))
    style_mgr.create_label(list_header, text="Tasks", font_style="subheading", anchor="w").pack(side="left")

    filter_var = tk.StringVar(value="all")
    filter_combo = customtkinter.CTkComboBox(list_header, values=["all", "pending", "in_progress", "completed", "overdue"],
                                              variable=filter_var, width=120, command=lambda _: refresh_list())
    filter_combo.pack(side="right")

    columns = ("title", "type", "priority", "customer", "due", "status")
    tree = ttk.Treeview(list_section, columns=columns, show="headings", height=10)
    for col in columns:
        tree.heading(col, text=col.title())
        tree.column(col, width=100)
    tree.pack(fill="both", expand=True, padx=16, pady=(8, 8))

    btn_row = style_mgr.create_frame(list_section, fg_color="transparent")
    btn_row.pack(fill="x", padx=16, pady=(0, 12))

    def mark_completed():
        sel = tree.selection()
        if not sel:
            return
        values = tree.item(sel[0])["values"]
        task_id = values[6] if len(values) > 6 else None
        if task_id:
            task_service.update_task_status(task_id, "completed")
            refresh_list()

    def refresh_list():
        for item in tree.get_children():
            tree.delete(item)
        f = filter_var.get()
        tasks = task_service.get_overdue_tasks() if f == "overdue" else task_service.get_tasks(status=f if f != "all" else "")
        for t in tasks:
            tree.insert("", "end", values=(t["title"][:50], t.get("task_type", ""), t.get("priority", ""),
                                            t.get("customer_name", ""), t.get("due_date", "")[:10], t["status"], t["id"]))

    style_mgr.create_button(btn_row, text="Mark Completed", command=mark_completed).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Refresh", command=refresh_list).pack(side="left")
    refresh_list()

    nav_frame = style_mgr.create_frame(frame, fg_color="transparent")
    nav_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
    style_mgr.create_button(nav_frame, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")
