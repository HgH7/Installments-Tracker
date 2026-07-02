import importlib
import inspect
import logging
import os
import sys
from typing import Dict, List, Optional

from app.plugins.plugin_api import PluginBase, PluginManifest

logger = logging.getLogger(__name__)


class PluginLoader:
    """Dynamically loads plugins from a directory."""

    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        self.plugin_dirs = plugin_dirs or []
        self._loaded: Dict[str, PluginBase] = {}

    def add_directory(self, path: str):
        if path not in self.plugin_dirs:
            self.plugin_dirs.append(path)

    def discover(self) -> Dict[str, str]:
        """Return {plugin_id: path} for all discoverable plugins."""
        found: Dict[str, str] = {}
        for d in self.plugin_dirs:
            if not os.path.isdir(d):
                continue
            for entry in os.listdir(d):
                plugin_path = os.path.join(d, entry)
                manifest_path = os.path.join(plugin_path, "plugin.json")
                if os.path.isdir(plugin_path) and os.path.exists(manifest_path):
                    import json
                    try:
                        with open(manifest_path) as f:
                            meta = json.load(f)
                        pid = meta.get("id", entry)
                        found[pid] = plugin_path
                    except (json.JSONDecodeError, IOError) as e:
                        logger.warning("Skipping %s: %s", entry, e)
        return found

    def load(self, plugin_id: str, plugin_path: str) -> Optional[PluginBase]:
        if plugin_id in self._loaded:
            return self._loaded[plugin_id]
        if plugin_path not in sys.path:
            sys.path.insert(0, os.path.dirname(plugin_path))
        try:
            module = importlib.import_module(os.path.basename(plugin_path))
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, PluginBase) and obj is not PluginBase:
                    instance = obj()
                    self._loaded[plugin_id] = instance
                    logger.info("Loaded plugin: %s", plugin_id)
                    return instance
            logger.warning("No PluginBase subclass in %s", plugin_id)
        except Exception as e:
            logger.error("Failed to load plugin %s: %s", plugin_id, e)
        return None

    def unload(self, plugin_id: str):
        instance = self._loaded.pop(plugin_id, None)
        if instance:
            try:
                instance.on_unload()
            except Exception as e:
                logger.error("Error unloading %s: %s", plugin_id, e)

    def get(self, plugin_id: str) -> Optional[PluginBase]:
        return self._loaded.get(plugin_id)

    @property
    def loaded(self) -> Dict[str, PluginBase]:
        return dict(self._loaded)
