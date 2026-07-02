from app.extensions.auth.permission_manager import PermissionManager, PermissionDenied
from app.extensions.auth.roles import Role, BUILTIN_ROLES
from app.extensions.auth.guard import Guard

perm_manager = PermissionManager()
guard = Guard(perm_manager)

__all__ = ["PermissionManager", "PermissionDenied", "Role", "BUILTIN_ROLES", "Guard", "perm_manager", "guard"]
