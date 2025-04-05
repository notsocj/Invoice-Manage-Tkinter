# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('logo.jpg', '.'),
    ('config/*.json', 'config/'),
    ('fonts/DejaVuSans.ttf', 'fonts/'),  # Add if you use these fonts
    ('fonts/DejaVuSans-Bold.ttf', 'fonts/'),
]

hiddenimports=[
    'sqlalchemy.sql.default_comparator', 
    'PIL._tkinter_finder',
    'reportlab.rl_config',  # For PDF generation
    'tkinter',
    'tkinter.ttk',
    'customtkinter',  # Make sure this is included
    'tempfile',  # For temporary file handling
],
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['sqlalchemy.sql.default_comparator', 'PIL._tkinter_finder'],
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
    [],
    exclude_binaries=True,
    name='Invoice Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.jpg',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Invoice Manager',
)