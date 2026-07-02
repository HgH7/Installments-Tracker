from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Event:
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    _stopped: bool = field(default=False, repr=False)

    def stop(self):
        self._stopped = True

    @property
    def stopped(self) -> bool:
        return self._stopped


EVENTS = {
    # Customer lifecycle
    "customer.created": "CustomerCreated",
    "customer.updated": "CustomerUpdated",
    "customer.deleted": "CustomerDeleted",
    # Installment lifecycle
    "installment.paid": "InstallmentPaid",
    "installment.created": "InstallmentCreated",
    "installment.overdue": "InstallmentOverdue",
    # Reminder lifecycle
    "reminder.sent": "ReminderSent",
    "reminder.generated": "ReminderGenerated",
    # Backup
    "backup.created": "BackupCreated",
    "backup.restored": "BackupRestored",
    # Activity
    "activity.logged": "ActivityLogged",
    # Automation
    "automation.rule_fired": "AutomationRuleFired",
    "automation.workflow_completed": "AutomationWorkflowCompleted",
    # Plugin
    "plugin.installed": "PluginInstalled",
    "plugin.enabled": "PluginEnabled",
    "plugin.disabled": "PluginDisabled",
    "plugin.uninstalled": "PluginUninstalled",
    # System
    "app.startup": "AppStartup",
    "app.shutdown": "AppShutdown",
    "app.theme_changed": "ThemeChanged",
    "app.language_changed": "LanguageChanged",
    # Integration
    "integration.synced": "IntegrationSynced",
    "integration.error": "IntegrationError",
}
