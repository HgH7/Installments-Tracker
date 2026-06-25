import re
import customtkinter
from datetime import datetime

from app.utils.serialization import load_json_dict, load_json_list


def compute_activity_feed(customer_service, csv_repository):
    today = datetime.now().date()
    data = customer_service.get_all_customers()
    feed = []

    for customer in data:
        name = customer.get("Name", "Unknown")
        dates_str = customer.get("Installment Dates", "")
        if not dates_str:
            continue
        dates = [d for d in dates_str.split(";") if d]
        paid = load_json_list(customer.get("Paid_Installments", "[]"))
        values = load_json_dict(customer.get("Installment_Values", "{}"))
        inst_value = customer.get("Installment Value", 0)

        for date_str in dates:
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
                value = values.get(date_str, inst_value)
                is_paid = date_str in paid

                if is_paid:
                    feed.append({
                        "type": "paid",
                        "date": d,
                        "text": f"{name} — Paid ${value:,.2f}",
                        "badge": "Paid",
                        "tone": "success",
                    })
                elif d < today:
                    days = (today - d).days
                    feed.append({
                        "type": "overdue",
                        "date": d,
                        "text": f"{name} — ${value:,.2f} overdue {days}d",
                        "badge": f"{days}d overdue",
                        "tone": "danger",
                    })
                else:
                    days = (d - today).days
                    if days <= 30:
                        feed.append({
                            "type": "upcoming",
                            "date": d,
                            "text": f"{name} — ${value:,.2f} due in {days}d",
                            "badge": f"in {days}d",
                            "tone": "warning",
                        })
            except ValueError:
                continue

    for customer in data:
        start_str = customer.get("Start Date", "")
        if start_str:
            try:
                d = datetime.strptime(start_str, "%Y-%m-%d").date()
                if (today - d).days <= 60:
                    feed.append({
                        "type": "new_customer",
                        "date": d,
                        "text": f'{customer.get("Name", "Unknown")} — New customer, {customer.get("Installments", 0)} installments',
                        "badge": "New",
                        "tone": "neutral",
                    })
            except ValueError:
                continue

    try:
        backup_files = csv_repository.get_backup_files()
        if backup_files:
            m = re.search(r'backup_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', backup_files[0])
            if m:
                y, mo, d, h, mi, s = m.groups()
                bt = datetime(int(y), int(mo), int(d), int(h), int(mi), int(s))
                feed.append({
                    "type": "backup",
                    "date": bt.date(),
                    "text": "Backup created",
                    "badge": "Backup",
                    "tone": "neutral",
                })
    except Exception:
        pass

    feed.sort(key=lambda x: x["date"], reverse=True)
    return feed[:20]


def create_activity_card(entry, StyleManager, master, row_index):
    card = StyleManager.create_frame(
        master,
        fg_color=StyleManager.COLORS["surface_low"],
        border_width=0,
        corner_radius=4,
    )
    card.grid(row=row_index, column=0, sticky="ew", pady=(0, 6))

    indent_colors = {
        "success": StyleManager.COLORS["success"],
        "danger": StyleManager.COLORS["danger"],
        "warning": StyleManager.COLORS["warning"],
        "neutral": StyleManager.COLORS["text_muted"],
    }
    indent = customtkinter.CTkFrame(
        card,
        width=3,
        fg_color=indent_colors.get(entry["tone"], StyleManager.COLORS["text_muted"]),
        corner_radius=0,
        border_width=0,
    )
    indent.pack(side="left", fill="y", padx=(0, 10))

    text_label = StyleManager.create_label(
        card,
        text=entry["text"],
        font_style="small",
        text_color=StyleManager.COLORS["text"],
        anchor="w",
    )
    text_label.pack(side="left", fill="x", expand=True, pady=6)

    StyleManager.create_badge(
        card,
        text=entry["badge"],
        tone=entry["tone"],
        width=80,
        height=22,
    ).pack(side="right", padx=(10, 12), pady=6)


