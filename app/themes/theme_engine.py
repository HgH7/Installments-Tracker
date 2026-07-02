import json
import logging
import os
from typing import Dict, List, Optional

import customtkinter

from app.events import dispatcher
from app.themes.theme import Theme

logger = logging.getLogger(__name__)

THEMES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "themes",
)
CURRENT_THEME_FILE = os.path.join(THEMES_DIR, "current_theme.json")

_DEFAULT_FONTS: Dict[str, tuple] = {
    "heading": ("Segoe UI", 20, "bold"),
    "subheading": ("Segoe UI", 15, "bold"),
    "section": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 13, "normal"),
    "body_bold": ("Segoe UI", 13, "bold"),
    "small": ("Segoe UI", 11, "normal"),
    "label": ("Segoe UI", 11, "bold"),
    "data": ("Courier New", 12, "normal"),
    "button": ("Segoe UI", 13, "bold"),
}

_BUILTIN_THEMES: Dict[str, Theme] = {
    "dark": Theme(
        name="dark",
        is_dark=True,
        colors={
            "background": "#1a1a2e",
            "surface": "#16213e",
            "surface_high": "#1e2a45",
            "surface_low": "#0f0f23",
            "primary": "#2563eb",
            "text": "#ffffff",
            "text_secondary": "#94a3b8",
            "text_muted": "#64748b",
            "border": "#2d3748",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#3b82f6",
        },
        fonts=_DEFAULT_FONTS,
        corner_radius=8,
    ),
    "light": Theme(
        name="light",
        is_dark=False,
        colors={
            "background": "#f8fafc",
            "surface": "#ffffff",
            "surface_high": "#f1f5f9",
            "surface_low": "#e2e8f0",
            "primary": "#2563eb",
            "text": "#0f172a",
            "text_secondary": "#475569",
            "text_muted": "#94a3b8",
            "border": "#cbd5e1",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#3b82f6",
        },
        fonts=_DEFAULT_FONTS,
        corner_radius=8,
    ),
    "corporate": Theme(
        name="corporate",
        is_dark=True,
        colors={
            "background": "#0f172a",
            "surface": "#1e293b",
            "surface_high": "#334155",
            "surface_low": "#0a0f1a",
            "primary": "#1d4ed8",
            "text": "#f1f5f9",
            "text_secondary": "#94a3b8",
            "text_muted": "#64748b",
            "border": "#334155",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#3b82f6",
        },
        fonts=_DEFAULT_FONTS,
        corner_radius=6,
    ),
}


class ThemeEngine:
    def __init__(self):
        self._themes: Dict[str, Theme] = {}
        self._current: Optional[Theme] = None
        self._ensure_dirs()
        self._load_builtin_themes()
        self._load_user_themes()
        self._load_current()

    # ------------------------------------------------------------------ #
    # internal helpers
    # ------------------------------------------------------------------ #

    def _ensure_dirs(self):
        try:
            os.makedirs(THEMES_DIR, exist_ok=True)
        except OSError:
            logger.exception("Failed to create themes directory")

    def _load_builtin_themes(self):
        for name, theme in _BUILTIN_THEMES.items():
            self._themes[name] = theme

    def _load_user_themes(self):
        if not os.path.isdir(THEMES_DIR):
            return
        for fname in os.listdir(THEMES_DIR):
            if fname == "current_theme.json" or not fname.endswith(".json"):
                continue
            path = os.path.join(THEMES_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                theme = Theme.from_dict(data)
                if theme.name not in _BUILTIN_THEMES:
                    self._themes[theme.name] = theme
            except Exception:
                logger.exception(f"Failed to load user theme from {fname}")

    def _load_current(self):
        try:
            if os.path.exists(CURRENT_THEME_FILE):
                with open(CURRENT_THEME_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("theme", "dark")
                self._current = self._themes.get(name)
        except Exception:
            logger.exception("Failed to load current theme preference")

        if self._current is None:
            self._current = self._themes.get("dark") or next(
                iter(self._themes.values()), None
            )

    def _persist_current(self, theme_name: str):
        try:
            with open(CURRENT_THEME_FILE, "w", encoding="utf-8") as f:
                json.dump({"theme": theme_name}, f, indent=2)
        except OSError:
            logger.exception("Failed to persist current theme")

    def _save_user_theme(self, theme: Theme):
        path = os.path.join(THEMES_DIR, f"{theme.name}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(theme.to_dict(), f, indent=2)
        except OSError:
            logger.exception(f"Failed to save user theme '{theme.name}'")

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #

    def register_theme(self, theme: Theme):
        if theme.name in _BUILTIN_THEMES:
            logger.warning(
                "Cannot register theme '%s': name conflicts with a built-in theme",
                theme.name,
            )
            return
        self._themes[theme.name] = theme
        self._save_user_theme(theme)
        logger.info("Theme '%s' registered successfully", theme.name)

    def apply(self, theme_name: str):
        if theme_name not in self._themes:
            raise ValueError(
                f"Theme '{theme_name}' not found. Available: {self.list_themes()}"
            )
        theme = self._themes[theme_name]
        self._current = theme
        try:
            customtkinter.set_appearance_mode("dark" if theme.is_dark else "light")
        except Exception:
            logger.exception("Failed to set customtkinter appearance mode")
        self._persist_current(theme_name)
        dispatcher.emit(
            "app.theme_changed",
            {"theme": theme_name, "theme_obj": theme},
        )
        logger.info("Theme switched to '%s'", theme_name)

    def get_current(self) -> Optional[Theme]:
        return self._current

    def list_themes(self) -> List[str]:
        return list(self._themes.keys())

    def create_custom(self, name: str, colors_dict: Dict[str, str]) -> Theme:
        if name in _BUILTIN_THEMES:
            raise ValueError(f"Cannot create theme with built-in name '{name}'")
        base = self._current or next(iter(self._themes.values()))
        colors = {**base.colors, **colors_dict}
        theme = Theme(
            name=name,
            is_dark=base.is_dark,
            colors=colors,
            fonts=dict(base.fonts),
            corner_radius=base.corner_radius,
        )
        self.register_theme(theme)
        return theme

    def remove_theme(self, name: str):
        if name in _BUILTIN_THEMES:
            raise ValueError(f"Cannot remove built-in theme '{name}'")
        if name not in self._themes:
            raise ValueError(f"Theme '{name}' not found")
        del self._themes[name]
        theme_file = os.path.join(THEMES_DIR, f"{name}.json")
        try:
            if os.path.exists(theme_file):
                os.remove(theme_file)
        except OSError:
            logger.exception(f"Failed to remove theme file '{theme_file}'")
        if self._current and self._current.name == name:
            fallback = "dark" if "dark" in self._themes else next(iter(self._themes))
            self.apply(fallback)
        logger.info("Theme '%s' removed", name)


theme_engine = ThemeEngine()
