# -*- coding: utf-8 -*-
"""
PySide6 (Qt) 原生媒體管理與文字標籤手動對齊視窗 (QtMediaManagerDialog)。
包含動態路線向量預覽圖表 (QtRoutePreviewWidget)、媒體對齊清單與文字標籤編輯器。
"""

from __future__ import annotations
import math
from typing import List, Optional, Callable
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QMessageBox, QSplitter
)

from gpx_renderer.core.media import MediaItem, match_media_to_ride, scan_media_files
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
        self.setMinimumSize(300, 300)

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
        self.scale *= factor
        self.update()

    def focus_active(self):
        if self.active_km >= 0:
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
            km = item.manual_distance_km if (item.manual_distance_km is not None and item.manual_distance_km >= 0) else getattr(item, "matched_km", 0.0)
            dists = np.abs(self.ride_data.distances - km)
            idx = int(np.argmin(dists))
            wx, wy = float(self.ride_data.xs[idx]), float(self.ride_data.ys[idx])
            px, py = self._world_to_canvas(wx, wy)

            is_sel = (i == self.selected_index)
            color = QColor("#ff9800") if not is_sel else QColor("#ff5722")
            radius = 6 if not is_sel else 9

            painter.setPen(QPen(QColor("#ffffff"), 1.5))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(px, py), radius, radius)

        # 3. 高亮選取中的標記資訊框
        if self.active_km >= 0:
            dists = np.abs(self.ride_data.distances - self.active_km)
            idx = int(np.argmin(dists))
            wx, wy = float(self.ride_data.xs[idx]), float(self.ride_data.ys[idx])
            apx, apy = self._world_to_canvas(wx, wy)

            painter.setPen(QPen(QColor("#ffab40"), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(apx, apy), 13, 13)

            # Bubble text
            txt = f"{self.active_km:.1f} km"
            painter.setPen(QPen(QColor("#ff7043"), 1))
            painter.setBrush(QBrush(QColor("#0a0f14")))
            painter.drawRect(QRectF(apx - 28, apy - 30, 56, 18))

            painter.setPen(QPen(QColor("#ffffff")))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.drawText(QRectF(apx - 28, apy - 30, 56, 18), Qt.AlignCenter, txt)

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
                km = item.manual_distance_km if (item.manual_distance_km is not None and item.manual_distance_km >= 0) else getattr(item, "matched_km", 0.0)
                dists = np.abs(self.ride_data.distances - km)
                idx = int(np.argmin(dists))
                wx, wy = float(self.ride_data.xs[idx]), float(self.ride_data.ys[idx])
                px, py = self._world_to_canvas(wx, wy)

                dist = math.hypot(click_pt.x() - px, click_pt.y() - py)
                if dist <= 12:
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


class QtMediaManagerDialog(QDialog):
    """PySide6 原生媒體管理與對齊對話框視窗。"""

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
        self.setWindowTitle("路線媒體對齊與文字標籤編輯器 (PySide6 Native)")
        self.resize(1200, 700)
        self.setMinimumSize(1000, 600)

        self.media_items = media_items
        self.ride_data = ride_data
        self.media_path = media_path
        self.total_distance_km = max(0.1, float(ride_data.distances[-1]))
        self.selected_index = -1
        self.result_overrides = {}

        # 初次載入自動配對 GPS / 時間
        match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times)

        self._init_ui()
        self._populate_tree()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. 頂部控制列
        top_group = QGroupBox(" 媒體播放與相機時間校正 ")
        top_layout = QVBoxLayout(top_group)

        row1 = QHBoxLayout()
        lbl_title = QLabel("路線媒體對齊與文字標籤編輯器")
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        row1.addWidget(lbl_title)
        lbl_sub = QLabel("（相片已自動依拍攝時間/GPS進行預設配對，可在地圖上拖拉微調並自訂下方文字標籤）")
        lbl_sub.setStyleSheet("color: #666666;")
        row1.addWidget(lbl_sub)
        row1.addStretch()
        top_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("媒體停留秒數："))
        self.spin_media_dur = QDoubleSpinBox()
        self.spin_media_dur.setRange(1.0, 30.0)
        self.spin_media_dur.setSingleStep(0.5)
        self.spin_media_dur.setValue(4.0)
        row2.addWidget(self.spin_media_dur)

        row2.addSpacing(20)
        row2.addWidget(QLabel("相機時間校正 (秒)："))
        self.spin_media_offset = QDoubleSpinBox()
        self.spin_media_offset.setRange(-86400, 86400)
        self.spin_media_offset.setValue(0.0)
        row2.addWidget(self.spin_media_offset)

        btn_realign = QPushButton("⏱️ 重新對齊時間")
        btn_realign.clicked.connect(self._recalculate_time_offset)
        row2.addWidget(btn_realign)

        lbl_hint = QLabel("💡 相機時間慢1分鐘請填 60 秒；快1分鐘請填 -60 秒")
        lbl_hint.setStyleSheet("color: #666666;")
        row2.addWidget(lbl_hint)
        row2.addStretch()
        top_layout.addLayout(row2)

        main_layout.addWidget(top_group)

        # 2. 中間 Splitter (媒體清單 | 地圖預覽 | 右側屬性)
        splitter = QSplitter(Qt.Horizontal)

        # 2.1 左側：Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["檔名", "類型", "拍攝時間", "匹配里程 (km)", "自訂說明"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_table_select)
        splitter.addWidget(self.table)

        # 2.2 中央：路線與媒體預覽 Canvas
        self.preview_widget = QtRoutePreviewWidget(self.ride_data)
        self.preview_widget.media_items = self.media_items
        self.preview_widget.item_selected.connect(self._on_canvas_select_item)
        splitter.addWidget(self.preview_widget)

        # 2.3 右側：詳細編輯區
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        right_group = QGroupBox("編輯選取項目屬性")
        form_layout = QGridLayout(right_group)

        self.lbl_selected_file = QLabel("尚未選取媒體項目")
        self.lbl_selected_file.setFont(QFont("Segoe UI", 9, QFont.Bold))
        form_layout.addWidget(self.lbl_selected_file, 0, 0, 1, 2)

        form_layout.addWidget(QLabel("手動里程 (km)："), 1, 0)
        self.spin_manual_km = QDoubleSpinBox()
        self.spin_manual_km.setRange(0.0, self.total_distance_km)
        self.spin_manual_km.setSingleStep(0.1)
        form_layout.addWidget(self.spin_manual_km, 1, 1)

        form_layout.addWidget(QLabel("自訂說明文字："), 2, 0)
        self.line_caption = QLineEdit()
        form_layout.addWidget(self.line_caption, 2, 1)

        btn_apply_item = QPushButton("套用單項修改")
        btn_apply_item.clicked.connect(self._apply_current_edit)
        form_layout.addWidget(btn_apply_item, 3, 0, 1, 2)

        right_layout.addWidget(right_group)
        right_layout.addStretch()
        splitter.addWidget(right_panel)

        splitter.setSizes([350, 550, 300])
        main_layout.addWidget(splitter)

        # 3. 底部動作按鈕
        bottom_bar = QHBoxLayout()
        btn_reset_all = QPushButton("🔄 重置所有手動變更")
        btn_reset_all.clicked.connect(self._reset_all)
        bottom_bar.addWidget(btn_reset_all)

        bottom_bar.addStretch()

        btn_save = QPushButton("💾 儲存並套用")
        btn_save.setFont(QFont("Segoe UI", 10, QFont.Bold))
        btn_save.clicked.connect(self._on_save_and_apply)
        bottom_bar.addWidget(btn_save)

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        bottom_bar.addWidget(btn_cancel)

        main_layout.addLayout(bottom_bar)

    def _populate_tree(self):
        self.table.setRowCount(0)
        for i, item in enumerate(self.media_items):
            self.table.insertRow(i)

            ts_str = item.timestamp.strftime("%H:%M:%S") if item.timestamp else "--:--:--"
            km = item.manual_distance_km if (item.manual_distance_km is not None and item.manual_distance_km >= 0) else getattr(item, "matched_km", 0.0)

            self.table.setItem(i, 0, QTableWidgetItem(item.filename))
            self.table.setItem(i, 1, QTableWidgetItem(item.media_type))
            self.table.setItem(i, 2, QTableWidgetItem(ts_str))
            self.table.setItem(i, 3, QTableWidgetItem(f"{km:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(item.caption or ""))

        self.preview_widget.update()

    def _on_table_select(self):
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if 0 <= row < len(self.media_items):
            self.selected_index = row
            item = self.media_items[row]

            self.lbl_selected_file.setText(f"選取：{item.filename}")
            km = item.manual_distance_km if (item.manual_distance_km is not None and item.manual_distance_km >= 0) else getattr(item, "matched_km", 0.0)
            self.spin_manual_km.setValue(km)
            self.line_caption.setText(item.caption or "")

            self.preview_widget.selected_index = row
            self.preview_widget.active_km = km
            self.preview_widget.focus_active()

    def _on_canvas_select_item(self, idx: int):
        if 0 <= idx < self.table.rowCount():
            self.table.selectRow(idx)

    def _recalculate_time_offset(self):
        offset_sec = self.spin_media_offset.value()
        match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times, time_offset_sec=offset_sec)
        self._populate_tree()
        QMessageBox.information(self, "完成", f"已重新根據校正時間 {offset_sec}s 配對媒體位置！")

    def _apply_current_edit(self):
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            item.manual_distance_km = round(self.spin_manual_km.value(), 2)
            item.caption = self.line_caption.text().strip()
            self._populate_tree()

    def _reset_all(self):
        if QMessageBox.question(self, "確認重置", "確定要重置所有相片的手動里程與說明文字嗎？") == QMessageBox.Yes:
            for item in self.media_items:
                item.manual_distance_km = None
                item.caption = ""
            self._populate_tree()

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
