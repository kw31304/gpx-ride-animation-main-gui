# -*- coding: utf-8 -*-
"""
PySide6 (Qt) 原生媒體管理與照片預覽/文字標籤對齊視窗 (QtMediaManagerDialog)。
包含動態路線向量預覽圖表 (QtRoutePreviewWidget)、Google Map 衛星/街道底圖載入、相片/影片即時縮圖預覽卡片、EXIF 拍攝資訊面板與文字標籤編輯器。
"""

from __future__ import annotations
import os
import math
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image, ImageOps
import contextily as cx

from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QUrl, QSize, QObject, QTimer
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap, QImage, QDesktopServices, QCursor, QPolygonF, QPainterPath
)
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QDoubleSpinBox, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QMessageBox, QSplitter, QFrame, QScrollArea,
    QSizePolicy, QCheckBox, QComboBox, QSlider, QFileDialog
)

from gpx_renderer.core.media import (
    MediaItem, match_media_to_ride, scan_media_files, load_media_thumbnail
)
from gpx_renderer.core.data import RideData
from gpx_renderer import config
from gpx_renderer.gui.media_dialog.map_worker import MapTileWorker, GOOGLE_STREETS_URL
from gpx_renderer.gui.media_dialog.widgets.clickable_preview import ClickablePreviewLabel
from gpx_renderer.gui.media_dialog.widgets.route_preview_widget import QtRoutePreviewWidget
from gpx_renderer.gui.video_trim_dialog import QtVideoTrimDialog



