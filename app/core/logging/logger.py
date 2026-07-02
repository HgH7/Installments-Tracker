import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "logs")


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


_ensure_log_dir()


class AppLogger:
    _instance: Optional["AppLogger"] = None

    def __init__(self, log_dir: str = LOG_DIR):
        self.log_dir = log_dir
        _ensure_log_dir()
        self._root = logging.getLogger()
        self._root.setLevel(logging.DEBUG)
        self._setup_handlers()
        self.info("AppLogger initialized", component="system")

    def _setup_handlers(self):
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        app_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "app.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(formatter)

        error_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "errors.log"),
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(formatter)

        migration_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "migrations.log"),
            maxBytes=1 * 1024 * 1024,
            backupCount=2,
        )
        migration_handler.setLevel(logging.INFO)
        migration_handler.setFormatter(formatter)

        backup_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "backups.log"),
            maxBytes=1 * 1024 * 1024,
            backupCount=2,
        )
        backup_handler.setLevel(logging.INFO)
        backup_handler.setFormatter(formatter)

        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)

        self._root.handlers.clear()
        self._root.addHandler(app_handler)
        self._root.addHandler(error_handler)
        self._root.addHandler(migration_handler)
        self._root.addHandler(backup_handler)
        self._root.addHandler(console)

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)

    def info(self, message: str, component: str = "app", **extra):
        logger = self.get_logger(component)
        extra_str = " ".join(f"{k}={v}" for k, v in extra.items())
        msg = f"{message}  {extra_str}" if extra_str else message
        logger.info(msg)

    def warning(self, message: str, component: str = "app", **extra):
        logger = self.get_logger(component)
        extra_str = " ".join(f"{k}={v}" for k, v in extra.items())
        msg = f"{message}  {extra_str}" if extra_str else message
        logger.warning(msg)

    def error(self, message: str, component: str = "app", **extra):
        logger = self.get_logger(component)
        extra_str = " ".join(f"{k}={v}" for k, v in extra.items())
        msg = f"{message}  {extra_str}" if extra_str else message
        logger.error(msg)

    def migration(self, message: str, **extra):
        self.info(message, component="migration", **extra)

    def backup(self, message: str, **extra):
        self.info(message, component="backup", **extra)


logger = AppLogger()
