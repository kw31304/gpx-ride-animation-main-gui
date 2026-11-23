# -*- coding: utf-8 -*-
"""
路線媒體管理器分頁控制器 (MediaTabController)
負責將「路線媒體」分頁之表格編輯、軌跡連動、HUD 即時預覽、影片裁剪與媒體檔案掃描直接整合至主介面。
"""

from __future__ import annotations
import math
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, TYPE_CHECKING
import numpy as np

# 確保直接執行或由子模組載入時，專案根目錄均在 sys.path 中
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from PySide6.QtCore import Qt, QUrl, QPointF, QRectF
from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QFont, QPen, QBrush,
    QPainterPath, QPolygonF, QDesktopServices, QCursor
)
from PySide6.QtWidgets import (
    QWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QHBoxLayout, QPushButton, QCheckBox, QDialog
)

from gpx_renderer import config
from gpx_renderer.core.data import RideData, latlon_to_mercator
from gpx_renderer.core.media import (
    MediaItem, match_media_to_ride, scan_media_files, load_media_thumbnail
)
from gpx_renderer.gui.media_dialog.map_worker import MediaBgTileWorker, GOOGLE_STREETS_URL
from gpx_renderer.gui.video_trim_dialog import QtVideoTrimDialog

if TYPE_CHECKING:
    from gpx_renderer.gui.main_window.main_controller import MainWindow

logger = logging.getLogger(__name__)


