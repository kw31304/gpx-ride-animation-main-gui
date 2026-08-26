# -*- coding: utf-8 -*-
"""
一鍵自動打包 GPX Ride Renderer 為獨立 Windows EXE 執行檔與 ZIP 壓縮包之建置腳本。
打包完成後可直接測試，確認無誤後再執行 `python publish_release.py` 發布至 GitHub Releases。
"""

import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def detect_version(project_root: Path) -> str:
    """自動從 gpx_renderer/__init__.py 讀取 __version__ 版本號。"""
    init_file = project_root / "gpx_renderer" / "__init__.py"
    if init_file.exists():
        try:
            content = init_file.read_text(encoding="utf-8")
            match = re.search(r'__version__\s*=\s*["\']([0-9\.]+)["\']', content)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"[WARN] 讀取 __init__.py 版本失敗：{e}")
    return "1.0.0"


def compress_to_zip(source_dir: Path, zip_file: Path) -> Path:
    """將打包產出的資料夾壓縮為 ZIP 檔案。"""
    print(f"\n[INFO] 正在壓縮發行資料夾至 ZIP：{zip_file.name} ...")
    if zip_file.exists():
        try:
            zip_file.unlink()
        except Exception:
            pass

    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in source_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(source_dir)
                zf.write(file, arcname)

    size_mb = zip_file.stat().st_size / (1024 * 1024)
    print(f"[OK] ZIP 壓縮完成！檔案大小：{size_mb:.2f} MB")
    return zip_file


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    cur_dir = Path(__file__).resolve().parent
    project_root = cur_dir if (cur_dir / "gpx_renderer").exists() else cur_dir.parent
    version = detect_version(project_root)

    # 確保環境 PATH 包含當前 Python 的 DLLs 與 Library/bin (避免從 GUI 或非 Conda Prompt 啟動時遺漏 DLL)
    python_dir = Path(sys.executable).parent
    paths_to_add = [
        str(python_dir),
        str(python_dir / "Scripts"),
        str(python_dir / "DLLs"),
        str(python_dir / "Library" / "bin"),
        str(python_dir / "Library" / "usr" / "bin"),
        str(python_dir / "Library" / "mingw-w64" / "bin"),
    ]
    current_path = os.environ.get("PATH", "")
    current_paths = current_path.split(os.pathsep)
    new_paths = [p for p in paths_to_add if Path(p).exists() and p not in current_paths]
    if new_paths:
        os.environ["PATH"] = os.pathsep.join(new_paths + [current_path])

    print("=" * 70)
    print(f"[INFO] 開始執行 GPX Ride Renderer 一鍵 EXE 打包與壓縮作業...")
    print(f"• 偵測目標版本：v{version}")
    print("=" * 70)

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
        root_ffmpeg = project_root.parent / "ffmpeg.exe"
        if root_ffmpeg.exists():
            ffmpeg_src = root_ffmpeg
            print(f"[OK] 找到專案根目錄 FFmpeg 核心：{ffmpeg_src}")

    if not ffmpeg_src or not ffmpeg_src.exists():
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            ffmpeg_src = Path(system_ffmpeg)
            print(f"[OK] 找到系統 FFmpeg 核心：{ffmpeg_src}")

    # 3. 處理 Conda 虛擬環境相容性（消除 PyInstaller conda-meta 警告）
    venv_dir = project_root / ".venv"
    if venv_dir.exists():
        conda_meta_dir = venv_dir / "conda-meta"
        if not conda_meta_dir.exists():
            try:
                conda_meta_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

    # 4. 檢查與準備 PyInstaller .spec 設定檔
    spec_file = project_root / "GPX_Ride_Renderer.spec"
    dist_dir = Path("D:/gpx-ride-animation-releases") if Path("D:/").exists() else (project_root.parent / "gpx-ride-animation-releases")
    dist_dir.mkdir(parents=True, exist_ok=True)

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
    "gpx_renderer.gui", "gpx_renderer.gui.main_window", "gpx_renderer.gui.main_window.main_controller",
    "gpx_renderer.gui.main_window.main_workers", "gpx_renderer.gui.main_window.ui_main_window",
    "gpx_renderer.gui.media_dialog", "gpx_renderer.gui.media_dialog.media_dialog_controller",
    "gpx_renderer.gui.media_dialog.map_worker", "gpx_renderer.gui.video_trim_dialog",
    "gpx_renderer.gui.video_trim_dialog.video_trim_controller", "gpx_renderer.gui.widgets",
    "gpx_renderer.gui.widgets.py_circular_progress", "gpx_renderer.gui.qt_app",
    "gpx_renderer.gui.qt_media_dialog", "gpx_renderer.gui.qt_video_trim_dialog",
    "ctypes", "_ctypes",
    "PySide6", "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets",
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
        "--distpath",
        str(dist_dir),
        str(spec_file),
    ]

    print(f"[INFO] 正在執行 PyInstaller 編譯打包至 {dist_dir} (讀取 GPX_Ride_Renderer.spec)...")
    subprocess.check_call(cmd, cwd=str(project_root))

    # 5. 複製 ffmpeg.exe 至 EXE 輸出資料夾
    target_output_dir = dist_dir / "GPX_Ride_Renderer"
    if ffmpeg_src and ffmpeg_src.exists():
        dest_ffmpeg = target_output_dir / "ffmpeg.exe"
        print(f"[INFO] 正在複製 FFmpeg 核心至輸出目錄：{dest_ffmpeg}")
        shutil.copy2(ffmpeg_src, dest_ffmpeg)

    exe_path = target_output_dir / "GPX_Ride_Renderer.exe"
    if not exe_path.exists():
        print("[ERROR] 打包失敗，未能產出 EXE 檔案。")
        sys.exit(1)

    print("=" * 70)
    print("[SUCCESS] 打包完成！")
    print(f"• EXE 執行檔路徑：{exe_path}")
    print(f"• 發行資料夾路徑：{target_output_dir}")
    print("=" * 70)

    # 6. 自動壓縮為 ZIP 檔案
    zip_filename = f"GPX_Ride_Renderer_v{version}_windows_x64.zip"
    zip_path = dist_dir / zip_filename
    compress_to_zip(target_output_dir, zip_path)

    # 7. 打包編譯完成後自動刪除 build 暫存資料夾
    build_dir = project_root / "build"
    if build_dir.exists():
        print(f"\n[INFO] 正在自動清理 build 編譯暫存資料夾：{build_dir} ...")
        try:
            shutil.rmtree(build_dir, ignore_errors=True)
            print("[OK] build 編譯暫存資料夾已自動刪除！")
        except Exception as e:
            print(f"[WARN] 清理 build 資料夾失敗：{e}")

    print("\n" + "=" * 70)
    print("💡 下一步指引：")
    print(f"1. 請先前往 `{target_output_dir}` 執行 `GPX_Ride_Renderer.exe` 進行功能測試。")
    print(f"2. 測試確認無誤後，請在終端機執行：")
    print(f"   python publish_release.py")
    print(f"   即可手動將 `{zip_filename}` 發布至 GitHub Releases 公開給其他使用者！")
    print("=" * 70)


if __name__ == "__main__":
    main()


