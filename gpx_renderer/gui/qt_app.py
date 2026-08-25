# -*- coding: utf-8 -*-
"""
相容轉發層 (Backward Compatibility Shim)。
將舊有對 `gpx_renderer.gui.qt_app` 的存取無縫導向 `gpx_renderer.gui.main_window`。
"""

from gpx_renderer.gui.main_window.main_controller import (
    MainWindow, launch_qt_gui, launch_qt_gui as launch_gui, RESOLUTION_PRESETS, CAMERA_MODE_LABELS
)
from gpx_renderer.gui.main_window.main_workers import (
    SubprocessReaderThread, GpxDistanceThread, CacheSizeWorkerThread
)

__all__ = [
    "MainWindow",
    "launch_qt_gui",
    "launch_gui",
    "SubprocessReaderThread",
    "GpxDistanceThread",
    "CacheSizeWorkerThread",
    "RESOLUTION_PRESETS",
    "CAMERA_MODE_LABELS",
]

if __name__ == "__main__":
    launch_qt_gui()
