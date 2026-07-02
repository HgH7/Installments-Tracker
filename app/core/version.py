"""Application version information — single source of truth for version metadata."""

__version__ = "2.0.0"
__release_date__ = "2026-06-27"
__build__ = "RC1"
__author__ = "Otman"
__license__ = "MIT"

APP_NAME = "Installments Tracker"
APP_DESCRIPTION = "Desktop management application for tracking customer installments and payments."
COMPANY_NAME = "Installments Tracker"
COMPANY_URL = "https://github.com/otman-22-git/Installments-Tracker"
COPYRIGHT = f"Copyright © 2020-2026 {COMPANY_NAME}. All rights reserved."
VERSION_STRING = f"v{__version__}"
VERSION_PARTS = tuple(int(p) for p in __version__.split("."))


def get_version_info() -> dict:
    return {
        "app_name": APP_NAME,
        "version": __version__,
        "version_parts": VERSION_PARTS,
        "build": __build__,
        "release_date": __release_date__,
        "version_string": VERSION_STRING,
        "company": COMPANY_NAME,
        "copyright": COPYRIGHT,
        "author": __author__,
        "license": __license__,
    }
