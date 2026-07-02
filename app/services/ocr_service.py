"""OCR Service — scan contracts, invoices, and receipts via Tesseract or PIL."""

import json
import logging
import os
import re
import subprocess
from datetime import datetime
from typing import List, Optional

from app.database.database import DatabaseManager

logger = logging.getLogger(__name__)

EXTRACT_PATTERNS = {
    "customer_name": [r"(?:customer|client|name)[:\s]+([A-Za-z\s]+)", r"([A-Za-z\s]{3,})"],
    "amount": [r"(?:total|amount|sum)[:\s]*\$?([\d,]+\.?\d*)", r"\$([\d,]+\.?\d*)"],
    "date": [r"(?:date)[:\s]+(\d{4}-\d{2}-\d{2})", r"(\d{2}/\d{2}/\d{4})"],
    "contract_number": [r"(?:contract|invoice|receipt)\s*(?:no|#|number)[:\s]+([A-Za-z0-9/-]+)"],
    "phone": [r"(\+?\d{10,15})"],
}


class OCRService:
    """Extract text from images using Tesseract OCR (optional)."""

    def __init__(self, db: DatabaseManager, tesseract_cmd: str = "tesseract"):
        self.db = db
        self.tesseract_cmd = tesseract_cmd
        self._available = None

    def is_available(self) -> bool:
        if self._available is None:
            try:
                subprocess.run([self.tesseract_cmd, "--version"], capture_output=True, timeout=5)
                self._available = True
            except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
                self._available = False
        return self._available

    def process_image(self, file_path: str, customer_id: int = None) -> dict:
        """Run OCR on an image and extract structured data."""
        ocr_text = self._run_ocr(file_path)
        extracted = self._extract_fields(ocr_text)
        doc_id = self._save_result(file_path, ocr_text, extracted, customer_id)
        return {"id": doc_id, "text": ocr_text, "extracted": extracted}

    def _run_ocr(self, file_path: str) -> str:
        if not self.is_available():
            logger.warning("Tesseract not available, returning empty text")
            return ""
        try:
            result = subprocess.run(
                [self.tesseract_cmd, file_path, "stdout"],
                capture_output=True, text=True, timeout=30,
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, OSError) as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def _extract_fields(self, text: str) -> dict:
        extracted = {}
        for field, patterns in EXTRACT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted[field] = match.group(1).strip()
                    break
        return extracted

    def _save_result(self, file_path: str, ocr_text: str, extracted: dict, customer_id: int = None) -> int:
        with self.db.transaction() as cur:
            cur.execute(
                "INSERT INTO ocr_documents (customer_id, file_path, ocr_text, extracted_data_json, status, created_at) "
                "VALUES (?, ?, ?, ?, 'completed', datetime('now'))",
                (customer_id, file_path, ocr_text, json.dumps(extracted)),
            )
            return cur.lastrowid

    def get_documents(self, customer_id: int = None) -> List[dict]:
        query = "SELECT * FROM ocr_documents"
        params = []
        if customer_id is not None:
            query += " WHERE customer_id = ?"
            params.append(customer_id)
        query += " ORDER BY created_at DESC"
        with self.db.transaction() as cur:
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]

    def get_document(self, doc_id: int) -> Optional[dict]:
        with self.db.transaction() as cur:
            cur.execute("SELECT * FROM ocr_documents WHERE id = ?", (doc_id,))
            row = cur.fetchone()
            if row:
                d = dict(row)
                d["extracted"] = json.loads(d.get("extracted_data_json", "{}"))
                return d
            return None

    def delete_document(self, doc_id: int) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM ocr_documents WHERE id = ?", (doc_id,))
            return cur.rowcount > 0
