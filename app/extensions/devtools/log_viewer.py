"""Read and filter application logs."""

import glob
import logging
import os
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

LOG_DIR = "logs"


class LogViewer:
    """Browse, search, and filter log files."""

    def list_logs(self) -> List[dict]:
        logs = []
        if not os.path.exists(LOG_DIR):
            return logs
        for f in sorted(glob.glob(os.path.join(LOG_DIR, "*.log")), reverse=True)[:20]:
            size = os.path.getsize(f)
            logs.append({
                "path": f,
                "name": os.path.basename(f),
                "size": size,
                "size_str": f"{size / 1024:.1f} KB" if size > 1024 else f"{size} B",
                "modified": datetime.fromtimestamp(os.path.getmtime(f)).isoformat(),
            })
        return logs

    def read(self, log_path: str, max_lines: int = 200,
             level: Optional[str] = None,
             search: Optional[str] = None) -> List[str]:
        if not os.path.exists(log_path):
            return ["[Log file not found]"]
        lines = []
        try:
            with open(log_path) as f:
                for line in f:
                    if level and level.upper() not in line:
                        continue
                    if search and search.lower() not in line.lower():
                        continue
                    lines.append(line.rstrip())
                    if len(lines) >= max_lines:
                        break
        except IOError as e:
            lines.append(f"[Error reading log: {e}]")
        return lines

    def tail(self, log_path: str, n: int = 50) -> List[str]:
        """Return last n lines of a log file."""
        if not os.path.exists(log_path):
            return ["[Log file not found]"]
        try:
            with open(log_path) as f:
                all_lines = f.readlines()
            return [l.rstrip() for l in all_lines[-n:]]
        except IOError as e:
            return [f"[Error: {e}]"]
