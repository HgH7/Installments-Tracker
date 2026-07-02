from dataclasses import dataclass, field
from typing import List


@dataclass
class Role:
    name: str
    permissions: List[str] = field(default_factory=list)

    def has(self, permission: str) -> bool:
        if "*" in self.permissions:
            return True
        return permission in self.permissions


BUILTIN_ROLES = {
    "admin": Role("admin", ["*"]),
    "manager": Role("manager", [
        "customer.view", "customer.create", "customer.edit", "customer.delete",
        "installment.view", "installment.create", "installment.edit", "installment.pay",
        "report.view", "export.csv", "export.excel",
        "backup.create", "backup.restore",
        "activity.view",
        "plugin.view", "plugin.install", "plugin.uninstall",
        "settings.view", "settings.edit",
        "task.view", "task.create", "task.edit", "task.delete",
        "contract.view", "contract.create", "contract.edit",
        "expense.view", "expense.create",
    ]),
    "accountant": Role("accountant", [
        "customer.view",
        "installment.view", "installment.pay",
        "report.view", "export.csv", "export.excel",
        "expense.view", "expense.create",
        "contract.view",
    ]),
    "readonly": Role("readonly", [
        "customer.view",
        "installment.view",
        "report.view",
        "activity.view",
    ]),
}
