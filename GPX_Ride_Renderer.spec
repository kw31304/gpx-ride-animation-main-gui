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
    "gpx_renderer.gui.main_window",
    "gpx_renderer.gui.main_window.main_controller",
    "gpx_renderer.gui.main_window.main_workers",
    "gpx_renderer.gui.main_window.ui_main_window",
    "gpx_renderer.gui.media_dialog",
    "gpx_renderer.gui.media_dialog.media_dialog_controller",
    "gpx_renderer.gui.media_dialog.map_worker",
    "gpx_renderer.gui.video_trim_dialog",
    "gpx_renderer.gui.video_trim_dialog.video_trim_controller",
    "gpx_renderer.gui.widgets",
    "gpx_renderer.gui.widgets.py_circular_progress",
    "gpx_renderer.gui.qt_app",
    "gpx_renderer.gui.qt_media_dialog",
    "gpx_renderer.gui.qt_video_trim_dialog",
    "ctypes",
    "_ctypes",
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

import sys
conda_lib_bin = Path(sys.prefix) / "Library" / "bin"
if conda_lib_bin.exists():
    for pattern in ["*ffi*.dll", "*ssl*.dll", "*crypto*.dll", "*sqlite*.dll", "*bz2*.dll", "*lzma*.dll", "*zlib*.dll"]:
        for dll_file in conda_lib_bin.glob(pattern):
            binaries.append((str(dll_file), "."))

python_dlls = Path(sys.prefix) / "DLLs"
if python_dlls.exists():
    for pyd_file in python_dlls.glob("_ctypes*.pyd"):
        binaries.append((str(pyd_file), "."))
    for dll_file in python_dlls.glob("*.dll"):
        binaries.append((str(dll_file), "."))

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