class QtMediaManagerDialog(QDialog):
    """PySide6 原生媒體管理與照片預覽/對齊對話框視窗。"""

    def __init__(
        self,
        media_items: List[MediaItem],
        ride_data: RideData,
        media_duration: float = 3.0,
        media_offset_sec: float = 0.0,
        media_path: str = "",
        default_caption_size: int = 22,
        frame_width: int = 1920,
        frame_height: int = 1080,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("路線媒體管理器與照片/影片標籤編輯器 (PySide6 Native)")
        self.resize(1300, 760)
        self.setMinimumSize(1080, 640)

        self.media_items = media_items
        self.ride_data = ride_data
        self.media_path = media_path
        self.default_caption_size = int(default_caption_size if default_caption_size > 0 else getattr(config, "MEDIA_CAPTION_FONT_SIZE", 22))
        self.frame_width = int(frame_width if frame_width > 0 else getattr(config, "FRAME_WIDTH", 1920))
        self.frame_height = int(frame_height if frame_height > 0 else getattr(config, "FRAME_HEIGHT", 1080))
        self.result_frame_size = (self.frame_width, self.frame_height)
        self.total_distance_km = max(0.1, float(ride_data.distances[-1])) if len(ride_data.distances) > 0 else 100.0
        self.selected_index = -1
        self.deleted_filenames: set[str] = set()
        self.result_overrides: Dict[str, dict] = {}
        self._pixmap_cache: Dict[str, Optional[QPixmap]] = {}
        self._raw_img_dims: Dict[str, tuple[int, int]] = {}

        # 初次載入自動配對 GPS / 時間
        match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times, time_offset_sec=media_offset_sec)

        self._init_ui()
        self.spin_photo_dur.setValue(media_duration if media_duration > 0 else 3.0)
        self.spin_default_caption_size.setValue(self.default_caption_size)
        self.spin_media_offset.setValue(media_offset_sec)
        self._populate_tree()

        # 開局自動選取第 1 筆項目展示預覽
        if self.media_items:
            self.table.selectRow(0)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 1. 頂部控制列
        top_group = QGroupBox(" 媒體播放與說明設定 ")
        top_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        top_layout = QVBoxLayout(top_group)
        top_layout.setContentsMargins(10, 8, 10, 8)
        top_layout.setSpacing(6)

        # 第 1 列：相機時間校正說明與照片提示
        row1 = QHBoxLayout()
        lbl_info = QLabel("💡 說明：相片預設停留 3.0 秒；影片預設保留原始片長（亦可透過「✂️ 裁剪」設定頭尾播放區間）。可自訂每張媒體說明文字與字級。")
        lbl_info.setStyleSheet("color: #a0aec0; font-size: 11px;")
        row1.addWidget(lbl_info)
        top_layout.addLayout(row1)

        # 第 2 列：相片預設秒數、說明文字預設大小、一鍵重設、秒數微調輸入與重新對齊按鈕
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("📷 相片預設停留："))
        self.spin_photo_dur = QDoubleSpinBox()
        self.spin_photo_dur.setRange(1.0, 30.0)
        self.spin_photo_dur.setSingleStep(0.5)
        self.spin_photo_dur.setValue(3.0)
        self.spin_photo_dur.setSuffix(" 秒")
        self.spin_photo_dur.valueChanged.connect(self._on_photo_default_changed)
        row2.addWidget(self.spin_photo_dur)

        row2.addSpacing(10)
        row2.addWidget(QLabel("🔤 說明預設字級："))
        self.spin_default_caption_size = QSpinBox()
        self.spin_default_caption_size.setRange(10, 72)
        self.spin_default_caption_size.setSingleStep(1)
        self.spin_default_caption_size.setValue(self.default_caption_size)
        self.spin_default_caption_size.setSuffix(" pt")
        self.spin_default_caption_size.setToolTip("設定說明文字之預設字級大小 (10~72 pt)")
        self.spin_default_caption_size.valueChanged.connect(self._on_default_caption_size_changed)
        row2.addWidget(self.spin_default_caption_size)

        btn_reset_defaults = QPushButton("⚡ 一鍵套用預設值 (停留/字級)")
        btn_reset_defaults.setToolTip("將所有照片設為預設停留秒數與預設說明字級，所有影片還原為原始片長")
        btn_reset_defaults.setCursor(QCursor(Qt.PointingHandCursor))
        btn_reset_defaults.clicked.connect(self._reset_all_durations_to_defaults)
        row2.addWidget(btn_reset_defaults)

        row2.addSpacing(16)
        row2.addWidget(QLabel("相機時間校正偏移："))
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

        lbl_hint = QLabel("💡 慢 1 分填 60s；快 1 分填 -60s")
        lbl_hint.setStyleSheet("color: #718096; font-size: 11px;")
        row2.addWidget(lbl_hint)
        row2.addStretch()
        top_layout.addLayout(row2)

        # 第 3 列：媒體統計與增加秒數摘要
        row3 = QHBoxLayout()
        self.lbl_stats_summary = QLabel("📊 媒體統計：共 0 項 | ⏱️ 停留總增加：+0.0 秒")
        self.lbl_stats_summary.setStyleSheet("color: #63b3ed; font-weight: bold; font-size: 11px;")
        row3.addWidget(self.lbl_stats_summary)
        row3.addStretch()
        top_layout.addLayout(row3)

        main_layout.addWidget(top_group, 0)

        # 2. 中間水平 Splitter (左側：清單+地圖上下排列 | 右側：照片預覽與編輯區)
        main_splitter = QSplitter(Qt.Horizontal)

        # ==========================================
        # 2.1 左側容器：垂直 Splitter (清單在上，路線地圖在下)
        # ==========================================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.left_vsplitter = QSplitter(Qt.Vertical)
        self.left_vsplitter.setChildrenCollapsible(False)

        # 2.1.1 上半部：媒體清單列表
        table_container = QWidget()
        table_vbox = QVBoxLayout(table_container)
        table_vbox.setContentsMargins(0, 0, 0, 4)
        table_vbox.setSpacing(4)

        table_header_layout = QHBoxLayout()
        self.lbl_table_header = QLabel("媒體清單 (共 0 項)")
        self.lbl_table_header.setFont(QFont("Segoe UI", 9, QFont.Bold))
        table_header_layout.addWidget(self.lbl_table_header)
        table_header_layout.addStretch()

        btn_add_files = QPushButton("➕ 新增照片/影片 (可多選)")
        btn_add_files.setToolTip("選取單張或多張照片/影片檔案加入清單")
        btn_add_files.setCursor(QCursor(Qt.PointingHandCursor))
        btn_add_files.clicked.connect(self._on_add_files)
        table_header_layout.addWidget(btn_add_files)

        btn_add_folder = QPushButton("📁 新增資料夾")
        btn_add_folder.setToolTip("選取包含照片/影片之資料夾加入清單")
        btn_add_folder.setCursor(QCursor(Qt.PointingHandCursor))
        btn_add_folder.clicked.connect(self._on_add_folder)
        table_header_layout.addWidget(btn_add_folder)

        table_vbox.addLayout(table_header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["檔名", "類型", "影片長度", "停留秒數", "拍攝時間", "匹配里程 (km)", "自訂說明", "操作"])
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.verticalHeader().setVisible(False)
        
        # 欄位寬度自適應設置：類型、長度、停留、時間、里程、操作依內容緊湊排版，檔名與自訂說明彈性伸展
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setMinimumSectionSize(50)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_table_select)
        self.table.itemChanged.connect(self._on_table_item_changed)
        self.table.cellDoubleClicked.connect(self._on_table_double_clicked)
        table_vbox.addWidget(self.table)

        self.left_vsplitter.addWidget(table_container)

        # 2.1.2 下半部：路線軌跡與 Google 街道圖預覽
        map_container = QWidget()
        map_vbox = QVBoxLayout(map_container)
        map_vbox.setContentsMargins(0, 4, 0, 0)
        map_vbox.setSpacing(4)

        map_toolbar = QHBoxLayout()
        lbl_map_header = QLabel("路線軌跡與 Google 街道圖預覽")
        lbl_map_header.setFont(QFont("Segoe UI", 9, QFont.Bold))
        map_toolbar.addWidget(lbl_map_header)

        map_toolbar.addStretch()

        btn_zoom_in = QPushButton("➕ 放大")
        btn_zoom_in.setToolTip("放大視角 (Canvas Zoom In)")
        btn_zoom_in.clicked.connect(lambda: self.preview_widget.zoom_in())
        map_toolbar.addWidget(btn_zoom_in)

        btn_zoom_out = QPushButton("➖ 縮小")
        btn_zoom_out.setToolTip("縮小視角 (Canvas Zoom Out)")
        btn_zoom_out.clicked.connect(lambda: self.preview_widget.zoom_out())
        map_toolbar.addWidget(btn_zoom_out)

        btn_reset_view = QPushButton("🔄 視野置中")
        btn_reset_view.setToolTip("重設視角至路線全景中央")
        btn_reset_view.clicked.connect(lambda: self.preview_widget.reset_view())
        map_toolbar.addWidget(btn_reset_view)

        map_vbox.addLayout(map_toolbar)

        self.preview_widget = QtRoutePreviewWidget(self.ride_data)
        self.preview_widget.media_items = self.media_items
        self.preview_widget.item_selected.connect(self._on_canvas_select_item)
        map_vbox.addWidget(self.preview_widget)

        lbl_map_hint = QLabel("💡 滑鼠滾輪縮放 / 拖曳平移 / 點擊橘色標記選取照片")
        lbl_map_hint.setStyleSheet("color: #718096; font-size: 11px;")
        lbl_map_hint.setAlignment(Qt.AlignCenter)
        map_vbox.addWidget(lbl_map_hint)

        self.left_vsplitter.addWidget(map_container)

        # 設定左側垂直 Splitter 上下比例與延展因子 (穩定版面高度避免刪除項目時震盪)
        self.left_vsplitter.setStretchFactor(0, 1)
        self.left_vsplitter.setStretchFactor(1, 1)
        self.left_vsplitter.setSizes([260, 320])
        left_layout.addWidget(self.left_vsplitter)

        main_splitter.addWidget(left_panel)

        # ==========================================
        # 2.2 右側容器：照片縮圖預覽卡片、EXIF 拍攝資訊與屬性編輯區
        # ==========================================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # 2.2.1 媒體照片預覽卡片 (依動畫長寬比與解析度同步模擬渲染)
        preview_group = QGroupBox(" 媒體畫面預覽 (動畫解析度同步模擬) ")
        preview_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        preview_vbox = QVBoxLayout(preview_group)
        preview_vbox.setContentsMargins(8, 8, 8, 8)
        preview_vbox.setSpacing(6)

        # 模擬解析度切換與同步列
        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("🎬 模擬解析度："))
        self.combo_preview_res = QComboBox()
        self.combo_preview_res.setToolTip("切換預覽的動畫長寬比例與解析度，即時檢視不同螢幕尺寸下的照片與文字排版")
        self._populate_resolution_combo()
        self.combo_preview_res.currentIndexChanged.connect(self._on_preview_res_changed)
        res_row.addWidget(self.combo_preview_res)
        preview_vbox.addLayout(res_row)

        # 畫面預覽容器 (高度依解析度長寬比動態自適應)
        self.lbl_preview_image = ClickablePreviewLabel()
        self.lbl_preview_image.setAlignment(Qt.AlignCenter)
        self.lbl_preview_image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.lbl_preview_image.setMinimumHeight(160)
        self.lbl_preview_image.setStyleSheet(
            "background-color: #0b0f14; border: 1px solid #2d3748; border-radius: 8px; color: #a0aec0;"
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

        # 2.2.2 拍攝與 EXIF 詳細資訊卡片
        info_group = QGroupBox(" 拍攝與 EXIF 資訊 ")
        info_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
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

        # 2.2.3 屬性編輯卡片 (即時自動儲存與雙向連動)
        edit_group = QGroupBox(" 編輯選取相片/影片屬性 ")
        edit_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        edit_layout = QGridLayout(edit_group)
        edit_layout.setContentsMargins(8, 8, 8, 8)
        edit_layout.setSpacing(6)

        # 停留展示秒數與影片裁剪按鈕
        edit_layout.addWidget(QLabel("⏱️ 停留展示秒數："), 0, 0)
        dur_h_layout = QHBoxLayout()
        self.spin_item_dur = QDoubleSpinBox()
        self.spin_item_dur.setRange(0.5, 300.0)
        self.spin_item_dur.setSingleStep(0.5)
        self.spin_item_dur.setDecimals(1)
        self.spin_item_dur.setSuffix(" 秒")
        self.spin_item_dur.valueChanged.connect(self._on_item_dur_changed)
        dur_h_layout.addWidget(self.spin_item_dur)

        self.btn_trim_video = QPushButton("✂️ 裁剪影片頭尾 / 播放預覽...")
        self.btn_trim_video.setToolTip("彈出專屬視窗，以滑桿調整影片播放起點與終點並即時預覽")
        self.btn_trim_video.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_trim_video.setStyleSheet("QPushButton { color: #63b3ed; font-weight: bold; }")
        self.btn_trim_video.clicked.connect(self._open_trim_dialog_for_selected)
        dur_h_layout.addWidget(self.btn_trim_video)
        edit_layout.addLayout(dur_h_layout, 0, 1)

        self.chk_manual_km = QCheckBox("啟用手動里程 (覆寫自動匹配)")
        self.chk_manual_km.toggled.connect(self._on_manual_km_toggled)
        edit_layout.addWidget(self.chk_manual_km, 1, 0, 1, 2)

        edit_layout.addWidget(QLabel("手動里程 (km)："), 2, 0)
        self.spin_manual_km = QDoubleSpinBox()
        self.spin_manual_km.setRange(0.0, self.total_distance_km)
        self.spin_manual_km.setSingleStep(0.1)
        self.spin_manual_km.setDecimals(2)
        self.spin_manual_km.setSuffix(f" / {self.total_distance_km:.1f} km")
        self.spin_manual_km.setEnabled(False)
        self.spin_manual_km.valueChanged.connect(self._on_manual_km_value_change)
        edit_layout.addWidget(self.spin_manual_km, 2, 1)

        edit_layout.addWidget(QLabel("路線位置滑桿："), 3, 0)
        self.slider_manual_km = QSlider(Qt.Horizontal)
        self.slider_manual_km.setRange(0, max(1, int(round(self.total_distance_km * 100))))
        self.slider_manual_km.setSingleStep(10)  # 0.1 km
        self.slider_manual_km.setPageStep(100)  # 1.0 km
        self.slider_manual_km.setEnabled(False)
        self.slider_manual_km.setCursor(QCursor(Qt.PointingHandCursor))
        self.slider_manual_km.valueChanged.connect(self._on_slider_km_value_change)
        edit_layout.addWidget(self.slider_manual_km, 3, 1)

        edit_layout.addWidget(QLabel("自訂說明文字："), 4, 0)
        self.line_caption = QLineEdit()
        self.line_caption.setPlaceholderText("例如：合歡山主峰登山口 3158m")
        self.line_caption.textChanged.connect(self._on_caption_text_changed)
        edit_layout.addWidget(self.line_caption, 4, 1)

        edit_layout.addWidget(QLabel("說明文字大小："), 5, 0)
        cap_size_h_layout = QHBoxLayout()
        self.spin_caption_size = QSpinBox()
        self.spin_caption_size.setRange(10, 72)
        self.spin_caption_size.setSingleStep(1)
        self.spin_caption_size.setValue(22)
        self.spin_caption_size.setSuffix(" pt")
        self.spin_caption_size.setToolTip("設定目前選取項目的說明文字字級大小 (10~72 pt)")
        self.spin_caption_size.valueChanged.connect(self._on_caption_size_changed)
        cap_size_h_layout.addWidget(self.spin_caption_size)

        btn_apply_cap_all = QPushButton("⚡ 套用字級至全部")
        btn_apply_cap_all.setToolTip("將目前的字級大小套用至清單中所有媒體項目")
        btn_apply_cap_all.setCursor(QCursor(Qt.PointingHandCursor))
        btn_apply_cap_all.clicked.connect(self._on_apply_caption_size_to_all)
        cap_size_h_layout.addWidget(btn_apply_cap_all)

        btn_reset_cap = QPushButton("恢復預設")
        btn_reset_cap.setToolTip("將目前選取項目的字級重設為頂部預設字級")
        btn_reset_cap.setCursor(QCursor(Qt.PointingHandCursor))
        btn_reset_cap.clicked.connect(self._on_reset_item_caption_size)
        cap_size_h_layout.addWidget(btn_reset_cap)

        edit_layout.addLayout(cap_size_h_layout, 5, 1)

        right_layout.addWidget(edit_group)
        right_layout.addStretch()

        scroll_right = QScrollArea()
        scroll_right.setWidgetResizable(True)
        scroll_right.setFrameShape(QFrame.NoFrame)
        scroll_right.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_right.setWidget(right_panel)
        main_splitter.addWidget(scroll_right)

        # 主水平分割器比例 (左側清單+地圖約 760px，右側約 440px)
        main_splitter.setSizes([760, 440])
        main_layout.addWidget(main_splitter)

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

    def _delete_media_item(self, item: MediaItem):
        """從清單中移除個別項目，並記錄至排除集合。"""
        res = QMessageBox.question(
            self,
            "確認移除",
            f"確定要從媒體清單中移除「{item.filename}」嗎？\n（此操作僅自本次清單排除，不會刪除硬碟原始檔案）",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if res != QMessageBox.Yes:
            return

        # 記錄為已排除
        self.deleted_filenames.add(item.filename)

        del_idx = self.media_items.index(item) if item in self.media_items else -1
        if del_idx >= 0:
            self.media_items.pop(del_idx)

        self.preview_widget.media_items = self.media_items

        if not self.media_items:
            self.selected_index = -1
            self.lbl_preview_image.setText("📷 清單已無媒體項目")
            self.lbl_preview_image.setPixmap(QPixmap())
            self.btn_view_full.setEnabled(False)
            self.lbl_info_filename.setText("-")
            self.lbl_info_time.setText("-")
            self.lbl_info_gps.setText("-")
            self.lbl_info_res.setText("-")
            self.lbl_info_match.setText("-")
            self.chk_manual_km.setChecked(False)
            self.spin_manual_km.setValue(0.0)
            self.slider_manual_km.setValue(0)
            self.line_caption.setText("")
            self.spin_caption_size.setValue(self.default_caption_size)
            self.preview_widget.selected_index = -1
            self.preview_widget.active_km = -1.0
            self._populate_tree()
        else:
            # 平滑單列移除，避免全表重建引發版面高度震盪
            saved_sizes = getattr(self, "left_vsplitter", None)
            sizes = saved_sizes.sizes() if saved_sizes else None
            self.table.blockSignals(True)
            self.table.setUpdatesEnabled(False)
            try:
                self.table.removeRow(del_idx)
                # 重新綁定後續列的刪除按鈕
                for r in range(del_idx, self.table.rowCount()):
                    r_item = self.media_items[r]
                    btn_del = self.table.cellWidget(r, 7)
                    if btn_del:
                        try:
                            btn_del.clicked.disconnect()
                        except Exception:
                            pass
                        btn_del.clicked.connect(lambda _, cur=r_item: self._delete_media_item(cur))
                self._update_stats_summary()
            finally:
                self.table.setUpdatesEnabled(True)
                self.table.blockSignals(False)
                if sizes and sum(sizes) > 0 and saved_sizes:
                    saved_sizes.setSizes(sizes)

            next_idx = min(max(0, del_idx), len(self.media_items) - 1)
            self.table.selectRow(next_idx)

            # 即時刷新右側媒體照片預覽、拍攝資訊與地圖視角
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
        """統計所有相片、影片與停留增加秒數。"""
        total_items = len(self.media_items)
        num_photos = sum(1 for it in self.media_items if it.media_type == "image")
        num_videos = sum(1 for it in self.media_items if it.media_type == "video")
        total_photo_sec = sum(it.effective_duration for it in self.media_items if it.media_type == "image")
        total_video_sec = sum(it.effective_duration for it in self.media_items if it.media_type == "video")
        total_media_sec = total_photo_sec + total_video_sec

        self.lbl_table_header.setText(f"媒體清單 (共 {total_items} 項：🎬 {num_videos} 部影片, 📷 {num_photos} 張相片)")
        self.lbl_stats_summary.setText(
            f"📊 媒體統計：共 {total_items} 項（🎬 {num_videos} 部影片 + 📷 {num_photos} 張相片） | "
            f"⏱️ 停留總增加：+{total_media_sec:.1f} 秒（影片增加 +{total_video_sec:.1f} 秒，相片增加 +{total_photo_sec:.1f} 秒）"
        )

    def _populate_tree(self):
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
                dur_str = item.duration_str if item.media_type == "video" else "--"
                trim_str = item.trim_summary_str

                item_fn = QTableWidgetItem(item.filename)
                item_fn.setToolTip(item.file_path)
                item_fn.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(i, 0, item_fn)

                item_type = QTableWidgetItem(type_label)
                item_type.setTextAlignment(Qt.AlignCenter)
                item_type.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(i, 1, item_type)

                item_dur = QTableWidgetItem(dur_str)
                item_dur.setTextAlignment(Qt.AlignCenter)
                item_dur.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(i, 2, item_dur)

                # 停留秒數欄位：支援雙擊修改或跳出影片裁剪視窗
                item_trim = QTableWidgetItem(trim_str)
                item_trim.setTextAlignment(Qt.AlignCenter)
                item_trim.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                if item.media_type == "video":
                    item_trim.setToolTip("雙擊可彈出影片裁剪視窗以滑桿調整播放區間")
                else:
                    item_trim.setToolTip("雙擊可直接輸入自訂停留秒數")
                self.table.setItem(i, 3, item_trim)

                item_ts = QTableWidgetItem(ts_str)
                item_ts.setTextAlignment(Qt.AlignCenter)
                item_ts.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(i, 4, item_ts)

                # 匹配里程欄位：支援雙擊直接手動輸入里程 (km)
                item_km = QTableWidgetItem(km_label)
                item_km.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_km.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                item_km.setToolTip("雙擊可直接輸入自訂手動里程 (km)")
                self.table.setItem(i, 5, item_km)

                # 自訂說明欄位：支援雙擊直接編輯文字
                item_cap = QTableWidgetItem(item.caption or "")
                item_cap.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                item_cap.setToolTip("雙擊可直接編輯說明文字")
                self.table.setItem(i, 6, item_cap)

                # 操作欄位：個別刪除按鈕
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
                btn_del.clicked.connect(lambda _, cur_item=item: self._delete_media_item(cur_item))
                self.table.setCellWidget(i, 7, btn_del)

            # 欄位內容自適應緊湊調整
            self.table.resizeColumnToContents(1)
            self.table.resizeColumnToContents(2)
            self.table.resizeColumnToContents(3)
            self.table.resizeColumnToContents(4)
            self.table.resizeColumnToContents(5)
            self.table.resizeColumnToContents(7)
        finally:
            self.table.setUpdatesEnabled(True)
            self.table.blockSignals(False)
            if sizes and sum(sizes) > 0 and saved_sizes:
                saved_sizes.setSizes(sizes)

        self.preview_widget.update()

    def _sync_table_dur_cell(self, row: int, item: MediaItem):
        """將 MediaItem 停留時長即時同步至表格第 3 欄 (停留秒數)。"""
        self.table.blockSignals(True)
        dur_item = self.table.item(row, 3)
        if dur_item:
            dur_item.setText(item.trim_summary_str)
        self.table.blockSignals(False)

    def _sync_table_km_cell(self, row: int, item: MediaItem):
        """將 MediaItem 當前里程即時同步至表格第 5 欄 (匹配里程)。"""
        self.table.blockSignals(True)
        km_item = self.table.item(row, 5)
        if km_item:
            km_label = f"{item.current_km:.2f} (手動)" if (item.manual_distance_km is not None and item.manual_distance_km >= 0) else f"{item.current_km:.2f}"
            km_item.setText(km_label)
        self.table.blockSignals(False)

    def _on_table_double_clicked(self, row: int, col: int):
        if not (0 <= row < len(self.media_items)):
            return
        item = self.media_items[row]
        if col == 3 and item.media_type == "video":
            self._open_trim_dialog_for_item(item, row)

    def _open_trim_dialog_for_selected(self):
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            if item.media_type == "video":
                self._open_trim_dialog_for_item(item, self.selected_index)

    def _open_trim_dialog_for_item(self, item: MediaItem, row: int):
        dlg = QtVideoTrimDialog(item, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._sync_table_dur_cell(row, item)
            self._update_stats_summary()
            if row == self.selected_index:
                self.spin_item_dur.blockSignals(True)
                self.spin_item_dur.setValue(item.effective_duration)
                self.spin_item_dur.blockSignals(False)
                self._update_photo_preview(item)

    def _on_photo_default_changed(self, val: float):
        self._update_stats_summary()

    def _on_default_caption_size_changed(self, val: int):
        self.default_caption_size = val
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            if item.caption_size is None:
                self.spin_caption_size.blockSignals(True)
                self.spin_caption_size.setValue(val)
                self.spin_caption_size.blockSignals(False)
                self._update_photo_preview(item)

    def _on_caption_size_changed(self, val: int):
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            item.caption_size = val
            self._update_photo_preview(item)

    def _on_apply_caption_size_to_all(self):
        val = self.spin_caption_size.value()
        for it in self.media_items:
            it.caption_size = val
        if 0 <= self.selected_index < len(self.media_items):
            self._update_photo_preview(self.media_items[self.selected_index])
        QMessageBox.information(self, "套用完成", f"已將所有媒體項目的說明文字大小設為 {val} pt！")

    def _on_reset_item_caption_size(self):
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            item.caption_size = None
            default_val = self.spin_default_caption_size.value()
            self.spin_caption_size.blockSignals(True)
            self.spin_caption_size.setValue(default_val)
            self.spin_caption_size.blockSignals(False)
            self._update_photo_preview(item)

    def _reset_all_durations_to_defaults(self):
        default_photo_dur = float(self.spin_photo_dur.value())
        default_cap_size = int(self.spin_default_caption_size.value())
        for item in self.media_items:
            item.caption_size = default_cap_size
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

    def _on_item_dur_changed(self, val: float):
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            item.popup_duration = round(val, 2)
            self._sync_table_dur_cell(self.selected_index, item)
            self._update_stats_summary()

    def _on_table_item_changed(self, table_item: QTableWidgetItem):
        """處理表格內直接編輯停留秒數、里程或說明的事件，即時自動更新並連動右側編輯區與地圖。"""
        if not table_item or self.table.signalsBlocked():
            return
        row = table_item.row()
        col = table_item.column()
        if not (0 <= row < len(self.media_items)):
            return

        item = self.media_items[row]
        if col == 3:
            # 1. 編輯停留秒數
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
                self.spin_item_dur.blockSignals(True)
                self.spin_item_dur.setValue(item.effective_duration)
                self.spin_item_dur.blockSignals(False)

        elif col == 5:
            # 2. 編輯里程欄位
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
                if not txt or txt == "--":
                    item.manual_distance_km = None

            # 規範化儲存格顯示文字
            self._sync_table_km_cell(row, item)

            # 若為當前選取項，即時同步右側控制項與地圖
            if row == self.selected_index:
                self._update_photo_preview(item)
                self.preview_widget.active_km = item.current_km
                self.preview_widget.focus_active()
            self.preview_widget.update()

        elif col == 6:
            # 3. 編輯說明欄位
            item.caption = table_item.text().strip()
            if row == self.selected_index:
                self.line_caption.blockSignals(True)
                self.line_caption.setText(item.caption)
                self.line_caption.blockSignals(False)

    def _on_caption_text_changed(self, text: str):
        """右側說明輸入框內容變更時，即時自動儲存並同步至表格第 6 欄與即時縮圖預覽。"""
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            item.caption = text.strip()
            self.table.blockSignals(True)
            cap_item = self.table.item(self.selected_index, 6)
            if cap_item:
                cap_item.setText(item.caption)
            self.table.blockSignals(False)
            self._update_photo_preview(item)

    def _on_manual_km_toggled(self, checked: bool):
        self.spin_manual_km.setEnabled(checked)
        self.slider_manual_km.setEnabled(checked)
        if 0 <= self.selected_index < len(self.media_items):
            item = self.media_items[self.selected_index]
            if checked:
                item.manual_distance_km = round(self.spin_manual_km.value(), 2)
            else:
                item.manual_distance_km = None

            self._sync_table_km_cell(self.selected_index, item)

            if checked:
                self.lbl_info_match.setText(f"📍 {item.current_km:.2f} km (手動指定)")
                self.lbl_info_match.setStyleSheet("color: #ecc94b; font-weight: bold;")
            else:
                self.lbl_info_match.setText(f"📍 {item.current_km:.2f} km (自動匹配)")
                self.lbl_info_match.setStyleSheet("color: #63b3ed; font-weight: bold;")

            self.preview_widget.active_km = item.current_km
            self.preview_widget.focus_active()
            self.preview_widget.update()

    def _on_manual_km_value_change(self, val: float):
        if 0 <= self.selected_index < len(self.media_items):
            self.slider_manual_km.blockSignals(True)
            self.slider_manual_km.setValue(int(round(val * 100)))
            self.slider_manual_km.blockSignals(False)

            if self.chk_manual_km.isChecked():
                item = self.media_items[self.selected_index]
                item.manual_distance_km = round(val, 2)
                self._sync_table_km_cell(self.selected_index, item)

                self.preview_widget.active_km = float(val)
                self.preview_widget.focus_active()
                self.preview_widget.update()
                self.lbl_info_match.setText(f"📍 {val:.2f} km (手動指定)")
                self.lbl_info_match.setStyleSheet("color: #ecc94b; font-weight: bold;")

    def _on_slider_km_value_change(self, int_val: int):
        val = int_val / 100.0
        if 0 <= self.selected_index < len(self.media_items):
            self.spin_manual_km.blockSignals(True)
            self.spin_manual_km.setValue(val)
            self.spin_manual_km.blockSignals(False)

            if self.chk_manual_km.isChecked():
                item = self.media_items[self.selected_index]
                item.manual_distance_km = round(val, 2)
                self._sync_table_km_cell(self.selected_index, item)

                self.preview_widget.active_km = float(val)
                self.preview_widget.focus_active()
                self.preview_widget.update()
                self.lbl_info_match.setText(f"📍 {val:.2f} km (手動指定)")
                self.lbl_info_match.setStyleSheet("color: #ecc94b; font-weight: bold;")

    def _on_save_and_apply(self):
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
        self.accept()

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

        # 2. 建立主畫布 QPixmap
        canvas = QPixmap(disp_w, disp_h)
        canvas.fill(Qt.transparent)

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        # 2.1 繪製主視訊畫面底色與外框 (深石板藍/黑底色 + 明確邊框)
        frame_rect = QRectF(0, 0, disp_w, disp_h)
        painter.setPen(QPen(QColor("#374151"), 1.5))
        painter.setBrush(QBrush(QColor("#111827")))
        painter.drawRoundedRect(frame_rect, 6, 6)

        # 2.2 繪製角落長寬比標籤 (例如 16:9 1920×1080)
        gcd_val = math.gcd(fw, fh)
        aspect_ratio_str = f"{fw // gcd_val}:{fh // gcd_val}" if gcd_val > 0 else ""
        res_tag = f"{aspect_ratio_str} ({fw}×{fh})"
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.setPen(QColor(156, 163, 175, 180))
        painter.drawText(QRectF(6, 4, disp_w - 12, 16), Qt.AlignRight | Qt.AlignTop, res_tag)

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

            painter.end()
            self.lbl_preview_image.setPixmap(canvas)
            self.btn_view_full.setEnabled(True)
        else:
            # 無縮圖狀態
            painter.setPen(QColor("#cbd5e0"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            msg = "🎬 影片檔案\n(點擊下方按鈕播放)" if item.media_type == "video" else "📷 無法載入照片縮圖"
            painter.drawText(frame_rect, Qt.AlignCenter, msg)
            painter.end()
            self.lbl_preview_image.setPixmap(canvas)
            self.btn_view_full.setEnabled(Path(item.file_path).is_file())

        if item.media_type == "video":
            self.btn_view_full.setText("▶ 播放/檢視完整影片")
            self.btn_view_full.setToolTip("使用系統預設播放器開啟影片原檔")
        else:
            self.btn_view_full.setText("🔍 檢視全螢幕原圖")
            self.btn_view_full.setToolTip("使用系統預設相片檢視器開啟原檔")

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

        # 4. 更新屬性編輯區
        self.spin_item_dur.blockSignals(True)
        self.spin_item_dur.setValue(item.effective_duration)
        self.spin_item_dur.blockSignals(False)

        if item.media_type == "video":
            self.btn_trim_video.setVisible(True)
            self.btn_trim_video.setEnabled(True)
        else:
            self.btn_trim_video.setVisible(False)
            self.btn_trim_video.setEnabled(False)

        self.chk_manual_km.blockSignals(True)
        self.spin_manual_km.blockSignals(True)
        self.slider_manual_km.blockSignals(True)
        self.line_caption.blockSignals(True)
        self.spin_caption_size.blockSignals(True)

        self.chk_manual_km.setChecked(is_manual)
        self.spin_manual_km.setEnabled(is_manual)
        self.slider_manual_km.setEnabled(is_manual)
        self.spin_manual_km.setValue(km)
        self.slider_manual_km.setValue(int(round(km * 100)))
        self.line_caption.setText(item.caption or "")
        self.spin_caption_size.setValue(item.effective_caption_size)

        self.chk_manual_km.blockSignals(False)
        self.spin_manual_km.blockSignals(False)
        self.slider_manual_km.blockSignals(False)
        self.line_caption.blockSignals(False)
        self.spin_caption_size.blockSignals(False)

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

    def _reset_all(self):
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
