# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for Installments Tracker."""

import os
import sys
from datetime import datetime

block_cipher = None

datadir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
datas = []
for root, dirs, files in os.walk(datadir):
    for fn in files:
        if fn.endswith((".png", ".ico", ".json", ".txt", ".md")):
            src = os.path.join(root, fn)
            rel = os.path.relpath(root, os.path.dirname(datadir))
            datas.append((src, rel))

a = Analysis(
    ["The-Project.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "customtkinter",
        "PIL",
        "PIL._tkinter_finder",
        "pandas",
        "pandas._libs.tslibs.timedeltas",
        "pandas._libs.tslibs.np_datetime",
        "pandas._libs.tslibs.nattype",
        "pandas._libs.skiplist",
        "arabic_reshaper",
        "bidi",
        "sqlite3",
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.ttk",
        "app.core.version",
        "app.core.branding",
        "app.core.settings",
        "app.core.crash_recovery",
        "app.core.updater",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter.test",
        "unittest",
        "pytest",
        "email",
        "http",
        # "urllib",  # required by updater
        "pydoc",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Installments-Tracker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join("app", "assets", "icon.ico") if os.path.exists(os.path.join("app", "assets", "icon.ico")) else None,
)

app = BUNDLE(
    exe,
    name="Installments-Tracker.app",
    icon=os.path.join("app", "assets", "icon.ico") if os.path.exists(os.path.join("app", "assets", "icon.ico")) else None,
    bundle_identifier="com.installments-tracker.app",
)
