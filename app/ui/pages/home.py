from datetime import datetime, timedelta

import customtkinter

from app.ui.pages.badge import get_action_badge
from app.utils.serialization import load_json_dict, load_json_list


def compute_dashboard_stats(customer_service, csv_repository):
    today = datetime.now().date()
    data = customer_service.get_all_customers()
    total = len(data)
    active = 0
    completed = 0
    overdue_count = 0
    due_today_count = 0
    due_week_count = 0
    total_outstanding = 0.0
    collected_month = 0.0
    overdue_installments = []

    month_start = today.replace(day=1)
    for customer in data:
        dates_str = customer.get("Installment Dates", "")
        amount = float(customer.get("Amount", 0))
        dates = [d for d in dates_str.split(";") if d]
        paid = load_json_list(customer.get("Paid_Installments", "[]"))
        values = load_json_dict(customer.get("Installment_Values", "{}"))
        inst_value = float(customer.get("Installment Value", 0))
        total_inst = len(dates)
        paid_count = len(paid)

        if total_inst == 0:
            continue
        if paid_count == total_inst:
            completed += 1
        else:
            active += 1

        for date_str in dates:
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            v = float(values.get(date_str, inst_value))
            is_paid = date_str in paid

            if not is_paid:
                total_outstanding += v
                if d < today:
                    overdue_count += 1
                    overdue_installments.append((customer.get("Name", "Unknown"), date_str, v, (today - d).days))
                if d == today:
                    due_today_count += 1
                if today <= d <= today + timedelta(days=7):
                    due_week_count += 1
            else:
                if d >= month_start or (d < month_start and date_str in paid):
                    try:
                        pd_dt = datetime.strptime(date_str, "%Y-%m-%d")
                        if pd_dt.date() >= month_start:
                            collected_month += v
                    except ValueError:
                        pass

    return {
        "total_customers": total,
        "active": active,
        "completed": completed,
        "due_today": due_today_count,
        "due_week": due_week_count,
        "overdue_count": overdue_count,
        "total_outstanding": round(total_outstanding, 2),
        "collected_month": round(collected_month, 2),
        "overdue_installments": overdue_installments,
    }


def create_stat_card(parent, label, value, tone, StyleManager, row, col):
    tone_color = {
        "neutral": StyleManager.COLORS["text_secondary"],
        "warning": StyleManager.COLORS["warning"],
        "success": StyleManager.COLORS["success"],
        "danger": StyleManager.COLORS["danger"],
        "info": StyleManager.COLORS["primary"],
    }[tone]

    card = StyleManager.create_frame(parent, fg_color=StyleManager.COLORS["surface_low"], corner_radius=6)
    card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
    card.grid_columnconfigure(0, weight=1)
    StyleManager.create_label(card, text=label, font_style="small",
                              text_color=StyleManager.COLORS["text_muted"]).pack(anchor="w", padx=12, pady=(10, 2))
    StyleManager.create_label(card, text=str(value), font_style="heading",
                              text_color=tone_color).pack(anchor="w", padx=12, pady=(0, 10))
    return card


