# -*- coding: utf-8 -*-
"""
PySide6 (Qt) 原生 GUI 主應用程式視窗。
直接讀取 main_window.ui (Ui_MainWindow)，並與 GPX Ride Renderer 的 subprocess 渲染核心完全對接。
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

from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget, QProgressBar
)

from gpx_renderer import config
from gpx_renderer.gui.ui_main_window import Ui_MainWindow
from gpx_renderer.utils import _self_subprocess_command
from gpx_renderer.core.data import quick_gpx_distance_km, auto_duration_seconds, format_seconds_human
from gpx_renderer.core.parallel import _default_benchmark_candidates


RESOLUTION_PRESETS = [
    ("1080p 直式 9:16 (1080×1920) - 社群媒體", 1080, 1920),
    ("1080p 橫式 16:9 (1920×1080) - YouTube", 1920, 1080),
    ("1080p 正方形 1:1 (1080×1080) - 標準方形", 1080, 1080),
    ("720p  直式 9:16 (720×1280)  - 社群媒體", 720, 1280),
    ("720p  橫式 16:9 (1280×720)", 1280, 720),     
    ("IG 貼文直式 4:5 (1080×1350)", 1080, 1350),
    ("1440p 正方形 1:1 (1440×1440) - 高畫質方形", 1440, 1440),
    ("2K 橫式 16:9 (2560×1440)", 2560, 1440),
    ("640×360  超低 16:9 測試 (極速)", 640, 360),
    ("480×480  超低 1:1  測試 (極速)", 480, 480),
    ("360×640  超低 直式 測試 (極速)", 360, 640),
    ("自訂解析度...", None, None),
]

CAMERA_MODE_LABELS = {
    "North-Up": "正北朝上 (North-Up)",
    "Heading-Up": "跟隨行進 (Heading-Up)",
    "3D-Terrain": "3D 真地形 (3D-Terrain)",
}


class SubprocessReaderThread(QThread):
    """讀取渲染/測試子程序 stdout 的線程 Signals"""
    line_signal = Signal(str)
    finished_signal = Signal(int)

    def __init__(self, proc: subprocess.Popen, parent=None):
        super().__init__(parent)
        self.proc = proc

    def run(self):
        buf = ""
        try:
            assert self.proc.stdout is not None
            while True:
                ch = self.proc.stdout.read(1)
                if ch == "":
                    if buf:
                        self.line_signal.emit(buf)
                    break
                if ch in "\r\n":
                    if buf.strip():
                        self.line_signal.emit(buf)
                    buf = ""
                else:
                    buf += ch
        finally:
            rc = self.proc.wait()
            self.finished_signal.emit(rc)


class GpxDistanceThread(QThread):
    """背景讀取 GPX 路線總里程"""
    success_signal = Signal(float)
    failed_signal = Signal(str)

    def __init__(self, gpx_path: str, parent=None):
        super().__init__(parent)
        self.gpx_path = gpx_path

    def run(self):
        try:
            dist = quick_gpx_distance_km(self.gpx_path)
            self.success_signal.emit(dist)
        except Exception as exc:
            self.failed_signal.emit(str(exc))


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("GPX Ride Renderer V1.2.1")

        self.state = {
            "proc": None, "proc_mode": None, "config_path": None,
            "gpx_distance_km": None, "gpx_distance_path": None,
            "benchmark_result": None, "media_overrides_json": "{}",
            "reader_thread": None,
        }

        self.worker_bars: List[QProgressBar] = [
            getattr(self, f"progressBar_worker_{i}", None) for i in range(1, 7)
        ]
        self.worker_bars = [b for b in self.worker_bars if b is not None]

        self.worker_status_labels = [
            getattr(self, f"lbl_worker_status_{i}", None) for i in range(1, 7)
        ]
        self.worker_status_labels = [l for l in self.worker_status_labels if l is not None]

        self._init_combos()
        self._init_default_values()
        self._connect_signals()
        self._update_dashboard_summary()

        # 隱藏進階設定 (預設折疊)
        if hasattr(self, "groupBox"):
            self.groupBox.setVisible(False)
        if hasattr(self, "btn_toggle_advanced_2"):
            self.btn_toggle_advanced_2.setText("進階設定 ▼")

        # 初始適應精簡高度並置中螢幕
        self.adjustSize()
        self.center_on_screen()

        # 開局自動刷新 GPX 距離
        QTimer.singleShot(200, self.refresh_gpx_distance)

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

    def _update_dashboard_summary(self):
        try:
            w, h = self.spin_width.value(), self.spin_height.value()
            fps = self.spin_fps.value()
            dur_text = self.lineEdit_duration.text().strip()
            dur = float(dur_text) if dur_text else 30.0
            is_auto = self.chk_auto_duration.isChecked()
            dur_mode = f"自動時長 {dur:.1f}s" if is_auto else f"手動時長 {dur:.1f}s"
            if hasattr(self, "label_cfg_res"):
                self.label_cfg_res.setText(f"畫面規格: {w}x{h} @ {fps} FPS ({dur_mode})")

            map_raw = self.combo_map_style_2.currentText()
            map_key = map_raw.split(".", 1)[0].strip()
            map_label = config.MAP_STYLE_OPTIONS.get(map_key, ("", ""))[0]
            cam_mode = self.combo_camera_mode_2.currentText()
            zoom = self.combo_local_zoom.currentText()
            if hasattr(self, "label_cfg_map"):
                self.label_cfg_map.setText(f"地圖視角: 風格 [{map_key}] {map_label} | {cam_mode} | Zoom: {zoom}")

            bitrate = self.combo_bitrate.currentText().strip()
            preset = self.combo_preset.currentText().strip()
            has_media = "有媒體卡片" if self.chk_enable_media_2.isChecked() and self.lineEdit_media.text().strip() else "無媒體 Overlay"
            if hasattr(self, "label_cfg_enc"):
                self.label_cfg_enc.setText(f"編碼設定: NVENC {bitrate} (preset: {preset}) | {has_media}")

            parallel = self.chk_parallel_2.isChecked()
            workers = self.spin_workers.value()
            chunks = self.spin_chunks.value()
            cache_info = "停用 Cache" if self.chk_disable_parallel_cache.isChecked() else "啟用 Cache"
            perf_text = f"多程序 ({workers} Workers × {chunks} chunks) | {cache_info}" if parallel else f"單程序渲染 | {cache_info}"
            if hasattr(self, "label_cfg_perf"):
                self.label_cfg_perf.setText(f"效能模式: {perf_text}")
        except Exception:
            pass

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
        self.combo_resolution_2.setCurrentIndex(6)  # 1440p 正方形 1:1

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

    def _init_default_values(self):
        self.lineEdit_gpx.setText(str(Path(config.gpx_filename).resolve()))
        self.lineEdit_output.setText(str(Path(config.output_filename).resolve()))
        self.lineEdit_media.setText(config.MEDIA_PATH)

        self.spin_width.setValue(config.FRAME_WIDTH)
        self.spin_height.setValue(config.FRAME_HEIGHT)
        self.spin_fps.setValue(config.FPS)
        self.lineEdit_duration.setText(str(config.VIDEO_DURATION))
        self.chk_auto_duration.setChecked(config.AUTO_DURATION_DEFAULT)
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

        self.chk_preview.setChecked(config.PREVIEW_MODE)
        self.chk_contextily_cache.setChecked(config.MAP_USE_CACHE)
        self.chk_disable_parallel_cache.setChecked(config.PARALLEL_DISABLE_TILE_CACHE)

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
        self.spin_workers.valueChanged.connect(lambda: self._update_dashboard_summary())
        self.spin_chunks.valueChanged.connect(lambda: self._update_dashboard_summary())
        self.chk_disable_parallel_cache.toggled.connect(lambda: self._update_dashboard_summary())
        self.chk_enable_media_2.toggled.connect(lambda: self._update_dashboard_summary())
        self.lineEdit_media.textChanged.connect(lambda: self._update_dashboard_summary())

        self.chk_auto_duration.toggled.connect(self.on_auto_duration_toggle)
        self.spin_seconds_per_100km.valueChanged.connect(self.on_duration_rate_change)
        self.lineEdit_duration.textChanged.connect(lambda: self._update_dashboard_summary())

        # 加入 400ms Debounce 防抖，避免連續輸入字元快速開線程
        self.gpx_debounce_timer = QTimer(self)
        self.gpx_debounce_timer.setSingleShot(True)
        self.gpx_debounce_timer.timeout.connect(self.refresh_gpx_distance)
        self.lineEdit_gpx.textChanged.connect(lambda: self.gpx_debounce_timer.start(400))

        self.btn_toggle_advanced_2.clicked.connect(self.toggle_advanced)

        self.btn_start_render.clicked.connect(self.start_render)
        self.btn_stop_render.clicked.connect(self.stop_render)
        self.btn_open_log_folder.clicked.connect(self.open_log_folder)

        if hasattr(self, "btn_autotune"):
            self.btn_autotune.clicked.connect(self.start_benchmark)
        if hasattr(self, "btn_benchmark"):
            self.btn_benchmark.clicked.connect(self.start_benchmark)
        if hasattr(self, "btn_apply_benchmark"):
            self.btn_apply_benchmark.clicked.connect(self.apply_benchmark_recommendation)

    # ---------- Slot Implementations ----------
    def toggle_advanced(self):
        is_visible = self.groupBox.isVisible()
        next_state = not is_visible
        self.groupBox.setVisible(next_state)
        self.btn_toggle_advanced_2.setText("進階設定 ▲" if next_state else "進階設定 ▼")

        # 重新計算 Layout 尺寸並自適應調整主視窗高度
        QApplication.processEvents()
        if not next_state:
            self.resize(self.width(), self.sizeHint().height())
            self.adjustSize()
        else:
            self.adjustSize()

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
        p = QFileDialog.getExistingDirectory(self, "選擇路線照片/影片資料夾")
        if not p:
            p, _ = QFileDialog.getOpenFileName(self, "選擇照片或影片檔", "", "媒體檔案 (*.jpg *.jpeg *.png *.webp *.mp4 *.mov)")
        if p:
            self.lineEdit_media.setText(p)
            self.chk_enable_media_2.setChecked(True)

    def open_media_dialog(self):
        media_p = self.lineEdit_media.text().strip()
        gpx_p = self.lineEdit_gpx.text().strip()
        if not media_p:
            QMessageBox.warning(self, "提示", "請先選擇路線媒體路徑。")
            return
        if not gpx_p or not Path(gpx_p).is_file():
            QMessageBox.warning(self, "提示", "請先選擇有效的 GPX 檔案。")
            return

        try:
            from gpx_renderer.core.data import load_gpx
            from gpx_renderer.core.media import scan_media_files
            from gpx_renderer.gui.qt_media_dialog import QtMediaManagerDialog
            from PySide6.QtWidgets import QDialog

            data = load_gpx(
                gpx_p,
                hide_start_km=self.spin_hide_start.value(),
                hide_end_km=self.spin_hide_end.value(),
            )
            scanned = scan_media_files(media_p, time_offset_sec=0.0)

            if not scanned:
                QMessageBox.information(self, "提示", "在指定的媒體路徑下未找到相應的照片或影片。")
                return

            dlg = QtMediaManagerDialog(scanned, data, media_duration=4.0, media_offset_sec=0.0, media_path=media_p, parent=self)
            if dlg.exec() == QDialog.Accepted:
                overrides = dlg.result_overrides
                self.state["media_overrides_json"] = json.dumps(overrides, ensure_ascii=False)
                QMessageBox.information(self, "成功", f"已儲存 {len(overrides)} 個媒體自訂標籤與微調設定！")
        except Exception as exc:
            QMessageBox.critical(self, "錯誤", f"無法開啟媒體管理視窗：{exc}")

    def on_map_change(self):
        pass

    def on_camera_mode_change(self):
        pass

    def apply_profile(self):
        mode = self.combo_profile_2.currentText()
        if mode == "快速":
            self.spin_width.setValue(1000); self.spin_height.setValue(1000)
            self.combo_local_zoom.setCurrentText("auto")
            self.combo_bitrate.setCurrentText("12M"); self.combo_preset.setCurrentText("p3")
            self.spin_workers.setValue(6); self.spin_chunks.setValue(4)
        elif mode == "高畫質":
            self.spin_width.setValue(1440); self.spin_height.setValue(1440)
            self.combo_local_zoom.setCurrentText("17")
            self.combo_bitrate.setCurrentText("30M"); self.combo_preset.setCurrentText("p5")
            self.spin_workers.setValue(6); self.spin_chunks.setValue(4)
        else:
            self.spin_width.setValue(1080); self.spin_height.setValue(1080)
            self.combo_local_zoom.setCurrentText("16")
            self.combo_bitrate.setCurrentText("20M"); self.combo_preset.setCurrentText("p4")
            self.spin_workers.setValue(6); self.spin_chunks.setValue(4)

    def on_res_preset_change(self):
        sel = self.combo_resolution_2.currentText()
        for label, w, h in RESOLUTION_PRESETS:
            if label == sel and w is not None and h is not None:
                self.spin_width.setValue(w)
                self.spin_height.setValue(h)
                break

    def on_custom_dim_change(self):
        w, h = self.spin_width.value(), self.spin_height.value()
        for label, pw, ph in RESOLUTION_PRESETS:
            if pw == w and ph == h:
                self.combo_resolution_2.setCurrentText(label)
                return
        self.combo_resolution_2.setCurrentText("✏️ 自訂解析度...")

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

        return {
            "gpx_filename": dict_self.lineEdit_gpx.text().strip(),
            "output_filename": dict_self.lineEdit_output.text().strip(),
            "map_style_key": map_key,
            "FRAME_WIDTH": dict_self.spin_width.value(),
            "FRAME_HEIGHT": dict_self.spin_height.value(),
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
            "MAP_USE_CACHE": dict_self.chk_contextily_cache.isChecked(),
            "PARALLEL_DISABLE_TILE_CACHE": dict_self.chk_disable_parallel_cache.isChecked(),
            "ENABLE_MEDIA": dict_self.chk_enable_media_2.isChecked(),
            "MEDIA_PATH": dict_self.lineEdit_media.text().strip(),
            "MEDIA_POPUP_DURATION": 4.0,
            "MEDIA_TIME_OFFSET_SEC": 0.0,
            "MEDIA_OVERRIDES_JSON": dict_self.state.get("media_overrides_json", "{}"),
            "USE_REAL_SPEED": dict_self.chk_real_speed_2.isChecked(),
            "HIDE_START_DISTANCE_KM": dict_self.spin_hide_start.value(),
            "HIDE_END_DISTANCE_KM": dict_self.spin_hide_end.value(),
            "CAMERA_MODE": cam_mode,
            "TRACK_COLOR_SCHEME": dict_self.combo_track_color_2.currentText(),
        }

    def set_running(self, running: bool):
        self.btn_start_render.setEnabled(not running)
        if hasattr(self, "btn_autotune"): self.btn_autotune.setEnabled(not running)
        if hasattr(self, "btn_benchmark"): self.btn_benchmark.setEnabled(not running)
        self.btn_stop_render.setEnabled(running)

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

        if hasattr(self, "label_autotune_result"):
            self.label_autotune_result.setText("測試中…")
        self.set_status_message("Auto Tune 效能測試中…")
        self._spawn_job(cfg, "benchmark")

    def _spawn_job(self, cfg: dict, mode: str):
        fd, cfg_path = tempfile.mkstemp(prefix=f"gpx_renderer_{mode}_", suffix=".json")
        os.close(fd)
        Path(cfg_path).write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        self.state["config_path"] = cfg_path

        flag = "--benchmark-config" if mode == "benchmark" else "--render-config"
        cmd = _self_subprocess_command(flag, cfg_path)

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
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

        self.reader_thread = SubprocessReaderThread(proc)
        self.reader_thread.line_signal.connect(self._parse_process_line)
        self.reader_thread.finished_signal.connect(self._finish_proc)
        self.reader_thread.start()

    def stop_render(self):
        proc = self.state.get("proc")
        if proc and proc.poll() is None:
            proc.terminate()
            self.set_status_message("已發送停止訊號…")

    def open_log_folder(self):
        log_dir = Path("logs").resolve()
        log_dir.mkdir(exist_ok=True)
        os.startfile(log_dir)

    def _parse_process_line(self, line: str):
        print(line)  # log to console
        # 解析進度 JSON
        if "[PROGRESS_JSON]" in line or "PROGRESS_JSON:" in line:
            try:
                sep = "[PROGRESS_JSON]" if "[PROGRESS_JSON]" in line else "PROGRESS_JSON:"
                json_str = line.split(sep, 1)[1].strip()
                data = json.loads(json_str)
                pct = float(data.get("pct", data.get("progress_percent", 0.0)))
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

        if returncode == 0:
            self.progressBar_main.setValue(100)
            for bar in self.worker_bars:
                bar.setValue(100)
            for lbl in self.worker_status_labels:
                lbl.setText("完成")
            self.set_status_message("完成！")
            QMessageBox.information(self, "完成", "程序已成功執行完成！")
        else:
            self.set_status_message(f"失敗 (退出碼 {returncode})")


def launch_qt_gui():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_qt_gui()
