"""Crash recovery and resilience system.

Captures unhandled exceptions, preserves crash logs, and attempts
to restore the last session on restart.
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime
from tkinter import messagebox
from typing import Optional

from app.core.version import APP_NAME, __version__

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CRASH_LOG_DIR = os.path.join(_BASE_DIR, "logs")
CRASH_LOG_FILE = os.path.join(CRASH_LOG_DIR, "crash.log")
SESSION_FILE = os.path.join(_BASE_DIR, "data", "session.json")


def _ensure_crash_dir():
    os.makedirs(CRASH_LOG_DIR, exist_ok=True)


def save_crash_log(
    exc_type: type,
    exc_value: BaseException,
    exc_tb: object,
) -> str:
    """Save a crash report to logs/crash.log. Returns the path."""
    _ensure_crash_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    report = (
        f"=== CRASH REPORT ===\n"
        f"Timestamp: {timestamp}\n"
        f"Version: {__version__}\n"
        f"Python: {sys.version}\n"
        f"Platform: {sys.platform}\n"
        f"\n{' '.join(tb_lines)}\n"
        f"=== END CRASH REPORT ===\n\n"
    )
    try:
        with open(CRASH_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(report)
    except OSError:
        pass
    return CRASH_LOG_FILE


def global_exception_handler(
    exc_type: type,
    exc_value: BaseException,
    exc_tb: object,
) -> None:
    """Replace sys.excepthook with this to catch all unhandled exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    path = save_crash_log(exc_type, exc_value, exc_tb)
    logging.critical(f"Unhandled exception: {exc_type.__name__}: {exc_value}")
    logging.critical(f"Crash log saved to: {path}")

    try:
        msg = (
            f"An unexpected error occurred.\n\n"
            f"{exc_type.__name__}: {exc_value}\n\n"
            f"A crash report has been saved to:\n{path}\n\n"
            f"Please report this issue."
        )
        messagebox.showerror(f"{APP_NAME} — Critical Error", msg)
    except Exception:
        pass


def install_global_exception_handler() -> None:
    """Install the global exception handler."""
    sys.excepthook = global_exception_handler


def save_session(page_name: str) -> None:
    """Save the current session state (last active page, etc.)."""
    session = {
        "last_page": page_name,
        "timestamp": datetime.now().isoformat(),
    }
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session, f)
    except OSError:
        pass


def load_session() -> Optional[str]:
    """Load the last saved session. Returns the last page name or None."""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                session = json.load(f)
            return session.get("last_page")
    except (OSError, json.JSONDecodeError):
        pass
    return None


def clear_session() -> None:
    """Remove the session file after successful restore."""
    try:
        if os.path.exists(SESSION_FILE):
            os.unlink(SESSION_FILE)
    except OSError:
        pass