class MediaTabController:
    """
    主介面第二分頁（路線媒體）專屬控制器。
    """
    def __init__(self, main_window: MainWindow):
        self.win = main_window
        self.media_items: List[MediaItem] = []
        self.ride_data: Optional[RideData] = None
        self.total_distance_km: float = 0.0

        self.selected_index: int = -1
        self.deleted_filenames: Set[str] = set()
        self._suppress_delete_confirm: bool = False

        # 縮圖與底圖快取
        self._pixmap_cache: Dict[str, Optional[QPixmap]] = {}
        self._raw_img_dims: Dict[str, Tuple[int, int]] = {}
        self._media_bg_cache: Dict[str, QPixmap] = {}
        self._pending_bg_fetches: Set[str] = set()

        # 底圖下載工作元件
        self.bg_worker = MediaBgTileWorker(self.win)
        self.bg_worker.tile_ready.connect(self._on_bg_tile_ready)
        self.bg_worker.fetch_failed.connect(self._on_bg_tile_failed)

        # 預設參數
        self.default_duration = float(getattr(config, "MEDIA_POPUP_DURATION", 3.0))
        self.default_caption_size = int(getattr(config, "MEDIA_CAPTION_FONT_SIZE", 60))

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        # 1. 旋轉鈕與控制項預設值
        if hasattr(self.win, "spin_photo_dur"):
            self.win.spin_photo_dur.setValue(self.default_duration)
        if hasattr(self.win, "spin_default_caption_size"):
            self.win.spin_default_caption_size.setValue(self.default_caption_size)

        # 2. 表格標頭設定
        if hasattr(self.win, "table"):
            header = self.win.table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)           # 檔名
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 類型
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 停留秒數
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 拍攝時間
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 匹配里程
            header.setSectionResizeMode(5, QHeaderView.Stretch)           # 自訂說明
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 字級
            header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # 操作
            header.setMinimumSectionSize(45)

            fm = self.win.table.fontMetrics()
            min_caption_w = max(110, fm.horizontalAdvance("自訂說明文字") + 20)
            self.win.table.setColumnWidth(5, min_caption_w)
            self.win.table.verticalHeader().setDefaultSectionSize(28)
            self.win.table.verticalHeader().setVisible(False)

        # Alias for backward compatibility
        if hasattr(self.win, "combo_preview_resolution") and not hasattr(self.win, "combo_preview_res"):
            self.win.combo_preview_res = self.win.combo_preview_resolution

        self._is_syncing_controls = False

        # 3. 預覽控制項下拉選單初始化 (地圖風格、視角模式、解析度)
        self._populate_preview_controls()

        # 4. 初始化路線向量畫布
        if hasattr(self.win, "preview_widget"):
            self.win.preview_widget.item_selected.connect(self._on_canvas_select_item)

        # 5. 連動 HUD 勾選變更
        if hasattr(self.win, "combo_hud_panels"):
            self.win.combo_hud_panels.selection_changed.connect(lambda _: self._on_hud_chk_toggled())

        # 6. 未載入 GPX 時隱藏地圖互動提示文字並禁用縮放按鈕
        has_ride = bool(self.ride_data and getattr(self.ride_data, "distances", None) is not None and len(self.ride_data.distances) > 0)
        if hasattr(self.win, "lbl_map_hint"):
            self.win.lbl_map_hint.setVisible(has_ride)
        if hasattr(self.win, "btn_zoom_in"):
            self.win.btn_zoom_in.setEnabled(has_ride)
        if hasattr(self.win, "btn_zoom_out"):
            self.win.btn_zoom_out.setEnabled(has_ride)
        if hasattr(self.win, "btn_reset_view"):
            self.win.btn_reset_view.setEnabled(has_ride)

    def _connect_signals(self):
        if hasattr(self.win, "btn_add_files"):
            self.win.btn_add_files.clicked.connect(self._on_add_files)
        if hasattr(self.win, "btn_add_folder"):
            self.win.btn_add_folder.clicked.connect(self._on_add_folder)

        if hasattr(self.win, "spin_photo_dur"):
            self.win.spin_photo_dur.valueChanged.connect(self._on_photo_default_changed)
        if hasattr(self.win, "spin_default_caption_size"):
            self.win.spin_default_caption_size.valueChanged.connect(self._on_default_caption_size_changed)
        if hasattr(self.win, "btn_reset_defaults"):
            self.win.btn_reset_defaults.clicked.connect(self._reset_all_durations_to_defaults)

        if hasattr(self.win, "table"):
            self.win.table.itemSelectionChanged.connect(self._on_table_select)
            self.win.table.itemChanged.connect(self._on_table_item_changed)
            self.win.table.cellDoubleClicked.connect(self._on_table_double_clicked)

        if hasattr(self.win, "lbl_preview_image"):
            self.win.lbl_preview_image.clicked.connect(self._open_full_media)

        if hasattr(self.win, "btn_zoom_in") and hasattr(self.win, "preview_widget"):
            self.win.btn_zoom_in.clicked.connect(lambda: self.win.preview_widget.zoom_in())
        if hasattr(self.win, "btn_zoom_out") and hasattr(self.win, "preview_widget"):
            self.win.btn_zoom_out.clicked.connect(lambda: self.win.preview_widget.zoom_out())
        if hasattr(self.win, "btn_reset_view") and hasattr(self.win, "preview_widget"):
            self.win.btn_reset_view.clicked.connect(lambda: self.win.preview_widget.reset_view())

        if hasattr(self.win, "combo_preview_map_style"):
            self.win.combo_preview_map_style.currentIndexChanged.connect(self._on_preview_map_style_changed)
        if hasattr(self.win, "combo_preview_camera_mode"):
            self.win.combo_preview_camera_mode.currentIndexChanged.connect(self._on_preview_camera_mode_changed)
        if hasattr(self.win, "combo_preview_resolution"):
            self.win.combo_preview_resolution.currentIndexChanged.connect(self._on_preview_res_changed)
        elif hasattr(self.win, "combo_preview_res"):
            self.win.combo_preview_res.currentIndexChanged.connect(self._on_preview_res_changed)

    # ---------- 資料對接與更新 ----------
    def set_ride_data(self, ride_data: RideData):
        """主視窗載入 GPX 後更新 RideData。"""
        self.ride_data = ride_data
        if ride_data and len(ride_data.distances) > 0:
            self.total_distance_km = float(ride_data.distances[-1])
        else:
            self.total_distance_km = 0.0

        has_ride = bool(self.ride_data and getattr(self.ride_data, "distances", None) is not None and len(self.ride_data.distances) > 0)
        if hasattr(self.win, "lbl_map_hint"):
            self.win.lbl_map_hint.setVisible(has_ride)
        if hasattr(self.win, "btn_zoom_in"):
            self.win.btn_zoom_in.setEnabled(has_ride)
        if hasattr(self.win, "btn_zoom_out"):
            self.win.btn_zoom_out.setEnabled(has_ride)
        if hasattr(self.win, "btn_reset_view"):
            self.win.btn_reset_view.setEnabled(has_ride)

        if hasattr(self.win, "preview_widget"):
            map_key = self.win.combo_map_style_2.currentText().split(".")[0].strip() if hasattr(self.win, "combo_map_style_2") else "1"
            map_label, map_source = config.MAP_STYLE_OPTIONS.get(map_key, ("Google Maps 街道圖", GOOGLE_STREETS_URL))
            self.win.preview_widget.set_ride_data(self.ride_data)
            self.win.preview_widget.set_map_style(map_source, map_label)
            self.win.preview_widget.media_items = self.media_items

        if self.media_items and self.ride_data:
            match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times)
            self._populate_tree()
            self._sync_overrides_to_config()

    def load_media_from_paths(self, paths: List[str] | str):
        """自路徑列表或資料夾載入媒體檔案。"""
        if isinstance(paths, str):
            if ";" in paths:
                raw_paths = [p.strip() for p in paths.split(";") if p.strip()]
            else:
                raw_paths = [paths.strip()] if paths.strip() else []
        else:
            raw_paths = list(paths)

        if not raw_paths:
            self.media_items.clear()
            self._populate_tree()
            return

        new_items = scan_media_files(raw_paths, time_offset_sec=0.0)
        self.media_items = new_items

        if self.ride_data:
            match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times)

        if hasattr(self.win, "preview_widget"):
            self.win.preview_widget.media_items = self.media_items
            self.win.preview_widget.update()

        self._populate_tree()
        if self.media_items and hasattr(self.win, "table"):
            self.win.table.selectRow(0)

        self._sync_overrides_to_config()

    def _sync_overrides_to_config(self):
        """將當前媒體之所有自訂覆寫資訊同步儲存至 MainWindow state 與 config。"""
        import json
        overrides = {}
        for fn in self.deleted_filenames:
            overrides[fn] = {"excluded": True, "deleted": True}

        for item in self.media_items:
            ovr = {}
            if item.caption:
                ovr["caption"] = item.caption
            if getattr(item, "caption_size", None) is not None and item.caption_size > 0:
                ovr["caption_size"] = int(item.caption_size)
            if item.manual_distance_km is not None and item.manual_distance_km >= 0:
                ovr["manual_distance_km"] = item.manual_distance_km
            if item.popup_duration is not None and item.popup_duration > 0:
                ovr["popup_duration"] = float(round(item.popup_duration, 2))
            if getattr(item, "clip_start_sec", 0.0) > 0.0:
                ovr["clip_start_sec"] = float(round(item.clip_start_sec, 2))
            if ovr:
                overrides[item.filename] = ovr

        self.win.state["media_overrides_json"] = json.dumps(overrides, ensure_ascii=False)
        config.MEDIA_OVERRIDES_JSON = self.win.state["media_overrides_json"]
        self.win._update_dashboard_summary()

    # ---------- 表格與項目呈現 ----------
    def _update_stats_summary(self):
        total_items = len(self.media_items)
        num_photos = sum(1 for it in self.media_items if it.media_type == "image")
        num_videos = sum(1 for it in self.media_items if it.media_type == "video")
        total_photo_sec = sum(it.effective_duration for it in self.media_items if it.media_type == "image")
        total_video_sec = sum(it.effective_duration for it in self.media_items if it.media_type == "video")
        total_media_sec = total_photo_sec + total_video_sec

        sec_str = f"{total_media_sec:.0f}" if total_media_sec.is_integer() else f"{total_media_sec:.1f}"
        title_text = f"媒體清單 (共 {total_items} 項) +{sec_str} 秒"

        if hasattr(self.win, "group_media_list"):
            self.win.group_media_list.setTitle(title_text)

    def _populate_tree(self):
        if not hasattr(self.win, "table"):
            return
        self._update_stats_summary()

        self.win.table.blockSignals(True)
        self.win.table.setUpdatesEnabled(False)
        try:
            self.win.table.setRowCount(0)
            for i, item in enumerate(self.media_items):
                self.win.table.insertRow(i)
                ts_str = item.timestamp.strftime("%Y-%m-%d %H:%M:%S") if item.timestamp else "--"
                km = item.current_km
                km_label = f"{km:.2f} (手動)" if (item.manual_distance_km is not None and item.manual_distance_km >= 0) else f"{km:.2f}"
                type_label = "🎬 影片" if item.media_type == "video" else "📷 相片"
                dur_str = f"{item.effective_duration:.1f}s"
                cap_size_label = f"{item.caption_size} pt (自訂)" if (item.caption_size is not None and item.caption_size > 0) else f"{self.default_caption_size} pt"

                # 0. 檔名
                it_fn = QTableWidgetItem(item.filename)
                it_fn.setToolTip(item.file_path)
                it_fn.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.win.table.setItem(i, 0, it_fn)

                # 1. 類型
                it_type = QTableWidgetItem(type_label)
                it_type.setTextAlignment(Qt.AlignCenter)
                it_type.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.win.table.setItem(i, 1, it_type)

                # 2. 停留秒數
                it_dur = QTableWidgetItem(dur_str)
                it_dur.setTextAlignment(Qt.AlignCenter)
                it_dur.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                it_dur.setToolTip("雙擊可輸入自訂停留秒數")
                self.win.table.setItem(i, 2, it_dur)

                # 3. 拍攝時間
                it_ts = QTableWidgetItem(ts_str)
                it_ts.setTextAlignment(Qt.AlignCenter)
                it_ts.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.win.table.setItem(i, 3, it_ts)

                # 4. 匹配里程 (km)
                it_km = QTableWidgetItem(km_label)
                it_km.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                it_km.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                it_km.setToolTip("雙擊可輸入自訂里程 (km)；清空或輸入 -- 恢復自動")
                self.win.table.setItem(i, 4, it_km)

                # 5. 自訂說明
                it_cap = QTableWidgetItem(item.caption or "")
                it_cap.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                it_cap.setToolTip("雙擊可輸入說明文字")
                self.win.table.setItem(i, 5, it_cap)

                # 6. 字級 (pt)
                it_cap_sz = QTableWidgetItem(cap_size_label)
                it_cap_sz.setTextAlignment(Qt.AlignCenter)
                it_cap_sz.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                it_cap_sz.setToolTip("雙擊可自訂說明字級 (50~80 pt)")
                self.win.table.setItem(i, 6, it_cap_sz)

                # 7. 操作欄位 (✂️ 裁剪 與 🗑️ 刪除)
                act_widget = QWidget()
                act_layout = QHBoxLayout(act_widget)
                act_layout.setContentsMargins(2, 1, 2, 1)
                act_layout.setSpacing(4)
                act_layout.setAlignment(Qt.AlignCenter)

                if item.media_type == "video":
                    btn_trim = QPushButton("✂️ 裁剪")
                    btn_trim.setCursor(QCursor(Qt.PointingHandCursor))
                    btn_trim.setStyleSheet("QPushButton { background-color: #2b6cb0; color: #ffffff; border-radius: 3px; padding: 2px 6px; font-size: 11px; } QPushButton:hover { background-color: #3182ce; }")
                    btn_trim.clicked.connect(lambda _, cur=item, cur_row=i: self._open_trim_dialog_for_item(cur, cur_row))
                    act_layout.addWidget(btn_trim)

                btn_del = QPushButton("🗑️ 刪除")
                btn_del.setCursor(QCursor(Qt.PointingHandCursor))
                btn_del.setStyleSheet("QPushButton { background-color: #2d3748; color: #feb2b2; border-radius: 3px; padding: 2px 6px; font-size: 11px; } QPushButton:hover { background-color: #e53e3e; color: #ffffff; }")
                btn_del.clicked.connect(lambda _, cur=item: self._delete_media_item(cur))
                act_layout.addWidget(btn_del)

                self.win.table.setCellWidget(i, 7, act_widget)

            self.win.table.resizeColumnToContents(1)
            self.win.table.resizeColumnToContents(2)
            self.win.table.resizeColumnToContents(3)
            self.win.table.resizeColumnToContents(4)
            self.win.table.resizeColumnToContents(6)
            self.win.table.resizeColumnToContents(7)
        finally:
            self.win.table.setUpdatesEnabled(True)
            self.win.table.blockSignals(False)

        if hasattr(self.win, "preview_widget"):
            self.win.preview_widget.update()

    def _sync_table_dur_cell(self, row: int, item: MediaItem):
        self.win.table.blockSignals(True)
        dur_item = self.win.table.item(row, 2)
        if dur_item:
            dur_item.setText(f"{item.effective_duration:.1f}s")
        self.win.table.blockSignals(False)

    def _sync_table_km_cell(self, row: int, item: MediaItem):
        self.win.table.blockSignals(True)
        km_item = self.win.table.item(row, 4)
        if km_item:
            km_label = f"{item.current_km:.2f} (手動)" if (item.manual_distance_km is not None and item.manual_distance_km >= 0) else f"{item.current_km:.2f}"
            km_item.setText(km_label)
        self.win.table.blockSignals(False)

    def _sync_table_cap_size_cell(self, row: int, item: MediaItem):
        self.win.table.blockSignals(True)
        cap_sz_item = self.win.table.item(row, 6)
        if cap_sz_item:
            label = f"{item.caption_size} pt (自訂)" if (item.caption_size is not None and item.caption_size > 0) else f"{self.default_caption_size} pt"
            cap_sz_item.setText(label)
        self.win.table.blockSignals(False)

    # ---------- 使用者操作事件 ----------
    def _delete_media_item(self, item: MediaItem):
        if not getattr(self, "_suppress_delete_confirm", False):
            msg_box = QMessageBox(self.win)
            msg_box.setWindowTitle("確認移除")
            msg_box.setText(f"確定要從媒體清單中移除「{item.filename}」嗎？")
            msg_box.setInformativeText("（此操作僅自本次清單排除，不會刪除硬碟原始檔案）")
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)

            chk = QCheckBox("不再顯示 (後續項目直接移除)", msg_box)
            msg_box.setCheckBox(chk)
            res = msg_box.exec()
            if res != QMessageBox.Yes:
                return
            if chk.isChecked():
                self._suppress_delete_confirm = True

        self.deleted_filenames.add(item.filename)
        del_idx = self.media_items.index(item) if item in self.media_items else -1
        if del_idx >= 0:
            self.media_items.pop(del_idx)

        if hasattr(self.win, "preview_widget"):
            self.win.preview_widget.media_items = self.media_items

        if not self.media_items:
            self.selected_index = -1
            if hasattr(self.win, "lbl_preview_image"):
                self.win.lbl_preview_image.setText("📷 清單已無媒體項目")
                self.win.lbl_preview_image.setPixmap(QPixmap())
            if hasattr(self.win, "lbl_info_filename"): self.win.lbl_info_filename.setText("-")
            if hasattr(self.win, "lbl_info_time"): self.win.lbl_info_time.setText("-")
            if hasattr(self.win, "lbl_info_gps"): self.win.lbl_info_gps.setText("-")
            if hasattr(self.win, "lbl_info_res"): self.win.lbl_info_res.setText("-")
            if hasattr(self.win, "lbl_info_match"): self.win.lbl_info_match.setText("-")
            self._populate_tree()
        else:
            self._populate_tree()
            next_idx = min(max(0, del_idx), len(self.media_items) - 1)
            self.win.table.selectRow(next_idx)

        self._sync_overrides_to_config()

    def _on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self.win,
            "選擇照片或影片檔案 (可複選)",
            "",
            "媒體檔案 (*.jpg *.jpeg *.png *.webp *.bmp *.mp4 *.mov *.avi *.mkv *.webm *.m4v *.flv *.wmv);;照片檔案 (*.jpg *.jpeg *.png *.webp *.bmp);;影片檔案 (*.mp4 *.mov *.avi *.mkv *.webm *.m4v *.flv *.wmv);;所有檔案 (*.*)"
        )
        if files:
            self._import_media_paths(files)

    def _on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self.win, "選擇媒體資料夾")
        if folder:
            self._import_media_paths([folder])

    def _import_media_paths(self, new_paths: List[str]):
        new_items = scan_media_files(new_paths, time_offset_sec=0.0)
        if not new_items:
            QMessageBox.information(self.win, "提示", "未在所選路徑中發現可支援的照片或影片。")
            return

        existing_paths = {Path(it.file_path).resolve() for it in self.media_items}
        added_count = 0
        for it in new_items:
            p = Path(it.file_path).resolve()
            if p not in existing_paths:
                existing_paths.add(p)
                self.media_items.append(it)
                added_count += 1

        if added_count == 0:
            QMessageBox.information(self.win, "提示", "所選媒體已全部在清單中，未重複新增。")
            return

        if self.ride_data:
            match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times)

        # 更新主介面路徑輸入框
        all_paths = [it.file_path for it in self.media_items]
        if hasattr(self.win, "lineEdit_media"):
            self.win.lineEdit_media.setText("; ".join(all_paths))

        if hasattr(self.win, "preview_widget"):
            self.win.preview_widget.media_items = self.media_items
            self.win.preview_widget.update()

        self._populate_tree()
        self._sync_overrides_to_config()
        QMessageBox.information(self.win, "成功", f"已成功新增 {added_count} 個媒體項目！")

    def _on_table_double_clicked(self, row: int, col: int):
        if not (0 <= row < len(self.media_items)):
            return
        item = self.media_items[row]
        if col == 2 and item.media_type == "video":
            self._open_trim_dialog_for_item(item, row)

    def _open_trim_dialog_for_item(self, item: MediaItem, row: int):
        dlg = QtVideoTrimDialog(item, parent=self.win)
        if dlg.exec() == QDialog.Accepted:
            self._sync_table_dur_cell(row, item)
            self._update_stats_summary()
            if row == self.selected_index:
                self._update_photo_preview(item)
            self._sync_overrides_to_config()

    def _on_photo_default_changed(self, val: float):
        self.default_duration = float(val)
        config.MEDIA_POPUP_DURATION = float(val)
        self._update_stats_summary()
        self._sync_overrides_to_config()

    def _on_default_caption_size_changed(self, val: int):
        self.default_caption_size = val
        for r, item in enumerate(self.media_items):
            if item.caption_size is None:
                self._sync_table_cap_size_cell(r, item)
        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])
        self._sync_overrides_to_config()

    def _reset_all_durations_to_defaults(self):
        default_photo_dur = float(self.win.spin_photo_dur.value()) if hasattr(self.win, "spin_photo_dur") else 3.0
        for item in self.media_items:
            item.caption_size = None
            if item.media_type == "video":
                item.clip_start_sec = 0.0
                item.popup_duration = round(item.duration_sec, 2) if item.duration_sec else 10.0
            else:
                item.popup_duration = default_photo_dur
                item.clip_start_sec = 0.0
        self._populate_tree()
        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])
        self._sync_overrides_to_config()
        QMessageBox.information(self.win, "重設完成", f"已將所有相片設為預設停留 {default_photo_dur}s，所有影片還原為原始片長！")

    def _on_table_item_changed(self, table_item: QTableWidgetItem):
        if not table_item or self.win.table.signalsBlocked():
            return
        row = table_item.row()
        col = table_item.column()
        if not (0 <= row < len(self.media_items)):
            return

        item = self.media_items[row]
        txt = table_item.text().strip()
        import re

        if col == 2:
            m = re.search(r"[-+]?(?:\d*\.\d+|\d+)", txt)
            if m:
                try:
                    val = float(m.group(0))
                    item.popup_duration = round(max(0.5, min(300.0, val)), 2)
                except Exception:
                    pass
            self._sync_table_dur_cell(row, item)
            self._update_stats_summary()
            if row == self.selected_index:
                self._update_photo_preview(item)
            self._sync_overrides_to_config()

        elif col == 4:
            m = re.search(r"[-+]?(?:\d*\.\d+|\d+)", txt)
            if m:
                try:
                    val = float(m.group(0))
                    item.manual_distance_km = round(max(0.0, min(self.total_distance_km, val)), 2)
                except Exception:
                    pass
            else:
                if not txt or txt in ("--", "auto", "自動", "None", "-1"):
                    item.manual_distance_km = None
            self._sync_table_km_cell(row, item)
            if row == self.selected_index:
                self._update_photo_preview(item)
                if hasattr(self.win, "preview_widget"):
                    self.win.preview_widget.active_km = item.current_km
                    self.win.preview_widget.focus_active()
            self._sync_overrides_to_config()

        elif col == 5:
            item.caption = txt
            if row == self.selected_index:
                self._update_photo_preview(item)
            self._sync_overrides_to_config()

        elif col == 6:
            m = re.search(r"\d+", txt)
            if m:
                try:
                    item.caption_size = max(50, min(80, int(m.group(0))))
                except Exception:
                    pass
            else:
                if not txt or txt in ("--", "auto", "預設", "None"):
                    item.caption_size = None
            self._sync_table_cap_size_cell(row, item)
            if row == self.selected_index:
                self._update_photo_preview(item)
            self._sync_overrides_to_config()

    def _on_table_select(self):
        if not hasattr(self.win, "table"):
            return
        selected_rows = self.win.table.selectedIndexes()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if 0 <= row < len(self.media_items):
            self.selected_index = row
            item = self.media_items[row]
            self._update_photo_preview(item)
            if hasattr(self.win, "preview_widget"):
                self.win.preview_widget.selected_index = row
                self.win.preview_widget.active_km = item.current_km
                self.win.preview_widget.focus_active()

    def _on_canvas_select_item(self, idx: int):
        if hasattr(self.win, "table") and 0 <= idx < self.win.table.rowCount():
            self.win.table.selectRow(idx)

    def _open_full_media(self):
        if 0 <= self.selected_index < len(self.media_items):
            p = Path(self.media_items[self.selected_index].file_path).resolve()
            if p.is_file():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))

    # ---------- 預覽控制項 (地圖風格、視角模式、解析度) ----------
    def _populate_preview_controls(self):
        """初始化媒體預覽區的「地圖風格」、「視角模式」、「解析度」選單，內容與順序與渲染設定完全一致。"""
        # 1. 地圖風格
        combo_map = getattr(self.win, "combo_preview_map_style", None)
        if combo_map is not None:
            combo_map.blockSignals(True)
            combo_map.clear()
            map_labels = [f"{k}. {v[0]}" for k, v in config.MAP_STYLE_OPTIONS.items()]
            combo_map.addItems(map_labels)
            if hasattr(self.win, "combo_map_style_2"):
                combo_map.setCurrentIndex(self.win.combo_map_style_2.currentIndex())
            combo_map.blockSignals(False)

        # 2. 視角模式
        combo_cam = getattr(self.win, "combo_preview_camera_mode", None)
        if combo_cam is not None:
            from gpx_renderer.gui.main_window.main_controller import CAMERA_MODE_LABELS
            combo_cam.blockSignals(True)
            combo_cam.clear()
            combo_cam.addItems(list(CAMERA_MODE_LABELS.values()))
            if hasattr(self.win, "combo_camera_mode_2"):
                combo_cam.setCurrentIndex(self.win.combo_camera_mode_2.currentIndex())
            combo_cam.blockSignals(False)

        # 3. 解析度
        combo_res = getattr(self.win, "combo_preview_resolution", getattr(self.win, "combo_preview_res", None))
        if combo_res is not None:
            from gpx_renderer.gui.main_window.main_controller import RESOLUTION_PRESETS
            combo_res.blockSignals(True)
            combo_res.clear()
            for label, pw, ph in RESOLUTION_PRESETS:
                combo_res.addItem(label, (pw, ph))
            if hasattr(self.win, "combo_resolution_2"):
                combo_res.setCurrentIndex(self.win.combo_resolution_2.currentIndex())
            combo_res.blockSignals(False)

    def _on_preview_map_style_changed(self, idx: int):
        if self._is_syncing_controls or idx < 0:
            return
        self._is_syncing_controls = True
        try:
            if hasattr(self.win, "combo_map_style_2") and self.win.combo_map_style_2.currentIndex() != idx:
                self.win.combo_map_style_2.setCurrentIndex(idx)
        finally:
            self._is_syncing_controls = False

        if hasattr(self.win, "preview_widget"):
            combo_map = getattr(self.win, "combo_preview_map_style", getattr(self.win, "combo_map_style_2", None))
            map_key = combo_map.currentText().split(".")[0].strip() if combo_map else "1"
            map_label, map_source = config.MAP_STYLE_OPTIONS.get(map_key, ("Google Maps 街道圖", GOOGLE_STREETS_URL))
            self.win.preview_widget.set_map_style(map_source, map_label)

        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])

    def _on_preview_camera_mode_changed(self, idx: int):
        if self._is_syncing_controls or idx < 0:
            return
        self._is_syncing_controls = True
        try:
            if hasattr(self.win, "combo_camera_mode_2") and self.win.combo_camera_mode_2.currentIndex() != idx:
                self.win.combo_camera_mode_2.setCurrentIndex(idx)
        finally:
            self._is_syncing_controls = False

        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])

    def _on_preview_res_changed(self, idx: int):
        if self._is_syncing_controls or idx < 0:
            return
        self._is_syncing_controls = True
        try:
            if hasattr(self.win, "combo_resolution_2") and self.win.combo_resolution_2.currentIndex() != idx:
                self.win.combo_resolution_2.setCurrentIndex(idx)
        finally:
            self._is_syncing_controls = False

        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])

    def _on_hud_chk_toggled(self):
        # 同步回 config
        if hasattr(self.win, "combo_hud_panels"):
            checked_huds = self.win.combo_hud_panels.checked_items()
            config.SHOW_SPEED_HUD = "速度與里程 HUD" in checked_huds
            config.SHOW_MINIMAP = "路線小地圖" in checked_huds
            config.SHOW_ELEVATION = "全景高程剖面" in checked_huds
        elif hasattr(self.win, "chk_show_speed_2"):
            config.SHOW_SPEED_HUD = self.win.chk_show_speed_2.isChecked()
            config.SHOW_MINIMAP = self.win.chk_show_minimap_2.isChecked()
            config.SHOW_ELEVATION = self.win.chk_show_elevation_2.isChecked()

        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])

    def refresh_preview(self):
        """當主視窗地圖風格、視角模式、解析度變更時刷新預覽。"""
        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])

    def _load_item_pixmap(self, item: MediaItem) -> Optional[QPixmap]:
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

    def _get_item_coords(self, item: MediaItem) -> Optional[Tuple[float, float]]:
        if item.mercator_x is not None and item.mercator_y is not None:
            return float(item.mercator_x), float(item.mercator_y)
        if item.current_km >= 0 and self.ride_data and len(self.ride_data.distances) > 0:
            wx = float(np.interp(item.current_km, self.ride_data.distances, self.ride_data.xs))
            wy = float(np.interp(item.current_km, self.ride_data.distances, self.ride_data.ys))
            return wx, wy
        if item.lat is not None and item.lon is not None:
            mx_arr, my_arr = latlon_to_mercator(np.array([item.lat]), np.array([item.lon]))
            return float(mx_arr[0]), float(my_arr[0])
        if self.ride_data:
            return float(self.ride_data.route_center_x), float(self.ride_data.route_center_y)
        return None

    def _on_bg_tile_ready(self, item_key: str, qimg: QImage):
        pix = QPixmap.fromImage(qimg)
        self._media_bg_cache[item_key] = pix
        self._pending_bg_fetches.discard(item_key)
        if 0 <= self.selected_index < len(self.media_items):
            cur_item = self.media_items[self.selected_index]
            map_key = self.win.combo_map_style_2.currentText().split(".")[0].strip() if hasattr(self.win, "combo_map_style_2") else "1"
            if f"{cur_item.filename}::{map_key}" == item_key:
                self._update_photo_preview(cur_item)

    def _on_bg_tile_failed(self, item_key: str, err: str):
        self._pending_bg_fetches.discard(item_key)

    def _update_photo_preview(self, item: MediaItem):
        if not hasattr(self.win, "lbl_preview_image"):
            return

        # 取得模擬解析度
        fw, fh = 1440, 1440
        combo_res = getattr(self.win, "combo_preview_resolution", getattr(self.win, "combo_preview_res", None))
        if combo_res is not None:
            data = combo_res.currentData()
            if data and isinstance(data, (tuple, list)) and data[0] is not None and data[1] is not None:
                fw, fh = int(data[0]), int(data[1])
            elif hasattr(self.win, "get_current_resolution"):
                fw, fh = self.win.get_current_resolution()
        elif hasattr(self.win, "get_current_resolution"):
            fw, fh = self.win.get_current_resolution()

        fw, fh = max(240, fw), max(240, fh)
        aspect = fw / float(fh)

        parent_w = self.win.lbl_preview_image.parentWidget().width() if self.win.lbl_preview_image.parentWidget() else 380
        avail_w = max(260, parent_w - 24)

        if aspect >= 1.2:
            disp_w = min(avail_w, 400)
            disp_h = max(160, int(round(disp_w / aspect)))
        elif aspect <= 0.8:
            disp_h = 380
            disp_w = max(140, int(round(disp_h * aspect)))
        else:
            disp_w = min(avail_w, 280)
            disp_h = max(180, int(round(disp_w / aspect)))

        self.win.lbl_preview_image.setFixedHeight(disp_h + 12)
        scale_to_disp = disp_h / float(fh)
        ui_scale = min(fw, fh) / 1000.0

        # 嚴格依據 renderer.py 計算實際輸出之標準幾何 (Video-space standard coordinates)
        margin_x = max(14, int(round(24 * ui_scale)))
        margin_y = max(14, int(round(22 * ui_scale)))
        top_panel_h = max(110, int(round(136 * ui_scale)))

        if aspect >= 1.3:
            hud_w_ratio = 0.25
        elif aspect <= 0.75:
            hud_w_ratio = 0.44
        else:
            t = (aspect - 0.75) / (1.3 - 0.75)
            hud_w_ratio = 0.44 + (0.25 - 0.44) * t

        hud_w = int(round(fw * hud_w_ratio))
        hud_w = max(int(round(240 * ui_scale)), min(int(round(620 * ui_scale)), hud_w))
        hud_h = top_panel_h
        hud_x = margin_x
        hud_y = margin_y

        if aspect <= 0.75:
            mini_w = hud_w
        else:
            mini_w = max(int(round(200 * ui_scale)), int(round(top_panel_h * 1.35)))
        mini_h = top_panel_h
        mini_x = fw - mini_w - margin_x
        mini_y = margin_y

        elev_x = margin_x
        elev_w = fw - 2 * margin_x
        elev_h = max(80, int(round(105 * ui_scale))) if aspect > 0.75 else max(90, int(round(115 * ui_scale)))
        elev_y = fh - elev_h - margin_y

        # 投影至預覽畫布 (Preview-space coordinates)
        sc = scale_to_disp
        p_hud_rect = QRectF(hud_x * sc, hud_y * sc, hud_w * sc, hud_h * sc)
        p_mini_rect = QRectF(mini_x * sc, mini_y * sc, mini_w * sc, mini_h * sc)
        p_elev_rect = QRectF(elev_x * sc, elev_y * sc, elev_w * sc, elev_h * sc)

        combo_map = getattr(self.win, "combo_preview_map_style", getattr(self.win, "combo_map_style_2", None))
        map_key = combo_map.currentText().split(".")[0].strip() if combo_map else "1"
        map_label, map_source = config.MAP_STYLE_OPTIONS.get(map_key, ("Google Maps 街道圖", GOOGLE_STREETS_URL))

        # 背景底圖
        item_key = f"{item.filename}::{map_key}"
        bg_pix = self._media_bg_cache.get(item_key, None)
        coords = self._get_item_coords(item)

        if bg_pix is None and coords is not None and item_key not in self._pending_bg_fetches:
            wx, wy = coords
            base_margin = float(getattr(config, "VIEW_MARGIN", 800.0))
            margin_x_bg = base_margin * aspect if aspect >= 1.0 else base_margin
            margin_y_bg = base_margin if aspect >= 1.0 else base_margin / aspect
            self._pending_bg_fetches.add(item_key)
            self.bg_worker.fetch_async(
                item_key, wx - margin_x_bg, wy - margin_y_bg, wx + margin_x_bg, wy + margin_y_bg,
                source=map_source,
                zoom=getattr(config, "LOCAL_MAP_ZOOM", 17),
            )

        canvas = QPixmap(disp_w, disp_h)
        canvas.fill(Qt.transparent)

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        frame_rect = QRectF(0, 0, disp_w, disp_h)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(frame_rect, 6, 6)
        painter.save()
        painter.setClipPath(clip_path)

        if bg_pix and not bg_pix.isNull():
            scaled_bg = bg_pix.scaled(disp_w, disp_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            bx = (disp_w - scaled_bg.width()) // 2
            by = (disp_h - scaled_bg.height()) // 2
            painter.drawPixmap(bx, by, scaled_bg)
            painter.fillRect(frame_rect, QColor(7, 11, 16, 125))
        else:
            painter.fillRect(frame_rect, QColor("#111827"))
            if item_key in self._pending_bg_fetches:
                font_loading = QFont("Segoe UI")
                font_loading.setPixelSize(max(8, int(round(12 * sc))))
                painter.setFont(font_loading)
                painter.setPen(QColor(148, 163, 184, 180))
                painter.drawText(frame_rect, Qt.AlignCenter, f"🗺️ 載入 [{map_label}] 底圖中…")

        painter.restore()

        painter.setPen(QPen(QColor("#374151"), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(frame_rect, 6, 6)

        # 檢查所選 HUD 面板
        if hasattr(self.win, "combo_hud_panels"):
            checked_huds = self.win.combo_hud_panels.checked_items()
            show_speed = "速度與里程 HUD" in checked_huds
            show_mini = "路線小地圖" in checked_huds
            show_elev = "全景高程剖面" in checked_huds
        elif hasattr(self.win, "chk_show_speed_2"):
            show_speed = self.win.chk_show_speed_2.isChecked()
            show_mini = self.win.chk_show_minimap_2.isChecked()
            show_elev = self.win.chk_show_elevation_2.isChecked()
        else:
            show_speed = getattr(config, "SHOW_SPEED_HUD", True)
            show_mini = getattr(config, "SHOW_MINIMAP", True)
            show_elev = getattr(config, "SHOW_ELEVATION", True)

        # 繪製中央媒體卡片 (依 renderer.py：卡片上限為畫面的 65% 寬度與 60% 高度)
        max_card_w = max(20, int(round(disp_w * 0.65)))
        max_card_h = max(20, int(round(disp_h * 0.60)))
        raw_pix = self._load_item_pixmap(item)

        if raw_pix and not raw_pix.isNull():
            card_pix = raw_pix.scaled(max_card_w, max_card_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            cw, ch = card_pix.width(), card_pix.height()
            cx = (disp_w - cw) / 2.0
            cy = (disp_h - ch) / 2.0
            radius = max(3.0, min(cw, ch) * 0.05)
            border_w = max(1.2, min(cw, ch) * 0.008)

            path = QPainterPath()
            path.addRoundedRect(QRectF(cx, cy, cw, ch), radius, radius)
            painter.save()
            painter.setClipPath(path)
            painter.drawPixmap(int(round(cx)), int(round(cy)), card_pix)
            painter.restore()

            painter.setPen(QPen(QColor(255, 255, 255, 245), border_w))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(cx, cy, cw, ch), radius, radius)

            if item.caption:
                eff_sz = item.effective_caption_size
                actual_font_px = max(10, int(round(float(eff_sz) * ui_scale)))
                disp_font_px = max(9, int(round(actual_font_px * sc)))

                cap_font = QFont("Segoe UI")
                cap_font.setBold(True)
                cap_font.setPixelSize(disp_font_px)
                painter.setFont(cap_font)
                fm = painter.fontMetrics()
                txt = item.caption
                tb_w = fm.horizontalAdvance(txt)
                tb_h = fm.height()

                pad_x = max(6, int(round(26 * ui_scale * sc)))
                pad_y = max(3, int(round(12 * ui_scale * sc)))
                gap = max(3, int(round(16 * ui_scale * sc)))

                cap_w = min(disp_w - 12, tb_w + 2 * pad_x)
                cap_h = tb_h + 2 * pad_y
                cap_x = (disp_w - cap_w) / 2.0
                cap_y = cy + ch + gap

                # 避免與底部高程圖或邊緣重疊；若超出則移至照片卡片內部下方 (與 renderer.py 行為一致)
                elev_limit = p_elev_rect.y() if show_elev else (disp_h - 6)
                if cap_y + cap_h > elev_limit - 3:
                    cap_y = cy + ch - cap_h - max(4, int(round(12 * ui_scale * sc)))

                cap_radius = max(4, int(round(16 * ui_scale * sc)))

                painter.setPen(QPen(QColor(255, 255, 255, 180), 1.2))
                painter.setBrush(QBrush(QColor(15, 23, 42, 240)))
                painter.drawRoundedRect(QRectF(cap_x, cap_y, cap_w, cap_h), cap_radius, cap_radius)

                painter.setBrush(Qt.NoBrush)
                elided_txt = fm.elidedText(txt, Qt.ElideRight, int(cap_w - 2 * pad_x))
                painter.setPen(QPen(QColor(0, 0, 0, 220)))
                painter.drawText(QRectF(cap_x + 1, cap_y + 1, cap_w, cap_h), Qt.AlignCenter, elided_txt)
                painter.setPen(QPen(QColor(255, 255, 255, 255)))
                painter.drawText(QRectF(cap_x, cap_y, cap_w, cap_h), Qt.AlignCenter, elided_txt)

        # 繪製 HUD 面板
        if show_speed:
            painter.save()
            painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
            painter.setBrush(QBrush(QColor(9, 13, 18, 200)))
            painter.drawRoundedRect(p_hud_rect, max(3.0, 6.0 * sc), max(3.0, 6.0 * sc))

            spd_val = f"{item.current_km * 3.6:.1f}" if item.current_km > 0 else "28.5"
            font_spd = QFont("Segoe UI")
            font_spd.setBold(True)
            font_spd.setPixelSize(max(8, int(round(p_hud_rect.height() * 0.42))))
            painter.setFont(font_spd)
            painter.setPen(QPen(QColor(255, 255, 255, 250)))
            pad_h = max(4.0, 6.0 * sc)
            painter.drawText(
                QRectF(p_hud_rect.x() + pad_h, p_hud_rect.y() + 2, p_hud_rect.width() - 2 * pad_h, p_hud_rect.height() * 0.55),
                Qt.AlignLeft | Qt.AlignVCenter, f"{spd_val} km/h"
            )

            dist_val = f"{item.current_km:.1f} km" if item.current_km >= 0 else "0.0 km"
            font_dst = QFont("Segoe UI")
            font_dst.setPixelSize(max(7, int(round(p_hud_rect.height() * 0.30))))
            painter.setFont(font_dst)
            painter.setPen(QPen(QColor(148, 163, 184, 230)))
            painter.drawText(
                QRectF(p_hud_rect.x() + pad_h, p_hud_rect.y() + p_hud_rect.height() * 0.5, p_hud_rect.width() - 2 * pad_h, p_hud_rect.height() * 0.45),
                Qt.AlignLeft | Qt.AlignVCenter, f"DST: {dist_val}"
            )
            painter.restore()

        if show_mini:
            painter.save()
            painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
            painter.setBrush(QBrush(QColor(9, 13, 18, 200)))
            painter.drawRoundedRect(p_mini_rect, max(3.0, 6.0 * sc), max(3.0, 6.0 * sc))

            font_lbl = QFont("Segoe UI")
            font_lbl.setBold(True)
            font_lbl.setPixelSize(max(6, int(round(p_mini_rect.height() * 0.24))))
            painter.setFont(font_lbl)
            painter.setPen(QPen(QColor(148, 163, 184, 200)))
            title_h = max(8.0, p_mini_rect.height() * 0.30)
            painter.drawText(
                QRectF(p_mini_rect.x() + 5, p_mini_rect.y() + 2, p_mini_rect.width() - 10, title_h),
                Qt.AlignLeft | Qt.AlignTop, "MINIMAP"
            )

            if self.ride_data and len(self.ride_data.xs) > 1:
                xs, ys = self.ride_data.xs, self.ride_data.ys
                min_x, max_x = float(xs.min()), float(xs.max())
                min_y, max_y = float(ys.min()), float(ys.max())
                rw = max(max_x - min_x, 1.0)
                rh = max(max_y - min_y, 1.0)
                pad_m = max(3.0, 5.0 * sc)
                mw_avail = max(10.0, p_mini_rect.width() - 2 * pad_m)
                mh_avail = max(10.0, p_mini_rect.height() - 2 * pad_m - title_h)
                route_sc = min(mw_avail / rw, mh_avail / rh)
                cx_m = p_mini_rect.x() + pad_m + (mw_avail - rw * route_sc) / 2.0
                cy_m = p_mini_rect.y() + pad_m + title_h + (mh_avail - rh * route_sc) / 2.0

                pts = []
                step = max(1, len(xs) // 35)
                for k in range(0, len(xs), step):
                    pts.append(QPointF(cx_m + (xs[k] - min_x) * route_sc, cy_m + (max_y - ys[k]) * route_sc))
                if len(pts) >= 2:
                    painter.setPen(QPen(QColor(255, 255, 255, 80), 1.0))
                    painter.drawPolyline(QPolygonF(pts))

                if item.current_km >= 0 and len(self.ride_data.distances) > 0:
                    ix = float(np.interp(item.current_km, self.ride_data.distances, xs))
                    iy = float(np.interp(item.current_km, self.ride_data.distances, ys))
                    painter.setPen(QPen(QColor(255, 255, 255, 255), 1.2))
                    painter.setBrush(QBrush(QColor(252, 76, 2)))
                    dot_r = max(2.0, 3.0 * sc)
                    painter.drawEllipse(QPointF(cx_m + (ix - min_x) * route_sc, cy_m + (max_y - iy) * route_sc), dot_r, dot_r)
            painter.restore()

        if show_elev:
            painter.save()
            painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
            painter.setBrush(QBrush(QColor(9, 13, 18, 200)))
            painter.drawRoundedRect(p_elev_rect, max(3.0, 6.0 * sc), max(3.0, 6.0 * sc))

            font_lbl = QFont("Segoe UI")
            font_lbl.setBold(True)
            font_lbl.setPixelSize(max(6, int(round(p_elev_rect.height() * 0.28))))
            painter.setFont(font_lbl)
            painter.setPen(QPen(QColor(148, 163, 184, 200)))
            title_h = max(8.0, p_elev_rect.height() * 0.32)
            painter.drawText(
                QRectF(p_elev_rect.x() + 6, p_elev_rect.y() + 2, p_elev_rect.width() - 12, title_h),
                Qt.AlignLeft | Qt.AlignTop, "ELEVATION"
            )

            if self.ride_data and len(self.ride_data.eles) > 1:
                dists = self.ride_data.distances
                eles = self.ride_data.eles
                d_min, d_max = float(dists.min()), max(float(dists.max()), float(dists.min()) + 0.001)
                e_min, e_max = float(eles.min()) - 5.0, float(eles.max()) + 5.0
                if e_max <= e_min: e_max = e_min + 10.0
                pad_e = max(3.0, 5.0 * sc)
                ew_avail = max(10.0, p_elev_rect.width() - 2 * pad_e)
                eh_avail = max(8.0, p_elev_rect.height() - 2 * pad_e - title_h)
                ex_base = p_elev_rect.x() + pad_e
                ey_base = p_elev_rect.y() + pad_e + title_h
                step = max(1, len(dists) // 45)
                poly_pts = [QPointF(ex_base, ey_base + eh_avail)]
                for k in range(0, len(dists), step):
                    poly_pts.append(QPointF(ex_base + (dists[k] - d_min) / (d_max - d_min) * ew_avail, ey_base + (e_max - eles[k]) / (e_max - e_min) * eh_avail))
                poly_pts.append(QPointF(ex_base + ew_avail, ey_base + eh_avail))

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(252, 76, 2, 80)))
                painter.drawPolygon(QPolygonF(poly_pts))
                painter.setPen(QPen(QColor(255, 255, 255, 140), 1.0))
                painter.setBrush(Qt.NoBrush)
                painter.drawPolyline(QPolygonF(poly_pts[1:-1]))

                if item.current_km >= 0 and d_max > d_min:
                    cur_d = min(max(item.current_km, d_min), d_max)
                    cur_e = float(np.interp(cur_d, dists, eles))
                    cur_px = ex_base + (cur_d - d_min) / (d_max - d_min) * ew_avail
                    cur_py = ey_base + (e_max - cur_e) / (e_max - e_min) * eh_avail
                    painter.setPen(QPen(QColor(255, 255, 255, 180), 1, Qt.DashLine))
                    painter.drawLine(QPointF(cur_px, ey_base), QPointF(cur_px, ey_base + eh_avail))
                    painter.setPen(QPen(QColor(255, 255, 255, 255), 1.0))
                    painter.setBrush(QBrush(QColor(56, 189, 248)))
                    dot_r = max(2.0, 2.5 * sc)
                    painter.drawEllipse(QPointF(cur_px, cur_py), dot_r, dot_r)
            painter.restore()

        painter.end()
        self.win.lbl_preview_image.setPixmap(canvas)

        # 更新 EXIF 資訊文字
        if hasattr(self.win, "lbl_info_filename"): self.win.lbl_info_filename.setText(item.filename)
        if hasattr(self.win, "lbl_info_time"):
            self.win.lbl_info_time.setText(item.timestamp.strftime("%Y-%m-%d %H:%M:%S") if item.timestamp else "無拍攝時間 (依里程對齊)")
        if hasattr(self.win, "lbl_info_gps"):
            self.win.lbl_info_gps.setText(f"{item.lat:.5f}°, {item.lon:.5f}°" if item.lat is not None and item.lon is not None else "無 GPS 座標標記")

        dims = self._raw_img_dims.get(item.file_path)
        try:
            sz_mb = Path(item.file_path).stat().st_size / (1024 * 1024)
            size_str = f"{sz_mb:.2f} MB"
        except Exception:
            size_str = ""

        if hasattr(self.win, "lbl_info_res"):
            if item.media_type == "video":
                dur_prefix = f"長度: {item.duration_str} | " if item.duration_str != "--" else ""
                self.win.lbl_info_res.setText(f"{dur_prefix}{dims[0]} × {dims[1]} px ({size_str})" if dims else f"{dur_prefix}影片")
            else:
                self.win.lbl_info_res.setText(f"{dims[0]} × {dims[1]} px ({size_str})" if dims else "相片")

        if hasattr(self.win, "lbl_info_match"):
            is_manual = (item.manual_distance_km is not None and item.manual_distance_km >= 0)
            km = item.current_km
            if is_manual:
                self.win.lbl_info_match.setText(f"📍 {km:.2f} km (手動指定)")
                self.win.lbl_info_match.setStyleSheet("color: #ecc94b; font-weight: bold;")
            else:
                self.win.lbl_info_match.setText(f"📍 {km:.2f} km (自動匹配)")
                self.win.lbl_info_match.setStyleSheet("color: #63b3ed; font-weight: bold;")
