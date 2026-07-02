import logging
import os
import shutil
from typing import List


class FileManager:
    """Handles all file operations for customer documents."""

    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        self._ensure_base_directory()

    def _ensure_base_directory(self):
        """Ensure the base directory exists."""
        try:
            os.makedirs(self.base_dir, exist_ok=True)
        except OSError as e:
            logging.error(f"Error creating base directory: {str(e)}")
            raise

    def _safe_name(self, name: str) -> str:
        """Sanitize a name to prevent path traversal and illegal characters."""
        safe = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        if not safe or safe in (".", ".."):
            return "_"
        return safe

    def _get_customer_dir(self, customer_name: str) -> str:
        """Get the directory path for a customer's files."""
        safe_name = self._safe_name(customer_name)
        customer_dir = os.path.join(self.base_dir, safe_name)

        resolved = os.path.realpath(customer_dir)
        if not resolved.startswith(os.path.realpath(self.base_dir) + os.sep) and resolved != os.path.realpath(self.base_dir):
            logging.error(f"Path traversal detected for customer: {customer_name}")
            raise ValueError(f"Invalid customer name: {customer_name}")

        try:
            os.makedirs(resolved, exist_ok=True)
        except OSError as e:
            logging.error(f"Error creating customer directory: {str(e)}")
            raise

        return resolved

    def add_files(self, customer_name: str, files: List[str]) -> bool:
        """Add files for a customer."""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            success = True

            for file_path in files:
                try:
                    file_name = os.path.basename(file_path)
                    safe_name = self._safe_name(file_name)
                    base, ext = os.path.splitext(safe_name)
                    counter = 1

                    while os.path.exists(os.path.join(customer_dir, safe_name)):
                        safe_name = f"{base}_{counter}{ext}"
                        counter += 1

                    dest_path = os.path.join(customer_dir, safe_name)
                    shutil.copy2(file_path, dest_path)
                    logging.info(f"Added file {safe_name} for customer {customer_name}")
                except Exception as e:
                    logging.error(f"Error adding file {file_path} for customer {customer_name}: {str(e)}")
                    success = False

            return success
        except Exception as e:
            logging.error(f"Error in add_files for customer {customer_name}: {str(e)}")
            return False


