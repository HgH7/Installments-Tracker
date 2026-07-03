"""Centralized application path management.

All module-level path computation lives here instead of being
duplicated across service, core, and UI files.
"""

import os
import sys


def _get_project_root() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def _get_data_dir() -> str:
    if getattr(sys, "frozen", False):
        # Use user-local data directory for writable data in packaged mode
        if sys.platform == "darwin":
            base = os.path.expanduser("~/Library/Application Support")
        elif sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        else:
            base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        return os.path.join(base, "Installments-Tracker", "data")
    return os.path.join(PROJECT_ROOT, "data")


PROJECT_ROOT = _get_project_root()

# Directories
DATA_DIR = _get_data_dir()
LOGS_DIR = os.path.join(DATA_DIR, "logs")
DOCUMENTS_DIR = os.path.join(DATA_DIR, "documents")
SETTINGS_DIR = DATA_DIR
CUSTOMER_FILES_DIR = os.path.join(DATA_DIR, "customer_files")

# Files
DB_PATH = os.path.join(DATA_DIR, "installment_tracker.db")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
SETTINGS_SCHEMA_FILE = os.path.join(SETTINGS_DIR, "settings_schema.json")
SETTINGS_DB_PATH = os.path.join(SETTINGS_DIR, "settings.db")
SESSION_FILE = os.path.join(DATA_DIR, "session.json")
CRASH_LOG_FILE = os.path.join(LOGS_DIR, "crash.log")
