# -*- coding: utf-8 -*-
"""
PySide6 (Qt) 原生 GUI 主應用程式視窗控制器 (MainWindow)。
直接讀取 ui_main_window (Ui_MainWindow)，並與 GPX Ride Renderer 的 subprocess 渲染核心完全對接。
"""

from __future__ import annotations
import os
import sys
import json
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

# 確保直接執行本模組時，專案根目錄能正確加入 sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer, QSettings, QSize
from PySide6.QtGui import QIcon, QActionGroup
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget, QProgressBar,
    QCheckBox
)

from gpx_renderer import config, __version__
from gpx_renderer.gui.main_window.ui_main_window import Ui_MainWindow
from gpx_renderer.gui.main_window.main_workers import (
    SubprocessReaderThread, GpxDistanceThread, CacheSizeWorkerThread
)
from gpx_renderer.utils import _self_subprocess_command, application_dir
from gpx_renderer.core.data import quick_gpx_distance_km, auto_duration_seconds, format_seconds_human
from gpx_renderer.core.parallel import _default_benchmark_candidates
from gpx_renderer.core.cache_manager import CacheManager
from gpx_renderer.gui.widgets.checkable_combo_box import CheckableComboBox


def _get_icon(name: str) -> QIcon:
    """載入 gui/icons 目錄中的 SVG 向量圖示"""
    icon_p = Path(__file__).resolve().parent.parent / "icons" / f"{name}.svg"
    if icon_p.is_file():
        return QIcon(str(icon_p))
    return QIcon()


RESOLUTION_PRESETS = [
    ("1080p 直式 (1080×1920)", 1080, 1920),
    ("1080p 橫式 (1920×1080)", 1920, 1080),
    ("1080p 正方形 (1080×1080)", 1080, 1080),
    ("1440p 正方形 (1440×1440)", 1440, 1440),
    ("2K 橫式 (2560×1440)", 2560, 1440),
    ("720p 直式 (720×1280)", 720, 1280),
    ("720p 橫式 (1280×720)", 1280, 720),
    ("IG 貼文 (1080×1350)", 1080, 1350),
    ("極速測試 (640×360)", 640, 360),
    ("自訂解析度...", None, None),
]

CAMERA_MODE_LABELS = {
    "North-Up": "正北朝上 (North-Up)",
    "Heading-Up": "跟隨行進 (Heading-Up)",
    "3D-Terrain": "3D 真地形 (3D-Terrain)",
}


