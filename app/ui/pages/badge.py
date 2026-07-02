def get_action_badge(action: str) -> tuple:
    badges = {
        "Customer created": ("New", "success"),
        "Customer updated": ("Updated", "info"),
        "Customer deleted": ("Deleted", "danger"),
        "Payment recorded": ("Payment", "success"),
        "Backup created": ("Backup", "info"),
        "Backup restored": ("Restored", "warning"),
        "Export completed": ("Export", "info"),
        "Import completed": ("Import", "info"),
    }
    for key, (text, tone) in badges.items():
        if key.lower() in action.lower():
            return text, tone
    return "Info", "info"
