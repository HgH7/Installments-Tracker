from typing import Dict, List

import customtkinter


def build_timeline(customer_name: str, activity_service, csv_repository, customer_service) -> List[Dict]:
    customer = customer_service.get_customer_by_name(customer_name)
    events = []

    if customer:
        start_str = customer.get("Start Date", "")
        if start_str:
            events.append({
                "date": start_str,
                "action": "Contract created",
                "detail": f"{customer.get('Installments', 0)} installments, ${customer.get('Amount', 0):,.2f}",
                "tone": "info",
            })

        dates_str = customer.get("Installment Dates", "")
        paid = []
        from app.utils.serialization import load_json_list
        paid = load_json_list(customer.get("Paid_Installments", "[]"))
        for date_str in (d for d in dates_str.split(";") if d):
            is_paid = date_str in paid
            events.append({
                "date": date_str,
                "action": "Installment paid" if is_paid else "Installment due",
                "detail": f"${customer.get('Installment Value', 0)}",
                "tone": "success" if is_paid else "neutral",
            })

    if activity_service:
        cid = csv_repository.get_customer_id_by_name(customer_name)
        if cid:
            for entry in activity_service.get_for_customer(cid):
                events.append({
                    "date": entry.get("created_at", "")[:10],
                    "action": entry.get("action", ""),
                    "detail": entry.get("detail", ""),
                    "tone": "info",
                })

    events.sort(key=lambda x: x.get("date", ""), reverse=True)
    return events


def show_customer_timeline(parent_window, customer_name: str, activity_service, csv_repository, customer_service, StyleManager):
    from customtkinter import CTkToplevel
    window = CTkToplevel(parent_window)
    window.geometry("650x500")
    window.title(f"Customer Timeline: {customer_name}")
    window.transient(parent_window)
    window.grab_set()

    main_frame = StyleManager.create_frame(window)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(0, weight=0)
    main_frame.grid_rowconfigure(1, weight=1)

    StyleManager.create_label(main_frame, text=f"Timeline: {customer_name}", font_style="subheading").grid(
        row=0, column=0, sticky="w", pady=(0, 16))

    scroll = customtkinter.CTkScrollableFrame(
        main_frame, fg_color=StyleManager.COLORS["background"], border_width=0,
        scrollbar_button_color=StyleManager.COLORS["surface_highest"],
        scrollbar_button_hover_color=StyleManager.COLORS["border"],
    )
    scroll.grid(row=1, column=0, sticky="nsew")
    scroll.grid_columnconfigure(0, weight=1)
    scroll.grid_columnconfigure(1, weight=1)

    events = build_timeline(customer_name, activity_service, csv_repository, customer_service)

    tone_map = {
        "success": StyleManager.COLORS["success"],
        "danger": StyleManager.COLORS["danger"],
        "warning": StyleManager.COLORS["warning"],
        "info": StyleManager.COLORS["primary"],
        "neutral": StyleManager.COLORS["text_muted"],
    }

    row = 0
    if not events:
        StyleManager.create_label(scroll, text="No events recorded for this customer.",
                                  font_style="body", text_color=StyleManager.COLORS["text_muted"]).grid(
            row=0, column=0, columnspan=2, pady=40)
    else:
        for ev in events:
            dot = customtkinter.CTkFrame(scroll, width=8, height=8,
                                         fg_color=tone_map.get(ev["tone"], tone_map["neutral"]),
                                         corner_radius=4, border_width=0)
            dot.grid(row=row, column=0, sticky="n", padx=(4, 8), pady=(8, 0))

            date_label = StyleManager.create_label(
                scroll, text=ev.get("date", ""), font_style="small",
                text_color=StyleManager.COLORS["text_muted"])
            date_label.grid(row=row, column=0, sticky="nw", padx=(20, 0), pady=(6, 0))

            action_label = StyleManager.create_label(
                scroll, text=ev.get("action", ""), font_style="body_bold")
            action_label.grid(row=row, column=1, sticky="nw", padx=(4, 0), pady=(6, 0))

            if ev.get("detail"):
                detail_label = StyleManager.create_label(
                    scroll, text=ev.get("detail", ""), font_style="small",
                    text_color=StyleManager.COLORS["text_secondary"])
                detail_label.grid(row=row + 1, column=1, sticky="nw", padx=(4, 0), pady=(0, 4))

            spacer = customtkinter.CTkFrame(scroll, height=1, fg_color=StyleManager.COLORS["border_soft"],
                                            corner_radius=0, border_width=0)
            spacer.grid(row=row + 2, column=0, columnspan=2, sticky="ew", pady=(2, 0))

            row += 3

    btn_frame = StyleManager.create_frame(window)
    btn_frame.pack(fill="x", padx=20, pady=(0, 20))
    StyleManager.create_button(btn_frame, text="Close", style="secondary", width=100,
                               command=window.destroy).pack(side="right")
