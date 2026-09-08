# -*- coding: utf-8 -*-
"""
進階渲染參數設定對話框 (AdvancedSettingsDialog)
提供使用者自訂解析度、並行運算進程、圖資連線數、NVENC 編碼參數等進階設定。
"""

from __future__ import annotations
from typing import Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QSpinBox, QComboBox, QCheckBox, QPushButton,
    QDialogButtonBox
)
from gpx_renderer import config


class AdvancedSettingsDialog(QDialog):
    """
    進階渲染參數設定對話框。
    """
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        custom_width: int = 1440,
        custom_height: int = 1440,
        workers: int = 6,
        chunks: int = 4,
        connections: int = 16,
        preset: str = "p4",
        bitrate: str = "20M",
        basemap: bool = True,
        parallel: bool = True,
        enable_media: bool = True,
        preview_mode: bool = False,
    ):
        super().__init__(parent)
        self.setWindowTitle("進階渲染參數設定")
        self.resize(480, 460)
        self.setModal(True)

        # 儲存傳入的初始值
        self._init_w = custom_width
        self._init_h = custom_height
        self._init_workers = workers
        self._init_chunks = chunks
        self._init_conn = connections
        self._init_preset = preset
        self._init_bitrate = bitrate
        self._init_basemap = basemap
        self._init_parallel = parallel
        self._init_enable_media = enable_media
        self._init_preview_mode = preview_mode

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # 1. 自訂畫面解析度
        grp_res = QGroupBox("自訂畫面解析度 (Custom Resolution)", self)
        res_layout = QGridLayout(grp_res)
        res_layout.addWidget(QLabel("寬度 (Width):"), 0, 0)
        self.spin_w = QSpinBox(grp_res)
        self.spin_w.setRange(240, 7680)
        self.spin_w.setSingleStep(2)
        self.spin_w.setValue(self._init_w)
        self.spin_w.setSuffix(" px")
        res_layout.addWidget(self.spin_w, 0, 1)

        res_layout.addWidget(QLabel("高度 (Height):"), 0, 2)
        self.spin_h = QSpinBox(grp_res)
        self.spin_h.setRange(240, 7680)
        self.spin_h.setSingleStep(2)
        self.spin_h.setValue(self._init_h)
        self.spin_h.setSuffix(" px")
        res_layout.addWidget(self.spin_h, 0, 3)

        btn_preset_1080p = QPushButton("1080p (1920×1080)")
        btn_preset_1080p.clicked.connect(lambda: (self.spin_w.setValue(1920), self.spin_h.setValue(1080)))
        btn_preset_sq = QPushButton("方形 (1440×1440)")
        btn_preset_sq.clicked.connect(lambda: (self.spin_w.setValue(1440), self.spin_h.setValue(1440)))
        btn_preset_vert = QPushButton("直式 (1080×1920)")
        btn_preset_vert.clicked.connect(lambda: (self.spin_w.setValue(1080), self.spin_h.setValue(1920)))

        h_presets = QHBoxLayout()
        h_presets.addWidget(btn_preset_1080p)
        h_presets.addWidget(btn_preset_sq)
        h_presets.addWidget(btn_preset_vert)
        res_layout.addLayout(h_presets, 1, 0, 1, 4)

        main_layout.addWidget(grp_res)

        # 2. 並行運算與圖資下載
        grp_perf = QGroupBox("並行算力與網路連線", self)
        perf_layout = QGridLayout(grp_perf)

        perf_layout.addWidget(QLabel("工作進程數 (Workers):"), 0, 0)
        self.spin_workers = QSpinBox(grp_perf)
        self.spin_workers.setRange(1, 32)
        self.spin_workers.setValue(self._init_workers)
        perf_layout.addWidget(self.spin_workers, 0, 1)

        perf_layout.addWidget(QLabel("每進程切片數 (Chunks):"), 0, 2)
        self.spin_chunks = QSpinBox(grp_perf)
        self.spin_chunks.setRange(1, 16)
        self.spin_chunks.setValue(self._init_chunks)
        perf_layout.addWidget(self.spin_chunks, 0, 3)

        perf_layout.addWidget(QLabel("圖資並行下載數:"), 1, 0)
        self.spin_conn = QSpinBox(grp_perf)
        self.spin_conn.setRange(1, 64)
        self.spin_conn.setValue(self._init_conn)
        self.spin_conn.setSuffix(" 條連線")
        perf_layout.addWidget(self.spin_conn, 1, 1)

        main_layout.addWidget(grp_perf)

        # 3. NVENC 硬體編碼器
        grp_enc = QGroupBox("NVENC 硬體編碼器設定", self)
        enc_layout = QGridLayout(grp_enc)

        enc_layout.addWidget(QLabel("編碼預設檔 (Preset):"), 0, 0)
        self.combo_preset = QComboBox(grp_enc)
        self.combo_preset.addItems(["p1", "p2", "p3", "p4", "p5", "p6", "p7"])
        self.combo_preset.setCurrentText(self._init_preset)
        enc_layout.addWidget(self.combo_preset, 0, 1)

        enc_layout.addWidget(QLabel("影片位元率 (Bitrate):"), 0, 2)
        self.combo_bitrate = QComboBox(grp_enc)
        self.combo_bitrate.addItems(["8M", "12M", "20M", "24M", "30M", "40M", "60M"])
        self.combo_bitrate.setCurrentText(self._init_bitrate)
        enc_layout.addWidget(self.combo_bitrate, 0, 3)

        main_layout.addWidget(grp_enc)

        # 4. 渲染功能開關
        grp_switches = QGroupBox("渲染功能開關", self)
        sw_layout = QGridLayout(grp_switches)

        self.chk_basemap = QCheckBox("啟用地圖底圖 (Basemap)", grp_switches)
        self.chk_basemap.setChecked(self._init_basemap)
        sw_layout.addWidget(self.chk_basemap, 0, 0)

        self.chk_parallel = QCheckBox("啟用多進程並行渲染", grp_switches)
        self.chk_parallel.setChecked(self._init_parallel)
        sw_layout.addWidget(self.chk_parallel, 0, 1)

        self.chk_enable_media = QCheckBox("啟用相片與影片插入", grp_switches)
        self.chk_enable_media.setChecked(self._init_enable_media)
        sw_layout.addWidget(self.chk_enable_media, 1, 0)

        self.chk_preview = QCheckBox("預覽模式 (快速低畫質測試)", grp_switches)
        self.chk_preview.setChecked(self._init_preview_mode)
        sw_layout.addWidget(self.chk_preview, 1, 1)

        main_layout.addWidget(grp_switches)

        # 按鈕列
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.button(QDialogButtonBox.Ok).setText("套用並儲存")
        button_box.button(QDialogButtonBox.Cancel).setText("取消")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def get_values(self) -> dict:
        return {
            "custom_width": self.spin_w.value(),
            "custom_height": self.spin_h.value(),
            "workers": self.spin_workers.value(),
            "chunks": self.spin_chunks.value(),
            "connections": self.spin_conn.value(),
            "preset": self.combo_preset.currentText().strip(),
            "bitrate": self.combo_bitrate.currentText().strip(),
            "basemap": self.chk_basemap.isChecked(),
            "parallel": self.chk_parallel.isChecked(),
            "enable_media": self.chk_enable_media.isChecked(),
            "preview_mode": self.chk_preview.isChecked(),
        }
