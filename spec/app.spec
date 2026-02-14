# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

# Chemins
project_root = Path(__file__).parent.parent
script_path = project_root / "src" / "KodiLogMonitor.py"
icon_path = project_root / "logo.ico"

# Vérification de l'existence du fichier principal
if not script_path.exists():
    raise FileNotFoundError(f"Le script principal n'existe pas: {script_path}")

# Vérification de l'icône (optionnelle)
datas = []
if icon_path.exists():
    datas.append((str(icon_path), "."))  # copie à la racine de l'exe

# Analyse
a = Analysis(
    [str(script_path)],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Compilation du bytecode
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Création de l'exécutable
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
    console=True,  # mettre False si tu veux une GUI
    icon=str(icon_path) if icon_path.exists() else None
)

# Collecte finale (dist)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="KodiLogMonitor"
)
