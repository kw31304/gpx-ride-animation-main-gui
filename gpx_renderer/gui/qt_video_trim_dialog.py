# -*- coding: utf-8 -*-
"""
PySide6 原生影片裁剪與播放預覽對話框 (QtVideoTrimDialog)。
支援滑桿調整影片頭尾 (起點與結束點)、視窗內即時 30FPS 循環播放預覽、時間戳記跳轉與非破壞性時間軸儲存。
"""

from __future__ import annotations
import os
import math
from typing import Optional
from pathlib import Path

import numpy as np
import cv2

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QImage, QPixmap, QFont, QCursor
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QDoubleSpinBox, QGroupBox, QFrame,
    QMessageBox, QSizePolicy
)

from gpx_renderer.core.media import MediaItem, extract_video_frame


class QtVideoTrimDialog(QDialog):
    """專屬影片裁剪與即時播放預覽視窗。"""

    def __init__(self, item: MediaItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle(f"🎬 影片裁剪與播放預覽 — {item.filename}")
        self.resize(860, 680)
        self.setMinimumSize(740, 580)

        # 讀取影片基本資訊
        self.file_path = str(Path(item.file_path).resolve())
        self.total_duration_sec = 10.0
        self.video_fps = 30.0
        self.video_w = 640
        self.video_h = 480
        self.total_frames = 300
        self._init_video_info()

        # 初始化起點與結束點秒數
        self.start_sec = max(0.0, float(getattr(item, "clip_start_sec", 0.0) or 0.0))
        if item.popup_duration is not None and item.popup_duration > 0:
            self.end_sec = min(self.total_duration_sec, self.start_sec + float(item.popup_duration))
        else:
            self.end_sec = self.total_duration_sec

        if self.end_sec <= self.start_sec:
            self.end_sec = self.total_duration_sec

        self.current_play_sec = self.start_sec
        self.is_playing = False
        self._cap: Optional[cv2.VideoCapture] = None

        # 播放定時器 (30 FPS)
        self.play_timer = QTimer(self)
        self.play_timer.setInterval(33)
        self.play_timer.timeout.connect(self._on_playback_tick)

        self._init_ui()
        self._seek_to(self.start_sec)
        self._update_trim_summary_label()

    def _init_video_info(self):
        """透過 OpenCV 讀取影片時長、FPS 與解析度。"""
        try:
            cap = cv2.VideoCapture(self.file_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                if fps and np.isfinite(fps) and fps > 0:
                    self.video_fps = float(fps)
                if frames and frames > 0:
                    self.total_frames = int(frames)
                    self.total_duration_sec = float(self.total_frames / self.video_fps)
                if w > 0 and h > 0:
                    self.video_w = w
                    self.video_h = h
                cap.release()
        except Exception:
            pass

        if self.item.duration_sec and self.item.duration_sec > 0:
            self.total_duration_sec = float(self.item.duration_sec)

        self.total_duration_sec = max(0.1, round(self.total_duration_sec, 2))

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(14, 12, 14, 12)

        # 1. 頂部資訊標籤
        lbl_top = QLabel(f"📹 檔案：{self.item.filename}  ({self.video_w} × {self.video_h} px | 原始時長：{self._fmt_time(self.total_duration_sec)})")
        lbl_top.setStyleSheet("color: #cbd5e0; font-size: 13px; font-weight: bold;")
        main_layout.addWidget(lbl_top)

        # 2. 視窗中央：16:9 高解析影片預覽視框
        preview_box = QFrame()
        preview_box.setStyleSheet("background-color: #111827; border: 1px solid #374151; border-radius: 6px;")
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(4, 4, 4, 4)

        self.lbl_viewport = QLabel()
        self.lbl_viewport.setAlignment(Qt.AlignCenter)
        self.lbl_viewport.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_viewport.setMinimumHeight(240)
        preview_layout.addWidget(self.lbl_viewport)

        main_layout.addWidget(preview_box, 1)

        # 3. 播放控制與進度列
        play_ctrl_layout = QHBoxLayout()
        play_ctrl_layout.setSpacing(8)

        self.btn_play = QPushButton("▶ 播放")
        self.btn_play.setFixedWidth(85)
        self.btn_play.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_play.setStyleSheet("""
            QPushButton {
                background-color: #3182ce;
                color: #ffffff;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #2b6cb0; }
        """)
        self.btn_play.clicked.connect(self._toggle_playback)
        play_ctrl_layout.addWidget(self.btn_play)

        self.btn_stop = QPushButton("⏹ 停止")
        self.btn_stop.setFixedWidth(75)
        self.btn_stop.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_stop.clicked.connect(self._stop_playback)
        play_ctrl_layout.addWidget(self.btn_stop)

        self.slider_progress = QSlider(Qt.Horizontal)
        self.slider_progress.setRange(0, 1000)
        self.slider_progress.setValue(0)
        self.slider_progress.sliderMoved.connect(self._on_progress_slider_moved)
        play_ctrl_layout.addWidget(self.slider_progress)

        self.lbl_time_display = QLabel("00:00.0 / 00:00.0")
        self.lbl_time_display.setStyleSheet("color: #a0aec0; font-family: monospace; font-size: 12px;")
        play_ctrl_layout.addWidget(self.lbl_time_display)

        main_layout.addLayout(play_ctrl_layout)

        # 4. 頭尾裁剪控制區 (Sliders & SpinBoxes)
        trim_group = QGroupBox(" ✂️ 影片頭尾裁剪範圍設定 (非破壞性時間軸) ")
        trim_layout = QVBoxLayout(trim_group)
        trim_layout.setSpacing(8)
        trim_layout.setContentsMargins(12, 10, 12, 10)

        # 4.1 起點滑桿與設定
        row_start = QHBoxLayout()
        row_start.addWidget(QLabel("🟢 播放起點 (Start)："))
        self.spin_start = QDoubleSpinBox()
        self.spin_start.setRange(0.0, self.total_duration_sec)
        self.spin_start.setSingleStep(0.1)
        self.spin_start.setValue(self.start_sec)
        self.spin_start.setSuffix(" 秒")
        self.spin_start.valueChanged.connect(self._on_spin_start_changed)
        row_start.addWidget(self.spin_start)

        self.slider_start = QSlider(Qt.Horizontal)
        self.slider_start.setRange(0, 1000)
        self.slider_start.setValue(int(round(self.start_sec / self.total_duration_sec * 1000)))
        self.slider_start.sliderMoved.connect(self._on_slider_start_moved)
        row_start.addWidget(self.slider_start, 1)

        btn_set_start = QPushButton("⏮ 設當前為起點")
        btn_set_start.setToolTip("將目前播放預覽的時間設定為影片起點")
        btn_set_start.clicked.connect(self._set_current_as_start)
        row_start.addWidget(btn_set_start)
        trim_layout.addLayout(row_start)

        # 4.2 結束點滑桿與設定
        row_end = QHBoxLayout()
        row_end.addWidget(QLabel("🔴 播放結束 (End)：  "))
        self.spin_end = QDoubleSpinBox()
        self.spin_end.setRange(0.0, self.total_duration_sec)
        self.spin_end.setSingleStep(0.1)
        self.spin_end.setValue(self.end_sec)
        self.spin_end.setSuffix(" 秒")
        self.spin_end.valueChanged.connect(self._on_spin_end_changed)
        row_end.addWidget(self.spin_end)

        self.slider_end = QSlider(Qt.Horizontal)
        self.slider_end.setRange(0, 1000)
        self.slider_end.setValue(int(round(self.end_sec / self.total_duration_sec * 1000)))
        self.slider_end.sliderMoved.connect(self._on_slider_end_moved)
        row_end.addWidget(self.slider_end, 1)

        btn_set_end = QPushButton("⏭ 設當前為結束")
        btn_set_end.setToolTip("將目前播放預覽的時間設定為影片結束點")
        btn_set_end.clicked.connect(self._set_current_as_end)
        row_end.addWidget(btn_set_end)
        trim_layout.addLayout(row_end)

        # 4.3 裁剪摘要卡片與快捷預設
        row_summary = QHBoxLayout()
        self.lbl_trim_summary = QLabel()
        self.lbl_trim_summary.setStyleSheet("color: #68d391; font-weight: bold; font-size: 12px;")
        row_summary.addWidget(self.lbl_trim_summary)
        row_summary.addStretch()

        btn_reset_full = QPushButton("🔄 還原全片長度")
        btn_reset_full.clicked.connect(self._reset_full_video)
        row_summary.addWidget(btn_reset_full)

        btn_pre_3s = QPushButton("⚡ 前 3 秒")
        btn_pre_3s.clicked.connect(lambda: self._apply_duration_preset(3.0))
        row_summary.addWidget(btn_pre_3s)

        btn_pre_5s = QPushButton("⚡ 前 5 秒")
        btn_pre_5s.clicked.connect(lambda: self._apply_duration_preset(5.0))
        row_summary.addWidget(btn_pre_5s)

        trim_layout.addLayout(row_summary)
        main_layout.addWidget(trim_group)

        # 5. 底部確定與取消按鈕
        btn_layout = QHBoxLayout()
        lbl_hint_bot = QLabel("💡 提示：點擊「確定套用」後僅記錄裁剪時間軸，不會修改或覆蓋原始影片檔案。")
        lbl_hint_bot.setStyleSheet("color: #718096; font-size: 11px;")
        btn_layout.addWidget(lbl_hint_bot)
        btn_layout.addStretch()

        btn_cancel = QPushButton("取消")
        btn_cancel.setFixedWidth(90)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_apply = QPushButton("✔ 確定套用")
        btn_apply.setFixedWidth(110)
        btn_apply.setCursor(QCursor(Qt.PointingHandCursor))
        btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #38a169;
                color: #ffffff;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton:hover { background-color: #2f855a; }
        """)
        btn_apply.clicked.connect(self._on_apply)
        btn_layout.addWidget(btn_apply)

        main_layout.addLayout(btn_layout)

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        s = max(0.0, float(seconds))
        m = int(s // 60)
        rem_s = s % 60
        return f"{m:02d}:{rem_s:04.1f}"

    def _seek_to(self, sec: float):
        """跳轉至指定秒數並繪製畫格。"""
        self.current_play_sec = max(0.0, min(self.total_duration_sec, sec))
        self.lbl_time_display.setText(f"{self._fmt_time(self.current_play_sec)} / {self._fmt_time(self.total_duration_sec)}")

        # 更新進度滑桿
        pct = int(round((self.current_play_sec / self.total_duration_sec) * 1000))
        self.slider_progress.blockSignals(True)
        self.slider_progress.setValue(pct)
        self.slider_progress.blockSignals(False)

        # 讀取並渲染畫面
        img = extract_video_frame(self.file_path, time_sec=self.current_play_sec)
        if img is not None:
            rgb = img.convert("RGB")
            data = rgb.tobytes("raw", "RGB")
            qimg = QImage(data, rgb.width, rgb.height, rgb.width * 3, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)

            target_w = max(320, self.lbl_viewport.width() - 8)
            target_h = max(220, self.lbl_viewport.height() - 8)
            scaled = pix.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_viewport.setPixmap(scaled)

    def _toggle_playback(self):
        if self.is_playing:
            self._pause_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        if self.current_play_sec >= self.end_sec or self.current_play_sec < self.start_sec:
            self.current_play_sec = self.start_sec
        self.is_playing = True
        self.btn_play.setText("⏸ 暫停")
        self.play_timer.start()

    def _pause_playback(self):
        self.is_playing = False
        self.btn_play.setText("▶ 播放")
        self.play_timer.stop()

    def _stop_playback(self):
        self._pause_playback()
        self._seek_to(self.start_sec)

    def _on_playback_tick(self):
        step_sec = 0.033
        next_sec = self.current_play_sec + step_sec
        if next_sec >= self.end_sec:
            # 循環回起點播放
            next_sec = self.start_sec
        self._seek_to(next_sec)

    def _on_progress_slider_moved(self, val: int):
        target_sec = (val / 1000.0) * self.total_duration_sec
        self._seek_to(target_sec)

    def _on_slider_start_moved(self, val: int):
        sec = round((val / 1000.0) * self.total_duration_sec, 1)
        if sec > self.end_sec - 0.2:
            sec = max(0.0, self.end_sec - 0.2)
        self.spin_start.blockSignals(True)
        self.spin_start.setValue(sec)
        self.spin_start.blockSignals(False)
        self.start_sec = sec
        self._seek_to(sec)
        self._update_trim_summary_label()

    def _on_spin_start_changed(self, val: float):
        sec = round(val, 1)
        if sec > self.end_sec - 0.2:
            sec = max(0.0, self.end_sec - 0.2)
            self.spin_start.setValue(sec)
        self.start_sec = sec
        self.slider_start.blockSignals(True)
        self.slider_start.setValue(int(round((sec / self.total_duration_sec) * 1000)))
        self.slider_start.blockSignals(False)
        self._seek_to(sec)
        self._update_trim_summary_label()

    def _on_slider_end_moved(self, val: int):
        sec = round((val / 1000.0) * self.total_duration_sec, 1)
        if sec < self.start_sec + 0.2:
            sec = min(self.total_duration_sec, self.start_sec + 0.2)
        self.spin_end.blockSignals(True)
        self.spin_end.setValue(sec)
        self.spin_end.blockSignals(False)
        self.end_sec = sec
        self._seek_to(sec)
        self._update_trim_summary_label()

    def _on_spin_end_changed(self, val: float):
        sec = round(val, 1)
        if sec < self.start_sec + 0.2:
            sec = min(self.total_duration_sec, self.start_sec + 0.2)
            self.spin_end.setValue(sec)
        self.end_sec = sec
        self.slider_end.blockSignals(True)
        self.slider_end.setValue(int(round((sec / self.total_duration_sec) * 1000)))
        self.slider_end.blockSignals(False)
        self._seek_to(sec)
        self._update_trim_summary_label()

    def _set_current_as_start(self):
        sec = round(self.current_play_sec, 1)
        if sec >= self.end_sec:
            sec = max(0.0, self.end_sec - 0.2)
        self.spin_start.setValue(sec)

    def _set_current_as_end(self):
        sec = round(self.current_play_sec, 1)
        if sec <= self.start_sec:
            sec = min(self.total_duration_sec, self.start_sec + 0.2)
        self.spin_end.setValue(sec)

    def _reset_full_video(self):
        self.spin_start.setValue(0.0)
        self.spin_end.setValue(self.total_duration_sec)

    def _apply_duration_preset(self, dur: float):
        st = self.start_sec
        et = min(self.total_duration_sec, st + dur)
        if et - st < dur:
            st = max(0.0, et - dur)
            self.spin_start.setValue(st)
        self.spin_end.setValue(et)

    def _update_trim_summary_label(self):
        dur = max(0.1, self.end_sec - self.start_sec)
        self.lbl_trim_summary.setText(
            f"⏱️ 裁剪後停留時長：{dur:.1f} 秒  |  播放區間：{self._fmt_time(self.start_sec)} ~ {self._fmt_time(self.end_sec)}  |  原片長度：{self._fmt_time(self.total_duration_sec)}"
        )

    def _on_apply(self):
        self._pause_playback()
        dur = max(0.1, round(self.end_sec - self.start_sec, 2))
        self.item.clip_start_sec = round(self.start_sec, 2)
        self.item.popup_duration = dur
        self.accept()

    def closeEvent(self, event):
        self._pause_playback()
        super().closeEvent(event)