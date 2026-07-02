import csv
import logging
import os
from datetime import datetime
from tkinter import messagebox
from typing import Dict, List

import pandas as pd


def write_excel(data: List[Dict], filepath: str) -> bool:
    try:
        arabic_columns = {
            "Name": "Customer Name", "Phone": "Phone", "Amount": "Total Amount",
            "Installments": "Installments", "Installment Value": "Installment Value",
            "Start Date": "Start Date", "Installment Dates": "Installment Dates",
            "Notification Sent": "Sent",
        }
        cleaned = []
        for row in data:
            r = row.copy()
            r["Notification Sent"] = "Yes" if row.get("Notification Sent") else "No"
            try:
                r["Amount"] = float(row.get("Amount", 0))
                r["Installment Value"] = float(row.get("Installment Value", 0))
                r["Installments"] = int(row.get("Installments", 0))
            except (ValueError, TypeError):
                pass
            cleaned.append(r)

        df = pd.DataFrame(cleaned).rename(columns=arabic_columns)
        with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Customer Data", index=False)
            workbook = writer.book
            worksheet = writer.sheets["Customer Data"]

            header_fmt = workbook.add_format({
                "bold": True, "font_size": 16, "font_name": "Arial",
                "align": "center", "valign": "vcenter", "bg_color": "#2B7DE9",
                "font_color": "white", "border": 2, "text_wrap": True,
                "border_color": "#1a5fb4",
            })
            cell_fmt = workbook.add_format({
                "font_size": 14, "font_name": "Arial", "align": "center",
                "valign": "vcenter", "border": 1, "text_wrap": True,
                "border_color": "#666666",
            })
            alt_fmt = workbook.add_format({
                "font_size": 14, "font_name": "Arial", "align": "center",
                "valign": "vcenter", "border": 1, "text_wrap": True,
                "border_color": "#666666", "bg_color": "#F5F5F5",
            })

            col_widths = {
                "Customer Name": 25, "Phone": 20, "Total Amount": 20,
                "Installments": 15, "Installment Value": 20, "Start Date": 20,
                "Installment Dates": 40, "Sent": 15,
            }
            for idx, col in enumerate(df.columns):
                worksheet.set_column(idx, idx, col_widths.get(col, 20))
                worksheet.write(0, idx, col, header_fmt)

            for row_num in range(1, len(df) + 1):
                fmt = alt_fmt if row_num % 2 == 0 else cell_fmt
                for col_num in range(len(df.columns)):
                    worksheet.write(row_num, col_num, df.iloc[row_num - 1][df.columns[col_num]], fmt)

            worksheet.set_default_row(45)
            worksheet.set_row(0, 60)
            worksheet.freeze_panes(1, 0)

        return True
    except Exception as e:
        logging.error(f"Excel write failed: {e}")
        return False


def write_pdf(data: List[Dict], filepath: str) -> bool:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        logging.error("reportlab not installed; falling back to CSV export")
        csv_path = filepath.replace(".pdf", ".csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            if data:
                w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                w.writeheader()
                w.writerows(data)
        logging.info(f"PDF unavailable — saved as CSV: {csv_path}")
        return False

    try:
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = [Paragraph("Installment Tracker Report", styles["Title"]), Spacer(1, 12)]

        if data:
            keys = list(data[0].keys())
            table_data = [keys]
            for row in data:
                table_data.append([str(row.get(k, "")) for k in keys])

            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B7DE9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ]))
            elements.append(table)

        doc.build(elements)
        return True
    except Exception as e:
        logging.error(f"PDF write failed: {e}")
        return False


def export_to_excel(repository):
    data = repository.read_data()
    if not data:
        messagebox.showerror("Error", "There is no data to export.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"customers_export_{timestamp}.xlsx"

    if write_excel(data, filename):
        messagebox.showinfo("Success", f"Data exported to: {filename}")
        try:
            os.startfile(os.path.abspath(filename))
        except AttributeError:
            pass
    else:
        messagebox.showerror("Error", "Failed to export data.")
