import logging
from datetime import datetime
from tkinter import messagebox, StringVar
from customtkinter import CTkToplevel, CTkRadioButton


def setup_backup_restore_page(frames, StyleManager, csv_repository, show_frame, app):
    frame = frames["backup_restore"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    header_frame = StyleManager.create_section_header(
        frame,
        "Backup & Restore",
        "Create backups and restore previous CSV snapshots.",
    )
    header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))

    content = StyleManager.create_frame(
        frame,
        fg_color=StyleManager.COLORS["background"],
        border_width=0,
    )
    content.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
    content.grid_columnconfigure(0, weight=1)
    content.grid_columnconfigure(1, weight=1)
    content.grid_rowconfigure(0, weight=1)

    def create_backup():
        try:
            backup_file = csv_repository.create_backup()
            if backup_file:
                messagebox.showinfo("Success", f"Backup created at: {backup_file}")
            else:
                messagebox.showerror("Error", "Failed to create backup.")
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            messagebox.showerror("Error", "An error occurred while creating backup.")

    def restore_backup():
        try:
            backup_files = csv_repository.get_backup_files()
            if not backup_files:
                messagebox.showerror("Error", "No backups are available.")
                return

            restore_window = CTkToplevel(app)
            restore_window.geometry("560x440")
            restore_window.title("Restore Backup")
            restore_window.transient(app)
            restore_window.grab_set()

            main_frame = StyleManager.create_frame(restore_window)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            StyleManager.create_label(
                main_frame,
                text="Select a backup to restore",
                font_style="subheading"
            ).pack(pady=(0, 6))

            StyleManager.create_label(
                main_frame,
                text="Current data will be replaced by the selected backup",
                font_style="small",
                text_color=StyleManager.COLORS["text_muted"]
            ).pack(pady=(0, 20))

            backup_list = StyleManager.create_frame(
                main_frame,
                fg_color=StyleManager.COLORS["background"],
                border_color=StyleManager.COLORS["border"],
            )
            backup_list.pack(fill="both", expand=True)

            selected_backup = StringVar()

            for i, backup in enumerate(sorted(backup_files, reverse=True)):
                backup_date = backup.replace("backup_", "").replace(".csv", "")
                try:
                    formatted_date = datetime.strptime(backup_date, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    formatted_date = backup_date

                radio = CTkRadioButton(
                    backup_list,
                    text=f"  Backup {formatted_date}",
                    variable=selected_backup,
                    value=backup,
                    font=StyleManager.FONTS["body"],
                    fg_color=StyleManager.COLORS["primary_action"],
                    hover_color=StyleManager.COLORS["primary_hover"],
                    text_color=StyleManager.COLORS["text"],
                )
                radio.pack(pady=6, padx=16, anchor="w")

            if backup_files:
                selected_backup.set(backup_files[0])

            buttons_frame = StyleManager.create_frame(main_frame)
            buttons_frame.pack(fill="x", pady=(20, 0))
            buttons_frame.grid_columnconfigure(0, weight=1)
            buttons_frame.grid_columnconfigure(1, weight=1)

            left_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
            left_side.grid(row=0, column=0, sticky="w")
            right_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
            right_side.grid(row=0, column=1, sticky="e")

            def confirm_restore():
                try:
                    selected = selected_backup.get()
                    if not selected:
                        messagebox.showerror("Error", "Select a backup.")
                        return

                    if messagebox.askyesno("Confirm", "Are you sure you want to restore this backup? Current data will be replaced."):
                        if csv_repository.restore_backup(selected):
                            messagebox.showinfo("Success", "Backup restored successfully.")
                            restore_window.destroy()
                        else:
                            messagebox.showerror("Error", "Failed to restore backup.")
                except Exception as e:
                    logging.error(f"Error restoring backup: {str(e)}")
                    messagebox.showerror("Error", "An error occurred while restoring backup.")

            StyleManager.create_button(
                left_side,
                text="Restore",
                width=160,
                command=confirm_restore
            ).pack(side="left", pady=10)

            StyleManager.create_button(
                right_side,
                text="Cancel",
                style="secondary",
                width=120,
                command=restore_window.destroy
            ).pack(side="right", pady=10)

        except Exception as e:
            logging.error(f"Error in restore backup window: {str(e)}")
            messagebox.showerror("Error", "An error occurred while opening the restore window.")

    cards = [
        {
            "title": "Create Backup",
            "label": "Save a copy of the current customer data to a timestamped CSV file.",
            "metric": "BACKUP",
            "command": create_backup,
        },
        {
            "title": "Restore Backup",
            "label": "Replace current data with a previously saved backup snapshot.",
            "metric": "RESTORE",
            "command": restore_backup,
        },
    ]

    for index, card_data in enumerate(cards):
        card = StyleManager.create_frame(
            content,
            fg_color=StyleManager.COLORS["surface"],
            border_color=StyleManager.COLORS["border"],
            corner_radius=8,
        )
        card.grid(row=0, column=index, sticky="nsew", padx=8, pady=8)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        top = StyleManager.create_frame(card, fg_color="transparent", border_width=0)
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        top.grid_columnconfigure(0, weight=1)

        StyleManager.create_label(
            top,
            text=card_data["title"],
            font_style="subheading",
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        StyleManager.create_badge(
            top,
            text=card_data["metric"],
            tone="neutral",
        ).grid(row=0, column=1, sticky="e")

        StyleManager.create_label(
            card,
            text=card_data["label"],
            font_style="body",
            text_color=StyleManager.COLORS["text_secondary"],
            anchor="nw",
            justify="left",
            wraplength=300,
        ).grid(row=1, column=0, sticky="new", padx=16, pady=(0, 14))

        StyleManager.create_button(
            card,
            text="Open",
            style="primary",
            command=card_data["command"],
            width=96,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))

    back_frame = StyleManager.create_frame(frame)
    back_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))
    back_frame.grid_columnconfigure(0, weight=1)

    StyleManager.create_button(
        back_frame,
        text="Back",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    ).grid(row=0, column=0)
