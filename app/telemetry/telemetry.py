"""Local-only telemetry — tracks performance, crashes, and plugin health."""

import json
import logging
import os
import time
import traceback
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

TELEMETRY_FILE = "data/telemetry.json"
MAX_RECORDS = 1000


class Telemetry:
    """Records local metrics. NO data leaves the machine."""

    def __init__(self):
        self._enabled = True
        self._metrics: Dict[str, list] = defaultdict(list)
        self._startup_time: Optional[float] = None
        self._load()

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ── Startup ──────────────────────────────────────────────────────────

    def record_startup(self):
        self._startup_time = time.time()

    def record_startup_complete(self):
        if self._startup_time:
            self._add("startup", {
                "duration_ms": round((time.time() - self._startup_time) * 1000, 2),
                "timestamp": datetime.now().isoformat(),
            })

    # ── Slow queries ─────────────────────────────────────────────────────

    def record_query(self, sql: str, duration_ms: float):
        if duration_ms > 100:
            self._add("slow_query", {
                "sql": sql[:120],
                "duration_ms": round(duration_ms, 2),
                "timestamp": datetime.now().isoformat(),
            })

    # ── Memory ───────────────────────────────────────────────────────────

    def record_memory(self, label: str = ""):
        try:
            import psutil
            proc = psutil.Process()
            mem = proc.memory_info().rss / 1024 / 1024
            self._add("memory", {
                "label": label,
                "mb": round(mem, 1),
                "timestamp": datetime.now().isoformat(),
            })
        except ImportError:
            pass

    # ── Plugin performance ───────────────────────────────────────────────

    def record_plugin_hook(self, plugin_id: str, hook: str, duration_ms: float):
        if duration_ms > 50:
            self._add("plugin_perf", {
                "plugin": plugin_id,
                "hook": hook,
                "duration_ms": round(duration_ms, 2),
            })

    # ── Crashes ──────────────────────────────────────────────────────────

    def record_crash(self, error: str, component: str = "unknown"):
        self._add("crash", {
            "error": str(error)[:200],
            "component": component,
            "traceback": traceback.format_exc()[-500:],
            "timestamp": datetime.now().isoformat(),
        })

    # ── Event counts ─────────────────────────────────────────────────────

    def record_event(self, event_name: str):
        self._add("events", {"event": event_name, "timestamp": datetime.now().isoformat()})

    # ── Internal ─────────────────────────────────────────────────────────

    def _add(self, category: str, data: dict):
        if not self._enabled:
            return
        self._metrics[category].append(data)
        if len(self._metrics[category]) > MAX_RECORDS:
            self._metrics[category] = self._metrics[category][-MAX_RECORDS:]
        self._save()

    def get_metrics(self, category: Optional[str] = None) -> dict:
        if category:
            return {category: self._metrics.get(category, [])}
        return dict(self._metrics)

    def clear(self):
        self._metrics.clear()
        if os.path.exists(TELEMETRY_FILE):
            os.remove(TELEMETRY_FILE)

    # ── Persistence ──────────────────────────────────────────────────────

    def _load(self):
        if os.path.exists(TELEMETRY_FILE):
            try:
                with open(TELEMETRY_FILE) as f:
                    loaded = json.load(f)
                for k, v in loaded.items():
                    self._metrics[k] = v
            except (json.JSONDecodeError, IOError):
                pass

    def _save(self):
        try:
            os.makedirs(os.path.dirname(TELEMETRY_FILE), exist_ok=True)
            with open(TELEMETRY_FILE, "w") as f:
                json.dump(dict(self._metrics), f, indent=2)
        except IOError as e:
            logger.warning("Failed to save telemetry: %s", e)
