from app.auth.permission_manager import PermissionManager, PermissionDenied
from app.auth.roles import Role, BUILTIN_ROLES
from app.auth.guard import Guard

perm_manager = PermissionManager()
guard = Guard(perm_manager)

__all__ = ["PermissionManager", "PermissionDenied", "Role", "BUILTIN_ROLES", "Guard", "perm_manager", "guard"]
