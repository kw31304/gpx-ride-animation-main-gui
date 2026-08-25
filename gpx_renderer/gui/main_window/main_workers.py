# -*- coding: utf-8 -*-
"""
主視窗專屬非同步背景工作執行緒 (Workers)
"""

from __future__ import annotations
import subprocess
from PySide6.QtCore import QThread, Signal
from gpx_renderer.core.data import quick_gpx_distance_km


class SubprocessReaderThread(QThread):
    """讀取渲染/測試子程序 stdout 的線程 Signals"""
    line_signal = Signal(str)
    finished_signal = Signal(int)

    def __init__(self, proc: subprocess.Popen, parent=None):
        super().__init__(parent)
        self.proc = proc

    def run(self):
        try:
            if self.proc.stdout is not None:
                for line in iter(self.proc.stdout.readline, ""):
                    line_str = line.strip()
                    if line_str:
                        self.line_signal.emit(line_str)
        except Exception:
            pass
        finally:
            rc = self.proc.wait()
            self.finished_signal.emit(rc)


class GpxDistanceThread(QThread):
    """背景讀取 GPX 路線總里程"""
    success_signal = Signal(float)
    failed_signal = Signal(str)

    def __init__(self, gpx_path: str, parent=None):
        super().__init__(parent)
        self.gpx_path = gpx_path

    def run(self):
        try:
            dist = quick_gpx_distance_km(self.gpx_path)
            self.success_signal.emit(dist)
        except Exception as exc:
            self.failed_signal.emit(str(exc))


class CacheSizeWorkerThread(QThread):
    """背景計算快取容量的執行緒，避免數萬張切片檔案遍歷阻塞 Qt 主執行緒"""
    size_signal = Signal(float)

    def run(self):
        try:
            from gpx_renderer.core.cache_manager import CacheManager
            mb = CacheManager.get_cache_size_mb(max_age_sec=30.0)
            self.size_signal.emit(mb)
        except Exception:
            pass


__all__ = [
    "SubprocessReaderThread",
    "GpxDistanceThread",
    "CacheSizeWorkerThread",
]
