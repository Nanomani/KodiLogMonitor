# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

# Définir les chemins relatifs à la racine du repo
cwd = Path.cwd()
src_dir = cwd / "src"
script_path = src_dir / "KodiLogMonitor.py"
icon_path = cwd / "logo.ico"

# Récupérer toutes les ressources si nécessaire (ici exemple avec Tkinter)
datas = [(str(icon_path), ".")]

# Analyse du script
a = Analysis(
    [str(script_path)],
    pathex=[str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False
)

# Créer archive PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Créer l’exécutable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="KodiLogMonitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Tkinter GUI, pas de console
    icon=str(icon_path)
)

# Collecter pour créer le dossier final si besoin
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="KodiLogMonitor"
)
