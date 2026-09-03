# -*- coding: utf-8 -*-
"""
媒體管理彈出對話框控制器 (Media Dialog Controller)。
負責路線照片與影片清單之檢視、停留時間與說明文字欄位直接編輯、影片區間裁剪、Google 街道圖軌跡連動與動態預覽。
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
import math
import logging
import numpy as np

from PySide6.QtWidgets import (
    QDialog, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QWidget, QHBoxLayout, QPushButton, QCheckBox,
    QGridLayout, QLabel, QComboBox
)
from PySide6.QtCore import QPointF, Qt, QUrl, QRectF
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QFont, QPen, QBrush,
    QPainterPath, QCursor, QDesktopServices, QImage, QPolygonF
)

from gpx_renderer import config
from gpx_renderer.core.data import RideData, latlon_to_mercator
from gpx_renderer.gui.widgets.checkable_combo_box import CheckableComboBox
from gpx_renderer.core.media import (
    MediaItem, match_media_to_ride, load_media_thumbnail
)
from gpx_renderer.gui.video_trim_dialog import QtVideoTrimDialog
from .map_worker import MediaBgTileWorker, GOOGLE_STREETS_URL
from .ui_media_dialog import Ui_MediaManagerDialog

logger = logging.getLogger(__name__)


class QtMediaManagerDialog(QDialog, Ui_MediaManagerDialog):
    """
    PySide6 原生路線媒體管理器與標籤編輯器對話框。
    支援：
    1. 相片/影片清單於表格中直接編輯停留秒數、手動指定里程、自訂說明與說明字級。
    2. 影片專屬頭尾裁剪與播放區間預覽 (`QtVideoTrimDialog`)。
    3. 自訂說明字級即時預覽與全螢幕原檔檢視。
    4. Google 街道圖底圖之互動式向量軌跡畫布與標記點雙向即時選取連動。
    """

    def __init__(
        self,
        media_items: List[MediaItem],
        ride_data: RideData,
        media_duration: float = 3.0,
        media_offset_sec: float = 0.0,
        media_path: str = "",
        default_duration: Optional[float] = None,
        default_caption_size: int = 60,
        frame_size: Optional[Tuple[int, int]] = None,
        frame_width: Optional[int] = None,
        frame_height: Optional[int] = None,
        parent=None,
        **kwargs,
    ):
        super().__init__(parent)
        self.media_items = list(media_items)
        self.ride_data = ride_data

        # 兼容 media_duration 與 default_duration
        if default_duration is not None:
            self.default_duration = float(default_duration)
        else:
            self.default_duration = float(media_duration)

        self.media_offset_sec = float(media_offset_sec)
        if default_caption_size is not None and int(default_caption_size) >= 50:
            self.default_caption_size = min(80, int(default_caption_size))
        else:
            self.default_caption_size = 60
        self.media_path = media_path

        # 兼容 frame_size 與 (frame_width, frame_height)
        if frame_width is not None and frame_height is not None:
            self.frame_width, self.frame_height = int(frame_width), int(frame_height)
        elif frame_size is not None:
            self.frame_width, self.frame_height = int(frame_size[0]), int(frame_size[1])
        else:
            self.frame_width, self.frame_height = 1920, 1080

        self.total_distance_km = float(self.ride_data.distances[-1]) if len(self.ride_data.distances) > 0 else 0.0
        self.selected_index: int = -1
        self.deleted_filenames: Set[str] = set()
        self._suppress_delete_confirm: bool = False

        # 縮圖記憶體快取
        self._pixmap_cache: Dict[str, Optional[QPixmap]] = {}
        self._raw_img_dims: Dict[str, Tuple[int, int]] = {}

        # 底圖風格與非同步背景預覽工作元件
        self.map_style_key = str(kwargs.get("map_style_key") or "1")
        self.map_style_label = str(kwargs.get("map_style_label") or "")
        self.map_source = kwargs.get("map_source", None)
        if not self.map_source:
            opt = config.MAP_STYLE_OPTIONS.get(self.map_style_key, None)
            if opt:
                self.map_style_label = opt[0]
                self.map_source = opt[1]
            else:
                self.map_source = GOOGLE_STREETS_URL
                self.map_style_label = "Google Maps 街道圖"
        if not self.map_style_label:
            self.map_style_label = "自訂底圖"

        # 接收主介面傳入之渲染設定
        self.camera_mode = str(kwargs.get("camera_mode") or "North-Up")
        self.resolution_preset = str(kwargs.get("resolution_preset") or "")
        self.track_color = str(kwargs.get("track_color") or getattr(config, "TRACK_COLOR_SCHEME", "Strava 經典橘"))
        self.local_zoom = str(kwargs.get("local_zoom") or getattr(config, "LOCAL_MAP_ZOOM", 17))
        self.hud_checked_items = list(kwargs.get("hud_checked_items") or ["速度與里程 HUD", "路線小地圖", "全景高程剖面"])

        # 傳出結果之設定屬性
        self.result_map_style_text = ""
        self.result_camera_mode = self.camera_mode
        self.result_resolution_preset = self.resolution_preset
        self.result_track_color = self.track_color
        self.result_local_zoom = self.local_zoom
        self.result_hud_checked_items = list(self.hud_checked_items)

        # 媒體底圖背景下載元件與快取
        self._media_bg_cache: Dict[str, QPixmap] = {}
        self._pending_bg_fetches: Set[str] = set()
        self.bg_worker = MediaBgTileWorker(self)
        self.bg_worker.tile_ready.connect(self._on_bg_tile_ready)
        self.bg_worker.fetch_failed.connect(self._on_bg_tile_failed)

        # 傳出結果
        self.result_overrides: Dict[str, Dict[str, Any]] = {}
        self.result_frame_size: Tuple[int, int] = (self.frame_width, self.frame_height)

        # 若傳入之媒體尚未計算匹配點位，執行初始對齊匹配
        if self.media_items and self.ride_data:
            match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times, time_offset_sec=self.media_offset_sec)

        # 載入由 Qt Designer 編譯生成的 UI
        self.setupUi(self)

        # 初始化控制項預設值
        self.spin_photo_dur.setValue(self.default_duration)
        self.spin_default_caption_size.setValue(self.default_caption_size)
        self.spin_media_offset.setValue(self.media_offset_sec)

        # 綁定 UI 事件與表格設定
        self._setup_ui_bindings()

        # 載入並渲染媒體清單
        self._populate_tree()

        # 開局自動選取第 1 筆項目展示預覽
        if self.media_items:
            self.table.selectRow(0)

    def _on_bg_tile_ready(self, item_key: str, qimg: QImage):
        """媒體背景底圖下載完成回調"""
        pix = QPixmap.fromImage(qimg)
        self._media_bg_cache[item_key] = pix
        self._pending_bg_fetches.discard(item_key)
        if 0 <= self.selected_index < len(self.media_items):
            cur_item = self.media_items[self.selected_index]
            if f"{cur_item.filename}::{self.map_style_key}" == item_key:
                self._update_photo_preview(cur_item)

    def _on_bg_tile_failed(self, item_key: str, err: str):
        """媒體背景底圖下載失敗回調"""
        self._pending_bg_fetches.discard(item_key)
        logger.debug("Failed to fetch media basemap for %s: %s", item_key, err)

    def _get_item_coords(self, item: MediaItem) -> Optional[Tuple[float, float]]:
        """取得該媒體項目的 Web Mercator (x, y) 世界座標。"""
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

    def _setup_ui_bindings(self):
        """初始化 UI 元件之動態設定、表格標頭自適應、分割器比例與信號槽綁定。"""
        # 1. 路線向量畫布初始化
        self.preview_widget.set_ride_data(self.ride_data)
        self.preview_widget.set_map_style(self.map_source, self.map_style_label)
        self.preview_widget.media_items = self.media_items
        self.preview_widget.item_selected.connect(self._on_canvas_select_item)

        # 2. 欄位寬度自適應設置 (共 8 欄：檔名, 類型, 停留秒數, 拍攝時間, 匹配里程, 自訂說明, 字級, 操作)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)           # 檔名
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 類型
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 停留秒數 (影片只顯示裁剪後秒數)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 拍攝時間
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 匹配里程 (km)
        header.setSectionResizeMode(5, QHeaderView.Stretch)           # 自訂說明 (自適應，最小容納 5 個中文)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 字級 (pt)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # 操作
        header.setMinimumSectionSize(45)

        fm = self.table.fontMetrics()
        min_caption_w = max(110, fm.horizontalAdvance("自訂說明文字") + 20)
        self.table.setColumnWidth(5, min_caption_w)

        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.verticalHeader().setVisible(False)

        # 3. 分割器比例配置 (若 UI 使用 Splitter 則設定比例)
        if hasattr(self, "left_vsplitter"):
            self.left_vsplitter.setStretchFactor(0, 1)
            self.left_vsplitter.setStretchFactor(1, 1)
            self.left_vsplitter.setSizes([280, 300])
        if hasattr(self, "main_splitter"):
            self.main_splitter.setSizes([840, 420])

        # 4. 建置與主介面同步之 6 項渲染設定控制元件 (地圖風格、視角模式、解析度預設、軌跡顏色、資訊面板、Local Zoom)
        self._setup_synchronized_render_controls()

        # 5. 信號與槽綁定 (Signal & Slot Connections)
        self.spin_photo_dur.valueChanged.connect(self._on_photo_default_changed)
        self.spin_default_caption_size.valueChanged.connect(self._on_default_caption_size_changed)
        self.btn_reset_defaults.clicked.connect(self._reset_all_durations_to_defaults)
        self.btn_realign.clicked.connect(self._recalculate_time_offset)
        self.btn_add_files.clicked.connect(self._on_add_files)
        self.btn_add_folder.clicked.connect(self._on_add_folder)

        self.table.itemSelectionChanged.connect(self._on_table_select)
        self.table.itemChanged.connect(self._on_table_item_changed)
        self.table.cellDoubleClicked.connect(self._on_table_double_clicked)

        self.btn_zoom_in.clicked.connect(lambda: self.preview_widget.zoom_in())
        self.btn_zoom_out.clicked.connect(lambda: self.preview_widget.zoom_out())
        self.btn_reset_view.clicked.connect(lambda: self.preview_widget.reset_view())

        self.lbl_preview_image.clicked.connect(self._open_full_media)

        self.btn_reset_all.clicked.connect(self._reset_all)
        self.btn_save.clicked.connect(self._on_save_and_apply)
        self.btn_cancel.clicked.connect(self.reject)

    def _delete_media_item(self, item: MediaItem):
        """從清單中移除個別項目，並記錄至排除集合。"""
        if not getattr(self, "_suppress_delete_confirm", False):
            msg_box = QMessageBox(self)
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

        self.preview_widget.media_items = self.media_items

        if not self.media_items:
            self.selected_index = -1
            self.lbl_preview_image.setText("📷 清單已無媒體項目")
            self.lbl_preview_image.setPixmap(QPixmap())
            self.lbl_preview_image.setToolTip("點擊可開啟原檔檢視")
            self.lbl_info_filename.setText("-")
            self.lbl_info_time.setText("-")
            self.lbl_info_gps.setText("-")
            self.lbl_info_res.setText("-")
            self.lbl_info_match.setText("-")
            self.preview_widget.selected_index = -1
            self.preview_widget.active_km = -1.0
            self._populate_tree()
        else:
            self._populate_tree()
            next_idx = min(max(0, del_idx), len(self.media_items) - 1)
            self.table.selectRow(next_idx)
            self.selected_index = next_idx
            item_now = self.media_items[next_idx]
            self._update_photo_preview(item_now)
            self.preview_widget.selected_index = next_idx
            self.preview_widget.active_km = item_now.current_km
            self.preview_widget.focus_active()

        self.preview_widget.update()

    def _on_add_files(self):
        """可單選/複選照片或影片檔案新增至清單。"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "選擇照片或影片檔案 (可複選)",
            "",
            "媒體檔案 (*.jpg *.jpeg *.png *.webp *.bmp *.mp4 *.mov *.avi *.mkv *.webm *.m4v *.flv *.wmv);;照片檔案 (*.jpg *.jpeg *.png *.webp *.bmp);;影片檔案 (*.mp4 *.mov *.avi *.mkv *.webm *.m4v *.flv *.wmv);;所有檔案 (*.*)"
        )
        if not files:
            return
        self._import_media_paths(files)

    def _on_add_folder(self):
        """選擇資料夾匯入其內部所有照片與影片。"""
        folder = QFileDialog.getExistingDirectory(self, "選擇媒體資料夾")
        if not folder:
            return
        self._import_media_paths([folder])

    def _import_media_paths(self, new_paths: list[str]):
        """將新選取的檔案/資料夾掃描解析並合併至當前媒體清單。"""
        from gpx_renderer.core.media import scan_media_files
        new_items = scan_media_files(new_paths, time_offset_sec=self.spin_media_offset.value())
        if not new_items:
            QMessageBox.information(self, "提示", "未在所選路徑中發現可支援的照片或影片。")
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
            QMessageBox.information(self, "提示", "所選媒體已全部在清單中，未重複新增。")
            return

        # 重新配對並更新
        match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times, time_offset_sec=self.spin_media_offset.value())
        self.preview_widget.media_items = self.media_items
        self._populate_tree()
        self.preview_widget.update()
        QMessageBox.information(self, "成功", f"已成功新增 {added_count} 個媒體項目！")

    def _update_stats_summary(self):
        """統計所有相片、影片與停留增加秒數，並動態更新媒體清單抬頭。"""
        total_items = len(self.media_items)
        num_photos = sum(1 for it in self.media_items if it.media_type == "image")
        num_videos = sum(1 for it in self.media_items if it.media_type == "video")
        total_photo_sec = sum(it.effective_duration for it in self.media_items if it.media_type == "image")
        total_video_sec = sum(it.effective_duration for it in self.media_items if it.media_type == "video")
        total_media_sec = total_photo_sec + total_video_sec

        sec_str = f"{total_media_sec:.0f}" if total_media_sec.is_integer() else f"{total_media_sec:.1f}"
        title_text = f"媒體清單 (共 {total_items} 項) +{sec_str} 秒"

        if hasattr(self, "group_media_list"):
            self.group_media_list.setTitle(title_text)
        elif hasattr(self, "groupBox"):
            self.groupBox.setTitle(title_text)

        if hasattr(self, "lbl_table_header"):
            self.lbl_table_header.setText(title_text)

        if hasattr(self, "lbl_stats_summary"):
            self.lbl_stats_summary.setText(
                f"📊 媒體統計：共 {total_items} 項（🎬 {num_videos} 部影片 + 📷 {num_photos} 張相片） | "
                f"⏱️ 停留總增加：+{sec_str} 秒（影片增加 +{total_video_sec:.1f} 秒，相片增加 +{total_photo_sec:.1f} 秒）"
            )

    def _populate_tree(self):
        """將所有媒體項目載入表格，各欄位具備直接點選編輯與操作功能。"""
        self._update_stats_summary()
        saved_sizes = getattr(self, "left_vsplitter", None)
        sizes = saved_sizes.sizes() if saved_sizes else None

        self.table.blockSignals(True)
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(0)

            for i, item in enumerate(self.media_items):
                self.table.insertRow(i)

                ts_str = item.timestamp.strftime("%Y-%m-%d %H:%M:%S") if item.timestamp else "--"
                km = item.current_km
                km_label = f"{km:.2f} (手動)" if (item.manual_distance_km is not None and item.manual_distance_km >= 0) else f"{km:.2f}"
                type_label = "🎬 影片" if item.media_type == "video" else "📷 相片"
                # 當媒體類型是影片時，「停留秒數」只顯示裁剪過後的秒數
                dur_str = f"{item.effective_duration:.1f}s"
                cap_size_label = f"{item.caption_size} pt (自訂)" if (item.caption_size is not None and item.caption_size > 0) else f"{self.default_caption_size} pt"

                # 0. 檔名
                item_fn = QTableWidgetItem(item.filename)
                item_fn.setToolTip(item.file_path)
                item_fn.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(i, 0, item_fn)

                # 1. 類型
                item_type = QTableWidgetItem(type_label)
                item_type.setTextAlignment(Qt.AlignCenter)
                item_type.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(i, 1, item_type)

                # 2. 停留秒數 (影片只顯示裁剪過後的秒數)
                item_dur = QTableWidgetItem(dur_str)
                item_dur.setTextAlignment(Qt.AlignCenter)
                item_dur.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                if item.media_type == "video":
                    item_dur.setToolTip("雙擊可輸入自訂秒數，或點擊右側「✂️ 裁剪」按鈕精確選取播放區間")
                else:
                    item_dur.setToolTip("雙擊可直接輸入自訂停留秒數 (0.5 ~ 300.0 秒)")
                self.table.setItem(i, 2, item_dur)

                # 3. 拍攝時間
                item_ts = QTableWidgetItem(ts_str)
                item_ts.setTextAlignment(Qt.AlignCenter)
                item_ts.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(i, 3, item_ts)

                # 4. 匹配里程 (km)
                item_km = QTableWidgetItem(km_label)
                item_km.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_km.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                item_km.setToolTip("雙擊可直接手動輸入里程 (km)；清空或輸入 -- 可恢復自動匹配")
                self.table.setItem(i, 4, item_km)

                # 5. 自訂說明
                item_cap = QTableWidgetItem(item.caption or "")
                item_cap.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                item_cap.setToolTip("雙擊可直接編輯相片/影片說明文字")
                self.table.setItem(i, 5, item_cap)

                # 6. 字級 (pt)
                item_cap_sz = QTableWidgetItem(cap_size_label)
                item_cap_sz.setTextAlignment(Qt.AlignCenter)
                item_cap_sz.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                item_cap_sz.setToolTip("雙擊可輸入自訂說明字級 (50~80 pt)；清空或輸入 -- 恢復預設")
                self.table.setItem(i, 6, item_cap_sz)

                # 7. 操作欄位 (包含 ✂️ 裁剪 與 🗑️ 刪除 按鈕)
                act_widget = QWidget()
                act_layout = QHBoxLayout(act_widget)
                act_layout.setContentsMargins(2, 1, 2, 1)
                act_layout.setSpacing(4)
                act_layout.setAlignment(Qt.AlignCenter)

                if item.media_type == "video":
                    btn_trim = QPushButton("✂️ 裁剪")
                    btn_trim.setToolTip(f"彈出影片裁剪視窗以設定「{item.filename}」播放起訖區間")
                    btn_trim.setCursor(QCursor(Qt.PointingHandCursor))
                    btn_trim.setStyleSheet("""
                        QPushButton {
                            background-color: #2b6cb0;
                            color: #ffffff;
                            border: 1px solid #3182ce;
                            border-radius: 3px;
                            padding: 2px 6px;
                            font-size: 11px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #3182ce;
                        }
                    """)
                    btn_trim.clicked.connect(lambda _, cur=item, cur_row=i: self._open_trim_dialog_for_item(cur, cur_row))
                    act_layout.addWidget(btn_trim)

                btn_del = QPushButton("🗑️ 刪除")
                btn_del.setToolTip(f"從清單中移除「{item.filename}」")
                btn_del.setCursor(QCursor(Qt.PointingHandCursor))
                btn_del.setStyleSheet("""
                    QPushButton {
                        background-color: #2d3748;
                        color: #feb2b2;
                        border: 1px solid #4a5568;
                        border-radius: 3px;
                        padding: 2px 6px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #e53e3e;
                        color: #ffffff;
                        border-color: #c53030;
                    }
                    QPushButton:pressed {
                        background-color: #9b2c2c;
                    }
                """)
                btn_del.clicked.connect(lambda _, cur=item: self._delete_media_item(cur))
                act_layout.addWidget(btn_del)

                self.table.setCellWidget(i, 7, act_widget)

            # 欄位內容自適應緊湊調整
            self.table.resizeColumnToContents(1)
            self.table.resizeColumnToContents(2)
            self.table.resizeColumnToContents(3)
            self.table.resizeColumnToContents(4)
            self.table.resizeColumnToContents(6)
            self.table.resizeColumnToContents(7)
        finally:
            self.table.setUpdatesEnabled(True)
            self.table.blockSignals(False)
            if sizes and sum(sizes) > 0 and saved_sizes:
                saved_sizes.setSizes(sizes)

        self.preview_widget.update()

    def _sync_table_dur_cell(self, row: int, item: MediaItem):
        """將 MediaItem 停留時長 (影片裁剪後秒數/相片秒數) 即時同步至表格第 2 欄 (停留秒數)。"""
        self.table.blockSignals(True)
        dur_item = self.table.item(row, 2)
        if dur_item:
            dur_item.setText(f"{item.effective_duration:.1f}s")
        self.table.blockSignals(False)

    def _sync_table_km_cell(self, row: int, item: MediaItem):
        """將 MediaItem 當前里程即時同步至表格第 4 欄 (匹配里程)。"""
        self.table.blockSignals(True)
        km_item = self.table.item(row, 4)
        if km_item:
            km_label = f"{item.current_km:.2f} (手動)" if (item.manual_distance_km is not None and item.manual_distance_km >= 0) else f"{item.current_km:.2f}"
            km_item.setText(km_label)
        self.table.blockSignals(False)

    def _sync_table_cap_cell(self, row: int, item: MediaItem):
        """將 MediaItem 說明文字即時同步至表格第 5 欄 (自訂說明)。"""
        self.table.blockSignals(True)
        cap_item = self.table.item(row, 5)
        if cap_item:
            cap_item.setText(item.caption or "")
        self.table.blockSignals(False)

    def _sync_table_cap_size_cell(self, row: int, item: MediaItem):
        """將 MediaItem 說明字級即時同步至表格第 6 欄 (字級)。"""
        self.table.blockSignals(True)
        cap_sz_item = self.table.item(row, 6)
        if cap_sz_item:
            label = f"{item.caption_size} pt (自訂)" if (item.caption_size is not None and item.caption_size > 0) else f"{self.default_caption_size} pt"
            cap_sz_item.setText(label)
        self.table.blockSignals(False)

    def _on_table_double_clicked(self, row: int, col: int):
        """雙擊停留秒數或操作欄時，若是影片則彈出專屬影片裁剪對話框。"""
        if not (0 <= row < len(self.media_items)):
            return
        item = self.media_items[row]
        if col == 2 and item.media_type == "video":
            self._open_trim_dialog_for_item(item, row)

    def _open_trim_dialog_for_item(self, item: MediaItem, row: int):
        """開啟影片裁剪對話框以滑桿設定影片頭尾區間。"""
        dlg = QtVideoTrimDialog(item, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._sync_table_dur_cell(row, item)
            self._update_stats_summary()
            if row == self.selected_index:
                self._update_photo_preview(item)

    def _on_photo_default_changed(self, val: float):
        """更新頂部預設相片停留秒數。"""
        self.default_duration = float(val)
        config.MEDIA_POPUP_DURATION = float(val)
        self._update_stats_summary()

    def _on_default_caption_size_changed(self, val: int):
        """更新頂部預設說明字級，並即時更新清單中未自訂字級之項目。"""
        self.default_caption_size = val
        for r, item in enumerate(self.media_items):
            if item.caption_size is None:
                self._sync_table_cap_size_cell(r, item)
        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])

    def _reset_all_durations_to_defaults(self):
        """一鍵將所有項目還原為預設停留秒數、預設字級與原始影片片長。"""
        default_photo_dur = float(self.spin_photo_dur.value())
        default_cap_size = int(self.spin_default_caption_size.value())
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
        QMessageBox.information(self, "重設完成", f"已將所有相片設為預設停留 {default_photo_dur}s、說明文字大小 {default_cap_size}pt，所有影片還原為原始全片長度！")

    def _on_table_item_changed(self, table_item: QTableWidgetItem):
        """處理表格內直接編輯停留秒數、里程、說明或字級的事件，即時自動更新並連動右側預覽與地圖。"""
        if not table_item or self.table.signalsBlocked():
            return
        row = table_item.row()
        col = table_item.column()
        if not (0 <= row < len(self.media_items)):
            return

        item = self.media_items[row]
        if col == 2:
            # 1. 編輯停留秒數 (0.5 ~ 300.0s)
            txt = table_item.text().strip()
            import re
            m = re.search(r"[-+]?(?:\d*\.\d+|\d+)", txt)
            if m:
                try:
                    val = float(m.group(0))
                    val = max(0.5, min(300.0, val))
                    item.popup_duration = round(val, 2)
                except Exception:
                    pass
            self._sync_table_dur_cell(row, item)
            self._update_stats_summary()
            if row == self.selected_index:
                self._update_photo_preview(item)

        elif col == 4:
            # 2. 編輯里程欄位 (0.0 ~ total_distance_km)
            txt = table_item.text().strip()
            import re
            m = re.search(r"[-+]?(?:\d*\.\d+|\d+)", txt)
            if m:
                try:
                    val = float(m.group(0))
                    val = max(0.0, min(self.total_distance_km, val))
                    item.manual_distance_km = round(val, 2)
                except Exception:
                    pass
            else:
                if not txt or txt in ("--", "auto", "自動", "None", "-1"):
                    item.manual_distance_km = None

            # 規範化儲存格顯示文字
            self._sync_table_km_cell(row, item)

            # 若為當前選取項，即時同步右側預覽與地圖
            if row == self.selected_index:
                self._update_photo_preview(item)
                self.preview_widget.active_km = item.current_km
                self.preview_widget.focus_active()
            self.preview_widget.update()

        elif col == 5:
            # 3. 編輯自訂說明文字
            item.caption = table_item.text().strip()
            if row == self.selected_index:
                self._update_photo_preview(item)

        elif col == 6:
            # 4. 編輯說明字級 (50 ~ 80 pt)
            txt = table_item.text().strip()
            import re
            m = re.search(r"\d+", txt)
            if m:
                try:
                    val = int(m.group(0))
                    val = max(50, min(80, val))
                    item.caption_size = val
                except Exception:
                    pass
            else:
                if not txt or txt in ("--", "auto", "預設", "None"):
                    item.caption_size = None

            self._sync_table_cap_size_cell(row, item)
            if row == self.selected_index:
                self._update_photo_preview(item)

    def _on_save_and_apply(self):
        """儲存並套用所有媒體設定與覆寫屬性。"""
        overrides = {}
        # 記錄已排除/刪除之檔案
        for fn in self.deleted_filenames:
            overrides[fn] = {
                "excluded": True,
                "deleted": True,
            }

        # 記錄目前保留項目之屬性覆寫
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

        self.result_overrides = overrides

        # 記錄同步渲染設定回傳值
        if hasattr(self, "combo_map_style"):
            self.result_map_style_text = self.combo_map_style.currentText()
        if hasattr(self, "combo_camera_mode"):
            self.result_camera_mode = self.combo_camera_mode.currentText()
        if hasattr(self, "combo_preview_res"):
            self.result_resolution_preset = self.combo_preview_res.currentText()
        if hasattr(self, "combo_track_color"):
            self.result_track_color = self.combo_track_color.currentText()
        if hasattr(self, "combo_local_zoom"):
            self.result_local_zoom = self.combo_local_zoom.currentText()
        if hasattr(self, "combo_hud_panels"):
            self.result_hud_checked_items = self.combo_hud_panels.checked_items()

        self.accept()

    def _setup_synchronized_render_controls(self):
        """建置與主介面同步的 6 項渲染設定控制元件並插入預覽區塊頂部。"""
        # 建立 2 欄 3 列的緊湊網格佈局
        self.render_controls_container = QWidget(self.preview_group)
        grid = QGridLayout(self.render_controls_container)
        grid.setContentsMargins(0, 0, 0, 2)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)

        combo_style = """
            QComboBox {
                background-color: #1a202c;
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
            }
            QComboBox:hover {
                border-color: #63b3ed;
            }
            QComboBox::drop-down {
                border: none;
                width: 16px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a202c;
                color: #e2e8f0;
                selection-background-color: #3182ce;
            }
        """

        # 1. 地圖風格
        lbl_style = QLabel("🗺️ 地圖風格：", self.render_controls_container)
        lbl_style.setStyleSheet("color: #a0aec0; font-size: 11px; font-weight: bold;")
        self.combo_map_style = QComboBox(self.render_controls_container)
        self.combo_map_style.setStyleSheet(combo_style)
        self.combo_map_style.setToolTip("設定渲染影片與相片卡片背景使用的底圖圖資風格")
        map_labels = [f"{k}. {v[0]}" for k, v in config.MAP_STYLE_OPTIONS.items()]
        self.combo_map_style.addItems(map_labels)

        # 預設選取當前風格
        matched_idx = 0
        for i, item_txt in enumerate(map_labels):
            if self.map_style_label and self.map_style_label in item_txt:
                matched_idx = i
                break
            if item_txt.startswith(f"{self.map_style_key}."):
                matched_idx = i
                break
        self.combo_map_style.setCurrentIndex(matched_idx)

        # 2. 視角模式
        lbl_camera = QLabel("🎥 視角模式：", self.render_controls_container)
        lbl_camera.setStyleSheet("color: #a0aec0; font-size: 11px; font-weight: bold;")
        self.combo_camera_mode = QComboBox(self.render_controls_container)
        self.combo_camera_mode.setStyleSheet(combo_style)
        self.combo_camera_mode.setToolTip("視角模式：正北朝上、跟隨行進或 3D 真地形")
        camera_labels = ["正北朝上 (North-Up)", "跟隨行進 (Heading-Up)", "3D 真地形 (3D-Terrain)"]
        self.combo_camera_mode.addItems(camera_labels)
        cam_idx = 0
        for i, txt in enumerate(camera_labels):
            if self.camera_mode in txt:
                cam_idx = i
                break
        self.combo_camera_mode.setCurrentIndex(cam_idx)

        # 3. 解析度預設 (重用原 combo_preview_res 並優化樣式與名稱)
        lbl_res = QLabel("🎬 解析度預設：", self.render_controls_container)
        lbl_res.setStyleSheet("color: #a0aec0; font-size: 11px; font-weight: bold;")
        self.combo_preview_res.setParent(self.render_controls_container)
        self.combo_preview_res.setStyleSheet(combo_style)
        self._populate_resolution_combo()

        # 4. 軌跡顏色
        lbl_track = QLabel("🎨 軌跡顏色：", self.render_controls_container)
        lbl_track.setStyleSheet("color: #a0aec0; font-size: 11px; font-weight: bold;")
        self.combo_track_color = QComboBox(self.render_controls_container)
        self.combo_track_color.setStyleSheet(combo_style)
        self.combo_track_color.setToolTip("自訂動畫中 GPS 軌跡線條配色方案")
        self.combo_track_color.addItems(config.TRACK_COLOR_OPTIONS)
        track_idx = self.combo_track_color.findText(self.track_color)
        if track_idx >= 0:
            self.combo_track_color.setCurrentIndex(track_idx)

        # 5. 資訊面板 (可複數勾選下拉選單)
        lbl_hud = QLabel("📊 資訊面板：", self.render_controls_container)
        lbl_hud.setStyleSheet("color: #a0aec0; font-size: 11px; font-weight: bold;")
        self.combo_hud_panels = CheckableComboBox(self.render_controls_container)
        self.combo_hud_panels.setStyleSheet(combo_style)
        self.combo_hud_panels.setToolTip("點擊可複數勾選或取消要在預覽畫面與影片中顯示的資訊面板")
        self.combo_hud_panels.add_checkable_item("速度與里程 HUD", data="speed", checked=("速度與里程 HUD" in self.hud_checked_items))
        self.combo_hud_panels.add_checkable_item("路線小地圖", data="minimap", checked=("路線小地圖" in self.hud_checked_items))
        self.combo_hud_panels.add_checkable_item("全景高程剖面", data="elevation", checked=("全景高程剖面" in self.hud_checked_items))

        # 6. Local Zoom
        lbl_zoom = QLabel("🔍 Local Zoom：", self.render_controls_container)
        lbl_zoom.setStyleSheet("color: #a0aec0; font-size: 11px; font-weight: bold;")
        self.combo_local_zoom = QComboBox(self.render_controls_container)
        self.combo_local_zoom.setStyleSheet(combo_style)
        self.combo_local_zoom.setToolTip("局部特寫地圖縮放層級 (14 ~ 18 或 auto 自動)")
        self.combo_local_zoom.addItems(["auto", "14", "15", "16", "17", "18"])
        zoom_idx = self.combo_local_zoom.findText(str(self.local_zoom))
        if zoom_idx >= 0:
            self.combo_local_zoom.setCurrentIndex(zoom_idx)
        else:
            self.combo_local_zoom.setCurrentText(str(self.local_zoom))

        # 依 2 欄 3 列編排
        # Row 0: 地圖風格, 視角模式
        grid.addWidget(lbl_style, 0, 0)
        grid.addWidget(self.combo_map_style, 0, 1)
        grid.addWidget(lbl_camera, 0, 2)
        grid.addWidget(self.combo_camera_mode, 0, 3)

        # Row 1: 解析度預設, 軌跡顏色
        grid.addWidget(lbl_res, 1, 0)
        grid.addWidget(self.combo_preview_res, 1, 1)
        grid.addWidget(lbl_track, 1, 2)
        grid.addWidget(self.combo_track_color, 1, 3)

        # Row 2: 資訊面板, Local Zoom
        grid.addWidget(lbl_hud, 2, 0)
        grid.addWidget(self.combo_hud_panels, 2, 1)
        grid.addWidget(lbl_zoom, 2, 2)
        grid.addWidget(self.combo_local_zoom, 2, 3)

        # 建立外置狀態標籤 (將原本畫布內的文字移到外面)
        self.lbl_preview_info_tag = QLabel(self.preview_group)
        self.lbl_preview_info_tag.setObjectName("lbl_preview_info_tag")
        self.lbl_preview_info_tag.setStyleSheet("color: #a0aec0; font-size: 11px; padding: 2px 4px; background-color: #1a202c; border: 1px solid #2d3748; border-radius: 4px;")
        self.lbl_preview_info_tag.setAlignment(Qt.AlignCenter)

        # 重新排版 self.preview_vbox
        # 先移除舊有的 res_row
        if hasattr(self, "res_row"):
            # 隱藏原有的 res_row 舊元件
            if hasattr(self, "lbl_preview_res_title"):
                self.lbl_preview_res_title.setVisible(False)
            if hasattr(self, "horizontalSpacer_6"):
                self.res_row.removeItem(self.horizontalSpacer_6)

        self.preview_vbox.insertWidget(0, self.render_controls_container)
        self.preview_vbox.insertWidget(1, self.lbl_preview_info_tag)

        # 事件監聽與即時聯動刷新預覽
        def _on_map_style_changed(idx: int):
            txt = self.combo_map_style.currentText()
            key = txt.split(".")[0].strip() if "." in txt else "1"
            self.map_style_key = key
            opt = config.MAP_STYLE_OPTIONS.get(key)
            if opt:
                self.map_style_label = opt[0]
                self.map_source = opt[1]
            if 0 <= self.selected_index < len(self.media_items):
                self._update_photo_preview(self.media_items[self.selected_index])

        def _on_camera_mode_changed(idx: int):
            self.camera_mode = self.combo_camera_mode.currentText()
            if 0 <= self.selected_index < len(self.media_items):
                self._update_photo_preview(self.media_items[self.selected_index])

        def _on_track_color_changed(idx: int):
            self.track_color = self.combo_track_color.currentText()
            if 0 <= self.selected_index < len(self.media_items):
                self._update_photo_preview(self.media_items[self.selected_index])

        def _on_hud_changed(checked_list):
            self.hud_checked_items = checked_list
            if 0 <= self.selected_index < len(self.media_items):
                self._update_photo_preview(self.media_items[self.selected_index])

        def _on_zoom_changed(idx: int):
            self.local_zoom = self.combo_local_zoom.currentText()
            if 0 <= self.selected_index < len(self.media_items):
                self._update_photo_preview(self.media_items[self.selected_index])

        self.combo_map_style.currentIndexChanged.connect(_on_map_style_changed)
        self.combo_camera_mode.currentIndexChanged.connect(_on_camera_mode_changed)
        self.combo_preview_res.currentIndexChanged.connect(self._on_preview_res_changed)
        self.combo_track_color.currentIndexChanged.connect(_on_track_color_changed)
        self.combo_hud_panels.selection_changed.connect(_on_hud_changed)
        self.combo_local_zoom.currentIndexChanged.connect(_on_zoom_changed)

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

    def _populate_resolution_combo(self):
        """填入常用影片解析度選項並預設選取當前設定。"""
        self.combo_preview_res.blockSignals(True)
        self.combo_preview_res.clear()

        cur_w, cur_h = self.frame_width, self.frame_height
        gcd_val = math.gcd(cur_w, cur_h)
        aspect_ratio_str = f"{cur_w // gcd_val}:{cur_h // gcd_val}" if gcd_val > 0 else ""

        preset_list = [
            (f"當前專案設定 ({cur_w} × {cur_h}, {aspect_ratio_str})", cur_w, cur_h),
            ("1920 × 1080 (16:9 橫向 Full HD)", 1920, 1080),
            ("3840 × 2160 (16:9 橫向 4K UHD)", 3840, 2160),
            ("2560 × 1440 (16:9 橫向 2K QHD)", 2560, 1440),
            ("1280 × 720 (16:9 橫向 720p HD)", 1280, 720),
            ("1080 × 1920 (9:16 直向 Shorts / Reels / TikTok)", 1080, 1920),
            ("1080 × 1080 (1:1 正方形 Instagram)", 1080, 1080),
            ("1440 × 1080 (4:3 傳統標準比例)", 1440, 1080),
        ]

        seen_res = set()
        for idx, (label, w, h) in enumerate(preset_list):
            key = (w, h)
            if idx > 0 and key in seen_res:
                continue
            seen_res.add(key)
            self.combo_preview_res.addItem(label, (w, h))

        self.combo_preview_res.setCurrentIndex(0)
        self.combo_preview_res.blockSignals(False)

    def _on_preview_res_changed(self, idx: int):
        """切換模擬解析度時，立即重新計算比例並刷新畫面預覽。"""
        data = self.combo_preview_res.currentData()
        if data and isinstance(data, (tuple, list)) and len(data) == 2:
            self.frame_width = int(data[0])
            self.frame_height = int(data[1])
            self.result_frame_size = (self.frame_width, self.frame_height)
            if 0 <= self.selected_index < len(self.media_items):
                self._update_photo_preview(self.media_items[self.selected_index])

    def _update_photo_preview(self, item: MediaItem):
        """更新右側預覽圖片與 EXIF 拍攝詳細資訊，依當前動畫解析度進行精確等比例模擬渲染。"""
        # 1. 取得當前模擬解析度與視框尺寸
        fw = max(240, self.frame_width)
        fh = max(240, self.frame_height)
        aspect = fw / float(fh)

        # 取得右側容器可用寬度 (扣除邊界 Padding)
        parent_w = self.lbl_preview_image.parentWidget().width() if self.lbl_preview_image.parentWidget() else 380
        avail_w = max(260, parent_w - 24)

        # 根據解析度長寬比動態自適應計算預覽畫布尺寸與視框高度
        if aspect >= 1.2:
            # 橫向螢幕 (例如 16:9 橫向, 4:3 橫向)
            disp_w = min(avail_w, 400)
            disp_h = max(160, int(round(disp_w / aspect)))
        elif aspect <= 0.8:
            # 直向短影音 (例如 9:16 Shorts / Reels / TikTok)
            disp_h = 320
            disp_w = max(120, int(round(disp_h * aspect)))
        else:
            # 正方形或接近正方形 (例如 1:1 Instagram)
            disp_w = min(avail_w, 260)
            disp_h = max(160, int(round(disp_w / aspect)))

        box_h = disp_h + 12
        self.lbl_preview_image.setFixedHeight(box_h)

        scale_to_disp = disp_h / float(fh)
        ui_scale = min(fw, fh) / 1000.0

        # 2. 準備背景底圖 (依照所選的底圖風格非同步載入)
        item_key = f"{item.filename}::{self.map_style_key}"
        bg_pix = self._media_bg_cache.get(item_key, None)
        coords = self._get_item_coords(item)

        if bg_pix is None and coords is not None and item_key not in self._pending_bg_fetches:
            wx, wy = coords
            base_margin = float(getattr(config, "VIEW_MARGIN", 1600.0))
            if aspect >= 1.0:
                margin_x = base_margin * aspect
                margin_y = base_margin
            else:
                margin_x = base_margin
                margin_y = base_margin / aspect
            west = wx - margin_x
            east = wx + margin_x
            south = wy - margin_y
            north = wy + margin_y

            self._pending_bg_fetches.add(item_key)
            target_zoom = getattr(config, "LOCAL_MAP_ZOOM", 17)
            self.bg_worker.fetch_async(
                item_key, west, south, east, north,
                source=self.map_source,
                zoom=target_zoom,
            )

        # 3. 建立主畫布 QPixmap
        canvas = QPixmap(disp_w, disp_h)
        canvas.fill(Qt.transparent)

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        # 3.1 繪製主視訊畫面底圖背景
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

            # 劇院級半透明暗色遮罩 (使中央媒體卡片更加突出清晰，與實際渲染器一致)
            painter.fillRect(frame_rect, QColor(7, 11, 16, 125))
        else:
            painter.fillRect(frame_rect, QColor("#111827"))
            if item_key in self._pending_bg_fetches:
                painter.setFont(QFont("Segoe UI", 8))
                painter.setPen(QColor(148, 163, 184, 180))
                painter.drawText(frame_rect, Qt.AlignCenter, f"🗺️ 載入 [{self.map_style_label}] 底圖中…")

        painter.restore()

        # 外框線
        painter.setPen(QPen(QColor("#374151"), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(frame_rect, 6, 6)

        # 3.2 更新外側預覽規格標籤條 (將文字移至外側，保持預覽畫面乾淨)
        gcd_val = math.gcd(fw, fh)
        aspect_ratio_str = f"{fw // gcd_val}:{fh // gcd_val}" if gcd_val > 0 else ""
        res_tag = f"{aspect_ratio_str} ({fw}×{fh})"
        style_title = self.map_style_label or "底圖風格"
        if hasattr(self, "lbl_preview_info_tag"):
            cam_txt = getattr(self, "camera_mode", "North-Up")
            self.lbl_preview_info_tag.setText(
                f"🖥️ 規格: <b style='color: #38bdf8;'>{res_tag}</b> │ "
                f"🗺️ 底圖: <b style='color: #34d399;'>{style_title}</b> │ "
                f"🎥 視角: <b style='color: #f59e0b;'>{cam_txt}</b>"
            )

        # 2.3 載入並繪製媒體卡片 (依 renderer.py 規範：卡片上限為畫面的 65% 寬度與 60% 高度)
        max_card_w = max(20, int(disp_w * 0.65))
        max_card_h = max(20, int(disp_h * 0.60))
        raw_pix = self._load_item_pixmap(item)

        if raw_pix and not raw_pix.isNull():
            card_pix = raw_pix.scaled(max_card_w, max_card_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            cw, ch = card_pix.width(), card_pix.height()
            cx = (disp_w - cw) // 2
            cy = (disp_h - ch) // 2

            # 劇院級中央圓角與精美白邊框
            radius = max(3.0, min(cw, ch) * 0.05)
            border_w = max(1.2, min(cw, ch) * 0.008)

            path = QPainterPath()
            path.addRoundedRect(QRectF(cx, cy, cw, ch), radius, radius)
            painter.save()
            painter.setClipPath(path)
            painter.drawPixmap(cx, cy, card_pix)
            painter.restore()

            # 白邊框
            painter.setPen(QPen(QColor(255, 255, 255, 245), border_w))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(cx, cy, cw, ch), radius, radius)

            # 2.4 說明文字標籤條渲染 (高對比、純白字體 + 陰影 + 亮白框線)
            if item.caption:
                eff_sz = item.effective_caption_size
                actual_font_pt = max(10, int(round(float(eff_sz) * ui_scale)))
                disp_font_pt = max(9, int(round(actual_font_pt * scale_to_disp)))
                cap_font = QFont("Segoe UI", disp_font_pt, QFont.Bold)
                painter.setFont(cap_font)
                fm = painter.fontMetrics()

                txt = item.caption
                tb_w = fm.horizontalAdvance(txt)
                tb_h = fm.height()

                pad_x = max(8, int(round(26 * ui_scale * scale_to_disp)))
                pad_y = max(4, int(round(12 * ui_scale * scale_to_disp)))
                gap = max(4, int(round(16 * ui_scale * scale_to_disp)))

                cap_w = min(disp_w - 12, tb_w + 2 * pad_x)
                cap_h = tb_h + 2 * pad_y
                cap_x = (disp_w - cap_w) // 2
                cap_y = cy + ch + gap

                # 若文字標籤超出畫面底部，向上移至卡片內部下方
                if cap_y + cap_h > disp_h - 6:
                    cap_y = cy + ch - cap_h - 6

                cap_radius = max(4, int(round(16 * ui_scale * scale_to_disp)))

                # 繪製質感深海藍浮雕背景框 (帶 1.5px 亮白邊框)
                painter.setPen(QPen(QColor(255, 255, 255, 180), 1.5))
                painter.setBrush(QBrush(QColor(15, 23, 42, 240)))
                painter.drawRoundedRect(QRectF(cap_x, cap_y, cap_w, cap_h), cap_radius, cap_radius)

                # 繪製文字 (純亮白 + 微距陰影，確保 100% 清晰可見)
                painter.setBrush(Qt.NoBrush)
                elided_txt = fm.elidedText(txt, Qt.ElideRight, int(cap_w - 2 * pad_x))

                # 微距黑陰影
                painter.setPen(QPen(QColor(0, 0, 0, 220)))
                painter.drawText(QRectF(cap_x + 1, cap_y + 1, cap_w, cap_h), Qt.AlignCenter, elided_txt)

                # 純亮白文字
                painter.setPen(QPen(QColor(255, 255, 255, 255)))
                painter.drawText(QRectF(cap_x, cap_y, cap_w, cap_h), Qt.AlignCenter, elided_txt)


        # 3.3 繪製所選之資訊面板預覽 (HUD / 小地圖 / 高程剖面)
        checked_huds = getattr(self, "hud_checked_items", [])

        # 3.3.1 速度與里程 HUD (左上角)
        if "速度與里程 HUD" in checked_huds:
            hud_w = max(60, min(140, int(round(disp_w * 0.38))))
            hud_h = max(26, int(round(34 * scale_to_disp * (ui_scale / 1.0))))
            hud_rect = QRectF(10, 10, hud_w, hud_h)
            painter.save()
            painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
            painter.setBrush(QBrush(QColor(9, 13, 18, 200)))
            painter.drawRoundedRect(hud_rect, 6, 6)

            # 速度文字
            spd_val = f"{item.current_km * 3.6:.1f}" if item.current_km > 0 else "28.5"
            painter.setFont(QFont("Segoe UI", max(7, int(11 * scale_to_disp * ui_scale)), QFont.Bold))
            painter.setPen(QPen(QColor(255, 255, 255, 250)))
            painter.drawText(QRectF(hud_rect.x() + 6, hud_rect.y() + 2, hud_w - 12, hud_h * 0.55), Qt.AlignLeft | Qt.AlignVCenter, f"{spd_val} km/h")

            # 里程與標籤
            dist_val = f"{item.current_km:.1f} km" if item.current_km >= 0 else "0.0 km"
            painter.setFont(QFont("Segoe UI", max(6, int(8 * scale_to_disp * ui_scale))))
            painter.setPen(QPen(QColor(148, 163, 184, 230)))
            painter.drawText(QRectF(hud_rect.x() + 6, hud_rect.y() + hud_h * 0.5, hud_w - 12, hud_h * 0.45), Qt.AlignLeft | Qt.AlignVCenter, f"DST: {dist_val}")
            painter.restore()

        # 3.3.2 路線小地圖 (右上角)
        if "路線小地圖" in checked_huds:
            mini_w = max(50, min(95, int(round(disp_w * 0.28))))
            mini_h = max(34, min(65, int(round(disp_h * 0.22))))
            mini_rect = QRectF(disp_w - mini_w - 10, 10, mini_w, mini_h)
            painter.save()
            painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
            painter.setBrush(QBrush(QColor(9, 13, 18, 200)))
            painter.drawRoundedRect(mini_rect, 6, 6)

            # 小地圖標籤
            painter.setFont(QFont("Segoe UI", max(5, int(7 * scale_to_disp * ui_scale)), QFont.Bold))
            painter.setPen(QPen(QColor(148, 163, 184, 200)))
            painter.drawText(QRectF(mini_rect.x() + 5, mini_rect.y() + 3, mini_w - 10, 12), Qt.AlignLeft | Qt.AlignTop, "MINIMAP")

            # 繪製簡化路線
            if self.ride_data and len(self.ride_data.xs) > 1:
                xs, ys = self.ride_data.xs, self.ride_data.ys
                min_x, max_x = float(xs.min()), float(xs.max())
                min_y, max_y = float(ys.min()), float(ys.max())
                rw = max(max_x - min_x, 1.0)
                rh = max(max_y - min_y, 1.0)
                pad_m = 6
                mw_avail = mini_w - 2 * pad_m
                mh_avail = mini_h - 2 * pad_m - 8
                sc = min(mw_avail / rw, mh_avail / rh)
                cx_m = mini_rect.x() + pad_m + (mw_avail - rw * sc) / 2
                cy_m = mini_rect.y() + pad_m + 8 + (mh_avail - rh * sc) / 2

                # 軌跡折線
                pts = []
                step = max(1, len(xs) // 35)
                for k in range(0, len(xs), step):
                    px_m = cx_m + (xs[k] - min_x) * sc
                    py_m = cy_m + (max_y - ys[k]) * sc
                    pts.append(QPointF(px_m, py_m))
                if len(pts) >= 2:
                    poly = QPolygonF(pts)
                    painter.setPen(QPen(QColor(255, 255, 255, 80), 1.2))
                    painter.drawPolyline(poly)

                # 當前點位標記 (依 track_color 設定對應醒目顏色)
                dot_color = QColor(252, 76, 2)
                if "螢光綠" in getattr(self, "track_color", ""):
                    dot_color = QColor(34, 197, 94)
                elif "電光藍" in getattr(self, "track_color", ""):
                    dot_color = QColor(56, 189, 248)
                elif "熾熱紅" in getattr(self, "track_color", ""):
                    dot_color = QColor(239, 68, 68)

                if item.current_km >= 0 and len(self.ride_data.distances) > 0:
                    ix = float(np.interp(item.current_km, self.ride_data.distances, xs))
                    iy = float(np.interp(item.current_km, self.ride_data.distances, ys))
                    ipx = cx_m + (ix - min_x) * sc
                    ipy = cy_m + (max_y - iy) * sc
                    painter.setPen(QPen(QColor(255, 255, 255, 255), 1.5))
                    painter.setBrush(QBrush(dot_color))
                    painter.drawEllipse(QPointF(ipx, ipy), 3.0, 3.0)
            painter.restore()

        # 3.3.3 全景高程剖面 (底部)
        if "全景高程剖面" in checked_huds:
            elev_w = disp_w - 20
            elev_h = max(26, min(45, int(round(disp_h * 0.16))))
            elev_y = disp_h - elev_h - 10
            elev_rect = QRectF(10, elev_y, elev_w, elev_h)
            painter.save()
            painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
            painter.setBrush(QBrush(QColor(9, 13, 18, 200)))
            painter.drawRoundedRect(elev_rect, 6, 6)

            painter.setFont(QFont("Segoe UI", max(5, int(7 * scale_to_disp * ui_scale)), QFont.Bold))
            painter.setPen(QPen(QColor(148, 163, 184, 200)))
            painter.drawText(QRectF(elev_rect.x() + 6, elev_rect.y() + 3, elev_w - 12, 10), Qt.AlignLeft | Qt.AlignTop, "ELEVATION")

            if self.ride_data and len(self.ride_data.eles) > 1:
                dists = self.ride_data.distances
                eles = self.ride_data.eles
                d_min, d_max = float(dists.min()), max(float(dists.max()), float(dists.min()) + 0.001)
                e_min, e_max = float(eles.min()) - 5.0, float(eles.max()) + 5.0
                if e_max <= e_min: e_max = e_min + 10.0

                pad_e = 6
                ew_avail = elev_w - 2 * pad_e
                eh_avail = elev_h - 2 * pad_e - 6
                ex_base = elev_rect.x() + pad_e
                ey_base = elev_rect.y() + pad_e + 6

                step = max(1, len(dists) // 45)
                poly_pts = [QPointF(ex_base, ey_base + eh_avail)]
                for k in range(0, len(dists), step):
                    px_e = ex_base + (dists[k] - d_min) / (d_max - d_min) * ew_avail
                    py_e = ey_base + (e_max - eles[k]) / (e_max - e_min) * eh_avail
                    poly_pts.append(QPointF(px_e, py_e))
                poly_pts.append(QPointF(ex_base + ew_avail, ey_base + eh_avail))

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(252, 76, 2, 80)))
                painter.drawPolygon(QPolygonF(poly_pts))

                # 輪廓線
                painter.setPen(QPen(QColor(255, 255, 255, 140), 1.0))
                painter.setBrush(Qt.NoBrush)
                painter.drawPolyline(QPolygonF(poly_pts[1:-1]))

                # 當前位置垂直指標線與點
                if item.current_km >= 0 and d_max > d_min:
                    cur_d = min(max(item.current_km, d_min), d_max)
                    cur_e = float(np.interp(cur_d, dists, eles))
                    cur_px = ex_base + (cur_d - d_min) / (d_max - d_min) * ew_avail
                    cur_py = ey_base + (e_max - cur_e) / (e_max - e_min) * eh_avail

                    painter.setPen(QPen(QColor(255, 255, 255, 180), 1, Qt.DashLine))
                    painter.drawLine(QPointF(cur_px, ey_base), QPointF(cur_px, ey_base + eh_avail))

                    painter.setPen(QPen(QColor(255, 255, 255, 255), 1.2))
                    painter.setBrush(QBrush(QColor(56, 189, 248)))
                    painter.drawEllipse(QPointF(cur_px, cur_py), 2.5, 2.5)
            painter.restore()

            painter.end()
            self.lbl_preview_image.setPixmap(canvas)
        else:
            # 無縮圖狀態
            painter.setPen(QColor("#cbd5e0"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            msg = "🎬 影片檔案\n(點擊此處播放影片)" if item.media_type == "video" else "📷 無法載入照片縮圖"
            painter.drawText(frame_rect, Qt.AlignCenter, msg)
            painter.end()
            self.lbl_preview_image.setPixmap(canvas)

        if item.media_type == "video":
            self.lbl_preview_image.setToolTip("▶ 點擊使用系統預設播放器開啟影片原檔")
        else:
            self.lbl_preview_image.setToolTip("🔍 點擊使用系統預設相片檢視器開啟全螢幕原圖")

        # 3. 更新 EXIF 與拍攝資訊面板
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

        if item.media_type == "video":
            dur_prefix = f"長度: {item.duration_str} | " if item.duration_str != "--" else ""
            if dims:
                self.lbl_info_res.setText(f"{dur_prefix}{dims[0]} × {dims[1]} px ({size_str})")
            else:
                self.lbl_info_res.setText(f"{dur_prefix}影片 ({size_str})" if size_str else f"{dur_prefix}影片")
        else:
            if dims:
                self.lbl_info_res.setText(f"{dims[0]} × {dims[1]} px ({size_str})")
            else:
                self.lbl_info_res.setText(f"相片 ({size_str})" if size_str else "相片")

        is_manual = (item.manual_distance_km is not None and item.manual_distance_km >= 0)
        km = item.current_km
        if is_manual:
            self.lbl_info_match.setText(f"📍 {km:.2f} km (手動指定)")
            self.lbl_info_match.setStyleSheet("color: #ecc94b; font-weight: bold;")
        else:
            self.lbl_info_match.setText(f"📍 {km:.2f} km (自動匹配)")
            self.lbl_info_match.setStyleSheet("color: #63b3ed; font-weight: bold;")

    def _on_table_select(self):
        """表格選取項目變更時，連動更新右側預覽畫面與地圖軌跡聚焦位置。"""
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
        """在地圖畫布上點選媒體標記點時，連動選取表格對應列。"""
        if 0 <= idx < self.table.rowCount():
            self.table.selectRow(idx)

    def _open_full_media(self):
        """以作業系統預設照片檢視器或影片播放器開啟原檔。"""
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            p = Path(item.file_path).resolve()
            if p.is_file():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))

    def _recalculate_time_offset(self):
        """依據上方校正秒數，重新與 GPX 時間軸匹配點位。"""
        offset_sec = self.spin_media_offset.value()
        match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times, time_offset_sec=offset_sec)
        self._populate_tree()
        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])
        QMessageBox.information(self, "完成", f"已重新根據校正時間 {offset_sec}s 配對媒體位置！")

    def _reset_all(self):
        """重置所有手動設定與已排除項目。"""
        if QMessageBox.question(self, "確認重置", "確定要重置所有相片的手動里程、說明文字與已刪除的媒體項目嗎？") == QMessageBox.Yes:
            self.deleted_filenames.clear()
            if self.media_path and Path(self.media_path).exists():
                from gpx_renderer.core.media import scan_media_files
                self.media_items = scan_media_files(self.media_path, time_offset_sec=self.spin_media_offset.value())
                match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times, time_offset_sec=self.spin_media_offset.value())
            else:
                for item in self.media_items:
                    item.manual_distance_km = None
                    item.caption = ""
                    item.caption_size = None
            self.preview_widget.media_items = self.media_items
            self._populate_tree()
            if self.media_items:
                self.table.selectRow(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])

    def keyPressEvent(self, event):
        """攔截並忽略 Esc 快捷鍵，避免使用者編輯過程中因誤觸 Esc 而關閉視窗。"""
        if event.key() == Qt.Key_Escape:
            event.ignore()
            return
        super().keyPressEvent(event)
