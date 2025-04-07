# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Define data files to include
datas = [
    ('customer_files', 'customer_files'),
    ('backups', 'backups'),
    ('logs', 'logs'),
    ('customers.csv', '.'),
    ('PyWhatKit_DB.txt', '.')
]

# Add additional binary dependencies
binaries = []

# Add additional hidden imports
hiddenimports = [
    'customtkinter',
    'tkinter',
    'tkcalendar',
    'pandas',
    'pywhatkit',
    'logging',
    'csv',
    'os',
    'sys',
    're',
    'datetime',
    'shutil',
    'threading',
    'time',
    'traceback',
    'numpy',
    'PIL',
    'PIL._tkinter_finder',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.ttk'
]

a = Analysis(
    ['The-Project.py'],
    pathex=[os.getcwd()],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Installments Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Installments Manager',
) 