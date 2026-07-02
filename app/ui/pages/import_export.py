import os
from tkinter import filedialog, messagebox

from app.services.export_service import ExportService
from app.services.import_service import ImportService


def setup_import_export_page(
    frames, StyleManager, csv_repository, customer_service,
    activity_service, show_frame, app,
):
    frame = frames["import_export"]
    frame.configure(fg_color=StyleManager.COLORS["background"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    header = StyleManager.create_section_header(
        frame, "Import & Export", "Import customers from CSV/Excel, export single or all customers."
    )
    header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))

    content = StyleManager.create_frame(frame, fg_color="transparent", border_width=0)
    content.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
    content.grid_columnconfigure(0, weight=1)
    content.grid_columnconfigure(1, weight=1)
    content.grid_rowconfigure(0, weight=1)
    content.grid_rowconfigure(1, weight=1)

    def do_import():
        filepath = filedialog.askopenfilename(
            title="Select CSV file to import",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if not filepath:
            return

        result = ImportService.import_csv(filepath)
        if result.errors:
            msg = f"Import completed with {result.error_count} errors:\n"
            for e in result.errors[:10]:
                msg += f"\n• {e}"
            if len(result.errors) > 10:
                msg += f"\n... and {len(result.errors) - 10} more"
            if not messagebox.askyesno("Import Warnings", msg + "\n\nContinue with valid records?"):
                return

        if result.records:
            warnings = ImportService.detect_duplicates(csv_repository, result.records)
            if warnings:
                msg = "Duplicate detection:\n" + "\n".join(f"• {w}" for w in warnings[:5])
                if not messagebox.askyesno("Duplicate Warnings", msg + "\n\nContinue with import?"):
                    return

            for record in result.records:
                csv_repository.append_record(record)
                if activity_service:
                    cid = csv_repository.get_customer_id_by_name(record["Name"])
                    activity_service.log("IMPORT_CSV", customer_id=cid, detail=f"Imported {record['Name']}")

            for item in tree.get_children():
                tree.delete(item)
            for c in csv_repository.read_data():
                tree.insert("", "end", values=(c["Name"], c["Phone"], c["Amount"], c["Installments"]))
            messagebox.showinfo("Success", f"Imported {result.success_count} customers successfully.")
        else:
            messagebox.showerror("Error", "No valid records found in file.")

    def do_export_all():
        data = csv_repository.read_data()
        if not data:
            messagebox.showerror("Error", "No data to export.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Export all customers",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
        )
        if not filepath:
            return

        if filepath.endswith(".xlsx"):
            ok = ExportService.export_excel(data, filepath)
        else:
            ok = ExportService.export_csv(data, filepath, csv_repository.columns)

        if ok:
            if activity_service:
                activity_service.log("EXPORT_CSV" if filepath.endswith(".csv") else "EXPORT_EXCEL",
                                     detail=f"Exported {len(data)} records")
            messagebox.showinfo("Success", f"Exported {len(data)} customers to {os.path.basename(filepath)}.")
        else:
            messagebox.showerror("Error", "Export failed.")

    def do_export_single():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select customers to export.")
            return
        customers = []
        for item in selected:
            name = tree.item(item)["values"][0]
            c = customer_service.get_customer_by_name(name)
            if c:
                customers.append(c)

        if not customers:
            messagebox.showerror("Error", "No valid customers selected.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Export selected customers",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not filepath:
            return

        if ExportService.export_csv(customers, filepath):
            messagebox.showinfo("Success", f"Exported {len(customers)} customer(s).")
        else:
            messagebox.showerror("Error", "Export failed.")

    # Left column — Import
    import_card = StyleManager.create_frame(content, fg_color=StyleManager.COLORS["surface"],
                                            border_color=StyleManager.COLORS["border"], corner_radius=8)
    import_card.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    import_card.grid_columnconfigure(0, weight=1)
    import_card.grid_rowconfigure(1, weight=1)

    StyleManager.create_label(import_card, text="Import Data", font_style="subheading").grid(
        row=0, column=0, sticky="w", padx=16, pady=(16, 8))
    StyleManager.create_label(import_card, text="Import customers from CSV or Excel files.\nDuplicates are detected and warned about.",
                              font_style="body", text_color=StyleManager.COLORS["text_secondary"], wraplength=280).grid(
        row=1, column=0, sticky="new", padx=16, pady=(0, 14))
    StyleManager.create_button(import_card, text="Import File", width=120, command=do_import).grid(
        row=2, column=0, sticky="w", padx=16, pady=(0, 16))

    # Right column — Export
    export_card = StyleManager.create_frame(content, fg_color=StyleManager.COLORS["surface"],
                                            border_color=StyleManager.COLORS["border"], corner_radius=8)
    export_card.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
    export_card.grid_columnconfigure(0, weight=1)
    export_card.grid_rowconfigure(1, weight=1)

    StyleManager.create_label(export_card, text="Export Data", font_style="subheading").grid(
        row=0, column=0, sticky="w", padx=16, pady=(16, 8))
    StyleManager.create_label(export_card, text="Export selected customers or the entire database to CSV or Excel.",
                              font_style="body", text_color=StyleManager.COLORS["text_secondary"], wraplength=280).grid(
        row=1, column=0, sticky="new", padx=16, pady=(0, 14))

    btn_frame = StyleManager.create_frame(export_card, fg_color="transparent", border_width=0)
    btn_frame.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))
    StyleManager.create_button(btn_frame, text="Export All", width=110, command=do_export_all).pack(side="left", padx=(0, 8))
    StyleManager.create_button(btn_frame, text="Export Selected", width=130, command=do_export_single).pack(side="left")

    bottom = StyleManager.create_frame(content, fg_color="transparent", border_width=0)
    bottom.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    StyleManager.create_label(bottom, text="Select customers below to export:", font_style="label").pack(anchor="w")

    tree_frame = StyleManager.create_frame(bottom, fg_color=StyleManager.COLORS["surface_low"])
    tree_frame.pack(fill="both", expand=True, pady=(8, 0))
    tree_frame.grid_columnconfigure(0, weight=1)
    tree_frame.grid_rowconfigure(0, weight=1)

    from tkinter import ttk
    columns = ("Name", "Phone", "Amount", "Installments")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Custom.Treeview")
    for col in columns:
        tree.column(col, width=120, anchor="center")
        tree.heading(col, text=col)
    tree.grid(row=0, column=0, sticky="nsew")
    scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    scroll.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scroll.set)

    for c in csv_repository.read_data():
        tree.insert("", "end", values=(c["Name"], c["Phone"], c["Amount"], c["Installments"]))

    nav_frame = StyleManager.create_frame(frame)
    nav_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))
    StyleManager.create_button(nav_frame, text="Back", style="secondary", width=120,
                               command=lambda: show_frame(frames["home"])).pack(side="right")
