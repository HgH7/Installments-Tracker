import json
import logging
import os
from typing import Dict, List, Optional, Type

from app.integrations.integration_base import IntegrationBase
from app.events import dispatcher

logger = logging.getLogger(__name__)

INTEGRATION_CONFIG_FILE = "data/integrations.json"


class IntegrationManager:
    """Manages all external integrations."""

    def __init__(self):
        self._providers: Dict[str, Type[IntegrationBase]] = {}
        self._instances: Dict[str, IntegrationBase] = {}
        self._configs: Dict[str, dict] = {}
        self._load_configs()

    def register(self, cls: Type[IntegrationBase]):
        name = cls.name or cls.__name__
        self._providers[name.lower()] = cls
        if name.lower() in self._configs:
            cfg = self._configs[name.lower()]
            if cfg.get("enabled"):
                self._enable(name.lower())

    def _enable(self, name: str):
        cls = self._providers.get(name)
        if not cls:
            return
        try:
            inst = cls()
            self._instances[name] = inst
            logger.info("Integration enabled: %s", name)
        except Exception as e:
            logger.error("Failed to enable integration %s: %s", name, e)

    def enable(self, name: str) -> bool:
        if name.lower() not in self._providers:
            return False
        self._configs.setdefault(name.lower(), {})["enabled"] = True
        self._enable(name.lower())
        self._save_configs()
        return True

    def disable(self, name: str):
        inst = self._instances.pop(name.lower(), None)
        if inst:
            try:
                inst.disconnect()
            except Exception as e:
                logger.warning("Disconnect error: %s", e)
        if name.lower() in self._configs:
            self._configs[name.lower()]["enabled"] = False
        self._save_configs()

    def get(self, name: str) -> Optional[IntegrationBase]:
        return self._instances.get(name.lower())

    def list_integrations(self) -> List[dict]:
        results = []
        for name, cls in self._providers.items():
            inst = self._instances.get(name)
            results.append({
                "name": name,
                "version": getattr(cls, "version", "1.0.0"),
                "enabled": inst is not None,
                "connected": inst is not None and self._test_connection(inst),
            })
        return results

    def sync_all(self):
        for name, inst in self._instances.items():
            try:
                result = inst.sync()
                dispatcher.emit("integration.synced", {"integration": name, "result": result})
            except Exception as e:
                logger.error("Sync failed for %s: %s", name, e)
                dispatcher.emit("integration.error", {"integration": name, "error": str(e)})

    def _test_connection(self, inst: IntegrationBase) -> bool:
        try:
            return inst.test_connection()
        except Exception:
            return False

    def _load_configs(self):
        if os.path.exists(INTEGRATION_CONFIG_FILE):
            try:
                with open(INTEGRATION_CONFIG_FILE) as f:
                    self._configs = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._configs = {}

    def _save_configs(self):
        os.makedirs(os.path.dirname(INTEGRATION_CONFIG_FILE), exist_ok=True)
        with open(INTEGRATION_CONFIG_FILE, "w") as f:
            json.dump(self._configs, f, indent=2)
