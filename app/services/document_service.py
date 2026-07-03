"""Document Generator — PDF generation for receipts, invoices, contracts, statements."""

import logging
import os
from datetime import datetime
from typing import List, Optional

from app.database.database import DatabaseManager
from app.utils.paths import DOCUMENTS_DIR

logger = logging.getLogger(__name__)

DOCUMENT_TYPES = [
    "receipt",
    "invoice",
    "contract",
    "statement",
    "reminder_letter",
    "certificate",
]


def _ensure_docs_dir():
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)


def _generate_html(template: str, data: dict) -> str:
    """Simple template substitution."""
    html = template
    for key, value in data.items():
        placeholder = "{{" + key + "}}"
        html = html.replace(placeholder, str(value))
    return html


class DocumentService:
    """Generate and manage PDF documents.

    Requires `weasyprint` or `fpdf2` for PDF generation.
    Falls back to HTML-only if neither is available.
    """

    def __init__(self, db: DatabaseManager):
        self.db = db
        self._pdf_backend = self._detect_backend()

    def _detect_backend(self) -> str:
        try:
            import weasyprint
            return "weasyprint"
        except ImportError:
            pass
        try:
            from fpdf import FPDF
            return "fpdf"
        except ImportError:
            pass
        return "html"

    @property
    def available(self) -> bool:
        return self._pdf_backend in ("weasyprint", "fpdf")

    def generate(self, document_type: str, customer_id: int, data: dict) -> Optional[str]:
        """Generate a PDF document. Returns the file path."""
        _ensure_docs_dir()
        customer = self._get_customer(customer_id)
        if not customer:
            logger.error(f"Customer {customer_id} not found")
            return None

        title = f"{document_type}_{customer['customer_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path = os.path.join(DOCUMENTS_DIR, f"{title}.pdf")

        full_data = {**data, "customer_name": customer["customer_name"], "date": datetime.now().strftime("%Y-%m-%d")}

        if self._pdf_backend == "weasyprint":
            success = self._generate_weasyprint(document_type, full_data, file_path)
        elif self._pdf_backend == "fpdf":
            success = self._generate_fpdf(document_type, full_data, file_path)
        else:
            file_path = file_path.replace(".pdf", ".html")
            success = self._generate_html_only(document_type, full_data, file_path)

        if success:
            self._save_record(document_type, title, file_path, customer_id)
            return file_path
        return None

    def _get_customer(self, customer_id: int) -> Optional[dict]:
        with self.db.transaction() as cur:
            cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def _get_installments(self, customer_id: int) -> List[dict]:
        with self.db.transaction() as cur:
            cur.execute(
                "SELECT * FROM installments WHERE customer_id = ? ORDER BY installment_number",
                (customer_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def _generate_weasyprint(self, doc_type: str, data: dict, file_path: str) -> bool:
        try:
            from weasyprint import HTML
            html = self._get_template(doc_type, data)
            HTML(string=html).write_pdf(file_path)
            return True
        except Exception as e:
            logger.error(f"weasyprint failed: {e}")
            return False

    def _generate_fpdf(self, doc_type: str, data: dict, file_path: str) -> bool:
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            title = doc_type.replace("_", " ").title()
            pdf.cell(200, 10, text=title, new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(10)
            for key, value in data.items():
                pdf.cell(200, 10, text=f"{key.replace('_', ' ').title()}: {value}", new_x="LMARGIN", new_y="NEXT")
            pdf.output(file_path)
            return True
        except Exception as e:
            logger.error(f"fpdf failed: {e}")
            return False

    def _generate_html_only(self, doc_type: str, data: dict, file_path: str) -> bool:
        try:
            html = self._get_template(doc_type, data)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html)
            return True
        except Exception as e:
            logger.error(f"HTML generation failed: {e}")
            return False

    def _get_template(self, doc_type: str, data: dict) -> str:
        templates = {
            "receipt": """<html><body>
                <h2>Payment Receipt</h2>
                <p><strong>Customer:</strong> {{customer_name}}</p>
                <p><strong>Amount:</strong> ${{amount}}</p>
                <p><strong>Date:</strong> {{date}}</p>
                <p><strong>Paid for:</strong> {{description}}</p>
                <hr><p>Thank you for your payment.</p></body></html>""",
            "invoice": """<html><body>
                <h2>Invoice</h2>
                <p><strong>Customer:</strong> {{customer_name}}</p>
                <p><strong>Amount:</strong> ${{amount}}</p>
                <p><strong>Due Date:</strong> {{due_date}}</p>
                <p><strong>Description:</strong> {{description}}</p>
                <hr><p>Please pay by the due date.</p></body></html>""",
            "contract": """<html><body>
                <h2>Contract Agreement</h2>
                <p><strong>Customer:</strong> {{customer_name}}</p>
                <p><strong>Contract #:</strong> {{contract_number}}</p>
                <p><strong>Total Amount:</strong> ${{total_amount}}</p>
                <p><strong>Installments:</strong> {{installment_count}}</p>
                <p><strong>Start Date:</strong> {{start_date}}</p>
                <hr><pre>{{terms}}</pre>
                <br><p>_________________________<br>Customer Signature</p>
                <p>_________________________<br>Company Signature</p>
                <p><strong>Date:</strong> {{date}}</p></body></html>""",
            "statement": """<html><body>
                <h2>Account Statement</h2>
                <p><strong>Customer:</strong> {{customer_name}}</p>
                <p><strong>Period:</strong> {{period_start}} to {{period_end}}</p>
                <table border='1' cellpadding='4'>
                <tr><th>#</th><th>Due Date</th><th>Amount</th><th>Status</th></tr>
                {{installment_rows}}</table>
                <p><strong>Total Paid:</strong> ${{total_paid}}</p>
                <p><strong>Balance:</strong> ${{balance}}</p></body></html>""",
            "reminder_letter": """<html><body>
                <h2>Payment Reminder</h2>
                <p><strong>Customer:</strong> {{customer_name}}</p>
                <p>This is a reminder that the following installment is due:</p>
                <p><strong>Amount:</strong> ${{amount}}</p>
                <p><strong>Due Date:</strong> {{due_date}}</p>
                <hr><p>Please make your payment at your earliest convenience.</p>
                <p><strong>Date:</strong> {{date}}</p></body></html>""",
            "certificate": """<html><body>
                <h2>Certificate of Completion</h2>
                <p>This certifies that <strong>{{customer_name}}</strong> has completed all installment payments.</p>
                <p><strong>Total Amount:</strong> ${{total_amount}}</p>
                <p><strong>Completion Date:</strong> {{date}}</p>
                <hr><p>Thank you for your business.</p></body></html>""",
        }
        template = templates.get(doc_type, "<html><body><pre>{{content}}</pre></body></html>")

        if doc_type == "statement":
            installments = self._get_installments(data.get("customer_id", 0))
            rows = "".join(
                f"<tr><td>{i['installment_number']}</td><td>{i['due_date']}</td>"
                f"<td>${i['amount']:.2f}</td><td>{i['status']}</td></tr>"
                for i in installments
            )
            data["installment_rows"] = rows
            total_paid = sum(i["amount"] for i in installments if i["status"] == "paid")
            balance = sum(i["amount"] for i in installments if i["status"] == "pending")
            data["total_paid"] = f"${total_paid:.2f}"
            data["balance"] = f"${balance:.2f}"

        return _generate_html(template, data)

    def _save_record(self, doc_type: str, title: str, file_path: str, customer_id: int):
        with self.db.transaction() as cur:
            cur.execute(
                "INSERT INTO generated_documents (customer_id, document_type, title, file_path, created_at) "
                "VALUES (?, ?, ?, ?, datetime('now'))",
                (customer_id, doc_type, title, file_path),
            )

    def get_documents(self, customer_id: int = None, doc_type: str = "") -> List[dict]:
        query = "SELECT * FROM generated_documents WHERE 1=1"
        params = []
        if customer_id is not None:
            query += " AND customer_id = ?"
            params.append(customer_id)
        if doc_type:
            query += " AND document_type = ?"
            params.append(doc_type)
        query += " ORDER BY created_at DESC"
        with self.db.transaction() as cur:
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]

    def get_document(self, doc_id: int) -> Optional[dict]:
        with self.db.transaction() as cur:
            cur.execute("SELECT * FROM generated_documents WHERE id = ?", (doc_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def delete_document(self, doc_id: int) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM generated_documents WHERE id = ?", (doc_id,))
            return cur.rowcount > 0

    def get_customer_name_for_doc(self, customer_id: int) -> str:
        with self.db.transaction() as cur:
            cur.execute("SELECT customer_name FROM customers WHERE id = ?", (customer_id,))
            row = cur.fetchone()
            return row[0] if row else f"ID:{customer_id}"

    def get_customer_id_by_name(self, name: str) -> Optional[int]:
        with self.db.transaction() as cur:
            cur.execute("SELECT id FROM customers WHERE customer_name = ?", (name,))
            row = cur.fetchone()
            return row[0] if row else None
