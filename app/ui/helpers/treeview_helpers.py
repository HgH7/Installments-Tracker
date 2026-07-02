from typing import Dict, List, Optional

from app.ui.styles.style import StyleManager


def refresh_treeview(tree, data: Optional[List[Dict]] = None):
    """Refresh the treeview with data."""
    for item in tree.get_children():
        tree.delete(item)

    columns = tree["columns"]
    tree.tag_configure("empty", foreground=StyleManager.COLORS["text_muted"])
    if not data:
        placeholder = ["—"] * len(columns)
        tree.insert("", "end", values=placeholder, tags=("empty",))
        return

    for customer in data:
        values = [customer.get(col, "") for col in columns]
        tree.insert("", "end", values=values)

