# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_data_files

# Coleta automaticamente arquivos estáticos, svg, css, js, templates, etc.
datas = collect_data_files("nicegui")

datas += [("images", "images")]
     
block_cipher = None

a = Analysis(
    ['main.py'],      # << ALTERE AQUI se seu arquivo principal tiver outro nome
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='main',       # << nome do executável
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,      # deixe True para ver erros no terminal (recomendado)
)
