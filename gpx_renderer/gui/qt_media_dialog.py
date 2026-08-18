# -*- coding: utf-8 -*-
"""
PySide6 (Qt) 原生媒體管理與照片預覽/文字標籤對齊視窗 (QtMediaManagerDialog)。
包含動態路線向量預覽圖表 (QtRoutePreviewWidget)、相片/影片即時縮圖預覽卡片、EXIF 拍攝資訊面板與文字標籤編輯器。
"""

from __future__ import annotations
import os
import math
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image, ImageOps

from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QUrl, QSize
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap, QImage, QDesktopServices, QCursor
)
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QMessageBox, QSplitter, QFrame, QScrollArea,
    QSizePolicy, QCheckBox
)

from gpx_renderer.core.media import (
    MediaItem, match_media_to_ride, scan_media_files, load_media_thumbnail
)
from gpx_renderer.core.data import RideData


class QtRoutePreviewWidget(QWidget):
    """PySide6 向量路線預覽 Canvas，支援滑鼠滾輪縮放、平移與動態媒體標記點連動。"""
    item_selected = Signal(int)

    def __init__(self, ride_data: RideData, parent=None):
        super().__init__(parent)
        self.ride_data = ride_data
        self.media_items: List[MediaItem] = []
        self.selected_index: int = -1
        self.active_km: float = -1.0

        self.view_center_x = float(ride_data.route_center_x)
        self.view_center_y = float(ride_data.route_center_y)

        min_x, max_x = float(ride_data.xs.min()), float(ride_data.xs.max())
        min_y, max_y = float(ride_data.ys.min()), float(ride_data.ys.max())
        self.route_w = max(max_x - min_x, 100.0)
        self.route_h = max(max_y - min_y, 100.0)

        self.scale = 1.0  # pixels per meter
        self.drag_start_pos: Optional[QPointF] = None
        self.is_dragging = False

        # 抽樣軌跡點以提升畫圖效率
        step = max(1, len(ride_data.xs) // 600)
        self.sampled_xs = ride_data.xs[::step]
        self.sampled_ys = ride_data.ys[::step]

        self.setMouseTracking(True)
        self.setMinimumSize(320, 320)

    def reset_view(self):
        cw = max(self.width(), 200)
        ch = max(self.height(), 200)

        scale_x = (cw * 0.82) / self.route_w
        scale_y = (ch * 0.82) / self.route_h
        self.scale = min(scale_x, scale_y)

        self.view_center_x = float(self.ride_data.route_center_x)
        self.view_center_y = float(self.ride_data.route_center_y)
        self.update()

    def zoom(self, factor: float, center_pt: Optional[QPointF] = None):
        self.scale = max(1e-4, min(100.0, self.scale * factor))
        self.update()

    def focus_active(self):
        if self.active_km >= 0 and len(self.ride_data.distances) > 0:
            dists = np.abs(self.ride_data.distances - self.active_km)
            best_i = int(np.argmin(dists))
            self.view_center_x = float(self.ride_data.xs[best_i])
            self.view_center_y = float(self.ride_data.ys[best_i])
            self.update()

    def _world_to_canvas(self, wx: float, wy: float) -> tuple[float, float]:
        cx = self.width() * 0.5
        cy = self.height() * 0.5
        px = cx + (wx - self.view_center_x) * self.scale
        py = cy - (wy - self.view_center_y) * self.scale
        return px, py

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#121820"))

        if self.scale == 1.0 and self.width() > 10 and self.height() > 10:
            self.reset_view()

        # 1. 繪製軌跡主線段
        pen_route = QPen(QColor("#00bcd4"), 3)
        painter.setPen(pen_route)

        pts = []
        for x, y in zip(self.sampled_xs, self.sampled_ys):
            px, py = self._world_to_canvas(x, y)
            pts.append(QPointF(px, py))

        for i in range(len(pts) - 1):
            painter.drawLine(pts[i], pts[i + 1])

        # 起點 (綠色) 與 終點 (紅色)
        if pts:
            spx, spy = pts[0].x(), pts[0].y()
            epx, epy = pts[-1].x(), pts[-1].y()

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#4caf50")))
            painter.drawEllipse(QPointF(spx, spy), 6, 6)

            painter.setBrush(QBrush(QColor("#f44336")))
            painter.drawEllipse(QPointF(epx, epy), 6, 6)

        # 2. 繪製所有媒體標記點
        for i, item in enumerate(self.media_items):
            km = item.current_km
            dists = np.abs(self.ride_data.distances - km)
            idx = int(np.argmin(dists))
            wx, wy = float(self.ride_data.xs[idx]), float(self.ride_data.ys[idx])
            px, py = self._world_to_canvas(wx, wy)

            is_sel = (i == self.selected_index)
            color = QColor("#ff9800") if not is_sel else QColor("#ff5722")
            radius = 6 if not is_sel else 9

            painter.setPen(QPen(QColor("#ffffff"), 1.8 if is_sel else 1.2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(px, py), radius, radius)

        # 3. 高亮選取中的標記資訊框
        if self.active_km >= 0 and len(self.ride_data.distances) > 0:
            dists = np.abs(self.ride_data.distances - self.active_km)
            idx = int(np.argmin(dists))
            wx, wy = float(self.ride_data.xs[idx]), float(self.ride_data.ys[idx])
            apx, apy = self._world_to_canvas(wx, wy)

            painter.setPen(QPen(QColor("#ffab40"), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(apx, apy), 14, 14)

            # Bubble text
            txt = f"{self.active_km:.1f} km"
            bw = max(60, len(txt) * 9)
            bh = 20
            bx = apx - bw / 2
            by = apy - 34

            painter.setPen(QPen(QColor("#ff7043"), 1))
            painter.setBrush(QBrush(QColor("#0a0f14")))
            painter.drawRoundedRect(QRectF(bx, by, bw, bh), 4, 4)

            painter.setPen(QPen(QColor("#ffffff")))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, txt)

    # --- 滑鼠互動事件 ---
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 0.85
        self.zoom(factor)

    def mousePressEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self.drag_start_pos = event.position()
            self.is_dragging = True

            # 判斷點擊近距離媒體標記
            click_pt = event.position()
            for i, item in enumerate(self.media_items):
                km = item.current_km
                dists = np.abs(self.ride_data.distances - km)
                idx = int(np.argmin(dists))
                wx, wy = float(self.ride_data.xs[idx]), float(self.ride_data.ys[idx])
                px, py = self._world_to_canvas(wx, wy)

                dist = math.hypot(click_pt.x() - px, click_pt.y() - py)
                if dist <= 14:
                    self.selected_index = i
                    self.active_km = km
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
        self.is_dragging = False
        self.drag_start_pos = None


class ClickablePreviewLabel(QLabel):
    """支援點擊開啟原圖之預覽圖片標籤元件。"""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class QtMediaManagerDialog(QDialog):
    """PySide6 原生媒體管理與照片預覽/對齊對話框視窗。"""

    def __init__(
        self,
        media_items: List[MediaItem],
        ride_data: RideData,
        media_duration: float = 4.0,
        media_offset_sec: float = 0.0,
        media_path: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("路線媒體管理器與照片標籤編輯器 (PySide6 Native)")
        self.resize(1260, 720)
        self.setMinimumSize(1060, 620)

        self.media_items = media_items
        self.ride_data = ride_data
        self.media_path = media_path
        self.total_distance_km = max(0.1, float(ride_data.distances[-1])) if len(ride_data.distances) > 0 else 100.0
        self.selected_index = -1
        self.result_overrides: Dict[str, dict] = {}
        self._pixmap_cache: Dict[str, Optional[QPixmap]] = {}
        self._raw_img_dims: Dict[str, tuple[int, int]] = {}

        # 初次載入自動配對 GPS / 時間
        match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times, time_offset_sec=media_offset_sec)

        self._init_ui()
        self.spin_media_dur.setValue(media_duration)
        self.spin_media_offset.setValue(media_offset_sec)
        self._populate_tree()

        # 開局自動選取第 1 筆項目展示預覽
        if self.media_items:
            self.table.selectRow(0)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # 1. 頂部控制列
        top_group = QGroupBox(" 媒體播放與相機時間校正 ")
        top_layout = QVBoxLayout(top_group)
        top_layout.setSpacing(6)

        row1 = QHBoxLayout()
        lbl_title = QLabel("路線媒體管理器與照片標籤編輯器")
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        row1.addWidget(lbl_title)
        lbl_sub = QLabel("（相片已依拍攝時間/GPS自動配對，可在地圖上拖拉微調並自訂文字標籤）")
        lbl_sub.setStyleSheet("color: #718096;")
        row1.addWidget(lbl_sub)
        row1.addStretch()
        top_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("媒體停留秒數："))
        self.spin_media_dur = QDoubleSpinBox()
        self.spin_media_dur.setRange(1.0, 30.0)
        self.spin_media_dur.setSingleStep(0.5)
        self.spin_media_dur.setValue(4.0)
        self.spin_media_dur.setSuffix(" 秒")
        row2.addWidget(self.spin_media_dur)

        row2.addSpacing(20)
        row2.addWidget(QLabel("相機時間校正："))
        self.spin_media_offset = QDoubleSpinBox()
        self.spin_media_offset.setRange(-86400, 86400)
        self.spin_media_offset.setSingleStep(1.0)
        self.spin_media_offset.setValue(0.0)
        self.spin_media_offset.setSuffix(" 秒")
        row2.addWidget(self.spin_media_offset)

        btn_realign = QPushButton("⏱️ 重新對齊時間")
        btn_realign.setToolTip("依據上方校正秒數，重新與 GPX 時間軸匹配點位")
        btn_realign.clicked.connect(self._recalculate_time_offset)
        row2.addWidget(btn_realign)

        lbl_hint = QLabel("💡 相機時間慢 1 分鐘請填 60 秒；快 1 分鐘請填 -60 秒")
        lbl_hint.setStyleSheet("color: #718096; font-size: 11px;")
        row2.addWidget(lbl_hint)
        row2.addStretch()
        top_layout.addLayout(row2)

        main_layout.addWidget(top_group)

        # 2. 中間 Splitter (媒體清單 | 地圖預覽 | 右側照片預覽與編輯區)
        splitter = QSplitter(Qt.Horizontal)

        # 2.1 左側：Table Widget (媒體清單)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        self.lbl_table_header = QLabel("媒體清單 (共 0 項)")
        self.lbl_table_header.setFont(QFont("Segoe UI", 9, QFont.Bold))
        left_layout.addWidget(self.lbl_table_header)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["檔名", "類型", "拍攝時間", "匹配里程 (km)", "自訂說明"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_table_select)
        left_layout.addWidget(self.table)
        splitter.addWidget(left_panel)

        # 2.2 中央：路線與媒體標記預覽 Canvas
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(4)

        lbl_map_header = QLabel("路線軌跡與媒體分佈")
        lbl_map_header.setFont(QFont("Segoe UI", 9, QFont.Bold))
        center_layout.addWidget(lbl_map_header)

        self.preview_widget = QtRoutePreviewWidget(self.ride_data)
        self.preview_widget.media_items = self.media_items
        self.preview_widget.item_selected.connect(self._on_canvas_select_item)
        center_layout.addWidget(self.preview_widget)

        lbl_map_hint = QLabel("💡 滑鼠滾輪縮放 / 拖曳平移 / 點擊橘色標記選取照片")
        lbl_map_hint.setStyleSheet("color: #718096; font-size: 11px;")
        lbl_map_hint.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(lbl_map_hint)

        splitter.addWidget(center_panel)

        # 2.3 右側：照片縮圖預覽卡片、EXIF 拍攝資訊與屬性編輯區
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # 2.3.1 照片縮圖預覽卡片
        preview_group = QGroupBox(" 媒體照片預覽 ")
        preview_vbox = QVBoxLayout(preview_group)
        preview_vbox.setContentsMargins(8, 8, 8, 8)
        preview_vbox.setSpacing(6)

        # 照片縮圖容器 (支援點擊開啟原圖)
        self.lbl_preview_image = ClickablePreviewLabel()
        self.lbl_preview_image.setAlignment(Qt.AlignCenter)
        self.lbl_preview_image.setMinimumSize(260, 180)
        self.lbl_preview_image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.lbl_preview_image.setStyleSheet(
            "background-color: #1a202c; border: 1px solid #2d3748; border-radius: 8px; color: #a0aec0;"
        )
        self.lbl_preview_image.setText("📷 請從清單或地圖選取照片")
        self.lbl_preview_image.clicked.connect(self._open_full_media)
        preview_vbox.addWidget(self.lbl_preview_image)

        btn_open_row = QHBoxLayout()
        self.btn_view_full = QPushButton("🔍 檢視全螢幕原圖")
        self.btn_view_full.setToolTip("使用系統預設相片檢視器開啟原檔")
        self.btn_view_full.clicked.connect(self._open_full_media)
        btn_open_row.addWidget(self.btn_view_full)
        preview_vbox.addLayout(btn_open_row)

        right_layout.addWidget(preview_group)

        # 2.3.2 拍攝與 EXIF 詳細資訊卡片
        info_group = QGroupBox(" 拍攝與 EXIF 資訊 ")
        info_layout = QGridLayout(info_group)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setHorizontalSpacing(8)
        info_layout.setVerticalSpacing(4)

        info_layout.addWidget(QLabel("📁 檔案："), 0, 0)
        self.lbl_info_filename = QLabel("-")
        self.lbl_info_filename.setStyleSheet("font-weight: bold; color: #e2e8f0;")
        self.lbl_info_filename.setWordWrap(True)
        info_layout.addWidget(self.lbl_info_filename, 0, 1)

        info_layout.addWidget(QLabel("📅 時間："), 1, 0)
        self.lbl_info_time = QLabel("-")
        self.lbl_info_time.setStyleSheet("color: #cbd5e0;")
        info_layout.addWidget(self.lbl_info_time, 1, 1)

        info_layout.addWidget(QLabel("📍 GPS："), 2, 0)
        self.lbl_info_gps = QLabel("-")
        self.lbl_info_gps.setStyleSheet("color: #cbd5e0;")
        info_layout.addWidget(self.lbl_info_gps, 2, 1)

        info_layout.addWidget(QLabel("📐 尺寸："), 3, 0)
        self.lbl_info_res = QLabel("-")
        self.lbl_info_res.setStyleSheet("color: #cbd5e0;")
        info_layout.addWidget(self.lbl_info_res, 3, 1)

        info_layout.addWidget(QLabel("📏 匹配："), 4, 0)
        self.lbl_info_match = QLabel("-")
        self.lbl_info_match.setStyleSheet("color: #63b3ed; font-weight: bold;")
        info_layout.addWidget(self.lbl_info_match, 4, 1)

        right_layout.addWidget(info_group)

        # 2.3.3 屬性編輯卡片
        edit_group = QGroupBox(" 編輯選取相片屬性 ")
        edit_layout = QGridLayout(edit_group)
        edit_layout.setContentsMargins(8, 8, 8, 8)
        edit_layout.setSpacing(6)

        self.chk_manual_km = QCheckBox("啟用手動里程 (覆寫自動匹配)")
        self.chk_manual_km.toggled.connect(self._on_manual_km_toggled)
        edit_layout.addWidget(self.chk_manual_km, 0, 0, 1, 2)

        edit_layout.addWidget(QLabel("手動里程 (km)："), 1, 0)
        self.spin_manual_km = QDoubleSpinBox()
        self.spin_manual_km.setRange(0.0, self.total_distance_km)
        self.spin_manual_km.setSingleStep(0.1)
        self.spin_manual_km.setSuffix(f" / {self.total_distance_km:.1f} km")
        self.spin_manual_km.setEnabled(False)
        self.spin_manual_km.valueChanged.connect(self._on_manual_km_value_change)
        edit_layout.addWidget(self.spin_manual_km, 1, 1)

        edit_layout.addWidget(QLabel("自訂說明文字："), 2, 0)
        self.line_caption = QLineEdit()
        self.line_caption.setPlaceholderText("例如：合歡山主峰登山口 3158m")
        edit_layout.addWidget(self.line_caption, 2, 1)

        btn_apply_item = QPushButton("套用此項修改")
        btn_apply_item.setStyleSheet("font-weight: bold; padding: 4px;")
        btn_apply_item.clicked.connect(self._apply_current_edit)
        edit_layout.addWidget(btn_apply_item, 3, 0, 1, 2)

        right_layout.addWidget(edit_group)
        right_layout.addStretch()
        splitter.addWidget(right_panel)

        splitter.setSizes([360, 480, 360])
        main_layout.addWidget(splitter)

        # 3. 底部動作按鈕
        bottom_bar = QHBoxLayout()
        btn_reset_all = QPushButton("🔄 重置所有手動變更")
        btn_reset_all.clicked.connect(self._reset_all)
        bottom_bar.addWidget(btn_reset_all)

        bottom_bar.addStretch()

        btn_save = QPushButton("💾 儲存並套用")
        btn_save.setFont(QFont("Segoe UI", 10, QFont.Bold))
        btn_save.setStyleSheet("background-color: #2b6cb0; color: white; padding: 6px 16px; border-radius: 4px;")
        btn_save.clicked.connect(self._on_save_and_apply)
        bottom_bar.addWidget(btn_save)

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        bottom_bar.addWidget(btn_cancel)

        main_layout.addLayout(bottom_bar)

    def _populate_tree(self):
        self.lbl_table_header.setText(f"媒體清單 (共 {len(self.media_items)} 項)")
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for i, item in enumerate(self.media_items):
            self.table.insertRow(i)

            ts_str = item.timestamp.strftime("%Y-%m-%d %H:%M:%S") if item.timestamp else "--"
            km = item.current_km
            km_label = f"{km:.2f} (手動)" if (item.manual_distance_km is not None and item.manual_distance_km >= 0) else f"{km:.2f}"
            type_label = "🎬 影片" if item.media_type == "video" else "📷 相片"

            item_fn = QTableWidgetItem(item.filename)
            item_fn.setToolTip(item.file_path)
            self.table.setItem(i, 0, item_fn)

            item_type = QTableWidgetItem(type_label)
            item_type.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, item_type)

            item_ts = QTableWidgetItem(ts_str)
            item_ts.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, item_ts)

            item_km = QTableWidgetItem(km_label)
            item_km.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 3, item_km)

            item_cap = QTableWidgetItem(item.caption or "")
            self.table.setItem(i, 4, item_cap)

        self.table.blockSignals(False)
        self.preview_widget.update()

    def _load_item_pixmap(self, item: MediaItem) -> Optional[QPixmap]:
        """從快取或檔案讀取經 EXIF 旋轉校正之 QPixmap。"""
        if item.file_path in self._pixmap_cache:
            return self._pixmap_cache[item.file_path]

        pil_img = load_media_thumbnail(item.file_path, max_w=720, max_h=540)
        if pil_img is not None:
            try:
                rgb_img = pil_img.convert("RGB")
                data = rgb_img.tobytes("raw", "RGB")
                qimg = QImage(data, rgb_img.width, rgb_img.height, rgb_img.width * 3, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                self._pixmap_cache[item.file_path] = pixmap
                self._raw_img_dims[item.file_path] = (pil_img.width, pil_img.height)
                return pixmap
            except Exception:
                pass

        self._pixmap_cache[item.file_path] = None
        return None

    def _update_photo_preview(self, item: MediaItem):
        """更新右側預覽圖片與 EXIF 拍攝詳細資訊。"""
        # 1. 讀取並渲染縮圖
        pixmap = self._load_item_pixmap(item)
        if pixmap and not pixmap.isNull():
            lbl_w = max(240, self.lbl_preview_image.width() - 10)
            lbl_h = max(180, self.lbl_preview_image.height() - 10)
            scaled_pix = pixmap.scaled(
                lbl_w, lbl_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.lbl_preview_image.setPixmap(scaled_pix)
            self.btn_view_full.setEnabled(True)
        else:
            if item.media_type == "video":
                self.lbl_preview_image.setText("🎬 影片檔案\n(點擊下方按鈕檢視影片)")
            else:
                self.lbl_preview_image.setText("📷 無法載入照片縮圖")
            self.btn_view_full.setEnabled(Path(item.file_path).is_file())

        # 2. 更新 EXIF 與拍攝資訊面板
        self.lbl_info_filename.setText(item.filename)
        self.lbl_info_filename.setToolTip(item.file_path)

        if item.timestamp:
            self.lbl_info_time.setText(item.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.lbl_info_time.setText("無拍攝時間 (依里程對齊)")

        if item.lat is not None and item.lon is not None:
            self.lbl_info_gps.setText(f"{item.lat:.5f}°, {item.lon:.5f}°")
        else:
            self.lbl_info_gps.setText("無 GPS 座標標記")

        dims = self._raw_img_dims.get(item.file_path)
        try:
            sz_mb = Path(item.file_path).stat().st_size / (1024 * 1024)
            size_str = f"{sz_mb:.2f} MB"
        except Exception:
            size_str = ""

        if dims:
            self.lbl_info_res.setText(f"{dims[0]} × {dims[1]} px ({size_str})")
        else:
            self.lbl_info_res.setText(f"{item.media_type.upper()} ({size_str})" if size_str else item.media_type.upper())

        is_manual = (item.manual_distance_km is not None and item.manual_distance_km >= 0)
        km = item.current_km
        if is_manual:
            self.lbl_info_match.setText(f"📍 {km:.2f} km (手動指定)")
            self.lbl_info_match.setStyleSheet("color: #ecc94b; font-weight: bold;")
        else:
            self.lbl_info_match.setText(f"📍 {km:.2f} km (自動匹配)")
            self.lbl_info_match.setStyleSheet("color: #63b3ed; font-weight: bold;")

        # 3. 更新屬性編輯區
        self.chk_manual_km.blockSignals(True)
        self.spin_manual_km.blockSignals(True)
        self.line_caption.blockSignals(True)

        self.chk_manual_km.setChecked(is_manual)
        self.spin_manual_km.setEnabled(is_manual)
        self.spin_manual_km.setValue(km)
        self.line_caption.setText(item.caption or "")

        self.chk_manual_km.blockSignals(False)
        self.spin_manual_km.blockSignals(False)
        self.line_caption.blockSignals(False)

    def _on_table_select(self):
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if 0 <= row < len(self.media_items):
            self.selected_index = row
            item = self.media_items[row]
            km = item.current_km

            self._update_photo_preview(item)

            self.preview_widget.selected_index = row
            self.preview_widget.active_km = km
            self.preview_widget.focus_active()

    def _on_canvas_select_item(self, idx: int):
        if 0 <= idx < self.table.rowCount():
            self.table.selectRow(idx)

    def _on_manual_km_toggled(self, checked: bool):
        self.spin_manual_km.setEnabled(checked)
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            if checked:
                item.manual_distance_km = round(self.spin_manual_km.value(), 2)
            else:
                item.manual_distance_km = None
            self._apply_current_edit()

    def _on_manual_km_value_change(self, val: float):
        if self.chk_manual_km.isChecked() and 0 <= self.selected_index < len(self.media_items):
            self.preview_widget.active_km = float(val)
            self.preview_widget.update()

    def _open_full_media(self):
        """以作業系統預設照片檢視器開啟原檔。"""
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            p = Path(item.file_path).resolve()
            if p.is_file():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))

    def _recalculate_time_offset(self):
        offset_sec = self.spin_media_offset.value()
        match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times, time_offset_sec=offset_sec)
        self._populate_tree()
        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])
        QMessageBox.information(self, "完成", f"已重新根據校正時間 {offset_sec}s 配對媒體位置！")

    def _apply_current_edit(self):
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            if self.chk_manual_km.isChecked():
                item.manual_distance_km = round(self.spin_manual_km.value(), 2)
            else:
                item.manual_distance_km = None

            item.caption = self.line_caption.text().strip()

            cur_row = self.selected_index
            self._populate_tree()
            self.table.selectRow(cur_row)

    def _reset_all(self):
        if QMessageBox.question(self, "確認重置", "確定要重置所有相片的手動里程與說明文字嗎？") == QMessageBox.Yes:
            for item in self.media_items:
                item.manual_distance_km = None
                item.caption = ""
            self._populate_tree()
            if self.media_items:
                self.table.selectRow(0)

    def _on_save_and_apply(self):
        self._apply_current_edit()
        overrides = {}
        for item in self.media_items:
            if item.caption or (item.manual_distance_km is not None and item.manual_distance_km >= 0):
                overrides[item.filename] = {
                    "caption": item.caption,
                    "manual_distance_km": item.manual_distance_km,
                }
        self.result_overrides = overrides
        self.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if 0 <= self.selected_index < len(self.media_items):
            # 重新縮放預覽縮圖以適應新視窗大小
            item = self.media_items[self.selected_index]
            pixmap = self._pixmap_cache.get(item.file_path)
            if pixmap and not pixmap.isNull():
                lbl_w = max(240, self.lbl_preview_image.width() - 10)
                lbl_h = max(180, self.lbl_preview_image.height() - 10)
                scaled_pix = pixmap.scaled(
                    lbl_w, lbl_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.lbl_preview_image.setPixmap(scaled_pix)
