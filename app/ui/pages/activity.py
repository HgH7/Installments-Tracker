import customtkinter
from datetime import datetime

from app.ui.pages.badge import get_action_badge


def setup_activity_page(frames, StyleManager, activity_service, show_frame):
    frame = frames["activity"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    header_frame = StyleManager.create_section_header(
        frame,
        "Activity Log",
        "Local audit trail of all application actions.",
    )
    header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))

    scroll = customtkinter.CTkScrollableFrame(
        frame,
        fg_color=StyleManager.COLORS["background"],
        border_width=0,
        scrollbar_button_color=StyleManager.COLORS["surface_highest"],
        scrollbar_button_hover_color=StyleManager.COLORS["border"],
    )
    scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
    scroll.grid_columnconfigure(0, weight=1)

    def refresh():
        for w in scroll.winfo_children():
            w.destroy()
        entries = activity_service.get_recent(200)
        if not entries:
            placeholder = StyleManager.create_frame(scroll, fg_color=StyleManager.COLORS["surface_low"])
            placeholder.grid(row=0, column=0, sticky="ew", pady=20)
            StyleManager.create_label(
                placeholder,
                text="No activity recorded yet.",
                font_style="body",
                text_color=StyleManager.COLORS["text_muted"],
            ).grid(pady=40, padx=20)
            return

        for i, entry in enumerate(entries):
            action = entry.get("action", "")
            detail = entry.get("detail", "")
            created = entry.get("created_at", "")
            customer_name = entry.get("customer_name", "")

            badge_text, tone = get_action_badge(action)

            card = StyleManager.create_frame(
                scroll, fg_color=StyleManager.COLORS["surface_low"], border_width=0, corner_radius=4,
            )
            card.grid(row=i, column=0, sticky="ew", pady=(0, 4))
            card.grid_columnconfigure(0, weight=0)
            card.grid_columnconfigure(1, weight=1)
            card.grid_columnconfigure(2, weight=0)
            card.grid_columnconfigure(3, weight=0)

            dot_colors = {
                "success": StyleManager.COLORS["success"],
                "danger": StyleManager.COLORS["danger"],
                "warning": StyleManager.COLORS["warning"],
                "neutral": StyleManager.COLORS["text_muted"],
                "info": StyleManager.COLORS["primary"],
            }
            dot = customtkinter.CTkFrame(
                card, width=3, fg_color=dot_colors.get(tone, dot_colors["neutral"]), corner_radius=0, border_width=0,
            )
            dot.grid(row=0, column=0, sticky="ns", padx=(0, 10))

            label_text = action
            if detail:
                label_text += f" — {detail}"
            if customer_name:
                label_text = f"{customer_name} — {label_text}"
            StyleManager.create_label(
                card, text=label_text, font_style="small", anchor="w",
            ).grid(row=0, column=1, sticky="w", pady=6)

            StyleManager.create_badge(card, text=badge_text, tone=tone, width=80, height=22).grid(
                row=0, column=2, padx=(10, 8), pady=6,
            )

            try:
                dt = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
                time_text = dt.strftime("%b %d, %H:%M")
            except ValueError:
                time_text = created
            StyleManager.create_label(
                card, text=time_text, font_style="small", text_color=StyleManager.COLORS["text_muted"],
            ).grid(row=0, column=3, padx=(0, 12), pady=6)

    btn_frame = StyleManager.create_frame(frame)
    btn_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))
    btn_frame.grid_columnconfigure(0, weight=1)

    left = StyleManager.create_frame(btn_frame, fg_color="transparent")
    left.grid(row=0, column=0, sticky="w")
    right = StyleManager.create_frame(btn_frame, fg_color="transparent")
    right.grid(row=0, column=1, sticky="e")

    StyleManager.create_button(left, text="Refresh", width=110, command=refresh).pack(side="left", pady=10)
    StyleManager.create_button(
        right, text="Back", style="secondary", width=100,
        command=lambda: show_frame(frames["home"]),
    ).pack(side="right", pady=10)

    refresh()
