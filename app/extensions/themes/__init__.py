from app.extensions.themes.theme import Theme
from app.extensions.themes.theme_engine import ThemeEngine, _BUILTIN_THEMES, theme_engine

builtin_themes = dict(_BUILTIN_THEMES)

__all__ = [
    "Theme",
    "ThemeEngine",
    "builtin_themes",
    "theme_engine",
]
