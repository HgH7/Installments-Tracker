"""Application settings — persistent config via JSON, with a UI editor."""

import copy
import json
import logging
import os
import sqlite3
from tkinter import messagebox
from typing import Any, Callable, Dict, List

from app.core.branding import APP_NAME
from app.utils.paths import SETTINGS_DIR, SETTINGS_FILE, SETTINGS_SCHEMA_FILE, SETTINGS_DB_PATH

logger = logging.getLogger(__name__)

SCHEMA_FILE = SETTINGS_SCHEMA_FILE


# ---------------------------------------------------------------------------
# Legacy Settings — flat key/value via SQLite for backward compatibility
# ---------------------------------------------------------------------------

class Settings:
    """Backward-compatible settings storage using SQLite.

    Used by existing pages and tests.  Stored in data/settings.db.
    """

    DEFAULTS = {
        "theme": "dark",
        "window_width": 1280,
        "window_height": 800,
        "language": "en",
        "backup_max_count": 50,
        "backup_compress": True,
        "auto_backup_on_start": False,
        "notification_reminder_days": 3,
        "reminder_template": "",
        "auto_update": True,
        "confirm_on_delete": True,
    }

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = SETTINGS_DB_PATH
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.commit()
            for k, v in self.DEFAULTS.items():
                conn.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, str(v))
                )
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize settings database: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get(self, key: str, default=None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            if row:
                val = row[0]
                orig_default = self.DEFAULTS.get(key)
                if isinstance(orig_default, bool):
                    return val.lower() == "true"
                if isinstance(orig_default, int):
                    return int(val)
                return val
            return default if default is not None else self.DEFAULTS.get(key)
        except (sqlite3.Error, ValueError):
            return default if default is not None else self.DEFAULTS.get(key)

    def set(self, key: str, value):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, str(value)),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error("Failed to set setting '%s': %s", key, e)

    def set_many(self, pairs: dict):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.executemany(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                [(k, str(v)) for k, v in pairs.items()],
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error("Failed to set multiple settings: %s", e)

    def get_all(self) -> dict:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT key, value FROM settings")
            result = {}
            for k, v in cursor.fetchall():
                orig_default = self.DEFAULTS.get(k)
                if isinstance(orig_default, bool):
                    result[k] = v.lower() == "true"
                elif isinstance(orig_default, int):
                    result[k] = int(v)
                else:
                    result[k] = v
            conn.close()
            for k, v in self.DEFAULTS.items():
                result.setdefault(k, v)
            return result
        except sqlite3.Error as e:
            logger.error("Failed to get all settings: %s", e)
            return dict(self.DEFAULTS)


settings = Settings()


# ---------------------------------------------------------------------------
# New SettingsManager — sectioned JSON config with UI support
# ---------------------------------------------------------------------------

DEFAULT_SETTINGS = {
    "general": {
        "app_name": APP_NAME,
        "language": "en",
        "check_updates": True,
        "save_session_on_exit": True,
        "confirm_on_delete": True,
    },
    "display": {
        "theme": "dark",
        "accent_color": "#1f6aa5",
        "items_per_page": 50,
        "date_format": "%Y-%m-%d",
        "show_currency_symbol": True,
        "currency_symbol": "$",
    },
    "notifications": {
        "enabled": True,
        "reminder_days_before": 3,
        "auto_dismiss": False,
        "notification_sound": False,
    },
    "backup": {
        "auto_backup": True,
        "backup_interval_days": 7,
        "max_backups": 10,
        "backup_directory": "backups",
    },
    "privacy": {
        "anonymize_logs": False,
        "collect_usage_stats": False,
        "crash_reporting": True,
    },
}


SETTINGS_SCHEMA = {
    "general": {
        "app_name": {"type": "string", "label": "Application Name", "readonly": True},
        "language": {"type": "select", "label": "Language", "options": ["en", "ar", "fr", "es"]},
        "check_updates": {"type": "bool", "label": "Check for Updates"},
        "save_session_on_exit": {"type": "bool", "label": "Save Session on Exit"},
        "confirm_on_delete": {"type": "bool", "label": "Confirm Before Deleting"},
    },
    "display": {
        "theme": {"type": "select", "label": "Theme", "options": ["dark", "light", "system"]},
        "accent_color": {"type": "color", "label": "Accent Color"},
        "items_per_page": {"type": "int", "label": "Items per Page", "min": 10, "max": 500},
        "date_format": {"type": "string", "label": "Date Format"},
        "show_currency_symbol": {"type": "bool", "label": "Show Currency Symbol"},
        "currency_symbol": {"type": "string", "label": "Currency Symbol", "maxlength": 5},
    },
    "notifications": {
        "enabled": {"type": "bool", "label": "Enable Notifications"},
        "reminder_days_before": {"type": "int", "label": "Reminder Days Before", "min": 0, "max": 30},
        "auto_dismiss": {"type": "bool", "label": "Auto-Dismiss Notifications"},
        "notification_sound": {"type": "bool", "label": "Notification Sound"},
    },
    "backup": {
        "auto_backup": {"type": "bool", "label": "Automatic Backup"},
        "backup_interval_days": {"type": "int", "label": "Backup Interval (days)", "min": 1, "max": 365},
        "max_backups": {"type": "int", "label": "Max Backup Files", "min": 1, "max": 100},
        "backup_directory": {"type": "string", "label": "Backup Directory"},
    },
    "privacy": {
        "anonymize_logs": {"type": "bool", "label": "Anonymize Logs"},
        "collect_usage_stats": {"type": "bool", "label": "Collect Usage Statistics"},
        "crash_reporting": {"type": "bool", "label": "Crash Reporting"},
    },
}


def _ensure_settings_dir():
    os.makedirs(SETTINGS_DIR, exist_ok=True)


class SettingsManager:
    """Load, save, and manage application settings with sections."""

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._listeners: List[Callable] = []
        self._load()

    def _load(self):
        _ensure_settings_dir()
        self._data = copy.deepcopy(DEFAULT_SETTINGS)
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                for section, values in saved.items():
                    if section in self._data:
                        self._data[section].update(values)
                    else:
                        self._data[section] = values
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load settings: {e}")

    def save(self):
        _ensure_settings_dir()
        try:
            tmp_path = SETTINGS_FILE + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            os.replace(tmp_path, SETTINGS_FILE)
            for cb in self._listeners:
                try:
                    cb(self._data)
                except Exception:
                    logger.exception("Settings listener error")
        except OSError as e:
            logger.error(f"Failed to save settings: {e}")

    def get(self, section: str, key: str, default=None):
        return self._data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any):
        if section not in self._data:
            self._data[section] = {}
        self._data[section][key] = value
        self.save()

    def get_section(self, section: str) -> Dict:
        return self._data.get(section, {}).copy()

    def set_section(self, section: str, values: Dict):
        if section not in self._data:
            self._data[section] = {}
        self._data[section].update(values)
        self.save()

    def reset_to_defaults(self):
        self._data = copy.deepcopy(DEFAULT_SETTINGS)
        self.save()

    def to_dict(self) -> Dict:
        return self._data.copy()

    def get_schema(self) -> Dict:
        return SETTINGS_SCHEMA

    def add_listener(self, callback: Callable[[Dict], None]):
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[Dict], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)


