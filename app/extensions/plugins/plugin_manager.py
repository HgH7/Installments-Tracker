import json
import logging
import os
import shutil
from typing import Dict, List, Optional

from app.extensions.plugins.plugin_api import PluginBase, PluginManifest
from app.extensions.plugins.plugin_loader import PluginLoader
from app.utils.paths import DATA_DIR

logger = logging.getLogger(__name__)

PLUGIN_DB_PATH = os.path.join(DATA_DIR, "plugin_registry.json")


class PluginManager:
    """Installs, enables, disables, and removes plugins."""

    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self._loader = PluginLoader([plugin_dir])
        self._registry: Dict[str, dict] = {}
        self._load_registry()

    # ── Registry persistence ─────────────────────────────────────────────

    def _load_registry(self):
        if os.path.exists(PLUGIN_DB_PATH):
            try:
                with open(PLUGIN_DB_PATH) as f:
                    self._registry = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._registry = {}

    def _save_registry(self):
        os.makedirs(os.path.dirname(PLUGIN_DB_PATH), exist_ok=True)
        tmp_path = PLUGIN_DB_PATH + ".tmp"
        try:
            with open(tmp_path, "w") as f:
                json.dump(self._registry, f, indent=2)
            os.replace(tmp_path, PLUGIN_DB_PATH)
        except OSError:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _plugin_path(self, plugin_id: str) -> str:
        return os.path.join(self.plugin_dir, plugin_id)

    # ── Lifecycle ────────────────────────────────────────────────────────

    def install(self, source_path: str) -> Optional[str]:
        meta_path = os.path.join(source_path, "plugin.json")
        if not os.path.exists(meta_path):
            return "Missing plugin.json"
        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except (json.JSONDecodeError, IOError):
            return "Invalid plugin.json"
        pid = meta.get("id")
        if not pid:
            return "plugin.json missing 'id'"
        dest = self._plugin_path(pid)
        if os.path.exists(dest):
            return f"Plugin '{pid}' already installed"
        shutil.copytree(source_path, dest)
        self._registry[pid] = {"enabled": True, "meta": meta}
        self._save_registry()
        from app.extensions.events import dispatcher
        dispatcher.emit("plugin.installed", {"plugin_id": pid})
        return None

    def uninstall(self, plugin_id: str) -> Optional[str]:
        if plugin_id not in self._registry:
            return f"Plugin '{plugin_id}' not found"
        self.disable(plugin_id)
        self._loader.unload(plugin_id)
        path = self._plugin_path(plugin_id)
        if os.path.exists(path):
            shutil.rmtree(path)
        del self._registry[plugin_id]
        self._save_registry()
        from app.extensions.events import dispatcher
        dispatcher.emit("plugin.uninstalled", {"plugin_id": plugin_id})
        return None

    def enable(self, plugin_id: str) -> Optional[str]:
        if plugin_id not in self._registry:
            return f"Plugin '{plugin_id}' not found"
        self._registry[plugin_id]["enabled"] = True
        self._save_registry()
        path = self._plugin_path(plugin_id)
        if os.path.exists(path):
            inst = self._loader.load(plugin_id, path)
            if inst:
                try:
                    inst.on_enable()
                except Exception as e:
                    logger.error("Plugin on_enable error: %s", e)
        from app.extensions.events import dispatcher
        dispatcher.emit("plugin.enabled", {"plugin_id": plugin_id})
        return None

    def disable(self, plugin_id: str) -> Optional[str]:
        if plugin_id not in self._registry:
            return f"Plugin '{plugin_id}' not found"
        self._registry[plugin_id]["enabled"] = False
        self._save_registry()
        inst = self._loader.get(plugin_id)
        if inst:
            try:
                inst.on_disable()
            except Exception as e:
                logger.error("Plugin on_disable error: %s", e)
        self._loader.unload(plugin_id)
        from app.extensions.events import dispatcher
        dispatcher.emit("plugin.disabled", {"plugin_id": plugin_id})
        return None

    def load_all(self):
        discovered = self._loader.discover()
        for pid, path in discovered.items():
            if self._registry.get(pid, {}).get("enabled", True):
                self._loader.load(pid, path)

    # ── Query ────────────────────────────────────────────────────────────

    def list_plugins(self) -> List[dict]:
        results = []
        for pid, info in self._registry.items():
            results.append({
                "id": pid,
                "name": info.get("meta", {}).get("name", pid),
                "version": info.get("meta", {}).get("version", "?"),
                "author": info.get("meta", {}).get("author", "Unknown"),
                "enabled": info.get("enabled", False),
                "loaded": self._loader.get(pid) is not None,
            })
        return results

    def is_enabled(self, plugin_id: str) -> bool:
        return self._registry.get(plugin_id, {}).get("enabled", False)

    @property
    def loader(self) -> PluginLoader:
        return self._loader
