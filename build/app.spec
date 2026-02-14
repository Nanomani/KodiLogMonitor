# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# chemin vers le script principal
script_path = str(Path(__file__).parent.parent / "src" / "KodiLogMonitor.py")

# chemin vers l'icône
icon_path = str(Path(__file__).parent.parent / "src" / "logo.ico")

# conversion icône macOS (.icns) si nécessaire
if sys.platform == "darwin":
    icon_path = str(Path(__file__).parent.parent / "logo.icns")  # généré dans workflow macOS

a = Analysis(
    [script_path],
    pathex=[],
    binaries=[],
    datas=[(icon_path, ".")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KodiLogMonitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="KodiLogMonitor",
)
