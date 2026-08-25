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

from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer, QSettings, QSize
from PySide6.QtGui import QIcon, QActionGroup
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget, QProgressBar,
    QHBoxLayout, QVBoxLayout, QGridLayout
)

from gpx_renderer import config, __version__
from gpx_renderer.gui.main_window.ui_main_window import Ui_MainWindow
from gpx_renderer.gui.main_window.main_workers import (
    SubprocessReaderThread, GpxDistanceThread, CacheSizeWorkerThread
)
from gpx_renderer.gui.widgets.py_circular_progress import PyCircularProgress
from gpx_renderer.utils import _self_subprocess_command, application_dir
from gpx_renderer.core.data import quick_gpx_distance_km, auto_duration_seconds, format_seconds_human
from gpx_renderer.core.parallel import _default_benchmark_candidates
from gpx_renderer.core.cache_manager import CacheManager


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


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(f"GPX Ride Renderer V{__version__}")

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

        # 升級主進度區為現代化圓形進度儀表板
        self._setup_circular_dashboard()

        self._init_combos()
        self._init_default_values()
        self._init_toolbar_and_menus()
        self._connect_signals()
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

    def _setup_circular_dashboard(self):
        """將 groupBox_main_progress 升級為現代化圓形進度儀表板"""
        if not hasattr(self, "groupBox_main_progress"):
            return

        # 隱藏原有水平 progressBar_main
        if hasattr(self, "progressBar_main") and self.progressBar_main is not None:
            self.progressBar_main.hide()

        # 建立圓形進度條 (科技青藍配色、正圓置中、柔和陰影)
        self.circular_progress_main = PyCircularProgress(
            value=0,
            progress_width=10,
            is_rounded=True,
            max_value=100,
            progress_color="#00adb5",
            bg_color="#2b2d42",
            text_color="#ffffff",
            font_size=15,
            suffix="%",
            parent=self.groupBox_main_progress,
        )
        self.circular_progress_main.setFixedSize(115, 115)
        self.circular_progress_main.add_shadow(True)

        # 重新排版 groupBox_main_progress 內部：左邊放置圓形進度環，右邊放置 ETA 資訊網格
        container_layout = QHBoxLayout()
        container_layout.setContentsMargins(6, 4, 6, 4)
        container_layout.setSpacing(16)

        container_layout.addWidget(self.circular_progress_main, 0, Qt.AlignCenter)

        eta_grid = QGridLayout()
        eta_grid.setHorizontalSpacing(14)
        eta_grid.setVerticalSpacing(6)

        if hasattr(self, "label_eta_elapsed"):
            eta_grid.addWidget(self.label_eta_elapsed, 0, 0)
        if hasattr(self, "label_eta_time"):
            eta_grid.addWidget(self.label_eta_time, 0, 1)
        if hasattr(self, "label_eta_clock"):
            eta_grid.addWidget(self.label_eta_clock, 1, 0)
        if hasattr(self, "label_eta_speed"):
            eta_grid.addWidget(self.label_eta_speed, 1, 1)
        if hasattr(self, "label_eta_frames"):
            eta_grid.addWidget(self.label_eta_frames, 2, 0, 1, 2)

        container_layout.addLayout(eta_grid, 1)

        # 加入主進度排版
        if hasattr(self, "verticalLayout_main_progress"):
            # 若已有水平 ETA 佈局，將其隱藏以避免重複
            if hasattr(self, "horizontalLayout_eta"):
                for i in range(self.horizontalLayout_eta.count()):
                    w = self.horizontalLayout_eta.itemAt(i).widget()
                    if w:
                        w.setParent(None)
            self.verticalLayout_main_progress.addLayout(container_layout)

        # 將 self.progressBar_main 指向圓形進度條實例，實現 API 完全相容
        self.progressBar_main = self.circular_progress_main

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
                        scanned = scan_media_files(media_p)
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

            if media_item_count > 0:
                if media_video_count > 0 and media_photo_count > 0:
                    media_tag = f" + 媒體 {media_item_count}個(影片 {media_video_count}部 +{video_added_sec:.1f}s, 相片 {media_photo_count}張 +{photo_added_sec:.1f}s) 總計+{media_added_sec:.1f}s"
                elif media_video_count > 0:
                    media_tag = f" + 影片 {media_video_count}部 (停留 +{video_added_sec:.1f}s)"
                else:
                    media_tag = f" + 相片 {media_photo_count}張 (停留 +{media_added_sec:.1f}s)"
                dur_mode = f"基礎 {base_dur:.1f}s{media_tag} → 總時長約 {total_anim_sec:.1f}s"
            else:
                dur_mode = f"自動時長 {base_dur:.1f}s" if is_auto else f"手動時長 {base_dur:.1f}s"

            if hasattr(self, "label_cfg_res"):
                self.label_cfg_res.setText(f"畫面規格: {w}x{h} @ {fps} FPS ({dur_mode})")

            # 更新 GPX 距離與總時長資訊列
            dist = self.state.get("gpx_distance_km")
            if dist is not None and hasattr(self, "label_distance_info"):
                m_total = int(total_anim_sec // 60)
                s_total = int(round(total_anim_sec % 60))
                time_str = f"{m_total:02d}:{s_total:02d}" if m_total > 0 else f"{total_anim_sec:.1f}s"
                if media_item_count > 0:
                    self.label_distance_info.setText(
                        f"GPX 距離：{dist:.2f} km  |  主動畫：{base_dur:.1f}s  |  媒體 {media_item_count} 個 (+{media_added_sec:.1f}s，含影片 +{video_added_sec:.1f}s, 相片 +{photo_added_sec:.1f}s)  |  預估總時長：約 {total_anim_sec:.1f}s ({time_str})"
                    )
                else:
                    mode_txt = "自動" if is_auto else "手動"
                    self.label_distance_info.setText(
                        f"GPX 距離：{dist:.2f} km  →  主動畫 {base_dur:.1f}s ({format_seconds_human(base_dur)}，{mode_txt})"
                    )

            map_raw = self.combo_map_style_2.currentText()
            map_key = map_raw.split(".", 1)[0].strip()
            map_label = config.MAP_STYLE_OPTIONS.get(map_key, ("", ""))[0]
            cam_mode = self.combo_camera_mode_2.currentText()
            zoom = self.combo_local_zoom.currentText()
            if hasattr(self, "label_cfg_map"):
                self.label_cfg_map.setText(f"地圖視角: 風格 [{map_key}] {map_label} | {cam_mode} | Zoom: {zoom}")

            bitrate = self.combo_bitrate.currentText().strip()
            preset = self.combo_preset.currentText().strip()
            if media_item_count > 0:
                has_media = f"路線媒體: {media_item_count} 個 (影片 {media_video_count} 部 +{video_added_sec:.1f}s, 相片 {media_photo_count} 張)"
            elif has_media_enabled:
                has_media = "已啟用媒體"
            else:
                has_media = "無媒體 Overlay"

            if hasattr(self, "label_cfg_enc"):
                self.label_cfg_enc.setText(f"編碼設定: NVENC {bitrate} (preset: {preset}) | {has_media}")

            parallel = self.chk_parallel_2.isChecked()
            workers = self.spin_workers.value()
            chunks = self.spin_chunks.value()
            cache_mode_txt = "永久保留快取" if self.combo_cache_mode.currentIndex() == 1 else "自動暫存 (關閉清除)"
            perf_text = f"多程序 ({workers} Workers × {chunks} chunks) | {cache_mode_txt}" if parallel else f"單程序渲染 | {cache_mode_txt}"
            if hasattr(self, "label_cfg_perf"):
                self.label_cfg_perf.setText(f"效能模式: {perf_text}")
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

        # 資訊面板雙向連動
        if hasattr(self, "action_show_speed") and hasattr(self, "chk_show_speed"):
            self.action_show_speed.toggled.connect(self.chk_show_speed.setChecked)
            self.chk_show_speed.toggled.connect(self.action_show_speed.setChecked)
        if hasattr(self, "action_show_minimap") and hasattr(self, "chk_show_minimap"):
            self.action_show_minimap.toggled.connect(self.chk_show_minimap.setChecked)
            self.chk_show_minimap.toggled.connect(self.action_show_minimap.setChecked)
        if hasattr(self, "action_show_elevation") and hasattr(self, "chk_show_elevation"):
            self.action_show_elevation.toggled.connect(self.chk_show_elevation.setChecked)
            self.chk_show_elevation.toggled.connect(self.action_show_elevation.setChecked)

        # 鏡頭與渲染特性雙向連動
        if hasattr(self, "action_dynamic_speed_zoom") and hasattr(self, "chk_dynamic_speed_zoom"):
            self.action_dynamic_speed_zoom.toggled.connect(self.chk_dynamic_speed_zoom.setChecked)
            self.chk_dynamic_speed_zoom.toggled.connect(self.action_dynamic_speed_zoom.setChecked)
        if hasattr(self, "action_real_speed") and hasattr(self, "chk_real_speed_2"):
            self.action_real_speed.toggled.connect(self.chk_real_speed_2.setChecked)
            self.chk_real_speed_2.toggled.connect(self.action_real_speed.setChecked)
        if hasattr(self, "action_basemap") and hasattr(self, "chk_basemap_2"):
            self.action_basemap.toggled.connect(self.chk_basemap_2.setChecked)
            self.chk_basemap_2.toggled.connect(self.action_basemap.setChecked)
        if hasattr(self, "action_parallel") and hasattr(self, "chk_parallel_2"):
            self.action_parallel.toggled.connect(self.chk_parallel_2.setChecked)
            self.chk_parallel_2.toggled.connect(self.action_parallel.setChecked)
        if hasattr(self, "action_enable_media") and hasattr(self, "chk_enable_media_2"):
            self.action_enable_media.toggled.connect(self.chk_enable_media_2.setChecked)
            self.chk_enable_media_2.toggled.connect(self.action_enable_media.setChecked)
        if hasattr(self, "action_preview") and hasattr(self, "chk_preview"):
            self.action_preview.toggled.connect(self.chk_preview.setChecked)
            self.chk_preview.toggled.connect(self.action_preview.setChecked)

        # 快取模式互斥群組與雙向連動
        from PySide6.QtGui import QActionGroup
        self.cache_action_group = QActionGroup(self)
        if hasattr(self, "action_cache_session") and hasattr(self, "action_cache_persistent"):
            self.action_cache_session.setActionGroup(self.cache_action_group)
            self.action_cache_persistent.setActionGroup(self.cache_action_group)
            cur_idx = 1 if getattr(config, "MAP_CACHE_MODE", "session") == "persistent" else 0
            self.action_cache_session.setChecked(cur_idx == 0)
            self.action_cache_persistent.setChecked(cur_idx == 1)
            self.action_cache_session.triggered.connect(lambda: self.combo_cache_mode.setCurrentIndex(0))
            self.action_cache_persistent.triggered.connect(lambda: self.combo_cache_mode.setCurrentIndex(1))

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

        # 2. 地圖風格
        self.combo_map_style_2.clear()
        self.map_labels = [f"{k}. {v[0]}" for k, v in config.MAP_STYLE_OPTIONS.items()]
        self.combo_map_style_2.addItems(self.map_labels)

        # 3. 視角模式
        self.combo_camera_mode_2.clear()
        self.combo_camera_mode_2.addItems(list(CAMERA_MODE_LABELS.values()))

        # 4. 解析度預設
        self.combo_resolution_2.clear()
        self.combo_resolution_2.addItems([p[0] for p in RESOLUTION_PRESETS])
        self._set_resolution_by_dim(1440, 1440)

        # 5. 軌跡顏色
        self.combo_track_color_2.clear()
        self.combo_track_color_2.addItems(config.TRACK_COLOR_OPTIONS)

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

        # 9. 快取模式
        self.combo_cache_mode.clear()
        self.combo_cache_mode.addItems(["自動暫存 (關閉清除)", "永久保留 (保留快取)"])
        self.combo_cache_mode.setCurrentIndex(1 if getattr(config, "MAP_CACHE_MODE", "session") == "persistent" else 0)

    def _init_default_values(self):
        self.lineEdit_gpx.setText(str(Path(config.gpx_filename).resolve()))
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
        self.lineEdit_duration.setText(str(config.VIDEO_DURATION))
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

        self.spin_hide_start.setValue(config.HIDE_START_DISTANCE_KM)
        self.spin_hide_end.setValue(config.HIDE_END_DISTANCE_KM)

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

        self.combo_cache_mode.currentIndexChanged.connect(self.on_cache_mode_change)
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

    def on_cache_mode_change(self, idx: int):
        mode = "session" if idx == 0 else "persistent"
        config.MAP_CACHE_MODE = mode
        if hasattr(self, "settings"):
            self.settings.setValue("map_cache_mode", mode)
        CacheManager.init_cache_system()
        if hasattr(self, "action_cache_session") and hasattr(self, "action_cache_persistent"):
            self.action_cache_session.blockSignals(True)
            self.action_cache_persistent.blockSignals(True)
            self.action_cache_session.setChecked(idx == 0)
            self.action_cache_persistent.setChecked(idx == 1)
            self.action_cache_session.blockSignals(False)
            self.action_cache_persistent.blockSignals(False)
        self.refresh_cache_size_display()
        self._update_dashboard_summary()

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
                self._update_dashboard_summary()
        elif chosen == act_folder:
            p = QFileDialog.getExistingDirectory(self, "選擇路線照片/影片資料夾")
            if p:
                self.lineEdit_media.setText(p)
                self.chk_enable_media_2.setChecked(True)
                self._update_dashboard_summary()

    def open_media_dialog(self):
        media_p = self.lineEdit_media.text().strip()
        gpx_p = self.lineEdit_gpx.text().strip()
        if not gpx_p or not Path(gpx_p).is_file():
            QMessageBox.warning(self, "提示", "請先選擇有效的 GPX 檔案。")
            return

        try:
            from gpx_renderer.core.data import load_gpx
            from gpx_renderer.core.media import scan_media_files
            from gpx_renderer.gui.media_dialog import QtMediaManagerDialog
            from PySide6.QtWidgets import QDialog

            data = load_gpx(
                gpx_p,
                hide_start_km=self.spin_hide_start.value(),
                hide_end_km=self.spin_hide_end.value(),
            )
            scanned = scan_media_files(media_p, time_offset_sec=0.0) if media_p else []

            initial_dur = float(self.state.get("media_popup_duration") or config.MEDIA_POPUP_DURATION)
            initial_offset = float(self.state.get("media_time_offset_sec") or config.MEDIA_TIME_OFFSET_SEC)
            initial_caption_size = int(self.state.get("media_caption_font_size") or getattr(config, "MEDIA_CAPTION_FONT_SIZE", 22))
            cur_w = int(self.spin_width.value())
            cur_h = int(self.spin_height.value())
            dlg = QtMediaManagerDialog(
                scanned,
                data,
                media_duration=initial_dur,
                media_offset_sec=initial_offset,
                media_path=media_p,
                default_caption_size=initial_caption_size,
                frame_width=cur_w,
                frame_height=cur_h,
                parent=self,
            )
            if dlg.exec() == QDialog.Accepted:
                overrides = dlg.result_overrides
                self.state["media_overrides_json"] = json.dumps(overrides, ensure_ascii=False)
                self.state["media_popup_duration"] = float(dlg.spin_photo_dur.value())
                self.state["media_caption_font_size"] = int(dlg.spin_default_caption_size.value())
                self.state["media_time_offset_sec"] = float(dlg.spin_media_offset.value())
                config.MEDIA_POPUP_DURATION = float(dlg.spin_photo_dur.value())
                config.MEDIA_CAPTION_FONT_SIZE = int(dlg.spin_default_caption_size.value())
                config.MEDIA_TIME_OFFSET_SEC = float(dlg.spin_media_offset.value())
                config.MEDIA_OVERRIDES_JSON = self.state["media_overrides_json"]

                # 若在對話框內切換了模擬解析度，同步更新主畫面解析度
                if hasattr(dlg, "result_frame_size") and dlg.result_frame_size:
                    new_w, new_h = dlg.result_frame_size
                    if new_w > 0 and new_h > 0 and (new_w != cur_w or new_h != cur_h):
                        self.spin_width.setValue(new_w)
                        self.spin_height.setValue(new_h)
                        config.FRAME_WIDTH = new_w
                        config.FRAME_HEIGHT = new_h

                # 若在對話框內新增或變更了媒體項目，同步回傳更新主介面路徑
                if getattr(dlg, "media_items", None):
                    all_paths = [it.file_path for it in dlg.media_items]
                    if len(all_paths) > 0 and (not media_p or len(all_paths) > len(scanned)):
                        self.lineEdit_media.setText("; ".join(all_paths))
                        self.chk_enable_media_2.setChecked(True)

                self._update_dashboard_summary()
                QMessageBox.information(self, "成功", f"已儲存媒體自訂標籤與微調設定！")
        except Exception as exc:
            QMessageBox.critical(self, "錯誤", f"無法開啟媒體管理視窗：{exc}")

    def on_map_change(self):
        pass

    def on_camera_mode_change(self):
        pass

    def _set_resolution_by_dim(self, w: int, h: int):
        """依寬高自動選擇對應的解析度預設項目"""
        for label, pw, ph in RESOLUTION_PRESETS:
            if pw == w and ph == h:
                self.combo_resolution_2.setCurrentText(label)
                return

    def apply_profile(self):
        mode = self.combo_profile_2.currentText()
        if mode == "快速":
            self._set_resolution_by_dim(1280, 720)
            self.combo_local_zoom.setCurrentText("auto")
            self.combo_bitrate.setCurrentText("12M"); self.combo_preset.setCurrentText("p3")
            self.spin_workers.setValue(6); self.spin_chunks.setValue(4)
        elif mode == "高畫質":
            self._set_resolution_by_dim(1440, 1440)
            self.combo_local_zoom.setCurrentText("17")
            self.combo_bitrate.setCurrentText("30M"); self.combo_preset.setCurrentText("p5")
            self.spin_workers.setValue(6); self.spin_chunks.setValue(4)
        else:
            self._set_resolution_by_dim(1080, 1080)
            self.combo_local_zoom.setCurrentText("16")
            self.combo_bitrate.setCurrentText("20M"); self.combo_preset.setCurrentText("p4")
            self.spin_workers.setValue(6); self.spin_chunks.setValue(4)

    def get_current_resolution(self) -> tuple[int, int]:
        """解析度優先採用一般設定的下拉選單；選「自訂解析度」才採用進階設定的自訂寬高。"""
        sel = self.combo_resolution_2.currentText()
        for label, pw, ph in RESOLUTION_PRESETS:
            if label == sel and pw is not None and ph is not None:
                return pw, ph
        # 若為「自訂解析度...」，才採用進階設定中的 spin_width 與 spin_height
        w = max(240, min(7680, self.spin_width.value()))
        h = max(240, min(7680, self.spin_height.value()))
        # 確保為偶數 (H.264 / NVENC 編碼要求)
        w = (w // 2) * 2
        h = (h // 2) * 2
        return w, h

    def on_res_preset_change(self):
        sel = self.combo_resolution_2.currentText()
        is_custom = False
        for label, w, h in RESOLUTION_PRESETS:
            if label == sel:
                if w is not None and h is not None:
                    self.spin_width.blockSignals(True)
                    self.spin_height.blockSignals(True)
                    self.spin_width.setValue(w)
                    self.spin_height.setValue(h)
                    self.spin_width.blockSignals(False)
                    self.spin_height.blockSignals(False)
                else:
                    is_custom = True
                break

        if is_custom:
            self.toggle_advanced(show=True)
            self.spin_width.setFocus()
            self.spin_width.selectAll()

        self._update_dashboard_summary()

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
        self._update_dashboard_summary()

    def on_auto_duration_toggle(self):
        is_auto = self.chk_auto_duration.isChecked()
        self.lineEdit_duration.setEnabled(not is_auto)
        if is_auto:
            self.refresh_gpx_distance()
        elif self.state.get("gpx_distance_km") is not None:
            dist = self.state["gpx_distance_km"]
            self.label_distance_info.setText(f"GPX 距離：{dist:.2f} km (手動秒數)")

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
            self.label_distance_info.setText("GPX 距離：找不到檔案")
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

    def _on_dist_failed(self, err: str):
        self.state["gpx_distance_km"] = None
        self.state["gpx_distance_path"] = None
        self.label_distance_info.setText(f"GPX 距離：讀取失敗 ({err})")

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
            "MAP_CACHE_MODE": "session" if dict_self.combo_cache_mode.currentIndex() == 0 else "persistent",
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
