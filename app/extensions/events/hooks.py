from typing import Any, Callable, Dict, List


class HookRegistry:
    """Before/after hooks for service methods.

    Allows plugins to wrap method calls without modifying the source.
    """

    def __init__(self):
        self._before: Dict[str, List[Callable]] = {}
        self._after: Dict[str, List[Callable]] = {}
        self._instead: Dict[str, Callable] = {}

    def register_before(self, hook_point: str, fn: Callable):
        self._before.setdefault(hook_point, []).append(fn)

    def register_after(self, hook_point: str, fn: Callable):
        self._after.setdefault(hook_point, []).append(fn)

    def register_instead(self, hook_point: str, fn: Callable):
        self._instead[hook_point] = fn

    def run_before(self, hook_point: str, *args, **kwargs) -> bool:
        for fn in self._before.get(hook_point, []):
            result = fn(*args, **kwargs)
            if result is False:
                return False
        return True

    def run_after(self, hook_point: str, *args, **kwargs):
        for fn in self._after.get(hook_point, []):
            fn(*args, **kwargs)

    def get_instead(self, hook_point: str):
        return self._instead.get(hook_point)

    def clear(self):
        self._before.clear()
        self._after.clear()
        self._instead.clear()
