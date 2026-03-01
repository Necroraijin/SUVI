# -*- mode: python ; coding: utf-8 -*-
# PyInstaller configuration for building the Windows Executable

block_cipher = None

a = Analysis(
    ['suvi\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pyautogui', 'pynput', 'qasync', 'mss', 'PIL', 'sounddevice'],
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
    name='SUVI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Set to False so the terminal hides when running the .exe!
    icon='suvi/resources/icons/app.ico' # We will generate this icon later
)