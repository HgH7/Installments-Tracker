import json
import logging
import os
from typing import Dict, Optional

from app.auth.roles import BUILTIN_ROLES, Role

logger = logging.getLogger(__name__)

PERMISSION_FILE = "data/permissions.json"


class PermissionDenied(Exception):
    pass


class PermissionManager:
    """Manages user roles and permission checks. Single-user mode by default."""

    def __init__(self):
        self._roles: Dict[str, Role] = dict(BUILTIN_ROLES)
        self._current_role: str = "admin"
        self._load()

    def _load(self):
        if os.path.exists(PERMISSION_FILE):
            try:
                with open(PERMISSION_FILE) as f:
                    data = json.load(f)
                self._current_role = data.get("role", "admin")
                for r in data.get("custom_roles", []):
                    self._roles[r["name"]] = Role(r["name"], r.get("permissions", []))
            except (json.JSONDecodeError, IOError):
                pass

    def _save(self):
        os.makedirs(os.path.dirname(PERMISSION_FILE), exist_ok=True)
        with open(PERMISSION_FILE, "w") as f:
            json.dump({
                "role": self._current_role,
                "custom_roles": [{"name": n, "permissions": r.permissions}
                                 for n, r in self._roles.items()
                                 if n not in BUILTIN_ROLES],
            }, f, indent=2)

    def set_role(self, role_name: str):
        if role_name in self._roles:
            self._current_role = role_name
            self._save()
        else:
            raise ValueError(f"Unknown role: {role_name}")

    def get_current_role(self) -> Role:
        return self._roles.get(self._current_role, self._roles["admin"])

    def has_permission(self, permission: str) -> bool:
        return self.get_current_role().has(permission)

    def require(self, permission: str):
        if not self.has_permission(permission):
            raise PermissionDenied(f"Missing permission: {permission}")

    def list_roles(self) -> Dict[str, Role]:
        return dict(self._roles)

    def add_role(self, role: Role):
        self._roles[role.name] = role
        self._save()