def setup_home_page(frames, StyleManager, show_frame, app, customer_service, csv_repository, activity_service, analytics_service):
    frame = frames["home"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)

    header_frame = StyleManager.create_frame(frame, fg_color="transparent", border_width=0)
    header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))
    header_frame.grid_columnconfigure(0, weight=1)

    title_frame = StyleManager.create_frame(header_frame, fg_color="transparent", border_width=0)
    title_frame.pack(fill="x")
    StyleManager.create_label(title_frame, text="Dashboard", font_style="heading", anchor="w").pack(side="left")
    StyleManager.create_label(title_frame, text=f"Last updated: {datetime.now().strftime('%H:%M')}",
                              font_style="small", text_color=StyleManager.COLORS["text_muted"],
                              anchor="e").pack(side="right", padx=(0, 0))

    body = customtkinter.CTkScrollableFrame(
        frame, fg_color=StyleManager.COLORS["background"], border_width=0,
        scrollbar_button_color=StyleManager.COLORS["surface_highest"],
        scrollbar_button_hover_color=StyleManager.COLORS["border"],
    )
    body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
    frame.grid_rowconfigure(1, weight=1)
    body.grid_columnconfigure(0, weight=1)

    def refresh():
        for w in body.winfo_children():
            w.destroy()

        stats = compute_dashboard_stats(customer_service, csv_repository)
        stats_grid = StyleManager.create_frame(body, fg_color="transparent", border_width=0)
        stats_grid.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        for c in range(4):
            stats_grid.grid_columnconfigure(c, weight=1, uniform="dash")

        stat_items = [
            ("Total Customers", str(stats["total_customers"]), "info"),
            ("Active", str(stats["active"]), "warning"),
            ("Completed", str(stats["completed"]), "success"),
            ("Overdue", str(stats["overdue_count"]), "danger"),
        ]
        for i, (label, value, tone) in enumerate(stat_items):
            create_stat_card(stats_grid, label, value, tone, StyleManager, 0, i)

        stat_items2 = [
            ("Due Today", str(stats["due_today"]), "warning"),
            ("Due This Week", str(stats["due_week"]), "info"),
            ("Outstanding", f"${stats['total_outstanding']:,.2f}", "danger"),
            ("Collected This Month", f"${stats['collected_month']:,.2f}", "success"),
        ]
        for i, (label, value, tone) in enumerate(stat_items2):
            create_stat_card(stats_grid, label, value, tone, StyleManager, 1, i)

        analytics = analytics_service.compute()
        if analytics:
            stat_items3 = [
                ("Collection Rate", f"{analytics.get('collection_rate', 0)}%", "success"),
                ("Avg Delay", f"{analytics.get('avg_payment_delay_days', 0)} days", "warning"),
                ("Avg Contract", f"${analytics.get('avg_contract_value', 0):,.2f}", "info"),
                ("New (30d)", str(analytics.get('new_customers_30d', 0)), "info"),
            ]
            for i, (label, value, tone) in enumerate(stat_items3):
                create_stat_card(stats_grid, label, value, tone, StyleManager, 2, i)

        row_idx = 1

        quick_header = StyleManager.create_section_header(body, "Quick Actions", "Navigate to commonly used pages.")
        quick_header.grid(row=row_idx, column=0, sticky="ew", pady=(0, 10))
        row_idx += 1

        actions_frame = StyleManager.create_frame(body, fg_color="transparent", border_width=0)
        actions_frame.grid(row=row_idx, column=0, sticky="ew", pady=(0, 16))
        row_idx += 1

        actions = [
            ("Add Customer", lambda: show_frame(frames["add"]), "primary"),
            ("Customers", lambda: show_frame(frames["view"]), "secondary"),
            ("Installments", lambda: show_frame(frames["manage"]), "secondary"),
            ("Notifications", lambda: show_frame(frames["notifications"]), "secondary"),
            ("Backup Manager", lambda: show_frame(frames["backup_manager"]), "secondary"),
            ("Activity Log", lambda: show_frame(frames["activity"]), "secondary"),
            ("Import / Export", lambda: show_frame(frames["import_export"]), "secondary"),
        ]

        btn_row = StyleManager.create_frame(actions_frame, fg_color="transparent", border_width=0)
        btn_row.pack(fill="x")
        for text, cmd, style in actions:
            StyleManager.create_button(btn_row, text=text, style=style, width=130, command=cmd).pack(
                side="left", padx=(0, 8), pady=6
            )

        act_header = StyleManager.create_section_header(body, "Recent Activity", "Latest system events.")
        act_header.grid(row=row_idx, column=0, sticky="ew", pady=(0, 10))
        row_idx += 1

        entries = activity_service.get_recent(15)
        if not entries:
            placeholder = StyleManager.create_frame(body, fg_color=StyleManager.COLORS["surface_low"])
            placeholder.grid(row=row_idx, column=0, sticky="ew", pady=6)
            row_idx += 1
            StyleManager.create_label(placeholder, text="No recent activity.",
                                      font_style="body", text_color=StyleManager.COLORS["text_muted"]).grid(pady=24, padx=16)
        else:
            for entry in entries:
                action = entry.get("action", "")
                detail = entry.get("detail", "")
                created = entry.get("created_at", "")
                customer_name = entry.get("customer_name", "")

                badge_text, tone = get_action_badge(action)
                card = StyleManager.create_frame(body, fg_color=StyleManager.COLORS["surface_low"],
                                                 border_width=0, corner_radius=4)
                card.grid(row=row_idx, column=0, sticky="ew", pady=(0, 3))
                card.grid_columnconfigure(0, weight=1)
                row_idx += 1

                indent_colors = {
                    "success": StyleManager.COLORS["success"], "danger": StyleManager.COLORS["danger"],
                    "warning": StyleManager.COLORS["warning"], "neutral": StyleManager.COLORS["text_muted"],
                    "info": StyleManager.COLORS["primary"],
                }
                indent = customtkinter.CTkFrame(card, width=3, fg_color=indent_colors.get(tone, indent_colors["neutral"]),
                                                corner_radius=0, border_width=0)
                indent.pack(side="left", fill="y", padx=(0, 10))

                label_parts = []
                if customer_name:
                    label_parts.append(customer_name)
                label_parts.append(action)
                if detail:
                    label_parts.append(f"({detail})")
                StyleManager.create_label(card, text=" — ".join(label_parts), font_style="small",
                                          anchor="w").pack(side="left", fill="x", expand=True, pady=6)

                StyleManager.create_badge(card, text=badge_text, tone=tone, width=70, height=22).pack(
                    side="right", padx=(8, 12), pady=6
                )

                try:
                    dt = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
                    time_text = dt.strftime("%b %d, %H:%M")
                except ValueError:
                    time_text = created
                StyleManager.create_label(card, text=time_text, font_style="small",
                                          text_color=StyleManager.COLORS["text_muted"]).pack(side="right", padx=(0, 8), pady=6)

    frame.page_on_show = refresh
    refresh()
