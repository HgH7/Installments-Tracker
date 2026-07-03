"""Notes & Tags — manage customer notes and tags."""
import logging
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter

logger = logging.getLogger(__name__)

NOTE_CATEGORY_NAMES = ["general", "follow-up", "complaint", "meeting", "call", "payment", "other"]


def _get_all_notes(notes_service):
    """Return all notes via search_notes with empty query (matches all)."""
    return notes_service.search_notes("")


def setup_notes_tags_page(frames, style_mgr, notes_service, tags_service, show_frame,
                          activity_service=None):
    frame = frames.get("notes_tags")
    if not frame:
        return
    frame.configure(fg_color=style_mgr.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    for w in frame.winfo_children():
        w.destroy()

    _pending_customer_filter = [None]

    header = style_mgr.create_frame(frame, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
    style_mgr.create_label(header, text="Notes & Tags", font_style="heading", anchor="w").pack(side="left")

    scroll = customtkinter.CTkScrollableFrame(frame, fg_color="transparent")
    scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
    scroll.grid_columnconfigure(0, weight=1)

    list_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    list_section.pack(fill="both", expand=True)

    list_header = style_mgr.create_frame(list_section, fg_color="transparent")
    list_header.pack(fill="x", padx=16, pady=(12, 4))
    style_mgr.create_label(list_header, text="Notes", font_style="subheading", anchor="w").pack(side="left")

    filter_row = style_mgr.create_frame(list_header, fg_color="transparent")
    filter_row.pack(side="right")

    style_mgr.create_label(filter_row, text="Search:", anchor="w").pack(side="left", padx=(0, 4))
    search_entry = style_mgr.create_entry(filter_row, width=150)
    search_entry.pack(side="left", padx=(0, 8))

    style_mgr.create_label(filter_row, text="Category:", anchor="w").pack(side="left", padx=(0, 4))
    filter_cat_var = tk.StringVar(value="all")
    filter_cat_combo = customtkinter.CTkComboBox(
        filter_row, values=["all"] + NOTE_CATEGORY_NAMES,
        variable=filter_cat_var, width=110, command=lambda _: refresh_list(),
    )
    filter_cat_combo.pack(side="left", padx=(0, 8))

    style_mgr.create_label(filter_row, text="Customer:", anchor="w").pack(side="left", padx=(0, 4))
    filter_cust_entry = style_mgr.create_entry(filter_row, width=120)
    filter_cust_entry.pack(side="left", padx=(0, 4))
    style_mgr.create_button(filter_row, text="Go", width=30, command=refresh_list).pack(side="left", padx=(0, 4))
    style_mgr.create_button(filter_row, text="✕", width=28, command=lambda: (
        filter_cust_entry.delete(0, "end"), refresh_list()
    )).pack(side="left")

    tree_frame = style_mgr.create_frame(list_section, fg_color="transparent")
    tree_frame.pack(fill="both", expand=True, padx=16, pady=(4, 12))
    tree_frame.grid_columnconfigure(0, weight=1)
    tree_frame.grid_rowconfigure(0, weight=1)

    columns = ("id", "content", "category", "customer", "pinned", "created")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse", height=16)
    tree.grid(row=0, column=0, sticky="nsew")

    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    vsb.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=vsb.set)

    tree.column("id", width=0, stretch=False)
    tree.column("content", width=250, minwidth=150)
    tree.column("category", width=100, minwidth=80)
    tree.column("customer", width=140, minwidth=100)
    tree.column("pinned", width=60, minwidth=50, anchor="center")
    tree.column("created", width=120, minwidth=90)

    tree.heading("id", text="ID")
    tree.heading("content", text="Content")
    tree.heading("category", text="Category")
    tree.heading("customer", text="Customer")
    tree.heading("pinned", text="Pinned")
    tree.heading("created", text="Created")

    action_row_outer = style_mgr.create_frame(list_section, fg_color="transparent")
    action_row_outer.pack(fill="x", padx=16, pady=(0, 12))

    tags_display_frame = customtkinter.CTkScrollableFrame(
        action_row_outer, fg_color="transparent", height=24
    )
    tags_display_frame.pack(fill="x", pady=(0, 8))

    action_row = style_mgr.create_frame(action_row_outer, fg_color="transparent")
    action_row.pack(fill="x")

    tag_entry_var = tk.StringVar()

    def _add_tag_to_selected():
        sel = tree.selection()
        if not sel or sel[0] == "empty":
            messagebox.showinfo("Info", "Select a note first.")
            return
        tag_text = tag_entry_var.get().strip()
        if not tag_text:
            return
        note_id = int(sel[0])
        all_notes = _get_all_notes(notes_service) if not search_entry.get().strip() \
            else notes_service.search_notes(search_entry.get().strip())
        match = next((n for n in all_notes if n["id"] == note_id), None)
        if not match:
            return
        cid = match["customer_id"]
        tags_service.add_tag(cid, tag_text)
        if activity_service:
            activity_service.log("TAG_ADDED", customer_id=cid, detail=tag_text)
        tag_entry_var.set("")
        refresh_tags_panel()

    def refresh_list():
        for item in tree.get_children():
            tree.delete(item)
        q = search_entry.get().strip()
        cat = filter_cat_var.get()
        cust_name = filter_cust_entry.get().strip()

        if q:
            all_notes = notes_service.search_notes(q)
        else:
            all_notes = _get_all_notes(notes_service)

        if cat != "all":
            all_notes = [n for n in all_notes if n.get("category") == cat]
        if cust_name:
            all_notes = [n for n in all_notes
                         if cust_name.lower() in (n.get("customer_name") or "").lower()]

        for n in all_notes:
            tree.insert("", "end", iid=str(n["id"]), values=(
                n["id"],
                (n.get("content") or "")[:80],
                n.get("category", ""),
                n.get("customer_name", ""),
                "★" if n.get("is_pinned") else "",
                (n.get("created_at") or "")[:10],
            ))

        if not tree.get_children():
            tree.insert("", "end", iid="empty", values=("", "No notes found.", "", "", "", ""))

    def show_detail():
        sel = tree.selection()
        if not sel or sel[0] == "empty":
            messagebox.showinfo("Info", "Select a note first.")
            return
        note_id = int(sel[0])
        all_notes = _get_filtered_notes()
        note = next((n for n in all_notes if n["id"] == note_id), None)
        if not note:
            messagebox.showerror("Error", "Note not found.")
            return

        d = customtkinter.CTkToplevel(frame)
        d.geometry("500x520")
        d.title(f"Note — {note.get('customer_name', 'Unknown')}")
        d.transient(frame)
        d.grab_set()
        body = style_mgr.create_frame(d, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)
        body.grid_columnconfigure(0, weight=1)

        style_mgr.create_label(body, text="Note Details", font_style="subheading",
                               anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 12))

        info_frame = style_mgr.create_frame(body, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        info_frame.grid_columnconfigure(1, weight=1)

        rows = [
            ("Customer:", note.get("customer_name", "—")),
            ("Category:", note.get("category", "—")),
            ("Pinned:", "Yes" if note.get("is_pinned") else "No"),
            ("Created:", note.get("created_at", "—")[:16]),
            ("Updated:", note.get("updated_at", "—")[:16]),
        ]
        for i, (lbl, val) in enumerate(rows):
            style_mgr.create_label(info_frame, text=lbl, font_style="body_bold").grid(
                row=i, column=0, sticky="w", padx=12, pady=(6, 0))
            style_mgr.create_label(info_frame, text=str(val), font_style="body").grid(
                row=i, column=1, sticky="w", padx=(8, 12), pady=(6, 0))

        content_label = style_mgr.create_label(body, text="Content:", font_style="body_bold", anchor="w")
        content_label.grid(row=2, column=0, sticky="w", pady=(0, 4))

        content_text = customtkinter.CTkTextbox(body, height=120,
                                                fg_color=style_mgr.COLORS["surface_high"])
        content_text.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        content_text.insert("0.0", note.get("content", ""))
        content_text.configure(state="disabled")

        cat_frame = style_mgr.create_frame(body, fg_color="transparent")
        cat_frame.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        style_mgr.create_label(cat_frame, text="Tags:", font_style="body_bold",
                               anchor="w").pack(side="left", padx=(0, 8))
        tags = tags_service.get_tags(note.get("customer_id"))
        for tag in tags:
            tag_lbl = style_mgr.create_frame(cat_frame, fg_color=style_mgr.COLORS["primary"], corner_radius=4,
                                             height=22)
            tag_lbl.pack(side="left", padx=(0, 4))
            style_mgr.create_label(tag_lbl, text=tag, font_style="small",
                                   text_color="white").pack(side="left", padx=6, pady=2)

        btn_frame = style_mgr.create_frame(body, fg_color="transparent")
        btn_frame.grid(row=5, column=0, sticky="ew", pady=(8, 0))

        def do_pin():
            if notes_service.toggle_pin(note_id):
                refresh_list()
                d.destroy()

        def do_edit():
            content = note.get("content", "")
            cat = note.get("category", "general")
            edit_d = customtkinter.CTkToplevel(d)
            edit_d.geometry("460x340")
            edit_d.title("Edit Note")
            edit_d.transient(d)
            edit_d.grab_set()
            edit_body = style_mgr.create_frame(edit_d, fg_color="transparent")
            edit_body.pack(fill="both", expand=True, padx=20, pady=20)
            edit_body.grid_columnconfigure(0, weight=1)

            style_mgr.create_label(edit_body, text="Edit Note", font_style="subheading",
                                   anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 12))

            style_mgr.create_label(edit_body, text="Content:", anchor="w").grid(
                row=1, column=0, sticky="w", pady=(0, 4))
            edit_content = customtkinter.CTkTextbox(edit_body, height=100,
                                                    fg_color=style_mgr.COLORS["surface_high"])
            edit_content.grid(row=2, column=0, sticky="ew", pady=(0, 8))
            edit_content.insert("0.0", content)

            style_mgr.create_label(edit_body, text="Category:", anchor="w").grid(
                row=3, column=0, sticky="w", pady=(0, 4))
            edit_cat_var = tk.StringVar(value=cat)
            edit_cat_combo = customtkinter.CTkComboBox(
                edit_body, values=NOTE_CATEGORY_NAMES, variable=edit_cat_var, width=200)
            edit_cat_combo.grid(row=4, column=0, sticky="w", pady=(0, 12))

            def save_edit():
                new_content = edit_content.get("0.0", "end").strip()
                new_cat = edit_cat_var.get()
                if not new_content:
                    messagebox.showerror("Error", "Content cannot be empty.")
                    return
                if notes_service.update_note(note_id, content=new_content, category=new_cat):
                    if activity_service:
                        activity_service.log("NOTE_EDITED", customer_id=note.get("customer_id"),
                                             detail=f"Note {note_id}")
                    refresh_list()
                    edit_d.destroy()
                    d.destroy()
                else:
                    logger.exception("Failed to update note %s", note_id)
                    messagebox.showerror("Error", "Failed to update note.")

            style_mgr.create_button(edit_body, text="Save", command=save_edit,
                                    style="primary").grid(row=5, column=0, sticky="w", padx=(0, 8))
            style_mgr.create_button(edit_body, text="Cancel", command=edit_d.destroy,
                                    style="secondary").grid(row=5, column=0, sticky="w", padx=(84, 0))

        def do_delete():
            if not messagebox.askyesno("Confirm", "Delete this note?"):
                return
            if notes_service.delete_note(note_id):
                if activity_service:
                    activity_service.log("NOTE_DELETED", customer_id=note.get("customer_id"),
                                         detail=f"Note {note_id}")
                refresh_list()
                d.destroy()
            else:
                logger.exception("Failed to delete note %s", note_id)
                messagebox.showerror("Error", "Failed to delete note.")

        style_mgr.create_button(btn_frame, text="Toggle Pin", command=do_pin,
                                style="secondary").pack(side="left", padx=(0, 8))
        style_mgr.create_button(btn_frame, text="Edit", command=do_edit,
                                style="secondary").pack(side="left", padx=(0, 8))
        style_mgr.create_button(btn_frame, text="Delete", command=do_delete,
                                style="secondary").pack(side="left", padx=(0, 8))
        style_mgr.create_button(btn_frame, text="Close", command=d.destroy,
                                style="secondary").pack(side="right")

    def refresh_tags_panel():
        for w in tags_display_frame.winfo_children():
            w.destroy()
        sel = tree.selection()
        if not sel or sel[0] == "empty":
            return
        note_id = int(sel[0])
        all_notes = _get_filtered_notes()
        match = next((n for n in all_notes if n["id"] == note_id), None)
        if not match:
            return
        cust_id = match["customer_id"]
        tags = tags_service.get_tags(cust_id)
        add_frame = style_mgr.create_frame(tags_display_frame, fg_color="transparent")
        add_frame.pack(fill="x", pady=(0, 4))
        tag_entry = customtkinter.CTkEntry(add_frame, placeholder_text="Add tag...",
                                           textvariable=tag_entry_var, width=120)
        tag_entry.pack(side="left", padx=(0, 4))
        style_mgr.create_button(add_frame, text="+", width=28, command=_add_tag_to_selected).pack(side="left")
        for tag in tags:
            tag_frame = style_mgr.create_frame(tags_display_frame, fg_color=style_mgr.COLORS["primary"],
                                                corner_radius=4, height=22)
            tag_frame.pack(side="left", padx=(0, 4), pady=2)
            lbl = style_mgr.create_label(tag_frame, text=tag, font_style="small",
                                          text_color="white")
            lbl.pack(side="left", padx=6, pady=2)
            rem_btn = style_mgr.create_label(tag_frame, text=" ✕", font_style="small",
                                              text_color="#ff9999")
            rem_btn.pack(side="left", padx=(0, 4))
            rem_btn.bind("<Button-1>", lambda e, t=tag, c=cust_id: (
                tags_service.remove_tag(c, t),
                activity_service and activity_service.log("TAG_REMOVED", customer_id=c, detail=t),
                refresh_tags_panel()
            ))

    def _get_filtered_notes():
        q = search_entry.get().strip()
        cat = filter_cat_var.get()
        cust_name = filter_cust_entry.get().strip()
        notes = notes_service.search_notes(q) if q else _get_all_notes(notes_service)
        if cat != "all":
            notes = [n for n in notes if n.get("category") == cat]
        if cust_name:
            notes = [n for n in notes
                     if cust_name.lower() in (n.get("customer_name") or "").lower()]
        return notes

    tree.bind("<<TreeviewSelect>>", lambda e: refresh_tags_panel())
    tree.bind("<Double-1>", lambda e: show_detail())

    btn_row = style_mgr.create_frame(list_section, fg_color="transparent")
    btn_row.pack(fill="x", padx=16, pady=(0, 12))

    style_mgr.create_button(
        btn_row, text="Refresh", command=refresh_list,
        style="secondary"
    ).pack(side="left", padx=(0, 8))

    def navigate_to_customer_notes(customer_name=None):
        if customer_name:
            filter_cust_entry.delete(0, "end")
            filter_cust_entry.insert(0, customer_name)
        refresh_list()

    frame.navigate_to_customer_notes = navigate_to_customer_notes
    refresh_list()

    return scroll