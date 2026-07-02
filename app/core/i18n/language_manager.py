import json
import logging
import os
from typing import Dict, Optional

from app.extensions.events import dispatcher

logger = logging.getLogger(__name__)

LOCALE_DIR = "app/i18n/locales"
LOCALE_PREF_FILE = "data/locale_pref.json"


class LanguageManager:
    """Manages UI string translations without restart."""

    def __init__(self):
        self._current_lang: str = "en"
        self._strings: Dict[str, str] = {}
        self._fallback: Dict[str, str] = {}
        self._load_preference()
        self._load_fallback()

    def _load_fallback(self):
        fallback_path = os.path.join(LOCALE_DIR, "en.json")
        if os.path.exists(fallback_path):
            try:
                with open(fallback_path) as f:
                    self._fallback = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load fallback locale: %s", e)

    def _load_preference(self):
        if os.path.exists(LOCALE_PREF_FILE):
            try:
                with open(LOCALE_PREF_FILE) as f:
                    self._current_lang = json.load(f).get("locale", "en")
            except (json.JSONDecodeError, IOError):
                pass

    def _save_preference(self):
        os.makedirs(os.path.dirname(LOCALE_PREF_FILE), exist_ok=True)
        with open(LOCALE_PREF_FILE, "w") as f:
            json.dump({"locale": self._current_lang}, f)

    def set_locale(self, lang: str) -> bool:
        path = os.path.join(LOCALE_DIR, f"{lang}.json")
        if not os.path.exists(path):
            logger.warning("Locale not found: %s", lang)
            return False
        try:
            with open(path) as f:
                self._strings = json.load(f)
            self._current_lang = lang
            self._save_preference()
            dispatcher.emit("app.language_changed", {"locale": lang})
            logger.info("Switched to locale: %s", lang)
            return True
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load locale %s: %s", lang, e)
            return False

    def get(self, key: str, default: Optional[str] = None) -> str:
        return self._strings.get(key, self._fallback.get(key, default or key))

    def get_current_locale(self) -> str:
        return self._current_lang

    def list_locales(self) -> list:
        if not os.path.exists(LOCALE_DIR):
            return ["en"]
        locales = []
        for f in os.listdir(LOCALE_DIR):
            if f.endswith(".json"):
                locales.append(f[:-5])
        return sorted(locales)

    def translate_ui(self, widget, key: str, attr: str = "text"):
        """Set a widget's text attribute from the current locale."""
        value = self.get(key)
        try:
            if hasattr(widget, attr):
                setattr(widget, attr, value)
            elif hasattr(widget, "configure"):
                widget.configure(**{attr: value})
        except Exception as e:
            logger.warning("Failed to translate widget: %s", e)
