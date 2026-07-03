"""Contract Management — templates, contracts, status tracking."""

import logging
import subprocess

logger = logging.getLogger(__name__)
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter

from app.services.contract_service import CONTRACT_STATUSES, CONTRACT_STATUS_TRANSITIONS, ContractService


def setup_contracts_page(frames, style_mgr, contract_service: ContractService, show_frame,
                         customer_service=None, document_service=None, activity_service=None):
    frame = frames.get("contracts")
    if not frame:
        return
    frame.configure(fg_color=style_mgr.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    for w in frame.winfo_children():
        w.destroy()

    header = style_mgr.create_frame(frame, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
    style_mgr.create_label(header, text="Contract Management", font_style="heading", anchor="w").pack(side="left")

    scroll = customtkinter.CTkScrollableFrame(frame, fg_color="transparent")
    scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
    scroll.grid_columnconfigure(0, weight=1)

    list_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    list_section.pack(fill="x", pady=(0, 12))
    style_mgr.create_label(list_section, text="Contracts", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=16, pady=(12, 4))

    columns = ("number", "customer", "status", "created")
    tree = ttk.Treeview(list_section, columns=columns, show="headings", height=10)
    tree.heading("number", text="Contract #")
    tree.heading("customer", text="Customer")
    tree.heading("status", text="Status")
    tree.heading("created", text="Created")
    for col in columns:
        tree.column(col, width=120)
    tree.pack(fill="x", padx=16, pady=(8, 4))

    action_frame = style_mgr.create_frame(list_section, fg_color="transparent")
    action_frame.pack(fill="x", padx=16, pady=(0, 12))

    style_mgr.create_label(action_frame, text="Search:", anchor="w").pack(side="left")
    search_entry = style_mgr.create_entry(action_frame, width=180)
    search_entry.pack(side="left", padx=(8, 8))

    status_var = tk.StringVar(value="All")
    status_menu = customtkinter.CTkOptionMenu(action_frame, values=["All"] + CONTRACT_STATUSES,
                                              variable=status_var, fg_color=style_mgr.COLORS["surface_high"],
                                              button_color=style_mgr.COLORS["surface_highest"],
                                              button_hover_color=style_mgr.COLORS["border"],
                                              text_color=style_mgr.COLORS["text"])
    status_menu.pack(side="left", padx=(0, 8))

    template_names = ["All"]
    template_ids = {"All": None}
    for template in contract_service.get_templates():
        template_names.append(template["name"])
        template_ids[template["name"]] = template["id"]
    template_var = tk.StringVar(value="All")
    template_menu = customtkinter.CTkOptionMenu(action_frame, values=template_names,
                                                variable=template_var, fg_color=style_mgr.COLORS["surface_high"],
                                                button_color=style_mgr.COLORS["surface_highest"],
                                                button_hover_color=style_mgr.COLORS["border"],
                                                text_color=style_mgr.COLORS["text"])
    template_menu.pack(side="left", padx=(0, 8))

    customer_entry = style_mgr.create_entry(action_frame, width=140)
    customer_entry.pack(side="left", padx=(0, 8))
    customer_entry.insert(0, "")

    date_entry = style_mgr.create_entry(action_frame, width=110)
    date_entry.pack(side="left", padx=(0, 8))
    date_entry.insert(0, "YYYY-MM-DD")

    def search():
        q = search_entry.get().strip()
        status = "" if status_var.get() == "All" else status_var.get()
        template_id = template_ids.get(template_var.get())
        customer_name = customer_entry.get().strip()
        customer_id = None
        if customer_name:
            customer_id = contract_service.get_customer_id_by_name(customer_name)
        created_on = date_entry.get().strip()
        if created_on == "YYYY-MM-DD":
            created_on = ""
        results = contract_service.find_contract(q, status=status, template_id=template_id,
                                                 customer_id=customer_id, created_on=created_on) if (q or status or template_id is not None or customer_name or created_on) else contract_service.get_all_contracts()
        for item in tree.get_children():
            tree.delete(item)
        for c in results:
            tree.insert("", "end", values=(c["contract_number"], c.get("customer_name", ""),
                                            c["status"], c["created_at"][:10]))

    style_mgr.create_button(action_frame, text="Search", command=search).pack(side="left")

    def show_new_contract_dialog():
        d = customtkinter.CTkToplevel(frame)
        d.geometry("420x280")
        d.title("New Contract")
        d.transient(frame)
        d.grab_set()

        style_mgr.create_label(d, text="Customer Name:", anchor="w").pack(anchor="w", padx=16, pady=(12, 4))
        cname_entry = style_mgr.create_entry(d, width=260)
        cname_entry.pack(anchor="w", padx=16, pady=4)

        style_mgr.create_label(d, text="Customer ID (optional):", anchor="w").pack(anchor="w", padx=16, pady=(8, 4))
        cid_entry = style_mgr.create_entry(d, width=200)
        cid_entry.pack(anchor="w", padx=16, pady=4)

        def create():
            cname = cname_entry.get().strip()
            cid_str = cid_entry.get().strip()
            cid = None
            if cname:
                cid = contract_service.get_customer_id_by_name(cname)
                if cid is None:
                    messagebox.showerror("Error", f"Customer not found: {cname}")
                    return
            elif cid_str:
                try:
                    cid = int(cid_str)
                except ValueError:
                    messagebox.showerror("Error", "Customer ID must be a number.")
                    return
            else:
                messagebox.showerror("Error", "Enter a customer name or ID.")
                return
            try:
                ct = contract_service.create_contract(cid)
            except ValueError as exc:
                logger.exception("Failed to create contract")
                messagebox.showerror("Error", "Failed to create the contract. Please check the customer information and try again.")
                return
            messagebox.showinfo("Success", f"Contract created: {ct['contract_number']}")
            if activity_service:
                activity_service.log("Contract created", customer_id=cid, detail=f"{ct['contract_number']}")
            d.destroy()
            refresh()

        style_mgr.create_button(d, text="Create", command=create).pack(anchor="w", padx=16, pady=12)

    style_mgr.create_button(action_frame, text="New Contract", command=show_new_contract_dialog).pack(side="right")

    def open_contract_detail(contract_id=None):
        if contract_id is None:
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Info", "Select a contract first.")
                return
            contract_id = tree.item(selected[0])["values"][0]
        contract = None
        for item in contract_service.get_all_contracts():
            if item["contract_number"] == contract_id:
                contract = item
                break
        if not contract:
            return
        contract = contract_service.get_contract(contract["id"])
        if not contract:
            return

        d = customtkinter.CTkToplevel(frame)
        d.geometry("620x580")
        d.title(f"Contract — {contract['contract_number']}")
        d.transient(frame)
        d.grab_set()

        main = style_mgr.create_frame(d, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)

        style_mgr.create_label(main, text=f"{contract['contract_number']} — {contract.get('status', 'draft')}", font_style="subheading").grid(row=0, column=0, sticky="w", pady=(0, 10))
        info_frame = style_mgr.create_frame(main, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        info_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 12))
        info_frame.grid_columnconfigure(0, weight=1)

        customer_summary = contract_service.get_customer_summary(contract["customer_id"])
        customer_label = style_mgr.create_label(info_frame, text=f"Customer: {customer_summary.get('customer_name', contract['customer_id']) if customer_summary else contract['customer_id']}", anchor="w")
        customer_label.pack(anchor="w", padx=16, pady=(12, 4))
        style_mgr.create_label(info_frame, text=f"Created: {contract['created_at'][:10]}", anchor="w").pack(anchor="w", padx=16, pady=2)
        style_mgr.create_label(info_frame, text=f"Signed: {contract.get('signed_date') or '—'}", anchor="w").pack(anchor="w", padx=16, pady=2)

        current_status = contract.get("status", "draft")
        status_var = tk.StringVar(value=current_status)
        style_mgr.create_label(main, text="Status:", anchor="w").grid(row=2, column=0, sticky="w", pady=(0, 4))
        status_frame = style_mgr.create_frame(main, fg_color="transparent")
        status_frame.grid(row=3, column=0, sticky="w", pady=(0, 8))
        status_label = style_mgr.create_label(status_frame, text=current_status.capitalize(), anchor="w")
        status_label.pack(side="left")

        transitions = CONTRACT_STATUS_TRANSITIONS.get(current_status, set())
        valid_next = [s for s in CONTRACT_STATUSES if s in transitions and s != current_status]

        def advance_status():
            if not valid_next:
                messagebox.showinfo("Info", f"No further transitions from {current_status}.")
                return
            next_status = valid_next[0]
            try:
                contract_service.update_contract_status(contract["id"], next_status)
                messagebox.showinfo("Success", f"Status advanced to {next_status.capitalize()}")
                if activity_service:
                    activity_service.log("Contract status changed", customer_id=contract["customer_id"],
                                         detail=f"{contract['contract_number']} → {next_status}")
                d.destroy()
                refresh()
            except ValueError as exc:
                logger.exception("Failed to advance contract status")
                messagebox.showerror("Error", "Failed to update the contract status. Please try again.")

        def cancel_contract():
            if current_status == "cancelled":
                messagebox.showinfo("Info", "Contract is already cancelled.")
                return
            if not messagebox.askyesno("Confirm Cancel", f"Cancel contract {contract['contract_number']}?"):
                return
            try:
                contract_service.update_contract_status(contract["id"], "cancelled")
                messagebox.showinfo("Success", "Contract cancelled.")
                if activity_service:
                    activity_service.log("Contract status changed", customer_id=contract["customer_id"],
                                         detail=f"{contract['contract_number']} → cancelled")
                d.destroy()
                refresh()
            except ValueError as exc:
                logger.exception("Failed to cancel contract")
                messagebox.showerror("Error", "Failed to cancel the contract. Please try again.")

        if valid_next:
            style_mgr.create_button(status_frame, text=f"Advance to {valid_next[0].capitalize()}",
                                    style="primary", width=160, command=advance_status).pack(side="left", padx=(12, 0))
        if current_status != "cancelled" and current_status != "completed":
            style_mgr.create_button(status_frame, text="Cancel", style="danger", width=100,
                                    command=cancel_contract).pack(side="left", padx=(8, 0))

        template_options = ["None"]
        template_ids = {"None": None}
        for template in contract_service.get_templates():
            template_options.append(template["name"])
            template_ids[template["name"]] = template["id"]
        current_template_name = "None"
        if contract.get("template_id"):
            template = contract_service.get_template(contract["template_id"])
            if template:
                current_template_name = template["name"]
        template_var = tk.StringVar(value=current_template_name)
        style_mgr.create_label(main, text="Template:", anchor="w").grid(row=4, column=0, sticky="w", pady=(0, 4))
        template_menu = customtkinter.CTkOptionMenu(main, values=template_options, variable=template_var,
                                                   fg_color=style_mgr.COLORS["surface_high"],
                                                   button_color=style_mgr.COLORS["surface_highest"],
                                                   button_hover_color=style_mgr.COLORS["border"],
                                                   text_color=style_mgr.COLORS["text"])
        template_menu.grid(row=5, column=0, sticky="w", pady=(0, 8))

        style_mgr.create_label(main, text="Notes:", anchor="w").grid(row=6, column=0, sticky="w", pady=(0, 4))
        notes_text = customtkinter.CTkTextbox(main, height=120, fg_color=style_mgr.COLORS["surface_high"],
                                             border_color=style_mgr.COLORS["border"], border_width=1)
        notes_text.grid(row=7, column=0, sticky="nsew", pady=(0, 8))
        notes_text.insert("0.0", contract.get("notes", ""))

        style_mgr.create_label(main, text="Signed date (YYYY-MM-DD):", anchor="w").grid(row=8, column=0, sticky="w", pady=(0, 4))
        signed_date_entry = style_mgr.create_entry(main, width=220)
        signed_date_entry.grid(row=9, column=0, sticky="w", pady=(0, 16))
        signed_date_entry.insert(0, contract.get("signed_date") or "")

        button_row = style_mgr.create_frame(main, fg_color="transparent")
        button_row.grid(row=10, column=0, sticky="ew", pady=(8, 0))

        def save_changes():
            try:
                contract_service.update_contract(
                    contract["id"],
                    notes=notes_text.get("0.0", "end").strip(),
                    signed_date=signed_date_entry.get().strip() or None,
                    template_id=template_ids.get(template_var.get()),
                )
                if status_var.get() != contract.get("status", "draft"):
                    contract_service.update_contract_status(contract["id"], status_var.get())
                messagebox.showinfo("Success", "Contract updated")
                d.destroy()
                refresh()
                if activity_service:
                    activity_service.log("Contract edited", customer_id=contract["customer_id"],
                                         detail=f"{contract['contract_number']}")
            except ValueError as exc:
                logger.exception("Failed to update contract")
                messagebox.showerror("Error", "Failed to update the contract. Please check your input and try again.")
            except Exception as exc:
                logger.exception("Failed to update contract")
                messagebox.showerror("Error", "An unexpected error occurred while updating the contract.")

        def view_customer():
            if customer_summary:
                name = customer_summary.get("customer_name", "")
                phone = customer_summary.get("phone_number", "")
                amount = customer_summary.get("total_amount", "")
                installments = customer_summary.get("installment_count", "")
                start = customer_summary.get("start_date", "")
                info = (
                    f"Customer: {name}\n"
                    f"Phone: {phone}\n"
                    f"Total Amount: {amount}\n"
                    f"Installments: {installments}\n"
                    f"Start Date: {start}\n"
                )
                messagebox.showinfo("Customer Details", info)
            else:
                messagebox.showinfo("Customer", f"Customer ID: {contract['customer_id']}")

        def view_template():
            template_id = template_ids.get(template_var.get())
            if not template_id:
                messagebox.showinfo("Template", "No template selected.")
                return
            template = contract_service.get_template(template_id)
            if not template:
                messagebox.showinfo("Template", "Template not found.")
                return
            preview = customtkinter.CTkToplevel(frame)
            preview.geometry("500x400")
            preview.title("Template Preview")
            preview.transient(frame)
            preview.grab_set()
            body = customtkinter.CTkTextbox(preview, fg_color=style_mgr.COLORS["surface_high"], border_color=style_mgr.COLORS["border"], border_width=1)
            body.pack(fill="both", expand=True, padx=16, pady=16)
            body.insert("0.0", template.get("content", ""))
            body.configure(state="disabled")

        def generate_document():
            if not document_service:
                messagebox.showinfo("Info", "Document generation is not available for this view.")
                return
            if not customer_summary:
                messagebox.showerror("Error", "Customer details are not available for document generation.")
                return
            data = {
                "contract_number": contract["contract_number"],
                "total_amount": customer_summary.get("total_amount", ""),
                "installment_count": customer_summary.get("installment_count", ""),
                "start_date": customer_summary.get("start_date", ""),
                "terms": notes_text.get("0.0", "end").strip() or "",
            }
            try:
                path = document_service.generate("contract", contract["customer_id"], data)
            except Exception as exc:
                logger.exception("Failed to generate contract document")
                messagebox.showerror("Error", "Document generation failed. Please try again or contact support.")
                return
            if not path:
                messagebox.showinfo("Info", "No document was generated.")
                return
            contract_service.update_contract(contract["id"], pdf_path=path)
            messagebox.showinfo("Success", f"Document saved: {path}")
            if activity_service:
                activity_service.log("Document generated", customer_id=contract["customer_id"],
                                     detail=f"contract — {path}")
            try:
                subprocess.Popen(["open", path])
            except Exception as e:
                logging.warning(f"Failed to open document: {e}")

        style_mgr.create_button(button_row, text="Save", command=save_changes).pack(side="left")
        style_mgr.create_button(button_row, text="View Customer", style="secondary", width=120, command=view_customer).pack(side="left", padx=(8, 0))
        style_mgr.create_button(button_row, text="View Template", style="secondary", width=120, command=view_template).pack(side="left", padx=(8, 0))
        style_mgr.create_button(button_row, text="Generate Document", style="secondary", width=140, command=generate_document).pack(side="left", padx=(8, 0))
        style_mgr.create_button(button_row, text="Cancel", style="secondary", width=100, command=d.destroy).pack(side="right")

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        for c in contract_service.get_all_contracts():
            tree.insert("", "end", values=(c["contract_number"], c.get("customer_name", ""),
                                            c["status"], c["created_at"][:10]))

    tree.bind("<Double-1>", lambda _e: open_contract_detail())

    refresh()

    bottom_frame = style_mgr.create_frame(frame, fg_color="transparent")
    bottom_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
    style_mgr.create_button(bottom_frame, text="View / Edit", command=lambda: open_contract_detail()).pack(side="left")
    style_mgr.create_button(bottom_frame, text="Refresh", command=refresh).pack(side="left", padx=(8, 0))
    style_mgr.create_button(bottom_frame, text="Back", style="secondary", width=100,
                            command=lambda: show_frame(frames["home"])).pack(side="right")

    template_section = style_mgr.create_frame(scroll, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
    template_section.pack(fill="x", pady=(0, 12))
    style_mgr.create_label(template_section, text="Templates", font_style="subheading",
                           anchor="w").pack(anchor="w", padx=16, pady=(12, 4))

    template_columns = ("name", "created")
    template_tree = ttk.Treeview(template_section, columns=template_columns, show="headings", height=6)
    template_tree.heading("name", text="Template")
    template_tree.heading("created", text="Created")
    template_tree.column("name", width=220)
    template_tree.column("created", width=160)
    template_tree.pack(fill="x", padx=16, pady=(8, 4))

    template_action_frame = style_mgr.create_frame(template_section, fg_color="transparent")
    template_action_frame.pack(fill="x", padx=16, pady=(0, 12))

    def refresh_templates():
        for item in template_tree.get_children():
            template_tree.delete(item)
        for template in contract_service.get_templates():
            template_tree.insert("", "end", values=(template["name"], template["created_at"][:10]))

    def show_template_dialog(template=None):
        d = customtkinter.CTkToplevel(frame)
        d.geometry("480x360")
        d.title("Template" if template else "New Template")
        d.transient(frame)
        d.grab_set()
        style_mgr.create_label(d, text="Name:", anchor="w").pack(anchor="w", padx=16, pady=(12, 4))
        name_entry = style_mgr.create_entry(d, width=280)
        name_entry.pack(anchor="w", padx=16, pady=4)
        if template:
            name_entry.insert(0, template.get("name", ""))
        style_mgr.create_label(d, text="Content:", anchor="w").pack(anchor="w", padx=16, pady=(8, 4))
        content_text = customtkinter.CTkTextbox(d, height=180, fg_color=style_mgr.COLORS["surface_high"],
                                               border_color=style_mgr.COLORS["border"], border_width=1)
        content_text.pack(fill="x", padx=16, pady=4)
        if template:
            content_text.insert("0.0", template.get("content", ""))

        def save():
            name = name_entry.get().strip()
            content = content_text.get("0.0", "end").strip()
            if not name:
                messagebox.showerror("Error", "Template name is required")
                return
            if template:
                contract_service.update_template(template["id"], name=name, content=content)
            else:
                contract_service.create_template(name, content)
            d.destroy()
            refresh_templates()

        style_mgr.create_button(d, text="Save", command=save).pack(anchor="w", padx=16, pady=12)

    def duplicate_selected_template():
        selected = template_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a template first.")
            return
        template_name = template_tree.item(selected[0])["values"][0]
        templates = {t["name"]: t for t in contract_service.get_templates()}
        template = templates.get(template_name)
        if not template:
            return
        duplicate_name = f"{template_name} Copy"
        contract_service.duplicate_template(template["id"], duplicate_name)
        refresh_templates()

    def delete_selected_template():
        selected = template_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a template first.")
            return
        template_name = template_tree.item(selected[0])["values"][0]
        templates = {t["name"]: t for t in contract_service.get_templates()}
        template = templates.get(template_name)
        if not template:
            return
        if messagebox.askyesno("Confirm", f"Delete template {template_name}?"):
            contract_service.delete_template(template["id"])
            refresh_templates()

    def preview_selected_template():
        selected = template_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a template first.")
            return
        template_name = template_tree.item(selected[0])["values"][0]
        templates = {t["name"]: t for t in contract_service.get_templates()}
        template = templates.get(template_name)
        if not template:
            return
        preview = customtkinter.CTkToplevel(frame)
        preview.geometry("500x300")
        preview.title("Template Preview")
        preview.transient(frame)
        preview.grab_set()
        body = customtkinter.CTkTextbox(preview, fg_color=style_mgr.COLORS["surface_high"], border_color=style_mgr.COLORS["border"], border_width=1)
        body.pack(fill="both", expand=True, padx=16, pady=16)
        body.insert("0.0", template.get("content", ""))
        body.configure(state="disabled")

    def edit_selected_template():
        selected = template_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a template first.")
            return
        template_name = template_tree.item(selected[0])["values"][0]
        templates = {t["name"]: t for t in contract_service.get_templates()}
        template = templates.get(template_name)
        if not template:
            return
        show_template_dialog(template)

    style_mgr.create_button(template_action_frame, text="New", command=lambda: show_template_dialog()).pack(side="left")
    style_mgr.create_button(template_action_frame, text="Edit", command=edit_selected_template).pack(side="left", padx=(8, 0))
    style_mgr.create_button(template_action_frame, text="Duplicate", command=duplicate_selected_template).pack(side="left", padx=(8, 0))
    style_mgr.create_button(template_action_frame, text="Delete", command=delete_selected_template).pack(side="left", padx=(8, 0))
    style_mgr.create_button(template_action_frame, text="Preview", command=preview_selected_template).pack(side="left", padx=(8, 0))

    refresh_templates()
