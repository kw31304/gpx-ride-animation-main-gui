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

    # 3. 執行 PyInstaller 編譯 (.spec 檔模式)
    spec_file = project_root / "GPX_Ride_Renderer.spec"
    dist_dir = project_root / "dist"

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
