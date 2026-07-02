"""Excel Import/Export integration."""

import csv
import io
import logging
import os
from typing import Dict, List, Optional

from app.integrations.integration_base import IntegrationBase

logger = logging.getLogger(__name__)


class ExcelIntegration(IntegrationBase):
    name = "excel"
    version = "1.0.0"

    def __init__(self):
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def sync(self, direction: str = "both") -> Dict:
        return {"status": "ok", "note": "Excel integration ready. Use export/import buttons."}

    def export_to_csv(self, data: List[Dict], columns: List[str], filepath: str) -> str:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in data:
                writer.writerow({c: row.get(c, "") for c in columns})
        logger.info("Exported CSV: %s", filepath)
        return filepath

    def import_from_csv(self, filepath: str) -> List[Dict]:
        results = []
        with open(filepath, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(dict(row))
        logger.info("Imported %d rows from CSV", len(results))
        return results
