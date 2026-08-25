# -*- coding: utf-8 -*-
"""
MapTileWorker
背景非同步下載 Google 街道地圖瓦片底圖的背景工作元件 (daemon thread)。
"""

from __future__ import annotations
import threading
import numpy as np
import contextily as cx
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

# 路線預覽專用 Google 街道圖 (Roadmap)
GOOGLE_STREETS_URL = "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"


class MapTileWorker(QObject):
    """背景非同步下載 Google 街道地圖瓦片底圖的背景工作元件 (daemon thread)。"""
    tile_ready = Signal(object, float, float, float, float)  # (QImage, left, right, bottom, top)
    fetch_failed = Signal(str)

    def fetch_async(self, west: float, south: float, east: float, north: float, source: str = GOOGLE_STREETS_URL, zoom="auto"):
        def _task():
            try:
                target_zoom = zoom
                try:
                    img_np, extent = cx.bounds2img(
                        west, south, east, north,
                        zoom=target_zoom,
                        source=source,
                        ll=False,
                        use_cache=True,
                        max_retries=2,
                    )
                except Exception:
                    # 若指定高縮放層級超過最大切片數量，自動降階以 auto 備援
                    if target_zoom != "auto":
                        img_np, extent = cx.bounds2img(
                            west, south, east, north,
                            zoom="auto",
                            source=source,
                            ll=False,
                            use_cache=True,
                            max_retries=2,
                        )
                    else:
                        raise

                if img_np is None:
                    return

                if img_np.ndim == 3 and img_np.shape[2] == 4:
                    rgb = np.ascontiguousarray(img_np[:, :, :3])
                else:
                    rgb = np.ascontiguousarray(img_np)

                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, w * ch, QImage.Format_RGB888).copy()
                left, right, bottom, top = map(float, extent)
                self.tile_ready.emit(qimg, left, right, bottom, top)
            except Exception as exc:
                self.fetch_failed.emit(str(exc))

        t = threading.Thread(target=_task, daemon=True)
        t.start()


__all__ = [
    "MapTileWorker",
    "GOOGLE_STREETS_URL",
]
