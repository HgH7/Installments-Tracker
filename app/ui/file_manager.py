import os
import shutil
import logging
from typing import List


class FileManager:
    """Handles all file operations for customer documents."""

    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        self._ensure_base_directory()

    def _ensure_base_directory(self):
        """Ensure the base directory exists."""
        try:
            if not os.path.exists(self.base_dir):
                os.makedirs(self.base_dir)
                logging.info(f"Created base directory: {self.base_dir}")
        except Exception as e:
            logging.error(f"Error creating base directory: {str(e)}")
            raise

    def _get_customer_dir(self, customer_name: str) -> str:
        """Get the directory path for a customer's files."""
        safe_name = "".join(c for c in customer_name if c.isalnum() or c in (' ', '-', '_')).strip()
        customer_dir = os.path.join(self.base_dir, safe_name)

        if not os.path.exists(customer_dir):
            os.makedirs(customer_dir)
            logging.info(f"Created customer directory: {customer_dir}")

        return customer_dir

    def add_files(self, customer_name: str, files: List[str]) -> bool:
        """Add files for a customer."""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            success = True

            for file_path in files:
                try:
                    file_name = os.path.basename(file_path)
                    safe_name = "".join(c for c in file_name if c.isalnum() or c in ('.', '-', '_')).strip()
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

    def get_files(self, customer_name: str) -> List[str]:
        """Get list of files for a customer."""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            if not os.path.exists(customer_dir):
                return []
            return [f for f in os.listdir(customer_dir) if os.path.isfile(os.path.join(customer_dir, f))]
        except Exception as e:
            logging.error(f"Error getting files for customer {customer_name}: {str(e)}")
            return []

    def delete_file(self, customer_name: str, file_name: str) -> bool:
        """Delete a specific file for a customer."""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            file_path = os.path.join(customer_dir, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Deleted file {file_name} for customer {customer_name}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error deleting file {file_name} for customer {customer_name}: {str(e)}")
            return False

    def delete_customer_files(self, customer_name: str) -> bool:
        """Delete all files for a customer."""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            if os.path.exists(customer_dir):
                shutil.rmtree(customer_dir)
                logging.info(f"Deleted all files for customer {customer_name}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error deleting files for customer {customer_name}: {str(e)}")
            return False

    def open_file(self, customer_name: str, file_name: str) -> bool:
        """Open a file using the system's default application."""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            file_path = os.path.join(customer_dir, file_name)
            if os.path.exists(file_path):
                os.startfile(file_path)
                logging.info(f"Opened file {file_name} for customer {customer_name}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error opening file {file_name} for customer {customer_name}: {str(e)}")
            return False
