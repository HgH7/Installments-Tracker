import os


def setup_home_page(frames, StyleManager, show_frame, app):
    frame = frames["home"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    header_frame = StyleManager.create_frame(
        frame,
        fg_color="transparent",
        border_width=0,
    )
    header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 14))
    header_frame.grid_columnconfigure(0, weight=1)

    StyleManager.create_label(
        header_frame,
        text="Installment Tracker",
        font_style="heading",
        anchor="w",
    ).grid(row=0, column=0, sticky="w")
    StyleManager.create_label(
        header_frame,
        text="Manage customers, installments, backups, and reminders from one local workspace.",
        font_style="small",
        text_color=StyleManager.COLORS["text_muted"],
        anchor="w",
    ).grid(row=1, column=0, sticky="w", pady=(3, 0))

    content = StyleManager.create_frame(
        frame,
        fg_color=StyleManager.COLORS["background"],
        border_width=0,
    )
    content.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
    for column in range(3):
        content.grid_columnconfigure(column, weight=1, uniform="home_cards")
    for row in range(2):
        content.grid_rowconfigure(row, weight=1, uniform="home_cards")

    cards = [
        {
            "title": "Add Customer",
            "label": "Create a new installment customer record",
            "metric": "NEW",
            "command": lambda: show_frame(frames["add"]),
        },
        {
            "title": "Customers",
            "label": "Search, edit, export, and review customer data",
            "metric": "TABLE",
            "command": lambda: show_frame(frames["view"]),
        },
        {
            "title": "Installments",
            "label": "Review payment schedules and update installment status",
            "metric": "PAY",
            "command": lambda: show_frame(frames["manage"]),
        },
        {
            "title": "Backup & Restore",
            "label": "Create backups and restore previous CSV snapshots",
            "metric": "CSV",
            "command": lambda: show_frame(frames["backup_restore"]),
        },
        {
            "title": "Notifications",
            "label": "Select due installments and prepare WhatsApp reminders",
            "metric": "MSG",
            "command": lambda: show_frame(frames["send_notification"]),
        },
        {
            "title": "Customer Files",
            "label": "Open the local folder for customer attachments",
            "metric": "FILES",
            "command": lambda: os.startfile("customer_files"),
        },
    ]

    for index, card in enumerate(cards):
        row, column = divmod(index, 3)
        card_frame = StyleManager.create_frame(
            content,
            fg_color=StyleManager.COLORS["surface"],
            border_color=StyleManager.COLORS["border"],
            corner_radius=8,
        )
        card_frame.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        card_frame.grid_columnconfigure(0, weight=1)
        card_frame.grid_rowconfigure(1, weight=1)

        top = StyleManager.create_frame(card_frame, fg_color="transparent", border_width=0)
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        top.grid_columnconfigure(0, weight=1)

        StyleManager.create_label(
            top,
            text=card["title"],
            font_style="subheading",
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        StyleManager.create_badge(
            top,
            text=card["metric"],
            tone="neutral",
        ).grid(row=0, column=1, sticky="e")

        StyleManager.create_label(
            card_frame,
            text=card["label"],
            font_style="body",
            text_color=StyleManager.COLORS["text_secondary"],
            anchor="nw",
            justify="left",
            wraplength=260,
        ).grid(row=1, column=0, sticky="new", padx=16, pady=(0, 14))

        StyleManager.create_button(
            card_frame,
            text="Open",
            style="secondary",
            command=card["command"],
            width=96,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))
