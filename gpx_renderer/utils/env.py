# -*- coding: utf-8 -*-
"""
執行環境設定、系統平台相容性 (UTF-8 stdio/Win32 Console) 及字型載入工具。
"""

import os
import sys
import subprocess
from pathlib import Path
from PIL import ImageFont


def _force_utf8_stdio():
    """Force UTF-8 for stdout/stderr in source, frozen EXE, and spawned workers.

    PyInstaller frozen subprocesses on Traditional-Chinese Windows can keep the
    system CP950 encoding even when PYTHONIOENCODING is present in the parent
    environment.  The GUI reads the pipe as UTF-8, so mixed CP950/UTF-8 output
    becomes mojibake.  Reconfigure the actual TextIOWrapper in every process.
    """
    for stream_name, fd in (("stdout", 1), ("stderr", 2)):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            try:
                stream = open(
                    fd, mode="w", encoding="utf-8", errors="replace",
                    buffering=1, closefd=False,
                )
            except (OSError, ValueError):
                stream = open(
                    os.devnull, mode="w", encoding="utf-8", errors="replace",
                    buffering=1,
                )
            setattr(sys, stream_name, stream)
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", write_through=True)
        except (AttributeError, ValueError, OSError):
            pass

    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"


def _background_subprocess_kwargs():
    """Return Windows flags that keep console executables in the background."""
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


def application_dir() -> Path:
    """原始碼模式回傳 .py 所在資料夾；PyInstaller 模式回傳 .exe 所在資料夾。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def _font_candidates(bold: bool):
    if os.name == "nt":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        if bold:
            names = ["msjhbd.ttc", "msjhl.ttc", "arialbd.ttf", "seguisb.ttf"]
        else:
            names = ["msjh.ttc", "msjhl.ttc", "arial.ttf", "segoeui.ttf"]
        return [windir / n for n in names]

    names = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    if bold:
        names = sorted(names, key=lambda p: ("Bold" not in p, p))
    return [Path(p) for p in names]


def load_font(size: int, bold: bool = False):
    for path in _font_candidates(bold):
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def _hide_frozen_console_for_gui():
    """PyInstaller 採 console bootloader 以保留子程序 stdout；GUI 模式啟動後隱藏主 console。"""
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except Exception:
        pass
