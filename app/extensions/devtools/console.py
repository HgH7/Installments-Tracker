"""Interactive Python console for developers."""

import logging
import traceback
from typing import Any, Dict, Optional

from app.extensions.scripting.sandbox import ScriptSandbox

logger = logging.getLogger(__name__)


class DeveloperConsole:
    """Interactive Python REPL for debugging and introspection."""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self._sandbox = ScriptSandbox(context)
        self._history: list = []

    def set_context(self, **kwargs):
        self._sandbox.set_context(**kwargs)

    def execute(self, code: str) -> Dict[str, Any]:
        self._history.append(code)
        return self._sandbox.execute(code)

    def get_history(self, limit: int = 50) -> list:
        return self._history[-limit:]

    def clear_history(self):
        self._history.clear()

    def inspect(self, obj_name: str) -> Dict[str, Any]:
        result = {"name": obj_name, "type": None, "value": None, "dir": []}
        try:
            val = self._sandbox.evaluate(obj_name)
            result["type"] = type(val).__name__
            result["value"] = repr(val)[:200]
            result["dir"] = [x for x in dir(val) if not x.startswith("_")]
        except Exception as e:
            result["error"] = str(e)
        return result
