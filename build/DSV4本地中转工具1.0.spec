# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — 从项目根目录运行:
#   pyinstaller build/DSV4本地中转工具1.0.spec

import os
_src = os.path.join(SPECPATH, '..', 'src')

a = Analysis(
    [os.path.join(_src, 'window_app.py')],
    pathex=[_src],
    binaries=[],
    datas=[(os.path.join(_src, 'ds_adapter'), 'ds_adapter')],
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
    a.binaries,
    a.datas,
    [],
    name='DSV4本地中转工具1.0',
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
)
