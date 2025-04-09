# -*- mode: python ; coding: utf-8 -*-

import sys
sys.path.append("src\\")
import swapper

a = Analysis(
    ['src\\swapper.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src\\LogoIcon.ico','.')
    ],
    hiddenimports=[],
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
    name='electron-swapper',
    debug=False,
    icon='src\\LogoIcon.ico',
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='src\\version.rc',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='swapper',
)