class _ValueProxy:
    """Proxy 物件，用以相容舊版直接存取 spin_workers, combo_bitrate 等已遷移至選單的元件。"""
    class _Signal:
        def connect(self, *a, **k): pass
        def disconnect(self, *a, **k): pass

    def __init__(self, getter, setter=None):
        self._getter = getter
        self._setter = setter
        self.valueChanged = self._Signal()
        self.currentIndexChanged = self._Signal()
        self.toggled = self._Signal()

    def value(self):
        return self._getter()

    def setValue(self, v):
        if self._setter: self._setter(v)

    def currentText(self):
        return str(self._getter())

    def setCurrentText(self, v):
        if self._setter: self._setter(v)

    def isChecked(self):
        return bool(self._getter())

    def setChecked(self, v):
        if self._setter: self._setter(v)

    def clear(self): pass
    def addItems(self, items): pass
    def setRange(self, *a): pass
    def setSingleStep(self, *a): pass
    def setToolTip(self, *a): pass
    def selectAll(self): pass
    def setFocus(self): pass
    def blockSignals(self, b): pass


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(f"GPX Ride Renderer V{__version__}")

        # 核心渲染與編碼屬性 (原進階元件改至選單列管理)
        self.nvenc_preset = str(config.NVENC_PRESET)
        self.nvenc_bitrate = str(config.NVENC_BITRATE)
        self.render_workers = int(config.RENDER_WORKERS)
        self.chunks_per_worker = int(config.CHUNKS_PER_WORKER)
        self.map_connections = int(config.MAP_CONNECTIONS)
        self.custom_width = int(config.FRAME_WIDTH)
        self.custom_height = int(config.FRAME_HEIGHT)
        self.enable_basemap = bool(config.ENABLE_BASEMAP)
        self.parallel_render = bool(config.PARALLEL_RENDER)
        self.enable_media = bool(config.ENABLE_MEDIA)
        self.preview_mode = bool(config.PREVIEW_MODE)

        # 建立 HUD 相容勾選物件
        self.chk_show_speed = QCheckBox()
        self.chk_show_minimap = QCheckBox()
        self.chk_show_elevation = QCheckBox()
        self.chk_show_speed.setChecked(getattr(config, "SHOW_SPEED_HUD", True))
        self.chk_show_minimap.setChecked(getattr(config, "SHOW_MINIMAP", True))
        self.chk_show_elevation.setChecked(getattr(config, "SHOW_ELEVATION", True))

        # 建立 Proxy 相容物件，確保既有存取完全無痛
        self.spin_workers = _ValueProxy(lambda: self.render_workers, self._set_workers)
        self.spin_chunks = _ValueProxy(lambda: self.chunks_per_worker, lambda v: setattr(self, 'chunks_per_worker', int(v)))
        self.spin_tile_connections = _ValueProxy(lambda: self.map_connections, self._set_connections)
        self.combo_preset = _ValueProxy(lambda: self.nvenc_preset, self._set_preset)
        self.combo_bitrate = _ValueProxy(lambda: self.nvenc_bitrate, self._set_bitrate)
        self.spin_width = _ValueProxy(lambda: self.custom_width, lambda v: setattr(self, 'custom_width', int(v)))
        self.spin_height = _ValueProxy(lambda: self.custom_height, lambda v: setattr(self, 'custom_height', int(v)))
        self.chk_basemap_2 = _ValueProxy(lambda: self.enable_basemap, self._set_basemap)
        self.chk_parallel_2 = _ValueProxy(lambda: self.parallel_render, self._set_parallel)
        self.chk_enable_media_2 = _ValueProxy(lambda: self.enable_media, self._set_enable_media)
        self.chk_preview = _ValueProxy(lambda: self.preview_mode, self._set_preview_mode)

        self.state = {
            "proc": None, "proc_mode": None, "config_path": None,
            "gpx_distance_km": None, "gpx_distance_path": None,
            "benchmark_result": None, "media_overrides_json": "{}",
            "reader_thread": None, "log_file": None, "log_path": None,
        }

        self.worker_bars: List[QProgressBar] = [
            getattr(self, f"progressBar_worker_{i}", None) for i in range(1, 7)
        ]
        self.worker_bars = [b for b in self.worker_bars if b is not None]

        self.worker_status_labels = [
            getattr(self, f"lbl_worker_status_{i}", None) for i in range(1, 7)
        ]
        self.worker_status_labels = [l for l in self.worker_status_labels if l is not None]

        # 讀取並還原上次使用者偏好的快取模式 (Session 暫存 或 永久保留)
        self.settings = QSettings("GPXRideRenderer", "GPXRideRenderer")
        saved_cache_mode = self.settings.value("map_cache_mode", "session")
        if str(saved_cache_mode).lower() in ("session", "persistent"):
            config.MAP_CACHE_MODE = str(saved_cache_mode).lower()

        CacheManager.init_cache_system()

        # 媒體摘要快取 (避免各 UI 元件事件觸發重複磁碟掃描)
        self._cached_media_path: str = ""
        self._cached_media_summary: Optional[tuple] = None

        self._init_combos()
        self._init_default_values()
        self._init_toolbar_and_menus()
        self._connect_signals()

        # 初始化路線媒體分頁控制器
        from gpx_renderer.gui.main_window.components.media_tab_controller import MediaTabController
        self.media_tab = MediaTabController(self)
        if hasattr(self, "lineEdit_media") and self.lineEdit_media.text().strip():
            self.media_tab.load_media_from_paths(self.lineEdit_media.text().strip())

        self._update_dashboard_summary(force_media_rescan=True)

        # 預設選取「一般設定」分頁 (Tab Index 0)
        if hasattr(self, "tabWidget"):
            self.tabWidget.setCurrentIndex(0)

        # 快取大小背景計算執行緒
        self._cache_size_thread: Optional[CacheSizeWorkerThread] = None

        # 開局自動非同步刷新 GPX 距離與快取容量
        QTimer.singleShot(200, self.refresh_gpx_distance)
        QTimer.singleShot(400, self.refresh_cache_size_display)

        # 每 30 秒週期性背景自動刷新快取容量顯示 (完全非同步，0 阻斷)
        self.cache_timer = QTimer(self)
        self.cache_timer.setInterval(30000)
        self.cache_timer.timeout.connect(self.refresh_cache_size_display)
        self.cache_timer.start()

        # 渲染計時器 (計算從開始渲染至完成所經過的時間)
        self._render_start_time: Optional[float] = None
        self._render_timer = QTimer(self)
        self._render_timer.setInterval(500)
        self._render_timer.timeout.connect(self._update_render_timer)

    @staticmethod
    def _format_elapsed_str(seconds: float) -> str:
        total = max(0, int(seconds))
        hrs = total // 3600
        mins = (total % 3600) // 60
        secs = total % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"

    def _update_render_timer(self):
        if self._render_start_time is not None and hasattr(self, "label_eta_elapsed"):
            elapsed = time.time() - self._render_start_time
            self.label_eta_elapsed.setText(f"渲染計時: {self._format_elapsed_str(elapsed)}")

    def center_on_screen(self):
        """將視窗定位至螢幕工作區域中央"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            win_geo = self.frameGeometry()
            win_geo.moveCenter(screen_geo.center())
            self.move(win_geo.topLeft())

    # ---------- 渲染與編碼設定即時同步控制 ----------
    def _set_preset(self, val: str):
        self.nvenc_preset = str(val).strip()
        config.NVENC_PRESET = self.nvenc_preset
        act = getattr(self, f"action_preset_{self.nvenc_preset}", None)
        if act:
            act.blockSignals(True)
            act.setChecked(True)
            act.blockSignals(False)
        self._update_dashboard_summary()

    def _set_bitrate(self, val: str):
        self.nvenc_bitrate = str(val).strip()
        config.NVENC_BITRATE = self.nvenc_bitrate
        act = getattr(self, f"action_bitrate_{self.nvenc_bitrate}", None)
        if act:
            act.blockSignals(True)
            act.setChecked(True)
            act.blockSignals(False)
        self._update_dashboard_summary()

    def _set_workers(self, val: int):
        self.render_workers = int(val)
        config.RENDER_WORKERS = self.render_workers
        act = getattr(self, f"action_workers_{self.render_workers}", None)
        if act:
            act.blockSignals(True)
            act.setChecked(True)
            act.blockSignals(False)
        self._update_dashboard_summary()

    def _set_connections(self, val: int):
        self.map_connections = int(val)
        config.MAP_CONNECTIONS = self.map_connections
        act = getattr(self, f"action_tile_conn_{self.map_connections}", None)
        if act:
            act.blockSignals(True)
            act.setChecked(True)
            act.blockSignals(False)
        self._update_dashboard_summary()

    def _set_basemap(self, val: bool):
        self.enable_basemap = bool(val)
        config.ENABLE_BASEMAP = self.enable_basemap
        if hasattr(self, "action_basemap"):
            self.action_basemap.blockSignals(True)
            self.action_basemap.setChecked(self.enable_basemap)
            self.action_basemap.blockSignals(False)
        self._update_dashboard_summary()
        if hasattr(self, "media_tab"):
            self.media_tab.refresh_preview()

    def _set_parallel(self, val: bool):
        self.parallel_render = bool(val)
        config.PARALLEL_RENDER = self.parallel_render
        if hasattr(self, "action_parallel"):
            self.action_parallel.blockSignals(True)
            self.action_parallel.setChecked(self.parallel_render)
            self.action_parallel.blockSignals(False)
        self._update_dashboard_summary()

    def _set_enable_media(self, val: bool):
        self.enable_media = bool(val)
        config.ENABLE_MEDIA = self.enable_media
        if hasattr(self, "action_enable_media"):
            self.action_enable_media.blockSignals(True)
            self.action_enable_media.setChecked(self.enable_media)
            self.action_enable_media.blockSignals(False)
        self._update_dashboard_summary()

    def _set_preview_mode(self, val: bool):
        self.preview_mode = bool(val)
        config.PREVIEW_MODE = self.preview_mode
        if hasattr(self, "action_preview"):
            self.action_preview.blockSignals(True)
            self.action_preview.setChecked(self.preview_mode)
            self.action_preview.blockSignals(False)
        self._update_dashboard_summary()

    def open_custom_resolution_dialog(self):
        """彈出精簡自訂解析度輸入對話框"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("自訂畫面解析度")
        dlg.resize(320, 160)
        layout = QVBoxLayout(dlg)

        h_w = QHBoxLayout()
        h_w.addWidget(QLabel("寬度 (Width):"))
        sp_w = QSpinBox()
        sp_w.setRange(240, 7680)
        sp_w.setSingleStep(2)
        sp_w.setValue(self.custom_width)
        sp_w.setSuffix(" px")
        h_w.addWidget(sp_w)
        layout.addLayout(h_w)

        h_h = QHBoxLayout()
        h_h.addWidget(QLabel("高度 (Height):"))
        sp_h = QSpinBox()
        sp_h.setRange(240, 7680)
        sp_h.setSingleStep(2)
        sp_h.setValue(self.custom_height)
        sp_h.setSuffix(" px")
        h_h.addWidget(sp_h)
        layout.addLayout(h_h)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dlg)
        bb.button(QDialogButtonBox.Ok).setText("確定")
        bb.button(QDialogButtonBox.Cancel).setText("取消")
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        layout.addWidget(bb)

        if dlg.exec() == QDialog.Accepted:
            self.custom_width = sp_w.value()
            self.custom_height = sp_h.value()
            config.FRAME_WIDTH = self.custom_width
            config.FRAME_HEIGHT = self.custom_height
            if "自訂" in self.combo_resolution_2.currentText():
                self._update_dashboard_summary()
                if hasattr(self, "media_tab"):
                    self.media_tab.refresh_preview()

    def open_advanced_settings_dialog(self):
        """彈出進階渲染參數綜合設定對話框"""
        from gpx_renderer.gui.main_window.components.advanced_settings_dialog import AdvancedSettingsDialog
        is_benchmarking = self.state.get("proc_mode") == "benchmark" and self.state.get("proc") is not None
        dlg = AdvancedSettingsDialog(
            parent=self,
            custom_width=self.custom_width,
            custom_height=self.custom_height,
            workers=self.render_workers,
            chunks=self.chunks_per_worker,
            connections=self.map_connections,
            preset=self.nvenc_preset,
            bitrate=self.nvenc_bitrate,
            basemap=self.enable_basemap,
            parallel=self.parallel_render,
            enable_media=self.enable_media,
            preview_mode=self.preview_mode,
            cache_mode=getattr(config, "MAP_CACHE_MODE", "session"),
            benchmark_result=self.state.get("benchmark_result"),
            is_benchmarking=is_benchmarking,
        )
        self._advanced_dialog = dlg
        try:
            if dlg.exec() == QDialog.Accepted:
                vals = dlg.get_values()
                self.custom_width = vals["custom_width"]
                self.custom_height = vals["custom_height"]
                config.FRAME_WIDTH = self.custom_width
                config.FRAME_HEIGHT = self.custom_height
                self._set_workers(vals["workers"])
                self.chunks_per_worker = vals["chunks"]
                config.CHUNKS_PER_WORKER = self.chunks_per_worker
                self._set_connections(vals["connections"])
                self._set_preset(vals["preset"])
                self._set_bitrate(vals["bitrate"])
                self._set_basemap(vals["basemap"])
                self._set_parallel(vals["parallel"])
                self._set_enable_media(vals["enable_media"])
                self._set_preview_mode(vals["preview_mode"])
                self._set_cache_mode(vals.get("cache_mode", "session"))
                self._update_dashboard_summary()
                if hasattr(self, "media_tab"):
                    self.media_tab.refresh_preview()
        finally:
            if getattr(self, "_advanced_dialog", None) is dlg:
                self._advanced_dialog = None

    def set_status_message(self, msg: str):
        if hasattr(self, "lbl_main_status"):
            self.lbl_main_status.setText(msg)
        if hasattr(self, "groupBox_main_progress"):
            self.groupBox_main_progress.setTitle(f"主進度與整體 ETA - {msg}")
        self.statusBar().showMessage(msg)

    def _update_dashboard_summary(self, force_media_rescan: bool = False):
        try:
            w, h = self.get_current_resolution()
            fps = self.spin_fps.value()
            dur_text = self.lineEdit_duration.text().strip()
            base_dur = float(dur_text) if dur_text else 30.0
            zoom_out_dur = float(self.lineEdit_zoomout.text().strip()) if hasattr(self, "lineEdit_zoomout") and self.lineEdit_zoomout.text().strip() else 0.0
            end_hold_dur = float(self.lineEdit_end_hold.text().strip()) if hasattr(self, "lineEdit_end_hold") and self.lineEdit_end_hold.text().strip() else 0.0

            media_item_count = 0
            media_video_count = 0
            media_photo_count = 0
            media_added_sec = 0.0
            video_added_sec = 0.0
            photo_added_sec = 0.0

            has_media_enabled = self.chk_enable_media_2.isChecked() and bool(self.lineEdit_media.text().strip())
            if has_media_enabled:
                media_p = self.lineEdit_media.text().strip()
                if force_media_rescan or media_p != getattr(self, "_cached_media_path", "") or self._cached_media_summary is None:
                    try:
                        from gpx_renderer.core.media import scan_media_files
                        if self.state.get("media_overrides_json"):
                            config.MEDIA_OVERRIDES_JSON = self.state["media_overrides_json"]
                        if self.state.get("media_popup_duration"):
                            config.MEDIA_POPUP_DURATION = float(self.state["media_popup_duration"])
                        offset_sec = float(self.state.get("media_time_offset_sec") or getattr(config, "MEDIA_TIME_OFFSET_SEC", 0.0))
                        scanned = scan_media_files(media_p, time_offset_sec=offset_sec)
                        media_item_count = len(scanned)
                        media_video_count = sum(1 for it in scanned if it.media_type == "video")
                        media_photo_count = sum(1 for it in scanned if it.media_type == "image")
                        video_added_sec = sum(it.effective_duration for it in scanned if it.media_type == "video")
                        photo_added_sec = sum(it.effective_duration for it in scanned if it.media_type == "image")
                        media_added_sec = video_added_sec + photo_added_sec
                        self._cached_media_path = media_p
                        self._cached_media_summary = (media_item_count, media_video_count, media_photo_count, media_added_sec, video_added_sec, photo_added_sec)
                    except Exception:
                        self._cached_media_summary = (0, 0, 0, 0.0, 0.0, 0.0)
                else:
                    media_item_count, media_video_count, media_photo_count, media_added_sec, video_added_sec, photo_added_sec = self._cached_media_summary

            total_anim_sec = base_dur + media_added_sec + zoom_out_dur + end_hold_dur
            is_auto = self.chk_auto_duration.isChecked()
            dist = self.state.get("gpx_distance_km")
            has_gpx = dist is not None and dist > 0

            # 1. 畫面規格與時長
            if not has_gpx:
                dur_html = "<span style='color: #f59e0b; font-weight: bold;'>請先匯入 GPX</span>"
            else:
                human_total = format_seconds_human(total_anim_sec)
                if media_item_count > 0:
                    dur_breakdown = f"(主動畫 {base_dur:.1f}s + 媒體停頓 {media_added_sec:.1f}s)"
                else:
                    mode_str = "自動計算" if is_auto else "手動指定"
                    dur_breakdown = f"({mode_str} {base_dur:.1f}s)"

                dur_html = (
                    f"<b style='color: #38bdf8;'>約 {total_anim_sec:.1f}s</b> "
                    f"<span style='color: #38bdf8; font-size: 11px;'>({human_total})</span> "
                    f"<span style='color: #64748b; font-size: 11px;'>{dur_breakdown}</span>"
                )

            if hasattr(self, "label_cfg_res"):
                self.label_cfg_res.setText(
                    f"<span style='color: #94a3b8; font-weight: bold;'>畫面規格：</span>"
                    f"<b style='color: #ffffff;'>{w}×{h} @ {fps} FPS</b>"
                    f"<span style='color: #475569;'> │ </span>"
                    f"<span style='color: #94a3b8;'>總時長：</span>"
                    f"{dur_html}"
                )

            # 更新 GPX 距離與總時長資訊列
            if has_gpx and hasattr(self, "label_distance_info"):
                m_total = int(total_anim_sec // 60)
                s_total = int(round(total_anim_sec % 60))
                time_str = f"{m_total:02d}:{s_total:02d}" if m_total > 0 else f"{total_anim_sec:.1f}s"
                if media_item_count > 0:
                    self.label_distance_info.setText(
                        f"<span style='color: #94a3b8;'>GPX 距離：</span><b style='color: #38bdf8;'>{dist:.2f} km</b>"
                        f"<span style='color: #475569;'> │ </span>"
                        f"<span style='color: #94a3b8;'>主動畫：</span><b style='color: #e2e8f0;'>{base_dur:.1f}s</b>"
                        f"<span style='color: #475569;'> │ </span>"
                        f"<span style='color: #94a3b8;'>媒體停頓：</span><b style='color: #c084fc;'>+{media_added_sec:.1f}s</b>"
                        f"<span style='color: #475569;'> │ </span>"
                        f"<span style='color: #94a3b8;'>預估總時長：</span><b style='color: #34d399;'>約 {total_anim_sec:.1f}s ({time_str})</b>"
                    )
                else:
                    mode_txt = "自動" if is_auto else "手動"
                    self.label_distance_info.setText(
                        f"<span style='color: #94a3b8;'>GPX 距離：</span><b style='color: #38bdf8;'>{dist:.2f} km</b>"
                        f"<span style='color: #475569;'> │ </span>"
                        f"<span style='color: #94a3b8;'>主動畫：</span><b style='color: #34d399;'>{base_dur:.1f}s</b> "
                        f"<span style='color: #64748b;'>({format_seconds_human(base_dur)}，{mode_txt})</span>"
                    )
            elif hasattr(self, "label_distance_info"):
                self.label_distance_info.setText(
                    "<span style='color: #94a3b8;'>GPX 距離：</span><span style='color: #f59e0b;'>請先匯入 GPX 路線檔案</span>"
                )

            # 2. 地圖視角
            map_raw = self.combo_map_style_2.currentText()
            map_key = map_raw.split(".", 1)[0].strip()
            map_label = config.MAP_STYLE_OPTIONS.get(map_key, ("", ""))[0]
            cam_mode = self.combo_camera_mode_2.currentText()
            zoom = self.combo_local_zoom.currentText()
            if hasattr(self, "label_cfg_map"):
                self.label_cfg_map.setText(
                    f"<span style='color: #94a3b8; font-weight: bold;'>地圖視角：</span>"
                    f"<b style='color: #ffffff;'>[{map_key}] {map_label}</b>"
                    f"<span style='color: #475569;'> │ </span>"
                    f"<span style='color: #e2e8f0;'>{cam_mode}</span>"
                    f"<span style='color: #475569;'> │ </span>"
                    f"<span style='color: #94a3b8;'>Zoom: </span><b style='color: #34d399;'>{zoom}</b>"
                )

            # 3. 編碼設定與媒體
            bitrate = self.combo_bitrate.currentText().strip()
            preset = self.combo_preset.currentText().strip()
            if media_item_count > 0:
                if media_video_count > 0 and media_photo_count > 0:
                    media_detail = f"影片 {media_video_count} 部 +{video_added_sec:.1f}s · 相片 {media_photo_count} 張 +{photo_added_sec:.1f}s"
                elif media_video_count > 0:
                    media_detail = f"影片 {media_video_count} 部 +{video_added_sec:.1f}s"
                else:
                    media_detail = f"相片 {media_photo_count} 張 +{photo_added_sec:.1f}s"
                media_html = (
                    f"<span style='color: #94a3b8;'>路線媒體：</span>"
                    f"<b style='color: #c084fc;'>{media_item_count} 個</b> "
                    f"<span style='color: #cbd5e1;'>({media_detail})</span>"
                )
            elif has_media_enabled:
                media_html = (
                    f"<span style='color: #94a3b8;'>路線媒體：</span>"
                    f"<span style='color: #f59e0b;'>已啟用 (未載入媒體)</span>"
                )
            else:
                media_html = (
                    f"<span style='color: #94a3b8;'>路線媒體：</span>"
                    f"<span style='color: #64748b;'>無媒體 Overlay</span>"
                )

            if hasattr(self, "label_cfg_enc"):
                self.label_cfg_enc.setText(
                    f"<span style='color: #94a3b8; font-weight: bold;'>編碼設定：</span>"
                    f"<b style='color: #ffffff;'>NVENC {bitrate}</b> "
                    f"<span style='color: #64748b;'>(Preset: {preset})</span>"
                    f"<span style='color: #475569;'> │ </span>"
                    f"{media_html}"
                )

            # 4. 效能模式與快取
            parallel = self.chk_parallel_2.isChecked()
            workers = self.spin_workers.value()
            chunks = self.spin_chunks.value()
            cache_mode = getattr(config, "MAP_CACHE_MODE", "session")
            if hasattr(self, "combo_cache_mode"):
                cache_mode = "persistent" if self.combo_cache_mode.currentIndex() == 1 else "session"
            if cache_mode == "persistent":
                cache_html = "<span style='color: #38bdf8; font-weight: bold;'>永久保留快取</span>"
            else:
                cache_html = "<span style='color: #94a3b8;'>自動暫存 (關閉清除)</span>"

            if parallel:
                perf_html = (
                    f"<b style='color: #fbbf24;'>多程序運算</b> "
                    f"<span style='color: #e2e8f0;'>({workers} Workers × {chunks} chunks)</span>"
                )
            else:
                perf_html = "<b style='color: #e2e8f0;'>單程序循序渲染</b>"

            if hasattr(self, "label_cfg_perf"):
                self.label_cfg_perf.setText(
                    f"<span style='color: #94a3b8; font-weight: bold;'>效能模式：</span>"
                    f"{perf_html}"
                    f"<span style='color: #475569;'> │ </span>"
                    f"<span style='color: #94a3b8;'>快取：</span>{cache_html}"
                )
        except Exception:
            pass
        except Exception:
            pass

    def _init_toolbar_and_menus(self):
        """初始化頂部選單列與 SVG 快捷工具列"""
        if hasattr(self, "toolBar"):
            self.toolBar.setIconSize(QSize(22, 22))
            self.toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        # 載入並綁定 SVG 向量圖示
        if hasattr(self, "action_open_gpx"): self.action_open_gpx.setIcon(_get_icon("file_gpx"))
        if hasattr(self, "action_save_output"): self.action_save_output.setIcon(_get_icon("video_output"))
        if hasattr(self, "action_media_dialog"): self.action_media_dialog.setIcon(_get_icon("media_manager"))
        if hasattr(self, "action_benchmark"): self.action_benchmark.setIcon(_get_icon("benchmark"))
        if hasattr(self, "action_clear_cache"): self.action_clear_cache.setIcon(_get_icon("clear_cache"))
        if hasattr(self, "action_open_log_folder"): self.action_open_log_folder.setIcon(_get_icon("log_folder"))
        if hasattr(self, "action_toggle_advanced"): self.action_toggle_advanced.setIcon(_get_icon("settings"))
        if hasattr(self, "action_advanced_settings"):
            self.action_advanced_settings.setIcon(_get_icon("settings"))
            self.action_advanced_settings.setToolTip("開啟進階渲染與效能調校詳細設定對話框")
        if hasattr(self, "action_start_render"): self.action_start_render.setIcon(_get_icon("start_render"))
        if hasattr(self, "action_stop_render"): self.action_stop_render.setIcon(_get_icon("stop_render"))
        if hasattr(self, "action_refresh_distance"): self.action_refresh_distance.setIcon(_get_icon("refresh"))
        if hasattr(self, "action_help_shortcuts"): self.action_help_shortcuts.setIcon(_get_icon("help"))
        if hasattr(self, "action_about"): self.action_about.setIcon(_get_icon("help"))

        # 連接檔案選單動作
        if hasattr(self, "action_open_gpx"): self.action_open_gpx.triggered.connect(self.browse_gpx)
        if hasattr(self, "action_save_output"): self.action_save_output.triggered.connect(self.browse_output)
        if hasattr(self, "action_select_media"): self.action_select_media.triggered.connect(self.browse_media)
        if hasattr(self, "action_media_dialog"): self.action_media_dialog.triggered.connect(self.open_media_dialog)
        if hasattr(self, "action_open_log_folder"): self.action_open_log_folder.triggered.connect(self.open_log_folder)
        if hasattr(self, "action_exit"): self.action_exit.triggered.connect(self.close)

        # 編輯與工具選單動作
        if hasattr(self, "action_benchmark"): self.action_benchmark.triggered.connect(self.start_benchmark)
        if hasattr(self, "action_apply_benchmark"): self.action_apply_benchmark.triggered.connect(self.apply_benchmark_recommendation)
        if hasattr(self, "action_clear_cache"): self.action_clear_cache.triggered.connect(self.on_clear_cache_clicked)
        if hasattr(self, "action_refresh_distance"): self.action_refresh_distance.triggered.connect(self.refresh_gpx_distance)

        # 檢視選單動作
        # 分頁切換與進階設定按鈕同步
        if hasattr(self, "tabWidget"):
            self.tabWidget.currentChanged.connect(self._on_tab_changed)
        if hasattr(self, "action_toggle_toolbar") and hasattr(self, "toolBar"):
            self.action_toggle_toolbar.toggled.connect(self.toolBar.setVisible)
        if hasattr(self, "action_toggle_advanced"):
            self.action_toggle_advanced.toggled.connect(lambda chk: self.toggle_advanced(show=chk))
        if hasattr(self, "action_toggle_summary"):
            self.action_toggle_summary.toggled.connect(self._on_toggle_summary)
        if hasattr(self, "action_toggle_workers"):
            self.action_toggle_workers.toggled.connect(self._on_toggle_workers)

        # 預設風格選單動作
        if hasattr(self, "action_profile_fast"):
            self.action_profile_fast.triggered.connect(lambda: self._select_profile("快速"))
        if hasattr(self, "action_profile_balanced"):
            self.action_profile_balanced.triggered.connect(lambda: self._select_profile("平衡"))
        if hasattr(self, "action_profile_quality"):
            self.action_profile_quality.triggered.connect(lambda: self._select_profile("高畫質"))

        # NVENC Preset 互斥群組
        self.preset_action_group = QActionGroup(self)
        for p in ["p1", "p2", "p3", "p4", "p5", "p6", "p7"]:
            act = getattr(self, f"action_preset_{p}", None)
            if act:
                act.setActionGroup(self.preset_action_group)
                act.setChecked(p == self.nvenc_preset)
                act.triggered.connect(lambda _, val=p: self._set_preset(val))

        # NVENC Bitrate 互斥群組
        self.bitrate_action_group = QActionGroup(self)
        for b in ["8M", "12M", "20M", "24M", "30M", "40M", "60M"]:
            act = getattr(self, f"action_bitrate_{b}", None)
            if act:
                act.setActionGroup(self.bitrate_action_group)
                act.setChecked(b == self.nvenc_bitrate)
                act.triggered.connect(lambda _, val=b: self._set_bitrate(val))

        # Workers 互斥群組
        self.workers_action_group = QActionGroup(self)
        for w in [2, 4, 6, 8, 12, 16]:
            act = getattr(self, f"action_workers_{w}", None)
            if act:
                act.setActionGroup(self.workers_action_group)
                act.setChecked(w == self.render_workers)
                act.triggered.connect(lambda _, val=w: self._set_workers(val))

        # Tile Connections 互斥群組
        self.tile_conn_action_group = QActionGroup(self)
        for c in [4, 8, 16, 24, 32]:
            act = getattr(self, f"action_tile_conn_{c}", None)
            if act:
                act.setActionGroup(self.tile_conn_action_group)
                act.setChecked(c == self.map_connections)
                act.triggered.connect(lambda _, val=c: self._set_connections(val))

        # 自訂解析度與進階設定對話框動作
        if hasattr(self, "action_custom_resolution"):
            self.action_custom_resolution.triggered.connect(self.open_custom_resolution_dialog)
        if hasattr(self, "action_advanced_settings"):
            self.action_advanced_settings.triggered.connect(self.open_advanced_settings_dialog)

        # 資訊面板雙向連動
        def _on_action_speed_toggled(c: bool):
            if hasattr(self, "combo_hud_panels"):
                self.combo_hud_panels.set_item_checked_by_data("speed", c)
            self.chk_show_speed.setChecked(c)

        def _on_action_minimap_toggled(c: bool):
            if hasattr(self, "combo_hud_panels"):
                self.combo_hud_panels.set_item_checked_by_data("minimap", c)
            self.chk_show_minimap.setChecked(c)

        def _on_action_elevation_toggled(c: bool):
            if hasattr(self, "combo_hud_panels"):
                self.combo_hud_panels.set_item_checked_by_data("elevation", c)
            self.chk_show_elevation.setChecked(c)

        if hasattr(self, "action_show_speed"):
            self.action_show_speed.setChecked(getattr(config, "SHOW_SPEED_HUD", True))
            self.action_show_speed.toggled.connect(_on_action_speed_toggled)
        if hasattr(self, "action_show_minimap"):
            self.action_show_minimap.setChecked(getattr(config, "SHOW_MINIMAP", True))
            self.action_show_minimap.toggled.connect(_on_action_minimap_toggled)
        if hasattr(self, "action_show_elevation"):
            self.action_show_elevation.setChecked(getattr(config, "SHOW_ELEVATION", True))
            self.action_show_elevation.toggled.connect(_on_action_elevation_toggled)

        # 鏡頭與渲染特性雙向連動
        if hasattr(self, "action_dynamic_speed_zoom") and hasattr(self, "chk_dynamic_speed_zoom"):
            self.action_dynamic_speed_zoom.toggled.connect(self.chk_dynamic_speed_zoom.setChecked)
            self.chk_dynamic_speed_zoom.toggled.connect(self.action_dynamic_speed_zoom.setChecked)
        if hasattr(self, "action_real_speed") and hasattr(self, "chk_real_speed_2"):
            self.action_real_speed.toggled.connect(self.chk_real_speed_2.setChecked)
            self.chk_real_speed_2.toggled.connect(self.action_real_speed.setChecked)
        if hasattr(self, "action_basemap"):
            self.action_basemap.setChecked(self.enable_basemap)
            self.action_basemap.toggled.connect(self._set_basemap)
        if hasattr(self, "action_parallel"):
            self.action_parallel.setChecked(self.parallel_render)
            self.action_parallel.toggled.connect(self._set_parallel)
        if hasattr(self, "action_enable_media"):
            self.action_enable_media.setChecked(self.enable_media)
            self.action_enable_media.toggled.connect(self._set_enable_media)
        if hasattr(self, "action_preview"):
            self.action_preview.setChecked(self.preview_mode)
            self.action_preview.toggled.connect(self._set_preview_mode)

        # 快取模式互斥群組與雙向連動
        self.cache_action_group = QActionGroup(self)
        if hasattr(self, "action_cache_session") and hasattr(self, "action_cache_persistent"):
            self.action_cache_session.setActionGroup(self.cache_action_group)
            self.action_cache_persistent.setActionGroup(self.cache_action_group)
            cur_idx = 1 if getattr(config, "MAP_CACHE_MODE", "session") == "persistent" else 0
            self.action_cache_session.setChecked(cur_idx == 0)
            self.action_cache_persistent.setChecked(cur_idx == 1)
            self.action_cache_session.triggered.connect(lambda: self._set_cache_mode("session"))
            self.action_cache_persistent.triggered.connect(lambda: self._set_cache_mode("persistent"))

        # 啟動與停止渲染動作
        if hasattr(self, "action_start_render"):
            self.action_start_render.triggered.connect(self.start_render)
        if hasattr(self, "action_stop_render"):
            self.action_stop_render.triggered.connect(self.stop_render)

        # 說明與手冊動作
        if hasattr(self, "action_help_shortcuts"):
            self.action_help_shortcuts.triggered.connect(self.show_shortcuts_dialog)
        if hasattr(self, "action_about"):
            self.action_about.triggered.connect(self.show_about_dialog)

    def _on_tab_changed(self, idx: int):
        if hasattr(self, "action_toggle_advanced"):
            self.action_toggle_advanced.blockSignals(True)
            self.action_toggle_advanced.setChecked(idx == 1)
            self.action_toggle_advanced.blockSignals(False)

    def _on_toggle_summary(self, visible: bool):
        if hasattr(self, "groupBox_summary"):
            self.groupBox_summary.setVisible(visible)
            QApplication.processEvents()
            self.adjustSize()

    def _on_toggle_workers(self, visible: bool):
        if hasattr(self, "tabWidget"):
            if visible:
                self.tabWidget.setCurrentIndex(2)
            elif self.tabWidget.currentIndex() == 2:
                self.tabWidget.setCurrentIndex(0)

    def _select_profile(self, name: str):
        if hasattr(self, "combo_profile_2"):
            self.combo_profile_2.setCurrentText(name)

    def show_shortcuts_dialog(self):
        shortcuts_info = (
            "GPX Ride Renderer 快捷鍵一覽：\\n\\n"
            "• Ctrl+O : 選擇 GPX 軌跡檔案\\n"
            "• Ctrl+S : 指定輸出 MP4 影片路徑\\n"
            "• Ctrl+M : 開啟路線照片與影片媒體管理器\\n"
            "• Ctrl+T : 執行 Auto Tune 效能基準測試\\n"
            "• Ctrl+L : 開啟 Log 日誌儲存資料夾\\n"
            "• Ctrl+R / F5 : 啟動影片渲染\\n"
            "• Esc : 停止當前渲染程序\\n"
            "• Ctrl+Shift+A : 展開 / 折疊進階設定面板\\n"
            "• Ctrl+Q : 關閉應用程式"
        )
        QMessageBox.information(self, "快捷鍵與使用手冊", shortcuts_info)

    def show_about_dialog(self):
        about_info = (
            f"GPX Ride Renderer V{__version__}\\n\\n"
            "高速 GPX / Strava 風格摩托車與單車騎乘路線動畫渲染器。\\n"
            "支援 3D 地形、自訂地圖風格、路線照片/影片即時解碼懸浮卡片與 NVIDIA NVENC 硬體加速。\\n\\n"
            "授權：MIT License"
        )
        QMessageBox.about(self, "關於 GPX Ride Renderer", about_info)

    def _init_combos(self):
        # 1. 預設模式
        self.combo_profile_2.clear()
        self.combo_profile_2.addItems(["快速", "平衡", "高畫質"])
        self.combo_profile_2.setCurrentText("高畫質")

        # 2. 地圖風格 (預設：4. 衛星影像)
        self.combo_map_style_2.clear()
        self.map_labels = [f"{k}. {v[0]}" for k, v in config.MAP_STYLE_OPTIONS.items()]
        self.combo_map_style_2.addItems(self.map_labels)
        target_map_idx = 3
        for i, lbl in enumerate(self.map_labels):
            if lbl.startswith("4.") or "衛星" in lbl:
                target_map_idx = i
                break
        self.combo_map_style_2.setCurrentIndex(target_map_idx)

        # 3. 視角模式 (預設：3D 真地形)
        self.combo_camera_mode_2.clear()
        self.combo_camera_mode_2.addItems(list(CAMERA_MODE_LABELS.values()))
        self.combo_camera_mode_2.setCurrentText(CAMERA_MODE_LABELS.get("3D-Terrain", "3D 真地形 (3D-Terrain)"))

        # 4. 解析度預設 (預設：1080p 直式 1080×1920)
        self.combo_resolution_2.clear()
        self.combo_resolution_2.addItems([p[0] for p in RESOLUTION_PRESETS])
        self._set_resolution_by_dim(1080, 1920)

        # 5. 軌跡顏色
        self.combo_track_color_2.clear()
        self.combo_track_color_2.addItems(config.TRACK_COLOR_OPTIONS)
        self.combo_track_color_2.setCurrentText(config.TRACK_COLOR_SCHEME)

        # 6. Local Zoom
        self.combo_local_zoom.clear()
        self.combo_local_zoom.addItems(["auto", "15", "16", "17", "18"])
        self.combo_local_zoom.setCurrentText(str(config.LOCAL_MAP_ZOOM))

        # 7. NVENC Preset
        self.combo_preset.clear()
        self.combo_preset.addItems(["p1", "p2", "p3", "p4", "p5", "p6", "p7"])
        self.combo_preset.setCurrentText(config.NVENC_PRESET)

        # 8. NVENC Bitrate
        self.combo_bitrate.clear()
        self.combo_bitrate.addItems(["8M", "12M", "20M", "24M", "30M", "40M", "60M"])
        self.combo_bitrate.setCurrentText(config.NVENC_BITRATE)

        # 9. 快取模式 (若 UI 存在則初始化，現已移至進階設定)
        if hasattr(self, "combo_cache_mode"):
            self.combo_cache_mode.clear()
            self.combo_cache_mode.addItems(["自動暫存 (關閉清除)", "永久保留 (保留快取)"])
            self.combo_cache_mode.setCurrentIndex(1 if getattr(config, "MAP_CACHE_MODE", "session") == "persistent" else 0)

    def _init_default_values(self):
        default_gpx = Path(config.gpx_filename)
        if default_gpx.is_file():
            self.lineEdit_gpx.setText(str(default_gpx.resolve()))
        else:
            self.lineEdit_gpx.setText("")
            self.lineEdit_gpx.setPlaceholderText("請選擇或拖曳 GPX 軌跡檔案...")
        self.lineEdit_output.setText(str(Path(config.output_filename).resolve()))
        self.lineEdit_media.setText(config.MEDIA_PATH)

        self.spin_width.setRange(240, 7680)
        self.spin_height.setRange(240, 7680)
        self.spin_width.setSingleStep(2)
        self.spin_height.setSingleStep(2)
        self.spin_width.setToolTip("自訂畫面寬度 (240 ~ 7680 px，建議偶數)")
        self.spin_height.setToolTip("自訂畫面高度 (240 ~ 7680 px，建議偶數)")

        self.spin_width.setValue(config.FRAME_WIDTH)
        self.spin_height.setValue(config.FRAME_HEIGHT)
        self.spin_fps.setValue(config.FPS)
        if default_gpx.is_file():
            self.lineEdit_duration.setText(str(config.VIDEO_DURATION))
        else:
            self.lineEdit_duration.setText("")
            self.lineEdit_duration.setPlaceholderText("自動計算 (待載入 GPX)")
        self.chk_auto_duration.setChecked(config.AUTO_DURATION_DEFAULT)
        self.spin_seconds_per_100km.setRange(1, 9999)
        self.spin_seconds_per_100km.setValue(int(config.AUTO_SECONDS_PER_100KM))

        self.lineEdit_zoomout.setText(str(config.ZOOM_OUT_DURATION))
        self.lineEdit_end_hold.setText(str(config.END_HOLD_DURATION))
        self.lineEdit_view_margin.setText(str(config.VIEW_MARGIN))

        self.spin_workers.setValue(config.RENDER_WORKERS)
        self.spin_chunks.setValue(config.CHUNKS_PER_WORKER)
        self.spin_tile_connections.setValue(config.MAP_CONNECTIONS)

        self.chk_parallel_2.setChecked(config.PARALLEL_RENDER)
        self.chk_basemap_2.setChecked(config.ENABLE_BASEMAP)
        self.chk_enable_media_2.setChecked(config.ENABLE_MEDIA)
        self.chk_real_speed_2.setChecked(config.USE_REAL_SPEED)

        if hasattr(self, "chk_preview"): self.chk_preview.setChecked(config.PREVIEW_MODE)
        if hasattr(self, "chk_contextily_cache"): self.chk_contextily_cache.setChecked(config.MAP_USE_CACHE)
        if hasattr(self, "chk_disable_parallel_cache"): self.chk_disable_parallel_cache.setChecked(config.PARALLEL_DISABLE_TILE_CACHE)

        self.chk_show_speed.setChecked(getattr(config, "SHOW_SPEED_HUD", True))
        self.chk_show_minimap.setChecked(getattr(config, "SHOW_MINIMAP", True))
        self.chk_show_elevation.setChecked(getattr(config, "SHOW_ELEVATION", True))
        self.chk_dynamic_speed_zoom.setChecked(getattr(config, "ENABLE_DYNAMIC_SPEED_ZOOM", True))

        # 初始化「路線媒體」分頁中由 .ui 載入的資訊面板複選下拉選單
        if hasattr(self, "combo_hud_panels"):
            self.combo_hud_panels.clear()
            self.combo_hud_panels.add_checkable_item("速度與里程 HUD", data="speed", checked=self.chk_show_speed.isChecked())
            self.combo_hud_panels.add_checkable_item("路線小地圖", data="minimap", checked=self.chk_show_minimap.isChecked())
            self.combo_hud_panels.add_checkable_item("全景高程剖面", data="elevation", checked=self.chk_show_elevation.isChecked())

            # 雙向同步事件綁定
            def _on_main_hud_selection_changed(checked_list):
                is_speed = "速度與里程 HUD" in checked_list
                is_mini = "路線小地圖" in checked_list
                is_elev = "全景高程剖面" in checked_list
                self.chk_show_speed.setChecked(is_speed)
                self.chk_show_minimap.setChecked(is_mini)
                self.chk_show_elevation.setChecked(is_elev)
                config.SHOW_SPEED_HUD = is_speed
                config.SHOW_MINIMAP = is_mini
                config.SHOW_ELEVATION = is_elev
                if hasattr(self, "action_show_speed"): self.action_show_speed.setChecked(is_speed)
                if hasattr(self, "action_show_minimap"): self.action_show_minimap.setChecked(is_mini)
                if hasattr(self, "action_show_elevation"): self.action_show_elevation.setChecked(is_elev)
                self._update_dashboard_summary()
                if hasattr(self, "media_tab") and self.media_tab:
                    self.media_tab.refresh_preview()

            self.combo_hud_panels.selection_changed.connect(_on_main_hud_selection_changed)

        self.spin_hide_start.setValue(config.HIDE_START_DISTANCE_KM)
        self.spin_hide_end.setValue(config.HIDE_END_DISTANCE_KM)

        # 初始化圓形進度條視覺樣式
        if hasattr(self, "progressBar_main"):
            self.progressBar_main.progress_width = 10
            self.progressBar_main.font_size = 14
            self.progressBar_main.set_progress_color("#00adb5")
            self.progressBar_main.add_shadow(True)

        for bar in self.worker_bars:
            bar.progress_width = 6
            bar.font_size = 11
            bar.set_progress_color("#2196f3")
            bar.add_shadow(True)

        # 優化設定摘要區塊字體與排版設定
        for lbl in (getattr(self, "label_cfg_res", None),
                    getattr(self, "label_cfg_map", None),
                    getattr(self, "label_cfg_enc", None),
                    getattr(self, "label_cfg_perf", None)):
            if lbl is not None:
                lbl.setWordWrap(True)
        if hasattr(self, "verticalLayout_17"):
            self.verticalLayout_17.setSpacing(6)

        self.on_auto_duration_toggle()

    def _connect_signals(self):
        self.btn_browse_gpx.clicked.connect(self.browse_gpx)
        self.btn_browse_output.clicked.connect(self.browse_output)
        self.btn_browse_media.clicked.connect(self.browse_media)
        self.btn_media_dialog.clicked.connect(self.open_media_dialog)

        self.combo_profile_2.currentIndexChanged.connect(self.apply_profile)
        self.combo_map_style_2.currentIndexChanged.connect(self.on_map_change)
        self.combo_camera_mode_2.currentIndexChanged.connect(self.on_camera_mode_change)
        self.combo_resolution_2.currentIndexChanged.connect(self.on_res_preset_change)

        self.spin_width.valueChanged.connect(self.on_custom_dim_change)
        self.spin_height.valueChanged.connect(self.on_custom_dim_change)
        self.spin_fps.valueChanged.connect(lambda: self._update_dashboard_summary())
        self.combo_track_color_2.currentIndexChanged.connect(lambda: self._update_dashboard_summary())

        self.combo_local_zoom.currentIndexChanged.connect(lambda: self._update_dashboard_summary())
        self.combo_preset.currentIndexChanged.connect(lambda: self._update_dashboard_summary())
        self.combo_bitrate.currentIndexChanged.connect(lambda: self._update_dashboard_summary())
        self.chk_parallel_2.toggled.connect(lambda: self._update_dashboard_summary())
        self.chk_show_speed.toggled.connect(lambda: self._update_dashboard_summary())
        self.chk_show_minimap.toggled.connect(lambda: self._update_dashboard_summary())
        self.chk_show_elevation.toggled.connect(lambda: self._update_dashboard_summary())
        self.chk_dynamic_speed_zoom.toggled.connect(lambda: self._update_dashboard_summary())
        self.spin_workers.valueChanged.connect(lambda: self._update_dashboard_summary())
        self.spin_chunks.valueChanged.connect(lambda: self._update_dashboard_summary())
        if hasattr(self, "chk_disable_parallel_cache"): self.chk_disable_parallel_cache.toggled.connect(lambda: self._update_dashboard_summary())
        self.chk_enable_media_2.toggled.connect(lambda: self._update_dashboard_summary())
        self.lineEdit_media.textChanged.connect(lambda: self._update_dashboard_summary())

        self.chk_auto_duration.toggled.connect(self.on_auto_duration_toggle)
        self.spin_seconds_per_100km.valueChanged.connect(self.on_duration_rate_change)
        self.lineEdit_duration.textChanged.connect(lambda: self._update_dashboard_summary())

        if hasattr(self, "combo_cache_mode"):
            self.combo_cache_mode.currentIndexChanged.connect(self.on_cache_mode_change)
        if hasattr(self, "btn_clear_cache"):
            self.btn_clear_cache.clicked.connect(self.on_clear_cache_clicked)

        # 加入 400ms Debounce 防抖，避免連續輸入字元快速開線程
        self.gpx_debounce_timer = QTimer(self)
        self.gpx_debounce_timer.setSingleShot(True)
        self.gpx_debounce_timer.timeout.connect(self.refresh_gpx_distance)
        self.lineEdit_gpx.textChanged.connect(lambda: self.gpx_debounce_timer.start(400))

        if hasattr(self, "btn_toggle_advanced_2"): self.btn_toggle_advanced_2.clicked.connect(lambda: self.toggle_advanced())

        self.btn_start_render.clicked.connect(self.start_render)
        self.btn_stop_render.clicked.connect(self.stop_render)
        if hasattr(self, "btn_open_log_folder"): self.btn_open_log_folder.clicked.connect(self.open_log_folder)

        if hasattr(self, "btn_autotune"):
            self.btn_autotune.clicked.connect(self.start_benchmark)
        if hasattr(self, "btn_benchmark"):
            self.btn_benchmark.clicked.connect(self.start_benchmark)
        if hasattr(self, "btn_apply_benchmark"):
            self.btn_apply_benchmark.clicked.connect(self.apply_benchmark_recommendation)

    # ---------- Slot Implementations ----------
    def refresh_cache_size_display(self):
        """背景啟動執行緒計算快取容量，不卡頓 Qt 主執行緒"""
        if hasattr(self, "_cache_size_thread") and self._cache_size_thread is not None:
            if self._cache_size_thread.isRunning():
                return
        self._cache_size_thread = CacheSizeWorkerThread(self)
        self._cache_size_thread.size_signal.connect(self._on_cache_size_calculated)
        self._cache_size_thread.start()

    def _on_cache_size_calculated(self, mb: float):
        if hasattr(self, "lbl_cache_size"):
            self.lbl_cache_size.setText(f"快取: {mb:.1f} MB")

    def _set_cache_mode(self, mode: str):
        mode = "persistent" if str(mode).lower() == "persistent" else "session"
        config.MAP_CACHE_MODE = mode
        if hasattr(self, "settings"):
            self.settings.setValue("map_cache_mode", mode)
        CacheManager.init_cache_system()
        if hasattr(self, "combo_cache_mode"):
            self.combo_cache_mode.blockSignals(True)
            self.combo_cache_mode.setCurrentIndex(1 if mode == "persistent" else 0)
            self.combo_cache_mode.blockSignals(False)
        if hasattr(self, "action_cache_session") and hasattr(self, "action_cache_persistent"):
            self.action_cache_session.blockSignals(True)
            self.action_cache_persistent.blockSignals(True)
            self.action_cache_session.setChecked(mode == "session")
            self.action_cache_persistent.setChecked(mode == "persistent")
            self.action_cache_session.blockSignals(False)
            self.action_cache_persistent.blockSignals(False)
        self.refresh_cache_size_display()
        self._update_dashboard_summary()

    def on_cache_mode_change(self, idx: int):
        self._set_cache_mode("persistent" if idx == 1 else "session")

    def on_clear_cache_clicked(self):
        reply = QMessageBox.question(
            self, "清除快取確認",
            "確定要立即清除所有本機磁碟底圖與高程快取嗎？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            CacheManager.cleanup_all_cache()
            self.refresh_cache_size_display()
            QMessageBox.information(self, "快取已清除", "所有底圖與高程快取已全數清空！")
    def toggle_advanced(self, *args, show: Optional[bool] = None):
        if hasattr(self, "tabWidget"):
            cur_idx = self.tabWidget.currentIndex()
            if show is True:
                target_idx = 1
            elif show is False:
                target_idx = 0 if cur_idx == 1 else cur_idx
            else:
                target_idx = 0 if cur_idx == 1 else 1
            self.tabWidget.setCurrentIndex(target_idx)
            if hasattr(self, "action_toggle_advanced"):
                self.action_toggle_advanced.blockSignals(True)
                self.action_toggle_advanced.setChecked(target_idx == 1)
                self.action_toggle_advanced.blockSignals(False)
            return

        is_visible = self.groupBox.isVisible() if hasattr(self, "groupBox") else False
        next_state = not is_visible if show is None else bool(show)
        if hasattr(self, "groupBox"):
            self.groupBox.setVisible(next_state)
        if hasattr(self, "btn_toggle_advanced_2"):
            self.btn_toggle_advanced_2.setText("進階設定 ▲" if next_state else "進階設定 ▼")
        if hasattr(self, "action_toggle_advanced"):
            self.action_toggle_advanced.blockSignals(True)
            self.action_toggle_advanced.setChecked(next_state)
            self.action_toggle_advanced.blockSignals(False)

    def browse_gpx(self):
        p, _ = QFileDialog.getOpenFileName(self, "選擇 GPX 檔案", "", "GPX 檔案 (*.gpx);;所有檔案 (*.*)")
        if p:
            self.lineEdit_gpx.setText(p)
            out_p = self.lineEdit_output.text().strip()
            if not out_p or Path(out_p).name == "ride_animation.mp4":
                self.lineEdit_output.setText(str(Path(p).with_name(Path(p).stem + "_animation.mp4")))
            self.state["gpx_distance_km"] = None
            self.state["gpx_distance_path"] = None
            self.refresh_gpx_distance()
            if hasattr(self, "media_tab"):
                try:
                    from gpx_renderer.core.data import load_gpx
                    data = load_gpx(
                        p,
                        hide_start_km=self.spin_hide_start.value() if hasattr(self, "spin_hide_start") else 0.0,
                        hide_end_km=self.spin_hide_end.value() if hasattr(self, "spin_hide_end") else 0.0,
                    )
                    self.media_tab.set_ride_data(data)
                except Exception:
                    pass

    def browse_output(self):
        p, _ = QFileDialog.getSaveFileName(self, "指定輸出 MP4 檔案", "", "MP4 影片檔 (*.mp4)")
        if p:
            self.lineEdit_output.setText(p)

    def browse_media(self):
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QCursor

        menu = QMenu(self)
        act_files = menu.addAction("選擇照片或影片檔案 (可多選)...")
        act_folder = menu.addAction("選擇照片/影片資料夾...")
        chosen = menu.exec_(QCursor.pos())

        if chosen == act_files:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "選擇路線照片或影片檔案 (可複選)",
                "",
                "媒體檔案 (*.jpg *.jpeg *.png *.webp *.bmp *.mp4 *.mov *.avi *.mkv *.webm *.m4v *.flv *.wmv);;照片檔案 (*.jpg *.jpeg *.png *.webp *.bmp);;影片檔案 (*.mp4 *.mov *.avi *.mkv *.webm *.m4v *.flv *.wmv);;所有檔案 (*.*)",
            )
            if files:
                self.lineEdit_media.setText("; ".join(files))
                self.chk_enable_media_2.setChecked(True)
                if hasattr(self, "media_tab"):
                    self.media_tab.load_media_from_paths(files)
                self._update_dashboard_summary()
        elif chosen == act_folder:
            p = QFileDialog.getExistingDirectory(self, "選擇路線照片/影片資料夾")
            if p:
                self.lineEdit_media.setText(p)
                self.chk_enable_media_2.setChecked(True)
                if hasattr(self, "media_tab"):
                    self.media_tab.load_media_from_paths(p)
                self._update_dashboard_summary()

    def open_media_dialog(self):
        """切換至第二分頁（路線媒體管理器）"""
        if hasattr(self, "tabWidget"):
            self.tabWidget.setCurrentIndex(1)

    def on_map_change(self, *args):
        if hasattr(self, "media_tab") and not getattr(self.media_tab, "_is_syncing_controls", False):
            combo_preview = getattr(self, "combo_preview_map_style", None)
            if combo_preview is not None and combo_preview.currentIndex() != self.combo_map_style_2.currentIndex():
                self.media_tab._is_syncing_controls = True
                try:
                    combo_preview.setCurrentIndex(self.combo_map_style_2.currentIndex())
                finally:
                    self.media_tab._is_syncing_controls = False

        self._update_dashboard_summary()
        if hasattr(self, "media_tab"):
            self.media_tab.refresh_preview()

    def on_camera_mode_change(self, *args):
        if hasattr(self, "media_tab") and not getattr(self.media_tab, "_is_syncing_controls", False):
            combo_preview = getattr(self, "combo_preview_camera_mode", None)
            if combo_preview is not None and combo_preview.currentIndex() != self.combo_camera_mode_2.currentIndex():
                self.media_tab._is_syncing_controls = True
                try:
                    combo_preview.setCurrentIndex(self.combo_camera_mode_2.currentIndex())
                finally:
                    self.media_tab._is_syncing_controls = False

        self._update_dashboard_summary()
        if hasattr(self, "media_tab"):
            self.media_tab.refresh_preview()

    def _set_resolution_by_dim(self, w: int, h: int):
        """依寬高自動選擇對應的解析度預設項目"""
        for label, pw, ph in RESOLUTION_PRESETS:
            if pw == w and ph == h:
                self.combo_resolution_2.setCurrentText(label)
                if hasattr(self, "media_tab") and not getattr(self.media_tab, "_is_syncing_controls", False):
                    combo_preview = getattr(self, "combo_preview_resolution", getattr(self, "combo_preview_res", None))
                    if combo_preview is not None and combo_preview.currentIndex() != self.combo_resolution_2.currentIndex():
                        self.media_tab._is_syncing_controls = True
                        try:
                            combo_preview.setCurrentIndex(self.combo_resolution_2.currentIndex())
                        finally:
                            self.media_tab._is_syncing_controls = False
                return

    def apply_profile(self):
        mode = self.combo_profile_2.currentText()
        if mode == "快速":
            self._set_resolution_by_dim(1280, 720)
            self.combo_local_zoom.setCurrentText("auto")
            self._set_bitrate("12M")
            self._set_preset("p3")
            self._set_workers(6)
            self.chunks_per_worker = 4
        elif mode == "高畫質":
            self._set_resolution_by_dim(1440, 1440)
            self.combo_local_zoom.setCurrentText("17")
            self._set_bitrate("30M")
            self._set_preset("p5")
            self._set_workers(6)
            self.chunks_per_worker = 4
        else:
            self._set_resolution_by_dim(1080, 1080)
            self.combo_local_zoom.setCurrentText("16")
            self._set_bitrate("20M")
            self._set_preset("p4")
            self._set_workers(6)
            self.chunks_per_worker = 4
        self._update_dashboard_summary()

    def get_current_resolution(self) -> tuple[int, int]:
        """解析度優先採用一般設定的下拉選單；選「自訂解析度」才採用自訂寬高。"""
        sel = self.combo_resolution_2.currentText()
        for label, pw, ph in RESOLUTION_PRESETS:
            if label == sel and pw is not None and ph is not None:
                return pw, ph
        w = max(240, min(7680, self.custom_width))
        h = max(240, min(7680, self.custom_height))
        return (w // 2) * 2, (h // 2) * 2

    def on_res_preset_change(self):
        sel = self.combo_resolution_2.currentText()
        if "自訂" in sel:
            self.open_custom_resolution_dialog()
        else:
            for label, w, h in RESOLUTION_PRESETS:
                if label == sel and w is not None and h is not None:
                    self.custom_width = w
                    self.custom_height = h
                    break

        if hasattr(self, "media_tab") and not getattr(self.media_tab, "_is_syncing_controls", False):
            combo_preview = getattr(self, "combo_preview_resolution", getattr(self, "combo_preview_res", None))
            if combo_preview is not None and combo_preview.currentIndex() != self.combo_resolution_2.currentIndex():
                self.media_tab._is_syncing_controls = True
                try:
                    combo_preview.setCurrentIndex(self.combo_resolution_2.currentIndex())
                finally:
                    self.media_tab._is_syncing_controls = False

        self._update_dashboard_summary()
        if hasattr(self, "media_tab"):
            self.media_tab.refresh_preview()

    def on_custom_dim_change(self):
        w, h = self.spin_width.value(), self.spin_height.value()
        matched = False
        self.combo_resolution_2.blockSignals(True)
        for label, pw, ph in RESOLUTION_PRESETS:
            if pw == w and ph == h:
                self.combo_resolution_2.setCurrentText(label)
                matched = True
                break
        if not matched:
            for label, pw, ph in RESOLUTION_PRESETS:
                if pw is None and ph is None:
                    self.combo_resolution_2.setCurrentText(label)
                    break
        self.combo_resolution_2.blockSignals(False)

        if hasattr(self, "media_tab") and not getattr(self.media_tab, "_is_syncing_controls", False):
            combo_preview = getattr(self, "combo_preview_resolution", getattr(self, "combo_preview_res", None))
            if combo_preview is not None and combo_preview.currentIndex() != self.combo_resolution_2.currentIndex():
                self.media_tab._is_syncing_controls = True
                try:
                    combo_preview.setCurrentIndex(self.combo_resolution_2.currentIndex())
                finally:
                    self.media_tab._is_syncing_controls = False

        self._update_dashboard_summary()
        if hasattr(self, "media_tab"):
            self.media_tab.refresh_preview()

    def on_auto_duration_toggle(self):
        is_auto = self.chk_auto_duration.isChecked()
        self.lineEdit_duration.setEnabled(not is_auto)
        if is_auto:
            self.refresh_gpx_distance()
        else:
            if not self.lineEdit_duration.text().strip():
                self.lineEdit_duration.setText("30.0")
            if self.state.get("gpx_distance_km") is not None:
                dist = self.state["gpx_distance_km"]
                self.label_distance_info.setText(f"GPX 距離：{dist:.2f} km (手動秒數)")
        self._update_dashboard_summary()

    def on_duration_rate_change(self):
        self._apply_cached_auto_duration()

    def _apply_cached_auto_duration(self):
        if not self.chk_auto_duration.isChecked():
            return
        dist = self.state.get("gpx_distance_km")
        if dist is None:
            return
        try:
            rate = float(self.spin_seconds_per_100km.value())
            if rate <= 0: return
        except Exception: return
        secs = auto_duration_seconds(dist, rate)
        self.lineEdit_duration.setText(str(round(secs, 1)))
        self.label_distance_info.setText(f"GPX 距離：{dist:.2f} km  →  主動畫 {secs:.1f}s ({format_seconds_human(secs)})")

    def refresh_gpx_distance(self):
        raw = self.lineEdit_gpx.text().strip()
        if not raw or not Path(raw).is_file():
            self.state["gpx_distance_km"] = None
            self.state["gpx_distance_path"] = None
            if hasattr(self, "label_distance_info"):
                if not raw:
                    self.label_distance_info.setText(
                        "<span style='color: #94a3b8;'>GPX 距離：</span><span style='color: #f59e0b;'>請先匯入 GPX 路線檔案</span>"
                    )
                else:
                    self.label_distance_info.setText(
                        "<span style='color: #94a3b8;'>GPX 距離：</span><span style='color: #ef4444;'>找不到檔案</span>"
                    )
            if self.chk_auto_duration.isChecked():
                self.lineEdit_duration.setText("")
                self.lineEdit_duration.setPlaceholderText("自動計算 (待載入 GPX)")
            self._update_dashboard_summary()
            if hasattr(self, "media_tab"):
                self.media_tab.set_ride_data(None)
            return

        if self.state.get("gpx_distance_path") == raw and self.state.get("gpx_distance_km") is not None:
            self._apply_cached_auto_duration()
            return

        if hasattr(self, "dist_thread") and self.dist_thread is not None:
            if self.dist_thread.isRunning():
                try:
                    self.dist_thread.success_signal.disconnect()
                    self.dist_thread.failed_signal.disconnect()
                except Exception:
                    pass
                self.dist_thread.quit()
                self.dist_thread.wait(100)

        self.label_distance_info.setText("GPX 距離：讀取中…")
        self.dist_thread = GpxDistanceThread(raw, parent=self)
        self.dist_thread.success_signal.connect(self._on_dist_success)
        self.dist_thread.failed_signal.connect(self._on_dist_failed)
        self.dist_thread.start()

    def _on_dist_success(self, dist: float):
        raw = self.lineEdit_gpx.text().strip()
        self.state["gpx_distance_km"] = dist
        self.state["gpx_distance_path"] = raw
        self._apply_cached_auto_duration()

        if hasattr(self, "media_tab") and raw and Path(raw).is_file():
            try:
                from gpx_renderer.core.data import load_gpx
                data = load_gpx(
                    raw,
                    hide_start_km=self.spin_hide_start.value() if hasattr(self, "spin_hide_start") else 0.0,
                    hide_end_km=self.spin_hide_end.value() if hasattr(self, "spin_hide_end") else 0.0,
                )
                self.media_tab.set_ride_data(data)
            except Exception:
                pass

    def _on_dist_failed(self, err: str):
        self.state["gpx_distance_km"] = None
        self.state["gpx_distance_path"] = None
        self.label_distance_info.setText(f"GPX 距離：讀取失敗 ({err})")
        if hasattr(self, "media_tab"):
            self.media_tab.set_ride_data(None)

    # ---------- Render Subprocess Job Management ----------
    def collect_config(dict_self) -> dict:
        map_key = dict_self.combo_map_style_2.currentText().split(".", 1)[0].strip()
        cam_sel = dict_self.combo_camera_mode_2.currentText()
        cam_mode = "North-Up"
        if "3D" in cam_sel: cam_mode = "3D-Terrain"
        elif "Heading" in cam_sel: cam_mode = "Heading-Up"

        dur = float(dict_self.lineEdit_duration.text()) if dict_self.lineEdit_duration.text() else 30.0
        frame_w, frame_h = dict_self.get_current_resolution()

        return {
            "gpx_filename": dict_self.lineEdit_gpx.text().strip(),
            "output_filename": dict_self.lineEdit_output.text().strip(),
            "map_style_key": map_key,
            "FRAME_WIDTH": frame_w,
            "FRAME_HEIGHT": frame_h,
            "FPS": dict_self.spin_fps.value(),
            "VIDEO_DURATION": dur,
            "AUTO_DURATION_ENABLED": dict_self.chk_auto_duration.isChecked(),
            "AUTO_SECONDS_PER_100KM": float(dict_self.spin_seconds_per_100km.value()),
            "GPX_DISTANCE_KM": dict_self.state.get("gpx_distance_km"),
            "ZOOM_OUT_DURATION": float(dict_self.lineEdit_zoomout.text()),
            "END_HOLD_DURATION": float(dict_self.lineEdit_end_hold.text()),
            "VIEW_MARGIN": float(dict_self.lineEdit_view_margin.text()),
            "LOCAL_MAP_ZOOM": config._normalize_zoom(dict_self.combo_local_zoom.currentText()),
            "RENDER_WORKERS": dict_self.spin_workers.value(),
            "CHUNKS_PER_WORKER": dict_self.spin_chunks.value(),
            "MAP_CONNECTIONS": dict_self.spin_tile_connections.value(),
            "NVENC_BITRATE": dict_self.combo_bitrate.currentText().strip(),
            "NVENC_PRESET": dict_self.combo_preset.currentText().strip(),
            "PARALLEL_RENDER": dict_self.chk_parallel_2.isChecked(),
            "ENABLE_BASEMAP": dict_self.chk_basemap_2.isChecked(),
            "PREVIEW_MODE": dict_self.chk_preview.isChecked(),
            "MAP_USE_CACHE": True,
            "MAP_CACHE_MODE": getattr(config, "MAP_CACHE_MODE", "session"),
            "MAP_CACHE_SESSION_ID": CacheManager.get_session_id(),
            "MAP_CACHE_MAX_MB": getattr(config, "MAP_CACHE_MAX_MB", 1024),
            "PARALLEL_DISABLE_TILE_CACHE": False,
            "ENABLE_MEDIA": dict_self.chk_enable_media_2.isChecked(),
            "MEDIA_PATH": dict_self.lineEdit_media.text().strip(),
            "MEDIA_POPUP_DURATION": float(dict_self.state.get("media_popup_duration") or config.MEDIA_POPUP_DURATION),
            "MEDIA_CAPTION_FONT_SIZE": int(dict_self.state.get("media_caption_font_size") or getattr(config, "MEDIA_CAPTION_FONT_SIZE", 22)),
            "MEDIA_TIME_OFFSET_SEC": float(dict_self.state.get("media_time_offset_sec") or config.MEDIA_TIME_OFFSET_SEC),
            "MEDIA_OVERRIDES_JSON": dict_self.state.get("media_overrides_json", "{}"),
            "USE_REAL_SPEED": dict_self.chk_real_speed_2.isChecked(),
            "ENABLE_DYNAMIC_SPEED_ZOOM": dict_self.chk_dynamic_speed_zoom.isChecked(),
            "SHOW_SPEED_HUD": dict_self.chk_show_speed.isChecked(),
            "SHOW_MINIMAP": dict_self.chk_show_minimap.isChecked(),
            "SHOW_ELEVATION": dict_self.chk_show_elevation.isChecked(),
            "HIDE_START_DISTANCE_KM": dict_self.spin_hide_start.value(),
            "HIDE_END_DISTANCE_KM": dict_self.spin_hide_end.value(),
            "CAMERA_MODE": cam_mode,
            "TRACK_COLOR_SCHEME": dict_self.combo_track_color_2.currentText(),
        }

    def set_running(self, running: bool):
        self.btn_start_render.setEnabled(not running)
        if hasattr(self, "action_start_render"): self.action_start_render.setEnabled(not running)
        if hasattr(self, "btn_autotune"): self.btn_autotune.setEnabled(not running)
        if hasattr(self, "btn_benchmark"): self.btn_benchmark.setEnabled(not running)
        if hasattr(self, "action_benchmark"): self.action_benchmark.setEnabled(not running)
        self.btn_stop_render.setEnabled(running)
        if hasattr(self, "action_stop_render"): self.action_stop_render.setEnabled(running)

    def start_render(self):
        if self.state["proc"] is not None: return
        try:
            cfg = self.collect_config()
        except Exception as exc:
            QMessageBox.critical(self, "設定錯誤", str(exc)); return

        if not Path(cfg["gpx_filename"]).is_file():
            QMessageBox.critical(self, "找不到 GPX 檔案", cfg["gpx_filename"]); return

        self.progressBar_main.setValue(0)
        for bar in self.worker_bars:
            bar.setValue(0)
        for lbl in self.worker_status_labels:
            lbl.setText("待命")

        if hasattr(self, "label_eta_elapsed"): self.label_eta_elapsed.setText("渲染計時: 00:00:00")
        if hasattr(self, "label_eta_time"): self.label_eta_time.setText("預估剩餘時間: --")
        if hasattr(self, "label_eta_clock"): self.label_eta_clock.setText("預計完成時刻: --:--:--")
        if hasattr(self, "label_eta_speed"): self.label_eta_speed.setText("渲染速度: -- frame/s")
        if hasattr(self, "label_eta_frames"): self.label_eta_frames.setText("已完成幀數: 0 / 0")

        self._update_dashboard_summary()
        self.set_status_message("啟動渲染程序中…")
        self._spawn_job(cfg, "render")

    def start_benchmark(self):
        if self.state["proc"] is not None: return
        try:
            cfg = self.collect_config()
        except Exception as exc:
            QMessageBox.critical(self, "設定錯誤", str(exc)); return

        if not Path(cfg["gpx_filename"]).is_file():
            QMessageBox.critical(self, "找不到 GPX 檔案", cfg["gpx_filename"]); return

        cfg["BENCHMARK_CANDIDATES"] = _default_benchmark_candidates(cfg.get("RENDER_WORKERS"))
        cfg["BENCHMARK_FRAMES"] = max(240, min(360, int(round(int(cfg["FPS"]) * 5.0))))
        self.progressBar_main.setValue(0)
        for bar in self.worker_bars:
            bar.setValue(0)
        for lbl in self.worker_status_labels:
            lbl.setText("待命")

        if hasattr(self, "label_eta_elapsed"): self.label_eta_elapsed.setText("渲染計時: 00:00:00")
        if hasattr(self, "label_autotune_result"):
            self.label_autotune_result.setText("測試中…")
        self.set_status_message("Auto Tune 效能測試中…")
        self._spawn_job(cfg, "benchmark")

    def _write_log(self, text: str):
        """將訊息寫入根目錄 logs 資料夾中的 log 檔案 (附加時間戳記並即時緩衝刷新)"""
        f = self.state.get("log_file")
        if f and not f.closed:
            try:
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{ts}] {text}\n")
                f.flush()
            except Exception:
                pass

    def _spawn_job(self, cfg: dict, mode: str):
        # 建立根目錄 logs 資料夾與本次執行之 log 檔案
        log_dir = (application_dir() / "logs").resolve()
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        log_path = log_dir / f"{mode}_{timestamp_str}.log"
        try:
            log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        except Exception:
            log_file = None
        self.state["log_file"] = log_file
        self.state["log_path"] = log_path

        fd, cfg_path = tempfile.mkstemp(prefix=f"gpx_renderer_{mode}_", suffix=".json")
        os.close(fd)
        Path(cfg_path).write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        self.state["config_path"] = cfg_path

        flag = "--benchmark-config" if mode == "benchmark" else "--render-config"
        cmd = _self_subprocess_command(flag, cfg_path)

        self._write_log("=" * 72)
        self._write_log(f"[INFO] 啟動 {'Auto Tune 效能測試' if mode == 'benchmark' else '渲染'}：{' '.join(cmd)}")

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        kwargs = dict(
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding="utf-8", errors="replace", bufsize=1, env=env,
        )
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        proc = subprocess.Popen(cmd, **kwargs)
        self.state["proc"] = proc
        self.state["proc_mode"] = mode
        self.set_running(True)

        self._render_start_time = time.time()
        if hasattr(self, "label_eta_elapsed"):
            self.label_eta_elapsed.setText("渲染計時: 00:00:00")
        self._render_timer.start(500)

        self.reader_thread = SubprocessReaderThread(proc)
        self.reader_thread.line_signal.connect(self._parse_process_line)
        self.reader_thread.finished_signal.connect(self._finish_proc)
        self.reader_thread.start()

    def stop_render(self):
        proc = self.state.get("proc")
        if proc and proc.poll() is None:
            self._write_log("[WARN] 使用者要求終止程序。")
            proc.terminate()
            self.set_status_message("已發送停止訊號…")

    def open_log_folder(self):
        log_dir = (application_dir() / "logs").resolve()
        log_dir.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(log_dir)
        else:
            subprocess.Popen(["xdg-open", str(log_dir)])

    def _parse_process_line(self, line: str):
        # 寫入 logs 檔案 (過濾掉純 JSON 傳輸字串，保留人類可讀 Log)
        if not ("[PROGRESS_JSON]" in line or "PROGRESS_JSON:" in line):
            self._write_log(line)

        # 解析進度 JSON
        if "[PROGRESS_JSON]" in line or "PROGRESS_JSON:" in line:
            try:
                sep = "[PROGRESS_JSON]" if "[PROGRESS_JSON]" in line else "PROGRESS_JSON:"
                json_str = line.split(sep, 1)[1].strip()
                data = json.loads(json_str)
                pct = float(data.get("pct", data.get("progress_percent", 0.0)))
                stage = data.get("stage", "render")

                if stage == "prefetch":
                    self.progressBar_main.setValue(int(round(pct)))
                    chunks_done = data.get("chunks_done", data.get("rendered", 0))
                    chunks_total = data.get("chunks_total", data.get("total", 0))

                    if hasattr(self, "label_eta_frames"):
                        self.label_eta_frames.setText(f"底圖區塊: {chunks_done} / {chunks_total}")
                    if hasattr(self, "label_eta_speed"):
                        self.label_eta_speed.setText("下載底圖切片與 DEM...")
                    if hasattr(self, "label_eta_time"):
                        self.label_eta_time.setText("預熱本機 SSD 快取")
                    if hasattr(self, "label_eta_clock"):
                        self.label_eta_clock.setText("完成後即刻啟動渲染")

                    status = str(data.get("status", f"下載底圖中 ({chunks_done}/{chunks_total})"))
                    self.set_status_message(f"{status} ({pct:.1f}%)")

                    workers_data = data.get("workers", [])
                    for i in range(len(self.worker_bars)):
                        self.worker_bars[i].setValue(int(round(pct)))
                        if i < len(self.worker_status_labels):
                            self.worker_status_labels[i].setText("預熱底圖中")
                else:
                    self.progressBar_main.setValue(int(round(pct)))

                    rendered = data.get("rendered")
                    total = data.get("total")
                    if rendered is not None and total is not None:
                        if hasattr(self, "label_eta_frames"):
                            self.label_eta_frames.setText(f"已完成幀數: {rendered} / {total}")

                    fps = data.get("fps")
                    if fps is not None:
                        if hasattr(self, "label_eta_speed"):
                            self.label_eta_speed.setText(f"渲染速度: {fps:.1f} frame/s")

                    eta_sec = data.get("eta_seconds")
                    if eta_sec is not None and eta_sec >= 0:
                        if hasattr(self, "label_eta_time"):
                            self.label_eta_time.setText(f"預估剩餘時間: {format_seconds_human(eta_sec)}")
                        eta_finish = time.strftime("%H:%M:%S", time.localtime(time.time() + eta_sec))
                        if hasattr(self, "label_eta_clock"):
                            self.label_eta_clock.setText(f"預計完成時刻: {eta_finish}")
                    else:
                        if hasattr(self, "label_eta_time"):
                            self.label_eta_time.setText("預估剩餘時間: --")
                        if hasattr(self, "label_eta_clock"):
                            self.label_eta_clock.setText("預計完成時刻: --:--:--")

                    status = str(data.get("status", "渲染中"))
                    self.set_status_message(f"{status} ({pct:.1f}%)")

                    # 解析每位 Worker 的進度
                    workers_data = data.get("workers", [])
                    for i, w_item in enumerate(workers_data):
                        if isinstance(w_item, dict):
                            w_pct = float(w_item.get("pct", 0.0))
                            w_status = str(w_item.get("status", "待命"))
                        else:
                            w_pct = float(w_item)
                            w_status = f"{w_pct:.0f}%"

                        if i < len(self.worker_bars):
                            self.worker_bars[i].setValue(int(round(w_pct)))
                        if i < len(self.worker_status_labels):
                            self.worker_status_labels[i].setText(w_status)
            except Exception:
                pass

        if "AUTO_TUNE_RESULT:" in line:
            try:
                res = json.loads(line.split("AUTO_TUNE_RESULT:", 1)[1].strip())
                rec = int(res["recommended_workers"])
                peak = float(res.get("peak_fps", 0.0))
                self.state["benchmark_result"] = res
                result_text = f"建議 {rec} Workers | 峰值 {peak:.1f} FPS"
                if hasattr(self, "label_autotune_result"):
                    self.label_autotune_result.setText(result_text)
                if hasattr(self, "lbl_benchmark_result"):
                    self.lbl_benchmark_result.setText(result_text)
                if hasattr(self, "action_apply_benchmark"): self.action_apply_benchmark.setEnabled(True)
                if hasattr(self, "btn_apply_benchmark"):
                    self.btn_apply_benchmark.setEnabled(True)
                if getattr(self, "_advanced_dialog", None) is not None:
                    try:
                        self._advanced_dialog.update_benchmark_result(res)
                    except Exception:
                        pass
                self.set_status_message(f"Auto Tune 完成：建議 {rec} Workers")
            except Exception:
                pass

    def apply_benchmark_recommendation(self):
        res = self.state.get("benchmark_result")
        if res:
            rec = int(res.get("recommended_workers", self.spin_workers.value()))
            self.spin_workers.setValue(rec)
            self.chk_parallel_2.setChecked(rec > 1)
            QMessageBox.information(self, "Auto Tune", f"已自動套用最佳 Workers 建議: {rec}")

    def _finish_proc(self, returncode: int):
        self.state["proc"] = None
        self.set_running(False)
        cfg_p = self.state.get("config_path")
        if cfg_p:
            try: Path(cfg_p).unlink(missing_ok=True)
            except Exception: pass

        self._render_timer.stop()
        final_elapsed = None
        if self._render_start_time is not None:
            final_elapsed = time.time() - self._render_start_time
            if hasattr(self, "label_eta_elapsed"):
                self.label_eta_elapsed.setText(f"渲染計時: {self._format_elapsed_str(final_elapsed)}")
            self._render_start_time = None

        self._write_log("=" * 72)
        if returncode == 0:
            if final_elapsed is not None:
                self._write_log(f"[OK] 程序執行成功完成 (總耗時: {self._format_elapsed_str(final_elapsed)})。")
            else:
                self._write_log("[OK] 程序執行成功完成。")
            self.progressBar_main.setValue(100)
            for bar in self.worker_bars:
                bar.setValue(100)
            for lbl in self.worker_status_labels:
                lbl.setText("完成")
            self.set_status_message("完成！")
            QMessageBox.information(self, "完成", "程序已成功執行完成！")
        else:
            self._write_log(f"[ERROR] 程序執行失敗 (退出碼 {returncode})。")
            self.set_status_message(f"失敗 (退出碼 {returncode})")

        f = self.state.get("log_file")
        if f and not f.closed:
            try:
                f.flush()
                f.close()
            except Exception:
                pass
        self.state["log_file"] = None
        self.refresh_cache_size_display()
        if getattr(self, "_advanced_dialog", None) is not None:
            try:
                self._advanced_dialog.on_benchmark_finished()
            except Exception:
                pass

    def closeEvent(self, event):
        proc = self.state.get("proc")
        if proc and proc.poll() is None:
            mode_name = "效能測試" if self.state.get("proc_mode") == "benchmark" else "渲染"
            reply = QMessageBox.question(
                self, "關閉確認",
                f"{mode_name}仍在執行中。確定要中止並退出嗎？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
            self.stop_render()
        f = self.state.get("log_file")
        if f and not f.closed:
            try:
                f.close()
            except Exception:
                pass

        # 停止背景定時器
        if hasattr(self, "cache_timer") and self.cache_timer.isActive():
            self.cache_timer.stop()

        # 若為 Session 暫存模式，關閉主程式時自動清除當前 Session 快取目錄
        if getattr(config, "MAP_CACHE_MODE", "session") == "session":
            CacheManager.cleanup_current_session()

        event.accept()


def launch_qt_gui():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_qt_gui()
