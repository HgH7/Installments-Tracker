"""Auto-update mechanism — checks GitHub releases and applies updates.

The updater fetches the latest release tag from a remote repository,
compares it against the local version, and either notifies the user
or performs a full replacement update.
"""

import json
import logging
import os
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from threading import Thread
from tkinter import messagebox
from typing import Callable, Optional

from app.core.version import APP_NAME, __version__

UPDATE_CHECK_INTERVAL_DAYS = 3
REMOTE_RELEASES_URL = "https://api.github.com/repos/otman-22-git/Installments-Tracker/releases/latest"
REMOTE_DOWNLOAD_URL_TEMPLATE = "https://github.com/otman-22-git/Installments-Tracker/releases/download/v{version}/Installments-Tracker-v{version}.zip"

logger = logging.getLogger(__name__)


@dataclass
class UpdateInfo:
    available: bool = False
    latest_version: str = ""
    download_url: str = ""
    release_notes: str = ""
    published_at: str = ""
    error: Optional[str] = None


class UpdateChecker:
    """Check for updates against the GitHub releases API."""

    def __init__(self, current_version: str = __version__):
        self.current_version = current_version
        self._info: Optional[UpdateInfo] = None

    def _parse_version(self, v: str) -> tuple:
        try:
            v = v.lstrip("v")
            parts = v.split(".")
            cleaned = []
            for p in parts[:3]:
                digits = ""
                for ch in p:
                    if ch.isdigit():
                        digits += ch
                    else:
                        break
                cleaned.append(int(digits) if digits else 0)
            return tuple(cleaned)
        except (ValueError, IndexError):
            return (0, 0, 0)

    def check(self, timeout: int = 10) -> UpdateInfo:
        """Query the GitHub API for the latest release."""
        info = UpdateInfo()
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(
                REMOTE_RELEASES_URL,
                headers={"Accept": "application/vnd.github.v3+json", "User-Agent": f"{APP_NAME}/{__version__}"},
            )
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            info.latest_version = data.get("tag_name", "").lstrip("v")
            info.published_at = data.get("published_at", "")
            info.release_notes = data.get("body", "")
            info.download_url = REMOTE_DOWNLOAD_URL_TEMPLATE.format(version=info.latest_version)

            current_parsed = self._parse_version(self.current_version)
            latest_parsed = self._parse_version(info.latest_version)
            info.available = latest_parsed > current_parsed
        except urllib.error.URLError as e:
            info.error = f"Network error: {e.reason}"
            logger.warning(f"Update check failed (network): {e}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            info.error = f"Parse error: {e}"
            logger.warning(f"Update check failed (parse): {e}")
        except Exception as e:
            info.error = f"Unexpected error: {e}"
            logger.warning(f"Update check failed: {e}")

        self._info = info
        return info

    @property
    def info(self) -> Optional[UpdateInfo]:
        return self._info


def check_for_updates_async(callback: Callable[[UpdateInfo], None]):
    """Run an update check in a background thread."""

    def _worker():
        checker = UpdateChecker()
        info = checker.check()
        callback(info)

    Thread(target=_worker, daemon=True).start()


def download_update(info: UpdateInfo, progress_callback: Optional[Callable[[int], None]] = None) -> Optional[str]:
    """Download the update zip file to a temp location. Returns the path."""
    if not info.download_url:
        return None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        tmp_path = tmp.name
        tmp.close()

        ctx = ssl.create_default_context()
        req = urllib.request.Request(info.download_url, headers={"User-Agent": f"{APP_NAME}/{__version__}"})
        with urllib.request.urlopen(req, context=ctx) as resp:
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 8192
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0 and progress_callback:
                        progress_callback(int(downloaded * 100 / total))
        return tmp_path
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return None


def apply_update(zip_path: str, target_dir: str = None) -> bool:
    """Extract the zip into the application directory and restart."""
    if target_dir is None:
        target_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        backup_dir = target_dir + ".bak"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(target_dir, backup_dir)

        extract_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        extracted_items = os.listdir(extract_dir)
        for item in extracted_items:
            src = os.path.join(extract_dir, item)
            dst = os.path.join(target_dir, item)
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                else:
                    os.unlink(dst)
            shutil.move(src, dst)

        shutil.rmtree(extract_dir)
        os.unlink(zip_path)
        logger.info(f"Update applied successfully. Backup at {backup_dir}")
        return True
    except Exception as e:
        logger.error(f"Update application failed: {e}", exc_info=True)
        if os.path.exists(backup_dir):
            try:
                shutil.rmtree(target_dir)
                shutil.copytree(backup_dir, target_dir)
                shutil.rmtree(backup_dir)
                logger.info("Rolled back to previous version.")
            except OSError:
                logger.critical("Rollback failed!")
        return False


def restart_application():
    """Restart the application (current process)."""
    python = sys.executable
    script = os.path.abspath(sys.argv[0])
    args = sys.argv[1:]
    try:
        subprocess.Popen([python, script] + args)
    except Exception as e:
        logger.error(f"Failed to restart: {e}")
    sys.exit(0)


def offer_update_dialog(parent, info: UpdateInfo) -> bool:
    """Show the user a dialog asking whether to download and install an update."""
    if not info.available:
        return False
    msg = (
        f"A new version of {APP_NAME} is available!\n\n"
        f"Current version: v{__version__}\n"
        f"Latest version:  v{info.latest_version}\n\n"
        f"{info.release_notes}\n\n"
        "Download and install now?"
    )
    return messagebox.askyesno(f"{APP_NAME} — Update Available", msg)


def show_no_update_dialog(parent):
    """Inform the user that the application is up to date."""
    messagebox.showinfo(
        f"{APP_NAME} — Up to Date",
        f"Version v{__version__} is the latest version.",
    )


def show_error_dialog(parent, error_msg: str):
    """Show an update error to the user."""
    messagebox.showerror(f"{APP_NAME} — Update Error", f"Could not check for updates.\n\n{error_msg}")
