from app.i18n.language_manager import LanguageManager
from app.i18n.locales import BUILTIN_LOCALES

lang = LanguageManager()

__all__ = ["LanguageManager", "BUILTIN_LOCALES", "lang"]
