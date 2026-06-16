import os
from customtkinter import CTkFrame, CTkButton


def setup_home_page(frames, StyleManager, show_frame, app):
    frame = frames["home"]
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_rowconfigure(0, weight=0)
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_rowconfigure(2, weight=1)
    frame.grid_rowconfigure(3, weight=1)

    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)

    StyleManager.create_label(
        header_frame,
        text="نظام إدارة الأقساط",
        font=("Arial", 42, "bold"),
        text_color="#ffffff"
    ).grid(row=0, column=0, pady=(20, 20))

    menu_items = [
        {
            "text": "إضافة عميل",
            "command": lambda: show_frame(frames["add"]),
            "icon": "👤",
            "color": "#4CAF50"
        },
        {
            "text": "عرض العملاء",
            "command": lambda: show_frame(frames["view"]),
            "icon": "📋",
            "color": "#2196F3"
        },
        {
            "text": "إدارة الأقساط",
            "command": lambda: show_frame(frames["manage"]),
            "icon": "💰",
            "color": "#9C27B0"
        },
        {
            "text": "النسخ الاحتياطية",
            "command": lambda: show_frame(frames["backup_restore"]),
            "icon": "🔒",
            "color": "#FF9800"
        },
        {
            "text": "إرسال إشعارات",
            "command": lambda: show_frame(frames["send_notification"]),
            "icon": "📨",
            "color": "#E91E63"
        },
        {
            "text": "ملفات العملاء",
            "command": lambda: os.startfile("customer_files"),
            "icon": "📁",
            "color": "#607D8B"
        }
    ]

    for i, item in enumerate(menu_items):
        row, col = divmod(i, 2)
        button_container = CTkFrame(
            frame,
            fg_color="transparent"
        )
        button_container.grid(row=row+1, column=col, padx=30, pady=25, sticky="nsew")

        button = CTkButton(
            button_container,
            text=f"{item['icon']}  {item['text']}",
            command=item["command"],
            width=500,
            height=80,
            corner_radius=15,
            fg_color=item["color"],
            hover_color=item["color"],
            text_color="#ffffff",
            font=("Arial", 24, "bold"),
            anchor="center"
        )
        button.pack(expand=True, fill="both")

        def on_enter(e, button=button):
            button.configure(border_width=2, border_color="#ffffff")

        def on_leave(e, button=button):
            button.configure(border_width=0)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
