# -*- mode: python ; coding: utf-8 -*-
"""
GPX Ride Renderer - PyInstaller 打包設定檔 (Spec)
"""

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

block_cipher = None

project_root = Path(os.path.abspath("."))
ui_file = project_root / "gpx_renderer" / "gui" / "main_window.ui"
assets_dir = project_root / "gpx_renderer" / "assets"

hidden_imports = [
    "gpx_renderer",
    "gpx_renderer.config",
    "gpx_renderer.utils",
    "gpx_renderer.utils.env",
    "gpx_renderer.core",
    "gpx_renderer.core.data",
    "gpx_renderer.core.map_utils",
    "gpx_renderer.core.encoder",
    "gpx_renderer.core.renderer",
    "gpx_renderer.core.parallel",
    "gpx_renderer.core.media",
    "gpx_renderer.core.dem_utils",
    "gpx_renderer.core.terrain_3d",
    "gpx_renderer.gui",
    "gpx_renderer.gui.qt_app",
    "gpx_renderer.gui.ui_main_window",
    "gpx_renderer.gui.qt_media_dialog",
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "PIL.ImageFont",
    "PIL.ImageFilter",
    "cv2",
    "numpy",
    "matplotlib",
    "gpxpy",
    "requests",
    "contextily",
    "geopy",
    "shapely",
    "pyproj",
    "exifread",
    "rasterio",
    "imageio_ffmpeg",
]

for pkg in ["rasterio", "contextily", "geopy", "pyproj", "shapely", "exifread", "PySide6"]:
    try:
        hidden_imports.extend(collect_submodules(pkg))
    except Exception:
        pass

hidden_imports = list(dict.fromkeys(hidden_imports))

datas = []
if ui_file.exists():
    datas.append((str(ui_file), "gpx_renderer/gui"))

if assets_dir.exists():
    datas.append((str(assets_dir), "gpx_renderer/assets"))

for pkg in ["rasterio", "contextily", "pyproj"]:
    try:
        datas.extend(collect_data_files(pkg))
    except Exception:
        pass

binaries = []
for pkg in ["rasterio", "shapely", "pyproj"]:
    try:
        binaries.extend(collect_dynamic_libs(pkg))
    except Exception:
        pass

a = Analysis(
    ["GPX_Ride_Renderer.py"],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
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
    name="GPX_Ride_Renderer",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GPX_Ride_Renderer",
)
