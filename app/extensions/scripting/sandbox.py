"""Safe Python script execution with restricted builtins."""

import logging
import traceback
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool,
    "dict": dict, "enumerate": enumerate, "filter": filter,
    "float": float, "format": format, "frozenset": frozenset,
    "int": int, "isinstance": isinstance, "len": len,
    "list": list, "map": map, "max": max, "min": min,
    "range": range, "reversed": reversed, "round": round,
    "set": set, "slice": slice, "sorted": sorted,
    "str": str, "sum": sum, "tuple": tuple, "type": type,
    "zip": zip, "True": True, "False": False, "None": None,
    "print": lambda *a: None,
}


class ScriptSandbox:
    """Executes user Python scripts in a restricted environment."""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self._context = {
            "__builtins__": SAFE_BUILTINS,
            "customers": [],
            "installments": [],
            "services": {},
            "db": None,
            "events": None,
        }
        if context:
            self._context.update(context)

    def set_context(self, **kwargs):
        self._context.update(kwargs)

    def execute(self, code: str) -> Dict[str, Any]:
        result = {"success": False, "output": None, "error": None}
        try:
            compiled = compile(code, "<script>", "exec")
            exec(compiled, self._context)
            result["success"] = True
            result["output"] = self._context.get("result")
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            logger.warning("Script execution failed: %s", e)
        return result

    def evaluate(self, expr: str) -> Any:
        try:
            compiled = compile(expr, "<script>", "eval")
            return eval(compiled, self._context)
        except Exception as e:
            logger.warning("Script evaluation failed: %s", e)
            return None
