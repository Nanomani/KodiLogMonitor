# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

project_root = Path(os.getcwd())

script_path = project_root / "src" / "KodiLogMonitor.py"
icon_path = project_root / "logo.ico"

if not script_path.exists():
    raise FileNotFoundError(f"Script introuvable: {script_path}")

datas = []
if icon_path.exists():
    datas.append((str(icon_path), "."))

a = Analysis(
    [str(script_path)],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KodiLogMonitor",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(icon_path) if icon_path.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="KodiLogMonitor",
)
