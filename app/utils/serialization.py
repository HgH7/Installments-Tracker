import ast
import json
import logging
from typing import Any, Dict, List


def _safe_load(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default.copy()
    if isinstance(value, (list, dict)):
        return value

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        pass

    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError, TypeError) as exc:
        logging.warning(f"Unable to parse serialized value: {value!r}. Error: {exc}")
        return default.copy()


def load_json_list(value: Any) -> List:
    parsed = _safe_load(value, [])
    if isinstance(parsed, list):
        return parsed
    logging.warning(f"Expected serialized list, got {type(parsed).__name__}: {value!r}")
    return []


def load_json_dict(value: Any) -> Dict:
    parsed = _safe_load(value, {})
    if isinstance(parsed, dict):
        return parsed
    logging.warning(f"Expected serialized dict, got {type(parsed).__name__}: {value!r}")
    return {}


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)