settings_manager = SettingsManager()


# ---------------------------------------------------------------------------
# Settings UI page builder
# ---------------------------------------------------------------------------

def setup_settings_page(parent_frame, style_mgr, settings_mgr: SettingsManager, show_frame_cb: callable):
    """Create and populate the settings page UI."""
    scroll_frame = style_mgr.create_scrollable_frame(parent_frame)
    scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

    header = style_mgr.create_frame(scroll_frame, fg_color="transparent")
    header.pack(fill="x", pady=(0, 20))
    style_mgr.create_label(header, text="Settings", font_style="heading", anchor="w").pack(side="left")
    style_mgr.create_button(header, text="Back", command=lambda: show_frame_cb(None),
                            width=80, fg_color=style_mgr.COLORS["surface"]).pack(side="right")

    sections = settings_mgr.to_dict()
    schema = settings_mgr.get_schema()
    entries = {}

    for section_name, section_data in sections.items():
        section_schema = schema.get(section_name, {})
        box = style_mgr.create_frame(scroll_frame, fg_color=style_mgr.COLORS["surface"], corner_radius=8)
        box.pack(fill="x", pady=(0, 16))
        style_mgr.create_label(box, text=section_name.replace("_", " ").title(), font_style="subheading",
                               anchor="w").pack(anchor="w", padx=16, pady=(12, 4))
        sep = style_mgr.create_frame(box, fg_color=style_mgr.COLORS["border"], height=1)
        sep.pack(fill="x", padx=16, pady=(0, 8))

        row_entries = {}
        for key, value in section_data.items():
            field_schema = section_schema.get(key, {"type": "string", "label": key.replace("_", " ").title()})
            label_text = field_schema.get("label", key.replace("_", " ").title())
            readonly = field_schema.get("readonly", False)

            row = style_mgr.create_frame(box, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)

            style_mgr.create_label(row, text=label_text, font_style="body", width=200, anchor="w").pack(side="left")

            if readonly:
                style_mgr.create_label(row, text=str(value), font_style="body",
                                       text_color=style_mgr.COLORS["text_secondary"], anchor="e").pack(side="right", fill="x", expand=True)
            else:
                field_type = field_schema.get("type", "string")
                from customtkinter import BooleanVar, StringVar

                if field_type == "bool":
                    var = BooleanVar(value=value)
                    ctrl = style_mgr.create_switch(row, text="", variable=var, onvalue=True, offvalue=False)
                    ctrl.pack(side="right")
                    row_entries[key] = ("bool", var)
                elif field_type == "select":
                    options = field_schema.get("options", [str(value)])
                    var = StringVar(value=str(value))
                    ctrl = style_mgr.create_combo(row, values=options, variable=var, width=160)
                    ctrl.pack(side="right")
                    row_entries[key] = ("select", var)
                elif field_type == "color":
                    var = StringVar(value=str(value))
                    ctrl = style_mgr.create_entry(row, variable=var, width=100)
                    ctrl.pack(side="right")
                    row_entries[key] = ("color", var)
                else:
                    var = StringVar(value=str(value))
                    ctrl = style_mgr.create_entry(row, variable=var, width=200)
                    ctrl.pack(side="right")
                    row_entries[key] = ("string", var)

            if key != list(section_data.keys())[-1]:
                sep = style_mgr.create_frame(box, fg_color=style_mgr.COLORS["border"], height=1)
                sep.pack(fill="x", padx=16)

        entries[section_name] = row_entries

    btn_frame = style_mgr.create_frame(scroll_frame, fg_color="transparent")
    btn_frame.pack(fill="x", pady=(8, 0))

    def save_all():
        for section_name, section_entries in entries.items():
            updates = {}
            for key, (ftype, var) in section_entries.items():
                try:
                    if ftype == "bool":
                        updates[key] = bool(var.get())
                    elif ftype == "int":
                        updates[key] = int(var.get())
                    else:
                        updates[key] = var.get()
                except (ValueError, TypeError):
                    pass
            if updates:
                settings_mgr.set_section(section_name, updates)
        messagebox.showinfo("Settings", "Settings saved successfully.")
        logger.info("Settings saved by user.")

    style_mgr.create_button(btn_frame, text="Save Settings", command=save_all,
                            fg_color=style_mgr.COLORS["primary"]).pack(side="left", padx=(0, 8))
    style_mgr.create_button(btn_frame, text="Reset to Defaults", command=lambda: (
        settings_mgr.reset_to_defaults(),
        messagebox.showinfo("Settings", "Reset to defaults. Please reopen Settings to see changes."),
    ), fg_color=style_mgr.COLORS["surface"]).pack(side="left")

    return scroll_frame
