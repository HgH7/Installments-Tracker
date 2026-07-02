import json
import os
from datetime import datetime
from tkinter import messagebox, ttk

import customtkinter

from app.settings import settings


def setup_backup_manager_page(frames, StyleManager, csv_repository, show_frame, app, activity_service=None):
    frame = frames["backup_manager"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    header = StyleManager.create_section_header(
        frame, "Backup Manager", "Create, view, restore, and manage backups."
    )
    header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))

    content = StyleManager.create_frame(frame, fg_color="transparent", border_width=0)
    content.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
    content.grid_columnconfigure(0, weight=1)
    content.grid_rowconfigure(1, weight=1)

    action_row = StyleManager.create_frame(content, fg_color="transparent", border_width=0)
    action_row.grid(row=0, column=0, sticky="ew", pady=(0, 12))

    StyleManager.create_button(action_row, text="Create Backup", width=140, command=lambda: do_create()).pack(side="left", padx=(0, 8))
    StyleManager.create_button(action_row, text="Refresh List", width=120, style="secondary", command=lambda: load_backups()).pack(side="left", padx=(0, 8))
    StyleManager.create_button(action_row, text="Delete Selected", width=130, style="danger", command=lambda: do_delete()).pack(side="left", padx=(0, 8))

    status_label = StyleManager.create_label(action_row, text="", font_style="small",
                                             text_color=StyleManager.COLORS["text_secondary"])
    status_label.pack(side="right")

    table_frame = StyleManager.create_frame(content, fg_color=StyleManager.COLORS["surface_low"])
    table_frame.grid(row=1, column=0, sticky="nsew")
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)

    columns = ("Backup", "Date", "Size", "Records", "Compressed")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Custom.Treeview")
    col_widths = {"Backup": 200, "Date": 150, "Size": 80, "Records": 80, "Compressed": 80}
    for col in columns:
        tree.column(col, width=col_widths[col], anchor="center")
        tree.heading(col, text=col)
    tree.grid(row=0, column=0, sticky="nsew")
    scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    scroll.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scroll.set)

    def load_backups():
        for row in tree.get_children():
            tree.delete(row)
        files = csv_repository.get_backup_files()
        if not files:
            status_label.configure(text="No backups available")
            tree.insert("", "end", values=("—", "—", "—", "—", "—"))
            return

        for f in files:
            fpath = os.path.join(csv_repository.backup_folder, f)
            size_str = "?"
            try:
                sz = os.path.getsize(fpath)
                size_str = f"{sz / 1024:.1f} KB" if sz < 1024 * 1024 else f"{sz / (1024 * 1024):.1f} MB"
            except OSError:
                pass

            records = "?"
            meta_path = os.path.join(csv_repository.backup_folder, f.replace(".csv.gz", "").replace(".csv", "") + ".meta.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path) as mf:
                        meta = json.load(mf)
                    records = str(meta.get("records", "?"))
                except (OSError, json.JSONDecodeError):
                    pass

            display = f.replace("backup_", "").replace(".csv.gz", "").replace(".csv", "")
            try:
                display = datetime.strptime(display, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

            compressed = "Yes" if f.endswith(".gz") else "No"
            tree.insert("", "end", values=(f, display, size_str, records, compressed))

        status_label.configure(text=f"Backups: {len(files)}")

    def do_create():
        path = csv_repository.create_backup()
        if path:
            if activity_service:
                activity_service.log("Backup created", detail=os.path.basename(path))
            messagebox.showinfo("Success", f"Backup created: {os.path.basename(path)}")
            load_backups()
        else:
            messagebox.showerror("Error", "Failed to create backup.")

    def do_delete():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a backup to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete the selected backup(s)? This cannot be undone."):
            return
        for item in selected:
            vals = tree.item(item)["values"]
            fname = vals[0]
            fpath = os.path.join(csv_repository.backup_folder, fname)
            try:
                if os.path.exists(fpath):
                    os.unlink(fpath)
                base = fname.replace(".csv.gz", "").replace(".csv", "")
                meta = os.path.join(csv_repository.backup_folder, f"{base}.meta.json")
                if os.path.exists(meta):
                    os.unlink(meta)
            except OSError as e:
                messagebox.showerror("Error", f"Failed to delete {fname}: {e}")
        load_backups()

    def do_restore():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a backup to restore.")
            return
        vals = tree.item(selected[0])["values"]
        fname = vals[0]
        if not messagebox.askyesno("Confirm", f"Restore backup {fname}? Current data will be replaced."):
            return
        if csv_repository.restore_backup(fname):
            if activity_service:
                activity_service.log("Backup restored", detail=fname)
            messagebox.showinfo("Success", "Backup restored.")
        else:
            messagebox.showerror("Error", "Failed to restore backup.")

    StyleManager.create_button(action_row, text="Restore Selected", width=140, command=do_restore).pack(side="left", padx=(8, 0))

    load_backups()

    nav_frame = StyleManager.create_frame(frame)
    nav_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))
    nav_frame.grid_columnconfigure(0, weight=1)
    left = StyleManager.create_frame(nav_frame, fg_color="transparent")
    left.grid(row=0, column=0, sticky="w")
    right = StyleManager.create_frame(nav_frame, fg_color="transparent")
    right.grid(row=0, column=1, sticky="e")

    StyleManager.create_button(left, text="Backup Settings", width=130, style="secondary",
                               command=lambda: show_backup_settings()).pack(side="left", pady=10)

    StyleManager.create_button(right, text="Back", style="secondary", width=100,
                               command=lambda: show_frame(frames["home"])).pack(side="right", pady=10)

    def show_backup_settings():
        settings_window = customtkinter.CTkToplevel(app)
        settings_window.geometry("480x400")
        settings_window.title("Backup Settings")
        settings_window.transient(app)
        settings_window.grab_set()

        main = StyleManager.create_frame(settings_window)
        main.pack(fill="both", expand=True, padx=20, pady=20)
        main.grid_columnconfigure(1, weight=1)

        row = 0
        StyleManager.create_label(main, text="Max backups to keep:", font_style="label").grid(row=row, column=0, sticky="w", pady=6)
        max_entry = StyleManager.create_entry(main)
        max_entry.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=6)
        max_entry.insert(0, str(settings.get("backup_max_count", 50)))
        row += 1

        compress_var = tk.BooleanVar(value=settings.get("backup_compress", True))
        StyleManager.create_checkbox(main, text="Compress backups (gzip)", variable=compress_var).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=6)
        row += 1

        auto_var = tk.BooleanVar(value=settings.get("auto_backup_on_start", False))
        StyleManager.create_checkbox(main, text="Create backup on application start", variable=auto_var).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=6)
        row += 1

        def do_save():
            try:
                settings.set("backup_max_count", int(max_entry.get()))
            except ValueError:
                messagebox.showerror("Error", "Invalid max backup count.")
                return
            settings.set("backup_compress", compress_var.get())
            settings.set("auto_backup_on_start", auto_var.get())
            messagebox.showinfo("Success", "Backup settings saved.")
            settings_window.destroy()

        btn_frame = StyleManager.create_frame(main, fg_color="transparent", border_width=0)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        btn_frame.grid_columnconfigure(0, weight=1)
        StyleManager.create_button(btn_frame, text="Save Settings", width=140, command=do_save).pack(side="left")
        StyleManager.create_button(btn_frame, text="Cancel", style="secondary", width=100,
                                   command=settings_window.destroy).pack(side="right")


import tkinter

tk = tkinter
