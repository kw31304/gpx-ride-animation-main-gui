# -*- coding: utf-8 -*-
"""
一鍵自動打包 GPX Ride Renderer 為獨立 Windows EXE 執行檔之建置腳本。
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 70)
    print("[INFO] 開始執行 GPX Ride Renderer 一鍵 EXE 打包作業...")
    print("=" * 70)

    project_root = Path(__file__).resolve().parent
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"

    if not venv_python.exists():
        venv_python = Path(sys.executable)

    # 1. 檢查與安裝 PyInstaller
    try:
        import PyInstaller
        print(f"[OK] 偵測到 PyInstaller 版本：{PyInstaller.__version__}")
    except ImportError:
        print("[INFO] 未偵測到 PyInstaller，正在自動透過 pip 安裝...")
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "pyinstaller"])

    # 2. 尋找 FFmpeg 執行檔核心
    ffmpeg_src = None
    try:
        import imageio_ffmpeg
        ffmpeg_src = Path(imageio_ffmpeg.get_ffmpeg_exe())
        if ffmpeg_src.exists():
            print(f"[OK] 找到 FFmpeg 核心：{ffmpeg_src}")
    except Exception:
        pass

    if not ffmpeg_src or not ffmpeg_src.exists():
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            ffmpeg_src = Path(system_ffmpeg)
            print(f"[OK] 找到系統 FFmpeg 核心：{ffmpeg_src}")

    # 3. 檢查與準備 PyInstaller .spec 設定檔
    spec_file = project_root / "GPX_Ride_Renderer.spec"
    dist_dir = project_root / "dist"

    if not spec_file.exists():
        print(f"[WARN] 未找到 {spec_file.name}，正在自動建立最新標準打包設定檔...")
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

block_cipher = None
project_root = Path(os.path.abspath("."))
ui_file = project_root / "gpx_renderer" / "gui" / "main_window.ui"
assets_dir = project_root / "gpx_renderer" / "assets"

hidden_imports = [
    "gpx_renderer", "gpx_renderer.config", "gpx_renderer.utils", "gpx_renderer.utils.env",
    "gpx_renderer.core", "gpx_renderer.core.data", "gpx_renderer.core.map_utils",
    "gpx_renderer.core.encoder", "gpx_renderer.core.renderer", "gpx_renderer.core.parallel",
    "gpx_renderer.core.media", "gpx_renderer.core.dem_utils", "gpx_renderer.core.terrain_3d",
    "gpx_renderer.gui", "gpx_renderer.gui.qt_app", "gpx_renderer.gui.ui_main_window",
    "gpx_renderer.gui.qt_media_dialog", "PySide6", "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets",
    "PIL", "PIL.Image", "PIL.ImageDraw", "PIL.ImageFont", "PIL.ImageFilter",
    "cv2", "numpy", "matplotlib", "gpxpy", "requests", "contextily",
    "geopy", "shapely", "pyproj", "exifread", "rasterio", "imageio_ffmpeg",
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
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="GPX_Ride_Renderer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GPX_Ride_Renderer",
)
'''
        with open(spec_file, "w", encoding="utf-8") as f:
            f.write(spec_content)
        print(f"[OK] 已成功產生 {spec_file.name}")

    cmd = [
        str(venv_python),
        "-m",
        "PyInstaller",
        "--noconfirm",
        str(spec_file),
    ]

    print("[INFO] 正在執行 PyInstaller 編譯打包 (讀取 GPX_Ride_Renderer.spec)...")
    subprocess.check_call(cmd, cwd=str(project_root))

    # 4. 複製 ffmpeg.exe 至 EXE 輸出資料夾
    target_output_dir = dist_dir / "GPX_Ride_Renderer"
    if ffmpeg_src and ffmpeg_src.exists():
        dest_ffmpeg = target_output_dir / "ffmpeg.exe"
        print(f"[INFO] 正在複製 FFmpeg 核心至輸出目錄：{dest_ffmpeg}")
        shutil.copy2(ffmpeg_src, dest_ffmpeg)

    exe_path = target_output_dir / "GPX_Ride_Renderer.exe"
    if exe_path.exists():
        print("=" * 70)
        print("[SUCCESS] 打包完成！")
        print(f"• EXE 執行檔路徑：{exe_path}")
        print(f"• 發行資料夾路徑：{target_output_dir}")
        print("=" * 70)
    else:
        print("[ERROR] 打包失敗，未能產出 EXE 檔案。")
        sys.exit(1)


if __name__ == "__main__":
    main()
