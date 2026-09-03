# -*- coding: utf-8 -*-
"""
QtRoutePreviewWidget
PySide6 向量路線預覽 Canvas，支援 Google 街道圖底圖、多層級動態縮放、平移與動態媒體標記點連動。
"""

from __future__ import annotations
import math
from typing import List, Optional
import numpy as np

from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QTimer
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QImage, QPolygonF
)
from PySide6.QtWidgets import QWidget

from gpx_renderer.core.media import MediaItem
from gpx_renderer.core.data import RideData
from gpx_renderer.gui.media_dialog.map_worker import MapTileWorker, GOOGLE_STREETS_URL


class QtRoutePreviewWidget(QWidget):
    """PySide6 向量路線預覽 Canvas，支援 Google 街道圖底圖、多層級動態縮放、平移與動態媒體標記點連動。"""
    item_selected = Signal(int)

    def __init__(self, parent=None, ride_data: Optional[RideData] = None):
        # 兼容 Qt uic 預設 (parent) 與直接傳入 (ride_data, parent) 兩種呼叫簽名
        if isinstance(parent, RideData):
            ride_data, parent = parent, ride_data
        super().__init__(parent)
        self.ride_data: Optional[RideData] = ride_data
        self.media_items: List[MediaItem] = []
        self.selected_index: int = -1
        self.active_km: float = -1.0

        self.scale = 1.0  # pixels per meter
        self.drag_start_pos: Optional[QPointF] = None
        self.is_dragging = False

        # 底圖狀態 (支援依風格設定或 Google 街道圖)
        self.map_source = GOOGLE_STREETS_URL
        self.map_style_label = "Google Maps 街道圖"
        self.map_zoom: int | str = "auto"
        self.map_qimage: Optional[QImage] = None
        self.map_extent: Optional[tuple[float, float, float, float]] = None
        self.is_loading_map = False
        self._current_rendered_zoom: int | str = "auto"

        self.map_worker = MapTileWorker(self)
        self.map_worker.tile_ready.connect(self._on_map_tile_ready)
        self.map_worker.fetch_failed.connect(self._on_map_fetch_failed)

        # 動態視野防抖計時器 (避免滑鼠連續滾輪或拖曳時過度請求)
        self._reload_timer = QTimer(self)
        self._reload_timer.setSingleShot(True)
        self._reload_timer.setInterval(200)  # 200ms 防抖
        self._reload_timer.timeout.connect(self._do_fetch_viewport_basemap)

        self.setMouseTracking(True)
        self.setMinimumSize(320, 240)

        if ride_data is not None:
            self.set_ride_data(ride_data)
        else:
            self.view_center_x = 0.0
            self.view_center_y = 0.0
            self.route_w = 100.0
            self.route_h = 100.0
            self.sampled_xs = np.array([])
            self.sampled_ys = np.array([])

    def set_ride_data(self, ride_data: RideData):
        """設置或更新 GPX 騎乘軌跡資料，重新初始化視圖座標與抽樣點。"""
        self.ride_data = ride_data
        self.view_center_x = float(ride_data.route_center_x)
        self.view_center_y = float(ride_data.route_center_y)

        min_x, max_x = float(ride_data.xs.min()), float(ride_data.xs.max())
        min_y, max_y = float(ride_data.ys.min()), float(ride_data.ys.max())
        self.route_w = max(max_x - min_x, 100.0)
        self.route_h = max(max_y - min_y, 100.0)

        # 抽樣軌跡點以提升畫圖效率
        step = max(1, len(ride_data.xs) // 600)
        self.sampled_xs = ride_data.xs[::step]
        self.sampled_ys = ride_data.ys[::step]

        # 初始載入全景視野
        self.reset_view()

    def set_map_style(self, source=None, label: str = ""):
        """路線軌跡預覽底圖固定使用 Google 街道圖。"""
        self.map_source = GOOGLE_STREETS_URL
        self.map_style_label = "Google Maps 街道圖"

    def compute_auto_zoom_level(self) -> int:
        """根據當前 Canvas scale (pixels per meter) 自動計算最佳 Google Map 瓦片層級 (10~19)。"""
        if self.scale <= 1e-6:
            return 11
        try:
            z_float = math.log2(max(1.0, 156543.03392 * self.scale))
            z_int = int(round(z_float + 0.3))
            return max(8, min(19, z_int))
        except Exception:
            return 14

    def schedule_basemap_reload(self):
        """安排防抖延遲下載當前可視範圍之高解析底圖。"""
        self._reload_timer.start()

    def set_map_zoom(self, zoom: int | str):
        """切換指定瓦片縮放層級並重新下載底圖。"""
        self.map_zoom = zoom
        self.schedule_basemap_reload()

    def load_basemap(self, zoom: int | str | None = None):
        if zoom is not None:
            self.map_zoom = zoom
        self.schedule_basemap_reload()

    def _do_fetch_viewport_basemap(self):
        """非同步下載涵蓋目前視窗視野範圍 (Viewport) 之 Google 街道圖底圖，保證放大後清晰銳利。"""
        if self.width() <= 10 or self.height() <= 10 or self.scale <= 1e-6:
            return

        w_meters = self.width() / self.scale
        h_meters = self.height() / self.scale

        # 加入 35% 邊界緩衝區，避免微幅平移時立刻出現空白邊框
        pad_w = w_meters * 0.35
        pad_h = h_meters * 0.35

        west = self.view_center_x - (w_meters * 0.5 + pad_w)
        east = self.view_center_x + (w_meters * 0.5 + pad_w)
        south = self.view_center_y - (h_meters * 0.5 + pad_h)
        north = self.view_center_y + (h_meters * 0.5 + pad_h)

        if self.map_zoom == "auto":
            target_z = self.compute_auto_zoom_level()
        else:
            try:
                target_z = int(self.map_zoom)
            except Exception:
                target_z = self.compute_auto_zoom_level()

        self._current_rendered_zoom = target_z
        self.is_loading_map = True
        self.update()

        self.map_worker.fetch_async(west, south, east, north, self.map_source, zoom=target_z)

    def zoom_in(self):
        """畫面視角放大。"""
        self.zoom(1.25)

    def zoom_out(self):
        """畫面視角縮小。"""
        self.zoom(0.8)

    def _on_map_tile_ready(self, qimg: QImage, left: float, right: float, bottom: float, top: float):
        self.map_qimage = qimg
        self.map_extent = (left, right, bottom, top)
        self.is_loading_map = False
        self.update()

    def _on_map_fetch_failed(self, err: str):
        self.is_loading_map = False
        self.update()

    def reset_view(self):
        cw = max(self.width(), 200)
        ch = max(self.height(), 200)

        scale_x = (cw * 0.82) / self.route_w
        scale_y = (ch * 0.82) / self.route_h
        self.scale = min(scale_x, scale_y)

        self.view_center_x = float(self.ride_data.route_center_x)
        self.view_center_y = float(self.ride_data.route_center_y)
        self.update()
        self.schedule_basemap_reload()

    def _get_km_world_coord(self, km: float) -> tuple[float, float]:
        """利用線性插值極速獲取指定里程在 WebMercator 座標系中的 (wx, wy)。"""
        if km < 0 or len(self.ride_data.distances) == 0:
            return float(self.ride_data.route_center_x), float(self.ride_data.route_center_y)
        wx = float(np.interp(km, self.ride_data.distances, self.ride_data.xs))
        wy = float(np.interp(km, self.ride_data.distances, self.ride_data.ys))
        return wx, wy

    def zoom(self, factor: float, center_pt: Optional[QPointF] = None):
        self.scale = max(1e-4, min(100.0, self.scale * factor))
        self.update()
        self.schedule_basemap_reload()

    def focus_active(self):
        if self.active_km >= 0 and len(self.ride_data.distances) > 0:
            self.view_center_x, self.view_center_y = self._get_km_world_coord(self.active_km)
            self.update()
            self.schedule_basemap_reload()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.schedule_basemap_reload()

    def _world_to_canvas(self, wx: float, wy: float) -> tuple[float, float]:
        cx = self.width() * 0.5
        cy = self.height() * 0.5
        px = cx + (wx - self.view_center_x) * self.scale
        py = cy - (wy - self.view_center_y) * self.scale
        return px, py

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.fillRect(self.rect(), QColor("#121820"))

        if self.scale == 1.0 and self.width() > 10 and self.height() > 10:
            self.reset_view()

        # 1. 繪製 Google Map 底圖
        if self.map_qimage and self.map_extent:
            left, right, bottom, top = self.map_extent
            px_l, py_t = self._world_to_canvas(left, top)
            px_r, py_b = self._world_to_canvas(right, bottom)
            dest_rect = QRectF(px_l, py_t, px_r - px_l, py_b - py_t)
            painter.drawImage(dest_rect, self.map_qimage)

        # 2. 向量化繪製軌跡主線段 (C++ Qt Polyline 快速渲染)
        if len(self.sampled_xs) > 1:
            cx = self.width() * 0.5
            cy = self.height() * 0.5
            pxs = cx + (self.sampled_xs - self.view_center_x) * self.scale
            pys = cy - (self.sampled_ys - self.view_center_y) * self.scale
            poly = QPolygonF([QPointF(x, y) for x, y in zip(pxs, pys)])

            # 2.1 黑色外框光暈 (增強對比)
            pen_outline = QPen(QColor(0, 0, 0, 180), 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen_outline)
            painter.drawPolyline(poly)

            # 2.2 青色核心軌跡
            pen_route = QPen(QColor("#00e5ff"), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen_route)
            painter.drawPolyline(poly)

            # 起點 (綠色) 與 終點 (紅色)
            spx, spy = pxs[0], pys[0]
            epx, epy = pxs[-1], pys[-1]
            painter.setPen(QPen(QColor("#ffffff"), 1.8))
            painter.setBrush(QBrush(QColor("#4caf50")))
            painter.drawEllipse(QPointF(spx, spy), 7, 7)

            painter.setPen(QPen(QColor("#ffffff"), 1.8))
            painter.setBrush(QBrush(QColor("#f44336")))
            painter.drawEllipse(QPointF(epx, epy), 7, 7)

        # 3. 繪製所有媒體標記點 (使用 O(1) 座標快查，無繁複 numpy 搜尋)
        for i, item in enumerate(self.media_items):
            wx, wy = self._get_km_world_coord(item.current_km)
            px, py = self._world_to_canvas(wx, wy)

            is_sel = (i == self.selected_index)
            color = QColor("#ff9800") if not is_sel else QColor("#ff5722")
            radius = 6 if not is_sel else 9

            # 黑色外光暈底
            painter.setPen(QPen(QColor(0, 0, 0, 160), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(px, py), radius + 1, radius + 1)

            # 實心標記
            painter.setPen(QPen(QColor("#ffffff"), 1.8 if is_sel else 1.2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(px, py), radius, radius)

        # 4. 高亮選取中的標記資訊框
        if self.active_km >= 0 and len(self.ride_data.distances) > 0:
            wx, wy = self._get_km_world_coord(self.active_km)
            apx, apy = self._world_to_canvas(wx, wy)

            painter.setPen(QPen(QColor("#ffab40"), 2.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(apx, apy), 15, 15)

            # Bubble text
            txt = f"{self.active_km:.2f} km"
            bw = max(68, len(txt) * 9)
            bh = 20
            bx = apx - bw / 2
            by = apy - 34

            painter.setPen(QPen(QColor("#ff7043"), 1.2))
            painter.setBrush(QBrush(QColor(13, 17, 23, 235)))
            painter.drawRoundedRect(QRectF(bx, by, bw, bh), 5, 5)

            painter.setPen(QPen(QColor("#ffffff")))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, txt)

        # 5. 右上角底圖載入指示與左下角標籤
        label_text = self.map_style_label or "Google Maps 街道圖"
        if self.is_loading_map:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
            painter.drawRoundedRect(QRectF(self.width() - 200, 8, 192, 24), 4, 4)
            painter.setPen(QPen(QColor("#ffcc00")))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QRectF(self.width() - 200, 8, 192, 24), Qt.AlignCenter, f"📡 載入 {label_text}...")

        # 水印標籤
        painter.setPen(QPen(QColor(0, 0, 0, 160)))
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.drawText(QRectF(9, self.height() - 19, 220, 16), Qt.AlignLeft | Qt.AlignVCenter, label_text)
        painter.setPen(QPen(QColor(255, 255, 255, 200)))
        painter.drawText(QRectF(8, self.height() - 20, 220, 16), Qt.AlignLeft | Qt.AlignVCenter, label_text)

    # --- 滑鼠互動事件 ---
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 1.18 if delta > 0 else 1.0 / 1.18

        # 依滑鼠游標位置為中心平滑縮放 (如同 Google Maps)
        cursor_pos = event.position()
        cx = self.width() * 0.5
        cy = self.height() * 0.5

        old_wx = self.view_center_x + (cursor_pos.x() - cx) / self.scale
        old_wy = self.view_center_y - (cursor_pos.y() - cy) / self.scale

        self.scale = max(1e-4, min(100.0, self.scale * factor))

        self.view_center_x = old_wx - (cursor_pos.x() - cx) / self.scale
        self.view_center_y = old_wy + (cursor_pos.y() - cy) / self.scale

        self.update()
        self.schedule_basemap_reload()

    def mousePressEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self.drag_start_pos = event.position()
            self.is_dragging = True

            # 判斷點擊近距離媒體標記
            click_pt = event.position()
            for i, item in enumerate(self.media_items):
                wx, wy = self._get_km_world_coord(item.current_km)
                px, py = self._world_to_canvas(wx, wy)

                dist = math.hypot(click_pt.x() - px, click_pt.y() - py)
                if dist <= 15:
                    self.selected_index = i
                    self.active_km = item.current_km
                    self.item_selected.emit(i)
                    self.update()
                    break

    def mouseMoveEvent(self, event):
        if self.is_dragging and self.drag_start_pos:
            diff = event.position() - self.drag_start_pos
            self.drag_start_pos = event.position()

            self.view_center_x -= diff.x() / self.scale
            self.view_center_y += diff.y() / self.scale
            self.update()

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.drag_start_pos = None
            self.schedule_basemap_reload()
        else:
            self.is_dragging = False
            self.drag_start_pos = None


__all__ = [
    "QtRoutePreviewWidget",
]
