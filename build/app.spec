block_cipher = None

a = Analysis(
    ['../src/KodiLogMonitor.py'],
    pathex=[],
    binaries=[],
    datas=[('../src/logo.ico', '.')],
    hiddenimports=[],
    hookspath=[],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KodiLogMonitor',
    console=False,
    icon='src/logo.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='KodiLogMonitor'
)
