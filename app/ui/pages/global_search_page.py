"""Global Search — unified search across customers, contracts, documents, tasks, expenses, and reminders."""

import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter

SEARCH_CATEGORIES = ["all", "customers", "contracts", "documents", "tasks", "expenses", "reminders"]


def setup_global_search_page(frames, style_mgr, global_search_service, show_frame):
    frame = frames.get("global_search")
    if not frame:
        return
    frame.configure(fg_color=style_mgr.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    for w in frame.winfo_children():
        w.destroy()

    header = style_mgr.create_frame(frame, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
    style_mgr.create_label(header, text="Global Search", font_style="heading", anchor="w").pack(side="left")

    scroll = customtkinter.CTkScrollableFrame(frame, fg_color="transparent")
    scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
    scroll.grid_columnconfigure(0, weight=1)

    search_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    search_section.pack(fill="x", pady=(0, 12))

    search_header = style_mgr.create_frame(search_section, fg_color="transparent")
    search_header.pack(fill="x", padx=16, pady=(12, 4))
    style_mgr.create_label(search_header, text="Search", font_style="subheading", anchor="w").pack(side="left")

    search_row = style_mgr.create_frame(search_section, fg_color="transparent")
    search_row.pack(fill="x", padx=16, pady=(4, 12))
    search_row.grid_columnconfigure(1, weight=1)

    style_mgr.create_label(search_row, text="Query:", anchor="w").grid(row=0, column=0, padx=(0, 8), sticky="w")
    search_entry = style_mgr.create_entry(search_row, width=300, placeholder_text="Search all entities...")
    search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

    style_mgr.create_label(search_row, text="Category:", anchor="w").grid(row=0, column=2, padx=(0, 8), sticky="w")
    cat_var = tk.StringVar(value="all")
    cat_combo = customtkinter.CTkComboBox(search_row, values=SEARCH_CATEGORIES, variable=cat_var, width=120)
    cat_combo.grid(row=0, column=3, padx=(0, 8))

    def do_search():
        refresh_results()

    search_entry.bind("<Return>", lambda _e: do_search())
    style_mgr.create_button(search_row, text="Search", width=100, command=do_search).grid(row=0, column=4)

    results_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    results_section.pack(fill="both", expand=True)

    results_header = style_mgr.create_frame(results_section, fg_color="transparent")
    results_header.pack(fill="x", padx=16, pady=(12, 4))
    style_mgr.create_label(results_header, text="Results", font_style="subheading", anchor="w").pack(side="left")

    columns = ("type", "title", "customer", "status", "date")
    tree = ttk.Treeview(results_section, columns=columns, show="headings", height=14)
    col_widths = {"type": 90, "title": 280, "customer": 140, "status": 80, "date": 100}
    col_labels = {"type": "Type", "title": "Title / Description", "customer": "Customer", "status": "Status", "date": "Date"}
    for col in columns:
        tree.heading(col, text=col_labels[col])
        tree.column(col, width=col_widths[col])
    tree.pack(fill="both", expand=True, padx=16, pady=(8, 4))

    empty_label = style_mgr.create_label(results_section, text="",
                                         font_style="small", text_color=style_mgr.COLORS["text_muted"])
    empty_label.pack(anchor="w", padx=16, pady=(0, 2))

    btn_row = style_mgr.create_frame(results_section, fg_color="transparent")
    btn_row.pack(fill="x", padx=16, pady=(0, 12))

    def get_selected_result():
        sel = tree.selection()
        if not sel:
            return None
        values = tree.item(sel[0], "values")
        result_type = values[0]
        # The iid stores the entity id, and we store result metadata on the tree item
        item_data = getattr(tree, "_result_data", {}).get(sel[0])
        return item_data

    def show_result_detail(result):
        if not result:
            return
        rtype = result["type"]
        rid = result["id"]
        d = customtkinter.CTkToplevel(frame)
        d.geometry("520x380")
        d.title(f"{rtype.title()} — {result.get('title', '')[:50]}")
        d.transient(frame)
        d.grab_set()

        body = style_mgr.create_frame(d, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)
        body.grid_columnconfigure(0, weight=1)

        style_mgr.create_label(body, text=f"{rtype.title()} Details", font_style="subheading").grid(
            row=0, column=0, sticky="w", pady=(0, 12))

        info = style_mgr.create_frame(body, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        info.grid(row=1, column=0, sticky="ew")
        info.grid_columnconfigure(1, weight=1)

        rows_data = [
            ("Type:", rtype.title()),
            ("Title:", result.get("title", "")),
            ("Customer:", result.get("customer_name", "") or "—"),
            ("Status:", result.get("status", "") or "—"),
            ("Date:", result.get("date", "")),
            ("Detail:", result.get("detail", "")),
        ]
        for i, (label, value) in enumerate(rows_data):
            style_mgr.create_label(info, text=label, font_style="body_bold").grid(
                row=i, column=0, sticky="w", padx=12, pady=(4, 0))
            style_mgr.create_label(info, text=value, font_style="small", wraplength=360).grid(
                row=i, column=1, sticky="w", padx=(8, 12), pady=(4, 0))

        btn_row_d = style_mgr.create_frame(body, fg_color="transparent")
        btn_row_d.grid(row=2, column=0, sticky="ew", pady=(16, 0))

        def navigate():
            d.destroy()
            if rtype == "customer":
                view_frame = frames.get("view")
                if view_frame:
                    show_frame(view_frame)
            elif rtype == "contract":
                show_frame(frames.get("contracts"))
            elif rtype == "document":
                show_frame(frames.get("documents"))
            elif rtype == "task":
                show_frame(frames.get("tasks"))
            elif rtype == "expense":
                show_frame(frames.get("expenses"))
            elif rtype == "reminder":
                rem_frame = frames.get("reminders")
                if rem_frame and hasattr(rem_frame, "navigate_to_customer_reminders"):
                    rem_frame.navigate_to_customer_reminders(customer_name=result.get("customer_name", ""))
                else:
                    show_frame(rem_frame)

        style_mgr.create_button(btn_row_d, text="Navigate", command=navigate).pack(side="left", padx=(0, 8))
        style_mgr.create_button(btn_row_d, text="Close", style="secondary", command=d.destroy).pack(side="left")

    def on_double_click(_e):
        sel = tree.selection()
        if not sel:
            return
        item_data = getattr(tree, "_result_data", {}).get(sel[0])
        if item_data:
            show_result_detail(item_data)

    def refresh_results():
        for item in tree.get_children():
            tree.delete(item)
        query = search_entry.get().strip()
        if not query:
            empty_label.configure(text="Enter a search query.")
            return
        category = cat_var.get()
        results = global_search_service.search(query, category=category)
        result_data = {}
        for i, r in enumerate(results):
            iid = f"r{i}"
            tree.insert("", "end", iid=iid, values=(
                r.get("type", ""),
                r.get("title", "")[:80],
                r.get("customer_name", ""),
                r.get("status", ""),
                r.get("date", ""),
            ))
            result_data[iid] = r
        tree._result_data = result_data
        count = len(results)
        if count == 0:
            empty_label.configure(text="No results found.")
        else:
            empty_label.configure(text=f"{count} result(s)")

    tree.bind("<Double-1>", on_double_click)

    style_mgr.create_button(btn_row, text="View Detail", command=lambda: show_result_detail(get_selected_result())).pack(
        side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Search", command=do_search).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_row, text="Refresh", command=refresh_results).pack(side="left")
    style_mgr.create_button(btn_row, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")

    search_entry.focus()

    nav_frame = style_mgr.create_frame(frame, fg_color="transparent")
    nav_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
    style_mgr.create_button(nav_frame, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")
