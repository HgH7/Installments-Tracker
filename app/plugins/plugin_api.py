from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    author: str = "Unknown"
    description: str = ""
    min_app_version: str = "2.0.0"
    dependencies: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)


class PluginBase:
    manifest: PluginManifest

    def on_load(self):
        pass

    def on_unload(self):
        pass

    def on_enable(self):
        pass

    def on_disable(self):
        pass


class PluginAPI:
    """Exposed to plugins for safe access to application internals."""

    def __init__(self, app_ref):
        self._app = app_ref

    @property
    def db(self):
        return self._app.db if hasattr(self._app, "db") else None

    @property
    def services(self):
        return self._app.services if hasattr(self._app, "services") else {}

    @property
    def events(self):
        from app.events import dispatcher
        return dispatcher

    @property
    def hooks(self):
        from app.events import hooks
        return hooks

    @property
    def settings(self):
        from app.settings import settings
        return settings

    def get_service(self, name: str):
        return self.services.get(name)

    def get_setting(self, key: str, default=None):
        return getattr(self.settings, key, default)

    def log(self, message: str, level: str = "info"):
        import logging
        getattr(logging.getLogger("plugin"), level)(message)
