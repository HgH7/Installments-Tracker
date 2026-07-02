"""Inspect plugin state, hooks, and events."""

import logging
from typing import Dict, List

from app.events import dispatcher, hooks
from app.plugins.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class PluginDebugger:
    """Monitor plugin lifecycle, hook registrations, and event flow."""

    def __init__(self, plugin_mgr: PluginManager):
        self._pm = plugin_mgr
        self._event_log: List[dict] = []

    def list_plugins(self) -> List[dict]:
        return self._pm.list_plugins()

    def plugin_detail(self, plugin_id: str) -> dict:
        inst = self._pm.loader.get(plugin_id)
        return {
            "id": plugin_id,
            "loaded": inst is not None,
            "enabled": self._pm.is_enabled(plugin_id),
            "manifest": getattr(inst, "manifest", None),
            "hooks": {},
        }

    def list_hooks(self) -> Dict[str, list]:
        result = {}
        for point, fns in hooks._before.items():
            result[f"before:{point}"] = [fn.__name__ for fn in fns]
        for point, fns in hooks._after.items():
            result[f"after:{point}"] = [fn.__name__ for fn in fns]
        for point, fn in hooks._instead.items():
            result[f"instead:{point}"] = [fn.__name__]
        return result

    def list_event_listeners(self) -> Dict[str, int]:
        from app.events import dispatcher as d
        result = {}
        for event, handlers in d._listeners.items():
            result[event] = len(handlers)
        result["*"] = len(d._wildcard)
        return result

    def record_event(self, event_name: str, data: dict = None):
        from datetime import datetime
        self._event_log.append({
            "event": event_name,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self._event_log) > 500:
            self._event_log = self._event_log[-500:]

    def get_event_log(self, limit: int = 50) -> List[dict]:
        return self._event_log[-limit:]
