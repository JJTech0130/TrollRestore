# -*- mode: python ; coding: utf-8 -*-
import site
import platform
from PyInstaller.utils.hooks import copy_metadata

site_packages_path = site.getsitepackages()[0]

datas = []
datas += copy_metadata('readchar')


block_cipher = None

# if windows
binaries = []
if platform.system() == 'Windows':
    binaries += [(f"{site_packages_path}/Lib/site-packages/pytun_pmd3/wintun/*", "pytun_pmd3/wintun/bin")]
else:
    binaries += [(f"{site_packages_path}/pytun_pmd3", "pytun_pmd3")]

a = Analysis(
    ['trollstore.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=['zeroconf', 'zeroconf._utils.ipaddress', 'zeroconf._handlers.answers'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='TrollRestore',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
