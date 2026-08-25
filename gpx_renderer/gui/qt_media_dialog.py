# -*- coding: utf-8 -*-
"""
相容轉發層 (Backward Compatibility Shim)。
將舊有對 `gpx_renderer.gui.qt_media_dialog` 的存取無縫導向 `gpx_renderer.gui.media_dialog`。
"""

from gpx_renderer.gui.media_dialog.media_dialog_controller import QtMediaManagerDialog
from gpx_renderer.gui.media_dialog.map_worker import MapTileWorker, GOOGLE_STREETS_URL
from gpx_renderer.gui.media_dialog.widgets import ClickablePreviewLabel, QtRoutePreviewWidget

__all__ = [
    "QtMediaManagerDialog",
    "MapTileWorker",
    "GOOGLE_STREETS_URL",
    "ClickablePreviewLabel",
    "QtRoutePreviewWidget",
]