def setup_home_page(frames, StyleManager, show_frame, app, customer_service, csv_repository):
    frame = frames["home"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)

    header_frame = StyleManager.create_frame(
        frame, fg_color="transparent", border_width=0,
    )
    header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 20))
    header_frame.grid_columnconfigure(0, weight=1)

    StyleManager.create_label(
        header_frame,
        text="Installment Tracker",
        font_style="heading",
        anchor="w",
    ).grid(row=0, column=0, sticky="w")
    StyleManager.create_label(
        header_frame,
        text="Overview of your workspace and quick actions.",
        font_style="small",
        text_color=StyleManager.COLORS["text_muted"],
        anchor="w",
    ).grid(row=1, column=0, sticky="w", pady=(3, 0))

    stats_frame = StyleManager.create_frame(frame, fg_color="transparent", border_width=0)
    stats_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 24))
    for col in range(4):
        stats_frame.grid_columnconfigure(col, weight=1, uniform="stats")

    body = customtkinter.CTkScrollableFrame(
        frame,
        fg_color=StyleManager.COLORS["background"],
        border_width=0,
        scrollbar_button_color=StyleManager.COLORS["surface_highest"],
        scrollbar_button_hover_color=StyleManager.COLORS["border"],
    )
    body.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))
    frame.grid_rowconfigure(2, weight=1)
    body.grid_columnconfigure(0, weight=1)

    actions_header = StyleManager.create_section_header(
        body,
        "Quick Actions",
        "Navigate to the most commonly used pages.",
    )
    actions_header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

    actions_frame = StyleManager.create_frame(body)
    actions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
    actions_frame.grid_columnconfigure(0, weight=1)

    actions = [
        ("Add Customer", lambda: show_frame(frames["add"]), "primary"),
        ("Customers", lambda: show_frame(frames["view"]), "secondary"),
        ("Installments", lambda: show_frame(frames["manage"]), "secondary"),
        ("Backup / Restore", lambda: show_frame(frames["backup_restore"]), "secondary"),
    ]

    btn_row = StyleManager.create_frame(actions_frame, fg_color="transparent", border_width=0)
    btn_row.pack(fill="x")

    for text, cmd, style in actions:
        StyleManager.create_button(btn_row, text=text, style=style, width=150, command=cmd).pack(
            side="left", padx=(0, 10), pady=10
        )

    act_header = StyleManager.create_section_header(
        body,
        "Recent Activity",
        "Latest payments, new customers, and upcoming installments.",
    )
    act_header.grid(row=2, column=0, sticky="ew", pady=(0, 12))

    act_frame = StyleManager.create_frame(body)
    act_frame.grid(row=3, column=0, sticky="ew", pady=(0, 0))
    act_frame.grid_columnconfigure(0, weight=1)

    def refresh():
        try:
            data = customer_service.get_all_customers()
        except Exception:
            data = []
        total_customers = len(data)
        today = datetime.now().date()

        try:
            active = 0
            paid = 0
            overdue = 0
            for customer in data:
                installment_dates = customer.get("Installment Dates", "").split(";")
                paid_installments = load_json_list(customer.get("Paid_Installments", "[]"))
                total_inst = len(installment_dates)
                if total_inst == 0:
                    continue
                if len(paid_installments) == total_inst:
                    paid += 1
                else:
                    active += 1
                is_overdue = False
                for date_str in installment_dates:
                    if not date_str:
                        continue
                    try:
                        d = datetime.strptime(date_str, "%Y-%m-%d").date()
                        if d < today and date_str not in paid_installments:
                            is_overdue = True
                            break
                    except ValueError:
                        continue
                if is_overdue:
                    overdue += 1
        except Exception:
            active = 0
            paid = 0
            overdue = 0

        for w in stats_frame.winfo_children():
            w.destroy()

        stat_cards = [
            ("Customers", str(total_customers), "neutral"),
            ("Active", str(active), "warning"),
            ("Paid", str(paid), "success"),
            ("Overdue", str(overdue), "danger"),
        ]

        for i, (label, value, tone) in enumerate(stat_cards):
            card = StyleManager.create_frame(stats_frame)
            card.grid(row=0, column=i, sticky="ew", padx=8)

            tone_color = {
                "neutral": StyleManager.COLORS["text_secondary"],
                "warning": StyleManager.COLORS["warning"],
                "success": StyleManager.COLORS["success"],
                "danger": StyleManager.COLORS["danger"],
            }[tone]

            StyleManager.create_label(
                card,
                text=label,
                font_style="label",
                text_color=StyleManager.COLORS["text_muted"],
            ).pack(anchor="w", padx=16, pady=(14, 2))

            StyleManager.create_label(
                card,
                text=value,
                font_style="heading",
                text_color=tone_color,
            ).pack(anchor="w", padx=16, pady=(0, 14))

        for w in act_frame.winfo_children():
            w.destroy()

        feed = compute_activity_feed(customer_service, csv_repository)

        if not feed:
            placeholder = StyleManager.create_frame(
                act_frame,
                fg_color=StyleManager.COLORS["surface_low"],
                border_color=StyleManager.COLORS["border_soft"],
            )
            placeholder.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
            placeholder.grid_columnconfigure(0, weight=1)
            StyleManager.create_label(
                placeholder,
                text="No recent activity to display.",
                font_style="body",
                text_color=StyleManager.COLORS["text_muted"],
            ).grid(row=0, column=0, pady=28, padx=16)
        else:
            for i, entry in enumerate(feed):
                create_activity_card(entry, StyleManager, act_frame, i)

    frame.page_on_show = refresh
    refresh()
