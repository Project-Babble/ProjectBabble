# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows, macOS and Linux. (Android builds use buildozer.spec instead.)
#   pyinstaller babbleapp.spec

import sys
from kivy.tools.packaging.pyinstaller_hooks import hookspath, runtime_hooks

block_cipher = None

# Kivy's native dependencies (SDL2, GLEW, ANGLE) ship as separate wheels on Windows.
kivy_dep_trees = []
if sys.platform == "win32":
    from kivy_deps import sdl2, glew

    dep_bins = sdl2.dep_bins + glew.dep_bins
    try:
        from kivy_deps import angle

        dep_bins += angle.dep_bins
    except ImportError:
        pass
    kivy_dep_trees = [Tree(p) for p in dep_bins]


a = Analysis(['babbleapp.py'],
             pathex=[],
             binaries=[],
             datas=[("Audio", "Audio"), ("Images", "Images"), ("Locale", "Locale"), ("Models", "Models")],
             hiddenimports=[],
             hookspath=hookspath(),
             runtime_hooks=runtime_hooks(),
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Babble_App',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon="Images/logo.ico" )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               *kivy_dep_trees,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Babble_App')
