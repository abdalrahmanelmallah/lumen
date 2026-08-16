# -*- mode: python ; coding: utf-8 -*-
# Lumen.spec — builds the Lumen desktop app for whichever OS you run
# PyInstaller on:
#   macOS   -> dist/Lumen.app  (plus registers the custom icon for .lu
#              files with Finder)
#   Windows -> dist/Lumen/Lumen.exe  (icon embedded in the .exe)
#   Linux   -> dist/Lumen/Lumen      (no icon embedding — ELF binaries
#              don't support it; see "Install Linux Desktop Entry.sh" for
#              getting the icon to show up in your app launcher/file manager)
#
# Built automatically by "Build for Mac.command" / "Build for Windows.bat" /
# "build.sh" — you shouldn't need to run this by hand, but you can with:
#   pyinstaller Lumen.spec

import sys

IS_MAC = sys.platform == "darwin"
IS_WINDOWS = sys.platform.startswith("win")

# Icon PyInstaller should embed in the executable itself. macOS wants
# .icns, Windows wants .ico, Linux (ELF) supports neither so we skip it —
# icon association happens via .desktop file instead on Linux.
if IS_MAC:
    exe_icon = "assets/lumen-app.icns"
elif IS_WINDOWS:
    exe_icon = "assets/lumen-app.ico"
else:
    exe_icon = None

a = Analysis(
    ['lumen_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('libs', 'libs'),
        ('assets/lumen-file.icns', '.'),
        ('assets/lumen-file.ico', '.'),
        ('assets/lumen-logo.png', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Lumen',
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
    icon=exe_icon,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Lumen',
)

# BUNDLE() only makes sense on macOS (it produces a .app). PyInstaller
# ignores/errors on this elsewhere, so only build it when we're on a Mac.
if IS_MAC:
    app = BUNDLE(
        coll,
        name='Lumen.app',
        icon='assets/lumen-app.icns',
        bundle_identifier='com.lumen.app',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            # Tells macOS: "Lumen.app opens .lu files, and here's the
            # icon Finder should show for them."
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Lumen Source File',
                    'CFBundleTypeExtensions': ['lu'],
                    'CFBundleTypeIconFile': 'lumen-file.icns',
                    'CFBundleTypeRole': 'Editor',
                    'LSItemContentTypes': ['com.lumen.lu'],
                    'LSHandlerRank': 'Owner',
                },
            ],
            # Declares the .lu extension as its own file type (UTI),
            # since macOS doesn't know about it otherwise.
            'UTExportedTypeDeclarations': [
                {
                    'UTTypeIdentifier': 'com.lumen.lu',
                    'UTTypeDescription': 'Lumen Source File',
                    'UTTypeConformsTo': ['public.plain-text'],
                    'UTTypeIconFile': 'lumen-file.icns',
                    'UTTypeTagSpecification': {
                        'public.filename-extension': ['lu'],
                    },
                },
            ],
        },
    )
