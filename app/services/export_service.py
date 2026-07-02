"""Exports customer data to CSV, Excel, PDF, JSON, and individual customer files."""

import csv
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional

from app.logging.logger import logger


class ExportService:
    @staticmethod
    def export_csv(data: List[Dict], filepath: str, columns: Optional[List[str]] = None) -> bool:
        try:
            if not columns:
                columns = list(data[0].keys()) if data else []
            fd, tmp_path = tempfile.mkstemp(suffix=".csv")
            try:
                with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=columns)
                    writer.writeheader()
                    for row in data:
                        out = {}
                        for col in columns:
                            val = row.get(col, "")
                            if isinstance(val, bool):
                                val = str(val)
                            out[col] = val
                        writer.writerow(out)
                os.replace(tmp_path, filepath)
            except BaseException:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
            logger.info(f"CSV export: {len(data)} rows to {os.path.basename(filepath)}", component="export")
            return True
        except (OSError, csv.Error) as e:
            logger.error(f"CSV export failed: {e}", component="export")
            return False

    @staticmethod
    def export_excel(data: List[Dict], filepath: str) -> bool:
        try:
            from app.export import write_excel
            return write_excel(data, filepath)
        except Exception as e:
            logger.error(f"Excel export failed: {e}", component="export")
            return False

    @staticmethod
    def export_pdf(data: List[Dict], filepath: str) -> bool:
        try:
            from app.export import write_pdf
            return write_pdf(data, filepath)
        except Exception as e:
            logger.error(f"PDF export failed: {e}", component="export")
            return False

    @staticmethod
    def export_report(report_data: Dict, format: str = "csv") -> Optional[str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.{format}"
        if format == "csv":
            data = report_data.get("rows", [])
            cols = report_data.get("columns", [])
            if ExportService.export_csv(data, filename, cols):
                return filename
        elif format == "json":
            try:
                fd, tmp_path = tempfile.mkstemp(suffix=".json")
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        json.dump(report_data, f, indent=2)
                    os.replace(tmp_path, filename)
                except BaseException:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                    raise
                logger.info(f"JSON report exported: {filename}", component="export")
                return filename
            except OSError as e:
                logger.error(f"JSON report export failed: {e}", component="export")
                return None
        return None

    @staticmethod
    def export_customer(data: Dict, format: str = "csv") -> Optional[str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = data.get("Name", "customer")
        filename = f"{name}_{timestamp}.{format}"
        if format == "csv":
            try:
                cols = list(data.keys())
                fd, tmp_path = tempfile.mkstemp(suffix=".csv")
                try:
                    with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=cols)
                        writer.writeheader()
                        writer.writerow(data)
                    os.replace(tmp_path, filename)
                except BaseException:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                    raise
                logger.info(f"Customer CSV exported: {filename}", component="export")
                return filename
            except (OSError, csv.Error) as e:
                logger.error(f"Customer CSV export failed: {e}", component="export")
                return None
        return None
