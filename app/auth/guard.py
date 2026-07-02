import logging
from functools import wraps
from typing import Callable

from app.auth.permission_manager import PermissionDenied, PermissionManager

logger = logging.getLogger(__name__)


class Guard:
    """Decorator-based permission checks."""

    def __init__(self, perm_mgr: PermissionManager):
        self._perm_mgr = perm_mgr

    def require(self, permission: str):
        def decorator(fn: Callable):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                self._perm_mgr.require(permission)
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    def check(self, permission: str) -> bool:
        return self._perm_mgr.has_permission(permission)
