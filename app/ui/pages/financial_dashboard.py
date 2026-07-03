"""Financial Dashboard — monthly income, expenses, P&L trends, analytics."""

from datetime import datetime

import customtkinter
from app.services.finance_service import FinanceService


def setup_financial_dashboard_page(frames, style_mgr, finance_service: FinanceService, show_frame,
                                   activity_service=None, analytics_service=None):
    frame = frames.get("financial_dashboard")
    if not frame:
        return
    frame.configure(fg_color=style_mgr.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    for w in frame.winfo_children():
        w.destroy()

    header = style_mgr.create_frame(frame, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
    style_mgr.create_label(header, text="Financial Dashboard", font_style="heading", anchor="w").pack(side="left")

    scroll = customtkinter.CTkScrollableFrame(frame, fg_color="transparent")
    scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
    scroll.grid_columnconfigure(0, weight=1)

    data = finance_service.compute_dashboard()
    income_trend = finance_service.get_income_trend(6)
    collection_trend = finance_service.get_collection_rate_trend(6)

    analytics = analytics_service.compute() if analytics_service else {}

    def kpi_card(parent, col, label, value, color):
        card = style_mgr.create_frame(parent, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        card.grid(row=0, column=col, sticky="nsew", padx=4)
        style_mgr.create_label(card, text=value, font_style="heading",
                               text_color=color, anchor="center").pack(pady=(16, 4), fill="x")
        style_mgr.create_label(card, text=label, font_style="small",
                               text_color=style_mgr.COLORS["text_secondary"], anchor="center").pack(pady=(0, 12))

    kpi_row1 = style_mgr.create_frame(scroll, fg_color="transparent")
    kpi_row1.pack(fill="x", pady=(0, 12))
    kpi_row1.grid_columnconfigure((0, 1, 2), weight=1)
    kpi_card(kpi_row1, 0, "Monthly Income", f"${data['monthly_income']:.2f}", style_mgr.COLORS.get("success", "#22c55e"))
    kpi_card(kpi_row1, 1, "Expected Income", f"${data['expected_income']:.2f}", style_mgr.COLORS.get("primary", "#2563eb"))
    kpi_card(kpi_row1, 2, "Outstanding", f"${data['outstanding_balance']:.2f}", style_mgr.COLORS.get("warning", "#f59e0b"))

    kpi_row2 = style_mgr.create_frame(scroll, fg_color="transparent")
    kpi_row2.pack(fill="x", pady=(0, 12))
    kpi_row2.grid_columnconfigure((0, 1, 2), weight=1)
    kpi_card(kpi_row2, 0, "Collection Rate", f"{data['collection_rate']}%", style_mgr.COLORS.get("info", "#3b82f6"))
    kpi_card(kpi_row2, 1, "Overdue Amount", f"${data['overdue_amount']:.2f}", style_mgr.COLORS.get("danger", "#ef4444"))
    kpi_card(kpi_row2, 2, "Monthly Growth", f"{data['monthly_growth']}%",
             style_mgr.COLORS.get("success", "#22c55e") if data['monthly_growth'] >= 0 else style_mgr.COLORS.get("danger", "#ef4444"))

    # Income trend
    trend_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    trend_section.pack(fill="x", pady=(0, 12))
    style_mgr.create_label(trend_section, text="Income Trend (6 months)", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=16, pady=(12, 8))
    chart_frame = style_mgr.create_frame(trend_section, fg_color="transparent", height=100)
    chart_frame.pack(fill="x", padx=16, pady=(0, 12))
    chart_frame.pack_propagate(False)
    max_income = max((t["income"] for t in income_trend), default=1)
    for t in income_trend:
        col = style_mgr.create_frame(chart_frame, fg_color="transparent")
        col.pack(side="left", expand=True, fill="both")
        h = int((t["income"] / max_income) * 80) if max_income > 0 else 0
        bar = style_mgr.create_frame(col, fg_color=style_mgr.COLORS.get("primary", "#2563eb"),
                                     height=max(4, h), corner_radius=3)
        bar.pack(side="bottom", pady=(0, 2))
        style_mgr.create_label(col, text=t.get("label", "")[-5:], font_style="small",
                               text_color=style_mgr.COLORS.get("text_muted", "#94a3b8"), anchor="center").pack()

    # P&L
    pl_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    pl_section.pack(fill="x", pady=(0, 12))
    style_mgr.create_label(pl_section, text="Profit & Loss (Monthly)", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=16, pady=(12, 8))
    for label, value, color in [
        ("Monthly Income", f"${data['monthly_income']:.2f}", style_mgr.COLORS.get("success", "#22c55e")),
        ("Monthly Expenses", f"${data['monthly_expenses']:.2f}", style_mgr.COLORS.get("danger", "#ef4444")),
        ("Net Profit", f"${data['net_profit']:.2f}",
         style_mgr.COLORS.get("success", "#22c55e") if data['net_profit'] >= 0 else style_mgr.COLORS.get("danger", "#ef4444")),
    ]:
        row = style_mgr.create_frame(pl_section, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=2)
        style_mgr.create_label(row, text=label, font_style="body", anchor="w").pack(side="left")
        style_mgr.create_label(row, text=value, font_style="body", text_color=color, anchor="e").pack(side="right")

    # Collection rate
    cr_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    cr_section.pack(fill="x", pady=(0, 12))
    style_mgr.create_label(cr_section, text="Collection Rate Trend", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=16, pady=(12, 8))
    for t in collection_trend:
        row = style_mgr.create_frame(cr_section, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=2)
        style_mgr.create_label(row, text=t["label"], font_style="body", width=80, anchor="w").pack(side="left")
        bg = style_mgr.create_frame(row, fg_color=style_mgr.COLORS.get("surface_low", "#1e293b"), height=16, corner_radius=3)
        bg.pack(side="left", fill="x", expand=True, padx=(8, 8))
        fill = style_mgr.create_frame(bg, fg_color=style_mgr.COLORS.get("success", "#22c55e") if t["rate"] >= 50 else style_mgr.COLORS.get("warning", "#f59e0b"),
                                       width=int(t["rate"] * 2), height=16, corner_radius=3)
        fill.pack(side="left")
        style_mgr.create_label(row, text=f"{t['rate']}%", font_style="small",
                               text_color=style_mgr.COLORS.get("text_secondary", "#64748b"), width=50, anchor="e").pack(side="right")

    # Analytics section
    if analytics:
        an_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        an_section.pack(fill="x", pady=(0, 12))
        style_mgr.create_label(an_section, text="Business Analytics", font_style="subheading",
                               anchor="w").pack(anchor="w", padx=16, pady=(12, 8))

        an_metrics = [
            ("Total Customers", str(analytics.get("total_customers", 0))),
            ("Collection Rate", f"{analytics.get('collection_rate', 0)}%"),
            ("Avg Payment Delay", f"{analytics.get('avg_payment_delay_days', 0)} days"),
            ("Avg Contract Value", f"${analytics.get('avg_contract_value', 0):.2f}"),
            ("New Customers (30d)", str(analytics.get("new_customers_30d", 0))),
            ("Collected (30d)", f"${analytics.get('collected_30d', 0):.2f}"),
            ("Upcoming Cash Flow (90d)", f"${analytics.get('upcoming_cash_flow_90d', 0):.2f}"),
            ("Total Outstanding", f"${analytics.get('total_outstanding', 0):.2f}"),
        ]
        for i, (lbl, val) in enumerate(an_metrics):
            row = style_mgr.create_frame(an_section, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)
            style_mgr.create_label(row, text=lbl, font_style="body", anchor="w").pack(side="left")
            style_mgr.create_label(row, text=val, font_style="body_bold",
                                   text_color=style_mgr.COLORS.get("primary", "#2563eb"), anchor="e").pack(side="right")

        top_customers = analytics.get("top_customers", [])
        if top_customers:
            style_mgr.create_label(an_section, text="Top Customers", font_style="body_bold",
                                   anchor="w").pack(anchor="w", padx=16, pady=(8, 4))
            for c in top_customers:
                row = style_mgr.create_frame(an_section, fg_color="transparent")
                row.pack(fill="x", padx=16, pady=1)
                style_mgr.create_label(row, text=c.get("customer_name", ""), font_style="small",
                                       anchor="w").pack(side="left")
                style_mgr.create_label(row, text=f"${c.get('total_amount', 0):.2f}", font_style="small",
                                       text_color=style_mgr.COLORS.get("text_secondary", "#64748b"),
                                       anchor="e").pack(side="right")

    btn_frame = style_mgr.create_frame(frame, fg_color="transparent")
    btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
    style_mgr.create_button(btn_frame, text="Refresh", command=lambda: setup_financial_dashboard_page(
        frames, style_mgr, finance_service, show_frame, activity_service=activity_service,
        analytics_service=analytics_service)).pack(side="left")
    if activity_service:
        style_mgr.create_button(btn_frame, text="Expenses", command=lambda: show_frame(frames["expenses"])
                                ).pack(side="left", padx=(8, 0))
    style_mgr.create_button(btn_frame, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")
