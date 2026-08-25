# -*- coding: utf-8 -*-
"""
相容轉發層 (Backward Compatibility Shim)。
將舊有對 `gpx_renderer.gui.qt_video_trim_dialog` 的存取無縫導向 `gpx_renderer.gui.video_trim_dialog`。
"""

from gpx_renderer.gui.video_trim_dialog.video_trim_controller import QtVideoTrimDialog

__all__ = [
    "QtVideoTrimDialog",
]
